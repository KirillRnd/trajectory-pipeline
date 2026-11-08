"""All four real mission combinations, mass references and impulse jumps."""
from pathlib import Path
from copy import deepcopy
import json
import shutil
import tempfile
import unittest
import numpy as np
from trajectory_pipeline.data import Trajectory,write_json,sha256
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.orbital_maneuvers import incoming_impulse,capture_impulse_event,validate_maneuvers
from trajectory_pipeline.orbital_pipeline import verify_orbital_mission

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'data/benchmarks/orbital_modes_v1/dry60'


class OrbitalModeTests(unittest.TestCase):
    def test_all_four_real_combinations(self):
        for dep in ('impulse','spiral'):
            for arr in ('impulse','spiral'):
                with self.subTest(departure=dep,arrival=arr):
                    p=ARCHIVE/f'mars_{dep}_{arr}_dry60'
                    c=verify_orbital_mission(p)
                    self.assertTrue(c['passed'])
                    self.assertAlmostEqual(c['initial_orbit_mass_kg'],156.)
                    expected=156. if dep=='impulse' else 108.5126429925
                    self.assertAlmostEqual(c['interplanetary_initial_mass_kg'],expected,places=6)
                    self.assertAlmostEqual(c['total_spacecraft_propellant_kg'],c['departure_propellant_kg']+c['interplanetary_propellant_kg']+c['arrival_propellant_kg'],places=6)
                    self.assertLess(c['departure_join']['velocity_error_m_s'],1e-6)
                    self.assertLess(c['arrival_join']['velocity_error_m_s'],1e-8)
                    self.assertLess(c['time_error_s'],1e-4)

    def test_arrival_uses_its_own_engine_and_full_vector(self):
        m=Mission.load(ROOT/'configs/orbital_modes/mars_impulse_impulse_dry90.json')
        a=m.orbital_maneuvers['arrival'];sol=incoming_impulse(a,130.)
        self.assertLess(float(sol['relative_state_si'][0,:3]@sol['relative_state_si'][0,3:]),0.)
        event=capture_impulse_event(sol['relative_state_si'][-1],130.,a,sol['duration_s'])
        np.testing.assert_allclose(np.asarray(event['state_after_si'])[3:]-np.asarray(event['state_before_si'])[3:],event['delta_v_vector_m_s'],rtol=0,atol=1e-12)
        self.assertAlmostEqual(event['mass_after_kg'],130.*np.exp(-event['delta_v_m_s']/3200.),places=10)
        different=capture_impulse_event(sol['relative_state_si'][-1],130.,dict(a,exhaust_velocity_m_s=6400.),sol['duration_s'])
        self.assertGreater(different['mass_after_kg'],event['mass_after_kg'])

    def test_missing_mass_reference_or_unknown_mode_is_rejected(self):
        m=Mission.load(ROOT/'configs/orbital_modes/mars_spiral_impulse_dry90.json')
        m.mass_reference=None
        with self.assertRaisesRegex(ValueError,'mass_reference'):m.validate()
        m.mass_reference='initial_orbit';m.orbital_maneuvers['arrival']['kind']='ballistic'
        with self.assertRaisesRegex(ValueError,'kind'):m.validate()

    def test_tampered_impulse_mass_time_or_vector_is_rejected_after_updating_hash(self):
        source=ARCHIVE/'mars_impulse_impulse_dry60'
        for field in ('mass_after_kg','time_s','delta_v_vector_m_s'):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)
                for name in ('mission.json','request.json','outer_request.json','impulses.json'):shutil.copy2(source/name,p/name)
                for name in ('departure','outer','arrival','final'):shutil.copytree(source/name,p/name)
                events=json.loads((p/'impulses.json').read_text())
                if field=='delta_v_vector_m_s':events[-1][field][1]+=1.
                else:events[-1][field]+=1.
                write_json(p/'impulses.json',events)
                meta=json.loads((p/'final/trajectory.json').read_text());meta['impulses_sha256']=sha256(p/'impulses.json')
                write_json(p/'final/trajectory.json',meta)
                self.assertFalse(verify_orbital_mission(p)['passed'])

    def test_tampered_engine_cannot_relabel_the_result(self):
        source=ARCHIVE/'mars_spiral_impulse_dry60'
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);shutil.copy2(source/'request.json',p/'request.json')
            mission=json.loads((source/'mission.json').read_text());mission['spacecraft']['thrust_N']*=2
            write_json(p/'mission.json',mission)
            with self.assertRaisesRegex(ValueError,'root request mismatch'):verify_orbital_mission(p)

    def test_wrong_impulsive_engine_types_are_rejected(self):
        m=Mission.load(ROOT/'configs/orbital_modes/mars_impulse_impulse_dry90.json')
        for value in (True,'3200',0.,float('nan')):
            cfg=deepcopy(m.orbital_maneuvers);cfg['arrival']['exhaust_velocity_m_s']=value
            with self.subTest(value=value),self.assertRaises(ValueError):validate_maneuvers(cfg)


if __name__=='__main__':unittest.main()
