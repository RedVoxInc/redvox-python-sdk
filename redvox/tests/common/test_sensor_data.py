"""
tests for sensor data and sensor metadata objects
"""
import os
import unittest
import numpy as np
import pandas as pd
import redvox.tests as tests
from redvox.common import sensor_data as sd, file_statistics as fs, date_time_utils as dtu, timesync as ts
from redvox.api900 import reader


class SensorDataTest(unittest.TestCase):
    def test_my_test(self):
        data_packet = reader.read_rdvxz_file(os.path.join(tests.TEST_DATA_DIR, "1637650010_1531343782220.rdvxz"))
        samp_rate = data_packet.microphone_sensor().sample_rate_hz()
        num_samples = fs.get_num_points_from_sample_rate(samp_rate)
        t_s_step = int(dtu.seconds_to_microseconds(fs.get_duration_seconds_from_sample_rate(samp_rate) / num_samples))
        timestamps = range(int(data_packet.microphone_sensor().first_sample_timestamp_epoch_microseconds_utc()),
                           int(data_packet.microphone_sensor().first_sample_timestamp_epoch_microseconds_utc()) +
                           int(t_s_step * num_samples), t_s_step)
        test_sensor = sd.SensorData(data_packet.microphone_sensor().sensor_name(),
                                    pd.DataFrame(np.transpose(data_packet.microphone_sensor().payload_values()),
                                                 index=timestamps, columns=["mic_value"]), samp_rate, True)
        test_packet = sd.DataPacket(data_packet.server_timestamp_epoch_microseconds_utc(),
                                    {sd.SensorType.AUDIO: test_sensor},
                                    data_packet.app_file_start_timestamp_epoch_microseconds_utc(),
                                    timestamps[-1], data_packet.time_synchronization_sensor().payload_values(),
                                    data_packet.best_latency(), data_packet.best_offset())
        test_timing = sd.StationTiming(data_packet.mach_time_zero(),
                                       data_packet.app_file_start_timestamp_epoch_microseconds_utc(),
                                       timestamps[-1], samp_rate,
                                       data_packet.app_file_start_timestamp_epoch_microseconds_utc(),
                                       data_packet.best_latency(), data_packet.best_offset())
        test_metadata = sd.StationMetadata(data_packet.redvox_id(), data_packet.device_make(),
                                           data_packet.device_model(), data_packet.device_os(),
                                           data_packet.device_os_version(), "redvox", data_packet.app_version(),
                                           test_timing)
        test_object = sd.Station(test_metadata,
                                 {data_packet.app_file_start_timestamp_epoch_microseconds_utc(): test_packet})
        test_timesync = ts.TimeSyncData(test_packet, test_metadata)
        self.assertEqual(test_packet.sensor_data_dict[sd.SensorType.AUDIO].num_samples(), 4096)
        self.assertEqual(test_timesync.num_tri_messages(), 8)
