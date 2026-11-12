"""Impulsive upper-stage departure from configurable circular Earth orbit.

The input is the velocity at the finite interface, not the asymptotic excess.
The orbital plane is free; its normal is chosen as close as possible to the
Earth orbital normal while containing the requested interface velocity.
"""
from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp
from .data import MU_EARTH,Scales


@dataclass(frozen=True)
class ParkingDeparture:
    interface_radius_m: float
    parking_altitude_m: float = 200000.
    planet_radius_m: float = 6378137.
    mu_m3_s2: float = MU_EARTH
    plane_mode: str = 'free'

    def validate(self):
        values=[self.interface_radius_m,self.parking_altitude_m,self.planet_radius_m,self.mu_m3_s2]
        if any(isinstance(x,(bool,str)) for x in values) or not np.isfinite(values).all() or min(values)<=0:
            raise ValueError('Parking departure dimensions must be positive finite numbers')
        if self.interface_radius_m<=self.planet_radius_m+self.parking_altitude_m:raise ValueError('Departure interface must lie above the parking orbit')
        if self.plane_mode!='free':raise ValueError('Only a freely selected parking-orbit plane is implemented')
        return self


def outgoing_hyperbola(spec,interface_velocity_m_s,reference_normal):
    spec.validate()
    velocity=np.asarray(interface_velocity_m_s,dtype=float)
    if velocity.shape!=(3,) or not np.isfinite(velocity).all():raise ValueError('Departure needs a finite velocity vector')
    speed=float(np.linalg.norm(velocity));mu=spec.mu_m3_s2
    excess2=speed*speed-2*mu/spec.interface_radius_m
    if excess2<=0:raise ValueError('Requested interface state is not an escaping hyperbola')
    rp=spec.planet_radius_m+spec.parking_altitude_m
    vp=np.sqrt(excess2+2*mu/rp);vc=np.sqrt(mu/rp)
    eccentricity=1+rp*excess2/mu;semimajor=mu/excess2
    p=rp*(1+eccentricity)
    f=np.arccos(np.clip((p/spec.interface_radius_m-1)/eccentricity,-1,1))
    local_velocity=np.array([-np.sin(f),eccentricity+np.cos(f),0.])
    local_velocity/=np.linalg.norm(local_velocity)
    axis=velocity/speed
    normal=np.asarray(reference_normal,dtype=float).copy();normal-=axis*np.dot(axis,normal)
    if np.linalg.norm(normal)<1e-10:
        normal=np.eye(3)[np.argmin(np.abs(axis))];normal-=axis*np.dot(axis,normal)
    normal/=np.linalg.norm(normal)
    source=np.column_stack([local_velocity,np.cross([0.,0.,1.],local_velocity),[0.,0.,1.]])
    rotation=np.column_stack([axis,np.cross(normal,axis),normal])@source.T
    endpoint_H=np.arccosh((spec.interface_radius_m/semimajor+1)/eccentricity)
    H=np.linspace(0,endpoint_H,1500)
    times=np.sqrt(semimajor**3/mu)*(eccentricity*np.sinh(H)-H)
    # Cartesian hyperbolic anomaly gives exact positions and velocities.
    r=semimajor*np.c_[eccentricity-np.cosh(H),np.sqrt(eccentricity**2-1)*np.sinh(H),np.zeros(len(H))]
    factor=np.sqrt(mu/semimajor)/(eccentricity*np.cosh(H)-1)
    v=factor[:,None]*np.c_[-np.sinh(H),np.sqrt(eccentricity**2-1)*np.cosh(H),np.zeros(len(H))]
    state=np.c_[r@rotation.T,v@rotation.T]
    return dict(t_s=times,relative_state_si=state,duration_s=float(times[-1]),
                delta_v_m_s=float(vp-vc),delta_v_vector_m_s=((vp-vc)*rotation[:,1]).tolist(),
                circular_velocity_m_s=(vc*rotation[:,1]).tolist(),
                periapsis_speed_m_s=float(vp),circular_speed_m_s=float(vc),
                interface_speed_m_s=speed,asymptotic_excess_m_s=float(np.sqrt(excess2)),
                orbit_normal_ecliptic=normal.tolist())


def verify_outgoing(spec,solution):
    """Independent forward propagation, not another conic reconstruction."""
    scales=Scales(spec.planet_radius_m+spec.parking_altitude_m,spec.mu_m3_s2)
    y0=scales.normalize_state(solution['relative_state_si'][0])
    def rhs(t,y):
        x,yc,z,vx,vy,vz=y
        inv=(x*x+yc*yc+z*z)**(-1.5)
        return [vx,vy,vz,-x*inv,-yc*inv,-z*inv]
    replay=solve_ivp(rhs,(0,solution['duration_s']/scales.time_s),y0,method='LSODA',
                     rtol=2e-12,atol=2e-14,t_eval=solution['t_s']/scales.time_s)
    if not replay.success:raise RuntimeError('Earth departure replay failed: '+replay.message)
    replay=scales.dimensional_state(replay.y.T)
    dr=float(np.linalg.norm(replay[:,:3]-solution['relative_state_si'][:,:3],axis=1).max())
    dv=float(np.linalg.norm(replay[:,3:]-solution['relative_state_si'][:,3:],axis=1).max())
    impulse=np.asarray(solution['delta_v_vector_m_s'])
    initial=solution['relative_state_si'][0]
    kick=float(np.linalg.norm(initial[3:]-solution['circular_velocity_m_s']-impulse))
    rp=spec.planet_radius_m+spec.parking_altitude_m
    parking_error=abs(float(np.linalg.norm(initial[:3]))-rp)
    radius_error=abs(float(np.linalg.norm(solution['relative_state_si'][-1,:3]))-spec.interface_radius_m)
    circular=np.asarray(solution['circular_velocity_m_s'])
    circular_error=abs(float(np.linalg.norm(circular))-np.sqrt(spec.mu_m3_s2/rp))
    tangent_error=abs(float(np.dot(initial[:3]/np.linalg.norm(initial[:3]),circular)))
    scalar_error=abs(float(np.linalg.norm(impulse))-solution['delta_v_m_s'])
    same_direction=float(np.dot(circular,initial[3:]))>0 and np.linalg.norm(np.cross(circular,initial[3:]))<1e-4
    end_speed=float(np.linalg.norm(solution['relative_state_si'][-1,3:]))
    excess=float(np.sqrt(max(0.,end_speed**2-2*spec.mu_m3_s2/spec.interface_radius_m)))
    values_error=max(abs(end_speed-solution['interface_speed_m_s']),abs(excess-solution['asymptotic_excess_m_s']))
    return dict(passed=bool(dr<10. and dv<.001 and kick<1e-8 and parking_error<.001 and radius_error<.001
                           and circular_error<1e-8 and tangent_error<1e-8 and scalar_error<1e-8 and same_direction and values_error<1e-8),
                replay_position_error_m=dr,replay_velocity_error_m_s=dv,impulse_vector_error_m_s=kick,
                parking_radius_error_m=parking_error,interface_radius_error_m=radius_error,
                circular_speed_error_m_s=circular_error,circular_tangency_error_m_s=tangent_error,delta_v_scalar_error_m_s=scalar_error)
