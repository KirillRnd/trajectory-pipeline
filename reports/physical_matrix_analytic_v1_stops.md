# Где остановилась траекторная цепочка

Отчёт читает сохранённые результаты и ничего не пересчитывает. Несходимость допустима; физическая недостижимость этими остановками не доказана.

| Случай | Статус | Блок | Причина остановки | Последняя принятая модель |
|---|---|---|---|---|
| earth_venus_2032 | completed | Финальная проверка | ПСИ принята | — |
| earth_mars_2028 | completed | Финальная проверка | ПСИ принята | — |
| earth_apophis_2029 | completed | Финальная проверка | ПСИ принята | — |
| earth_eros_2029 | partial | ПСИ: введение массы | Исчерпан бюджет этапа | α=0.5, β=0.9875, F/Fзад=3.269757 |
| earth_bennu_2029 | completed | Финальная проверка | ПСИ принята | — |
| earth_ryugu_2028 | completed | Финальная проверка | ПСИ принята | — |
| earth_polyhymnia_2029 | partial | ПСИ: введение массы | Исчерпан бюджет этапа | α=0.5, β=0.9996094, F/Fзад=1.530273 |
| earth_ceres_2030 | partial | ПСИ: точное управление | Исчерпан бюджет этапа | α=0.5148438, β=1, F/Fзад=1 |
| earth_mercury_2029 | partial | ПСИ: введение массы | Исчерпан бюджет этапа | α=0.5, β=0.9445312, F/Fзад=6.151302 |
| earth_jupiter_2028 | failed | Пазов: предел ускорения | Ошибка программы | α=0, β=0, F/Fзад=1.929865 |
| venus_earth_2029 | partial | ПСИ: введение массы | Исчерпан бюджет этапа | α=0.5, β=0.9966011, F/Fзад=25.81371 |
| earth_mars_flyby_2028 | completed | Финальная проверка | ПСИ принята | — |
| earth_2015re36_2028 | partial | ПСИ: физический предел тяги | Исчерпан бюджет этапа | α=0.5, β=1, F/Fзад=1.106558 |
| earth_saturn_flyby_2028 | partial | Начальная дополнительная скорость | Решение не получено при минимальном шаге | — |
| earth_mars_2029 | partial | ПСИ: введение массы | Исчерпан бюджет этапа | α=0.5, β=0.9996094, F/Fзад=15.00415 |

## earth_eros_2029

Блок: **ПСИ: введение массы**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/physical_matrix_analytic_v1/earth_eros_2029/stage_psi/mass/point_0011`.


## earth_polyhymnia_2029

Блок: **ПСИ: введение массы**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/physical_matrix_analytic_v1/earth_polyhymnia_2029/stage_psi/mass/point_0013`.


## earth_ceres_2030

Блок: **ПСИ: точное управление**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached`.

Последний проверенный артефакт: `data/benchmarks/physical_matrix_analytic_v1/earth_ceres_2030/stage_psi/fuel/point_0007`.


## earth_mercury_2029

Блок: **ПСИ: введение массы**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/physical_matrix_analytic_v1/earth_mercury_2029/stage_psi/mass/point_0013`.


## earth_jupiter_2028

Блок: **Пазов: предел ускорения**. Ошибка программы.

Основание: `TypeError: unsupported operand type(s) for +=: 'cell' and 'int'`.

Последняя отклонённая попытка: `RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached`.

Последний проверенный артефакт: `data/benchmarks/physical_matrix_analytic_v1/earth_jupiter_2028/stage_pazov/limit/point_0006`.


## venus_earth_2029

Блок: **ПСИ: введение массы**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; active shooting: Required step size is less than spacing between numbers.; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached`.

Последний проверенный артефакт: `data/benchmarks/physical_matrix_analytic_v1/venus_earth_2029/stage_psi/mass/point_0021`.


## earth_2015re36_2028

Блок: **ПСИ: физический предел тяги**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached`.

Последний проверенный артефакт: `data/benchmarks/physical_matrix_analytic_v1/earth_2015re36_2028/stage_psi/limit/point_0010`.


## earth_saturn_flyby_2028

Блок: **Начальная дополнительная скорость**. Решение не получено при минимальном шаге.

Основание: `minimum_step`.

Последняя отклонённая попытка: `RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 3502.452195654816, 'velocity_residual_m_s': 12375.987126770508, 'trajectory_difference_m': 3502.4521909522105, 'velocity_difference_m_s': 7.824416948155355e-05, 'free_velocity_transversality': 1.8331674784407398e-10, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}`.

Последний проверенный артефакт: `data/benchmarks/physical_matrix_analytic_v1/earth_saturn_flyby_2028/stage_departure/point_0003`.


## earth_mars_2029

Блок: **ПСИ: введение массы**. Исчерпан бюджет этапа.

Основание: `time_budget`.

Последняя отклонённая попытка: `RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 23.108690679353323, 'velocity_residual_m_s': 3.441137672341599e-05, 'parameter_audit': {'passed': True, 'configuration_sha256': '38603cdb963b19f5e10d136ab2ce6528b7dcbe6e5a4fa80acd419df556b86267', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2029-09-01T00:00:00', 'tof_days': 300, 'departure': 'Earth', 'target': 'Mars', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.3751037388772162), 'thrust_to_requested_ratio': np.float64(15.004149555088647), 'alpha': 0.5, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': False, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 28.382663618027543, 'velocity_difference_m_s': 4.122468806607114e-05, 'stored_throttle_error': 1.2212453270876722e-15, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 1.4991539139153227e-09, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 2999.9999999255115, 'minimum_mass_kg': 18.549756235306152, 'fuel_kg': 137.45024376469385, 'mass_difference_kg': 4.175874945833158e-08, 'stored_thrust_error_N': 4.718447854656915e-16}; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached`.

Последний проверенный артефакт: `data/benchmarks/physical_matrix_analytic_v1/earth_mars_2029/stage_psi/mass/point_0013`.
