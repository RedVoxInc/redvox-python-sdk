"""
tests for data window objects
"""
import unittest

import redvox.tests as tests
import redvox.common.date_time_utils as dt
from redvox.common import data_window as dw


class DataWindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.TEST_DATA_DIR

    def test_data_window_simple(self):
        # with contextlib.redirect_stdout(None):
        datawindow = dw.DataWindow(
            config=dw.DataWindowConfig(
                input_dir=self.input_dir, structured_layout=False)
        )
        self.assertEqual(len(datawindow.stations()), 3)
        self.assertEqual(len(datawindow.station_ids()), 3)
        self.assertTrue("1637680001" in datawindow.station_ids())
        self.assertEqual(len(datawindow.config().extensions), 2)
        self.assertEqual(len(datawindow.config().api_versions), 2)

    def test_data_window(self):
        # with contextlib.redirect_stdout(None):
        datawindow = dw.DataWindow(
            config=dw.DataWindowConfig(
                input_dir=self.input_dir,
                structured_layout=False,
                station_ids={"1637650010", "0000000001"},
            )
        )
        self.assertEqual(len(datawindow.stations()), 2)
        test_station = datawindow.get_station("1637650010")[0]
        self.assertTrue(test_station.is_timestamps_updated)
        self.assertNotEqual(test_station.first_data_timestamp,
                            test_station.audio_sensor().unaltered_data_timestamps()[0])
        self.assertIsNotNone(datawindow.get_station("1637650010")[0].audio_sensor())
        test_sensor = datawindow.get_station("1637650010")[0].accelerometer_sensor()
        self.assertEqual(test_sensor.num_samples(), 643)
        self.assertEqual(test_sensor.first_data_timestamp(), test_station.audio_sensor().first_data_timestamp())
        test_sensor = datawindow.get_station("0000000001")[0].audio_sensor()
        self.assertIsNotNone(test_sensor)
        self.assertEqual(test_sensor.num_samples(), 720000)
        test_sensor = datawindow.get_station("0000000001")[0].location_sensor()
        self.assertIsNotNone(test_sensor)
        self.assertEqual(test_sensor.num_samples(), 4)

    def test_dw_with_start_end(self):
        # with contextlib.redirect_stdout(None):
        dw_with_start_end = dw.DataWindow(
            config=dw.DataWindowConfig(
                input_dir=self.input_dir,
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
        self.assertEqual(loc_sensor.num_samples(), 4)

    def test_dw_invalid(self):
        dw_invalid = dw.DataWindow(
            config=dw.DataWindowConfig(
                input_dir=self.input_dir,
                station_ids={"does_not_exist"},
                structured_layout=False,
            )
        )
        self.assertIsNone(dw_invalid.get_station("does_not_exist"))
        self.assertIsNone(dw_invalid.first_station())

    def test_dw_first_station(self):
        dw_test = dw.DataWindow(
            config=dw.DataWindowConfig(
                input_dir=self.input_dir, structured_layout=False, station_ids=["1637650010"])
        )
        first_station = dw_test.first_station()
        self.assertEqual("1637650010", first_station.id())


# doesn't work with test module, but works on its own.
# class DataWindowConfigFileTest(unittest.TestCase):
#     def test_load(self):
#         dw_test = dw.DataWindow.from_config_file(f"{tests.TEST_DATA_DIR}/dw_test.config.toml")
#         self.assertEqual(len(dw_test.stations()), 2)
