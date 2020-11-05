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
        datawindow = dw.DataWindow(input_dir=self.input_dir, station_ids={"1637650010", "0000000001"},
                                   structured_layout=False)
        self.assertEqual(len(datawindow.stations.station_id_uuid_to_stations), 2)
        test_station = datawindow.stations.get_station("1637650010")
        self.assertTrue(test_station.has_audio_sensor())
        self.assertTrue(test_station.has_accelerometer_sensor())
        self.assertTrue(test_station.has_magnetometer_sensor())
        self.assertTrue(test_station.has_barometer_sensor())
        self.assertTrue(test_station.has_location_sensor())
        test_station = datawindow.stations.get_station("0000000001")
        self.assertTrue(test_station.has_audio_sensor())
        self.assertEqual(test_station.audio_sensor().num_samples(), 720000)
        self.assertTrue(test_station.has_location_sensor())
        self.assertEqual(test_station.location_sensor().num_samples(), 4)

    def test_dw_with_start_end(self):
        dw_with_start_end = dw.DataWindow(input_dir=self.input_dir, station_ids={"1637650010", "0000000001"},
                                          start_datetime=dt.datetime_from_epoch_seconds_utc(1597189455),
                                          end_datetime=dt.datetime_from_epoch_seconds_utc(1597189465),
                                          structured_layout=False)
        self.assertEqual(len(dw_with_start_end.stations.station_id_uuid_to_stations), 1)
        test_station = dw_with_start_end.stations.get_station("0000000001")
        self.assertTrue(test_station.has_audio_sensor())
        self.assertEqual(test_station.audio_sensor().num_samples(), 479986)
        self.assertTrue(test_station.has_location_sensor())
        self.assertEqual(test_station.location_sensor().num_samples(), 4)

    def test_dw_invalid(self):
        dw_invalid = dw.DataWindow(input_dir=self.input_dir, station_ids={"does_not_exist"}, structured_layout=False)
        self.assertEqual(len(dw_invalid.stations.station_id_uuid_to_stations), 0)

    def test_station_params(self):
        stress_test_dir = "/Users/tyler/Documents/stress_test_files"
        dw_invalid = dw.DataWindow(input_dir=stress_test_dir, station_ids=None, structured_layout=False)
        self.assertEqual(len(dw_invalid.stations.station_id_uuid_to_stations), 3)
        dw_invalid = dw.DataWindow(input_dir=stress_test_dir, station_ids=set(), structured_layout=False)
        self.assertEqual(len(dw_invalid.stations.station_id_uuid_to_stations), 3)
        dw_invalid = dw.DataWindow(input_dir=stress_test_dir, structured_layout=False)
        self.assertEqual(len(dw_invalid.stations.station_id_uuid_to_stations), 3)


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


class StressDataWindowTest(unittest.TestCase):
    def test_stress(self):
        start_year = 2020
        start_month = 7
        start_day = 11
        start_hour = 19
        start_minute = 50
        start_second = 0
        duration_seconds = 1200
        input_dir = "/Users/tyler/Documents/pipeline_tests/"
        start_datetime = dt.datetime_from(start_year, start_month, start_day, start_hour, start_minute, start_second)
        end_datetime = start_datetime + dt.timedelta(seconds=duration_seconds)
        start = dt.now()
        stress_window = dw.DataWindow(input_dir=input_dir, start_datetime=start_datetime, end_datetime=end_datetime,
                                      station_ids=None)
        end = dt.now()
        print(f"data read: {end - start}")
        self.assertTrue(True)
