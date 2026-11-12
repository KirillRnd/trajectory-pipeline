"""Duration optimization on verified homotopy models, then physical continuation.

The outer bounded scalar optimizer varies flight time; existing boundary-value
correctors eliminate costates at each trial. The objective is the CURRENT model's
mixed functional, not physical fuel. A feasible best trial may survive exhaustion
of the optimization budget; it is explicitly not an optimality certificate.
"""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from time import perf_counter
import numpy as np
from scipy.optimize import minimize_scalar
from .data import Scales, DAY_S, write_json
from .problem import Mission
from .contract import audit_configuration, configuration_hash, make_request, specification
from .bounded import collocate, verify_bounded, canonical, assemble
from .bounded_model import BoundedModel
from .verification import verify_irt
from .ephemerides import Ephemerides
from .continuation import continue_parameter


def verify_intermediate(source):
    if source.metadata.get('status')!='verified_extremal':
        raise ValueError('Intermediate release requires an independently verified source')
    audit_configuration(source)
    mission=Mission(**source.metadata['mission'])
    if mission.center.lower()!='sun' or any(getattr(mission,k) is not None for k in
        ('time_policy','capture','parking_departure','orbital_maneuvers','lunar','arrival_offset_state_si','departure_offset_state_si')):
        raise ValueError('Intermediate release supports central body-to-body missions only')
    if source.metadata.get('gravity_spec') is not None:raise ValueError('Central model required')
    if 'bounded_model' in source.metadata:
        model=BoundedModel(**source.metadata['bounded_model'])
        if model.gravity is not None or model.alpha>=1:raise ValueError('Smooth intermediate alpha < 1 required')
        check=verify_bounded(source)
    else:
        if source.metadata.get('stage') not in ('irt','departure'):raise ValueError('Unsupported intermediate stage')
        check=verify_irt(source)
    if not check['passed']:raise ValueError('Intermediate source failed independent replay')
    return check


def time_context(source,duration,eph):
    """New endpoint and time mesh; old arrays are only a corrector guess."""
    context=deepcopy(source);old=Mission(**source.metadata['mission'])
    mission=replace(old,tof_days=float(duration))
    context.arrays['t_s']=source.arrays['t_s']*(duration/old.tof_days)
    context.metadata.update(mission=mission.to_dict(),configuration_sha256=configuration_hash(mission),
                            target_state_si=eph.state(mission.target,mission.arrival_jd,mission.center).tolist())
    for k in ('arrays_sha256','verification','free_time','switch_times_s','initial_throttle'):
        context.metadata.pop(k,None)
    epochs=np.linspace(mission.launch_jd,mission.arrival_jd,180)
    context.arrays['departure_orbit_m']=eph.state(mission.departure,epochs,mission.center)[:,:3]
    context.arrays['target_orbit_m']=eph.state(mission.target,epochs,mission.center)[:,:3]
    context.metadata['markers']=[dict(label=mission.departure+', старт',r_m=context.metadata.get('body_initial_state_si',context.metadata['initial_state_si'])[:3]),
                                 dict(label=mission.target+', прибытие',r_m=context.metadata['target_state_si'][:3])]
    return context


def correct_departure(context,previous,parameter,deadline):
    from .departure import _correct
    context=deepcopy(context);m=context.metadata;mission=m['mission']
    body=np.asarray(m.get('body_initial_state_si',m['initial_state_si']),dtype=float).copy()
    if 'body_initial_state_si' not in m and m.get('departure'):
        body[3:]-=m['departure']['vector_m_s']
    m['initial_state_si']=body.tolist();m['body_initial_state_si']=body.tolist()
    # Try the source face first, but never accept a free excess outside the ball.
    mode=mission['departure_mode'];free_first=mode=='free' or not previous.metadata.get('departure',{}).get('bound_active',True)
    faces=[True] if mode=='free' else [free_first,not free_first] if mode=='bounded_norm' else [False]
    errors=[]
    for free in faces:
        try:
            result=_correct(context,parameter,previous,deadline,free=free)
            if free and mode=='bounded_norm':
                if result.metadata['departure']['norm_m_s']>parameter*mission['vinf_max_m_s']+mission['velocity_tolerance_m_s']:
                    raise ValueError('Free intermediate excess exceeds its current homotopy bound')
                result.metadata['departure'].update(requested_mode=mode,bound_active=False,bound_m_s=parameter*mission['vinf_max_m_s'])
            return result
        except (ValueError,RuntimeError,TimeoutError) as exc:errors.append(str(exc))
    raise RuntimeError('; '.join(errors))


def release_intermediate_duration(source,bounds_days,deadline,output):
    verify_intermediate(source)
    root=Path(output);root.mkdir(parents=True,exist_ok=False)
    mission=Mission(**source.metadata['mission']);lo,hi=map(float,bounds_days)
    if not np.isfinite([lo,hi]).all() or not 0<lo<=mission.tof_days<=hi or lo==hi:
        raise ValueError('Intermediate duration bounds must contain source duration')
    eph=mission.ephemerides();requested_bounds=[lo,hi]
    model=BoundedModel(**source.metadata['bounded_model']) if 'bounded_model' in source.metadata else None
    candidates=[source];history=[];scale=max(abs(source.metadata['functional_dimensionless']),1e-12)
    attempt=float(mission.solver.get('bounded_attempt_s',20))
    def evaluate(duration):
        if perf_counter()>=deadline:raise TimeoutError('Intermediate duration budget reached')
        duration=float(duration)
        nearest=min(candidates,key=lambda x:abs(x.metadata['mission']['tof_days']-duration))
        context=time_context(nearest,duration,eph);event=dict(tof_days=duration)
        try:
            if model is not None:
                candidate=collocate(context,context,model,min(deadline,perf_counter()+attempt),source.metadata['stage'])
            else:
                parameter=float(source.metadata.get('departure',{}).get('parameter',0.))
                candidate=correct_departure(context,context,parameter,min(deadline,perf_counter()+attempt))
            expected=replace(mission,tof_days=duration)
            audit_configuration(candidate,expected,make_request(expected))
            if model is not None and candidate.metadata['bounded_model']!=source.metadata['bounded_model']:
                raise ValueError('Duration correction changed the intermediate model')
            objective=float(candidate.metadata['functional_dimensionless'])
            candidate.save(root/f'candidate_{len(history):03d}')
            candidates.append(candidate);event.update(accepted=True,objective=objective,artifact=str(root/f'candidate_{len(history):03d}'))
            value=objective/scale
        except (ValueError,RuntimeError,TimeoutError) as exc:
            event.update(accepted=False,error=type(exc).__name__+': '+str(exc));value=1e6+abs(duration/mission.tof_days-1)
        history.append(event);write_json(root/'trials.json',history)
        return value
    optimized=False;reason=None
    try:
        # Explicit endpoints permit a constrained optimum at either duration bound.
        evaluate(hi);evaluate(lo)
        opt=minimize_scalar(evaluate,bounds=(lo,hi),method='bounded',options=dict(xatol=.05,maxiter=24))
        optimized=bool(opt.success);reason=str(opt.message)
    except TimeoutError as exc:reason=str(exc)
    changed=[x for x in candidates[1:] if abs(x.metadata['mission']['tof_days']-mission.tof_days)>1e-6]
    if not changed:raise RuntimeError('No independently verified changed-duration intermediate; see trials.json')
    best=min(changed,key=lambda x:x.metadata['functional_dimensionless'])
    # A feasible time change is useful for continuation even if it did not minimize J.
    best.metadata['intermediate_time']=dict(method='bounded_scalar_with_BVP_correction',seed_tof_days=mission.tof_days,
        resolved_tof_days=best.metadata['mission']['tof_days'],bounds_days=[lo,hi],requested_bounds_days=requested_bounds,objective='current_model_functional',
        seed_objective=source.metadata['functional_dimensionless'],objective_value=best.metadata['functional_dimensionless'],
        optimizer_success=optimized,stop_reason=reason,trials=len(history),physical_solution=False,global_optimality=False)
    verify_intermediate(best)
    return best


def continue_physical_model(source,output):
    """Continue the actual saved alpha/beta/thrust; do not restart mass at zero."""
    verify_intermediate(source)
    root=Path(output);root.mkdir(parents=True,exist_ok=False)
    current=source;settings=source.metadata['mission']['solver'];attempt=float(settings.get('bounded_attempt_s',20))
    def run_phase(name,make,stage):
        nonlocal current
        initial=current
        def correct(s,previous,deadline):
            model=make(s)
            if model.alpha==1:
                from .bangbang import solve_bangbang
                return solve_bangbang(initial,previous,model,min(deadline,perf_counter()+attempt),'psi')
            return collocate(initial,previous,model,min(deadline,perf_counter()+attempt),stage)
        current,state=continue_parameter(initial,root/name,correct,
            profile=dict(stage=name,mission=current.metadata['mission'],start_model=current.metadata.get('bounded_model'),
                         budget_s=settings.get('psi_budget_s',60),min_step=1e-4,max_step=.2))
        summary=dict(status='completed_stage' if state['status']=='completed_stage' else 'partial',phase=name,
                     reached_parameter=state['reached_parameter'],last_result=name+'/'+state['last_point'])
        write_json(root/'summary.json',summary)
        return state['status']=='completed_stage',summary
    if 'bounded_model' not in current.metadata:
        start=float(current.metadata.get('departure',{}).get('parameter',0.))
        context=deepcopy(current)
        if start<1:
            def correct(s,previous,deadline):return correct_departure(context,previous,start+(1-start)*s,deadline)
            current,state=continue_parameter(current,root/'departure',correct,
                profile=dict(stage='departure_remaining',start_parameter=start,mission=current.metadata['mission'],
                             budget_s=settings.get('departure_budget_s',40),min_step=.001,max_step=.25))
            if state['status']!='completed_stage':return current,dict(status='partial',phase='departure',last_result='departure/'+state['last_point'])
        from .pazov import run_pazov
        current,summary=run_pazov(current,root/'pazov',target_alpha=settings.get('pipeline_pazov_alpha',.5))
        # As in the standard route, retain the verified higher-thrust bridge.
    scales=Scales(**current.metadata['scales']);mission=current.metadata['mission']
    hardware=mission['spacecraft'];actual=hardware['thrust_N']/mission['mass_kg']/scales.acceleration_m_s2
    model=BoundedModel(**current.metadata['bounded_model']);alpha=model.alpha;force=model.a_max
    if force<actual*(1-1e-9):raise ValueError('Checkpoint force is below requested physical thrust')
    q=force*scales.velocity_m_s/hardware['exhaust_velocity_m_s']
    if not model.variable_mass:
        model=BoundedModel(force,alpha=alpha,beta=0,q=q,variable_mass=True)
        current=assemble(current,model,current.arrays['t_s']/scales.time_s,canonical(current,model),
                         'active' if current.metadata['departure']['bound_active'] else 'free','psi_mass')
        check=verify_bounded(current)
        if not check['passed']:raise ValueError('Mass-zero checkpoint conversion failed')
        current.metadata.update(status='verified_extremal',verification=check)
    start_beta=model.beta
    if start_beta<1 or force>actual*(1+1e-9):
        # Reach beta=1 only together with the requested force. Completing mass
        # first at an artificial high force can violate the fuel reserve before
        # the trajectory ever reaches the specified spacecraft model.
        def coupled(s):
            a=force+(actual-force)*s
            return BoundedModel(a,alpha=alpha,beta=start_beta+(1-start_beta)*s,
                                q=a*scales.velocity_m_s/hardware['exhaust_velocity_m_s'],variable_mass=True)
        ok,summary=run_phase('mass_and_thrust',coupled,'psi_limit')
        if not ok:return current,summary
    ok,summary=run_phase('fuel',lambda s:BoundedModel(actual,alpha=alpha+(1-alpha)*s,beta=1,
                        q=actual*scales.velocity_m_s/hardware['exhaust_velocity_m_s'],variable_mass=True),'psi')
    if ok:
        audit_configuration(current,require_final=True)
        summary.update(status='completed',phase='final')
    write_json(root/'summary.json',summary)
    return current,summary
