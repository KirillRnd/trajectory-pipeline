# 79 ИРТ Апофиса → полные эфемериды → ПСИ

Пересогласовано **79/79**, принято физических ПСИ **50/79**. У 22 принятых ПСИ изменилась длительность.

Минимальный наблюдённый расход 25.64612 кг при старте 2029-08-24 и длительности 409.407 суток.

Расчёты межпланетного участка выполнены в Linux Docker. Движение аппарата считалось в центральном поле Солнца. Полные эфемериды задают обе границы в положении и скорости. Даты старта зафиксированы. Горизонт перелёта 1095,75 суток, избыток до 3 км/с. Земная граница взята из KIAM/JPLEPH, граница Апофиса — из номинальных векторов Horizons JPL#220 на дату прибытия. После встречи 13.04.2029 эта таблица задаёт прогноз по довстречным наблюдениям. Рассеяние орбиты в серии не оценивалось.

Физическая приёмка требует точных дуг, α=β=1, 204 кг на старте, сухую массу 140 кг, расход не более 64 кг ксенона, тягу 36 мН и скорость истечения 11767,98 м/с. У принятых ПСИ повторены независимое интегрирование, KIAM и аудит исходного запроса с полными эфемеридами и принятой длительностью. Для гладкого продолжения резерв сухой массы мог временно нарушаться при положительной массе.

Основной путь использует добавочный импульс, Пазов и последовательное введение массы, тяги и топливного функционала. После отказов проверены совместное продолжение и освобождение длительности на разных моделях. Оставшиеся случаи направлены на коррекцию точных дуг, независимый R-перенос при наличии совместимой опоры и раннее освобождение времени в диапазоне 1–1095,75 суток. Несходимость в этих бюджетах не доказывает физическую недостижимость.

Основные бюджеты продолжения составляют 45–90 секунд на этап. Внешние лимиты операций составляют 35–480 секунд. Бюджеты и фактические причины остановок записаны в диагностике.

Первоначальный физический запуск прерван после расхождений границ в дочерних процессах. Повтор выполнен со свежими процессами Linux. Результаты первого запуска использованы только после повторной приёмки. Диагностика первой попытки сохранена.

| Дата старта TDB | Исходная ИРТ, сут | ПСИ, сут | Ксенон, кг | Результат |
|---|---:|---:|---:|---|
| 2027-11-12 | 1065.812 | 592.725 | 34.38005 | independent R transfer, changed duration |
| 2027-11-19 | 1016.422 | — | — | departure, irt, pazov_limit, psi, psi_limit. broad_early_time: No independently verified changed-duration intermediate; see trials.json |
| 2027-11-26 | 971.082 | — | — | departure, irt. broad_early_time: No independently verified changed-duration intermediate; see trials.json |
| 2027-12-03 | 929.817 | 556.965 | 39.80262 | independent R transfer + free duration |
| 2027-12-10 | 892.648 | — | — | departure, irt, pazov, psi, psi_mass. broad_early_time: partial |
| 2027-12-17 | 859.604 | — | — | departure, irt, pazov, psi, psi_limit, psi_mass. broad_early_time: partial |
| 2027-12-24 | 830.727 | — | — | departure, irt, pazov_limit, psi_mass. broad_early_time: partial |
| 2027-12-31 | 806.076 | — | — | departure, irt, pazov, pazov_limit, psi_mass. broad_early_time: partial |
| 2028-01-07 | 785.715 | — | — | departure, irt, pazov_limit, psi_limit, psi_mass. broad_early_time: partial |
| 2028-01-14 | 769.584 | — | — | departure, irt, pazov, pazov_limit, psi_limit, psi_mass. broad_early_time: partial |
| 2028-01-21 | 749.621 | — | — | departure, irt, pazov, pazov_limit, psi_limit, psi_mass. broad_early_time: partial |
| 2028-01-28 | 754.056 | — | — | departure, irt, pazov, pazov_limit, psi_limit, psi_mass. broad_early_time: partial |
| 2028-02-04 | 752.576 | — | — | departure, irt, pazov, pazov_limit, psi_limit, psi_mass. broad_early_time: partial |
| 2028-02-11 | 756.779 | — | — | departure, irt, pazov, pazov_limit, psi_limit, psi_mass. broad_early_time: partial |
| 2028-02-18 | 766.710 | — | — | departure, irt. broad_early_time: partial |
| 2028-02-25 | 782.568 | — | — | departure, irt. broad_early_time: partial |
| 2028-03-03 | 804.527 | — | — | departure, irt. broad_early_time: partial |
| 2028-03-10 | 832.673 | — | — | departure, irt, pazov, psi_limit, psi_mass. broad_early_time: partial |
| 2028-03-17 | 866.950 | — | — | departure, irt, pazov, psi_mass. broad_early_time: No independently verified changed-duration intermediate; see trials.json |
| 2028-03-24 | 907.110 | — | — | departure, irt, pazov, psi, psi_mass. broad_early_time: No independently verified changed-duration intermediate; see trials.json |
| 2028-03-31 | 952.670 | — | — | departure, irt, pazov, psi. broad_early_time: No independently verified changed-duration intermediate; see trials.json |
| 2028-04-07 | 1002.883 | — | — | departure, irt, pazov, pazov_limit, psi, psi_limit. broad_early_time: partial |
| 2028-04-14 | 1056.730 | — | — | departure, irt, pazov, psi_limit, psi_mass. broad_early_time: No independently verified changed-duration intermediate; see trials.json |
| 2028-09-15 | 1037.108 | — | — | departure, irt, pazov, pazov_limit, psi, psi_mass. broad_early_time: partial |
| 2028-09-22 | 977.786 | — | — | departure, irt, pazov, psi. broad_early_time: No independently verified changed-duration intermediate; see trials.json |
| 2028-09-29 | 918.790 | — | — | departure, irt, pazov, psi_limit, psi_mass. broad_early_time: partial |
| 2028-10-06 | 860.616 | — | — | departure, irt, pazov, psi_limit, psi_mass. broad_early_time: partial |
| 2028-10-13 | 803.658 | — | — | departure, irt, pazov, psi, psi_mass. broad_early_time: partial |
| 2028-10-20 | 748.215 | 592.725 | 30.58421 | independent R transfer, changed duration |
| 2028-10-27 | 694.496 | 592.725 | 30.38803 | independent R transfer, changed duration |
| 2028-11-03 | 642.640 | 642.640 | 30.10734 | exact physical arcs in cartesian costate coordinates |
| 2028-11-10 | 592.725 | 592.725 | 32.74377 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2028-11-17 | 544.776 | 544.776 | 35.31235 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2028-11-24 | 498.779 | 498.779 | 37.98051 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2028-12-01 | 454.694 | 454.694 | 40.50951 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2028-12-08 | 412.458 | 412.458 | 42.07928 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2028-12-15 | 371.999 | 371.999 | 43.61504 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2028-12-22 | 333.237 | 333.237 | 45.15951 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2028-12-29 | 296.102 | 296.102 | 46.66870 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-01-05 | 260.485 | 260.485 | 47.83104 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-01-12 | 226.377 | 226.377 | 49.57819 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-01-19 | 193.783 | 387.566 | 47.26965 | early duration -> Pazov(.3) -> coupled mass/thrust -> fuel |
| 2029-01-26 | 162.724 | 325.448 | 45.92645 | early duration -> Pazov(.3) -> coupled mass/thrust -> fuel |
| 2029-02-02 | 133.276 | 266.553 | 45.56607 | early duration -> Pazov(.3) -> coupled mass/thrust -> fuel |
| 2029-02-09 | 105.601 | 266.553 | 43.28248 | independent R transfer, changed duration |
| 2029-02-16 | 80.026 | 266.553 | 40.35335 | independent R transfer, changed duration |
| 2029-02-23 | 57.331 | 266.553 | 36.89855 | independent R transfer, changed duration |
| 2029-03-02 | 40.175 | 266.553 | 34.08174 | independent R transfer, changed duration |
| 2029-03-09 | 48.274 | 266.553 | 32.46926 | independent R transfer, changed duration |
| 2029-05-11 | 36.522 | 419.131 | 26.59573 | broad early duration -> coupled physical continuation |
| 2029-05-18 | 52.627 | — | — | departure, irt, pazov, pazov_limit, psi_limit, psi_mass. broad_early_time: partial |
| 2029-05-25 | 83.380 | 419.127 | 27.23768 | broad early duration -> coupled physical continuation |
| 2029-06-01 | 119.997 | 320.150 | 45.87559 | independent R transfer, changed duration |
| 2029-06-08 | 160.086 | 320.150 | 45.00079 | early duration -> Pazov(.3) -> coupled mass/thrust -> fuel |
| 2029-06-15 | 351.829 | 351.829 | 34.66614 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-06-22 | 330.548 | 330.548 | 38.84413 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-06-29 | 307.314 | 307.314 | 45.38892 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-07-06 | 320.547 | 320.547 | 40.81602 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-07-13 | 352.548 | 352.548 | 36.30311 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-07-20 | 378.808 | 378.808 | 34.16839 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-07-27 | 398.619 | 398.619 | 32.91490 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-08-03 | 411.615 | 411.615 | 31.38525 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-08-10 | 417.741 | 417.741 | 29.45799 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-08-17 | 417.138 | 417.138 | 27.18335 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-08-24 | 409.407 | 409.407 | 25.64612 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-08-31 | 401.474 | 401.474 | 25.71719 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-09-07 | 383.153 | 383.153 | 28.11062 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-09-14 | 361.799 | 361.799 | 33.13328 | exact physical arcs in cartesian costate coordinates |
| 2029-09-21 | 337.102 | 337.102 | 39.65632 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-09-28 | 309.587 | 309.587 | 48.39755 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |
| 2029-10-05 | 279.703 | 399.123 | 41.89284 | early duration -> Pazov(.3) -> coupled mass/thrust -> fuel |
| 2029-10-12 | 248.096 | 354.022 | 56.08507 | early duration -> Pazov(.3) -> coupled mass/thrust -> fuel |
| 2029-10-19 | 215.116 | 430.214 | 40.39257 | early duration -> Pazov(.3) -> coupled mass/thrust -> fuel |
| 2029-10-26 | 181.115 | 362.200 | 62.68062 | early duration -> Pazov(.3) -> coupled mass/thrust -> fuel |
| 2029-11-02 | 146.392 | — | — | departure, irt, pazov_limit, psi_limit. broad_early_time: partial |
| 2029-11-09 | 111.251 | — | — | departure, irt, pazov_limit, psi, psi_limit. broad_early_time: partial |
| 2029-11-16 | 76.254 | 386.501 | 60.97199 | independent R transfer, changed duration |
| 2029-11-23 | 44.304 | 386.501 | 62.22674 | independent R transfer, changed duration |
| 2029-11-30 | 386.501 | 386.501 | 63.12579 | standard: departure -> Pazov(.5) -> mass -> thrust -> fuel |

Параметры α/β, тяга, длительность, причины остановок, траектории и SHA256 сохранены по каждому случаю в архиве. Полные рабочие результаты лежат в runs/apophis_new_full_psi_v1.
