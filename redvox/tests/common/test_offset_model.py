"""
tests for offset model
"""
import unittest

import numpy as np

import redvox.tests as tests
from redvox.common import offset_model as om
from redvox.common import file_statistics as fs
from redvox.common import date_time_utils as dtu
from redvox.common.io import ReadFilter, index_unstructured


class OffsetModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.apim_filter = ReadFilter(extensions={".rdvxm"}, station_ids={"0000000001"})
        cls.api900_filter = ReadFilter(extensions={".rdvxz"}, station_ids={"1637650010"})

    def test_model_init(self):
        index = index_unstructured(tests.TEST_DATA_DIR, self.apim_filter)
        stats = fs.extract_stats(index)
        latencies = [st.latency for st in stats]
        offsets = [st.offset for st in stats]
        times = [dtu.datetime_to_epoch_microseconds_utc(st.packet_start_dt) for st in stats]
        packet_duration = np.mean([dtu.seconds_to_microseconds(st.packet_duration.total_seconds()) for st in stats])
        model = om.OffsetModel(np.array(latencies), np.array(offsets),
                               times + 0.5 * packet_duration, 5, 3, times[0],
                               times[-1] + packet_duration)
        self.assertEqual(model.best_latency, 1296)
        self.assertEqual(model.best_offset, 3440)
        self.assertAlmostEqual(model.slope, 1.39e-06, 2)
        self.assertAlmostEqual(model.intercept, 3436.51, 2)
