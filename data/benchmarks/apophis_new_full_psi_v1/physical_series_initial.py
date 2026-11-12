"""Run physical routes and independently audit admissions against original dates."""
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
from time import sleep

from series import ARCHIVE, HORIZON, ROOT, SOURCES, WORKERS, run_batch
from trajectory_pipeline.accepted_irt_routes import physical, run_case
from trajectory_pipeline.contract import audit_configuration, make_request
from trajectory_pipeline.data import Trajectory, write_json
from trajectory_pipeline.physical_transfer_routes import compatible, worker
from trajectory_pipeline.problem import Mission


SETTINGS = dict(intermediate_allow_below_dry_mass=True)
ROUTES = ROOT / "routes"


def physical_case(row, phase_result):
    if phase_result.get("status") != "completed":
        return None
    trajectory = Trajectory.load(phase_result["artifact"])
    actual = Mission(**trajectory.metadata["mission"])
    original = Mission(**Trajectory.load(row["source"]).metadata["mission"])
    expected = replace(original, orbit_sources=json.loads(SOURCES.read_text()),
                       tof_days=actual.tof_days)
    if not 1 <= actual.tof_days <= HORIZON:
        raise ValueError("Duration outside requested search interval")
    check = physical(trajectory, expected)
    if check["fuel_kg"] > 64 + 1e-5:
        raise ValueError("Xenon reserve exceeded")
    return dict(phase_result, **check)


def main():
    transitions = json.loads((ROOT / "reconciled.json").read_text())
    for _ in range(55):
        if len(transitions) == 79:
            break
        sleep(10)
        transitions = json.loads((ROOT / "reconciled.json").read_text())
    assert len(transitions) == 79
    base = Mission.load("configs/apophis_spd50m_204.json")
    early = Mission.load("configs/apophis_new_early.json")
    assert base.spacecraft == early.spacecraft and base.mass_kg == early.mass_kg == 204
    assert base.spacecraft == dict(thrust_N=.036, exhaust_velocity_m_s=11767.98,
                                   dry_mass_kg=140)
    cases = []
    for key, row in transitions.items():
        if row["status"] != "completed_stage":
            continue
        source = row["full_source"]
        original = Mission(**Trajectory.load(row["source"]).metadata["mission"])
        expected = replace(original, orbit_sources=json.loads(SOURCES.read_text()))
        assert original.spacecraft == base.spacecraft and original.mass_kg == base.mass_kg
        audit_configuration(Trajectory.load(source), expected, make_request(expected))
        cases.append(dict(case_id=key, source=source, settings=SETTINGS,
                          horizon_days=HORIZON, transfer_bounds_days=[1., HORIZON]))
    write_json(ROOT / "physical_design.json", dict(cases=cases, workers=WORKERS,
               settings=SETTINGS, horizon_days=HORIZON))
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        primary = run_batch(pool, "primary", run_case,
                            [(c["case_id"], (c, str(ROUTES), "primary")) for c in cases])
        pending = [c for c in cases if primary[c["case_id"]]["status"] != "completed"]
        recover = run_batch(pool, "recover", run_case,
                            [(c["case_id"], (c, str(ROUTES), "recover")) for c in pending])
        pending = [c for c in pending if recover[c["case_id"]]["status"] != "completed"]
        references = []
        for key, row in (primary | recover).items():
            accepted = physical_case(transitions[key], row)
            if accepted:
                path = accepted["artifact"]
                references.append((Mission(**Trajectory.load(path).metadata["mission"]), path))
        tasks = []
        for c in pending:
            mission = Mission(**Trajectory.load(c["source"]).metadata["mission"])
            options = [(abs(mission.launch_jd - other.launch_jd), path)
                       for other, path in references if compatible(mission, other)]
            reference = min(options)[1] if options else None
            tasks.append((c["case_id"], (c, str(ROUTES), reference)))
        write_json(ROOT / "transfer_design.json", [dict(case_id=k, reference=t[2])
                                                    for k, t in tasks])
        transfer = run_batch(pool, "transfer", worker, tasks)
    results = []
    for key, row in sorted(transitions.items(), key=lambda item: item[1]["launch_tdb"]):
        attempts = [phase[key] for phase in (primary, recover, transfer) if key in phase]
        accepted = None
        for attempt in attempts:
            try:
                accepted = physical_case(row, attempt) or accepted
            except (ValueError, RuntimeError, KeyError) as exc:
                attempt["final_admission_error"] = str(exc)
        results.append(dict(row, physical=accepted, physical_attempts=attempts))
    write_json(ROOT / "final.json", results)


if __name__ == "__main__":
    main()

