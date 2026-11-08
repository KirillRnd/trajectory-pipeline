"""Real departure vectors, configurable orbit height and finite SOI matching."""
from pathlib import Path
from copy import deepcopy
from dataclasses import replace
import unittest
import numpy as np
from trajectory_pipeline.data import Trajectory
from trajectory_pipeline.problem import Mission,departure_speed_limit
from trajectory_pipeline.contract import configuration_hash
from trajectory_pipeline.ephemerides import Ephemerides
from trajectory_pipeline.parking_departure import ParkingDeparture,outgoing_hyperbola,verify_outgoing
from trajectory_pipeline.launch_pipeline import verify_launch_mission

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'data/benchmarks/examples/earth_mars_2030_dec01_leo200_capture'


class ParkingDepartureTests(unittest.TestCase):
    def test_actual_end_to_end_launch_and_capture(self):
        check=verify_launch_mission(CASE)
        self.assertTrue(check['passed'])
        self.assertLess(check['join_position_error_m'],.05)
        self.assertLess(check['join_velocity_error_m_s'],1e-6)
        self.assertGreater(check['delta_v_m_s'],3300.)
        self.assertLess(check['delta_v_m_s'],3500.)

    def test_real_vectors_dates_and_two_parking_heights(self):
        baseline=Mission.load(CASE/'mission.json')
        for name in ['earth_apophis_2029','earth_bennu_2029','earth_mars_2028','earth_venus_2032']:
            old=Trajectory.load(ROOT/'data/benchmarks/psi'/name)
            planet=Ephemerides().state('Earth',old.metadata['epoch_jd'])
            velocity=old.arrays['v_m_s'][0]-planet[3:]
            for altitude in [200000.,400000.]:
                with self.subTest(name=name,altitude=altitude):
                    spec=ParkingDeparture(**dict(baseline.parking_departure,parking_altitude_m=altitude))
                    h=outgoing_hyperbola(spec,velocity,np.cross(planet[:3],planet[3:]))
                    self.assertTrue(verify_outgoing(spec,h)['passed'])
                    np.testing.assert_allclose(h['relative_state_si'][-1,3:],velocity,rtol=0,atol=1e-8)

    def test_height_is_defaulted_configurable_and_hashed(self):
        mission=Mission.load(CASE/'mission.json')
        defaulted=deepcopy(mission);defaulted.parking_departure.pop('parking_altitude_m')
        self.assertEqual(configuration_hash(mission),configuration_hash(defaulted))
        changed=replace(mission,parking_departure=dict(mission.parking_departure,parking_altitude_m=400000.))
        self.assertNotEqual(configuration_hash(mission),configuration_hash(changed))

    def test_speed_limit_uses_excess_not_interface_speed(self):
        m=Mission.load(CASE/'mission.json');s=ParkingDeparture(**m.parking_departure)
        bound=departure_speed_limit(m.to_dict())
        self.assertGreater(bound,m.vinf_max_m_s)
        self.assertAlmostEqual(bound**2-2*s.mu_m3_s2/s.interface_radius_m,m.vinf_max_m_s**2,places=6)

    def test_wrong_impulse_or_parking_orbit_is_rejected(self):
        m=Mission.load(CASE/'mission.json');s=ParkingDeparture(**m.parking_departure)
        saved=Trajectory.load(CASE/'launch');info=saved.metadata['injection']
        h=dict(info,t_s=saved.arrays['t_s'],relative_state_si=np.c_[saved.arrays['r_m'],saved.arrays['v_m_s']])
        wrong=dict(h,delta_v_m_s=h['delta_v_m_s']+10.)
        self.assertFalse(verify_outgoing(s,wrong)['passed'])
        self.assertFalse(verify_outgoing(replace(s,parking_altitude_m=400000.),h)['passed'])


if __name__=='__main__':unittest.main()
