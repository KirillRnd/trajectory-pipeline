"""Physical angular captures, full saved Mars seam, flags and budget guards."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json
import math
import tempfile
import shutil
import unittest
import numpy as np
from trajectory_pipeline.planetary_capture import CaptureOrbit,backward_capture,forward_capture
from trajectory_pipeline.capture_control import apply_capture_flags,capture_budget_check
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.orbital_pipeline import verify_orbital_mission
from trajectory_pipeline.data import write_json

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'data/benchmarks/angular_capture_v1/mars_fixed'


class AngularCaptureTests(unittest.TestCase):
    def test_independent_physical_replay_and_mass_flow(self):
        cases=[(CaptureOrbit(4.2828375662e13,3396190.,400e3,30000e3,577230383.942),60.,.04,16000.,2.7),
               (CaptureOrbit(6.26325e10,469700.,100e3,3000e3,75e6),60.,.002,16000.,2.)]
        for orbit,mass,force,exhaust,width in cases:
            b=backward_capture(orbit,mass,force,exhaust,control={'mode':'angular','half_width_rad':width})
            f=forward_capture(orbit,b['relative_state_si'][0],b['entry_mass_kg'],force,exhaust,b['burn_start_s'],b['duration_s'],
                              control=b['control'],reference_axis=b['reference_axis'],sample_times=b['t_s'])
            indices=np.searchsorted(f['t_s'],b['t_s'])
            self.assertLess(np.linalg.norm(f['relative_state_si'][indices,:3]-b['relative_state_si'][:,:3],axis=1).max(),100.)
            self.assertLess(np.linalg.norm(f['relative_state_si'][indices,3:]-b['relative_state_si'][:,3:],axis=1).max(),.01)
            self.assertLess(abs(f['mass_kg'][-1]-mass),1e-6)
            self.assertLess(abs(b['entry_mass_kg']-mass-force/exhaust*b['active_duration_s']),1e-6)
            self.assertEqual(len(b['arcs']),len(f['arcs']))
            self.assertGreater(len(b['arcs']),3)
            self.assertLess(b['active_duration_s'],b['duration_s'])

    def test_full_mars_stitch_and_budget(self):
        check=verify_orbital_mission(ARCHIVE)
        self.assertTrue(check['passed'])
        self.assertTrue(check['capture_budget']['passed'])
        self.assertLess(check['arrival_join']['velocity_error_m_s'],1e-8)
        self.assertLess(check['arrival_join']['mass_error_kg'],1e-6)
        self.assertLess(check['time_error_s'],1e-4)
        self.assertAlmostEqual(check['total_spacecraft_propellant_kg'],sum(check[k] for k in
                               ('departure_propellant_kg','interplanetary_propellant_kg','arrival_propellant_kg')),places=6)

    def test_cli_flags_are_saved_as_physical_configuration(self):
        m=Mission.load(ROOT/'configs/orbital_modes/mars_impulse_spiral_dry60.json')
        flags=SimpleNamespace(capture_mode='angular',capture_half_width_deg=120.,capture_search_widths_deg=[100.,120.],capture_fuel_budget_kg=6.,spacecraft_fuel_budget_kg=40.,capture_max_days=1800.)
        new=apply_capture_flags(m,flags);a=new.orbital_maneuvers['arrival']
        self.assertAlmostEqual(a['capture_control']['half_width_rad'],2*math.pi/3)
        self.assertEqual(a['arrival_propellant_budget_kg'],6.)
        self.assertNotIn('capture_control',m.orbital_maneuvers['arrival'])
        self.assertTrue(capture_budget_check(a,156.,130.,125.,1000*86400)['passed'])
        self.assertFalse(capture_budget_check(a,156.,130.,123.,1000*86400)['passed'])
        self.assertFalse(capture_budget_check(a,156.,115.,110.,1000*86400)['passed'])
        self.assertFalse(capture_budget_check(a,156.,130.,125.,1900*86400)['passed'])
        with self.assertRaises(ValueError):apply_capture_flags(m,SimpleNamespace(capture_mode='continuous',capture_half_width_deg=120.))
        with self.assertRaises(ValueError):apply_capture_flags(m,SimpleNamespace(capture_mode='angular',capture_search_widths_deg=[120.]))

    def test_duration_limit_reports_a_local_failure(self):
        orbit=CaptureOrbit(4.2828375662e13,3396190.,400e3,30000e3,577230383.942)
        with self.assertRaisesRegex(RuntimeError,'capture_duration_limit'):
            backward_capture(orbit,90.,.025,20000.,control={'mode':'angular','half_width_rad':2.},max_days=10.)

    def test_metadata_cannot_relabel_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            for name in ('mission.json','request.json','outer_request.json','impulses.json'):shutil.copy2(ARCHIVE/name,p/name)
            for name in ('departure','outer','arrival','final'):shutil.copytree(ARCHIVE/name,p/name)
            meta=json.loads((p/'arrival/trajectory.json').read_text());meta['maneuver']['control']['half_width_rad']=2.4
            write_json(p/'arrival/trajectory.json',meta)
            with self.assertRaisesRegex(ValueError,'control differs'):verify_orbital_mission(p)
            meta=json.loads((ARCHIVE/'arrival/trajectory.json').read_text())
            meta['maneuver']['arcs'][1]['active']=not meta['maneuver']['arcs'][1]['active']
            write_json(p/'arrival/trajectory.json',meta)
            self.assertFalse(verify_orbital_mission(p)['passed'])

    def test_search_selects_verified_feasible_minimum_and_preserves_rejection(self):
        from trajectory_pipeline.capture_search import verify_capture_search
        archive=ARCHIVE.parent/'mars_search_fuel6'
        check=verify_capture_search(archive)
        self.assertTrue(check['passed'])
        self.assertEqual(check['feasible_count'],2)
        self.assertEqual(check['selected_folder'],'candidates/001')
        rows=json.loads((archive/'capture_search.json').read_text())['candidates']
        self.assertEqual(rows[2]['stop_kind'],'capture_budget_constraint')
        self.assertLess(rows[1]['duration_s'],rows[0]['duration_s'])


if __name__=='__main__':unittest.main()
