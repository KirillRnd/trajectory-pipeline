import unittest

import numpy as np
from numpy.testing import assert_allclose

from trajectory_pipeline.r_transform import (
    costate_chart, orbital_frame, transport_costates, transport_matrix, transport_vector,
)


class RTransformTests(unittest.TestCase):
    def test_legacy_maps_both_phase_vectors_and_preserves_dual_pairing(self):
        old = np.array([1., .3, -.1, .2, 1.1, .2])
        new = np.array([.7, .6, .3, -.3, 1.2, .2])
        adjoint = np.array([.1, .3, -.2, -.9, .2, .4, .5])
        matrix = transport_matrix(old, new)
        moved = transport_costates(adjoint, matrix)
        for start in (0, 3):
            block = slice(start, start+3)
            vector = transport_vector(old[block], matrix)
            assert_allclose(vector, new[block], atol=1e-15)
            assert_allclose(moved[block]@vector, adjoint[block]@old[block], atol=1e-15)
        self.assertEqual(moved[6], adjoint[6])

    def test_chart_leaves_non_costate_unknowns_in_physical_coordinates(self):
        frame = orbital_frame([1.2, 0., 0., .2, .8, 0.], 'legacy')
        point = np.arange(9.)
        for blocks in (1, 2):
            chart = costate_chart(frame, size=len(point), blocks=blocks)
            physical = chart@point
            for start in range(0, 3*blocks, 3):
                block = slice(start, start+3)
                assert_allclose(frame@physical[block], point[block], atol=1e-15)
            assert_allclose(physical[3*blocks:], point[3*blocks:])

    def test_rtn_has_no_nonorthogonal_scaling(self):
        frame = orbital_frame([1.2, 0., 0., .2, .8, .1], 'rtn')
        assert_allclose(frame@frame.T, np.eye(3), atol=1e-15)
        with self.assertRaises(ValueError):
            orbital_frame([1., 0., 0., .2, 0., 0.])
