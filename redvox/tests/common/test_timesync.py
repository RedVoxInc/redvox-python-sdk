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

    def test_validate_sensors(self):
        test_ts = ts.TimeSyncData()
        test_ts.station_id = "test"
        test_ts.sample_rate_hz = 80.0
        test_ts.station_start_timestamp = 1
        other_ts = ts.TimeSyncData()
        other_ts.station_id = "test"
        other_ts.sample_rate_hz = 80.0
        tsa_test = ts.TimeSyncAnalysis("test", [test_ts, other_ts])
        self.assertFalse(ts.validate_sensors(tsa_test))
