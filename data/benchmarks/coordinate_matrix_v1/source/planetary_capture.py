"""Planet-centered transverse-braking capture and a real state/mass interface.

The legacy integrate_equinoctial.m control_type=2 is constant retrograde
transverse thrust. Here it uses the requested constant F,c and remaining mass,
without the historical power law or empirical fuel multiplier. The model is
patched central fields, not an N-body or globally optimal capture solution.
"""
from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp
from .data import Scales,DAY_S
from dataclasses import replace
from copy import deepcopy
from time import perf_counter


@dataclass(frozen=True)
class CaptureOrbit:
    mu_m3_s2: float
    planet_radius_m: float
    periapsis_altitude_m: float
    apoapsis_altitude_m: float
    interface_radius_m: float

    def validate(self):
        values=np.array(list(self.__dict__.values()),dtype=float)
        if not np.isfinite(values).all() or np.min(values)<=0:raise ValueError('Capture dimensions must be positive and finite')
        if self.apoapsis_altitude_m<self.periapsis_altitude_m:raise ValueError('Apoapsis must not be below periapsis')
        if self.interface_radius_m<=self.planet_radius_m+self.apoapsis_altitude_m:raise ValueError('Capture interface must lie above the final orbit')
        return self


def elements(rv,mu):
    r,v=np.asarray(rv[:3]),np.asarray(rv[3:6]);R=np.linalg.norm(r)
    h=np.cross(r,v);energy=np.dot(v,v)/2-mu/R
    eccentricity=np.linalg.norm(np.cross(v,h)/mu-r/R)
    a=-mu/(2*energy) if energy<0 else np.inf
    return dict(energy_m2_s2=float(energy),eccentricity=float(eccentricity),
                periapsis_radius_m=float(np.dot(h,h)/mu/(1+eccentricity)),
                apoapsis_radius_m=float(a*(1+eccentricity)))


def backward_capture(orbit,final_mass_kg,thrust_N,exhaust_velocity_m_s,*,max_days=2000.,control=None):
    if control is not None:
        from .angular_capture import backward_angular_capture
        return backward_angular_capture(orbit,final_mass_kg,thrust_N,exhaust_velocity_m_s,control,max_days)
    orbit.validate()
    if min(final_mass_kg,thrust_N,exhaust_velocity_m_s)<=0:raise ValueError('Capture engine/mass must be positive')
    rp=orbit.planet_radius_m+orbit.periapsis_altitude_m
    ra=orbit.planet_radius_m+orbit.apoapsis_altitude_m
    scales=Scales(rp,orbit.mu_m3_s2)
    Rjoin=orbit.interface_radius_m/rp
    A=thrust_N/final_mass_kg/scales.acceleration_m_s2
    q=thrust_N*scales.time_s/(final_mass_kg*exhaust_velocity_m_s)
    y0=np.r_[1.,0.,0.,0.,np.sqrt(2*ra/(rp+ra)),0.,1.]
    def ode(t,y):
        r,v=y[:3],y[3:6];R=np.linalg.norm(r);er=r/R
        transverse=v-er*np.dot(v,er);transverse/=np.linalg.norm(transverse)
        return np.r_[v,-r/R**3-A/y[6]*transverse,-q]
    def apo_event(t,y):
        E=np.dot(y[3:6],y[3:6])/2-1/np.linalg.norm(y[:3])
        if E>=0:return Rjoin*1e6
        h=np.cross(y[:3],y[3:6]);e=np.linalg.norm(np.cross(y[3:6],h)-y[:3]/np.linalg.norm(y[:3]))
        return -(1+e)/(2*E)-Rjoin
    apo_event.terminal=True;apo_event.direction=1
    sol=solve_ivp(ode,(0,-max_days*DAY_S/scales.time_s),y0,method='DOP853',
                  rtol=2e-11,atol=2e-13,events=apo_event,dense_output=True)
    if not sol.success or not len(sol.t_events[0]):raise RuntimeError('Backward capture did not reach the interface apoapsis')
    tb=float(sol.t[-1]);yb=sol.y[:,-1]
    r,v=yb[:3],yb[3:6];R=np.linalg.norm(r);h=np.cross(r,v)
    evec=np.cross(v,h)-r/R;e=np.linalg.norm(evec);a=Rjoin/(1+e)
    eh=evec/e if e>1e-10 else r/R
    nh=h/np.linalg.norm(h);apo=-Rjoin*eh
    va=np.linalg.norm(h)/Rjoin*np.cross(nh,-eh)
    # Analytic Kepler coast from the preceding apoapsis to thrust onset.
    E=np.arctan2(np.dot(r,v)/np.sqrt(a),1-R/a)
    M=E-e*np.sin(E)
    coast=float(np.mod(M-np.pi,2*np.pi)*a**1.5)
    start=tb-coast
    burn_t=np.unique(np.r_[sol.t[::-1],np.linspace(tb,0,1200)])
    burn_y=sol.sol(burn_t)
    coast_t=np.linspace(start,tb,300) if coast>1e-9 else np.array([tb])
    mean=np.pi+(coast_t-start)/a**1.5
    anomaly=mean.copy()
    for _ in range(20):
        change=(anomaly-e*np.sin(anomaly)-mean)/(1-e*np.cos(anomaly));anomaly-=change
        if np.max(np.abs(change))<1e-13:break
    oh=np.cross(nh,eh)
    rc=a*(np.cos(anomaly)-e)[:,None]*eh+a*np.sqrt(1-e*e)*np.sin(anomaly)[:,None]*oh
    factor=1/(np.sqrt(a)*(1-e*np.cos(anomaly)))
    vc=factor[:,None]*(-np.sin(anomaly)[:,None]*eh+np.sqrt(1-e*e)*np.cos(anomaly)[:,None]*oh)
    coast_y=np.c_[rc,vc,np.full(len(rc),yb[6])].T
    t=np.r_[coast_t[:-1],burn_t]-start
    y=np.c_[coast_y[:,:-1],burn_y]
    state=np.c_[y[:3].T*scales.distance_m,y[3:6].T*scales.velocity_m_s]
    mass=y[6]*final_mass_kg
    duration=-start*scales.time_s
    return dict(t_s=t*scales.time_s,relative_state_si=state,mass_kg=mass,
                thrust_N=np.where(t>=coast,thrust_N,0.),
                burn_start_s=coast*scales.time_s,duration_s=duration,
                entry_mass_kg=float(mass[0]),final_mass_kg=final_mass_kg,
                final_elements=elements(state[-1],orbit.mu_m3_s2),
                entry_elements=elements(state[0],orbit.mu_m3_s2))


def orient_capture(capture,planet_state):
    """Exploit free orbit orientation; rotate the entire solution, not its seam."""
    y=capture['relative_state_si'];r,v=y[0,:3],y[0,3:]
    er=r/np.linalg.norm(r);n=np.cross(r,v);n/=np.linalg.norm(n)
    source=np.column_stack((er,np.cross(n,er),n))
    radial=-planet_state[:3]/np.linalg.norm(planet_state[:3])
    normal=np.cross(planet_state[:3],planet_state[3:]);normal/=np.linalg.norm(normal)
    target=np.column_stack((radial,np.cross(normal,radial),normal))
    rotation=target@source.T
    result=dict(capture)
    result['relative_state_si']=np.c_[y[:,:3]@rotation.T,y[:,3:]@rotation.T]
    result['rotation_to_ecliptic']=rotation.tolist()
    if 'reference_axis' in capture:
        result['reference_axis']=(rotation@np.asarray(capture['reference_axis'])).tolist()
    return result


def correct_interface(seed,mission,*,budget_s=60.):
    """Re-solve the physical outer segment; old data are an unverified guess."""
    from .contract import configuration_hash,make_request,audit_configuration
    from .bounded_model import BoundedModel
    from .bangbang import solve_bangbang
    from .bounded import verify_bounded
    from .ephemerides import Ephemerides
    old=seed.metadata['mission']
    for key in ('departure','target','launch_tdb','tof_days','mass_kg','spacecraft','departure_mode','vinf_max_m_s'):
        if old[key]!=mission.to_dict()[key]:raise ValueError('Capture seed must use the same physical transfer inputs: '+key)
    initial,target,scales=mission.boundary()
    context=deepcopy(seed)
    context.metadata.update(mission=mission.to_dict(),case_id=mission.case_id,target_state_si=target.tolist(),body_initial_state_si=initial.tolist(),
                            configuration_sha256=configuration_hash(mission),status='unverified_boundary_seed')
    context.metadata.pop('verification',None)
    # Markers describe the body and the actual nonzero-radius interface.
    planet=mission.ephemerides().state(mission.target,mission.arrival_jd,mission.center)
    context.metadata['markers']=[dict(label=mission.departure+', старт',r_m=initial[:3].tolist()),
                                 dict(label=mission.target,r_m=planet[:3].tolist(),color='#df1111',role='target'),
                                 dict(label='Вход в сферу '+mission.target,r_m=target[:3].tolist(),hollow=True)]
    model=BoundedModel(**seed.metadata['bounded_model'])
    if not (model.alpha==1 and model.beta==1 and model.variable_mass):raise ValueError('Capture boundary corrector requires a verified physical PSI seed')
    result=solve_bangbang(context,seed,model,perf_counter()+budget_s,'psi')
    request=make_request(mission)
    audit_configuration(result,mission,request,require_final=True)
    if not verify_bounded(result)['passed']:raise RuntimeError('Corrected capture interface failed independent replay')
    return result,request


def forward_capture(orbit,initial_state_si,initial_mass_kg,thrust_N,exhaust_velocity_m_s,
                    burn_start_s,duration_s,*,sample_times=None,control=None,reference_axis=None):
    """Independent forward replay, cross-product transverse axis, LSODA."""
    if control is not None:
        from .angular_capture import forward_angular_capture
        if reference_axis is None:raise ValueError('Controlled capture needs its rotated reference axis')
        return forward_angular_capture(orbit,initial_state_si,initial_mass_kg,thrust_N,exhaust_velocity_m_s,
                                       burn_start_s,duration_s,control,reference_axis,sample_times=sample_times)
    scales=Scales(orbit.planet_radius_m+orbit.periapsis_altitude_m,orbit.mu_m3_s2)
    y=np.r_[scales.normalize_state(initial_state_si),1.]
    A=thrust_N/initial_mass_kg/scales.acceleration_m_s2
    q=thrust_N*scales.time_s/(initial_mass_kg*exhaust_velocity_m_s)
    edges=np.array([0.,burn_start_s,duration_s])/scales.time_s
    times=np.unique(np.r_[np.linspace(0,duration_s,2500),sample_times if sample_times is not None else [],burn_start_s])
    # Adaptive and uniform grids can differ by sub-nanoseconds. Such samples
    # collapse when translated to the heliocentric clock. Keep one sample,
    # retaining the exact endpoints and thrust switch.
    protected=np.array([0.,burn_start_s,duration_s])
    times=times[np.min(np.abs(times[:,None]-protected),axis=1)>1e-6]
    times=np.unique(np.r_[times,protected])
    keep=np.r_[np.diff(times)>1e-6,True]
    times=times[keep]
    output=np.empty((7,len(times)));minimum=np.inf
    for k,(left,right) in enumerate(zip(edges[:-1],edges[1:])):
        if right<=left:continue
        d=float(k==1)
        def rhs(t,z):
            r,v=z[:3],z[3:6];R=np.sqrt(np.dot(r,r))
            transverse=np.cross(np.cross(r,v),r);transverse/=np.sqrt(np.dot(transverse,transverse))
            return np.r_[v,-r/(R*R*R)-d*A/z[6]*transverse,-d*q]
        def peri(t,z):return float(np.dot(z[:3],z[3:6]))
        peri.direction=1
        sol=solve_ivp(rhs,(left,right),y,method='LSODA',rtol=5e-13,atol=5e-14,dense_output=True,events=peri)
        if not sol.success:raise RuntimeError('Independent planet-centered capture replay failed')
        probes=np.c_[sol.y[:,[0,-1]],sol.y_events[0].T] if len(sol.y_events[0]) else sol.y[:,[0,-1]]
        minimum=min(minimum,float(np.linalg.norm(probes[:3],axis=0).min()*scales.distance_m))
        mask=(times/scales.time_s>=left)&(times/scales.time_s<=right)
        output[:,mask]=sol.sol(times[mask]/scales.time_s)
        y=sol.y[:,-1]
    rv=scales.dimensional_state(output[:6].T)
    # Preserve the authoritative seam exactly. Dense interpolation at t=0
    # followed by normalization can shift its last bits; repeated long spirals
    # then start from different initial states despite identical input files.
    rv[0]=np.asarray(initial_state_si,dtype=float)
    output[6,0]=1.
    return dict(t_s=times,relative_state_si=rv,mass_kg=output[6]*initial_mass_kg,
                thrust_N=np.where(times>=burn_start_s,thrust_N,0.),minimum_radius_m=minimum,
                final_elements=elements(rv[-1],orbit.mu_m3_s2))
