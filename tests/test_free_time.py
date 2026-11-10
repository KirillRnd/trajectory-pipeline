from pathlib import Path
import json
from dataclasses import replace
import unittest
from trajectory_pipeline.data import Trajectory
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.free_time import audit_time_result
from trajectory_pipeline.bounded import verify_bounded
from trajectory_pipeline.kiam_verification import verify_kiam_psi

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'data/benchmarks/free_time_v1'


class FreeTimeTests(unittest.TestCase):
    def test_independent_dates_release_the_same_reference_duration(self):
        rows=json.loads((ARCHIVE/'sweep/results.json').read_text())
        self.assertEqual(len(rows),2)
        for row in rows:
            self.assertEqual(row['selected'],'fast')
            requested=Mission.load(ARCHIVE/'sweep/inputs'/f"{row['case_id']}.json")
            result=Trajectory.load(ARCHIVE/'sweep'/row['artifact'])
            self.assertTrue(audit_time_result(result,requested)['passed'])
            self.assertTrue(verify_bounded(result)['passed'])
            self.assertTrue(verify_kiam_psi(result)['passed'])
            self.assertGreater(abs(row['tof_days']-requested.tof_days),10.)
            self.assertLess(row['fuel_kg'],27.652004775448063)
            seed=json.loads((ARCHIVE/'sweep'/row['fast']['attempt']/'seed.json').read_text())
            self.assertEqual(seed['reference_epoch_tdb'],'2032-11-01T00:00:00')
        self.assertNotEqual(rows[0]['tof_days'],rows[1]['tof_days'])

    def test_cold_iltt_and_forced_standard_rerun_release_duration(self):
        cold=ARCHIVE/'cold'
        mission=Mission.load(cold/'mission.json');result=Trajectory.load(cold/'final')
        self.assertTrue(audit_time_result(result,mission)['passed'])
        self.assertTrue(verify_bounded(result)['passed'])
        row=json.loads((ARCHIVE/'fallback/results.json').read_text())[0]
        self.assertEqual(row['selected'],'standard')
        self.assertNotEqual(row['fast']['status'],'completed')
        requested=Mission.load(ARCHIVE/'fallback/inputs/date_000000.json')
        result=Trajectory.load(ARCHIVE/'fallback'/row['artifact'])
        self.assertTrue(audit_time_result(result,requested)['passed'])
        self.assertTrue(verify_bounded(result)['passed'])
        self.assertGreater(abs(row['tof_days']-requested.tof_days),10.)

    def test_time_release_cannot_change_hardware_or_bounds(self):
        result=Trajectory.load(ARCHIVE/'cold/final');mission=Mission.load(ARCHIVE/'cold/mission.json')
        wrong=replace(mission,mass_kg=mission.mass_kg+1)
        with self.assertRaisesRegex(ValueError,'other than duration'):audit_time_result(result,wrong)
        wrong=replace(mission,time_policy={'bounds_days':[390.,400.]})
        with self.assertRaisesRegex(ValueError,'outside requested bounds'):audit_time_result(result,wrong)

    def test_old_fixed_time_serialization_is_preserved(self):
        fixed=Mission(**Trajectory.load(ROOT/'data/benchmarks/psi/earth_venus_2032').metadata['mission'])
        self.assertNotIn('time_policy',fixed.to_dict())
        for bounds in ([0,500],[400,500],[100,float('inf')],[True,500]):
            with self.assertRaises(ValueError):replace(fixed,time_policy={'bounds_days':bounds}).validate()


if __name__=='__main__':unittest.main()
