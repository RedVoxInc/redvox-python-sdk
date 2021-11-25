"""
tests for data window objects
"""
import unittest
import contextlib
import tempfile

import numpy as np

import redvox.tests as tests
import redvox.common.date_time_utils as dt
from redvox.common import data_window_old as dw


class DataWindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.TEST_DATA_DIR

    def test_data_window_simple(self):
        with contextlib.redirect_stdout(None):
            datawindow = dw.DataWindow(
                input_dir=self.input_dir,
                structured_layout=False
            )
            self.assertEqual(len(datawindow.stations), 3)
            self.assertEqual(len(datawindow.station_ids), 3)
            self.assertTrue("1637680001" in datawindow.station_ids)
            self.assertEqual(len(datawindow.extensions), 2)
            self.assertEqual(len(datawindow.api_versions), 2)

    def test_data_window(self):
        with contextlib.redirect_stdout(None):
            datawindow = dw.DataWindow(
                input_dir=self.input_dir,
                structured_layout=False,
                station_ids=["1637650010", "0000000001"],
            )
            self.assertEqual(len(datawindow.stations), 2)
            test_station = datawindow.get_station("1637650010")[0]
            self.assertTrue(test_station.is_timestamps_updated)
            self.assertNotEqual(test_station.first_data_timestamp,
                                test_station.audio_sensor().get_data_channel("unaltered_timestamps")[0])
            self.assertIsNotNone(datawindow.get_station("1637650010")[0].audio_sensor())
            test_sensor = datawindow.get_station("1637650010")[0].accelerometer_sensor()
            self.assertEqual(test_sensor.num_samples(), 642)
            self.assertEqual(test_sensor.first_data_timestamp(), test_station.audio_sensor().first_data_timestamp())
            test_sensor = datawindow.get_station("0000000001")[0].audio_sensor()
            self.assertIsNotNone(test_sensor)
            self.assertEqual(test_sensor.num_samples(), 720000)
            test_sensor = datawindow.get_station("0000000001")[0].location_sensor()
            self.assertIsNotNone(test_sensor)
            self.assertEqual(test_sensor.num_samples(), 5)

    def test_dw_with_start_end(self):
        with contextlib.redirect_stdout(None):
            dw_with_start_end = dw.DataWindow(
                input_dir=self.input_dir,
                station_ids=["1637650010", "0000000001"],
                start_datetime=dt.datetime_from_epoch_seconds_utc(1597189455),
                end_datetime=dt.datetime_from_epoch_seconds_utc(1597189465),
                structured_layout=False,
            )
            self.assertEqual(len(dw_with_start_end.stations), 1)
            audio_sensor = dw_with_start_end.get_station("0000000001")[0].audio_sensor()
            self.assertIsNotNone(audio_sensor)
            self.assertEqual(audio_sensor.num_samples(), 480000)
            loc_sensor = dw_with_start_end.get_station("0000000001")[0].location_sensor()
            self.assertIsNotNone(loc_sensor)
            self.assertEqual(loc_sensor.num_samples(), 4)

    def test_dw_invalid(self):
        dw_invalid = dw.DataWindow(
            input_dir=self.input_dir,
            station_ids=["does_not_exist"],
            structured_layout=False,
        )
        self.assertIsNone(dw_invalid.get_station("does_not_exist"))

    def test_dw_insert_audio_before_data(self):
        dw_audio = dw.DataWindow(
            input_dir=self.input_dir,
            station_ids=["0000000001"],
            start_datetime=dt.datetime_from_epoch_seconds_utc(1597189452),
            end_datetime=dt.datetime_from_epoch_seconds_utc(1597189453),
            structured_layout=False,
        )
        x = dw_audio.stations[0]
        self.assertEqual(x.audio_sensor().num_samples(), 48000)
        self.assertEqual(np.count_nonzero(np.isnan(x.audio_sensor().get_data_channel("microphone"))), 45572)

    def test_dw_insert_audio_after_data(self):
        dw_audio = dw.DataWindow(
            input_dir=self.input_dir,
            station_ids=["0000000001"],
            start_datetime=dt.datetime_from_epoch_seconds_utc(1597189467),
            end_datetime=dt.datetime_from_epoch_seconds_utc(1597189468),
            structured_layout=False,
        )
        x = dw_audio.stations[0]
        self.assertEqual(x.audio_sensor().num_samples(), 48000)
        self.assertEqual(np.count_nonzero(np.isnan(x.audio_sensor().get_data_channel("microphone"))), 2428)


class DataWindowJsonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.temp_dir_path = cls.temp_dir.name

    def test_dw_json_pkl_compression(self):
        d_w = dw.DataWindow(tests.TEST_DATA_DIR, False, station_ids={"0000000001"})
        json_str = d_w.to_json_file(self.temp_dir_path, "d_w", "pkl")
        unjsonified = dw.DataWindow.from_json_file(self.temp_dir_path, "d_w")
        self.assertTrue("0000000001" in unjsonified.station_ids)
        self.assertTrue(unjsonified.get_station("0000000001")[0].has_audio_data())
        json_str = d_w.to_json(self.temp_dir_path, "d_w", "pkl")
        unjsonified = dw.DataWindow.from_json(json_str, self.temp_dir_path + "/dw")
        self.assertTrue("0000000001" in unjsonified.station_ids)
        self.assertTrue(unjsonified.get_station("0000000001")[0].has_audio_data())

    def test_dw_json_lz4_compression(self):
        d_w = dw.DataWindow(tests.TEST_DATA_DIR, False, station_ids={"0000000001"})
        json_str = d_w.to_json_file(self.temp_dir_path, "d_w", "lz4")
        unjsonified = dw.DataWindow.from_json_file(self.temp_dir_path, "d_w")
        self.assertTrue("0000000001" in unjsonified.station_ids)
        self.assertTrue(unjsonified.get_station("0000000001")[0].has_audio_data())
        json_str = d_w.to_json(self.temp_dir_path, "d_w", "lz4")
        unjsonified = dw.DataWindow.from_json(json_str, self.temp_dir_path + "/dw")
        self.assertTrue("0000000001" in unjsonified.station_ids)
        self.assertTrue(unjsonified.get_station("0000000001")[0].has_audio_data())

    def test_dw_json_start_dt(self):
        d_w = dw.DataWindow(tests.TEST_DATA_DIR, False, station_ids={"0000000001"})
        json_str = d_w.to_json_file(self.temp_dir_path, "d_w", "lz4")
        unjsonified = dw.DataWindow.from_json_file(self.temp_dir_path, "d_w",
                                                   start_dt=dt.datetime_from_epoch_seconds_utc(1597189455))
        self.assertTrue("0000000001" in unjsonified.station_ids)
        self.assertTrue(unjsonified.get_station("0000000001")[0].has_audio_data())
        unjsonified = dw.DataWindow.from_json_file(self.temp_dir_path, "d_w",
                                                   start_dt=dt.datetime_from_epoch_seconds_utc(1597189300))
        self.assertIsNone(unjsonified)

    def test_dw_json_end_dt(self):
        d_w = dw.DataWindow(tests.TEST_DATA_DIR, False, station_ids={"0000000001"})
        json_str = d_w.to_json_file(self.temp_dir_path, "d_w", "lz4")
        unjsonified = dw.DataWindow.from_json_file(self.temp_dir_path, "d_w",
                                                   end_dt=dt.datetime_from_epoch_seconds_utc(1597189465))
        self.assertTrue("0000000001" in unjsonified.station_ids)
        self.assertTrue(unjsonified.get_station("0000000001")[0].has_audio_data())
        unjsonified = dw.DataWindow.from_json_file(self.temp_dir_path, "d_w",
                                                   end_dt=dt.datetime_from_epoch_seconds_utc(1597189495))
        self.assertIsNone(unjsonified)

    def test_dw_json_station_ids(self):
        d_w = dw.DataWindow(tests.TEST_DATA_DIR, False, station_ids={"0000000001"})
        json_str = d_w.to_json_file(self.temp_dir_path, "d_w", "lz4")
        unjsonified = dw.DataWindow.from_json_file(self.temp_dir_path, "d_w", station_ids=["0000000001"])
        self.assertTrue("0000000001" in unjsonified.station_ids)
        self.assertTrue(unjsonified.get_station("0000000001")[0].has_audio_data())
        unjsonified = dw.DataWindow.from_json_file(self.temp_dir_path, "d_w", station_ids=["0000000002"])
        self.assertIsNone(unjsonified)

    def test_empty_dw_json(self):
        d_w = dw.DataWindow(".")
        json_str = d_w.to_json_file(self.temp_dir_path, "d_w", "pkl")
        unjsonified = dw.DataWindow.from_json_file(self.temp_dir_path, "d_w")
        self.assertEqual(len(unjsonified.station_ids), 0)
        json_str = d_w.to_json(self.temp_dir_path, "d_w", "lz4")
        unjsonified = dw.DataWindow.from_json(json_str, self.temp_dir_path + "/dw")
        self.assertEqual(len(unjsonified.station_ids), 0)

    # noinspection PyUnresolvedReferences
    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()
