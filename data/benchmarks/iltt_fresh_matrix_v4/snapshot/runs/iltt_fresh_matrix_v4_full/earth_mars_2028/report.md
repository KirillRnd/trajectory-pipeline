# Граф поиска траекторий

Статус: finished. Узлов: 32; принятых: 6; попаданий в кеш: 9.

Принятые решения сохранены независимо от неудач их улучшения. Изменения относятся к исходной постановке. Физическая недостижимость не доказывается.

| Узел | Операция | Статус | Причина |
|---|---|---|---|
| c69b70cf9b5a1cb6476734b5 | cold | partial |  |
| 7437b90ad6c53674e9c6cf4f | intermediate_release | intermediate |  |
| c132aae3cddc6b387147cf27 | physical_continue | completed |  |
| 7801555b0082bc6dc0032c14 | release | failed | TimeoutError: Free-duration integration budget reached |
| aa854ff1ac9be096c824b62e | cold | completed |  |
| 7a61d9f079d46d21d8f078bc | release | failed | TimeoutError: Free-duration integration budget reached |
| 5f411778ec7aad59365c5421 | cold | initial_failed | ValueError: ILTT phase/orbit correction failed: The iteration is not making good progress, as measured by the   improvement from the last five Jacobian evaluations.; residual=[-3.31871510e-02 -4.73406442e-06 -1.76611155e-03 -2.41506660e-04  -3.58468871e-03  6.33964753e-03]; x=[-0.10140269 -0.23550478  0.88975989  5.69598831  1.54314017  4.49248233]; x0=[-0.09679823 -0.22388401  0.86343997  5.86653688  1.53517239  4.4149297 ] |
| 4d5a7f8b187769e47eb5d3bd | cold | initial_failed | ValueError: ILTT phase/orbit correction failed: The iteration is not making good progress, as measured by the   improvement from the last five Jacobian evaluations.; residual=[-3.31871510e-02 -4.73406442e-06 -1.76611155e-03 -2.41506660e-04  -3.58468871e-03  6.33964753e-03]; x=[-0.10140269 -0.23550478  0.88975989  5.69598831  1.54314017  4.49248233]; x0=[-0.09679823 -0.22388401  0.86343997  5.86653688  1.53517239  4.4149297 ] |
| 5c332602c5249d8047f0a3e5 | cold | initial_failed | ValueError: ILTT phase/orbit correction failed: The iteration is not making good progress, as measured by the   improvement from the last five Jacobian evaluations.; residual=[ 1.10845680e-02  1.13080064e-03  1.92698447e-03  3.62936440e-05   1.22435114e-03 -2.95927351e-03]; x=[-0.05515973 -0.27910212  0.78816032  5.75734218  1.42706958  2.12972671]; x0=[-0.05944244 -0.22055957  0.8634436   5.86729346  1.54562309  1.98059743] |
| df15dda2ac1a8104acb40285 | cold | partial |  |
| 316be182c16e430cb200d640 | intermediate_release | intermediate |  |
| c676314cf01957c04735a73b | physical_continue | partial |  |
| e985e7a46f1286f720478fb4 | intermediate_release | intermediate |  |
| b360e347dfa6b0cab66b8ec9 | physical_continue | partial |  |
| 151d217a5b2d14739d4d84fb | cold | completed |  |
| bf61d9a2567e8ab882091345 | release | completed |  |
| 8812b38e293ffffcf4c2cade | cold | partial |  |
| 081ea69aaeabbee4d10de1cb | intermediate_release | intermediate |  |
| 7eedc03ecbc92d0d93e2bcb3 | physical_continue | partial |  |
| db890717410fda713a2ce5d4 | intermediate_release | failed | RuntimeError: No independently verified changed-duration intermediate; see trials.json |
| c4fd4bc358041f52dbee1931 | physical_continue | partial |  |
| 41ff2a3e4264dbd978db589a | cold | partial |  |
| 08e89e025383a6f73883911d | intermediate_release | intermediate |  |
| 4b10a43dedaaa271866f7d9e | physical_continue | completed |  |
| 4cc9cef30cd788e4889897c8 | release | failed | TimeoutError: Free-duration integration budget reached |
| 722068d91713ec8314c80039 | cold | partial |  |
| 536eed03256e36fb4717327b | intermediate_release | intermediate |  |
| afe2b29ec3353535b2910df2 | physical_continue | completed |  |
| adde2fac99bec8d94cd7e004 | release | failed | RuntimeError: active: Free-duration physical replay failed: {'passed': False, 'position_residual_m': 2.3622325309632655, 'velocity_residual_m_s': 2.3082525579869577e-07, 'parameter_audit': {'passed': True, 'configuration_sha256': '6d076245f3b4e93a6fb97d7cf2c8716c08bc1d70ede770329beba0e4f470bda7', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2028-11-01T00:00:00', 'tof_days': 409.50946026234607, 'departure': 'Earth', 'target': 'Mars', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.025), 'thrust_to_requested_ratio': np.float64(1.0), 'alpha': 1.0, 'beta': 1, 'variable_mass': True, 'hardware_limit_reached': True, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': True}, 'trajectory_difference_m': 2.775404938455215, 'velocity_difference_m_s': 3.3173474940566905e-07, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 1.769683490985138e-11, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 3000.0000000000027, 'switching_sign_violation': 4.544200753436958e-05, 'switching_node_residual': 3.4753965257050716e-12, 'minimum_mass_kg': 133.102739085885, 'fuel_kg': 22.89726091411501, 'mass_difference_kg': 2.5979218776228663e-13, 'stored_thrust_error_N': 0.0, 'mass_balance_error_kg': np.float64(1.9184653865522705e-13)}; free: Free-duration optimizer: Positive directional derivative for linesearch |
| c6a3d434e057bfea78cd4f4f | cold | initial_failed | ValueError: ILTT phase/orbit correction failed: The iteration is not making good progress, as measured by the   improvement from the last five Jacobian evaluations.; residual=[-3.31871510e-02 -4.73406442e-06 -1.76611155e-03 -2.41506660e-04  -3.58468871e-03  6.33964753e-03]; x=[-0.10140269 -0.23550478  0.88975989  5.69598831  1.54314017  4.49248233]; x0=[-0.09679823 -0.22388401  0.86343997  5.86653688  1.53517239  4.4149297 ] |
| dbb9feb8985c6475a958ffc2 | cold | initial_failed | No independently verified IRT; see diagnostics.json for each attempted branch/corrector |
| 9820bb644e08aa62bfe69fb7 | cold | initial_failed | ValueError: math domain error |

## Решение c132aae3cddc6b387147cf27

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_2028/nodes/c132aae3cddc6b387147cf27/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 31.56202497979481, 381.19221822213365].

## Решение aa854ff1ac9be096c824b62e

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_2028/nodes/aa854ff1ac9be096c824b62e/final`. Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.0, 12.09267721620255, 364.7580441797355].

## Решение 151d217a5b2d14739d4d84fb

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_2028/nodes/151d217a5b2d14739d4d84fb/final`. Изменения: `{"launch_tdb": {"requested": "2028-11-01T00:00:00", "actual": "2028-08-03T00:00:00"}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.2465753424657534, 28.959343133618855, 571.468966781484].

## Решение bf61d9a2567e8ab882091345

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_2028/nodes/bf61d9a2567e8ab882091345/final`. Изменения: `{"launch_tdb": {"requested": "2028-11-01T00:00:00", "actual": "2028-08-03T00:00:00"}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.2465753424657534, 26.532393839914434, 634.9358181120356].

## Решение 4b10a43dedaaa271866f7d9e

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_2028/nodes/4b10a43dedaaa271866f7d9e/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 22.961926770456664, 405.5722450303945].

## Решение afe2b29ec3353535b2910df2

Артефакт: `runs/iltt_fresh_matrix_v4_full/earth_mars_2028/nodes/afe2b29ec3353535b2910df2/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 22.908847718975906, 407.7858312349366].
