# Граф поиска траекторий

Статус: budget_exhausted. Узлов: 43; принятых: 7; попаданий в кеш: 7.

Принятые решения сохранены независимо от неудач их улучшения. Изменения относятся к исходной постановке. Физическая недостижимость не доказывается.

| Узел | Операция | Статус | Причина |
|---|---|---|---|
| 3cf8c5240217f4be301f84b1 | cold | partial |  |
| 842c26d8fc8e1d8eb86aec5a | intermediate_release | intermediate |  |
| 30b598996993767d941ec72a | physical_continue | partial |  |
| 5981af51fb585540ddfe6c8a | intermediate_release | intermediate |  |
| b8b4b4411f6bc8fb56e6a8b0 | physical_continue | partial |  |
| 6b9f847de20f6bd31052739c | cold | completed |  |
| 9c78a7c8d0cc1eabef92a6e0 | release | completed |  |
| a1a2fda2fce7a74c3a24330d | cold | partial |  |
| 0738f49812bdbf2be9f81db9 | intermediate_release | intermediate |  |
| bd14e3fbacb15328b28d1fee | physical_continue | partial |  |
| 161eae5319c9baf4e17c4002 | intermediate_release | intermediate |  |
| f8ecdfa451ddc0257dfec313 | physical_continue | partial |  |
| 4fa7e344fb6705ae7a0fb9c2 | cold | partial |  |
| f5c0d2d65b75ee20af687723 | intermediate_release | intermediate |  |
| b14768518f0d1d3147af39fd | physical_continue | partial |  |
| 814fcfc91a29bd3dc1a4cdff | intermediate_release | failed | RuntimeError: No independently verified changed-duration intermediate; see trials.json |
| 6fa9d2b4108f1c68c6ebe18d | physical_continue | partial |  |
| b4e872186c1489d3f81fa5b3 | cold | partial |  |
| c911c2af5a7e950490d3fba0 | intermediate_release | failed | RuntimeError: No independently verified changed-duration intermediate; see trials.json |
| 6638246063cc7615e4f207e9 | physical_continue | partial |  |
| 075369f3ce46bbd639d06e6e | intermediate_release | intermediate |  |
| f5d777d331c8849bb95ad722 | physical_continue | partial |  |
| d273dc149aea6bad1235e8d8 | cold | completed |  |
| 63a9bbb2b9ca33de43f67837 | release | completed |  |
| 55a04e0f4d18c1dc4f1c7d74 | cold | completed |  |
| f9bb474a17f4cab03028ee12 | release | failed | TimeoutError: Free-duration integration budget reached |
| a667493fbbfdc40beaeabffb | cold | initial_failed | ValueError: ILTT phase/orbit correction failed: The iteration is not making good progress, as measured by the   improvement from the last ten iterations.; residual=[-0.14386855 -0.26637634 -0.12606302 -0.52547692  1.59996602  0.02512931]; x=[0.00811772 0.94160173 1.33443335 2.28723288 0.73462322 0.24271655]; x0=[0.00778242 0.94337498 1.33675984 2.29717714 0.73430648 0.24293387] |
| 5658e6f9a0c8f43855d655c1 | cold | completed |  |
| 645dd25d8a0eed665122284c | release | completed |  |
| 15c065d71c45a3f236890dbb | cold | partial |  |
| 3e583a091b6b4489a51f289e | intermediate_release | intermediate |  |
| 87933546f5722e45bc761b53 | physical_continue | partial |  |
| d32f262de09fee4b10cc8e7f | intermediate_release | intermediate |  |
| c2093bfd4c622f3c646e2d35 | physical_continue | partial |  |
| f1492f2d63c38445d5b65f49 | cold | partial |  |
| 6dffc4521f8c0a6f8212ca70 | intermediate_release | intermediate |  |
| 7d6a0931018e22ccb6729164 | physical_continue | partial |  |
| 734557123ce13f2ca40a8f4d | intermediate_release | intermediate |  |
| c6fe7ac0fb580eb8fac7da1f | physical_continue | partial |  |
| 28e2a33fda4b96c021646319 | cold | partial |  |
| c4dd6ea61f5c725b11058983 | intermediate_release | intermediate |  |
| e4c9a9dbaba6dd21f57d68e2 | physical_continue | partial |  |
| e79fab10faaa7b93d96460bb | intermediate_release | failed | Worker wall-time budget reached |

## Решение 6b9f847de20f6bd31052739c

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_venus_2032/nodes/6b9f847de20f6bd31052739c/final`. Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.0, 14.047238884388003, 241.10616306380314].

## Решение 9c78a7c8d0cc1eabef92a6e0

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_venus_2032/nodes/9c78a7c8d0cc1eabef92a6e0/final`. Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.0, 14.045927227662776, 241.6554648927137].

## Решение d273dc149aea6bad1235e8d8

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_venus_2032/nodes/d273dc149aea6bad1235e8d8/final`. Изменения: `{"launch_tdb": {"requested": "2032-11-01T00:00:00", "actual": "2032-05-05T00:00:00"}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.4931506849315068, 28.61321532293865, 569.9062128604398].

## Решение 63a9bbb2b9ca33de43f67837

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_venus_2032/nodes/63a9bbb2b9ca33de43f67837/final`. Изменения: `{"launch_tdb": {"requested": "2032-11-01T00:00:00", "actual": "2032-05-05T00:00:00"}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.4931506849315068, 28.613215322938583, 569.9062128604398].

## Решение 55a04e0f4d18c1dc4f1c7d74

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_venus_2032/nodes/55a04e0f4d18c1dc4f1c7d74/final`. Изменения: `{"launch_tdb": {"requested": "2032-11-01T00:00:00", "actual": "2032-08-03T00:00:00"}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.2465753424657534, 35.41671811850231, 403.9870907343292].

## Решение 5658e6f9a0c8f43855d655c1

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_venus_2032/nodes/5658e6f9a0c8f43855d655c1/final`. Изменения: `{"launch_tdb": {"requested": "2032-11-01T00:00:00", "actual": "2032-05-05T00:00:00"}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.4931506849315068, 28.613215322947, 569.9062128604398].

## Решение 645dd25d8a0eed665122284c

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_venus_2032/nodes/645dd25d8a0eed665122284c/final`. Изменения: `{"launch_tdb": {"requested": "2032-11-01T00:00:00", "actual": "2032-05-05T00:00:00"}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.4931506849315068, 28.61321532286494, 569.9062118783548].
