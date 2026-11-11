# Граф поиска траекторий

Статус: budget_exhausted. Узлов: 38; принятых: 2; попаданий в кеш: 11.

Принятые решения сохранены независимо от неудач их улучшения. Изменения относятся к исходной постановке. Физическая недостижимость не доказывается.

| Узел | Операция | Статус | Причина |
|---|---|---|---|
| e8925db54c45c0635b933862 | cold | partial |  |
| ac5ed81fdf329c4ba8e9e902 | intermediate_release | intermediate |  |
| 878f5666481dff9c5607c59e | physical_continue | partial |  |
| bd5c77e04ca284f4fc6d9d55 | intermediate_release | intermediate |  |
| 0494b3948fe0a574056f6040 | physical_continue | partial |  |
| c4f769b984fc837b3be7821d | cold | partial |  |
| c1a901b58bd0cee8a06cc99e | intermediate_release | failed | RuntimeError: No independently verified changed-duration intermediate; see trials.json |
| 6dc3e68b3698ea2caa8bc0f7 | physical_continue | partial |  |
| 80265e3ba46d75dd9000bd5f | intermediate_release | failed | RuntimeError: No independently verified changed-duration intermediate; see trials.json |
| b6353e18ede4b8f243b3a020 | physical_continue | partial |  |
| f45189ee885064c50d2df0dc | cold | initial_failed | No independently verified IRT; see diagnostics.json for each attempted branch/corrector |
| 9bd523ee0506d9e7175aa396 | cold | initial_failed | No independently verified IRT; see diagnostics.json for each attempted branch/corrector |
| cfbed348f399e199ba596d5b | cold | partial |  |
| 737a9a6d6896573888a645b8 | intermediate_release | intermediate |  |
| b4d4ce05ac784f2e6db9540a | physical_continue | partial |  |
| 73891faa591b17db942b8ef3 | intermediate_release | intermediate |  |
| bd3084f3032fbb51b5e828c1 | physical_continue | completed |  |
| 06dd9bc19e896ab20ab11e2c | release | completed |  |
| f257844a91f98789ca70b278 | cold | partial |  |
| 0b255ea2e4f8492cb63d2a37 | intermediate_release | intermediate |  |
| c6d61735a89a1e86d783bbf2 | physical_continue | partial |  |
| 46886ef89b29ab58bd316704 | intermediate_release | failed | RuntimeError: No independently verified changed-duration intermediate; see trials.json |
| 2facac5236644e0058a31411 | physical_continue | partial |  |
| ac054fd07cb16736ab84c3e5 | cold | partial |  |
| 45a178a418511dc26f621f65 | intermediate_release | intermediate |  |
| e2be7a20dc4e24150b80fd8b | physical_continue | partial |  |
| 912120f98962038ec9743f86 | intermediate_release | intermediate |  |
| 2217df5fabe42b22a9717118 | physical_continue | partial |  |
| 23990ce346b88e4d5ad9beca | cold | partial |  |
| 7d08ef4727996be7725b5b4d | intermediate_release | intermediate |  |
| 7f07bdb0a7278b14877f1791 | physical_continue | partial |  |
| 448bd1cdb717397ec14d0ffc | intermediate_release | failed | RuntimeError: No independently verified changed-duration intermediate; see trials.json |
| 65e75bd2c7186a48fae2ab16 | physical_continue | partial |  |
| f4cd00b6ea7baa1ffd6a17d0 | cold | partial |  |
| b06fb5583b623357801122ab | intermediate_release | intermediate |  |
| 00c9cfbb830cb4886d7f0670 | physical_continue | partial |  |
| 876e0f3c6fb3cf678f2b4fd4 | intermediate_release | intermediate |  |
| 22e55164e75618866bf1b881 | physical_continue | failed | Worker wall-time budget reached |

## Решение bd3084f3032fbb51b5e828c1

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_2029/nodes/bd3084f3032fbb51b5e828c1/final`. Изменения: `{"launch_tdb": {"requested": "2029-09-01T00:00:00", "actual": "2028-12-05T00:00:00"}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.7397260273972602, 25.89763969792092, 361.22360658838045].

## Решение 06dd9bc19e896ab20ab11e2c

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_2029/nodes/06dd9bc19e896ab20ab11e2c/final`. Изменения: `{"launch_tdb": {"requested": "2029-09-01T00:00:00", "actual": "2028-12-05T00:00:00"}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.7397260273972602, 29.88021941722342, 353.5832199512723].
