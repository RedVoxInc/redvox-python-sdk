"""
Tri-message statistics tests
"""

import unittest

# noinspection Mypy
import numpy as np

import redvox.tests as tests
from redvox.api900.timesync import tri_message_stats
from redvox.api900 import reader


test_filepath_api900: str = tests.test_data("1637680001_1532459248280.rdvxz")

api900_packet = reader.read_file(test_filepath_api900)
api900_wrapped_packet: reader.WrappedRedvoxPacket = reader.wrap(api900_packet)
timesync_channel: reader.TimeSynchronizationSensor = api900_wrapped_packet.time_synchronization_sensor()
coeffs900: np.ndarray = timesync_channel.payload_values()
nm900: int = int(len(coeffs900) / 6)

fs: float = api900_wrapped_packet.microphone_sensor().sample_rate_hz()
b0 = api900_wrapped_packet.app_file_start_timestamp_machine()

a1, a2, a3, b1, b2, b3 = tri_message_stats.transmit_receive_timestamps_microsec(coeffs900)

d1_900, d3_900 = tri_message_stats.latencies(a1, a2, a3, b1, b2, b3)
o1_900, o3_900 = tri_message_stats.offsets(a1, a2, a3, b1, b2, b3)


class TriMessageStatTests(unittest.TestCase):

    def test_tri_message_class(self):
        # due to the way the init function works, this also tests find_best_latency and find_best_offset
        temp = tri_message_stats.TriMessageStats(api900_wrapped_packet.redvox_id(), a1, a2, a3, b1, b2, b3)
        self.assertEqual(73300.0, temp.best_latency)
        self.assertEqual(4, temp.best_latency_index)
        self.assertEqual(3, temp.best_latency_array_index)
        self.assertEqual(-22903665.0, temp.best_offset)

    def test_set_latency(self):
        temp = tri_message_stats.TriMessageStats(api900_wrapped_packet.redvox_id(), a1, a2, a3, b1, b2, b3)
        temp.set_latency(a1/2, a2/2, a3/2, b1/2, b2/2, b3/2)
        self.assertEqual(36650.0, temp.best_latency)

    def test_set_offset(self):
        temp = tri_message_stats.TriMessageStats(api900_wrapped_packet.redvox_id(), a1, a2, a3, b1, b2, b3)
        temp.set_offset(a1/2, a2/2, a3/2, b1/2, b2/2, b3/2)
        self.assertEqual(-11451832.5, temp.best_offset)

    def test_transmit_receive_timestamps_microsec(self):
        self.assertTrue(np.array_equal(a1, coeffs900[0: nm900 * 6: 6]))
        self.assertTrue(np.array_equal(a2, coeffs900[1: nm900 * 6: 6]))
        self.assertTrue(np.array_equal(a3, coeffs900[2: nm900 * 6: 6]))
        self.assertTrue(np.array_equal(b1, coeffs900[3: nm900 * 6: 6]))
        self.assertTrue(np.array_equal(b2, coeffs900[4: nm900 * 6: 6]))
        self.assertTrue(np.array_equal(b3, coeffs900[5: nm900 * 6: 6]))

    def test_latencies(self):
        # d1_900 and d3_900 are set above
        self.assertTrue(np.array_equal(d1_900, ((a2 - a1) - (b2 - b1)) / 2.))
        self.assertTrue(np.array_equal(d3_900, ((b3 - b2) - (a3 - a2)) / 2.))

    def test_offsets(self):
        # o1_900 and o3_900 are set above
        self.assertTrue(np.array_equal(o1_900, ((a1 - b1 + a2 - b2) / 2)))
        self.assertTrue(np.array_equal(o3_900, ((a3 - b3 + a2 - b2) / 2)))
