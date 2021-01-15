"""
tests for station
"""
import unittest
import numpy as np
import pandas as pd

import redvox.tests as tests
from redvox.common import api_reader
from redvox.common.station import Station
from redvox.common import sensor_data as sd


class StationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.empty_apim_station = Station([])
        reader = api_reader.ApiReader(tests.APIX_READER_TEST_DATA_DIR, False, extensions={".rdvxm"},
                                      station_ids={"0000000001"})
        cls.apim_station = reader.get_station_by_id("0000000001")
        # cls.api900_station = load_sd.load_station_from_api900_file(os.path.join(tests.TEST_DATA_DIR,
        #                                                                          "1637650010_1531343782220.rdvxz"))
        # cls.apim_station = load_sd.load_station_from_apim_file(os.path.join(tests.TEST_DATA_DIR,
        #                                                                      "0000000001_1597189452945991.rdvxm"))
        # cls.mseed_data = load_sd.load_from_mseed(os.path.join(tests.TEST_DATA_DIR, "out.mseed"))

    def test_api900_station(self):
        self.assertEqual(len(self.api900_station.packet_data), 1)
        self.assertEqual(len(self.api900_station.station_data), 6)
        self.assertTrue(np.isnan(self.api900_station.packet_data[0].timesync.best_latency))
        self.assertEqual(self.api900_station.station_metadata.timing_data.station_best_latency, 70278.0)
        self.assertEqual(self.api900_station.audio_sensor().sample_rate, 80)
        self.assertTrue(self.api900_station.audio_sensor().is_sample_rate_fixed)
        self.assertEqual(self.api900_station.location_sensor().data_df.shape, (2, 11))

    def test_apim_station(self):
        self.assertEqual(len(self.apim_station.data), 1)
        # self.assertEqual(self.apim_station.data[0].timesync.best_latency, 1296.0)
        # self.assertEqual(len(self.apim_station.station_data), 2)
        audio_sensor = self.apim_station.audio_sensor()
        self.assertIsNotNone(audio_sensor)
        self.assertEqual(audio_sensor.sample_rate, 48000.0)
        self.assertTrue(audio_sensor.is_sample_rate_fixed)
        loc_sensor = self.apim_station.location_sensor()
        self.assertIsNotNone(loc_sensor)
        self.assertEqual(loc_sensor.data_df.shape, (1, 11))

    def test_create_read_update_delete_audio_sensor(self):
        self.assertTrue(self.api900_station.has_audio_sensor())
        audio_sensor = sd.SensorData("test_audio", pd.DataFrame(np.transpose([[10, 20, 30, 40], [1, 2, 3, 4]]),
                                                                columns=["timestamps", "microphone"]), 1, True)
        self.api900_station.set_audio_sensor(audio_sensor)
        self.assertTrue(self.api900_station.has_audio_sensor())
        self.assertEqual(self.api900_station.audio_sensor().sample_rate, 1)
        self.assertEqual(self.api900_station.audio_sensor().num_samples(), 4)
        self.assertIsInstance(self.api900_station.audio_sensor().get_channel("microphone"), np.ndarray)
        self.assertRaises(ValueError, self.api900_station.audio_sensor().get_channel, "do_not_exist")
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
