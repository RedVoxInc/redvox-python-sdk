"""
tests for loading sensor data
"""
import unittest

import pyarrow as pa
import numpy as np

from redvox.common.sensor_data import SensorType
from redvox.common import sensor_reader_utils as sdru


class EmptySensorTest(unittest.TestCase):
    def test_empty_sensor(self):
        empty_sensor = sdru.get_empty_sensor("empty")
        self.assertEqual(empty_sensor.num_samples(), 0)
        self.assertTrue(np.isnan(empty_sensor.sample_rate_hz()))
        self.assertEqual(empty_sensor.type().value, SensorType.UNKNOWN_SENSOR.value)


class SampleStatisticsTest(unittest.TestCase):
    def test_sample_stats(self):
        new_df = pa.Table.from_pydict({"timestamps": [10000, 20000, 30000, 40000, 50000]})
        rate, interval, intvl_std = sdru.get_sample_statistics(new_df)
        self.assertEqual(rate, 1e2)
        self.assertEqual(interval, 1e-2)
        self.assertEqual(intvl_std, 0)
