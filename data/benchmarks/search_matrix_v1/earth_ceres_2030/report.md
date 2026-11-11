# Граф поиска траекторий

Статус: finished. Узлов: 8; принятых: 2; попаданий в кеш: 4.

Принятые решения сохранены независимо от неудач их улучшения. Изменения относятся к исходной постановке. Физическая недостижимость не доказывается.

| Узел | Операция | Статус | Причина |
|---|---|---|---|
| 051effa7065e39297ca2b178 | cold | partial |  |
| ab18373dc98fd77cf4feca4f | cold | partial |  |
| 6ec275fd02107a63900b0a77 | reference | completed |  |
| 4079f7d3f2108a8fb1289e33 | release | failed | TimeoutError: Free-duration integration budget reached |
| 18abb9b66937b9188bca5b2b | cold | partial |  |
| 788a0f11f73ef4e67ed5f4e7 | cold | partial |  |
| 367b7f975a1155866ff90d52 | reference | completed |  |
| 195e2fcc0cd78663e1eac686 | release | failed | TimeoutError: Free-duration integration budget reached |

## Решение 6ec275fd02107a63900b0a77

Артефакт: `runs/search_matrix_v1/earth_ceres_2030/nodes/6ec275fd02107a63900b0a77/final`. Изменения: `{"launch_tdb": {"requested": "2030-02-01T00:00:00", "actual": "2029-11-03T00:00:00"}, "tof_days": {"requested": 1000.0, "actual": 800.0}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.4465753424657533, 40.28939127316824, 800.0].

## Решение 367b7f975a1155866ff90d52

Артефакт: `runs/search_matrix_v1/earth_ceres_2030/nodes/367b7f975a1155866ff90d52/final`. Изменения: `{"launch_tdb": {"requested": "2030-02-01T00:00:00", "actual": "2029-11-03T00:00:00"}, "tof_days": {"requested": 1000.0, "actual": 800.0}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.4465753424657533, 40.28939127316824, 800.0].
