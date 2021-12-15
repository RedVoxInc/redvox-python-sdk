import unittest

import numpy as np
import pyarrow as pa

import redvox.common.date_time_utils as dt
import redvox.common.gap_and_pad_utils as gpu


class CalcTimestampsTest(unittest.TestCase):
    def test_calc_timestamps(self):
        timestamps = gpu.calc_evenly_sampled_timestamps(1000., 100, 1000)
        self.assertEqual(len(timestamps), 100)
        self.assertEqual(timestamps[0], 1000)
        self.assertEqual(timestamps[1], 2000)
        self.assertEqual(timestamps[99], 100000)


class InterpolateGapsTest(unittest.TestCase):
    def test_create_simple_df(self):
        my_df = pa.Table.from_pydict({"timestamps": [1000., 8000., 9000., 15000.], "data": [50., 400., 450., 750.]})
        gaps = [(1000., 8000.), (9000., 15000.)]
        filled_df = gpu.fill_gaps(my_df, gaps, 1000.)
        self.assertEqual(len(filled_df[0]["timestamps"].to_numpy()), 15)

    def test_create_gap_after_end(self):
        my_df = pa.Table.from_pydict({"timestamps": [1000., 8000., 9000., 15000.], "data": [50., 400., 450., 750.]})
        gaps = [(1000., 8000.), (9000., 19000.)]
        filled_df = gpu.fill_gaps(my_df, gaps, 1000.)
        self.assertEqual(len(filled_df[0]["timestamps"].to_numpy()), 15)

    def test_create_gap_before_begin(self):
        my_df = pa.Table.from_pydict({"timestamps": [11000., 18000., 19000., 25000.], "data": [50., 400., 450., 750.]})
        gaps = [(1000., 18000.), (19000., 29000.)]
        filled_df = gpu.fill_gaps(my_df, gaps, 1000.)
        self.assertEqual(len(filled_df[0]["timestamps"].to_numpy()), 15)

    def test_create_gap_intersect_end(self):
        my_df = pa.Table.from_pydict({"timestamps": [1000., 8000., 9000., 15000.], "data": [50., 400., 450., 750.]})
        gaps = [(1000., 7000.), (6000., 8000.), (9000., 15000.)]
        filled_df = gpu.fill_gaps(my_df, gaps, 1000.)
        self.assertEqual(len(filled_df[0]["timestamps"].to_numpy()), 15)

    def test_create_gap_intersect_begin(self):
        my_df = pa.Table.from_pydict({"timestamps": [1000., 8000., 9000., 15000.], "data": [50., 400., 450., 750.]})
        gaps = [(5000., 8000.), (1000., 7000.), (9000., 15000.)]
        filled_df = gpu.fill_gaps(my_df, gaps, 1000.)
        self.assertEqual(len(filled_df[0]["timestamps"].to_numpy()), 15)

    def test_create_gap_overlap(self):
        my_df = pa.Table.from_pydict({"timestamps": [1000., 8000., 9000., 15000.], "data": [50., 400., 450., 750.]})
        gaps = [(4000., 6000.), (1000., 8000.), (9000., 15000.)]
        filled_df = gpu.fill_gaps(my_df, gaps, 1000.)
        self.assertEqual(len(filled_df[0]["timestamps"].to_numpy()), 15)


class AudioGapFillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sample_interval = 250

    def test_audio_gap_df(self):
        my_data = [(1000., pa.Table.from_pydict({"microphone": [10, 20, 30, 40]})),
                   (2000., pa.Table.from_pydict({"microphone": [40, 30, 20, 10]})),
                   (5000., pa.Table.from_pydict({"microphone": [5, 15, 25, 35]}))
                   ]
        result = gpu.fill_audio_gaps(my_data, self.sample_interval)
        filled_df = result.result
        gaps = result.gaps
        self.assertEqual(len(filled_df["timestamps"]), 20)
        self.assertEqual(len(gaps), 1)

    def test_misshapen_audio_gap_df(self):
        my_data = [(1000., pa.Table.from_pydict({"microphone": [10, 20, 30, 40]})),
                   (2000., pa.Table.from_pydict({"microphone": [40, 30, 20, 10]})),
                   (5000., pa.Table.from_pydict({"microphone": [5, 15, 25, 35]}))
                   ]
        result = gpu.fill_audio_gaps(my_data, self.sample_interval)
        filled_df = result.result
        gaps = result.gaps
        self.assertEqual(len(filled_df["timestamps"]), 20)
        self.assertEqual(len(gaps), 1)

    def test_tiny_audio_gap_df(self):
        my_data = [(1000., pa.Table.from_pydict({"microphone": [10, 20, 30, 40]})),
                   (2000., pa.Table.from_pydict({"microphone": [40, 30, 20, 10]})),
                   (3005., pa.Table.from_pydict({"microphone": [5, 15, 25, 35]}))
                   ]
        result = gpu.fill_audio_gaps(my_data, self.sample_interval)
        filled_df = result.result
        gaps = result.gaps
        self.assertEqual(len(filled_df["timestamps"]), 12)
        self.assertEqual(len(gaps), 0)

    def test_undersized_audio_gap_df(self):
        my_data = [(1000., pa.Table.from_pydict({"microphone": [10, 20, 30, 40]})),
                   (2000., pa.Table.from_pydict({"microphone": [40, 30, 20, 10]})),
                   (3100., pa.Table.from_pydict({"microphone": [5, 15, 25, 35]}))
                   ]
        result = gpu.fill_audio_gaps(my_data, self.sample_interval)
        filled_df = result.result
        gaps = result.gaps
        self.assertEqual(len(filled_df["timestamps"]), 13)
        self.assertEqual(len(gaps), 1)

    def test_failure_audio_gap_df(self):
        my_data = [(1000., pa.Table.from_pydict({"microphone": [10, 20, 30, 40]})),
                   (1500., pa.Table.from_pydict({"microphone": [40, 30, 20, 10]}))
                   ]
        result = gpu.fill_audio_gaps(my_data, self.sample_interval)
        error = result.errors.get()
        self.assertEqual(len(error), 1)
