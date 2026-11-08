# Где остановилась траекторная цепочка

Отчёт читает сохранённые результаты и ничего не пересчитывает. Несходимость допустима; физическая недостижимость этими остановками не доказана.

| Случай | Статус | Блок | Причина остановки | Последняя принятая модель |
|---|---|---|---|---|
| earth_venus_2032__reference | completed | Финальная проверка | ПСИ принята | — |
| earth_venus_2032__thrust_x2 | partial | ПСИ: точное управление | Решение не получено при минимальном шаге | α=0.8, β=1, F/Fзад=1 |
| earth_venus_2032__exhaust_x2 | completed | Финальная проверка | ПСИ принята | — |
| earth_venus_2032__mass_x2 | partial | ПСИ: физический предел тяги | Исчерпан бюджет этапа | α=0.5, β=1, F/Fзад=1.724177 |
| earth_venus_2032__launch_plus_90d | partial | ПСИ: физический предел тяги | Исчерпан бюджет этапа | α=0.5, β=1, F/Fзад=1.129821 |
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
| earth_ceres_2030__reference | failed | ПСИ: точное управление | Ошибка программы | α=0.5, β=1, F/Fзад=1 |
| earth_ceres_2030__thrust_x2 | partial | ПСИ: введение массы | Исчерпан бюджет этапа | α=0.5, β=0.9580078, F/Fзад=1 |
| earth_ceres_2030__exhaust_x2 | completed | Финальная проверка | ПСИ принята | — |
| earth_ceres_2030__mass_x2 | partial | ПСИ: физический предел тяги | Исчерпан бюджет этапа | α=0.5, β=1, F/Fзад=1.681925 |
| earth_ceres_2030__launch_plus_90d | partial | ПСИ: точное управление | Исчерпан бюджет этапа | α=0.6681641, β=1, F/Fзад=1 |
| earth_ceres_2030__duration_x1p2 | partial | ПСИ: введение массы | Исчерпан бюджет этапа | α=0.07578125, β=0.3015625, F/Fзад=1 |

## earth_venus_2032__thrust_x2

Блок: **ПСИ: точное управление**. Решение не получено при минимальном шаге.

Основание: `minimum_step`.

Последняя отклонённая попытка: `RuntimeError: free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_analytic_v1/earth_venus_2032__thrust_x2/stage_psi/fuel/point_0002`.


## earth_venus_2032__mass_x2

Блок: **ПСИ: физический предел тяги**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: free: Bounded collocation budget reached; active: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_analytic_v1/earth_venus_2032__mass_x2/stage_psi/limit/point_0009`.


## earth_venus_2032__launch_plus_90d

Блок: **ПСИ: физический предел тяги**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_analytic_v1/earth_venus_2032__launch_plus_90d/stage_psi/limit/point_0009`.


## earth_mars_2028__mass_x2

Блок: **ПСИ: физический предел тяги**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: free: Bounded collocation budget reached; active: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_analytic_v1/earth_mars_2028__mass_x2/stage_psi/limit/point_0006`.


## earth_apophis_2029__mass_x2

Блок: **ПСИ: физический предел тяги**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_analytic_v1/earth_apophis_2029__mass_x2/stage_psi/limit/point_0018`.


## earth_ceres_2030__reference

Блок: **ПСИ: точное управление**. Ошибка программы.

Основание: `TypeError: unsupported operand type(s) for +=: 'cell' and 'int'`.

Последняя отклонённая попытка: `не записана`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_analytic_v1/earth_ceres_2030__reference/stage_psi/fuel/initial`.


## earth_ceres_2030__thrust_x2

Блок: **ПСИ: введение массы**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; active shooting: Required step size is less than spacing between numbers.; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_analytic_v1/earth_ceres_2030__thrust_x2/stage_psi/mass/point_0014`.


## earth_ceres_2030__mass_x2

Блок: **ПСИ: физический предел тяги**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 39.142288161457884, 'velocity_residual_m_s': 7.181798087515012e-07, 'parameter_audit': {'passed': True, 'configuration_sha256': '7ce099eb6d3a7fc443ab9dded438734926bbb8b1e5b8bb50ce405dc0dfadfdca', 'configuration_hash_version': 2, 'requested': {'mass_kg': 312, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 180, 'launch_tdb': '2030-02-01T00:00:00', 'tof_days': 1000, 'departure': 'Earth', 'target': 'Ceres', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.04155423101966183), 'thrust_to_requested_ratio': np.float64(1.6621692407864732), 'alpha': 0.5, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': False, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 24.31386084770848, 'velocity_difference_m_s': 1.4524025723476237e-06, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 2.686149506501305e-10, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 2999.9999999994175, 'minimum_mass_kg': 179.6490528263939, 'fuel_kg': 132.3509471736061, 'mass_difference_kg': 7.506296917370037e-09, 'stored_thrust_error_N': 0.0}; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_analytic_v1/earth_ceres_2030__mass_x2/stage_psi/limit/point_0007`.


## earth_ceres_2030__launch_plus_90d

Блок: **ПСИ: точное управление**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_analytic_v1/earth_ceres_2030__launch_plus_90d/stage_psi/fuel/point_0010`.


## earth_ceres_2030__duration_x1p2

Блок: **ПСИ: введение массы**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached`.

Последний проверенный артефакт: `data/benchmarks/parameter_study_analytic_v1/earth_ceres_2030__duration_x1p2/stage_psi/mass/point_0008`.
