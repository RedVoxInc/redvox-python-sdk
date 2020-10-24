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

    def test_get_station(self):
        test_station = self.datawindow.stations.get_station("0000000001")
        self.assertTrue(test_station.has_audio_sensor())
        self.assertEqual(test_station.audio_sensor().num_samples(), 720000)

    def test_read_data_window(self):
        self.assertTrue(len(self.datawindow.stations.station_id_uuid_to_stations), 2)
        test_station = self.datawindow.stations.get_station("0000000001")
        self.assertTrue(test_station.has_location_sensor())
        self.assertEqual(test_station.location_sensor().num_samples(), 4)
        test_station = self.datawindow.stations.get_station("1637650010")
        self.assertTrue(test_station.has_audio_sensor())
        self.assertTrue(test_station.has_accelerometer_sensor())
        self.assertTrue(test_station.has_magnetometer_sensor())
        self.assertTrue(test_station.has_barometer_sensor())
        self.assertTrue(test_station.has_location_sensor())


class GapFillerTest(unittest.TestCase):
    def setUp(self):
        timestamps = [dt.seconds_to_microseconds(10), dt.seconds_to_microseconds(30), dt.seconds_to_microseconds(100)]
        self.dataframe = pd.DataFrame(np.transpose([timestamps, [1, 3, 10]]), columns=["timestamps", "temp"])

    def test_gap_filler(self):
        filled_dataframe = dw.fill_gaps(self.dataframe, 10)
        self.assertEqual(filled_dataframe.shape, (10, 2))


class CreateDatalessTimestampsDFTest(unittest.TestCase):
    def test_create_dataless_timestamps_df(self):
        base_df = pd.DataFrame([], columns=["timestamps", "data"])
        new_df = dw.create_dataless_timestamps_df(2000, 1000, base_df.columns, 7, False)
        self.assertEqual(new_df.loc[0, "timestamps"], 3000)
        self.assertEqual(new_df.loc[6, "timestamps"], 9000)
        new_df = dw.create_dataless_timestamps_df(8000, 1000, base_df.columns, 7, True)
        self.assertEqual(new_df.loc[0, "timestamps"], 7000)
        self.assertEqual(new_df.loc[6, "timestamps"], 1000)
