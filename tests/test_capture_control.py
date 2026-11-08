import math
import unittest
import numpy as np
from trajectory_pipeline.capture_control import CaptureControl


class CaptureControlTests(unittest.TestCase):
    def test_elliptical_mars_and_venus_orbits(self):
        for mu, radius in [(4.282837e13, 3389500.), (3.24859e14, 6051800.)]:
            rp, ra = radius + 400e3, radius + 30000e3
            a = (rp + ra) / 2
            peri = np.array([rp, 0, 0, 0, math.sqrt(mu*(2/rp-1/a)), 0])
            apo = np.array([-ra, 0, 0, 0, -math.sqrt(mu*(2/ra-1/a)), 0])
            policy = CaptureControl(mode='angular', half_width_rad=math.pi/2)
            self.assertEqual(policy.throttle(peri, mu, [1, 0, 0]), 1)
            self.assertEqual(policy.throttle(apo, mu, [1, 0, 0]), 0)
            rotation = np.array([[0., -1, 0], [0, 0, 1], [-1, 0, 0]])
            for state in (peri, apo):
                rotated = np.r_[rotation @ state[:3], rotation @ state[3:]]
                self.assertAlmostEqual(policy.margin(state, mu, [1, 0, 0]), policy.margin(rotated, mu, rotation @ np.array([1, 0, 0])))

    def test_explicit_fixed_axis_and_affine_width(self):
        mu, r = 4.282837e13, 4e6
        state = np.array([0, r, 0, -math.sqrt(mu/r), 0, 0])
        control = CaptureControl(mode='angular', phase_reference='fixed_axis', half_width_rad=.4)
        self.assertEqual(control.throttle(state, mu, [1, 0, 0]), 0)
        self.assertEqual(control.throttle(state, mu, [0, 1, 0]), 1)
        affine = CaptureControl(mode='angular', half_width_rad=2., eccentricity_slope_rad=4.)
        eccentric = np.array([r, 0, 0, 0, math.sqrt(1.7*mu/r), 0])
        with self.assertRaisesRegex(ValueError, 'Angular law'):
            affine.throttle(eccentric, mu, [1, 0, 0])

    def test_no_silently_unused_flags(self):
        with self.assertRaises(ValueError):
            CaptureControl(half_width_rad=1.).validate()
        with self.assertRaises(ValueError):
            CaptureControl(mode='legacy_2').validate()


if __name__ == '__main__':
    unittest.main()
