"""
tests for data window objects
"""
import unittest
import pandas as pd
import redvox.tests as tests
import numpy as np
import redvox.common.date_time_utils as dt
from redvox.common import data_window as dw


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
        self.assertTrue(test_station.has_audio_data())
        self.assertEqual(test_station.audio_sensor().num_samples(), 720000)
        test_station = self.datawindow.stations.get_station("1637650010")
        self.assertTrue(test_station.has_audio_sensor())
        self.assertTrue(test_station.has_accelerometer_sensor())
        self.assertTrue(test_station.has_magnetometer_sensor())
        self.assertTrue(test_station.has_barometer_sensor())
        self.assertTrue(test_station.has_location_sensor())


class GapFillerTest(unittest.TestCase):
    def setUp(self):
        timestamps = [dt.seconds_to_microseconds(10), dt.seconds_to_microseconds(30), dt.seconds_to_microseconds(100)]
        self.dataframe = pd.DataFrame(np.transpose([timestamps, [1, 3, 10]]), columns=["timestamps", "temp"])

    def test_gap_filler(self):
        filled_dataframe = dw.gap_filler(self.dataframe, 10)
        self.assertEqual(filled_dataframe.shape, (10, 2))


# class OtherTest(unittest.TestCase):
#     def test_mytest(self):
#         from datetime import datetime, timedelta
#         input_dir = "/Users/tyler/Documents/api900"
#         station_ids = {"1637620003", "1637610015", "1637610013"}
#         # please note that InputSettings is a temporary stand-in for a config file
#         settings = [2020, 7, 11, 22, 15, 30, 300]
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
#                                    end_datetime=end_timestamp_s,
#                                    structured_layout=True)
#         new_datawindow = datawindow.create_window()
#         for station in new_datawindow.stations.get_all_stations():
#             print(f"station id: {station.station_metadata.station_id}")
#             for sensor_type, sensor_data in station.station_data.items():
#                 print(f"sensor type: {sensor_type.name}\n"
#                       f"the data timestamps:\n{sensor_data.data_timestamps()}\n"
#                       f"the first data timestamp: {sensor_data.first_data_timestamp()}\n"
#                       f"the last data timestamp: {sensor_data.last_data_timestamp()}\n"
#                       f""f"the sample interval: {sensor_data.sample_interval_s}\n"
#                       f"the calculated sample interval: "
#                       f"{dt.microseconds_to_seconds(np.mean(np.diff(sensor_data.data_timestamps())))}\n"
#                       f"calculated is wrong because technically we have fewer samples than what is listed below\n"
#                       f"the number of data samples: {sensor_data.num_samples()}\n")
#             print(f"station_id: {station.station_metadata.station_id}")
#             if station.has_audio_data():
#                 print(f"mic sample interval: {station.audio_sensor().sample_interval_s}\n"
#                       f"the number of data samples: {station.audio_sensor().num_samples()}\n")
#                 for packet in station.packet_data:
#                     if not np.isnan(packet.sample_interval_to_next_packet):
#                         print(f"packet sample interval to next packet: "
#                               f"{dt.microseconds_to_seconds(packet.sample_interval_to_next_packet)}")
#                 print(f"AUDIO DATA:\n----------------------------\n"
#                       f"mic sample rate in hz: {station.audio_sensor().sample_rate}\n"
#                       f"mic sample interval in seconds: {station.audio_sensor().sample_interval_s}\n"
#                       f"is mic sample rate constant: {station.audio_sensor().is_sample_rate_fixed}\n"
#                       f"the data timestamps: {station.audio_sensor().data_timestamps()}\n"
#                       f"the first data timestamp: {station.audio_sensor().first_data_timestamp()}\n"
#                       f"the last data timestamp: {station.audio_sensor().last_data_timestamp()}\n"
#                       f"the number of data samples: {station.audio_sensor().num_samples()}\n"
#                       f"the duration of the data in seconds: {station.audio_sensor().data_duration_s()}\n"
#                       f"the names of the dataframe columns: {station.audio_sensor().data_fields()}\n")
#             if station.has_barometer_data():
#                 print(f"BAROMETER DATA:\n----------------------------\n"
#                       f"barometer sample rate: {station.barometer_sensor().sample_rate}\n"
#                       f"barometer mean sample interval: {station.barometer_sensor().sample_interval_s}\n"
#                       f"is barometer sample rate constant: {station.barometer_sensor().is_sample_rate_fixed}\n"
#                       f"the data timestamps: {station.barometer_sensor().data_timestamps()}\n"
#                       f"the first data timestamp: {station.barometer_sensor().first_data_timestamp()}\n"
#                       f"the last data timestamp: {station.barometer_sensor().last_data_timestamp()}\n"
#                       f"the number of data samples: {station.barometer_sensor().num_samples()}\n"
#                       f"the duration of the data in seconds: {station.barometer_sensor().data_duration_s()}\n"
#                       f"the names of the dataframe columns: {station.barometer_sensor().data_fields()}\n"
#                       f"the barometer channel data values: {station.barometer_sensor().get_channel('barometer')}\n"
#                       f"the valid barometer channel data values: "
#                       f"{station.barometer_sensor().get_valid_channel_values('barometer')}\n")
#             if station.has_location_data():
#                 print(f"LOCATION DATA:\n----------------------------\n"
#                       f"location sample rate: {station.location_sensor().sample_rate}\n"
#                       f"location mean sample interval: {station.location_sensor().sample_interval_s}\n"
#                       f"is location sample rate constant: {station.location_sensor().is_sample_rate_fixed}\n"
#                       f"the data: \n{station.location_sensor().data_df}\n"
#                       f"the first data timestamp: {station.location_sensor().first_data_timestamp()}\n"
#                       f"the last data timestamp: {station.location_sensor().last_data_timestamp()}\n"
#                       f"the number of data samples: {station.location_sensor().num_samples()}\n"
#                       f"the duration of the data in seconds: {station.location_sensor().data_duration_s()}\n"
#                       f"the names of the dataframe columns: {station.location_sensor().data_fields()}\n")
#             if station.has_accelerometer_sensor():
#                 print(f"ACCELEROMETER DATA:\n----------------------------\n"
#                       f"accelerometer sample rate: {station.accelerometer_sensor().sample_rate}\n"
#                       f"is accelerometer sample rate constant:"
#                       f"{station.accelerometer_sensor().is_sample_rate_fixed}\n"
#                       f"the data as an ndarray: \n{station.accelerometer_sensor().samples()}\n"
#                       f"the data timestamps: {station.accelerometer_sensor().data_timestamps()}\n"
#                       f"the first data timestamp: {station.accelerometer_sensor().first_data_timestamp()}\n"
#                       f"the last data timestamp: {station.accelerometer_sensor().last_data_timestamp()}\n"
#                       f"the number of data samples: {station.accelerometer_sensor().num_samples()}\n"
#                       f"the duration of the data in seconds: {station.accelerometer_sensor().data_duration_s()}\n"
#                       f"the names of the dataframe columns: {station.accelerometer_sensor().data_fields()}\n")
#             print("\n-------------\n")
