"""
This module creates specific time-bounded segments of data for users
"""
from typing import Optional, Set, List

import pandas as pd
import numpy as np

from redvox.common import date_time_utils as dtu
from redvox.common.station import Station
from redvox.common.station_reader_utils import ReadResult
from redvox.common.station_reader_utils import read_all_in_dir
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
from redvox.api1000.wrapped_redvox_packet.sensors.image import ImageCodec


DEFAULT_GAP_TIME_S: float = 0.25        # default length of a gap in seconds
DEFAULT_START_PADDING_S: float = 120.   # default padding to start time of data in seconds
DEFAULT_END_PADDING_S: float = 120.     # default padding to end time of data in seconds
# default maximum number of points required to brute force calculate gap timestamps
DEFAULT_MAX_BRUTE_FORCE_GAP_TIMESTAMPS: int = 5000


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
        apply_correction: bool, if True, update the timestamps in the data based on best station offset.  Default True
        structured_layout: bool, if True, the input_directory contains specially named and organized
                            directories of data.  Default True
        stations: optional ReadResult, the results of reading the data from input_directory
        debug: bool, if True, outputs additional information during initialization. Default False
    """
    def __init__(self, input_dir: str, station_ids: Optional[Set[str]] = None,
                 start_datetime: Optional[dtu.datetime] = None, end_datetime: Optional[dtu.datetime] = None,
                 start_padding_s: float = DEFAULT_START_PADDING_S, end_padding_s: float = DEFAULT_END_PADDING_S,
                 gap_time_s: float = DEFAULT_GAP_TIME_S, apply_correction: bool = True,
                 structured_layout: bool = True, debug: bool = False):
        """
        initialize the data window with params
        :param input_dir: string, directory that contains the files to read data from
        :param station_ids: optional set of strings, list of station ids to filter on.
                            If empty or None, get any ids found in the input directory.  Default None
        :param start_datetime: optional datetime, start datetime of the window.
                                If None, uses the first timestamp of the filtered data.  Default None
        :param end_datetime: optional datetime, end datetime of the window.
                                If None, uses the last timestamp of the filtered data.  Default None
        :param start_padding_s: float, the amount of seconds to include before the start_datetime
                                when filtering data.  Default DEFAULT_START_PADDING_S
        :param end_padding_s: float, the amount of seconds to include after the end_datetime
                                when filtering data.  Default DEFAULT_END_PADDING_S
        :param gap_time_s: float, the minimum amount of seconds between data points that would indicate a gap.
                            Default DEFAULT_GAP_TIME_S
        :param apply_correction: bool, if True, update the timestamps in the data based on best station offset.
                                    Default True
        :param structured_layout: bool, if True, the input_directory contains specially named and organized
                                    directories of data.  Default True
        :param debug: bool, if True, outputs warnings and additional information, default False
        """
        self.input_directory: str = input_dir
        self.station_ids: Optional[Set[str]] = station_ids
        self.start_datetime: Optional[dtu.datetime] = start_datetime
        self.end_datetime: Optional[dtu.datetime] = end_datetime
        self.start_padding_s: float = start_padding_s
        self.end_padding_s: float = end_padding_s
        self.gap_time_s: float = gap_time_s
        self.apply_correction: bool = apply_correction
        self.structured_layout: bool = structured_layout
        self.debug: bool = debug
        start_time = self._pad_start_datetime_s()
        if np.isnan(start_time):
            start_time = None
        else:
            start_time = int(start_time)
        end_time = self._pad_end_datetime_s()
        if np.isnan(end_time):
            end_time = None
        else:
            end_time = int(end_time)
        self.stations: ReadResult = read_all_in_dir(self.input_directory, start_time, end_time,
                                                    self.station_ids, self.structured_layout)
        if self.station_ids is None or len(self.station_ids) == 0:
            self.station_ids = self.stations.get_all_station_ids()
        else:
            self.check_valid_ids()
        self.create_data_window()

    def _has_time_window(self) -> bool:
        """
        Returns true if there is a start or end datetime in the settings
        :return: True if start_datetime or end_datetime exists
        """
        return self.start_datetime is not None or self.end_datetime is not None

    def _pad_start_datetime_s(self) -> float:
        """
        apply padding to the start datetime
        :return: padded start datetime as seconds since epoch UTC or np.nan if start datetime is undefined
        """
        if self.start_datetime is None:
            return np.nan
        return dtu.datetime_to_epoch_seconds_utc(self.start_datetime) - self.start_padding_s

    def _pad_end_datetime_s(self) -> float:
        """
        apply padding to the end datetime
        :return: padded end datetime as seconds since epoch UTC or np.nan if end datetime is undefined
        """
        if self.end_datetime is None:
            return np.nan
        return dtu.datetime_to_epoch_seconds_utc(self.end_datetime) + self.end_padding_s

    def get_station(self, station: str) -> Optional[Station]:
        """
        :param station: the station id to search for
        :return: A single station based on the id given or None if the station doesn't exist
        """
        return self.stations.get_station(station)

    def get_all_stations(self) -> List[Station]:
        """
        :return: A list of all stations in the object
        """
        return self.stations.get_all_stations()

    def correct_timestamps(self):
        """
        update the timestamps in all stations
        """
        if self.apply_correction:
            for station in self.stations.station_id_uuid_to_stations.values():
                station.update_timestamps()

    def check_valid_ids(self):
        """
        searches the data window station_ids for any ids not in the data collected
        """
        for ids in self.station_ids:
            if not self.stations.check_for_id(ids) and self.debug:
                print(f"WARNING: Requested {ids} but there is no data to read for that station")

    def create_window_in_sensors(self, station: Station, start_date_timestamp: float, end_date_timestamp: float):
        """
        truncate the sensors in the station to only contain data from start_date_timestamp to end_date_timestamp
        returns nothing, updates the station in place
        :param station: station object to truncate sensors of
        :param start_date_timestamp: float, timestamp in microseconds since epoch UTC of start of window
        :param end_date_timestamp: float, timestamp in microseconds since epoch UTC of end of window
        """
        gap_time_micros = dtu.seconds_to_microseconds(self.gap_time_s)
        station_id = station.station_metadata.station_id
        for sensor_type, sensor in station.station_data.items():
            # calculate the sensor's sample interval, std sample interval and sample rate of all data
            sensor.organize_and_update_stats()
            # get only the timestamps between the start and end timestamps
            df_timestamps = sensor.data_timestamps()
            if len(df_timestamps) > 0:
                window_indices = np.where((start_date_timestamp <= df_timestamps) &
                                          (df_timestamps <= end_date_timestamp))[0]
                # check if all the samples have been cut off
                if len(window_indices) < 1:
                    if self.debug:
                        print(f"WARNING: Data window for {station_id} {sensor_type.name} "
                              f"sensor has truncated all data points")
                else:
                    sensor.data_df = sensor.data_df.iloc[window_indices].reset_index(drop=True)
                    if sensor.is_sample_interval_invalid():
                        if self.debug:
                            print(f"WARNING: Cannot fill gaps or pad {station_id} {sensor_type.name} "
                                  f"sensor; it has undefined sample interval and sample rate!")
                    else:  # GAP FILL and PAD DATA
                        sample_interval_micros = dtu.seconds_to_microseconds(sensor.sample_interval_s)
                        sensor.data_df = fill_gaps(sensor.data_df, sample_interval_micros +
                                                   dtu.seconds_to_microseconds(sensor.sample_interval_std_s),
                                                   gap_time_micros, DEFAULT_MAX_BRUTE_FORCE_GAP_TIMESTAMPS)
                        sensor.data_df = pad_data(start_date_timestamp, end_date_timestamp, sensor.data_df,
                                                  sample_interval_micros)
            elif self.debug:
                print(f"WARNING: Data window for {station_id} {sensor_type.name} sensor has no data points!")

    def truncate_metadata(self, station: Station, start_date_timestamp: float, end_date_timestamp: float):
        """
        truncates and updates the metadata of the station to only be from start_date_timestamp to end_date_timestamp.
        Returns nothing; updates metadata in place
        :param station: station object to update
        :param start_date_timestamp: float, timestamp in microseconds since epoch UTC of start of window
        :param end_date_timestamp: float, timestamp in microseconds since epoch UTC of end of window
        """
        station.packet_gap_detector(self.gap_time_s)
        station.packet_data = [p for p in station.packet_data
                               if p.data_end_timestamp > start_date_timestamp and
                               p.data_start_timestamp < end_date_timestamp]
        if station.has_location_data():
            # anything with 0 altitude is likely a network provided location
            station.location_sensor().data_df.loc[(station.location_sensor().data_df["altitude"] == 0),
                                                  "location_provider"] = LocationProvider.NETWORK
        station.update_station_location_metadata(start_date_timestamp, end_date_timestamp)
        station.station_metadata.timing_data.episode_start_timestamp_s = \
            dtu.microseconds_to_seconds(start_date_timestamp)
        station.station_metadata.timing_data.episode_end_timestamp_s = dtu.microseconds_to_seconds(end_date_timestamp)
        station.station_metadata.timing_data.station_first_data_timestamp = \
            station.audio_sensor().first_data_timestamp()

    def create_data_window(self):
        """
        updates the data window to contain only the data within the window parameters
        stations without audio or any data within the window are removed
        """
        ids_to_pop = []
        for station in self.stations.get_all_stations():
            ids_to_pop = check_audio_data(station, ids_to_pop, self.debug)
            # apply time correction
            if self.apply_correction:
                station.update_timestamps()
            # set the window start and end if they were specified, otherwise use the bounds of the data
            if self.start_datetime:
                start_datetime = dtu.datetime_to_epoch_microseconds_utc(self.start_datetime)
            else:
                start_datetime = station.audio_sensor().first_data_timestamp()
            if self.end_datetime:
                end_datetime = dtu.datetime_to_epoch_microseconds_utc(self.end_datetime)
            else:
                end_datetime = station.audio_sensor().last_data_timestamp()
            # TRUNCATE!
            self.create_window_in_sensors(station, start_datetime, end_datetime)
            self.truncate_metadata(station, start_datetime, end_datetime)
            ids_to_pop = check_audio_data(station, ids_to_pop, self.debug)
        # remove any stations that don't have audio data
        for ids in ids_to_pop:
            self.stations.pop_station(ids)


def check_audio_data(station: Station, ids_to_remove: List[str], debug: bool = False) -> List[str]:
    """
    check if the station has audio data; if it does not, update the list of stations to remove
    :param station: station object to check for audio data
    :param ids_to_remove: list of strings, the station ids to remove from the data window
    :param debug: bool, if True, output warning message, default False
    :return: an updated list of station ids to remove from the data window
    """
    station_id = station.station_metadata.station_id
    if not station.has_audio_data():
        if debug:
            print(f"WARNING: {station_id} doesn't have any audio data to read")
        ids_to_remove.append(station_id)
    return ids_to_remove


def pad_data(expected_start: float, expected_end: float, data_df: pd.DataFrame,
             sample_interval_micros: float) -> pd.DataFrame:
    """
    Pad the start and end of the dataframe with np.nan
    :param expected_start: timestamp indicating start time of the data to pad from
    :param expected_end: timestamp indicating end time of the data to pad from
    :param data_df: dataframe with timestamps as column "timestamps"
    :param sample_interval_micros: constant sample interval in microseconds
    :return: dataframe padded with np.nans in front and back to meet full size of expected start and end
    """
    # extract the necessary information to pad the data
    data_time_stamps = data_df["timestamps"].to_numpy()
    first_data_timestamp = data_time_stamps[0]
    last_data_timestamp = data_time_stamps[-1]
    result_df = data_df.copy()
    # FRONT/END GAP FILL!  calculate the audio samples missing based on inputs
    if expected_start < first_data_timestamp:
        start_diff = first_data_timestamp - expected_start
        num_missing_samples = np.ceil(start_diff / sample_interval_micros)
        # add the gap data to the result dataframe
        result_df = result_df.append(create_dataless_timestamps_df(expected_start - sample_interval_micros,
                                                                   sample_interval_micros, data_df.columns,
                                                                   num_missing_samples), ignore_index=True)
    if expected_end > last_data_timestamp:
        last_diff = expected_end - last_data_timestamp
        num_missing_samples = np.ceil(last_diff / sample_interval_micros)
        # add the gap data to the result dataframe
        result_df = result_df.append(create_dataless_timestamps_df(expected_end + sample_interval_micros,
                                                                   sample_interval_micros, data_df.columns,
                                                                   num_missing_samples, True), ignore_index=True)
    return result_df.sort_values("timestamps", ignore_index=True)


def fill_gaps(data_df: pd.DataFrame, sample_interval_micros: float, gap_time_micros: float,
              num_points_to_brute_force: int = DEFAULT_MAX_BRUTE_FORCE_GAP_TIMESTAMPS) -> pd.DataFrame:
    """
    fills gaps in the dataframe with np.nan by interpolating timestamps based on the mean expected sample interval
    :param data_df: dataframe with timestamps as column "timestamps"
    :param sample_interval_micros: float, sample interval in microseconds
    :param gap_time_micros: float, minimum amount of microseconds between data points that would indicate a gap
    :param num_points_to_brute_force: int, maximum number of points to calculate when filling a gap
    :return: dataframe without gaps
    """
    # extract the necessary information to compute gap size and gap timestamps
    data_time_stamps = data_df["timestamps"].to_numpy()
    first_data_timestamp = data_time_stamps[0]
    last_data_timestamp = data_time_stamps[-1]
    data_duration_micros = last_data_timestamp - first_data_timestamp
    num_points = len(data_time_stamps)
    # add one to calculation to include the last timestamp
    expected_num_points = np.ceil(data_duration_micros / sample_interval_micros) + 1
    # gap duration cannot be less than sample interval
    gap_time_micros = np.max([sample_interval_micros, gap_time_micros])
    result_df = data_df.copy()
    # if there are less points than our expected amount, we have gaps to fill
    if num_points < expected_num_points:
        # if the data we're looking at is short enough, we can start comparing points
        if num_points < num_points_to_brute_force:
            # look at every timestamp difference
            timestamp_diffs = np.diff(data_time_stamps)
            for index in np.where(timestamp_diffs > gap_time_micros)[0]:
                # calc samples to add, subtracting 1 to prevent copying last timestamp
                num_new_samples = np.ceil(timestamp_diffs[index] / sample_interval_micros) - 1
                if timestamp_diffs[index] > gap_time_micros and num_new_samples > 0:
                    # add the gap data to the result dataframe
                    result_df = result_df.append(
                        create_dataless_timestamps_df(data_time_stamps[index], sample_interval_micros,
                                                      data_df.columns, num_new_samples), ignore_index=True)
                    if len(result_df) >= expected_num_points:
                        break  # stop the for loop execution when enough points are added
        else:
            # too many points to check, divide and conquer using recursion!
            half_samples = int(num_points / 2)
            first_data_df = data_df.iloc[:half_samples].copy().reset_index(drop=True)
            second_data_df = data_df.iloc[half_samples:].copy().reset_index(drop=True)
            # give half the samples to each recursive call
            first_data_df = fill_gaps(first_data_df, sample_interval_micros, gap_time_micros, num_points_to_brute_force)
            second_data_df = fill_gaps(second_data_df, sample_interval_micros, gap_time_micros,
                                       num_points_to_brute_force)
            result_df = first_data_df.append(second_data_df, ignore_index=True)
    return result_df.sort_values("timestamps", ignore_index=True)


def create_dataless_timestamps_df(start_timestamp: float, sample_interval_micros: float, columns: pd.Index,
                                  num_samples_to_add: int, add_to_start: bool = False) -> pd.DataFrame:
    """
    Creates an empty dataframe with num_samples_to_add timestamps, using columns as the columns
    the first timestamp created is 1 sample_interval_s from the start_timestamp
    :param start_timestamp: float, timestamp in microseconds since epoch UTC to start calculating other timestamps from
    :param sample_interval_micros: float, fixed sample interval in microseconds since epoch UTC
    :param columns: dataframe index, the non-timestamp columns of the dataframe
    :param num_samples_to_add: int, the number of timestamps to create
    :param add_to_start: bool, if True, subtracts sample_interval_s from start_timestamp, default False
    :return: dataframe with timestamps and no data
    """
    if add_to_start:
        sample_interval_micros = -sample_interval_micros
    new_timestamps = start_timestamp + np.arange(1, num_samples_to_add + 1) * sample_interval_micros
    empty_df = pd.DataFrame([], columns=columns)
    for column_index in columns:
        if column_index == "timestamps":
            empty_df[column_index] = new_timestamps
        elif column_index == "location_provider":
            empty_df[column_index] = LocationProvider.UNKNOWN
        elif column_index == "image_codec":
            empty_df[column_index] = ImageCodec.UNKNOWN
        else:
            empty_df[column_index] = np.nan
    return empty_df
