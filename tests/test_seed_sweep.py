import json,unittest
from pathlib import Path
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.seed_sweep import catalogue,summarize,collect_case

ROOT=Path(__file__).resolve().parents[1]
class EarlySweepTests(unittest.TestCase):
    def test_real_catalogue_screens_KLO_before_IRT_without_inverse_time(self):
        m=Mission.load(ROOT/'configs/apophis_spd50m_204.json')
        design=json.loads((ROOT/'configs/apophis_early_sweep_2027_2033.json').read_text())
        design.update(start_tdb='2029-07-01T00:00:00',stop_tdb='2029-07-01T00:00:00')
        rows,requests=catalogue(m,design)
        self.assertEqual(len(rows),1);self.assertEqual(len(requests),1)
        self.assertIsNone(requests[0]['tof_days'])
        self.assertAlmostEqual(rows[0]['candidates'][0]['lambda_initial'],.8543901812548569)
        self.assertEqual(rows[0]['candidates'][1]['reason'],'KLO_duration_above_horizon')
        self.assertEqual(summarize(rows,[])['dates'][0]['status'],'pending')

    def test_archived_real_IRT_has_comparable_dimensional_cost(self):
        folder=ROOT/'data/benchmarks/apophis_classical_204_v1/runs/apophis_classical_204/chain_july_final/01_irt'
        m=Mission.load(folder/'mission.json');m.solver['iltt_branch']=0
        row=collect_case(folder,m)
        self.assertEqual(row['status'],'accepted')
        self.assertGreater(row['functional_si_m2_s3'],0)
        self.assertNotEqual(row['functional_si_m2_s3'],row['functional_dimensionless'])
