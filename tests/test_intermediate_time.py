"""Contract checks use real archived Mars and Bennu trajectories."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from trajectory_pipeline.data import Trajectory,sha256,write_json
from trajectory_pipeline.search_graph import read,worker,verify_cached,save_intermediate,validate_design
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.intermediate_time import verify_intermediate,time_context
from trajectory_pipeline.ephemerides import Ephemerides

ROOT=Path(__file__).resolve().parents[1]

def mars_checkpoint():
    root=ROOT/'data/benchmarks/search_matrix_v1/earth_mars_2029'
    graph=read(root/'graph.json')
    node=next(k for k,n in graph['nodes'].items() if n['request']['mission']['tof_days']==300 and n['request']['mission']['spacecraft']['thrust_N']==.025)
    folder=root/'nodes'/node/'run/stage_psi/mass'
    return Trajectory.load(folder/read(folder/'continuation.json')['last_point'])

class IntermediateTimeTests(unittest.TestCase):
    def test_verified_status_without_artifact_is_not_a_valid_cache_entry(self):
        for status in ('completed','intermediate'):
            with self.assertRaisesRegex(ValueError,'Missing verified graph artifact'):
                verify_cached(dict(status=status))

    def test_rejected_snapshot_cannot_keep_intermediate_status(self):
        with TemporaryDirectory() as d, patch('trajectory_pipeline.intermediate_time.verify_intermediate',side_effect=ValueError('replay failed')):
            folder=Path(d);save_intermediate(mars_checkpoint(),folder,'intermediate','intermediate_release')
            result=read(folder/'result.json')
            self.assertEqual(result['status'],'failed')
            self.assertNotIn('artifact',result)
            self.assertIn('replay failed',result['error'])

    def test_real_partial_saturn_excess_is_a_valid_early_source(self):
        root=ROOT/'data/benchmarks/search_matrix_v1/earth_saturn_flyby_2028'
        graph=read(root/'graph.json')
        node=next(k for k,n in graph['nodes'].items() if n['phase']=='departure')
        folder=root/'nodes'/node/'run/stage_departure'
        source=Trajectory.load(folder/read(folder/'continuation.json')['last_point'])
        self.assertTrue(verify_intermediate(source)['passed'])
        self.assertLess(source.metadata['departure']['parameter'],1)

    def test_real_mass_checkpoint_is_not_physical_admission(self):
        source=mars_checkpoint();self.assertTrue(verify_intermediate(source)['passed'])
        self.assertLess(source.metadata['bounded_model']['beta'],1)
        with TemporaryDirectory() as d:
            folder=Path(d);save_intermediate(source,folder,'partial','mass')
            result=read(folder/'result.json');self.assertEqual(result['status'],'partial')
            verify_cached(result)
            result['arrays_sha256']='changed'
            with self.assertRaisesRegex(ValueError,'Cached artifact changed'):verify_cached(result)

    def test_duration_context_preserves_model_and_hardware_and_moves_target(self):
        source=mars_checkpoint();context=time_context(source,450,Ephemerides())
        self.assertEqual(context.metadata['bounded_model'],source.metadata['bounded_model'])
        a,b=deepcopy(context.metadata['mission']),deepcopy(source.metadata['mission'])
        a.pop('tof_days');b.pop('tof_days');self.assertEqual(a,b)
        self.assertAlmostEqual(context.arrays['t_s'][-1],450*86400)
        self.assertNotEqual(context.metadata['target_state_si'],source.metadata['target_state_si'])
        self.assertEqual(source.metadata['mission']['tof_days'],300)

    def test_final_bangbang_is_not_silently_regularized(self):
        final=Trajectory.load(ROOT/'data/benchmarks/psi/earth_bennu_2029')
        with self.assertRaisesRegex(ValueError,'alpha < 1'):verify_intermediate(final)

    def test_parent_hash_bound_before_continuation(self):
        source=ROOT/'data/benchmarks/psi/earth_bennu_2029'
        with TemporaryDirectory() as d:
            request=Path(d)/'request.json'
            write_json(request,dict(operation='physical_continue',mission=read(source/'trajectory.json')['mission'],budget_s=1,
                parent_artifact=str(source),parent_sha256=sha256(source/'trajectory.npz'),parent_metadata_sha256='changed'))
            worker(request);result=read(Path(d)/'result.json')
            self.assertEqual(result['status'],'failed');self.assertIn('Parent artifact changed',result['error'])

    def test_new_design_validates_limits_and_route(self):
        design=read(ROOT/'configs/search_graph_v1.json');design.update(routes=['intermediate'],intermediate_rounds=1,intermediate_release_budget_s=120,physical_continue_budget_s=240)
        base=Mission(**mars_checkpoint().metadata['mission']);validate_design(design,base)
        for key,value in [('intermediate_rounds',0),('physical_continue_budget_s',float('nan'))]:
            bad=deepcopy(design);bad[key]=value
            with self.assertRaises(ValueError):validate_design(bad,base)

    def test_physical_release_can_start_on_intermediate_duration_bound(self):
        from trajectory_pipeline.free_time import release_duration
        final=Trajectory.load(ROOT/'data/benchmarks/psi/earth_bennu_2029')
        with patch('trajectory_pipeline.free_time.minimize',side_effect=TimeoutError('optimizer reached')):
            for bounds in ([250,500],[500,750]):
                with self.assertRaisesRegex(TimeoutError,'optimizer reached'):
                    release_duration(final,final,bounds,float('inf'))

if __name__=='__main__':unittest.main()
