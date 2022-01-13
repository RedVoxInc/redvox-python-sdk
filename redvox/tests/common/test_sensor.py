"""
tests for sensor data and sensor metadata objects
"""
import unittest

import numpy as np

from redvox.common import date_time_utils as dtu
from redvox.common.sensor_data import SensorData, SensorType


class SensorDataTest(unittest.TestCase):
    def setUp(self):
        timestamps = [120., 60., 80., 100., 40., 140., 20., 160., 180.]
        sensor_data = [-20., 15., 50., -5., 20., -15., 10., 74., 111.]
        test_data = [75., 12., 86., 22., 200., 52., 99., 188., 121.]
        self.even_sensor = SensorData.from_dict(
            "test",
            dict(zip(["timestamps", "unaltered_timestamps", "microphone", "test_data"],
                     [timestamps, timestamps, sensor_data, test_data])),
            SensorType.AUDIO,
            1 / dtu.microseconds_to_seconds(20),
            dtu.microseconds_to_seconds(20),
            0,
            True,
        )
        timestamps = [14., 25., 31., 65., 74., 83., 97., 111., 120.]
        sample_interval = dtu.microseconds_to_seconds(
            float(np.mean(np.diff(timestamps)))
        )
        sample_interval_std = dtu.microseconds_to_seconds(
            float(np.std(np.diff(timestamps)))
        )
        self.uneven_sensor = SensorData.from_dict(
            "test",
            dict(zip(["timestamps", "unaltered_timestamps", "barometer", "test_data"],
                     [timestamps, timestamps, sensor_data, test_data])),
            SensorType.PRESSURE,
            1 / sample_interval,
            sample_interval,
            sample_interval_std,
            False,
        )

    def test_empty(self):
        self.empty_sensor = SensorData("empty")
        self.assertEqual(self.empty_sensor.errors().get_num_errors(), 0)
        self.assertEqual(self.empty_sensor.num_samples(), 0)
        self.assertEqual(len(self.empty_sensor.data_channels()), 0)
        self.assertEqual(len(self.empty_sensor.get_data_channel("failure")), 0)
        self.assertEqual(self.empty_sensor.errors().get_num_errors(), 1)

    def test_name(self):
        self.assertEqual(self.even_sensor.name, "test")
        self.assertEqual(self.uneven_sensor.name, "test")

    def test_data_df(self):
        self.assertEqual(self.even_sensor.data_df().size, 36)
        self.assertEqual(self.even_sensor.data_df().ndim, 2)
        self.assertTrue("test_data" in self.uneven_sensor.data_df().columns)

    def test_sample_rate(self):
        self.assertAlmostEqual(self.even_sensor.sample_rate_hz(), 50000.0, 1)
        self.assertAlmostEqual(self.uneven_sensor.sample_rate_hz(), 75471.7, 1)

    def test_sample_interval_s(self):
        self.assertEqual(self.even_sensor.sample_interval_s(), 0.00002)
        self.assertAlmostEqual(self.uneven_sensor.sample_interval_s(), 0.000013, 6)

    def test_sample_interval_std_s(self):
        self.assertEqual(self.even_sensor.sample_interval_std_s(), 0)
        self.assertAlmostEqual(self.uneven_sensor.sample_interval_std_s(), 0.000008, 6)

    def test_is_sample_rate_fixed(self):
        self.assertTrue(self.even_sensor.is_sample_rate_fixed())
        self.assertFalse(self.uneven_sensor.is_sample_rate_fixed())

    def test_empty_data(self):
        empty = SensorData.from_dict("", {"": []}, is_sample_rate_fixed=True)
        self.assertEqual(empty.errors().get_num_errors(), 1)
        self.assertEqual(empty.type().value, SensorType.UNKNOWN_SENSOR.value)
        self.assertTrue(np.isnan(empty.first_data_timestamp()))
        self.assertTrue(np.isnan(empty.last_data_timestamp()))
        self.assertEqual(empty.num_samples(), 0)
        self.assertEqual(len(empty.data_channels()), 0)
        self.assertEqual(len(empty.get_data_channel("failure")), 0)
        self.assertEqual(empty.errors().get_num_errors(), 2)

    def test_invalid_data(self):
        invalid = SensorData.from_dict(
            "",
            {"not_timestamps": [1]},
            is_sample_rate_fixed=True,
        )
        self.assertTrue(invalid.errors().get_num_errors() == 1)

    def test_append_data(self):
        self.even_sensor.append_data(
            [[0.], [0.], [np.nan], [np.nan]]
        )
        self.assertEqual(len(self.even_sensor.get_data_channel("test_data")), 10)
        self.assertEqual(
            len(self.even_sensor.get_valid_data_channel_values("test_data")), 9
        )
        self.even_sensor.append_data(
            [[200.], [200.], [10.], [69.]]
        )
        self.assertEqual(len(self.even_sensor.get_data_channel("test_data")), 11)
        self.assertEqual(
            len(self.even_sensor.get_valid_data_channel_values("test_data")), 10
        )
        self.uneven_sensor.append_data(
            [[151.], [151.], [10.], [69.]],
            True,
        )
        self.assertEqual(len(self.uneven_sensor.get_data_channel("test_data")), 10)
        self.assertEqual(
            len(self.uneven_sensor.get_valid_data_channel_values("test_data")), 10
        )
        self.assertAlmostEqual(self.uneven_sensor.sample_interval_s(), 0.000015, 6)
        self.assertAlmostEqual(self.uneven_sensor.sample_interval_std_s(), 0.00001, 6)

    def test_is_sample_interval_invalid(self):
        self.assertFalse(self.even_sensor.is_sample_interval_invalid())
        self.even_sensor.append_data(
            [[0.], [0.], [np.nan], [np.nan]]
        )
        self.assertEqual(len(self.even_sensor.get_data_channel("test_data")), 10)
        self.assertEqual(
            len(self.even_sensor.get_valid_data_channel_values("test_data")), 9
        )

    def test_samples(self):
        self.assertEqual(len(self.even_sensor.samples()), 2)
        self.assertEqual(len(self.even_sensor.samples()[0]), 9)

    def test_num_samples(self):
        self.assertEqual(self.even_sensor.num_samples(), 9)

    def test_get_channel(self):
        self.assertEqual(len(self.even_sensor.get_data_channel("test_data")), 9)
        empty_channel = self.even_sensor.get_data_channel("not_exist")
        self.assertEqual(len(empty_channel), 0)
        self.assertEqual(self.even_sensor.errors().get_num_errors(), 1)
        self.even_sensor.append_data(
            [[0.], [0.], [np.nan], [np.nan]]
        )
        self.assertEqual(len(self.even_sensor.get_data_channel("test_data")), 10)

    def test_get_valid_channel_values(self):
        empty_channel = self.even_sensor.get_data_channel("not_exist")
        self.assertEqual(len(empty_channel), 0)
        self.assertEqual(self.even_sensor.errors().get_num_errors(), 1)
        self.assertEqual(
            len(self.even_sensor.get_valid_data_channel_values("test_data")), 9
        )

    def test_data_timestamps(self):
        self.assertEqual(len(self.even_sensor.data_timestamps()), 9)

    def test_first_data_timestamp(self):
        self.assertEqual(self.even_sensor.first_data_timestamp(), 20)

    def test_last_data_timestamp(self):
        self.assertEqual(self.even_sensor.last_data_timestamp(), 180)

    def test_data_fields(self):
        self.assertEqual(len(self.even_sensor.data_channels()), 4)
        self.assertEqual(self.even_sensor.data_channels()[0], "timestamps")
        self.assertEqual(self.even_sensor.data_channels()[2], "microphone")

    def test_organize_and_update_stats(self):
        self.even_sensor.organize_and_update_stats(self.even_sensor.pyarrow_table())
        self.assertEqual(self.even_sensor.data_timestamps()[1], 40)
        self.assertAlmostEqual(self.even_sensor.sample_rate_hz(), 50000.0, 1)
        self.assertEqual(self.even_sensor.sample_interval_std_s(), 0)
        timestamps = [120, 111, 97, 83, 74, 65, 31, 25, 14]
        test_data = [75, 12, 86, 22, 200, 52, 99, 188, 121]
        sample_interval = dtu.microseconds_to_seconds(
            float(np.mean(np.diff(timestamps)))
        )
        sample_interval_std = dtu.microseconds_to_seconds(
            float(np.std(np.diff(timestamps)))
        )
        uneven_sensor = SensorData.from_dict(
            "test",
            dict(zip(["timestamps", "test_data"], [timestamps, test_data])),
            SensorType.UNKNOWN_SENSOR,
            1 / sample_interval,
            sample_interval,
            sample_interval_std,
            False,
        )
        uneven_sensor.organize_and_update_stats(uneven_sensor.pyarrow_table())
        self.assertAlmostEqual(uneven_sensor.sample_interval_s(), 0.000013, 6)
        self.assertAlmostEqual(uneven_sensor.sample_interval_std_s(), 0.000008, 6)

    # technically this is done any time timestamps are added during initialization or appending functions
    # so unless users are altering the data directly, sort_by_data_timestamps() should always happen
    def test_sort_by_data_timestamps(self):
        self.even_sensor.sort_by_data_timestamps(self.even_sensor.pyarrow_table())
        self.assertEqual(self.even_sensor.data_timestamps()[1], 40)
        self.even_sensor.sort_by_data_timestamps(self.even_sensor.pyarrow_table(), ascending=False)
        self.assertEqual(self.even_sensor.data_timestamps()[1], 160)

    def test_create_read_update_audio_sensor(self):
        audio_sensor = SensorData.from_dict(
            "test_audio",
            dict(zip(["timestamps", "microphone"], [[10, 20, 30, 40], [1, 2, 3, 4]])),
            SensorType.AUDIO,
            1,
            True,
        )
        self.assertEqual(audio_sensor.sample_rate_hz(), 1)
        self.assertEqual(audio_sensor.num_samples(), 4)
        self.assertIsInstance(audio_sensor.get_data_channel("microphone"), np.ndarray)
        empty_channel = audio_sensor.get_data_channel("do_not_exist")
        self.assertEqual(len(empty_channel), 0)
        self.assertEqual(audio_sensor.errors().get_num_errors(), 1)
        self.assertEqual(audio_sensor.first_data_timestamp(), 10)
        self.assertEqual(audio_sensor.last_data_timestamp(), 40)
