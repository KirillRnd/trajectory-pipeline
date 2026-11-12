from pathlib import Path
from datetime import datetime
import json,csv,collections
import numpy as np
from scipy.integrate import simpson
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PIL import Image
from trajectory_pipeline.data import Trajectory,write_json,sha256,AU_M
from trajectory_pipeline.visualization import render

root=Path('runs/apophis_early_sweep_2027_2033_v1')
summary=json.loads((root/'summary.json').read_text());assert summary['status']=='finished'
results=json.loads((root/'results.json').read_text());catalog=json.loads((root/'catalogue.json').read_text())
accepted=sorted((r for r in results if r['status']=='accepted'),key=lambda r:r['functional_si_m2_s3'])
for row in accepted:
    result=Trajectory.load(row['artifact']);a=result.arrays
    actual=float(simpson(.5*np.sum(a['acceleration_m_s2']**2,axis=1),x=a['t_s']))
    assert np.isclose(actual,row['functional_si_m2_s3'],rtol=1e-10,atol=1e-12)
    assert result.metadata['stage']=='irt' and result.metadata['chosen_seed']['source']=='ILTT date/phase'
    assert np.linalg.norm(a['v_m_s'][0]-np.asarray(result.metadata['initial_state_si'])[3:])<1e-8
    assert row['duration_days']<=1095.75
failures=collections.Counter(r['phase'] for r in results if r['status']!='accepted')
write_json(root/'selection_audit.json',dict(accepted=accepted,failure_stages=dict(failures),dimensional_cost_integrals_checked=len(accepted),
    scope='Only KLO and IRT, no departure impulse or physical propulsion stage'))
with (root/'dates.csv').open('w',newline='') as stream:
    columns=['launch_tdb','status','attempted','accepted','k','lambda_corrected','duration_days','functional_si_m2_s3','artifact']
    writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
    for row in summary['dates']:
        chosen=row['selected'] or {};writer.writerow({k:row[k] if k in row else chosen.get(k,'') for k in columns})
out=Path('output/pipeline/apophis_early_sweep_2027_2033_v1');out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
fig,axes=plt.subplots(2,1,figsize=(12.8,7.8),sharex=True,layout='constrained')
xs=[datetime.fromisoformat(r['launch_tdb']) for r in accepted]
axes[0].scatter(xs,[r['functional_si_m2_s3'] for r in accepted],color='#125aad',s=28,label='Принятая ИРТ');axes[0].set_yscale('log')
axes[0].set_ylabel('J = ½∫|u|²dt, м²/с³')
axes[1].scatter(xs,[r['duration_days'] for r in accepted],color='#125aad',s=28)
axes[1].axhline(1095.75,color='.6',lw=.8,ls='--');axes[1].set_ylabel('Длительность, сут')
for ax in axes:
    for status,color,label in [('no_verified_IRT','#c04a32','КЛО-кандидат не дал принятую ИРТ'),('no_KLO_candidate_in_horizon','.7','Нет КЛО-кандидата в горизонте')]:
        xx=[datetime.fromisoformat(r['launch_tdb']) for r in summary['dates'] if r['status']==status]
        ax.scatter(xx,[.025]*len(xx),marker='|',color=color,s=35,transform=ax.get_xaxis_transform(),label=label if ax is axes[0] else None)
    ax.grid(alpha=.2);ax.spines[['top','right']].set_visible(False)
axes[0].legend(fontsize=9,loc='upper right');axes[1].xaxis.set_major_locator(mdates.YearLocator());axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
axes[1].set_xlim(datetime(2027,1,1),datetime(2033,12,31))
axes[1].set_xlabel('Дата старта, TDB');fig.suptitle('Земля → Апофис: ранний sweep КЛО + ИРТ\n2027–2033 · шаг 7 суток · до 3 лет · без добавочного импульса',fontsize=14)
fig.savefig(out/'date_cost.svg');fig.savefig(out/'date_cost.png',dpi=180);plt.close(fig)
previews=[]
def preview(p):
    im=Image.open(p).convert('RGB');im.thumbnail((1280,1280));dest=p.with_suffix('.jpg');im.save(dest,quality=85,optimize=True)
    assert dest.stat().st_size<200*1024
    previews.append(dict(path=str(dest),format='JPEG',size=im.size,bytes=dest.stat().st_size,sha256=sha256(dest)))
preview(out/'date_cost.png')
if accepted:
    render(Trajectory.load(accepted[0]['artifact']),out/'best_irt')
    preview(out/'best_irt/trajectory.png')
write_json(out/'preview_manifest.json',previews)
lines=['# Ранний sweep Апофиса: КЛО + оптимизация ИРТ','',
    'Старты 01.01.2027–31.12.2033 TDB с шагом 7 суток (последняя точка сетки 30.12.2033). Горизонт — 1095,75 суток. Индекс расслоения k перебирается от −5 до +5; λ — витковая дальность.', '',
    f"Проверено {summary['totals']['dates']} дат, {summary['totals']['candidate_runs']} кандидатов КЛО после начального фильтра. Принято {len(accepted)} ИРТ на {summary['totals']['accepted_dates']} датах. Отсечено {summary['totals']['screened_candidates']} кандидатов. Этапы отказа: {dict(failures)}.", '',
    'Порядок: дата → фаза → все положительные λ(k) → время КЛО → фильтр начальной оценки по горизонту → согласование ILTT → ИРТ при выведенной длительности → независимая проверка. Исправленная длительность также обязана уложиться в горизонт. Фильтр начальной оценки может исключить кандидатов, которые при другой коррекции вошли бы в горизонт: полнота поиска не утверждается.', '',
    'Минимум выбирается на каждой дате только среди принятых ИРТ. Для сравнения разных дат используется физический J = ½∫|u|²dt (м²/с³), а не безразмерный функционал с меняющимся масштабом. Его интеграл повторно проверен по сохранённым массивам. Это не расход ксенона и не приёмка физической тяги/массы.', '',
    'На каждой дате стартовая скорость равна скорости Земли; добавочный импульс, Пазов, ПСИ и освобождение времени не выполнялись. Аппарат 204/140 кг сохранён в запросе как будущая постановка, но не влияет на этот квадратичный ИРТ. Старые решения и переносы между датами не использовались.', '',
    '## Самые дешёвые принятые ИРТ на сетке','',
    '| Старт TDB | k | λ после согласования | Длительность, сут | J, м²/с³ |','|---|---:|---:|---:|---:|']
for r in accepted[:15]:lines.append(f"| {r['launch_tdb'][:10]} | {r['k']} | {r['lambda_corrected']:.6f} | {r['duration_days']:.3f} | {r['functional_si_m2_s3']:.8g} |")
lines+=['','Отсутствие принятой ИРТ не означает физическую недостижимость. Даты без КЛО-кандидата в горизонте отделены от отказов согласования ILTT и независимой приёмки ИРТ. Высшие расслоения вне горизонта сохранены в catalogue.json, а не скрыты.','',
    'Архив: [исходные данные, все даты, массивы и SHA256](../data/benchmarks/apophis_early_sweep_2027_2033_v1/README.md). Таблица всех дат — dates.csv. Минимум относится к проверенным кандидатам, не к множеству всех физических траекторий.','',
    '![Дата и стоимость ИРТ](../data/benchmarks/apophis_early_sweep_2027_2033_v1/figures/date_cost.jpg)','',
    '![Самая дешёвая принятая ИРТ](../data/benchmarks/apophis_early_sweep_2027_2033_v1/figures/best_irt/trajectory.jpg)','',
    'Воспроизведение:','',
    '```text','docker compose run --rm pipeline sweep-irt configs/apophis_spd50m_204.json --design configs/apophis_early_sweep_2027_2033.json --output runs/apophis_early_new','```','',
    'Продолжить прерванную серию можно с --resume при неизменных входах, коде, данных и среде. Сохранённые отказы не запускаются повторно автоматически.']
(root/'report.md').write_text('\n'.join(lines)+'\n')
print(summary['totals']);print('Best:',accepted[0] if accepted else None)
