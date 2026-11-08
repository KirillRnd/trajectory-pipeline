"""Describe where a real pipeline run stopped, without retrying or tuning it."""
from pathlib import Path
import json
import csv
import re
from collections import Counter
from trajectory_pipeline.data import Trajectory,Scales,write_json
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.contract import audit_configuration

STEPS=[('departure','stage_departure','Начальная дополнительная скорость'),
       ('pazov','stage_pazov/limit','Пазов: предел ускорения'),
       ('pazov','stage_pazov/functional','Пазов: функционал'),
       ('psi','stage_psi/regularize','ПСИ: регуляризация входа'),
       ('psi','stage_psi/mass','ПСИ: введение массы'),
       ('psi','stage_psi/limit','ПСИ: физический предел тяги'),
       ('psi','stage_psi/fuel','ПСИ: точное управление')]
LABELS={'completed':'ПСИ принята','pending':'Не начат','running':'Расчёт идёт',
        'stage_time_budget':'Исчерпан бюджет этапа','stage_attempt_budget':'Исчерпано число попыток',
        'minimum_step':'Решение не получено при минимальном шаге',
        'worker_time_limit':'Превышен лимит рабочего процесса','worker_crash':'Авария рабочего процесса',
        'program_error':'Ошибка программы','worker_error':'Рабочий процесс завершился с ошибкой',
        'initial_not_found':'Не получено начальное приближение',
        'unclassified_stop':'Остановка без достаточной диагностики'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def describe(case,mission=None):
    case=Path(case);summary=read(case/'summary.json')
    mission=mission or read(case/'mission.json')
    status=summary.get('status','pending');phase=summary.get('phase','initialization')
    row=dict(case_id=mission.get('case_id',case.name),status=status,module=phase,
             block={'irt':'ИРТ','initialization':'Постановка и ИРТ','departure':'Начальная скорость',
                    'pazov':'Переход Пазова','psi':'Переход к ПСИ','final':'Финальная проверка'}.get(phase,phase),
             stop_kind=status,reason=summary.get('error',''),last_rejection='',
             last_verified_artifact=None,last_model=None,physically_unreachable_proven=False)
    request=read(case/'request.json') or None
    if mission.get('parking_departure') is not None:
        row.update(block='Отлёт с НОО: '+summary.get('launch_phase','постановка'),stop_kind=summary.get('stop_kind',status))
        if status=='completed':
            from .launch_pipeline import verify_launch_mission
            if Mission(**mission).to_dict()!=Mission.load(case/'mission.json').to_dict():raise ValueError('Configuration mismatch: parking departure mission')
            if not verify_launch_mission(case)['passed']:raise ValueError('Parking departure acceptance failed')
            row.update(block='Импульс РБ, сшивка отлёта и прибытие',last_verified_artifact=str(case/'final'),stop_kind='completed')
        row['stop_label']=LABELS.get(row['stop_kind'],row['stop_kind'])
        return row
    if mission.get('capture') is not None:
        row.update(block='Захват: '+summary.get('capture_phase','постановка'),stop_kind=summary.get('stop_kind',status))
        if status=='completed':
            from .capture_pipeline import verify_capture_mission
            if Mission(**mission).to_dict()!=Mission.load(case/'mission.json').to_dict():raise ValueError('Configuration mismatch: capture mission')
            check=verify_capture_mission(case)
            if not check['passed']:raise ValueError('Capture final acceptance failed')
            row.update(block='Сшивка и конечная планетоцентрическая орбита',last_verified_artifact=str(case/'final'),stop_kind='completed')
        else:row['last_verified_artifact']=summary.get('last_verified_artifact')
        row['stop_label']=LABELS.get(row['stop_kind'],row['stop_kind'])
        return row
    if status=='completed':
        artifact=Trajectory.load(case/'final')
        audit_configuration(artifact,Mission(**mission),request,require_final=True)
        if not summary.get('verification',{}).get('passed') or not summary.get('kiam_verification',{}).get('passed'):
            raise ValueError('Completed run lacks independent final acceptance: '+str(case))
        row.update(block='Финальная проверка',last_verified_artifact=str(case/'final'),stop_kind='completed')
    elif status not in ('pending','initial_failed'):
        candidates=[(folder,label,read(case/folder/'continuation.json'))
                    for module,folder,label in STEPS if module==phase and (case/folder/'continuation.json').exists()]
        if candidates:
            folder,label,checkpoint=candidates[-1]
            row.update(block=label,checkpoint=str(case/folder/'continuation.json'),
                       accepted_parameter=checkpoint.get('reached_parameter'),
                       next_step=checkpoint.get('next_step'))
            rejected=[event for event in checkpoint.get('history',[]) if not event.get('accepted')]
            row['last_rejection']=rejected[-1].get('message','') if rejected else ''
            row['reason']=summary.get('error') or checkpoint.get('error') or checkpoint.get('stop_reason','')
            if status=='partial':
                row['stop_kind']={'time_budget':'stage_time_budget','attempt_budget':'stage_attempt_budget',
                                  'minimum_step':'minimum_step'}.get(checkpoint.get('stop_reason'),'unclassified_stop')
            last=checkpoint.get('last_point')
            if last and (case/folder/last/'trajectory.json').exists():
                artifact=Trajectory.load(case/folder/last)
                audit_configuration(artifact,Mission(**mission),request)
                if artifact.metadata.get('status')=='verified_extremal' and artifact.metadata.get('verification',{}).get('passed'):
                    row['last_verified_artifact']=str(case/folder/last)
                    model=artifact.metadata.get('bounded_model')
                    if model:
                        scales=Scales(**artifact.metadata['scales'])
                        force=model['a_max']*scales.acceleration_m_s2*mission['mass_kg']
                        row['last_model']=dict(alpha=model['alpha'],beta=model['beta'],variable_mass=model['variable_mass'],
                                               model_thrust_N=force,requested_thrust_N=mission['spacecraft']['thrust_N'],
                                               thrust_ratio=force/mission['spacecraft']['thrust_N'])
        if status=='failed':
            error=row['reason']
            exitcode=re.search(r'exit code (-?\d+)',error)
            row['stop_kind']=('worker_time_limit' if 'Worker exceeded wall-time' in error else
                              'worker_crash' if exitcode and (int(exitcode[1])<0 or int(exitcode[1])>255) else
                              'worker_error' if 'Worker terminated' in error else 'program_error')
    if status=='initial_failed':row['stop_kind']='initial_not_found'
    if status=='partial' and row['stop_kind']=='partial':row['stop_kind']='unclassified_stop'
    row['stop_label']=LABELS.get(row['stop_kind'],row['stop_kind'])
    return row


def report(source,output):
    source=Path(source);output=Path(output)
    missions=json.loads((source/'matrix.json').read_text(encoding='utf-8'))
    if not isinstance(missions,list) or not missions:raise ValueError('A nonempty declared mission matrix is required')
    rows=[describe(source/mission['case_id'],Mission(**mission).validate().to_dict()) for mission in missions]
    lines=['# Где остановилась траекторная цепочка','',
           'Отчёт читает сохранённые результаты и ничего не пересчитывает. Несходимость допустима; физическая недостижимость этими остановками не доказана.','',
           '| Случай | Статус | Блок | Причина остановки | Последняя принятая модель |','|---|---|---|---|---|']
    for row in rows:
        m=row['last_model'];model='—' if not m else f"α={m['alpha']:.7g}, β={m['beta']:.7g}, F/Fзад={m['thrust_ratio']:.7g}"
        lines.append(f"| {row['case_id']} | {row['status']} | {row['block']} | {row['stop_label']} | {model} |")
    for row in rows:
        if row['status'] in ('completed','pending','running'):continue
        lines += ['',f"## {row['case_id']}",'',f"Блок: **{row['block']}**. {row['stop_label']}.",'',
                  f"Основание: `{row['reason']}`.",'',f"Последняя отклонённая попытка: `{row['last_rejection'] or 'не записана'}`.",'',
                  f"Последний проверенный артефакт: `{row['last_verified_artifact'] or 'не найден'}`.",'']
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text('\n'.join(lines),encoding='utf-8')
    write_json(output.with_suffix('.json'),dict(rows=rows,stop_counts=dict(Counter(row['stop_kind'] for row in rows))))
    with output.with_suffix('.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(dict.fromkeys(k for row in rows for k in row)))
        writer.writeheader();writer.writerows(rows)
    return rows
