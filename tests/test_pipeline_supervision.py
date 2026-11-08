import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from trajectory_pipeline.data import write_json
from trajectory_pipeline.runner import sweep_pipeline

ROOT=Path(__file__).resolve().parents[1]


class SupervisionTests(unittest.TestCase):
    def test_native_worker_exit_preserves_next_case_and_first_pass(self):
        missions=json.loads((ROOT/'configs/physical_matrix.json').read_text(encoding='utf-8'))[:2]
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);matrix=root/'input.json';write_json(matrix,missions)
            calls=[]
            def worker(command,**options):
                destination=Path(command[command.index('--output')+1])
                destination.mkdir()
                calls.append(destination.name)
                crashed=len(calls)==1
                write_json(destination/'summary.json',dict(case_id=destination.name,
                           status='running' if crashed else 'partial',phase='psi',stages={}))
                return subprocess.CompletedProcess(command,3221225477 if crashed else 2)
            with patch('trajectory_pipeline.runner.subprocess.run',side_effect=worker):
                rows=sweep_pipeline(matrix,root/'run')
            self.assertEqual(len(calls),2)
            self.assertEqual([row['status'] for row in rows],['failed','partial'])
            failed=json.loads((root/'run'/missions[0]['case_id']/'summary.json').read_text(encoding='utf-8'))
            self.assertIn('3221225477',failed['error'])
            self.assertTrue((root/'run'/failed['worker_log']).is_file())
            with patch('trajectory_pipeline.runner.subprocess.run',side_effect=AssertionError('First-pass outcomes must not be retried')):
                resumed=sweep_pipeline(matrix,root/'run',resume=True,pending_only=True)
            self.assertEqual(resumed,rows)
            environment_path=root/'run/environment.json'
            environment=json.loads(environment_path.read_text(encoding='utf-8'))
            environment['python']='incompatible-interpreter'
            write_json(environment_path,environment)
            with patch('trajectory_pipeline.runner.subprocess.run',side_effect=AssertionError('Incompatible runtime must not launch a worker')):
                with self.assertRaisesRegex(ValueError,'environment differs'):
                    sweep_pipeline(matrix,root/'run',resume=True,pending_only=True)


if __name__=='__main__':unittest.main()
