"""Real stored cases and observed ephemerides; no optimizer training fixtures."""
from pathlib import Path
import json
import tempfile
import unittest
import numpy as np
from trajectory_pipeline.data import Trajectory, Scales, AU_M, MU_SUN
from trajectory_pipeline.ephemerides import Ephemerides, parse_horizons
from trajectory_pipeline.reference import import_ummp

ROOT = Path(__file__).resolve().parents[1]


class FoundationTests(unittest.TestCase):
    def test_reference_matches_saved_mat_and_roundtrips(self):
        t = import_ummp(ROOT/'data/references/apophis_ummp_156kg_hard_bangbang_verified.mat')
        self.assertEqual(len(t.arrays['t_s']), 1655)
        self.assertAlmostEqual(t.arrays['mass_kg'][-1], 156-34.66762796734692)
        self.assertEqual(np.count_nonzero(np.diff(t.arrays['active'].astype(int)) == 1), 3)
        with tempfile.TemporaryDirectory() as tmp:
            path = t.save(Path(tmp)/'result')
            loaded = Trajectory.load(path)
            np.testing.assert_array_equal(loaded.arrays['r_m'], t.arrays['r_m'])
            np.testing.assert_array_equal(loaded.arrays['legacy_costates'], t.arrays['legacy_costates'])

    def test_reference_integrity_guard(self):
        t = Trajectory.load(ROOT/'data/references/ummp156')
        with tempfile.TemporaryDirectory() as tmp:
            path = t.save(Path(tmp)/'result')
            with (path/'trajectory.npz').open('ab') as f:
                f.write(b'changed')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                Trajectory.load(path)

    def test_scales_roundtrip_real_trajectory(self):
        t = Trajectory.load(ROOT/'data/references/ummp156')
        scales = Scales(AU_M, MU_SUN)
        state = np.c_[t.arrays['r_m'], t.arrays['v_m_s']]
        np.testing.assert_allclose(scales.dimensional_state(scales.normalize_state(state)), state, rtol=2e-16, atol=1e-4)

    def test_eight_asteroids_against_withheld_horizons_epochs(self):
        eph = Ephemerides()
        folder = ROOT/'data/ephemerides/validation'
        for body in ('apophis','eros','bennu','ryugu','polyhymnia','ceres','2015re36','vesta'):
            with self.subTest(body=body):
                j, s = parse_horizons((folder/f'{body}_horizons.txt').read_text(encoding='utf-8'))
                prediction = eph.state(body, j)
                self.assertLess(np.linalg.norm(prediction[:,:3]-s[:,:3],axis=1).max(), 20.)
                self.assertLess(np.linalg.norm(prediction[:,3:]-s[:,3:],axis=1).max(), .001)

    def test_local_planet_centers_jupiter_saturn(self):
        for body,position,velocity in (('Jupiter',50.,.006),('Saturn',20.,.001)):
            with self.subTest(body=body):
                j, s = parse_horizons((ROOT/f'data/ephemerides/validation/{body.lower()}_horizons.txt').read_text(encoding='utf-8'))
                prediction = Ephemerides().state(body, j)
                self.assertLess(np.linalg.norm(prediction[:,:3]-s[:,:3],axis=1).max(),position)
                self.assertLess(np.linalg.norm(prediction[:,3:]-s[:,3:],axis=1).max(),velocity)

    def test_major_bodies_local_and_moon_center_consistency(self):
        eph = Ephemerides()
        epochs = [2461771.5,2462240.5,2463232.5]
        for body in ('mercury','venus','earth','moon','mars','saturn','uranus','neptune','pluto'):
            self.assertTrue(np.isfinite(eph.state(body, epochs)).all(), body)
        moon = eph.state('Moon', epochs, 'Earth')
        distances = np.linalg.norm(moon[:,:3],axis=1)
        self.assertTrue(np.all((distances > 3.4e8) & (distances < 4.1e8)))
        np.testing.assert_allclose(moon, eph.state('Moon',epochs)-eph.state('Earth',epochs), atol=0)

    def test_extrapolation_is_available_with_derivative_velocity(self):
        eph = Ephemerides()
        for body,epoch in [('Apophis',eph.coverage('Apophis')['start_jd']-.01),
                           ('Vesta',eph.coverage('Vesta')['stop_jd']+.01),
                           ('Moon',eph.coverage('Moon')['start_jd']-.5),
                           ('Moon',eph.coverage('Moon')['stop_jd']+.5)]:
            state=eph.state(body,epoch)
            self.assertTrue(np.isfinite(state).all())
            self.assertTrue(eph.evaluation_record(body,epoch)['extrapolated'])
            times=np.array([epoch-.001,epoch+.001]);states=eph.state(body,times)
            derivative=(states[1,:3]-states[0,:3])/((times[1]-times[0])*86400)
            np.testing.assert_allclose(derivative,state[3:],rtol=1e-6,atol=.05)


if __name__ == '__main__':
    unittest.main()
