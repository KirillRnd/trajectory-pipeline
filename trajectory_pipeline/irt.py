"""Energy-optimal two-body transfers seeded by the local ILTT Toolbox.

Canonical dimensionless state [r,v,p_r,p_v], u=p_v. Returned SI arrays keep
canonical costates separately. A converged extremal is not a global optimum.
"""
from dataclasses import dataclass
from functools import lru_cache
import importlib.util
from pathlib import Path
from time import perf_counter
import warnings
import numpy as np
from scipy.integrate import solve_ivp, solve_bvp, simpson
from scipy.optimize import least_squares, minimize_scalar
from .data import Trajectory, DAY_S
from .ephemerides import Ephemerides
from .r_transform import costate_chart

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=2)
def _module(name, rel):
    # Load explicitly from this repository, never a neighboring project.
    import sys
    spec = importlib.util.spec_from_file_location(name, ROOT/rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def rhs(t, y, gravity=None):
    r, v, pr, pv = y[:3], y[3:6], y[6:9], y[9:12]
    radius = np.linalg.norm(r, axis=0)
    if gravity is not None:
        g,gradient=gravity.acceleration_gradient(t,r)
        return np.concatenate([v,g+pv,-np.einsum('ij...,j...->i...',gradient,pv),-pr],axis=0)
    return np.concatenate([v, -r/radius**3+pv,
                           pv/radius**3-3*r*np.sum(r*pv, axis=0)/radius**5, -pr], axis=0)


def iltt_seeds(r0, v0, rf, vf, tof):
    iltt = _module('_pipeline_iltt', 'ILTT/ILTTToolbox.py')
    energy = 2/np.linalg.norm(rf)-np.dot(vf, vf)
    kappa = 1/energy if energy > 0 else np.linalg.norm(rf)
    fit = minimize_scalar(lambda l: (2*np.pi*iltt.T_a(l,kappa)-tof)**2,
                          bounds=(.1, 3.), method='bounded')
    frame = iltt.calculate_R_matrix(r0, v0)
    lambdas = [float(fit.x), max(.1, float(fit.x)-.4), float(fit.x)+.4]
    for lam in lambdas:
        try:
            pr, pv = iltt.get_initial_adjoint(lam,kappa)
            pr, pv = iltt.apply_R(frame,pr,pv)
            p = np.r_[pr,pv].astype(float)
            if np.isfinite(p).all():
                yield dict(source='ILTT', lambda_turns=lam, kappa=float(kappa)),p
        except (ValueError, OverflowError, np.linalg.LinAlgError):
            continue


def _physical_errors(sol, target, scales, mode):
    dr = np.linalg.norm(sol.y[:3,-1]-target[:3])*scales.distance_m
    dv = np.linalg.norm(sol.y[3:6,-1]-target[3:])*scales.velocity_m_s
    pv = np.linalg.norm(sol.y[9:12,-1])
    return dict(position_residual_m=float(dr),velocity_residual_m_s=float(dv),
                free_velocity_transversality=float(pv))


def correct_shooting(initial, target, tof, guess, *, mode='rendezvous', max_nfev=70,
                     deadline=np.inf, costate_frame=None, coordinates="costates",
                     iltt_reference=None, dm_limit=.999*abs(np.sin(.642)), rtol=2e-12):
    if isinstance(coordinates,(list,tuple)):
        if not coordinates:raise ValueError('Empty coordinate schedule')
        current=np.asarray(guess).copy();history=[];reference=iltt_reference
        for coordinate in coordinates:
            current,diag=correct_shooting(initial,target,tof,current,mode=mode,max_nfev=max_nfev,
                deadline=deadline,costate_frame=costate_frame,coordinates=coordinate,
                iltt_reference=reference,dm_limit=dm_limit,rtol=rtol)
            history.append(diag)
            if 'iltt_parameters' in diag:reference=diag['iltt_parameters']
        return current,dict(coordinate_steps=history,nfev=sum(x['nfev'] for x in history),
                            integrations=sum(x['integrations'] for x in history),
                            optimizer_success=history[-1]['optimizer_success'],residual_norm=history[-1]['residual_norm'])
    if coordinates not in ('costates','iltt'):raise ValueError('Unknown IRT optimization coordinates')
    if coordinates=='iltt' and costate_frame is not None:raise ValueError('Choose ILTT coordinates or a linear costate frame, not both')
    cm = _module('_pipeline_continuation','ILTT/continuation_methods.py')
    problem = cm.BoundaryProblem(initial[:3],initial[3:],target[:3],target[3:],tof,mode=mode)
    def guard():
        if perf_counter() > deadline:
            raise TimeoutError('IRT integration time budget reached')
    cfg = cm.ContinuationConfig(rtol=rtol,atol=rtol/100,raise_on_internal_failure=True,integration_guard=guard)
    last_x = None
    last_eval = None
    calls = 0

    def evaluate(x):
        nonlocal last_x,last_eval,calls
        if perf_counter() > deadline:
            raise TimeoutError('IRT corrector time budget reached')
        if last_x is None or not np.array_equal(x,last_x):
            calls += 1
            last_eval = cm.evaluate_residual_and_jacobian_simple(problem,cm.z_from_pr_pv(x[:3],x[3:]),cfg)
            last_x = x.copy()
        return last_eval

    transform = np.block([[np.zeros((3,3)),np.eye(3)],[-np.eye(3),np.zeros((3,3))]])
    conversion={}
    if coordinates=='iltt':
        from .iltt_coordinates import ILTTCoordinates
        if iltt_reference is None:raise ValueError('ILTT mode needs an explicit local parameter reference')
        chart=ILTTCoordinates(initial,iltt_reference,dm_limit=dm_limit)
        z0,conversion=chart.from_costates(guess,deadline=deadline)
        decode=chart.to_costates;derivative=chart.jacobian;bounds=(chart.lower,chart.upper)
    else:
        chart=costate_chart(costate_frame)
        z0=np.linalg.solve(chart,guess);decode=lambda z:chart@z
        derivative=lambda z:chart;bounds=(-np.inf,np.inf)
    opt = least_squares(lambda z:evaluate(decode(z)).residual,z0,
                        jac=lambda z:evaluate(decode(z)).jacobian@transform@derivative(z),
                        bounds=bounds,xtol=1e-11,ftol=1e-11,gtol=1e-11,max_nfev=max_nfev,
                        method='trf',x_scale='jac')
    diag=dict(nfev=int(opt.nfev),integrations=calls,optimizer_success=bool(opt.success),
              residual_norm=float(np.linalg.norm(opt.fun)),coordinates=coordinates,conversion=conversion)
    if coordinates=='iltt':
        diag['iltt_parameters']=opt.x.tolist()
        diag['iltt_chart']=chart.record(opt.x)
    return decode(opt.x),diag



def collocation_seed(initial,target,tof,guess,mode,deadline):
    """A second numerical route for a real BVP when single shooting struggles."""
    t = np.linspace(0,tof,100)
    if perf_counter() > deadline:
        raise TimeoutError('IRT time budget reached')
    def vector_rhs(t,y):
        if perf_counter() > deadline:
            raise TimeoutError('IRT collocation time budget reached')
        return rhs(t,y)
    s = t/tof
    # Independent boundary-Hermite starting path, rather than repeating a
    # shooting seed that approaches the central singularity.
    y = np.zeros((12,len(t)))
    y[:3] = initial[:3,None]*(2*s**3-3*s*s+1)+initial[3:,None]*tof*(s**3-2*s*s+s)+target[:3,None]*(-2*s**3+3*s*s)+target[3:,None]*tof*(s**3-s*s)
    y[3:6] = initial[:3,None]*(6*s*s-6*s)/tof+initial[3:,None]*(3*s*s-4*s+1)+target[:3,None]*(-6*s*s+6*s)/tof+target[3:,None]*(3*s*s-2*s)
    acceleration = initial[:3,None]*(12*s-6)/tof**2+initial[3:,None]*(6*s-4)/tof+target[:3,None]*(-12*s+6)/tof**2+target[3:,None]*(6*s-2)/tof
    y[9:12] = acceleration+y[:3]/np.linalg.norm(y[:3],axis=0)**3
    y[6:9] = -np.gradient(y[9:12],t,axis=1,edge_order=2)
    def bc(a,b):
        return np.r_[a[:6]-initial,b[:3]-target[:3],b[3:6]-target[3:] if mode=='rendezvous' else b[9:12]]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        sol = solve_bvp(vector_rhs,bc,t,y,tol=2e-7,max_nodes=5000)
    if not sol.success:
        raise RuntimeError('Collocation: '+sol.message)
    return sol.y[6:12,0]


def solve_irt(mission, eph=None, *, costate_seed=None):
    eph = eph or mission.ephemerides()
    from .iltt_entry import resolve_date_mission,date_entry
    if costate_seed is None:mission=resolve_date_mission(mission,eph)
    initial_si,target_si,scales = mission.boundary(eph)
    initial,target = scales.normalize_state(initial_si),scales.normalize_state(target_si)
    tof = mission.tof_days*DAY_S/scales.time_s
    begin = perf_counter()
    deadline = begin+float(mission.solver.get('budget_s',90))
    history = []
    accepted = []
    collocation_attempted = False
    rtol=float(mission.solver.get('irt_integration_rtol',2e-12))
    if costate_seed is not None:
        seeds=[(dict(source='orbit-source boundary correction'),np.asarray(costate_seed,dtype=float))]
    elif date_entry(mission):
        entry=mission.solver['iltt_resolved']
        seeds=[(dict(source='ILTT date/phase',branch_rank=entry['branch_rank'],k=entry['k'],
                     lambda_turns=entry['lambda_corrected'],kappa=entry['kappa']),np.asarray(entry['costates']))]
    else:
        seeds = list(iltt_seeds(*[initial[:3],initial[3:],target[:3],target[3:],tof]))
    for info,seed in seeds:
        for route in ('shooting','collocation'):
            if (date_entry(mission) or costate_seed is not None) and route=='collocation':continue  # Never silently replace the ILTT branch.
            if route=='collocation' and collocation_attempted:
                continue
            if route=='collocation':
                collocation_attempted=True
            attempt = dict(**info,route=route)
            if route=='collocation':
                attempt['source']='boundary Hermite collocation'
            started = perf_counter()
            attempt_deadline=min(deadline,started+float(mission.solver.get('attempt_budget_s',12)))
            try:
                guess = seed if route=='shooting' else collocation_seed(initial,target,tof,seed,mission.mode,attempt_deadline)
                costates,diag = correct_shooting(initial,target,tof,guess,mode=mission.mode,
                                                 max_nfev=int(mission.solver.get('max_nfev',70)),deadline=attempt_deadline,
                                                 coordinates=mission.solver.get('irt_coordinates','costates'),
                                                 iltt_reference=mission.solver.get('iltt_coordinate_reference',mission.solver.get('iltt_resolved',{}).get('x_corrected')),
                                                 dm_limit=mission.solver.get('iltt_dm_limit',.999*abs(np.sin(.642))),rtol=rtol)
                attempt['last_costates']=costates.tolist()
                sol = solve_ivp(rhs,(0,tof),np.r_[initial,costates],method='DOP853',
                                rtol=rtol,atol=rtol/100,t_eval=np.linspace(0,tof,801))
                if not sol.success or abs(sol.t[-1]-tof)>1e-12:
                    raise RuntimeError('Final integration did not reach arrival')
                errors = _physical_errors(sol,target,scales,mission.mode)
                ok = errors['position_residual_m']<=mission.position_tolerance_m
                ok &= errors['velocity_residual_m_s']<=mission.velocity_tolerance_m_s if mission.mode=='rendezvous' else errors['free_velocity_transversality']<1e-8
                if ok:
                    from .verification import replay_irt
                    independent = replay_irt(initial,costates,sol.t,rtol=1.5*rtol)
                    if not independent.success or independent.y.shape!=sol.y.shape:
                        ok=False
                        attempt['independent_failure']='Independent integration did not reach arrival'
                    else:
                        independent_errors=_physical_errors(independent,target,scales,mission.mode)
                        difference_r=float(np.linalg.norm(independent.y[:3]-sol.y[:3],axis=0).max()*scales.distance_m)
                        difference_v=float(np.linalg.norm(independent.y[3:6]-sol.y[3:6],axis=0).max()*scales.velocity_m_s)
                        attempt['independent_check']=dict(**independent_errors,difference_r_m=difference_r,difference_v_m_s=difference_v)
                        ok=independent_errors['position_residual_m']<=mission.position_tolerance_m
                        ok &= independent_errors['velocity_residual_m_s']<=mission.velocity_tolerance_m_s if mission.mode=='rendezvous' else independent_errors['free_velocity_transversality']<1e-8
                        ok &= difference_r<=mission.position_tolerance_m and difference_v<=mission.velocity_tolerance_m_s
                attempt.update(**diag,**errors,accepted=bool(ok))
                if ok:
                    J = simpson(.5*np.sum(sol.y[9:12]**2,axis=0),x=sol.t)
                    accepted.append((float(J),sol,costates,dict(attempt)))
            except (RuntimeError,ValueError,OverflowError,TimeoutError,np.linalg.LinAlgError) as exc:
                attempt.update(accepted=False,message=str(exc))
            attempt['elapsed_s'] = perf_counter()-started
            history.append(attempt)
            if attempt.get('accepted') or perf_counter()>deadline:
                break
        if accepted and not mission.solver.get('compare_seeds',True):
            break
        if perf_counter()>deadline:
            break
    if not accepted:
        return None,dict(status='initial_failed',attempts=history,elapsed_s=perf_counter()-begin)
    J,sol,costates,chosen = min(accepted,key=lambda row:row[0])
    rv_si = scales.dimensional_state(sol.y[:6].T)
    acceleration = sol.y[9:12].T*scales.acceleration_m_s2
    # IRT has no mass-flow law: do not invent fuel consumption or mass history.
    epochs = mission.launch_jd+sol.t*scales.time_s/DAY_S
    overlays = dict(departure_orbit_m=eph.state(mission.departure,epochs,mission.center)[:,:3],
                    target_orbit_m=eph.state(mission.target,epochs,mission.center)[:,:3])
    metadata = dict(case_id=mission.case_id,epoch_jd=mission.launch_jd,time_scale='TDB',
                    center=mission.center,frame='ECLIPJ2000',model='IRT two-body minimum integral acceleration squared / 2',
                    status='solved_extremal',stage='irt',mission=mission.to_dict(),
                    scales=dict(distance_m=scales.distance_m,mu_m3_s2=scales.mu_m3_s2),
                    initial_state_si=initial_si.tolist(),target_state_si=target_si.tolist(),
                    costate_convention='dimensionless [p_r,p_v], H=p_r*v+p_v*(g+u)-|u|^2/2, u=p_v',
                    costates_initial=costates.tolist(),functional_dimensionless=J,chosen_seed=chosen,
                    title=f'{mission.departure} → {mission.target}: ИРТ',
                    ephemerides={name:eph.coverage(name) for name in (mission.departure,mission.target)},
                    overlays=[dict(array='departure_orbit_m',label=f'Орбита {mission.departure}'),
                              dict(array='target_orbit_m',label=f'Орбита {mission.target}',linestyle='-.',color='.65')],
                    markers=[dict(label=f'{mission.departure}, старт',r_m=initial_si[:3].tolist()),
                             dict(label=f'{mission.departure}, прибытие',r_m=overlays['departure_orbit_m'][-1].tolist(),hollow=True),
                             dict(label=mission.target,r_m=target_si[:3].tolist(),color='#df1111',role='target')])
    if mission.lunar is not None:
        from .lunar import lunar_presentation
        overlays,presentation=lunar_presentation(mission,eph,initial_si,target_si)
        metadata.update(presentation)
    trajectory = Trajectory(metadata,dict(t_s=sol.t*scales.time_s,r_m=rv_si[:,:3],v_m_s=rv_si[:,3:],
                                         acceleration_m_s2=acceleration,costates=sol.y[6:12].T,
                                         active=np.ones(len(sol.t),dtype=bool),**overlays)).validate()
    return trajectory,dict(status='solved_extremal',attempts=history,elapsed_s=perf_counter()-begin)
