# Граф поиска траекторий

Статус: finished. Узлов: 6; принятых: 3; попаданий в кеш: 4.

Принятые решения сохранены независимо от неудач их улучшения. Изменения относятся к исходной постановке. Физическая недостижимость не доказывается.

| Узел | Операция | Статус | Причина |
|---|---|---|---|
| 0f9e122b85679c12fe17e6e2 | reference | completed |  |
| ee324b115719cece679e3807 | release | completed |  |
| ddd6f120b3a5e2ee44d88a58 | cold | partial |  |
| 5cedb03f754532844ae401d7 | r_transfer | failed | RuntimeError: free: Exact independent replay failed: {'passed': False, 'position_residual_m': 1840175469.8962452, 'velocity_residual_m_s': 261.15697016424025, 'parameter_audit': {'passed': True, 'configuration_sha256': '018e49c5760235134faab9d4a91ff0d2738bc84796534736ed974be733e6a5a6', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2033-01-30T00:00:00', 'tof_days': 390.8, 'departure': 'Earth', 'target': 'Venus', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.025), 'thrust_to_requested_ratio': np.float64(1.0), 'alpha': 1.0, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': True, 'exhaust_velocity_m_s': np.float64(19999.999999999996)}, 'geometry': None, 'final_admission': True}, 'trajectory_difference_m': 2.627596358310222, 'velocity_difference_m_s': 6.186658253497434e-07, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 0.01522066154383208, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 4598.633941097791, 'switching_sign_violation': 0.00019540495971200468, 'switching_node_residual': 0.00019540495971200468, 'minimum_mass_kg': 116.70359044826067, 'fuel_kg': 39.29640955173933, 'mass_difference_kg': 6.235012506294879e-13, 'stored_thrust_error_N': 0.0, 'mass_balance_error_kg': np.float64(5.400124791776761e-13)}; active: Exact independent replay failed: {'passed': False, 'position_residual_m': 3138874843.568556, 'velocity_residual_m_s': 350.15378931059024, 'parameter_audit': {'passed': True, 'configuration_sha256': '018e49c5760235134faab9d4a91ff0d2738bc84796534736ed974be733e6a5a6', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2033-01-30T00:00:00', 'tof_days': 390.8, 'departure': 'Earth', 'target': 'Venus', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.025), 'thrust_to_requested_ratio': np.float64(1.0), 'alpha': 1.0, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': True, 'exhaust_velocity_m_s': np.float64(19999.999999999996)}, 'geometry': None, 'final_admission': True}, 'trajectory_difference_m': 8.405553733502932, 'velocity_difference_m_s': 2.499005019260488e-06, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 0.03342596562008721, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 3623.5085129971017, 'switching_sign_violation': 0.27269734460583966, 'switching_node_residual': 0.0015418788415513668, 'minimum_mass_kg': 117.07499716086132, 'fuel_kg': 38.925002839138685, 'mass_difference_kg': 2.078337502098293e-13, 'stored_thrust_error_N': 0.0, 'mass_balance_error_kg': np.float64(5.684341886080802e-14)} |
| 4058e9c5e5216da727d35b5c | r_release | failed | TimeoutError: Free-duration integration budget reached |
| 32ac39b8ac740ec89ae297b5 | reference | completed |  |

## Решение 0f9e122b85679c12fe17e6e2

Артефакт: `runs/search_matrix_v1/earth_venus_2032/nodes/0f9e122b85679c12fe17e6e2/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 27.65200477561803, 390.8].

## Решение ee324b115719cece679e3807

Артефакт: `runs/search_matrix_v1/earth_venus_2032/nodes/ee324b115719cece679e3807/final`. Изменения: `{"tof_days": {"requested": 390.8, "actual": 410.9696560096026}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0516111975680722, 26.86008745703935, 410.9696560096026].

## Решение 32ac39b8ac740ec89ae297b5

Артефакт: `runs/search_matrix_v1/earth_venus_2032/nodes/32ac39b8ac740ec89ae297b5/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 27.65200477561803, 390.8].
