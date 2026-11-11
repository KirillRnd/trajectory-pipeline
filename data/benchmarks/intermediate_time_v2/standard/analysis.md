# Освобождение длительности на промежуточных моделях: пять прежних отказов

Завершено 5 из 5 поисков. Принята физическая ПСИ для 0 постановок, исходные условия сохранены для 0. Промежуточные модели не считаются решениями.

Код 69460613; Docker Linux, неизменённый KIAM 6.1.6. Общий дизайн search_graph_intermediate_v2.json: 2 поколения × 4 особи, seed=17; даты 0/±90 суток; начальные длительности 0,8/1/1,2; пределы свободного времени 0,5–1,5 от исходной длительности. Двигатели 25 мН / 20 км/с и 50 мН / 40 км/с, массы 156/90 кг, избыток до 3 км/с, допуски 1000 м / 0,01 м/с. Эти физические диапазоны совпадают с предыдущей широкой серией.

Для каждой особи используется новый маршрут intermediate: холодный расчёт → при наличии проверенной промежуточной модели освобождение T → совместное продолжение beta и предела тяги к физическим значениям → alpha=1 и точная ПСИ. Разрешено до двух циклов. Внутри отдельного продолжения выбранная длительность фиксирована; новое освобождение выполняется отдельным ребром от следующей проверенной промежуточной точки, а не как совместная свободная переменная на каждом шаге гомотопии. Далее пробуется свободное время физической ПСИ; неудача улучшения не удаляет принятое решение. Промежуточный оптимизатор меняет непрерывную длительность и на каждой пробе заново корректирует сопряжённые при обновлённой цели. Его критерий — функционал текущей модели, не физический расход. Для продолжения выбирается лучший проверенный изменённый вариант; его функционал может оказаться хуже исходного. Успех завершения скалярного оптимизатора не означает ни улучшения исходной опоры, ни доказанного минимума.

Единые бюджеты: поиск 4800 с, холодный узел 240 с, освобождение промежуточного времени 120 с, продолжение 240 с, финальное освобождение 90 с; пять отдельных процессов. Внутренние бюджеты стадий сохранены из предыдущей матрицы. Два поколения не исчерпывают пространство. Бюджет всей серии больше предыдущего из-за дополнительных рёбер; это не сравнение при равных вычислительных затратах. Отдельные случаи не перенастраивались.

| Постановка | Физическая ПСИ | Изменения выбранного варианта | Маршрут / остановки |
|---|---|---|---|
| earth_eros_2029 | Не найдена в бюджете | — | psi: 6, mass_and_thrust: 12 |
| earth_mercury_2029 | Не найдена в бюджете | — | psi: 6, mass_and_thrust: 12 |
| venus_earth_2029 | Не найдена в бюджете | — | psi: 6, mass_and_thrust: 12 |
| earth_saturn_flyby_2028 | Не найдена в бюджете | — | departure: 3, mass_and_thrust: 5, irt: 2, intermediate_release: 1 |
| earth_mars_2029 | Не найдена в бюджете | — | psi: 6, mass_and_thrust: 12 |

## earth_eros_2029

Исходно: 2029-03-01T00:00:00, T=400 суток, rendezvous. Поиск: finished, 8 геномов / 30 узлов.

Проверенных освобождений на промежуточных моделях: 12. Принятых физических конфигураций: 0.

| Промежуточный узел | T до → после, сутки | alpha / beta / модельная тяга, мН | J до → после | Оптимизатор завершён |
|---|---:|---|---|---|
| `cb9c56096d70c60c9bf7e3a6` | 400.000000 → 447.195679 | 0.5 / 0.8 / 81.7439 | 0.211509 → 0.195271 | True |
| `ca9d49a5b7cf939d84cd2763` | 447.195679 → 467.356225 | 0.5 / 0.9 / 53.372 | 0.213961 → 0.203843 | True |
| `a2655e52153db2c374ce071f` | 400.000000 → 447.195679 | 0.5 / 1 / 66.0035 | 0.248422 → 0.224966 | True |
| `97ad8a3571dc1e91e6d5736f` | 447.195679 → 505.544806 | 0.5 / 1 / 59.202 | 0.247897 → 0.20978 | True |
| `5f756f9da74c77eba573205a` | 320.000000 → 447.187483 | 0.3 / 0.975 / 504.294 | 0.444586 → 0.269738 | True |
| `0a4d487164ed8f6e81d36f7c` | 447.187483 → 600.000000 | 0.3 / 0.99625 / 118.144 | 0.31983 → 0.138962 | True |
| `b66ba8b71ca5cd054ac030fc` | 480.000000 → 600.000000 | 0.5 / 0.975 / 173.001 | 0.370767 → 0.202076 | True |
| `c188418eebaf3f61a8640c2f` | 600.000000 → 599.973890 | 0.5 / 0.9975 / 62.3001 | 0.304741 → 0.304806 | True |
| `286d1ab6c62c58ad88949890` | 320.000000 → 599.973890 | 0.3 / 0.936719 / 505.336 | 0.257095 → 0.113101 | True |
| `9c263deb36f3dcabca7109e5` | 599.973890 → 600.000000 | 0.3 / 0.996045 / 55.021 | 0.135032 → 0.135017 | True |
| `052a43270d828b5ece58b89e` | 320.000000 → 599.973890 | 0.5 / 0.975 / 534.322 | 0.663284 → 0.319406 | True |
| `360a08e71e80c19c437a2f75` | 599.973890 → 600.000000 | 0.5 / 0.9975 / 98.4322 | 0.401325 → 0.40129 | True |

Остановившиеся попытки (полные ошибки в verified_results.json и исходном графе):

- `d7bc2497e9f5f697132f7ae2`, cold: partial/psi; модель `{"a_max": 0.08674051192651461, "alpha": 0.5, "beta": 0.8, "q": 0.1297768139255286, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `fd4a5cca30abeb16e01a5e92`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.05663431842918878, "alpha": 0.5, "beta": 0.9, "q": 0.08473343356343845, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `6989568273b5b372bc9254fc`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.054000026498172767, "alpha": 0.5, "beta": 0.9087500000000001, "q": 0.08079213778175556, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `c93b8891d06eadd7fd0c78a5`, cold: partial/psi; модель `{"a_max": 0.07003793846991459, "alpha": 0.5, "beta": 1.0, "q": 0.05239362961241259, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `1435567fbee451fc7e4d9032`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.0628207208122844, "alpha": 0.5, "beta": 1.0, "q": 0.04699460963771028, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `3953b3132165757779958d7b`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.054032696958581754, "alpha": 0.5, "beta": 1.0, "q": 0.04042050884498452, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `e7be2208e830779001b7e827`, cold: partial/psi; модель `{"a_max": 0.530021428721014, "alpha": 0.3, "beta": 0.9750000000000001, "q": 0.3974457343911698, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `648ec268e8efa3d45c4ae550`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.12417140414786976, "alpha": 0.3, "beta": 0.99625, "q": 0.09311207479105492, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `7071680ebd3c500d1c3ea052`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.06195101435117822, "alpha": 0.3, "beta": 0.9995078125, "q": 0.04645503947736089, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `734f800503c056606bc2beac`, cold: partial/psi; модель `{"a_max": 0.18182637830881915, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.1363456542370739, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `a42e93a955eba6148bdb6237`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.06547836824940656, "alpha": 0.5, "beta": 0.9975, "q": 0.049100086799168045, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `1f9516af61537f975444b9e1`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.061600101247426146, "alpha": 0.5, "beta": 0.9982500000000001, "q": 0.04619190121790452, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `7c823701d752108c157aecc5`, cold: partial/psi; модель `{"a_max": 0.5311165399327844, "alpha": 0.3, "beta": 0.93671875, "q": 0.7965338449438181, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `977d4cefbf7924a64cbbba29`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.05782797667211398, "alpha": 0.3, "beta": 0.996044921875, "q": 0.0867266167417602, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `707681eaea2a333469a84d7c`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.045995762590597206, "alpha": 0.3, "beta": 0.997528076171875, "q": 0.06898143603670873, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `6c00f80b7bdc061c60504310`, cold: partial/psi; модель `{"a_max": 0.5669822811160536, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.4241452601629028, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `af8d95b0347a2d843ada79c7`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.10444885298895867, "alpha": 0.5, "beta": 0.9975, "q": 0.07813557389750378, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `6042b17e3d6c4eea48702d7d`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.08565843247129544, "alpha": 0.5, "beta": 0.9984140625000001, "q": 0.06407893039297194, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения

## earth_mercury_2029

Исходно: 2029-01-01T00:00:00, T=300 суток, rendezvous. Поиск: finished, 8 геномов / 30 узлов.

Проверенных освобождений на промежуточных моделях: 12. Принятых физических конфигураций: 0.

| Промежуточный узел | T до → после, сутки | alpha / beta / модельная тяга, мН | J до → после | Оптимизатор завершён |
|---|---:|---|---|---|
| `95fbad0d81de21aa63a5ca8e` | 300.000000 → 299.983329 | 0.5 / 0.3 / 153.783 | 0.353939 → 0.353939 | True |
| `ad080e21d188d260090fda11` | 299.983329 → 304.009816 | 0.5 / 0.36125 / 142.514 | 0.382986 → 0.380249 | False |
| `d98f9dbca15ef6b1faae1a19` | 300.000000 → 294.805244 | 0.5 / 1 / 123.554 | 0.291214 → 0.291203 | False |
| `3d7d3ad4a93f26a73bb4215c` | 294.805244 → 289.057647 | 0.5 / 1 / 121.715 | 0.296026 → 0.296011 | False |
| `61194fd98efcf03776543a1e` | 240.000000 → 150.000000 | 0.3 / 0.975 / 493.952 | 0.275448 → 0.187458 | True |
| `7317153a38d71293646f9476` | 150.000000 → 160.300467 | 0.3 / 0.988438 / 255.328 | 0.257039 → 0.184462 | True |
| `8d9d437e7ecbbcdf768f12f8` | 360.000000 → 360.891347 | 0.5 / 0.8875 / 109.145 | 0.253313 → 0.253248 | False |
| `b8786845c05f5021f7c4eefa` | 360.891347 → 363.013332 | 0.5 / 0.938125 / 82.5295 | 0.282859 → 0.282663 | True |
| `2f2b75c6dc533c6cdfe9f011` | 240.000000 → 264.564469 | 0.3 / 0.975 / 494.769 | 0.18249 → 0.14495 | True |
| `66a41bf53c391fbb714aaff7` | 264.564469 → 269.730747 | 0.3 / 0.995625 / 107.21 | 0.169313 → 0.161302 | True |
| `c5a29f0218861e8d27b7ceac` | 240.000000 → 245.280156 | 0.5 / 1 / 132.242 | 0.296661 → 0.283947 | False |
| `6a2c0d6638e7246ad8a48100` | 245.280156 → 244.174588 | 0.5 / 1 / 130.186 | 0.29189 → 0.294971 | False |

Остановившиеся попытки (полные ошибки в verified_results.json и исходном графе):

- `f9d03d8b6f1827043f0bb214`, cold: partial/psi; модель `{"a_max": 0.16072939226301447, "alpha": 0.5, "beta": 0.3, "q": 0.24138762376208234, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `7dd04534221ff47fc2dbae02`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.14895188681592275, "alpha": 0.5, "beta": 0.36124999999999996, "q": 0.22369985667921854, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `b1b3787816ba0a9c021aa1c6`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.14588132289578812, "alpha": 0.5, "beta": 0.37721874999999994, "q": 0.21908840311832906, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `f5def431bf6602e583f0edcb`, cold: partial/psi; модель `{"a_max": 0.12913513534743598, "alpha": 0.5, "beta": 1.0, "q": 0.09696926936270565, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `a29da085106dec9f71c50175`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.12721322346427696, "alpha": 0.5, "beta": 1.0, "q": 0.09552608048472898, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `eeb6f662866b255260b618f4`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.12721322346427696, "alpha": 0.5, "beta": 1.0, "q": 0.09552608048472898, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `6d9cbdf7b96b1aafa03a3c3e`, cold: partial/psi; модель `{"a_max": 0.5345413363771343, "alpha": 0.3, "beta": 0.9750000000000001, "q": 0.3979182640737732, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `37fd0be5825251cbec37729e`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.2763087716881669, "alpha": 0.3, "beta": 0.9884375000000001, "q": 0.20568719254471315, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `548f399bc8e55fd0dbcd4f7d`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.22075874323763323, "alpha": 0.3, "beta": 0.9913281250000001, "q": 0.16433515971578744, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `a2c8dba2b581b60fef217681`, cold: partial/psi; модель `{"a_max": 0.11811336168654435, "alpha": 0.5, "beta": 0.8875000000000001, "q": 0.08792484443722788, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `f6250bd540634405265d9891`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.08931124497631387, "alpha": 0.5, "beta": 0.938125, "q": 0.06648424199352998, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `a29b1dcc34ab860aea02430d`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.08843118029905683, "alpha": 0.5, "beta": 0.9396718749999999, "q": 0.06582911247441699, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `cbabee4d5a1654324c0fac61`, cold: partial/psi; модель `{"a_max": 0.5354257592364966, "alpha": 0.3, "beta": 0.9750000000000001, "q": 0.7971532757401265, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `5f2565f11351b1b08901a1b7`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.11601932924437514, "alpha": 0.3, "beta": 0.995625, "q": 0.1727320487684556, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `f49e019f4ba371753143091d`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.10712282921423923, "alpha": 0.3, "beta": 0.9960625, "q": 0.15948675001451107, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `701fdb21827af4c4f00a8d89`, cold: partial/psi; модель `{"a_max": 0.1382156884461351, "alpha": 0.5, "beta": 1.0, "q": 0.10378797596041853, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `d3b664ff0bf5b1d179ac4eb5`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.1360667627355086, "alpha": 0.5, "beta": 1.0, "q": 0.10217431941749903, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `6060f282f7713a0bad0b6288`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.1360667627355086, "alpha": 0.5, "beta": 1.0, "q": 0.10217431941749903, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения

## venus_earth_2029

Исходно: 2029-01-01T00:00:00, T=250 суток, rendezvous. Поиск: finished, 8 геномов / 30 узлов.

Проверенных освобождений на промежуточных моделях: 12. Принятых физических конфигураций: 0.

| Промежуточный узел | T до → после, сутки | alpha / beta / модельная тяга, мН | J до → после | Оптимизатор завершён |
|---|---:|---|---|---|
| `8bd3f2081cd9782424fea1dd` | 250.000000 → 374.973405 | 0.5 / 0.936719 / 645.343 | 0.329585 → 0.216375 | True |
| `2292c5e5a3219659481aa3b6` | 374.973405 → 375.000000 | 0.5 / 0.988926 / 133.56 | 0.241104 → 0.241078 | True |
| `064e6842ffcd3bffc3b8950d` | 250.000000 → 374.973405 | 0.5 / 0.975 / 646.446 | 0.51579 → 0.26621 | True |
| `5bcfa7eb823bee480945c3a9` | 374.973405 → 375.000000 | 0.5 / 0.995625 / 154.378 | 0.363663 → 0.363586 | True |
| `81ba9c6f8dd0dde21792a269` | 200.000000 → 374.973405 | 0.3 / 0.975 / 631.755 | 0.31686 → 0.0890797 | True |
| `995457a78d8c63d2d7f41a08` | 374.973405 → 375.000000 | 0.3 / 0.998437 / 86.3597 | 0.154626 → 0.154543 | False |
| `1c110ca93344bd479724c1d4` | 300.000000 → 374.973405 | 0.5 / 0.975 / 234.54 | 0.282455 → 0.144529 | True |
| `227c3546562efd157d4a4f82` | 374.973405 → 375.000000 | 0.5 / 0.995 / 86.9081 | 0.247983 → 0.24785 | False |
| `d9bf3ef2d17bdc11c3fd7ea4` | 200.000000 → 279.481900 | 0.3 / 0.989063 / 631.32 | 0.188156 → 0.141274 | True |
| `84177e98030ea8c20b200557` | 279.481900 → 374.973405 | 0.3 / 0.998359 / 115.948 | 0.164104 → 0.0905213 | True |
| `4bf187bae2ccf268ef4e5ee9` | 200.000000 → 374.790120 | 0.5 / 0.975 / 631.755 | 0.455319 → 0.135286 | True |
| `69c0c3478b77a14a84aed2b0` | 374.790120 → 375.000000 | 0.5 / 0.9975 / 108.175 | 0.193961 → 0.193505 | True |

Остановившиеся попытки (полные ошибки в verified_results.json и исходном графе):

- `25efd64aedf6daa81a444886`, cold: partial/psi; модель `{"a_max": 0.3659468013766871, "alpha": 0.5, "beta": 0.9367187500000003, "q": 0.6403653870221859, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `19a4f944a0fc30622d6dd23e`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.07573626136876332, "alpha": 0.5, "beta": 0.9889257812500001, "q": 0.13252986538089523, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `a4d20651113d39f109cf3f57`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.05284370646094132, "alpha": 0.5, "beta": 0.9930440063476563, "q": 0.09247049137263814, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `8b12ceb5f13e2a7abc4a17bc`, cold: partial/psi; модель `{"a_max": 0.3665722364289253, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.3207299137050898, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `08b4017d3003a9499fef8f22`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.08754128363074809, "alpha": 0.5, "beta": 0.995625, "q": 0.07659365755040343, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `ef04532ac93737d236bedbf9`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.07570360684537089, "alpha": 0.5, "beta": 0.9964999999999999, "q": 0.06623636183475008, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `7b19a01faea16c645ec9e87f`, cold: partial/psi; модель `{"a_max": 0.3538061099531336, "alpha": 0.3, "beta": 0.9750000000000001, "q": 0.31052591903996907, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `b1b012486ffec86c366d0141`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.048364630810312115, "alpha": 0.3, "beta": 0.9984375, "q": 0.04244830998930564, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `dc4b253f19f2e27764596013`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.04785556167840741, "alpha": 0.3, "beta": 0.9984765624999999, "q": 0.0420015139742212, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `fad1de731b60e9e21e64c9b8`, cold: partial/psi; модель `{"a_max": 0.13135129818946653, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.11528343191354168, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `a5c0ea12ab687bbc57b75ce4`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.0486717520651925, "alpha": 0.5, "beta": 0.995, "q": 0.042717861891450784, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `e2d509433ecf02c5862a2393`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.047767444529458254, "alpha": 0.5, "beta": 0.99521875, "q": 0.04192417596933416, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `48c0e1598b49704c2055090f`, cold: partial/psi; модель `{"a_max": 0.3535627398417247, "alpha": 0.3, "beta": 0.9890625000000001, "q": 0.6206246395359551, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `c0742cfce7d4f094b0178842`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.06493520382826135, "alpha": 0.3, "beta": 0.998359375, "q": 0.11398369490843203, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `9d9177b3444b4118bdbc3c4b`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.039468068297661675, "alpha": 0.3, "beta": 0.9991796875000001, "q": 0.06928008214718005, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `b61683a4bc2bda1d00f18321`, cold: partial/psi; модель `{"a_max": 0.3538061099531336, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.31052591903996907, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `c4fcf99eb25750dfdd4d0a41`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.06058228997602494, "alpha": 0.5, "beta": 0.9975, "q": 0.053171414351332144, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `40fd89c076bbe40dbc9a89b6`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.04836463081031209, "alpha": 0.5, "beta": 0.9984375000000001, "q": 0.04244830998930562, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения

## earth_saturn_flyby_2028

Исходно: 2028-06-01T00:00:00, T=2200 суток, flyby. Поиск: finished, 8 геномов / 16 узлов.

Проверенных освобождений на промежуточных моделях: 5. Принятых физических конфигураций: 0.

| Промежуточный узел | T до → после, сутки | alpha / beta / модельная тяга, мН | J до → после | Оптимизатор завершён |
|---|---:|---|---|---|
| `a4047b0997292de1247a59dc` | 2200.000000 → 1812.730712 | ИРТ/избыток | 0.0195963 → 0.0223209 | True |
| `7d8883bfd3a8cab46fbf2dca` | 1812.730712 → 1737.501273 | 0 / 0.1 / 57.2123 | 0.0127232 → 0.013355 | False |
| `eafbb4a3a075575c90747f07` | 2200.000000 → 1812.730712 | ИРТ/избыток | 0.0195963 → 0.0223209 | True |
| `5938c63e278b1098d27421cc` | 1812.730712 → 2769.000000 | 0 / 0.4 / 56.9874 | 0.0121008 → 0.00874247 | False |
| `d4982981a42701672f7c0b0e` | 2200.000000 → 1812.730712 | ИРТ/избыток | 0.0195963 → 0.0223209 | True |

Остановившиеся попытки (полные ошибки в verified_results.json и исходном графе):

- `da7121e0af34f280055e714b`, cold: partial/departure; модель `null`. См. checkpoint продолжения
- `d37e3962a051e3ce13091b37`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.0635939370401794, "alpha": 0.0, "beta": 0.1, "q": 0.09404830852865514, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `eb2be4cd67933bf7a5acd8c1`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.06180366791084465, "alpha": 0.0, "beta": 0.14500000000000002, "q": 0.09140070104810834, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `390f81e72eb6b0be16f0ca2b`, cold: partial/departure; модель `null`. См. checkpoint продолжения
- `71fd402ee2d294f6c7cb0d0a`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.06334395326784426, "alpha": 0.0, "beta": 0.4, "q": 0.04683930526737934, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `b8e5e918c505df942f276fa2`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.06023721552349396, "alpha": 0.0, "beta": 0.64, "q": 0.044542046727515154, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `0865b5d13e41b689faeb1e75`, cold: initial_failed/irt; модель `null`. См. checkpoint продолжения
- `6cf58f1399759825a7e07a21`, cold: initial_failed/irt; модель `null`. См. checkpoint продолжения
- `3f7858210329129ca0204b7d`, cold: partial/departure; модель `null`. См. checkpoint продолжения
- `f335828637ab8098fa1bc313`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.062102046099067096, "alpha": 0.0, "beta": 0.1375, "q": 0.0918419689615328, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `646590d7327ce88e9b1d7579`, intermediate_release: failed/intermediate_release; модель `null`. RuntimeError: No independently verified changed-duration intermediate; see trials.json

## earth_mars_2029

Исходно: 2029-09-01T00:00:00, T=300 суток, rendezvous. Поиск: finished, 8 геномов / 30 узлов.

Проверенных освобождений на промежуточных моделях: 12. Принятых физических конфигураций: 0.

| Промежуточный узел | T до → после, сутки | alpha / beta / модельная тяга, мН | J до → после | Оптимизатор завершён |
|---|---:|---|---|---|
| `e2337dfae82d91298a7bc6e5` | 300.000000 → 449.967911 | 0.5 / 0.975 / 376.309 | 0.345626 → 0.246852 | True |
| `6b8e3d4fb089131b87d88cc2` | 449.967911 → 443.614129 | 0.5 / 0.996563 / 73.3049 | 0.303595 → 0.308231 | False |
| `9f189c3d404499da8e969c67` | 300.000000 → 449.967911 | 0.5 / 0.975 / 374.048 | 0.528903 → 0.312742 | True |
| `cc05414c9d5519ca97e2fb2e` | 449.967911 → 450.000000 | 0.5 / 0.995625 / 106.708 | 0.435617 → 0.435532 | True |
| `dd3faf191e6df5f4c17cfec7` | 240.000000 → 449.967911 | 0.3 / 0.975 / 376.701 | 0.33848 → 0.116287 | True |
| `09f8b43970d5c774f32848e3` | 449.967911 → 450.000000 | 0.3 / 0.998437 / 70.4188 | 0.167106 → 0.167044 | True |
| `e5695540a48549ad978a843b` | 360.000000 → 450.000000 | 0.5 / 1 / 152.006 | 0.308868 → 0.181811 | True |
| `632278d02091164883cdb6f8` | 450.000000 → 449.967911 | 0.5 / 1 / 67.851 | 0.281555 → 0.281682 | True |
| `9e53ca5c9e0c0f7416706fcc` | 360.000000 → 450.000000 | 0.5 / 0.975 / 161.098 | 0.231762 → 0.156206 | True |
| `79ec0839dd45f14976925194` | 450.000000 → 449.967911 | 0.5 / 0.994375 / 55.6221 | 0.216651 → 0.216699 | True |
| `4c8a15ebe204fa1d8ce609aa` | 360.000000 → 449.967911 | 0.7 / 1 / 152.006 | 0.413641 → 0.244567 | True |
| `33fa4890abc419ae299fa6e8` | 449.967911 → 450.000000 | 0.7 / 1 / 67.851 | 0.38616 → 0.385975 | True |

Остановившиеся попытки (полные ошибки в verified_results.json и исходном графе):

- `6e49058a4786760a2d7b7753`, cold: partial/psi; модель `{"a_max": 0.41434554590712563, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.6142212388866224, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `71a0a509d4b22225d2f15a49`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.08071452595160866, "alpha": 0.5, "beta": 0.9965625, "q": 0.11965031750879723, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `819b908390bd0b452621cfa7`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.07938483710395987, "alpha": 0.5, "beta": 0.9966484375, "q": 0.11767920151779868, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `90d4a060afe6b507784d0d16`, cold: partial/psi; модель `{"a_max": 0.411856548408551, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.30526578830869233, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `496d28fbdedf4bddcfb447d3`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.11749439984682991, "alpha": 0.5, "beta": 0.995625, "q": 0.08708619719582576, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `417c4e609e5f890c621b0edb`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.11320161851363815, "alpha": 0.5, "beta": 0.99592578125, "q": 0.08390441149209646, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `d9fcb2149109cb9a89376fcb`, cold: partial/psi; модель `{"a_max": 0.4189260012682512, "alpha": 0.3, "beta": 0.9750000000000001, "q": 0.30973414942198324, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `53aa101bb6f08b9a38bfbe5a`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.07831209832160302, "alpha": 0.3, "beta": 0.9984375, "q": 0.057900276157747045, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `357b91507a6472442429a2f8`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.07433826945389213, "alpha": 0.3, "beta": 0.9987109375, "q": 0.05496221430299763, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `950d42895f6c99f7d7898eea`, cold: partial/psi; модель `{"a_max": 0.16904386452873965, "alpha": 0.5, "beta": 1.0, "q": 0.12498306965025856, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `1b01581c631ead02933b1c7a`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.07545639274578629, "alpha": 0.5, "beta": 1.0, "q": 0.055788901989403575, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `2dbfafab2b72bd101d46e229`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.07427768689851993, "alpha": 0.5, "beta": 1.0, "q": 0.05491742241564471, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `b1db1174b7891ca6de8e0d14`, cold: partial/psi; модель `{"a_max": 0.1791557310832063, "alpha": 0.5, "beta": 0.9750000000000001, "q": 0.2649186148061414, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `d8828d2566bf92714c62ccf4`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.06185678510055416, "alpha": 0.5, "beta": 0.994375, "q": 0.09146798556831688, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `21cf198f3d494bca64ef1302`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.05887701348889808, "alpha": 0.5, "beta": 0.9948671875, "q": 0.08706178006751732, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `69ad87d28e68be286e003b88`, cold: partial/psi; модель `{"a_max": 0.16904386452873965, "alpha": 0.7, "beta": 1.0, "q": 0.12498306965025856, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `014f503d4e218c6c1c3f3284`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.07545639274578629, "alpha": 0.7, "beta": 1.0, "q": 0.055788901989403575, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения
- `a29c79a219faf5c63190f8a6`, physical_continue: partial/mass_and_thrust; модель `{"a_max": 0.07427768689851993, "alpha": 0.7, "beta": 1.0, "q": 0.05491742241564471, "variable_mass": true, "gravity_spec": null}`. См. checkpoint продолжения

## Область вывода

Проверен только межпланетный участок центральной модели с постоянными F/c. Массы и физические ограничения не ослаблялись. Физическая недостижимость не доказывается. Пара 50 мН / 40 км/с — математический вариант, без подтверждения массы и мощности реальной энергосистемы. Промежуточные узлы и незавершённая оптимизация не являются физическими решениями или доказательством минимума.
