# Граф поиска траекторий

Статус: finished. Узлов: 6; принятых: 3; попаданий в кеш: 4.

Принятые решения сохранены независимо от неудач их улучшения. Изменения относятся к исходной постановке. Физическая недостижимость не доказывается.

| Узел | Операция | Статус | Причина |
|---|---|---|---|
| f35658b2b98f6d968a8fdee2 | reference | completed |  |
| 909a2dfbf2e47c5e9e08b47e | release | completed |  |
| 50a9dc3715a1f83cd60af23e | cold | partial |  |
| 5bce4b46396d67bf3e25bc0c | r_transfer | failed | RuntimeError: active: Exact independent replay failed: {'passed': False, 'position_residual_m': 1.8613458180816123, 'velocity_residual_m_s': 3.1915369334318667e-07, 'parameter_audit': {'passed': True, 'configuration_sha256': '6b43f61ee215812c626a3f6bb88732501054b16143dbf89db9393ffd51e49ac8', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2028-08-30T00:00:00', 'tof_days': 600.0, 'departure': 'Earth', 'target': 'Ryugu', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.025), 'thrust_to_requested_ratio': np.float64(1.0), 'alpha': 1.0, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': True, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': True}, 'trajectory_difference_m': 1.858404914957922, 'velocity_difference_m_s': 3.2010977364511723e-07, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 1.6839944343354065e-11, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 2999.999999999984, 'switching_sign_violation': 0.46256044054334516, 'switching_node_residual': 2.8568821147159472e-11, 'minimum_mass_kg': 123.60404610112343, 'fuel_kg': 32.39595389887657, 'mass_difference_kg': 4.156675004196586e-13, 'stored_thrust_error_N': 0.0, 'mass_balance_error_kg': np.float64(3.979039320256561e-13)}; free: Exact independent replay failed: {'passed': False, 'position_residual_m': 7897014815.74404, 'velocity_residual_m_s': 837.3952601434099, 'parameter_audit': {'passed': True, 'configuration_sha256': '6b43f61ee215812c626a3f6bb88732501054b16143dbf89db9393ffd51e49ac8', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2028-08-30T00:00:00', 'tof_days': 600.0, 'departure': 'Earth', 'target': 'Ryugu', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.025), 'thrust_to_requested_ratio': np.float64(1.0), 'alpha': 1.0, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': True, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': True}, 'trajectory_difference_m': 0.6967104153973551, 'velocity_difference_m_s': 1.8028101148264304e-07, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 0.059428132282862256, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 5666.199295851775, 'switching_sign_violation': 0.7944379318165301, 'switching_node_residual': 0.006196985929999791, 'minimum_mass_kg': 132.99875797162338, 'fuel_kg': 23.00124202837663, 'mass_difference_kg': 3.9834802123550617e-13, 'stored_thrust_error_N': 0.0, 'mass_balance_error_kg': np.float64(3.836930773104541e-13)} |
| 0ef1c15c485308a604b4ecf8 | r_release | failed | TimeoutError: Free-duration integration budget reached |
| fa9625637441138eb15388a3 | reference | completed |  |

## Решение f35658b2b98f6d968a8fdee2

Артефакт: `runs/search_matrix_v1/earth_ryugu_2028/nodes/f35658b2b98f6d968a8fdee2/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 20.831503693032758, 600.0].

## Решение 909a2dfbf2e47c5e9e08b47e

Артефакт: `runs/search_matrix_v1/earth_ryugu_2028/nodes/909a2dfbf2e47c5e9e08b47e/final`. Изменения: `{"tof_days": {"requested": 600.0, "actual": 656.3187285322039}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.09386454755367302, 17.32092170073716, 656.3187285322039].

## Решение fa9625637441138eb15388a3

Артефакт: `runs/search_matrix_v1/earth_ryugu_2028/nodes/fa9625637441138eb15388a3/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 20.831503693032758, 600.0].
