"""Audit and compactly archive an accepted-IRT continuation matrix."""
import argparse,csv,json,shutil
from pathlib import Path
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor
from collections import Counter
from .data import Trajectory,Scales,write_json,sha256
from .problem import Mission
from .contract import audit_configuration,make_request
from .accepted_irt_routes import physical


def inspect_case(task):
    c,rootstr=task;root=Path(rootstr)/c['case_id']
    assert sha256(Path(c['source'])/'trajectory.npz')==c['source_sha256']
    assert sha256(Path(c['source'])/'trajectory.json')==c['metadata_sha256']
    original=Mission(**Trajectory.load(c['source']).metadata['mission'])
    records={p:json.loads((root/(p+'.json')).read_text()) for p in ('primary','recover','transfer') if (root/(p+'.json')).exists()}
    if records['primary']['status']!='completed':assert 'recover' in records
    if not any(r['status']=='completed' for r in records.values()):assert 'transfer' in records
    accepted=[]
    for phase,r in records.items():
        if r['status']!='completed':continue
        t=Trajectory.load(r['artifact']);actual=Mission(**t.metadata['mission'])
        expected=replace(original,tof_days=actual.tof_days)
        audit=audit_configuration(t,expected,make_request(expected),require_final=True)
        checks=physical(t)
        bounds=c.get('duration_bounds_days',[.5*original.tof_days,min(c.get('horizon_days',float('inf')),max(2*original.tof_days,1095.75))])
        assert bounds[0]-1e-8<=actual.tof_days<=bounds[1]+1e-8
        accepted.append(dict(phase=phase,artifact=r['artifact'],route=r['route'],original_request_audit=audit,**checks))
    row=dict(case_id=c['case_id'],departure=original.departure,target=original.target,mode=original.mode,launch=original.launch_tdb,original_days=original.tof_days,source=c['source'],physical_request=original.to_dict(),status='completed' if accepted else 'partial',phases=list(records))
    if accepted:
        best=min(accepted,key=lambda r:r['fuel_kg']);row.update(best);row['all_accepted']=accepted;row['archive_artifact']=c['case_id']+'/physical';row['duration_changed']=abs(row['tof_days']-original.tof_days)>1e-5
    else:
        row['failures']=[dict(phase=p,operation=e['operation'],status=e.get('status'),error=e.get('error'),details=e.get('details')) for p,r in records.items() for e in r.get('events',[]) if e.get('status') not in ('completed','completed_stage')]
        checkpoints=[]
        for name in ('primary_last','recover_last','broad_last'):
            path=root/name
            if (path/'trajectory.json').exists():
                t=Trajectory.load(path);checkpoints.append(dict(path=str(path),archive_path=c['case_id']+'/'+name,stage=t.metadata.get('stage'),days=t.metadata['mission']['tof_days'],model=t.metadata.get('bounded_model'),thrust_N=(t.metadata['bounded_model']['a_max']*Scales(**t.metadata['scales']).acceleration_m_s2*original.mass_kg if 'bounded_model' in t.metadata else None),departure_parameter=t.metadata.get('departure',{}).get('parameter')))
        row['continuation_stops']=[]
        for file in root.rglob('continuation.json'):
            state=json.loads(file.read_text())
            if state.get('stop_reason')=='completed':continue
            rejected=[e for e in state.get('history',[]) if not e.get('accepted',True)]
            if rejected:row['continuation_stops'].append(dict(path=str(file.relative_to(root)),stop_reason=state.get('stop_reason'),last_rejection=rejected[-1].get('message')))
        row['checkpoints']=checkpoints
        row['last_stage']=' → '.join(str(x['stage']) for x in checkpoints)
        last=row['failures'][-1] if row['failures'] else {}
        row['last_error']=last.get('error') or ('Остановка: '+str((last.get('details') or {}).get('phase',last.get('status','see diagnostics'))))
    return row


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();root=Path(a.output)
    design=json.loads((root/'design.json').read_text())
    with ProcessPoolExecutor(max_workers=4) as pool:rows=list(pool.map(inspect_case,[(c,str(root)) for c in design['cases']]))
    ok=[r for r in rows if r['status']=='completed'];counts=Counter(r['phase'] for r in ok)
    write_json(root/'final.json',dict(total=len(rows),physical=len(ok),by_route_phase=dict(counts),cases=rows))
    archive=root/'archive'
    if archive.exists():
        index=2
        while (root/f'archive_{index:03d}').exists():index+=1
        archive=root/f'archive_{index:03d}'
    archive.mkdir(exist_ok=False)
    shutil.copy2(root/'design.json',archive/'design.json');shutil.copy2(root/'final.json',archive/'final.json')
    for filename in ('environment.json','docker_image_id.txt'):
        if (root/filename).exists():shutil.copy2(root/filename,archive/filename)
    for file in root.glob('*design.json'):
        if file.name!='design.json':shutil.copy2(file,archive/file.name)
    for row in rows:
        folder=archive/row['case_id'];folder.mkdir()
        raw=root/row['case_id']
        for file in raw.glob('*.json'):shutil.copy2(file,folder/file.name)
        if row['status']=='completed':
            shutil.copytree(row['artifact'],folder/'physical')
            write_json(folder/'final_audit.json',{k:row[k] for k in ('verification','kiam_verification','original_request_audit')})
        else:
            for checkpoint in row['checkpoints']:shutil.copytree(checkpoint['path'],folder/Path(checkpoint['path']).name)
        # Diagnostics retain trial reasons without archiving thousands of trajectory nodes.
        for pattern in ('**/profile.json','**/continuation.json','**/trials.json','**/summary.json'):
            for file in raw.glob(pattern):
                dest=folder/'diagnostics'/file.relative_to(raw);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest)
    if (root/'executed_sources').exists():shutil.copytree(root/'executed_sources',archive/'executed_sources')
    (archive/'source').mkdir()
    for name in ('accepted_irt_routes.py','physical_transfer_routes.py','accepted_irt_report.py'):
        shutil.copy2(Path('trajectory_pipeline')/name,archive/'source'/name)
    with (archive/'results.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        fields=['case_id','departure','target','mode','launch','status','original_days','tof_days','fuel_kg','phase','route','last_stage','last_error']
        w=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    configurations={json.dumps({k:r['physical_request'][k] for k in ('mass_kg','spacecraft','departure_mode','vinf_max_m_s','orbit_sources') if k in r['physical_request']},sort_keys=True,ensure_ascii=False) for r in rows}
    lines=[f'# Продолжение {len(rows)} принятых ИРТ до физической ПСИ','',f'Принято **{len(ok)} из {len(rows)}**. Основной маршрут: {counts["primary"]}; альтернативное продолжение: {counts["recover"]}; коррекция точных дуг / независимый перенос / расширенное время: {counts["transfer"]}.', '',
    'Исходные ИРТ, их SHA256 и запросы сохранены. Проверка конечных параметров выполнена относительно каждого исходного запроса; разрешено изменение длительности. Фактические конфигурации этой серии (SI): '+ '; '.join(sorted(configurations)), '',
    '## Маршруты и приёмка','',
    '1. ИРТ → избыток → Пазов (α=0,5) → масса → ограничение тяги → топливный функционал → точные дуги.',
    '2. После отказа — совместное продолжение массы/тяги; освобождение времени на последней проверенной модели в [0,5T;1,5T]; возврат к ранней модели, α=0,3 и время [0,5T;2T].',
    '3. Для остатка — коррекция точных дуг в декартовых, legacy-R и RTN координатах, свободное время; при наличии совместимой физической опоры — независимый R-перенос на исходную дату и фиксированная/свободная коррекция. Последняя общая попытка: раннее освобождение времени в [0,5T;max(2T,1095,75 суток)] и совместное продолжение.', '',
    'Ветвление прекращается после принятой физической ПСИ. Бюджеты отдельных этапов конечны (45–90 секунд, внешние ограничения 65–480 секунд); отказ в таком бюджете не доказывает физическую недостижимость. Продолжение не является доказательством глобального минимума. Изменение длительности не обязательно означает успешное завершение её оптимизации.', '',
    'Каждый принятый результат заново независимо проинтегрирован, проверен KIAM и привязан к исходному запросу с единственным разрешённым изменением tof_days. Требуются α=β=1, фактическая тяга аппарата, точное управление, масса не ниже сухой, граничные условия и трансверсальность. Проверена гелиоцентрическая межпланетная часть; отлёт с орбиты и захват не входят в эту серию.', '',
    'Техническое исправление: для свободного времени от гладкой модели теперь явно строится непроверенное приближение моментов переключения по пересечению throttle=0,5. Раньше этот дополнительный маршрут завершался KeyError; затронутые попытки повторены отдельно, прежние ошибки сохранены.', '',
    '## Все случаи','', '| Случай / дата старта | ИРТ, сут | ПСИ, сут | Топливо, кг | Результат / маршрут |', '|---|---:|---:|---:|---|']
    for r in rows:
        label=r['case_id']+' / '+r['launch'][:10]
        if r['status']=='completed':lines.append(f'| {label} | {r["original_days"]:.2f} | {r["tof_days"]:.2f} | {r["fuel_kg"]:.3f} | {r["route"]} |')
        else:lines.append(f'| {label} | {r["original_days"]:.2f} | — | — | Частично: {r["last_stage"]}; {r["last_error"].replace(chr(10)," ").replace("|","/")} |')
    lines+=['','## Незавершённые пути','', 'Последовательность ниже показывает сохранённые опоры основного, восстановительного и расширенного маршрутов. Она не означает монотонного улучшения: маршрут может возвращаться к ранней модели. Полные причины попыток и параметры — в JSON каждого случая.','']
    for r in rows:
        if r['status']=='completed':continue
        lines+=['### '+r['case_id'],'']
        for cp in r['checkpoints']:
            model=cp['model'] or {};lines.append(f'- {Path(cp["path"]).name}: {cp["stage"]}, T={cp["days"]:.3f} сут, α={model.get("alpha","—")}, β={model.get("beta","—")}, variable_mass={model.get("variable_mass","—")}, F={cp["thrust_N"]} Н, departure parameter={cp["departure_parameter"]}.')
        for f in r['failures']:
            detail=f['error'] or (f.get('details') or {}).get('error') or (f.get('details') or {}).get('phase') or f['status']
            lines.append(f'- {f["phase"]}/{f["operation"]}: {str(detail).replace(chr(10)," ")}.')
        for stop in r['continuation_stops']:
            lines.append(f'- {stop["path"]}: {stop["stop_reason"]}; {stop["last_rejection"]}.')
        lines.append('')
    lines+=['## Артефакты','', f'[Сводные данные и проверки]({archive.name}/final.json), [таблица CSV]({archive.name}/results.csv). Полные узлы продолжения: {root}.','']
    (root/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    (archive/'README.md').write_text(f'# Accepted IRT → physical PSI: {len(rows)} cases\n\nSee final.json, design.json and results.csv. archive_artifact/archive_path are relative to this archive; original run paths are retained for provenance. Partial checkpoints are not physical acceptance. SHA256.json binds this archive.\n',encoding='utf-8')
    write_json(archive/'SHA256.json',{str(f.relative_to(archive)):sha256(f) for f in sorted(archive.rglob('*')) if f.is_file()})
    print(json.dumps(dict(total=len(rows),physical=len(ok),by_phase=dict(counts)),ensure_ascii=False))
if __name__=='__main__':main()






