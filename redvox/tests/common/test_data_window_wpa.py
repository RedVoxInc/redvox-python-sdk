"""
tests for data window objects
"""
import unittest
import contextlib
import tempfile

import redvox.tests as tests
import redvox.common.date_time_utils as dt
from redvox.common import data_window_wpa as dw


class DataWindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.TEST_DATA_DIR

    def test_data_window_simple(self):
        with contextlib.redirect_stdout(None):
            datawindow = dw.DataWindowArrow(
                input_dir=self.input_dir,
                config=dw.DataWindowConfigWpa(structured_layout=False)
            )
            self.assertEqual(len(datawindow.stations()), 3)
            self.assertEqual(len(datawindow.station_ids), 3)
            self.assertTrue("1637680001" in datawindow.station_ids)
            self.assertEqual(len(datawindow.config.extensions), 2)
            self.assertEqual(len(datawindow.config.api_versions), 2)

    def test_data_window(self):
        with contextlib.redirect_stdout(None):
            datawindow = dw.DataWindowArrow(
                input_dir=self.input_dir,
                config=dw.DataWindowConfigWpa(
                    structured_layout=False,
                    station_ids={"1637650010", "0000000001"},
                )
            )
            self.assertEqual(len(datawindow.stations()), 2)
            test_station = datawindow.get_station("1637650010")[0]
            self.assertTrue(test_station.is_timestamps_updated)
            self.assertNotEqual(test_station.first_data_timestamp,
                                test_station.audio_sensor().get_data_channel("unaltered_timestamps")[0])
            self.assertIsNotNone(datawindow.get_station("1637650010")[0].audio_sensor())
            test_sensor = datawindow.get_station("1637650010")[0].accelerometer_sensor()
            self.assertEqual(test_sensor.num_samples(), 643)
            self.assertEqual(test_sensor.first_data_timestamp(), test_station.audio_sensor().first_data_timestamp())
            test_sensor = datawindow.get_station("0000000001")[0].audio_sensor()
            self.assertIsNotNone(test_sensor)
            self.assertEqual(test_sensor.num_samples(), 720000)
            test_sensor = datawindow.get_station("0000000001")[0].location_sensor()
            self.assertIsNotNone(test_sensor)
            self.assertEqual(test_sensor.num_samples(), 5)

    def test_dw_with_start_end(self):
        with contextlib.redirect_stdout(None):
            dw_with_start_end = dw.DataWindowArrow(
                input_dir=self.input_dir,
                config=dw.DataWindowConfigWpa(
                    station_ids={"1637650010", "0000000001"},
                    start_datetime=dt.datetime_from_epoch_seconds_utc(1597189455),
                    end_datetime=dt.datetime_from_epoch_seconds_utc(1597189465),
                    structured_layout=False,
                )
            )
            self.assertEqual(len(dw_with_start_end.stations()), 1)
            audio_sensor = dw_with_start_end.get_station("0000000001")[0].audio_sensor()
            self.assertIsNotNone(audio_sensor)
            self.assertEqual(audio_sensor.num_samples(), 480000)
            loc_sensor = dw_with_start_end.get_station("0000000001")[0].location_sensor()
            self.assertIsNotNone(loc_sensor)
            self.assertEqual(loc_sensor.num_samples(), 3)

    def test_dw_invalid(self):
        dw_invalid = dw.DataWindowArrow(
            input_dir=self.input_dir,
            config=dw.DataWindowConfigWpa(
                station_ids={"does_not_exist"},
                structured_layout=False,
            )
        )
        self.assertIsNone(dw_invalid.get_station("does_not_exist"))


class DataWindowJsonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.temp_dir_path = cls.temp_dir.name

    def test_dw_json_compression(self):
        d_w = dw.DataWindowArrow(tests.TEST_DATA_DIR, config=dw.DataWindowConfigWpa(False, station_ids={"0000000001"}),
                                 save_files=True, out_dir=self.temp_dir_path)
        json_str = d_w._to_json_file("d_w", self.temp_dir_path, dw.DataWindowOrigin(), 0)
        unjsonified = dw.DataWindowArrow.from_json_file(self.temp_dir_path + "/d_w_dw.json")
        self.assertTrue("0000000001" in unjsonified.station_ids())
        self.assertTrue(unjsonified.get_station("0000000001")[0].has_audio_data())
        json_str = d_w.to_json("d_w", self.temp_dir_path, dw.DataWindowOrigin(), 0)
        unjsonified = dw.DataWindowArrow.from_json(json_str, self.temp_dir_path + "/d_w_dw.json")
        self.assertTrue("0000000001" in unjsonified.station_ids())
        self.assertTrue(unjsonified.get_station("0000000001")[0].has_audio_data())

    # def test_empty_dw_json(self):
    #     d_w = dw.DataWindowArrow(".")
    #     json_str = d_w.to_json_file("d_w", self.temp_dir_path, dw.DataWindowResultLocation(), 0)
    #     unjsonified = dw.DataWindowArrow.from_json_file(self.temp_dir_path)
    #     self.assertEqual(len(unjsonified.station_ids), 0)
    #     json_str = d_w.to_json("d_w", self.temp_dir_path, dw.DataWindowResultLocation(), 0)
    #     unjsonified = dw.DataWindowArrow.from_json(json_str, self.temp_dir_path + "/dw")
    #     self.assertEqual(len(unjsonified.station_ids), 0)

    # noinspection PyUnresolvedReferences
    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()
