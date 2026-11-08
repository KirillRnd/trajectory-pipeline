from pathlib import Path
import unittest
from trajectory_pipeline.diagnostics import prepare_step

ROOT=Path(__file__).resolve().parents[1]/'data/benchmarks'


class SavedStepDiagnosticsTests(unittest.TestCase):
    def test_failed_real_fuel_input_keeps_physical_parameters(self):
        case=ROOT/'parameter_study_analytic_v1/earth_ceres_2030__reference'
        mission,request,source,previous,model,trial=prepare_step(case,'fuel')
        self.assertEqual(trial,.2)
        self.assertEqual(model.alpha,.6)
        self.assertEqual(model.beta,1)
        self.assertEqual(mission.mass_kg,156)
        self.assertEqual(source.metadata['mission']['spacecraft'],mission.spacecraft)
        self.assertEqual(request['mission']['launch_tdb'],mission.launch_tdb)
        self.assertEqual(previous.metadata['bounded_model']['alpha'],.5)

    def test_mass_and_thrust_diagnostics_use_recorded_common_profiles(self):
        for key,phase in (('earth_ceres_2030__thrust_x2','mass'),('earth_mars_2028__mass_x2','limit')):
            with self.subTest(case=key):
                mission,request,source,previous,model,trial=prepare_step(ROOT/'parameter_study_analytic_v1'/key,phase)
                if phase=='mass':self.assertEqual(model.beta,trial)
                else:
                    self.assertEqual(model.beta,1)
                    self.assertLessEqual(model.a_max,previous.metadata['bounded_model']['a_max'])
                self.assertEqual(source.metadata['mission']['spacecraft'],mission.spacecraft)


if __name__=='__main__':unittest.main()
