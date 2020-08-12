"""
tests for timesync
"""
import unittest
import os
import glob
import numpy as np
import redvox.tests as tests
from redvox.api1000 import io


class IoTest(unittest.TestCase):
    def setUp(self) -> None:
        test_dir = tests.TEST_DATA_DIR
        self.read_result = io.read_dir(test_dir)

    def test_read_dir(self):
        self.assertEqual(self.read_result.start_timestamp_s, None)
        self.assertEqual(len(self.read_result.all_wrapped_packets), 1)
        self.assertEqual(self.read_result.get_by_id("0000000001")[0][0].get_timing_information()
                         .get_packet_end_mach_timestamp(), 1597189457945991.0)
        self.assertEqual(len(self.read_result.all_wrapped_packets[0]._identify_gaps(5)), 0)


if __name__ == '__main__':
    unittest.main()
