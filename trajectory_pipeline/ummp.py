"""Continue a verified physical PSI to the historical UMMP engine."""
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.integrate import quad, solve_ivp

from .bangbang import solve_bangbang
from .bounded import canonical, verify_bounded
from .bounded_model import boundary_residual, origin_and_boundary
from .continuation import continue_parameter
from .contract import audit_configuration, digest
from .data import DAY_S, Scales, Trajectory, write_json
from .kiam_verification import verify_kiam_psi
from .problem import departure_speed_limit
from .ummp_model import UmmpEngine, UmmpModel


def _model(meta, fraction):
    mission = meta['mission']
    hardware = mission['spacecraft']
    return UmmpModel(Scales(**meta['scales']), mission['mass_kg'], hardware['thrust_N'],
                     hardware['exhaust_velocity_m_s'], fraction)


def _profiles(model, times, y, throttle):
    radius = np.linalg.norm(y[:3], axis=0)
    power, *_ = model.engine.performance(times*model.scales.time_s, radius*model.scales.distance_m)
    force, flow, _, _ = model.coefficients(times, radius)
    thrust = force*model.mass_kg*model.scales.acceleration_m_s2
    flow = flow*model.mass_kg/model.scales.time_s
    primer = y[10:13]
    direction = primer/np.maximum(np.linalg.norm(primer, axis=0), 1e-15)
    return dict(power_W=power, available_thrust_N=thrust, thrust_N=thrust*throttle,
                available_mass_flow_kg_s=flow, mass_flow_kg_s=flow*throttle,
                acceleration_m_s2=(force*throttle/y[6]*direction).T*model.scales.acceleration_m_s2)


def assemble_ummp(source, model, times, y, face, stage, extra, throttle_override):
    meta = dict(source.metadata)
    for key in ('bounded_model', 'hardware_limit_reached', 'parameter_audit', 'kiam_verification',
                'arrays_sha256', 'verification'):
        meta.pop(key, None)
    meta.update(extra)
    scales = model.scales
    rv = scales.dimensional_state(y[:6].T)
    body, _ = origin_and_boundary(source, scales)
    delta = rv[0,3:]-scales.dimensional_state(body)[3:]
    mission = meta['mission']
    meta.update(stage=stage, status='solved_extremal',
                model='historical UMMP power law with full fuel-optimal costates',
                title=f"{mission['departure']} → {mission['target']}: УММП {mission['mass_kg']:g} кг",
                ummp=dict(fraction=model.fraction, engine=asdict(model.engine),
                          source_psi_arrays_sha256=source.metadata['arrays_sha256']),
                initial_state_si=rv[0].tolist(), costates_initial=y[7:,0].tolist(),
                functional_dimensionless=float(model.fuel_weight*(1-y[6,-1])),
                costate_convention='dimensionless [p_r,p_v,p_m] for remaining mass; fuel objective weighted by baseline c/VU',
                departure=dict(mode=mission['departure_mode'], bound_active=face=='active',
                               vector_m_s=delta.tolist(), norm_m_s=float(np.linalg.norm(delta)),
                               bound_m_s=departure_speed_limit(mission)))
    overlays = {'departure_orbit_m', 'target_orbit_m', *(item['array'] for item in meta.get('overlays',[]))}
    arrays = {key: value for key,value in source.arrays.items() if key in overlays}
    arrays.update(t_s=times*scales.time_s, r_m=rv[:,:3], v_m_s=rv[:,3:],
                  mass_kg=y[6]*model.mass_kg, costates=y[7:].T, throttle=throttle_override,
                  active=throttle_override>0, switching_function=model.switching(y,times),
                  **_profiles(model,times,y,throttle_override))
    return Trajectory(meta,arrays).validate()


def _replay_rhs(t, y, model, on):
    # Separate canonical replay with the gravity Jacobian and a radial engine
    # gradient, using the same declared hardware law.
    r,v,m,pr,pv,pm = y[:3],y[3:6],y[6],y[7:10],y[10:13],y[13]
    radius = np.linalg.norm(r)
    radial = r/radius
    jacobian = (3*np.outer(radial,radial)-np.eye(3))/radius**3
    force, flow, df, dq = model.coefficients(t,radius)
    norm = np.linalg.norm(pv)
    thrust = on*force/m
    d_hamiltonian_dr = on*(df*norm/m-dq*(model.fuel_weight+pm))
    return np.r_[v, -radial/radius**2+thrust*pv/max(norm,1e-15), -on*flow,
                 -jacobian.T@pv-d_hamiltonian_dr*radial, -pr, thrust*norm/m]


def verify_ummp(trajectory, deadline=np.inf):
    meta, arrays = trajectory.metadata, trajectory.arrays
    fraction = meta['ummp']['fraction']
    if not 0 < fraction <= 1 or meta['ummp']['engine'] != asdict(UmmpEngine()):
        raise ValueError('Invalid historical UMMP model configuration')
    model = _model(meta,fraction)
    scales = model.scales
    audit = audit_configuration(trajectory)
    audit['scope'] = 'mission and PSI baseline; UMMP hardware verified separately'
    times = arrays['t_s']/scales.time_s
    switches = np.asarray(meta['switch_times_s'])/scales.time_s
    edges = np.r_[0,switches,times[-1]]
    first = meta['initial_throttle']
    if first not in (0.,1.) or np.any(np.diff(edges)<=0):
        raise ValueError('Invalid UMMP switch schedule')
    flags = np.where(np.arange(len(edges)-1)%2==0,first,1-first)
    stored = canonical(trajectory,model)
    state = stored[:,0].copy()
    replay = np.empty_like(stored)
    sign_error = switch_error = used = 0.
    min_power = np.inf
    for i,(left,right,on) in enumerate(zip(edges[:-1],edges[1:],flags)):
        def ode(t,y):
            if perf_counter()>deadline:
                raise TimeoutError('Independent UMMP replay budget reached')
            return _replay_rhs(t,y,model,on)
        sol = solve_ivp(ode,(left,right),state,method='LSODA',rtol=2e-12,atol=2e-14,
                        dense_output=True,max_step=5*DAY_S/scales.time_s)
        if not sol.success:
            raise RuntimeError('Independent UMMP integration failed')
        state = sol.y[:,-1]
        mask = (times>=left)&(times<=right)
        replay[:,mask] = sol.sol(times[mask])
        probes = np.unique(np.r_[times[mask], np.linspace(left,right,max(41,int((right-left)*scales.time_s/DAY_S)+2))])
        states = sol.sol(probes)
        switch = model.switching(states,probes)/model.a_max
        sign_error = max(sign_error,float(np.max(-switch if on else switch)))
        if i<len(switches):
            switch_error = max(switch_error,abs(float(switch[-1])))
        power = model.engine.performance(probes*scales.time_s,np.linalg.norm(states[:3],axis=0)*scales.distance_m)[0]
        min_power = min(min_power,float(np.min(power)))
        if on:
            used += quad(lambda t:model.coefficients(t,np.linalg.norm(sol.sol(t)[:3]))[1],
                         left,right,epsabs=1e-9,limit=120)[0]
    if min_power <= model.engine.minimum_power_W:
        raise ValueError('UMMP power cutoff reached; hybrid costate matching at 200 W is outside this solver')

    mission = meta['mission']
    _,target = origin_and_boundary(trajectory,scales)
    dr = float(np.linalg.norm(state[:3]-target[:3])*scales.distance_m)
    dv = float(np.linalg.norm(state[3:6]-target[3:])*scales.velocity_m_s)
    replay_position = float(np.max(np.linalg.norm(replay[:3]-stored[:3],axis=0))*scales.distance_m)
    replay_velocity = float(np.max(np.linalg.norm(replay[3:6]-stored[3:6],axis=0))*scales.velocity_m_s)
    face = 'active' if meta['departure']['bound_active'] else 'free'
    bc = boundary_residual(replay[:,0],state,trajectory,scales,model,face,kkt=True)
    bc_error = float(np.linalg.norm(bc))
    p_tol,v_tol = mission['position_tolerance_m'],mission['velocity_tolerance_m_s']
    passed = max(dr,replay_position)<=p_tol and replay_velocity<=v_tol
    passed &= dv<=v_tol if mission['mode']=='rendezvous' else np.linalg.norm(state[10:13])<1e-8
    passed &= bc_error<max(1e-8,2*p_tol/scales.distance_m,2*v_tol/scales.velocity_m_s)
    if mission['departure_mode']=='bounded_norm':
        body,_ = origin_and_boundary(trajectory,scales)
        excess = replay[3:6,0]-body[3:]
        passed &= np.linalg.norm(excess)*scales.velocity_m_s<=departure_speed_limit(mission)+v_tol
        if face=='active':
            passed &= np.dot(replay[10:13,0],excess)>=-1e-9
    expected_throttle = flags[np.searchsorted(switches,times,side='right')]
    profiles = _profiles(model,times,stored,expected_throttle)
    passed &= np.array_equal(arrays['throttle'],expected_throttle)
    for name, profile in profiles.items():
        passed &= np.allclose(arrays[name],profile,rtol=1e-8,atol=1e-11)
    mass = model.mass_kg
    fuel = float(mass*(1-state[6]))
    mass_error = float(np.max(np.abs(replay[6]-stored[6]))*mass)
    mass_balance = abs(fuel-used*mass)
    minimum = float(np.min(replay[6])*mass)
    passed &= minimum>=mission['spacecraft']['dry_mass_kg']-1e-5 and mass_error<1e-4 and mass_balance<1e-4
    passed &= sign_error<1e-6 and switch_error<1e-6 and abs(state[13])<1e-8
    return dict(passed=bool(passed), method='independent segmented LSODA and quadrature of compensated mass flow',
                parameter_audit=audit, position_residual_m=dr, velocity_residual_m_s=dv,
                replay_position_error_m=replay_position, replay_velocity_error_m_s=replay_velocity,
                canonical_boundary_residual=bc_error, terminal_mass_costate=float(state[13]),
                switching_sign_violation=sign_error,
                switching_node_residual=switch_error, minimum_mass_kg=minimum, fuel_kg=fuel,
                mass_replay_error_kg=mass_error, mass_balance_error_kg=mass_balance,
                minimum_available_power_W=min_power, maximum_thrust_N=float(np.max(arrays['thrust_N'])))


def run_ummp(source, output, *, resume=False):
    meta = source.metadata
    mission = meta.get('mission',{})
    if (meta.get('stage')!='psi' or meta.get('status')!='verified_extremal'
        or meta.get('center','').lower()!='sun' or meta.get('gravity_spec') is not None
        or meta.get('bounded_model',{}).get('gravity_spec') is not None
        or 'switch_times_s' not in meta):
        raise ValueError('UMMP requires a verified exact heliocentric PSI with central solar gravity')
    audit_configuration(source,require_final=True)
    if not verify_bounded(source)['passed'] or not verify_kiam_psi(source)['passed']:
        raise ValueError('Source PSI failed independent replay')
    settings = mission['solver']
    profile = dict(stage='ummp', source_metadata_sha256=digest(meta), engine=asdict(UmmpEngine()),
                   budget_s=float(settings.get('ummp_budget_s',240)), min_step=.001, max_step=.25)
    attempt_budget = float(settings.get('ummp_attempt_s',25))

    def correct(fraction, previous, deadline):
        stage = 'ummp' if fraction==1 else 'ummp_transition'
        return solve_bangbang(source,previous,_model(meta,fraction),
                              min(deadline,perf_counter()+attempt_budget),stage,
                              assemble_result=assemble_ummp,verify_result=verify_ummp)

    result,state = continue_parameter(source,output,correct,profile=profile,resume=resume)
    summary = dict(status=state['status'],phase='ummp_engine_law',reached_fraction=state['reached_parameter'],
                   last_result=state['last_point'],stop_reason=state['stop_reason'],
                   verification=result.metadata.get('verification'))
    if state['status']=='completed_stage':
        check = verify_ummp(result)
        if not check['passed'] or result.metadata['ummp']['fraction']!=1:
            raise ValueError('Saved final UMMP result failed admission')
    write_json(Path(output)/'summary.json',summary)
    return result,summary
