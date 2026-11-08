"""
Continuation methods for energy-optimal low-thrust boundary-value problems.

This module is a Python translation/generalization of the MATLAB continuation
code used in the dissertation experiments.  It intentionally works with plain
initial/final vectors and does not depend on the ephemeris layer.  The intended
usage is:

    problem = BoundaryProblem(r0, v0, rf, vf, tof, mode="rendezvous")
    result = solve_gravity_continuation(problem, branch_n=N)

or, for the simpler residual-continuation variant:

    result = solve_simple_continuation(problem)

State convention
----------------
The continuation variable is

    z = [p_v(t0), d p_v/dt(t0)]

because the MATLAB implementation uses the second-order primer-vector equation.
For compatibility with first-order Hamiltonian notation, helper functions
``z_from_pr_pv`` and ``pr_pv_from_z`` are provided. Since

    d p_v / dt = -p_r,

we have z = [p_v0, -p_r0].

Problem modes
-------------
- mode="rendezvous": final position and velocity are fixed,
      f = [r(tf)-rf, v(tf)-vf]
- mode="flyby": final position is fixed, final velocity is free,
      f = [r(tf)-rf, p_v(tf)]

The gravity-continuation variant scales the initial and target velocities along
mu(tau), as in the lecture notes / MATLAB code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import perf_counter
from typing import Callable, Iterable, Optional, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.integrate import solve_ivp
from scipy.optimize import root


# -----------------------------------------------------------------------------
# Basic types
# -----------------------------------------------------------------------------

class TrajectoryMode(str, Enum):
    """Boundary condition type at the right endpoint."""

    RENDEZVOUS = "rendezvous"  # fixed final r and v
    FLYBY = "flyby"            # fixed final r, free final v, pv(tf)=0


@dataclass(slots=True)
class ContinuationConfig:
    """Numerical parameters for continuation and internal integrations."""

    rtol: float = 1e-10
    atol: float = 1e-10
    method_internal: str = "DOP853"
    # External continuation integrator. Supported special values:
    #   "RK4_FIXED"  -- fixed-step RK4 on t_eval_tau/tau_span, much faster for checks;
    #   "EULER_FIXED" -- fixed-step Euler, mainly for debugging;
    # otherwise passed to scipy.solve_ivp (e.g. "LSODA", "DOP853").
    method_external: str = "RK4_FIXED"
    tau_span: tuple[float, float] = (0.0, 1.0)
    external_fixed_steps: int = 20
    t_eval_tau: Optional[NDArray[np.float64]] = None
    max_step_tau: Optional[float] = None
    refine: bool = False
    # Root refinement is intentionally disabled by default.
    # Continuation itself is the two-nested-integrator method; refinement is a separate check.
    root_method: str = "lm"
    output_points: int = 400
    debug: bool = False
    debug_first_unique_taus: int = 2
    debug_tau_unique_tol: float = 1e-12
    debug_print: bool = True
    trivial_residual_tol: float = 1e-13
    raise_on_internal_failure: bool = False
    # Optional caller-owned budget/cancellation check, evaluated inside solve_ivp.
    integration_guard: Optional[Callable[[], None]] = None


@dataclass(slots=True)
class BoundaryProblem:
    """Boundary-value problem in dimensionless units.

    Parameters
    ----------
    r0, v0 : initial position and velocity.
    rf, vf : target final position and velocity.  ``vf`` is ignored in flyby
        mode, but can still be supplied for diagnostics.
    tof : time of flight in the same dimensionless time units as the dynamics.
    mu : physical/final gravitational parameter. In the dissertation's
        dimensionless two-body setting this is usually 1.
    mode : "rendezvous" or "flyby".
    """

    r0: NDArray[np.float64]
    v0: NDArray[np.float64]
    rf: NDArray[np.float64]
    vf: Optional[NDArray[np.float64]]
    tof: float
    mu: float = 1.0
    mode: TrajectoryMode | str = TrajectoryMode.RENDEZVOUS

    def __post_init__(self):
        object.__setattr__(self, "r0", _vec3(self.r0, "r0"))
        object.__setattr__(self, "v0", _vec3(self.v0, "v0"))
        object.__setattr__(self, "rf", _vec3(self.rf, "rf"))
        if self.vf is not None:
            object.__setattr__(self, "vf", _vec3(self.vf, "vf"))
        if isinstance(self.mode, str):
            object.__setattr__(self, "mode", TrajectoryMode(self.mode))
        if self.mode == TrajectoryMode.RENDEZVOUS and self.vf is None:
            raise ValueError("vf must be supplied for rendezvous mode")
        if self.tof <= 0:
            raise ValueError("tof must be positive")
        if self.mu <= 0:
            raise ValueError("mu must be positive")


@dataclass(slots=True)
class ContinuationDiagnostics:
    """Counters and timing data collected during a continuation run."""

    elapsed_sec: float = 0.0
    external_nfev: int = 0
    internal_integrations: int = 0
    internal_nfev_total: int = 0
    root_nfev: int = 0
    continuation_success: bool = False
    refinement_success: Optional[bool] = None
    message: str = ""
    debug_trace: list[dict] = field(default_factory=list)


@dataclass(slots=True)
class ContinuationResult:
    """Result of one continuation run."""

    method: str
    problem: BoundaryProblem
    z0: NDArray[np.float64]
    z_cont: NDArray[np.float64]
    z_final: NDArray[np.float64]
    success: bool
    residual: NDArray[np.float64]
    residual_norm: float
    diagnostics: ContinuationDiagnostics
    branch_n: Optional[int] = None
    mu0: Optional[float] = None
    tau_grid: Optional[NDArray[np.float64]] = None
    z_path: Optional[NDArray[np.float64]] = None
    final_state: Optional[NDArray[np.float64]] = None
    functional: Optional[float] = None
    endpoint: dict[str, float] = field(default_factory=dict)

    @property
    def pv0(self) -> NDArray[np.float64]:
        return self.z_final[:3]

    @property
    def pr0(self) -> NDArray[np.float64]:
        return -self.z_final[3:6]

    @property
    def endpoint_errors(self) -> dict[str, float]:
        """Backward-compatible alias for ``endpoint``.

        Some early notebook cells used the longer name ``endpoint_errors``.
        The stored field is ``endpoint``.
        """
        return self.endpoint


# -----------------------------------------------------------------------------
# Public helpers for adjoint convention conversion
# -----------------------------------------------------------------------------

def z_from_pr_pv(pr0: ArrayLike, pv0: ArrayLike) -> NDArray[np.float64]:
    """Convert first-order adjoints (pr0, pv0) to continuation z.

    Since d(pv)/dt = -pr, z = [pv0, -pr0].
    """

    pr = _vec3(pr0, "pr0")
    pv = _vec3(pv0, "pv0")
    return np.concatenate([pv, -pr]).astype(float)


def pr_pv_from_z(z: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Convert continuation z = [pv0, pv_dot0] to first-order adjoints."""

    z = _vec6(z, "z")
    pv0 = z[:3].copy()
    pr0 = -z[3:6].copy()
    return pr0, pv0


# -----------------------------------------------------------------------------
# Main solvers
# -----------------------------------------------------------------------------


def solve_simple_continuation(
    problem: BoundaryProblem,
    z_initial: Optional[ArrayLike] = None,
    config: Optional[ContinuationConfig] = None,
) -> ContinuationResult:
    """Solve by the simple residual-continuation method.

    This is the Python analogue of ``externalIntegrationSimple.m``:

        f(z(tau)) = (1 - tau) b,
        dz/dtau = - (df/dz)^(-1) b,

    where b = f(z_initial).

    Notes
    -----
    By default this function performs *only continuation*. Root refinement is a
    separate optional stage controlled by ``config.refine``. This keeps the call
    faithful to the two-nested-integrator continuation scheme and avoids hiding a
    slow Newton/LM solve inside a smoke test.
    """

    cfg = config or ContinuationConfig()
    z0 = _vec6(np.zeros(6) if z_initial is None else z_initial, "z_initial")
    counters = {"internal_integrations": 0, "internal_nfev_total": 0}
    debug_trace: list[dict] = []
    t_start = perf_counter()

    b_eval = evaluate_residual_and_jacobian_simple(problem, z0, cfg, counters)
    b = b_eval.residual

    # Trivial case: the initial guess already satisfies the boundary conditions.
    # This is important for smoke tests and also explains why root_nfev should be
    # zero unless explicit post-continuation refinement is requested.
    if np.linalg.norm(b) <= cfg.trivial_residual_tol:
        endpoint = _endpoint_errors(problem, b_eval.state, velocity_scale=1.0)
        elapsed = perf_counter() - t_start
        diag = ContinuationDiagnostics(
            elapsed_sec=elapsed,
            external_nfev=0,
            internal_integrations=counters["internal_integrations"],
            internal_nfev_total=counters["internal_nfev_total"],
            root_nfev=0,
            continuation_success=True,
            refinement_success=None,
            message="initial residual is already below trivial_residual_tol; continuation skipped",
            debug_trace=debug_trace,
        )
        return ContinuationResult(
            method="simple_residual_continuation",
            problem=problem,
            z0=z0,
            z_cont=z0.copy(),
            z_final=z0.copy(),
            success=True,
            residual=b,
            residual_norm=float(np.linalg.norm(b)),
            diagnostics=diag,
            tau_grid=np.array([0.0, 1.0]),
            z_path=np.vstack([z0, z0]),
            final_state=b_eval.state,
            functional=b_eval.functional,
            endpoint=endpoint,
        )

    def rhs_tau(tau: float, z: NDArray[np.float64]) -> NDArray[np.float64]:
        ev = evaluate_residual_and_jacobian_simple(problem, z, cfg, counters)
        dzdtau = _solve_linear(ev.jacobian, -b)
        _record_debug_point(debug_trace, cfg, method="simple", tau=float(tau), z=z, ev=ev, dzdtau=dzdtau)
        return dzdtau

    sol_tau = _integrate_external_continuation(rhs_tau, z0, cfg)
    _debug_print_accepted_points(cfg, "simple", sol_tau)

    z_cont = sol_tau.y[:, -1]
    z_final, root_nfev, refine_success, refine_msg = _maybe_refine(
        problem, z_cont, cfg, simple=True, mu0=None, counters=counters
    )
    final_eval = evaluate_residual_and_jacobian_simple(problem, z_final, cfg, counters)
    final_summary = _evaluate_final_solution_simple(problem, z_final, cfg, counters)

    elapsed = perf_counter() - t_start
    diag = ContinuationDiagnostics(
        elapsed_sec=elapsed,
        external_nfev=int(sol_tau.nfev),
        internal_integrations=counters["internal_integrations"],
        internal_nfev_total=counters["internal_nfev_total"],
        root_nfev=root_nfev,
        continuation_success=bool(sol_tau.success),
        refinement_success=refine_success,
        message=(sol_tau.message if sol_tau.message else "") + ("; " + refine_msg if refine_msg else ""),
        debug_trace=debug_trace,
    )

    success = bool(sol_tau.success) and (refine_success is not False) and np.all(np.isfinite(final_eval.residual))
    return ContinuationResult(
        method="simple_residual_continuation",
        problem=problem,
        z0=z0,
        z_cont=z_cont,
        z_final=z_final,
        success=success,
        residual=final_eval.residual,
        residual_norm=float(np.linalg.norm(final_eval.residual)),
        diagnostics=diag,
        tau_grid=sol_tau.t,
        z_path=sol_tau.y.T,
        final_state=final_summary["state"],
        functional=final_summary["functional"],
        endpoint=final_summary["endpoint"],
    )


def solve_gravity_continuation(
    problem: BoundaryProblem,
    branch_n: Optional[int] = None,
    mu0: Optional[float] = None,
    z_initial: Optional[ArrayLike] = None,
    config: Optional[ContinuationConfig] = None,
) -> ContinuationResult:
    """Solve by gravitational-parameter continuation.

    This is the Python analogue of ``externalIntegration.m``:

        mu(tau) = mu0 + (mu - mu0) tau,
        f(z(tau), tau) = (1 - tau) b,
        dz/dtau = -(df/dz)^(-1) (df/dtau + b).

    Either ``mu0`` or ``branch_n`` must be supplied.  If ``branch_n`` is given,
    ``mu0`` is computed from the passive Keplerian branch condition.

    By default this function performs *only continuation*. Root refinement is a
    separate optional stage controlled by ``config.refine``.
    """

    cfg = config or ContinuationConfig()
    z0 = _vec6(np.zeros(6) if z_initial is None else z_initial, "z_initial")
    if mu0 is None:
        if branch_n is None:
            raise ValueError("Either mu0 or branch_n must be supplied")
        mu0 = mu0_for_branch(problem.r0, problem.v0, problem.rf, problem.tof, branch_n, mu=problem.mu)
    if mu0 <= 0:
        raise ValueError("mu0 must be positive")

    counters = {"internal_integrations": 0, "internal_nfev_total": 0}
    debug_trace: list[dict] = []
    t_start = perf_counter()

    b_eval = evaluate_residual_and_jacobian_gravity(problem, z0, tau=0.0, mu0=mu0, cfg=cfg, counters=counters)
    b = b_eval.residual

    # Trivial case: no deformation in mu and the initial residual is already zero.
    # Smoke tests for one circular revolution enter here and therefore should not
    # show any root_nfev.
    if (
        np.linalg.norm(b) <= cfg.trivial_residual_tol
        and abs(float(mu0) - float(problem.mu)) <= cfg.trivial_residual_tol * max(1.0, abs(float(problem.mu)))
    ):
        endpoint = _endpoint_errors(problem, b_eval.state, velocity_scale=1.0)
        elapsed = perf_counter() - t_start
        diag = ContinuationDiagnostics(
            elapsed_sec=elapsed,
            external_nfev=0,
            internal_integrations=counters["internal_integrations"],
            internal_nfev_total=counters["internal_nfev_total"],
            root_nfev=0,
            continuation_success=True,
            refinement_success=None,
            message="mu0 == mu and initial residual is below trivial_residual_tol; continuation skipped",
            debug_trace=debug_trace,
        )
        return ContinuationResult(
            method="gravity_parameter_continuation",
            problem=problem,
            z0=z0,
            z_cont=z0.copy(),
            z_final=z0.copy(),
            success=True,
            residual=b,
            residual_norm=float(np.linalg.norm(b)),
            diagnostics=diag,
            branch_n=branch_n,
            mu0=float(mu0),
            tau_grid=np.array([0.0, 1.0]),
            z_path=np.vstack([z0, z0]),
            final_state=b_eval.state,
            functional=b_eval.functional,
            endpoint=endpoint,
        )

    def rhs_tau(tau: float, z: NDArray[np.float64]) -> NDArray[np.float64]:
        ev = evaluate_residual_and_jacobian_gravity(problem, z, tau=tau, mu0=mu0, cfg=cfg, counters=counters)
        dzdtau = _solve_linear(ev.jacobian, -(ev.dfdtau + b))
        _record_debug_point(debug_trace, cfg, method="gravity", tau=float(tau), z=z, ev=ev, dzdtau=dzdtau)
        return dzdtau

    sol_tau = _integrate_external_continuation(rhs_tau, z0, cfg)
    _debug_print_accepted_points(cfg, "gravity", sol_tau)

    z_cont = sol_tau.y[:, -1]
    z_final, root_nfev, refine_success, refine_msg = _maybe_refine(
        problem, z_cont, cfg, simple=False, mu0=mu0, counters=counters
    )
    final_eval = evaluate_residual_and_jacobian_gravity(problem, z_final, tau=1.0, mu0=mu0, cfg=cfg, counters=counters)
    final_summary = _evaluate_final_solution_gravity(problem, z_final, tau=1.0, mu0=mu0, cfg=cfg, counters=counters)

    elapsed = perf_counter() - t_start
    diag = ContinuationDiagnostics(
        elapsed_sec=elapsed,
        external_nfev=int(sol_tau.nfev),
        internal_integrations=counters["internal_integrations"],
        internal_nfev_total=counters["internal_nfev_total"],
        root_nfev=root_nfev,
        continuation_success=bool(sol_tau.success),
        refinement_success=refine_success,
        message=(sol_tau.message if sol_tau.message else "") + ("; " + refine_msg if refine_msg else ""),
        debug_trace=debug_trace,
    )

    success = bool(sol_tau.success) and (refine_success is not False) and np.all(np.isfinite(final_eval.residual))
    return ContinuationResult(
        method="gravity_parameter_continuation",
        problem=problem,
        z0=z0,
        z_cont=z_cont,
        z_final=z_final,
        success=success,
        residual=final_eval.residual,
        residual_norm=float(np.linalg.norm(final_eval.residual)),
        diagnostics=diag,
        branch_n=branch_n,
        mu0=float(mu0),
        tau_grid=sol_tau.t,
        z_path=sol_tau.y.T,
        final_state=final_summary["state"],
        functional=final_summary["functional"],
        endpoint=final_summary["endpoint"],
    )

def scan_gravity_branches(
    problem: BoundaryProblem,
    branches: Iterable[int],
    z_initial: Optional[ArrayLike] = None,
    config: Optional[ContinuationConfig] = None,
    choose_by: str = "functional",
) -> tuple[Optional[ContinuationResult], list[ContinuationResult]]:
    """Run gravitational continuation for several branches and select the best.

    Parameters
    ----------
    branches : iterable of branch numbers N.
    choose_by : "functional" or "residual_norm".

    Returns
    -------
    best, all_results
    """

    results: list[ContinuationResult] = []
    for n in sorted(set(int(x) for x in branches if int(x) >= 0)):
        try:
            res = solve_gravity_continuation(problem, branch_n=n, z_initial=z_initial, config=config)
        except Exception as exc:  # keep the branch scan robust
            dummy_diag = ContinuationDiagnostics(message=f"failed before result: {exc}")
            dummy = ContinuationResult(
                method="gravity_parameter_continuation",
                problem=problem,
                z0=_vec6(np.zeros(6) if z_initial is None else z_initial, "z_initial"),
                z_cont=np.full(6, np.nan),
                z_final=np.full(6, np.nan),
                success=False,
                residual=np.full(6, np.nan),
                residual_norm=np.inf,
                diagnostics=dummy_diag,
                branch_n=n,
                mu0=None,
            )
            results.append(dummy)
        else:
            results.append(res)

    candidates = [r for r in results if r.success and np.isfinite(r.residual_norm)]
    if not candidates:
        return None, results

    if choose_by == "functional":
        candidates = [r for r in candidates if r.functional is not None and np.isfinite(r.functional)]
        if not candidates:
            return None, results
        best = min(candidates, key=lambda r: float(r.functional))
    elif choose_by == "residual_norm":
        best = min(candidates, key=lambda r: r.residual_norm)
    else:
        raise ValueError("choose_by must be 'functional' or 'residual_norm'")

    return best, results


def candidate_branches_around_lambda(lambda_guess: float, radius: int = 1) -> list[int]:
    """Return a compact branch list around a guessed vitkovaya dalnost.

    This mirrors the MATLAB logic floor/ceil(lambda), floor/ceil(lambda±1),
    generalized to an arbitrary integer radius.
    """

    branches: set[int] = set()
    for shift in range(-radius, radius + 1):
        x = float(lambda_guess) + shift
        branches.add(int(np.floor(x)))
        branches.add(int(np.ceil(x)))
    return sorted(n for n in branches if n >= 0)


# -----------------------------------------------------------------------------
# Residual/Jacobian evaluation
# -----------------------------------------------------------------------------

@dataclass(slots=True)
class _EvalResult:
    residual: NDArray[np.float64]
    jacobian: NDArray[np.float64]
    dfdtau: NDArray[np.float64]
    state: NDArray[np.float64]
    functional: float


def evaluate_residual_and_jacobian_simple(
    problem: BoundaryProblem,
    z: ArrayLike,
    cfg: Optional[ContinuationConfig] = None,
    counters: Optional[dict] = None,
) -> _EvalResult:
    cfg = cfg or ContinuationConfig()
    sol = _integrate_augmented_simple(problem, _vec6(z, "z"), cfg, counters)
    y = sol.y[:, -1]
    residual, jac = _residual_and_jac_from_augmented(problem, y, velocity_scale=1.0)
    functional = _functional_from_solution(sol)
    return _EvalResult(residual=residual, jacobian=jac, dfdtau=np.zeros_like(residual), state=y, functional=functional)


def evaluate_residual_and_jacobian_gravity(
    problem: BoundaryProblem,
    z: ArrayLike,
    tau: float,
    mu0: float,
    cfg: Optional[ContinuationConfig] = None,
    counters: Optional[dict] = None,
) -> _EvalResult:
    cfg = cfg or ContinuationConfig()
    sol = _integrate_augmented_gravity(problem, _vec6(z, "z"), tau=tau, mu0=mu0, cfg=cfg, counters=counters)
    y = sol.y[:, -1]
    mu_t = _mu_tau(float(tau), mu0, problem.mu)
    velocity_scale = np.sqrt(mu_t / problem.mu)
    residual, jac = _residual_and_jac_from_augmented(problem, y, velocity_scale=velocity_scale)

    r_tau = y[84:87]
    v_tau = y[87:90]
    pv_tau = y[90:93]
    if problem.mode == TrajectoryMode.RENDEZVOUS:
        target_v_tau = _velocity_scale_derivative(float(tau), mu0, problem.mu) * problem.vf
        dfdtau = np.concatenate([r_tau, v_tau - target_v_tau])
    else:
        dfdtau = np.concatenate([r_tau, pv_tau])

    functional = _functional_from_solution(sol)
    return _EvalResult(residual=residual, jacobian=jac, dfdtau=dfdtau, state=y, functional=functional)


# -----------------------------------------------------------------------------
# Internal augmented integrations
# -----------------------------------------------------------------------------

def _integrate_augmented_simple(
    problem: BoundaryProblem,
    z: NDArray[np.float64],
    cfg: ContinuationConfig,
    counters: Optional[dict] = None,
):
    y0 = _initial_augmented_state(problem, z, include_tau_derivatives=False)
    def guarded_rhs(t, y, mu):
        if cfg.integration_guard is not None:
            cfg.integration_guard()
        return _rhs_augmented_simple(t, y, mu)

    sol = solve_ivp(
        guarded_rhs,
        (0.0, problem.tof),
        y0,
        args=(problem.mu,),
        method=cfg.method_internal,
        rtol=cfg.rtol,
        atol=cfg.atol,
    )
    _update_counters(sol, counters)
    if (not sol.success) and cfg.raise_on_internal_failure:
        raise RuntimeError(sol.message)
    return sol


def _integrate_augmented_gravity(
    problem: BoundaryProblem,
    z: NDArray[np.float64],
    tau: float,
    mu0: float,
    cfg: ContinuationConfig,
    counters: Optional[dict] = None,
):
    y0 = _initial_augmented_state(problem, z, include_tau_derivatives=True)
    mu_t = _mu_tau(float(tau), mu0, problem.mu)
    vel_scale = np.sqrt(mu_t / problem.mu)
    y0[3:6] = problem.v0 * vel_scale
    y0[87:90] = _velocity_scale_derivative(float(tau), mu0, problem.mu) * problem.v0
    sol = solve_ivp(
        _rhs_augmented_gravity,
        (0.0, problem.tof),
        y0,
        args=(float(tau), float(mu0), float(problem.mu)),
        method=cfg.method_internal,
        rtol=cfg.rtol,
        atol=cfg.atol,
    )
    _update_counters(sol, counters)
    if (not sol.success) and cfg.raise_on_internal_failure:
        raise RuntimeError(sol.message)
    return sol


def _initial_augmented_state(problem: BoundaryProblem, z: NDArray[np.float64], include_tau_derivatives: bool) -> NDArray[np.float64]:
    n = 96 if include_tau_derivatives else 84
    y0 = np.zeros(n, dtype=float)
    y0[0:3] = problem.r0
    y0[3:6] = problem.v0
    y0[6:9] = z[:3]       # pv0
    y0[9:12] = z[3:6]     # d(pv)/dt at t0 = -pr0

    # Variations wrt z = [pv0, pv_dot0]
    # dr/dz, dv/dz are initially zero.
    # dpv/dpv0 = I; d(pv_dot)/d(pv_dot0) = I.
    dpvdz0 = np.zeros((3, 6), dtype=float)
    dpvdz0[:, 0:3] = np.eye(3)
    ddpvdzdt0 = np.zeros((3, 6), dtype=float)
    ddpvdzdt0[:, 3:6] = np.eye(3)
    y0[48:66] = dpvdz0.reshape(-1)
    y0[66:84] = ddpvdzdt0.reshape(-1)
    return y0


def _rhs_augmented_simple(t: float, y: NDArray[np.float64], mu: float) -> NDArray[np.float64]:
    res = np.zeros_like(y)
    r = y[0:3]
    v = y[3:6]
    pv = y[6:9]
    pvdot = y[9:12]

    drdz = y[12:30].reshape(3, 6)
    dvdz = y[30:48].reshape(3, 6)
    dpvdz = y[48:66].reshape(3, 6)
    dpvdotdz = y[66:84].reshape(3, 6)

    g = gravity_accel(r, mu=mu)
    H = gravity_hessian(r, mu=mu)
    Jhpv = gravity_hessian_action_jacobian(r, pv, mu=mu)

    res[0:3] = v
    res[3:6] = g + pv
    res[6:9] = pvdot
    res[9:12] = H @ pv

    res[12:30] = dvdz.reshape(-1)
    res[30:48] = (H @ drdz + dpvdz).reshape(-1)
    res[48:66] = dpvdotdz.reshape(-1)
    res[66:84] = (Jhpv @ drdz + H @ dpvdz).reshape(-1)
    return res


def _rhs_augmented_gravity(t: float, y: NDArray[np.float64], tau: float, mu0: float, mu: float) -> NDArray[np.float64]:
    res = np.zeros_like(y)
    r = y[0:3]
    v = y[3:6]
    pv = y[6:9]
    pvdot = y[9:12]

    drdz = y[12:30].reshape(3, 6)
    dvdz = y[30:48].reshape(3, 6)
    dpvdz = y[48:66].reshape(3, 6)
    dpvdotdz = y[66:84].reshape(3, 6)

    r_tau = y[84:87]
    v_tau = y[87:90]
    pv_tau = y[90:93]
    pvdot_tau = y[93:96]

    mu_t = _mu_tau(tau, mu0, mu)
    scale = mu_t / mu
    dscale_dtau = (mu - mu0) / mu

    g_unit = gravity_accel(r, mu=1.0)
    H_unit = gravity_hessian(r, mu=1.0)
    Jhpv_unit = gravity_hessian_action_jacobian(r, pv, mu=1.0)

    res[0:3] = v
    res[3:6] = scale * g_unit + pv
    res[6:9] = pvdot
    res[9:12] = scale * H_unit @ pv

    res[12:30] = dvdz.reshape(-1)
    res[30:48] = (scale * H_unit @ drdz + dpvdz).reshape(-1)
    res[48:66] = dpvdotdz.reshape(-1)
    res[66:84] = (scale * (Jhpv_unit @ drdz + H_unit @ dpvdz)).reshape(-1)

    # Derivatives wrt continuation parameter tau.
    res[84:87] = v_tau
    res[87:90] = dscale_dtau * g_unit + scale * H_unit @ r_tau + pv_tau
    res[90:93] = pvdot_tau
    res[93:96] = dscale_dtau * H_unit @ pv + scale * (Jhpv_unit @ r_tau + H_unit @ pv_tau)
    return res


# -----------------------------------------------------------------------------
# Dynamics: central Newtonian field
# -----------------------------------------------------------------------------

def gravity_accel(r: ArrayLike, mu: float = 1.0) -> NDArray[np.float64]:
    """Central gravitational acceleration: -mu r / |r|^3."""

    r = _vec3(r, "r")
    rn = np.linalg.norm(r)
    if rn == 0:
        raise ValueError("gravity_accel undefined at r=0")
    return -mu * r / rn**3


def gravity_hessian(r: ArrayLike, mu: float = 1.0) -> NDArray[np.float64]:
    """Jacobian of gravity_accel wrt r."""

    r = _vec3(r, "r")
    rn = np.linalg.norm(r)
    if rn == 0:
        raise ValueError("gravity_hessian undefined at r=0")
    I = np.eye(3)
    return mu * (-I / rn**3 + 3.0 * np.outer(r, r) / rn**5)


def gravity_hessian_action_jacobian(r: ArrayLike, pv: ArrayLike, mu: float = 1.0) -> NDArray[np.float64]:
    """Jacobian wrt r of H(r) @ pv, where H is gravity_hessian."""

    r = _vec3(r, "r")
    pv = _vec3(pv, "pv")
    rn = np.linalg.norm(r)
    if rn == 0:
        raise ValueError("gravity_hessian_action_jacobian undefined at r=0")
    rp = float(np.dot(r, pv))
    I = np.eye(3)
    return mu * (
        3.0 * np.outer(pv, r) / rn**5
        + 3.0 * I * rp / rn**5
        + 3.0 * np.outer(r, pv) / rn**5
        - 15.0 * np.outer(r, r) * rp / rn**7
    )


# -----------------------------------------------------------------------------
# Branch/mu0 helper
# -----------------------------------------------------------------------------

def mu0_for_branch(
    r0: ArrayLike,
    v0: ArrayLike,
    rf: ArrayLike,
    tof: float,
    branch_n: int,
    mu: float = 1.0,
) -> float:
    """Compute artificial mu0 for a passive branch with N full revolutions.

    This implements the lecture formula

        mu0 = a0^3 * ((2*pi*N + Mf - M0) / tof)^2.

    The final true anomaly is obtained by projecting rf to the initial orbital
    plane and measuring the positive angular distance from r0 along the initial
    direction of motion. For nearly circular initial orbits this is the most
    stable convention.
    """

    if branch_n < 0:
        raise ValueError("branch_n must be non-negative")
    r0 = _vec3(r0, "r0")
    v0 = _vec3(v0, "v0")
    rf = _vec3(rf, "rf")
    if tof <= 0:
        raise ValueError("tof must be positive")

    a0, e, hhat, p_hat, q_hat = _initial_orbit_frame(r0, v0, mu)
    theta0 = _true_anomaly_in_frame(r0, p_hat, q_hat)
    rf_proj = rf - np.dot(rf, hhat) * hhat
    if np.linalg.norm(rf_proj) < 1e-14:
        raise ValueError("rf projection to initial orbital plane is degenerate")
    theta_f_direct = _positive_angle_from_to(r0, rf_proj, hhat)
    theta_f = theta0 + theta_f_direct

    M0 = _mean_anomaly_from_true(theta0, e)
    Mf = _mean_anomaly_from_true(theta_f, e)
    delta_M = 2.0 * np.pi * int(branch_n) + (Mf - M0)
    if delta_M <= 0:
        delta_M += 2.0 * np.pi
    return float(a0**3 * (delta_M / tof) ** 2)


def _initial_orbit_frame(r: NDArray[np.float64], v: NDArray[np.float64], mu: float):
    rn = np.linalg.norm(r)
    vn2 = float(np.dot(v, v))
    energy = 0.5 * vn2 - mu / rn
    if abs(energy) < 1e-14:
        raise ValueError("parabolic initial orbit is not supported for mu0 branch helper")
    a = -mu / (2.0 * energy)
    if a <= 0:
        raise ValueError("hyperbolic initial orbit is not supported for mu0 branch helper")

    h = np.cross(r, v)
    hn = np.linalg.norm(h)
    if hn < 1e-14:
        raise ValueError("degenerate initial angular momentum")
    hhat = h / hn

    evec = np.cross(v, h) / mu - r / rn
    e = float(np.linalg.norm(evec))
    if e > 1e-10:
        p_hat = evec / e
    else:
        p_hat = r / rn
    q_hat = np.cross(hhat, p_hat)
    q_hat /= np.linalg.norm(q_hat)
    return float(a), e, hhat, p_hat, q_hat


def _true_anomaly_in_frame(r: NDArray[np.float64], p_hat: NDArray[np.float64], q_hat: NDArray[np.float64]) -> float:
    return float(np.arctan2(np.dot(r, q_hat), np.dot(r, p_hat)))


def _mean_anomaly_from_true(theta: float, e: float) -> float:
    # Elliptic case only. Use robust atan2 form.
    if e < 1e-12:
        return float(theta)
    theta_wrapped = np.arctan2(np.sin(theta), np.cos(theta))
    E = 2.0 * np.arctan2(
        np.sqrt(1.0 - e) * np.sin(theta_wrapped / 2.0),
        np.sqrt(1.0 + e) * np.cos(theta_wrapped / 2.0),
    )
    M = E - e * np.sin(E)
    # Preserve the revolution count of theta.
    revolutions = np.floor((theta + np.pi) / (2.0 * np.pi))
    return float(M + revolutions * 2.0 * np.pi)


def _positive_angle_from_to(a: NDArray[np.float64], b: NDArray[np.float64], normal: NDArray[np.float64]) -> float:
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    x = float(np.dot(a, b))
    y = float(np.dot(normal, np.cross(a, b)))
    ang = float(np.arctan2(y, x))
    if ang < 0:
        ang += 2.0 * np.pi
    return ang


# -----------------------------------------------------------------------------
# Final solution summaries and refinement
# -----------------------------------------------------------------------------

def _maybe_refine(problem: BoundaryProblem, z_start: NDArray[np.float64], cfg: ContinuationConfig, simple: bool, mu0: Optional[float], counters: dict):
    if not cfg.refine:
        return z_start, 0, None, ""

    def fun(z):
        if simple:
            return evaluate_residual_and_jacobian_simple(problem, z, cfg, counters).residual
        return evaluate_residual_and_jacobian_gravity(problem, z, tau=1.0, mu0=float(mu0), cfg=cfg, counters=counters).residual

    def jac(z):
        if simple:
            return evaluate_residual_and_jacobian_simple(problem, z, cfg, counters).jacobian
        return evaluate_residual_and_jacobian_gravity(problem, z, tau=1.0, mu0=float(mu0), cfg=cfg, counters=counters).jacobian

    try:
        sol = root(fun, z_start, jac=jac, method=cfg.root_method)
    except Exception as exc:
        return z_start, 0, False, f"root failed: {exc}"
    return sol.x, int(getattr(sol, "nfev", 0)), bool(sol.success), str(sol.message)


def _evaluate_final_solution_simple(problem: BoundaryProblem, z: NDArray[np.float64], cfg: ContinuationConfig, counters: Optional[dict]):
    sol = _integrate_augmented_simple(problem, z, cfg, counters)
    y = sol.y[:, -1]
    endpoint = _endpoint_errors(problem, y, velocity_scale=1.0)
    return {"state": y, "functional": _functional_from_solution(sol), "endpoint": endpoint}


def _evaluate_final_solution_gravity(problem: BoundaryProblem, z: NDArray[np.float64], tau: float, mu0: float, cfg: ContinuationConfig, counters: Optional[dict]):
    sol = _integrate_augmented_gravity(problem, z, tau=tau, mu0=mu0, cfg=cfg, counters=counters)
    y = sol.y[:, -1]
    mu_t = _mu_tau(tau, mu0, problem.mu)
    endpoint = _endpoint_errors(problem, y, velocity_scale=np.sqrt(mu_t / problem.mu))
    return {"state": y, "functional": _functional_from_solution(sol), "endpoint": endpoint}


def _residual_and_jac_from_augmented(problem: BoundaryProblem, y: NDArray[np.float64], velocity_scale: float):
    r = y[0:3]
    v = y[3:6]
    pv = y[6:9]
    drdz = y[12:30].reshape(3, 6)
    dvdz = y[30:48].reshape(3, 6)
    dpvdz = y[48:66].reshape(3, 6)

    if problem.mode == TrajectoryMode.RENDEZVOUS:
        residual = np.concatenate([r - problem.rf, v - velocity_scale * problem.vf])
        jac = np.vstack([drdz, dvdz])
    else:
        residual = np.concatenate([r - problem.rf, pv])
        jac = np.vstack([drdz, dpvdz])
    return residual.astype(float), jac.astype(float)


def _endpoint_errors(problem: BoundaryProblem, y: NDArray[np.float64], velocity_scale: float) -> dict[str, float]:
    r = y[0:3]
    v = y[3:6]
    pv = y[6:9]
    out = {"r_norm": float(np.linalg.norm(r - problem.rf))}
    if problem.mode == TrajectoryMode.RENDEZVOUS:
        out["v_norm"] = float(np.linalg.norm(v - velocity_scale * problem.vf))
    else:
        out["pv_final_norm"] = float(np.linalg.norm(pv))
    return out


def _functional_from_solution(sol) -> float:
    # J = 1/2 int |a|^2 dt = 1/2 int |pv|^2 dt.
    pv = sol.y[6:9, :]
    integrand = 0.5 * np.sum(pv * pv, axis=0)
    return float(np.trapz(integrand, sol.t))


# -----------------------------------------------------------------------------
# Small utilities
# -----------------------------------------------------------------------------

def _vec3(x: ArrayLike, name: str) -> NDArray[np.float64]:
    arr = np.asarray(x, dtype=float).reshape(-1)
    if arr.size != 3:
        raise ValueError(f"{name} must have 3 elements, got shape {np.asarray(x).shape}")
    return arr.copy()


def _vec6(x: ArrayLike, name: str) -> NDArray[np.float64]:
    arr = np.asarray(x, dtype=float).reshape(-1)
    if arr.size != 6:
        raise ValueError(f"{name} must have 6 elements, got shape {np.asarray(x).shape}")
    return arr.copy()


def _mu_tau(tau: float, mu0: float, mu: float) -> float:
    return float(mu0 + (mu - mu0) * tau)


def _velocity_scale_derivative(tau: float, mu0: float, mu: float) -> float:
    mu_t = _mu_tau(tau, mu0, mu)
    return float(0.5 * np.sqrt(mu / mu_t) * (1.0 - mu0 / mu))


def _solve_linear(A: NDArray[np.float64], b: NDArray[np.float64]) -> NDArray[np.float64]:
    try:
        return np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return np.linalg.lstsq(A, b, rcond=None)[0]


def _update_counters(sol, counters: Optional[dict]) -> None:
    if counters is None:
        return
    counters["internal_integrations"] = counters.get("internal_integrations", 0) + 1
    counters["internal_nfev_total"] = counters.get("internal_nfev_total", 0) + int(getattr(sol, "nfev", 0))


class _ExternalContinuationSolution:
    """Minimal OdeResult-like object for fixed-step external integrators."""

    def __init__(self, t, y, success=True, message="", nfev=0):
        self.t = np.asarray(t, dtype=float)
        self.y = np.asarray(y, dtype=float)
        self.success = bool(success)
        self.message = str(message)
        self.nfev = int(nfev)


def _tau_nodes_from_config(cfg: ContinuationConfig) -> NDArray[np.float64]:
    if cfg.t_eval_tau is not None:
        nodes = np.asarray(cfg.t_eval_tau, dtype=float).reshape(-1)
    else:
        t0, t1 = cfg.tau_span
        n = max(1, int(cfg.external_fixed_steps))
        nodes = np.linspace(float(t0), float(t1), n + 1)
    if nodes.size < 2:
        t0, t1 = cfg.tau_span
        nodes = np.array([float(t0), float(t1)], dtype=float)
    if np.any(np.diff(nodes) <= 0):
        raise ValueError("tau nodes must be strictly increasing")
    return nodes


def _integrate_external_continuation(rhs, z0: NDArray[np.float64], cfg: ContinuationConfig):
    """Integrate the external continuation equation.

    Adaptive ``solve_ivp`` may take hundreds of RHS calls for this problem; each
    RHS call contains a full internal augmented integration. For dissertation
    benchmarking and debugging this is usually undesirable. Therefore the module
    supports fixed-step external RK4/Euler, which keeps the cost explicit:
    ``external_nfev`` equals 4 times the number of tau intervals for RK4.
    """

    method = str(cfg.method_external).upper()
    if method not in {"RK4_FIXED", "FIXED_RK4", "EULER_FIXED", "FIXED_EULER"}:
        sol = solve_ivp(
            rhs,
            cfg.tau_span,
            z0,
            method=cfg.method_external,
            rtol=cfg.rtol,
            atol=cfg.atol,
            t_eval=cfg.t_eval_tau,
            max_step=np.inf if cfg.max_step_tau is None else cfg.max_step_tau,
        )
        # If LSODA fails before producing a dense ndarray, keep a normal shape.
        if not isinstance(sol.y, np.ndarray) or np.asarray(sol.y).ndim != 2 or np.asarray(sol.y).size == 0:
            sol.y = np.asarray(z0, dtype=float).reshape(-1, 1)
            sol.t = np.array([float(cfg.tau_span[0])], dtype=float)
        return sol

    nodes = _tau_nodes_from_config(cfg)
    z = np.asarray(z0, dtype=float).copy()
    path = [z.copy()]
    nfev = 0

    for a, b in zip(nodes[:-1], nodes[1:]):
        h = float(b - a)
        if method in {"EULER_FIXED", "FIXED_EULER"}:
            z = z + h * rhs(float(a), z)
            nfev += 1
        else:
            k1 = rhs(float(a), z)
            k2 = rhs(float(a + 0.5*h), z + 0.5*h*k1)
            k3 = rhs(float(a + 0.5*h), z + 0.5*h*k2)
            k4 = rhs(float(b), z + h*k3)
            z = z + (h/6.0) * (k1 + 2.0*k2 + 2.0*k3 + k4)
            nfev += 4
        if not np.all(np.isfinite(z)):
            return _ExternalContinuationSolution(
                nodes[:len(path)],
                np.asarray(path).T,
                success=False,
                message="fixed external integration produced non-finite z",
                nfev=nfev,
            )
        path.append(z.copy())

    return _ExternalContinuationSolution(
        nodes,
        np.asarray(path, dtype=float).T,
        success=True,
        message="fixed-step external continuation reached tau_span end",
        nfev=nfev,
    )

# -----------------------------------------------------------------------------
# Debug helpers for the external continuation integration
# -----------------------------------------------------------------------------

def _record_debug_point(
    debug_trace: list[dict],
    cfg: ContinuationConfig,
    method: str,
    tau: float,
    z: NDArray[np.float64],
    ev: _EvalResult,
    dzdtau: NDArray[np.float64],
) -> None:
    """Store/print the first distinct external RHS evaluations.

    This is intentionally attached to the external integrator, not to the root
    refinement.  It is meant to verify the two-level continuation mechanism:
    one external RHS call equals one internal augmented integration plus one
    linear solve for dz/dtau.
    """

    if not cfg.debug:
        return

    # Keep only first distinct tau values. solve_ivp often evaluates RHS several
    # times at exactly tau=0; these duplicates are not useful for diagnostics.
    for row in debug_trace:
        if abs(float(row["tau"]) - tau) <= cfg.debug_tau_unique_tol:
            return

    if len(debug_trace) >= cfg.debug_first_unique_taus:
        return

    try:
        cond_jac = float(np.linalg.cond(ev.jacobian))
    except Exception:
        cond_jac = float("nan")

    row = {
        "method": method,
        "tau": float(tau),
        "z": np.asarray(z, dtype=float).copy(),
        "residual_norm": float(np.linalg.norm(ev.residual)),
        "dfdtau_norm": float(np.linalg.norm(ev.dfdtau)),
        "jac_cond": cond_jac,
        "dzdtau_norm": float(np.linalg.norm(dzdtau)),
        "functional": float(ev.functional),
    }
    debug_trace.append(row)

    if cfg.debug_print:
        print(
            f"[continuation-debug:{method}] external RHS #{len(debug_trace)}: "
            f"tau={row['tau']:.16g}, "
            f"||f||={row['residual_norm']:.6e}, "
            f"||df/dtau||={row['dfdtau_norm']:.6e}, "
            f"cond(df/dz)={row['jac_cond']:.6e}, "
            f"||dz/dtau||={row['dzdtau_norm']:.6e}"
        )
        print(f"    z = {np.array2string(row['z'], precision=6, suppress_small=False)}")


def _debug_print_accepted_points(cfg: ContinuationConfig, method: str, sol_tau) -> None:
    """Print the first two accepted external integration points."""

    if not (cfg.debug and cfg.debug_print):
        return

    if getattr(sol_tau, "t", None) is None or getattr(sol_tau, "y", None) is None:
        return

    n = min(2, len(sol_tau.t))
    print(f"[continuation-debug:{method}] first accepted external points:")
    for idx in range(n):
        z = sol_tau.y[:, idx]
        print(
            f"    accepted[{idx}]: tau={float(sol_tau.t[idx]):.16g}, "
            f"z={np.array2string(z, precision=6, suppress_small=False)}"
        )
