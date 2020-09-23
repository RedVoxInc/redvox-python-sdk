"""
This module creates specific time-bounded segments of data for users
"""
import pandas as pd
import numpy as np
from typing import Optional, Set
from dataclasses import dataclass
from redvox.common import date_time_utils as dtu
from datetime import datetime
from redvox.common.sensor_data import SensorData
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
    gap_time_s: float = .5
    apply_correction: bool = False
    structured_layout: bool = False
    stations: Optional[ReadResult] = None

    def __post_init__(self):
        self.read_data_window()

    def _has_time_window(self) -> bool:
        """
        Returns true if there is a start or end datetime in the settings
        :return: True if start_datetime or end_datetime exists
        """
        return self.start_datetime is not None or self.end_datetime is not None

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

    def data_padder(self, data_df: pd.DataFrame, sample_rate_hz: float) -> pd.DataFrame:
        """
        Pad the start and end of the dataframe with np.nan
        :param data_df: dataframe with timestamps as column "timestamps"
        :param sample_rate_hz: constant sample rate of data in hz
        :return: dataframe padded with np.nans in front and back to meet full size of expected start and end
        """
        # extract the necessary information to pad the data
        data_time_stamps = data_df.sort_values("timestamps")["timestamps"].to_numpy()
        first_data_timestamp = data_time_stamps[0]
        last_data_timestamp = data_time_stamps[-1]
        expected_start = dtu.datetime_to_epoch_microseconds_utc(self.start_datetime)
        expected_end = dtu.datetime_to_epoch_microseconds_utc(self.end_datetime)
        result_df = data_df.copy()
        # FRONT/END GAP FILL!  calculate the audio samples missing based on inputs
        if expected_start < first_data_timestamp:
            start_diff = first_data_timestamp - expected_start
            num_missing_samples = int(dtu.microseconds_to_seconds(start_diff) * sample_rate_hz)
            # add the gap data to the result dataframe
            result_df = result_df.append(create_empty_df(first_data_timestamp, sample_rate_hz, data_df.columns,
                                                         num_missing_samples, True), ignore_index=True)
        if expected_end > last_data_timestamp:
            last_diff = expected_end - last_data_timestamp
            num_missing_samples = int(dtu.microseconds_to_seconds(last_diff) * sample_rate_hz)
            # add the gap data to the result dataframe
            result_df = result_df.append(create_empty_df(last_data_timestamp, sample_rate_hz, data_df.columns,
                                                         num_missing_samples), ignore_index=True)
        return result_df.sort_values("timestamps")

    def fill_sensor_gap(self, sensor: SensorData):
        """
        fill gaps in the sensor
        :param sensor: a sensor with timestamps and data
        """
        if sensor.is_sample_rate_fixed:
            sensor.data_df = gap_filler(sensor.data_df, sensor.sample_rate, self.gap_time_s)

    def pad_sensor_data(self, sensor: SensorData):
        """
        pads the front and back of sensor data
        :param sensor: a sensor with timestamps and data
        """
        if sensor.is_sample_rate_fixed:
            sensor.data_df = self.data_padder(sensor.data_df, sensor.sample_rate)

    def read_data_window(self):
        """
        read data using the properties of the class
        """
        start_time = None
        end_time = None
        if self.start_datetime:
            start_time = int(self._pad_start_datetime_s())
        if self.end_datetime:
            end_time = int(self._pad_end_datetime_s())
        self.stations = read_all_in_dir(self.input_directory, start_time, end_time,
                                        self.station_ids, self.structured_layout)

        # check if ids in station data from files
        for ids in self.station_ids:
            if not self.stations.check_for_id(ids):
                # error handling
                print(f"WARNING: {ids} doesn't have any data to read")

        if self._has_time_window():
            # fill in gaps and truncate
            for station_id, station in self.stations.station_id_uuid_to_stations.items():
                # apply time correction
                if self.apply_correction:
                    station.update_timestamps()
                # prepare a bunch of information to be used later
                if station.has_audio_sensor():
                    # compute the length in seconds of one sample
                    one_sample_s = 1 / station.audio_sensor().sample_rate
                else:
                    # print warning and use 0 as the size of one sample
                    print(f"WARNING: {station.station_metadata.station_id} audio sensor does not exist!")
                    one_sample_s = 0
                # get the start and end timestamps + 1 sample to be safe
                if self.start_datetime:
                    start_timestamp = int(dtu.seconds_to_microseconds(
                        dtu.datetime_to_epoch_seconds_utc(self.start_datetime) - one_sample_s))
                else:
                    start_timestamp = station.audio_sensor().first_data_timestamp()
                if self.end_datetime:
                    end_timestamp = int(dtu.seconds_to_microseconds(
                        dtu.datetime_to_epoch_seconds_utc(self.end_datetime) + one_sample_s))
                else:
                    end_timestamp = station.audio_sensor().last_data_timestamp()
                # TRUNCATE!  get only the timestamps between the start and end timestamps
                for sensor_types in station.station_data.keys():
                    # get the timestamps of the data
                    df_timestamps = station.station_data[sensor_types].data_timestamps()
                    temp = np.where(
                        (start_timestamp < df_timestamps) & (df_timestamps < end_timestamp))[0]
                    new_df = station.station_data[sensor_types].data_df.iloc[temp].reset_index(drop=True)
                    station.station_data[sensor_types].data_df = new_df
                    # oops, all the samples have been cut off
                    if station.station_data[sensor_types].num_samples() < 1:
                        print(f"WARNING: {station.station_metadata.station_id} {sensor_types} sensor "
                              f"has been truncated and no valid data remains!")
                if station.has_audio_data():
                    # GAP FILL
                    self.fill_sensor_gap(station.audio_sensor())
                    # PAD DATA
                    self.pad_sensor_data(station.audio_sensor())


def gap_filler(data_df: pd.DataFrame, sample_rate_hz: float, gap_duration_s: float = 5.0) -> pd.DataFrame:
    """
    fills gaps in the dataframe with np.nan by interpolating timestamps
    :param data_df: dataframe with timestamps as column "timestamps"
    :param sample_rate_hz: constant sample rate of data in hz
    :param gap_duration_s: duration in seconds of minimum missing data to be considered a gap
    :return: dataframe without gaps
    """
    # extract the necessary information to compute gap size and gap timestamps
    data_time_stamps = data_df.sort_values("timestamps")["timestamps"].to_numpy()
    first_data_timestamp = data_time_stamps[0]
    last_data_timestamp = data_time_stamps[-1]
    data_duration_s = dtu.microseconds_to_seconds(last_data_timestamp - first_data_timestamp)
    tolerance = gap_duration_s * sample_rate_hz
    num_points = len(data_time_stamps)
    expected_num_points = sample_rate_hz * data_duration_s  # expected number of points for the data
    one_sample_s = 1 / sample_rate_hz
    result_df = data_df.copy()
    # if there are less points than our expected amount - tolerance points, we have gaps to fill
    if num_points < expected_num_points - tolerance:
        # if the data we're looking at is short enough, we can start comparing points
        if data_duration_s < gap_duration_s or num_points < sample_rate_hz / 2:
            # look at every timestamp except the last one
            for index in range(0, num_points - 1):
                # compare that timestamp to the next
                time_diff = dtu.microseconds_to_seconds(data_time_stamps[index + 1] - data_time_stamps[index])
                # anything bigger than one sample needs to be filled
                if time_diff > one_sample_s:
                    # calc samples to add, subtracting 1 to prevent copying existing data
                    num_new_samples = int(time_diff * sample_rate_hz) - 1
                    # add the gap data to the result dataframe
                    result_df = result_df.append(create_empty_df(first_data_timestamp, sample_rate_hz,
                                                                 data_df.columns, num_new_samples), ignore_index=True)
        else:
            # gap's too big, divide and conquer using recursion!
            half_samples = int(num_points / 2)
            first_data_df = data_df.iloc[:half_samples].copy().reset_index(drop=True)
            second_data_df = data_df.iloc[half_samples:].copy().reset_index(drop=True)
            # give half the samples and expected duration to each recursive call
            first_data_df = gap_filler(first_data_df, sample_rate_hz, gap_duration_s)
            second_data_df = gap_filler(second_data_df, sample_rate_hz, gap_duration_s)
            result_df = first_data_df.append(second_data_df, ignore_index=True)
    return result_df.sort_values("timestamps")


def create_empty_df(start_timestamp: float, sample_rate_hz: float, columns: pd.Index,
                    num_samples_to_add: int, add_to_start: bool = False) -> pd.DataFrame:
    """
    Creates an empty dataframe with num_samples_to_add - 1 timestamps, using columns as the columns
    The one timestamp not being added would be a copy of the start timestamp.
    :param start_timestamp: timestamp to start calculating other timestamps from
    :param sample_rate_hz: fixed sample rate of data in hz
    :param columns: the non-timestamp columns of the dataframe
    :param num_samples_to_add: the number of timestamps to create
    :param add_to_start: if True, invert the results, default False
    :return:
    """
    one_sample_s = 1 / sample_rate_hz
    if add_to_start:
        new_timestamps = np.vectorize(lambda t: start_timestamp - dtu.seconds_to_microseconds(t * one_sample_s))(
            list(range(1, num_samples_to_add)))
        new_timestamps = new_timestamps[::-1]
    else:
        new_timestamps = np.vectorize(lambda t: start_timestamp + dtu.seconds_to_microseconds(t * one_sample_s))(
            list(range(1, num_samples_to_add)))
    empty_df = pd.DataFrame([], columns=columns)
    # add the gap data to a temporary dataframe
    for column_index in columns:
        if column_index == "timestamps":
            empty_df["timestamps"] = new_timestamps
        else:
            empty_df[column_index] = np.nan
    # return a dataframe with only timestamps
    return empty_df
