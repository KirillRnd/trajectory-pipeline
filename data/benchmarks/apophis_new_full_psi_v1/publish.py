"""Publish one audited row per original start and retain reproducible artifacts."""
import csv
import json
import platform
import shutil
import subprocess
from collections import Counter
from importlib.metadata import version
from pathlib import Path

import numpy as np

from series import ARCHIVE, ROOT, SOURCES
from physical_series import physical_case
from trajectory_pipeline.data import Scales, Trajectory, sha256, write_json
from trajectory_pipeline.verification import verify_irt


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def checkpoint(path, destination):
    trajectory = Trajectory.load(path)
    meta = trajectory.metadata
    model = meta.get("bounded_model", {})
    mass = meta["mission"]["mass_kg"]
    force = (model["a_max"] * Scales(**meta["scales"]).acceleration_m_s2 * mass
             if model else None)
    shutil.copytree(path, destination)
    return dict(path=str(path), archive_path=str(destination.relative_to(OUT)),
                stage=meta["stage"], days=meta["mission"]["tof_days"],
                alpha=model.get("alpha"), beta=model.get("beta"), thrust_N=force,
                variable_mass=model.get("variable_mass"),
                minimum_mass_kg=meta.get("verification", {}).get("minimum_mass_kg"),
                departure_parameter=meta.get("departure", {}).get("parameter"))


def reasons(attempts):
    result = []
    for attempt in attempts:
        if attempt.get("error"):
            result.append(attempt["error"])
        if attempt.get("final_admission_error"):
            result.append(attempt["final_admission_error"])
        for event in attempt.get("events", []):
            if event["status"] in ("completed", "completed_stage"):
                continue
            detail = event.get("details", {})
            reason = event.get("error") or event.get("reason") or detail.get("stop_reason")
            reason = reason or event.get("stopped_phase") or event["status"]
            if reason != "Physical PSI requires exact active/passive arcs":
                result.append(f'{event["operation"]}: {reason}')
    return result


def collect(row):
    case = row["case_id"]
    source = Path(row["source"])
    assert sha256(source / "trajectory.json") == row["metadata_sha256"]
    assert sha256(source / "trajectory.npz") == row["source_sha256"]
    folder = OUT / case
    folder.mkdir()
    checkpoints = []
    continuation_stops = []
    if row.get("full_source"):
        full = Trajectory.load(row["full_source"])
        early = Trajectory.load(source)
        check = verify_irt(full)
        assert check["passed"]
        shifts = {}
        for endpoint, key in (("departure", "initial_state_si"), ("target", "target_state_si")):
            delta = np.asarray(full.metadata[key]) - np.asarray(early.metadata[key])
            shifts[endpoint] = dict(position_m=float(np.linalg.norm(delta[:3])),
                                    velocity_m_s=float(np.linalg.norm(delta[3:])),
                                    state_delta_si=delta.tolist())
        row["reconciliation_replay"] = check
        row["reconciliation_shifts"] = shifts
        checkpoints.append(checkpoint(Path(row["full_source"]), folder / "full_irt"))
    for phase_root in (ROOT / "routes" / case, ROOT / "routes_spawn" / case):
        if not phase_root.exists():
            continue
        label = phase_root.parent.name
        for raw in sorted(phase_root.rglob("*.json")):
            if raw.name in {"trajectory.json", "request.json"}:
                continue
            target = folder / "diagnostics" / label / raw.relative_to(phase_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(raw, target)
            if label == "routes_spawn" and raw.name == "continuation.json":
                state = read(raw)
                if state.get("status") == "completed_stage":
                    continue
                rejected = [event for event in state.get("history", [])
                            if not event.get("accepted")]
                continuation_stops.append(dict(
                    path=str(target.relative_to(OUT)),
                    stage=state.get("profile", {}).get("stage"),
                    reached=state.get("reached_parameter"),
                    reason=state.get("stop_reason", state.get("error", "interrupted")),
                    last_rejection=rejected[-1].get("message") if rejected else None))
        for path in sorted(phase_root.iterdir()):
            if (label == "routes_spawn" and path.name.endswith(("_checkpoint", "_last"))
                    and (path / "trajectory.json").exists()):
                target = folder / label / path.name
                target.parent.mkdir(exist_ok=True)
                checkpoints.append(checkpoint(path, target))
    if row["physical"]:
        audited = physical_case(row, row["physical"])
        assert audited
        checkpoints.append(checkpoint(Path(audited["artifact"]), folder / "physical"))
        audited["archive_artifact"] = f"{case}/physical"
        row["physical"] = audited
    row["final_status"] = "physical_accepted" if row["physical"] else "partial"
    row["checkpoints"] = checkpoints
    row["route_stops"] = reasons(row["physical_attempts"])
    row["continuation_stops"] = continuation_stops
    write_json(folder / "result.json", row)
    return row


def report(rows, summary):
    lines = ["# 79 ИРТ Апофиса → полные эфемериды → ПСИ", "",
             f'Пересогласовано **{summary["reconciled"]}/79**, принято физических '
             f'ПСИ **{summary["physical"]}/79**. У {summary["duration_changed"]} '
             "принятых ПСИ изменилась длительность.", "",
             "Расчёты межпланетного участка выполнены в Linux Docker. Движение "
             "аппарата считалось в центральном поле Солнца. Полные "
             "эфемериды задают обе границы в положении и скорости. Даты старта "
             "зафиксированы. Горизонт перелёта 1095,75 суток, избыток до 3 км/с. "
             "Земная граница взята из KIAM/JPLEPH, граница Апофиса — из "
             "номинальных векторов Horizons JPL#220 на дату прибытия. "
             "После встречи 13.04.2029 эта таблица задаёт прогноз по "
             "довстречным наблюдениям. Рассеяние орбиты в серии не оценивалось.", "",
             "Физическая приёмка требует точных дуг, α=β=1, 204 кг на старте, "
             "сухую массу 140 кг, расход не более 64 кг ксенона, тягу 36 мН и "
             "скорость истечения 11767,98 м/с. У принятых ПСИ повторены независимое "
             "интегрирование, KIAM и аудит исходного запроса с полными эфемеридами "
             "и принятой длительностью. Для гладкого продолжения резерв сухой "
             "массы мог временно нарушаться при положительной массе.", "",
             "Основной путь использует добавочный импульс, Пазов и последовательное "
             "введение массы, тяги и топливного функционала. После отказов проверены "
             "совместное продолжение и освобождение длительности на разных моделях. "
             "Оставшиеся случаи направлены на коррекцию точных дуг, независимый "
             "R-перенос при наличии совместимой опоры и раннее освобождение времени "
             "в диапазоне 1–1095,75 суток. Несходимость в этих бюджетах не доказывает "
             "физическую недостижимость.", "",
             "Основные бюджеты продолжения составляют 45–90 секунд на этап. "
             "Внешние лимиты операций составляют 35–480 секунд. Бюджеты и "
             "фактические причины остановок записаны в диагностике.", "",
             "Первоначальный физический запуск прерван после расхождений границ "
             "в дочерних процессах. Повтор выполнен со свежими процессами Linux. "
             "Результаты первого запуска использованы только после повторной "
             "приёмки. Диагностика первой попытки сохранена.", "",
             "| Дата старта TDB | Исходная ИРТ, сут | ПСИ, сут | Ксенон, кг | Результат |",
             "|---|---:|---:|---:|---|"]
    best = summary.get("minimum_observed_xenon")
    if best:
        lines[4:4] = [
            f'Минимальный наблюдённый расход {best["fuel_kg"]:.5f} кг при старте '
            f'{best["launch_tdb"][:10]} и длительности {best["tof_days"]:.3f} суток.', ""]
    for row in rows:
        physical = row["physical"]
        if physical:
            result = (f'{physical["tof_days"]:.3f} | {physical["fuel_kg"]:.5f} | '
                      f'{physical["route"]}')
        elif not row.get("full_source"):
            result = "— | — | Остановка при пересогласовании"
        else:
            stages = sorted({x["stage"] for x in row["checkpoints"]})
            last_reason = (row["route_stops"] or ["см. диагностику"])[-1]
            last_reason = last_reason.replace("|", "/").replace("\n", " ")
            result = f'— | — | {", ".join(stages)}. {last_reason}'
        lines.append(f'| {row["launch_tdb"][:10]} | {row["initial_days"]:.3f} | {result} |')
    lines.extend(["", "Параметры α/β, тяга, длительность, причины остановок, "
                  "траектории и SHA256 сохранены по каждому случаю в архиве. "
                  "Полные рабочие результаты лежат в runs/apophis_new_full_psi_v1.", ""])
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")


OUT = ROOT / "archive"


def main():
    rows = read(ROOT / "final.json")
    assert len(rows) == len({row["launch_tdb"] for row in rows}) == 79
    for row in rows:
        if not row.get("full_source"):
            continue
        attempts = row["physical_attempts"]
        assert attempts and attempts[0].get("phase") == "primary", row["case_id"]
        if attempts[0]["status"] != "completed":
            assert len(attempts) >= 2, row["case_id"]
            if attempts[1]["status"] != "completed":
                assert len(attempts) == 3, row["case_id"]
    for name, expected in read(ARCHIVE / "SHA256.json").items():
        assert sha256(ARCHIVE / name) == expected, name
    OUT.mkdir(exist_ok=False)
    rows = [collect(row) for row in rows]
    physical = [row["physical"] for row in rows if row["physical"]]
    summary = dict(total=len(rows), reconciled=sum(bool(r.get("full_source")) for r in rows),
                   physical=len(physical), by_route=dict(Counter(r["route"] for r in physical)),
                   partial=len(rows)-len(physical),
                   duration_changed=sum(abs(r["physical"]["tof_days"] - r["initial_days"]) > 1e-5
                                        for r in rows if r["physical"]))
    if physical:
        best = min((row for row in rows if row["physical"]),
                   key=lambda row: row["physical"]["fuel_kg"])
        summary["minimum_observed_xenon"] = dict(
            launch_tdb=best["launch_tdb"], case_id=best["case_id"],
            **{key: best["physical"][key] for key in ("tof_days", "fuel_kg", "final_mass_kg")})
        summary["max_accepted_fuel_kg"] = max(row["fuel_kg"] for row in physical)
    write_json(OUT / "summary.json", summary)
    write_json(OUT / "final.json", rows)
    with (OUT / "dates.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["case_id", "launch_tdb", "initial_days", "reconciled", "status",
                  "tof_days", "fuel_kg", "final_mass_kg", "route", "route_stops"]
        table = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        table.writeheader()
        for row in rows:
            psi = row["physical"] or {}
            table.writerow(dict(row, reconciled=bool(row.get("full_source")),
                                status="physical" if psi else "partial",
                                route_stops=" | ".join(row["route_stops"]),
                                **{field: psi.get(field) for field in fields[5:-1]}))
    shutil.copy2(ROOT / "README.md", OUT / "README.md")
    for file in ROOT.glob("*.json"):
        if file.name != "final.json":
            shutil.copy2(file, OUT / file.name)
    for name in ("series.py", "physical_series.py", "physical_series_initial.py",
                 "reconcile_extra.py", "publish.py"):
        shutil.copy2(ROOT / name, OUT / name)
    shutil.copytree("trajectory_pipeline", OUT / "source" / "trajectory_pipeline",
                    ignore=shutil.ignore_patterns("__pycache__"))
    for path in (SOURCES, Path("configs/apophis_new_early.json"),
                 Path("configs/apophis_spd50m_204.json"), Path("compose.yaml"),
                 Path("docker/pipeline.Dockerfile"), Path("docker/requirements.lock.txt")):
        destination = OUT / "source" / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    paths = [Path("data/ephemerides/apophis/vectors.npz"),
             Path("data/ephemerides/apophis/metadata.json"), ARCHIVE / "SHA256.json",
             *Path("ILTT").glob("*.py"), *Path("data/orbits").glob("*.txt"),
             *Path("third_party/kiam_astro").glob("*.whl")]
    write_json(OUT / "environment.json", dict(python=platform.python_version(),
               platform=platform.platform(), kiam=version("kiam-astro"),
               scipy=version("scipy"), numpy=version("numpy"),
               git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
               inputs={str(path): sha256(path) for path in paths}))
    report(rows, summary)
    checksums = {str(file.relative_to(OUT)): sha256(file)
                 for file in sorted(OUT.rglob("*")) if file.is_file()}
    write_json(OUT / "SHA256.json", checksums)
    assert all(sha256(OUT / path) == digest for path, digest in checksums.items())
    print(summary, "verified_files", len(checksums), flush=True)


if __name__ == "__main__":
    main()







