# Апофис. Продолжение 79 ИРТ до физической ПСИ

`dates.csv` содержит по одной строке на каждую исходную дату. `final.json`
содержит проверки, все выбранные маршруты, отказы и пути к сохранённым массивам.
`archive_artifact` и `archive_path` заданы относительно этого архива.
Исходная ИРТ читается из архива apophis_new_early_sweep_2027_2033_v1 по полю
`source`. Её метаданные и массивы привязаны SHA256. Массивы на полных
эфемеридах лежат в `<case_id>/full_irt`. В `<case_id>/physical` сохранены
принятые точные дуги и независимые проверки. Подкаталоги `routes_spawn`
содержат проверенные промежуточные опоры. Полные журналы континуации
в `diagnostics` сохраняют бюджеты, достигнутые параметры и причины отказов.
`routes` в диагностике относится к прерванному первому запуску, а
`primary_reused.json` перечисляет повторно проверенные принятые результаты из него.

Воспроизведение выполняется из корня отдельной чистой копии trajectory-pipeline.
Используются исходный архив, локальные эфемериды, неизменённый KIAM wheel
и версия исходников из `source/`. Хеши входов в `environment.json`, образ
первоначального и основного запуска в `docker_image.json`. Поместить
`series.py`, `physical_series.py`, `reconcile_extra.py`, `publish.py`,
`physical_series_initial.py` и этот README в новый пустой каталог
`runs/apophis_new_full_psi_v1`. Штатный запуск каждого файла:

```sh
docker compose run --rm -T --entrypoint python -e PYTHONPATH=/workspace pipeline runs/apophis_new_full_psi_v1/series.py
docker compose run --rm -T --entrypoint python -e PYTHONPATH=/workspace pipeline runs/apophis_new_full_psi_v1/physical_series.py
docker compose run --rm -T --entrypoint python -e PYTHONPATH=/workspace pipeline runs/apophis_new_full_psi_v1/publish.py
```

`reconcile_extra.py` — отдельно воспроизводимая проверка 17.12.2027 с
первоочередной коррекцией границы Апофиса и более точным интегрированием.
Штатное пересогласование этой даты прошло. Для воспроизведения истории
прерванного запуска сохранён `physical_series_initial.py`; при новом расчёте
использовать основной сценарий со свежими процессами. Временные бюджеты
контроллеров зависят от производительности. `SHA256.json` фиксирует
содержимое поставленного архива.
