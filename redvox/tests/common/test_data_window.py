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
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.TEST_DATA_DIR

    def test_data_window_simple(self):
        datawindow = dw.DataWindow(
            input_dir=self.input_dir,
            structured_layout=False
        )
        self.assertEqual(len(datawindow.stations), 3)
        self.assertEqual(len(datawindow.station_ids), 3)
        self.assertTrue("1637680001" in datawindow.station_ids)

    def test_data_window(self):
        datawindow = dw.DataWindow(
            input_dir=self.input_dir,
            structured_layout=False,
            station_ids=["1637650010", "0000000001"],
        )
        self.assertEqual(len(datawindow.stations), 2)
        test_station = datawindow.get_station("1637650010")
        self.assertTrue(test_station.is_timestamps_updated)
        self.assertNotEqual(test_station.first_data_timestamp,
                            test_station.audio_sensor().get_data_channel("unaltered_timestamps")[0])
        self.assertIsNotNone(datawindow.get_station("1637650010").audio_sensor())
        test_sensor = datawindow.get_station("1637650010").accelerometer_sensor()
        self.assertEqual(test_sensor.num_samples(), 641)
        test_sensor = datawindow.get_station("0000000001").audio_sensor()
        self.assertIsNotNone(test_sensor)
        self.assertEqual(test_sensor.num_samples(), 720000)
        test_sensor = datawindow.get_station("0000000001").location_sensor()
        self.assertIsNotNone(test_sensor)
        self.assertEqual(test_sensor.num_samples(), 3)

    def test_dw_with_start_end(self):
        dw_with_start_end = dw.DataWindow(
            input_dir=self.input_dir,
            station_ids=["1637650010", "0000000001"],
            start_datetime=dt.datetime_from_epoch_seconds_utc(1597189455),
            end_datetime=dt.datetime_from_epoch_seconds_utc(1597189465),
            structured_layout=False,
        )
        self.assertEqual(len(dw_with_start_end.stations), 1)
        audio_sensor = dw_with_start_end.get_station("0000000001").audio_sensor()
        self.assertIsNotNone(audio_sensor)
        self.assertEqual(audio_sensor.num_samples(), 479984)
        loc_sensor = dw_with_start_end.get_station("0000000001").location_sensor()
        self.assertIsNotNone(loc_sensor)
        self.assertEqual(loc_sensor.num_samples(), 2)

    def test_dw_invalid(self):
        dw_invalid = dw.DataWindow(
            input_dir=self.input_dir,
            station_ids=["does_not_exist"],
            structured_layout=False,
        )
        self.assertIsNone(dw_invalid.get_station("does_not_exist"))


class PadDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        timestamps = [
            dt.seconds_to_microseconds(40),
            dt.seconds_to_microseconds(50),
            dt.seconds_to_microseconds(60),
        ]
        cls.dataframe = pd.DataFrame(
            np.transpose([timestamps, [4, 5, 6]]), columns=["timestamps", "temp"]
        )

    def test_pad_data(self):
        filled_dataframe = dw.pad_data(
            dt.seconds_to_microseconds(10),
            dt.seconds_to_microseconds(100),
            self.dataframe,
            dt.seconds_to_microseconds(10),
        )
        self.assertEqual(filled_dataframe.shape, (10, 2))
        self.assertEqual(
            filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(20)
        )
        self.assertEqual(
            filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(30)
        )

    def test_pad_data_uneven_ends(self):
        filled_dataframe = dw.pad_data(
            dt.seconds_to_microseconds(10),
            dt.seconds_to_microseconds(100),
            self.dataframe,
            dt.seconds_to_microseconds(12),
        )
        self.assertEqual(filled_dataframe.shape, (8, 2))
        self.assertEqual(
            filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(28)
        )
        self.assertEqual(
            filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(40)
        )
        self.assertEqual(
            filled_dataframe.loc[6, "timestamps"], dt.seconds_to_microseconds(84)
        )
        self.assertEqual(
            filled_dataframe.loc[7, "timestamps"], dt.seconds_to_microseconds(96)
        )


class FillGapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        timestamps = [
            dt.seconds_to_microseconds(10),
            dt.seconds_to_microseconds(30),
            dt.seconds_to_microseconds(100),
        ]
        cls.dataframe = pd.DataFrame(
            np.transpose([timestamps, [1, 3, 10]]), columns=["timestamps", "temp"]
        )

    def test_fill_gaps(self):
        filled_dataframe = dw.fill_gaps(
            self.dataframe,
            dt.seconds_to_microseconds(10),
            dt.seconds_to_microseconds(10),
        )
        self.assertEqual(filled_dataframe.shape, (10, 2))
        self.assertEqual(
            filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(20)
        )
        self.assertEqual(
            filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(30)
        )

    def test_fill_gaps_long_interval(self):
        filled_dataframe = dw.fill_gaps(
            self.dataframe,
            dt.seconds_to_microseconds(20),
            dt.seconds_to_microseconds(10),
        )
        self.assertEqual(filled_dataframe.shape, (6, 2))
        self.assertEqual(
            filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(30)
        )
        self.assertEqual(
            filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(50)
        )

    def test_fill_gaps_long_gap(self):
        filled_dataframe = dw.fill_gaps(
            self.dataframe,
            dt.seconds_to_microseconds(10),
            dt.seconds_to_microseconds(20),
        )
        self.assertEqual(filled_dataframe.shape, (9, 2))
        self.assertEqual(
            filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(30)
        )
        self.assertEqual(
            filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(40)
        )


class CreateDatalessTimestampsDFTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base_df = pd.DataFrame([], columns=["timestamps", "data"])

    def test_create_dataless_timestamps_df(self):
        new_df = dw.create_dataless_timestamps_df(2000, 1000, self.base_df.columns, 7, False)
        self.assertEqual(new_df.loc[0, "timestamps"], 3000)
        self.assertEqual(new_df.loc[6, "timestamps"], 9000)
        new_df = dw.create_dataless_timestamps_df(8000, 1000, self.base_df.columns, 7, True)
        self.assertEqual(new_df.loc[0, "timestamps"], 7000)
        self.assertEqual(new_df.loc[6, "timestamps"], 1000)

    def test_add_dataless_timestamps_df_empty(self):
        # dataframe to alter is empty, so nothing changes
        new_base_df = self.base_df.copy()
        new_df = dw.add_dataless_timestamps_to_df(new_base_df, 0, 1000, 1000, 7, False)
        self.assertEqual(len(new_df), 0)

    def test_add_dataless_timestamps_df(self):
        new_df = dw.create_dataless_timestamps_df(8000, 1000, self.base_df.columns, 7, True)
        new_df = dw.add_dataless_timestamps_to_df(new_df, 6, 1000, 1000, 7, False)
        self.assertEqual(new_df.loc[7, "timestamps"], 2000)
        self.assertEqual(new_df.loc[13, "timestamps"], 8000)
        new_df = dw.add_dataless_timestamps_to_df(new_df, 0, 1000, 1000, 7, True)
        self.assertEqual(new_df.loc[14, "timestamps"], 6000)
        self.assertEqual(new_df.loc[20, "timestamps"], 0)

    def test_add_dataless_timestamps_df_index_too_high(self):
        # no change to dataframe if index is too high
        new_df = dw.create_dataless_timestamps_df(8000, 1000, self.base_df.columns, 7, True)
        new_df = dw.add_dataless_timestamps_to_df(new_df, 99, 1000, 1000, 7, True)
        self.assertEqual(len(new_df), 7)
        self.assertEqual(new_df.loc[0, "timestamps"], 7000)
        self.assertEqual(new_df.loc[6, "timestamps"], 1000)

    def test_add_dataless_timestamps_df_not_enough_samples(self):
        # no change to dataframe if adding less than 1 samples
        new_df = dw.create_dataless_timestamps_df(8000, 1000, self.base_df.columns, 7, True)
        new_df = dw.add_dataless_timestamps_to_df(new_df, 0, 1000, 1000, -10, True)
        self.assertEqual(len(new_df), 7)
        self.assertEqual(new_df.loc[0, "timestamps"], 7000)
        self.assertEqual(new_df.loc[6, "timestamps"], 1000)
        new_df = dw.add_dataless_timestamps_to_df(new_df, 0, 1000, 1000, 0, True)
        self.assertEqual(len(new_df), 7)
        self.assertEqual(new_df.loc[0, "timestamps"], 7000)
        self.assertEqual(new_df.loc[6, "timestamps"], 1000)
