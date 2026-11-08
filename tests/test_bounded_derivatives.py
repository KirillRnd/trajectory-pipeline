from pathlib import Path
import json
import unittest
import numpy as np
from trajectory_pipeline.data import Trajectory
from trajectory_pipeline.bounded import canonical
from trajectory_pipeline.bounded_model import BoundedModel
from trajectory_pipeline.bounded_derivatives import canonical_jacobian

ROOT=Path(__file__).resolve().parents[1]


class RealCanonicalDerivativesTests(unittest.TestCase):
    def test_real_models_across_bodies_hardware_mass_and_geometry(self):
        root=ROOT/'data/benchmarks/parameter_study_v1'
        selected={}
        for file in sorted(root.glob('*/**/trajectory.json')):
            # One saved state for each case and stage/model region, avoiding
            # hundreds of almost identical continuation points in this check.
            meta=json.loads(file.read_text(encoding='utf-8'))
            if 'bounded_model' not in meta:continue
            model=BoundedModel(**meta['bounded_model'])
            if model.gravity is not None:continue
            region=(model.variable_mass,model.beta==0,model.beta==1,
                    model.alpha==0,model.alpha==1,model.alpha>=.9)
            key=(meta['case_id'],region)
            if key not in selected:selected[key]=file.parent
        self.assertEqual(len({k[0] for k in selected}),24)
        self.assertGreater(len(selected),60)
        for folder in selected.values():
            with self.subTest(folder=str(folder)):
                trajectory=Trajectory.load(folder)
                model=BoundedModel(**trajectory.metadata['bounded_model'])
                states=canonical(trajectory,model)
                y=states[:,np.unique(np.linspace(0,states.shape[1]-1,7,dtype=int))]
                # A finite difference straddling a clipping corner does not
                # estimate either one-sided Jacobian. Check smooth real nodes.
                switch=model.switching(y)
                threshold=(1-model.alpha)*model.a_max**2
                distance=np.minimum(abs(switch),abs(switch-threshold))
                smooth=distance>1e-4*max(model.a_max,threshold)
                y=y[:,smooth]
                if not y.shape[1]:continue
                exact=canonical_jacobian(model,y)
                np.testing.assert_allclose(canonical_jacobian(model,y[:,0]),exact[:,:,0],atol=1e-13)
                finite=np.empty_like(exact)
                for k in range(model.dimension):
                    h=1e-7*np.maximum(1.,abs(y[k]))
                    upper=y.copy();lower=y.copy()
                    upper[k]+=h;lower[k]-=h
                    finite[:,k]=(model.rhs(0,upper)-model.rhs(0,lower))/(2*h)
                np.testing.assert_allclose(exact,finite,rtol=3e-5,atol=3e-7)
                half=model.dimension//2
                symplectic=np.block([[np.zeros((half,half)),np.eye(half)],[-np.eye(half),np.zeros((half,half))]])
                hessian=np.einsum('ab,bcn->acn',symplectic,exact)
                np.testing.assert_allclose(hessian,hessian.transpose(1,0,2),rtol=1e-12,atol=1e-12)


if __name__=='__main__':unittest.main()
