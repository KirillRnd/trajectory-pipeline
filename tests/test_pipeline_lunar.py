from pathlib import Path
import unittest
import numpy as np
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.gravity import Gravity,prepare_lunar_ephemerides
from trajectory_pipeline.ephemerides import Ephemerides

ROOT=Path(__file__).resolve().parents[1]


class LunarTests(unittest.TestCase):
    def test_real_lunar_boundaries_and_gravity_derivatives(self):
        mission=Mission.load(ROOT/'configs/lunar_high_orbit.json')
        initial,target,scales=mission.boundary()
        moon=Ephemerides().state('Moon',mission.arrival_jd,'Earth')
        self.assertAlmostEqual(np.linalg.norm(initial[:3]),150e6,places=6)
        self.assertAlmostEqual(np.linalg.norm(target[:3]-moon[:3]),20e6,places=6)
        spec=prepare_lunar_ephemerides(mission,scales)
        field=Gravity(spec)
        times=np.linspace(0,mission.tof_days*86400/scales.time_s,17)
        # Real boundary geometry and intermediate positions, away from collisions.
        fraction=np.linspace(0,1,17)
        positions=(initial[:3,None]*(1-fraction)+target[:3,None]*fraction)/scales.distance_m
        accelerated,gradient=field.acceleration_gradient(times,positions)
        for i,t in enumerate(times):
            r=positions[:,i]
            a,j=field.independent_scalar(t,r)
            np.testing.assert_allclose(accelerated[:,i],a,atol=2e-13)
            np.testing.assert_allclose(gradient[:,:,i],j,atol=2e-12)
            h=1e-6
            finite=np.column_stack([(field.independent_scalar(t,r+e*h)[0]-field.independent_scalar(t,r-e*h)[0])/(2*h) for e in np.eye(3)])
            np.testing.assert_allclose(j,finite,rtol=2e-8,atol=2e-8)
        for t in (-.01,times[-1]+.01):
            extended=field.positions(t)
            self.assertTrue(all(np.isfinite(value).all() for value in extended))
            for value,spline in zip(extended,field.splines):
                np.testing.assert_allclose(value,spline(t))
            self.assertGreater(np.linalg.norm(extended[0]-field.positions(np.clip(t,0,times[-1]))[0]),0)


if __name__=='__main__':unittest.main()
