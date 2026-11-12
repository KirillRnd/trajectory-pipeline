"""Audit regressions on real saved spacecraft trajectories."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
import signal
from unittest.mock import patch
from dataclasses import replace
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.data import write_json
from trajectory_pipeline.data import Trajectory
from trajectory_pipeline.stage_journal import stage
from trajectory_pipeline.accepted_irt_routes import verify_stage
from trajectory_pipeline.bounded import verify_bounded
from trajectory_pipeline.contract import stamp_configuration

ROOT=Path(__file__).resolve().parents[1]


class AuditRoutesTests(unittest.TestCase):
    def test_date_origin_survives_interruption_before_final_summary(self):
        from trajectory_pipeline.runner import run_pipeline
        source=Trajectory.load(ROOT/'data/benchmarks/accepted42_psi_v1/earth_ceres_2030_d+0/physical')
        resolved=Mission(**source.metadata['mission'])
        resolved=replace(resolved,solver=dict(resolved.solver,irt_entry='fixed_time'))
        requested=replace(resolved,tof_days=None,solver=dict(resolved.solver,irt_entry='date'))
        def interrupt(mission,folder,**kwargs):
            Path(folder).mkdir();write_json(Path(folder)/'mission.json',mission.to_dict())
            raise KeyboardInterrupt()
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as directory:
            root=Path(directory)/'run'
            with patch('trajectory_pipeline.irt_entry_routes.resolve_with_fallback',return_value=resolved),patch('trajectory_pipeline.runner._run_pipeline',side_effect=interrupt):
                with self.assertRaises(KeyboardInterrupt):run_pipeline(requested,root)
            with patch('trajectory_pipeline.runner._run_pipeline',return_value=(source,dict(status='completed',phase='final'))) as resume:
                run_pipeline(requested,root,resume=True)
                self.assertEqual(resume.call_args.args[0].tof_days,resolved.tof_days)
            with self.assertRaisesRegex(ValueError,'entry request differs'):
                run_pipeline(replace(requested,mass_kg=requested.mass_kg+1),root,resume=True)

    def test_nested_budget_preserves_outer_deadline(self):
        from trajectory_pipeline.coordinate_matrix import timed_call
        signal.setitimer(signal.ITIMER_REAL,10)
        try:
            self.assertEqual(timed_call(1,lambda:42),42)
            remaining,_=signal.getitimer(signal.ITIMER_REAL)
            self.assertGreater(remaining,8)
            self.assertLessEqual(remaining,10)
        finally:signal.setitimer(signal.ITIMER_REAL,0)

    def test_skill_components_commands_and_links(self):
        from trajectory_pipeline.skill_audit import audit
        result=audit()
        self.assertTrue(result['passed'],result['issues'])

    def test_journal_replays_final_and_rejects_tampered_checkpoint(self):
        source=Trajectory.load(ROOT/'data/benchmarks/accepted42_psi_v1/earth_ceres_2030_d+0/physical')
        calls=[]
        def execute(seed,folder):
            folder.mkdir();calls.append(folder)
            return seed,dict(status='completed_stage')
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as directory:
            root=Path(directory)
            stage(root,'physical',source,execute,verify_stage)
            # Recover the narrow crash window after output, before receipt.
            (root/'physical_receipt.json').unlink()
            stage(root,'physical',source,execute,verify_stage)
            stage(root,'physical',source,execute,verify_stage)
            self.assertEqual(len(calls),1)
            with (root/'physical_checkpoint/trajectory.npz').open('ab') as stream:stream.write(b'changed')
            with self.assertRaisesRegex(ValueError,'changed'):
                stage(root,'physical',source,execute,verify_stage)

    def test_partial_stage_retries_without_overwriting_checkpoint(self):
        source=Trajectory.load(ROOT/'data/benchmarks/accepted42_psi_v1/earth_ceres_2030_d+0/physical')
        calls=[]
        def execute(seed,folder):
            folder.mkdir();calls.append(folder)
            return seed,dict(status='partial' if len(calls)==1 else 'completed_stage')
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as directory:
            root=Path(directory)
            stage(root,'physical',source,execute,verify_stage)
            stage(root,'physical',source,execute,verify_stage)
            self.assertEqual(len(calls),2)
            self.assertTrue((root/'physical_checkpoint/trajectory.npz').exists())
            self.assertTrue((root/'physical_checkpoint_2/trajectory.npz').exists())
            changed=deepcopy(source);changed.metadata['mission']['mass_kg']+=1
            with self.assertRaisesRegex(ValueError,'input changed'):
                stage(root,'physical',changed,execute,verify_stage)

    def test_intermediate_can_cross_reserve_but_final_cannot(self):
        root=ROOT/'data/benchmarks/ummp_apophis_156kg_benchmark/psi/fuel'
        for point,expected in [('point_0003',True),('point_0004',False)]:
            result=Trajectory.load(root/point)
            result.metadata['mission']['spacecraft']['dry_mass_kg']=155.
            stamp_configuration(result)
            report=verify_bounded(result)
            self.assertEqual(report['passed'],expected,(point,report))
            if expected:self.assertFalse(report['dry_mass_constraint_enforced'])
