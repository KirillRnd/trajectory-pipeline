"""Initial planar CR3BP approximations, not corrected periodic solutions.

Normalized rotating barycentric coordinates: distance between primaries = 1,
total gravitational parameter = 1, angular speed = 1. No SI conversion or
connection to the heliocentric mission solver is implied.
"""
from importlib import import_module
import math

import numpy as np


# These are source demonstration intervals, NOT certified accuracy domains.
_EM = 0.012150584460351
CATALOGUE = {
    "L1": ("l1", _EM, 0.836915131427382 - 0.2734644, 0.836915131427382 - 1e-5, "x"),
    "L2": ("l2", _EM, 1.155682161024677 + 1e-4, 1.155682161024677 + 0.3464867, "x"),
    "L3": ("l3", _EM, -1.99906, -1.00607, "x"),
    "L4_v2": ("l4_v2", 1 / 82, 0.1, 2.79, "a"),
    "L4_v3": ("l4_v3", 1 / 82, 0.01, 2.69, "a"),
    "S3": ("s3", _EM, 0.005, 4.19, "a"),
}


def seed(family, parameter, *, mu=None):
    """Evaluate a source approximation with explicit provenance and guardrails.

S3 formulas have mu as an argument, but their fit domain has not been
established. This adapter admits only the source demonstration mu. Raw
formulas (including C1/C2, whose x-domain is unverified) remain separate.
"""
    if family not in CATALOGUE:
        raise ValueError(f"Unknown supported family {family!r}; choose {list(CATALOGUE)}")
    module_name, source_mu, lower, upper, parameter_name = CATALOGUE[family]
    value = float(parameter)
    if not math.isfinite(value) or not lower <= value <= upper:
        raise ValueError(f"{family}: parameter outside source demonstration interval [{lower}, {upper}]")
    if mu is not None and (not math.isfinite(float(mu)) or not math.isclose(float(mu), source_mu, rel_tol=0, abs_tol=1e-15)):
        raise ValueError(f"{family}: unsupported mu={mu}; source uses {source_mu}")
    module = import_module(f"components.cr3bp.approximations.{module_name}")
    arguments = (value, source_mu) if family == "S3" else (value,)
    names = ("x1", "x2", "v1", "v2", "T") if family.startswith("L4_") else ("x1_fun", "x2_fun", "v1_fun", "v2_fun", "T_fun")
    try:
        with np.errstate(all="raise"):
            values = np.asarray([getattr(module, name)(*arguments) for name in names], dtype=float)
    except (ValueError, OverflowError, FloatingPointError, ZeroDivisionError, TypeError) as exc:
        raise ValueError(f"{family}: source formula undefined at {value}") from exc
    if not np.all(np.isfinite(values)) or values[-1] <= 0:
        raise ValueError(f"{family}: invalid state or period at {value}")
    return {"family": family, "parameter": value, "parameter_name": parameter_name,
            "mu": source_mu, "state_xy_vxvy": values[:4].tolist(), "period": float(values[4]),
            "units": "normalized", "frame": "rotating_barycentric",
            "status": "approximation_only", "domain_status": "source_demo_not_accuracy_certificate",
            "source_module": f"components/cr3bp/approximations/{module_name}.py"}
