"""
tests for api X reader
"""
import unittest

import redvox.tests as tests
from redvox.common import api_reader


class ApiReaderTest(unittest.TestCase):
    def setUp(self):
        self.input_dir = tests.APIX_READER_TEST_DATA_DIR

    # def test_api_reader_read_all_in_dir(self):
    #     result = api_reader.read_all_in_dir(self.input_dir, structured_layout=True)
    #     self.assertEqual(len(result.all_wrapped_packets), 6)
    #     self.assertEqual(len(result.get_by_id("1637610022")), 3)
    #     self.assertEqual(len(result.get_by_id("1637620009")), 3)
    #     self.assertEqual(len(result.get_by_id("1637110703")), 3)
    #     self.assertEqual(len(result.get_by_id("1637620010")), 3)

    def test_read_all_in_unstructured_dir(self):
        result = api_reader.read_all_in_unstructured_dir(self.input_dir)
        self.assertEqual(len(result.station_id_uuid_to_packets.keys()), 2)
        self.assertEqual(len(result.get_packets_for_station_id("0000000001")), 1)
        self.assertEqual(len(result.get_packets_for_station_id("1637650010")), 1)

    def test_read_all_in_structured_dir_io_raw(self):
        result = api_reader.read_all_in_structured_dir_io_raw(self.input_dir)
        self.assertEqual(len(result.station_id_uuid_to_packets.keys()), 6)
        self.assertEqual(len(result.get_packets_for_station_id("1637610022")), 3)
        self.assertEqual(len(result.get_packets_for_station_id("1637620009")), 3)
        self.assertEqual(len(result.get_packets_for_station_id("1637110703")), 3)
        self.assertEqual(len(result.get_packets_for_station_id("1637620010")), 3)
