from copy import deepcopy
from pathlib import Path
import random
import tempfile
import unittest
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.search_graph import read, validate_design, repair, breed, pareto, changes, worker, verify_cached
from trajectory_pipeline.data import sha256, write_json

ROOT=Path(__file__).resolve().parents[1]


class SearchGraphTests(unittest.TestCase):
    def setUp(self):
        self.base=Mission(**read(ROOT/'data/benchmarks/psi/earth_bennu_2029/trajectory.json')['mission'])
        self.design=read(ROOT/'configs/search_graph_v1.json')

    def test_r_transfer_cannot_relabel_engine_or_duration(self):
        history=dict(references=[dict(mission=self.base.to_dict())])
        self.assertEqual(repair([1,0,0,0,0,1],self.base,self.design,history)[-1],1)
        self.assertEqual(repair([1,0,1,0,0,1],self.base,self.design,history)[-1],0)
        self.assertEqual(repair([1,1,0,0,0,1],self.base,self.design,history)[-1],0)

    def test_mutation_crossover_and_elitism_are_reproducible(self):
        population=[[0,0],[1,1],[0,1],[1,0]];scores=[[0,4],[1,0],[0,3],[0,2]]
        args=(population,scores,[2,2])
        first=breed(*args,random.Random(17),list)
        self.assertEqual(first,breed(*args,random.Random(17),list))
        self.assertEqual(first[0][0],[1,1])
        self.assertTrue(all(x['kind']=='crossover_mutation' for x in first[1][1:]))

    def test_pareto_preserves_original_against_cheaper_changed_hardware(self):
        rows=[dict(objectives=[0,30,500]),dict(objectives=[1,20,500]),dict(objectives=[1,35,600])]
        self.assertEqual(pareto(rows),rows[:2])
        other=deepcopy(self.base);other.case_id='different_label'
        self.assertEqual(changes(self.base,other),{})
        other.spacecraft['thrust_N']*=2
        self.assertIn('spacecraft',changes(self.base,other))

    def test_invalid_spaces_fail_before_execution(self):
        validate_design(self.design,self.base)
        for key,value in [('duration_factors',[0]),('mass_alphas',[1]),('wall_budget_s',float('nan')),('routes',['cr3bp'])]:
            bad=deepcopy(self.design);bad[key]=value
            with self.assertRaises(ValueError):validate_design(bad,self.base)

    def test_worker_rejects_engine_change_disguised_as_date_transfer(self):
        source=ROOT/'data/benchmarks/psi/earth_bennu_2029'
        mission=deepcopy(self.base);mission.spacecraft['thrust_N']*=2
        with tempfile.TemporaryDirectory() as directory:
            request=Path(directory)/'request.json'
            write_json(request,dict(operation='r_transfer',mission=mission.to_dict(),budget_s=1,
                reference=dict(path=str(source),metadata_sha256=sha256(source/'trajectory.json'),arrays_sha256=sha256(source/'trajectory.npz'))))
            worker(request)
            result=read(Path(directory)/'result.json')
            self.assertEqual(result['status'],'failed')
            self.assertIn('only supports a changed launch date',result['error'])

    def test_cached_artifact_identity_checked_without_reoptimization(self):
        source=ROOT/'data/benchmarks/psi/earth_bennu_2029'
        cached=dict(status='completed',artifact=str(source),metadata_sha256=sha256(source/'trajectory.json'),arrays_sha256=sha256(source/'trajectory.npz'))
        verify_cached(cached)
        cached['metadata_sha256']='modified'
        with self.assertRaisesRegex(ValueError,'Cached artifact changed'):verify_cached(cached)


if __name__=='__main__':unittest.main()
