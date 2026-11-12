import csv,json,shutil
from pathlib import Path
from dataclasses import replace
from collections import Counter
import numpy as np
from scipy.integrate import simpson
from trajectory_pipeline.data import Trajectory,Scales,sha256,write_json
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.contract import audit_configuration,make_request
from trajectory_pipeline.verification import verify_irt
from trajectory_pipeline.seed_sweep import summarize
R=Path('runs/apophis_new_early_sweep_2027_2033_v1')
primary=json.loads((R/'results.json').read_text());fallback={r['case_id']:r for r in json.loads((R/'fallback_results.json').read_text())}
missions={m['case_id']:Mission(**m) for m in json.loads((R/'missions.json').read_text())};catalog=json.loads((R/'catalogue.json').read_text())
branches={c['case_id']:c for d in catalog for c in d['candidates'] if 'case_id' in c}
rows=[]
for old in primary:
 case=old['case_id'];m=missions[case];choices=[]
 if old['status']=='accepted':choices.append((old['artifact'],'standard costates after ILTT'))
 f=fallback.get(case)
 if f:
  for s in f['stages']:
   if s.get('accepted'):choices.append((str(R/'coordinate_fallback'/case/s['coordinates']),'fallback '+s['coordinates']))
 accepted=[]
 for path,route in choices:
  t=Trajectory.load(path);actual=Mission(**t.metadata['mission']);expected=replace(m,tof_days=actual.tof_days)
  check=verify_irt(t);assert check['passed'];audit=audit_configuration(t,expected,make_request(expected))
  assert 0<actual.tof_days<=1095.75
  assert actual.orbit_sources==m.orbit_sources
  scale=Scales(**t.metadata['scales']);J=float(t.metadata['functional_dimensionless'])*scale.acceleration_m_s2**2*scale.time_s
  direct=float(simpson(.5*np.sum(t.arrays['acceleration_m_s2']**2,axis=1),x=t.arrays['t_s']))
  assert np.isclose(J,direct,rtol=1e-10,atol=1e-12)
  accepted.append(dict(case_id=case,launch_tdb=m.launch_tdb,status='accepted',phase='irt',branch_rank=old['branch_rank'],duration_days=actual.tof_days,functional_si_m2_s3=J,route=route,artifact=path,archive_artifact=case+'/irt',verification=check,parameter_audit=audit,arrays_sha256=sha256(Path(path)/'trajectory.npz')))
 row=min(accepted,key=lambda r:r['functional_si_m2_s3']) if accepted else dict(old,fallback=f)
 row['primary_status']=old['status'];row['lambda_initial']=branches[case]['lambda_initial'];row['k']=branches[case]['k'];rows.append(row)
summary=summarize(catalog,rows);summary['status']='finished';summary['primary_totals']=json.loads((R/'summary.json').read_text())['totals'];summary['coordinate_fallback_attempts']=len(fallback)
write_json(R/'final_results.json',rows);write_json(R/'final_summary.json',summary)
accepted=sorted([r for r in rows if r['status']=='accepted'],key=lambda r:r['functional_si_m2_s3'])
archive=R/'archive';archive.mkdir(exist_ok=False)
for name in ('request.json','catalogue.json','missions.json','results.json','summary.json','fallback_design.json','fallback_results.json','final_results.json','final_summary.json'):shutil.copy2(R/name,archive/name)
for row in rows:
 folder=archive/row['case_id'];folder.mkdir()
 for source,label in ((R/'cases'/row['case_id'],'primary'),(R/'coordinate_fallback'/row['case_id'],'fallback')):
  if source.exists():
   dest=folder/label;dest.mkdir()
   for p in source.glob('*.json'):shutil.copy2(p,dest/p.name)
 if row['status']=='accepted':shutil.copytree(row['artifact'],folder/'irt')
 log=R/(row['case_id']+'.log')
 if log.exists():shutil.copy2(log,folder/'primary.log')
with (archive/'dates.csv').open('w',newline='',encoding='utf-8-sig') as out:
 w=csv.writer(out);w.writerow(['launch_tdb','status','candidate_runs','accepted_branches','duration_days','J_m2_s3','route','artifact'])
 for d in summary['dates']:
  best=d['selected'] or {};w.writerow([d['launch_tdb'],d['status'],d['attempted'],d['accepted'],best.get('duration_days'),best.get('functional_si_m2_s3'),best.get('route'),best.get('archive_artifact')])
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
fig,ax=plt.subplots(2,1,figsize=(11,6),sharex=True,layout='constrained')
for route,marker in [('standard','o'),('fallback','s')]:
 pts=[r for r in accepted if r['route'].startswith(route)];dates=[datetime.fromisoformat(r['launch_tdb']) for r in pts]
 ax[0].scatter(dates,[r['functional_si_m2_s3'] for r in pts],s=22,marker=marker,label=route)
 ax[1].scatter(dates,[r['duration_days'] for r in pts],s=22,marker=marker)
ax[0].set_yscale('log');ax[0].set_ylabel('IRT J, m²/s³');ax[0].legend();ax[0].set_title('EarthSimple → ApophisNew: 7-day launch-date sweep')
ax[1].set_ylabel('Flight duration, days');ax[1].set_xlabel('Launch date (TDB)');ax[1].set_xlim(datetime(2027,1,1),datetime(2034,1,1))
for a in ax:a.grid(alpha=.25)
fig.savefig(R/'sweep.png',dpi=160)
from PIL import Image
im=Image.open(R/'sweep.png').convert('RGB');im.thumbnail((1280,1280));im.save(R/'sweep.jpg',quality=83,optimize=True)
assert (R/'sweep.jpg').stat().st_size<200*1024
print('JPEG',im.size,(R/'sweep.jpg').stat().st_size)
shutil.copy2(R/'sweep.jpg',archive/'sweep.jpg')
tot=summary['totals'];primary_ok=sum(r['status']=='accepted' for r in primary);rescued=sum(r['status']=='accepted' and r['primary_status']!='accepted' for r in rows)
lines=['# Новый ранний sweep Апофиса: ApophisNew','',f'366 дат, 01.01.2027–31.12.2033, шаг 7 суток; фактическая последняя точка 30.12.2033. Горизонт 1095,75 суток. Рассчитано {len(rows)} кандидатов; принято {len(accepted)} ИРТ на {tot["accepted_dates"]} датах: {primary_ok} основным маршрутом, ещё {rescued} после переключения координат. На {sum(d["status"]=="no_KLO_candidate_in_horizon" for d in summary["dates"])} датах начальный каталог не дал кандидата в горизонте.','',
'Обе орбиты кеплеровы: EarthSimple и послевстречный набор ApophisNew (эпоха 01.05.2029). ApophisNew используется на всём интервале, включая распространение назад; это ранняя модель целевой орбиты, а не фактические эфемериды Апофиса до встречи. Переход к полным эфемеридам в этой серии не выполнялся.','',
'Вход: дата → фаза → положительные λ(k), |k|≤5 → длительность КЛО → согласование ILTT → ИРТ. k — индекс расслоения. Первоначальная оценка и принятая длительность не превышают трёх лет. Каталог и начальный фильтр могут пропустить другие корни: минимум выбирается только среди проверенных кандидатов на каждой дате, глобальный минимум не заявляется.','',
'Сохранена граница R ±0,598199639. После отказа основной цепочки применяется существующий coordinate_matrix: отдельные режимы ILTT и сопряжённых, по 20 секунд / 70 итераций; при отказе согласования берётся непроверенное приближение той же выбранной по дате ветви. Его принятие как ИРТ требует независимого интегрирования и аудита границ. Коррекция ИРТ фиксирует выведенную длительность; обратного подбора λ по времени нет.','',
'Расчёты выполнены в Docker. ИРТ безмассовая: J=½∫|u|²dt в м²/с³. Метаданные аппарата 204/140 кг, два СПД-50М сохранены только для последующей цепочки; ограничений массы, тяги и топлива в ИРТ нет. Начальная скорость равна скорости Земли. Добавочный импульс, Пазов, ПСИ и оптимизация свободной длительности не выполнялись. Все принятые результаты повторно независимо проверены, включая выбранные источники орбит.','',
'## Самые дешёвые принятые даты','', '| Старт TDB | Длительность, сутки | J, м²/с³ | Маршрут |','|---|---:|---:|---|']
for r in accepted[:15]:lines.append(f'| {r["launch_tdb"][:10]} | {r["duration_days"]:.3f} | {r["functional_si_m2_s3"]:.9g} | {r["route"]} |')
lines+=['','[Все 366 дат, включая отсутствие кандидатов и отказы](../data/benchmarks/apophis_new_early_sweep_2027_2033_v1/dates.csv). [Результаты и независимые проверки](../data/benchmarks/apophis_new_early_sweep_2027_2033_v1/final_results.json).','',
'![J и длительность по датам](../data/benchmarks/apophis_new_early_sweep_2027_2033_v1/sweep.jpg)','',
'## Воспроизведение','', '`docker compose run --rm -T -e OPENBLAS_NUM_THREADS=1 -e OMP_NUM_THREADS=1 pipeline sweep-irt configs/apophis_new_early.json --design configs/apophis_early_sweep_2027_2033.json --output runs/<new>`','',
'Дополнительные переключения и сборка отчёта: архив source/. Полные первичные результаты оставлены в runs/apophis_new_early_sweep_2027_2033_v1. Старый sweep не перезаписан; его семь ИРТ получены на другом источнике орбит и автоматически в новую серию не включались.','']
(R/'report.md').write_text('\n'.join(lines),encoding='utf-8')
(archive/'source').mkdir()
for name in ('apophis_new_irt_switch.py','apophis_new_irt_report.py'):shutil.copy2(Path('runs')/name,archive/'source'/name)
shutil.copy2('data/orbits/apophis_horizons_elements_post_2029-05-01.txt',archive/'source/apophis_horizons_elements_post_2029-05-01.txt')
shutil.copy2('trajectory_pipeline/orbit_sources.py',archive/'source/orbit_sources.py')
shutil.copy2('trajectory_pipeline/coordinate_matrix.py',archive/'source/coordinate_matrix.py')
write_json(archive/'SHA256.json',{str(p.relative_to(archive)):sha256(p) for p in archive.rglob('*') if p.is_file()})
print(json.dumps(dict(totals=tot,primary=primary_ok,rescued=rescued,best=accepted[0] if accepted else None),ensure_ascii=False))

