"""
tests for timesync
"""
import os
import unittest
import numpy as np
import pandas as pd
import redvox.tests as tests
from redvox.common import sensor_data as sd, file_statistics as fs, date_time_utils as dtu, timesync as ts
from redvox.api900 import reader


class TimesyncTest(unittest.TestCase):
    def test_my_test(self):
        test_timesync = ts.TimeSyncData()
        self.assertEqual(test_timesync.sample_rate_hz, None)
