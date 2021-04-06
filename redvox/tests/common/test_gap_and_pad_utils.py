import unittest

import numpy as np
import pandas as pd

import redvox.common.date_time_utils as dt
import redvox.common.gap_and_pad_utils as gpu


class PadDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        timestamps = [
            dt.seconds_to_microseconds(40),
            dt.seconds_to_microseconds(50),
            dt.seconds_to_microseconds(60),
        ]
        cls.dataframe = pd.DataFrame(
            np.transpose([timestamps, [4, 5, 6]]), columns=["timestamps", "temp"]
        )
        cls.singleton = pd.DataFrame(
            [[timestamps[0], 1]], columns=["timestamps", "temp"]
        )

    def test_pad_data(self):
        filled_dataframe = gpu.pad_data(
            dt.seconds_to_microseconds(10),
            dt.seconds_to_microseconds(100),
            self.dataframe,
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
            self.singleton,
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
            self.dataframe,
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


class FillGapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        timestamps = [
            dt.seconds_to_microseconds(10),
            dt.seconds_to_microseconds(30),
            dt.seconds_to_microseconds(100),
        ]
        cls.dataframe = pd.DataFrame(
            np.transpose([timestamps, [1, 3, 10]]), columns=["timestamps", "temp"]
        )
        cls.singleton = pd.DataFrame(
            [[timestamps[0], 1]], columns=["timestamps", "temp"]
        )

    def test_singleton_fill_gaps(self):
        filled_singleton = gpu.fill_gaps(
            self.singleton,
            dt.seconds_to_microseconds(10),
            dt.seconds_to_microseconds(10)
        )
        self.assertEqual(filled_singleton.shape, (1, 2))
        self.assertEqual(
            filled_singleton.loc[0, "timestamps"], dt.seconds_to_microseconds(10)
        )

    def test_fill_gaps(self):
        filled_dataframe = gpu.fill_gaps(
            self.dataframe,
            dt.seconds_to_microseconds(10),
            dt.seconds_to_microseconds(10)
        )
        self.assertEqual(filled_dataframe.shape, (10, 2))
        self.assertEqual(
            filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(20)
        )
        self.assertEqual(
            filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(30)
        )

    def test_fill_gaps_long_interval(self):
        filled_dataframe = gpu.fill_gaps(
            self.dataframe,
            dt.seconds_to_microseconds(20),
            dt.seconds_to_microseconds(10),
        )
        self.assertEqual(filled_dataframe.shape, (6, 2))
        self.assertEqual(
            filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(30)
        )
        self.assertEqual(
            filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(50)
        )

    def test_fill_gaps_long_gap(self):
        filled_dataframe = gpu.fill_gaps(
            self.dataframe,
            dt.seconds_to_microseconds(10),
            dt.seconds_to_microseconds(20),
        )
        self.assertEqual(filled_dataframe.shape, (9, 2))
        self.assertEqual(
            filled_dataframe.loc[1, "timestamps"], dt.seconds_to_microseconds(30)
        )
        self.assertEqual(
            filled_dataframe.loc[2, "timestamps"], dt.seconds_to_microseconds(40)
        )


class CreateDatalessTimestampsDFTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base_df = pd.DataFrame([], columns=["timestamps", "data"])

    def test_create_dataless_timestamps_df(self):
        new_df = gpu.create_dataless_timestamps_df(2000, 1000, self.base_df.columns, 7, False)
        self.assertEqual(new_df.loc[0, "timestamps"], 3000)
        self.assertEqual(new_df.loc[6, "timestamps"], 9000)
        new_df = gpu.create_dataless_timestamps_df(8000, 1000, self.base_df.columns, 7, True)
        self.assertEqual(new_df.loc[0, "timestamps"], 7000)
        self.assertEqual(new_df.loc[6, "timestamps"], 1000)

    def test_add_dataless_timestamps_df_empty(self):
        # dataframe to alter is empty, so nothing changes
        new_base_df = self.base_df.copy()
        new_df = gpu.add_dataless_timestamps_to_df(new_base_df, 0, 1000, 7, False)
        self.assertEqual(len(new_df), 0)

    def test_add_dataless_timestamps_df(self):
        new_df = gpu.create_dataless_timestamps_df(8000, 1000, self.base_df.columns, 7, True)
        new_df = gpu.add_dataless_timestamps_to_df(new_df, 6, 1000, 7, False)
        self.assertEqual(new_df.loc[7, "timestamps"], 2000)
        self.assertEqual(new_df.loc[13, "timestamps"], 8000)
        new_df = gpu.add_dataless_timestamps_to_df(new_df, 0, 1000, 7, True)
        self.assertEqual(new_df.loc[14, "timestamps"], 6000)
        self.assertEqual(new_df.loc[20, "timestamps"], 0)

    def test_add_dataless_timestamps_df_index_too_high(self):
        # no change to dataframe if index is too high
        new_df = gpu.create_dataless_timestamps_df(8000, 1000, self.base_df.columns, 7, True)
        new_df = gpu.add_dataless_timestamps_to_df(new_df, 99, 1000, 7, True)
        self.assertEqual(len(new_df), 7)
        self.assertEqual(new_df.loc[0, "timestamps"], 7000)
        self.assertEqual(new_df.loc[6, "timestamps"], 1000)

    def test_add_dataless_timestamps_df_not_enough_samples(self):
        # no change to dataframe if adding less than 1 samples
        new_df = gpu.create_dataless_timestamps_df(8000, 1000, self.base_df.columns, 7, True)
        new_df = gpu.add_dataless_timestamps_to_df(new_df, 0, 1000, -10, True)
        self.assertEqual(len(new_df), 7)
        self.assertEqual(new_df.loc[0, "timestamps"], 7000)
        self.assertEqual(new_df.loc[6, "timestamps"], 1000)
        new_df = gpu.add_dataless_timestamps_to_df(new_df, 0, 1000, 0, True)
        self.assertEqual(len(new_df), 7)
        self.assertEqual(new_df.loc[0, "timestamps"], 7000)
        self.assertEqual(new_df.loc[6, "timestamps"], 1000)
