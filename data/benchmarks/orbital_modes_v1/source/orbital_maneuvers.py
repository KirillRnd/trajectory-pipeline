"""Local orbital maneuvers with explicit mass reference and impulse events."""
from dataclasses import asdict
import math
import numpy as np
from scipy.integrate import solve_ivp
from .data import Scales,DAY_S
from .parking_departure import ParkingDeparture,outgoing_hyperbola,verify_outgoing
from .planetary_capture import CaptureOrbit,orient_capture,elements


def validate_maneuvers(spec):
    if not isinstance(spec,dict) or set(spec)!={'departure','arrival'}:raise ValueError('orbital_maneuvers needs exactly departure and arrival')
    d,a=spec['departure'],spec['arrival']
    if not isinstance(d,dict) or not isinstance(a,dict):raise ValueError('Orbital modes must be objects')
    if d.get('kind') not in ('spiral','impulse') or a.get('kind') not in ('spiral','impulse'):raise ValueError('Orbital kind must be spiral or impulse')
    if set(d)-{'kind',*ParkingDeparture.__dataclass_fields__}:raise ValueError('Unknown orbital departure parameter')
    ParkingDeparture(**{k:v for k,v in d.items() if k!='kind'}).validate()
    required=set(CaptureOrbit.__dataclass_fields__)
    extra={'kind','plane','interface_side'}|({'excess_velocity_m_s','exhaust_velocity_m_s'} if a['kind']=='impulse' else set())
    if not required<=set(a) or set(a)-required-extra:raise ValueError('Missing or unknown orbital arrival parameter')
    if any(isinstance(a[k],bool) or not isinstance(a[k],(int,float)) or not np.isfinite(a[k]) for k in required):raise ValueError('Arrival dimensions must be finite numbers')
    CaptureOrbit(**{k:a[k] for k in required}).validate()
    if a.get('plane','planet_orbit')!='planet_orbit' or a.get('interface_side','sunward')!='sunward':raise ValueError('Arrival supports the planet plane and sunward interface')
    if a['kind']=='impulse':
        for k in ('excess_velocity_m_s','exhaust_velocity_m_s'):
            x=a.get(k)
            if isinstance(x,bool) or not isinstance(x,(int,float)) or not np.isfinite(x) or x<=0:raise ValueError('Impulse arrival needs positive '+k)
    return spec


def spiral_departure(spec,initial_mass_kg,thrust_N,exhaust_velocity_m_s,*,max_days=1500.,rtol=3e-13):
    """Exact central-field polar equations, positive transverse thrust and -F/c.

    Radius, radial speed and angular momentum decouple from longitude. This
    resolves the small radial oscillations without propagating large Cartesian
    Kepler velocities through thousands of low-altitude revolutions.
    """
    spec.validate();rp=spec.planet_radius_m+spec.parking_altitude_m
    scales=Scales(rp,spec.mu_m3_s2)
    A=thrust_N/initial_mass_kg/scales.acceleration_m_s2
    q=thrust_N*scales.time_s/(initial_mass_kg*exhaust_velocity_m_s)
    if min(initial_mass_kg,thrust_N,exhaust_velocity_m_s)<=0:raise ValueError('Spiral mass and engine must be positive')
    def rhs(t,y):
        r,u,h,L,m=y
        if m<=0:raise ValueError('Departure exhausted its mass before reaching the interface')
        return [u,h*h/r**3-1/r**2,A*r/m,h/r**2,-q]
    def interface(t,y):return y[0]-spec.interface_radius_m/rp
    interface.terminal=True;interface.direction=1
    end=min(max_days*DAY_S/scales.time_s,.99/q)
    sol=solve_ivp(rhs,(0,end),[1.,0.,1.,0.,1.],method='DOP853',rtol=rtol,
                  atol=[rtol/10,rtol/100,rtol/10,rtol,rtol/100],events=interface,dense_output=True)
    if not sol.success or not len(sol.t_events[0]):raise RuntimeError('Departure spiral did not reach the interface')
    # Preserve the integrator mesh; decimation would alias the many revolutions.
    times=sol.t; r,u,h,L,m=sol.y
    cs,sn=np.cos(L),np.sin(L);zeros=np.zeros(len(times))
    positions=np.c_[r*cs,r*sn,zeros]*rp
    velocities=np.c_[u*cs-h/r*sn,u*sn+h/r*cs,zeros]*scales.velocity_m_s
    state=np.c_[positions,velocities]
    state[0]=[rp,0.,0.,0.,scales.velocity_m_s,0.]
    return dict(t_s=times*scales.time_s,relative_state_si=state,mass_kg=m*initial_mass_kg,
                thrust_N=np.full(len(times),thrust_N),duration_s=float(times[-1]*scales.time_s),
                initial_mass_kg=float(initial_mass_kg),interface_mass_kg=float(m[-1]*initial_mass_kg),
                thrust_direction='prograde transverse',polar_state=sol.y.T)


def orient_departure(solution,velocity_direction,reference_normal):
    """Rotate all states by one proper rotation, preserving radial velocity."""
    y=solution['relative_state_si'];axis=y[-1,3:]/np.linalg.norm(y[-1,3:])
    normal=np.cross(y[-1,:3],y[-1,3:]);normal/=np.linalg.norm(normal)
    source=np.column_stack([axis,np.cross(normal,axis),normal])
    target_axis=np.asarray(velocity_direction,dtype=float);target_axis/=np.linalg.norm(target_axis)
    n=np.asarray(reference_normal,dtype=float).copy();n-=target_axis*np.dot(target_axis,n)
    if np.linalg.norm(n)<1e-10:
        n=np.eye(3)[np.argmin(np.abs(target_axis))];n-=target_axis*np.dot(target_axis,n)
    n/=np.linalg.norm(n)
    rotation=np.column_stack([target_axis,np.cross(n,target_axis),n])@source.T
    result=dict(solution);result['relative_state_si']=np.c_[y[:,:3]@rotation.T,y[:,3:]@rotation.T]
    result['rotation']=rotation.tolist()
    return result


def replay_departure_spiral(spec,initial_state,initial_mass,F,c,times):
    """Independent radius/angular-rate equations, LSODA (primary uses h)."""
    scale=Scales(spec.planet_radius_m+spec.parking_altitude_m,spec.mu_m3_s2)
    x=scale.normalize_state(initial_state);R=np.linalg.norm(x[:3]);ex=x[:3]/R
    normal=np.cross(x[:3],x[3:]);normal/=np.linalg.norm(normal);ey=np.cross(normal,ex)
    radial=float(x[3:]@ex);omega=float(x[3:]@ey)/R
    A=F/initial_mass/scale.acceleration_m_s2;q=F*scale.time_s/(initial_mass*c)
    def rhs(t,z):
        radius,u,w,phase,m=z
        return [u,radius*w*w-1/radius**2,A/(m*radius)-2*u*w/radius,w,-q]
    sol=solve_ivp(rhs,(0,times[-1]/scale.time_s),[R,radial,omega,0.,1.],method='LSODA',
                  rtol=3e-13,atol=3e-15,t_eval=times/scale.time_s)
    if not sol.success:raise RuntimeError('Independent departure spiral replay failed')
    r,u,w,L,m=sol.y;er=np.cos(L)[:,None]*ex+np.sin(L)[:,None]*ey
    et=-np.sin(L)[:,None]*ex+np.cos(L)[:,None]*ey
    state=np.c_[r[:,None]*er*scale.distance_m,(u[:,None]*er+(r*w)[:,None]*et)*scale.velocity_m_s]
    state[0]=initial_state
    return np.c_[state,m*initial_mass]


def incoming_impulse(spec,interface_mass_kg):
    """Incoming positive-energy conic followed by an explicit vector impulse."""
    orbit=CaptureOrbit(**{k:spec[k] for k in CaptureOrbit.__dataclass_fields__});orbit.validate()
    parking=ParkingDeparture(interface_radius_m=orbit.interface_radius_m,parking_altitude_m=orbit.periapsis_altitude_m,
                             planet_radius_m=orbit.planet_radius_m,mu_m3_s2=orbit.mu_m3_s2)
    speed=np.sqrt(spec['excess_velocity_m_s']**2+2*orbit.mu_m3_s2/orbit.interface_radius_m)
    out=outgoing_hyperbola(parking,[speed,0.,0.],[0.,0.,1.])
    rv=out['relative_state_si'][::-1].copy();rv[:,3:]*=-1
    t=out['duration_s']-out['t_s'][::-1];t[0]=0.
    return dict(t_s=t,relative_state_si=rv,mass_kg=np.full(len(t),interface_mass_kg),
                thrust_N=np.zeros(len(t)),duration_s=out['duration_s'])


def capture_impulse_event(state_before,mass_before,spec,time_s):
    """The full vector jump; capture propellant was carried through transfer."""
    orbit=CaptureOrbit(**{k:spec[k] for k in CaptureOrbit.__dataclass_fields__})
    r=state_before[:3];v=state_before[3:];R=np.linalg.norm(r)
    h=np.cross(r,v);tangent=np.cross(h,r);tangent/=np.linalg.norm(tangent)
    rp=orbit.planet_radius_m+orbit.periapsis_altitude_m;ra=orbit.planet_radius_m+orbit.apoapsis_altitude_m
    target=tangent*np.sqrt(orbit.mu_m3_s2*(2/R-2/(rp+ra)))
    jump=target-v;delta=float(np.linalg.norm(jump))
    after=mass_before*np.exp(-delta/spec['exhaust_velocity_m_s'])
    return dict(kind='arrival_impulse',time_s=float(time_s),state_before_si=np.asarray(state_before).tolist(),
                state_after_si=np.r_[r,target].tolist(),delta_v_vector_m_s=jump.tolist(),delta_v_m_s=delta,
                mass_before_kg=float(mass_before),mass_after_kg=float(after),
                propellant_kg=float(mass_before-after),exhaust_velocity_m_s=spec['exhaust_velocity_m_s'])


def replay_transverse(initial_state,initial_mass,mu,F,c,duration,sample_times,*,sign=1,burn_start=0.):
    """Independent Cartesian LSODA replay of a transverse law or coast."""
    scale=Scales(float(np.linalg.norm(initial_state[:3])),mu)
    z=np.r_[scale.normalize_state(initial_state),initial_mass]
    result=np.empty((len(sample_times),7));edges=[0.,duration] if burn_start==0 else [0.,burn_start,duration]
    for left,right in zip(edges[:-1],edges[1:]):
        active=left>=burn_start
        def ode(t,x):
            r,v=x[:3],x[3:6];R=math.sqrt(float(r@r))
            e=r/R;transverse=v-e*float(v@e);transverse/=np.linalg.norm(transverse)
            return np.r_[v,-r/R**3+(sign*F/x[6]/scale.acceleration_m_s2*transverse if active else 0.),-F/c*scale.time_s if active else 0.]
        sol=solve_ivp(ode,(left/scale.time_s,right/scale.time_s),z,method='LSODA',rtol=3e-12,atol=3e-14,dense_output=True)
        if not sol.success:raise RuntimeError('Independent local replay failed')
        mask=(sample_times>=left)&(sample_times<=right)
        result[mask]=sol.sol(sample_times[mask]/scale.time_s).T;z=sol.y[:,-1]
    result[:,:6]=scale.dimensional_state(result[:,:6]);result[0,:6]=initial_state;result[0,6]=initial_mass
    return result
