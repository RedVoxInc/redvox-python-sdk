"""
tests for sensor data and sensor metadata objects
"""
import os
import unittest
import pandas as pd
import redvox.tests as tests
from redvox.common import sensor_data as sd


class SensorDataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.station = sd.load_station_from_api900(os.path.join(tests.TEST_DATA_DIR, "1637650010_1531343782220.rdvxz"))

    def test_load_api900(self):
        self.assertEqual(len(self.station.station_data), 1)
        for sensor in self.station.station_data:
            self.assertIsNone(sensor.packet_best_latency)
            self.assertEqual(len(sensor.sensor_data_dict), 5)
            self.assertEqual(sensor.audio_sensor().sample_rate, 80)
            self.assertTrue(sensor.audio_sensor().is_sample_rate_fixed)
            self.assertEqual(sensor.location_sensor().data_df.shape, (2, 5))

    def test_create_read_update_delete_audio_sensor(self):
        self.assertTrue(self.station.station_data[0].has_audio_sensor())
        audio_sensor = sd.SensorData("test_audio", pd.DataFrame([1, 2, 3, 4], columns=["microphone"],
                                                                index=[10, 20, 30, 40]), 1, True)
        self.station.station_data[0].set_audio_sensor(audio_sensor)
        self.assertTrue(self.station.station_data[0].has_audio_sensor())
        self.assertEqual(self.station.station_data[0].audio_sensor().sample_rate, 1)
        self.assertEqual(self.station.station_data[0].audio_sensor().num_samples(), 4)
        self.assertEqual(self.station.station_data[0].audio_sensor().first_data_timestamp(), 10)
        self.station.station_data[0].set_audio_sensor(None)
        self.assertFalse(self.station.station_data[0].has_audio_sensor())
