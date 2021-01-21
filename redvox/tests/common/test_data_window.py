"""
tests for data window objects
"""
import unittest

import numpy as np
import pandas as pd

import redvox.tests as tests
import redvox.common.date_time_utils as dt
from redvox.common import data_window as dw


class DataWindowTest(unittest.TestCase):
    def setUp(self):
        self.input_dir = tests.TEST_DATA_DIR

    def test_data_window(self):
        datawindow = dw.DataWindow(input_dir=self.input_dir, structured_layout=False,
                                   station_ids={"1637650010", "0000000001"})
        self.assertEqual(len(datawindow.sensors), 2)
        self.assertIsNotNone(datawindow.get_sensor_from_station(dw.SensorType.AUDIO, "1637650010"))
        self.assertIsNotNone(datawindow.get_sensor_from_station(dw.SensorType.ACCELEROMETER, "1637650010"))
        self.assertIsNotNone(datawindow.get_sensor_from_station(dw.SensorType.MAGNETOMETER, "1637650010"))
        self.assertIsNotNone(datawindow.get_sensor_from_station(dw.SensorType.PRESSURE, "1637650010"))
        self.assertIsNotNone(datawindow.get_sensor_from_station(dw.SensorType.LOCATION, "1637650010"))
        test_sensor = datawindow.get_sensor_from_station(dw.SensorType.AUDIO, "0000000001")
        self.assertIsNotNone(test_sensor)
        self.assertEqual(test_sensor.num_samples(), 720001)
        test_sensor = datawindow.get_sensor_from_station(dw.SensorType.LOCATION, "0000000001")
        self.assertIsNotNone(test_sensor)
        self.assertEqual(test_sensor.num_samples(), 5)

    def test_dw_with_start_end(self):
        dw_with_start_end = dw.DataWindow(input_dir=self.input_dir, station_ids={"1637650010", "0000000001"},
                                          start_datetime=dt.datetime_from_epoch_seconds_utc(1597189455),
                                          end_datetime=dt.datetime_from_epoch_seconds_utc(1597189465),
                                          structured_layout=False)
        self.assertEqual(len(dw_with_start_end.sensors), 1)
        audio_sensor = dw_with_start_end.get_sensor_from_station(dw.SensorType.AUDIO, "0000000001")
        self.assertIsNotNone(audio_sensor)
        self.assertEqual(audio_sensor.num_samples(), 479986)
        loc_sensor = dw_with_start_end.get_sensor_from_station(dw.SensorType.LOCATION, "0000000001")
        self.assertIsNotNone(loc_sensor)
        self.assertEqual(loc_sensor.num_samples(), 4)

    def test_dw_invalid(self):
        dw_invalid = dw.DataWindow(input_dir=self.input_dir, station_ids={"does_not_exist"}, structured_layout=False)
        self.assertIsNone(dw_invalid.get_all_sensors_from_station("does_not_exist"))


class PadDataTest(unittest.TestCase):
    def setUp(self):
        timestamps = [dt.seconds_to_microseconds(40), dt.seconds_to_microseconds(50), dt.seconds_to_microseconds(60)]
        self.dataframe = pd.DataFrame(np.transpose([timestamps, [4, 5, 6]]), columns=["timestamps", "temp"])

    def test_pad_data(self):
        filled_dataframe = dw.pad_data(dt.seconds_to_microseconds(10), dt.seconds_to_microseconds(100),
                                       self.dataframe, dt.seconds_to_microseconds(10))
        self.assertEqual(filled_dataframe.shape, (10, 2))
        self.assertEqual(filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(20))
        self.assertEqual(filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(30))

    def test_pad_data_uneven_ends(self):
        filled_dataframe = dw.pad_data(dt.seconds_to_microseconds(10), dt.seconds_to_microseconds(100),
                                       self.dataframe, dt.seconds_to_microseconds(12))
        self.assertEqual(filled_dataframe.shape, (10, 2))
        self.assertEqual(filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(22))
        self.assertEqual(filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(34))
        self.assertEqual(filled_dataframe.loc[6, "timestamps"], dt.seconds_to_microseconds(64))
        self.assertEqual(filled_dataframe.loc[9, "timestamps"], dt.seconds_to_microseconds(100))


class FillGapTest(unittest.TestCase):
    def setUp(self):
        timestamps = [dt.seconds_to_microseconds(10), dt.seconds_to_microseconds(30), dt.seconds_to_microseconds(100)]
        self.dataframe = pd.DataFrame(np.transpose([timestamps, [1, 3, 10]]), columns=["timestamps", "temp"])

    def test_fill_gaps(self):
        filled_dataframe = dw.fill_gaps(self.dataframe, dt.seconds_to_microseconds(10), dt.seconds_to_microseconds(10))
        self.assertEqual(filled_dataframe.shape, (10, 2))
        self.assertEqual(filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(20))
        self.assertEqual(filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(30))

    def test_fill_gaps_long_interval(self):
        filled_dataframe = dw.fill_gaps(self.dataframe, dt.seconds_to_microseconds(20), dt.seconds_to_microseconds(10))
        self.assertEqual(filled_dataframe.shape, (6, 2))
        self.assertEqual(filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(30))
        self.assertEqual(filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(50))

    def test_fill_gaps_long_gap(self):
        filled_dataframe = dw.fill_gaps(self.dataframe, dt.seconds_to_microseconds(10), dt.seconds_to_microseconds(20))
        self.assertEqual(filled_dataframe.shape, (9, 2))
        self.assertEqual(filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(30))
        self.assertEqual(filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(40))


class CreateDatalessTimestampsDFTest(unittest.TestCase):
    def test_create_dataless_timestamps_df(self):
        base_df = pd.DataFrame([], columns=["timestamps", "data"])
        new_df = dw.create_dataless_timestamps_df(2000, 1000, base_df.columns, 7, False)
        self.assertEqual(new_df.loc[0, "timestamps"], 3000)
        self.assertEqual(new_df.loc[6, "timestamps"], 9000)
        new_df = dw.create_dataless_timestamps_df(8000, 1000, base_df.columns, 7, True)
        self.assertEqual(new_df.loc[0, "timestamps"], 7000)
        self.assertEqual(new_df.loc[6, "timestamps"], 1000)
