"""
redvox stats helper test module
"""
import unittest
import numpy as np

from redvox.common import stats_helper


class RdvxStatsContainerTests(unittest.TestCase):
    def setUp(self):
        self.sc = stats_helper.StatsContainer("sc")
        counts = [100, 200, 300, 400, 500]

        for i in range(len(counts)):
            value = counts[i]
            data = np.ndarray((value,), int)
            for k in range(value):
                data[k] = (120 / (i + 1)) - np.sqrt(k)
            self.sc.add(float(np.mean(data)), float(np.std(data)), value)

    def test_add(self):
        self.sc.add(0, 0, 0)
        self.assertEqual(len(self.sc.count_array), 6)
        self.assertEqual(len(self.sc.mean_array), 6)
        self.assertEqual(len(self.sc.std_dev_array), 6)
        self.assertEqual(self.sc.mean_of_means(), 27.024)
        self.assertAlmostEqual(self.sc.variance_of_means(), 707.53, 2)
        self.assertAlmostEqual(self.sc.mean_of_variance(), 20.8, 2)
        self.assertAlmostEqual(self.sc.total_variance(), 728.33, 2)
        self.assertAlmostEqual(self.sc.total_std_dev(), 26.99, 2)

    def test_mean_of_means(self):
        self.assertEqual(self.sc.mean_of_means(), 27.024)

    def test_variance_of_means(self):
        self.assertAlmostEqual(self.sc.variance_of_means(), 707.53, 2)

    def test_mean_of_variance(self):
        self.assertAlmostEqual(self.sc.mean_of_variance(), 20.8, 2)

    def test_total_variance(self):
        self.assertAlmostEqual(self.sc.total_variance(), 728.33, 2)

    def test_total_std_dev(self):
        self.assertAlmostEqual(self.sc.total_std_dev(), 26.99, 2)

    def test_empty_stats(self):
        sc2 = stats_helper.StatsContainer("empty")
        sc2.add(0, 0, 0)
        self.assertTrue(np.isnan(sc2.mean_of_means()))
        self.assertTrue(np.isnan(sc2.variance_of_means()))
        self.assertTrue(np.isnan(sc2.mean_of_variance()))
        self.assertTrue(np.isnan(sc2.total_variance()))
        self.assertTrue(np.isnan(sc2.total_std_dev()))
