# Границы работоспособности общей траекторной цепочки

Серия: `/workspace/data/benchmarks/physical_matrix_analytic_v1`. SHA256 объявленной матрицы: `2f052032b21cc90287a6f4b18c7ddd64f652638a9b5502c75194ebe3057f15f1`.

Число постановок: 15. Единые аппарат, ограничения, допуски и настройки: **да**.

Проверяется полная цепочка ИРТ → начальная скорость → Пазов → переменная масса → точная ПСИ → независимая/Fortran-проверка. Луна исключена по поручению пользователя.

Результаты относятся к заданным датам, длительностям, аппарату и численным бюджетам. Частичный путь означает незавершённый расчёт; это не доказательство физической недостижимости. Полученная экстремаль не является доказанным глобальным минимумом.

| № | Случай | Условие | Сутки | Результат | Этап | Расход, кг | Ошибка, м |
|---:|---|---|---:|---|---|---:|---:|
| 1 | Earth → Venus | rendezvous | 390.8 | ПСИ получена | Финальная проверка | 27.6520 | 1.198 |
| 2 | Earth → Mars | rendezvous | 500 | ПСИ получена | Финальная проверка | 22.8989 | 2.936 |
| 3 | Earth → Apophis | rendezvous | 422.662 | ПСИ получена | Финальная проверка | 18.6404 | 0.915 |
| 4 | Earth → Eros | rendezvous | 400 | Частично | ПСИ: введение массы | — | — |
| 5 | Earth → Bennu | rendezvous | 500 | ПСИ получена | Финальная проверка | 32.6311 | 1.115 |
| 6 | Earth → Ryugu | rendezvous | 600 | ПСИ получена | Финальная проверка | 20.8315 | 2.276 |
| 7 | Earth → Polyhymnia | rendezvous | 900 | Частично | ПСИ: введение массы | — | — |
| 8 | Earth → Ceres | rendezvous | 1000 | Частично | ПСИ: точное управление | — | — |
| 9 | Earth → Mercury | rendezvous | 300 | Частично | ПСИ: введение массы | — | — |
| 10 | Earth → Jupiter | rendezvous | 1100 | Ошибка | Пазов: предел ускорения | — | — |
| 11 | Venus → Earth | rendezvous | 250 | Частично | ПСИ: введение массы | — | — |
| 12 | Earth → Mars | flyby | 500 | ПСИ получена | Финальная проверка | 17.5096 | 3.382 |
| 13 | Earth → 2015RE36 | rendezvous | 600 | Частично | ПСИ: физический предел тяги | — | — |
| 14 | Earth → Saturn | flyby | 2200 | Частично | Начальная дополнительная скорость | — | — |
| 15 | Earth → Mars | rendezvous | 300 | Частично | ПСИ: введение массы | — | — |

## Условия сравнения

`{"departure_mode": "bounded_norm", "mass_kg": 156, "position_tolerance_m": 1000, "solver": {"bounded_attempt_s": 20, "budget_s": 45, "compare_seeds": true, "departure_budget_s": 60, "limit_budget_s": 60, "pazov_budget_s": 90, "psi_budget_s": 120}, "spacecraft": {"dry_mass_kg": 90, "exhaust_velocity_m_s": 20000, "thrust_N": 0.025}, "velocity_tolerance_m_s": 0.01, "vinf_max_m_s": 3000}`

Различаются тела, эпохи, длительности и явно указанные конечные условия. Не использованы индивидуальные изменения двигателя или отдельные миссионные решатели.

## Остановки

### 4. earth_eros_2029

Блок **ПСИ: введение массы**. Исчерпан бюджет этапа. Параметр последнего продолжения: `0.9875`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.9875, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 3.2697566130024707}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.42500000000000004, "last_result": "limit/point_0005"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.9875, "last_result": "mass/point_0011"}}`.

### 7. earth_polyhymnia_2029

Блок **ПСИ: введение массы**. Исчерпан бюджет этапа. Параметр последнего продолжения: `0.999609375`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.999609375, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 1.5302732634445286}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.6250000000000001, "last_result": "limit/point_0006"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.999609375, "last_result": "mass/point_0013"}}`.

### 8. earth_ceres_2030

Блок **ПСИ: точное управление**. Исчерпан бюджет этапа. Параметр последнего продолжения: `0.029687500000000002`.

Последняя модель: `{'alpha': 0.51484375, 'beta': 1.0, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 1.0}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "completed_stage", "phase": "mixed_functional", "hardware_limit_reached": true, "reached_alpha": 0.5, "last_result": "functional/point_0004"}, "psi": {"status": "partial", "phase": "fuel", "reached_alpha": 0.51484375, "last_result": "fuel/point_0007"}}`.

### 9. earth_mercury_2029

Блок **ПСИ: введение массы**. Исчерпан бюджет этапа. Параметр последнего продолжения: `0.9445312499999999`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.9445312499999999, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 6.15130170571513}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.38125000000000003, "last_result": "limit/point_0006"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.9445312499999999, "last_result": "mass/point_0013"}}`.

### 10. earth_jupiter_2028

Блок **Пазов: предел ускорения**. Ошибка программы. Параметр последнего продолжения: `0.5375`.

Последняя модель: `{'alpha': 0.0, 'beta': 0.0, 'variable_mass': False, 'acceleration_bound_to_hardware_ratio': 1.9298649117557298}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

TypeError: unsupported operand type(s) for +=: 'cell' and 'int'; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}}`.

### 11. venus_earth_2029

Блок **ПСИ: введение массы**. Исчерпан бюджет этапа. Параметр последнего продолжения: `0.9966011047363285`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.9966011047363285, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 25.813712544317998}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Required step size is less than spacing between numbers.; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.5, "last_result": "limit/point_0003"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.9966011047363285, "last_result": "mass/point_0021"}}`.

### 13. earth_2015re36_2028

Блок **ПСИ: физический предел тяги**. Исчерпан бюджет этапа. Параметр последнего продолжения: `0.821875`.

Последняя модель: `{'alpha': 0.5, 'beta': 1.0, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 1.1065583814274353}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.7750000000000001, "last_result": "limit/point_0006"}, "psi": {"status": "partial", "phase": "physical_thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.821875, "last_result": "limit/point_0010"}}`.

### 14. earth_saturn_flyby_2028

Блок **Начальная дополнительная скорость**. Решение не получено при минимальном шаге. Параметр последнего продолжения: `0.125`.

Последняя модель: `{}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

minimum_step; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 3502.452195654816, 'velocity_residual_m_s': 12375.987126770508, 'trajectory_difference_m': 3502.4521909522105, 'velocity_difference_m_s': 7.824416948155355e-05, 'free_velocity_transversality': 1.8331674784407398e-10, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "partial", "reached_parameter": 0.125, "last_result": "stage_departure/point_0003"}}`.

### 15. earth_mars_2029

Блок **ПСИ: введение массы**. Исчерпан бюджет этапа. Параметр последнего продолжения: `0.999609375`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.999609375, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 15.004149555088649}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 23.108690679353323, 'velocity_residual_m_s': 3.441137672341599e-05, 'parameter_audit': {'passed': True, 'configuration_sha256': '38603cdb963b19f5e10d136ab2ce6528b7dcbe6e5a4fa80acd419df556b86267', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2029-09-01T00:00:00', 'tof_days': 300, 'departure': 'Earth', 'target': 'Mars', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.3751037388772162), 'thrust_to_requested_ratio': np.float64(15.004149555088647), 'alpha': 0.5, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': False, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 28.382663618027543, 'velocity_difference_m_s': 4.122468806607114e-05, 'stored_throttle_error': 1.2212453270876722e-15, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 1.4991539139153227e-09, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 2999.9999999255115, 'minimum_mass_kg': 18.549756235306152, 'fuel_kg': 137.45024376469385, 'mass_difference_kg': 4.175874945833158e-08, 'stored_thrust_error_N': 4.718447854656915e-16}; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.48925781250000006, "last_result": "limit/point_0012"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.999609375, "last_result": "mass/point_0013"}}`.

## Полнота

Завершено ПСИ: 6/15; остальные статусы: `{'completed': 6, 'partial': 8, 'failed': 1}`.
Целевых больших тел: 6; астероидов: 7. Это выборка геометрий, а не доказательство работоспособности для всех миссий к этим телам.

При следующем улучшении общего метода повторять ту же матрицу с едиными правилами и сравнивать результаты. Причины ограничивать подтверждённой диагностикой: бюджет, шаг продолжения, сходимость, независимые невязки или физические ограничения.
