from pathlib import Path
import json
from trajectory_pipeline.data import sha256,write_json
root=Path('data/ephemerides');rows=[]
for folder in sorted(root.iterdir()):
    if not (folder/'validation.json').exists():continue
    meta=json.loads((folder/'metadata.json').read_text());check=json.loads((folder/'validation.json').read_text())
    assert sha256(folder/'vectors.npz')==meta['arrays_sha256']==check['arrays_sha256']
    assert sha256(folder/'horizons.txt')==meta['raw_sha256']
    for ref in meta.get('refinements',[]):assert sha256(folder/ref['raw'])==ref['raw_sha256']
    assert check['max_position_m']<100 and check['max_velocity_m_s']<.001
    rows.append(dict(body=folder.name,knots=meta['knots'],step_days=meta['max_step_days'],samples=len(check['samples']),position_m=check['max_position_m'],velocity_m_s=check['max_velocity_m_s'],arrays_sha256=meta['arrays_sha256']))
write_json(Path('runs/ephemerides_v4_audit.json'),rows)
lines=['# Эфемериды для свежей широкой проверки ILTT','',
       'Все десять локальных таблиц заново получены от JPL Horizons для 01.01.2020–01.01.2080 TDB. Геометрические состояния относительно Солнца, ECLIPJ2000, SI. Идентификаторы Юпитера/Сатурна 599/699 соответствуют центрам планет. KIAM wheel не изменён.',
       '', 'Начальный шаг 12 ч. Сохранены заново запрошенные сгущения Апофиса около сближения 2029 года; Бенну уточнён около выявленного сближения. Для Юпитера выборочная ошибка скорости потребовала равномерного шага 3 ч. Порог приёмки выборки: 100 м / 0,001 м/с; допуски траекторной матрицы — 1000 м / 0,01 м/с.',
       '', '| Тело | Узлов | Проверочных эпох | Ошибка положения, м | Ошибка скорости, м/с |','|---|---:|---:|---:|---:|']
for r in rows:lines.append(f'| {r["body"]} | {r["knots"]} | {r["samples"]} | {r["position_m"]:.4f} | {r["velocity_m_s"]:.3g} |')
lines+=['','Проверяются эпохи между узлами, равномерная выборка и области резкого изменения ускорения; новые интервалы уточнения проверены дополнительно. Это измеренная ошибка интерполяции относительно Horizons на выборке, не строгая оценка на всём интервале и не неопределённость долгосрочного орбитального прогноза.',
        '', 'Исходные ответы, параметры запросов, SHA256, таблицы и проверки сохранены в data/ephemerides/<body>/. Предыдущий набор остаётся в Git до e113b305 и в runs/ephemerides_before_v4. Пробный запуск на прежних таблицах не включается в итог новой матрицы.']
Path('runs/ephemerides_v4_report.md').write_text('\n'.join(lines)+'\n')
print('Verified hashes and interpolation probes:',len(rows))
