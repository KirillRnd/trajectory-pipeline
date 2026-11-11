# Граф поиска траекторий

Статус: finished. Узлов: 7; принятых: 4; попаданий в кеш: 6.

Принятые решения сохранены независимо от неудач их улучшения. Изменения относятся к исходной постановке. Физическая недостижимость не доказывается.

| Узел | Операция | Статус | Причина |
|---|---|---|---|
| 40ef4fa3c505aaa0dd4e75c0 | reference | completed |  |
| c218561a082f6f32f36caed5 | release | failed | TimeoutError: Free-duration integration budget reached |
| 5c1538b3374e96954a3d3ce9 | cold | completed |  |
| bf77b0540a62ab8268d72eec | release | completed |  |
| 782f176eb45cf20102b81e01 | r_transfer | failed | RuntimeError: active: Exact independent replay failed: {'passed': False, 'position_residual_m': 65127565.275247715, 'velocity_residual_m_s': 21.498148346972737, 'parameter_audit': {'passed': True, 'configuration_sha256': '679fe996dcde174aadad721d35790ca6d2021b5e116dc0d38a44588f350fa7bc', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2029-01-30T00:00:00', 'tof_days': 500.0, 'departure': 'Earth', 'target': 'Mars', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.025), 'thrust_to_requested_ratio': np.float64(1.0), 'alpha': 1.0, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': True, 'exhaust_velocity_m_s': np.float64(19999.999999999996)}, 'geometry': None, 'final_admission': True}, 'trajectory_difference_m': 4.629976673363121, 'velocity_difference_m_s': 4.2527396289385616e-07, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 0.001528333006300278, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 3038.0406508961078, 'switching_sign_violation': 0.3026674671190252, 'switching_node_residual': 6.857240375419694e-07, 'minimum_mass_kg': 121.52493713533386, 'fuel_kg': 34.47506286466614, 'mass_difference_kg': 2.078337502098293e-13, 'stored_thrust_error_N': 0.0, 'mass_balance_error_kg': np.float64(1.7053025658242404e-13)}; free: Exact independent replay failed: {'passed': False, 'position_residual_m': 1.5313547593699794, 'velocity_residual_m_s': 1.6125465501078407e-07, 'parameter_audit': {'passed': True, 'configuration_sha256': '679fe996dcde174aadad721d35790ca6d2021b5e116dc0d38a44588f350fa7bc', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2029-01-30T00:00:00', 'tof_days': 500.0, 'departure': 'Earth', 'target': 'Mars', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.025), 'thrust_to_requested_ratio': np.float64(1.0), 'alpha': 1.0, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': True, 'exhaust_velocity_m_s': np.float64(19999.999999999996)}, 'geometry': None, 'final_admission': True}, 'trajectory_difference_m': 1.5076272895257454, 'velocity_difference_m_s': 1.586707772138711e-07, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 1.1700705083009598e-11, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 5861.030324487887, 'switching_sign_violation': 1.0998646236434113, 'switching_node_residual': 2.0234994336403354e-12, 'minimum_mass_kg': 124.42567800271671, 'fuel_kg': 31.574321997283295, 'mass_difference_kg': 1.7319479184152442e-13, 'stored_thrust_error_N': 0.0, 'mass_balance_error_kg': np.float64(1.9539925233402755e-13)} |
| e1f6e710eb2ea2e3a317b9cd | r_release | failed | RuntimeError: active: Free-duration physical replay failed: {'passed': False, 'position_residual_m': 0.9354905014022049, 'velocity_residual_m_s': 3.122099286213288e-07, 'parameter_audit': {'passed': True, 'configuration_sha256': 'b09ef4828892699068e9238149a2570c773a4c4e6be9d106e753442cd833c0ea', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2029-01-30T00:00:00', 'tof_days': 505.6371325076202, 'departure': 'Earth', 'target': 'Mars', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.025), 'thrust_to_requested_ratio': np.float64(1.0), 'alpha': 1.0, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': True, 'exhaust_velocity_m_s': np.float64(19999.999999999996)}, 'geometry': None, 'final_admission': True}, 'trajectory_difference_m': 1.6029394198730629, 'velocity_difference_m_s': 2.9492452112962504e-07, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 1.2190533912249933e-11, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 3000.0000000000105, 'switching_sign_violation': 0.31728665055396876, 'switching_node_residual': 6.546154297643929e-11, 'minimum_mass_kg': 121.17196125001527, 'fuel_kg': 34.82803874998472, 'mass_difference_kg': 4.3298697960381105e-13, 'stored_thrust_error_N': 0.0, 'mass_balance_error_kg': np.float64(3.979039320256561e-13)}; free: Free-duration optimizer: Positive directional derivative for linesearch |
| 95845bcad451f7bd3be40d44 | reference | completed |  |

## Решение 40ef4fa3c505aaa0dd4e75c0

Артефакт: `runs/search_matrix_v1/earth_mars_2028/nodes/40ef4fa3c505aaa0dd4e75c0/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 22.898851471019444, 500.0].

## Решение 5c1538b3374e96954a3d3ce9

Артефакт: `runs/search_matrix_v1/earth_mars_2028/nodes/5c1538b3374e96954a3d3ce9/final`. Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.0, 11.695753835267116, 500.0].

## Решение bf77b0540a62ab8268d72eec

Артефакт: `runs/search_matrix_v1/earth_mars_2028/nodes/bf77b0540a62ab8268d72eec/final`. Изменения: `{"tof_days": {"requested": 500.0, "actual": 659.526155907966}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [2.319052311815932, 11.472716576543503, 659.526155907966].

## Решение 95845bcad451f7bd3be40d44

Артефакт: `runs/search_matrix_v1/earth_mars_2028/nodes/95845bcad451f7bd3be40d44/final`. Изменения: `{}`.
Критерии [изменения условий, топливо кг, длительность сутки]: [0.0, 22.898851471019444, 500.0].
