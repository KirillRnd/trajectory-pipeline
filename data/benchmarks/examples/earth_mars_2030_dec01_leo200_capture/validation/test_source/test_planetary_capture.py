"""Real Mars capture: independent replay, hardware binding and seam rejection."""
from pathlib import Path
from dataclasses import replace
import tempfile
import shutil
import unittest
import numpy as np
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.data import Trajectory,write_json
from trajectory_pipeline.contract import configuration_hash
from trajectory_pipeline.capture_pipeline import verify_capture_mission
from trajectory_pipeline.planetary_capture import CaptureOrbit,backward_capture,forward_capture

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'data/benchmarks/examples/earth_mars_2030_dec01_capture_400x30000'


class MarsCaptureTests(unittest.TestCase):
    def test_observed_spiral_preserves_initial_bits_and_replay(self):
        from trajectory_pipeline.ephemerides import Ephemerides
        case=ROOT/'data/benchmarks/examples/earth_mars_2030_dec01_leo200_capture/match_05'
        outer=Trajectory.load(case/'outer');saved=Trajectory.load(case/'capture')
        mission=Mission.load(case/'mission.json');orbit=CaptureOrbit(**saved.metadata['orbit'])
        initial=np.r_[outer.arrays['r_m'][-1],outer.arrays['v_m_s'][-1]]-Ephemerides().state('Mars',mission.arrival_jd)
        def replay(state,mass,times):
            return forward_capture(orbit,state,mass,.025,20000.,saved.metadata['burn_start_s'],saved.metadata['duration_s'],sample_times=times)
        a=replay(initial,outer.arrays['mass_kg'][-1],saved.arrays['t_s'])
        np.testing.assert_array_equal(a['relative_state_si'][0],initial)
        b=replay(a['relative_state_si'][0],a['mass_kg'][0],a['t_s'])
        np.testing.assert_array_equal(a['relative_state_si'],b['relative_state_si'][np.searchsorted(b['t_s'],a['t_s'])])

    def test_actual_stitched_mission_replays(self):
        check=verify_capture_mission(CASE)
        self.assertTrue(check['passed'])
        self.assertLess(check['orbit_element_error_m'],1.)
        self.assertAlmostEqual(check['total_fuel_kg'],33.8940414227,places=6)

    def test_actual_capture_law_with_second_engine(self):
        mission=Mission.load(CASE/'mission.json')
        orbit=CaptureOrbit(**{k:mission.capture[k] for k in CaptureOrbit.__dataclass_fields__})
        nominal=backward_capture(orbit,120.,.05,30000.)
        replay=forward_capture(orbit,nominal['relative_state_si'][0],nominal['entry_mass_kg'],.05,30000.,nominal['burn_start_s'],nominal['duration_s'])
        self.assertLess(abs(replay['final_elements']['periapsis_radius_m']-3796190.),1.)
        self.assertLess(abs(replay['final_elements']['apoapsis_radius_m']-33396190.),1.)
        self.assertAlmostEqual(replay['mass_kg'][-1],120.,places=7)
        self.assertTrue(np.all(np.diff(500*86400+replay['t_s'])>0))

    def test_tampered_joint_velocity_and_mass_are_rejected(self):
        for key,delta in [('v_m_s',1.),('mass_kg',.1)]:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as directory:
                target=Path(directory)/'case';target.mkdir()
                for name in ('mission.json','outer_request.json'):shutil.copy2(CASE/name,target/name)
                for name in ('outer','capture'):shutil.copytree(CASE/name,target/name)
                artifact=Trajectory.load(CASE/'final');artifact.arrays[key][-1]+=delta
                artifact.save(target/'final')
                self.assertFalse(verify_capture_mission(target)['passed'])

    def test_capture_request_is_bound_and_old_identity_is_preserved(self):
        mission=Mission.load(CASE/'mission.json')
        changed=replace(mission,capture=dict(mission.capture,apoapsis_altitude_m=20000000.))
        self.assertNotEqual(configuration_hash(mission),configuration_hash(changed))
        legacy=Trajectory.load(ROOT/'data/benchmarks/examples/earth_mars_2030_dec01_500d/final')
        old=Mission(**legacy.metadata['mission'])
        self.assertNotIn('capture',old.to_dict())
        self.assertNotIn('arrival_offset_state_si',old.to_dict())
        self.assertEqual(configuration_hash(old),legacy.metadata['configuration_sha256'])


if __name__=='__main__':unittest.main()
