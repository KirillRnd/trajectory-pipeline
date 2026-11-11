from pathlib import Path
from collections import Counter
import json
from trajectory_pipeline.data import write_json
root=Path('runs/iltt_preflight_v4');rows=json.loads((root/'results.json').read_text())
assert len(rows)==210 and len({(r['case_id'],r['offset_days'],r['branch']) for r in rows})==210
totals=dict(cases=15,attempts=len(rows),resolved=sum(r['status']=='resolved' for r in rows),failed=sum(r['status']!='resolved' for r in rows))
write_json(root/'totals.json',totals)
lines=['# Полная проверка входов ILTT перед физической цепочкой','',
       f'Проверены все 210 сочетаний: 15 постановок × 7 дат (0/±90/±180/±270 суток) × 2 угловые ветви. Согласование орбиты/фазы выполнено для {totals["resolved"]}. Это ещё не приёмка ИРТ или ПСИ.',
       '', 'Используются те же эфемериды и исходный код, что в основной серии. Каждая попытка разрешает дату через ILTT с исходным tof_days=None. Первые попытки выполнялись последовательно; после выявленного превышения мягкого дедлайна внутри интегрирования остальные изолированы процессом с пределом 40 с. Никаких физических корректоров после ILTT здесь нет.',
       '', '| Постановка | Согласовано / 14 | Длительности согласованных, сутки | Причины остальных остановок |','|---|---:|---|---|']
for case in sorted({r['case_id'] for r in rows}):
    selected=[r for r in rows if r['case_id']==case];ok=[r for r in selected if r['status']=='resolved']
    reasons=Counter()
    for r in selected:
        if r['status']=='resolved':continue
        error=r.get('error','')
        key='жёсткий лимит времени' if 'TimeoutExpired' in error else 'покрытие' if 'coverage' in error else 'область формул' if any(x in error for x in ('domain','Invalid ILTT','positive','finite')) else 'ветвь' if 'branch' in error else 'согласование орбиты/фазы'
        reasons[key]+=1
    span=f'{min(r["iltt"]["tof_days"] for r in ok):.2f}–{max(r["iltt"]["tof_days"] for r in ok):.2f}' if ok else '—'
    lines.append(f'| {case} | {len(ok)} | {span} | '+', '.join(f'{k}: {v}' for k,v in reasons.items())+' |')
lines+=['','Мягкий iltt_budget_s проверяется между вызовами модели; отдельное вложенное интегрирование может превысить его. Поэтому граф использует дополнительный жёсткий лимит рабочего процесса. Это ограничение управления вычислениями, а не свидетельство физической недостижимости.',
        '', 'Аппроксимации начальных сопряжённых используют опорные κ=0,72 и 1,52. Перенос на более дальние тела требует численной проверки; согласование не гарантируется. Для κ≈1 формула a_OM содержит малый знаменатель log(κ). Наличие положительных ветвей в каталоге не доказывает полноту всех возможных коротких решений. Ошибку области формул нельзя называть отказом двигателя или физическим запретом перелёта.']
(root/'analysis.md').write_text('\n'.join(lines)+'\n')
print(totals)
