"""Algebraic step from Preprint2024_7.m:31-43,175-176.

This constructs a prescribed matrix; it does NOT recover it from two BVPs.
Costates below are synthetic; no orbital integration is performed.
"""
import numpy as np

j = 0.1  # i_coef in MATLAB, not the resulting orbital inclination
omega = 0.0  # O_coef
delta = np.arctan(j)
c, s = np.cos(delta), np.sin(delta)

# Equivalent to quat2rotm for the x-axis quaternion used in MATLAB.
r_code = np.array([[1., 0., 0.], [0., c, -s], [0., s, c]])
r_code[:, 2] *= r_code[1, 1]
r_code[:, 1] *= r_code[1, 1]
np.testing.assert_allclose(
    r_code,
    [[1., 0., 0.], [0., 1 / (1 + j*j), -j / (1 + j*j)],
     [0., j / (1 + j*j), 1 / (1 + j*j)]], atol=1e-14,
)

phi = omega - np.pi
c, s = np.cos(phi), np.sin(phi)
q = np.array([[c, -s, 0.], [s, c, 0.], [0., 0., 1.]])
r_io = q @ r_code @ q.T
p_before = np.array([[1., 3.], [2., 1.], [0., 0.]])
p_after = np.linalg.solve(r_io, p_before)  # exactly the old R^(-1) action

np.set_printoptions(precision=8, suppress=True)
print("R_i0 prescribed from j:\n", r_code)
print("R_iOmega:\n", r_io)
print("P_before, columns p_r and p_v:\n", p_before)
print("P_after = solve(R_iOmega, P_before):\n", p_after)
print("Residual:", np.linalg.norm(r_io @ p_after - p_before))

# To express the same numerical action in dissertation notation:
r_text = r_io.T
np.testing.assert_allclose(np.linalg.solve(r_text.T, p_before), p_after)
