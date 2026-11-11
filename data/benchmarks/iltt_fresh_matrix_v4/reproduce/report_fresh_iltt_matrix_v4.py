"""Independent acceptance of the fresh date-first study, no new optimization."""
from pathlib import Path
from collections import Counter
from datetime import datetime
from dataclasses import replace
import json,sys
import numpy as np
from trajectory_pipeline.data import Trajectory,write_json,sha256,Scales
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.search_graph import verify_cached,check_result,changes
from trajectory_pipeline.intermediate_time import verify_intermediate
from trajectory_pipeline.verification import verify_irt
from trajectory_pipeline.contract import audit_configuration,make_request
from trajectory_pipeline.runtime import runtime_environment

root=Path('runs/iltt_fresh_matrix_v4_full')
read=lambda p:json.loads(p.read_text())
design=read(root/'design.json');rows=[]
bases=read(root/'matrix.json');by_case={m['case_id']:m for m in bases}
extra=Path('runs/iltt_missed_inputs_v4')
partial_mode='--partial' in sys.argv
sources=[(base,root/base['case_id'],'main') for base in bases]
if not partial_mode:assert read(extra/'summary.json')['status']=='finished'
sources.extend((by_case[r['case_id']],extra/r['name'],'supplement') for r in read(extra/'results.json'))
cache=root/'audit_cache';cache.mkdir(exist_ok=True)
code={p.name:sha256(p) for p in Path('trajectory_pipeline').glob('*.py') if p.name not in ('__main__.py','runner.py','free_time.py')}
environment=runtime_environment()
ephemerides={str(p):sha256(p) for p in Path('data/ephemerides').glob('*/*') if p.name in ('metadata.json','vectors.npz')}
for base,folder,study in sources:
    case=base['case_id']
    if partial_mode and not (folder/'summary.json').exists():continue
    graph=read(folder/'graph.json');summary=read(folder/'summary.json')
    assert not read(folder/'history.json')['references']
    fingerprint=dict(graph=sha256(folder/'graph.json'),summary=sha256(folder/'summary.json'),code=code,reporter=sha256(Path(__file__)),environment=environment,ephemerides=ephemerides)
    cache_path=cache/(folder.name+'.json')
    if cache_path.exists() and read(cache_path)['fingerprint']==fingerprint:
        for node in graph['nodes'].values():
            if node.get('artifact'):verify_cached(node)
        rows.append(read(cache_path)['row']);print(folder.name,'cached independent verification',flush=True);continue
    def route(key):
        parents=[e['parent'] for e in graph['edges'] if e['child']==key and e['parent']]
        return (route(parents[0]) if parents else [])+[graph['nodes'][key]['request']['operation']]
    accepted=[];partial=[];stops=[];entries=[]
    for key,node in graph['nodes'].items():
        operation=node['request']['operation']
        assert operation not in ('reference','r_transfer','r_release')
        if node.get('artifact'):verify_cached(node)
        if operation=='cold':
            request=node['request']['mission']
            assert request['tof_days'] is None and request['solver']['irt_entry']=='date'
            run=folder/'nodes'/key/'run';entry=run/'iltt_entry.json'
            iltt=read(entry) if entry.exists() else read(run/'mission.json').get('solver',{}).get('iltt_resolved') if (run/'mission.json').exists() else None
            irt_check=None;irt_source=None
            if iltt:
                for field in ('departure','target','center','launch_tdb'):assert iltt['binding'][field]==request[field]
                assert iltt['branch_rank']==request['solver']['iltt_branch']
            summary_path=run/'stage_irt'/'summary.json'
            if summary_path.exists():
                irt_summary=read(summary_path)
                path=run/'stage_irt'/irt_summary.get('last_result','irt') if irt_summary.get('last_result','irt') else None
                if path and (path/'trajectory.json').exists():
                    tr=Trajectory.load(path);irt_source=tr.metadata['chosen_seed']['source']
                    assert irt_source=='ILTT date/phase' and iltt is not None
                    assert tr.metadata['mission']['tof_days']==iltt['tof_days']
                    expected=replace(Mission(**request),tof_days=iltt['tof_days'])
                    audit_configuration(tr,expected,make_request(expected))
                    irt_check=verify_irt(tr);assert irt_check['passed']
            entries.append(dict(node=key,date=request['launch_tdb'],branch=request['solver']['iltt_branch'],
                                iltt=iltt,irt_source=irt_source,irt_check=irt_check))
        if node['status']!='completed':
            if node.get('artifact'):
                tr=Trajectory.load(node['artifact']);model=tr.metadata.get('bounded_model')
                partial.append(dict(node=key,check=verify_intermediate(tr),mission=tr.metadata['mission'],model=model,
                                    model_thrust_N=model['a_max']*Scales(**tr.metadata['scales']).acceleration_m_s2*tr.metadata['mission']['mass_kg'] if model else None,
                                    route=route(key)))
            if node['status']!='intermediate':
                phase=node.get('phase');checkpoint=None
                if operation=='cold' and phase=='cold':
                    path=folder/'nodes'/key/'run'/'summary.json'
                    if path.exists():
                        checkpoint=read(path);phase=checkpoint.get('phase',phase)
                    else:phase='iltt_entry_unfinished'
                elif operation=='physical_continue' and phase=='physical_continue':
                    path=folder/'nodes'/key/'continuation'/'summary.json'
                    if path.exists():checkpoint=read(path)
                stops.append(dict(node=key,operation=operation,status=node['status'],phase=phase,error=node.get('error'),last_model=node.get('last_model'),checkpoint_summary=checkpoint))
    for solution in graph['solutions']:
        node=graph['nodes'][solution['node']]
        tr=Trajectory.load(node['artifact']);m=Mission(**tr.metadata['mission'])
        check,kiam=check_result(tr,m)
        for field in ('departure','target','center','mode','mass_kg','departure_mode','vinf_max_m_s','position_tolerance_m','velocity_tolerance_m_s'):
            assert getattr(m,field)==base[field],(case,field)
        assert m.spacecraft['dry_mass_kg']==base['spacecraft']['dry_mass_kg']
        assert any(m.spacecraft['thrust_N']==e['thrust_N'] and m.spacecraft['exhaust_velocity_m_s']==e['exhaust_velocity_m_s'] for e in design['engines'])
        offset=(datetime.fromisoformat(m.launch_tdb)-datetime.fromisoformat(base['launch_tdb'])).total_seconds()/86400
        assert offset in design['date_offsets_days']
        anchor=m.solver['iltt_resolved']['tof_days'];lo,hi=design['time_bounds_factors']
        assert lo*anchor-1e-6<=m.tof_days<=hi*anchor+1e-6
        delta=changes(Mission(**base),m);assert delta==solution['changes']
        positions=tr.arrays['r_m'];angles=np.unwrap(np.arctan2(positions[:,1],positions[:,0]))
        parents=[e['parent'] for e in graph['edges'] if e['child']==solution['node'] and e['parent']]
        parent=graph['nodes'][parents[0]] if parents else {}
        fuel_delta=check['fuel_kg']-parent['fuel_kg'] if node['request']['operation']=='release' and 'fuel_kg' in parent else None
        accepted.append(dict(**solution,study=study,folder=str(folder),mission=m.to_dict(),route=route(solution['node']),verification=check,kiam_verification=kiam,
                             xy_turns=float((angles[-1]-angles[0])/(2*np.pi)),release_fuel_change_kg=fuel_delta))
    accepted.sort(key=lambda s:s['objectives'])
    rows.append(dict(case_id=case,study=study,folder=str(folder),base=base,summary=summary,accepted=accepted,selected=accepted[0] if accepted else None,partial_checks=partial,stops=stops,entries=entries))
    write_json(cache_path,dict(fingerprint=fingerprint,row=rows[-1]))
    write_json(root/'verified_searches.json',rows)
    print(case,'accepted',len(accepted),'partial replayed',len(partial),flush=True)
if partial_mode:
    write_json(root/'verified_searches_partial.json',rows)
    print('Finished searches independently checked:',len(rows),flush=True)
    sys.exit(0)
searches=rows;rows=[]
for base in bases:
    matching=[r for r in searches if r['case_id']==base['case_id']]
    accepted=sorted([s for r in matching for s in r['accepted']],key=lambda s:s['objectives'])
    rows.append(dict(case_id=base['case_id'],base=base,accepted=accepted,selected=accepted[0] if accepted else None,
                     stops=[s for r in matching for s in r['stops']],partial_checks=[s for r in matching for s in r['partial_checks']],searches=[r['folder'] for r in matching]))
write_json(root/'verified_results.json',rows)
totals=dict(cases=len(rows),found=sum(bool(r['accepted']) for r in rows),original=sum(any(s['original_conditions'] for s in r['accepted']) for r in rows),
            main_found=sum(bool(r['accepted']) for r in searches if r['study']=='main'),supplementary_searches=sum(r['study']=='supplement' for r in searches),
            irt_replayed=sum(bool(e['irt_check']) for r in searches for e in r['entries']),
            accepted_nodes=sum(len(r['accepted']) for r in rows),partial_replayed=sum(len(r['partial_checks']) for r in rows),nodes=sum(r['summary']['nodes'] for r in searches))
write_json(root/'totals.json',totals)
lines=['# Свежая широкая проверка входа ILTT','',f'Проверено {totals["cases"]} постановок; физическая ПСИ найдена в {totals["found"]}, исходные условия сохранены в {totals["original"]}.',
       '', 'Все цепочки начаты заново: дата → фаза → угловая ветвь → ILTT → длительность. Старые решения не импортировались. Массы 156/90 кг, избыток до 3 км/с, допуски 1000 м / 0,01 м/с. Варианты F/c: 25 мН / 20 км/с и 50 мН / 40 км/с.',
       '', 'Общий дизайн: ветви 0/1, даты 0/±90/±180/±270 суток; 8 особей × 2 поколения, seed 17, лимит 4800 с на случай. Время освобождается в границах 0,5–1,5 длительности ILTT конкретной ветви; до двух промежуточных циклов. Принятый физический родитель сохраняется при неудаче финальной оптимизации времени. Это ограниченный поиск, не полный перебор и не доказательство глобального оптимума.',
       '', f'Основной проход нашёл ПСИ для {totals["main_found"]} постановок. Отдельно выполнено {totals["supplementary_searches"]} дополнительных поисков: для каждого случая без ПСИ до двух согласовавшихся, покрытых эфемеридами и входов с непроверенными сочетаниями F/c из полной проверки 210 вариантов. Выбор по наименьшему сдвигу даты, затем длительности ILTT; непосещённые варианты из двух прежних двигателей, 1–2 особи × 1 поколение и 1800 с на вход. Это единое дополнение протокола, исходный проход не переписан.',
       '', '| Постановка | ПСИ | Дата / длительность | F / c | Топливо, кг | Маршрут либо остановки |','|---|---|---|---|---|---|']
for r in rows:
    s=r['selected']
    if s:
        m=s['mission'];e=m['spacecraft']
        lines.append(f'| {r["case_id"]} | {"исходные условия" if s["original_conditions"] else "изменены условия"} | {m["launch_tdb"][:10]} / {m["tof_days"]:.2f} сут | {e["thrust_N"]*1000:g} мН / {e["exhaust_velocity_m_s"]/1000:g} км/с | {s["verification"]["fuel_kg"]:.3f} | '+ ' → '.join(s['route'])+' |')
    else:
        phases=Counter(s.get('phase') or s['operation'] for s in r['stops'])
        lines.append(f'| {r["case_id"]} | пока не найдена | — | — | — | '+', '.join(f'{k}: {v}' for k,v in phases.items())+' |')
lines+=['','## Принятые альтернативы условий','',
        'Основная таблица предпочитает меньшую перемену условий, затем расход. Ниже для каждой принятой пары «дата / двигатель» выбран наименьший расход среди сохранённых узлов; это не доказательство глобального минимума.',
        '', '| Постановка | Старт | F / c | Длительность, сут | Топливо, кг |','|---|---|---|---:|---:|']
for row in rows:
    alternatives={}
    for solution in row['accepted']:
        m=solution['mission'];e=m['spacecraft'];key=(m['launch_tdb'],e['thrust_N'],e['exhaust_velocity_m_s'])
        if key not in alternatives or solution['verification']['fuel_kg']<alternatives[key]['verification']['fuel_kg']:alternatives[key]=solution
    for key,s in sorted(alternatives.items()):
        lines.append(f'| {row["case_id"]} | {key[0][:10]} | {key[1]*1000:g} мН / {key[2]/1000:g} км/с | {s["mission"]["tof_days"]:.3f} | {s["verification"]["fuel_kg"]:.4f} |')
worse=[s for r in rows for s in r['accepted'] if s['release_fuel_change_kg'] is not None and s['release_fuel_change_kg']>1e-4]
lines+=['',f'Отдельная диагностика: {len(worse)} принятых результатов финального release имеют больший расход, чем их физический родитель. Успех локального оптимизатора не означает фактического улучшения. Родители сохранены; таблицы сравнивают все принятые узлы, а не автоматически выбирают последний.',
        '', 'Для каждого отказа точная причина, модель и посещённые даты/ветви находятся в verified_results.json / verified_searches.json и graph.json соответствующего случая. Несходимость, истечение бюджета и недостаток покрытия не доказывают физическую недостижимость. Приёмка относится к центральному межпланетному участку с постоянными F/c; локальные манёвры и УММП этой серией не проверялись.']
(root/'analysis.md').write_text('\n'.join(lines)+'\n')
print(totals,flush=True)
