import json
from pathlib import Path
import shutil
import tempfile
import unittest

from trajectory_pipeline.matrix_report import report_matrix

ROOT = Path(__file__).resolve().parents[1]


class FreeTimeReportTests(unittest.TestCase):
    def test_saved_real_result_reports_resolved_not_seed_duration(self):
        saved = ROOT/'data/benchmarks/free_time_v1/cold'
        mission = json.loads((saved/'mission.json').read_text())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(saved, root/mission['case_id'])
            (root/'matrix.json').write_text(json.dumps([mission]))
            result = report_matrix(root, root/'report.md')
            self.assertEqual(result['counts'], {'completed': 1})
            row = result['rows'][0]
            self.assertAlmostEqual(row['seed_tof_days'], 390.8)
            self.assertAlmostEqual(row['tof_days'], 410.9696560096026)
            self.assertTrue(row['verification']['passed'])
            self.assertTrue(row['kiam_verification']['passed'])
            self.assertTrue(row['time_optimization']['optimizer_success'])
            self.assertIn('410.969656', (root/'report.csv').read_text())


if __name__ == '__main__':
    unittest.main()
