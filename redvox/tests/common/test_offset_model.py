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
        times = [st.best_latency_timestamp for st in stats]
        start_time = dtu.datetime_to_epoch_microseconds_utc(stats[0].packet_start_dt)
        end_time = dtu.datetime_to_epoch_microseconds_utc(stats[-1].packet_start_dt + stats[-1].packet_duration)
        model = om.OffsetModel(np.array(latencies), np.array(offsets), np.array(times), start_time, end_time)
        self.assertEqual(model.intercept, 3440)
        self.assertEqual(model.slope, 0.0)

    def test_empty_model(self):
        model = om.OffsetModel.empty_model()
        self.assertEqual(model.intercept, 0.)
        self.assertEqual(model.slope, 0.)
        self.assertEqual(model.score, 0.)
        self.assertEqual(model.k_bins, 1)
        self.assertEqual(model.n_samples, 3)
        self.assertEqual(model.mean_latency, 0.0)
        self.assertEqual(model.std_dev_latency, 0.0)
