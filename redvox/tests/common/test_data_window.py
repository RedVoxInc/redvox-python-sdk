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
        input_dir = tests.TEST_DATA_DIR
        self.datawindow = dw.DataWindow(input_dir=input_dir, station_ids={"1637650010", "0000000001"},
                                        structured_layout=False)
        self.dw_with_start_end = dw.DataWindow(input_dir=input_dir, station_ids={"1637650010", "0000000001"},
                                               start_datetime=dt.datetime_from_epoch_seconds_utc(1597189455),
                                               end_datetime=dt.datetime_from_epoch_seconds_utc(1597189465),
                                               structured_layout=False)
        self.dw_invalid = dw.DataWindow(input_dir=input_dir, station_ids={"does_not_exist"}, structured_layout=False)

    def test_data_window(self):
        self.assertEqual(len(self.datawindow.stations.station_id_uuid_to_stations), 2)
        test_station = self.datawindow.stations.get_station("1637650010")
        self.assertTrue(test_station.has_audio_sensor())
        self.assertTrue(test_station.has_accelerometer_sensor())
        self.assertTrue(test_station.has_magnetometer_sensor())
        self.assertTrue(test_station.has_barometer_sensor())
        self.assertTrue(test_station.has_location_sensor())
        test_station = self.datawindow.stations.get_station("0000000001")
        self.assertTrue(test_station.has_audio_sensor())
        self.assertEqual(test_station.audio_sensor().num_samples(), 720000)
        self.assertTrue(test_station.has_location_sensor())
        self.assertEqual(test_station.location_sensor().num_samples(), 4)

    def test_dw_with_start_end(self):
        self.assertEqual(len(self.dw_with_start_end.stations.station_id_uuid_to_stations), 1)
        test_station = self.dw_with_start_end.stations.get_station("0000000001")
        self.assertTrue(test_station.has_audio_sensor())
        self.assertEqual(test_station.audio_sensor().num_samples(), 479986)
        self.assertTrue(test_station.has_location_sensor())
        self.assertEqual(test_station.location_sensor().num_samples(), 5)

    def test_dw_invalid(self):
        self.assertEqual(len(self.dw_invalid.stations.station_id_uuid_to_stations), 0)


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
