"""
tests for loading sensor data
"""
import unittest

import pandas as pd
import numpy as np

import redvox.tests as tests
from redvox.common.io import index_unstructured, ReadFilter
from redvox.common.sensor_data_old import SensorType
from redvox.common import sensor_reader_utils_old as sdru


class EmptySensorTest(unittest.TestCase):
    def test_empty_sensor(self):
        empty_sensor = sdru.get_empty_sensor_data("empty")
        self.assertEqual(empty_sensor.num_samples(), 0)
        self.assertTrue(np.isnan(empty_sensor.sample_rate_hz))
        self.assertEqual(empty_sensor.type, SensorType.UNKNOWN_SENSOR)


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
                                            ).read_raw()

    def test_load_audio(self):
        audio = sdru.load_apim_audio(self.apim_files[0])
        self.assertEqual(audio.sample_rate_hz, 48000)
        self.assertEqual(audio.num_samples(), 240000)
        audio_list, gaps = sdru.load_apim_audio_from_list(self.apim_files)
        self.assertEqual(audio_list.sample_rate_hz, 48000)
        self.assertEqual(audio_list.num_samples(), 720000)

    def test_load_location(self):
        location = sdru.load_apim_location(self.apim_files[0])
        self.assertTrue(np.isnan(location.sample_rate_hz))
        self.assertEqual(location.num_samples(), 1)
        location_list = sdru.load_apim_location_from_list(self.apim_files, [])
        self.assertAlmostEqual(location_list.sample_rate_hz, .2, 1)
        self.assertEqual(location_list.num_samples(), 3)

    def test_load_sensor_failure(self):
        pressure = sdru.load_apim_pressure(self.apim_files[0])
        self.assertIsNone(pressure)
