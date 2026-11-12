"""Event-resolved transverse capture. Primary uses longitude and momentum;
independent replay uses time and angular rate. All switches carry physical time.
"""
from dataclasses import asdict
import math
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from .data import Scales, DAY_S
from .capture_control import CaptureControl


def policy_margin(control, r, u, h, phi):
    if control.mode == 'continuous':
        return 1.
    ecos, esin = h*h/r-1., u*h
    e = math.hypot(ecos, esin)
    width = control.half_width_rad + control.eccentricity_slope_rad*e
    if not 0 < width <= math.pi:
        raise ValueError('capture_control: width outside (0, pi] on encountered orbit')
    if width == math.pi:
        return 1.
    if control.phase_reference == 'periapsis':
        if e < control.circular_eccentricity:
            raise ValueError('capture_control: undefined periapsis; use fixed_axis for near-circular orbits')
        phase = math.atan2(esin, ecos)
    else:
        phase = phi
    return width-abs(math.remainder(phase-control.phase_offset_rad, 2*math.pi))


def _switch(margin, start, active):
    def event(t, y):
        if abs(t-start) < 1e-11:
            return 1e-10 if active else -1e-10
        return margin(t, y)
    event.terminal = True
    event.direction = -1 if active else 1
    return event


def _width_step(control):
    # Resolve angular windows even when the orbital timescale changes greatly.
    # Affine windows additionally require valid widths at every evaluation.
    widths=(control.half_width_rad,control.half_width_rad+control.eccentricity_slope_rad)
    if control.mode=='continuous' or widths==(math.pi,math.pi):return .15
    return min(.15,.3*min(min(widths),math.pi-max(widths)))


def backward_angular_capture(orbit, final_mass, thrust, exhaust, control, max_days):
    from .planetary_capture import elements
    orbit.validate();control=CaptureControl(**control).validate()
    if min(final_mass, thrust, exhaust, max_days)<=0 or not np.isfinite([final_mass,thrust,exhaust,max_days]).all():
        raise ValueError('Capture mass, engine and duration must be finite and positive')
    rp=orbit.planet_radius_m+orbit.periapsis_altitude_m
    ra=orbit.planet_radius_m+orbit.apoapsis_altitude_m
    scale=Scales(rp,orbit.mu_m3_s2);join=orbit.interface_radius_m/rp
    acceleration=thrust/final_mass/scale.acceleration_m_s2
    flow=thrust*scale.time_s/(final_mass*exhaust)
    # y = r, radial speed, angular momentum, remaining mass, physical time.
    y=np.array([1.,0.,np.sqrt(2*ra/(rp+ra)),1.,0.]);angle=0.
    margin=lambda phi,z:policy_margin(control,z[0],z[1],z[2],phi)
    active=margin(angle,y)>=0
    pieces=[]
    for _ in range(100000):
        def rhs(phi,z):
            r,u,h,m,t=z;dt=r*r/h
            return np.array([u,h*h/r**3-1/r**2,-float(active)*acceleration*r/m,-float(active)*flow,1.])*dt
        def interface(phi,z):
            r,u,h=z[:3];energy=(u*u+(h/r)**2)/2-1/r
            if energy>=0:return 1e6
            e=math.hypot(h*h/r-1,u*h)
            return -(1+e)/(2*energy)-join
        interface.terminal=True;interface.direction=1
        def duration(phi,z):return z[4]+max_days*DAY_S/scale.time_s
        duration.terminal=True;duration.direction=-1
        switch=_switch(margin,angle,active)
        end=angle-2*math.pi
        sol=solve_ivp(rhs,(angle,end),y,method='DOP853',rtol=2.3e-14,atol=2e-15,
                      max_step=_width_step(control),events=(interface,duration,switch),dense_output=True)
        if not sol.success:raise RuntimeError('capture_backward_integration: '+sol.message)
        pieces.append((sol,active))
        delta=abs(sol.t[-1]-angle);angle=float(sol.t[-1]);y=sol.y[:,-1]
        if len(sol.t_events[0]):break
        if len(sol.t_events[1]):raise RuntimeError('capture_duration_limit: backward capture did not reach interface')
        if len(sol.t_events[2]):
            if delta<1e-9:raise RuntimeError('capture_switch_chatter: unresolved angular boundary')
            active=not active
    else:raise RuntimeError('capture_event_limit: too many revolutions/switches')
    # The interface remains the preceding apoapsis of this osculating orbit.
    r,u,h,m,t=y;e=math.hypot(h*h/r-1,u*h);a=join/(1+e)
    nu=math.atan2(u*h,h*h/r-1);peri=angle-nu
    E=math.atan2(r*u/math.sqrt(a),1-r/a);mean=E-e*math.sin(E)
    coast=float(np.mod(mean-math.pi,2*math.pi)*a**1.5)
    duration_s=(-t+coast)*scale.time_s
    if duration_s>max_days*DAY_S:raise RuntimeError('capture_duration_limit: initial coast exceeds duration cap')
    times=[];states=[];masses=[];arcs=[]
    for sol,on in reversed(pieces):
        phis=np.linspace(sol.t[-1],sol.t[0],max(2,int(abs(sol.t[0]-sol.t[-1])/.06)+2))
        z=sol.sol(phis);r,u,h=z[:3]
        rv=np.c_[r*np.cos(phis),r*np.sin(phis),np.zeros(len(phis)),
                 u*np.cos(phis)-h/r*np.sin(phis),u*np.sin(phis)+h/r*np.cos(phis),np.zeros(len(phis))]
        ts=(z[4]-t+coast)*scale.time_s
        times.extend(ts);states.extend(rv);masses.extend(z[3]*final_mass)
        arcs.append(dict(start_s=float(ts[0]),end_s=float(ts[-1]),active=bool(on)))
    coast_t=np.linspace(0,coast, max(2,int(coast/(a**1.5)*40)+2))
    M=math.pi+coast_t/a**1.5
    anom=np.array([brentq(lambda E:E-e*math.sin(E)-mean,mean-e,mean+e,xtol=1e-14) for mean in M])
    ex=np.array([math.cos(peri),math.sin(peri),0]);ey=np.array([-math.sin(peri),math.cos(peri),0])
    rc=a*(np.cos(anom)-e)[:,None]*ex+a*np.sqrt(1-e*e)*np.sin(anom)[:,None]*ey
    vc=(-np.sin(anom)[:,None]*ex+np.sqrt(1-e*e)*np.cos(anom)[:,None]*ey)/(np.sqrt(a)*(1-e*np.cos(anom)))[:,None]
    times=np.r_[coast_t[:-1]*scale.time_s,times];states=np.vstack([np.c_[rc,vc][:-1],states]);masses=np.r_[np.full(len(coast_t)-1,m*final_mass),masses]
    keep=np.r_[np.diff(times)>1e-6,True];times=times[keep];states=scale.dimensional_state(states[keep]);masses=masses[keep]
    times[0]=0.;times[-1]=duration_s
    arcs=merge_arcs(([dict(start_s=0.,end_s=coast*scale.time_s,active=False)] if coast>0 else [])+arcs)
    return dict(t_s=times,relative_state_si=states,mass_kg=masses,thrust_N=thrust*schedule_throttle(times,arcs),
                burn_start_s=coast*scale.time_s,duration_s=duration_s,entry_mass_kg=float(masses[0]),final_mass_kg=final_mass,
                control=asdict(control),reference_axis=[1.,0.,0.],arcs=arcs,
                active_duration_s=sum(a['end_s']-a['start_s'] for a in arcs if a['active']),
                final_elements=elements(states[-1],orbit.mu_m3_s2),entry_elements=elements(states[0],orbit.mu_m3_s2))


def merge_arcs(arcs):
    result=[]
    for arc in arcs:
        if arc['end_s']-arc['start_s']<=1e-9:continue
        if result and result[-1]['active']==arc['active']:
            result[-1]['end_s']=arc['end_s']
        else:result.append(dict(arc))
    return result


def schedule_throttle(times,arcs):
    index=np.searchsorted([a['start_s'] for a in arcs],times,side='right')-1
    return np.array([a['active'] for a in arcs],dtype=float)[np.maximum(index,0)]


def forward_angular_capture(orbit,state,mass,thrust,exhaust,burn_start,duration,control,reference_axis,*,sample_times=None):
    """Independent time-domain angular-rate replay; re-detect all switches.

    No backward event list is used as a forcing schedule.
    """
    from .planetary_capture import elements
    control=CaptureControl(**control).validate();orbit.validate()
    if not np.isfinite([mass,thrust,exhaust,burn_start,duration]).all() or min(mass,thrust,exhaust,duration)<=0 or not 0<=burn_start<duration:
        raise ValueError('Invalid forward capture mass, engine or duration')
    if sample_times is not None:
        samples=np.asarray(sample_times)
        if samples.ndim!=1 or not np.isfinite(samples).all() or np.any(samples<0) or np.any(samples>duration):
            raise ValueError('Capture samples must lie within the propagated interval')
    scale=Scales(orbit.planet_radius_m+orbit.periapsis_altitude_m,orbit.mu_m3_s2)
    if np.shape(state)!=(6,) or np.shape(reference_axis)!=(3,) or not np.isfinite(np.r_[state,reference_axis]).all():
        raise ValueError('Invalid capture state or reference axis')
    rv=scale.normalize_state(np.asarray(state));rvec,vvec=rv[:3],rv[3:]
    r=np.linalg.norm(rvec);normal=np.cross(rvec,vvec)
    if r<=0 or np.linalg.norm(normal)<=0:raise ValueError('Capture requires a nonradial orbit')
    normal/=np.linalg.norm(normal)
    ex=np.asarray(reference_axis,dtype=float);ex=ex-normal*np.dot(ex,normal)
    if np.linalg.norm(ex)<1e-14:raise ValueError('Reference axis has no orbital-plane projection')
    ex/=np.linalg.norm(ex);ey=np.cross(normal,ex)
    phi=math.atan2(np.dot(rvec,ey),np.dot(rvec,ex));u=np.dot(rvec,vvec)/r;w=np.linalg.norm(np.cross(rvec,vvec))/r**2
    y=np.array([r,u,w,phi,1.]);start=0.;stop=duration/scale.time_s;coast=burn_start/scale.time_s
    acceleration=thrust/mass/scale.acceleration_m_s2;flow=thrust*scale.time_s/(mass*exhaust)
    margin=lambda t,z:policy_margin(control,z[0],z[1],z[2]*z[0]**2,z[3])
    pieces=[];arcs=[];minimum=r
    active=False if coast>0 else margin(start,y)>=0
    for _ in range(100000):
        coast_phase=start<coast-1e-12
        right=min(coast,stop) if coast_phase else stop
        def rhs(t,z):
            r,u,w,phi,m=z
            return [u,r*w*w-1/r**2,-2*u*w/r-float(active)*acceleration/(m*r),w,-float(active)*flow]
        switch=_switch(margin,start,active)
        def peri(t,z):return z[1]
        peri.direction=1
        # Local dynamical step prevents missing multiple angular crossings.
        r,u,w=y[:3];energy=(u*u+(w*r)**2)/2-1/r
        h=w*r*r;e=math.hypot(h*h/r-1,u*h);rp=h*h/(1+e)
        step=np.inf if coast_phase else _width_step(control)*(-1/(2*energy))**1.5 if energy<0 else _width_step(control)*r*r/h
        sol=solve_ivp(rhs,(start,right),y,method='DOP853',rtol=2.3e-14,atol=2e-15,max_step=step,
                      events=(peri,) if coast_phase else (peri,switch),dense_output=True)
        if not sol.success:raise RuntimeError('capture_forward_integration: '+sol.message)
        end=float(sol.t[-1]);pieces.append((start,end,sol));arcs.append(dict(start_s=start*scale.time_s,end_s=end*scale.time_s,active=bool(active)))
        minimum=min(minimum,float(sol.y[0].min()),float(sol.y_events[0][:,0].min()) if len(sol.y_events[0]) else np.inf)
        if end>=stop:break
        if end-start<1e-11:raise RuntimeError('capture_switch_chatter: forward event made no progress')
        start=end;y=sol.y[:,-1]
        active=(margin(start,y)>=0) if coast_phase else not active
    else:raise RuntimeError('capture_event_limit: forward replay exhausted event limit')
    arcs=merge_arcs(arcs)
    times=np.unique(np.r_[0.,duration,sample_times if sample_times is not None else np.linspace(0,duration,2500),
                           [a['start_s'] for a in arcs]])
    # Preserve caller samples exactly: independent verification indexes them.
    result=np.empty((5,len(times)))
    for left,right,sol in pieces:
        mask=(times>=left*scale.time_s-1e-7)&(times<=right*scale.time_s+1e-7)
        result[:,mask]=sol.sol(np.clip(times[mask]/scale.time_s,left,right))
    r,u,w,phi,m=result
    er=np.cos(phi)[:,None]*ex+np.sin(phi)[:,None]*ey;et=-np.sin(phi)[:,None]*ex+np.cos(phi)[:,None]*ey
    states=scale.dimensional_state(np.c_[r[:,None]*er,u[:,None]*er+(r*w)[:,None]*et]);states[0]=state
    return dict(t_s=times,relative_state_si=states,mass_kg=m*mass,thrust_N=thrust*schedule_throttle(times,arcs),
                minimum_radius_m=minimum*scale.distance_m,arcs=arcs,
                active_duration_s=sum(a['end_s']-a['start_s'] for a in arcs if a['active']),
                final_elements=elements(states[-1],orbit.mu_m3_s2))
