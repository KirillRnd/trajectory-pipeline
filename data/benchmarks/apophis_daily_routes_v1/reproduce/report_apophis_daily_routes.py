import json,csv,shutil,sys
from pathlib import Path
from datetime import datetime
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PIL import Image
from trajectory_pipeline.data import Trajectory,write_json,sha256,AU_M
from trajectory_pipeline.contract import audit_configuration
from trajectory_pipeline.problem import Mission

root=Path('runs/apophis_daily_routes_v1');snapshot='--snapshot' in sys.argv
assert snapshot or ((root/'finished.json').exists() and (root/'anchor_recovery.json').exists())
design=json.loads((root/'design.json').read_text());anchor_dates={r['launch_tdb'] for r in design['anchors']}
routes=[json.loads(p.read_text()) for p in sorted((root/'chains').glob('*/summary.json'))]
assert len(routes)==49 and (snapshot or all(r['status']!='running' for r in routes))
rows=[];checks=[]
for i in range(2):
    summary=json.loads((root/f'daily_{i}/summary.json').read_text())
    early=json.loads((root/f'daily_{i}/results.json').read_text())
    for row in summary['dates']:
        date=row['launch_tdb'];route=next((r for r in routes if r['date']==date),{})
        rec=dict(date=date,original_anchor=date in anchor_dates,irt_status=row['status'],route_status=route.get('status','not_started'),phase=route.get('phase','iltt_entry'))
        errors=[r['error'] for r in early if r['launch_tdb']==date and r.get('error')]
        if route:
            errors=[] if route.get('status')=='completed' else ([route['error']] if route.get('error') else [s['error'] for s in route.get('stages',[]) if s.get('error')][-1:])
        rec['error']='; '.join(errors)
        for key in ('physical','free_time'):
            info=route.get(key)
            if info:
                t=Trajectory.load(info['path']);mission=Mission(**t.metadata['mission'])
                request=json.loads((root/'chains'/date[:10]/'request.json').read_text())
                expected=Mission(**dict(request['mission'],tof_days=mission.tof_days))
                audit=audit_configuration(t,expected,require_final=True)
                assert mission.mass_kg==204 and mission.spacecraft['dry_mass_kg']==140
                assert mission.spacecraft['thrust_N']==.036 and mission.spacecraft['exhaust_velocity_m_s']==11767.98
                assert mission.tof_days<=1095.75 and mission.launch_tdb==date
                assert t.metadata['verification']['passed'] and t.metadata['kiam_verification']['passed']
                fuel=float(t.arrays['mass_kg'][0]-t.arrays['mass_kg'][-1]);assert 0<fuel<=64
                if key=='free_time':
                    assert t.metadata['free_time']['optimizer_success']
                    assert fuel<=route['physical']['fuel_kg']+1e-5
                rec.update({key+'_fuel_kg':fuel,key+'_days':mission.tof_days,key+'_path':info['path']})
                checks.append(dict(date=date,stage=key,audit=audit,arrays_sha256=sha256(Path(info['path'])/'trajectory.npz')))
        rows.append(rec)
write_json(root/'final_routes.json',routes);write_json(root/'final_audit.json',checks)
write_json(root/'daily_results.json',rows)
columns=['date','original_anchor','irt_status','route_status','phase','error','physical_days','physical_fuel_kg','free_time_days','free_time_fuel_kg','physical_path','free_time_path']
with (root/'daily_results.csv').open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(rows)
stats=dict(provisional=snapshot,dates=len(rows),irt=sum(r['irt_status']=='accepted' for r in rows),physical=sum('physical_path' in r for r in rows),free_time=sum('free_time_path' in r for r in rows),route_status=dict(Counter(r['status'] for r in routes)))
write_json(root/'final_summary.json',stats);print(stats)
out=Path('output/pipeline/apophis_daily_routes_v1');out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
fig,axes=plt.subplots(2,2,figsize=(12.8,7.8),layout='constrained')
for i,(start,stop) in enumerate(design['windows']):
    subset=[r for r in rows if start<=r['date'][:10]<=stop]
    for stage,label,marker,color in [('physical','Принятая ПСИ','o','#8895a7'),('free_time','После оптимизации времени','o','#125aad')]:
        part=[r for r in subset if stage+'_path' in r];dates=[datetime.fromisoformat(r['date']) for r in part]
        axes[0,i].plot(dates,[r[stage+'_fuel_kg'] for r in part],marker,ms=4,color=color,label=label)
        axes[1,i].plot(dates,[r[stage+'_days'] for r in part],marker,ms=4,color=color)
    for ax in axes[:,i]:
        failed=[datetime.fromisoformat(r['date']) for r in subset if r['irt_status']!='accepted']
        ax.scatter(failed,[.02]*len(failed),marker='|',s=40,color='#c04a32',transform=ax.get_xaxis_transform())
        partial=[datetime.fromisoformat(r['date']) for r in subset if r['irt_status']=='accepted' and 'physical_path' not in r]
        if partial:ax.scatter(partial,[.04]*len(partial),marker='x',s=30,color='#9556a5',transform=ax.get_xaxis_transform(),label='ПСИ не принята' if ax is axes[0,i] else None)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7));ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
        ax.set_xlim(datetime.fromisoformat(start),datetime.fromisoformat(stop));ax.grid(alpha=.2)
    axes[0,i].axhline(64,color='.4',lw=.7,ls='--');axes[0,i].set_title(start[:4]);axes[0,i].legend(fontsize=8)
    axes[1,i].set_xlabel('Старт TDB; красные отметки — отказ ILTT')
axes[0,0].set_ylabel('Ксенон, кг');axes[1,0].set_ylabel('Длительность, сутки')
fig.suptitle('Земля → Апофис · суточная сетка · 204/140 кг · 2 СПД-50М\nИсходная граница Δm ±0,5982 · избыток скорости ≤3 км/с')
fig.savefig(out/'daily_fuel.svg');fig.savefig(out/'daily_fuel.png',dpi=160);plt.close(fig)
best=[]
for start,stop in design['windows']:
    options=[dict(r,chosen_stage='free_time' if 'free_time_path' in r else 'physical') for r in rows if start<=r['date'][:10]<=stop and 'physical_path' in r]
    if options:best.append(min(options,key=lambda r:r[r['chosen_stage']+'_fuel_kg']))
fig,axes=plt.subplots(1,len(best),figsize=(12.8,6),layout='constrained',squeeze=False)
for ax,row in zip(axes[0],best):
    stage=row['chosen_stage'];tr=Trajectory.load(row[stage+'_path']);a=tr.arrays;r=a['r_m']/AU_M
    for key,color,label in [('departure_orbit_m','.8','Земля'),('target_orbit_m','.6','Апофис')]:
        orbit=a[key]/AU_M;ax.plot(orbit[:,0],orbit[:,1],color=color,lw=.7,label=label)
    ax.plot(r[:,0],r[:,1],color='k',lw=1,ls='--')
    throttle=a['throttle'];active=r.copy();active[throttle<.5]=np.nan
    ax.plot(active[:,0],active[:,1],color='k',lw=2,label='Тяга')
    ax.scatter([0],[0],s=30,c='orange');ax.scatter(*r[0,:2],c='#125aad',s=30);ax.scatter(*r[-1,:2],c='#c04a32',s=30)
    ax.set_aspect('equal');ax.grid(alpha=.2);ax.set_xlabel('x, а.е.');ax.set_ylabel('y, а.е.')
    mode='свободное время' if stage=='free_time' else 'без финальной оптимизации времени'
    ax.set_title(f"{row['date'][:10]} · {row[stage+'_days']:.2f} сут\nКсенон {row[stage+'_fuel_kg']:.3f} кг · {mode}");ax.legend(fontsize=8)
fig.suptitle('Лучшие принятые ПСИ в двух окнах · сплошная — тяга, штриховая — пассивные дуги')
fig.savefig(out/'best_trajectories.svg');fig.savefig(out/'best_trajectories.png',dpi=160);plt.close(fig)
previews=[]
for name in ('daily_fuel','best_trajectories'):
    im=Image.open(out/(name+'.png')).convert('RGB');im.thumbnail((1280,1280));p=out/(name+'.jpg');im.save(p,quality=85,optimize=True)
    assert p.stat().st_size<204800;previews.append(dict(path=str(p),format='JPEG',size=im.size,bytes=p.stat().st_size,sha256=sha256(p)))
write_json(out/'previews.json',previews)
lines=['# Апофис: суточная сетка и физические маршруты','',f"{'Предварительно: ' if snapshot else ''}Проверено {stats['dates']} даты: {stats['irt']} принятых ИРТ, {stats['physical']} физических ПСИ, {stats['free_time']} ПСИ с финальной оптимизацией времени. Остальные 23 даты остановились на согласовании ILTT.",'',
 'Сетка 28.01–10.03.2028 и 01.06–29.06.2029, шаг 1 сутки TDB. Исходные семь принятых ИРТ использованы непосредственно; для остальных дат — независимый холодный вход ILTT. Изменения границы R не использованы. 204 кг, сухая 140 кг, F=36 мН, c=11767,98 м/с, избыток скорости ≤3 км/с. Межпланетный участок от Земли до встречи с Апофисом; локальные орбитальные манёвры не добавлялись.',
 'Маршрут: ИРТ → продолжение начальной скорости → Пазов α=0,5 → масса и физическая тяга → точная ПСИ → освобождение длительности. При частичном физическом переходе предусмотрены две общие попытки освобождения времени на промежуточной модели. Интервал времени [0,5T_ILTT; min(1,5T_ILTT;1095,75)] суток. Без индивидуальной смены двигателя, дат и допусков. Неуспех освобождения времени сохраняет принятую физическую ПСИ.', '',
 '## Исходные семь дат','', '| Старт | Принятая ПСИ: сутки / кг ксенона | Свободное время: сутки / кг | Статус |','|---|---:|---:|---|']
def value(r,stage):return f"{r[stage+'_days']:.3f} / {r[stage+'_fuel_kg']:.3f}" if stage+'_path' in r else '—'
for r in rows:
    if r['original_anchor']:lines.append(f"| {r['date'][:10]} | {value(r,'physical')} | {value(r,'free_time')} | {r['route_status']} |")
lines+=['','## Лучшие результаты внутри каждого окна','']
for r in best:lines.append(f"- {r['date'][:10]}: {value(r,r['chosen_stage'])} (сутки / кг ксенона); {r['chosen_stage']}.")
lines+=['','Все физические результаты прошли независимый пересчёт, проверку параметров/массы/переключений и KIAM; после освобождения времени повторно проверены новые границы. Это локальные экстремали, не доказательство глобального минимума. Отказы ILTT не являются доказательством недостижимости.',
 'Для 23.02.2028 дополнительно проверен прямой переход от освобождённой промежуточной модели к α=1 штатным корректором точных дуг. Замыкание границ около 2 м при 3 км/с не прошло проверку знаков функции переключения (нарушение 0,03089); свободная ветвь требовала 3,20996 км/с и также нарушала знаки. Эта диагностическая попытка не принята и не меняет условия задачи. Подробности — chains/2028-02-23/direct_exact_probe.',
 'Затем применён штатный независимый R-перенос ПСИ от ближайшей по дате опоры среди исходных семи (25.02.2028). При времени опоры 351,382425 суток для 23.02 получена принятая ПСИ с расходом 47,355046 кг за 1,78 с коррекции. Параметры двигателя, массы и ограничение избытка не менялись; длительность отличается от исходной ILTT, но лежит в объявленном интервале. Холодное продолжение остановлено после независимой приёмки альтернативного маршрута с сохранением всех его точек.',
 'До отладки финальная оптимизация времени не была принята для 22 дат: для 21 исчерпан бюджет 120 с; для R-переноса 23.02.2028 активная ветвь отвергнута проверкой баланса F/c, свободная ветвь — остановкой SLSQP. После локализации дефекта повторялся только этот этап от принятых физических родителей, с прежними бюджетами и ограничениями; исходные попытки сохранены.',
 'После адресного повтора приняты ещё три свободные по времени ПСИ: 16, 23 и 27 февраля 2028. Для 19 дат сохранена физическая ПСИ без принятой финальной оптимизации времени: 16 бюджетных остановок и три отказа приёмки знаков переключения (15, 23, 24 июня 2029; свободная ветвь SLSQP также не завершилась). Это границы текущего численного маршрута, не физическая недостижимость.',
 'Технический дефект: после пересчёта сетки по новой длительности последняя точка могла оказаться на один ULP за концом интегрированной дуги. При заполнении np.empty она не получала состояния; в реальной диагностике нормированная масса последней точки была 7,75e-304 вместо 0,768. Общая сетка теперь сохраняет только точки внутри интервала дуг и точные границы; оба сборщика проверяют полноту заполнения. После исправления 23.02.2028 принят со свободной длительностью 353,879820 суток и расходом 47,327863 кг. Допуски приёмки не ослаблены. Три адресных проверки сетки/точных дуг и 13 проверок свободного/промежуточного времени прошли в Docker.',
 'При запуске также исправлены ошибки экспериментального контроллера записи статуса и восстановления завершённых этапов. Ранее принятые участки не пересчитывались ради этих исправлений. Уравнения, двигатель и критерии приёмки не менялись; техническая сборка сетки исправлена отдельно.', '',
 '[Данные всех 72 дат и архив](../data/benchmarks/apophis_daily_routes_v1/README.md).', '',
 '![Суточная сетка](../data/benchmarks/apophis_daily_routes_v1/figures/daily_fuel.jpg)', '',
 '![Траектории](../data/benchmarks/apophis_daily_routes_v1/figures/best_trajectories.jpg)']
(root/'report.md').write_text('\n'.join(lines)+'\n')
