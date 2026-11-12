"""Address the source-transition case with large independent replay drift."""
import json
from pathlib import Path
from series import ARCHIVE, ROOT, SOURCES
from trajectory_pipeline.data import Trajectory, write_json
from trajectory_pipeline.coordinate_matrix import timed_call
from trajectory_pipeline.orbit_transition import reconcile_irt


def main():
    key = "date_0050_branch_00"
    row = next(x for x in json.loads((ARCHIVE / "final_results.json").read_text())
               if x["case_id"] == key)
    root = ROOT / "reconcile" / key / "target_first_precise"
    seed = Trajectory.load(ARCHIVE / row["archive_artifact"])
    seed.metadata["mission"]["solver"].update(budget_s=60, attempt_budget_s=60,
                                                max_nfev=150)
    # Keep original replay semantics while verifying the archived parent.
    trajectory, summary = timed_call(360, reconcile_irt, seed,
                                     json.loads(SOURCES.read_text()), root,
                                     coordinates="costates", boundary_first="Apophis", integration_rtol=1e-13)
    write_json(ROOT / "extra_transition.json", dict(case_id=key, chart="costates",
               budget_s=360, output=str(root), summary=summary,
               full_source=str(root / "irt") if trajectory is not None else None))


if __name__ == "__main__":
    main()

