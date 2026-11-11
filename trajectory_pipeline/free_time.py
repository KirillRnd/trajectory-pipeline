"""Constrained fuel minimization with duration as a decision variable.

Follows venus_cycle.m / fun2min_core.m: hold launch date, optimize duration
and shooting variables, reevaluate the moving target for every trial.
"""
from copy import deepcopy
from dataclasses import replace
from time import perf_counter
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize
from scipy.special import softmax
from .problem import Mission,departure_speed_limit
from .data import Scales,DAY_S
from .bounded import canonical,assemble,verify_bounded
from .bounded_model import BoundedModel,origin_and_boundary
from .contract import configuration_hash,make_request,audit_configuration
from .ephemerides import Ephemerides


def audit_time_result(result,requested):
    """Bind a resolved duration to the original date/hardware/bounds request."""
    from .contract import specification
    actual=Mission(**result.metadata['mission'])
    if requested.time_policy is None:return audit_configuration(result,requested,make_request(requested),require_final=True)
    expected=replace(requested,tof_days=actual.tof_days,time_policy=None)
    if specification(expected)!=specification(actual):raise ValueError('Free-time result changes parameters other than duration')
    lo,hi=requested.time_policy['bounds_days']
    if not lo<=actual.tof_days<=hi:raise ValueError('Resolved duration outside requested bounds')
    record=result.metadata.get('free_time',{})
    if not record.get('optimizer_success') or record.get('bounds_days')!=[float(lo),float(hi)]:
        raise ValueError('Missing verified duration optimization')
    return audit_configuration(result,actual,make_request(actual),require_final=True)


def run_time_pipeline(mission,output,resume=False):
    """Cold ILTT path, followed by the same constrained release as the sweep."""
    from pathlib import Path
    import json
    from .runner import run_pipeline
    from .data import Trajectory,write_json
    from .kiam_verification import verify_kiam_psi
    output=Path(output)
    if resume:
        if Mission.load(output/'mission.json').to_dict()!=mission.to_dict():raise ValueError('Time-release resume changed request')
        if (output/'final').exists():
            result=Trajectory.load(output/'final');audit_time_result(result,mission)
            if not verify_bounded(result)['passed']:raise ValueError('Saved free-time result failed replay')
            return result,json.loads((output/'summary.json').read_text())
    output.mkdir(parents=True,exist_ok=resume)
    write_json(output/'mission.json',mission.to_dict())
    if any(x is not None for x in (mission.capture,mission.parking_departure,mission.orbital_maneuvers,mission.lunar)):
        raise ValueError('Free-time orbital coupling is not available; a fixed-time mission is not an acceptable substitute')
    write_json(output/'request.json',make_request(mission))
    bounds=mission.time_policy['bounds_days'];base=replace(mission,time_policy=None)
    ephemerides=Ephemerides()
    for body in (mission.departure,mission.target):
        coverage=ephemerides.coverage(body)
        if mission.launch_jd<coverage['start_jd'] or mission.launch_jd+bounds[1]>coverage['stop_jd']:
            raise ValueError('Ephemerides do not cover the full free-duration interval: '+body)
    # Generate alternative initial durations from the actual ILTT lambda law.
    # Every anchor uses this departure date, and a fresh cold ILTT chain.
    from .irt import _module,iltt_seeds
    initial,target,scales=base.boundary();rf=scales.normalize_state(target)[:3];vf=scales.normalize_state(target)[3:]
    energy=2/np.linalg.norm(rf)-vf@vf;kappa=1/energy if energy>0 else np.linalg.norm(rf)
    toolbox=_module('_pipeline_iltt','ILTT/ILTTToolbox.py')
    durations=[base.tof_days]
    for info,_ in iltt_seeds(*[scales.normalize_state(initial)[:3],scales.normalize_state(initial)[3:],rf,vf],base.tof_days*DAY_S/scales.time_s):
        duration=float(2*np.pi*toolbox.T_a(info['lambda_turns'],kappa)*scales.time_s/DAY_S)
        if bounds[0]<duration<bounds[1] and all(abs(duration-t)>1 for t in durations):durations.append(duration)
    history=[];result=None
    for index,duration in enumerate(durations):
        child=replace(base,tof_days=duration);folder=output/f'anchor_{index:02d}'
        write_json(output/'summary.json',dict(case_id=mission.case_id,status='running',phase='iltt_anchor',anchor=index,seed_tof_days=duration))
        current,status=run_pipeline(child,folder,resume=resume and folder.exists())
        row=dict(seed_tof_days=duration,anchor_status=status['status'],phase=status.get('phase'),error=status.get('error'))
        if status['status']=='completed':
            write_json(output/'summary.json',dict(case_id=mission.case_id,status='running',phase='time_release',anchor=index,seed_tof_days=duration))
            try:
                result=release_duration(current,current,bounds,perf_counter()+float(mission.solver.get('free_time_budget_s',120.)))
                audit_time_result(result,mission)
                kiam=verify_kiam_psi(result)
                if not kiam['passed']:raise RuntimeError('Free-time KIAM check failed')
                row.update(status='completed',resolved_tof_days=result.metadata['mission']['tof_days'])
                result.metadata['kiam_verification']=kiam
            except (ValueError,RuntimeError,TimeoutError) as exc:
                result=None;row.update(status='partial',phase='time_release',error=str(exc))
        else:row['status']='partial'
        history.append(row);write_json(output/'time_history.json',history)
        if result is not None:break
    summary=dict(case_id=mission.case_id,status='completed' if result is not None else 'partial',phase='final' if result is not None else history[-1]['phase'],
                 completion_scope='heliocentric_segment',duration_released=result is not None,last_result='final' if result is not None else None)
    if result is not None:
        result.save(output/'final');write_json(output/'resolved_request.json',make_request(Mission(**result.metadata['mission'])))
        from .visualization import render
        render(result,output/'plots')
        summary.update(tof_days=result.metadata['mission']['tof_days'],verification=result.metadata['verification'])
    else:summary['error']='No independently accepted free-duration result; see time_history.json'
    write_json(output/'summary.json',summary)
    return result,summary


def release_duration(source,previous,bounds_days,deadline):
    """Return only a verified physical solution; never relabel a failed seed."""
    context=deepcopy(source);mission=Mission(**source.metadata['mission'])
    if any(x is not None for x in (mission.capture,mission.parking_departure,mission.orbital_maneuvers,mission.lunar,mission.arrival_offset_state_si,mission.departure_offset_state_si)):
        raise ValueError('Body-to-body time release requires unresolved local maneuvers to be handled by their controller')
    bounds=np.asarray(bounds_days,dtype=float)
    if bounds.shape!=(2,) or not np.isfinite(bounds).all() or not 0<bounds[0]<=mission.tof_days<=bounds[1] or bounds[0]==bounds[1]:
        raise ValueError('Duration bounds must contain the initial guess')
    model=BoundedModel(**source.metadata['bounded_model'])
    if not model.variable_mass or model.alpha!=1 or model.beta!=1 or model.gravity is not None:
        raise ValueError('Duration release requires physical central-field PSI')
    scales=Scales(**source.metadata['scales']);eph=Ephemerides()
    body,_=origin_and_boundary(source,scales)
    old_t=previous.arrays['t_s']/scales.time_s;guess=canonical(previous,model)
    switches=np.asarray(previous.metadata['switch_times_s'])/scales.time_s
    intervals=np.diff(np.r_[0,switches,old_t[-1]])
    if np.any(intervals<=0):raise ValueError('Invalid reference switching topology')
    count=len(switches);first=float(previous.metadata['initial_throttle'])
    weights0=np.log(intervals[:-1]/intervals[-1])
    variable=mission.departure_mode!='fixed_vector' and (mission.vinf_max_m_s>0 or mission.departure_mode=='free')
    faces=['fixed'] if not variable else ['free','active'] if mission.departure_mode=='bounded_norm' else ['free' if mission.departure_mode=='free' else 'active']
    if mission.departure_mode=='bounded_norm' and previous.metadata.get('departure',{}).get('bound_active'):
        faces=['active','free']
    limit=departure_speed_limit(mission.to_dict())/scales.velocity_m_s
    errors=[]
    for face in faces:
        if face=='free':prefix=np.r_[guess[7:10,0],guess[13,0],guess[3:6,0]]
        else:prefix=np.r_[guess[7:14,0],guess[3:6,0]] if variable else guess[7:14,0]
        n=len(prefix);x0=np.r_[prefix,weights0,0.]
        cache={}
        def evaluate(x,dense=False):
            if perf_counter()>deadline:raise TimeoutError('Free-duration constrained optimization budget reached')
            if not dense and 'x' in cache and np.array_equal(cache['x'],x):return cache['value']
            duration=mission.tof_days*np.exp(x[-1]);resolved=replace(mission,tof_days=float(duration))
            target=scales.normalize_state(eph.state(mission.target,resolved.arrival_jd,mission.center))
            tf=duration*DAY_S/scales.time_s;edges=np.r_[0,np.cumsum(softmax(np.r_[x[n:n+count],0.]))*tf];edges[-1]=tf
            y=np.zeros(14);y[:3]=body[:3];y[6]=1.
            if face=='free':y[7:10]=x[:3];y[13]=x[3];y[3:6]=x[4:7]
            else:
                y[7:14]=x[:7]
                y[3:6]=x[7:10] if variable else guess[3:6,0]
            initial=y.copy();solutions=[];switch_values=[]
            for i,(left,right) in enumerate(zip(edges[:-1],edges[1:])):
                throttle=first if i%2==0 else 1-first
                def rhs(t,z):
                    if perf_counter()>deadline:raise TimeoutError('Free-duration integration budget reached')
                    return model.rhs(t,z,throttle=throttle)
                sol=solve_ivp(rhs,(left,right),y,method='DOP853',rtol=1e-12,atol=1e-14,dense_output=dense)
                if not sol.success:raise RuntimeError(sol.message)
                y=sol.y[:,-1];solutions.append(sol)
                if i<count:switch_values.append(float(model.switching(y,right)/model.a_max))
            endpoint=y[3:6]-target[3:] if mission.mode=='rendezvous' else y[10:13]
            eq=np.r_[y[:3]-target[:3],endpoint,y[13],switch_values]
            dv=initial[3:6]-body[3:]
            if face=='active':
                axis=np.eye(3)[np.argmin(abs(dv))];u=np.cross(dv,axis);u/=np.linalg.norm(u);v=np.cross(dv,u);v/=np.linalg.norm(v)
                eq=np.r_[eq,initial[10:13]@u,initial[10:13]@v,(np.linalg.norm(dv)-limit)]
            value=(float(1-y[6]),eq,initial,y,edges,solutions,resolved)
            if not dense:cache.update(x=x.copy(),value=value)
            return value
        def inequality(x):
            value=evaluate(x);initial=value[2];dv=initial[3:6]-body[3:]
            result=[value[3][6]-mission.spacecraft['dry_mass_kg']/mission.mass_kg]
            if face=='free' and mission.departure_mode=='bounded_norm':result.append(limit-np.linalg.norm(dv))
            if face=='active':result.append(float(initial[10:13]@dv))
            return np.array(result)
        try:
            opt=minimize(lambda x:evaluate(x)[0],x0,method='SLSQP',
                bounds=[(None,None)]*n+[(-20.,20.)]*count+[(np.log(bounds[0]/mission.tof_days),np.log(bounds[1]/mission.tof_days))],
                constraints=[dict(type='eq',fun=lambda x:evaluate(x)[1]),dict(type='ineq',fun=inequality)],
                options=dict(ftol=1e-11,maxiter=160,eps=1e-6))
            fuel,eq,initial,final,edges,solutions,resolved=evaluate(opt.x,True)
            if not opt.success:raise RuntimeError('Free-duration optimizer: '+opt.message)
            context.metadata.update(mission=resolved.to_dict(),target_state_si=eph.state(mission.target,resolved.arrival_jd,mission.center).tolist(),configuration_sha256=configuration_hash(resolved))
            epochs=np.linspace(resolved.launch_jd,resolved.arrival_jd,180)
            context.arrays['departure_orbit_m']=eph.state(resolved.departure,epochs,resolved.center)[:,:3]
            context.arrays['target_orbit_m']=eph.state(resolved.target,epochs,resolved.center)[:,:3]
            context.metadata['overlays']=[dict(array='departure_orbit_m',label='Орбита '+resolved.departure),dict(array='target_orbit_m',label='Орбита '+resolved.target)]
            context.metadata['markers']=[dict(label=resolved.departure+', старт',r_m=context.metadata['body_initial_state_si'][:3]),
                dict(label=resolved.target+', прибытие',r_m=context.metadata['target_state_si'][:3])]
            from .bangbang import _sampling_times
            times=_sampling_times(old_t*edges[-1]/old_t[-1],edges,scales.time_s)
            states=np.empty((14,len(times)));throttles=np.empty(len(times))
            for i,sol in enumerate(solutions):
                mask=(times>=edges[i])&(times<=edges[i+1]);states[:,mask]=sol.sol(times[mask]);throttles[mask]=first if i%2==0 else 1-first
            result=assemble(context,model,times,states,'free' if face=='free' else 'active','psi',
                extra=dict(switch_times_s=(edges[1:-1]*scales.time_s).tolist(),initial_throttle=first,
                           functional_dimensionless=float(model.a_max*np.dot(np.diff(edges),[first if i%2==0 else 1-first for i in range(len(edges)-1)])),
                           free_time=dict(method='constrained_shooting_SLSQP',seed_tof_days=mission.tof_days,resolved_tof_days=resolved.tof_days,
                                          bounds_days=bounds.tolist(),optimizer_success=True,iterations=int(opt.nit),objective='propellant',global_optimality=False)),
                throttle_override=throttles)
            check=verify_bounded(result,deadline)
            if not check['passed']:raise RuntimeError('Free-duration physical replay failed: '+str(check))
            audit_configuration(result,resolved,make_request(resolved),require_final=True)
            result.metadata.update(status='verified_extremal',verification=check)
            return result
        except (ValueError,RuntimeError) as exc:errors.append(face+': '+str(exc))
    raise RuntimeError('; '.join(errors))
