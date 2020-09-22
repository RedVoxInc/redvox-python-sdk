"""
This module creates specific time-bounded segments of data for users
"""
import pandas as pd
import numpy as np
from typing import Optional, Set
from dataclasses import dataclass
from redvox.common import date_time_utils as dtu
from datetime import datetime
from redvox.common.sensor_data import SensorType, SensorData
from redvox.common.load_sensor_data import ReadResult, read_all_in_dir


@dataclass
class DataWindow:
    """
    Holds the data for a given time window
    """
    input_directory: str
    station_ids: Optional[Set[str]] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    start_padding_s: float = 120
    end_padding_s: float = 120
    gap_time_s: float = 5
    apply_correction: bool = False
    structured_layout: bool = False
    stations: Optional[ReadResult] = None

    def __post_init__(self):
        self.read_data_window()

    def _pad_start_datetime_s(self) -> float:
        """
        apply padding to the start datetime
        :return: padded start datetime as seconds since epoch UTC
        """
        return dtu.datetime_to_epoch_seconds_utc(self.start_datetime) - self.start_padding_s

    def _pad_end_datetime_s(self) -> float:
        """
        apply padding to the end datetime
        :return: padded end datetime as seconds since epoch UTC
        """
        return dtu.datetime_to_epoch_seconds_utc(self.end_datetime) + self.end_padding_s

    def correct_timestamps(self):
        """
        update the timestamps in all stations
        """
        for station in self.stations.station_id_uuid_to_stations.values():
            if self.apply_correction:
                station.update_timestamps()

    def gap_filler(self, data_df: pd.DataFrame, expected_start: float, expected_end: float,
                   sample_rate_hz: float, gap_duration_s: float = 5.0) -> pd.DataFrame:
        """
        fills in the dataframe
        :param data_df: dataframe with timestamps as column "timestamps"
        :param expected_start: timestamp data is supposed to start at
        :param expected_end: timestamp data is supposed to end at
        :param sample_rate_hz: sample rate of data in hz
        :param gap_duration_s: duration in seconds of minimum missing data to be considered a gap
        :return: dataframe without gaps
        """
        time_stamps = data_df.sort_values("timestamps")["timestamps"].to_numpy()
        data_duration = dtu.microseconds_to_seconds(time_stamps[-1] - time_stamps[0])
        tolerance = gap_duration_s * sample_rate_hz
        num_points = len(time_stamps)
        expected_num_points = sample_rate_hz * dtu.microseconds_to_seconds(time_stamps[-1] - time_stamps[0])
        one_sample_s = 1 / sample_rate_hz
        result_df = data_df.copy()
        if num_points < expected_num_points - tolerance:
            if data_duration < gap_duration_s or num_points < sample_rate_hz / 2:
                for index in range(0, num_points - 1):
                    time_diff = dtu.microseconds_to_seconds(time_stamps[index + 1] - time_stamps[index])
                    if time_diff > one_sample_s:
                        # calc samples to add:
                        num_new_samples = int(time_diff * sample_rate_hz) - 2
                        new_timestamps = np.vectorize(lambda t: time_stamps[index] +
                                                      dtu.seconds_to_microseconds(t * one_sample_s)
                                                      )(list(range(1, num_new_samples-1)))
                        empty_df = pd.DataFrame([], columns=data_df.columns)
                        empty_df["timestamps"] = new_timestamps
                        for column_index in data_df.columns:
                            if column_index != "timestamps":
                                empty_df[column_index] = np.nan
                        result_df = result_df.append(empty_df, ignore_index=True)
            else:
                half_samples = int(num_points / 2)
                first_data_df = data_df.iloc[0:half_samples].copy().reset_index(drop=True)
                second_data_df = data_df.iloc[half_samples:-1].copy().reset_index(drop=True)
                first_data_df = self.gap_filler(first_data_df, expected_start, expected_end,
                                                sample_rate_hz, gap_duration_s)
                second_data_df = self.gap_filler(second_data_df, expected_start, expected_end,
                                                 sample_rate_hz, gap_duration_s)
                result_df = first_data_df.append(second_data_df, ignore_index=True)
        return result_df.sort_values("timestamps")

    def fill_sensor_gap(self, sensor: SensorData):
        """
        fill gaps in the sensor
        :param sensor: a sensor with timestamps and data
        """
        if sensor.is_sample_rate_fixed:
            sensor.data_df = self.gap_filler(sensor.data_df, sensor.first_data_timestamp(),
                                             sensor.last_data_timestamp(), sensor.sample_rate, self.gap_time_s)

    def read_data_window(self):
        """
        read data using the properties of the class
        """
        # read in data from files/buffer/whatever
        # correct data using w/e
        # push data into data_window object
        #   use Station as data storage, id as key
        #   sort the data by timestamp as it's pushed in
        #   store the start timestamps of chunks/packets as they enter
        # truncate
        # gap fill
        #   use start timestamps of chunks/packets and the timestamp before each one to id gaps
        #   checking every data point is exhausting, but O(n)
        self.stations = read_all_in_dir(self.input_directory, int(self._pad_start_datetime_s()),
                                        int(self._pad_end_datetime_s()), self.station_ids,
                                        self.structured_layout)

        # check if ids in station data from files
        for ids in self.station_ids:
            if not self.stations.check_for_id(ids):
                # error handling
                print(f"WARNING: {ids} doesn't have any data to read")

        # fill in gaps and truncate
        for station_id, station in self.stations.station_id_uuid_to_stations.items():
            # apply time correction
            if self.apply_correction:
                station.update_timestamps()
            # prepare a bunch of information to be used later
            # compute the length in seconds of one sample
            one_sample_s = 1 / station.station_data[SensorType.AUDIO].sample_rate
            # get the start and end timestamps + 1 sample to be safe
            start_timestamp = int(dtu.seconds_to_microseconds(dtu.datetime_to_epoch_seconds_utc(self.start_datetime) - one_sample_s))
            end_timestamp = int(dtu.seconds_to_microseconds(dtu.datetime_to_epoch_seconds_utc(self.end_datetime) + one_sample_s))
            # TRUNCATE!  get only the timestamps between the start and end timestamps
            for sensor_types in station.station_data.keys():
                # get the timestamps of the data
                df_timestamps = station.station_data[sensor_types].data_timestamps()
                temp = np.where(
                    (start_timestamp < df_timestamps) & (df_timestamps < end_timestamp))[0]
                new_df = station.station_data[sensor_types].data_df.iloc[temp].reset_index(drop=True)
                station.station_data[sensor_types].data_df = new_df
            if len(station.station_data[SensorType.AUDIO].data_df.values) < 1:
                print(f"WARNING: {station.station_metadata.station_id} audio sensor has been truncated and "
                      f"no valid data remains!")
            else:
                # GAP FILL
                self.fill_sensor_gap(station.station_data[SensorType.AUDIO])
                # FRONT/END GAP FILL!  calculate the audio samples missing based on inputs
                first_timestamp = station.station_data[SensorType.AUDIO].first_data_timestamp()
                last_timestamp = station.station_data[SensorType.AUDIO].last_data_timestamp()
                start_diff = first_timestamp - dtu.seconds_to_microseconds(
                    dtu.datetime_to_epoch_seconds_utc(self.start_datetime))
                last_diff = dtu.seconds_to_microseconds(dtu.datetime_to_epoch_seconds_utc(self.end_datetime)) \
                    - last_timestamp
                if start_diff > dtu.seconds_to_microseconds(one_sample_s):
                    num_missing_samples = int(dtu.microseconds_to_seconds(start_diff) *
                                              station.station_data[SensorType.AUDIO].sample_rate)
                    time_before = np.vectorize(
                        lambda t: first_timestamp - dtu.seconds_to_microseconds(t * one_sample_s))(
                        list(range(1, num_missing_samples)))
                    time_before = time_before[::-1]
                    empty_df = pd.DataFrame([], columns=["timestamps", "microphone"])
                    empty_df["timestamps"] = time_before
                    empty_df["microphone"] = np.nan
                    station.audio_sensor().append_data(empty_df)
                if last_diff > dtu.seconds_to_microseconds(one_sample_s):
                    num_missing_samples = int(dtu.microseconds_to_seconds(last_diff) *
                                              station.station_data[SensorType.AUDIO].sample_rate)
                    time_after = np.vectorize(
                        lambda t: last_timestamp + dtu.seconds_to_microseconds(t * one_sample_s))(
                        list(range(1, num_missing_samples)))
                    empty_df = pd.DataFrame([], columns=["timestamps", "microphone"])
                    empty_df["timestamps"] = time_after
                    empty_df["microphone"] = np.nan
                    station.audio_sensor().append_data(empty_df)
                # ALL DONE!  set the dataframe to the updated dataframe
                station.station_data[SensorType.AUDIO].data_df.sort_values("timestamps", inplace=True)
