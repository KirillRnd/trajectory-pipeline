from pathlib import Path
import unittest
import tempfile
from trajectory_pipeline.data import Trajectory
from trajectory_pipeline.visualization import _presentation,render

ROOT=Path(__file__).resolve().parents[1]


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
        with tempfile.TemporaryDirectory() as temporary:
            for name,result in (('final',final),('intermediate',partial),('historical',historical)):
                render(result,Path(temporary)/name)


if __name__=='__main__':unittest.main()
