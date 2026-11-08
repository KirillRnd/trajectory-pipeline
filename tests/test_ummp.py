from pathlib import Path
import unittest

import numpy as np
from scipy.io import loadmat

from trajectory_pipeline.bounded import canonical
from trajectory_pipeline.bounded_model import BoundedModel
from trajectory_pipeline.data import Trajectory
from trajectory_pipeline.ummp import _model
from trajectory_pipeline.ummp_model import UmmpEngine


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT/'data/references/apophis_ummp_156kg_hard_bangbang_verified.mat'


class UmmpTests(unittest.TestCase):
    def test_historical_force_and_compensated_fuel(self):
        reference = loadmat(REFERENCE,simplify_cells=True)['verification']
        times, y = reference['t_sol'], reference['Y_sol']
        power, thrust, _, flow, _, _ = UmmpEngine().performance(times,np.linalg.norm(y[:,:3],axis=1))
        self.assertLess(power.min(),400.)
        self.assertEqual(power.max(),450.)
        active = reference['thrust_N']>0
        np.testing.assert_allclose(thrust*active,reference['thrust_N'],rtol=1e-13,atol=1e-14)
        self.assertAlmostEqual(np.trapezoid(flow*active,times),reference['fuel_kg'],places=4)

    def test_zero_fraction_is_the_verified_constant_exhaust_model(self):
        trajectory = Trajectory.load(ROOT/'data/benchmarks/psi/earth_apophis_2029')
        psi = BoundedModel(**trajectory.metadata['bounded_model'])
        model = _model(trajectory.metadata,0.)
        states = canonical(trajectory,psi)
        for i in range(0,states.shape[1],83):
            t = trajectory.arrays['t_s'][i]/model.scales.time_s
            state = states[:,i]
            on = trajectory.arrays['throttle'][i]
            np.testing.assert_allclose(model.rhs(t,state,on),psi.rhs(t,state,on),atol=2e-15)
            self.assertAlmostEqual(model.switching(state,t),psi.switching(state),places=15)

    def test_engine_gradient_in_full_adjoint_equations(self):
        trajectory = Trajectory.load(ROOT/'data/benchmarks/psi/earth_apophis_2029')
        model = _model(trajectory.metadata,1.)
        state = canonical(trajectory,model)[:,0].copy()
        state[:3] *= 1.2  # Powered and below the 450 W cap.
        t = 1.

        def hamiltonian(y):
            r = y[:3]
            radius = np.linalg.norm(r)
            force, flow, _, _ = model.coefficients(t,radius)
            return (y[7:10]@y[3:6]-y[10:13]@r/radius**3+
                    force*np.linalg.norm(y[10:13])/y[6]-flow*(model.fuel_weight+y[13]))

        perturbations = 1e-6*np.eye(14)[:3]
        expected = np.array([-(hamiltonian(state+d)-hamiltonian(state-d))/2e-6
                             for d in perturbations])
        np.testing.assert_allclose(model.rhs(t,state,1.)[7:10],expected,atol=1e-9)
