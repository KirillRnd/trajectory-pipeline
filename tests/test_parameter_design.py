from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch
from trajectory_pipeline.parameter_study import build_matrix
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.data import write_json
from trajectory_pipeline.runner import sweep_pipeline

ROOT=Path(__file__).resolve().parents[1]


class ParameterDesignTests(unittest.TestCase):
    def test_stale_generated_matrix_is_rejected_before_any_worker(self):
        design=ROOT/'configs/parameter_study_design.json'
        rows=build_matrix(design)
        rows[0]['spacecraft']['thrust_N']=.05
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);matrix=root/'stale.json';write_json(matrix,rows)
            with patch('trajectory_pipeline.runner.subprocess.run',side_effect=AssertionError('No stale-matrix computation may start')):
                with self.assertRaisesRegex(ValueError,'differs from its declared design'):
                    sweep_pipeline(matrix,root/'run',parameter_design=design)
            self.assertFalse((root/'run').exists())

    def test_balanced_real_missions_keep_independent_variations(self):
        rows=build_matrix(ROOT/'configs/parameter_study_design.json')
        self.assertEqual(len(rows),24)
        self.assertEqual(len({r['case_id'] for r in rows}),24)
        grouped={}
        for row in rows:
            base,variant=row['case_id'].rsplit('__',1)
            grouped.setdefault(base,{})[variant]=row
        self.assertEqual(len(grouped),4)
        for base,variants in grouped.items():
            with self.subTest(base=base):
                self.assertEqual(len(variants),6)
                reference=variants['reference']
                for row in variants.values():self.assertEqual(row['solver'],reference['solver'])
                self.assertEqual(variants['thrust_x2']['spacecraft']['thrust_N'],2*reference['spacecraft']['thrust_N'])
                self.assertEqual(variants['exhaust_x2']['spacecraft']['exhaust_velocity_m_s'],2*reference['spacecraft']['exhaust_velocity_m_s'])
                self.assertEqual(variants['mass_x2']['mass_kg'],2*reference['mass_kg'])
                self.assertEqual(variants['mass_x2']['spacecraft']['thrust_N'],reference['spacecraft']['thrust_N'])
                self.assertEqual(variants['mass_x2']['spacecraft']['dry_mass_kg'],2*reference['spacecraft']['dry_mass_kg'])
                self.assertAlmostEqual(Mission(**variants['launch_plus_90d']).launch_jd-Mission(**reference).launch_jd,90.)
                self.assertEqual(variants['duration_x1p2']['launch_tdb'],reference['launch_tdb'])
                self.assertAlmostEqual(variants['duration_x1p2']['tof_days'],1.2*reference['tof_days'])


if __name__=='__main__':unittest.main()
