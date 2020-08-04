"""
tests for sensor data and sensor metadata objects
"""
import os
import unittest
import redvox.tests as tests
from redvox.common import sensor_data as sd


class SensorDataTest(unittest.TestCase):
    def test_my_test(self):
        station = sd.load_station_from_api900(os.path.join(tests.TEST_DATA_DIR, "1637650010_1531343782220.rdvxz"))
        self.assertEqual(len(station.sensor_dict), 1)
        for sensor in station.sensor_dict.values():
            self.assertIsNone(sensor.packet_best_latency)
            self.assertEqual(len(sensor.sensor_data_dict), 5)
            self.assertEqual(sensor.sensor_data_dict[sd.SensorType.AUDIO].sample_rate, 80)
            self.assertTrue(sensor.sensor_data_dict[sd.SensorType.AUDIO].is_sample_rate_fixed)
            self.assertEqual(sensor.sensor_data_dict[sd.SensorType.LOCATION].data_df.shape, (2, 5))
