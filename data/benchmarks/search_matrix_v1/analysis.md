# Широкая матрица графа поиска — 11 ноября 2026

Завершено 15 из 15 постановок. Принято хотя бы одно решение: 10; исходные условия: 6.

Единый дизайн: 2 поколения × 4 особи, seed=17; даты 0/±90 суток; начальные длительности 0,8/1/1,2 от исходной; фиксированное и свободное время (0,5–1,5 от исходной длительности); F/c = 25 мН / 20 км/с либо 50 мН / 40 км/с; α=0,3/0,5/0,7. Масса 156 кг, сухая 90 кг, предел избытка 3 км/с. Пары F/c — варианты математической модели, без подтверждения реализуемости энергетической установки при той же массе.

Бюджет поиска 1800 с, узла 240 с, освобождения времени 90 с. В холодном пути: ИРТ 30 с, избыток 40 с, Пазов/масса/ПСИ по штатным бюджетам 60 с, отдельная bounded-попытка 20 с. Четыре отдельных процесса Docker. Один план и один набор истории для всей серии; индивидуальных повторов и подгонки не было. Это ограниченный генетический поиск, не полный перебор декартова произведения.

Каждая принятая траектория дополнительно перепроверена независимым интегрированием, аудитом параметров и неизменённым KIAM Fortran. Повторные узлы с одной физической конфигурацией не считаются разными решениями. Выбран вариант с наименьшим отклонением от исходной задачи; при равном отклонении — с меньшим расходом.

| Постановка | Итог | Старт TDB | T, сутки | F, мН / c, км/с | Топливо, кг | Сработавший маршрут |
|---|---|---|---:|---|---:|---|
| earth_venus_2032 | Исходные условия | 2032-11-01T00:00:00 | 390.800000 | 25 / 20 | 27.652005 | сохранённая ПСИ → повторная независимая проверка |
| earth_mars_2028 | Исходные условия | 2028-11-01T00:00:00 | 500.000000 | 25 / 20 | 22.898851 | сохранённая ПСИ → повторная независимая проверка |
| earth_apophis_2029 | Исходные условия | 2029-02-14T12:00:00 | 422.661802 | 25 / 20 | 18.640351 | сохранённая ПСИ → повторная независимая проверка |
| earth_eros_2029 | Не найдено в бюджете | — | — | — | — | psi: 6 |
| earth_bennu_2029 | Исходные условия | 2029-06-01T00:00:00 | 500.000000 | 25 / 20 | 32.631074 | сохранённая ПСИ → повторная независимая проверка |
| earth_ryugu_2028 | Исходные условия | 2028-06-01T00:00:00 | 600.000000 | 25 / 20 | 20.831504 | сохранённая ПСИ → повторная независимая проверка |
| earth_polyhymnia_2029 | Изменены условия | 2029-03-01T00:00:00 | 900.000000 | 50 / 40 | 37.579233 | ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T) |
| earth_ceres_2030 | Изменены условия | 2029-11-03T00:00:00 | 800.000000 | 50 / 40 | 40.289391 | сохранённая ПСИ → повторная независимая проверка |
| earth_mercury_2029 | Не найдено в бюджете | — | — | — | — | psi: 6 |
| earth_jupiter_2028 | Изменены условия | 2028-06-01T00:00:00 | 1100.000000 | 50 / 40 | 58.612970 | ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T) |
| venus_earth_2029 | Не найдено в бюджете | — | — | — | — | psi: 6 |
| earth_mars_flyby_2028 | Исходные условия | 2028-11-01T00:00:00 | 500.000000 | 25 / 20 | 17.509634 | сохранённая ПСИ → повторная независимая проверка |
| earth_2015re36_2028 | Изменены условия | 2028-09-01T00:00:00 | 600.000000 | 50 / 40 | 27.076223 | ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T) |
| earth_saturn_flyby_2028 | Не найдено в бюджете | — | — | — | — | departure: 3, irt: 2 |
| earth_mars_2029 | Не найдено в бюджете | — | — | — | — | psi: 7 |

## earth_venus_2032

Исходно: Earth → Venus, rendezvous, 2032-11-01T00:00:00, T=390.8 суток.

Поиск: finished; геномов 8, узлов 6, физических конфигураций 2.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `0f9e122b85679c12fe17e6e2` / reference | 2032-11-01T00:00:00 | 390.8000 | 25 / 20 | 0.5 | completed: final |
| `ee324b115719cece679e3807` / release | 2032-11-01T00:00:00 | 390.8000 | 25 / 20 | 0.5 | completed: final |
| `ddd6f120b3a5e2ee44d88a58` / cold | 2032-11-01T00:00:00 | 390.8000 | 50 / 40 | 0.5 | partial: psi |
| `5cedb03f754532844ae401d7` / r_transfer | 2033-01-30T00:00:00 | 390.8000 | 25 / 20 | 0.5 | failed: r_transfer |
| `4058e9c5e5216da727d35b5c` / r_release | 2033-01-30T00:00:00 | 390.8000 | 25 / 20 | 0.5 | failed: r_release |
| `32ac39b8ac740ec89ae297b5` / reference | 2032-11-01T00:00:00 | 390.8000 | 25 / 20 | 0.7 | completed: final |

- Узел `0f9e122b85679c12fe17e6e2`: сохранённая ПСИ → повторная независимая проверка. Изменения: `{}`. Топливо 27.652005 кг; невязки 1.19797 м / 3.71074e-07 м/с.
  Исторический источник: `data/benchmarks/free_time_physical_matrix_v1/earth_venus_2032/anchor_00/final`.

- Узел `ee324b115719cece679e3807`: сохранённая ПСИ → повторная независимая проверка → освобождение T. Изменения: `{"tof_days": {"requested": 390.8, "actual": 410.9696560096026}}`. Топливо 26.860087 кг; невязки 1.53044 м / 4.97658e-07 м/с.

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `ddd6f120b3a5e2ee44d88a58` / cold: partial, этап psi; α/β={"a_max": 0.05324958477304662, "alpha": 0.8, "beta": 1.0, "q": 0.03979847562457073, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "fuel", "last_result": "fuel/point_0002"}.
- `5cedb03f754532844ae401d7` / r_transfer: failed, этап r_transfer; α/β=null; RuntimeError: free: Exact independent replay failed: {'passed': False, 'position_residual_m': 1840175469.8962452, 'velocity_residual_m_s': 261.15697016424025, 'parameter_audit': {'passed': True, 'configuration_sha256': '018e49c5760235134faab9d4a91ff0d2738bc84796534736ed974be733e6a5a6', 'configuratio.
- `4058e9c5e5216da727d35b5c` / r_release: failed, этап r_release; α/β=null; TimeoutError: Free-duration integration budget reached.

## earth_mars_2028

Исходно: Earth → Mars, rendezvous, 2028-11-01T00:00:00, T=500 суток.

Поиск: finished; геномов 8, узлов 7, физических конфигураций 3.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `40ef4fa3c505aaa0dd4e75c0` / reference | 2028-11-01T00:00:00 | 500.0000 | 25 / 20 | 0.5 | completed: final |
| `c218561a082f6f32f36caed5` / release | 2028-11-01T00:00:00 | 500.0000 | 25 / 20 | 0.5 | failed: release |
| `5c1538b3374e96954a3d3ce9` / cold | 2028-11-01T00:00:00 | 500.0000 | 50 / 40 | 0.5 | completed: final |
| `bf77b0540a62ab8268d72eec` / release | 2028-11-01T00:00:00 | 500.0000 | 50 / 40 | 0.5 | completed: final |
| `782f176eb45cf20102b81e01` / r_transfer | 2029-01-30T00:00:00 | 500.0000 | 25 / 20 | 0.5 | failed: r_transfer |
| `e1f6e710eb2ea2e3a317b9cd` / r_release | 2029-01-30T00:00:00 | 500.0000 | 25 / 20 | 0.5 | failed: r_release |
| `95845bcad451f7bd3be40d44` / reference | 2028-11-01T00:00:00 | 500.0000 | 25 / 20 | 0.7 | completed: final |

- Узел `40ef4fa3c505aaa0dd4e75c0`: сохранённая ПСИ → повторная независимая проверка. Изменения: `{}`. Топливо 22.898851 кг; невязки 2.93625 м / 2.52269e-07 м/с.
  Исторический источник: `data/benchmarks/free_time_physical_matrix_v1/earth_mars_2028/anchor_00/final`.

- Узел `5c1538b3374e96954a3d3ce9`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T). Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 11.695754 кг; невязки 6.69594 м / 7.79239e-07 м/с.

- Узел `bf77b0540a62ab8268d72eec`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T) → освобождение T. Изменения: `{"tof_days": {"requested": 500.0, "actual": 659.526155907966}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 11.472717 кг; невязки 5.31315 м / 4.77727e-07 м/с.

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `c218561a082f6f32f36caed5` / release: failed, этап release; α/β=null; TimeoutError: Free-duration integration budget reached.
- `782f176eb45cf20102b81e01` / r_transfer: failed, этап r_transfer; α/β=null; RuntimeError: active: Exact independent replay failed: {'passed': False, 'position_residual_m': 65127565.275247715, 'velocity_residual_m_s': 21.498148346972737, 'parameter_audit': {'passed': True, 'configuration_sha256': '679fe996dcde174aadad721d35790ca6d2021b5e116dc0d38a44588f350fa7bc', 'configurat.
- `e1f6e710eb2ea2e3a317b9cd` / r_release: failed, этап r_release; α/β=null; RuntimeError: active: Free-duration physical replay failed: {'passed': False, 'position_residual_m': 0.9354905014022049, 'velocity_residual_m_s': 3.122099286213288e-07, 'parameter_audit': {'passed': True, 'configuration_sha256': 'b09ef4828892699068e9238149a2570c773a4c4e6be9d106e753442cd833c0ea', 'co.

## earth_apophis_2029

Исходно: Earth → Apophis, rendezvous, 2029-02-14T12:00:00, T=422.6618015373437 суток.

Поиск: finished; геномов 8, узлов 7, физических конфигураций 2.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `4801b96f480e5a1eb4a9f01d` / reference | 2029-02-14T12:00:00 | 422.6618 | 25 / 20 | 0.5 | completed: final |
| `89bfa20c65fee8fc23e4c957` / release | 2029-02-14T12:00:00 | 422.6618 | 25 / 20 | 0.5 | completed: final |
| `7cfb5368528e28305f0414f3` / cold | 2029-02-14T12:00:00 | 422.6618 | 50 / 40 | 0.5 | completed: final |
| `9e36965099b7ca4893a480b9` / release | 2029-02-14T12:00:00 | 422.6618 | 50 / 40 | 0.5 | completed: final |
| `69428d0ccf57f72055740daa` / r_transfer | 2029-05-15T12:00:00 | 422.6618 | 25 / 20 | 0.5 | failed: r_transfer |
| `6b6dda1396be66289cf69c03` / r_release | 2029-05-15T12:00:00 | 422.6618 | 25 / 20 | 0.5 | failed: r_release |
| `7c448e450d17d8de7ff5eb46` / reference | 2029-02-14T12:00:00 | 422.6618 | 25 / 20 | 0.7 | completed: final |

- Узел `4801b96f480e5a1eb4a9f01d`: сохранённая ПСИ → повторная независимая проверка. Изменения: `{}`. Топливо 18.640351 кг; невязки 0.914896 м / 1.14234e-07 м/с.
  Исторический источник: `data/benchmarks/free_time_physical_matrix_v1/earth_apophis_2029/anchor_00/final`.

- Узел `9e36965099b7ca4893a480b9`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T) → освобождение T. Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 9.211762 кг; невязки 1.28564 м / 1.75118e-07 м/с.

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `69428d0ccf57f72055740daa` / r_transfer: failed, этап r_transfer; α/β=null; RuntimeError: active: Exact independent replay failed: {'passed': False, 'position_residual_m': 8552855686.082364, 'velocity_residual_m_s': 1827.6628277133048, 'parameter_audit': {'passed': True, 'configuration_sha256': 'f8fc5680270ac96b06b2c5e09ef85d88267e3a2dfd5c9b6e6482be165788690d', 'configurati.
- `6b6dda1396be66289cf69c03` / r_release: failed, этап r_release; α/β=null; TimeoutError: Free-duration integration budget reached.

## earth_eros_2029

Исходно: Earth → Eros, rendezvous, 2029-03-01T00:00:00, T=400 суток.

Поиск: finished; геномов 8, узлов 6, физических конфигураций 0.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `d7bc2497e9f5f697132f7ae2` / cold | 2029-03-01T00:00:00 | 400.0000 | 25 / 20 | 0.5 | partial: psi |
| `c93b8891d06eadd7fd0c78a5` / cold | 2029-03-01T00:00:00 | 400.0000 | 50 / 40 | 0.5 | partial: psi |
| `e7be2208e830779001b7e827` / cold | 2028-12-01T00:00:00 | 320.0000 | 50 / 40 | 0.3 | partial: psi |
| `734f800503c056606bc2beac` / cold | 2028-12-01T00:00:00 | 480.0000 | 50 / 40 | 0.5 | partial: psi |
| `d0c7aeac5e75b4ffa3cfa65c` / cold | 2028-12-01T00:00:00 | 480.0000 | 25 / 20 | 0.5 | partial: psi |
| `2803a4a0d0ee2a838d9d717d` / cold | 2029-03-01T00:00:00 | 480.0000 | 50 / 40 | 0.7 | partial: psi |

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `d7bc2497e9f5f697132f7ae2` / cold: partial, этап psi; α/β={"a_max": 0.08674051192651461, "alpha": 0.5, "beta": 0.8, "q": 0.1297768139255286, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.8, "last_result": "mass/point_0008"}.
- `c93b8891d06eadd7fd0c78a5` / cold: partial, этап psi; α/β={"a_max": 0.07003793846991459, "alpha": 0.5, "beta": 1.0, "q": 0.05239362961241259, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "physical_thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.5, "last_result": "limit/point_0003"}.
- `e7be2208e830779001b7e827` / cold: partial, этап psi; α/β={"a_max": 0.530021428721014, "alpha": 0.3, "beta": 0.9750000000000001, "q": 0.3974457343911698, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `734f800503c056606bc2beac` / cold: partial, этап psi; α/β={"a_max": 0.18182637830881915, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.1363456542370739, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `d0c7aeac5e75b4ffa3cfa65c` / cold: partial, этап psi; α/β={"a_max": 0.1814766323776624, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.2721667824043459, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `2803a4a0d0ee2a838d9d717d` / cold: partial, этап psi; α/β={"a_max": 0.23467630380186996, "alpha": 0.7, "beta": 0.9750000000000001, "q": 0.17555547191736443, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.

## earth_bennu_2029

Исходно: Earth → Bennu, rendezvous, 2029-06-01T00:00:00, T=500 суток.

Поиск: finished; геномов 8, узлов 6, физических конфигураций 1.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `dd6f34a8470c52a5a64825e4` / reference | 2029-06-01T00:00:00 | 500.0000 | 25 / 20 | 0.5 | completed: final |
| `301237f14108edac031d541e` / release | 2029-06-01T00:00:00 | 500.0000 | 25 / 20 | 0.5 | failed: release |
| `f453e754e3feebba7af095d4` / cold | 2029-06-01T00:00:00 | 500.0000 | 50 / 40 | 0.5 | partial: psi |
| `a6d15b20cb1a36c5ed749993` / r_transfer | 2029-08-30T00:00:00 | 500.0000 | 25 / 20 | 0.5 | failed: r_transfer |
| `0c9e431bd6d51ebaaac6e59a` / r_release | 2029-08-30T00:00:00 | 500.0000 | 25 / 20 | 0.5 | failed: r_release |
| `720311bc15a1bf4dfa31a898` / reference | 2029-06-01T00:00:00 | 500.0000 | 25 / 20 | 0.7 | completed: final |

- Узел `dd6f34a8470c52a5a64825e4`: сохранённая ПСИ → повторная независимая проверка. Изменения: `{}`. Топливо 32.631074 кг; невязки 1.11455 м / 1.93822e-07 м/с.
  Исторический источник: `data/benchmarks/free_time_physical_matrix_v1/earth_bennu_2029/anchor_00/final`.

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `301237f14108edac031d541e` / release: failed, этап release; α/β=null; TimeoutError: Free-duration integration budget reached.
- `f453e754e3feebba7af095d4` / cold: partial, этап psi; α/β={"a_max": 0.05557024434919569, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.04109235189196995, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0009"}.
- `a6d15b20cb1a36c5ed749993` / r_transfer: failed, этап r_transfer; α/β=null; RuntimeError: free: Exact independent replay failed: {'passed': False, 'position_residual_m': 2407468620.9691725, 'velocity_residual_m_s': 438.53457422428636, 'parameter_audit': {'passed': True, 'configuration_sha256': '7bb71546346bdc818fc88ce03ef1ff4bf704edfa9e8c67d65a9bd3eae65b4faa', 'configuratio.
- `0c9e431bd6d51ebaaac6e59a` / r_release: failed, этап r_release; α/β=null; TimeoutError: Free-duration integration budget reached.

## earth_ryugu_2028

Исходно: Earth → Ryugu, rendezvous, 2028-06-01T00:00:00, T=600 суток.

Поиск: finished; геномов 8, узлов 6, физических конфигураций 2.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `f35658b2b98f6d968a8fdee2` / reference | 2028-06-01T00:00:00 | 600.0000 | 25 / 20 | 0.5 | completed: final |
| `909a2dfbf2e47c5e9e08b47e` / release | 2028-06-01T00:00:00 | 600.0000 | 25 / 20 | 0.5 | completed: final |
| `50a9dc3715a1f83cd60af23e` / cold | 2028-06-01T00:00:00 | 600.0000 | 50 / 40 | 0.5 | partial: psi |
| `5bce4b46396d67bf3e25bc0c` / r_transfer | 2028-08-30T00:00:00 | 600.0000 | 25 / 20 | 0.5 | failed: r_transfer |
| `0ef1c15c485308a604b4ecf8` / r_release | 2028-08-30T00:00:00 | 600.0000 | 25 / 20 | 0.5 | failed: r_release |
| `fa9625637441138eb15388a3` / reference | 2028-06-01T00:00:00 | 600.0000 | 25 / 20 | 0.7 | completed: final |

- Узел `f35658b2b98f6d968a8fdee2`: сохранённая ПСИ → повторная независимая проверка. Изменения: `{}`. Топливо 20.831504 кг; невязки 2.27619 м / 4.07487e-07 м/с.
  Исторический источник: `data/benchmarks/free_time_physical_matrix_v1/earth_ryugu_2028/anchor_00/final`.

- Узел `909a2dfbf2e47c5e9e08b47e`: сохранённая ПСИ → повторная независимая проверка → освобождение T. Изменения: `{"tof_days": {"requested": 600.0, "actual": 656.3187285322039}}`. Топливо 17.320922 кг; невязки 6.4169 м / 1.25685e-06 м/с.

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `50a9dc3715a1f83cd60af23e` / cold: partial, этап psi; α/β={"a_max": 0.05557710890696852, "alpha": 0.5, "beta": 0.65625, "q": 0.04109615891771888, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.65625, "last_result": "mass/point_0006"}.
- `5bce4b46396d67bf3e25bc0c` / r_transfer: failed, этап r_transfer; α/β=null; RuntimeError: active: Exact independent replay failed: {'passed': False, 'position_residual_m': 1.8613458180816123, 'velocity_residual_m_s': 3.1915369334318667e-07, 'parameter_audit': {'passed': True, 'configuration_sha256': '6b43f61ee215812c626a3f6bb88732501054b16143dbf89db9393ffd51e49ac8', 'config.
- `0ef1c15c485308a604b4ecf8` / r_release: failed, этап r_release; α/β=null; TimeoutError: Free-duration integration budget reached.

## earth_polyhymnia_2029

Исходно: Earth → Polyhymnia, rendezvous, 2029-03-01T00:00:00, T=900 суток.

Поиск: finished; геномов 8, узлов 9, физических конфигураций 5.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `77bd25e53515f7270b462048` / cold | 2029-03-01T00:00:00 | 900.0000 | 25 / 20 | 0.5 | partial: psi |
| `f5edb236ccb9617ce6690ec7` / cold | 2029-03-01T00:00:00 | 900.0000 | 50 / 40 | 0.5 | completed: final |
| `c5b957b2812cd49ba966c80e` / release | 2029-03-01T00:00:00 | 900.0000 | 50 / 40 | 0.5 | completed: final |
| `69cb93ec688c684a1ac41bec` / cold | 2028-12-01T00:00:00 | 720.0000 | 50 / 40 | 0.3 | completed: final |
| `b80f2908245b8c97458792ca` / release | 2028-12-01T00:00:00 | 720.0000 | 50 / 40 | 0.3 | completed: final |
| `b39937f750f63d3a00371bbe` / cold | 2028-12-01T00:00:00 | 1080.0000 | 50 / 40 | 0.5 | partial: psi |
| `6d510b965e46cb5ba6ba8b9f` / cold | 2028-12-01T00:00:00 | 720.0000 | 25 / 20 | 0.3 | partial: psi |
| `7b78c7717903b482d25bb07b` / cold | 2029-03-01T00:00:00 | 720.0000 | 50 / 40 | 0.5 | completed: final |
| `f08592f35dc9dd116bdf2820` / release | 2029-03-01T00:00:00 | 720.0000 | 50 / 40 | 0.5 | completed: final |

- Узел `f5edb236ccb9617ce6690ec7`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T). Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 37.579233 кг; невязки 1.19144 м / 8.40643e-08 м/с.

- Узел `7b78c7717903b482d25bb07b`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T). Изменения: `{"tof_days": {"requested": 900.0, "actual": 720.0}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 42.790661 кг; невязки 4.71724 м / 3.48321e-07 м/с.

- Узел `69cb93ec688c684a1ac41bec`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T). Изменения: `{"launch_tdb": {"requested": "2029-03-01T00:00:00", "actual": "2028-12-01T00:00:00"}, "tof_days": {"requested": 900.0, "actual": 720.0}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 50.647456 кг; невязки 39.8951 м / 3.09921e-06 м/с.

- Узел `f08592f35dc9dd116bdf2820`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T) → освобождение T. Изменения: `{"tof_days": {"requested": 900.0, "actual": 1350.0}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 30.874283 кг; невязки 4.75693 м / 8.69122e-08 м/с.

- Узел `b80f2908245b8c97458792ca`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T) → освобождение T. Изменения: `{"launch_tdb": {"requested": "2029-03-01T00:00:00", "actual": "2028-12-01T00:00:00"}, "tof_days": {"requested": 900.0, "actual": 1350.0}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 28.728179 кг; невязки 4.51103 м / 2.92093e-07 м/с.

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `77bd25e53515f7270b462048` / cold: partial, этап psi; α/β={"a_max": 0.040595280312546084, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.060736627238714265, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `b39937f750f63d3a00371bbe` / cold: partial, этап psi; α/β={"a_max": 0.05255081157613851, "alpha": 0.5, "beta": 0.4375, "q": 0.039406134861622956, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.4375, "last_result": "mass/point_0005"}.
- `6d510b965e46cb5ba6ba8b9f` / cold: partial, этап psi; α/β={"a_max": 0.0565315836037363, "alpha": 0.3, "beta": 0.9750000000000001, "q": 0.08478237121808649, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.

## earth_ceres_2030

Исходно: Earth → Ceres, rendezvous, 2030-02-01T00:00:00, T=1000 суток.

Поиск: finished; геномов 8, узлов 8, физических конфигураций 1.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `051effa7065e39297ca2b178` / cold | 2030-02-01T00:00:00 | 1000.0000 | 25 / 20 | 0.5 | partial: psi |
| `ab18373dc98fd77cf4feca4f` / cold | 2030-02-01T00:00:00 | 1000.0000 | 50 / 40 | 0.5 | partial: psi |
| `6ec275fd02107a63900b0a77` / reference | 2029-11-03T00:00:00 | 800.0000 | 50 / 40 | 0.3 | completed: final |
| `4079f7d3f2108a8fb1289e33` / release | 2029-11-03T00:00:00 | 800.0000 | 50 / 40 | 0.3 | failed: release |
| `18abb9b66937b9188bca5b2b` / cold | 2029-11-03T00:00:00 | 1200.0000 | 50 / 40 | 0.5 | partial: psi |
| `788a0f11f73ef4e67ed5f4e7` / cold | 2029-11-03T00:00:00 | 800.0000 | 25 / 20 | 0.3 | partial: psi |
| `367b7f975a1155866ff90d52` / reference | 2029-11-03T00:00:00 | 800.0000 | 50 / 40 | 0.5 | completed: final |
| `195e2fcc0cd78663e1eac686` / release | 2029-11-03T00:00:00 | 800.0000 | 50 / 40 | 0.5 | failed: release |

- Узел `6ec275fd02107a63900b0a77`: сохранённая ПСИ → повторная независимая проверка. Изменения: `{"launch_tdb": {"requested": "2030-02-01T00:00:00", "actual": "2029-11-03T00:00:00"}, "tof_days": {"requested": 1000.0, "actual": 800.0}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 40.289391 кг; невязки 2.19756 м / 1.79407e-07 м/с.
  Исторический источник: `data/benchmarks/search_graph_v1/ceres/nodes/7d310ebe418ba840076228ae/final`.

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `051effa7065e39297ca2b178` / cold: partial, этап psi; α/β={"a_max": 0.026237657322759737, "alpha": 0.5125, "beta": 1.0, "q": 0.03936366772285469, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "fuel", "last_result": "fuel/point_0003"}.
- `ab18373dc98fd77cf4feca4f` / cold: partial, этап psi; α/β={"a_max": 0.05247531464551947, "alpha": 0.5, "beta": 0.25, "q": 0.03936366772285469, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.25, "last_result": "mass/point_0003"}.
- `4079f7d3f2108a8fb1289e33` / release: failed, этап release; α/β=null; TimeoutError: Free-duration integration budget reached.
- `18abb9b66937b9188bca5b2b` / cold: partial, этап psi; α/β={"a_max": 0.05319634768076462, "alpha": 0.125, "beta": 1.0, "q": 0.03976863003956065, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "fuel", "last_result": "fuel/initial"}.
- `788a0f11f73ef4e67ed5f4e7` / cold: partial, этап psi; α/β={"a_max": 0.0418754655489796, "alpha": 0.3, "beta": 0.8875000000000002, "q": 0.0626106854983921, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.8875000000000002, "last_result": "mass/point_0009"}.
- `195e2fcc0cd78663e1eac686` / release: failed, этап release; α/β=null; TimeoutError: Free-duration integration budget reached.

## earth_mercury_2029

Исходно: Earth → Mercury, rendezvous, 2029-01-01T00:00:00, T=300 суток.

Поиск: finished; геномов 8, узлов 6, физических конфигураций 0.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `f9d03d8b6f1827043f0bb214` / cold | 2029-01-01T00:00:00 | 300.0000 | 25 / 20 | 0.5 | partial: psi |
| `f5def431bf6602e583f0edcb` / cold | 2029-01-01T00:00:00 | 300.0000 | 50 / 40 | 0.5 | partial: psi |
| `6d9cbdf7b96b1aafa03a3c3e` / cold | 2028-10-03T00:00:00 | 240.0000 | 50 / 40 | 0.3 | partial: psi |
| `a2c8dba2b581b60fef217681` / cold | 2028-10-03T00:00:00 | 360.0000 | 50 / 40 | 0.5 | partial: psi |
| `cbabee4d5a1654324c0fac61` / cold | 2028-10-03T00:00:00 | 240.0000 | 25 / 20 | 0.3 | partial: psi |
| `701fdb21827af4c4f00a8d89` / cold | 2029-01-01T00:00:00 | 240.0000 | 50 / 40 | 0.5 | partial: psi |

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `f9d03d8b6f1827043f0bb214` / cold: partial, этап psi; α/β={"a_max": 0.16072939226301447, "alpha": 0.5, "beta": 0.3, "q": 0.24138762376208234, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.3, "last_result": "mass/point_0005"}.
- `f5def431bf6602e583f0edcb` / cold: partial, этап psi; α/β={"a_max": 0.12913513534743598, "alpha": 0.5, "beta": 1.0, "q": 0.09696926936270565, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "physical_thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.3375, "last_result": "limit/point_0005"}.
- `6d9cbdf7b96b1aafa03a3c3e` / cold: partial, этап psi; α/β={"a_max": 0.5345413363771343, "alpha": 0.3, "beta": 0.9750000000000001, "q": 0.3979182640737732, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `a2c8dba2b581b60fef217681` / cold: partial, этап psi; α/β={"a_max": 0.11811336168654435, "alpha": 0.5, "beta": 0.8875000000000001, "q": 0.08792484443722788, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.8875000000000001, "last_result": "mass/point_0008"}.
- `cbabee4d5a1654324c0fac61` / cold: partial, этап psi; α/β={"a_max": 0.5354257592364966, "alpha": 0.3, "beta": 0.9750000000000001, "q": 0.7971532757401265, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `701fdb21827af4c4f00a8d89` / cold: partial, этап psi; α/β={"a_max": 0.1382156884461351, "alpha": 0.5, "beta": 1.0, "q": 0.10378797596041853, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "physical_thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.3375, "last_result": "limit/point_0005"}.

## earth_jupiter_2028

Исходно: Earth → Jupiter, rendezvous, 2028-06-01T00:00:00, T=1100 суток.

Поиск: finished; геномов 8, узлов 7, физических конфигураций 2.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `d99d648a97fd004529563d9e` / cold | 2028-06-01T00:00:00 | 1100.0000 | 25 / 20 | 0.5 | partial: psi |
| `f5021dcd3d6a47e87e9d7dc0` / cold | 2028-06-01T00:00:00 | 1100.0000 | 50 / 40 | 0.5 | completed: final |
| `7cec44b2d7a50babfc172c57` / release | 2028-06-01T00:00:00 | 1100.0000 | 50 / 40 | 0.5 | completed: final |
| `c2648b2aa9fbec567f0f9737` / cold | 2028-03-03T00:00:00 | 880.0000 | 50 / 40 | 0.3 | partial: departure |
| `a96213375654f12b4aed0f97` / cold | 2028-03-03T00:00:00 | 1320.0000 | 50 / 40 | 0.5 | partial: psi |
| `783b4326370dd72bb25a15ba` / cold | 2028-03-03T00:00:00 | 1320.0000 | 25 / 20 | 0.5 | partial: psi |
| `ab51c2f6b9f2751dad451ff6` / cold | 2028-06-01T00:00:00 | 1320.0000 | 50 / 40 | 0.7 | partial: psi |

- Узел `f5021dcd3d6a47e87e9d7dc0`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T). Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 58.612970 кг; невязки 15.9744 м / 4.35142e-07 м/с.

- Узел `7cec44b2d7a50babfc172c57`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T) → освобождение T. Изменения: `{"tof_days": {"requested": 1100.0, "actual": 1360.2395578302157}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 46.879012 кг; невязки 12.5248 м / 1.66949e-07 м/с.

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `d99d648a97fd004529563d9e` / cold: partial, этап psi; α/β={"a_max": 0.053628156188192694, "alpha": 0.5, "beta": 0.7437500000000001, "q": 0.079310035103243, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.7437500000000001, "last_result": "mass/point_0008"}.
- `c2648b2aa9fbec567f0f9737` / cold: partial, этап departure; α/β=null; {"status": "partial", "reached_parameter": 0.936328125, "last_result": "stage_departure/point_0010"}.
- `a96213375654f12b4aed0f97` / cold: partial, этап psi; α/β={"a_max": 0.05311613045177622, "alpha": 0.39250000000000007, "beta": 1.0, "q": 0.03972364484126802, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "fuel", "last_result": "fuel/point_0001"}.
- `783b4326370dd72bb25a15ba` / cold: partial, этап psi; α/β={"a_max": 0.03932696640115103, "alpha": 0.5, "beta": 0.8, "q": 0.05882244932816121, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.8, "last_result": "mass/point_0003"}.
- `ab51c2f6b9f2751dad451ff6` / cold: partial, этап psi; α/β={"a_max": 0.05557710890696852, "alpha": 0.3578125, "beta": 1.0, "q": 0.04109615891771888, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "fuel", "last_result": "fuel/point_0004"}.

## venus_earth_2029

Исходно: Venus → Earth, rendezvous, 2029-01-01T00:00:00, T=250 суток.

Поиск: finished; геномов 8, узлов 6, физических конфигураций 0.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `25efd64aedf6daa81a444886` / cold | 2029-01-01T00:00:00 | 250.0000 | 25 / 20 | 0.5 | partial: psi |
| `8b12ceb5f13e2a7abc4a17bc` / cold | 2029-01-01T00:00:00 | 250.0000 | 50 / 40 | 0.5 | partial: psi |
| `7b19a01faea16c645ec9e87f` / cold | 2028-10-03T00:00:00 | 200.0000 | 50 / 40 | 0.3 | partial: psi |
| `fad1de731b60e9e21e64c9b8` / cold | 2028-10-03T00:00:00 | 300.0000 | 50 / 40 | 0.5 | partial: psi |
| `ba9ceae19847ecc15dcb23f7` / cold | 2028-10-03T00:00:00 | 300.0000 | 25 / 20 | 0.5 | partial: psi |
| `c20c4d470149837d5a477d55` / cold | 2029-01-01T00:00:00 | 300.0000 | 50 / 40 | 0.7 | partial: psi |

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `25efd64aedf6daa81a444886` / cold: partial, этап psi; α/β={"a_max": 0.3659468013766871, "alpha": 0.5, "beta": 0.9367187500000003, "q": 0.6403653870221859, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9367187500000003, "last_result": "mass/point_0011"}.
- `8b12ceb5f13e2a7abc4a17bc` / cold: partial, этап psi; α/β={"a_max": 0.3665722364289253, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.3207299137050898, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `7b19a01faea16c645ec9e87f` / cold: partial, этап psi; α/β={"a_max": 0.3538061099531336, "alpha": 0.3, "beta": 0.9750000000000001, "q": 0.31052591903996907, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `fad1de731b60e9e21e64c9b8` / cold: partial, этап psi; α/β={"a_max": 0.13135129818946653, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.11528343191354168, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `ba9ceae19847ecc15dcb23f7` / cold: partial, этап psi; α/β={"a_max": 0.1311852278168525, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.23027535300445726, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `c20c4d470149837d5a477d55` / cold: partial, этап psi; α/β={"a_max": 0.24363211415802266, "alpha": 0.7, "beta": 0.9750000000000001, "q": 0.21316428028188047, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.

## earth_mars_flyby_2028

Исходно: Earth → Mars, flyby, 2028-11-01T00:00:00, T=500 суток.

Поиск: finished; геномов 8, узлов 7, физических конфигураций 6.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `1a9aa7be8cde7ec9fcebcac1` / reference | 2028-11-01T00:00:00 | 500.0000 | 25 / 20 | 0.5 | completed: final |
| `0c413c7a4640904225f52a14` / release | 2028-11-01T00:00:00 | 500.0000 | 25 / 20 | 0.5 | completed: final |
| `7f8ceb2edb724b578a63c028` / cold | 2028-11-01T00:00:00 | 500.0000 | 50 / 40 | 0.5 | completed: final |
| `9309d596e20f8b04ffcedb81` / release | 2028-11-01T00:00:00 | 500.0000 | 50 / 40 | 0.5 | completed: final |
| `b3b25d66ead61e52f9c0c1f1` / r_transfer | 2029-01-30T00:00:00 | 500.0000 | 25 / 20 | 0.5 | completed: final |
| `6e0a10cbd8ebc45810d1ef59` / release | 2029-01-30T00:00:00 | 500.0000 | 25 / 20 | 0.5 | completed: final |
| `610068a9a502bbbf18a22c2e` / reference | 2028-11-01T00:00:00 | 500.0000 | 25 / 20 | 0.7 | completed: final |

- Узел `1a9aa7be8cde7ec9fcebcac1`: сохранённая ПСИ → повторная независимая проверка. Изменения: `{}`. Топливо 17.509634 кг; невязки 3.38221 м / 4187.09 м/с.
  Исторический источник: `data/benchmarks/free_time_physical_matrix_v1/earth_mars_flyby_2028/anchor_00/final`.

- Узел `b3b25d66ead61e52f9c0c1f1`: сохранённая ПСИ → R-перенос даты → коррекция при фикс. T. Изменения: `{"launch_tdb": {"requested": "2028-11-01T00:00:00", "actual": "2029-01-30T00:00:00"}}`. Топливо 16.578208 кг; невязки 7.31227 м / 6056.31 м/с.
  Исторический источник: `data/benchmarks/free_time_physical_matrix_v1/earth_mars_flyby_2028/anchor_00/final`.

- Узел `0c413c7a4640904225f52a14`: сохранённая ПСИ → повторная независимая проверка → освобождение T. Изменения: `{"tof_days": {"requested": 500.0, "actual": 306.9815310032382}}`. Топливо 2.854265 кг; невязки 1.06541 м / 3019.83 м/с.

- Узел `6e0a10cbd8ebc45810d1ef59`: сохранённая ПСИ → R-перенос даты → коррекция при фикс. T → освобождение T. Изменения: `{"launch_tdb": {"requested": "2028-11-01T00:00:00", "actual": "2029-01-30T00:00:00"}, "tof_days": {"requested": 500.0, "actual": 377.6788282703631}}`. Топливо 1.402932 кг; невязки 6.48051 м / 6764.73 м/с.

- Узел `7f8ceb2edb724b578a63c028`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T). Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 8.625263 кг; невязки 2.46634 м / 4255.4 м/с.

- Узел `9309d596e20f8b04ffcedb81`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T) → освобождение T. Изменения: `{"tof_days": {"requested": 500.0, "actual": 306.95659461234834}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 1.429933 кг; невязки 0.920093 м / 3020.53 м/с.

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):


## earth_2015re36_2028

Исходно: Earth → 2015RE36, rendezvous, 2028-09-01T00:00:00, T=600 суток.

Поиск: finished; геномов 8, узлов 7, физических конфигураций 2.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `83f5783e95f8671257bc1360` / cold | 2028-09-01T00:00:00 | 600.0000 | 25 / 20 | 0.5 | partial: psi |
| `467f062746f922e0fcb511f3` / cold | 2028-09-01T00:00:00 | 600.0000 | 50 / 40 | 0.5 | completed: final |
| `86b93226de94efccb9a5d9f0` / release | 2028-09-01T00:00:00 | 600.0000 | 50 / 40 | 0.5 | failed: release |
| `4c783c88bcb7a75866595146` / cold | 2028-06-03T00:00:00 | 480.0000 | 50 / 40 | 0.3 | partial: psi |
| `72a47c2421671676e8998901` / cold | 2028-06-03T00:00:00 | 720.0000 | 50 / 40 | 0.5 | completed: final |
| `cf058b5e1d58861d2de6f272` / cold | 2028-06-03T00:00:00 | 720.0000 | 25 / 20 | 0.5 | partial: psi |
| `3b41955c66e1cfc581ad2886` / cold | 2028-09-01T00:00:00 | 720.0000 | 50 / 40 | 0.7 | partial: psi |

- Узел `467f062746f922e0fcb511f3`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T). Изменения: `{"spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 27.076223 кг; невязки 4.14199 м / 1.04864e-06 м/с.

- Узел `72a47c2421671676e8998901`: ILTT → избыток → Пазов → масса → точная ПСИ (фикс. T). Изменения: `{"launch_tdb": {"requested": "2028-09-01T00:00:00", "actual": "2028-06-03T00:00:00"}, "tof_days": {"requested": 600.0, "actual": 720.0}, "spacecraft": {"requested": {"thrust_N": 0.025, "exhaust_velocity_m_s": 20000.0, "dry_mass_kg": 90.0}, "actual": {"thrust_N": 0.05, "exhaust_velocity_m_s": 40000.0, "dry_mass_kg": 90.0}}}`. Топливо 23.514101 кг; невязки 5.06865 м / 1.20228e-06 м/с.

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `83f5783e95f8671257bc1360` / cold: partial, этап psi; α/β={"a_max": 0.03081479729077688, "alpha": 0.5, "beta": 1.0, "q": 0.04568159818327857, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "physical_thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.8, "last_result": "limit/point_0003"}.
- `86b93226de94efccb9a5d9f0` / release: failed, этап release; α/β=null; TimeoutError: Free-duration integration budget reached.
- `4c783c88bcb7a75866595146` / cold: partial, этап psi; α/β={"a_max": 0.128912019012213, "alpha": 0.3, "beta": 1.0, "q": 0.0953097580247491, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "physical_thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.05, "last_result": "limit/point_0002"}.
- `cf058b5e1d58861d2de6f272` / cold: partial, этап psi; α/β={"a_max": 0.0352145430937749, "alpha": 0.5, "beta": 0.8, "q": 0.052071011018791254, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.8, "last_result": "mass/point_0008"}.
- `3b41955c66e1cfc581ad2886` / cold: partial, этап psi; α/β={"a_max": 0.05504389533209501, "alpha": 0.13265625, "beta": 1.0, "q": 0.04080009167796498, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "fuel", "last_result": "fuel/point_0003"}.

## earth_saturn_flyby_2028

Исходно: Earth → Saturn, flyby, 2028-06-01T00:00:00, T=2200 суток.

Поиск: finished; геномов 8, узлов 5, физических конфигураций 0.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `da7121e0af34f280055e714b` / cold | 2028-06-01T00:00:00 | 2200.0000 | 25 / 20 | 0.5 | partial: departure |
| `390f81e72eb6b0be16f0ca2b` / cold | 2028-06-01T00:00:00 | 2200.0000 | 50 / 40 | 0.5 | partial: departure |
| `0865b5d13e41b689faeb1e75` / cold | 2028-03-03T00:00:00 | 1760.0000 | 50 / 40 | 0.3 | initial_failed: irt |
| `6cf58f1399759825a7e07a21` / cold | 2028-03-03T00:00:00 | 2640.0000 | 50 / 40 | 0.5 | initial_failed: irt |
| `3f7858210329129ca0204b7d` / cold | 2028-06-01T00:00:00 | 2200.0000 | 25 / 20 | 0.7 | partial: departure |

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `da7121e0af34f280055e714b` / cold: partial, этап departure; α/β=null; {"status": "partial", "reached_parameter": 0.125, "last_result": "stage_departure/point_0003"}.
- `390f81e72eb6b0be16f0ca2b` / cold: partial, этап departure; α/β=null; {"status": "partial", "reached_parameter": 0.125, "last_result": "stage_departure/point_0003"}.
- `0865b5d13e41b689faeb1e75` / cold: initial_failed, этап irt; α/β=null; {"status": "initial_failed"}.
- `6cf58f1399759825a7e07a21` / cold: initial_failed, этап irt; α/β=null; {"status": "initial_failed"}.
- `3f7858210329129ca0204b7d` / cold: partial, этап departure; α/β=null; {"status": "partial", "reached_parameter": 0.125, "last_result": "stage_departure/point_0003"}.

## earth_mars_2029

Исходно: Earth → Mars, rendezvous, 2029-09-01T00:00:00, T=300 суток.

Поиск: finished; геномов 8, узлов 7, физических конфигураций 0.

Фактически испытанные узлы (все даты TDB):

| Узел / операция | Дата старта | Заданное T | F, мН / c, км/с | α | Исход |
|---|---|---:|---|---:|---|
| `6e49058a4786760a2d7b7753` / cold | 2029-09-01T00:00:00 | 300.0000 | 25 / 20 | 0.5 | partial: psi |
| `90d4a060afe6b507784d0d16` / cold | 2029-09-01T00:00:00 | 300.0000 | 50 / 40 | 0.5 | partial: psi |
| `d9fcb2149109cb9a89376fcb` / cold | 2029-06-03T00:00:00 | 240.0000 | 50 / 40 | 0.3 | partial: psi |
| `950d42895f6c99f7d7898eea` / cold | 2029-06-03T00:00:00 | 360.0000 | 50 / 40 | 0.5 | partial: psi |
| `b1db1174b7891ca6de8e0d14` / cold | 2029-06-03T00:00:00 | 360.0000 | 25 / 20 | 0.5 | partial: psi |
| `e350fa006be0b9a15c6c66ca` / cold | 2029-09-01T00:00:00 | 360.0000 | 25 / 20 | 0.5 | partial: psi |
| `51996503e9d78ea8faedda5d` / cold | 2029-09-01T00:00:00 | 360.0000 | 50 / 40 | 0.7 | partial: psi |

Неудавшиеся узлы (полные ошибки и входные параметры — в verified_results.json и графе):

- `6e49058a4786760a2d7b7753` / cold: partial, этап psi; α/β={"a_max": 0.41434554590712563, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.6142212388866224, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `90d4a060afe6b507784d0d16` / cold: partial, этап psi; α/β={"a_max": 0.411856548408551, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.30526578830869233, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `d9fcb2149109cb9a89376fcb` / cold: partial, этап psi; α/β={"a_max": 0.4189260012682512, "alpha": 0.3, "beta": 0.9750000000000001, "q": 0.30973414942198324, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `950d42895f6c99f7d7898eea` / cold: partial, этап psi; α/β={"a_max": 0.16904386452873965, "alpha": 0.5, "beta": 1.0, "q": 0.12498306965025856, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "physical_thrust_limit", "hardware_limit_reached": false, "reached_parameter": 0.08750000000000001, "last_result": "limit/point_0004"}.
- `b1db1174b7891ca6de8e0d14` / cold: partial, этап psi; α/β={"a_max": 0.1791557310832063, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.2649186148061414, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `e350fa006be0b9a15c6c66ca` / cold: partial, этап psi; α/β={"a_max": 0.288140113911649, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.4271357071119946, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.
- `51996503e9d78ea8faedda5d` / cold: partial, этап psi; α/β={"a_max": 0.2891478970228258, "alpha": 0.7, "beta": 0.9750000000000001, "q": 0.21431481680586262, "variable_mass": true, "gravity_spec": null}; {"status": "partial", "phase": "mass", "reached_beta": 0.9750000000000001, "last_result": "mass/point_0007"}.

## Границы вывода

Проверен межпланетный участок в центральном поле Солнца с постоянными F/c. Локальные раскрутка/скрутка, импульсы на парковочных орбитах и УММП не входят в этот граф версии 1. Отказы свободного времени не отменяют принятые фиксированные решения. «Не найдено» относится к объявленному пространству и бюджету, не к физической недостижимости. Подробные входы каждого узла и неудавшиеся улучшения сохранены.
