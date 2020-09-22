"""
tests for data window objects
"""
import os
import unittest
import pandas as pd
import redvox.tests as tests
import numpy as np
from datetime import timedelta
import redvox.common.date_time_utils as dt
from typing import List
from redvox.common import data_window as dw
from dataclasses import dataclass


# this is a stand-in for a config file
@dataclass
class InputSettings:
    start_year: int
    start_month: int
    start_day: int
    start_hour: int
    start_minute: int
    start_second: int
    duration_seconds: int
    comment: str = "I am the settings comment"


class DataWindowTest(unittest.TestCase):
    def setUp(self):
        self.data_windows = []
        input_dir = os.path.join("/Users/tyler/IdeaProjects/redvox-projects/tyler/test_read_data")
        station_ids = {"1637610011", "1637610015"}
        all_settings: List[InputSettings] = [InputSettings(2020, 7, 11, 19, 57, 30, 60, "missing end"),
                                             InputSettings(2020, 7, 11, 19, 55, 30, 60, "missing beginning")]
            # InputSettings(2020, 7, 11, 19, 57, 30, 1, "1 second length"),
            #                                  InputSettings(2020, 7, 11, 19, 55, 30, 60, "missing beginning"),
            #                                  InputSettings(2020, 7, 11, 19, 56, 25, 60, "gap in middle"),
            #                                  InputSettings(2020, 7, 11, 19, 57, 30, 60, "missing end"),
            #                                  InputSettings(2020, 7, 11, 19, 57, 40, 60, "start beyond data available")]

        padding_duration_s = 120
        gap_time_s = 5
        apply_correction = False
        structured_layout = False
        for settings in all_settings:
            start_timestamp_s = dt.datetime_from(settings.start_year,
                                                 settings.start_month,
                                                 settings.start_day,
                                                 settings.start_hour,
                                                 settings.start_minute,
                                                 settings.start_second)

            end_timestamp_s = start_timestamp_s + timedelta(seconds=settings.duration_seconds)

            datawindow = dw.DataWindow(input_directory=input_dir,
                                       station_ids=station_ids,
                                       start_datetime=start_timestamp_s,
                                       end_datetime=end_timestamp_s,
                                       start_padding_s=padding_duration_s,
                                       end_padding_s=padding_duration_s,
                                       gap_time_s=gap_time_s,
                                       apply_correction=apply_correction,
                                       structured_layout=structured_layout)
            datawindow.read_data_window()
            self.data_windows.append(datawindow)

    def test_something(self):
        for windows in self.data_windows:
            test_station = windows.stations.get_station("1637610011")
            if test_station.has_audio_data():
                print(f"station_id: {test_station.station_metadata.station_id}\n"
                      f"mic sample rate: {test_station.audio_sensor().sample_rate}\n"
                      f"is mic sample rate constant: {test_station.audio_sensor().is_sample_rate_fixed}\n"
                      f"the data as an ndarray: {test_station.audio_sensor().samples()}\n"
                      f"the data timestamps: {test_station.audio_sensor().data_timestamps()}\n"
                      f"the first data timestamp: {test_station.audio_sensor().first_data_timestamp()}\n"
                      f"the last data timestamp: {test_station.audio_sensor().last_data_timestamp()}\n"
                      f"the number of data samples: {test_station.audio_sensor().num_samples()}\n"
                      f"the duration of the data in seconds: {test_station.audio_sensor().data_duration_s()}\n"
                      f"the names of the dataframe columns: {test_station.audio_sensor().data_fields()}")
                print("Plot the mic data!")
                print(test_station.audio_sensor().get_channel("microphone"))
            print("\n-------------\n")


if __name__ == '__main__':
    unittest.main()
