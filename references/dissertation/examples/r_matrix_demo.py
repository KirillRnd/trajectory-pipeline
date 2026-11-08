"""Six linear equations for nine entries of A = R^{-T}.

Synthetic algebraic example, not a numerical solution of the orbital BVP.
Run: python examples/r_matrix_demo.py   (requires NumPy)
Optional structured completion and noise study: add --structured
"""

import argparse

import numpy as np


def recover(p1, p2):
    """p1, p2: (3, 2) arrays, columns are p_r and p_v.

    p1 must be planar in Oxy. The third column of A is chosen as
    cross(A[:, 0], A[:, 1]); this enforces the structure of equation (8).
    """
    p1, p2 = np.asarray(p1, dtype=float), np.asarray(p2, dtype=float)
    if p1.shape != (3, 2) or p2.shape != (3, 2):
        raise ValueError("Expected two (3, 2) matrices.")
    if not np.isfinite(p1).all() or not np.isfinite(p2).all():
        raise ValueError("Costates must be finite.")
    if np.any(p1[2] != 0):
        raise ValueError("This demonstration assumes an exactly planar source.")
    b = p1[:2].T  # rows: (p_rx, p_ry), (p_vx, p_vy)
    if np.linalg.matrix_rank(b) < 2:
        raise ValueError("The two source costates are linearly dependent.")
    if np.linalg.matrix_rank(p2) < 2:
        raise ValueError("No invertible map to dependent target costates.")

    # Three 2x2 systems, one for each output coordinate.
    ab = np.linalg.solve(b, p2.T).T
    a = np.column_stack((ab, np.cross(ab[:, 0], ab[:, 1])))
    r = np.linalg.solve(a.T, np.eye(3))
    return a, r, np.linalg.cond(b)


def structured_demo():
    np.set_printoptions(precision=8, suppress=True)
    p1 = np.array([[1., 3.], [2., 1.], [0., 0.]])
    j = 0.1  # matrix parameter, NOT the final orbital inclination i
    a_exact = np.array([[1., 0., 0.], [0., 1., -j], [0., j, 1.]])
    p2 = a_exact @ p1
    a, r, cond = recover(p1, p2)
    print("Synthetic costates, columns p_r and p_v:")
    print("P1 =\n", p1, "\nP2 =\n", p2)
    print("Recovered A = R^(-T):\n", a)
    print("Recovered R:\n", r)
    print(f"cond_2(B) = {cond:.6f}")
    print(f"||A P1 - P2||_F = {np.linalg.norm(a @ p1 - p2):.3e}")
    print(f"||R[:,2] - cross(R[:,0],R[:,1])|| = "
          f"{np.linalg.norm(r[:, 2] - np.cross(r[:, 0], r[:, 1])):.3e}")
    np.testing.assert_allclose(a, a_exact, atol=1e-14)
    np.testing.assert_allclose(np.linalg.solve(r.T, p1), p2, atol=1e-14)
    np.testing.assert_allclose(r[:, 2], np.cross(r[:, 0], r[:, 1]), atol=1e-14)

    # Without the cross-product condition, the third column is unconstrained.
    a_other = a.copy()
    a_other[:, 2] += [0.3, -0.2, 0.5]
    np.testing.assert_allclose(a_other @ p1, p2, atol=1e-14)
    print("A second, different invertible A has the same action on P1:")
    print(a_other)
    print(f"det(A_other) = {np.linalg.det(a_other):.6f}")

    # Fixed absolute noise; source matrix B and its condition number stay fixed.
    noise = 1e-10 * np.array([[1., -1.], [-0.5, 0.7], [0.3, -0.8]])
    print("\nSmall deformation with fixed absolute target noise:")
    print("j          cond(B)     abs_error_A  error/||A-I||  abs_error_R")
    for j in (1e-1, 1e-3, 1e-5, 1e-7, 1e-9):
        a_true = np.array([[1., 0., 0.], [0., 1., -j], [0., j, 1.]])
        r_true = np.linalg.solve(a_true.T, np.eye(3))
        a_fit, r_fit, cond = recover(p1, a_true @ p1 + noise)
        err = np.linalg.norm(a_fit - a_true)
        rel_change = err / np.linalg.norm(a_true - np.eye(3))
        print(f"{j:9.1e}  {cond:9.3e}  {err:11.3e}  {rel_change:13.3e}  "
              f"{np.linalg.norm(r_fit - r_true):11.3e}")

    # Actual ill-conditioning: source costates become nearly parallel.
    print("\nNearly parallel source costates (a separate mechanism):")
    print("delta      cond(B)     abs_error_A")
    for delta in (1., 1e-2, 1e-4, 1e-6):
        source = np.array([[1., 1.], [0., delta], [0., 0.]])
        a_fit, _, cond = recover(source, a_exact @ source + noise)
        print(f"{delta:9.1e}  {cond:9.3e}  "
              f"{np.linalg.norm(a_fit - a_exact):11.3e}")


def main():
    np.set_printoptions(precision=6, suppress=True)
    # Each column is one 3D costate: position, then velocity.
    p1 = np.array([[1., 3.], [2., 1.], [0., 0.]])
    p2 = np.array([[1., 3.], [2., 1.], [0.2, 0.1]])

    # Unknowns ordered by rows: a11, a12, a13, a21, ..., a33.
    # Equation order: A p_r = p_r_target, then A p_v = p_v_target.
    m = np.vstack([np.kron(np.eye(3), p1[:, k]) for k in range(2)])
    rhs = p2.T.reshape(-1)
    solution, _, rank, _ = np.linalg.lstsq(m, rhs, rcond=None)
    a0 = solution.reshape(3, 3)
    print("Full system M vec_rows(A) = b:")
    print("M =\n", m, "\nb =", rhs)
    print(f"Shape: {m.shape}; rank: {rank}; free parameters: {9 - rank}")
    print("Minimum-norm solution (singular in this planar example):\n", a0)
    print("All solutions: A = [[1,0,c1],[0,1,c2],[0,0.1,c3]]")
    print("Invertibility condition: c3 - 0.1*c2 != 0")
    assert rank == 6
    np.testing.assert_allclose(a0 @ p1, p2, atol=1e-14)
    assert np.linalg.matrix_rank(a0) == 2

    # Two arbitrary choices of the free third column, both invertible.
    for c in ([0., 0., 1.], [1., 2., 3.]):
        a = a0.copy()
        a[:, 2] = c
        r = np.linalg.solve(a.T, np.eye(3))
        residual = np.linalg.norm(a @ p1 - p2)
        print("\nA =\n", a)
        print(f"det(A) = {np.linalg.det(a):.6f}; residual = {residual:.3e}")
        np.testing.assert_allclose(a @ p1, p2, atol=1e-14)
        np.testing.assert_allclose(r.T @ p2, p1, atol=1e-14)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structured", action="store_true")
    if parser.parse_args().structured:
        print("\nOPTIONAL: extra cross-product constraint, not implied by M a = b")
        structured_demo()


if __name__ == "__main__":
    main()
