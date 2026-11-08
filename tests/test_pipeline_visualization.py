"""Saved real missions must remain renderable without any numerical solver."""
from pathlib import Path
from contextlib import ExitStack
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from trajectory_pipeline.data import Trajectory,sha256
from trajectory_pipeline.visualization import render

ROOT=Path(__file__).resolve().parents[1]


class StandaloneVisualizationTests(unittest.TestCase):
    def test_distinct_real_engines_render_offline_without_recalculation(self):
        cases=('earth_venus_2032__exhaust_x2','earth_mars_2028__thrust_x2')
        for case in cases:
            folder=ROOT/'data/benchmarks/parameter_study_v1'/case/'final'
            with self.subTest(case=case),tempfile.TemporaryDirectory() as temporary:
                trajectory=Trajectory.load(folder)
                before={p.name:sha256(p) for p in folder.iterdir() if p.is_file()}
                with ExitStack() as guards:
                    for name in ('trajectory_pipeline.ephemerides.Ephemerides.state',
                                 'trajectory_pipeline.runner.run_irt',
                                 'trajectory_pipeline.departure.run_departure',
                                 'trajectory_pipeline.pazov.run_pazov',
                                 'trajectory_pipeline.psi.run_psi'):
                        guards.enter_context(patch(name,side_effect=AssertionError('Rendering cannot call '+name)))
                    render(trajectory,temporary)
                self.assertEqual(before,{p.name:sha256(p) for p in folder.iterdir() if p.is_file()})
                for stem in ('trajectory','trajectory_3d','profiles'):
                    for suffix in ('.svg','.png'):
                        self.assertGreater((Path(temporary)/(stem+suffix)).stat().st_size,1000)
                    preview=Path(temporary)/(stem+'_preview.jpg')
                    with Image.open(preview) as image:
                        self.assertEqual(image.format,'JPEG')
                        self.assertLessEqual(max(image.size),1600)
                    self.assertLessEqual(preview.stat().st_size,200*1024)


if __name__=='__main__':unittest.main()
