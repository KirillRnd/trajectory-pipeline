# Границы работоспособности общей траекторной цепочки

Серия: `/workspace/data/benchmarks/physical_matrix_docker_v1`. SHA256 объявленной матрицы: `2f052032b21cc90287a6f4b18c7ddd64f652638a9b5502c75194ebe3057f15f1`.

Число постановок: 15. Единые аппарат, ограничения, допуски и настройки: **да**.

Проверяется полная цепочка ИРТ → начальная скорость → Пазов → переменная масса → точная ПСИ → независимая/Fortran-проверка. Луна исключена по поручению пользователя.

Результаты относятся к заданным датам, длительностям, аппарату и численным бюджетам. Частичный путь означает незавершённый расчёт; это не доказательство физической недостижимости. Полученная экстремаль не является доказанным глобальным минимумом.

| № | Случай | Условие | Сутки | Результат | Этап | Расход, кг | Ошибка, м |
|---:|---|---|---:|---|---|---:|---:|
| 1 | Earth → Venus | rendezvous | 390.8 | ПСИ получена | Финальная проверка | 27.6520 | 1.198 |
| 2 | Earth → Mars | rendezvous | 500 | ПСИ получена | Финальная проверка | 22.8989 | 2.928 |
| 3 | Earth → Apophis | rendezvous | 422.662 | ПСИ получена | Финальная проверка | 18.6404 | 0.919 |
| 4 | Earth → Eros | rendezvous | 400 | Частично | ПСИ: введение массы | — | — |
| 5 | Earth → Bennu | rendezvous | 500 | ПСИ получена | Финальная проверка | 32.6311 | 0.603 |
| 6 | Earth → Ryugu | rendezvous | 600 | ПСИ получена | Финальная проверка | 20.8315 | 2.326 |
| 7 | Earth → Polyhymnia | rendezvous | 900 | Частично | ПСИ: введение массы | — | — |
| 8 | Earth → Ceres | rendezvous | 1000 | Частично | ПСИ: точное управление | — | — |
| 9 | Earth → Mercury | rendezvous | 300 | Частично | ПСИ: введение массы | — | — |
| 10 | Earth → Jupiter | rendezvous | 1100 | Частично | ПСИ: введение массы | — | — |
| 11 | Venus → Earth | rendezvous | 250 | Ошибка | ПСИ: введение массы | — | — |
| 12 | Earth → Mars | flyby | 500 | ПСИ получена | Финальная проверка | 17.5096 | 3.390 |
| 13 | Earth → 2015RE36 | rendezvous | 600 | Ошибка | Пазов: предел ускорения | — | — |
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

time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 19.748318277055752, 'velocity_residual_m_s': 3.0027946786671636e-06, 'trajectory_difference_m': 44.05370918027529, 'velocity_difference_m_s': 1.6843003299335772e-06, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 1.7265150266878718e-10, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 2999.999999914147, 'minimum_mass_kg': 85.48507885737762, 'fuel_kg': 70.51492114262238, 'mass_difference_kg': 3.709728524370348e-09, 'stored_thrust_error_N': 0.0}; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.6250000000000001, "last_result": "limit/point_0006"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.999609375, "last_result": "mass/point_0013"}}`.

### 8. earth_ceres_2030

Блок **ПСИ: точное управление**. Исчерпан бюджет этапа. Параметр последнего продолжения: `0.029687500000000002`.

Последняя модель: `{'alpha': 0.51484375, 'beta': 1.0, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 1.0}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "completed_stage", "phase": "mixed_functional", "hardware_limit_reached": true, "reached_alpha": 0.5, "last_result": "functional/point_0004"}, "psi": {"status": "partial", "phase": "fuel", "reached_alpha": 0.51484375, "last_result": "fuel/point_0007"}}`.

### 9. earth_mercury_2029

Блок **ПСИ: введение массы**. Исчерпан бюджет этапа. Параметр последнего продолжения: `0.9445312499999999`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.9445312499999999, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 6.15130170571513}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.38125000000000003, "last_result": "limit/point_0006"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.9445312499999999, "last_result": "mass/point_0013"}}`.

### 10. earth_jupiter_2028

Блок **ПСИ: введение массы**. Исчерпан бюджет этапа. Параметр последнего продолжения: `0.9904296875000002`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.9904296875000002, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 1.9298649117557298}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 114.11564897052887, 'velocity_residual_m_s': 6.478680038069588e-06, 'trajectory_difference_m': 21.63526196629225, 'velocity_difference_m_s': 1.176437560069424e-06, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 7.902574373347563e-10, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 3000.0000000000077, 'minimum_mass_kg': 64.19199277579011, 'fuel_kg': 91.80800722420989, 'mass_difference_kg': 4.065574543687944e-09, 'stored_thrust_error_N': 0.0}; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.5375, "last_result": "limit/point_0006"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.9904296875000002, "last_result": "mass/point_0013"}}`.

### 11. venus_earth_2029

Блок **ПСИ: введение массы**. Ошибка программы. Параметр последнего продолжения: `0.9367187500000003`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.9367187500000003, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 25.813712544317998}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

TypeError: unsupported operand type(s) for +=: 'cell' and 'int'; RuntimeError: active: Nonpositive mass or central collision during propagation; active shooting: Required step size is less than spacing between numbers.; free: Nonpositive mass or central collision during propagation; free shooting: Required step size is less than spacing between numbers.

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.5, "last_result": "limit/point_0003"}}`.

### 13. earth_2015re36_2028

Блок **Пазов: предел ускорения**. Авария рабочего процесса. Параметр последнего продолжения: `0.7000000000000001`.

Последняя модель: `{'alpha': 0.0, 'beta': 0.0, 'variable_mass': False, 'acceleration_bound_to_hardware_ratio': 1.7976299896322636}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

Worker terminated without a terminal result; exit code -11; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}}`.

### 14. earth_saturn_flyby_2028

Блок **Начальная дополнительная скорость**. Решение не получено при минимальном шаге. Параметр последнего продолжения: `0.125`.

Последняя модель: `{}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

minimum_step; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 3502.452195654816, 'velocity_residual_m_s': 12375.987126770508, 'trajectory_difference_m': 3502.4521909522105, 'velocity_difference_m_s': 7.824416948155355e-05, 'free_velocity_transversality': 1.8331674784407398e-10, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "partial", "reached_parameter": 0.125, "last_result": "stage_departure/point_0003"}}`.

### 15. earth_mars_2029

Блок **ПСИ: введение массы**. Исчерпан бюджет этапа. Параметр последнего продолжения: `0.999609375`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.999609375, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 14.968001176695973}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.4905761718750001, "last_result": "limit/point_0014"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.999609375, "last_result": "mass/point_0013"}}`.

## Полнота

Завершено ПСИ: 6/15; остальные статусы: `{'completed': 6, 'partial': 7, 'failed': 2}`.
Целевых больших тел: 6; астероидов: 7. Это выборка геометрий, а не доказательство работоспособности для всех миссий к этим телам.

При следующем улучшении общего метода повторять ту же матрицу с едиными правилами и сравнивать результаты. Причины ограничивать подтверждённой диагностикой: бюджет, шаг продолжения, сходимость, независимые невязки или физические ограничения.
