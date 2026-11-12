import json
from pathlib import Path
from trajectory_pipeline.data import write_json
root=Path('runs/apophis_dm_relaxation_v1')
rows=json.loads((root/'results.json').read_text());assert len(rows)==21
# The first probe runner killed its timed-out child but did not annotate its
# empty summary. Preserve this explicitly; no successful result is inferred.
for r in rows:
    if r['status']=='failed' and r['error'] is None:
        assert not (root/(r['case_id']+f"_dm{r['dm_limit']:.4f}")/'summary.json').exists()
        r['error']='Hard worker time limit: 150 s'
write_json(root/'results.json',rows)
lines=['# Проба ослабления геометрической границы Δm в R','',
 '12.11.2026. Linux Docker. Семь дат × три границы = 21 независимый запуск.',
 'Шесть дат равномерно выбраны из 61 случая упора в старую границу; успешный старт 08.06.2029 — контроль. Выбор сохранён до запуска в design.json.',
 'Все прочие настройки одинаковы: лимит корректора 60 с, процесса 150 с, 200 оценок TRF, горизонт 1095,75 суток. Мягкий бюджет проверяется между интегрированиями; отдельное долгое интегрирование ограничено жёстким бюджетом процесса.',
 'Менялся только solver.iltt_dm_limit: 0,598199639 → 0,8 → 1,0. Старые результаты сохранены; ПСИ и физические ограничения не рассчитывались. Δm не является массой КА.', '',
 '| Дата | ±0,5982 | ±0,8 | ±1,0 |','|---|---:|---:|---:|']
for date in dict.fromkeys(r['launch_tdb'] for r in rows):
    group=[r for r in rows if r['launch_tdb']==date]
    def cell(r):
        if r['status']=='accepted':return 'ИРТ принята'
        return f"{r['iltt_residual']:.5g}" if 'iltt_residual' in r else r['error'].split(':')[0]
    lines.append('| '+date[:10]+' | '+' | '.join(map(cell,group))+' |')
lines+=['','Числа — нормы смешанной невязки орбитальных элементов/фазы, не метры; допуск 1e-7. Меньшая невязка без выполнения допуска не означает решения.',
 'Одна из шести неудачных дат дала принятую ИРТ: 28.01.2028 при ±0,8, Δm=0,6144315491. Длительность 403,799531 суток; λ=1,226735434; J=0,316947993 м²/с³. Независимая невязка положения 6,69 м, скорости 1,40e-6 м/с. Контроль прошёл для всех трёх границ с независимой проверкой. При ±1,0 для 19.02.2027 сработал жёсткий лимит 150 с.',
 'Вывод: умеренное расширение помогло одному случаю; эффект не монотонен. Базовая ручная граница сохранена, ослабление доступно явно как отдельная попытка. Снятие ограничения или индивидуальная подгонка не применялись.', '',
 'Реализация передаёт предел в матрицу R, корректор и финальное восстановление сопряжённых; сохраняет его в binding и инвалидирует несовместимый кеш. Лимит обязан оставаться внутри несингулярной области вокруг нуля. 13 адресных тестов Docker прошли.', '',
 '[Первичные данные и скрипт воспроизведения](../data/benchmarks/apophis_dm_relaxation_v1/README.md).']
(root/'report.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
