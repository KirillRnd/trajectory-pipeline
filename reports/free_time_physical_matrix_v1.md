# Широкая матрица со свободной длительностью

Серия: `runs/free_time_physical_matrix_v1`. Постановок: 15. Статусы: `{'completed': 5, 'partial': 9, 'failed': 1}`.
SHA256 матрицы: `3089d1a25c6759be782abd9e84a10d43b95ba11d69f723c271af22d59da08ad6`.
Единые аппарат, допуски и численные настройки: True.

Дата старта фиксирована; длительность оптимизируется после ПСИ. Каждый дополнительный ILTT-кандидат проходит полную холодную цепочку. Принятые результаты повторно проверены интегрированием, аудитом параметров и KIAM.

| Случай | Статус | Исходное время, сут | Принятое время, сут | Топливо, кг | Последний этап |
|---|---|---:|---:|---:|---|
| earth_venus_2032 | completed | 390.8 | 410.969656 | 26.860087 | final |
| earth_mars_2028 | completed | 500 | 710.439280 | 22.216345 | final |
| earth_apophis_2029 | completed | 422.662 | 422.661802 | 18.640351 | final |
| earth_eros_2029 | partial | 400 | — | — | psi |
| earth_bennu_2029 | partial | 500 | — | — | psi |
| earth_ryugu_2028 | completed | 600 | 656.318729 | 17.320922 | final |
| earth_polyhymnia_2029 | partial | 900 | — | — | psi |
| earth_ceres_2030 | partial | 1000 | — | — | psi |
| earth_mercury_2029 | partial | 300 | — | — | psi |
| earth_jupiter_2028 | partial | 1100 | — | — | psi |
| venus_earth_2029 | partial | 250 | — | — | psi |
| earth_mars_flyby_2028 | completed | 500 | 306.981531 | 2.854265 | final |
| earth_2015re36_2028 | partial | 600 | — | — | psi |
| earth_saturn_flyby_2028 | failed | 2200 | — | — | initialization |
| earth_mars_2029 | partial | 300 | — | — | psi |

## Условия

`{"mass_kg": 156, "spacecraft": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000, "dry_mass_kg": 90}, "vinf_max_m_s": 3000, "departure_mode": "bounded_norm", "position_tolerance_m": 1000, "velocity_tolerance_m_s": 0.01, "solver": {"budget_s": 45, "compare_seeds": true, "departure_budget_s": 60, "limit_budget_s": 60, "pazov_budget_s": 90, "psi_budget_s": 120, "bounded_attempt_s": 20, "free_time_budget_s": 120}}`

Интервалы длительности явно сохранены для каждой строки в JSON. Незавершённая цепочка не доказывает недостижимость. Успех локальной оптимизации не доказывает глобальный минимум. Отлёт с орбиты и захват в эту матрицу не входят.

## История попыток

### earth_venus_2032

Границы, суток: [195.4, 586.2]. 

Итераций оптимизатора времени: 12; старт корректора 390.800000000, результат 410.969656010 суток.
- anchor_00: фиксированный этап — completed, Финальная проверка; ПСИ принята.  
  Начальная длительность 390.800000 суток; после обработки: completed, этап final; .

### earth_mars_2028

Границы, суток: [250.0, 750.0]. 

Итераций оптимизатора времени: 13; старт корректора 696.601698873, результат 710.439279611 суток.
- anchor_00: фиксированный этап — completed, Финальная проверка; ПСИ принята.  
  Начальная длительность 500.000000 суток; после обработки: partial, этап time_release; Free-duration integration budget reached.
- anchor_01: фиксированный этап — partial, ПСИ: физический предел тяги; Решение не получено при минимальном шаге. minimum_step RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 648823.5637296173, 'velocity_residual_m_s': 0.217393852091302, 'parameter_audit': {'passed': True, 'configuration_sha256': 'ac659634705ad80090731e9a83631b0f041338d7e0445fdff774667cfc7eea5b', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2028-11-01T00:00:00', 'tof_days': 303.84646922620584, 'departure': 'Earth', 'target': 'Mars', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.044741750509542405), 'thrust_to_requested_ratio': np.float64(1.7896700203816962), 'alpha': 0.5, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': False, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 4.134817666401032, 'velocity_difference_m_s': 5.351218691826589e-07, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 1.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 8.54633206836956e-06, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 3000.030933865236, 'minimum_mass_kg': 97.27122898851877, 'fuel_kg': 58.72877101148123, 'mass_difference_kg': 4.503064587879635e-13, 'stored_thrust_error_N': 0.0}; free: Inactive departure branch is outside the allowed excess ball
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 1.0, "variable_mass": true, "model_thrust_N": 0.04474648153475631, "requested_thrust_N": 0.025, "thrust_ratio": 1.7898592613902524}`.
  Начальная длительность 303.846469 суток; после обработки: partial, этап psi; .
- anchor_02: фиксированный этап — completed, Финальная проверка; ПСИ принята.  
  Начальная длительность 696.601699 суток; после обработки: completed, этап final; .

### earth_apophis_2029

Границы, суток: [211.33090076867185, 633.9927023060155]. 

Итераций оптимизатора времени: 1; старт корректора 422.661801537, результат 422.661801537 суток.
- anchor_00: фиксированный этап — completed, Финальная проверка; ПСИ принята.  
  Начальная длительность 422.661802 суток; после обработки: completed, этап final; .

### earth_eros_2029

Границы, суток: [200.0, 600.0]. No independently accepted free-duration result; see time_history.json

- anchor_00: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.9875, "variable_mass": true, "model_thrust_N": 0.08174391532506176, "requested_thrust_N": 0.025, "thrust_ratio": 3.2697566130024702}`.
  Начальная длительность 400.000000 суток; после обработки: partial, этап psi; .
- anchor_01: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Nonpositive mass or central collision during propagation; active shooting: Bounded shooting budget reached; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.7643476486206056, "variable_mass": true, "model_thrust_N": 1.1023564157443717, "requested_thrust_N": 0.025, "thrust_ratio": 44.09425662977487}`.
  Начальная длительность 208.771952 суток; после обработки: partial, этап psi; .
- anchor_02: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.999609375, "variable_mass": true, "model_thrust_N": 0.049477792395978624, "requested_thrust_N": 0.025, "thrust_ratio": 1.9791116958391448}`.
  Начальная длительность 590.451888 суток; после обработки: partial, этап psi; .

### earth_bennu_2029

Границы, суток: [250.0, 750.0]. No independently accepted free-duration result; see time_history.json

- anchor_00: фиксированный этап — completed, Финальная проверка; ПСИ принята.  
  Начальная длительность 500.000000 суток; после обработки: partial, этап time_release; free: Free-duration physical replay failed: {'passed': False, 'position_residual_m': 3.2750421245100108, 'velocity_residual_m_s': 5.937236481157715e-07, 'parameter_audit': {'passed': True, 'configuration_sha256': '9e17bcf8d38518b55f620194bf7bd3b6a39198c6972d3787b26e0c76450236f7', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2029-06-01T00:00:00', 'tof_days': 537.3333007678337, 'departure': 'Earth', 'target': 'Bennu', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.025), 'thrust_to_requested_ratio': np.float64(1.0), 'alpha': 1.0, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': True, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': True}, 'trajectory_difference_m': 2.972412337151836, 'velocity_difference_m_s': 5.644930188615647e-07, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 2.961308639909066e-11, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 1749.7151826598595, 'switching_sign_violation': 0.14890401101553571, 'switching_node_residual': 3.222407160650797e-11, 'minimum_mass_kg': 124.4776574903166, 'fuel_kg': 31.522342509683394, 'mass_difference_kg': 2.424727085781342e-13, 'stored_thrust_error_N': 0.0, 'mass_balance_error_kg': np.float64(1.5276668818842154e-13)}; active: Free-duration optimizer: Positive directional derivative for linesearch.
- anchor_01: фиксированный этап — partial, ПСИ: физический предел тяги; Исчерпан бюджет этапа. time_budget RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 1.0, "variable_mass": true, "model_thrust_N": 0.026582364582748947, "requested_thrust_N": 0.025, "thrust_ratio": 1.0632945833099579}`.
  Начальная длительность 338.784114 суток; после обработки: partial, этап psi; .
- anchor_02: фиксированный этап — partial, ПСИ: точное управление; Исчерпан бюджет этапа. time_budget RuntimeError: free: Bounded collocation budget reached; active: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.7154296875, "beta": 1.0, "variable_mass": true, "model_thrust_N": 0.025, "requested_thrust_N": 0.025, "thrust_ratio": 1.0}`.
  Начальная длительность 661.215886 суток; после обработки: partial, этап psi; .

### earth_ryugu_2028

Границы, суток: [300.0, 900.0]. 

Итераций оптимизатора времени: 27; старт корректора 600.000000000, результат 656.318728532 суток.
- anchor_00: фиксированный этап — completed, Финальная проверка; ПСИ принята.  
  Начальная длительность 600.000000 суток; после обработки: completed, этап final; .

### earth_polyhymnia_2029

Границы, суток: [450.0, 1350.0]. No independently accepted free-duration result; see time_history.json

- anchor_00: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.999609375, "variable_mass": true, "model_thrust_N": 0.03825683158611321, "requested_thrust_N": 0.025, "thrust_ratio": 1.5302732634445284}`.
  Начальная длительность 900.000000 суток; после обработки: partial, этап psi; .
- anchor_01: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 38.27197485255987, 'velocity_residual_m_s': 2.418496364320585e-06, 'parameter_audit': {'passed': True, 'configuration_sha256': '75079105ec345363fe46199403db22588a54fb696d3db939f92c43b68637ec38', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2029-03-01T00:00:00', 'tof_days': 594.3137813289023, 'departure': 'Earth', 'target': 'Polyhymnia', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.05687681660286155), 'thrust_to_requested_ratio': np.float64(2.275072664114462), 'alpha': 0.5, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': False, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 34.44464576546362, 'velocity_difference_m_s': 2.0121368253649457e-06, 'stored_throttle_error': 3.885780586188048e-15, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 2.712790651648365e-10, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 3000.0000000000036, 'minimum_mass_kg': 81.78794870017408, 'fuel_kg': 74.21205129982592, 'mass_difference_kg': 6.337890212648745e-09, 'stored_thrust_error_N': 2.220446049250313e-16}; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.999609375, "variable_mass": true, "model_thrust_N": 0.05687681660286155, "requested_thrust_N": 0.025, "thrust_ratio": 2.275072664114462}`.
  Начальная длительность 594.313781 суток; после обработки: partial, этап psi; .
- anchor_02: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.9458984375000002, "variable_mass": true, "model_thrust_N": 0.02767214722878891, "requested_thrust_N": 0.025, "thrust_ratio": 1.1068858891515563}`.
  Начальная длительность 1196.466721 суток; после обработки: partial, этап psi; .

### earth_ceres_2030

Границы, суток: [500.0, 1500.0]. No independently accepted free-duration result; see time_history.json

- anchor_00: фиксированный этап — partial, ПСИ: точное управление; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached
  Последняя проверенная модель: `{"alpha": 0.51484375, "beta": 1.0, "variable_mass": true, "model_thrust_N": 0.025, "requested_thrust_N": 0.025, "thrust_ratio": 1.0}`.
  Начальная длительность 1000.000000 суток; после обработки: partial, этап psi; .
- anchor_01: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 61.44570811187406, 'velocity_residual_m_s': 3.464493302143938e-06, 'parameter_audit': {'passed': True, 'configuration_sha256': 'f1c16c80fb2a6d75ee27a5a9ccbc328cd9bb30dcdcda630794039ee0b30bee79', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2030-02-01T00:00:00', 'tof_days': 711.3552499793979, 'departure': 'Earth', 'target': 'Ceres', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.03848660264805843), 'thrust_to_requested_ratio': np.float64(1.539464105922337), 'alpha': 0.5, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': False, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 56.84406603969048, 'velocity_difference_m_s': 3.0250863171525475e-06, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 4.415959892610772e-10, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 2999.999999999997, 'minimum_mass_kg': 82.05894520294946, 'fuel_kg': 73.94105479705054, 'mass_difference_kg': 1.5355415605711187e-08, 'stored_thrust_error_N': 0.0}; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.999609375, "variable_mass": true, "model_thrust_N": 0.03848660264805843, "requested_thrust_N": 0.025, "thrust_ratio": 1.539464105922337}`.
  Начальная длительность 711.355250 суток; после обработки: partial, этап psi; .
- anchor_02: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached
  Последняя проверенная модель: `{"alpha": 0.203125, "beta": 0.0, "variable_mass": true, "model_thrust_N": 0.025, "requested_thrust_N": 0.025, "thrust_ratio": 1.0}`.
  Начальная длительность 1288.644750 суток; после обработки: partial, этап psi; .

### earth_mercury_2029

Границы, суток: [150.0, 450.0]. No independently accepted free-duration result; see time_history.json

- anchor_00: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.9445312499999999, "variable_mass": true, "model_thrust_N": 0.15378254264287824, "requested_thrust_N": 0.025, "thrust_ratio": 6.151301705715129}`.
  Начальная длительность 300.000000 суток; после обработки: partial, этап psi; .
- anchor_01: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.999609375, "variable_mass": true, "model_thrust_N": 0.18164826023483907, "requested_thrust_N": 0.025, "thrust_ratio": 7.265930409393563}`.
  Начальная длительность 232.855521 суток; после обработки: partial, этап psi; .
- anchor_02: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.9666992187500001, "variable_mass": true, "model_thrust_N": 0.11619939249779952, "requested_thrust_N": 0.025, "thrust_ratio": 4.647975699911981}`.
  Начальная длительность 367.144479 суток; после обработки: partial, этап psi; .

### earth_jupiter_2028

Границы, суток: [550.0, 1650.0]. No independently accepted free-duration result; see time_history.json

- anchor_00: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.9875, "variable_mass": true, "model_thrust_N": 0.048246622793893246, "requested_thrust_N": 0.025, "thrust_ratio": 1.9298649117557298}`.
  Начальная длительность 1100.000000 суток; после обработки: partial, этап psi; .
- anchor_01: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached
  Последняя проверенная модель: `{"alpha": 0.32500000000000007, "beta": 0.37734375000000003, "variable_mass": true, "model_thrust_N": 0.025, "requested_thrust_N": 0.025, "thrust_ratio": 1.0}`.
  Начальная длительность 1630.956624 суток; после обработки: partial, этап psi; .

### venus_earth_2029

Границы, суток: [125.0, 375.0]. No independently accepted free-duration result; see time_history.json

- anchor_00: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.9966011047363285, "variable_mass": true, "model_thrust_N": 0.6453428136079501, "requested_thrust_N": 0.025, "thrust_ratio": 25.813712544318}`.
  Начальная длительность 250.000000 суток; после обработки: partial, этап psi; .
- anchor_01: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Nonpositive mass or central collision during propagation; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.7514279305934907, "variable_mass": true, "model_thrust_N": 1.7601007447834116, "requested_thrust_N": 0.025, "thrust_ratio": 70.40402979133646}`.
  Начальная длительность 135.973118 суток; после обработки: partial, этап psi; .
- anchor_02: фиксированный этап — partial, ПСИ: физический предел тяги; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 1.0, "variable_mass": true, "model_thrust_N": 0.04699774417732127, "requested_thrust_N": 0.025, "thrust_ratio": 1.8799097670928506}`.
  Начальная длительность 363.898526 суток; после обработки: partial, этап psi; .

### earth_mars_flyby_2028

Границы, суток: [250.0, 750.0]. 

Итераций оптимизатора времени: 32; старт корректора 500.000000000, результат 306.981531003 суток.
- anchor_00: фиксированный этап — completed, Финальная проверка; ПСИ принята.  
  Начальная длительность 500.000000 суток; после обработки: completed, этап final; .

### earth_2015re36_2028

Границы, суток: [300.0, 900.0]. No independently accepted free-duration result; see time_history.json

- anchor_00: фиксированный этап — partial, ПСИ: физический предел тяги; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 1.0, "variable_mass": true, "model_thrust_N": 0.027663959535685883, "requested_thrust_N": 0.025, "thrust_ratio": 1.1065583814274353}`.
  Начальная длительность 600.000000 суток; после обработки: partial, этап psi; .
- anchor_01: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.9875, "variable_mass": true, "model_thrust_N": 0.10657903923582553, "requested_thrust_N": 0.025, "thrust_ratio": 4.263161569433021}`.
  Начальная длительность 420.801245 суток; после обработки: partial, этап psi; .
- anchor_02: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached
  Последняя проверенная модель: `{"alpha": 0.13125, "beta": 0.19375000000000003, "variable_mass": true, "model_thrust_N": 0.025, "requested_thrust_N": 0.025, "thrust_ratio": 1.0}`.
  Начальная длительность 779.198755 суток; после обработки: partial, этап psi; .

### earth_saturn_flyby_2028

Границы, суток: [1100.0, 3300.0]. ValueError: Ephemerides do not cover the full free-duration interval: Saturn


### earth_mars_2029

Границы, суток: [150.0, 450.0]. No independently accepted free-duration result; see time_history.json

- anchor_00: фиксированный этап — partial, ПСИ: введение массы; Исчерпан бюджет этапа. time_budget RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 23.108690679353323, 'velocity_residual_m_s': 3.441137672341599e-05, 'parameter_audit': {'passed': True, 'configuration_sha256': '38603cdb963b19f5e10d136ab2ce6528b7dcbe6e5a4fa80acd419df556b86267', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2029-09-01T00:00:00', 'tof_days': 300, 'departure': 'Earth', 'target': 'Mars', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.3751037388772162), 'thrust_to_requested_ratio': np.float64(15.004149555088647), 'alpha': 0.5, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': False, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 28.382663618027543, 'velocity_difference_m_s': 4.122468806607114e-05, 'stored_throttle_error': 1.2212453270876722e-15, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 1.4991539139153227e-09, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 2999.9999999255115, 'minimum_mass_kg': 18.549756235306152, 'fuel_kg': 137.45024376469385, 'mass_difference_kg': 4.175874945833158e-08, 'stored_thrust_error_N': 4.718447854656915e-16}; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached
  Последняя проверенная модель: `{"alpha": 0.5, "beta": 0.999609375, "variable_mass": true, "model_thrust_N": 0.3751037388772162, "requested_thrust_N": 0.025, "thrust_ratio": 15.004149555088647}`.
  Начальная длительность 300.000000 суток; после обработки: partial, этап psi; .
