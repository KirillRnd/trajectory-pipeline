"""Regressions for continuation orchestration, using real archived trajectories."""
import json,tempfile,unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from trajectory_pipeline.data import Trajectory
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.contract import audit_configuration,make_request
from trajectory_pipeline.accepted_irt_routes import design
from trajectory_pipeline.physical_transfer_routes import exact_time_seed
from trajectory_pipeline.free_time import release_duration

ARCHIVE=Path('data/benchmarks/accepted42_psi_v1')

class AcceptedIRTRoutesTests(unittest.TestCase):
    def test_smooth_parent_can_initialize_free_time_without_relabelling_parent(self):
        parent=Trajectory.load(ARCHIVE/'earth_2015re36_2028_d+0/recover_last')
        self.assertNotIn('switch_times_s',parent.metadata)
        guess=exact_time_seed(parent)
        self.assertNotIn('switch_times_s',parent.metadata)
        self.assertEqual(guess.metadata['status'],'unverified_arc_guess')
        context=deepcopy(parent);context.metadata['bounded_model'].update(alpha=1.,beta=1.)
        duration=context.metadata['mission']['tof_days']
        with self.assertRaises(TimeoutError):
            release_duration(context,guess,[.5*duration,2*duration],perf_counter()-1)

    def test_final_audit_rejects_different_original_mass(self):
        result=Trajectory.load(ARCHIVE/'earth_ceres_2030_d+0/physical')
        original=Mission(**result.metadata['mission']);wrong=replace(original,mass_kg=original.mass_kg+1)
        with self.assertRaises(ValueError):audit_configuration(result,wrong,make_request(wrong),require_final=True)

    def test_manifest_hash_and_resume_identity(self):
        source=json.loads((ARCHIVE/'design.json').read_text())['cases'][0]
        with tempfile.TemporaryDirectory(dir='runs') as folder:
            root=Path(folder);manifest=root/'input.json'
            manifest.write_text(json.dumps([dict(case_id=source['case_id'],source=source['source'])]))
            records=design(root,manifest)
            self.assertEqual(records[0]['source_sha256'],source['source_sha256'])
            self.assertEqual(design(root,manifest),records)
            manifest.write_text(json.dumps([dict(case_id='different',source=source['source'])]))
            with self.assertRaises(ValueError):design(root,manifest)
