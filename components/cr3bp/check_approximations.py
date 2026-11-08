"""Independent propagation of six representative seeds, without correction.

Run in Docker with PYTHONPATH=/workspace. Closure residuals are observations,
not acceptance of the seed as a periodic orbit or a mission segment.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

from trajectory_pipeline.cr3bp import seed


def rhs(_t, state, mu):
    position, velocity = state[:2], state[2:]
    r1 = position + np.array([mu, 0.])
    r2 = position + np.array([mu - 1., 0.])
    gravity = -(1 - mu) * r1 / np.linalg.norm(r1)**3 - mu * r2 / np.linalg.norm(r2)**3
    return np.r_[velocity, gravity + position + np.array([2 * velocity[1], -2 * velocity[0]])]


def jacobi(states, mu):
    x, y, vx, vy = np.asarray(states).T
    return x*x + y*y + 2*(1-mu)/np.hypot(x+mu, y) + 2*mu/np.hypot(x+mu-1, y) - vx*vx - vy*vy


def check():
    rows = []
    for family, parameter in [("L1", .8), ("L2", 1.2), ("L3", -1.3), ("L4_v2", 1.), ("L4_v3", 1.), ("S3", 1.)]:
        result = seed(family, parameter)
        initial = np.array(result["state_xy_vxvy"])
        sol = solve_ivp(rhs, [0, result["period"]], initial, args=(result["mu"],),
                        method="DOP853", rtol=1e-11, atol=1e-13)
        result.update(integration_success=bool(sol.success), integration_message=sol.message,
                      position_closure=float(np.linalg.norm(sol.y[:2, -1] - initial[:2])),
                      velocity_closure=float(np.linalg.norm(sol.y[2:, -1] - initial[2:])),
                      jacobi_max_drift=float(np.max(np.abs(jacobi(sol.y.T, result["mu"]) - jacobi(initial, result["mu"])))),
                      accepted_as_periodic_orbit=False)
        rows.append(result)
    return {"scope": "six source approximations; normalized units; no correction or mission stitching", "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = check()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
