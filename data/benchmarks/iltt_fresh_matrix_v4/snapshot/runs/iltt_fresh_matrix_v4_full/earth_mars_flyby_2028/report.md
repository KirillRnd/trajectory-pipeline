# Граф поиска траекторий

Статус: finished. Узлов: 36; принятых: 12; попаданий в кеш: 3.

Принятые решения сохранены независимо от неудач их улучшения. Изменения относятся к исходной постановке. Физическая недостижимость не доказывается.

| Узел | Операция | Статус | Причина |
|---|---|---|---|
| 8a2e6d775fa19d32051ee6f2 | cold | completed |  |
| 494fd7295a8cca3b991831ac | release | completed |  |
| d0bda5285005af9264b45a58 | cold | completed |  |
| fcaea141cc5f90fd660c2188 | release | completed |  |
| 650b8133bc543bbbbe466aae | cold | initial_failed | ValueError: ILTT phase/orbit correction failed: The iteration is not making good progress, as measured by the   improvement from the last five Jacobian evaluations.; residual=[-3.31871510e-02 -4.73406442e-06 -1.76611155e-03 -2.41506660e-04  -3.58468871e-03  6.33964753e-03]; x=[-0.10140269 -0.23550478  0.88975989  5.69598831  1.54314017  4.49248233]; x0=[-0.09679823 -0.22388401  0.86343997  5.86653688  1.53517239  4.4149297 ] |
| c548ca7fe2f305cf11da138e | cold | initial_failed | ValueError: ILTT phase/orbit correction failed: The iteration is not making good progress, as measured by the   improvement from the last five Jacobian evaluations.; residual=[-3.31871510e-02 -4.73406442e-06 -1.76611155e-03 -2.41506660e-04  -3.58468871e-03  6.33964753e-03]; x=[-0.10140269 -0.23550478  0.88975989  5.69598831  1.54314017  4.49248233]; x0=[-0.09679823 -0.22388401  0.86343997  5.86653688  1.53517239  4.4149297 ] |
| 0052dd0bfe2e10733e1e2910 | cold | initial_failed | ValueError: ILTT phase/orbit correction failed: The iteration is not making good progress, as measured by the   improvement from the last five Jacobian evaluations.; residual=[ 1.10845680e-02  1.13080064e-03  1.92698447e-03  3.62936440e-05   1.22435114e-03 -2.95927351e-03]; x=[-0.05515973 -0.27910212  0.78816032  5.75734218  1.42706958  2.12972671]; x0=[-0.05944244 -0.22055957  0.8634436   5.86729346  1.54562309  1.98059743] |
| ca050d9855f2bfb2fcccd1b8 | cold | completed |  |
| 5a7435bce2e49b50c47bde7c | release | completed |  |
| 083f2ce19479133dd511b369 | cold | completed |  |
| de28d71bb2365330d3a59de8 | release | completed |  |
| 254a7114e8b1a3f27787523e | cold | partial |  |
| 0c904e2e8575c59b3199236f | intermediate_release | intermediate |  |
| 0fd9d96bcfd20d10f11f8ac0 | physical_continue | partial |  |
| c40e43d56efed12ef5a0b2e5 | intermediate_release | intermediate |  |
| 660b8d71e941a1b674d354e6 | physical_continue | partial |  |
| 256b84da1f06a5ee6bb12ddf | cold | completed |  |
| 2dd220e8211fa18e19ead787 | release | completed |  |
| 4b251a63befd5754e4cdba38 | cold | partial |  |
| b35537aca34b40963546caea | intermediate_release | failed | RuntimeError: No independently verified changed-duration intermediate; see trials.json |
| 8f82171970ebd80d3612e605 | physical_continue | partial |  |
| 9f028d8f80b4840906b034f2 | intermediate_release | intermediate |  |
| e7a8b490d066a2c51a6562fb | physical_continue | partial |  |
| bb35f819e73b42c44402e4b8 | cold | completed |  |
| 2611bbe93475a37b815bf876 | release | completed |  |
| b0175aa11f673dd4872a2dc4 | cold | partial |  |
| cca66d4877c1ca71fe225447 | intermediate_release | intermediate |  |
| d5258d5b309f87acd0bd21df | physical_continue | partial |  |
| 0d9e927a5c1b3f9e3f68958a | intermediate_release | intermediate |  |
| b1667441ef0956d889ca879c | physical_continue | partial |  |
| 431f90197e8fa82ef740d9cb | cold | partial |  |
| 3b2805142eefd42fad0cff0e | intermediate_release | intermediate |  |
| 75c63a8356b348c6346b1e1e | physical_continue | partial |  |
| f0cf05d83635587ca980fcc5 | intermediate_release | intermediate |  |
| 5fcf8c074ca753621f6c2959 | physical_continue | partial |  |
| edf95f0a68348605a4cf5755 | cold | initial_failed | ValueError: math domain error |

## Решение 8a2e6d775fa19d32051ee6f2

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_flyby_2028/nodes/8a2e6d775fa19d32051ee6f2/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 4.847151260059801, 364.7580441797355].

## Решение 494fd7295a8cca3b991831ac

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_flyby_2028/nodes/494fd7295a8cca3b991831ac/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 2.854264629685012, 306.9814624712902].

## Решение d0bda5285005af9264b45a58

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_flyby_2028/nodes/d0bda5285005af9264b45a58/final`. Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.0, 2.4282803585046615, 364.7580441797355].

## Решение fcaea141cc5f90fd660c2188

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_flyby_2028/nodes/fcaea141cc5f90fd660c2188/final`. Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.0, 1.4299331521226994, 306.9565896694566].

## Решение ca050d9855f2bfb2fcccd1b8

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_flyby_2028/nodes/ca050d9855f2bfb2fcccd1b8/final`. Изменения: `{"launch_tdb": {"requested": "2028-11-01T00:00:00", "actual": "2028-05-05T00:00:00"}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.4931506849315068, 5.772567211524734, 772.0239672039633].

## Решение 5a7435bce2e49b50c47bde7c

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_flyby_2028/nodes/5a7435bce2e49b50c47bde7c/final`. Изменения: `{"launch_tdb": {"requested": "2028-11-01T00:00:00", "actual": "2028-05-05T00:00:00"}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.4931506849315068, 2.7241791830893645, 720.7015933772082].

## Решение 083f2ce19479133dd511b369

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_flyby_2028/nodes/083f2ce19479133dd511b369/final`. Изменения: `{"launch_tdb": {"requested": "2028-11-01T00:00:00", "actual": "2028-08-03T00:00:00"}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.2465753424657534, 10.686479421413765, 571.468966781484].

## Решение de28d71bb2365330d3a59de8

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_flyby_2028/nodes/de28d71bb2365330d3a59de8/final`. Изменения: `{"launch_tdb": {"requested": "2028-11-01T00:00:00", "actual": "2028-08-03T00:00:00"}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.2465753424657534, 5.578659264962637, 695.3166077128733].

## Решение 256b84da1f06a5ee6bb12ddf

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_flyby_2028/nodes/256b84da1f06a5ee6bb12ddf/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 4.847151260073188, 364.7580441797355].

## Решение 2dd220e8211fa18e19ead787

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_flyby_2028/nodes/2dd220e8211fa18e19ead787/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 2.854264629791059, 306.9815796869846].

## Решение bb35f819e73b42c44402e4b8

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_flyby_2028/nodes/bb35f819e73b42c44402e4b8/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 4.84715126005987, 364.7580441797355].

## Решение 2611bbe93475a37b815bf876

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_flyby_2028/nodes/2611bbe93475a37b815bf876/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 2.854264629762101, 306.98154093988427].
