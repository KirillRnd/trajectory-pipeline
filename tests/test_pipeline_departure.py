from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
import numpy as np
from trajectory_pipeline.data import Trajectory
from trajectory_pipeline.departure import run_departure

ROOT=Path(__file__).resolve().parents[1]


class DepartureTests(unittest.TestCase):
    def test_real_apophis_boundary_modes_and_completed_resume(self):
        original=Trajectory.load(ROOT/'data/benchmarks/irt/earth_apophis_2029')
        bounded=Trajectory.load(ROOT/'data/benchmarks/departure/earth_apophis_2029')
        for mode in ('fixed_norm','fixed_vector','free'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                source=deepcopy(original)
                source.metadata['mission']['departure_mode']=mode
                if mode=='fixed_vector':
                    source.metadata['mission']['vinf_vector_m_s']=bounded.metadata['departure']['vector_m_s']
                target=Path(tmp)/'continuation'
                result,checkpoint=run_departure(source,target)
                self.assertEqual(checkpoint['status'],'completed_stage',checkpoint['history'])
                info=result.metadata['departure']
                self.assertTrue(result.metadata['verification']['passed'])
                if mode=='fixed_norm':self.assertLess(abs(info['norm_m_s']-3000),.01)
                if mode=='fixed_vector':np.testing.assert_allclose(info['vector_m_s'],bounded.metadata['departure']['vector_m_s'],atol=.01)
                if mode=='free':self.assertLess(info['pv0_norm'],1e-8)
                resumed,state=run_departure(source,target,resume=True)
                self.assertEqual(state['last_point'],checkpoint['last_point'])
                np.testing.assert_array_equal(resumed.arrays['r_m'],result.arrays['r_m'])


if __name__=='__main__':unittest.main()
