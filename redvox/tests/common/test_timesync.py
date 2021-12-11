"""
tests for timesync
"""
import unittest
import contextlib
import redvox.tests as tests
from redvox.common import timesync as ts
from redvox.common import api_reader
from redvox.common.io import ReadFilter


class TimesyncTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with contextlib.redirect_stdout(None):
            result = api_reader.ApiReader(tests.TEST_DATA_DIR, structured_dir=False,
                                          read_filter=ReadFilter(station_ids={"1637680001"}))
            cls.timesync = ts.TimeSync().from_raw_packets(result.read_files_by_id("1637680001"))

    def test_num_tri_messages(self):
        self.assertEqual(self.timesync.num_tri_messages(), 14)

    def test_latencies(self):
        self.assertEqual(len(self.timesync.latencies()[0]), 14)
        self.assertEqual(self.timesync.latencies()[0][0], 74559.5)

    def test_offsets(self):
        self.assertEqual(len(self.timesync.offsets()[0]), 14)
        self.assertEqual(self.timesync.offsets()[0][0], -22907018.5)

    def test_best_latencies_per_exchange(self):
        ltncs = self.timesync.best_latency_per_exchange()
        self.assertEqual(len(ltncs), 14)
        self.assertEqual(ltncs[0], 74559.5)
        self.assertEqual(self.timesync.best_latency(), ltncs[2])

    def test_best_offsets_per_exchange(self):
        ofsts = self.timesync.best_offset_per_exchange()
        self.assertEqual(len(ofsts), 14)
        self.assertEqual(ofsts[0], -22907018.5)
        self.assertEqual(self.timesync.best_offset(), ofsts[2])

    def test_best_latency(self):
        self.assertEqual(self.timesync.best_latency(), 69664.0)
        self.assertEqual(self.timesync.best_latency_index(), 2)

    def test_best_offset(self):
        self.assertEqual(self.timesync.best_offset(), -22906528.0)

    def test_latency_mean(self):
        self.assertAlmostEqual(self.timesync.mean_latency(), 118049.66, 2)

    def test_latency_std_dev(self):
        self.assertAlmostEqual(self.timesync.latency_std(), 84458.71, 2)

    def test_offset_mean(self):
        self.assertAlmostEqual(self.timesync.mean_offset(), -22903096.02, 2)

    def test_offset_std_dev(self):
        self.assertAlmostEqual(self.timesync.offset_std(), 91847.39, 2)

    def test_best_latency_timestamp(self):
        self.assertEqual(self.timesync.get_best_latency_timestamp(), 1532459236518989.)
