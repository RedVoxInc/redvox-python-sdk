"""
tests for packet to pyarrow
"""
import unittest
import contextlib

import redvox.tests as tests
from redvox.common import api_reader
from redvox.common.io import ReadFilter
import redvox.common.packet_to_pyarrow as ptp
from redvox.common.sensor_data import SensorType


class PyarrowSummaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with contextlib.redirect_stdout(None):
            reader = api_reader.ApiReader(
                tests.TEST_DATA_DIR,
                False,
                ReadFilter(extensions={".rdvxm"}, station_ids={"0000000001"}),
            )
            cls.indexes = reader.files_index

    def test_packet_to_pyarrow(self):
        pkt = self.indexes[0].read_contents()[0]
        summary = ptp.packet_to_pyarrow(pkt)
        self.assertEqual(len(summary.summaries), 3)
        self.assertTrue(SensorType.AUDIO in summary.sensor_types())

    def test_aggregate_summary(self):
        summaries = ptp.AggregateSummary()
        for idx in self.indexes:
            pkts = idx.read_contents()
            summaries.add_aggregate_summary(ptp.stream_to_pyarrow(pkts, None))
        self.assertEqual(len(summaries.summaries), 9)
        dct = summaries.to_dict()
        frm_dct = ptp.AggregateSummary.from_dict(dct)
        self.assertEqual(len(frm_dct.summaries), len(summaries.summaries))
