"""
tests for station
"""
import unittest
import contextlib

import numpy as np

import redvox.tests as tests
from redvox.common import api_reader
from redvox.common.io import ReadFilter
from redvox.common.station import Station
from redvox.common.sensor_data import SensorType
from redvox.common.sensor_reader_utils import get_empty_sensor


class StationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with contextlib.redirect_stdout(None):
            reader = api_reader.ApiReader(
                tests.TEST_DATA_DIR,
                False,
                ReadFilter(extensions={".rdvxm"}, station_ids={"0000000001"}),
            )
            cls.apim_station = reader.get_station_by_id("0000000001")[0]
            reader = api_reader.ApiReader(
                tests.TEST_DATA_DIR,
                False,
                ReadFilter(extensions={".rdvxz"}, station_ids={"1637650010"}),
            )
            cls.api900_station = reader.get_station_by_id("1637650010")[0]

    def test_empty_station(self):
        empty_apim_station = Station()
        self.assertEqual(len(empty_apim_station._data), 0)
        self.assertTrue(np.isnan(empty_apim_station.start_date()))
        self.assertFalse(empty_apim_station.audio_sensor())

    def test_empty_station_update_timestamp(self):
        empty_apim_station = Station()
        empty_apim_station.set_start_date(empty_apim_station.start_date() + 100)
        self.assertTrue(np.isnan(empty_apim_station.start_date()))

    def test_api900_station(self):
        self.assertEqual(len(self.api900_station._data), 6)
        self.assertEqual(
            self.api900_station.timesync_data().best_latency(), 70278.0
        )
        self.assertTrue(self.api900_station.has_audio_sensor())
        audio_sensor = self.api900_station.audio_sensor()
        self.assertEqual(audio_sensor.sample_rate_hz(), 80)
        self.assertTrue(audio_sensor.is_sample_rate_fixed())
        self.assertTrue(self.api900_station.has_location_sensor())
        loc_sensor = self.api900_station.location_sensor()
        self.assertEqual(loc_sensor.data_df().shape, (2, 13))

    def test_apim_station(self):
        self.assertEqual(len(self.apim_station._data), 3)
        self.assertEqual(self.apim_station.timesync_data().best_latency(), 1296.0)
        audio_sensor = self.apim_station.audio_sensor()
        self.assertIsNotNone(audio_sensor)
        self.assertEqual(audio_sensor.sample_rate_hz(), 48000.0)
        self.assertTrue(audio_sensor.is_sample_rate_fixed())
        loc_sensor = self.apim_station.location_sensor()
        self.assertIsNotNone(loc_sensor)
        self.assertEqual(loc_sensor.data_df().shape, (3, 13))
        self.assertAlmostEqual(loc_sensor.get_data_channel("latitude")[0], 21.309, 3)
        accel_sensor = self.apim_station.accelerometer_sensor()
        self.assertIsNone(accel_sensor)
        health_sensor = self.apim_station.health_sensor()
        self.assertIsNone(health_sensor)

    def test_check_key(self):
        empty_apim_station = Station()
        with contextlib.redirect_stdout(None):
            self.assertFalse(empty_apim_station.check_key())
            empty_apim_station.set_id("1234567890")
            self.assertFalse(empty_apim_station.check_key())
            empty_apim_station.set_uuid("abcdefghij")
            self.assertTrue(empty_apim_station.check_key())
            empty_apim_station.set_start_date(1579448154300000)
            self.assertTrue(empty_apim_station.check_key())

    def test_append_station_mismatch(self):
        empty_apim_station = Station()
        with contextlib.redirect_stdout(None):
            empty_apim_station.append_station(self.apim_station)
        self.assertEqual(len(empty_apim_station.data()), 0)

    def test_append_station_success(self):
        empty_apim_station = Station()
        empty_apim_station.set_id(self.apim_station.id()).set_uuid(
            self.apim_station.uuid()
        ).set_start_date(self.apim_station.start_date())
        empty_apim_station.set_metadata(self.apim_station.metadata())
        empty_apim_station.append_station(self.apim_station)
        self.assertEqual(len(empty_apim_station.data()), 3)
        self.assertEqual(
            empty_apim_station.timesync_data().best_latency(), 1296.0
        )

    def test_append_sensor(self):
        empty_apim_station = Station()
        self.assertFalse(empty_apim_station.has_audio_sensor())
        empty_apim_station.append_sensor(self.apim_station.audio_sensor())
        self.assertEqual(len(empty_apim_station.data()), 1)
        self.assertTrue(empty_apim_station.has_audio_sensor())
        self.assertEqual(empty_apim_station.audio_sensor().sample_rate_hz(), 48000.0)
        self.assertTrue(empty_apim_station.audio_sensor().is_sample_rate_fixed)
        empty_apim_station.append_sensor(self.api900_station.pressure_sensor())
        self.assertAlmostEqual(
            empty_apim_station.pressure_sensor().sample_rate_hz(), 5.01, 2
        )

    def test_set_sensor(self):
        empty_apim_station = Station()
        self.assertFalse(empty_apim_station.has_audio_sensor())
        self.assertIsNone(empty_apim_station.audio_sensor())
        empty_apim_station.set_audio_sensor(
            get_empty_sensor("empty mic", SensorType.AUDIO).class_from_type()
        )
        self.assertTrue(empty_apim_station.has_audio_sensor())
        self.assertFalse(empty_apim_station.has_audio_data())
        empty_apim_station.set_audio_sensor()
        self.assertFalse(empty_apim_station.has_audio_sensor())
        empty_apim_station.set_audio_sensor(self.apim_station.audio_sensor())
        self.assertTrue(empty_apim_station.has_audio_sensor())
        self.assertTrue(empty_apim_station.has_audio_data())
        self.assertEqual(empty_apim_station.audio_sensor().sample_rate_hz(), 48000)

    def test_update_timestamps(self):
        updated_station = self.api900_station
        self.assertEqual(updated_station.first_data_timestamp(),
                         updated_station.audio_sensor().get_data_channel("unaltered_timestamps")[0])
        updated_station.set_correct_timestamps()
        updated_station.update_timestamps()
        self.assertNotEqual(updated_station.first_data_timestamp(),
                            updated_station.audio_sensor().get_data_channel("unaltered_timestamps")[0])
