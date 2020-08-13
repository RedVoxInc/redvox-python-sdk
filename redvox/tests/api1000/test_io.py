"""
tests for timesync
"""
import unittest
import os
import glob
import numpy as np
import redvox.tests as tests
from redvox.api1000 import io
TEST_DIR = tests.TEST_DATA_DIR


class ReadWrappedPacketTest(unittest.TestCase):
    def setUp(self) -> None:
        file_one = TEST_DIR + "/0000000001_1597189452945991.rdvxm"
        self.read_wrapped_packet = io.ReadWrappedPackets([io.read_rdvxz_file(file_one)])

    def test_init(self):
        self.assertEqual(self.read_wrapped_packet.start_mach_timestamp, 1597189452943691.0)
        self.assertEqual(self.read_wrapped_packet.redvox_id, "0000000001")
        self.assertEqual(self.read_wrapped_packet.uuid, "0000000001")

    def test_add_packet(self):
        self.read_wrapped_packet.add_packet(io.read_rdvxz_file(TEST_DIR + "/0000000001_1597189457945569.rdvxm"))
        self.assertEqual(len(self.read_wrapped_packet.wrapped_packets), 2)

    def test_validate_packet(self):
        self.assertTrue(self.read_wrapped_packet.validate_sensors(
            io.read_rdvxz_file(TEST_DIR + "/0000000001_1597189457945569.rdvxm")))

    def test_add_gap(self):
        self.read_wrapped_packet.add_packet(io.read_rdvxz_file(TEST_DIR + "/0000000001_1597189462946314.rdvxm"))
        self.assertEqual(len(self.read_wrapped_packet.wrapped_packets), 2)
        self.assertTrue(len(self.read_wrapped_packet.identify_gaps(5)) > 0)

    def test_read_synth(self):
        file_two = TEST_DIR + "/example.rdvxm"
        read_synth_packet = io.ReadWrappedPackets([io.read_rdvxz_file(file_two)])
        self.assertEqual(read_synth_packet.redvox_id, "1234567890")
        print(read_synth_packet.wrapped_packets[0].get_station_information().get_app_settings())


class ReadResultTest(unittest.TestCase):
    def setUp(self) -> None:
        self.read_result = io.read_dir(TEST_DIR)

    def test_read_dir(self):
        self.assertEqual(self.read_result.start_timestamp_s, None)
        self.assertEqual(len(self.read_result.all_wrapped_packets), 1)

    def test_get_by_id(self):
        self.assertEqual(self.read_result.get_by_id("0000000001")[0].get_timing_information()
                         .get_packet_end_mach_timestamp(), 1597189457945991.0)

    def test_identify_gaps(self):
        self.assertEqual(len(self.read_result.all_wrapped_packets[0].identify_gaps(5)), 0)


if __name__ == '__main__':
    unittest.main()
