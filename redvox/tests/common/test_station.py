"""
tests for station
"""
import unittest

import redvox.tests as tests
from redvox.common import api_reader
from redvox.common.station import Station


class StationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.empty_apim_station = Station([])
        reader = api_reader.ApiReader(tests.APIX_READER_TEST_DATA_DIR, False, extensions={".rdvxm"},
                                      station_ids={"0000000001"})
        cls.apim_station = reader.get_station_by_id("0000000001")
        reader = api_reader.ApiReader(tests.TEST_DATA_DIR, False, extensions={".rdvxz"},
                                      station_ids={"1637650010"})
        cls.api900_station = reader.get_station_by_id("1637650010")

    def test_api900_station(self):
        self.assertEqual(len(self.api900_station.data), 1)
        self.assertEqual(self.api900_station.timesync_analysis.get_best_latency(), 70278.0)
        self.assertTrue(self.api900_station.has_audio_sensor())
        audio_sensor = self.api900_station.audio_sensor()
        self.assertEqual(audio_sensor.sample_rate, 80)
        self.assertTrue(audio_sensor.is_sample_rate_fixed)
        self.assertTrue(self.api900_station.has_location_sensor())
        loc_sensor = self.api900_station.location_sensor()
        self.assertEqual(loc_sensor.data_df.shape, (2, 11))

    def test_apim_station(self):
        self.assertEqual(len(self.apim_station.data), 1)
        self.assertEqual(self.apim_station.timesync_analysis.get_best_latency(), 1296.0)
        audio_sensor = self.apim_station.audio_sensor()
        self.assertIsNotNone(audio_sensor)
        self.assertEqual(audio_sensor.sample_rate, 48000.0)
        self.assertTrue(audio_sensor.is_sample_rate_fixed)
        loc_sensor = self.apim_station.location_sensor()
        self.assertIsNotNone(loc_sensor)
        self.assertEqual(loc_sensor.data_df.shape, (1, 11))
        accel_sensor = self.apim_station.accelerometer_sensor()
        self.assertIsNone(accel_sensor)
        gyro_sensor = self.apim_station.gyroscope_sensor()
        self.assertIsNone(gyro_sensor)
        mag_sensor = self.apim_station.magnetometer_sensor()
        self.assertIsNone(mag_sensor)
        pressure_sensor = self.apim_station.pressure_sensor()
        self.assertIsNone(pressure_sensor)
        image_sensor = self.apim_station.image_sensor()
        self.assertIsNone(image_sensor)
        amb_temp_sensor = self.apim_station.ambient_temperature_sensor()
        self.assertIsNone(amb_temp_sensor)
        health_sensor = self.apim_station.health_sensor()
        self.assertIsNone(health_sensor)
