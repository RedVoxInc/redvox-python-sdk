"""
tests for timesync
"""
import os
import glob
import unittest
import numpy as np
import pandas as pd
import redvox.tests as tests
from typing import List
from redvox.common import sensor_data as sd, file_statistics as fs, date_time_utils as dtu, timesync as ts
from redvox.api900 import reader


def load_api_900_data(wrapped_packets: List[reader.WrappedRedvoxPacket]) -> ts.TimeSyncAnalysis:
    data_packets = {}
    sample_rate = wrapped_packets[0].microphone_sensor().sample_rate_hz()
    start_ts = wrapped_packets[0].microphone_sensor().first_sample_timestamp_epoch_microseconds_utc()
    for packet in wrapped_packets:
        mic_sensor = sd.SensorData(packet.microphone_sensor().sensor_name(),
                                   pd.DataFrame(packet.microphone_sensor().payload_values()), sample_rate, True)
        data_pack = sd.DataPacket(packet.server_timestamp_epoch_microseconds_utc(), {sd.SensorType.AUDIO: mic_sensor},
                                  start_ts, int(start_ts +
                                                dtu.seconds_to_microseconds(fs.get_duration_seconds_from_sample_rate(
                                                    sample_rate))),
                                  packet.time_synchronization_sensor().payload_values(),
                                  packet.best_latency(), packet.best_offset())
        data_packets[packet.microphone_sensor().first_sample_timestamp_epoch_microseconds_utc()] = data_pack
    station_timing = sd.StationTiming(
        wrapped_packets[0].mach_time_zero(),
        start_ts, int(start_ts + dtu.seconds_to_microseconds(fs.get_duration_seconds_from_sample_rate(sample_rate))),
        sample_rate, wrapped_packets[0].app_file_start_timestamp_epoch_microseconds_utc(),
        wrapped_packets[0].best_latency(), wrapped_packets[0].best_offset())
    station_metadata = sd.StationMetadata(wrapped_packets[0].redvox_id(), wrapped_packets[0].device_make(),
                                          wrapped_packets[0].device_model(), wrapped_packets[0].device_os(),
                                          wrapped_packets[0].device_os_version(), "redvox",
                                          wrapped_packets[0].app_version(), station_timing)
    station = sd.Station(station_metadata, data_packets)
    return ts.TimeSyncAnalysis(station)


class TimesyncTest(unittest.TestCase):
    def setUp(self) -> None:
        data_paths: List[str] = sorted(glob.glob(os.path.join(tests.TEST_DATA_DIR, "1637680001*.rdvxz")))
        self.wrapped_packets_fs: List[reader.WrappedRedvoxPacket] = list(map(lambda path: reader.read_rdvxz_file(path),
                                                                             data_paths))
        mic_channels: List[reader.MicrophoneSensor] = list(map(
            lambda wrapped_packet: wrapped_packet.microphone_sensor(), self.wrapped_packets_fs))
        self.fs: float = mic_channels[0].sample_rate_hz()
        self.time_sync_analysis = load_api_900_data(self.wrapped_packets_fs)

    def test_my_test(self):
        test_timesync = ts.TimeSyncData()
        self.assertEqual(test_timesync.sample_rate_hz, None)

    def test_validate_sensors(self):
        test_ts = ts.TimeSyncData()
        test_ts.station_id = "test"
        test_ts.sample_rate_hz = 80.0
        test_ts.station_start_timestamp = 1
        other_ts = ts.TimeSyncData()
        other_ts.station_id = "test"
        other_ts.sample_rate_hz = 80.0
        tsa_test = ts.TimeSyncAnalysis()
        tsa_test.station_id = "test"
        tsa_test.timesync_data = [test_ts, other_ts]
        tsa_test.sample_rate_hz = 80.0
        tsa_test.station_start_timestamp = 1
        # there should be a warning message
        self.assertFalse(ts.validate_sensors(tsa_test))

    def test_get_time_sync_data(self):
        self.assertEqual(len(self.time_sync_analysis.get_start_times()), len(self.wrapped_packets_fs))
        self.assertEqual(len(self.time_sync_analysis.get_latencies()), len(self.wrapped_packets_fs))
        self.assertEqual(len(self.time_sync_analysis.get_offsets()), len(self.wrapped_packets_fs))
        self.assertEqual(self.time_sync_analysis.get_best_latency(), 69664.0)

    def test_compute_tri_message_stats(self):
        self.assertEqual(self.time_sync_analysis.get_latencies()[0], 69664.0)
        self.assertEqual(self.time_sync_analysis.get_offsets()[0], -22906528)

    def test_find_bad_packets(self):
        self.assertEqual(len(self.time_sync_analysis.get_bad_packets()), 0)

    def test_evaluate_latencies_and_offsets(self):
        self.assertEqual(len(self.time_sync_analysis.get_latencies()), len(self.wrapped_packets_fs))
        self.assertEqual(len(self.time_sync_analysis.get_offsets()), len(self.wrapped_packets_fs))
        self.assertEqual(self.time_sync_analysis.get_best_latency(), 69664.0)
        self.assertEqual(self.time_sync_analysis.best_latency_index, 0)

    def test_get_latency_mean(self):
        self.assertAlmostEqual(self.time_sync_analysis.get_mean_latency(), 118049.66, 2)

    def test_get_latency_std_dev(self):
        self.assertAlmostEqual(self.time_sync_analysis.get_latency_std(), 84458.71, 2)

    def test_get_offset_mean(self):
        self.assertAlmostEqual(self.time_sync_analysis.get_mean_offset(), -22903096.02, 2)

    def test_get_offset_std_dev(self):
        self.assertAlmostEqual(self.time_sync_analysis.get_offset_std(), 91847.39, 2)

    def test_get_best_start_time(self):
        best_start = self.time_sync_analysis.get_best_start_time()
        self.assertEqual(1532459197088000, best_start)

    def test_correct_time_array(self):
        """ Example: A sample is taken every 0.5 seconds, and a file has 5 seconds (10 samples). Let's say we sampled
        for a total of 20 seconds (4 files, 40 samples). At the beginning of each file (every 10th sample, or every
        5 seconds), there is a start mach time and a start epoch time. Rebuild the time array
        with the packet with the lowest latency being the best start time. In this case, the best latency is 1,
        which occurs in file 2, which starts at 4 seconds.  In the end we should get 40 timestamps,
        starting at -1.0 and increasing at a rate of 0.5 seconds, and the 11th sample (idx 10) = 4 seconds. """
        # the revised start times are in microseconds, but the corrected time is in seconds
        tsd_one = ts.TimeSyncData()
        tsd_one.packet_start_time = 1000000
        tsd_one.best_latency = 2
        tsd_one.sample_rate_hz = 2
        tsd_one.station_start_timestamp = 0
        tsd_two = ts.TimeSyncData()
        tsd_two.packet_start_time = 4000000
        tsd_two.best_latency = 1
        tsd_two.sample_rate_hz = 2
        tsd_thr = ts.TimeSyncData()
        tsd_thr.packet_start_time = 8000000
        tsd_thr.best_latency = 2
        tsd_thr.sample_rate_hz = 2
        tsd_for = ts.TimeSyncData()
        tsd_for.packet_start_time = 13000000
        tsd_for.best_latency = 2
        tsd_for.sample_rate_hz = 2
        tsa_one = ts.TimeSyncAnalysis()
        tsa_one.station_id = "test_station"
        tsa_one.timesync_data = [tsd_one, tsd_two, tsd_thr, tsd_for]
        tsa_one.best_latency_index = 1
        tsa_one.sample_rate_hz = 2
        file_samples = 10  # 10 samples per file
        correct_time_array_sec = ts.update_evenly_sampled_time_array(tsa_one, file_samples)

        self.assertTrue(np.array_equal(np.arange(-1.0, 19.0, 0.5), correct_time_array_sec))
        self.assertEqual(4.0, correct_time_array_sec[10])
        self.assertTrue(isinstance(correct_time_array_sec, np.ndarray))
