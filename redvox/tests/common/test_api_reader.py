"""
tests for api X reader
"""
from datetime import timedelta
import unittest
import os

import redvox.tests as tests
from redvox.common import date_time_utils as dtu
from redvox.common import api_reader, io


class ApiReaderTest(unittest.TestCase):
    def setUp(self):
        self.input_dir = tests.APIX_READER_TEST_DATA_DIR
        self.filter = io.ReadFilter(extensions={".rdvxm", ".rdvxz"})
        self.api_900_filter = io.ReadFilter(extensions={".rdvxz"})
        self.api_1000_filter = io.ReadFilter(extensions={".rdvxm"})

    def test_read_all_in_dir_start_time(self):
        time_filter = io.ReadFilter(extensions={".rdvxm", ".rdvxz"}, start_dt_buf=timedelta(seconds=10),
                                    start_dt=dtu.datetime_from_epoch_microseconds_utc(1609984850000000))
        reader = api_reader.ApiReader(time_filter, self.input_dir, True)
        result = reader.read_files()
        self.assertEqual(len(result), 12)
        result_by_id = api_reader.get_data_by_id(result, "1637610021")
        self.assertEqual(len(result_by_id), 2)
        result_by_id = api_reader.get_data_by_id(result, "1637620009")
        self.assertEqual(len(result_by_id), 2)
        result_by_id = api_reader.get_data_by_id(result, "1637110703")
        self.assertEqual(len(result_by_id), 2)

    def test_read_all_in_dir_station_ids_fail(self):
        ids_filter = io.ReadFilter(extensions={".rdvxm", ".rdvxz"}, station_ids={"1637610021"})
        api1000_dir = os.path.join(tests.APIX_READER_TEST_DATA_DIR, "api1000")
        reader = api_reader.ApiReader(ids_filter, api1000_dir, True)
        result = reader.read_files()
        self.assertEqual(len(result), 0)

    def test_read_all_in_dir_station_ids(self):
        ids_filter = io.ReadFilter(extensions={".rdvxm", ".rdvxz"}, station_ids={"1637610021", "0000000001"})
        reader = api_reader.ApiReader(ids_filter, self.input_dir, True)
        result = reader.read_files()
        self.assertEqual(len(result), 3)
        result_by_id = api_reader.get_data_by_id(result, "1637610021")
        self.assertEqual(len(result_by_id), 3)

    def test_read_all_api900_in_unstructured_dir(self):
        reader = api_reader.ApiReader(self.api_900_filter, self.input_dir)
        result = reader.read_files()
        self.assertEqual(len(result), 1)
        result_by_id = api_reader.get_data_by_id(result, "1637650010")
        self.assertEqual(len(result_by_id), 1)

    def test_read_all_api900_in_structured_dir_io_raw(self):
        reader = api_reader.ApiReader(self.api_900_filter, self.input_dir, True)
        result = reader.read_files()
        self.assertEqual(len(result), 9)
        result_by_id = api_reader.get_data_by_id(result, "1637610021")
        self.assertEqual(len(result_by_id), 3)
        result_by_id = api_reader.get_data_by_id(result, "1637620009")
        self.assertEqual(len(result_by_id), 3)
        result_by_id = api_reader.get_data_by_id(result, "1637110703")
        self.assertEqual(len(result_by_id), 3)

    def test_read_all_api1000_in_unstructured_dir(self):
        reader = api_reader.ApiReader(self.api_1000_filter, self.input_dir)
        result = reader.read_files()
        self.assertEqual(len(result), 1)
        result_by_id = api_reader.get_data_by_id(result, "0000000001")
        self.assertEqual(len(result_by_id), 1)

    def test_read_all_api1000_in_structured_dir_io_raw(self):
        reader = api_reader.ApiReader(self.api_1000_filter, self.input_dir, True)
        result = reader.read_files()
        self.assertEqual(len(result), 9)
        result_by_id = api_reader.get_data_by_id(result, "1637610022")
        self.assertEqual(len(result_by_id), 3)
        result_by_id = api_reader.get_data_by_id(result, "1637620010")
        self.assertEqual(len(result_by_id), 3)
        result_by_id = api_reader.get_data_by_id(result, "1637110704")
        self.assertEqual(len(result_by_id), 3)

    def test_read_all_in_unstructured_dir(self):
        reader = api_reader.ApiReader(self.filter, self.input_dir)
        result = reader.read_files()
        self.assertEqual(len(result), 2)
        result_by_id = api_reader.get_data_by_id(result, "0000000001")
        self.assertEqual(len(result_by_id), 1)
        result_by_id = api_reader.get_data_by_id(result, "1637650010")
        self.assertEqual(len(result_by_id), 1)

    def test_read_all_in_structured_dir_io_raw(self):
        reader = api_reader.ApiReader(self.filter, self.input_dir, True)
        result = reader.read_files()
        self.assertEqual(len(result), 18)
        result_by_id = api_reader.get_data_by_id(result, "1637610022")
        self.assertEqual(len(result_by_id), 3)
        result_by_id = api_reader.get_data_by_id(result, "1637620010")
        self.assertEqual(len(result_by_id), 3)
        result_by_id = api_reader.get_data_by_id(result, "1637620009")
        self.assertEqual(len(result_by_id), 3)
        result_by_id = api_reader.get_data_by_id(result, "1637110703")
        self.assertEqual(len(result_by_id), 3)

    def test_filter_loop(self):
        filter_ids = ["1637610021", "1637610022", "1637620009", "1637620010", "1637650010"]
        final_result = []
        for f_id in filter_ids:
            read_filter = io.ReadFilter(station_ids={f_id})
            reader = api_reader.ApiReader(read_filter, self.input_dir, True)
            result = reader.read_files()
            if len(result) == 0:
                self.assertTrue("1637650010" in reader.filter.station_ids)
                continue  # skip failed filter result
            self.assertEqual(len(result), 3)
            final_result.extend(result)
        self.assertEqual(len(final_result), 12)
