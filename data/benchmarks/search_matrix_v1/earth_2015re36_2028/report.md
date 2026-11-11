# Граф поиска траекторий

Статус: finished. Узлов: 7; принятых: 2; попаданий в кеш: 3.

Принятые решения сохранены независимо от неудач их улучшения. Изменения относятся к исходной постановке. Физическая недостижимость не доказывается.

| Узел | Операция | Статус | Причина |
|---|---|---|---|
| 83f5783e95f8671257bc1360 | cold | partial |  |
| 467f062746f922e0fcb511f3 | cold | completed |  |
| 86b93226de94efccb9a5d9f0 | release | failed | TimeoutError: Free-duration integration budget reached |
| 4c783c88bcb7a75866595146 | cold | partial |  |
| 72a47c2421671676e8998901 | cold | completed |  |
| cf058b5e1d58861d2de6f272 | cold | partial |  |
| 3b41955c66e1cfc581ad2886 | cold | partial |  |

## Решение 467f062746f922e0fcb511f3

Артефакт: `runs/search_matrix_v1/earth_2015re36_2028/nodes/467f062746f922e0fcb511f3/final`. Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.0, 27.076222557366982, 600.0].

## Решение 72a47c2421671676e8998901

Артефакт: `runs/search_matrix_v1/earth_2015re36_2028/nodes/72a47c2421671676e8998901/final`. Изменения: `{"launch_tdb": {"requested": "2028-09-01T00:00:00", "actual": "2028-06-03T00:00:00"}, "tof_days": {"requested": 600.0, "actual": 720.0}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.4465753424657533, 23.51410062315418, 720.0].
