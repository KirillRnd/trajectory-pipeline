# Сравнение двух общих проходов

Первый: `/workspace/data/benchmarks/parameter_study_v1`. Второй: `/workspace/data/benchmarks/parameter_study_analytic_v1`.

Все 24 объектов миссий и настроек совпадают. Канонический SHA256 JSON: `9e622ff8d0bc7e8561a35407f7cd5a254d4ed62d5ad761b5f70e51f4aff3ad66`. Различия CRLF/LF не влияют на это сравнение.

| Случай | Первый: статус / этап | Второй: статус / этап | Δ расхода второго, кг |
|---|---|---|---:|
| earth_venus_2032__reference | completed / final | completed / final | -0.00000000 |
| earth_venus_2032__thrust_x2 | partial / psi | partial / psi | — |
| earth_venus_2032__exhaust_x2 | completed / final | completed / final | -0.00000000 |
| earth_venus_2032__mass_x2 | failed / psi | partial / psi | — |
| earth_venus_2032__launch_plus_90d | failed / psi | partial / psi | — |
| earth_venus_2032__duration_x1p2 | completed / final | completed / final | -0.00000000 |
| earth_mars_2028__reference | completed / final | completed / final | +0.00000000 |
| earth_mars_2028__thrust_x2 | completed / final | completed / final | +0.00000000 |
| earth_mars_2028__exhaust_x2 | completed / final | completed / final | +0.00000000 |
| earth_mars_2028__mass_x2 | partial / psi | partial / psi | — |
| earth_mars_2028__launch_plus_90d | completed / final | completed / final | -0.00000000 |
| earth_mars_2028__duration_x1p2 | completed / final | completed / final | -0.00000000 |
| earth_apophis_2029__reference | completed / final | completed / final | -0.00000000 |
| earth_apophis_2029__thrust_x2 | completed / final | completed / final | -0.00000000 |
| earth_apophis_2029__exhaust_x2 | completed / final | completed / final | -0.00000000 |
| earth_apophis_2029__mass_x2 | partial / psi | partial / psi | — |
| earth_apophis_2029__launch_plus_90d | completed / final | completed / final | +0.00000000 |
| earth_apophis_2029__duration_x1p2 | completed / final | completed / final | -0.00000000 |
| earth_ceres_2030__reference | partial / psi | failed / psi | — |
| earth_ceres_2030__thrust_x2 | partial / psi | partial / psi | — |
| earth_ceres_2030__exhaust_x2 | completed / final | completed / final | -0.00000000 |
| earth_ceres_2030__mass_x2 | partial / psi | partial / psi | — |
| earth_ceres_2030__launch_plus_90d | partial / psi | partial / psi | — |
| earth_ceres_2030__duration_x1p2 | partial / psi | partial / psi | — |

## Среда и область вывода

Первый итог: `{'completed': 14, 'partial': 8, 'failed': 2}`. Второй: `{'completed': 14, 'partial': 9, 'failed': 1}`.

Сравнение сохраняет разные окружения и реальные ошибки. Само изменение статуса не доказывает причину: численные бюджеты зависят также от скорости среды. Ошибку процесса нельзя приравнивать к физической недостижимости.

Окружение 1: `{"python": "3.12.16", "executable": "/usr/local/bin/python", "system": "Linux", "machine": "x86_64", "libc": ["glibc", "2.41"], "kernel": "6.6.87.2-microsoft-standard-WSL2", "container": true, "runtime": "docker-linux", "image_id": "sha256:17c8bdce3cd3c235b7a7245aa1315c0a764e7ad2beacfa26698fb17c41e75a2a", "dependencies": {"numpy": "2.2.5", "scipy": "1.15.1", "matplotlib": "3.10.0", "pandas": "2.2.3", "kiam-astro": "6.1.6", "daceypy": "1.4.0", "pillow": "13.0.0"}, "thread_limits": {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}}`.

Окружение 2: `{"python": "3.12.16", "executable": "/usr/local/bin/python", "system": "Linux", "machine": "x86_64", "libc": ["glibc", "2.41"], "kernel": "6.6.87.2-microsoft-standard-WSL2", "container": true, "runtime": "docker-linux", "image_id": "sha256:17c8bdce3cd3c235b7a7245aa1315c0a764e7ad2beacfa26698fb17c41e75a2a", "dependencies": {"numpy": "2.2.5", "scipy": "1.15.1", "matplotlib": "3.10.0", "pandas": "2.2.3", "kiam-astro": "6.1.6", "daceypy": "1.4.0", "pillow": "13.0.0"}, "thread_limits": {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}}`.
