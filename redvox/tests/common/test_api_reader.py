"""
tests for api X reader
"""
from datetime import timedelta
import unittest
import os

import redvox.tests as tests
from redvox.common import date_time_utils as dtu
from redvox.common import api_reader


class ApiReaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.APIX_READER_TEST_DATA_DIR
        cls.api_900_extensions = {".rdvxz"}
        cls.api_1000_extensions = {".rdvxm"}

    def test_read_all_start_time(self):
        reader = api_reader.ApiReader(self.input_dir, True, start_dt_buf=timedelta(seconds=10),
                                      start_dt=dtu.datetime_from_epoch_microseconds_utc(1609984850000000))
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 12)
        result_by_id = reader.read_files_by_id("1637610021")
        self.assertEqual(len(result_by_id), 2)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637610021")
        result_by_id = reader.read_files_by_id("1637620010")
        self.assertEqual(len(result_by_id), 2)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637620010")
        result_by_id = reader.read_files_by_id("1637110703")
        self.assertEqual(len(result_by_id), 2)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637110703")

    def test_read_all_end_time(self):
        reader = api_reader.ApiReader(self.input_dir, True, end_dt_buf=timedelta(seconds=10),
                                      end_dt=dtu.datetime_from_epoch_microseconds_utc(1609984860000000))
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 12)
        result_by_id = reader.read_files_by_id("1637610021")
        self.assertEqual(len(result_by_id), 2)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637610021")
        result_by_id = reader.read_files_by_id("1637620010")
        self.assertEqual(len(result_by_id), 2)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637620010")
        result_by_id = reader.read_files_by_id("1637110703")
        self.assertEqual(len(result_by_id), 2)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637110703")

    def test_read_all_start_time_no_match(self):
        reader = api_reader.ApiReader(self.input_dir, True, start_dt=dtu.datetime_from_epoch_seconds_utc(1700000000))
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 0)

    def test_read_all_station_ids_no_match(self):
        api1000_dir = os.path.join(tests.APIX_READER_TEST_DATA_DIR, "api1000")
        reader = api_reader.ApiReader(api1000_dir, True, station_ids={"1637610021"})
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 0)
        result_by_id = reader.read_files_by_id("1637610021")
        self.assertIsNone(result_by_id)

    def test_read_all_station_ids(self):
        reader = api_reader.ApiReader(self.input_dir, True, station_ids={"1637610021", "0000000001"})
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 3)
        result_by_id = reader.read_files_by_id("1637610021")
        self.assertEqual(len(result_by_id), 3)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637610021")

    def test_read_all_api900_in_unstructured_dir(self):
        reader = api_reader.ApiReader(self.input_dir, extensions=self.api_900_extensions)
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 1)
        result_by_id = reader.read_files_by_id("1637650010")
        self.assertEqual(len(result_by_id), 1)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637650010")

    def test_read_all_api900_in_structured_dir(self):
        reader = api_reader.ApiReader(self.input_dir, True, extensions=self.api_900_extensions)
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 9)
        result_by_id = reader.read_files_by_id("1637610021")
        self.assertEqual(len(result_by_id), 3)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637610021")
        result_by_id = reader.read_files_by_id("1637620009")
        self.assertEqual(len(result_by_id), 3)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637620009")
        result_by_id = reader.read_files_by_id("1637110703")
        self.assertEqual(len(result_by_id), 3)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637110703")

    def test_read_all_api1000_in_unstructured_dir(self):
        reader = api_reader.ApiReader(self.input_dir, extensions=self.api_1000_extensions)
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 1)
        result_by_id = reader.read_files_by_id("0000000001")
        self.assertEqual(len(result_by_id), 1)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "0000000001")

    def test_read_all_api1000_in_structured_dir(self):
        reader = api_reader.ApiReader(self.input_dir, True, extensions=self.api_1000_extensions)
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 9)
        result_by_id = reader.read_files_by_id("1637610022")
        self.assertEqual(len(result_by_id), 3)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637610022")
        result_by_id = reader.read_files_by_id("1637620010")
        self.assertEqual(len(result_by_id), 3)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637620010")
        result_by_id = reader.read_files_by_id("1637110704")
        self.assertEqual(len(result_by_id), 3)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637110704")

    def test_read_all_in_unstructured_dir(self):
        reader = api_reader.ApiReader(self.input_dir)
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 2)
        result_by_id = reader.read_files_by_id("0000000001")
        self.assertEqual(len(result_by_id), 1)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "0000000001")
        result_by_id = reader.read_files_by_id("1637650010")
        self.assertEqual(len(result_by_id), 1)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637650010")

    def test_read_all_in_structured_dir(self):
        reader = api_reader.ApiReader(self.input_dir, True)
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 18)
        result_by_id = reader.read_files_by_id("1637610022")
        self.assertEqual(len(result_by_id), 3)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637610022")
        result_by_id = reader.read_files_by_id("1637620010")
        self.assertEqual(len(result_by_id), 3)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637620010")
        result_by_id = reader.read_files_by_id("1637620009")
        self.assertEqual(len(result_by_id), 3)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637620009")
        result_by_id = reader.read_files_by_id("1637110703")
        self.assertEqual(len(result_by_id), 3)
        self.assertEqual(result_by_id[0].get_station_information().get_id(), "1637110703")

    def test_filter_loop(self):
        filter_ids = ["1637610021", "1637610022", "1637620009", "1637620010", "1637650010"]
        final_result = 0
        for f_id in filter_ids:
            reader = api_reader.ApiReader(self.input_dir, True, station_ids={f_id})
            result = reader.index_summary.total_packets()
            if result == 0:
                self.assertTrue("1637650010" in reader.filter.station_ids)
                continue  # skip failed filter result
            self.assertEqual(result, 3)
            final_result += result
        self.assertEqual(final_result, 12)
