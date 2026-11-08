"""Earth-centered lunar boundary states and continuation of the IRT seed."""
from copy import deepcopy
import numpy as np
from .data import Scales,MU_EARTH,DAY_S
from .gravity import MU_MOON
from .data import Trajectory


def orbit_frame(state):
    radial=state[:3]/np.linalg.norm(state[:3])
    normal=np.cross(state[:3],state[3:]);normal/=np.linalg.norm(normal)
    return radial,np.cross(normal,radial),normal


def lunar_boundary(mission,eph):
    spec=mission.lunar
    radius=float(spec.get('parking_radius_m',150e6))
    lunar_radius=float(spec.get('arrival_radius_m',20e6))
    if radius<=6578136.3 or lunar_radius<=1837400.:
        raise ValueError('Parking/arrival orbit intersects the physical body or minimum clearance')
    moon0=eph.state('Moon',mission.launch_jd,'Earth')
    moon1=eph.state('Moon',mission.arrival_jd,'Earth')
    er,et,en=orbit_frame(moon0)
    phase=np.deg2rad(spec.get('parking_phase_deg',-60.))
    r0=radius*(np.cos(phase)*er+np.sin(phase)*et)
    v0=np.sqrt(MU_EARTH/radius)*(-np.sin(phase)*er+np.cos(phase)*et)
    er,et,en=orbit_frame(moon1)
    phase=np.deg2rad(spec.get('arrival_phase_deg',180.))
    offset=lunar_radius*(np.cos(phase)*er+np.sin(phase)*et)
    relative_v=np.sqrt(MU_MOON/lunar_radius)*(-np.sin(phase)*er+np.cos(phase)*et)
    # An instantaneous osculating circular Moon-relative endpoint, not a claim
    # of a permanently closed/stable orbit in the full third-body model.
    return np.r_[r0,v0],moon1+np.r_[offset,relative_v],Scales(radius,MU_EARTH)


def lunar_presentation(mission,eph,initial,target):
    r0=initial[:3]
    er=r0/np.linalg.norm(r0);et=initial[3:]/np.linalg.norm(initial[3:])
    angle=np.linspace(0,2*np.pi,500)
    parking=np.linalg.norm(r0)*(np.cos(angle)[:,None]*er+np.sin(angle)[:,None]*et)
    moon_orbit=eph.state('Moon',mission.launch_jd+np.linspace(0,27.321661,700),'Earth')[:,:3]
    moon=eph.state('Moon',mission.arrival_jd,'Earth')
    er,et,en=orbit_frame(moon)
    radius=float(mission.lunar.get('arrival_radius_m',20e6))
    arrival=moon[:3]+radius*(np.cos(angle)[:,None]*er+np.sin(angle)[:,None]*et)
    arrays=dict(departure_orbit_m=parking,target_orbit_m=moon_orbit,arrival_orbit_m=arrival)
    meta=dict(departure_quantity='parking_orbit_delta_v',
              title='Околоземная орбита → Луна: ИРТ',
              overlays=[dict(array='departure_orbit_m',label='Опорная околоземная орбита',linestyle=':',color='.8'),
                        dict(array='target_orbit_m',label='Орбита Луны',linestyle='-.',color='.65'),
                        dict(array='arrival_orbit_m',label='Осцулирующая орбита у Луны',linestyle=':',color='.75')],
              markers=[dict(label='Старт с околоземной орбиты',r_m=initial[:3].tolist()),
                       dict(label='Луна, прибытие',r_m=moon[:3].tolist(),color='#df1111',role='target'),
                       dict(label='Целевое состояние',r_m=target[:3].tolist(),hollow=True)])
    return arrays,meta


def solve_lunar_irt(mission,output,resume=False):
    from pathlib import Path
    from time import perf_counter
    from scipy.integrate import solve_bvp,simpson
    from .irt import solve_irt,rhs
    from .verification import verify_irt
    from .gravity import prepare_lunar_ephemerides,Gravity
    from .continuation import continue_parameter
    output=Path(output)
    if resume and (output/'two_body/trajectory.json').exists():
        seed=Trajectory.load(output/'two_body')
        diagnostics=dict(status='restored_seed')
    else:
        seed,diagnostics=solve_irt(mission)
        if seed is None:return None,diagnostics
        check=verify_irt(seed)
        if not check['passed']:return None,dict(status='initial_failed',verification=check)
        seed.metadata.update(status='verified_extremal',verification=check)
        seed.save(output/'two_body')
        seed=Trajectory.load(output/'two_body')
    scales=Scales(**seed.metadata['scales'])
    full_spec=prepare_lunar_ephemerides(mission,scales)
    initial=deepcopy(seed)
    initial.metadata['gravity_spec']=dict(full_spec,perturbation_scale=0.)
    initial.metadata['model']='IRT Earth-Moon-Sun point-mass gravity continuation'
    start=scales.normalize_state(seed.metadata['initial_state_si'])
    target=scales.normalize_state(seed.metadata['target_state_si'])
    def correct(s,previous,deadline):
        from .data import write_json
        specification=dict(full_spec,perturbation_scale=s)
        gravity=Gravity(specification)
        times=previous.arrays['t_s']/scales.time_s
        rv=scales.normalize_state(np.c_[previous.arrays['r_m'],previous.arrays['v_m_s']])
        guess=np.vstack([rv.T,previous.arrays['costates'].T])
        deadline=min(deadline,perf_counter()+float(mission.solver.get('lunar_attempt_s',20)))
        def ode(t,y):
            if perf_counter()>deadline:raise TimeoutError('Lunar IRT correction budget reached')
            return rhs(t,y,gravity)
        def bc(a,b):
            return np.r_[a[:6]-start,b[:3]-target[:3],b[3:6]-target[3:] if mission.mode=='rendezvous' else b[9:12]]
        mesh,iterate=times,guess
        reasons=[]
        for tolerance in (2e-9,2e-10,2e-11):
            sol=solve_bvp(ode,bc,mesh,iterate,tol=tolerance,max_nodes=12000)
            if not sol.success:raise RuntimeError(sol.message)
            y=sol.sol(times)
            rv=scales.dimensional_state(y[:6].T)
            m=deepcopy(seed.metadata);a={k:v.copy() for k,v in seed.arrays.items()}
            a.update(r_m=rv[:,:3],v_m_s=rv[:,3:],costates=y[6:12].T,
                     acceleration_m_s2=y[9:12].T*scales.acceleration_m_s2)
            m.update(gravity_spec=specification,model='IRT Earth-Moon-Sun point masses',
                     costates_initial=y[6:12,0].tolist(),status='solved_extremal',
                     functional_dimensionless=float(simpson(.5*np.sum(y[9:12]**2,axis=0),x=times)))
            result=Trajectory(m,a).validate()
            check=verify_irt(result)
            if check['passed']:
                result.metadata.update(status='verified_extremal',verification=check)
                return result
            mesh,iterate=sol.x,sol.y
            reasons.append(str(check))
        raise RuntimeError('Independent lunar replay failed: '+'; '.join(reasons))
    profile=dict(stage='lunar_gravity',mission=mission.to_dict(),source_arrays_sha256=seed.metadata['arrays_sha256'],
                 ephemeris_sha256=full_spec['ephemeris_sha256'],budget_s=mission.solver.get('lunar_budget_s',150),
                 min_step=1e-4,max_step=.2)
    result,checkpoint=continue_parameter(initial,output/'gravity',correct,profile=profile,
                                         resume=resume and (output/'gravity/continuation.json').exists())
    diagnostics.update(status='solved_extremal' if checkpoint['status']=='completed_stage' else 'partial',
                       gravity_status=checkpoint['status'],reached_gravity=checkpoint['reached_parameter'],
                       gravity_history=checkpoint['history'])
    return result,diagnostics
