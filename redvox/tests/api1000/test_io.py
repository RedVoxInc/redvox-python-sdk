"""
tests for timesync
"""
import unittest
import redvox.tests as tests
from redvox.api1000 import io
TEST_DIR = tests.TEST_DATA_DIR


class ReadWrappedPacketTest(unittest.TestCase):
    def setUp(self) -> None:
        file_one = TEST_DIR + "/0000000001_1597189462946314.rdvxm"
        self.read_wrapped_packet = io.ReadWrappedPackets([io.read_rdvxm_file(file_one)])
        self.empty_read_result = io.ReadResult()

    def test_init(self):
        self.assertEqual(self.read_wrapped_packet.start_mach_timestamp, 1597189452943691.0)
        self.assertEqual(self.read_wrapped_packet.redvox_id, "0000000001")
        self.assertEqual(self.read_wrapped_packet.uuid, "0000000001")

    def test_add_packet(self):
        # this also tests sort_packets; the added packet should appear first
        self.read_wrapped_packet.add_packet(io.read_rdvxm_file(TEST_DIR + "/0000000001_1597189457945569.rdvxm"))
        self.assertEqual(len(self.read_wrapped_packet.wrapped_packets), 2)
        self.assertEqual(
            self.read_wrapped_packet.wrapped_packets[0].get_timing_information().get_packet_start_mach_timestamp(),
            1597189457945569)

    def test_validate_sensors(self):
        self.assertTrue(self.read_wrapped_packet.validate_sensors(
            io.read_rdvxm_file(TEST_DIR + "/0000000001_1597189457945569.rdvxm")))

    def test_identify_gaps(self):
        self.read_wrapped_packet.add_packet(io.read_rdvxm_file(TEST_DIR + "/0000000001_1597189452945991.rdvxm"))
        self.assertEqual(len(self.read_wrapped_packet.wrapped_packets), 2)
        self.assertTrue(len(self.read_wrapped_packet.identify_gaps(5.0)) > 0)


class ReadResultTest(unittest.TestCase):
    def setUp(self) -> None:
        self.read_result = io.read_dir(TEST_DIR)

    def test_read_dir(self):
        self.assertEqual(self.read_result.start_timestamp_s, None)
        self.assertEqual(len(self.read_result.all_wrapped_packets), 2)

    def test_get_by_id(self):
        self.assertEqual(self.read_result.get_by_id("0000000001")[0].get_timing_information()
                         .get_packet_end_mach_timestamp(), 1597189457945991.0)

    def test_identify_gaps(self):
        temp_result = io.ReadResult()
        temp_result.add_packet(io.read_rdvxm_file(TEST_DIR + "/0000000001_1597189462946314.rdvxm"))
        temp_result.add_packet(io.read_rdvxm_file(TEST_DIR + "/0000000001_1597189452945991.rdvxm"))
        new_temp = temp_result.identify_gaps(5.0)
        self.assertEqual(len(new_temp.all_wrapped_packets), 2)
        new_result = self.read_result.identify_gaps(5.0)
        self.assertEqual(len(new_result.all_wrapped_packets), 2)

    def test_reorganize_packets(self):
        new_result = self.read_result.reorganize_packets(5.0)
        self.assertEqual(new_result.start_timestamp_s, self.read_result.start_timestamp_s)
        self.assertEqual(new_result.end_timestamp_s, self.read_result.end_timestamp_s)
        self.assertEqual(len(new_result.all_wrapped_packets), len(self.read_result.all_wrapped_packets))


if __name__ == '__main__':
    unittest.main()
