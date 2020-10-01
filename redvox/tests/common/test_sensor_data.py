"""
tests for sensor data and sensor metadata objects
"""
import os
import unittest
import pandas as pd
import redvox.tests as tests
import numpy as np
from redvox.common import sensor_data as sd, load_sensor_data as load_sd


class SensorDataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.api900_station = load_sd.load_station_from_api900_file(os.path.join(tests.TEST_DATA_DIR,
                                                                                 "1637650010_1531343782220.rdvxz"))
        self.apim_station = load_sd.load_station_from_apim(os.path.join(tests.TEST_DATA_DIR,
                                                                        "0000000001_1597189452945991.rdvxm"))
        self.mseed_data = load_sd.load_from_mseed(os.path.join(tests.TEST_DATA_DIR, "out.mseed"))
        self.all_data = load_sd.read_all_in_dir(tests.TEST_DATA_DIR,
                                                redvox_ids=["1637650010", "0000000001", "UHMB3_00"])

    def test_pop_station(self):
        self.all_data.pop_station("1107483069")
        self.assertEqual(len(self.all_data.get_station_summaries()), 2)
        self.all_data.pop_station("0000000001")
        self.assertEqual(len(self.all_data.get_station_summaries()), 1)
        self.all_data.pop_station("UHMB3_00:UHMB3_00")
        self.assertEqual(len(self.all_data.get_station_summaries()), 0)

    def test_api900_station(self):
        self.assertEqual(len(self.api900_station.packet_data), 1)
        self.assertEqual(len(self.api900_station.station_data), 5)
        self.assertTrue(np.isnan(self.api900_station.packet_data[0].packet_best_latency))
        self.assertEqual(self.api900_station.station_metadata.timing_data.station_best_latency, 70278.0)
        self.assertEqual(self.api900_station.audio_sensor().sample_rate, 80)
        self.assertTrue(self.api900_station.audio_sensor().is_sample_rate_fixed)
        self.assertEqual(self.api900_station.location_sensor().data_df.shape, (2, 7))

    def test_apim_station(self):
        self.assertEqual(len(self.apim_station.packet_data), 1)
        self.assertEqual(self.apim_station.packet_data[0].packet_best_latency, 1296.0)
        self.assertEqual(len(self.apim_station.station_data), 2)
        self.assertEqual(self.apim_station.audio_sensor().sample_rate, 48000.0)
        self.assertTrue(self.apim_station.audio_sensor().is_sample_rate_fixed)
        self.assertEqual(self.apim_station.location_sensor().data_df.shape, (1, 11))

    def test_create_read_update_delete_audio_sensor(self):
        self.assertTrue(self.api900_station.has_audio_sensor())
        audio_sensor = sd.SensorData("test_audio", pd.DataFrame(np.transpose([[10, 20, 30, 40], [1, 2, 3, 4]]),
                                                                columns=["timestamps", "microphone"]), 1, True)
        self.api900_station.set_audio_sensor(audio_sensor)
        self.assertTrue(self.api900_station.has_audio_sensor())
        self.assertEqual(self.api900_station.audio_sensor().sample_rate, 1)
        self.assertEqual(self.api900_station.audio_sensor().num_samples(), 4)
        self.assertIsInstance(self.api900_station.audio_sensor().get_channel("microphone"), np.ndarray)
        self.assertRaises(ValueError, self.api900_station.audio_sensor().get_channel, "nonexistant")
        self.assertEqual(self.api900_station.audio_sensor().first_data_timestamp(), 10)
        self.assertEqual(self.api900_station.audio_sensor().last_data_timestamp(), 40)
        self.api900_station.set_audio_sensor(None)
        self.assertFalse(self.api900_station.has_audio_sensor())

    def test_mseed_read(self):
        self.assertTrue(self.mseed_data.check_for_id("UHMB3_00"))
        mb3_station = self.mseed_data.get_station("UHMB3_00")
        self.assertEqual(mb3_station.audio_sensor().num_samples(), 6001)
        self.assertEqual(mb3_station.station_metadata.station_network_name, "UH")
        self.assertEqual(mb3_station.station_metadata.station_name, "MB3")
        self.assertEqual(mb3_station.station_metadata.station_channel_name, "BDF")

    def test_read_any_dir(self):
        self.assertEqual(len(self.all_data.station_id_uuid_to_stations), 3)
        self.assertEqual(len(self.all_data.get_station_summaries()), 3)
        # api900 station
        station = self.all_data.get_station("1637650010")
        self.assertEqual(len(station.packet_data), 1)
        self.assertTrue(np.isnan(station.packet_data[0].packet_best_latency))
        self.assertEqual(len(station.station_data), 5)
        self.assertEqual(station.audio_sensor().sample_rate, 80)
        self.assertTrue(station.audio_sensor().is_sample_rate_fixed)
        self.assertAlmostEqual(station.audio_sensor().data_duration_s(), 51.2, 1)
        self.assertEqual(station.location_sensor().data_df.shape, (2, 7))
        self.assertAlmostEqual(station.location_sensor().data_duration_s(), 40.04, 2)
        # api m station
        station = self.all_data.get_station("0000000001")
        self.assertEqual(len(station.packet_data), 3)
        self.assertEqual(station.packet_data[0].packet_best_latency, 1296.0)
        self.assertEqual(len(station.station_data), 2)
        self.assertEqual(station.audio_sensor().sample_rate, 48000.0)
        self.assertTrue(station.audio_sensor().is_sample_rate_fixed)
        self.assertAlmostEqual(station.audio_sensor().data_duration_s(), 15.0, 2)
        self.assertEqual(station.location_sensor().data_df.shape, (3, 11))
        self.assertAlmostEqual(station.location_sensor().data_duration_s(), 10.0, 3)
        # mseed station
        station = self.all_data.get_station("UHMB3_00")
        self.assertEqual(len(station.station_data), 1)
        self.assertEqual(station.audio_sensor().num_samples(), 6001)
        self.assertEqual(station.station_metadata.station_network_name, "UH")
        self.assertEqual(station.station_metadata.station_name, "MB3")
        self.assertEqual(station.station_metadata.station_channel_name, "BDF")
