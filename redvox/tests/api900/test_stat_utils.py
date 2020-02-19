import numpy

import redvox.api900.stat_utils as stat_utils
from redvox.tests import ArraysTestCase


class ModuleFunctionTests(ArraysTestCase):
    def test__calc_utils(self):
        test_values = numpy.array([1.0, 2.0, 3.0])
        test_std, test_mean, test_med = stat_utils.calc_utils(test_values)
        self.assertEqual(test_mean, 2.0)
        self.assertAlmostEqual(test_std, 0.816496580927726, 15)
        self.assertEqual(test_med, 2.0)

    def test__calc_utils_timeseries(self):
        test_values = numpy.array([10.0, 20.0, 40.0, 70.0])
        # the timeseries array is the diff of test_values and will end up being [10, 20, 30]
        test_std, test_mean, test_med = stat_utils.calc_utils_timeseries(test_values)
        self.assertEqual(test_mean, 20.0)
        self.assertAlmostEqual(test_std, 8.16496580927726, 14)
        self.assertEqual(test_med, 20.0)
