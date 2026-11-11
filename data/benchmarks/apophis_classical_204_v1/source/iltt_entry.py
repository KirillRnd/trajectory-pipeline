"""Date-first ILTT entry, adapted from ILTT/transfer_legacy.py.

The phase chooses angular-distance branches BEFORE flight time is evaluated.
Ephemerides and dimensional time use the pipeline's scales, not the legacy
toolbox's hard-coded AU-to-days conversion. No inverse duration fit is used.
"""
from dataclasses import replace
from time import perf_counter
import numpy as np
from scipy.optimize import root,least_squares
from .data import Scales, MU_SUN, DAY_S
from .ephemerides import Ephemerides


def date_entry(mission):
    mode=mission.solver.get('irt_entry','date')
    if mode not in ('date','fixed_time'):raise ValueError('irt_entry must be date or fixed_time')
    return mode=='date' and mission.center.lower()=='sun' and not any(getattr(mission,k) is not None for k in
        ('lunar','departure_offset_state_si','arrival_offset_state_si','orbital_maneuvers','parking_departure','capture'))


def angular_branches(mission,eph=None):
    from .irt import _module
    tb=_module('_pipeline_iltt','ILTT/ILTTToolbox.py');eph=eph or Ephemerides()
    initial=eph.state(mission.departure,mission.launch_jd,mission.center)
    scale=Scales(float(np.linalg.norm(initial[:3])),MU_SUN)
    initial=scale.normalize_state(initial)
    target=scale.normalize_state(eph.state(mission.target,mission.launch_jd,mission.center))
    def elements(rv):return np.array([float(x[0]) for x in tb.rv2orb(rv[:3,None],rv[3:,None],1)])
    start_el,end_el=elements(initial),elements(target)
    phase=float(np.arctan2(np.sin(end_el[6]-start_el[6]),np.cos(end_el[6]-start_el[6])))
    kappa=float(end_el[0]);branches=[]
    if kappa<=0 or abs(np.log(kappa))<1e-8:raise ValueError('ILTT phase formula is singular for this semimajor-axis ratio')
    for k in tb.k_order(int(mission.solver.get('iltt_max_abs_k',5))):
        lam=float(tb.a_OM(phase/(2*np.pi),kappa,k))
        if np.isfinite(lam) and lam>0:
            branches.append(dict(k=int(k),lambda_initial=lam,
                                 approximation_family='short' if lam<.75 else 'long'))
    branches.sort(key=lambda x:x['lambda_initial'])
    return tb,eph,scale,initial,end_el,phase,branches


def resolve_date_mission(mission,eph=None):
    if not date_entry(mission):return mission
    binding={k:getattr(mission,k) for k in ('departure','target','launch_tdb','center')}
    binding.update(max_abs_k=mission.solver.get('iltt_max_abs_k',5),duration_bounds_days=mission.solver.get('iltt_duration_bounds_days'),angular_min=0.)
    if type(binding['max_abs_k']) is not int or binding['max_abs_k']<1:raise ValueError('iltt_max_abs_k must be a positive integer')
    bounds=binding['duration_bounds_days']
    if bounds is not None and (not isinstance(bounds,list) or len(bounds)!=2 or not np.isfinite(bounds).all() or not 0<bounds[0]<bounds[1]):
        raise ValueError('Invalid ILTT duration filter')
    rank=mission.solver.get('iltt_branch',0)
    if type(rank) is not int or rank<0:raise ValueError('iltt_branch must be a nonnegative branch rank')
    saved=mission.solver.get('iltt_resolved')
    if saved and saved['binding']==binding and saved['branch_rank']==rank and saved['tof_days']==mission.tof_days:
        return mission
    tb,eph,scale,initial,el,phase,branches=angular_branches(mission,eph)
    if rank>=len(branches):raise ValueError('Requested angular-distance branch does not exist')
    chosen=branches[rank];lam=chosen['lambda_initial'];kappa=float(el[0])
    F,x0=tb.make_F_function(initial[:3][None,:],initial[3:][None,:],lam,kappa,0,1,float(el[2]),float(el[3]),float(el[1]),float(el[8]))
    deadline=perf_counter()+float(mission.solver.get('iltt_budget_s',30))
    calls=0
    def evaluate(x):
        nonlocal calls
        if perf_counter()>deadline:raise TimeoutError('ILTT date/phase correction budget reached')
        calls+=1
        duration=float(2*np.pi*tb.T_a(float(x[5]),float(x[4]))*scale.time_s/DAY_S)
        if not np.isfinite(duration) or duration<=0:raise ValueError('Invalid ILTT-derived duration')
        target=scale.normalize_state(eph.state(mission.target,mission.launch_jd+duration,mission.center))
        result=F(x)
        desired=np.array([float(a[0]) for a in tb.rv2orb(target[:3,None],target[3:,None],1)])
        actual=np.array([float(a[0]) for a in tb.rv2orb(result['rf'][:,None],result['vf'][:,None],1)])
        residual=np.r_[desired[[0,2,1]]-actual[[0,2,1]],tb.ang_err(desired[[3,8,6]],actual[[3,8,6]])]
        return residual,result,duration
    lower=0. if rank==0 else .5*(branches[rank-1]['lambda_initial']+lam)
    upper=np.inf if rank+1==len(branches) else .5*(lam+branches[rank+1]['lambda_initial'])
    # The toolbox clips dm internally. Starting outside that interval makes
    # its entire Jacobian column exactly zero, so unconstrained Newton cannot
    # recover. Keep the existing R model, but correct inside its active domain.
    dm_limit=.999*abs(np.sin(.642))
    saturated=bool(abs(x0[0])>=dm_limit)
    attempts=[];opt=None;residual=np.full(6,np.inf)
    if not saturated:
        try:
            opt=root(lambda x:evaluate(x)[0],x0,method='hybr',options={'xtol':1e-9,'maxfev':200})
            residual,result,duration=evaluate(opt.x)
            attempts.append(dict(route='hybr',residual_norm=float(np.linalg.norm(residual)),message=str(opt.message)))
        except (ValueError,OverflowError,np.linalg.LinAlgError) as exc:
            attempts.append(dict(route='hybr',error=str(exc)))
    if not np.isfinite(residual).all() or np.linalg.norm(residual)>1e-7:
        # A declared finite trust domain also prevents a failed local step
        # from sending the transformed inclination or orbit size to infinity.
        lo=np.array([-dm_limit,-30,-np.inf,-np.inf,.1,lower])
        hi=np.array([dm_limit,30,np.inf,np.inf,10,upper])
        seed=np.maximum(lo+1e-7,np.minimum(hi-1e-7,x0))
        opt=least_squares(lambda x:evaluate(x)[0],seed,bounds=(lo,hi),
                          method='trf',x_scale='jac',diff_step=1e-5,
                          ftol=1e-11,xtol=1e-11,gtol=1e-11,max_nfev=200)
        residual,result,duration=evaluate(opt.x)
        attempts.append(dict(route='bounded_R',residual_norm=float(np.linalg.norm(residual)),message=str(opt.message),
                             trust_domain=dict(dm=[-dm_limit,dm_limit],j=[-30,30],kappa=[.1,10],lambda_turns=[lower,float(upper) if np.isfinite(upper) else None])))
    if not np.isfinite(residual).all() or np.linalg.norm(residual)>1e-7:
        raise ValueError('ILTT phase/orbit correction failed: '+str(opt.message)+'; residual='+str(residual)+'; x='+str(opt.x)+'; x0='+str(x0))
    if not lower<float(opt.x[5])<upper:raise ValueError('ILTT correction left its angular-distance branch')
    bounds=mission.solver.get('iltt_duration_bounds_days')
    if bounds is not None and not bounds[0]<=duration<=bounds[1]:
        raise ValueError(f'ILTT-derived duration {duration:.6f} days outside declared filter {bounds}')
    dm,j,node,peri,kappa,lam=map(float,opt.x)
    start=tb.rv2orb(initial[:3,None],initial[3:,None],1)[6][0]
    R=tb.calculate_RiO_matrix_noapprox(j,node-start)@tb.calculate_Reo_matrix_noapprox(dm,peri-start)@tb.calculate_R_matrix(initial[:3][None,:],initial[3:][None,:])
    pr,pv=tb.apply_R(R,*tb.get_initial_adjoint(lam,kappa,1))
    record=dict(binding=binding,branch_rank=rank,branches=branches,phase_rad=phase,k=chosen['k'],
                lambda_initial=chosen['lambda_initial'],lambda_corrected=lam,kappa=kappa,
                x_initial=np.asarray(x0).tolist(),x_corrected=opt.x.tolist(),
                tof_days=duration,initial_tof_days=float(2*np.pi*tb.T_a(chosen['lambda_initial'],float(el[0]))*scale.time_s/DAY_S),
                costates=np.r_[pr,pv].tolist(),orbit_phase_residual=residual.tolist(),evaluations=calls,
                initial_transform_saturated=saturated,correction_attempts=attempts,
                source='ILTT/transfer_legacy.py: phase -> a_OM branches -> make_F_function -> moving-target orbit correction',
                duration_role='derived from ILTT; input tof_days was not used')
    return replace(mission,tof_days=duration,solver=dict(mission.solver,iltt_resolved=record))
