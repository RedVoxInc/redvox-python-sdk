import unittest

import numpy as np
import pandas as pd

import redvox.common.date_time_utils as dt
import redvox.common.gap_and_pad_utils_old as gpu


class CalcTimestampsTest(unittest.TestCase):
    def test_calc_timestamps(self):
        timestamps = gpu.calc_evenly_sampled_timestamps(1000, 100, 1000)
        self.assertEqual(len(timestamps), 100)
        self.assertEqual(timestamps[0], 1000)
        self.assertEqual(timestamps[1], 2000)
        self.assertEqual(timestamps[99], 100000)


class PadDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.timestamps = [
            dt.seconds_to_microseconds(40),
            dt.seconds_to_microseconds(50),
            dt.seconds_to_microseconds(60),
        ]

    def test_pad_data(self):
        filled_dataframe = gpu.pad_data(
            dt.seconds_to_microseconds(10),
            dt.seconds_to_microseconds(100),
            pd.DataFrame(np.transpose([self.timestamps, [4, 5, 6]]), columns=["timestamps", "temp"]),
            dt.seconds_to_microseconds(10),
        )
        self.assertEqual(filled_dataframe.shape, (10, 2))
        self.assertEqual(
            filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(20)
        )
        self.assertEqual(
            filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(30)
        )

    def test_pad_data_single_value(self):
        filled_singleton = gpu.pad_data(
            dt.seconds_to_microseconds(10),
            dt.seconds_to_microseconds(100),
            pd.DataFrame([[self.timestamps[0], 1]], columns=["timestamps", "temp"]),
            dt.seconds_to_microseconds(10),
        )
        self.assertEqual(filled_singleton.shape, (10, 2))
        self.assertEqual(
            filled_singleton.loc[1, "timestamps"], dt.seconds_to_microseconds(20)
        )
        self.assertEqual(
            filled_singleton.loc[3, "timestamps"], dt.seconds_to_microseconds(40)
        )

    def test_pad_data_uneven_ends(self):
        filled_dataframe = gpu.pad_data(
            dt.seconds_to_microseconds(10),
            dt.seconds_to_microseconds(100),
            pd.DataFrame(np.transpose([self.timestamps, [4, 5, 6]]), columns=["timestamps", "temp"]),
            dt.seconds_to_microseconds(12),
        )
        self.assertEqual(filled_dataframe.shape, (8, 2))
        self.assertEqual(
            filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(28)
        )
        self.assertEqual(
            filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(40)
        )
        self.assertEqual(
            filled_dataframe.loc[6, "timestamps"], dt.seconds_to_microseconds(84)
        )
        self.assertEqual(
            filled_dataframe.loc[7, "timestamps"], dt.seconds_to_microseconds(96)
        )


# class FillGapTest(unittest.TestCase):
#     @classmethod
#     def setUpClass(cls) -> None:
#         timestamps = [
#             dt.seconds_to_microseconds(10),
#             dt.seconds_to_microseconds(30),
#             dt.seconds_to_microseconds(100),
#         ]
#         cls.dataframe = pd.DataFrame(
#             np.transpose([timestamps, [1, 3, 10]]), columns=["timestamps", "temp"]
#         )
#         cls.singleton = pd.DataFrame(
#             [[timestamps[0], 1]], columns=["timestamps", "temp"]
#         )
#
#     def test_singleton_fill_gaps(self):
#         filled_singleton = gpu.fill_gaps(
#             self.singleton,
#             dt.seconds_to_microseconds(10),
#             dt.seconds_to_microseconds(10)
#         )
#         self.assertEqual(filled_singleton.shape, (1, 2))
#         self.assertEqual(
#             filled_singleton.loc[0, "timestamps"], dt.seconds_to_microseconds(10)
#         )
#
#     def test_fill_gaps(self):
#         filled_dataframe = gpu.fill_gaps(
#             self.dataframe,
#             dt.seconds_to_microseconds(10),
#             dt.seconds_to_microseconds(10)
#         )
#         self.assertEqual(filled_dataframe.shape, (10, 2))
#         self.assertEqual(
#             filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(20)
#         )
#         self.assertEqual(
#             filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(30)
#         )
#
#     def test_fill_gaps_long_interval(self):
#         filled_dataframe = gpu.fill_gaps(
#             self.dataframe,
#             dt.seconds_to_microseconds(20),
#             dt.seconds_to_microseconds(10),
#         )
#         self.assertEqual(filled_dataframe.shape, (6, 2))
#         self.assertEqual(
#             filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(30)
#         )
#         self.assertEqual(
#             filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(50)
#         )
#
#     def test_fill_gaps_long_gap(self):
#         filled_dataframe = gpu.fill_gaps(
#             self.dataframe,
#             dt.seconds_to_microseconds(10),
#             dt.seconds_to_microseconds(20),
#         )
#         self.assertEqual(filled_dataframe.shape, (9, 2))
#         self.assertEqual(
#             filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(30)
#         )
#         self.assertEqual(
#             filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(40)
#         )


class CreateDatalessTimestampsDFTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base_df = pd.DataFrame([], columns=["timestamps", "data"])

    def test_create_dataless_timestamps_df(self):
        new_df = gpu.create_dataless_timestamps_df(2000, 1000, self.base_df.columns, 7, False)
        self.assertEqual(new_df.iloc[0].loc["timestamps"], 3000)
        self.assertEqual(new_df.iloc[6].loc["timestamps"], 9000)
        new_df = gpu.create_dataless_timestamps_df(8000, 1000, self.base_df.columns, 7, True)
        self.assertEqual(new_df.iloc[0].loc["timestamps"], 7000)
        self.assertEqual(new_df.iloc[6].loc["timestamps"], 1000)

    def test_add_dataless_timestamps_df_empty(self):
        # dataframe to alter is empty, so nothing changes
        new_base_df = self.base_df.copy()
        new_df = gpu.add_dataless_timestamps_to_df(new_base_df, 0, 1000, 7, False)
        self.assertEqual(len(new_df), 0)

    def test_add_dataless_timestamps_df(self):
        new_df = gpu.create_dataless_timestamps_df(8000, 1000, self.base_df.columns, 7, True)
        new_df = gpu.add_dataless_timestamps_to_df(new_df, 6, 1000, 7, False)
        self.assertEqual(new_df.iloc[7].loc["timestamps"], 2000)
        self.assertEqual(new_df.iloc[13].loc["timestamps"], 8000)
        new_df = gpu.add_dataless_timestamps_to_df(new_df, 0, 1000, 7, True)
        self.assertEqual(new_df.iloc[14].loc["timestamps"], 6000)
        self.assertEqual(new_df.iloc[20].loc["timestamps"], 0)

    def test_add_dataless_timestamps_df_index_too_high(self):
        # no change to dataframe if index is too high
        new_df = gpu.create_dataless_timestamps_df(8000, 1000, self.base_df.columns, 7, True)
        new_df = gpu.add_dataless_timestamps_to_df(new_df, 99, 1000, 7, True)
        self.assertEqual(len(new_df), 7)
        self.assertEqual(new_df.iloc[0].loc["timestamps"], 7000)
        self.assertEqual(new_df.iloc[6].loc["timestamps"], 1000)

    def test_add_dataless_timestamps_df_not_enough_samples(self):
        # no change to dataframe if adding less than 1 samples
        new_df = gpu.create_dataless_timestamps_df(8000, 1000, self.base_df.columns, 7, True)
        new_df = gpu.add_dataless_timestamps_to_df(new_df, 0, 1000, -10, True)
        self.assertEqual(len(new_df), 7)
        self.assertEqual(new_df.iloc[0].loc["timestamps"], 7000)
        self.assertEqual(new_df.iloc[6].loc["timestamps"], 1000)
        new_df = gpu.add_dataless_timestamps_to_df(new_df, 0, 1000, 0, True)
        self.assertEqual(len(new_df), 7)
        self.assertEqual(new_df.iloc[0].loc["timestamps"], 7000)
        self.assertEqual(new_df.iloc[6].loc["timestamps"], 1000)


class InterpolateGapsTest(unittest.TestCase):
    def test_create_simple_df(self):
        my_df = pd.DataFrame([[1000, 50], [8000, 400], [9000, 450], [15000, 750]], columns=["timestamps", "data"])
        gaps = [(1000, 8000), (9000, 15000)]
        filled_df = gpu.fill_gaps(my_df, gaps, 1000)
        self.assertEqual(len(filled_df["timestamps"]), 15)

    def test_create_gap_after_end(self):
        my_df = pd.DataFrame([[1000, 50], [8000, 400], [9000, 450], [15000, 750]], columns=["timestamps", "data"])
        gaps = [(1000, 8000), (9000, 19000)]
        filled_df = gpu.fill_gaps(my_df, gaps, 1000)
        self.assertEqual(len(filled_df["timestamps"]), 15)

    def test_create_gap_before_begin(self):
        my_df = pd.DataFrame([[11000, 50], [18000, 400], [19000, 450], [25000, 750]], columns=["timestamps", "data"])
        gaps = [(1000, 18000), (19000, 29000)]
        filled_df = gpu.fill_gaps(my_df, gaps, 1000)
        self.assertEqual(len(filled_df["timestamps"]), 15)

    def test_create_gap_intersect_end(self):
        my_df = pd.DataFrame([[1000, 50], [8000, 400], [9000, 450], [15000, 750]], columns=["timestamps", "data"])
        gaps = [(1000, 7000), (6000, 8000), (9000, 15000)]
        filled_df = gpu.fill_gaps(my_df, gaps, 1000)
        self.assertEqual(len(filled_df["timestamps"]), 15)

    def test_create_gap_intersect_begin(self):
        my_df = pd.DataFrame([[1000, 50], [8000, 400], [9000, 450], [15000, 750]], columns=["timestamps", "data"])
        gaps = [(5000, 8000), (1000, 7000), (9000, 15000)]
        filled_df = gpu.fill_gaps(my_df, gaps, 1000)
        self.assertEqual(len(filled_df["timestamps"]), 15)

    def test_create_gap_overlap(self):
        my_df = pd.DataFrame([[1000, 50], [8000, 400], [9000, 450], [15000, 750]], columns=["timestamps", "data"])
        gaps = [(4000, 6000), (1000, 8000), (9000, 15000)]
        filled_df = gpu.fill_gaps(my_df, gaps, 1000)
        self.assertEqual(len(filled_df["timestamps"]), 15)


class AudioGapFillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sample_interval = 250

    def test_audio_gap_df(self):
        my_data = ([(1000, [10, 20, 30, 40]), (2000, [40, 30, 20, 10]), (5000, [5, 15, 25, 35])])
        result = gpu.fill_audio_gaps(my_data, self.sample_interval)
        filled_df = result.result_df
        gaps = result.gaps
        self.assertEqual(len(filled_df["timestamps"]), 20)
        self.assertEqual(len(gaps), 1)

    def test_misshapen_audio_gap_df(self):
        my_data = ([(1000, [10, 20, 30, 40]), (2000, [40, 30, 20, 10]), (4500, [5, 15, 25, 35])])
        result = gpu.fill_audio_gaps(my_data, self.sample_interval)
        filled_df = result.result_df
        gaps = result.gaps
        self.assertEqual(len(filled_df["timestamps"]), 18)
        self.assertEqual(len(gaps), 1)

    def test_tiny_audio_gap_df(self):
        my_data = ([(1000, [10, 20, 30, 40]), (2000, [40, 30, 20, 10]), (3005, [5, 15, 25, 35])])
        result = gpu.fill_audio_gaps(my_data, self.sample_interval)
        filled_df = result.result_df
        gaps = result.gaps
        self.assertEqual(len(filled_df["timestamps"]), 12)
        self.assertEqual(len(gaps), 0)

    def test_undersized_audio_gap_df(self):
        my_data = ([(1000, [10, 20, 30, 40]), (2000, [40, 30, 20, 10]), (3100, [5, 15, 25, 35])])
        result = gpu.fill_audio_gaps(my_data, self.sample_interval)
        filled_df = result.result_df
        gaps = result.gaps
        self.assertEqual(len(filled_df["timestamps"]), 13)
        self.assertEqual(len(gaps), 1)

    def test_failure_audio_gap_df(self):
        my_data = ([(1000, [10, 20, 30, 40]), (1500, [40, 30, 20, 10])])
        result = gpu.fill_audio_gaps(my_data, self.sample_interval)
        error = result.errors.get()
        self.assertEqual(len(error), 1)
