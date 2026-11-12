"""Read and independently verify a declared free-duration matrix."""
from collections import Counter
from pathlib import Path
import csv
import json
from .data import Trajectory, sha256, write_json
from .problem import Mission
from .free_time import audit_time_result
from .bounded import verify_bounded
from .kiam_verification import verify_kiam_psi
from .outcomes import describe


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def report_free_time_matrix(source, output):
    source, output = Path(source), Path(output)
    missions = read(source/'matrix.json')
    rows = []
    for spec in missions:
        mission = Mission(**spec).validate()
        case = source/mission.case_id
        summary = read(case/'summary.json', {})
        history = read(case/'time_history.json', [])
        attempts = []
        for anchor in sorted(case.glob('anchor_*')):
            if not (anchor/'summary.json').exists():
                continue
            detail = describe(anchor)
            index = int(anchor.name.split('_')[-1])
            attempts.append(dict(anchor=anchor.name, fixed_time=detail,
                                 release=history[index] if index < len(history) else None))
        row = dict(case_id=mission.case_id, departure=mission.departure, target=mission.target,
                   launch_tdb=mission.launch_tdb, mode=mission.mode,
                   seed_tof_days=mission.tof_days, bounds_days=mission.time_policy['bounds_days'],
                   status=summary.get('status', 'pending'), phase=summary.get('phase'),
                   tof_days=None, fuel_kg=None, verification=None, kiam_verification=None,
                   reason=summary.get('error'), attempts=attempts)
        if row['status'] == 'completed':
            result = Trajectory.load(case/'final')
            audit_time_result(result, mission)
            check, kiam = verify_bounded(result), verify_kiam_psi(result)
            if not check['passed'] or not kiam['passed']:
                raise ValueError('Independent free-time verification failed: '+mission.case_id)
            row.update(tof_days=result.metadata['mission']['tof_days'],
                       fuel_kg=check['fuel_kg'], verification=check, kiam_verification=kiam,
                       time_optimization=result.metadata['free_time'],
                       arrays_sha256=sha256(case/'final/trajectory.npz'),
                       metadata_sha256=sha256(case/'final/trajectory.json'))
        rows.append(row)
    common_keys = ('mass_kg','spacecraft','vinf_max_m_s','departure_mode',
                   'position_tolerance_m','velocity_tolerance_m_s','solver')
    common = {k: missions[0][k] for k in common_keys}
    identical = all(all(m[k] == common[k] for k in common_keys) for m in missions)
    counts = dict(Counter(r['status'] for r in rows))
    lines = ['# Широкая матрица со свободной длительностью', '',
             f'Серия: `{source}`. Постановок: {len(rows)}. Статусы: `{counts}`.',
             f'SHA256 матрицы: `{sha256(source/"matrix.json")}`.',
             f'Единые аппарат, допуски и численные настройки: {identical}.', '',
             'Дата старта фиксирована; длительность оптимизируется после ПСИ. '
             'Каждый дополнительный ILTT-кандидат проходит полную холодную цепочку. '
             'Принятые результаты повторно проверены интегрированием, аудитом параметров и KIAM.', '',
             '| Случай | Статус | Исходное время, сут | Принятое время, сут | Топливо, кг | Последний этап |',
             '|---|---|---:|---:|---:|---|']
    for r in rows:
        duration = '—' if r['tof_days'] is None else f"{r['tof_days']:.6f}"
        fuel = '—' if r['fuel_kg'] is None else f"{r['fuel_kg']:.6f}"
        lines.append(f"| {r['case_id']} | {r['status']} | {r['seed_tof_days']:g} | {duration} | {fuel} | {r['phase']} |")
    lines += ['', '## Условия', '', f'`{json.dumps(common, ensure_ascii=False)}`', '',
              'Интервалы длительности явно сохранены для каждой строки в JSON. '
              'Незавершённая цепочка не доказывает недостижимость. '
              'Успех локальной оптимизации не доказывает глобальный минимум. '
              'Отлёт с орбиты и захват в эту матрицу не входят.', '',
              '## История попыток', '']
    for r in rows:
        lines += [f"### {r['case_id']}", '', f"Границы, суток: {r['bounds_days']}. {r['reason'] or ''}", '']
        if r.get('time_optimization'):
            info = r['time_optimization']
            lines.append(f"Итераций оптимизатора времени: {info['iterations']}; "
                         f"старт корректора {info['seed_tof_days']:.9f}, результат {r['tof_days']:.9f} суток.")
        for a in r['attempts']:
            fixed, release = a['fixed_time'], a['release']
            lines.append(f"- {a['anchor']}: фиксированный этап — {fixed['status']}, {fixed['block']}; "
                         f"{fixed['stop_label']}. {fixed['reason']} {fixed['last_rejection']}")
            if fixed.get('last_model'):
                lines.append(f"  Последняя проверенная модель: `{json.dumps(fixed['last_model'])}`.")
            if release:
                lines.append(f"  Начальная длительность {release['seed_tof_days']:.6f} суток; "
                             f"после обработки: {release['status']}, этап {release.get('phase')}; "
                             f"{release.get('error') or ''}.")
        lines.append('')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(lines), encoding='utf-8')
    result = dict(cases=len(rows), counts=counts, identical_settings=identical,
                  common_conditions=common, matrix_sha256=sha256(source/'matrix.json'),
                  environment=read(source/'environment.json'), rows=rows)
    result['execution_notes'] = read(source/'execution_notes.json', {})
    write_json(output.with_suffix('.json'), result)
    fields = ['case_id','target','launch_tdb','mode','status','phase','seed_tof_days','tof_days','fuel_kg','reason']
    with output.with_suffix('.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)
    return result
