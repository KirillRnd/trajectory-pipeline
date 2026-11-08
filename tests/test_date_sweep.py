import unittest

from trajectory_pipeline.date_sweep import fuel_outliers


class FuelOutlierTests(unittest.TestCase):
    def test_spike_does_not_flag_its_neighbors(self):
        dates = list(range(9))
        rows = [dict(status='completed', fuel_kg=20. + .2 * day) for day in dates]
        rows[4]['fuel_kg'] += 3.
        flags = fuel_outliers(dates, rows, .5, .05)
        self.assertEqual(set(flags), {4})
        self.assertAlmostEqual(flags[4]['residual_kg'], 3.)

    def test_uses_actual_date_spacing_when_a_fast_solve_fails(self):
        dates = [0, 1, 3, 5, 8]
        rows = [dict(status='completed', fuel_kg=20. + .3 * day) for day in dates]
        rows[2] = dict(status='failed')
        self.assertEqual(fuel_outliers(dates, rows, .01, 0.), {})

    def test_two_verified_dates_do_not_define_an_outlier(self):
        rows = [dict(status='completed', fuel_kg=1.), dict(status='completed', fuel_kg=100.)]
        self.assertEqual(fuel_outliers([0, 1], rows, 0., 0.), {})
