from pathlib import Path
import json
import unittest
from trajectory_pipeline.data import Trajectory,write_json,sha256
from trajectory_pipeline.visualization import _presentation,render

ROOT=Path('/workspace')


class RealPlotLabelsTests(unittest.TestCase):
    def test_final_and_intermediate_models_have_distinct_labels(self):
        root=ROOT/'data/benchmarks/parameter_study_v1'
        final=Trajectory.load(root/'earth_venus_2032__exhaust_x2/final')
        title,caption=_presentation(final)
        self.assertIn('ПСИ',title)
        for text in ('F=25 мН','c=40 км/с','m₀=156 кг','2032-11-01','TDB','390.8 сут'):
            self.assertIn(text,caption)
        partial=Trajectory.load(root/'earth_apophis_2029__mass_x2/stage_psi/limit/point_0018')
        title,caption=_presentation(partial)
        self.assertNotIn('ПСИ',title)
        self.assertIn('промежуточная',title)
        self.assertIn('F=25 мН',caption)
        self.assertIn('α=0.5',caption)
        self.assertIn('β=1',caption)
        self.assertIn('Модель: F=',caption)
        historical=Trajectory.load(ROOT/'data/references/ummp156')
        self.assertEqual(_presentation(historical),(historical.metadata['title'],''))
        # Prepare review artifacts from each real class without optimization.
        out=ROOT/'runs/visualization_release_v1/review'
        manifests=[]
        for name,result in (('final',final),('intermediate',partial),('historical',historical)):
            render(result,out/name)
            manifests.append(dict(kind=name,arrays_sha256=result.metadata['arrays_sha256'],
                                  previews={p.name:sha256(p) for p in (out/name).glob('*.jpg')}))
        write_json(out/'manifest.json',manifests)


if __name__=='__main__':unittest.main()
