"""Reproduce the R study on saved planetary and asteroid arcs."""
import argparse
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.integrate import solve_ivp
from scipy.spatial.transform import Rotation

from . import irt
from .bangbang import solve_bangbang
from .bounded import canonical, collocate
from .bounded_model import BoundedModel
from .contract import audit_configuration, make_request
from .data import DAY_S, Scales, Trajectory, sha256, write_json
from .date_sweep import _date_context, _reference_mission, _seed
from .problem import Mission
from .kiam_verification import verify_kiam_psi
from .r_transform import costate_chart, orbital_frame, transport_costates, transport_matrix
from .verification import replay_irt


ROOT = Path('data/benchmarks')
MARS = ROOT / 'examples/earth_mars_2030_dec01_500d'
ARCS = {
    'Mars IRT': MARS / 'stage_irt/irt',
    'Mars departure': MARS / 'stage_departure/point_0004',
    'Mars Pazov': MARS / 'stage_pazov/functional/point_0003',
    'Mars mass': MARS / 'stage_psi/mass/point_0003',
    'Mars PSI': MARS / 'final',
    'Venus PSI': ROOT / 'psi/earth_venus_2032',
    'Apophis PSI': ROOT / 'psi/earth_apophis_2029',
    'Ceres mass': ROOT / 'physical_matrix_common_v1/earth_ceres_2030/stage_psi/mass/point_0004',
}
CHARTS = (None, 'rtn', 'legacy')


def frame(state, kind):
    return orbital_frame(state, kind) if kind is not None else None


def angle_cosine(state):
    r, v = state[:3], state[3:6]
    return float(np.dot(r, v) / (np.linalg.norm(r) * np.linalg.norm(v)))


def central_difference(residual, point, step):
    perturbations = np.diag(step * np.maximum(np.abs(point), 1.))
    return np.column_stack([(residual(point+d)-residual(point-d))/(2*h)
                            for d, h in zip(perturbations, perturbations.diagonal())])


def spectrum(jacobian):
    singular = np.linalg.svd(jacobian, compute_uv=False)
    return dict(sigma_max=float(singular[0]), sigma_min=float(singular[-1]),
                condition=float(singular[0]/singular[-1]) if singular[-1] > 0 else None)


def replay_tail(initial, start, stop, rhs, switches, first, model):
    # Use the saved schedule and keep its switches fixed in this local test.
    remaining = switches[(switches > start) & (switches < stop)]
    arc = np.searchsorted(switches, start, side='right')
    state = initial
    switch_errors = []
    edges = np.r_[start, remaining, stop]
    for k, (left, right) in enumerate(zip(edges[:-1], edges[1:])):
        throttle = 1-first if first is not None and (k+arc) % 2 else first
        def ode(t, y):
            return rhs(t, y, throttle=throttle) if first is not None else rhs(t, y)
        sol = solve_ivp(ode, (left, right), state, method='DOP853', rtol=2e-12, atol=2e-14)
        if not sol.success:
            raise RuntimeError(sol.message)
        state = sol.y[:, -1]
        if k < len(remaining):
            switch_errors.append(float(model.switching(state)/model.a_max))
    return state, switch_errors


def arc_study(reference, fractions):
    meta, arrays = reference.metadata, reference.arrays
    scales = Scales(**meta['scales'])
    model = BoundedModel(**meta['bounded_model']) if 'bounded_model' in meta else None
    if model is None and meta.get('gravity_spec') is not None:
        raise ValueError('IRT diagnostics require the central-field model')
    states = canonical(reference, model) if model is not None else np.c_[
        scales.normalize_state(np.c_[arrays['r_m'], arrays['v_m_s']]), arrays['costates']].T
    times = arrays['t_s']/scales.time_s
    switches = np.asarray(meta.get('switch_times_s', []))/scales.time_s
    first = meta.get('initial_throttle')
    if model is not None and model.alpha == 1 and first is None:
        raise ValueError('Exact arcs require the saved switch schedule')
    rhs = model.rhs if model is not None else irt.rhs
    pstart = 7 if model is not None and model.variable_mass else 6
    pv = slice(pstart+3, pstart+6)
    final = states[:, -1]
    rendezvous = meta['mission']['mode'] == 'rendezvous'
    results = []
    for fraction in fractions:
        node = np.argmin(np.abs(times[:-1]-fraction*times[-1]))
        state, time = states[:, node], times[node]
        phase, adjoint = state[:pstart], state[pstart:]

        def replay(phase, adjoint):
            return replay_tail(np.r_[phase, adjoint], time, times[-1], rhs, switches, first, model)

        def residual(p):
            end, events = replay(phase, p)
            diff = end-final
            return np.r_[diff[:3], diff[3:6] if rendezvous else diff[pv],
                         diff[13:] if pstart == 7 else [], events]

        coarse = central_difference(residual, adjoint, 2e-5)
        jacobian = central_difference(residual, adjoint, 1e-5)
        charts = {}
        for kind in (*CHARTS, 'angular'):
            chart = costate_chart(frame(phase[:6], kind), size=len(adjoint))
            transformed = jacobian@chart
            recovered = np.linalg.solve(chart.T, transformed.T).T
            charts[kind or 'cartesian'] = dict(**spectrum(transformed), physical_relative_error=float(
                np.linalg.norm(recovered-jacobian)/np.linalg.norm(jacobian)))

        # Chapter 3 comparison: fixed position and speed, changed direction.
        # All candidates replay the same altered physical state.
        base_end, _ = replay(phase, adjoint)
        normal = orbital_frame(phase[:6], 'rtn')[2]
        rotations = []
        for degrees in (-1., -.1, .1, 1.):
            rotation = Rotation.from_rotvec(np.deg2rad(degrees)*normal).as_matrix()
            new_phase = phase.copy()
            new_phase[3:6] = rotation@phase[3:6]
            transport = transport_matrix(phase[:6], new_phase[:6])
            angular = transport_matrix(phase[:6], new_phase[:6], 'angular')
            trials = {}
            for name, matrix in (('cartesian', np.eye(3)), ('simple_rotation', rotation),
                                 ('legacy', transport), ('angular', angular)):
                end, events = replay(new_phase, transport_costates(adjoint, matrix))
                trials[name] = dict(position_m=float(np.linalg.norm(end[:3]-base_end[:3])*scales.distance_m),
                                    velocity_m_s=float(np.linalg.norm(end[3:6]-base_end[3:6])*scales.velocity_m_s),
                                    switch_residual_norm=float(np.linalg.norm(events)))
            rotations.append(dict(degrees=degrees, cosine=angle_cosine(new_phase), trials=trials))
        results.append(dict(day=float(arrays['t_s'][node]/DAY_S), fraction=fraction, cosine=angle_cosine(phase),
                            jacobian_relative_change=float(np.linalg.norm(jacobian-coarse)/np.linalg.norm(jacobian)),
                            nominal_residual_norm=float(np.linalg.norm(residual(adjoint))),
                            charts=charts, velocity_rotation=rotations))
    return results


def irt_tail_correction(reference):
    arrays, meta = reference.arrays, reference.metadata
    scales = Scales(**meta['scales'])
    node = np.argmin(np.abs(arrays['t_s']-.5*arrays['t_s'][-1]))
    start = scales.normalize_state(np.r_[arrays['r_m'][node], arrays['v_m_s'][node]])
    end_jd = meta['epoch_jd'] + arrays['t_s'][-1]/DAY_S
    target = scales.normalize_state(Mission(**meta['mission']).ephemerides().state(meta['mission']['target'], end_jd+1, meta['center']))
    tof = (arrays['t_s'][-1]-arrays['t_s'][node])/scales.time_s
    guess = arrays['costates'][node]
    rows = {}
    for kind in CHARTS:
        costates, diag = irt.correct_shooting(start, target, tof, guess, costate_frame=frame(start, kind))
        independent = replay_irt(start, costates, np.linspace(0, tof, 101))
        errors = irt._physical_errors(independent, target, scales, 'rendezvous')
        rows[kind or 'cartesian'] = dict(**diag, **errors, independent_success=bool(independent.success))
    return rows


def pazov_correction(reference):
    previous = Trajectory.load(MARS / 'stage_pazov/functional/point_0002')
    model = BoundedModel(**reference.metadata['bounded_model'])
    scales = Scales(**reference.metadata['scales'])
    node = len(reference.arrays['t_s'])//2
    state = scales.normalize_state(np.r_[reference.arrays['r_m'][node], reference.arrays['v_m_s'][node]])
    rows = {}
    for kind in CHARTS:
        started = perf_counter()
        try:
            result = collocate(previous, previous, model, started+20, 'pazov', costate_frame=frame(state, kind))
            keys = ('collocation_nodes', 'collocation_iterations', 'corrector', 'corrector_nfev', 'verification')
            row = {key: result.metadata[key] for key in keys if key in result.metadata}
        except (ValueError, RuntimeError, TimeoutError) as exc:
            row = dict(error=str(exc))
        rows[kind or 'cartesian'] = dict(**row, seconds=perf_counter()-started)
    return rows


def psi_correction(reference, day):
    base = _reference_mission(reference)
    epoch = datetime.fromisoformat(base.launch_tdb)+timedelta(days=day)
    mission = replace(base, launch_tdb=epoch.isoformat())
    body, target, scales = mission.boundary()
    old_scales = Scales(**reference.metadata['scales'])
    old_body = np.asarray(reference.metadata['body_initial_state_si'])
    context, model = _date_context(mission, body, target, scales)
    request = make_request(mission)
    seed_errors = {}
    target_normalized = scales.normalize_state(target)
    for kind in CHARTS:
        seed, _ = _seed(reference, old_body, body, old_scales, scales, frame_kind=kind)
        initial = canonical(seed, model)[:, 0]
        switches = np.array(reference.metadata['switch_times_s'])/scales.time_s
        end, events = replay_tail(initial, 0., mission.tof_days*DAY_S/scales.time_s, model.rhs,
                                  switches, reference.metadata['initial_throttle'], model)
        seed_errors[kind or 'cartesian'] = dict(
            position_m=float(np.linalg.norm(end[:3]-target_normalized[:3])*scales.distance_m),
            velocity_m_s=float(np.linalg.norm(end[3:6]-target_normalized[3:6])*scales.velocity_m_s),
            switch_residual_norm=float(np.linalg.norm(events)))
    guess = seed  # All correctors start from the same legacy-transferred physical guess.
    rows = {}
    for kind in CHARTS:
        started = perf_counter()
        try:
            result = solve_bangbang(context, guess, model, started+15, 'psi',
                                    costate_frame=frame(scales.normalize_state(body), kind))
            audit_configuration(result, mission, request, require_final=True)
            check = verify_kiam_psi(result)
            row = dict(**result.metadata['bangbang_corrector'],
                       passed=check['passed'] and result.metadata['verification']['passed'],
                       fuel_kg=float(mission.mass_kg-result.arrays['mass_kg'][-1]),
                       switch_count=len(result.metadata['switch_times_s']))
        except (ValueError, RuntimeError, TimeoutError) as exc:
            row = dict(passed=False, error=str(exc))
        rows[kind or 'cartesian'] = dict(**row, seconds=perf_counter()-started)
    return dict(days=day, launch_tdb=epoch.isoformat(), seed_errors=seed_errors, charts=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--trajectory', type=Path, help='Analyze one saved arc without running the benchmark correctors')
    parser.add_argument('--fractions', nargs='+', type=float, default=(0., .25, .5, .75),
                        help='Fractions of elapsed arc time at which to inspect the remaining arc')
    args = parser.parse_args()
    if not all(0 <= fraction < 1 for fraction in args.fractions):
        parser.error('fractions must be in [0, 1)')
    args.output.mkdir(parents=True, exist_ok=False)
    arcs = ARCS if args.trajectory is None else {'custom': args.trajectory}
    data = {}
    for label, path in arcs.items():
        print(label, flush=True)
        reference = Trajectory.load(path)
        row = dict(path=path.as_posix(), metadata_sha256=sha256(path/'trajectory.json'),
                   arrays_sha256=reference.metadata['arrays_sha256'], nodes=arc_study(reference,args.fractions))
        if label == 'Mars IRT':
            row['correction'] = irt_tail_correction(reference)
        elif label == 'Mars Pazov':
            row['correction'] = pazov_correction(reference)
        elif label in ('Mars PSI', 'Venus PSI', 'Apophis PSI'):
            row['correction'] = [psi_correction(reference, days) for days in (1, 7, 30)]
        data[label] = row
        write_json(args.output/'results.json', data)


if __name__ == '__main__':
    main()
