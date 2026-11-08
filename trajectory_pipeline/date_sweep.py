"""Independent date transfers of one physical PSI, with cold reruns on demand."""
import csv
from dataclasses import asdict, replace
from datetime import datetime, timedelta
from itertools import combinations
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import numpy as np

from .bangbang import solve_bangbang
from .bounded import verify_bounded
from .bounded_model import BoundedModel
from .contract import audit_configuration, configuration_hash, make_request
from .data import Scales, Trajectory, sha256, write_json
from .ephemerides import Ephemerides
from .kiam_verification import verify_kiam_psi
from .problem import Mission
from .r_transform import transport_costates, transport_matrix, transport_vector
from .runtime import runtime_environment


def _reference_mission(reference):
    mission = Mission(**reference.metadata['mission']).validate()
    unsupported = (mission.capture, mission.parking_departure, mission.orbital_maneuvers,
                   mission.lunar, mission.departure_offset_state_si, mission.arrival_offset_state_si)
    if mission.center.lower() != 'sun' or any(item is not None for item in unsupported):
        raise ValueError('sweep-psi requires a heliocentric body-to-body reference without local orbital interfaces')
    if reference.metadata.get('stage') != 'psi' or reference.metadata.get('status') != 'verified_extremal':
        raise ValueError('sweep-psi requires an accepted physical PSI reference')
    if reference.metadata['bounded_model'].get('gravity_spec') is not None:
        raise ValueError('Date transfer currently supports the central solar field')
    return mission


def _identity(path):
    return {name: sha256(path / name) for name in ('trajectory.json', 'trajectory.npz')}


def _seed(reference, old_body, new_body, old_scale, new_scale, *, frame_kind='legacy'):
    # Same convention as venus_cycle.m. Common row scales keep the frame
    # solve well conditioned without changing R_new^-1 R_ref.
    transform = (np.eye(3) if frame_kind is None else
                 transport_matrix(old_scale.normalize_state(old_body),
                                  old_scale.normalize_state(new_body), frame_kind))
    reference_arrays = reference.arrays
    arrays = {name: reference_arrays[name].copy() for name in
              ('t_s', 'r_m', 'v_m_s', 'mass_kg', 'costates', 'throttle')}
    excess = reference_arrays['v_m_s'][0] - old_body[3:]
    arrays['r_m'][0] = new_body[:3]
    arrays['v_m_s'][0] = new_body[3:] + transport_vector(excess, transform)
    velocity_ratio = old_scale.velocity_m_s / new_scale.velocity_m_s
    arrays['costates'][0] = transport_costates(arrays['costates'][0], transform)
    arrays['costates'][0, :3] *= new_scale.distance_m / old_scale.distance_m * velocity_ratio
    arrays['costates'][0, 6] *= velocity_ratio
    metadata = dict(reference.metadata, scales=asdict(new_scale), status='unverified_date_seed')
    return Trajectory(metadata, arrays), transform


def _date_context(mission, body, target, scale):
    context = Trajectory(dict(case_id=mission.case_id, mission=mission.to_dict(), scales=asdict(scale),
                              epoch_jd=mission.launch_jd, center=mission.center, time_scale='TDB',
                              frame='ECLIPJ2000', body_initial_state_si=body.tolist(),
                              target_state_si=target.tolist(), configuration_sha256=configuration_hash(mission)), {})
    hardware = mission.spacecraft
    model = BoundedModel(a_max=hardware['thrust_N'] / mission.mass_kg / scale.acceleration_m_s2,
                         alpha=1., beta=1., variable_mass=True,
                         q=hardware['thrust_N'] * scale.time_s / (mission.mass_kg * hardware['exhaust_velocity_m_s']))
    return context, model


def _fast_worker(plan_path, mission_path, attempt):
    plan = json.loads(Path(plan_path).read_text(encoding='utf-8'))
    source = Path(plan['reference'])
    if _identity(source) != plan['reference_sha256']:
        raise ValueError('Reference changed during the sweep')
    reference = Trajectory.load(source)
    base = _reference_mission(reference)
    mission = Mission.load(mission_path)
    expected = replace(base, case_id=mission.case_id, launch_tdb=mission.launch_tdb)
    if mission.to_dict() != expected.to_dict():
        raise ValueError('Only the epoch and case ID may differ from the reference')
    body, target, scale = mission.boundary()
    old_scale = Scales(**reference.metadata['scales'])
    old_body = np.asarray(reference.metadata['body_initial_state_si'])
    guess, transform = _seed(reference, old_body, body, old_scale, scale)
    context, model = _date_context(mission, body, target, scale)
    request = make_request(mission)
    attempt = Path(attempt)
    write_json(attempt / 'request.json', request)
    write_json(attempt / 'seed.json', dict(reference_epoch_tdb=base.launch_tdb,
               reference_sha256=plan['reference_sha256'], transform=transform.tolist(),
               initial_costates=guess.arrays['costates'][0].tolist(),
               initial_excess_m_s=(guess.arrays['v_m_s'][0] - body[3:]).tolist()))
    started = perf_counter()
    result = solve_bangbang(context, guess, model, started + plan['fast_budget_s'], 'psi')
    audit = audit_configuration(result, mission, request, require_final=True)
    kiam = verify_kiam_psi(result)
    if not kiam['passed']:
        raise RuntimeError('Date solution failed the KIAM cross-check')
    result.metadata.update(parameter_audit=audit, kiam_verification=kiam)
    result.save(attempt / 'final')
    write_json(attempt / 'summary.json', dict(status='completed',
               fuel_kg=float(mission.mass_kg - result.arrays['mass_kg'][-1]),
               verification=result.metadata['verification'], kiam_verification=kiam,
               artifact_sha256=_identity(attempt / 'final'),
               correction_s=perf_counter() - started))


def _fast_attempt(output, mission, mission_path, budget):
    case = output / 'fast' / mission.case_id
    case.mkdir(parents=True, exist_ok=True)
    record = case / 'result.json'
    if record.exists():
        row = json.loads(record.read_text(encoding='utf-8'))
        if row['status'] == 'completed' and _identity(output / row['attempt'] / 'final') != row['artifact_sha256']:
            raise ValueError(f'Fast artifact changed since acceptance for {mission.case_id}')
        return row
    attempt = case / f'attempt_{len(list(case.glob("attempt_*"))):03d}'
    attempt.mkdir()
    command = [sys.executable, '-X', 'faulthandler', '-m', 'trajectory_pipeline.date_sweep',
               str((output / 'sweep.json').resolve()), str(mission_path.resolve()), str(attempt.resolve())]
    started = perf_counter()
    try:
        with (attempt / 'worker.log').open('w', encoding='utf-8') as stream:
            worker = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=budget + 15)
        summary = attempt / 'summary.json'
        if worker.returncode == 0 and summary.exists():
            row = json.loads(summary.read_text(encoding='utf-8'))
        else:
            row = dict(status='failed', error=f'Fast worker exit code {worker.returncode}')
    except subprocess.TimeoutExpired:
        row = dict(status='failed', error='Fast worker wall time exceeded')
    row.update(attempt=attempt.relative_to(output).as_posix(), elapsed_s=perf_counter() - started)
    write_json(record, row)
    return row


def fuel_outliers(dates, fast, abs_kg, relative):
    """Use the median of local pairwise predictions, excluding the tested date."""
    accepted = [i for i, row in enumerate(fast) if row['status'] == 'completed']
    if len(accepted) < 3:
        return {}
    flags = {}
    for index, i in enumerate(accepted):
        nearby = accepted[max(0, index - 6):index] + accepted[index + 1:index + 7]
        neighbors = sorted(nearby, key=lambda j: abs(dates[i] - dates[j]))[:6]
        predictions = []
        for left, right in combinations(neighbors, 2):
            weight = (dates[i] - dates[left]) / (dates[right] - dates[left])
            a, b = fast[left]['fuel_kg'], fast[right]['fuel_kg']
            predictions.append(a + weight * (b - a))
        predicted = float(np.median(predictions))
        threshold = max(abs_kg, relative * abs(predicted))
        residual = fast[i]['fuel_kg'] - predicted
        if abs(residual) > threshold:
            flags[i] = dict(predicted_fuel_kg=predicted, residual_kg=residual, threshold_kg=threshold,
                            neighbor_indices=neighbors)
    return flags


def run_date_sweep(reference_path, output, start, stop, *, step_days=1, fast_budget_s=10.,
                   outlier_abs_kg=.5, outlier_rel=.05, resume=False):
    from fcntl import LOCK_EX, LOCK_NB, flock

    source, output = Path(reference_path).resolve(), Path(output)
    first, last = datetime.fromisoformat(start), datetime.fromisoformat(stop)
    if first.tzinfo is not None or last.tzinfo is not None or last < first or step_days <= 0:
        raise ValueError('Supply an ordered TDB date range and a positive day step')
    settings = [fast_budget_s, outlier_abs_kg, outlier_rel]
    if not np.isfinite(settings).all() or fast_budget_s <= 0 or min(settings[1:]) < 0:
        raise ValueError('Fast budget must be positive and outlier thresholds nonnegative')
    reference_hash = _identity(source)
    reference = Trajectory.load(source)
    base = _reference_mission(reference)
    audit_configuration(reference, base, make_request(base), require_final=True)
    if not verify_bounded(reference)['passed'] or not verify_kiam_psi(reference)['passed']:
        raise ValueError('Reference failed independent physical verification')
    if _identity(source) != reference_hash:
        raise ValueError('Reference changed during verification')
    dates = [first + timedelta(days=i) for i in range(0, (last - first).days + 1, step_days)]
    missions = [replace(base, case_id=f'date_{i:06d}', launch_tdb=date.isoformat())
                for i, date in enumerate(dates)]
    ephemerides = Ephemerides()
    for body in (base.departure, base.target):
        coverage = ephemerides.coverage(body)
        if missions[0].launch_jd < coverage['start_jd'] or missions[-1].arrival_jd > coverage['stop_jd']:
            raise ValueError(f'{body} ephemeris does not cover the full sweep and its standard reruns')
    plan = dict(reference=source.as_posix(), reference_sha256=reference_hash,
                start=first.isoformat(), stop=last.isoformat(), step_days=step_days,
                fast_budget_s=fast_budget_s, outlier_abs_kg=outlier_abs_kg, outlier_rel=outlier_rel,
                outlier_method='median_of_local_pair_predictions_v1',
                source_sha256={path.name: sha256(path) for path in sorted(Path(__file__).parent.glob('*.py'))},
                environment=runtime_environment())
    output.mkdir(parents=True, exist_ok=resume)
    with (output / '.sweep.lock').open('a') as lock:
        try:
            flock(lock, LOCK_EX | LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('Another sweep is using this output directory') from exc
        return _run_plan(output, plan, missions, resume)


def _run_plan(output, plan, missions, resume):
    from .runner import sweep_pipeline

    plan_file = output / 'sweep.json'
    if resume:
        if json.loads(plan_file.read_text(encoding='utf-8')) != plan:
            raise ValueError('Sweep resume requires the same reference, range, settings, source and environment')
    else:
        write_json(plan_file, plan)
    inputs = output / 'inputs'
    inputs.mkdir(exist_ok=True)
    fast = []
    for mission in missions:
        path = inputs / (mission.case_id + '.json')
        write_json(path, mission.to_dict())
        row = _fast_attempt(output, mission, path, plan['fast_budget_s'])
        fast.append(row)
        print(f'{mission.launch_tdb}: fast {row["status"]} ({row["elapsed_s"]:.1f} s)', flush=True)

    flags = fuel_outliers([m.launch_jd for m in missions], fast, plan['outlier_abs_kg'], plan['outlier_rel'])
    fallback = [m.to_dict() for i, m in enumerate(missions) if fast[i]['status'] != 'completed' or i in flags]
    write_json(output / 'fallback_matrix.json', fallback)
    standard = {}
    if fallback:
        standard_dir = output / 'standard'
        existing = standard_dir.exists()
        rows = sweep_pipeline(output / 'fallback_matrix.json', standard_dir, resume=existing, pending_only=existing)
        standard = {row['case_id']: row for row in rows}

    rows = []
    for i, mission in enumerate(missions):
        fast_result = fast[i]
        fast_ok = fast_result['status'] == 'completed'
        standard_result = standard.get(mission.case_id)
        fallback_reason = 'fast_failed' if not fast_ok else 'fuel_outlier' if i in flags else None
        row = dict(case_id=mission.case_id, launch_tdb=mission.launch_tdb, fast=fast_result,
                   outlier=flags.get(i), fallback_reason=fallback_reason, standard=standard_result,
                   selected=None, fuel_kg=None, standard_fuel_kg=None)
        if standard_result and standard_result['status'] == 'completed':
            path = output / 'standard' / mission.case_id / 'final'
            result = Trajectory.load(path)
            audit_configuration(result, mission, make_request(mission), require_final=True)
            fuel = float(mission.mass_kg - result.arrays['mass_kg'][-1])
            row.update(selected='standard', fuel_kg=fuel, standard_fuel_kg=fuel,
                       status='completed', artifact=path.relative_to(output).as_posix())
        elif standard_result:
            row['status'] = 'review_required' if fast_ok else standard_result['status']
        if fast_ok and (standard_result is None or
                        (row['selected'] == 'standard' and fast_result['fuel_kg'] < row['fuel_kg'] - 1e-4)):
            path = output / fast_result['attempt'] / 'final'
            result = Trajectory.load(path)
            audit_configuration(result, mission, make_request(mission), require_final=True)
            row.update(selected='fast', fuel_kg=fast_result['fuel_kg'], status='completed', artifact=path.relative_to(output).as_posix())
        rows.append(row)
    write_json(output / 'results.json', rows)
    fields = ['case_id', 'launch_tdb', 'status', 'selected', 'fuel_kg', 'fast_fuel_kg', 'standard_fuel_kg',
              'fast_elapsed_s', 'standard_elapsed_s', 'fallback_reason', 'standard_status', 'artifact']
    with (output / 'results.csv.tmp').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            item = {key: row.get(key) for key in fields}
            item.update(fast_fuel_kg=row['fast'].get('fuel_kg'), fast_elapsed_s=row['fast']['elapsed_s'],
                        standard_elapsed_s=row['standard']['elapsed_s'] if row['standard'] else '',
                        standard_status=row['standard']['status'] if row['standard'] else '')
            writer.writerow(item)
    (output / 'results.csv.tmp').replace(output / 'results.csv')
    return rows


if __name__ == '__main__':
    try:
        _fast_worker(*sys.argv[1:])
    except (ValueError, RuntimeError, TimeoutError) as exc:
        write_json(Path(sys.argv[3]) / 'summary.json', dict(status='failed', error=f'{type(exc).__name__}: {exc}'))
