"""
tests for station
"""
import unittest
import contextlib

import numpy as np

import redvox.tests as tests
from redvox.common import api_reader
from redvox.common.io import ReadFilter
from redvox.common.station_wpa import StationPa
from redvox.common.sensor_data_with_pyarrow import SensorType
from redvox.common.sensor_reader_utils_wpa import get_empty_sensor_data


class StationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with contextlib.redirect_stdout(None):
            reader = api_reader.ApiReader(
                tests.TEST_DATA_DIR,
                False,
                ReadFilter(extensions={".rdvxm"}, station_ids={"0000000001"}),
            )
            cls.apim_station = reader.get_station_wpa_by_id("0000000001")[0]
            reader = api_reader.ApiReader(
                tests.TEST_DATA_DIR,
                False,
                ReadFilter(extensions={".rdvxz"}, station_ids={"1637650010"}),
            )
            cls.api900_station = reader.get_station_wpa_by_id("1637650010")[0]

    def test_empty_station(self):
        empty_apim_station = StationPa()
        self.assertEqual(len(empty_apim_station._data), 0)
        self.assertTrue(np.isnan(empty_apim_station.get_start_date()))
        self.assertFalse(empty_apim_station.audio_sensor())

    def test_empty_station_update_timestamp(self):
        empty_apim_station = StationPa()
        empty_apim_station.set_start_date(empty_apim_station.get_start_date() + 100)
        self.assertTrue(np.isnan(empty_apim_station.get_start_date()))

    def test_api900_station(self):
        self.assertEqual(len(self.api900_station._data), 6)
        self.assertEqual(
            self.api900_station.timesync_data.best_latency, 70278.0
        )
        self.assertTrue(self.api900_station.has_audio_sensor())
        audio_sensor = self.api900_station.audio_sensor()
        self.assertEqual(audio_sensor.sample_rate_hz, 80)
        self.assertTrue(audio_sensor.is_sample_rate_fixed)
        self.assertTrue(self.api900_station.has_location_sensor())
        loc_sensor = self.api900_station.location_sensor()
        self.assertEqual(loc_sensor.data_df().shape, (2, 13))

    def test_apim_station(self):
        self.assertEqual(len(self.apim_station._data), 3)
        self.assertEqual(self.apim_station.timesync_data.best_latency, 1296.0)
        audio_sensor = self.apim_station.audio_sensor()
        self.assertIsNotNone(audio_sensor)
        self.assertEqual(audio_sensor.sample_rate_hz, 48000.0)
        self.assertTrue(audio_sensor.is_sample_rate_fixed)
        loc_sensor = self.apim_station.location_sensor()
        self.assertIsNotNone(loc_sensor)
        self.assertEqual(loc_sensor.data_df().shape, (3, 13))
        self.assertAlmostEqual(loc_sensor.get_data_channel("latitude")[0], 21.309, 3)
        accel_sensor = self.apim_station.accelerometer_sensor()
        self.assertIsNone(accel_sensor)
        health_sensor = self.apim_station.health_sensor()
        self.assertIsNone(health_sensor)

    def test_check_key(self):
        empty_apim_station = StationPa()
        with contextlib.redirect_stdout(None):
            self.assertFalse(empty_apim_station.check_key())
            empty_apim_station.set_id("1234567890")
            self.assertFalse(empty_apim_station.check_key())
            empty_apim_station.set_uuid("abcdefghij")
            self.assertTrue(empty_apim_station.check_key())
            empty_apim_station.set_start_date(1579448154300000)
            self.assertTrue(empty_apim_station.check_key())

    def test_append_station_mismatch(self):
        empty_apim_station = StationPa()
        with contextlib.redirect_stdout(None):
            empty_apim_station.append_station(self.apim_station)
        self.assertEqual(len(empty_apim_station._data), 0)

    def test_append_station_success(self):
        empty_apim_station = StationPa()
        empty_apim_station.set_id(self.apim_station.get_id()).set_uuid(
            self.apim_station.get_uuid()
        ).set_start_date(self.apim_station.get_start_date())
        empty_apim_station.metadata = self.apim_station.metadata
        empty_apim_station.append_station(self.apim_station)
        self.assertEqual(len(empty_apim_station._data), 3)
        self.assertEqual(
            empty_apim_station.timesync_data.best_latency, 1296.0
        )

    def test_append_sensor(self):
        empty_apim_station = StationPa()
        self.assertFalse(empty_apim_station.has_audio_sensor())
        empty_apim_station.append_sensor(self.apim_station.audio_sensor())
        self.assertEqual(len(empty_apim_station._data), 1)
        self.assertTrue(empty_apim_station.has_audio_sensor())
        self.assertEqual(empty_apim_station.audio_sensor().sample_rate_hz, 48000.0)
        self.assertTrue(empty_apim_station.audio_sensor().is_sample_rate_fixed)
        empty_apim_station.append_sensor(self.api900_station.pressure_sensor())
        self.assertAlmostEqual(
            empty_apim_station.pressure_sensor().sample_rate_hz, 5.01, 2
        )

    def test_set_sensor(self):
        empty_apim_station = StationPa()
        self.assertFalse(empty_apim_station.has_audio_sensor())
        self.assertIsNone(empty_apim_station.audio_sensor())
        empty_apim_station.set_audio_sensor(
            get_empty_sensor_data("empty mic", SensorType.AUDIO)
        )
        self.assertTrue(empty_apim_station.has_audio_sensor())
        self.assertFalse(empty_apim_station.has_audio_data())
        empty_apim_station.set_audio_sensor()
        self.assertFalse(empty_apim_station.has_audio_sensor())
        empty_apim_station.set_audio_sensor(self.apim_station.audio_sensor())
        self.assertTrue(empty_apim_station.has_audio_sensor())
        self.assertTrue(empty_apim_station.has_audio_data())
        self.assertEqual(empty_apim_station.audio_sensor().sample_rate_hz, 48000)

    def test_update_timestamps(self):
        with contextlib.redirect_stdout(None):
            updated_station = api_reader.ApiReader(
                tests.TEST_DATA_DIR,
                False,
                ReadFilter(extensions={".rdvxz"}, station_ids={"1637650010"}),
            ).get_station_by_id("1637650010")[0]
            self.assertEqual(updated_station.first_data_timestamp,
                             updated_station.audio_sensor().get_data_channel("unaltered_timestamps")[0])
            updated_station.update_timestamps()
            self.assertNotEqual(updated_station.first_data_timestamp,
                                updated_station.audio_sensor().get_data_channel("unaltered_timestamps")[0])


# class StationSaveTest(unittest.TestCase):
#     def setUp(self):
#         reader = api_reader.ApiReader(
#             tests.TEST_DATA_DIR,
#             False,
#             ReadFilter(extensions={".rdvxm"}, station_ids={"0000000001"}),
#         )
#         self.apim_station = \
#             StationPa.create_from_packets(reader.read_files_by_id("0000000001"),
#                                           base_out_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)),
#                                                                     "pa_test"),
#                                           save_output=True)
#         self.apim_station2 = StationPa.create_from_packets(reader.read_files_by_id("0000000001"), save_output=True)
#
#     def test_me_bro(self):
#         self.apim_station.load_data_from_parquet()
#         self.assertEqual(len(self.apim_station._data), 3)
#         self.assertEqual(self.apim_station.timesync_analysis.get_best_latency(), 1296.0)
#         audio_sensor = self.apim_station.audio_sensor()
#         self.assertIsNotNone(audio_sensor)
#         self.assertEqual(audio_sensor.num_samples(), 720000)
#         self.assertEqual(audio_sensor.sample_rate_hz, 48000.0)
#         self.assertTrue(audio_sensor.is_sample_rate_fixed)
#         loc_sensor = self.apim_station.location_sensor()
#         self.assertIsNotNone(loc_sensor)
#         self.assertEqual(loc_sensor.data_df().shape, (3, 13))
#         self.assertFalse(loc_sensor.is_sample_rate_fixed)
#         self.assertAlmostEqual(loc_sensor.get_data_channel("latitude")[0], 21.309, 3)
#         accel_sensor = self.apim_station.accelerometer_sensor()
#         self.assertIsNone(accel_sensor)
#         health_sensor = self.apim_station.health_sensor()
#         self.assertIsNone(health_sensor)
#
#     def test_me2_bro(self):
#         self.apim_station2.load_data_from_parquet()
#         self.assertEqual(len(self.apim_station2._data), 3)
#         self.assertEqual(self.apim_station2.timesync_analysis.get_best_latency(), 1296.0)
#         audio_sensor = self.apim_station2.audio_sensor()
#         self.assertIsNotNone(audio_sensor)
#         self.assertEqual(audio_sensor.num_samples(), 720000)
#         self.assertEqual(audio_sensor.sample_rate_hz, 48000.0)
#         self.assertTrue(audio_sensor.is_sample_rate_fixed)
#         loc_sensor = self.apim_station2.location_sensor()
#         self.assertIsNotNone(loc_sensor)
#         self.assertEqual(loc_sensor.data_df().shape, (3, 13))
#         self.assertFalse(loc_sensor.is_sample_rate_fixed)
#         self.assertAlmostEqual(loc_sensor.get_data_channel("latitude")[0], 21.309, 3)
#         accel_sensor = self.apim_station2.accelerometer_sensor()
#         self.assertIsNone(accel_sensor)
#         health_sensor = self.apim_station2.health_sensor()
#         self.assertIsNone(health_sensor)