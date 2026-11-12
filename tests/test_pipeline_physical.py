from pathlib import Path
from time import perf_counter
import unittest
import numpy as np
from components.pazov import OptimalControlSolver
from trajectory_pipeline.data import Trajectory,Scales
from trajectory_pipeline.bounded import canonical,collocate,verify_bounded
from trajectory_pipeline.bounded_model import BoundedModel
from trajectory_pipeline.kiam_verification import verify_kiam_psi
from trajectory_pipeline.bangbang import solve_bangbang,_sampling_times

ROOT=Path(__file__).resolve().parents[1]


class PhysicalTests(unittest.TestCase):
    def test_rescaled_real_mesh_stays_inside_integrated_arcs(self):
        source=Trajectory.load(ROOT/'data/benchmarks/psi/earth_bennu_2029')
        scale=Scales(**source.metadata['scales']).time_s
        old=source.arrays['t_s']/scale
        for factor in np.linspace(.5,1.5,101):
            end=old[-1]*factor
            edges=np.r_[0,np.asarray(source.metadata['switch_times_s'])/scale*factor,end]
            samples=np.r_[old*end/old[-1],np.nextafter(end,np.inf)]
            merged=_sampling_times(samples,edges,scale)
            self.assertEqual(merged[0],0.)
            self.assertEqual(merged[-1],end)
            covered=np.any([(merged>=a)&(merged<=b) for a,b in zip(edges[:-1],edges[1:])],axis=0)
            self.assertTrue(covered.all())

    def test_real_switch_grid_survives_dimensional_rounding(self):
        source=Trajectory.load(ROOT/'data/benchmarks/psi/earth_bennu_2029')
        scale=Scales(**source.metadata['scales']).time_s
        times=source.arrays['t_s']/scale
        edges=np.r_[0,np.asarray(source.metadata['switch_times_s'])/scale,times[-1]]
        # Nearby meshes arise when the same real switching time is normalized
        # on different hosts. Preserve the new event and the exported clock.
        samples=np.r_[times,np.nextafter(edges[1:-1],np.inf),np.nextafter(edges[1:-1],0.)]
        merged=_sampling_times(samples,edges,scale)
        self.assertTrue(np.all(np.diff(merged*scale)>0))
        self.assertTrue(np.isin(edges,merged).all())
        expected_seconds=np.unique(np.r_[samples,edges]*scale)
        np.testing.assert_array_equal(merged*scale,expected_seconds)

    def test_exact_free_departure_recovery_on_real_bennu(self):
        source=Trajectory.load(ROOT/'data/benchmarks/psi/earth_bennu_2029')
        self.assertFalse(source.metadata['departure']['bound_active'])
        result=solve_bangbang(source,source,BoundedModel(**source.metadata['bounded_model']),perf_counter()+20,'psi')
        np.testing.assert_array_equal(result.arrays['costates'][0,3:6],np.zeros(3))
        self.assertTrue(result.metadata['verification']['passed'])

    def test_pazov_array_and_zero_mass_bridge_on_real_primer(self):
        source=Trajectory.load(ROOT/'data/benchmarks/departure/earth_apophis_2029')
        pv=source.arrays['costates'][:,3:].T
        for alpha in (0.,.4,.9,1.):
            solver=OptimalControlSolver(1.,.04,alpha,'mixed')
            expected=np.stack([solver.optimal_control(p) for p in pv.T],axis=1)
            np.testing.assert_allclose(solver.optimal_control_array(pv),expected,atol=1e-15)
            physical=BoundedModel(.04,alpha=alpha,beta=0,q=.002,variable_mass=True)
            state=canonical(source,physical)
            np.testing.assert_allclose(physical.throttle(state),np.linalg.norm(expected,axis=0)/.04,atol=1e-14)
            bounded=BoundedModel(.04,alpha=alpha)
            nominal=canonical(source,bounded)
            fraction=bounded.throttle(nominal)
            self.assertTrue(np.all((fraction>=0)&(fraction<=1)))
            for column in nominal.T[::37]:
                self.assertLessEqual(bounded.throttle(column),1.)

    def test_real_physical_results_against_independent_integrator_and_kiam(self):
        for key in ('earth_apophis_2029','earth_mars_2028','earth_venus_2032','earth_bennu_2029'):
            with self.subTest(case=key):
                result=Trajectory.load(ROOT/'data/benchmarks/psi'/key)
                check=verify_bounded(result)
                vendor=verify_kiam_psi(result)
                self.assertTrue(check['passed'],check)
                self.assertTrue(vendor['passed'],vendor)
                self.assertLess(check['mass_balance_error_kg'],1e-4)
                self.assertLess(check['switching_sign_violation'],1e-6)
                self.assertLessEqual(result.arrays['thrust_N'].max(),result.metadata['mission']['spacecraft']['thrust_N']*(1+1e-12))
                self.assertTrue(np.isin(result.arrays['throttle'],[0.,1.]).all())

    def test_real_mars_free_to_active_mass_transition(self):
        seed=Trajectory.load(ROOT/'data/benchmarks/psi/mars_constraint_transition_seed')
        self.assertFalse(seed.metadata['departure']['bound_active'])
        parameters=dict(seed.metadata['bounded_model'],beta=.8)
        result=collocate(seed,seed,BoundedModel(**parameters),perf_counter()+30,'psi_mass')
        self.assertTrue(result.metadata['departure']['bound_active'])
        self.assertAlmostEqual(result.metadata['departure']['norm_m_s'],3000.,places=4)
        self.assertTrue(result.metadata['verification']['passed'])


if __name__=='__main__':unittest.main()
