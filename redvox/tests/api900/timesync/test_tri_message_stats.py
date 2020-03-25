"""
Tri-message statistics tests
"""

import unittest

# noinspection Mypy
import numpy as np

import redvox.tests as tests
from redvox.api900.timesync import tri_message_stats
from redvox.api900 import reader


class TriMessageStatTests(unittest.TestCase):
    def setUp(self) -> None:
        test_filepath_api900: str = tests.test_data("1637680001_1532459248280.rdvxz")

        api900_packet = reader.read_file(test_filepath_api900)
        self.api900_wrapped_packet: reader.WrappedRedvoxPacket = reader.wrap(api900_packet)
        timesync_channel: reader.TimeSynchronizationSensor = self.api900_wrapped_packet.time_synchronization_sensor()
        self.coeffs900: np.ndarray = timesync_channel.payload_values()
        self.nm900: int = int(len(self.coeffs900) / 6)

        self.fs: float = self.api900_wrapped_packet.microphone_sensor().sample_rate_hz()
        self.b0 = self.api900_wrapped_packet.app_file_start_timestamp_machine()

        self.a1, self.a2, self.a3, self.b1, self.b2, self.b3 = \
            tri_message_stats.transmit_receive_timestamps_microsec(self.coeffs900)
        self.tri_ms = tri_message_stats.TriMessageStats(self.api900_wrapped_packet.redvox_id(),
                                                        self.a1, self.a2, self.a3, self.b1, self.b2, self.b3)

    def test_tri_message_class(self):
        self.assertEqual(73300.0, self.tri_ms.best_latency)
        self.assertEqual(4, self.tri_ms.best_latency_index)
        self.assertEqual(3, self.tri_ms.best_latency_array_index)
        self.assertEqual(-22903665.0, self.tri_ms.best_offset)

    def test_find_best_latency_bad(self):
        # specifically testing for latency arrays that are filled with bad values
        bad_values = np.zeros([5])
        self.tri_ms.set_latency(bad_values, bad_values, bad_values, bad_values, bad_values, bad_values)
        self.assertEqual(None, self.tri_ms.best_latency)
        self.assertEqual(None, self.tri_ms.best_latency_array_index)
        self.assertEqual(None, self.tri_ms.best_latency_index)
        bad_values = np.zeros([0])
        self.tri_ms.set_latency(bad_values, bad_values, bad_values, bad_values, bad_values, bad_values)
        self.assertEqual(None, self.tri_ms.best_latency)
        self.assertEqual(None, self.tri_ms.best_latency_array_index)
        self.assertEqual(None, self.tri_ms.best_latency_index)

    def test_find_best_offset_bad(self):
        # specifically testing for latency (and by extension, offset) arrays that are filled with bad values
        bad_values = np.zeros([5])
        self.tri_ms.set_latency(bad_values, bad_values, bad_values, bad_values, bad_values, bad_values)
        self.tri_ms.find_best_offset()
        self.assertEqual(0.0, self.tri_ms.best_offset)

    def test_set_latency(self):
        self.tri_ms.set_latency(self.a1/2, self.a2/2, self.a3/2, self.b1/2, self.b2/2, self.b3/2)
        self.assertEqual(36650.0, self.tri_ms.best_latency)

    def test_set_offset(self):
        self.tri_ms.set_offset(self.a1/2, self.a2/2, self.a3/2, self.b1/2, self.b2/2, self.b3/2)
        self.assertEqual(-11451832.5, self.tri_ms.best_offset)

    def test_transmit_receive_timestamps_microsec(self):
        self.assertTrue(np.array_equal(self.a1, self.coeffs900[0: self.nm900 * 6: 6]))
        self.assertTrue(np.array_equal(self.a2, self.coeffs900[1: self.nm900 * 6: 6]))
        self.assertTrue(np.array_equal(self.a3, self.coeffs900[2: self.nm900 * 6: 6]))
        self.assertTrue(np.array_equal(self.b1, self.coeffs900[3: self.nm900 * 6: 6]))
        self.assertTrue(np.array_equal(self.b2, self.coeffs900[4: self.nm900 * 6: 6]))
        self.assertTrue(np.array_equal(self.b3, self.coeffs900[5: self.nm900 * 6: 6]))

    def test_validate_timestamps(self):
        coeffs1 = np.array([10, 10, 10, 10, 10])
        coeffs2 = coeffs3 = coeffs4 = coeffs5 = coeffs6 = coeffs1
        coeffs1, coeffs2, coeffs3, coeffs4, coeffs5, coeffs6 = \
            tri_message_stats.validate_timestamps(coeffs1, coeffs2, coeffs3, coeffs4, coeffs5, coeffs6)
        self.assertEqual(len(coeffs1), 1)
        coeffs1 = np.array([10, 10, 12, 10, 10])
        coeffs2 = coeffs3 = coeffs4 = coeffs5 = coeffs6 = coeffs1
        coeffs1, coeffs2, coeffs3, coeffs4, coeffs5, coeffs6 = \
            tri_message_stats.validate_timestamps(coeffs1, coeffs2, coeffs3, coeffs4, coeffs5, coeffs6)
        self.assertEqual(len(coeffs1), 2)
        coeffs1 = np.array([10, 10, 12, 13, 14])
        coeffs2 = coeffs3 = coeffs4 = coeffs5 = coeffs6 = coeffs1
        coeffs1, coeffs2, coeffs3, coeffs4, coeffs5, coeffs6 = \
            tri_message_stats.validate_timestamps(coeffs1, coeffs2, coeffs3, coeffs4, coeffs5, coeffs6)
        self.assertEqual(len(coeffs1), 4)

    def test_latencies(self):
        d1_900, d3_900 = tri_message_stats.latencies(self.a1, self.a2, self.a3, self.b1, self.b2, self.b3)
        self.assertTrue(np.array_equal(d1_900, ((self.a2 - self.a1) - (self.b2 - self.b1)) / 2.))
        self.assertTrue(np.array_equal(d3_900, ((self.b3 - self.b2) - (self.a3 - self.a2)) / 2.))

    def test_offsets(self):
        o1_900, o3_900 = tri_message_stats.offsets(self.a1, self.a2, self.a3, self.b1, self.b2, self.b3)
        self.assertTrue(np.array_equal(o1_900, ((self.a1 - self.b1 + self.a2 - self.b2) / 2)))
        self.assertTrue(np.array_equal(o3_900, ((self.a3 - self.b3 + self.a2 - self.b2) / 2)))
