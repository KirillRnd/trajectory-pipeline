import json
from pathlib import Path
import unittest
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.irt import solve_irt
from trajectory_pipeline.verification import verify_irt

ROOT = Path(__file__).resolve().parents[1]


class RealIRTTests(unittest.TestCase):
    def test_real_venus_rendezvous_and_mars_flyby(self):
        configurations=json.loads((ROOT/'configs/irt_matrix.json').read_text(encoding='utf-8'))
        for index in (0,11):
            with self.subTest(case=configurations[index]['case_id']):
                result,diagnostics=solve_irt(Mission(**configurations[index]))
                self.assertIsNotNone(result,diagnostics)
                self.assertTrue(verify_irt(result)['passed'])
                self.assertNotIn('mass_kg',result.arrays)
                self.assertNotIn('fuel_kg',result.metadata)

    def test_budget_interrupts_difficult_real_shooting(self):
        configuration=json.loads((ROOT/'configs/irt_matrix.json').read_text(encoding='utf-8'))[9]
        configuration['solver']={'budget_s':.02,'attempt_budget_s':.02}
        result,diagnostics=solve_irt(Mission(**configuration))
        self.assertIsNone(result)
        self.assertLess(diagnostics['elapsed_s'],2.)
        self.assertTrue(any('time budget' in x.get('message','') for x in diagnostics['attempts']))


if __name__=='__main__':
    unittest.main()
