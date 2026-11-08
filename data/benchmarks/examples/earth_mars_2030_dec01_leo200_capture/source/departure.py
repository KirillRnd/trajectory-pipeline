"""Continuation of an IRT extremal in the departure excess constraint."""
from copy import deepcopy
from time import perf_counter
import numpy as np
from scipy.integrate import solve_bvp,simpson,solve_ivp
from scipy.optimize import least_squares
from .continuation import continue_parameter
from .data import Scales,Trajectory
from .irt import rhs,_module
from .verification import verify_irt


def _free_shooting(body_state,target,times,guess,mode,deadline,gravity=None):
    """Free v0: p_v0=0 exactly; shoot in [v0,p_r0] with variational derivatives."""
    if gravity is not None:
        def propagate(x,full=False):
            initial=np.r_[body_state[:3],x[:3],x[3:6],np.zeros(3)]
            def ode(t,y):
                if perf_counter()>deadline:raise TimeoutError('Perturbed free-departure shooting budget reached')
                return rhs(t,y,gravity)
            sol=solve_ivp(ode,(0,times[-1]),initial,t_eval=times if full else None,
                           method='DOP853',rtol=2e-12,atol=2e-14)
            if not sol.success:raise RuntimeError(sol.message)
            return sol
        def residual(x):
            y=propagate(x).y[:,-1]
            return np.r_[y[:3]-target[:3],y[3:6]-target[3:] if mode=='rendezvous' else y[9:12]]
        opt=least_squares(residual,np.r_[guess[3:6,0],guess[6:9,0]],diff_step=1e-5,
                          x_scale='jac',max_nfev=70,xtol=1e-11,ftol=1e-11,gtol=1e-11)
        return propagate(opt.x,full=True).y
    cm=_module('_pipeline_continuation','ILTT/continuation_methods.py')
    last_x=None
    last=None
    def augmented_rhs(t,y):
        if perf_counter()>deadline:
            raise TimeoutError('Free-departure shooting budget reached')
        return cm._rhs_augmented_simple(t,y,1.)
    def evaluate(x):
        nonlocal last_x,last
        if last_x is None or not np.array_equal(x,last_x):
            y=np.zeros(84)
            y[:3]=body_state[:3]
            y[3:6]=x[:3]
            y[9:12]=-x[3:6]
            dvdx=np.zeros((3,6));dvdx[:,:3]=np.eye(3)
            dpvdotdx=np.zeros((3,6));dpvdotdx[:,3:]=-np.eye(3)
            y[30:48]=dvdx.ravel();y[66:84]=dpvdotdx.ravel()
            sol=solve_ivp(augmented_rhs,(0,times[-1]),y,rtol=2e-12,atol=2e-14,method='DOP853')
            if not sol.success:
                raise RuntimeError(sol.message)
            y=sol.y[:,-1]
            residual=np.r_[y[:3]-target[:3],y[3:6]-target[3:] if mode=='rendezvous' else y[6:9]]
            jac=np.vstack([y[12:30].reshape(3,6),y[30:48].reshape(3,6) if mode=='rendezvous' else y[48:66].reshape(3,6)])
            last=(residual,jac);last_x=x.copy()
        return last
    opt=least_squares(lambda x:evaluate(x)[0],np.r_[guess[3:6,0],guess[6:9,0]],
                       jac=lambda x:evaluate(x)[1],x_scale='jac',max_nfev=70,
                       xtol=1e-11,ftol=1e-11,gtol=1e-11)
    sol=solve_ivp(rhs,(0,times[-1]),np.r_[body_state[:3],opt.x[:3],opt.x[3:6],np.zeros(3)],
                   t_eval=times,method='DOP853',rtol=2e-12,atol=2e-14)
    if not sol.success or sol.y.shape[1]!=len(times):
        raise RuntimeError('Free-departure final integration failed')
    return sol.y


def _correct(source,parameter,previous,deadline,free=False):
    meta=source.metadata
    mission=meta['mission']
    scales=Scales(**meta['scales'])
    body_state=scales.normalize_state(meta['initial_state_si'])
    target=scales.normalize_state(meta['target_state_si'])
    mode='free' if free else mission['departure_mode']
    bound=parameter*mission['vinf_max_m_s']/scales.velocity_m_s
    vector=np.asarray(mission.get('vinf_vector_m_s') or [0.,0.,0.])/scales.velocity_m_s
    times=previous.arrays['t_s']/scales.time_s
    guess=np.vstack([scales.normalize_state(np.c_[previous.arrays['r_m'],previous.arrays['v_m_s']]).T,
                     previous.arrays['costates'].T])
    if meta.get('gravity_spec') is not None:
        from .gravity import Gravity
        gravity=Gravity(meta['gravity_spec'])
    else:gravity=None
    collocation_deadline=min(deadline,perf_counter()+3.) if mode=='free' else deadline
    def ode(t,y):
        if perf_counter()>collocation_deadline:
            raise TimeoutError('Departure continuation budget reached')
        return rhs(t,y,gravity)
    def bc(a,b):
        if mode=='free':
            initial=a[9:12]
        elif mode=='fixed_vector':
            initial=a[3:6]-body_state[3:]-parameter*vector
        elif bound==0:
            initial=a[3:6]-body_state[3:]
        else:
            pv=a[9:12]
            initial=a[3:6]-body_state[3:]-bound*pv/max(np.linalg.norm(pv),1e-15)
        final=b[3:6]-target[3:] if mission['mode']=='rendezvous' else b[9:12]
        return np.r_[a[:3]-body_state[:3],initial,b[:3]-target[:3],final]
    if mode=='free':
        try:
            sol=solve_bvp(ode,bc,times,guess,tol=2e-9,max_nodes=12000)
            if not sol.success:
                raise RuntimeError(sol.message)
            y=sol.sol(times)
        except (RuntimeError,TimeoutError):
            y=_free_shooting(body_state,target,times,guess,mission['mode'],deadline,gravity)
    else:
        sol=solve_bvp(ode,bc,times,guess,tol=2e-9,max_nodes=12000)
        if not sol.success:
            raise RuntimeError(sol.message)
        y=sol.sol(times)
    rv=scales.dimensional_state(y[:6].T)
    m=deepcopy(meta)
    a={k:v.copy() for k,v in previous.arrays.items()}
    a.update(r_m=rv[:,:3],v_m_s=rv[:,3:],costates=y[6:12].T,
             acceleration_m_s2=y[9:12].T*scales.acceleration_m_s2)
    m.update(stage='departure',status='solved_extremal',initial_state_si=rv[0].tolist(),
             costates_initial=y[6:12,0].tolist(),
             functional_dimensionless=float(simpson(.5*np.sum(y[9:12]**2,axis=0),x=times)))
    dv=rv[0,3:]-np.asarray(meta['initial_state_si'])[3:]
    info=dict(parameter=parameter,mode=mode,bound_m_s=parameter*mission['vinf_max_m_s'],
              vector_m_s=dv.tolist(),norm_m_s=float(np.linalg.norm(dv)),
              bound_active=mode in ('fixed_norm','bounded_norm'),
              pv0_norm=float(np.linalg.norm(y[9:12,0])))
    m['departure']=info
    result=Trajectory(m,a).validate()
    check=verify_irt(result)
    if not check['passed']:
        raise RuntimeError('Independent departure replay failed: '+str(check))
    if mode=='free':
        if info['pv0_norm']>1e-8:
            raise RuntimeError('Free departure transversality failed')
    elif mode in ('fixed_norm','bounded_norm'):
        error=abs(info['norm_m_s']-info['bound_m_s'])
        cross=np.linalg.norm(np.cross(y[9:12,0],dv/scales.velocity_m_s))
        info.update(norm_error_m_s=float(error),transversality_cross_norm=float(cross))
        if error>mission['velocity_tolerance_m_s'] or cross>1e-8:
            raise RuntimeError('Departure norm or direction condition failed')
    result.metadata.update(status='verified_extremal',verification=check)
    return result


def run_departure(source,output,resume=False):
    from .contract import audit_configuration
    audit_configuration(source)
    if source.metadata.get('stage')!='irt' or source.metadata['status']!='verified_extremal':
        raise ValueError('Departure continuation requires a verified IRT source')
    mission=source.metadata['mission']
    free_solution=None
    free_attempted=False
    free_failure=None
    last_free_guess=None
    profile=dict(stage='departure',mission=mission,source_arrays_sha256=source.metadata.get('arrays_sha256'),
                 budget_s=mission['solver'].get('departure_budget_s',90),
                 min_step=.2 if mission['departure_mode']=='free' else .001,max_step=.25)
    def correct(parameter,previous,deadline):
        nonlocal free_solution,free_attempted,free_failure,last_free_guess
        mode=mission['departure_mode']
        if mode in ('bounded_norm','free') and not free_attempted:
            # Solve the inactive-constraint branch separately, never force the
            # velocity onto the bound after the unconstrained optimum is inside it.
            free_attempted=True
            last_free_guess=tuple(previous.metadata['costates_initial'])
            try:
                free_solution=_correct(source,parameter,previous,min(deadline,perf_counter()+12),free=True)
            except (ValueError,RuntimeError,TimeoutError) as exc:
                free_failure=str(exc)
        if mode=='free' and free_solution is None:
            raise RuntimeError('Free branch unavailable: '+str(free_failure))
        if mode=='free' or (mode=='bounded_norm' and free_solution is not None and free_solution.metadata['departure']['norm_m_s']<=parameter*mission['vinf_max_m_s']):
            result=deepcopy(free_solution)
            result.metadata['departure'].update(parameter=parameter,bound_active=False,
                                                requested_mode=mode,bound_m_s=parameter*mission['vinf_max_m_s'])
            return result
        try:
            result=_correct(source,parameter,previous,deadline)
        except (ValueError,RuntimeError,TimeoutError):
            seed=tuple(previous.metadata['costates_initial'])
            if mode=='bounded_norm' and seed!=last_free_guess:
                # The active branch approaches p_v(t0)=0 at release of the
                # inequality. Its improved current solution is a new seed for
                # the inactive branch, which may have failed from the original IRT.
                last_free_guess=seed
                try:
                    candidate=_correct(source,parameter,previous,min(deadline,perf_counter()+12),free=True)
                    free_solution=candidate
                    if candidate.metadata['departure']['norm_m_s']<=parameter*mission['vinf_max_m_s']:
                        candidate.metadata['departure'].update(parameter=parameter,bound_active=False,
                                                               requested_mode=mode,bound_m_s=parameter*mission['vinf_max_m_s'])
                        return candidate
                except (ValueError,RuntimeError,TimeoutError) as exc:
                    free_failure=str(exc)
            raise
        if free_failure is not None:
            result.metadata['departure']['free_branch_failure']=free_failure
        return result
    return continue_parameter(source,output,correct,profile=profile,resume=resume)
