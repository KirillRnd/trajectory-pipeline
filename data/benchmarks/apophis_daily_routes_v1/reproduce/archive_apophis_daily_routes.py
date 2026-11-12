import json,shutil
from pathlib import Path
from trajectory_pipeline.data import sha256,write_json
root=Path('runs/apophis_daily_routes_v1');dest=Path('runs/apophis_daily_archive_v1');dest.mkdir(exist_ok=False)
for name in ('design.json','final_routes.json','final_audit.json','daily_results.json','daily_results.csv','final_summary.json','report.md','clock_regression.json','free_time_recheck_design.json','free_time_recheck_results.json'):
    shutil.copy2(root/name,dest/name)
for p in root.glob('*.log'):
    (dest/'logs').mkdir(exist_ok=True);shutil.copy2(p,dest/'logs'/p.name)
for i in range(2):shutil.copytree(root/f'daily_{i}',dest/f'daily_{i}')
anchors={r['launch_tdb'][:10] for r in json.loads((root/'design.json').read_text())['anchors']}
for folder in (root/'chains').iterdir():
    if not folder.is_dir():continue
    out=dest/'chains'/folder.name;out.mkdir(parents=True)
    for name in ('request.json','summary.json','error.log','hard_timeout.json','cold_route_stopped.json','pre_grid_fix_summary.json'):
        if (folder/name).exists():shutil.copy2(folder/name,out/name)
    for name in ('00_irt','physical','free_time','direct_exact_probe','r_fixed','r_free','free_time_recheck'):
        if (folder/name).exists():shutil.copytree(folder/name,out/name)
    for p in folder.rglob('continuation.json'):
        q=out/p.relative_to(folder);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    if folder.name in anchors:
        for name in ('01_departure','02_pazov','03_psi'):
            p=folder/name
            if (p/'summary.json').exists():
                s=json.loads((p/'summary.json').read_text());shutil.copy2(p/'summary.json',out/name/'summary.json')
                key=s.get('last_result')
            elif (p/'continuation.json').exists():key=json.loads((p/'continuation.json').read_text()).get('last_point')
            else:key=None
            if key and (p/key).exists():shutil.copytree(p/key,out/name/key,dirs_exist_ok=True)
shutil.copytree('output/pipeline/apophis_daily_routes_v1',dest/'figures')
(dest/'reproduce').mkdir()
for name in ('apophis_daily_routes.py','resume_daily_anchors.py','report_apophis_daily_routes.py','archive_apophis_daily_routes.py','probe_daily_exact.py','rescue_daily_r.py','adopt_daily_r.py','probe_daily_free_capture.py','check_daily_clock.py','recheck_daily_free_time.py'):
    shutil.copy2(Path('runs')/name,dest/'reproduce'/name)
write_json(dest/'raw_runs_sha256.json',{str(p.relative_to(root)):sha256(p) for p in sorted(root.rglob('*')) if p.is_file()})
(dest/'README.md').write_text('''# Апофис: суточная сетка и полные межпланетные маршруты

daily_results.csv/json — все 72 даты; final_routes.json — физические маршруты.
design.json фиксирует окна, исходные семь ИРТ и аппарат. Базовая граница R сохранена.
daily_0, daily_1 — полный ранний sweep. chains — запросы, итоги, ИРТ, физические
и свободные по времени ПСИ, журналы продолжения. Для исходных семи дат добавлены
последние принятые результаты промежуточных модулей.
Все промежуточные массивы полной серии сохранены локально в
runs/apophis_daily_routes_v1; raw_runs_sha256.json фиксирует их хеши.
Этот компактный архив не содержит каждый промежуточный массив продолжения.
Пути внутри JSON сохранены относительно исходного корня проекта.

reproduce/ содержит контроллер опыта и отчёт. Все Python-запуски — Linux Docker,
PYTHONPATH=/workspace. Для нового опыта восстановить исходные семь ИРТ по
путям первого раннего sweep и выбрать новый ROOT в контроллере.
Сохранённые физические участки проверены независимым интегрированием и KIAM.
При неудаче освобождения времени физическая ПСИ сохранена и явно отмечена.
Неизменённые критерии приёмки; без индивидуальной подгонки параметров двигателя.
''')
print('archive files',sum(p.is_file() for p in dest.rglob('*')))
