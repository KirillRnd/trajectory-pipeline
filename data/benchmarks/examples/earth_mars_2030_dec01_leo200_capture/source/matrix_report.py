"""Read-only assessment of a declared matrix; no trajectory optimization."""
from collections import Counter
from pathlib import Path
import json
import numpy as np
from .data import Trajectory,Scales,sha256,write_json
from .ephemerides import MAJOR,canonical
import hashlib
from .outcomes import describe


def _read(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def _stop(case,summary,outcome=None):
    outcome=outcome or describe(case)
    folder=Path(outcome['checkpoint']).parent if outcome.get('checkpoint') else None
    checkpoint=_read(folder/'continuation.json') if folder is not None else {}
    reason=outcome['reason']
    if outcome['last_rejection']:reason+='; '+outcome['last_rejection']
    return reason,checkpoint,folder


def report_matrix(source,output):
    source=Path(source)
    missions=json.loads((source/'matrix.json').read_text(encoding='utf-8'))
    rows=[];details=[];counts=Counter()
    common_keys=('mass_kg','spacecraft','vinf_max_m_s','departure_mode','position_tolerance_m','velocity_tolerance_m_s','solver')
    common={key:missions[0][key] for key in common_keys}
    identical=all(all(mission[key]==common[key] for key in common_keys) for mission in missions)
    execution_notes=_read(source/'execution_notes.json')
    environment=_read(source/'environment.json')
    lines=['# Границы работоспособности общей траекторной цепочки','',
           f'Серия: `{source.resolve()}`. SHA256 объявленной матрицы: `{sha256(source/"matrix.json")}`.','',
           f'Число постановок: {len(missions)}. Единые аппарат, ограничения, допуски и настройки: **{"да" if identical else "нет"}**.','',
           'Проверяется полная цепочка ИРТ → начальная скорость → Пазов → переменная масса → точная ПСИ → независимая/Fortran-проверка. Луна исключена по поручению пользователя.','',
           'Результаты относятся к заданным датам, длительностям, аппарату и численным бюджетам. Частичный путь означает незавершённый расчёт; это не доказательство физической недостижимости. Полученная экстремаль не является доказанным глобальным минимумом.','',
           '| № | Случай | Условие | Сутки | Результат | Этап | Расход, кг | Ошибка, м |',
           '|---:|---|---|---:|---|---|---:|---:|']
    for number,mission in enumerate(missions,1):
        case=source/mission['case_id'];summary=_read(case/'summary.json')
        status=summary.get('status','pending');phase=summary.get('phase','—')
        outcome=describe(case,mission)
        if status=='running' and (case/'stage_psi').exists():phase='psi'
        fuel=error='—';verification=None;digest=None
        if status=='completed' and mission.get('parking_departure') is not None:
            from .launch_pipeline import verify_launch_mission
            check=verify_launch_mission(case)
            if not check['passed']:raise ValueError('Completed parking departure failed verification')
            final=Trajectory.load(case/'final')
            if summary['arrays_sha256']!=final.metadata['arrays_sha256']:raise ValueError('Final checksum differs from summary')
            downstream=check['downstream_verification']
            fuel=f"{downstream.get('total_fuel_kg',downstream.get('fuel_kg')):.4f}"
            error=f"{check['join_position_error_m']:.3f}"
            verification=check;digest=final.metadata['arrays_sha256']
        elif status=='completed' and mission.get('capture') is not None:
            from .capture_pipeline import verify_capture_mission
            check=verify_capture_mission(case)
            if not check['passed']:raise ValueError('Completed capture failed verification')
            final=Trajectory.load(case/'final')
            if summary['arrays_sha256']!=final.metadata['arrays_sha256']:raise ValueError('Final checksum differs from summary')
            fuel=f"{check['total_fuel_kg']:.4f}";error=f"{check['orbit_element_error_m']:.3f}"
            verification=check;digest=final.metadata['arrays_sha256']
        elif status=='completed':
            final=Trajectory.load(case/'final')
            model=final.metadata['bounded_model'];check=summary['verification'];vendor=summary['kiam_verification']
            if not (model['alpha']==1 and model['beta']==1 and model['variable_mass'] and final.metadata['hardware_limit_reached'] and check['passed'] and vendor['passed']):
                raise ValueError('Completed row lacks final physical acceptance: '+mission['case_id'])
            if summary['arrays_sha256']!=final.metadata['arrays_sha256']:raise ValueError('Final checksum differs from summary')
            scales=Scales(**final.metadata['scales'])
            force=model['a_max']*scales.acceleration_m_s2*mission['mass_kg']
            if not np.isclose(force,mission['spacecraft']['thrust_N'],rtol=1e-10,atol=1e-12):
                raise ValueError('Final thrust differs from the common spacecraft')
            fuel=f"{check['fuel_kg']:.4f}";error=f"{check['position_residual_m']:.3f}"
            verification=check
            digest=final.metadata['arrays_sha256']
        elif status not in ('pending','running'):
            reason,checkpoint,folder=_stop(case,summary,outcome)
            stages=summary.get('stages',{})
            detail=dict(number=number,case_id=mission['case_id'],phase=phase,
                        block=outcome['block'],stop_kind=outcome['stop_kind'],stop_label=outcome['stop_label'],
                        reached_parameter=checkpoint.get('reached_parameter'),reason=reason,
                        stages={k:{a:b for a,b in v.items() if a in ('status','phase','reached_parameter','reached_alpha','reached_beta','hardware_limit_reached','last_result')} for k,v in stages.items()})
            if folder is not None and checkpoint.get('last_point'):
                accepted=_read(folder/checkpoint['last_point']/'trajectory.json')
                model=accepted.get('bounded_model')
                if model:
                    scales=Scales(**accepted['scales'])
                    hardware=mission['spacecraft']['thrust_N']/mission['mass_kg']/scales.acceleration_m_s2
                    detail['last_model']=dict(alpha=model['alpha'],beta=model['beta'],variable_mass=model['variable_mass'],
                                              acceleration_bound_to_hardware_ratio=float(model['a_max']/hardware))
            if folder is not None:detail['checkpoint']=str(folder/'continuation.json')
            details.append(detail)
        counts[status]+=1
        label=dict(completed='ПСИ получена',partial='Частично',failed='Ошибка',initial_failed='Не получено ИРТ',pending='Не начат',running='Считается').get(status,status)
        lines.append(f"| {number} | {mission['departure']} → {mission['target']} | {mission['mode']} | {mission['tof_days']:g} | {label} | {outcome['block']} | {fuel} | {error} |")
        rows.append(dict(case_id=mission['case_id'],status=status,phase=phase,block=outcome['block'],stop_kind=outcome['stop_kind'],verification=verification,arrays_sha256=digest))
    lines+=['','## Условия сравнения','',f'`{json.dumps(common,ensure_ascii=False,sort_keys=True)}`','',
            'Различаются тела, эпохи, длительности и явно указанные конечные условия. Не использованы индивидуальные изменения двигателя или отдельные миссионные решатели.','',
            '## Остановки','']
    if execution_notes:
        lines+=['Примечания к выполнению:','']+['- '+str(note) for note in execution_notes.get('notes',[])]+['']
    for detail in details:
        lines += [f"### {detail['number']}. {detail['case_id']}",'',
                  f"Блок **{detail['block']}**. {detail['stop_label']}. Параметр последнего продолжения: `{detail['reached_parameter']}`.",'',
                  f"Последняя модель: `{detail.get('last_model',{})}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.",'',
                  str(detail['reason']).replace('\n',' '),'',
                  f"Этапы: `{json.dumps(detail['stages'],ensure_ascii=False)}`.",'']
    planets={canonical(m['target']) for m in missions if canonical(m['target']) in MAJOR}
    asteroids={canonical(m['target']) for m in missions if canonical(m['target']) not in MAJOR}
    lines+=['## Полнота','',f'Завершено ПСИ: {counts["completed"]}/{len(missions)}; остальные статусы: `{dict(counts)}`.',
            f'Целевых больших тел: {len(planets)}; астероидов: {len(asteroids)}. Это выборка геометрий, а не доказательство работоспособности для всех миссий к этим телам.','',
            'При следующем улучшении общего метода повторять ту же матрицу с едиными правилами и сравнивать результаты. Причины ограничивать подтверждённой диагностикой: бюджет, шаг продолжения, сходимость, независимые невязки или физические ограничения.','']
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text('\n'.join(lines),encoding='utf-8')
    result=dict(counts=dict(counts),cases=len(missions),rows=rows,details=details,report=str(output),
                matrix_sha256=sha256(source/'matrix.json'),common_conditions=common,identical_settings=identical)
    result['execution_notes']=execution_notes
    result['environment']=environment
    write_json(output.with_suffix('.json'),result)
    return result


def compare_matrices(first,second,output):
    """Compare declared missions and terminal outcomes, without optimization."""
    roots=[Path(first),Path(second)]
    missions=[json.loads((root/'matrix.json').read_text(encoding='utf-8')) for root in roots]
    if missions[0]!=missions[1]:raise ValueError('The two series do not contain identical mission/configuration objects')
    canonical_matrix=json.dumps(missions[0],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    digest=hashlib.sha256(canonical_matrix).hexdigest()
    rows=[];counts=[Counter(),Counter()]
    lines=['# Сравнение двух общих проходов','',
           f'Первый: `{roots[0].resolve()}`. Второй: `{roots[1].resolve()}`.','',
           f'Все {len(missions[0])} объектов миссий и настроек совпадают. Канонический SHA256 JSON: `{digest}`. Различия CRLF/LF не влияют на это сравнение.','',
           '| Случай | Первый: статус / этап | Второй: статус / этап | Δ расхода второго, кг |',
           '|---|---|---|---:|']
    for mission in missions[0]:
        key=mission['case_id'];values=[]
        for index,root in enumerate(roots):
            summary=_read(root/key/'summary.json')
            status=summary.get('status','pending')
            item=dict(status=status,phase=summary.get('phase'),error=summary.get('error'))
            counts[index][status]+=1
            if status=='completed':
                artifact=Trajectory.load(root/key/'final')
                if summary.get('arrays_sha256')!=artifact.metadata['arrays_sha256']:
                    raise ValueError('Final checksum differs from comparison summary')
                item.update(fuel_kg=summary['verification']['fuel_kg'],arrays_sha256=artifact.metadata['arrays_sha256'])
            values.append(item)
        delta=values[1]['fuel_kg']-values[0]['fuel_kg'] if all(v['status']=='completed' for v in values) else None
        delta_label='—' if delta is None else f'{delta:+.8f}'
        lines.append(f"| {key} | {values[0]['status']} / {values[0]['phase']} | {values[1]['status']} / {values[1]['phase']} | {delta_label} |")
        rows.append(dict(case_id=key,first=values[0],second=values[1],fuel_difference_kg=delta))
    environments=[_read(root/'environment.json') for root in roots]
    lines+=['','## Среда и область вывода','',
            f'Первый итог: `{dict(counts[0])}`. Второй: `{dict(counts[1])}`.','',
            'Сравнение сохраняет разные окружения и реальные ошибки. Само изменение статуса не доказывает причину: численные бюджеты зависят также от скорости среды. Ошибку процесса нельзя приравнивать к физической недостижимости.','']
    for index,environment in enumerate(environments,1):
        lines += [f'Окружение {index}: `{json.dumps(environment,ensure_ascii=False)}`.' if environment else f'Окружение {index}: отдельный environment.json не был записан; смотреть исходные ИРТ-сводки и журнал выполнения.','']
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text('\n'.join(lines),encoding='utf-8')
    result=dict(identical_missions=True,mission_count=len(missions[0]),matrix_semantic_sha256=digest,
                first_counts=dict(counts[0]),second_counts=dict(counts[1]),environments=environments,rows=rows)
    write_json(output.with_suffix('.json'),result)
    return result
