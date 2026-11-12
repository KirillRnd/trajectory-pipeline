# Продолжение 42 принятых ИРТ до физической ПСИ

Принято **17 из 42**. Основной маршрут: 9; альтернативное продолжение: 3; коррекция точных дуг / независимый перенос / расширенное время: 5.

Все расчёты выполнены в Linux Docker. Исходные ИРТ и их SHA256 сохранены. Апофис взят после пересогласования на полные эфемериды. Даты старта, источники орбит, тип задачи и аппарат сохранены: 156 кг начальной / 90 кг сухой массы, 25 мН, c=20 км/с, избыток скорости ≤3 км/с. Менялась только длительность. Три непринятых ИРТ Сатурна не входят в эти 42.

## Маршруты и приёмка

1. ИРТ → избыток → Пазов (α=0,5) → масса → ограничение тяги → топливный функционал → точные дуги.
2. После отказа — совместное продолжение массы/тяги; освобождение времени на последней проверенной модели в [0,5T;1,5T]; возврат к ранней модели, α=0,3 и время [0,5T;2T].
3. Для остатка — коррекция точных дуг в декартовых, legacy-R и RTN координатах, свободное время; при наличии совместимой физической опоры — независимый R-перенос на исходную дату и фиксированная/свободная коррекция. Последняя общая попытка: раннее освобождение времени в [0,5T;max(2T,1095,75 суток)] и совместное продолжение.

Ветвление прекращается после принятой физической ПСИ. Бюджеты отдельных этапов конечны (45–90 секунд, внешние ограничения 65–480 секунд); отказ в таком бюджете не доказывает физическую недостижимость. Продолжение не является доказательством глобального минимума. Изменение длительности не обязательно означает успешное завершение её оптимизации.

Каждый принятый результат заново независимо проинтегрирован, проверен KIAM и привязан к исходному запросу с единственным разрешённым изменением tof_days. Требуются α=β=1, фактическая тяга аппарата, точное управление, масса не ниже сухой, граничные условия и трансверсальность. Проверена гелиоцентрическая межпланетная часть; отлёт с орбиты и захват не входят в эту серию.

Техническое исправление: для свободного времени от гладкой модели теперь явно строится непроверенное приближение моментов переключения по пересечению throttle=0,5. Раньше этот дополнительный маршрут завершался KeyError; затронутые попытки повторены отдельно, прежние ошибки сохранены.

## Все случаи

| Случай / дата старта | ИРТ, сут | ПСИ, сут | Топливо, кг | Результат / маршрут |
|---|---:|---:|---:|---|
| earth_2015re36_2028_d+0 / 2028-09-01 | 1142.49 | — | — | Частично: departure → psi_mass; Free-duration integration budget reached |
| earth_2015re36_2028_d+90 / 2028-11-30 | 1224.65 | — | — | Частично: departure → departure; No independently verified changed-duration intermediate; see trials.json |
| earth_2015re36_2028_d-90 / 2028-06-03 | 1422.79 | — | — | Частично: departure → departure; No independently verified changed-duration intermediate; see trials.json |
| earth_apophis_2029_d+0 / 2029-02-14 | 85.30 | — | — | Частично: psi_limit → psi_mass → psi_limit; Остановка: mass_and_thrust |
| earth_apophis_2029_d+90 / 2029-05-15 | 44.08 | — | — | Частично: psi_mass → psi_mass → psi_limit; Остановка: mass_and_thrust |
| earth_apophis_2029_d-90 / 2028-11-16 | 548.14 | 548.14 | 16.741 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| earth_bennu_2029_d+0 / 2029-06-01 | 724.23 | 724.23 | 31.118 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| earth_bennu_2029_d+90 / 2029-08-30 | 568.32 | 568.32 | 18.951 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| earth_bennu_2029_d-90 / 2029-03-03 | 1014.06 | — | — | Частично: psi → psi_limit → psi_limit; Free-duration integration budget reached |
| earth_ceres_2030_d+0 / 2030-02-01 | 1018.38 | 1018.38 | 62.917 | exact physical arcs in cartesian costate coordinates |
| earth_ceres_2030_d+90 / 2030-05-02 | 652.48 | — | — | Частично: psi_limit → psi_limit → psi_limit; Остановка: mass_and_thrust |
| earth_ceres_2030_d-90 / 2029-11-03 | 1252.48 | — | — | Частично: psi_mass → psi_limit → psi_mass; Остановка: mass_and_thrust |
| earth_eros_2029_d+0 / 2029-03-01 | 1118.74 | 1158.05 | 35.433 | exact physical arcs in cartesian costate coordinates |
| earth_eros_2029_d+90 / 2029-05-30 | 904.77 | 904.77 | 45.156 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| earth_eros_2029_d-90 / 2028-12-01 | 1320.26 | — | — | Частично: psi → psi; Free-duration integration budget reached |
| earth_jupiter_2028_d+0 / 2028-06-01 | 1410.83 | — | — | Частично: psi_mass → departure → departure; Остановка: departure |
| earth_jupiter_2028_d+90 / 2028-08-30 | 1032.24 | — | — | Частично: psi_mass → psi_limit → psi_limit; Остановка: mass_and_thrust |
| earth_jupiter_2028_d-90 / 2028-03-03 | 1649.30 | — | — | Частично: departure → departure → psi_limit; Остановка: mass_and_thrust |
| earth_mars_2028_d+0 / 2028-11-01 | 364.76 | 639.11 | 22.879 | early duration -> Pazov(.3) -> coupled mass/thrust -> fuel |
| earth_mars_2028_d+90 / 2029-01-30 | 179.83 | 474.09 | 36.670 | broad early duration -> coupled physical continuation |
| earth_mars_2028_d-90 / 2028-08-03 | 571.47 | 571.47 | 28.959 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| earth_mars_2029_d+0 / 2029-09-01 | 1369.45 | — | — | Частично: pazov_limit → psi → psi; Остановка: fuel |
| earth_mars_2029_d+90 / 2029-11-30 | 1395.04 | — | — | Частично: pazov_limit → psi_limit; No independently verified changed-duration intermediate; see trials.json |
| earth_mars_2029_d-90 / 2029-06-03 | 1759.49 | — | — | Частично: pazov_limit → psi_limit; No independently verified changed-duration intermediate; see trials.json |
| earth_mars_flyby_2028_d+0 / 2028-11-01 | 364.76 | 364.76 | 4.847 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| earth_mars_flyby_2028_d+90 / 2029-01-30 | 179.83 | 359.66 | 2.564 | early duration -> Pazov(.3) -> coupled mass/thrust -> fuel |
| earth_mars_flyby_2028_d-90 / 2028-08-03 | 571.47 | 571.47 | 10.686 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| earth_mercury_2029_d+0 / 2029-01-01 | 190.52 | — | — | Частично: psi_mass → psi_limit → psi_limit; Остановка: mass_and_thrust |
| earth_mercury_2029_d+90 / 2029-04-01 | 68.48 | — | — | Частично: pazov → psi_limit → psi_limit; Остановка: mass_and_thrust |
| earth_mercury_2029_d-90 / 2028-10-03 | 143.96 | — | — | Частично: psi_mass → psi_mass → psi_mass; Остановка: mass_and_thrust |
| earth_polyhymnia_2029_d+0 / 2029-03-01 | 1288.48 | — | — | Частично: psi_mass → psi → psi_limit; Остановка: mass_and_thrust |
| earth_polyhymnia_2029_d+90 / 2029-05-30 | 531.47 | — | — | Частично: psi_mass → psi_limit → psi_limit; Остановка: mass_and_thrust |
| earth_polyhymnia_2029_d-90 / 2028-12-01 | 886.97 | — | — | Частично: psi_mass → psi_limit → psi_limit; Остановка: mass_and_thrust |
| earth_ryugu_2028_d+0 / 2028-06-01 | 868.40 | 898.92 | 17.324 | exact physical arcs in cartesian costate coordinates |
| earth_ryugu_2028_d+90 / 2028-08-30 | 691.28 | 691.28 | 28.775 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| earth_ryugu_2028_d-90 / 2028-03-03 | 1096.37 | 1096.37 | 27.093 | exact physical arcs in cartesian costate coordinates |
| earth_venus_2032_d+0 / 2032-11-01 | 241.11 | 456.20 | 26.852 | early duration -> Pazov(.3) -> coupled mass/thrust -> fuel |
| earth_venus_2032_d+90 / 2033-01-30 | 70.27 | — | — | Частично: psi_mass → psi_limit → psi_limit; Остановка: mass_and_thrust |
| earth_venus_2032_d-90 / 2032-08-03 | 403.99 | 403.99 | 35.417 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| venus_earth_2029_d+0 / 2029-01-01 | 841.32 | — | — | Частично: pazov_limit → psi_limit; No independently verified changed-duration intermediate; see trials.json |
| venus_earth_2029_d+90 / 2029-04-01 | 655.97 | — | — | Частично: pazov_limit → psi_limit → psi_limit; Остановка: mass_and_thrust |
| venus_earth_2029_d-90 / 2028-10-03 | 1017.47 | — | — | Частично: pazov_limit → psi_limit → psi_limit; Остановка: mass_and_thrust |

## Незавершённые пути

Последовательность ниже показывает сохранённые опоры основного, восстановительного и расширенного маршрутов. Она не означает монотонного улучшения: маршрут может возвращаться к ранней модели. Полные причины попыток и параметры — в JSON каждого случая.

### earth_2015re36_2028_d+0

- primary_last: departure, T=1142.493 сут, α=—, β=—, variable_mass=—, F=None Н, departure parameter=0.501788330078125.
- recover_last: psi_mass, T=1142.493 сут, α=0.03, β=0, variable_mass=True, F=0.025 Н, departure parameter=None.
- primary/departure: partial.
- recover/coupled: fuel.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/release_early: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: mass_and_thrust.
- transfer/exact_arcs_cartesian: Exact arc integration budget reached.
- transfer/exact_arcs_legacy: Exact arc integration budget reached.
- transfer/exact_arcs_rtn: Exact arc integration budget reached.
- transfer/exact_free_time: 'switch_times_s'.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: No independently verified changed-duration intermediate; see trials.json.
- transfer/exact_free_time_topology_fix: Free-duration integration budget reached.
- departure/continuation.json: minimum_step; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 1161.5125654681376, 'velocity_residual_m_s': 0.0002502135710055848, 'trajectory_difference_m': 1161.5125654681426, 'velocity_difference_m_s': 0.0002502135710055848, 'free_velocity_transversality': 0.03009550341434208, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}.
- coupled/departure/continuation.json: target_reached; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 1555.0117614215721, 'velocity_residual_m_s': 0.0003386617357854145, 'trajectory_difference_m': 1555.0117614215721, 'velocity_difference_m_s': 0.00033866173865799835, 'free_velocity_transversality': 0.029936613475799585, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}; Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 267105165.53206414, 'velocity_residual_m_s': 41.668565681075854, 'trajectory_difference_m': 506.7218093250922, 'velocity_difference_m_s': 0.0001141042170840453, 'free_velocity_transversality': 0.022745164931133915, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}.
- coupled/fuel/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- coupled/mass_and_thrust/continuation.json: target_reached; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- coupled/pazov/functional/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/departure/continuation.json: target_reached; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 1555.0117614215721, 'velocity_residual_m_s': 0.0003386617357854145, 'trajectory_difference_m': 1555.0117614215721, 'velocity_difference_m_s': 0.00033866173865799835, 'free_velocity_transversality': 0.029936613475799585, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}; Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 267105165.53206414, 'velocity_residual_m_s': 41.668565681075854, 'trajectory_difference_m': 506.7218093250922, 'velocity_difference_m_s': 0.0001141042170840453, 'free_velocity_transversality': 0.022745164931133915, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- early_continue/pazov/functional/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.

### earth_2015re36_2028_d+90

- primary_last: departure, T=1224.654 сут, α=—, β=—, variable_mass=—, F=None Н, departure parameter=0.112890625.
- recover_last: departure, T=1224.654 сут, α=—, β=—, variable_mass=—, F=None Н, departure parameter=0.112890625.
- primary/departure: partial.
- recover/coupled: departure.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/release_early: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: departure.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: No independently verified changed-duration intermediate; see trials.json.
- departure/continuation.json: time_budget; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 1588.661802879417, 'velocity_residual_m_s': 0.00020413779786888228, 'trajectory_difference_m': 1990.9805876348912, 'velocity_difference_m_s': 0.0004680406647330006, 'free_velocity_transversality': 0.009228027785575764, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}.
- coupled/departure/continuation.json: time_budget; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 1270.0181046875994, 'velocity_residual_m_s': 0.00016252262263328235, 'trajectory_difference_m': 1570.673803058787, 'velocity_difference_m_s': 0.00037023142958680363, 'free_velocity_transversality': 0.008820517449550867, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}; Free-departure shooting budget reached.
- early_continue/departure/continuation.json: time_budget; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 1270.0181046875994, 'velocity_residual_m_s': 0.00016252262263328235, 'trajectory_difference_m': 1570.673803058787, 'velocity_difference_m_s': 0.00037023142958680363, 'free_velocity_transversality': 0.008820517449550867, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}; Free-departure shooting budget reached.

### earth_2015re36_2028_d-90

- primary_last: departure, T=1422.787 сут, α=—, β=—, variable_mass=—, F=None Н, departure parameter=0.19257812500000002.
- recover_last: departure, T=1422.787 сут, α=—, β=—, variable_mass=—, F=None Н, departure parameter=1.0.
- primary/departure: partial.
- recover/coupled: ValueError: Initial bounded quadratic conversion failed: {'passed': False, 'position_residual_m': 1227.7216204952424, 'velocity_residual_m_s': 0.00014625310707957033, 'parameter_audit': {'passed': True, 'configuration_sha256': '0bd31054b22864650525e45f81b087823a38b9474ed82dd294d2eaff75163636', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2028-06-03T00:00:00', 'tof_days': 1422.7872026667071, 'departure': 'Earth', 'target': '2015RE36', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.03809163500526486), 'thrust_to_requested_ratio': np.float64(1.5236654002105943), 'alpha': 0.0, 'beta': 0.0, 'variable_mass': False, 'hardware_limit_reached': False}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 1473.603259529551, 'velocity_difference_m_s': 0.00040227330050165923, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 1.224821733444012e-39, 'stored_throttle_maximum': 0.9708737864077669, 'canonical_boundary_residual': 9.482584674519525e-09, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 675.4137984337885}.
- recover/after_release: ValueError: Initial bounded quadratic conversion failed: {'passed': False, 'position_residual_m': 1154.2600409705205, 'velocity_residual_m_s': 0.00011726354627748515, 'parameter_audit': {'passed': True, 'configuration_sha256': '6bc67c46897a3fbffe8d9c5bcf0969a70218b30ad5d35a9a73602a65f12006d9', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2028-06-03T00:00:00', 'tof_days': 1590.7244513397634, 'departure': 'Earth', 'target': '2015RE36', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.037663963683364804), 'thrust_to_requested_ratio': np.float64(1.5065585473345922), 'alpha': 0.0, 'beta': 0.0, 'variable_mass': False, 'hardware_limit_reached': False}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 1264.0116610393447, 'velocity_difference_m_s': 0.00020402311374420365, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 0.9708737864077669, 'canonical_boundary_residual': 8.578183281334022e-09, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 654.3408393571063}.
- recover/release_early: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: ValueError: Initial bounded quadratic conversion failed: {'passed': False, 'position_residual_m': 1227.7216204952424, 'velocity_residual_m_s': 0.00014625310707957033, 'parameter_audit': {'passed': True, 'configuration_sha256': '0bd31054b22864650525e45f81b087823a38b9474ed82dd294d2eaff75163636', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2028-06-03T00:00:00', 'tof_days': 1422.7872026667071, 'departure': 'Earth', 'target': '2015RE36', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.03809163500526486), 'thrust_to_requested_ratio': np.float64(1.5236654002105943), 'alpha': 0.0, 'beta': 0.0, 'variable_mass': False, 'hardware_limit_reached': False}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 1473.603259529551, 'velocity_difference_m_s': 0.00040227330050165923, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 1.224821733444012e-39, 'stored_throttle_maximum': 0.9708737864077669, 'canonical_boundary_residual': 9.482584674519525e-09, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 675.4137984337885}.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: No independently verified changed-duration intermediate; see trials.json.
- departure/continuation.json: minimum_step; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 1111.1321155285718, 'velocity_residual_m_s': 0.0001317743758587791, 'trajectory_difference_m': 1388.095285479006, 'velocity_difference_m_s': 0.00037807700534813696, 'free_velocity_transversality': 0.009074473424457276, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}.

### earth_apophis_2029_d+0

- primary_last: psi_limit, T=85.302 сут, α=0.5, β=1.0, variable_mass=True, F=0.12956396877975127 Н, departure parameter=None.
- recover_last: psi_mass, T=170.604 сут, α=0.0, β=0, variable_mass=True, F=0.03696654059642766 Н, departure parameter=None.
- broad_last: psi_limit, T=847.127 сут, α=0.0, β=0.025, variable_mass=True, F=0.05161322967274529 Н, departure parameter=None.
- primary/pazov: thrust_limit.
- primary/psi: physical_thrust_limit.
- recover/coupled: mass_and_thrust.
- recover/after_release: mass_and_thrust.
- recover/early_continue: mass_and_thrust.
- transfer/R_fixed: Exact arc integration budget reached.
- transfer/R_free: Free-duration integration budget reached.
- transfer/broad_early_time: mass_and_thrust.
- after_release/mass_and_thrust/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- broad_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached.
- early_continue/pazov/limit/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 185679218.35679787, 'velocity_residual_m_s': 38.31571542547558, 'parameter_audit': {'passed': True, 'configuration_sha256': 'f1ad4a65af2d41e135ba08eb7ced8175a47db6ec0637fec8c7a9913a3288794a', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2029-02-14T12:00:00', 'tof_days': 170.60433786148585, 'departure': 'Earth', 'target': 'Apophis', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.03615064010121668), 'thrust_to_requested_ratio': np.float64(1.446025604048667), 'alpha': 0.0, 'beta': 0.0, 'variable_mass': False, 'hardware_limit_reached': False}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 0.2733141263111454, 'velocity_difference_m_s': 5.649373169456224e-08, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 6.522879205168855e-07, 'stored_throttle_maximum': 1.0, 'canonical_boundary_residual': 0.00179269463011446, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 1423.6651614462412}; active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached.
- pazov/limit/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- psi/limit/continuation.json: time_budget; RuntimeError: free: Bounded collocation budget reached; active: Bounded collocation budget reached.

### earth_apophis_2029_d+90

- primary_last: psi_mass, T=44.078 сут, α=0.5, β=0.999609375, variable_mass=True, F=1.147626117233934 Н, departure parameter=None.
- recover_last: psi_mass, T=88.155 сут, α=0.0, β=0, variable_mass=True, F=0.3787703133980685 Н, departure parameter=None.
- broad_last: psi_limit, T=275.485 сут, α=0.0, β=0.0015625, variable_mass=True, F=0.030624674401507672 Н, departure parameter=None.
- primary/pazov: thrust_limit.
- primary/psi: mass.
- recover/coupled: mass_and_thrust.
- recover/after_release: mass_and_thrust.
- recover/early_continue: mass_and_thrust.
- transfer/R_fixed: Exact arc integration budget reached.
- transfer/R_free: Free-duration integration budget reached.
- transfer/broad_early_time: mass_and_thrust.
- after_release/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.
- broad_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached.
- early_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- pazov/limit/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- psi/mass/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.

### earth_bennu_2029_d-90

- primary_last: psi, T=1014.059 сут, α=0.13621093750000002, β=1.0, variable_mass=True, F=0.025 Н, departure parameter=None.
- recover_last: psi_limit, T=1014.059 сут, α=0.05437500000000001, β=0.496875, variable_mass=True, F=0.025 Н, departure parameter=None.
- broad_last: psi_limit, T=1022.546 сут, α=0.11812500000000001, β=0.05, variable_mass=True, F=0.025 Н, departure parameter=None.
- primary/pazov: mixed_functional.
- primary/psi: fuel.
- recover/coupled: fuel.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/release_early: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: mass_and_thrust.
- transfer/exact_arcs_cartesian: Exact arc integration budget reached.
- transfer/exact_arcs_legacy: Exact arc integration budget reached.
- transfer/exact_arcs_rtn: Exact arc integration budget reached.
- transfer/exact_free_time: 'switch_times_s'.
- transfer/R_fixed: Exact arc integration budget reached.
- transfer/R_free: Free-duration integration budget reached.
- transfer/broad_early_time: mass_and_thrust.
- transfer/exact_free_time_topology_fix: Free-duration integration budget reached.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- broad_continue/pazov/functional/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.
- coupled/fuel/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- early_continue/pazov/functional/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- pazov/functional/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- psi/fuel/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- psi/mass/continuation.json: target_reached; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.

### earth_ceres_2030_d+90

- primary_last: psi_limit, T=652.481 сут, α=0.5, β=1.0, variable_mass=True, F=0.026788825361672153 Н, departure parameter=None.
- recover_last: psi_limit, T=1304.935 сут, α=0.1275, β=0.109375, variable_mass=True, F=0.025 Н, departure parameter=None.
- broad_last: psi_limit, T=1304.938 сут, α=0.13968750000000002, β=0.18906250000000002, variable_mass=True, F=0.025 Н, departure parameter=None.
- primary/pazov: thrust_limit.
- primary/psi: physical_thrust_limit.
- recover/coupled: mass_and_thrust.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: mass_and_thrust.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: mass_and_thrust.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- broad_continue/pazov/functional/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/pazov/functional/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- pazov/limit/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.
- psi/limit/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.
- psi/mass/continuation.json: target_reached; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Inactive departure branch is outside the allowed excess ball.

### earth_ceres_2030_d-90

- primary_last: psi_mass, T=1252.482 сут, α=0.14375, β=0.659375, variable_mass=True, F=0.025 Н, departure parameter=None.
- recover_last: psi_limit, T=1343.849 сут, α=0.195, β=0.034375, variable_mass=True, F=0.025 Н, departure parameter=None.
- broad_last: psi_mass, T=1517.535 сут, α=0.075, β=0, variable_mass=True, F=0.025 Н, departure parameter=None.
- primary/pazov: mixed_functional.
- primary/psi: mass.
- recover/coupled: mass_and_thrust.
- recover/after_release: fuel.
- recover/early_continue: mass_and_thrust.
- transfer/exact_arcs_cartesian: Exact arc integration budget reached.
- transfer/exact_arcs_legacy: Exact arc integration budget reached.
- transfer/exact_arcs_rtn: Exact arc integration budget reached.
- transfer/exact_free_time: Free-duration integration budget reached.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: mass_and_thrust.
- after_release/fuel/continuation.json: time_budget; RuntimeError: active: Independent bounded replay budget reached; free: Bounded collocation budget reached.
- after_release/mass_and_thrust/continuation.json: target_reached; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- broad_continue/pazov/functional/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/pazov/functional/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- pazov/functional/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- psi/mass/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.

### earth_eros_2029_d-90

- primary_last: psi, T=1320.264 сут, α=0.014013671875000001, β=1.0, variable_mass=True, F=0.025 Н, departure parameter=None.
- recover_last: psi, T=1320.264 сут, α=0.024218750000000004, β=1, variable_mass=True, F=0.025 Н, departure parameter=None.
- primary/pazov: mixed_functional.
- primary/psi: fuel.
- recover/coupled: fuel.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/release_early: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: fuel.
- transfer/exact_arcs_cartesian: Exact arc integration budget reached.
- transfer/exact_arcs_legacy: Exact arc integration budget reached.
- transfer/exact_arcs_rtn: Exact arc integration budget reached.
- transfer/exact_free_time: 'switch_times_s'.
- transfer/R_fixed: Exact arc integration budget reached.
- transfer/R_free: Free-duration integration budget reached.
- transfer/broad_early_time: No independently verified changed-duration intermediate; see trials.json.
- transfer/exact_free_time_topology_fix: Free-duration integration budget reached.
- coupled/fuel/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached.
- early_continue/fuel/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/pazov/functional/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- pazov/functional/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- psi/fuel/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.

### earth_jupiter_2028_d+0

- primary_last: psi_mass, T=1410.831 сут, α=0.5, β=0.20625000000000002, variable_mass=True, F=0.03055119231229731 Н, departure parameter=None.
- recover_last: departure, T=1987.819 сут, α=—, β=—, variable_mass=—, F=None Н, departure parameter=1.0.
- broad_last: departure, T=2295.431 сут, α=—, β=—, variable_mass=—, F=None Н, departure parameter=0.0.
- primary/pazov: thrust_limit.
- primary/psi: mass.
- recover/coupled: mass_and_thrust.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: ValueError: Initial bounded quadratic conversion failed: {'passed': False, 'position_residual_m': 1513.2415550953033, 'velocity_residual_m_s': 3.588580294323224e-05, 'parameter_audit': {'passed': True, 'configuration_sha256': '17c3cb2d9ff16d8d9e43d18c52f367986e74b60647250b93e352443f448fd89d', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2028-06-01T00:00:00', 'tof_days': 1987.818853476213, 'departure': 'Earth', 'target': 'Jupiter', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.027250385702177284), 'thrust_to_requested_ratio': np.float64(1.0900154280870913), 'alpha': 0.0, 'beta': 0.0, 'variable_mass': False, 'hardware_limit_reached': False}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 1513.241522803484, 'velocity_difference_m_s': 3.5885803617494834e-05, 'stored_throttle_error': 0.0, 'stored_throttle_minimum': 0.07906185447463761, 'stored_throttle_maximum': 0.970873786407767, 'canonical_boundary_residual': 1.0048839997957211e-08, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 3000.0000000000036}.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: departure.
- broad_continue/departure/continuation.json: time_budget; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 3805.256616793101, 'velocity_residual_m_s': 8.858085091998023e-05, 'trajectory_difference_m': 3805.256616793101, 'velocity_difference_m_s': 8.858085091998023e-05, 'free_velocity_transversality': 0.006239067695383944, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}; Free-departure shooting budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- psi/mass/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.

### earth_jupiter_2028_d+90

- primary_last: psi_mass, T=1032.237 сут, α=0.5, β=0.9890625000000001, variable_mass=True, F=0.042416874042371266 Н, departure parameter=None.
- recover_last: psi_limit, T=2064.475 сут, α=0.0, β=0.059375000000000004, variable_mass=True, F=0.0321466070176103 Н, departure parameter=None.
- broad_last: psi_limit, T=2064.475 сут, α=0.0, β=0.115625, variable_mass=True, F=0.03171923516983944 Н, departure parameter=None.
- primary/pazov: thrust_limit.
- primary/psi: mass.
- recover/coupled: mass_and_thrust.
- recover/after_release: mass_and_thrust.
- recover/early_continue: mass_and_thrust.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: mass_and_thrust.
- after_release/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- broad_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- psi/mass/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.

### earth_jupiter_2028_d-90

- primary_last: departure, T=1649.301 сут, α=—, β=—, variable_mass=—, F=None Н, departure parameter=0.91875.
- recover_last: departure, T=1881.154 сут, α=—, β=—, variable_mass=—, F=None Н, departure parameter=0.91875.
- broad_last: psi_limit, T=1461.332 сут, α=0.0, β=0.034375, variable_mass=True, F=0.029838045740734544 Н, departure parameter=None.
- primary/departure: partial.
- recover/coupled: departure.
- recover/after_release: departure.
- recover/early_continue: departure.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: mass_and_thrust.
- departure/continuation.json: time_budget; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 1082.664049260956, 'velocity_residual_m_s': 2.8042516139922082e-05, 'trajectory_difference_m': 1082.664049260956, 'velocity_difference_m_s': 2.8042516140099665e-05, 'free_velocity_transversality': 0.033928758497143115, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}.
- after_release/departure/continuation.json: time_budget; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 1513.8539241689223, 'velocity_residual_m_s': 3.572086294576992e-05, 'trajectory_difference_m': 1513.8539241689223, 'velocity_difference_m_s': 3.572086294576992e-05, 'free_velocity_transversality': 0.016558598910717374, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}; Free-departure shooting budget reached.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- broad_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- coupled/departure/continuation.json: time_budget; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 1191.1067248133788, 'velocity_residual_m_s': 2.800859543768628e-05, 'trajectory_difference_m': 1191.106615818588, 'velocity_difference_m_s': 2.800859543768628e-05, 'free_velocity_transversality': 0.03372611085015276, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}; Free-departure shooting budget reached.
- early_continue/departure/continuation.json: time_budget; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 1213.8080866651928, 'velocity_residual_m_s': 2.9578543019521205e-05, 'trajectory_difference_m': 1213.8080866651928, 'velocity_difference_m_s': 2.95785424567319e-05, 'free_velocity_transversality': 0.023126722688293234, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}; Free-departure shooting budget reached.

### earth_mars_2029_d+0

- primary_last: pazov_limit, T=1369.454 сут, α=0.0, β=0.0, variable_mass=False, F=0.025 Н, departure parameter=None.
- recover_last: psi, T=1762.090 сут, α=0.0106015625, β=1, variable_mass=True, F=0.025 Н, departure parameter=None.
- broad_last: psi, T=1417.552 сут, α=0.554135009765625, β=1, variable_mass=True, F=0.025 Н, departure parameter=None.
- primary/pazov: mixed_functional.
- primary/psi: regularize.
- recover/coupled: mass_and_thrust.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: fuel.
- transfer/exact_arcs_cartesian: Exact arc integration budget reached.
- transfer/exact_arcs_legacy: Exact arc integration budget reached.
- transfer/exact_arcs_rtn: Independent bounded replay budget reached.
- transfer/exact_free_time: Free-duration integration budget reached.
- transfer/R_fixed: Exact arc integration budget reached.
- transfer/R_free: Free-duration integration budget reached.
- transfer/broad_early_time: fuel.
- departure/continuation.json: target_reached; RuntimeError: The maximum number of mesh nodes is exceeded..
- broad_continue/departure/continuation.json: target_reached; RuntimeError: The maximum number of mesh nodes is exceeded.; Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 1881825499.9443102, 'velocity_residual_m_s': 504.55426079677676, 'trajectory_difference_m': 225.73938004429343, 'velocity_difference_m_s': 2.423963125710799e-05, 'free_velocity_transversality': 0.03894688238874723, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}.
- broad_continue/fuel/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- broad_continue/pazov/functional/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- early_continue/fuel/continuation.json: time_budget; RuntimeError: free: Nonpositive mass or central collision during propagation; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- early_continue/pazov/functional/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached.
- pazov/functional/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- psi/regularize/continuation.json: time_budget; RuntimeError: free: Bounded collocation budget reached; active: Bounded collocation budget reached.

### earth_mars_2029_d+90

- primary_last: pazov_limit, T=1395.038 сут, α=0.0, β=0.0, variable_mass=False, F=0.025 Н, departure parameter=None.
- recover_last: psi_limit, T=1575.044 сут, α=0.0, β=0.9750000000000001, variable_mass=True, F=0.025 Н, departure parameter=None.
- primary/pazov: mixed_functional.
- primary/psi: regularize.
- recover/coupled: fuel.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: mass_and_thrust.
- transfer/exact_arcs_cartesian: Exact arc integration budget reached.
- transfer/exact_arcs_legacy: Independent bounded replay budget reached.
- transfer/exact_arcs_rtn: Independent bounded replay budget reached.
- transfer/exact_free_time: Free-duration integration budget reached.
- transfer/R_fixed: Exact arc integration budget reached.
- transfer/R_free: Free-duration integration budget reached.
- transfer/broad_early_time: No independently verified changed-duration intermediate; see trials.json.
- departure/continuation.json: target_reached; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 2856.9148229817656, 'velocity_residual_m_s': 0.0002900004406428059, 'trajectory_difference_m': 6275.722543064024, 'velocity_difference_m_s': 0.0008490209870806706, 'free_velocity_transversality': 0.011066624161093141, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}.
- coupled/fuel/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Independent replay failed at final accuracy: {'passed': False, 'position_residual_m': 1854.4960553467174, 'velocity_residual_m_s': 0.00019267451238108897, 'parameter_audit': {'passed': True, 'configuration_sha256': '68a42974695dd670058f0c202143ba02fd6af4d5e4b2d18186308e63c6dd36a6', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2029-11-30T00:00:00', 'tof_days': 1575.044498650178, 'departure': 'Earth', 'target': 'Mars', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.025), 'thrust_to_requested_ratio': np.float64(1.0), 'alpha': 0.0, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': True, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 1854.4960553467174, 'velocity_difference_m_s': 0.0001976395379698546, 'stored_throttle_error': 1.1102230246251565e-16, 'stored_throttle_minimum': 0.03902140087800798, 'stored_throttle_maximum': 0.30558878808633955, 'canonical_boundary_residual': 1.4115605210531467e-08, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 2999.999999999999, 'minimum_mass_kg': 126.47079277170302, 'fuel_kg': 29.529207228296986, 'mass_difference_kg': 1.1491474438685145e-08, 'stored_thrust_error_N': 3.469446951953614e-18}; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached.
- early_continue/pazov/functional/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached.
- pazov/functional/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- psi/regularize/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.

### earth_mars_2029_d-90

- primary_last: pazov_limit, T=1759.493 сут, α=0.0, β=0.0, variable_mass=False, F=0.025 Н, departure parameter=None.
- recover_last: psi_limit, T=1759.493 сут, α=0.0, β=0.9, variable_mass=True, F=0.025 Н, departure parameter=None.
- primary/pazov: mixed_functional.
- primary/psi: regularize.
- recover/coupled: mass_and_thrust.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/release_early: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: mass_and_thrust.
- transfer/R_fixed: Exact arc integration budget reached.
- transfer/R_free: Free-duration integration budget reached.
- transfer/broad_early_time: No independently verified changed-duration intermediate; see trials.json.
- departure/continuation.json: target_reached; RuntimeError: The maximum number of mesh nodes is exceeded..
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Active departure branch has a negative inequality multiplier; free: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Active departure branch has a negative inequality multiplier; free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached.
- early_continue/pazov/functional/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- pazov/functional/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.
- psi/regularize/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.

### earth_mercury_2029_d+0

- primary_last: psi_mass, T=190.524 сут, α=0.5, β=0.999609375, variable_mass=True, F=0.23795802750367534 Н, departure parameter=None.
- recover_last: psi_limit, T=291.733 сут, α=0.0, β=0.00625, variable_mass=True, F=0.23574401356051194 Н, departure parameter=None.
- broad_last: psi_limit, T=209.446 сут, α=0.0, β=0.0125, variable_mass=True, F=0.1996634322833309 Н, departure parameter=None.
- primary/pazov: thrust_limit.
- primary/psi: mass.
- recover/coupled: mass_and_thrust.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: mass_and_thrust.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: mass_and_thrust.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached.
- broad_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached.
- early_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.
- pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- psi/mass/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting replay failed: {'passed': False, 'position_residual_m': 1.9351813141394594, 'velocity_residual_m_s': 9.740631351353911e-07, 'parameter_audit': {'passed': True, 'configuration_sha256': 'c2620486de818d4523f7fdece99442d57fe8b1f1cde0a5eabbed1b9dce8d5b87', 'configuration_hash_version': 2, 'requested': {'mass_kg': 156, 'thrust_N': 0.025, 'exhaust_velocity_m_s': 20000, 'dry_mass_kg': 90, 'launch_tdb': '2029-01-01T00:00:00', 'tof_days': 190.52367309235476, 'departure': 'Earth', 'target': 'Mercury', 'mode': 'rendezvous'}, 'recovered_model': {'model_thrust_N': np.float64(0.23795802750367534), 'thrust_to_requested_ratio': np.float64(9.518321100147013), 'alpha': 0.5, 'beta': 1.0, 'variable_mass': True, 'hardware_limit_reached': False, 'exhaust_velocity_m_s': np.float64(20000.0)}, 'geometry': None, 'final_admission': False}, 'trajectory_difference_m': 3.127879212759152, 'velocity_difference_m_s': 1.9253347988574987e-06, 'stored_throttle_error': 1.7763568394002505e-15, 'stored_throttle_minimum': 0.0, 'stored_throttle_maximum': 0.8066566612042347, 'canonical_boundary_residual': 4.010157768132811e-11, 'method': 'LSODA with independent bounded/mass equations', 'scope': 'Numerical extremal and constraints; no global optimality proof', 'departure_norm_m_s': 3000.000000011742, 'minimum_mass_kg': 69.62635895237642, 'fuel_kg': 86.37364104762358, 'mass_difference_kg': 3.58314911075297e-09, 'stored_thrust_error_N': 4.163336342344337e-16}; free: Bounded collocation budget reached.

### earth_mercury_2029_d+90

- primary_last: pazov, T=68.483 сут, α=0.103515625, β=0.0, variable_mass=False, F=1.2040390928260885 Н, departure parameter=None.
- recover_last: psi_limit, T=97.698 сут, α=0.0, β=0.00625, variable_mass=True, F=0.6226293289865776 Н, departure parameter=None.
- broad_last: psi_limit, T=111.645 сут, α=0.0, β=0.00625, variable_mass=True, F=0.4996611972774905 Н, departure parameter=None.
- primary/pazov: thrust_limit.
- primary/psi: regularize.
- recover/coupled: mass_and_thrust.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: mass_and_thrust.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: mass_and_thrust.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached.
- broad_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- psi/regularize/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.

### earth_mercury_2029_d-90

- primary_last: psi_mass, T=143.960 сут, α=0.5, β=0.999609375, variable_mass=True, F=0.49812963625316353 Н, departure parameter=None.
- recover_last: psi_mass, T=187.374 сут, α=0.0, β=0, variable_mass=True, F=0.23934031490832153 Н, departure parameter=None.
- broad_last: psi_mass, T=335.426 сут, α=0.0, β=0, variable_mass=True, F=0.43009762666117435 Н, departure parameter=None.
- primary/pazov: thrust_limit.
- primary/psi: mass.
- recover/coupled: mass_and_thrust.
- recover/after_release: mass_and_thrust.
- recover/early_continue: mass_and_thrust.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: mass_and_thrust.
- after_release/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached.
- broad_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached.
- early_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- psi/mass/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.
- psi/regularize/continuation.json: target_reached; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Inactive departure branch is outside the allowed excess ball.

### earth_polyhymnia_2029_d+0

- primary_last: psi_mass, T=1288.477 сут, α=0.30000000000000004, β=0.05, variable_mass=True, F=0.025 Н, departure parameter=None.
- recover_last: psi, T=1721.098 сут, α=0.19465820312499998, β=1, variable_mass=True, F=0.025 Н, departure parameter=None.
- broad_last: psi_limit, T=1543.416 сут, α=0.22499999999999998, β=0.3140625, variable_mass=True, F=0.025 Н, departure parameter=None.
- primary/pazov: mixed_functional.
- primary/psi: mass.
- recover/coupled: mass_and_thrust.
- recover/after_release: mass_and_thrust.
- recover/early_continue: fuel.
- transfer/exact_arcs_cartesian: Exact arc integration budget reached.
- transfer/exact_arcs_legacy: Exact arc integration budget reached.
- transfer/exact_arcs_rtn: Exact arc integration budget reached.
- transfer/exact_free_time: Free-duration integration budget reached.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: mass_and_thrust.
- after_release/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- broad_continue/pazov/functional/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached.
- early_continue/fuel/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: target_reached; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- early_continue/pazov/functional/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- pazov/functional/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- psi/mass/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.

### earth_polyhymnia_2029_d+90

- primary_last: psi_mass, T=531.472 сут, α=0.5, β=0.999609375, variable_mass=True, F=0.05576330215024744 Н, departure parameter=None.
- recover_last: psi_limit, T=1062.944 сут, α=0.0, β=0.025, variable_mass=True, F=0.028113921526790448 Н, departure parameter=None.
- broad_last: psi_limit, T=1095.750 сут, α=0.0, β=0.043750000000000004, variable_mass=True, F=0.027899996851287044 Н, departure parameter=None.
- primary/pazov: thrust_limit.
- primary/psi: mass.
- recover/coupled: mass_and_thrust.
- recover/after_release: mass_and_thrust.
- recover/early_continue: mass_and_thrust.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: mass_and_thrust.
- after_release/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- broad_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- early_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- psi/mass/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.

### earth_polyhymnia_2029_d-90

- primary_last: psi_mass, T=886.967 сут, α=0.5, β=0.9875, variable_mass=True, F=0.04279764002530825 Н, departure parameter=None.
- recover_last: psi_limit, T=1265.721 сут, α=0.3, β=0.6343750000000001, variable_mass=True, F=0.025 Н, departure parameter=None.
- broad_last: psi_limit, T=1331.255 сут, α=0.3, β=0.55, variable_mass=True, F=0.025 Н, departure parameter=None.
- primary/pazov: thrust_limit.
- primary/psi: mass.
- recover/coupled: mass_and_thrust.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: mass_and_thrust.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: mass_and_thrust.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- broad_continue/pazov/functional/continuation.json: target_reached; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached.
- psi/mass/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.

### earth_venus_2032_d+90

- primary_last: psi_mass, T=70.270 сут, α=0.5, β=0.999609375, variable_mass=True, F=0.6542590824816115 Н, departure parameter=None.
- recover_last: psi_limit, T=140.540 сут, α=0.0, β=0.00625, variable_mass=True, F=0.0977113263779545 Н, departure parameter=None.
- broad_last: psi_limit, T=440.226 сут, α=0.0, β=0.00625, variable_mass=True, F=0.13688954607949072 Н, departure parameter=None.
- primary/pazov: thrust_limit.
- primary/psi: mass.
- recover/coupled: mass_and_thrust.
- recover/after_release: mass_and_thrust.
- recover/early_continue: mass_and_thrust.
- transfer/R_fixed: Exact arc integration budget reached.
- transfer/R_free: Free-duration integration budget reached.
- transfer/broad_early_time: mass_and_thrust.
- after_release/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; free: Bounded collocation budget reached.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached.
- broad_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached.
- early_continue/pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- pazov/limit/continuation.json: time_budget; RuntimeError: active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.
- psi/mass/continuation.json: time_budget; RuntimeError: active: Bounded collocation budget reached; active shooting: Bounded shooting budget reached; free: Bounded collocation budget reached.

### venus_earth_2029_d+0

- primary_last: pazov_limit, T=841.323 сут, α=0.0, β=0.0, variable_mass=False, F=0.025 Н, departure parameter=None.
- recover_last: psi_limit, T=1403.772 сут, α=0.0, β=0.00625, variable_mass=True, F=0.025 Н, departure parameter=None.
- primary/pazov: mixed_functional.
- primary/psi: regularize.
- recover/coupled: mass_and_thrust.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: mass_and_thrust.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: No independently verified changed-duration intermediate; see trials.json.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- early_continue/pazov/functional/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- pazov/functional/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached.
- psi/regularize/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached.

### venus_earth_2029_d+90

- primary_last: pazov_limit, T=655.975 сут, α=0.0, β=0.0, variable_mass=False, F=0.025 Н, departure parameter=None.
- recover_last: psi_limit, T=1259.052 сут, α=0.0, β=0.00625, variable_mass=True, F=0.025 Н, departure parameter=None.
- broad_last: psi_limit, T=683.647 сут, α=0.0, β=0.08281250000000001, variable_mass=True, F=0.025 Н, departure parameter=None.
- primary/pazov: mixed_functional.
- primary/psi: regularize.
- recover/coupled: mass_and_thrust.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: mass_and_thrust.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: mass_and_thrust.
- broad_continue/departure/continuation.json: target_reached; RuntimeError: The solver was unable to satisfy boundary conditions tolerance on iteration 10.; Free intermediate excess exceeds its current homotopy bound.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: free: Bounded collocation budget reached; active: Bounded collocation budget reached.
- broad_continue/pazov/functional/continuation.json: time_budget; RuntimeError: free: Bounded collocation budget reached; active: Bounded collocation budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- early_continue/pazov/functional/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- pazov/functional/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached.
- psi/regularize/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached.

### venus_earth_2029_d-90

- primary_last: pazov_limit, T=1017.472 сут, α=0.0, β=0.0, variable_mass=False, F=0.025 Н, departure parameter=None.
- recover_last: psi_limit, T=1451.984 сут, α=0.0, β=0.000390625, variable_mass=True, F=0.025 Н, departure parameter=None.
- broad_last: psi_limit, T=1019.385 сут, α=0.0, β=0.0546875, variable_mass=True, F=0.025 Н, departure parameter=None.
- primary/pazov: mixed_functional.
- primary/psi: regularize.
- recover/coupled: mass_and_thrust.
- recover/release_intermediate: RuntimeError: No independently verified changed-duration intermediate; see trials.json.
- recover/early_continue: mass_and_thrust.
- transfer/R_transfer: unavailable.
- transfer/broad_early_time: mass_and_thrust.
- departure/continuation.json: target_reached; RuntimeError: The maximum number of mesh nodes is exceeded..
- broad_continue/departure/continuation.json: target_reached; RuntimeError: Independent departure replay failed: {'passed': False, 'method': 'LSODA, independently implemented Hamiltonian RHS', 'position_residual_m': 1398.8018252977736, 'velocity_residual_m_s': 0.0002754706934086001, 'trajectory_difference_m': 1398.8018317556503, 'velocity_difference_m_s': 0.0002754706920195451, 'free_velocity_transversality': 0.0074266782264731795, 'scope': 'Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity'}; Free intermediate excess exceeds its current homotopy bound.
- broad_continue/mass_and_thrust/continuation.json: time_budget; RuntimeError: free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- broad_continue/pazov/functional/continuation.json: time_budget; RuntimeError: free: Bounded collocation budget reached; active: Bounded collocation budget reached.
- coupled/mass_and_thrust/continuation.json: time_budget; RuntimeError: free: Bounded collocation budget reached; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- early_continue/mass_and_thrust/continuation.json: minimum_step; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- early_continue/pazov/functional/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: Bounded collocation budget reached.
- pazov/functional/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached.
- psi/regularize/continuation.json: time_budget; RuntimeError: free: The maximum number of mesh nodes is exceeded.; free shooting: Bounded shooting budget reached; active: The maximum number of mesh nodes is exceeded.; active shooting: Bounded shooting budget reached.

## Артефакты

[Сводные данные и проверки](../data/benchmarks/accepted42_psi_v1/final.json), [таблица CSV](../data/benchmarks/accepted42_psi_v1/results.csv). Компактный архив сохраняет финальные траектории, частичные опоры и диагностику. Полные узлы продолжения остаются в `runs/accepted42_psi_v1/`.

## Итоговые проверки

17 принятых решений: 14 встреч и 3 пролёта. Максимальная ошибка положения
при независимом интегрировании — 19,531 м; максимальная ошибка скорости
для встреч — 2,061×10⁻⁶ м/с. Для пролётов равенство скорости скорости цели
не является граничным условием. Все 17 прошли KIAM и аудит исходного запроса.

Из 8 дополнительных успехов четыре получены через изменение времени и
продолжение, четыре — через отдельную коррекцию точных дуг. Независимые
R-переносы в этой серии новых принятых решений не дали. Длительность
изменилась у 6 из 17 принятых траекторий, включая родителей коррекции дуг.

В Docker прошли 16 адресных тестов: 4 для физического свободного времени,
9 для промежуточного освобождения времени, 3 для новых контроллеров
(инициализация дуг от гладкого родителя, защита исходной массы и неизменность
дизайна серии). SHA256 проверены у всех 1037 файлов компактного архива.
