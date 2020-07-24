"""
tests for sensor data and sensor metadata objects
"""
import os
import unittest
import numpy as np
import pandas as pd
import redvox.tests as tests
from redvox.common import sensor_data as sd, file_statistics as fs, date_time_utils as dtu
from redvox.api900 import reader


class SensorData(unittest.TestCase):
    def test_my_test(self):
        data_packet = reader.read_rdvxz_file(os.path.join(tests.TEST_DATA_DIR, "1637650010_1531343782220.rdvxz"))
        samp_rate = data_packet.microphone_sensor().sample_rate_hz()
        num_samples = fs.get_num_points_from_sample_rate(samp_rate)
        t_s_step = int(dtu.seconds_to_microseconds(fs.get_duration_seconds_from_sample_rate(samp_rate) / num_samples))
        timestamps = range(data_packet.microphone_sensor().first_sample_timestamp_epoch_microseconds_utc(),
                           data_packet.microphone_sensor().first_sample_timestamp_epoch_microseconds_utc() +
                           t_s_step*num_samples, t_s_step)
        test_sensor = sd.SensorData(data_packet.microphone_sensor().sensor_name(), samp_rate, True,
                                    pd.DataFrame(np.transpose(data_packet.microphone_sensor().payload_values()),
                                                 index=timestamps, columns=["mic_value"]))
        test_metadata = sd.SensorMetadata(data_packet.mach_time_zero(), data_packet.device_make(),
                                          data_packet.device_model(), data_packet.device_os(),
                                          data_packet.device_os_version(), "redvox", data_packet.app_version(),
                                          {"idk": data_packet.time_synchronization_sensor().payload_values()})
        test_object = sd.Station(test_metadata, {data_packet.microphone_sensor().sensor_name(): test_sensor})
        self.assertEqual(test_object.sensor_data_dict[data_packet.microphone_sensor().sensor_name()].num_samples(),
                         4096)
