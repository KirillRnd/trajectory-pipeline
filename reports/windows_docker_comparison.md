# Сравнение двух общих проходов

Первый: `/workspace/data/benchmarks/physical_matrix_common_v1`. Второй: `/workspace/data/benchmarks/physical_matrix_docker_v1`.

Все 15 объектов миссий и настроек совпадают. Канонический SHA256 JSON: `3c237d9680d448c924bca5a8394988e1789a30e33eb5751a1f36e314eaa4605d`. Различия CRLF/LF не влияют на это сравнение.

| Случай | Первый: статус / этап | Второй: статус / этап | Δ расхода второго, кг |
|---|---|---|---:|
| earth_venus_2032 | completed / final | completed / final | +0.00000000 |
| earth_mars_2028 | completed / final | completed / final | +0.00000000 |
| earth_apophis_2029 | completed / final | completed / final | +0.00000000 |
| earth_eros_2029 | partial / psi | partial / psi | — |
| earth_bennu_2029 | completed / final | completed / final | +0.00000000 |
| earth_ryugu_2028 | completed / final | completed / final | -0.00000000 |
| earth_polyhymnia_2029 | partial / psi | partial / psi | — |
| earth_ceres_2030 | partial / psi | partial / psi | — |
| earth_mercury_2029 | partial / psi | partial / psi | — |
| earth_jupiter_2028 | partial / psi | partial / psi | — |
| venus_earth_2029 | failed / psi | failed / psi | — |
| earth_mars_flyby_2028 | completed / final | completed / final | +0.00000000 |
| earth_2015re36_2028 | partial / psi | failed / pazov | — |
| earth_saturn_flyby_2028 | partial / departure | partial / departure | — |
| earth_mars_2029 | partial / psi | partial / psi | — |

## Среда и область вывода

Первый итог: `{'completed': 6, 'partial': 8, 'failed': 1}`. Второй: `{'completed': 6, 'partial': 7, 'failed': 2}`.

Сравнение сохраняет разные окружения и реальные ошибки. Само изменение статуса не доказывает причину: численные бюджеты зависят также от скорости среды. Ошибку процесса нельзя приравнивать к физической недостижимости.

Окружение 1: отдельный environment.json не был записан; смотреть исходные ИРТ-сводки и журнал выполнения.

Окружение 2: `{"python": "3.12.16", "executable": "/usr/local/bin/python", "system": "Linux", "machine": "x86_64", "libc": ["glibc", "2.41"], "kernel": "6.6.87.2-microsoft-standard-WSL2", "container": true, "runtime": "docker-linux", "image_id": "sha256:17c8bdce3cd3c235b7a7245aa1315c0a764e7ad2beacfa26698fb17c41e75a2a", "dependencies": {"numpy": "2.2.5", "scipy": "1.15.1", "matplotlib": "3.10.0", "pandas": "2.2.3", "kiam-astro": "6.1.6", "daceypy": "1.4.0", "pillow": "13.0.0"}, "thread_limits": {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}}`.
