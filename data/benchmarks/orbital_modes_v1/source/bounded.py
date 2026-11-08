"""Shared collocation adapter, conversion and verification for bounded stages."""
from copy import deepcopy
from dataclasses import asdict
from time import perf_counter
import numpy as np
from scipy.integrate import solve_bvp,solve_ivp,simpson
from scipy.optimize import least_squares
from .data import Scales,Trajectory
from .bounded_model import BoundedModel,boundary_residual,origin_and_boundary
from .bounded_derivatives import canonical_jacobian
from .problem import departure_speed_limit


def canonical(trajectory,model):
    scales=Scales(**trajectory.metadata['scales'])
    a=trajectory.arrays
    rv=scales.normalize_state(np.c_[a['r_m'],a['v_m_s']]).T
    p=a['costates'].T
    if not model.variable_mass:
        return np.vstack([rv,p[:6]])
    mass=a.get('mass_fraction_proxy',a.get('mass_kg',np.full(len(rv.T),trajectory.metadata['mission']['mass_kg']))/trajectory.metadata['mission']['mass_kg'])
    pm=p[6] if len(p)==7 else np.zeros(len(rv.T))
    return np.vstack([rv,mass,p[:6],pm])


def assemble(source,model,times,y,face,stage,extra=None,throttle_override=None):
    meta=deepcopy(source.metadata)
    scales=Scales(**meta['scales'])
    body,target=origin_and_boundary(source,scales)
    rv=scales.dimensional_state(y[:6].T)
    r,v,pr,pv,m,pm=model.split(y)
    throttle=model.throttle(y) if throttle_override is None else throttle_override
    acceleration=(model.a_max*throttle/(1+model.beta*(m-1))*pv/np.maximum(np.linalg.norm(pv,axis=0),1e-15)).T*scales.acceleration_m_s2
    arrays={k:value.copy() for k,value in source.arrays.items()
            if k not in ('costates','mass_kg','thrust_N','switching_function','mass_fraction_proxy','acceleration_m_s2','throttle')}
    arrays.update(t_s=times*scales.time_s,r_m=rv[:,:3],v_m_s=rv[:,3:],
                  costates=np.c_[pr.T,pv.T,pm] if model.variable_mass else np.c_[pr.T,pv.T],
                  acceleration_m_s2=acceleration,throttle=throttle,
                  switching_function=model.switching(y),active=throttle>1e-7)
    if model.variable_mass:
        if model.beta==1:
            arrays.update(mass_kg=m*meta['mission']['mass_kg'],
                          thrust_N=model.a_max*scales.acceleration_m_s2*meta['mission']['mass_kg']*throttle)
        else:
            arrays['mass_fraction_proxy']=m
    meta.update(stage=stage,status='solved_extremal',bounded_model=asdict(model),
                body_initial_state_si=scales.dimensional_state(body).tolist(),
                initial_state_si=rv[0].tolist(),costates_initial=arrays['costates'][0].tolist(),
                model='physical constant thrust and exhaust, variable mass' if model.variable_mass and model.beta==1 else 'Pazov bounded acceleration / mass homotopy',
                functional_dimensionless=float(simpson((1-model.alpha)*.5*(model.a_max*throttle)**2+model.alpha*model.a_max*throttle,x=times)))
    hardware=meta['mission']['spacecraft']['thrust_N']/meta['mission']['mass_kg']/scales.acceleration_m_s2
    meta['hardware_limit_reached']=bool(np.isclose(model.a_max,hardware,rtol=1e-10,atol=1e-14))
    if model.gravity_spec is not None:meta['gravity_spec']=deepcopy(model.gravity_spec)
    if model.variable_mass and model.beta==1:
        meta['title']=f"{meta['mission']['departure']} → {meta['mission']['target']}: ПСИ {meta['mission']['mass_kg']:g} кг"
    else:
        meta['title']=f"{meta['mission']['departure']} → {meta['mission']['target']}: ограниченное ускорение"
    for key in ('switch_times_s','initial_throttle'):
        meta.pop(key,None)
    meta['costate_convention']='dimensionless [p_r,p_v,p_m] for normalized remaining mass' if model.variable_mass else 'dimensionless [p_r,p_v], maximizing Hamiltonian'
    dv=rv[0,3:]-meta['body_initial_state_si'][3:]
    meta['departure']=dict(mode=meta['mission']['departure_mode'],bound_active=face=='active',
                           vector_m_s=dv.tolist(),norm_m_s=float(np.linalg.norm(dv)),
                           bound_m_s=departure_speed_limit(meta['mission']))
    if meta['mission'].get('parking_departure'):
        spec=meta['mission']['parking_departure']
        meta['departure_quantity']='boundary_speed'
        meta['departure']['asymptotic_excess_m_s']=float(np.sqrt(max(0.,np.dot(dv,dv)-2*spec['mu_m3_s2']/spec['interface_radius_m'])))
    if extra:
        meta.update(extra)
    return Trajectory(meta,arrays).validate()


def _independent_rhs(t,y,model,forced=None):
    # Deliberately separate from Pazov and BoundedModel.right-hand sides.
    if model.variable_mass:
        r,v,m,pr,pv,pm=y[:3],y[3:6],y[6],y[7:10],y[10:13],y[13]
    else:
        r,v,pr,pv=y[:3],y[3:6],y[6:9],y[9:12]
        m,pm=1.,0.
    rho=np.linalg.norm(r)
    me=1+model.beta*(m-1)
    qpv=np.linalg.norm(pv)
    switch=model.a_max*qpv/me-model.beta*model.q*pm-model.alpha*model.a_max
    if forced is not None:
        d=forced
    elif model.alpha>=1-1e-12:
        d=float(switch>0)
    else:
        d=np.clip(switch/((1-model.alpha)*model.a_max**2),0.,1.)
    e=pv/max(qpv,1e-15)
    force=model.a_max*d/me*e
    jac=(3*np.outer(r,r)/rho**2-np.eye(3))/rho**3
    gravity=-r/rho**3
    if model.gravity is not None:gravity,jac=model.gravity.independent_scalar(t,r)
    if model.variable_mass:
        return np.r_[v,gravity+force,-model.beta*model.q*d,-jac.T@pv,-pr,model.beta*model.a_max*d*qpv/me**2]
    return np.r_[v,gravity+force,-jac.T@pv,-pr]


def verify_bounded(trajectory,deadline=np.inf):
    meta,a=trajectory.metadata,trajectory.arrays
    model=BoundedModel(**meta['bounded_model'])
    from .contract import audit_configuration
    try:
        parameter_audit=audit_configuration(trajectory,require_final=meta.get('stage')=='psi' and model.alpha==1 and model.beta==1)
    except ValueError as exc:
        return dict(passed=False,method='configuration and physical parameter contract',error=str(exc))
    scales=Scales(**meta['scales'])
    times=a['t_s']/scales.time_s
    stored=canonical(trajectory,model)
    def ode(t,y,forced=None):
        if perf_counter()>deadline:
            raise TimeoutError('Independent bounded replay budget reached')
        return _independent_rhs(t,y,model,forced)
    switches=np.asarray(meta.get('switch_times_s',[]))/scales.time_s
    if model.alpha==1 and 'initial_throttle' in meta:
        edges=np.r_[0,switches,times[-1]]
        state=stored[:,0].copy()
        replay=np.empty_like(stored)
        arc_solutions=[]
        sign_violation=0.
        switch_error=0.
        for k,(left,right) in enumerate(zip(edges[:-1],edges[1:])):
            d=float(meta['initial_throttle'] if k%2==0 else 1-meta['initial_throttle'])
            sol=solve_ivp(lambda t,y:ode(t,y,d),(left,right),state,method='LSODA',rtol=2e-12,atol=2e-14,dense_output=True)
            if not sol.success:raise RuntimeError('Independent segmented replay failed')
            state=sol.y[:,-1]
            arc_solutions.append(sol)
            mask=(times>=left)&(times<=right)
            replay[:,mask]=sol.sol(times[mask])
            probes=sol.sol(np.linspace(left,right,41))
            switch=model.switching(probes)/model.a_max
            sign_violation=max(sign_violation,float(np.max(-switch if d else switch)))
            if k<len(switches):switch_error=max(switch_error,abs(float(model.switching(state)/model.a_max)))
    else:
        sol=solve_ivp(ode,(0,times[-1]),stored[:,0],t_eval=times,method='LSODA',rtol=2e-12,atol=2e-14,dense_output=model.gravity is not None)
        if not sol.success or sol.y.shape!=stored.shape:
            raise RuntimeError('Independent bounded replay did not reach arrival')
        replay=sol.y
    _,target=origin_and_boundary(trajectory,scales)
    dr=float(np.linalg.norm(replay[:3,-1]-target[:3])*scales.distance_m)
    dv=float(np.linalg.norm(replay[3:6,-1]-target[3:])*scales.velocity_m_s)
    diff_r=float(np.linalg.norm(replay[:3]-stored[:3],axis=0).max()*scales.distance_m)
    diff_v=float(np.linalg.norm(replay[3:6]-stored[3:6],axis=0).max()*scales.velocity_m_s)
    mission=meta['mission']
    face=meta['departure'].get('face','active' if meta['departure']['bound_active'] else 'free')
    bc=boundary_residual(replay[:,0],replay[:,-1],trajectory,scales,model,face,kkt=True)
    bc_error=float(np.linalg.norm(bc))
    if model.alpha==1 and 'initial_throttle' in meta:
        parity=np.searchsorted(np.asarray(meta['switch_times_s']),a['t_s'],side='right')%2
        expected_throttle=np.where(parity==0,meta['initial_throttle'],1-meta['initial_throttle'])
    else:expected_throttle=model.throttle(stored)
    throttle_error=float(np.max(np.abs(a['throttle']-expected_throttle)))
    passed=dr<=mission['position_tolerance_m'] and diff_r<=mission['position_tolerance_m'] and diff_v<=mission['velocity_tolerance_m_s']
    passed &= throttle_error<1e-7 and np.min(a['throttle'])>=0 and np.max(a['throttle'])<=1
    passed &= dv<=mission['velocity_tolerance_m_s'] if mission['mode']=='rendezvous' else np.linalg.norm(replay[model.pv_slice,-1])<1e-8
    # Boundary position/velocity components are checked dimensionally above;
    # the remaining transversality components must also converge.
    passed &= bc_error<max(1e-8,mission['position_tolerance_m']/scales.distance_m*2,
                          mission['velocity_tolerance_m_s']/scales.velocity_m_s*2)
    if mission['departure_mode']=='bounded_norm':
        passed &= meta['departure']['norm_m_s']<=departure_speed_limit(mission)+mission['velocity_tolerance_m_s']
        if face=='active':
            body,_=origin_and_boundary(trajectory,scales)
            passed &= np.dot(replay[model.pv_slice,0],replay[3:6,0]-body[3:])>=-1e-9
    report=dict(passed=bool(passed),position_residual_m=dr,velocity_residual_m_s=dv,
                 parameter_audit=parameter_audit,
                 trajectory_difference_m=diff_r,velocity_difference_m_s=diff_v,
                 stored_throttle_error=throttle_error,
                 stored_throttle_minimum=float(np.min(a['throttle'])),
                 stored_throttle_maximum=float(np.max(a['throttle'])),
                 canonical_boundary_residual=bc_error,
                 method='LSODA with independent bounded/mass equations',
                 scope='Numerical extremal and constraints; no global optimality proof')
    report['departure_norm_m_s']=meta['departure']['norm_m_s']
    if model.gravity is not None:
        if model.alpha==1 and 'initial_throttle' in meta:
            def state_at(t):
                values=np.asarray(t)
                indices=np.clip(np.searchsorted(edges,values,side='right')-1,0,len(arc_solutions)-1)
                if values.ndim==0:return arc_solutions[int(indices)].sol(float(values))
                states=np.empty((model.dimension,len(values)))
                for k,arc in enumerate(arc_solutions):
                    mask=indices==k
                    if np.any(mask):states[:,mask]=arc.sol(values[mask])
                return states
        else:state_at=sol.sol
        clearance=model.gravity.clearance_report(state_at,times)
        passed &= clearance['passed']
        report.update(clearance=clearance,passed=bool(passed))
    if model.alpha==1 and 'initial_throttle' in meta:
        passed &= sign_violation<1e-6 and switch_error<1e-6
        report.update(switching_sign_violation=sign_violation,switching_node_residual=switch_error,passed=bool(passed))
    if model.variable_mass:
        minimum=float(replay[6].min()*mission['mass_kg'])
        report['minimum_mass_kg']=minimum
        if model.beta==1:
            report['fuel_kg']=float(mission['mass_kg']*(1-replay[6,-1]))
            mass_difference=float(np.max(np.abs(replay[6]-stored[6]))*mission['mass_kg'])
            force=model.a_max*scales.acceleration_m_s2*mission['mass_kg']
            thrust_error=float(np.max(np.abs(a['thrust_N']-force*expected_throttle)))
            passed &= mass_difference<1e-4 and thrust_error<1e-9
            report.update(mass_difference_kg=mass_difference,stored_thrust_error_N=thrust_error)
            if meta['stage']=='psi' and model.alpha==1:
                passed &= force<=mission['spacecraft']['thrust_N']*(1+1e-9)
            passed &= minimum>=mission['spacecraft']['dry_mass_kg']-1e-5
            report['passed']=bool(passed)
            if model.alpha==1 and 'initial_throttle' in meta:
                durations=np.diff(np.r_[0,switches,times[-1]])*scales.time_s
                flags=np.array([meta['initial_throttle'] if k%2==0 else 1-meta['initial_throttle'] for k in range(len(durations))])
                expected=model.q/scales.time_s*mission['mass_kg']*float(np.dot(durations,flags))
                balance=abs(expected-report['fuel_kg'])
                passed &= balance<1e-4
                report.update(mass_balance_error_kg=balance,passed=bool(passed))
    return report


def _shoot_bounded(source,model,guess,times,face,deadline,stage):
    scales=Scales(**source.metadata['scales'])
    body,target=origin_and_boundary(source,scales)
    mission=source.metadata['mission']
    if mission['departure_mode']=='fixed_vector':
        guess=guess.copy();guess[3:6,0]=body[3:]+np.asarray(mission['vinf_vector_m_s'])/scales.velocity_m_s
    variable_velocity=mission['departure_mode']!='fixed_vector' and (mission['vinf_max_m_s']>0 or mission['departure_mode']=='free')
    p=np.r_[guess[7:13,0],guess[13,0]] if model.variable_mass else guess[6:12,0]
    size=len(p)
    x0=np.r_[p,guess[3:6,0]] if variable_velocity else p
    last_x=None;last=None
    def propagate(x,full=False):
        y=np.zeros(model.dimension);y[:3]=body[:3]
        y[3:6]=x[size:size+3] if variable_velocity else guess[3:6,0]
        if model.variable_mass:y[6]=1.;y[7:13]=x[:6];y[13]=x[6]
        else:y[6:12]=x[:6]
        def ode(t,state):
            if perf_counter()>deadline:raise TimeoutError('Bounded shooting budget reached')
            return model.rhs(t,state)
        sol=solve_ivp(ode,(0,times[-1]),y,method='DOP853',rtol=2e-12,atol=2e-14,t_eval=times if full else None)
        if not sol.success:raise RuntimeError(sol.message)
        return y,sol
    def residual(x):
        nonlocal last_x,last
        if last_x is None or not np.array_equal(last_x,x):
            initial,sol=propagate(x)
            last=boundary_residual(initial,sol.y[:,-1],source,scales,model,face,kkt=True);last_x=x.copy()
        return last
    opt=least_squares(residual,x0,method='trf',diff_step=1e-5,x_scale='jac',max_nfev=60,
                      xtol=1e-11,ftol=1e-11,gtol=1e-11)
    initial,sol=propagate(opt.x,full=True)
    candidate=assemble(source,model,times,sol.y,face,stage)
    check=verify_bounded(candidate,deadline)
    if not check['passed']:raise RuntimeError('Bounded shooting replay failed: '+str(check))
    candidate.metadata.update(status='verified_extremal',verification=check,
                               corrector='bounded single shooting',corrector_nfev=int(opt.nfev))
    return candidate


def collocate(source,previous,model,deadline,stage,*,analytic_derivatives=True):
    scales=Scales(**source.metadata['scales'])
    times=previous.arrays['t_s']/scales.time_s
    guess=canonical(previous,model)
    if source.metadata['mission']['departure_mode']=='fixed_vector':
        body,_=origin_and_boundary(source,scales)
        guess[3:6,0]=body[3:]+np.asarray(source.metadata['mission']['vinf_vector_m_s'])/scales.velocity_m_s
    old=previous.metadata.get('bounded_model',{})
    old_alpha=float(old.get('alpha',0.))
    if model.alpha<old_alpha and old_alpha>0:
        if model.variable_mass:guess[7:14]*=model.alpha/old_alpha
        else:guess[6:12]*=model.alpha/old_alpha
    if model.alpha>old_alpha and old_alpha<1:
        if model.variable_mass and old_alpha>0:
            # For nearly linear physical controls, homogeneous costate scaling
            # preserves switching locations while the regularization shrinks.
            guess[7:14]*=model.alpha/old_alpha
        elif not model.variable_mass:
            # Predict the change of primer norm across the moving dead zone.
            # Reusing the old primer unmodified can turn every control off and
            # leave Newton with a zero control Jacobian.
            c=(1-model.alpha)/(1-old_alpha)
            d=model.alpha-c*old_alpha
            pv=guess[9:12].copy();pr=guess[6:9].copy()
            den=np.sqrt(np.sum(pv*pv,axis=0)+max(model.a_max*.1,1e-5)**2)
            factor=c+d/den
            guess[9:12]=factor*pv
            guess[6:9]=factor*pr-d*np.sum(pv*pr,axis=0)/den**3*pv
    mission=source.metadata['mission']
    default_face='free' if not previous.metadata.get('departure',{}).get('bound_active',True) else 'active'
    if mission['departure_mode']=='free':default_face='free'
    faces=[default_face]
    if mission['departure_mode']=='bounded_norm':faces.append('free' if default_face=='active' else 'active')
    reasons=[]
    for face in faces:
        fallback_allowed=True
        settings=source.metadata['mission']['solver']
        collocation_seconds=float(settings.get('collocation_budget_s',12. if model.gravity is not None else 4.))
        shooting_seconds=float(settings.get('shooting_budget_s',12. if model.gravity is not None else 6.))
        collocation_deadline=min(deadline,perf_counter()+collocation_seconds)
        def ode(t,y):
            if perf_counter()>collocation_deadline:raise TimeoutError('Bounded collocation budget reached')
            return model.rhs(t,y)
        def ode_jac(t,y):
            if perf_counter()>collocation_deadline:raise TimeoutError('Bounded collocation budget reached')
            return canonical_jacobian(model,y)
        fun_jac=ode_jac if analytic_derivatives and model.gravity is None else None
        mesh,iterate=times,guess
        use_parameters=face=='active' and mission['departure_mode'] in ('fixed_norm','bounded_norm') and mission['vinf_max_m_s']>0
        parameters=None
        if use_parameters:
            body,_=origin_and_boundary(source,scales)
            bound=departure_speed_limit(mission)/scales.velocity_m_s
            dv=guess[3:6,0]-body[3:]
            direction=dv/max(np.linalg.norm(dv),1e-15)
            initial_excess=bound*direction
            parameters=np.r_[initial_excess,np.dot(guess[model.pv_slice,0],initial_excess)/bound**2]
        def param_bc(a,b,p):
            bc=boundary_residual(a,b,source,scales,model,face)
            bc[3:6]=a[3:6]-body[3:]-p[:3]
            return np.r_[bc,a[model.pv_slice]-p[3]*p[:3],(np.dot(p[:3],p[:3])-bound**2)/(2*bound)]
        for tolerance in (2e-8,2e-9,2e-10):
            try:
                if use_parameters:
                    def parameter_jac(t,y,p):
                        return ode_jac(t,y),np.zeros((model.dimension,len(p),len(t)))
                    sol=solve_bvp(lambda t,y,p:ode(t,y),param_bc,mesh,iterate,p=parameters,tol=tolerance,max_nodes=12000,
                                  fun_jac=parameter_jac if fun_jac is not None else None)
                else:
                    sol=solve_bvp(ode,lambda x,z:boundary_residual(x,z,source,scales,model,face),mesh,iterate,tol=tolerance,max_nodes=12000,fun_jac=fun_jac)
                if not sol.success:raise RuntimeError(sol.message)
                y=sol.sol(times)
                candidate=assemble(source,model,times,y,face,stage)
                if mission['departure_mode']=='bounded_norm' and candidate.metadata['departure']['norm_m_s']>departure_speed_limit(mission)+mission['velocity_tolerance_m_s']:
                    fallback_allowed=False
                    raise ValueError('Inactive departure branch is outside the allowed excess ball')
                if mission['departure_mode']=='bounded_norm' and face=='active':
                    body,_=origin_and_boundary(source,scales)
                    if np.dot(y[model.pv_slice,0],y[3:6,0]-body[3:])<-1e-9:
                        fallback_allowed=False
                        raise ValueError('Active departure branch has a negative inequality multiplier')
                check=verify_bounded(candidate,deadline)
                if check['passed']:
                    candidate.metadata.update(status='verified_extremal',verification=check,collocation_tolerance=tolerance,
                                              collocation_derivatives='analytic central-field' if fun_jac is not None else 'finite differences',
                                              collocation_nodes=int(len(sol.x)),collocation_iterations=int(sol.niter))
                    return candidate
                if tolerance==2e-10:
                    raise RuntimeError('Independent replay failed at final accuracy: '+str(check))
                # A boundary-exact collocation polynomial can have a measurable
                # forward error. Tighten its accuracy before reducing a physical
                # continuation parameter; use the already converged mesh.
                mesh,iterate=sol.x,sol.y
                if use_parameters:parameters=sol.p
            except (ValueError,RuntimeError,TimeoutError) as exc:
                reasons.append(face+': '+str(exc))
                break
        if fallback_allowed and perf_counter()<deadline:
            try:return _shoot_bounded(source,model,guess,times,face,min(deadline,perf_counter()+shooting_seconds),stage)
            except (ValueError,RuntimeError,TimeoutError) as exc:reasons.append(face+' shooting: '+str(exc))
    raise RuntimeError('; '.join(reasons))
