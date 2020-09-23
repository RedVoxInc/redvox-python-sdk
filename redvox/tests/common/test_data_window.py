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


class DataWindowTest(unittest.TestCase):
    def setUp(self):
        input_dir = tests.TEST_DATA_DIR
        self.datawindow = dw.DataWindow(input_directory=input_dir, station_ids={"1637650010", "0000000001"})

    def test_get_station(self):
        test_station = self.datawindow.stations.get_station("0000000001")
        self.assertTrue(test_station.has_audio_sensor())
        self.assertEqual(test_station.audio_sensor().num_samples(), 720000)

    def test_read_data_window(self):
        self.assertTrue(len(self.datawindow.stations.station_id_uuid_to_stations), 2)
        test_station = self.datawindow.stations.get_station("0000000001")
        self.assertTrue(test_station.has_audio_sensor())
        self.assertEqual(test_station.audio_sensor().num_samples(), 720000)
        test_station = self.datawindow.stations.get_station("1637650010")
        self.assertTrue(test_station.has_audio_sensor())
        self.assertTrue(test_station.has_accelerometer_sensor())
        self.assertTrue(test_station.has_magnetometer_sensor())
        self.assertTrue(test_station.has_barometer_sensor())
        self.assertTrue(test_station.has_location_sensor())


# class OtherTest(unittest.TestCase):
#     def test_mytest(self):
#         from datetime import datetime, timedelta
#         input_dir = "/Users/tyler/IdeaProjects/redvox-projects/tyler/test_read_data"
#         station_ids = {"1637610011", "1637610015"}
#         # please note that InputSettings is a temporary stand-in for a config file
#         settings = [2020, 7, 11, 19, 56, 25, 60]
#         start_timestamp_s: datetime = dt.datetime_from(settings[0],
#                                                        settings[1],
#                                                        settings[2],
#                                                        settings[3],
#                                                        settings[4],
#                                                        settings[5])
#
#         end_timestamp_s: datetime = start_timestamp_s + timedelta(seconds=settings[6])
#         datawindow = dw.DataWindow(input_directory=input_dir,
#                                    station_ids=station_ids,
#                                    start_datetime=start_timestamp_s,
#                                    end_datetime=end_timestamp_s)
#         for station in datawindow.stations.get_all_stations():
#             print(f"station_id: {station.station_metadata.station_id}")
#             if station.has_audio_data():
#                 print(f"AUDIO DATA:\n----------------------------\n"
#                       f"mic sample rate: {station.audio_sensor().sample_rate}\n"
#                       f"is mic sample rate constant: {station.audio_sensor().is_sample_rate_fixed}\n"
#                       f"the data as an ndarray: {station.audio_sensor().samples()}\n"
#                       f"the data timestamps: {station.audio_sensor().data_timestamps()}\n"
#                       f"the first data timestamp: {station.audio_sensor().first_data_timestamp()}\n"
#                       f"the last data timestamp: {station.audio_sensor().last_data_timestamp()}\n"
#                       f"the number of data samples: {station.audio_sensor().num_samples()}\n"
#                       f"the duration of the data in seconds: {station.audio_sensor().data_duration_s()}\n"
#                       f"the names of the dataframe columns: {station.audio_sensor().data_fields()}\n")
        #     if station.has_location_data():
        #         print(f"LOCATION DATA:\n----------------------------\n"
        #               f"location sample rate: {station.location_sensor().sample_rate}\n"
        #               f"is location sample rate constant: {station.location_sensor().is_sample_rate_fixed}\n"
        #               f"the data as an ndarray: {station.location_sensor().samples()}\n"
        #               f"the data timestamps: {station.location_sensor().data_timestamps()}\n"
        #               f"the first data timestamp: {station.location_sensor().first_data_timestamp()}\n"
        #               f"the last data timestamp: {station.location_sensor().last_data_timestamp()}\n"
        #               f"the number of data samples: {station.location_sensor().num_samples()}\n"
        #               f"the duration of the data in seconds: {station.location_sensor().data_duration_s()}\n"
        #               f"the names of the dataframe columns: {station.location_sensor().data_fields()}\n")
        #     if station.has_accelerometer_sensor():
        #         print(f"ACCELEROMETER DATA:\n----------------------------\n"
        #               f"accelerometer sample rate: {station.accelerometer_sensor().sample_rate}\n"
        #               f"is accelerometer sample rate constant: {station.accelerometer_sensor().is_sample_rate_fixed}\n"
        #               f"the data as an ndarray: {station.accelerometer_sensor().samples()}\n"
        #               f"the data timestamps: {station.accelerometer_sensor().data_timestamps()}\n"
        #               f"the first data timestamp: {station.accelerometer_sensor().first_data_timestamp()}\n"
        #               f"the last data timestamp: {station.accelerometer_sensor().last_data_timestamp()}\n"
        #               f"the number of data samples: {station.accelerometer_sensor().num_samples()}\n"
        #               f"the duration of the data in seconds: {station.accelerometer_sensor().data_duration_s()}\n"
        #               f"the names of the dataframe columns: {station.accelerometer_sensor().data_fields()}\n")
        #     print("\n-------------\n")


if __name__ == '__main__':
    unittest.main()
