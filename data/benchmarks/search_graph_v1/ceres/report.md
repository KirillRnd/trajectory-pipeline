# Граф поиска траекторий

Статус: finished. Узлов: 8; принятых: 2; попаданий в кеш: 4.

Принятые решения сохранены независимо от неудач их улучшения. Изменения относятся к исходной постановке. Физическая недостижимость не доказывается.

| Узел | Операция | Статус | Причина |
|---|---|---|---|
| 051effa7065e39297ca2b178 | cold | partial |  |
| ab18373dc98fd77cf4feca4f | cold | partial |  |
| a73d7e6e50a215f16e3c939d | cold | completed |  |
| b35361ff79eb2e502a59d1ce | release | failed | TimeoutError: Free-duration integration budget reached |
| 18abb9b66937b9188bca5b2b | cold | partial |  |
| 788a0f11f73ef4e67ed5f4e7 | cold | partial |  |
| 7d310ebe418ba840076228ae | cold | completed |  |
| f9461577e4bd73453517e2aa | release | failed | TimeoutError: Free-duration integration budget reached |

## Решение a73d7e6e50a215f16e3c939d

Артефакт: `runs/search_graph_ceres_v1/nodes/a73d7e6e50a215f16e3c939d/final`. Изменения: `{"launch_tdb": {"requested": "2030-02-01T00:00:00", "actual": "2029-11-03T00:00:00"}, "tof_days": {"requested": 1000.0, "actual": 800.0}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.4465753424657533, 40.28939127316353, 800.0].

## Решение 7d310ebe418ba840076228ae

Артефакт: `runs/search_graph_ceres_v1/nodes/7d310ebe418ba840076228ae/final`. Изменения: `{"launch_tdb": {"requested": "2030-02-01T00:00:00", "actual": "2029-11-03T00:00:00"}, "tof_days": {"requested": 1000.0, "actual": 800.0}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.4465753424657533, 40.28939127316824, 800.0].
