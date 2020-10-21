"""
tests for loading or reading station data from various sources
"""
import os
import unittest
import numpy as np

import redvox.tests as tests
from redvox.common import date_time_utils as dtu
from redvox.common import station_reader_utils as sr_utils


class StationSummaryTest(unittest.TestCase):
    def setUp(self):
        self.now_time = dtu.datetime.now()
        self.station_summary = sr_utils.StationSummary("1234567890", "9876543210", "test_os", "test_os_version",
                                                       "test_app_version", 800.0, 40.96,
                                                       self.now_time - dtu.timedelta(seconds=40.96), self.now_time)
        real_station = sr_utils.load_station_from_api900_file(os.path.join(tests.TEST_DATA_DIR,
                                                                           "1637650010_1531343782220.rdvxz"))
        self.real_summary = sr_utils.StationSummary.from_station(real_station)

    def test_station_summary_init(self):
        self.assertEqual(self.station_summary.station_id, "1234567890")
        self.assertEqual(self.station_summary.station_uuid, "9876543210")
        self.assertEqual(self.station_summary.os, "test_os")
        self.assertEqual(self.station_summary.os_version, "test_os_version")
        self.assertEqual(self.station_summary.app_version, "test_app_version")
        self.assertEqual(self.station_summary.audio_sampling_rate_hz, 800.)
        self.assertEqual(self.station_summary.total_duration_s, 40.96)
        self.assertEqual(self.station_summary.start_dt, self.now_time - dtu.timedelta(seconds=40.96))
        self.assertEqual(self.station_summary.end_dt, self.now_time)

    def test_from_station(self):
        self.assertEqual(self.real_summary.station_id, "1637650010")
        self.assertEqual(self.real_summary.station_uuid, "1107483069")
        self.assertEqual(self.real_summary.os, "Android")
        self.assertEqual(self.real_summary.os_version, "8.1.0")
        self.assertEqual(self.real_summary.app_version, "2.3.1")
        self.assertEqual(self.real_summary.audio_sampling_rate_hz, 80.)
        self.assertEqual(self.real_summary.total_duration_s, 51.1875)
        self.assertEqual(self.real_summary.start_dt, dtu.datetime(2018, 7, 11, 21, 16, 22, 220500))
        self.assertEqual(self.real_summary.end_dt, dtu.datetime(2018, 7, 11, 21, 17, 13, 408000))


class ReadResultTests(unittest.TestCase):
    def setUp(self):
        api900_station = sr_utils.load_station_from_api900_file(os.path.join(tests.TEST_DATA_DIR,
                                                                             "1637650010_1531343782220.rdvxz"))
        apim_station = sr_utils.load_station_from_apim(os.path.join(tests.TEST_DATA_DIR,
                                                                    "0000000001_1597189452945991.rdvxm"))
        mseed_data = sr_utils.load_from_mseed(os.path.join(tests.TEST_DATA_DIR, "out.mseed"))
        read_result = {"1637650010:1107483069": api900_station, "0000000001:0000000001": apim_station}
        self.read_result = sr_utils.ReadResult(read_result)
        self.read_result.append(mseed_data)

        # todo: the rest of the readresult tests, and the test_station_reader_utils tests

    def test_pop_station(self):
        self.read_result.pop_station("1107483069")
        self.assertEqual(len(self.read_result.get_station_summaries()), 2)
        self.read_result.pop_station("0000000001")
        self.assertEqual(len(self.read_result.get_station_summaries()), 1)
        self.read_result.pop_station("UHMB3_00:UHMB3_00")
        self.assertEqual(len(self.read_result.get_station_summaries()), 0)


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.all_data = sr_utils.read_all_in_dir(tests.TEST_DATA_DIR,
                                                 redvox_ids=["1637650010", "0000000001", "UHMB3_00"])

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
        self.assertEqual(station.location_sensor().data_df.shape, (2, 11))
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
