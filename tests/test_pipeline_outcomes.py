from pathlib import Path
import unittest
import json
from trajectory_pipeline.outcomes import describe,report

ROOT=Path(__file__).resolve().parents[1]/'data/benchmarks/parameter_study_v1'


class ActualOutcomeTests(unittest.TestCase):
    def test_saved_real_stops_are_distinguished(self):
        expected={'earth_venus_2032__mass_x2':('ПСИ: физический предел тяги','program_error'),
                  'earth_venus_2032__launch_plus_90d':('ПСИ: физический предел тяги','worker_crash'),
                  'earth_venus_2032__thrust_x2':('ПСИ: точное управление','minimum_step'),
                  'earth_ceres_2030__thrust_x2':('ПСИ: введение массы','stage_time_budget')}
        for key,values in expected.items():
            with self.subTest(case=key):
                row=describe(ROOT/key)
                self.assertEqual((row['block'],row['stop_kind']),values)
                self.assertIsNotNone(row['last_verified_artifact'])
                self.assertFalse(row['physically_unreachable_proven'])
        row=describe(ROOT/'earth_mars_2028__mass_x2')
        self.assertEqual(row['stop_kind'],'stage_time_budget')
        self.assertGreater(row['last_model']['thrust_ratio'],1)

    def test_completed_label_rejects_another_requested_engine(self):
        folder=ROOT/'earth_venus_2032__reference'
        mission=json.loads((folder/'mission.json').read_text())
        mission['spacecraft']['exhaust_velocity_m_s']*=2
        with self.assertRaisesRegex(ValueError,'Configuration mismatch'):
            describe(folder,mission)


if __name__=='__main__':unittest.main()
