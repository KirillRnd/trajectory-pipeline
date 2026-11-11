from pathlib import Path
import json, csv, shutil
from collections import Counter
from datetime import datetime
from trajectory_pipeline.data import Trajectory, write_json, sha256
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.search_graph import check_result, verify_cached, physical_spec
from trajectory_pipeline.contract import digest

root=Path('runs/search_matrix_v1')
read=lambda p:json.loads(p.read_text())
base=read(root/'matrix.json')
if isinstance(base,dict):base=base.get('missions',base.get('cases'))
rows=[]
route_names={'cold':'ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T)', 'reference':'сохранённая ПСИ → повторная независимая проверка','r_transfer':'сохранённая ПСИ → R-перенос даты → коррекция при фикс. T','r_release':'сохранённая ПСИ → R-перенос даты → свободное T','release':'освобождение T'}
for b in base:
    case=b['case_id']; folder=root/case
    if not (folder/'summary.json').exists():continue
    g=read(folder/'graph.json');summary=read(folder/'summary.json')
    def route(nid):
        n=g['nodes'][nid]; op=n['request']['operation']
        parents=[e['parent'] for e in g['edges'] if e['child']==nid and e['parent']]
        return (route(parents[0])+' → ' if op=='release' and parents else '')+route_names[op]
    accepted=[]
    for s in g['solutions']:
        nid=s['node']; n=g['nodes'][nid];verify_cached(n)
        result=Trajectory.load(folder/'nodes'/nid/'final');m=Mission(**result.metadata['mission'])
        check,kiam=check_result(result,m)
        # Check invariants against this row, not merely artifact metadata.
        for k in ('departure','target','mode','center','mass_kg','departure_mode','vinf_max_m_s','position_tolerance_m','velocity_tolerance_m_s'):
            assert getattr(m,k)==b[k],(case,k)
        assert m.spacecraft['dry_mass_kg']==b['spacecraft']['dry_mass_kg']
        assert (m.spacecraft['thrust_N'],m.spacecraft['exhaust_velocity_m_s']) in ((.025,20000),(.05,40000))
        dt=(datetime.fromisoformat(m.launch_tdb)-datetime.fromisoformat(b['launch_tdb'])).total_seconds()/86400
        assert dt in (0,90,-90),(case,dt)
        assert .5*b['tof_days']-1e-6<=m.tof_days<=1.5*b['tof_days']+1e-6
        original=physical_spec(m)==physical_spec(Mission(**b))
        assert original==s['original_conditions']
        accepted.append(dict(**s,mission=m.to_dict(),route=route(nid),operation=n['request']['operation'],reference=n['request'].get('reference'),
                             configuration=digest(physical_spec(m)),verification=check,kiam_verification=kiam))
    accepted.sort(key=lambda s:s['objectives'])
    failures=[]
    for nid,n in g['nodes'].items():
        if n['status']=='completed':continue
        nested=folder/'nodes'/nid/'run'/'summary.json'
        stages=read(nested).get('stages',{}) if nested.exists() else {}
        stages={k:{a:v for a,v in stage.items() if a in ('status','phase','reached_parameter','reached_beta','hardware_limit_reached','last_result','error')} for k,stage in stages.items()}
        continuations=[]
        for cp in (folder/'nodes'/nid/'run').rglob('continuation.json'):
            d=read(cp);continuations.append(dict(path=cp.relative_to(folder).as_posix(),stop_reason=d.get('stop_reason'),last_point=d.get('last_point'),last_parameter=d.get('last_parameter'),last_attempt=(d.get('history') or d.get('attempts') or [None])[-1] if isinstance(d.get('history') or d.get('attempts') or [],list) else None))
        failures.append(dict(continuations=continuations,stages=stages,node=nid,operation=n['request']['operation'],mission=n['request']['mission'],status=n['status'],phase=n.get('phase'),last_model=n.get('last_model'),error=n.get('error'),checkpoint=n.get('checkpoint')))
    attempts=[dict(node=nid,operation=n['request']['operation'],status=n['status'],phase=n.get('phase'),mission=n['request']['mission']) for nid,n in g['nodes'].items()]
    rows.append(dict(attempts=attempts,case_id=case,base=b,summary=summary,selected=accepted[0] if accepted else None,accepted=accepted,failures=failures))
    print(case,len(accepted),'verified',flush=True)
write_json(root/'verified_results.json',rows)
totals=dict(completed_cases=len(rows),found_cases=sum(bool(r['accepted']) for r in rows),
            original_cases=sum(r['summary']['original_conditions_found'] for r in rows),
            accepted_nodes=sum(len(r['accepted']) for r in rows),
            accepted_physical_configurations=sum(r['summary']['accepted_configurations'] for r in rows),
            evaluated_genomes=sum(r['summary']['evaluated'] for r in rows),
            operation_outcomes=dict(Counter(a['operation']+':'+a['status'] for r in rows for a in r['attempts'])),
            source_commit='3a77b5c',physical_unreachability_proven=False)
write_json(root/'totals.json',totals)
lines=['# Широкая матрица графа поиска — 11 ноября 2026', '',
       f'Завершено {len(rows)} из {len(base)} постановок. Принято хотя бы одно решение: {sum(bool(r["accepted"]) for r in rows)}; исходные условия: {sum(r["summary"]["original_conditions_found"] for r in rows)}.', '',
       'Единый дизайн: 2 поколения × 4 особи, seed=17; даты 0/±90 суток; начальные длительности 0,8/1/1,2 от исходной; фиксированное и свободное время (0,5–1,5 от исходной длительности); F/c = 25 мН / 20 км/с либо 50 мН / 40 км/с; α=0,3/0,5/0,7. Масса 156 кг, сухая 90 кг, предел избытка 3 км/с. Пары F/c — варианты математической модели, без подтверждения реализуемости энергетической установки при той же массе.', '',
       'Бюджет поиска 1800 с, узла 240 с, освобождения времени 90 с. В холодном пути: ИРТ 30 с, избыток 40 с, Пазов/масса/ПСИ по штатным бюджетам 60 с, отдельная bounded-попытка 20 с. Четыре отдельных процесса Docker. Один план и один набор истории для всей серии; индивидуальных повторов и подгонки не было. Это ограниченный генетический поиск, не полный перебор декартова произведения.', '',
       'Каждая принятая траектория дополнительно перепроверена независимым интегрированием, аудитом параметров и неизменённым KIAM Fortran. Повторные узлы с одной физической конфигурацией не считаются разными решениями. Выбран вариант с наименьшим отклонением от исходной задачи; при равном отклонении — с меньшим расходом.', '',
       '| Постановка | Итог | Старт TDB | T, сутки | F, мН / c, км/с | Топливо, кг | Сработавший маршрут |',
       '|---|---|---|---:|---|---:|---|']
for r in rows:
    s=r['selected']
    if s:
        m=s['mission'];engine=m['spacecraft'];result='Исходные условия' if s['original_conditions'] else 'Изменены условия'
        lines.append(f'| {r["case_id"]} | {result} | {m["launch_tdb"]} | {m["tof_days"]:.6f} | {engine["thrust_N"]*1000:g} / {engine["exhaust_velocity_m_s"]/1000:g} | {s["verification"]["fuel_kg"]:.6f} | {s["route"]} |')
    else:
        stages=Counter((f.get('phase') or f['status']) for f in r['failures'])
        lines.append(f'| {r["case_id"]} | Не найдено в бюджете | — | — | — | — | '+', '.join(f'{k}: {v}' for k,v in stages.items())+' |')
for r in rows:
    lines += ['',f'## {r["case_id"]}', '',f'Исходно: {r["base"]["departure"]} → {r["base"]["target"]}, {r["base"]["mode"]}, {r["base"]["launch_tdb"]}, T={r["base"]["tof_days"]} суток.', '',
              f'Поиск: {r["summary"]["status"]}; геномов {r["summary"]["evaluated"]}, узлов {r["summary"]["nodes"]}, физических конфигураций {r["summary"]["accepted_configurations"]}.']
    lines += ['', 'Фактически испытанные узлы (все даты TDB):', '', '| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |','|---|---|---:|---|---:|---|']
    for attempt in r['attempts']:
        m=attempt['mission'];e=m['spacecraft']
        lines.append(f'| `{attempt["node"]}` / {attempt["operation"]} | {m["launch_tdb"]} | {m["tof_days"]:.4f} | {e["thrust_N"]*1000:g} / {e["exhaust_velocity_m_s"]/1000:g} | {m["solver"].get("psi_mass_alpha")} | {attempt["status"]}: {attempt["phase"]} |')
    seen=set()
    for s in r['accepted']:
        if s['configuration'] in seen:continue
        seen.add(s['configuration'])
        lines += ['',f'- Узел `{s["node"]}`: {s["route"]}. Изменения: `{json.dumps(s["changes"],ensure_ascii=False)}`. Топливо {s["verification"]["fuel_kg"]:.6f} кг; невязки {s["verification"]["position_residual_m"]:.6g} м / {s["verification"]["velocity_residual_m_s"]:.6g} м/с.']
        if s['reference']:lines += [f'  Исторический источник: `{s["reference"]["path"]}`.']
    lines+=['','Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):','']
    for f in r['failures']:
        err=str(f['error'] or json.dumps(f['stages'].get(f['phase'],f['stages']),ensure_ascii=False))
        # Keep diagnostic readable without dumping enormous replay dictionaries into prose.
        lines.append(f'- `{f["node"]}` / {f["operation"]}: {f["status"]}, этап {f["phase"]}; α/β={json.dumps(f["last_model"],ensure_ascii=False)}; {err[:300]}.')
lines+=['','## Границы вывода','','Проверен межпланетный участок в центральном поле Солнца с постоянными F/c. Локальные раскрутка/скрутка, импульсы на парковочных орбитах и УММП не входят в этот граф версии 1. Отказы свободного времени не отменяют принятые фиксированные решения. «Не найдено» относится к объявленному пространству и бюджету, не к физической недостижимости. Подробные входы каждого узла и неудавшиеся улучшения сохранены.']
(root/'analysis.md').write_text('\n'.join(lines)+'\n')
with (root/'results.csv').open('w',newline='') as fp:
    writer=csv.writer(fp);writer.writerow(['case_id','found','original_conditions','launch_tdb','tof_days','thrust_N','exhaust_velocity_m_s','fuel_kg','route'])
    for r in rows:
        s=r['selected'];m=s['mission'] if s else {};e=m.get('spacecraft',{})
        writer.writerow([r['case_id'],bool(s),s['original_conditions'] if s else False,m.get('launch_tdb'),m.get('tof_days'),e.get('thrust_N'),e.get('exhaust_velocity_m_s'),s['verification']['fuel_kg'] if s else None,s['route'] if s else ''])
print('Verified completed cases:',len(rows))





