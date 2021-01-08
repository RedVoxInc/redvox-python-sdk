"""
tests for api X reader
"""
import unittest

import redvox.tests as tests
from redvox.common import date_time_utils as dtu
from redvox.common import api_reader
from redvox.common.io import types as io_types


class ApiReaderTest(unittest.TestCase):
    def setUp(self):
        self.input_dir = tests.APIX_READER_TEST_DATA_DIR
        self.filter = io_types.ReadFilter(extensions={".rdvxm", ".rdvxz"})
        self.api_900_filter = io_types.ReadFilter(extensions={".rdvxz"})
        self.api_1000_filter = io_types.ReadFilter(extensions={".rdvxm"})

    # todo: filter on time
    # def test_read_all_in_dir_start_time(self):
    #     time_filter = io_types.ReadFilter(extensions={".rdvxm", ".rdvxz"},
    #                                       start_dt=dtu.datetime_from_epoch_microseconds_utc(1609984840000000))
    #     result = api_reader.read_all_in_dir(self.input_dir, time_filter, True)
    #     self.assertEqual(len(result.station_id_uuid_to_packets.keys()), 1)
    #     self.assertEqual(len(result.get_packets_for_station_id("1637610021")), 3)

    def test_read_all_in_dir_station_ids(self):
        ids_filter = io_types.ReadFilter(extensions={".rdvxm", ".rdvxz"}, station_ids={"1637610021", "0000000001"})
        result = api_reader.read_all_in_dir(self.input_dir, ids_filter, True)
        self.assertEqual(len(result.station_id_uuid_to_packets.keys()), 1)
        self.assertEqual(len(result.get_packets_for_station_id("1637610021")), 3)

    def test_read_all_api900_in_unstructured_dir(self):
        result = api_reader.read_all_in_dir(self.input_dir, self.api_900_filter)
        self.assertEqual(len(result.station_id_uuid_to_packets.keys()), 1)
        self.assertEqual(len(result.get_packets_for_station_id("1637650010")), 1)

    def test_read_all_api900_in_structured_dir_io_raw(self):
        result = api_reader.read_all_in_dir(self.input_dir, self.api_900_filter, True)
        self.assertEqual(len(result.station_id_uuid_to_packets.keys()), 3)
        self.assertEqual(len(result.get_packets_for_station_id("1637610021")), 3)
        self.assertEqual(len(result.get_packets_for_station_id("1637620009")), 3)
        self.assertEqual(len(result.get_packets_for_station_id("1637110703")), 3)

    def test_read_all_api1000_in_unstructured_dir(self):
        result = api_reader.read_all_in_dir(self.input_dir, self.api_1000_filter)
        self.assertEqual(len(result.station_id_uuid_to_packets.keys()), 1)
        self.assertEqual(len(result.get_packets_for_station_id("0000000001")), 1)

    def test_read_all_api1000_in_structured_dir_io_raw(self):
        result = api_reader.read_all_in_dir(self.input_dir, self.api_1000_filter, True)
        self.assertEqual(len(result.station_id_uuid_to_packets.keys()), 3)
        self.assertEqual(len(result.get_packets_for_station_id("1637610022")), 3)
        self.assertEqual(len(result.get_packets_for_station_id("1637620010")), 3)
        self.assertEqual(len(result.get_packets_for_station_id("1637110704")), 3)

    def test_read_all_in_unstructured_dir(self):
        result = api_reader.read_all_in_dir(self.input_dir, self.filter)
        self.assertEqual(len(result.station_id_uuid_to_packets.keys()), 2)
        self.assertEqual(len(result.get_packets_for_station_id("0000000001")), 1)
        self.assertEqual(len(result.get_packets_for_station_id("1637650010")), 1)

    def test_read_all_in_structured_dir_io_raw(self):
        result = api_reader.read_all_in_dir(self.input_dir, self.filter, True)
        self.assertEqual(len(result.station_id_uuid_to_packets.keys()), 6)
        self.assertEqual(len(result.get_packets_for_station_id("1637610022")), 3)
        self.assertEqual(len(result.get_packets_for_station_id("1637620009")), 3)
        self.assertEqual(len(result.get_packets_for_station_id("1637110703")), 3)
        self.assertEqual(len(result.get_packets_for_station_id("1637620010")), 3)
