"""
API900 timesync test module
"""

import glob
import os.path
from typing import List
import unittest

# noinspection Mypy
import numpy as np

import redvox.tests as tests
import redvox.api900.reader as reader
import redvox.api900.timesync.api900_timesync as api900_timesync

data_paths: List[str] = glob.glob(os.path.join(tests.TEST_DATA_DIR, "1637680001*.rdvxz"))
wrapped_packets_fs: List[reader.WrappedRedvoxPacket] = list(map(lambda path: reader.read_rdvxz_file(path),
                                                                data_paths))
mic_channels: List[reader.MicrophoneSensor] = list(map(lambda wrapped_packet: wrapped_packet.microphone_sensor(),
                                                       wrapped_packets_fs))
fs: float = mic_channels[0].sample_rate_hz()
time_sync_data = api900_timesync.TimeSyncData(wrapped_packets_fs)


class RedVoxTimesyncTests(unittest.TestCase):
    def test_get_time_sync_data(self):
        self.assertEqual(len(time_sync_data.rev_start_times), len(wrapped_packets_fs))
        self.assertEqual(len(time_sync_data.latencies), len(wrapped_packets_fs))
        self.assertEqual(len(time_sync_data.offsets), len(wrapped_packets_fs))
        self.assertEqual(time_sync_data.best_latency, 69664.0)

    def test__compute_tri_message_stats(self):
        self.assertEqual(time_sync_data.latencies[0], 69664.0)
        self.assertEqual(time_sync_data.offsets[0], -22906528.)

    def test_find_bad_packets(self):
        self.assertEqual(len(time_sync_data.bad_packets), 0)

    def test_find_bad_packets_ratio(self):
        self.assertEqual(time_sync_data.get_ratio_bad_packets(), 0)

    def test__evaluate_latencies_and_offsets(self):
        self.assertEqual(len(time_sync_data.latencies), len(wrapped_packets_fs))
        self.assertEqual(len(time_sync_data.offsets), len(wrapped_packets_fs))
        self.assertEqual(time_sync_data.best_latency, 69664.0)
        self.assertEqual(time_sync_data.best_latency_index, 0)

    def test_get_valid_latencies(self):
        valid_latencies = time_sync_data.get_valid_latencies()
        self.assertEqual(len(valid_latencies), len(wrapped_packets_fs))
        self.assertEqual(69664.0, valid_latencies[0])
        latency_array = [1, 2, 3, 4, 0, 0, 6, 216]
        valid_latencies = time_sync_data.get_valid_latencies(latency_array)
        self.assertEqual(6, len(valid_latencies))
        self.assertEqual(6, valid_latencies[4])

    def test_get_valid_offsets(self):
        valid_offsets = time_sync_data.get_valid_offsets()
        self.assertEqual(len(valid_offsets), len(wrapped_packets_fs))
        self.assertEqual(-22906528.0, valid_offsets[0])
        offset_array = [1, 2, 3, 4, 0, 0, 6, 216]
        valid_offsets = time_sync_data.get_valid_offsets(offset_array)
        self.assertEqual(6, len(valid_offsets))
        self.assertEqual(6, valid_offsets[4])

    def test_get_valid_rev_start_times(self):
        valid_starts = time_sync_data.get_valid_rev_start_times()
        self.assertEqual(len(valid_starts), len(wrapped_packets_fs))
        self.assertEqual(1532459174181472., valid_starts[0])

    def test_get_best_rev_start_time(self):
        best_start = time_sync_data.get_best_rev_start_time()
        self.assertEqual(1532459174181472.0, best_start)

    def test_correct_time_array(self):
        """ Example: A sample is taken every 0.5 seconds, and a file has 5 seconds (10 samples). Let's say we sampled
        for a total of 20 seconds (4 files, 40 samples). At the beginning of each file (every 10th sample, or every
        5 seconds), there is a start mach time and a start epoch time. Rebuild the time array
        with the packet with the lowest latency being the best start time. In this case, the best latency is 1,
        which occurs in file 2, which starts at 4 seconds.  In the end we should get 40 timestamps,
        starting at -1.0 and increasing at a rate of 0.5 seconds, and the 11th sample (idx 10) = 4 seconds. """
        # the revised start times are in microseconds, but the corrected time is in seconds
        tsd_corrected = api900_timesync.TimeSyncData()
        tsd_corrected.rev_start_times = np.array([1000000, 4000000, 8000000, 13000000])
        tsd_corrected.best_latency = 1
        tsd_corrected.best_latency_index = 1
        tsd_corrected.latencies = np.array([2, 1, 2, 2])
        tsd_corrected.num_packets = 4
        tsd_corrected.sample_rate_hz = 2
        file_samples = 10  # 10 samples per file
        correct_time_array_sec = api900_timesync.update_evenly_sampled_time_array(tsd_corrected, file_samples)

        self.assertTrue(np.array_equal(np.arange(-1.0, 19.0, 0.5), correct_time_array_sec))
        self.assertEqual(4.0, correct_time_array_sec[10])
        self.assertTrue(isinstance(correct_time_array_sec, np.ndarray))

    def test_sync_packet_time(self):
        api900_timesync.sync_packet_time_900(wrapped_packets_fs, verbose=False)
        self.assertEqual(
            wrapped_packets_fs[0].magnetometer_sensor()._unevenly_sampled_channel.timestamps_microseconds_utc[0],
            1532459174286232)
        self.assertEqual(wrapped_packets_fs[0].microphone_sensor().first_sample_timestamp_epoch_microseconds_utc(),
                         1532459174181472)
        self.assertEqual(wrapped_packets_fs[0].app_file_start_timestamp_epoch_microseconds_utc(), 1532459174181472)
        self.assertEqual(wrapped_packets_fs[0].is_synch_corrected(), True)