import unittest
import tempfile
from pathlib import Path
from dataclasses import replace
import numpy as np
from trajectory_pipeline.data import Trajectory,Scales
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.iltt_coordinates import ILTTCoordinates
from trajectory_pipeline.irt import solve_irt,correct_shooting
from trajectory_pipeline.verification import verify_irt

APOPHIS=Path('data/benchmarks/apophis_orbit_sources_v1/2029-06-15/early/irt')
MARS=Path('data/benchmarks/mars_short_psi_2029jan01/initial_chain/stage_irt/irt')


def context(path):
    t=Trajectory.load(path);s=Scales(**t.metadata['scales'])
    x=t.metadata['mission']['solver']['iltt_resolved']['x_corrected']
    return t,ILTTCoordinates(s.normalize_state(t.metadata['initial_state_si']),x)


class ILTTCoordinateTests(unittest.TestCase):
    def test_roundtrip_long_and_short_preserves_state_and_time(self):
        for path in (APOPHIS,MARS):
            t,chart=context(path);p=np.asarray(t.metadata['costates_initial'])
            x,diag=chart.from_costates(p)
            np.testing.assert_allclose(chart.to_costates(x),p,rtol=2e-11,atol=1e-15)
            self.assertEqual(diag['local_rank'],6)
            restored=ILTTCoordinates.restore(chart.record(x))
            np.testing.assert_array_equal(restored.to_costates(x),chart.to_costates(x))
            # No date or duration is inferred from the chart's lambda/kappa.
            self.assertNotIn('tof_days',chart.record(x))

    def test_physical_costates_outside_raw_iltt_are_preserved(self):
        early,original=context(APOPHIS)
        full=Trajectory.load('data/benchmarks/apophis_orbit_sources_v1/2029-06-15/full/irt')
        s=Scales(**full.metadata['scales']);p=np.asarray(full.metadata['costates_initial'])
        chart=ILTTCoordinates(s.normalize_state(full.metadata['initial_state_si']),original.reference)
        x,d=chart.from_costates(p)
        self.assertTrue(d['anchored']);self.assertGreater(d['unanchored_fit_error'],1e-4)
        self.assertLess(d['costate_roundtrip_error'],1e-15)
        self.assertAlmostEqual(chart.dm_limit,.5981996389807971)
        saved=chart.record(x);restored=ILTTCoordinates.restore(saved)
        np.testing.assert_allclose(restored.to_costates(saved['parameters']),p,rtol=0,atol=1e-15)
        # The offset is mandatory persisted data, never silently dropped.
        del saved['costate_offset']
        with self.assertRaises(KeyError):ILTTCoordinates.restore(saved)

    def test_chart_jacobian_matches_directional_change(self):
        for path in (APOPHIS,MARS):
            t,chart=context(path);x,_=chart.from_costates(t.metadata['costates_initial'])
            direction=np.array([.1,.2,-.1,.15,.05,.03]);h=1e-5
            fd=(chart.to_costates(x+h*direction)-chart.to_costates(x-h*direction))/(2*h)
            np.testing.assert_allclose(chart.jacobian(x)@direction,fd,rtol=2e-6,atol=1e-9)

    def test_corrector_switches_on_real_changed_boundaries(self):
        # One day later on the same short Mars family: actual correction,
        # not merely converting an already stationary point.
        t,chart=context(MARS);old=Mission(**t.metadata['mission'])
        settings=dict(old.solver,irt_entry='fixed_time',irt_coordinates=['iltt','costates','iltt','costates'],
                      iltt_coordinate_reference=chart.reference.tolist(),attempt_budget_s=30)
        mission=replace(old,launch_tdb='2029-01-02T00:00:00',solver=settings)
        result,diag=solve_irt(mission,costate_seed=t.metadata['costates_initial'])
        self.assertIsNotNone(result,diag);self.assertTrue(verify_irt(result)['passed'])
        steps=diag['attempts'][0]['coordinate_steps']
        self.assertEqual([s['coordinates'] for s in steps],settings['irt_coordinates'])
        self.assertGreater(steps[0]['nfev'],1)
        self.assertEqual(result.metadata['mission']['tof_days'],old.tof_days)

    def test_raw_chart_does_not_clip_or_cross_approximation_family(self):
        _,chart=context(MARS);x=chart.reference.copy();x[0]=chart.dm_limit+.01
        with self.assertRaises(ValueError):chart.to_costates(x)
        x=chart.reference.copy();x[5]=.8
        with self.assertRaises(ValueError):chart.to_costates(x)

    def test_invalid_modes_fail_explicitly(self):
        t,chart=context(MARS);s=Scales(**t.metadata['scales'])
        args=(s.normalize_state(t.metadata['initial_state_si']),s.normalize_state(t.metadata['target_state_si']),t.arrays['t_s'][-1]/s.time_s,t.metadata['costates_initial'])
        for mode in ('typo',[]):
            with self.assertRaises(ValueError):correct_shooting(*args,coordinates=mode)
