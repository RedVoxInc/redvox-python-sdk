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
        self.api900_station = sd.load_station_from_api900(os.path.join(tests.TEST_DATA_DIR,
                                                                       "1637650010_1531343782220.rdvxz"))
        self.apim_station = sd.load_station_from_apim(os.path.join(tests.TEST_DATA_DIR,
                                                                   "0000000001_1597189452945991.rdvxm"))
        self.mseed_data = sd.load_from_mseed(os.path.join(tests.TEST_DATA_DIR, "out.mseed"))

    def test_api900_station(self):
        self.assertEqual(len(self.api900_station.station_data), 1)
        for sensor in self.api900_station.station_data:
            self.assertIsNone(sensor.packet_best_latency)
            self.assertEqual(len(sensor.sensor_data_dict), 5)
            self.assertEqual(sensor.audio_sensor().sample_rate, 80)
            self.assertTrue(sensor.audio_sensor().is_sample_rate_fixed)
            self.assertEqual(sensor.location_sensor().data_df.shape, (2, 5))

    def test_apim_station(self):
        self.assertEqual(len(self.apim_station.station_data), 1)
        sensor = self.apim_station.station_data[0]
        self.assertEqual(sensor.packet_best_latency, 1296.0)
        self.assertEqual(len(sensor.sensor_data_dict), 2)
        self.assertEqual(sensor.audio_sensor().sample_rate, 48000.0)
        self.assertTrue(sensor.audio_sensor().is_sample_rate_fixed)
        self.assertEqual(sensor.location_sensor().data_df.shape, (1, 9))

    def test_create_read_update_delete_audio_sensor(self):
        self.assertTrue(self.api900_station.station_data[0].has_audio_sensor())
        audio_sensor = sd.SensorData("test_audio", pd.DataFrame([1, 2, 3, 4], columns=["microphone"],
                                                                index=[10, 20, 30, 40]), 1, True)
        self.api900_station.station_data[0].set_audio_sensor(audio_sensor)
        self.assertTrue(self.api900_station.station_data[0].has_audio_sensor())
        self.assertEqual(self.api900_station.station_data[0].audio_sensor().sample_rate, 1)
        self.assertEqual(self.api900_station.station_data[0].audio_sensor().num_samples(), 4)
        self.assertEqual(self.api900_station.station_data[0].audio_sensor().first_data_timestamp(), 10)
        self.api900_station.station_data[0].set_audio_sensor(None)
        self.assertFalse(self.api900_station.station_data[0].has_audio_sensor())

    def test_mseed_read(self):
        self.assertEqual(self.mseed_data[0].station_data[0].audio_sensor().num_samples(), 6001)
        self.assertEqual(self.mseed_data[0].station_metadata.station_network_name, "UH")
        self.assertEqual(self.mseed_data[0].station_metadata.station_name, "MB3")
        self.assertEqual(self.mseed_data[0].station_metadata.station_channel_name, "BDF")
