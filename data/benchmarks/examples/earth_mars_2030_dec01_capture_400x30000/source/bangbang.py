"""Exact bang-bang correction using smooth, explicitly separated arcs."""
from time import perf_counter
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares
from scipy.special import softmax
from .data import Scales
from .bounded import canonical,assemble,verify_bounded
from .bounded_model import origin_and_boundary,boundary_residual


def solve_bangbang(source,previous,model,deadline,stage):
    if model.alpha!=1:
        raise ValueError('Exact arc correction requires alpha=1')
    scales=Scales(**source.metadata['scales'])
    times=previous.arrays['t_s']/scales.time_s
    guess=canonical(previous,model)
    throttle=np.asarray(previous.arrays.get('throttle'))
    if throttle.shape!=times.shape:
        raise ValueError('A preceding mixed-functional solution is required')
    active=throttle>.5
    changes=np.flatnonzero(np.diff(active.astype(int)))
    switches=[]
    for index in changes:
        fraction=(.5-throttle[index])/(throttle[index+1]-throttle[index])
        switches.append(times[index]+fraction*(times[index+1]-times[index]))
    edges=np.r_[0,switches,times[-1]]
    durations=np.diff(edges)
    if np.any(durations<=1e-10):
        raise ValueError('Degenerate switch intervals in the preceding solution')
    count=len(switches)
    first=float(active[0])
    pcount=7 if model.variable_mass else 6
    if model.variable_mass:
        p0=np.r_[guess[7:13,0],guess[13,0]]
    else:
        p0=guess[6:12,0]
    alpha_previous=previous.metadata['bounded_model']['alpha']
    p0=p0/max(alpha_previous,.1)
    mission=source.metadata['mission']
    variable_velocity=mission['departure_mode']!='fixed_vector' and (mission['vinf_max_m_s']>0 or mission['departure_mode']=='free')
    face='active' if previous.metadata['departure']['bound_active'] else 'free'
    faces=[face]
    if mission['departure_mode']=='bounded_norm':faces.append('free' if face=='active' else 'active')
    body,target=origin_and_boundary(source,scales)
    free_departure=False
    prefix=None

    def integrate(x,dense=False):
        if perf_counter()>deadline:raise TimeoutError('Exact bang-bang correction budget reached')
        weights=softmax(np.r_[x[len(prefix):],0.])
        arc_edges=np.r_[0,np.cumsum(weights)*times[-1]]
        arc_edges[-1]=times[-1]
        state=np.zeros(model.dimension)
        state[:3]=body[:3]
        if free_departure:
            # Enforce the inactive initial-velocity transversality exactly.
            # Leaving tiny p_v(0) as three independent shooting unknowns makes
            # lunar endpoint sensitivity compete with the same residual rows.
            velocity_index=4 if model.variable_mass else 3
            state[3:6]=x[velocity_index:velocity_index+3]
            if model.variable_mass:
                state[6]=1.;state[7:10]=x[:3];state[13]=x[3]
            else:state[6:9]=x[:3]
        elif model.variable_mass:
            state[3:6]=x[pcount:pcount+3] if variable_velocity else guess[3:6,0]
            state[6]=1.;state[7:13]=x[:6];state[13]=x[6]
        else:
            state[3:6]=x[pcount:pcount+3] if variable_velocity else guess[3:6,0]
            state[6:12]=x[:6]
        initial=state.copy()
        switch_states=[]
        solutions=[]
        for k,(left,right) in enumerate(zip(arc_edges[:-1],arc_edges[1:])):
            d=first if k%2==0 else 1-first
            def ode(t,y):
                if perf_counter()>deadline:raise TimeoutError('Exact arc integration budget reached')
                return model.rhs(t,y,throttle=d)
            sol=solve_ivp(ode,(left,right),state,method='DOP853',rtol=1e-12,atol=1e-14,dense_output=dense)
            if not sol.success:raise RuntimeError(sol.message)
            state=sol.y[:,-1]
            if k<count:switch_states.append(state.copy())
            solutions.append(sol)
        return initial,state,np.array(switch_states),arc_edges,solutions

    failures=[]
    for face in faces:
        free_departure=variable_velocity and face=='free' and mission['departure_mode'] in ('free','bounded_norm')
        if free_departure:
            independent=np.r_[p0[:3],p0[6]] if model.variable_mass else p0[:3]
            prefix=np.r_[independent,guess[3:6,0]]
        else:prefix=np.r_[p0,guess[3:6,0]] if variable_velocity else p0
        x0=np.r_[prefix,np.log(durations[:-1]/durations[-1])]
        last_x=None;last=None
        def residual(x):
            nonlocal last_x,last
            if last_x is None or not np.array_equal(last_x,x):
                initial,final,nodes,_,_=integrate(x)
                values=boundary_residual(initial,final,source,scales,model,face,kkt=True)
                if len(nodes):values=np.r_[values,model.switching(nodes.T)/model.a_max]
                last=values;last_x=x.copy()
            return last
        try:
            lower=np.r_[np.full(len(prefix),-np.inf),np.full(count,-20.)]
            upper=np.r_[np.full(len(prefix),np.inf),np.full(count,20.)]
            opt=least_squares(residual,x0,method='trf',bounds=(lower,upper),diff_step=1e-6 if model.gravity is not None else 1e-5,
                              x_scale='jac',max_nfev=80,xtol=1e-11,ftol=1e-11,gtol=1e-11)
            initial,final,nodes,arc_edges,solutions=integrate(opt.x,dense=True)
            evaluation=np.unique(np.r_[times,arc_edges])
            y=np.empty((model.dimension,len(evaluation)))
            control=np.empty(len(evaluation))
            for k,sol in enumerate(solutions):
                mask=(evaluation>=arc_edges[k])&(evaluation<=arc_edges[k+1])
                y[:,mask]=sol.sol(evaluation[mask])
                control[mask]=first if k%2==0 else 1-first
            result=assemble(source,model,evaluation,y,face,stage,
                            extra=dict(switch_times_s=(arc_edges[1:-1]*scales.time_s).tolist(),
                                       functional_dimensionless=float(model.a_max*np.dot(np.diff(arc_edges),[first if k%2==0 else 1-first for k in range(len(arc_edges)-1)])),
                                       initial_throttle=first,bangbang_corrector=dict(nfev=int(opt.nfev),
                                       residual_norm=float(np.linalg.norm(opt.fun)),optimizer_success=bool(opt.success))),
                            throttle_override=control)
            check=verify_bounded(result,deadline)
            if not check['passed']:raise RuntimeError('Exact independent replay failed: '+str(check))
            result.metadata.update(status='verified_extremal',verification=check)
            return result
        except (ValueError,RuntimeError) as exc:
            failures.append(face+': '+str(exc))
    raise RuntimeError('; '.join(failures))
