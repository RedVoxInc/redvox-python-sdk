"""
This module creates specific time-bounded segments of data for users
"""
import pandas as pd
import numpy as np
from typing import Optional, Set
from dataclasses import dataclass
from redvox.common import date_time_utils as dtu
from redvox.common.sensor_data import SensorType
from redvox.common.load_sensor_data import ReadResult, read_all_in_dir


DEFAULT_GAP_TIME_S: float = 0.25
DEFAULT_START_PADDING_S: float = 120.
DEFAULT_END_PADDING_S: float = 120.


@dataclass
class DataWindow:
    """
    Holds the data for a given time window; adds interpolated timestamps to fill gaps and pad start and end values
    Properties:
        input_directory: string, directory that contains the files to read data from.  REQUIRED
        station_ids: optional set of strings, list of station ids to filter on.
                        If empty or None, get any ids found in the input directory.  Default None
        start_datetime: optional datetime, start datetime of the window.
                        If None, uses the first timestamp of the filtered data.  Default None
        end_datetime: optional datetime, end datetime of the window.
                        If None, uses the last timestamp of the filtered data.  Default None
        start_padding_s: float, the amount of seconds to include before the start_datetime
                            when filtering data.  Default DEFAULT_START_PADDING_S
        end_padding_s: float, the amount of seconds to include after the end_datetime
                        when filtering data.  Default DEFAULT_END_PADDING_S
        gap_time_s: float, the minimum amount of seconds between data points that would indicate a gap.
                    Default DEFAULT_GAP_TIME_S
        apply_correction: bool, if True, update the timestamps in the data based on best station offset.  Default False
        structured_layout: bool, if True, the input_directory contains specially named and organized
                            directories of data.  Default False
        stations: optional ReadResult, the results of reading the data from input_directory
    """
    input_directory: str
    station_ids: Optional[Set[str]] = None
    start_datetime: Optional[dtu.datetime] = None
    end_datetime: Optional[dtu.datetime] = None
    start_padding_s: float = DEFAULT_START_PADDING_S
    end_padding_s: float = DEFAULT_END_PADDING_S
    gap_time_s: float = DEFAULT_GAP_TIME_S
    apply_correction: bool = False
    structured_layout: bool = False
    stations: Optional[ReadResult] = None

    def __post_init__(self):
        """
        loads the data after initialization
        """
        if self.stations is None:
            self.read_data()

    def copy(self) -> 'DataWindow':
        """
        :return: a copy of the DataWindow
        """
        return DataWindow(self.input_directory, self.station_ids, self.start_datetime, self.end_datetime,
                          self.start_padding_s, self.end_padding_s, self.gap_time_s,
                          self.apply_correction, self.structured_layout, self.stations)

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

    def data_padder(self, data_df: pd.DataFrame, sample_interval_s: float) -> pd.DataFrame:
        """
        Pad the start and end of the dataframe with np.nan
        :param data_df: dataframe with timestamps as column "timestamps"
        :param sample_interval_s: constant sample interval in seconds
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
            num_missing_samples = int(dtu.microseconds_to_seconds(start_diff) / sample_interval_s) + 1
            # add the gap data to the result dataframe
            result_df = result_df.append(create_empty_df(expected_start -
                                                         dtu.seconds_to_microseconds(sample_interval_s),
                                                         sample_interval_s, data_df.columns,
                                                         num_missing_samples), ignore_index=True)
        if expected_end > last_data_timestamp:
            last_diff = expected_end - last_data_timestamp
            num_missing_samples = int(dtu.microseconds_to_seconds(last_diff) / sample_interval_s) + 1
            # add the gap data to the result dataframe
            result_df = result_df.append(create_empty_df(expected_end +
                                                         dtu.seconds_to_microseconds(sample_interval_s),
                                                         sample_interval_s, data_df.columns,
                                                         num_missing_samples, True), ignore_index=True)
        return result_df.sort_values("timestamps", ignore_index=True)

    def read_data(self):
        """
        read data using the properties of the class
        """
        start_time = int(self._pad_start_datetime_s()) if self.start_datetime else None
        end_time = int(self._pad_end_datetime_s()) if self.end_datetime else None
        self.stations = read_all_in_dir(self.input_directory, start_time, end_time,
                                        self.station_ids, self.structured_layout)

        ids_to_pop = []
        # check if ids in station data from files
        for ids in self.station_ids:
            if not self.stations.check_for_id(ids):
                # error handling
                print(f"WARNING: {ids} doesn't have any data to read")
            elif not self.stations.get_station(ids).has_audio_data():
                # no audio data is about the same as no data
                print(f"WARNING: {ids} doesn't have any audio data to read")
                ids_to_pop.append(ids)
        for ids in ids_to_pop:
            self.stations.pop_station(ids)
        # calculate time differences in audio samples
        for station in self.stations.get_all_stations():
            # apply time correction
            if self.apply_correction:
                station.update_timestamps()
            for packet in range(len(station.packet_data) - 1):
                data_start = station.packet_data[packet].data_start_timestamp
                data_num_samples = station.packet_data[packet].packet_num_audio_samples
                next_packet_start_index = \
                    station.audio_sensor().data_df.query("timestamps == @data_start").first_valid_index() + \
                    data_num_samples
                data_end = station.audio_sensor().data_timestamps()[next_packet_start_index - 1]
                next_packet_start = station.audio_sensor().data_timestamps()[next_packet_start_index]
                if next_packet_start - data_end < dtu.seconds_to_microseconds(self.gap_time_s):
                    station.packet_data[packet].sample_interval_to_next_packet = \
                        (next_packet_start - data_start) / data_num_samples

    def create_window(self) -> 'DataWindow':
        """
        constrain the data to the window specified by the parameters
        :return: only the data in the window specified by the parameters
        """
        if self._has_time_window():
            new_data_window = self.copy()
            ids_to_pop = []
            # fill in gaps and truncate
            for station_id, station in new_data_window.stations.station_id_uuid_to_stations.items():
                # prepare a bunch of information to be used later
                if new_data_window.start_datetime:
                    start_timestamp = dtu.seconds_to_microseconds(
                        dtu.datetime_to_epoch_seconds_utc(new_data_window.start_datetime))
                else:
                    start_timestamp = station.audio_sensor().first_data_timestamp()
                if new_data_window.end_datetime:
                    end_timestamp = dtu.seconds_to_microseconds(
                        dtu.datetime_to_epoch_seconds_utc(new_data_window.end_datetime))
                else:
                    end_timestamp = station.audio_sensor().last_data_timestamp()
                # truncate packets to include only the ones with the data for the window
                station.packet_data = [p for p in station.packet_data
                                       if p.data_end_timestamp > start_timestamp and
                                       p.data_start_timestamp < end_timestamp]
                for sensor_type, sensor in station.station_data.items():
                    # TRUNCATE!  get only the timestamps between the start and end timestamps
                    df_timestamps = sensor.data_timestamps()
                    if len(df_timestamps) < 1:
                        print(f"WARNING: Data window for {station.station_metadata.station_id} {sensor_type.name} "
                              f"sensor has no data points!")
                        if sensor_type == SensorType.AUDIO:
                            ids_to_pop.append(station.station_metadata.station_id)
                        break
                    temp = np.where(
                        (start_timestamp < df_timestamps) & (df_timestamps < end_timestamp))[0]
                    # oops, all the samples have been cut off
                    if len(temp) < 1:
                        print(f"WARNING: Data window for {station.station_metadata.station_id} {sensor_type.name} "
                              f"sensor has truncated all data points")
                        if sensor_type == SensorType.LOCATION:
                            # take the locations before the start_timestamp as valid locations
                            temp = np.where(df_timestamps < end_timestamp)[0]
                            if len(temp) < 1:
                                break
                            else:
                                print(f"Using all {sensor_type.name} data points before {end_timestamp} instead")
                        else:
                            if sensor_type == SensorType.AUDIO:
                                ids_to_pop.append(station.station_metadata.station_id)
                            break
                    sensor.data_df = sensor.data_df.iloc[temp].reset_index(drop=True)
                    if sensor.is_sample_interval_invalid():
                        print(f"WARNING: {sensor_type.name} has undefined sample interval and sample rate!")
                        break
                    # GAP FILL
                    sensor.data_df = gap_filler(sensor.data_df, sensor.sample_interval_s)
                    # PAD DATA
                    sensor.data_df = new_data_window.data_padder(sensor.data_df, sensor.sample_interval_s)
            # remove any station without audio sensor
            for ids in ids_to_pop:
                new_data_window.stations.pop_station(ids)
            return new_data_window
        else:
            return self


def gap_filler(data_df: pd.DataFrame, sample_interval_s: float,
               gap_duration_s: float = DEFAULT_GAP_TIME_S) -> pd.DataFrame:
    """
    fills gaps in the dataframe with np.nan by interpolating timestamps based on the mean expected sample interval
    :param data_df: dataframe with timestamps as column "timestamps"
    :param sample_interval_s: sample interval in seconds
    :param gap_duration_s: duration in seconds of minimum missing data to be considered a gap
    :return: dataframe without gaps
    """
    # extract the necessary information to compute gap size and gap timestamps
    data_time_stamps = data_df.sort_values("timestamps", ignore_index=True)["timestamps"].to_numpy()
    first_data_timestamp = data_time_stamps[0]
    last_data_timestamp = data_time_stamps[-1]
    data_duration_s = dtu.microseconds_to_seconds(last_data_timestamp - first_data_timestamp)
    num_points = len(data_time_stamps)
    # add one to calculation to include the last timestamp
    expected_num_points = int(data_duration_s / sample_interval_s) + 1
    # gap duration cannot be less than sample interval
    if gap_duration_s < sample_interval_s:
        gap_duration_s = sample_interval_s
    result_df = data_df.copy()
    # if there are less points than our expected amount, we have gaps to fill
    if num_points < expected_num_points:
        # if the data we're looking at is short enough, we can start comparing points
        if num_points < 1000:
            # look at every timestamp except the last one
            for index in range(0, num_points - 1):
                # compare that timestamp to the next
                time_diff = dtu.microseconds_to_seconds(data_time_stamps[index + 1] - data_time_stamps[index])
                # calc samples to add, subtracting 1 to prevent copying last timestamp
                num_new_samples = int(time_diff / sample_interval_s) - 1
                if time_diff > gap_duration_s and num_new_samples > 0:
                    # add the gap data to the result dataframe
                    result_df = result_df.append(create_empty_df(data_time_stamps[index], sample_interval_s,
                                                                 data_df.columns, num_new_samples), ignore_index=True)
        else:
            # too many points to check, divide and conquer using recursion!
            half_samples = int(num_points / 2)
            first_data_df = data_df.iloc[:half_samples].copy().reset_index(drop=True)
            second_data_df = data_df.iloc[half_samples:].copy().reset_index(drop=True)
            # give half the samples to each recursive call
            first_data_df = gap_filler(first_data_df, sample_interval_s, gap_duration_s)
            second_data_df = gap_filler(second_data_df, sample_interval_s, gap_duration_s)
            result_df = first_data_df.append(second_data_df, ignore_index=True)
    return result_df.sort_values("timestamps", ignore_index=True)


def create_empty_df(start_timestamp: float, sample_interval_s: float, columns: pd.Index,
                    num_samples_to_add: int, add_to_start: bool = False) -> pd.DataFrame:
    """
    Creates an empty dataframe with num_samples_to_add - 1 timestamps, using columns as the columns
    The one timestamp not being added would be a copy of the start timestamp.
    :param start_timestamp: timestamp to start calculating other timestamps from
    :param sample_interval_s: fixed sample interval in seconds
    :param columns: the non-timestamp columns of the dataframe
    :param num_samples_to_add: the number of timestamps to create
    :param add_to_start: if True, subtracts sample_interval_s from start_timestamp, default False
    :return:
    """
    if add_to_start:
        sample_interval_s = -sample_interval_s
    new_timestamps = np.vectorize(lambda t: start_timestamp + dtu.seconds_to_microseconds(t * sample_interval_s))(
        list(range(1, num_samples_to_add + 1)))
    empty_df = pd.DataFrame([], columns=columns)
    for column_index in columns:
        if column_index == "timestamps":
            empty_df["timestamps"] = new_timestamps
        else:
            empty_df[column_index] = np.nan
    # return a dataframe with only timestamps
    return empty_df
