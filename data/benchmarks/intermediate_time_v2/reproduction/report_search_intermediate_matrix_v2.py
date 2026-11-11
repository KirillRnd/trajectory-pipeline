"""Read-only verification/report for the declared five-case intermediate search."""
from pathlib import Path
from collections import Counter
from datetime import datetime
import json,csv,sys
from trajectory_pipeline.data import Trajectory,write_json,Scales
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.search_graph import verify_cached,check_result,physical_spec
from trajectory_pipeline.intermediate_time import verify_intermediate
root=Path(sys.argv[1] if len(sys.argv)>1 else 'runs/search_intermediate_matrix_v2')
read=lambda p:json.loads(p.read_text())
base={m['case_id']:m for m in read(root/'matrix.json')};rows=[]
design=read(root/'design.json')
names={'cold':'ILTT → избыток → Пазов → масса/ПСИ','reference':'историческая ПСИ','r_transfer':'R-перенос',
       'release':'свободное T физической ПСИ','r_release':'R-перенос → свободное T',
       'intermediate_release':'свободное T промежуточной модели','physical_continue':'совместное продолжение массы/тяги → точная ПСИ'}
for case,b in base.items():
    folder=root/case
    if not (folder/'summary.json').exists():continue
    graph=read(folder/'graph.json');summary=read(folder/'summary.json')
    def route(nid):
        parents=[e['parent'] for e in graph['edges'] if e['child']==nid and e['parent']]
        return (route(parents[0])+' → ' if parents else '')+names[graph['nodes'][nid]['request']['operation']]
    accepted=[];bridges=[];stops=[];partial_checks=[]
    for nid,n in graph['nodes'].items():
        if n.get('artifact'):verify_cached(n)
        operation=n['request']['operation']
        if n['status']=='intermediate':
            result=Trajectory.load(n['artifact']);check=verify_intermediate(result)
            parent=Trajectory.load(n['request']['parent_artifact'])
            old,new=physical_spec(Mission(**parent.metadata['mission'])),physical_spec(Mission(**result.metadata['mission']))
            old.pop('tof_days');new.pop('tof_days');assert old==new
            assert result.metadata.get('bounded_model')==parent.metadata.get('bounded_model')
            assert result.metadata['scales']==parent.metadata['scales']
            if 'bounded_model' not in parent.metadata:
                assert result.metadata.get('departure',{}).get('parameter',0)==parent.metadata.get('departure',{}).get('parameter',0)
            lo,hi=n['request']['bounds_days'];assert lo<=result.metadata['mission']['tof_days']<=hi
            bridges.append(dict(node=nid,mission=result.metadata['mission'],model=result.metadata.get('bounded_model'),
                model_thrust_N=(result.metadata['bounded_model']['a_max']*Scales(**result.metadata['scales']).acceleration_m_s2*result.metadata['mission']['mass_kg']) if 'bounded_model' in result.metadata else None,departure=result.metadata.get('departure'),time_search=result.metadata['intermediate_time'],verification=check,route=route(nid)))
        elif n['status']!='completed':
            if n.get('artifact'):
                check=verify_intermediate(Trajectory.load(n['artifact']));partial_checks.append(dict(node=nid,verification=check))
            stops.append(dict(node=nid,operation=operation,status=n['status'],phase=n.get('phase'),error=n.get('error'),
                model=n.get('last_model'),mission=n.get('mission',n['request']['mission']),checkpoint=n.get('checkpoint'),
                intermediate_unavailable=n.get('intermediate_unavailable'),route=route(nid)))
    for s in graph['solutions']:
        n=graph['nodes'][s['node']];result=Trajectory.load(n['artifact']);m=Mission(**result.metadata['mission'])
        check,kiam=check_result(result,m)
        for key in ('departure','target','mode','center','mass_kg','departure_mode','vinf_max_m_s','position_tolerance_m','velocity_tolerance_m_s'):
            assert getattr(m,key)==b[key],(case,key)
        assert m.spacecraft['dry_mass_kg']==b['spacecraft']['dry_mass_kg']
        assert (m.spacecraft['thrust_N'],m.spacecraft['exhaust_velocity_m_s']) in ((.025,20000),(.05,40000))
        offset=(datetime.fromisoformat(m.launch_tdb)-datetime.fromisoformat(b['launch_tdb'])).total_seconds()/86400
        assert offset in design['date_offsets_days']
        assert design['time_bounds_factors'][0]*b['tof_days']-1e-7<=m.tof_days<=design['time_bounds_factors'][1]*b['tof_days']+1e-7
        assert (physical_spec(m)==physical_spec(Mission(**b)))==s['original_conditions']
        accepted.append(dict(**s,mission=m.to_dict(),route=route(s['node']),verification=check,kiam_verification=kiam))
    accepted.sort(key=lambda s:s['objectives'])
    rows.append(dict(case_id=case,base=b,summary=summary,selected=accepted[0] if accepted else None,accepted=accepted,
                     intermediate=bridges,stops=stops,partial_checks=partial_checks))
    print(case, 'final:',len(accepted),'intermediate:',len(bridges),'verified',flush=True)
write_json(root/'verified_results.json',rows)
totals=dict(cases=len(rows),found=sum(bool(r['accepted']) for r in rows),original=sum(r['summary']['original_conditions_found'] for r in rows),
    accepted_nodes=sum(len(r['accepted']) for r in rows),accepted_configurations=sum(r['summary']['accepted_configurations'] for r in rows),
    intermediate_nodes=sum(len(r['intermediate']) for r in rows),partial_nodes_rechecked=sum(len(r['partial_checks']) for r in rows),
    evaluated=sum(r['summary']['evaluated'] for r in rows),nodes=sum(r['summary']['nodes'] for r in rows))
write_json(root/'totals.json',totals)
lines=['# Освобождение длительности на промежуточных моделях: пять прежних отказов','',
       f'Завершено {len(rows)} из 5 поисков. Принята физическая ПСИ для {totals["found"]} постановок, исходные условия сохранены для {totals["original"]}. Промежуточные модели не считаются решениями.', '',
       'Код 69460613; Docker Linux, неизменённый KIAM 6.1.6. Общий дизайн search_graph_intermediate_v2.json: 2 поколения × 4 особи, seed=17; даты 0/±90 суток; начальные длительности 0,8/1/1,2; пределы свободного времени 0,5–1,5 от исходной длительности. Двигатели 25 мН / 20 км/с и 50 мН / 40 км/с, массы 156/90 кг, избыток до 3 км/с, допуски 1000 м / 0,01 м/с. Эти физические диапазоны совпадают с предыдущей широкой серией.', '',
       'Для каждой особи используется новый маршрут intermediate: холодный расчёт → при наличии проверенной промежуточной модели освобождение T → совместное продолжение beta и предела тяги к физическим значениям → alpha=1 и точная ПСИ. Разрешено до двух циклов. Внутри отдельного продолжения выбранная длительность фиксирована; новое освобождение выполняется отдельным ребром от следующей проверенной промежуточной точки, а не как совместная свободная переменная на каждом шаге гомотопии. Далее пробуется свободное время физической ПСИ; неудача улучшения не удаляет принятое решение. Промежуточный оптимизатор меняет непрерывную длительность и на каждой пробе заново корректирует сопряжённые при обновлённой цели. Его критерий — функционал текущей модели, не физический расход. Для продолжения выбирается лучший проверенный изменённый вариант; его функционал может оказаться хуже исходного. Успех завершения скалярного оптимизатора не означает ни улучшения исходной опоры, ни доказанного минимума.', '',
       'Единые бюджеты: поиск 4800 с, холодный узел 240 с, освобождение промежуточного времени 120 с, продолжение 240 с, финальное освобождение 90 с; пять отдельных процессов. Внутренние бюджеты стадий сохранены из предыдущей матрицы. Два поколения не исчерпывают пространство. Бюджет всей серии больше предыдущего из-за дополнительных рёбер; это не сравнение при равных вычислительных затратах. Отдельные случаи не перенастраивались.', '',
       '| Постановка | Физическая ПСИ | Изменения выбранного варианта | Маршрут / остановки |','|---|---|---|---|']
for r in rows:
    s=r['selected']
    if s:lines.append(f'| {r["case_id"]} | Да | `{json.dumps(s["changes"],ensure_ascii=False)}` | {s["route"]} |')
    else:
        counts=Counter(x['phase'] for x in r['stops'])
        lines.append(f'| {r["case_id"]} | Не найдена в бюджете | — | '+', '.join(f'{k}: {v}' for k,v in counts.items())+' |')
for r in rows:
    lines+=['',f'## {r["case_id"]}','',f'Исходно: {r["base"]["launch_tdb"]}, T={r["base"]["tof_days"]} суток, {r["base"]["mode"]}. Поиск: {r["summary"]["status"]}, {r["summary"]["evaluated"]} геномов / {r["summary"]["nodes"]} узлов.', '',
            f'Проверенных освобождений на промежуточных моделях: {len(r["intermediate"])}. Принятых физических конфигураций: {r["summary"]["accepted_configurations"]}.', '',
            '| Промежуточный узел | T до → после, сутки | alpha / beta / модельная тяга, мН | J до → после | Оптимизатор завершён |','|---|---:|---|---|---|']
    for bridge in r['intermediate']:
        t=bridge['time_search'];m=bridge['model']
        model=f'{m["alpha"]:.6g} / {m["beta"]:.6g} / {bridge["model_thrust_N"]*1000:.6g}' if m else 'ИРТ/избыток'
        lines.append(f'| `{bridge["node"]}` | {t["seed_tof_days"]:.6f} → {t["resolved_tof_days"]:.6f} | {model} | {t["seed_objective"]:.6g} → {t["objective_value"]:.6g} | {t["optimizer_success"]} |')
    for s in r['accepted']:
        lines+=['',f'Принят `{s["node"]}`: {s["route"]}. Расход {s["verification"]["fuel_kg"]:.6f} кг; невязки {s["verification"]["position_residual_m"]:.6g} м / {s["verification"]["velocity_residual_m_s"]:.6g} м/с. Изменения: `{json.dumps(s["changes"],ensure_ascii=False)}`.']
    lines+=['','Остановившиеся попытки (полные ошибки в verified_results.json и исходном графе):','']
    for stop in r['stops']:
        lines.append(f'- `{stop["node"]}`, {stop["operation"]}: {stop["status"]}/{stop["phase"]}; модель `{json.dumps(stop["model"],ensure_ascii=False)}`. '+str(stop['error'] or stop['intermediate_unavailable'] or 'См. checkpoint продолжения')[:300])
lines+=['','## Область вывода','','Проверен только межпланетный участок центральной модели с постоянными F/c. Массы и физические ограничения не ослаблялись. Физическая недостижимость не доказывается. Пара 50 мН / 40 км/с — математический вариант, без подтверждения массы и мощности реальной энергосистемы. Промежуточные узлы и незавершённая оптимизация не являются физическими решениями или доказательством минимума.']
if root.name=='search_intermediate_long_v2':
    replacements={
        'пять прежних отказов':'общая дополнительная проверка расширенного времени',
        'search_graph_intermediate_v2.json: 2 поколения × 4 особи':'search_graph_intermediate_long_v2.json: 1 поколение × 2 особи',
        'даты 0/±90 суток; начальные длительности 0,8/1/1,2; пределы свободного времени 0,5–1,5':'исходные даты; начальная длительность 1,2; пределы свободного времени 0,5–2',
        'Эти физические диапазоны совпадают с предыдущей широкой серией.':'Верхний предел времени расширен одинаково для всех пяти случаев после наблюдения выхода к границе 1,5T у Марса, Венера→Земля и Эроса. Это отдельный эксперимент, основная серия не менялась.',
        'поиск 4800 с':'поиск 1800 с',
        'Два поколения не исчерпывают пространство.':'Две общие начальные опоры не исчерпывают пространство.'}
    for old,new in replacements.items():lines=[line.replace(old,new) for line in lines]
(root/'analysis.md').write_text('\n'.join(lines)+'\n')
with (root/'results.csv').open('w',newline='') as fp:
    writer=csv.writer(fp);writer.writerow(['case_id','found','intermediate_count','date','days','thrust_N','exhaust_m_s','fuel_kg','route'])
    for r in rows:
        s=r['selected'];m=s['mission'] if s else {};e=m.get('spacecraft',{})
        writer.writerow([r['case_id'],bool(s),len(r['intermediate']),m.get('launch_tdb'),m.get('tof_days'),e.get('thrust_N'),e.get('exhaust_velocity_m_s'),s['verification']['fuel_kg'] if s else None,s['route'] if s else ''])
print(totals)
