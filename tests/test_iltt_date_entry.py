import json
import unittest
from tempfile import TemporaryDirectory
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
        def stop_at_time_controller(mission,output,resume=False):
            Path(output).mkdir()
            return None,{'status':'partial'}
        with TemporaryDirectory() as temporary:
            output=Path(temporary)/'case'
            with patch('sys.argv',['pipeline','solve','unused.json','--output',str(output)]), \
                 patch.object(Mission,'load',return_value=self.mission), \
                 patch('trajectory_pipeline.free_time.run_time_pipeline',side_effect=stop_at_time_controller) as run:
                main()
            self.assertIsNone(json.loads((output/'entry_request.json').read_text())['tof_days'])
            with patch('sys.argv',['pipeline','solve','unused.json','--output',str(output),'--resume','--fixed-time']), \
                 patch.object(Mission,'load',return_value=self.mission), \
                 patch('trajectory_pipeline.runner.run_pipeline',side_effect=AssertionError('Changed flags reached computation')):
                with self.assertRaisesRegex(ValueError,'duration policy'):main()
        submitted=run.call_args.args[0]
        self.assertAlmostEqual(submitted.tof_days,self.resolved.tof_days)
        self.assertEqual(submitted.time_policy['bounds_days'],[self.resolved.tof_days*.5,self.resolved.tof_days*1.5])

    def test_cli_reports_real_iltt_filter_failure_before_time_dispatch(self):
        from trajectory_pipeline.__main__ import main
        constrained=replace(self.mission,solver=dict(self.mission.solver,iltt_duration_bounds_days=[150,600]))
        with TemporaryDirectory() as temporary:
            output=Path(temporary)/'case'
            with patch('sys.argv',['pipeline','solve','unused.json','--output',str(output)]),patch.object(Mission,'load',return_value=constrained):
                self.assertEqual(main(),1)
            summary=json.loads((output/'summary.json').read_text())
            self.assertEqual(summary['status'],'initial_failed')
            self.assertEqual(summary['phase'],'iltt_entry')

    def test_short_formula_is_admissible(self):
        short=resolve_date_mission(replace(self.mission,launch_tdb='2029-01-01T00:00:00'))
        self.assertLess(short.solver['iltt_resolved']['lambda_corrected'],.75)
        self.assertAlmostEqual(short.tof_days,234.6999519747,places=4)

    def test_apophis_saturated_R_seed_recovers_without_changing_toolbox(self):
        raw=next(x for x in json.loads((ROOT/'configs/search_matrix_date_v4.json').read_text()) if x['target']=='Apophis')
        mission=replace(Mission(**raw),launch_tdb='2029-07-01T00:00:00')
        tb,eph,scale,initial,el,phase,branches=angular_branches(mission)
        F,x=tb.make_F_function(initial[:3][None,:],initial[3:][None,:],branches[0]['lambda_initial'],el[0],0,1,el[2],el[3],el[1],el[8])
        a=F(x);shift=x.copy();shift[0]+=1e-5;b=F(shift)
        np.testing.assert_array_equal(a['rf'],b['rf'])
        resolved=resolve_date_mission(mission)
        record=resolved.solver['iltt_resolved']
        self.assertTrue(record['initial_transform_saturated'])
        self.assertEqual(record['correction_attempts'][-1]['route'],'bounded_R')
        self.assertLess(np.linalg.norm(record['orbit_phase_residual']),1e-7)
        self.assertLess(abs(record['x_corrected'][0]),.999*np.sin(.642))
        result,diagnostic=solve_irt(resolved)
        self.assertIsNotNone(result,diagnostic)
        self.assertTrue(verify_irt(result)['passed'])

    def test_real_apophis_corrector_can_extrapolate_trial(self):
        from trajectory_pipeline.ephemerides import Ephemerides
        mission=Mission.load(ROOT/'configs/apophis_spd50m_204.json')
        mission=replace(mission,launch_tdb='2029-09-21T00:00:00',
                        solver=dict(mission.solver,iltt_duration_bounds_days=[1e-8,1095.75]))
        eph=Ephemerides();original=eph.state;coverage=eph.coverage('Apophis')
        outside=[]
        def checked(body,jd,center):
            if body.lower()=='apophis':
                if not coverage['start_jd']<=jd<=coverage['stop_jd']:outside.append(jd)
            return original(body,jd,center)
        with patch.object(eph,'state',side_effect=checked):
            try:
                resolve_date_mission(mission,eph)
            except (ValueError,TimeoutError) as exc:
                self.assertNotIn('extrapolation forbidden',str(exc))
        self.assertTrue(outside)

    def test_explicit_dm_limit_reaches_R_without_changing_default(self):
        tb,*_=angular_branches(self.mission)
        default=tb.calculate_Reo_matrix_noapprox(.75,.3)
        relaxed=tb.calculate_Reo_matrix_noapprox(.75,.3,dm_limit=.8)
        self.assertGreater(np.linalg.norm(default-relaxed),.01)
        np.testing.assert_array_equal(default,tb.calculate_Reo_matrix_noapprox(.75,.3))
        np.testing.assert_array_equal(tb.calculate_Reo_matrix_noapprox(.9,.3,dm_limit=.8),
                                      tb.calculate_Reo_matrix_noapprox(.8,.3,dm_limit=.8))
        with self.assertRaises(ValueError):tb.calculate_Reo_matrix_noapprox(.75,.3,dm_limit=1.3)
        changed=replace(self.resolved,solver=dict(self.resolved.solver,iltt_dm_limit=.8))
        refreshed=resolve_date_mission(changed)
        self.assertEqual(refreshed.solver['iltt_resolved']['binding']['dm_limit'],.8)
        self.assertLessEqual(abs(refreshed.solver['iltt_resolved']['x_corrected'][0]),.8)
