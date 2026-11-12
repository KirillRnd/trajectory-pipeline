"""Continue the archived 79 Apophis cases through full ephemerides and PSI."""
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from trajectory_pipeline.coordinate_matrix import timed_call
from trajectory_pipeline.data import Trajectory, sha256, write_json
from trajectory_pipeline.orbit_transition import reconcile_irt

ROOT = Path("runs/apophis_new_full_psi_v1")
ARCHIVE = Path("data/benchmarks/apophis_new_early_sweep_2027_2033_v1")
SOURCES = Path("configs/apophis_full_sources.json")
WORKERS = 24
HORIZON = 1095.75


def reconcile(row):
    root = ROOT / "reconcile" / row["case_id"]
    root.mkdir(parents=True, exist_ok=True)
    final = root / "result.json"
    if final.exists():
        return json.loads(final.read_text())
    source = ARCHIVE / row["archive_artifact"]
    result = dict(case_id=row["case_id"], launch_tdb=row["launch_tdb"],
                  initial_days=row["duration_days"], source=str(source),
                  source_sha256=sha256(source / "trajectory.npz"),
                  metadata_sha256=sha256(source / "trajectory.json"),
                  status="partial", attempts=[])
    for chart, budget in (("costates", 240), ("iltt", 240)):
        output = root / chart
        seed = Trajectory.load(source)
        seed.metadata["mission"]["solver"].update(budget_s=35, attempt_budget_s=35,
                                                    max_nfev=120)
        try:
            trajectory, summary = timed_call(budget, reconcile_irt, seed,
                                             json.loads(SOURCES.read_text()), output,
                                             coordinates=chart)
        except Exception as exc:
            saved = output / "summary.json"
            summary = json.loads(saved.read_text()) if saved.exists() else {}
            summary.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            trajectory = None
        result["attempts"].append(dict(chart=chart, budget_s=budget,
                                       output=str(output), summary=summary))
        if trajectory is not None:
            result.update(status="completed_stage", full_source=str(output / "irt"))
            break
    write_json(final, result)
    return result


def run_batch(pool, name, fn, tasks):
    futures = {pool.submit(fn, arg): case for case, arg in tasks}
    results = {}
    for future in as_completed(futures):
        case = futures[future]
        try:
            row = future.result()
        except Exception as exc:
            row = dict(case_id=case, status="worker_error",
                       error=f"{type(exc).__name__}: {exc}")
        results[case] = row
        write_json(ROOT / f"{name}.json", results)
        print(name, case, row["status"], row.get("fuel_kg"), flush=True)
    return results


def main():
    rows = json.loads((ARCHIVE / "final_results.json").read_text())
    assert len(rows) == len({row["launch_tdb"] for row in rows}) == 79
    assert all(row["status"] == "accepted" for row in rows)
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        run_batch(pool, "reconciled", reconcile,
                  [(row["case_id"], row) for row in rows])


if __name__ == "__main__":
    main()
