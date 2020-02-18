"""
Redvox file helper test module
"""

import unittest

from redvox.common import file_statistics


class RdvxFileHelperTests(unittest.TestCase):
    """
    redvox file helper test case
    """

    def test_get_file_stats(self):
        self.assertEqual((4096, 51.20), file_statistics.get_file_stats(80))
        self.assertEqual((4096, 51.20), file_statistics.get_file_stats(80.))
        self.assertEqual((32768, 40.96), file_statistics.get_file_stats(800))
        self.assertEqual((32768, 40.96), file_statistics.get_file_stats(800.))
        self.assertEqual((262144, 32.768), file_statistics.get_file_stats(8000))
        self.assertEqual((262144, 32.768), file_statistics.get_file_stats(8000.))
        self.assertRaises(ValueError, file_statistics.get_file_stats, 50)

    def test__get_duration_seconds_from_sample_rate(self):
        self.assertEqual(51.2, file_statistics.get_duration_seconds_from_sample_rate(80))
        self.assertEqual(40.96, file_statistics.get_duration_seconds_from_sample_rate(800))
        self.assertEqual(32.768, file_statistics.get_duration_seconds_from_sample_rate(8000))
        self.assertRaises(ValueError, file_statistics.get_duration_seconds_from_sample_rate, 100)
