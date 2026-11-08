from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from trajectory_pipeline.data import Trajectory,write_json
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.contract import audit_configuration,make_request,stamp_configuration,configuration_hash,digest
from trajectory_pipeline.bounded import verify_bounded
from trajectory_pipeline.runner import run_pipeline

ROOT=Path(__file__).resolve().parents[1]


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.source=Trajectory.load(ROOT/'data/benchmarks/psi/earth_apophis_2029')

    def test_saved_real_solution_matches_requested_ephemerides_and_hardware(self):
        mission=Mission(**self.source.metadata['mission'])
        check=audit_configuration(self.source,mission,make_request(mission),require_final=True)
        self.assertAlmostEqual(check['recovered_model']['model_thrust_N'],.025)
        self.assertAlmostEqual(check['recovered_model']['exhaust_velocity_m_s'],20000)

    def test_physical_equations_reject_relabelled_engine_and_mass(self):
        for field,value in (('thrust_N',.05),('exhaust_velocity_m_s',40000),('dry_mass_kg',150),('mass_kg',312)):
            with self.subTest(field=field):
                artifact=deepcopy(self.source)
                artifact.metadata.pop('configuration_sha256',None)
                if field=='mass_kg':artifact.metadata['mission'][field]=value
                else:artifact.metadata['mission']['spacecraft'][field]=value
                with self.assertRaisesRegex(ValueError,'Configuration mismatch'):
                    audit_configuration(artifact,require_final=True)
                self.assertFalse(verify_bounded(artifact)['passed'])

    def test_launch_relabelling_cannot_reuse_old_planet_positions(self):
        artifact=deepcopy(self.source)
        mission=Mission(**deepcopy(artifact.metadata['mission']))
        mission.launch_tdb='2029-05-15T12:00:00'
        artifact.metadata.update(mission=mission.to_dict(),epoch_jd=mission.launch_jd)
        artifact.metadata.pop('configuration_sha256',None)
        with self.assertRaisesRegex(ValueError,'ephemeris/boundary'):
            audit_configuration(artifact,mission,make_request(mission),require_final=True)

    def test_duration_mismatch_is_not_hidden_by_saved_target_state(self):
        artifact=deepcopy(self.source)
        artifact.metadata['mission']['tof_days']*=1.2
        artifact.metadata.pop('configuration_sha256',None)
        with self.assertRaisesRegex(ValueError,'time of flight'):
            audit_configuration(artifact,require_final=True)

    def test_stored_acceleration_must_match_actual_thrust_and_mass(self):
        artifact=deepcopy(self.source)
        artifact.arrays['acceleration_m_s2']*=2
        with self.assertRaisesRegex(ValueError,'acceleration/thrust/mass'):
            audit_configuration(artifact,require_final=True)

    def test_hardware_flag_must_describe_actual_model_limit(self):
        artifact=deepcopy(self.source)
        artifact.metadata['hardware_limit_reached']=False
        with self.assertRaisesRegex(ValueError,'hardware_limit_reached flag'):
            audit_configuration(artifact)

    def test_mass_and_thrust_homology_on_real_trajectory(self):
        artifact=deepcopy(self.source)
        mission=Mission(**deepcopy(artifact.metadata['mission']))
        mission.case_id+='__mass_thrust_x2'
        mission.mass_kg*=2
        mission.spacecraft['thrust_N']*=2
        mission.spacecraft['dry_mass_kg']*=2
        artifact.metadata.update(case_id=mission.case_id,mission=mission.to_dict())
        artifact.metadata.pop('configuration_sha256',None)
        artifact.arrays['mass_kg']*=2
        artifact.arrays['thrust_N']*=2
        stamp_configuration(artifact)
        audit_configuration(artifact,mission,make_request(mission),require_final=True)
        check=verify_bounded(artifact)
        self.assertTrue(check['passed'],check)
        self.assertAlmostEqual(check['fuel_kg'],2*self.source.metadata['verification']['fuel_kg'],places=5)
        np.testing.assert_array_equal(artifact.arrays['r_m'],self.source.arrays['r_m'])

    def test_completed_resume_refuses_final_with_different_hardware(self):
        mission=Mission(**deepcopy(self.source.metadata['mission']))
        mission.spacecraft['thrust_N']=.05
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)/'run';folder.mkdir()
            write_json(folder/'mission.json',mission.to_dict())
            self.source.save(folder/'final')
            write_json(folder/'summary.json',dict(status='completed',phase='final',case_id=mission.case_id))
            with patch('trajectory_pipeline.runner.run_irt',side_effect=AssertionError('Must not recalculate on mismatch')):
                _,summary=run_pipeline(mission,folder,resume=True)
            self.assertEqual(summary['status'],'failed')
            self.assertIn('mission.spacecraft',summary['error'])

    def test_resume_rejects_wrong_irt_before_departure_module(self):
        seed=Trajectory.load(ROOT/'data/benchmarks/irt/earth_apophis_2029')
        mission=Mission(**deepcopy(seed.metadata['mission']))
        mission.spacecraft['thrust_N']=.05
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)/'run';stage=folder/'stage_irt';stage.mkdir(parents=True)
            write_json(folder/'mission.json',mission.to_dict())
            seed.save(stage/'irt')
            write_json(stage/'summary.json',dict(status='completed_stage',last_result='irt'))
            with patch('trajectory_pipeline.departure.run_departure',side_effect=AssertionError('Wrong stage parameters must be rejected first')):
                _,summary=run_pipeline(mission,folder,resume=True)
            self.assertEqual(summary['status'],'failed')
            self.assertIn('mission.spacecraft',summary['error'])

    def test_early_validation_rejects_nonfinite_or_unused_engine_fields(self):
        for value in (float('nan'),float('inf'),0.,-1.,True,'0.025'):
            mission=Mission(**deepcopy(self.source.metadata['mission']))
            mission.spacecraft['thrust_N']=value
            with self.subTest(value=value),self.assertRaises(ValueError):mission.validate()
        mission=Mission(**deepcopy(self.source.metadata['mission']))
        mission.spacecraft['Isp_s']=2000
        with self.assertRaisesRegex(ValueError,'unknown engine fields'):mission.validate()

    def test_parameter_hash_ignores_integer_float_spelling(self):
        mission=Mission(**deepcopy(self.source.metadata['mission']))
        alternative=deepcopy(mission)
        alternative.mass_kg=float(mission.mass_kg)
        alternative.spacecraft={key:float(value) for key,value in mission.spacecraft.items()}
        alternative.vinf_max_m_s=float(mission.vinf_max_m_s)
        self.assertEqual(configuration_hash(mission),configuration_hash(alternative))

    def test_legacy_request_stamps_remain_valid_against_normalized_parameters(self):
        artifact=deepcopy(self.source)
        mission=Mission(**deepcopy(artifact.metadata['mission']))
        raw=mission.to_dict();raw.pop('solver')
        request=make_request(mission)
        request.pop('configuration_hash_version')
        request.update(mission=raw,configuration_sha256=digest(raw))
        request['request_sha256']=digest({k:v for k,v in request.items() if k!='request_sha256'})
        artifact.metadata['configuration_sha256']=digest(raw)
        alternative=deepcopy(mission);alternative.mass_kg=float(mission.mass_kg)
        self.assertTrue(audit_configuration(artifact,alternative,request,require_final=True)['passed'])


if __name__=='__main__':unittest.main()
