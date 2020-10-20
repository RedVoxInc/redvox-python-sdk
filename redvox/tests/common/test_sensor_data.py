"""
tests for sensor data and sensor metadata objects
"""
import unittest
import pandas as pd
import numpy as np

from redvox.common import date_time_utils as dtu
from redvox.common.sensor_data import SensorData


class SensorDataTest(unittest.TestCase):
    def setUp(self):
        timestamps = [120, 60, 80, 100, 40, 140, 20, 160, 180]
        sensor_data = [-20, 15, 50, -5, 20, -15, 10, 74, 111]
        test_data = [75, 12, 86, 22, 200, 52, 99, 188, 121]
        self.even_sensor = SensorData("test", pd.DataFrame(np.transpose([timestamps, sensor_data, test_data]),
                                                           columns=["timestamps", "microphone", "test_data"]),
                                      1 / dtu.microseconds_to_seconds(20), dtu.microseconds_to_seconds(20), 0, True)
        timestamps = [14, 25, 31, 65, 74, 83, 97, 111, 120]
        sample_interval = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
        sample_interval_std = dtu.microseconds_to_seconds(float(np.std(np.diff(timestamps))))
        self.uneven_sensor = SensorData("test", pd.DataFrame(np.transpose([timestamps, sensor_data, test_data]),
                                                             columns=["timestamps", "barometer", "test_data"]),
                                        1 / sample_interval, sample_interval, sample_interval_std, False)

    def test_sample_rate(self):
        self.assertAlmostEqual(self.even_sensor.sample_rate, 50000.0, 1)
        self.assertAlmostEqual(self.uneven_sensor.sample_rate, 75471.7, 1)

    def test_sample_interval_s(self):
        self.assertEqual(self.even_sensor.sample_interval_s, .00002)
        self.assertAlmostEqual(self.uneven_sensor.sample_interval_s, .000013, 6)

    def test_sample_interval_std_s(self):
        self.assertEqual(self.even_sensor.sample_interval_std_s, 0)
        self.assertAlmostEqual(self.uneven_sensor.sample_interval_std_s, .000008, 6)

    def test_is_sample_rate_fixed(self):
        self.assertTrue(self.even_sensor.is_sample_rate_fixed)
        self.assertFalse(self.uneven_sensor.is_sample_rate_fixed)

    def test_append_data(self):
        self.even_sensor.append_data(pd.DataFrame([[0, np.nan, np.nan]],
                                                  columns=["timestamps", "microphone", "test_data"]))
        self.assertEqual(len(self.even_sensor.get_channel("test_data")), 10)
        self.assertEqual(len(self.even_sensor.get_valid_channel_values("test_data")), 9)
        self.even_sensor.append_data(pd.DataFrame([[200, 10, 69]],
                                                  columns=["timestamps", "microphone", "test_data"]))
        self.assertEqual(len(self.even_sensor.get_channel("test_data")), 11)
        self.assertEqual(len(self.even_sensor.get_valid_channel_values("test_data")), 10)
        self.uneven_sensor.append_data(pd.DataFrame([[151, 10, 69]],
                                                    columns=["timestamps", "microphone", "test_data"]))
        self.assertEqual(len(self.uneven_sensor.get_channel("test_data")), 10)
        self.assertEqual(len(self.uneven_sensor.get_valid_channel_values("test_data")), 10)
        self.assertAlmostEqual(self.uneven_sensor.sample_interval_s, .000015, 6)
        self.assertAlmostEqual(self.uneven_sensor.sample_interval_std_s, .00001, 6)

    def test_is_sample_interval_invalid(self):
        self.assertFalse(self.even_sensor.is_sample_interval_invalid())

    def test_samples(self):
        self.assertEqual(len(self.even_sensor.samples()), 2)
        self.assertEqual(len(self.even_sensor.samples()[0]), 9)

    def test_num_samples(self):
        self.assertEqual(self.even_sensor.num_samples(), 9)

    def test_get_channel(self):
        self.assertEqual(len(self.even_sensor.get_channel("test_data")), 9)
        self.assertRaises(ValueError, self.even_sensor.get_channel, "not_exist")
        self.even_sensor.append_data(pd.DataFrame([[0, np.nan, np.nan]],
                                                  columns=["timestamps", "microphone", "test_data"]))
        self.assertEqual(len(self.even_sensor.get_channel("test_data")), 10)
        self.assertEqual(len(self.even_sensor.get_valid_channel_values("test_data")), 9)

    def test_data_timestamps(self):
        self.assertEqual(len(self.even_sensor.data_timestamps()), 9)

    def test_first_data_timestamp(self):
        self.assertEqual(self.even_sensor.first_data_timestamp(), 20)

    def test_last_data_timestamp(self):
        self.assertEqual(self.even_sensor.last_data_timestamp(), 180)

    def test_data_duration_s(self):
        self.assertEqual(self.even_sensor.data_duration_s(), .00016)

    def test_data_fields(self):
        self.assertEqual(len(self.even_sensor.data_fields()), 3)
        self.assertEqual(self.even_sensor.data_fields()[0], "timestamps")
        self.assertEqual(self.even_sensor.data_fields()[1], "microphone")

    def test_update_data_timestamps(self):
        self.even_sensor.update_data_timestamps(100)
        self.assertEqual(self.even_sensor.first_data_timestamp(), 120)
        self.assertEqual(self.even_sensor.last_data_timestamp(), 280)
        self.even_sensor.update_data_timestamps(-100)
        self.assertEqual(self.even_sensor.first_data_timestamp(), 20)
        self.assertEqual(self.even_sensor.last_data_timestamp(), 180)

    # technically this is done any time timestamps are added during initialization or appending functions
    # so unless users are altering the dataframe directly, sort_by_data_timestamps() should always happen
    def test_sort_by_data_timestamps(self):
        self.even_sensor.sort_by_data_timestamps()
        self.assertEqual(self.even_sensor.data_timestamps()[1], 40)
        self.even_sensor.sort_by_data_timestamps(False)
        self.assertEqual(self.even_sensor.data_timestamps()[1], 160)
