import json
import unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
import numpy as np
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.iltt_entry import angular_branches,resolve_date_mission
from trajectory_pipeline.irt import solve_irt
from trajectory_pipeline.verification import verify_irt
from trajectory_pipeline.search_graph import decode,validate_design,changes

ROOT=Path(__file__).resolve().parents[1]

class DateFirstILTTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw=next(x for x in json.loads((ROOT/'configs/physical_matrix.json').read_text()) if x['case_id']=='earth_mars_2029')
        raw.pop('tof_days');cls.mission=Mission(**raw).validate()
        cls.resolved=resolve_date_mission(cls.mission)

    def test_phase_sign_and_angular_variants_precede_duration(self):
        tb,eph,scale,initial,el,phase,branches=angular_branches(self.mission)
        start=eph.state('Earth',self.mission.launch_jd,'Sun');end=eph.state('Mars',self.mission.launch_jd,'Sun')
        delta=np.arctan2(end[1],end[0])-np.arctan2(start[1],start[0])
        self.assertAlmostEqual(phase,np.arctan2(np.sin(delta),np.cos(delta)),delta=.001)
        self.assertEqual(branches[0]['k'],1)
        self.assertGreater(branches[1]['lambda_initial'],branches[0]['lambda_initial'])

    def test_old_duration_does_not_drive_date_entry(self):
        other=resolve_date_mission(replace(self.mission,tof_days=360.))
        self.assertEqual(other.solver['iltt_resolved'],self.resolved.solver['iltt_resolved'])
        self.assertGreater(other.tof_days,1000.)
        self.assertLess(other.tof_days,1600.)
        self.assertNotIn('tof_days',changes(self.mission,other))

    def test_real_mars_irt_uses_date_seed_without_inverse_fit(self):
        with patch('trajectory_pipeline.irt.iltt_seeds',side_effect=AssertionError('Inverse duration fit forbidden')):
            result,diagnostic=solve_irt(self.resolved)
        self.assertIsNotNone(result,diagnostic)
        self.assertTrue(verify_irt(result)['passed'])
        self.assertEqual(result.metadata['chosen_seed']['source'],'ILTT date/phase')

    def test_duration_filter_rejects_instead_of_retargeting_lambda(self):
        m=replace(self.mission,solver=dict(self.mission.solver,iltt_duration_bounds_days=[150,600]))
        with self.assertRaisesRegex(ValueError,'outside declared filter'):resolve_date_mission(m)
        cached=replace(self.resolved,solver=dict(self.resolved.solver,iltt_duration_bounds_days=[150,600]))
        with self.assertRaisesRegex(ValueError,'outside declared filter'):resolve_date_mission(cached)

    def test_graph_gene_is_angular_branch(self):
        design=json.loads((ROOT/'configs/search_graph_date_v3.json').read_text())
        validate_design(design,self.mission)
        m,_,_=decode(self.mission,design,[0,1,0,0,0,0])
        self.assertIsNone(m.tof_days)
        self.assertEqual(m.solver['iltt_branch'],1)
        self.assertEqual(m.solver['irt_entry'],'date')
        with self.assertRaises(ValueError):validate_design(dict(design,duration_factors=[1]),self.mission)

    def test_cli_resolves_date_before_default_time_bounds(self):
        from trajectory_pipeline.__main__ import main
        with patch('sys.argv',['pipeline','solve','unused.json','--output','unused']), \
             patch.object(Mission,'load',return_value=self.mission), \
             patch('trajectory_pipeline.runner.run_pipeline',return_value=(None,{'status':'partial'})) as run:
            main()
        submitted=run.call_args.args[0]
        self.assertAlmostEqual(submitted.tof_days,self.resolved.tof_days)
        self.assertEqual(submitted.time_policy['bounds_days'],[self.resolved.tof_days*.5,self.resolved.tof_days*1.5])

    def test_short_formula_is_admissible(self):
        short=resolve_date_mission(replace(self.mission,launch_tdb='2029-01-01T00:00:00'))
        self.assertLess(short.solver['iltt_resolved']['lambda_corrected'],.75)
        self.assertAlmostEqual(short.tof_days,234.6999519747,places=4)
