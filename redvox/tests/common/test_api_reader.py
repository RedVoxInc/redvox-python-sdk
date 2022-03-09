"""
tests for api X reader
"""
from datetime import timedelta
import unittest
import os

import redvox.tests as tests
from redvox.common import date_time_utils as dtu
from redvox.common import api_reader
from redvox.common.io import ReadFilter


class ApiReaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.APIX_READER_TEST_DATA_DIR
        cls.api_900_extensions = {".rdvxz"}
        cls.api_1000_extensions = {".rdvxm"}

    def test_read_all_start_time(self):
        reader = api_reader.ApiReader(
            self.input_dir,
            True,
            ReadFilter(start_dt_buf=timedelta(seconds=30),
                       start_dt=dtu.datetime_from_epoch_seconds_utc(1611696200)),
        )
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 2)
        result_by_id = reader.read_files_by_id("1000001000")
        self.assertEqual(len(result_by_id), 1)
        self.assertEqual(
            result_by_id[0].station_information.id, "1000001000"
        )

    def test_read_all_end_time(self):
        reader = api_reader.ApiReader(
            self.input_dir,
            True,
            ReadFilter(end_dt_buf=timedelta(seconds=30),
                       end_dt=dtu.datetime_from_epoch_seconds_utc(1611696100)),
        )
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 2)
        result_by_id = reader.read_files_by_id("1000000900")
        self.assertEqual(len(result_by_id), 1)
        self.assertEqual(
            result_by_id[0].station_information.id, "1000000900"
        )

    def test_read_all_start_time_no_match(self):
        reader = api_reader.ApiReader(
            self.input_dir,
            True,
            ReadFilter(start_dt=dtu.datetime_from_epoch_seconds_utc(1700000000)),
        )
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 0)

    def test_read_all_station_ids_no_match(self):
        api1000_dir = os.path.join(self.input_dir, "api1000")
        reader = api_reader.ApiReader(api1000_dir, True, ReadFilter(station_ids={"1000000900"}))
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 0)
        result_by_id = reader.read_files_by_id("1000000900")
        self.assertIsNone(result_by_id)

    def test_read_all_station_ids(self):
        reader = api_reader.ApiReader(
            self.input_dir, True, ReadFilter(station_ids={"1000001000", "2000001000"})
        )
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 2)
        result_by_id = reader.read_files_by_id("1000001000")
        self.assertEqual(len(result_by_id), 2)
        self.assertEqual(
            result_by_id[0].station_information.id, "1000001000"
        )

    def test_read_all_api900_in_unstructured_dir(self):
        reader = api_reader.ApiReader(
            self.input_dir, read_filter=ReadFilter(extensions=self.api_900_extensions)
        )
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 1)
        result_by_id = reader.read_files_by_id("2000000900")
        self.assertEqual(len(result_by_id), 1)
        self.assertEqual(
            result_by_id[0].station_information.id, "2000000900"
        )

    def test_read_all_api900_in_structured_dir(self):
        reader = api_reader.ApiReader(
            self.input_dir, True, ReadFilter(extensions=self.api_900_extensions)
        )
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 2)
        result_by_id = reader.read_files_by_id("1000000900")
        self.assertEqual(len(result_by_id), 2)
        self.assertEqual(
            result_by_id[0].station_information.id, "1000000900"
        )

    def test_read_all_api1000_in_unstructured_dir(self):
        reader = api_reader.ApiReader(
            self.input_dir, read_filter=ReadFilter(extensions=self.api_1000_extensions)
        )
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 1)
        result_by_id = reader.read_files_by_id("2000001000")
        self.assertEqual(len(result_by_id), 1)
        self.assertEqual(
            result_by_id[0].station_information.id, "2000001000"
        )

    def test_read_all_api1000_in_structured_dir(self):
        reader = api_reader.ApiReader(
            self.input_dir, True, ReadFilter(extensions=self.api_1000_extensions)
        )
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 2)
        result_by_id = reader.read_files_by_id("1000001000")
        self.assertEqual(len(result_by_id), 2)
        self.assertEqual(
            result_by_id[0].station_information.id, "1000001000"
        )

    def test_read_all_in_unstructured_dir(self):
        reader = api_reader.ApiReader(self.input_dir)
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 2)
        result_by_id = reader.read_files_by_id("2000001000")
        self.assertEqual(len(result_by_id), 1)
        self.assertEqual(
            result_by_id[0].station_information.id, "2000001000"
        )
        result_by_id = reader.read_files_by_id("2000000900")
        self.assertEqual(len(result_by_id), 1)
        self.assertEqual(
            result_by_id[0].station_information.id, "2000000900"
        )

    def test_read_all_in_structured_dir(self):
        reader = api_reader.ApiReader(self.input_dir, True)
        result = reader.index_summary.total_packets()
        self.assertEqual(result, 4)
        result_by_id = reader.read_files_by_id("1000001000")
        self.assertEqual(len(result_by_id), 2)
        self.assertEqual(
            result_by_id[0].station_information.id, "1000001000"
        )
        result_by_id = reader.read_files_by_id("1000000900")
        self.assertEqual(len(result_by_id), 2)
        self.assertEqual(
            result_by_id[0].station_information.id, "1000000900"
        )

    def test_filter_loop(self):
        filter_ids = ["1000000900", "1000001000", "2000000900"]
        final_result = 0
        for f_id in filter_ids:
            reader = api_reader.ApiReader(self.input_dir, True, ReadFilter(station_ids={f_id}))
            result = reader.index_summary.total_packets()
            if result == 0:
                self.assertTrue("2000000900" in reader.filter.station_ids)
                continue  # skip failed filter result
            self.assertEqual(result, 2)
            final_result += result
        self.assertEqual(final_result, 4)

    def test_file_size(self):
        reader = api_reader.ApiReader(self.input_dir)
        for i in reader.index_summary.station_summaries.values():
            for s in i.values():
                self.assertTrue(s.single_packet_decompressed_size_bytes > 0)
