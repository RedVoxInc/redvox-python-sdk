"""
tests for loading sensor data
"""
import unittest

import pandas as pd
import numpy as np

import redvox.tests as tests
from redvox.common.io import index_unstructured, ReadFilter
from redvox.common.sensor_data import SensorType
from redvox.common import sensor_reader_utils as sdru


class EmptySensorTest(unittest.TestCase):
    def test_empty_sensor(self):
        empty_sensor = sdru.get_empty_sensor_data("empty")
        self.assertEqual(empty_sensor.num_samples(), 0)
        self.assertTrue(np.isnan(empty_sensor.sample_rate))
        self.assertEqual(empty_sensor.type, SensorType.UNKNOWN_SENSOR)


class CalcTimestampsTest(unittest.TestCase):
    def test_calc_timestamps(self):
        timestamps = sdru.calc_evenly_sampled_timestamps(1000, 100, 1000)
        self.assertEqual(len(timestamps), 100)
        self.assertEqual(timestamps[0], 1000)
        self.assertEqual(timestamps[1], 2000)
        self.assertEqual(timestamps[99], 100000)


class SampleStatisticsTest(unittest.TestCase):
    def test_sample_stats(self):
        new_df = pd.DataFrame([10000, 20000, 30000, 40000, 50000], columns=["timestamps"])
        rate, interval, intvl_std = sdru.get_sample_statistics(new_df)
        self.assertEqual(rate, 1e2)
        self.assertEqual(interval, 1e-2)
        self.assertEqual(intvl_std, 0)


class ReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.apim_files = index_unstructured(tests.TEST_DATA_DIR,
                                            ReadFilter(extensions={".rdvxm"}, station_ids={"0000000001"})
                                            ).read()

    def test_load_audio(self):
        audio = sdru.load_apim_audio(self.apim_files[0])
        self.assertEqual(audio.sample_rate, 48000)
        self.assertEqual(audio.num_samples(), 240000)
        audio_list = sdru.load_apim_audio_from_list(self.apim_files)
        self.assertEqual(audio_list.sample_rate, 48000)
        self.assertEqual(audio_list.num_samples(), 720000)

    def test_load_location(self):
        location = sdru.load_apim_location(self.apim_files[0])
        self.assertTrue(np.isnan(location.sample_rate))
        self.assertEqual(location.num_samples(), 1)
        location_list = sdru.load_apim_location_from_list(self.apim_files)
        self.assertAlmostEqual(location_list.sample_rate, .2, 1)
        self.assertEqual(location_list.num_samples(), 3)

    def test_load_sensor_failure(self):
        pressure = sdru.load_apim_pressure(self.apim_files[0])
        self.assertIsNone(pressure)


# class AnyReaderTest(unittest.TestCase):
#     def setUp(self):
#         self.all_data = sr_utils.read_all_in_dir(tests.TEST_DATA_DIR,
#                                                  station_ids=["1637650010", "0000000001", "UHMB3_00"])
#
#     def test_read_any_dir(self):
#         self.assertEqual(len(self.all_data.station_id_uuid_to_stations), 3)
#         self.assertEqual(len(self.all_data.get_station_summaries()), 3)
#         # api900 station
#         station = self.all_data.get_station("1637650010")
#         self.assertEqual(len(station.packet_data), 1)
#         self.assertTrue(np.isnan(station.packet_data[0].timesync.best_latency))
#         self.assertEqual(len(station.station_data), 6)
#         self.assertEqual(station.audio_sensor().sample_rate, 80)
#         self.assertTrue(station.audio_sensor().is_sample_rate_fixed)
#         self.assertAlmostEqual(station.audio_sensor().data_duration_s(), 51.2, 1)
#         self.assertEqual(station.location_sensor().data_df.shape, (2, 11))
#         self.assertAlmostEqual(station.location_sensor().data_duration_s(), 40.04, 2)
#         # api m station
#         station = self.all_data.get_station("0000000001")
#         self.assertEqual(len(station.packet_data), 3)
#         self.assertEqual(station.packet_data[0].timesync.best_latency, 1296.0)
#         self.assertEqual(len(station.station_data), 2)
#         self.assertEqual(station.audio_sensor().sample_rate, 48000.0)
#         self.assertTrue(station.audio_sensor().is_sample_rate_fixed)
#         self.assertAlmostEqual(station.audio_sensor().data_duration_s(), 15.0, 2)
#         self.assertEqual(station.location_sensor().data_df.shape, (3, 11))
#         self.assertAlmostEqual(station.location_sensor().data_duration_s(), 10.0, 3)
#         # mseed station
#         station = self.all_data.get_station("UHMB3_00")
#         self.assertEqual(len(station.station_data), 1)
#         self.assertEqual(station.audio_sensor().num_samples(), 6001)
#         self.assertEqual(station.station_metadata.station_network_name, "UH")
#         self.assertEqual(station.station_metadata.station_name, "MB3")
#         self.assertEqual(station.station_metadata.station_channel_name, "BDF")
