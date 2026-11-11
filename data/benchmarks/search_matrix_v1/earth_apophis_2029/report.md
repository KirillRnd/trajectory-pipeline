# Граф поиска траекторий

Статус: finished. Узлов: 7; принятых: 5; попаданий в кеш: 5.

Принятые решения сохранены независимо от неудач их улучшения. Изменения относятся к исходной постановке. Физическая недостижимость не доказывается.

| Узел | Операция | Статус | Причина |
|---|---|---|---|
| 4801b96f480e5a1eb4a9f01d | reference | completed |  |
| 89bfa20c65fee8fc23e4c957 | release | completed |  |
| 7cfb5368528e28305f0414f3 | cold | completed |  |
| 9e36965099b7ca4893a480b9 | release | completed |  |
| 69428d0ccf57f72055740daa | r_transfer | failed | RuntimeError: active: Exact independent replay failed: {'passed': False, 'position_residual_m': 8552855686.082364, 'velocity_residual_m_s': 1827.6628277133048, 'parameter_audit': {'passed': True, 'configuration_sha256': 'f8fc5680270ac96b06b2c5e09ef85d88267e3a2dfd5c9b6e6482be165788690d', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2029-05-15T12:00:00', 'tof_days': 422.6618015373437, 'departure': 'Earth', 'target': 'Apophis', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.025), 'thrust_to_requested_ratio': np.float64(1.0), 'alpha': 1.0, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': True, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': True}, 'trajectory_difference_m': 2.196106718849908, 'velocity_difference_m_s': 5.189377375769566e-07, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 0.0845254389809495, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 2655.3848577414137, 'switching_sign_violation': 0.0071698943293934305, 'switching_node_residual': 0.0071698943293934305, 'minimum_mass_kg': 143.32452952022766, 'fuel_kg': 12.675470479772343, 'mass_difference_kg': 1.7319479184152442e-13, 'stored_thrust_error_N': 0.0, 'mass_balance_error_kg': np.float64(1.5987211554602254e-13)}; free: Exact independent replay failed: {'passed': False, 'position_residual_m': 13524808165.195374, 'velocity_residual_m_s': 712.0286302880046, 'parameter_audit': {'passed': True, 'configuration_sha256': 'f8fc5680270ac96b06b2c5e09ef85d88267e3a2dfd5c9b6e6482be165788690d', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2029-05-15T12:00:00', 'tof_days': 422.6618015373437, 'departure': 'Earth', 'target': 'Apophis', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.025), 'thrust_to_requested_ratio': np.float64(1.0), 'alpha': 1.0, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': True, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': True}, 'trajectory_difference_m': 0.9245365531163799, 'velocity_difference_m_s': 2.8116333985805465e-07, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 0.09260165301765932, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 1625.0770225037684, 'switching_sign_violation': 0.6338975823615512, 'switching_node_residual': 0.001953281434216598, 'minimum_mass_kg': 129.48346570151048, 'fuel_kg': 26.516534298489507, 'mass_difference_kg': 5.195843755245733e-13, 'stored_thrust_error_N': 0.0, 'mass_balance_error_kg': np.float64(4.654054919228656e-13)} |
| 6b6dda1396be66289cf69c03 | r_release | failed | TimeoutError: Free-duration integration budget reached |
| 7c448e450d17d8de7ff5eb46 | reference | completed |  |

## Решение 4801b96f480e5a1eb4a9f01d

Артефакт: `runs/search_matrix_v1/earth_apophis_2029/nodes/4801b96f480e5a1eb4a9f01d/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 18.640351096134413, 422.6618015373437].

## Решение 89bfa20c65fee8fc23e4c957

Артефакт: `runs/search_matrix_v1/earth_apophis_2029/nodes/89bfa20c65fee8fc23e4c957/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 18.64035109613448, 422.6618015373437].

## Решение 7cfb5368528e28305f0414f3

Артефакт: `runs/search_matrix_v1/earth_apophis_2029/nodes/7cfb5368528e28305f0414f3/final`. Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.0, 9.211762028295203, 422.6618015373437].

## Решение 9e36965099b7ca4893a480b9

Артефакт: `runs/search_matrix_v1/earth_apophis_2029/nodes/9e36965099b7ca4893a480b9/final`. Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.0, 9.211762028294977, 422.6618015373437].

## Решение 7c448e450d17d8de7ff5eb46

Артефакт: `runs/search_matrix_v1/earth_apophis_2029/nodes/7c448e450d17d8de7ff5eb46/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 18.640351096134413, 422.6618015373437].
