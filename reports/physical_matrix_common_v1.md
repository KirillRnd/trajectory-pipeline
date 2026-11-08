# Границы работоспособности общей траекторной цепочки

Серия: `D:\MATLAB\asteroid_venus_AI\data\benchmarks\physical_matrix_common_v1`. SHA256 объявленной матрицы: `bc802499cb5e2c1c8578a7d21b57c9129703944196c913e152c7e9349ac71542`.

Число постановок: 15. Единые аппарат, ограничения, допуски и настройки: **да**.

Проверяется полная цепочка ИРТ → начальная скорость → Пазов → переменная масса → точная ПСИ → независимая/Fortran-проверка. Луна исключена по поручению пользователя.

Результаты относятся к заданным датам, длительностям, аппарату и численным бюджетам. Частичный путь означает незавершённый расчёт; это не доказательство физической недостижимости. Полученная экстремаль не является доказанным глобальным минимумом.

| № | Случай | Условие | Сутки | Результат | Этап | Расход, кг | Ошибка, м |
|---:|---|---|---:|---|---|---:|---:|
| 1 | Earth → Venus | rendezvous | 390.8 | ПСИ получена | final | 27.6520 | 1.499 |
| 2 | Earth → Mars | rendezvous | 500 | ПСИ получена | final | 22.8989 | 2.932 |
| 3 | Earth → Apophis | rendezvous | 422.662 | ПСИ получена | final | 18.6404 | 0.945 |
| 4 | Earth → Eros | rendezvous | 400 | Частично | psi | — | — |
| 5 | Earth → Bennu | rendezvous | 500 | ПСИ получена | final | 32.6311 | 1.184 |
| 6 | Earth → Ryugu | rendezvous | 600 | ПСИ получена | final | 20.8315 | 2.225 |
| 7 | Earth → Polyhymnia | rendezvous | 900 | Частично | psi | — | — |
| 8 | Earth → Ceres | rendezvous | 1000 | Частично | psi | — | — |
| 9 | Earth → Mercury | rendezvous | 300 | Частично | psi | — | — |
| 10 | Earth → Jupiter | rendezvous | 1100 | Частично | psi | — | — |
| 11 | Venus → Earth | rendezvous | 250 | Ошибка | psi | — | — |
| 12 | Earth → Mars | flyby | 500 | ПСИ получена | final | 17.5096 | 3.392 |
| 13 | Earth → 2015RE36 | rendezvous | 600 | Частично | psi | — | — |
| 14 | Earth → Saturn | flyby | 2200 | Частично | departure | — | — |
| 15 | Earth → Mars | rendezvous | 300 | Частично | psi | — | — |

## Условия сравнения

`{"departure_mode": "bounded_norm", "mass_kg": 156, "position_tolerance_m": 1000, "solver": {"bounded_attempt_s": 20, "budget_s": 45, "compare_seeds": true, "departure_budget_s": 60, "limit_budget_s": 60, "pazov_budget_s": 90, "psi_budget_s": 120}, "spacecraft": {"dry_mass_kg": 90, "exhaust_velocity_m_s": 20000, "thrust_N": 0.025}, "velocity_tolerance_m_s": 0.01, "vinf_max_m_s": 3000}`

Различаются тела, эпохи, длительности и явно указанные конечные условия. Не использованы индивидуальные изменения двигателя или отдельные миссионные решатели.

## Остановки

Примечания к выполнению:

- Cases 1-11 initially ran sequentially in one process with unchanged numerical settings.
- The process crashed during case 11 (Venus-Earth); Windows Application Error python311.dll, exception 0x80000003. Cause is not established; event XML is retained.
- Terminal outcomes 1-11 were preserved. Cases 12-15 were executed with identical mission/solver settings in separate worker processes using --resume --pending-only. No first-pass partial case received another numerical budget.
- All cases used the same numerical equations and correctors. Supervisor/progress reporting changed after the crash; code hashes are stored with stage summaries and continuation sessions.
- Elapsed time for case 11 is unknown and stored as null. Moon is excluded from this matrix.

### 4. earth_eros_2029

Этап `psi`, параметр последнего продолжения: `0.9875`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.9875, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 3.2697566130024702}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.42500000000000004, "last_result": "limit/point_0005"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.9875, "last_result": "mass/point_0011"}}`.

### 7. earth_polyhymnia_2029

Этап `psi`, параметр последнего продолжения: `0.999609375`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.999609375, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 1.5302732634445286}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 364.4171835787285, 'velocity_residual_m_s': 1.855196749910947e-05, 'trajectory_difference_m': 165.14560853939366, 'velocity_difference_m_s': 8.81191621743065e-06, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 2.547146613363892e-09, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 2999.9999999561724, 'minimum_mass_kg': 85.48507880160976, 'fuel_kg': 70.51492119839024, 'mass_difference_kg': 1.9954308871916737e-08, 'stored_thrust_error_N': 0.0}; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.6250000000000001, "last_result": "limit/point_0006"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.999609375, "last_result": "mass/point_0013"}}`.

### 8. earth_ceres_2030

Этап `psi`, параметр последнего продолжения: `0.029687500000000002`.

Последняя модель: `{'alpha': 0.51484375, 'beta': 1.0, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 1.0}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "completed_stage", "phase": "mixed_functional", "hardware_limit_reached": true, "reached_alpha": 0.5, "last_result": "functional/point_0004"}, "psi": {"status": "partial", "phase": "fuel", "reached_alpha": 0.51484375, "last_result": "fuel/point_0007"}}`.

### 9. earth_mercury_2029

Этап `psi`, параметр последнего продолжения: `0.8794921875000001`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.8794921875000001, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 6.151301705715131}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.38125000000000003, "last_result": "limit/point_0006"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.8794921875000001, "last_result": "mass/point_0013"}}`.

### 10. earth_jupiter_2028

Этап `psi`, параметр последнего продолжения: `0.9875`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.9875, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 1.9298649117557298}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 36.9795360524537, 'velocity_residual_m_s': 2.692739449687167e-06, 'trajectory_difference_m': 91.68852745333125, 'velocity_difference_m_s': 3.2340999368777793e-06, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 2.6548620764545133e-10, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 2999.999999904574, 'minimum_mass_kg': 64.19199278559444, 'fuel_kg': 91.80800721440556, 'mass_difference_kg': 4.500882333502432e-09, 'stored_thrust_error_N': 0.0}; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.5375, "last_result": "limit/point_0006"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.9875, "last_result": "mass/point_0010"}}`.

### 11. venus_earth_2029

Этап `psi`, параметр последнего продолжения: `None`.

Последняя модель: `{}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

Python process crashed; Windows Application Error 2026-11-05 11:40:11 Europe/Moscow: python311.dll, exception 0x80000003; process exit code 1. Cause not established.

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.5, "last_result": "limit/point_0003"}}`.

### 13. earth_2015re36_2028

Этап `psi`, параметр последнего продолжения: `0.821875`.

Последняя модель: `{'alpha': 0.5, 'beta': 1.0, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 1.106558381427435}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.7750000000000001, "last_result": "limit/point_0006"}, "psi": {"status": "partial", "phase": "physical_thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.821875, "last_result": "limit/point_0010"}}`.

### 14. earth_saturn_flyby_2028

Этап `departure`, параметр последнего продолжения: `0.125`.

Последняя модель: `{}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

minimum_step; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 3496.9344202836373, 'velocity_residual_m_s': 12375.987126732074, 'trajectory_difference_m': 3496.934415555714, 'velocity_difference_m_s': 7.812386322099952e-05, 'free_velocity_transversality': 1.8302466480970884e-10, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "partial", "reached_parameter": 0.125, "last_result": "stage_departure/point_0003"}}`.

### 15. earth_mars_2029

Этап `psi`, параметр последнего продолжения: `0.999609375`.

Последняя модель: `{'alpha': 0.5, 'beta': 0.999609375, 'variable_mass': True, 'acceleration_bound_to_hardware_ratio': 15.004149555088649}`. При β<1 масса промежуточная; отношение пределов >1 означает повышенную суррогатную тягу.

time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached

Этапы: `{"irt": {"status": "completed_stage", "last_result": "irt"}, "departure": {"status": "completed_stage", "reached_parameter": 1.0, "last_result": "stage_departure/point_0004"}, "pazov": {"status": "partial", "phase": "thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.48925781250000006, "last_result": "limit/point_0012"}, "psi": {"status": "partial", "phase": "mass", "reached_beta": 0.999609375, "last_result": "mass/point_0013"}}`.

## Полнота

Завершено ПСИ: 6/15; остальные статусы: `{'completed': 6, 'partial': 8, 'failed': 1}`.
Целевых больших тел: 6; астероидов: 7. Это выборка геометрий, а не доказательство работоспособности для всех миссий к этим телам.

При следующем улучшении общего метода повторять ту же матрицу с едиными правилами и сравнивать результаты. Причины ограничивать подтверждённой диагностикой: бюджет, шаг продолжения, сходимость, независимые невязки или физические ограничения.
