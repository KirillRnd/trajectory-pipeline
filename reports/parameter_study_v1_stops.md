# Где остановилась траекторная цепочка

Отчёт читает сохранённые результаты и ничего не пересчитывает. Несходимость допустима; физическая недостижимость этими остановками не доказана.

| Случай | Статус | Блок | Причина остановки | Последняя принятая модель |
|---|---|---|---|---|
| earth_venus_2032__reference | completed | Финальная проверка | ПСИ принята | — |
| earth_venus_2032__thrust_x2 | partial | ПСИ: точное управление | Решение не получено при минимальном шаге | α=0.8, β=1, F/Fзад=1 |
| earth_venus_2032__exhaust_x2 | completed | Финальная проверка | ПСИ принята | — |
| earth_venus_2032__mass_x2 | failed | ПСИ: физический предел тяги | Ошибка программы | α=0.5, β=1, F/Fзад=1.774877 |
| earth_venus_2032__launch_plus_90d | failed | ПСИ: физический предел тяги | Авария рабочего процесса | α=0.5, β=1, F/Fзад=1.134263 |
| earth_venus_2032__duration_x1p2 | completed | Финальная проверка | ПСИ принята | — |
| earth_mars_2028__reference | completed | Финальная проверка | ПСИ принята | — |
| earth_mars_2028__thrust_x2 | completed | Финальная проверка | ПСИ принята | — |
| earth_mars_2028__exhaust_x2 | completed | Финальная проверка | ПСИ принята | — |
| earth_mars_2028__mass_x2 | partial | ПСИ: физический предел тяги | Исчерпан бюджет этапа | α=0.5, β=1, F/Fзад=1.12152 |
| earth_mars_2028__launch_plus_90d | completed | Финальная проверка | ПСИ принята | — |
| earth_mars_2028__duration_x1p2 | completed | Финальная проверка | ПСИ принята | — |
| earth_apophis_2029__reference | completed | Финальная проверка | ПСИ принята | — |
| earth_apophis_2029__thrust_x2 | completed | Финальная проверка | ПСИ принята | — |
| earth_apophis_2029__exhaust_x2 | completed | Финальная проверка | ПСИ принята | — |
| earth_apophis_2029__mass_x2 | partial | ПСИ: физический предел тяги | Исчерпан бюджет этапа | α=0.5, β=1, F/Fзад=1.141419 |
| earth_apophis_2029__launch_plus_90d | completed | Финальная проверка | ПСИ принята | — |
| earth_apophis_2029__duration_x1p2 | completed | Финальная проверка | ПСИ принята | — |
| earth_ceres_2030__reference | partial | ПСИ: точное управление | Исчерпан бюджет этапа | α=0.5148438, β=1, F/Fзад=1 |
| earth_ceres_2030__thrust_x2 | partial | ПСИ: введение массы | Исчерпан бюджет этапа | α=0.5, β=0.615625, F/Fзад=1 |
| earth_ceres_2030__exhaust_x2 | completed | Финальная проверка | ПСИ принята | — |
| earth_ceres_2030__mass_x2 | partial | ПСИ: физический предел тяги | Исчерпан бюджет этапа | α=0.5, β=1, F/Fзад=1.677534 |
| earth_ceres_2030__launch_plus_90d | partial | ПСИ: точное управление | Исчерпан бюджет этапа | α=0.815625, β=1, F/Fзад=1 |
| earth_ceres_2030__duration_x1p2 | partial | ПСИ: введение массы | Исчерпан бюджет этапа | α=0.07578125, β=0.3, F/Fзад=1 |

## earth_venus_2032__thrust_x2

Блок: **ПСИ: точное управление**. Решение не получено при минимальном шаге.

Основание: `minimum_step`.

Последняя отклонённая попытка: `RuntimeError: free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_v1/earth_venus_2032__thrust_x2/stage_psi/fuel/point_0002`.


## earth_venus_2032__mass_x2

Блок: **ПСИ: физический предел тяги**. Ошибка программы.

Основание: `TypeError: unsupported operand type(s) for +=: 'cell' and 'int'`.

Последняя отклонённая попытка: `не записана`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_v1/earth_venus_2032__mass_x2/stage_psi/limit/point_0000`.


## earth_venus_2032__launch_plus_90d

Блок: **ПСИ: физический предел тяги**. Авария рабочего процесса.

Основание: `Worker terminated without a terminal result; exit code -11`.

Последняя отклонённая попытка: `RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 216626277.73472428, 'velocity_residual_m_s': 23.645066652980404, 'parameter_audit': {'passed': True, 'configuration_sha256': 'a69a2f0c78d91496a75afd000f1f6c8e2d49947902c09bcf0871cc318d234458', 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2033-01-30T00:00:00', 'tof_days': 390.8, 'departure': 'Earth', 'target': 'Venus', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.027912327277517735), 'thrust_to_requested_ratio': np.float64(1.1164930911007094), 'alpha': 0.5, 'beta': 1.0, 'variable_mass': True, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 1.2810692240709642, 'velocity_difference_m_s': 4.831053598703014e-07, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 1.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 0.0018708760578194544, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 3025.3288638219838, 'minimum_mass_kg': 108.8768459997668, 'fuel_kg': 47.1231540002332, 'mass_difference_kg': 2.424727085781342e-13, 'stored_thrust_error_N': 0.0}; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_v1/earth_venus_2032__launch_plus_90d/stage_psi/limit/point_0005`.


## earth_mars_2028__mass_x2

Блок: **ПСИ: физический предел тяги**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_v1/earth_mars_2028__mass_x2/stage_psi/limit/point_0006`.


## earth_apophis_2029__mass_x2

Блок: **ПСИ: физический предел тяги**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_v1/earth_apophis_2029__mass_x2/stage_psi/limit/point_0018`.


## earth_ceres_2030__reference

Блок: **ПСИ: точное управление**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_v1/earth_ceres_2030__reference/stage_psi/fuel/point_0007`.


## earth_ceres_2030__thrust_x2

Блок: **ПСИ: введение массы**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_v1/earth_ceres_2030__thrust_x2/stage_psi/mass/point_0010`.


## earth_ceres_2030__mass_x2

Блок: **ПСИ: физический предел тяги**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 70.56291161325154, 'velocity_residual_m_s': 1.641700669723347e-06, 'parameter_audit': {'passed': True, 'configuration_sha256': 'be81ec5fbaf04923c78960e44cb05fc4e17851f990a76760ce5dde93e2eb1c6e', 'requested': {'mass_kg': 312, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 180, 'launch_tdb': '2030-02-01T00:00:00', 'tof_days': 1000, 'departure': 'Earth', 'target': 'Ceres', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.04144447921179667), 'thrust_to_requested_ratio': np.float64(1.6577791684718668), 'alpha': 0.5, 'beta': 1.0, 'variable_mass': True, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 104.11601550731643, 'velocity_difference_m_s': 4.543084536796978e-06, 'stored_throttle_error': 7.327471962526033e-15, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 4.85782214548046e-10, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 3000.0000000000878, 'minimum_mass_kg': 179.47950102137887, 'fuel_kg': 132.52049897862113, 'mass_difference_kg': 1.917969516540552e-08, 'stored_thrust_error_N': 3.0357660829594124e-16}; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_v1/earth_ceres_2030__mass_x2/stage_psi/limit/point_0008`.


## earth_ceres_2030__launch_plus_90d

Блок: **ПСИ: точное управление**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_v1/earth_ceres_2030__launch_plus_90d/stage_psi/fuel/point_0008`.


## earth_ceres_2030__duration_x1p2

Блок: **ПСИ: введение массы**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_v1/earth_ceres_2030__duration_x1p2/stage_psi/mass/point_0002`.
