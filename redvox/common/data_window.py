"""
This module creates specific time-bounded segments of data for users
combine the data packets into a new data packet based on the user parameters
"""
from typing import Optional, Set, List, Dict, Iterable
from datetime import timedelta

import pandas as pd
import numpy as np

from redvox.common import date_time_utils as dtu
from redvox.common import io
from redvox.common.station import Station
from redvox.common.sensor_data import SensorType, SensorData
from redvox.common.api_reader import ApiReader
from redvox.common.data_window_configuration import DataWindowConfig
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
from redvox.api1000.wrapped_redvox_packet.sensors.image import ImageCodec


DEFAULT_GAP_TIME_S: float = 0.25  # default length of a gap in seconds
DEFAULT_START_BUFFER_TD: timedelta = timedelta(minutes=2.0)  # default padding to start time of data
DEFAULT_END_BUFFER_TD: timedelta = timedelta(minutes=2.0)    # default padding to end time of data
# default maximum number of points required to brute force calculate gap timestamps
DEFAULT_MAX_BRUTE_FORCE_GAP_TIMESTAMPS: int = 5000


class DataWindow:
    """
    Holds the data for a given time window; adds interpolated timestamps to fill gaps and pad start and end values
    Properties:
        input_directory: string, directory that contains the files to read data from.  REQUIRED
        structured_layout: bool, if True, the input_directory contains specially named and organized
                            directories of data.  Default True
        station_ids: optional set of strings, representing the station ids to filter on.
                        If empty or None, get any ids found in the input directory.  Default None
        extensions: optional set of strings, representing file extensions to filter on.
                        If None, gets as much data as it can in the input directory.  Default None
        api_versions: optional set of ApiVersions, representing api versions to filter on.
                        If None, get as much data as it can in the input directory.  Default None
        start_datetime: optional datetime, start datetime of the window.
                        If None, uses the first timestamp of the filtered data.  Default None
        end_datetime: optional datetime, end datetime of the window.
                        If None, uses the last timestamp of the filtered data.  Default None
        start_buffer_td: timedelta, the amount of time to include before the start_datetime when filtering data.
                            Default DEFAULT_START_BUFFER_TD
        end_buffer_td: float, the amount of time to include after the end_datetime when filtering data.
                            Default DEFAULT_END_BUFFER_TD
        gap_time_s: float, the minimum amount of seconds between data points that would indicate a gap.
                    Default DEFAULT_GAP_TIME_S
        apply_correction: bool, if True, update the timestamps in the data based on best station offset.  Default True
        stations: list of Stations, the results of reading the data from input_directory
        debug: bool, if True, outputs additional information during initialization. Default False
    """

    def __init__(
        self,
        input_dir: str,
        structured_layout: bool = True,
        start_datetime: Optional[dtu.datetime] = None,
        end_datetime: Optional[dtu.datetime] = None,
        start_buffer_td: timedelta = DEFAULT_START_BUFFER_TD,
        end_buffer_td: timedelta = DEFAULT_END_BUFFER_TD,
        gap_time_s: float = DEFAULT_GAP_TIME_S,
        station_ids: Optional[Iterable[str]] = None,
        extensions: Optional[Set[str]] = None,
        api_versions: Optional[Set[io.ApiVersion]] = None,
        apply_correction: bool = True,
        debug: bool = False,
    ):
        """
        initialize the data window with params
        :param input_dir: string, directory that contains the files to read data from
        :param structured_layout: bool, if True, the input_directory contains specially named and organized
                                    directories of data.  Default True
        :param start_datetime: optional start datetime of the window. If None, uses the first timestamp of the
                                filtered data. Default None
        :param end_datetime: optional end datetime of the window. If None, uses the last timestamp of the filtered
                                data.  Default None
        :param start_buffer_td: the amount of time to include before the start_datetime when filtering data.
                                Default DEFAULT_START_BUFFER_TD
        :param end_buffer_td: the amount of time to include after the end_datetime when filtering data.
                                Default DEFAULT_END_BUFFER_TD
        :param gap_time_s: the minimum amount of seconds between data points that would indicate a gap.
                            Default DEFAULT_GAP_TIME_S
        :param station_ids: optional iterable of station ids to filter on. If empty or None, get any ids found in the
                            input directory.  Default None
        :param extensions: optional set of file extensions to filter on.  If None, get all data in the input directory.
                            Default None
        :param api_versions: optional set of api versions to filter on.  If None, get all data in the input directory.
                                Default None
        :param apply_correction: if True, update the timestamps in the data based on best station offset.
                                    Default True
        :param debug: bool, if True, outputs warnings and additional information, default False
        """

        self.input_directory: str = input_dir
        self.structured_layout: bool = structured_layout
        self.start_datetime: Optional[dtu.datetime] = start_datetime
        self.end_datetime: Optional[dtu.datetime] = end_datetime
        self.start_buffer_td: timedelta = start_buffer_td
        self.end_buffer_td: timedelta = end_buffer_td
        self.gap_time_s: float = gap_time_s
        self.station_ids: Optional[Set[str]]
        if station_ids:
            self.station_ids = set(station_ids)
        else:
            self.station_ids = None
        self.extensions: Optional[Set[str]] = extensions
        self.api_versions: Optional[Set[io.ApiVersion]] = api_versions
        self.apply_correction: bool = apply_correction
        self.debug: bool = debug
        self.stations: Dict[str, Station] = {}
        self.create_data_window()

    def from_config_file(self, file: str) -> "DataWindow":
        """
        Loads a configuration file to create the DataWindow
        :param file: full path to config file
        :return: a data window
        """
        return self.from_config(DataWindowConfig.from_path(file))

    @staticmethod
    def from_config(config: DataWindowConfig) -> "DataWindow":
        """
        Loads a configuration to create the DataWindow
        :param config: DataWindow configuration object
        :return: a data window
        """
        if config.start_year:
            start_time = dtu.datetime(
                year=config.start_year,
                month=config.start_month,
                day=config.start_day,
                hour=config.start_hour,
                minute=config.start_minute,
                second=config.start_second,
            )
        else:
            start_time = None
        if config.end_year:
            end_time = dtu.datetime(
                year=config.end_year,
                month=config.end_month,
                day=config.end_day,
                hour=config.end_hour,
                minute=config.end_minute,
                second=config.end_second,
            )
        else:
            end_time = None
        if config.api_versions:
            api_versions = set([io.ApiVersion.from_str(v) for v in config.api_versions])
        else:
            api_versions = None
        if config.extensions:
            extensions = set(config.extensions)
        else:
            extensions = None
        if config.station_ids:
            station_ids = set(config.station_ids)
        else:
            station_ids = None
        return DataWindow(
            config.input_directory,
            config.structured_layout,
            start_time,
            end_time,
            dtu.timedelta(seconds=config.start_padding_seconds),
            dtu.timedelta(seconds=config.end_padding_seconds),
            config.gap_time_seconds,
            station_ids,
            extensions,
            api_versions,
            config.apply_correction,
            config.debug,
        )

    def _has_time_window(self) -> bool:
        """
        Returns true if there is a start or end datetime in the settings
        :return: True if start_datetime or end_datetime exists
        """
        return self.start_datetime is not None or self.end_datetime is not None

    def get_station(self, station_id: str) -> Optional[Station]:
        """
        Get a single station from the data window
        :param station_id: the id of the station to get
        :return: A single station or None if the station cannot be found
        """
        if station_id in self.stations.keys():
            return self.stations[station_id]
        if self.debug:
            print(f"Warning: Attempted to get station {station_id}, but that station is not in this data window!")
        return None

    def get_all_stations(self) -> List[Station]:
        """
        :return: all stations in the data window as a list
        """
        return list(self.stations.values())

    def get_all_station_ids(self) -> List[str]:
        """
        :return: A list of all station ids with data
        """
        return list(self.stations.keys())

    def check_valid_ids(self):
        """
        searches the data window station_ids for any ids not in the data collected
        outputs a message for each id requested but has no data
        """
        for ids in self.station_ids:
            if ids not in self.stations.keys() and self.debug:
                print(
                    f"WARNING: Requested {ids} but there is no data to read for that station"
                )

    def process_sensor(self, sensor: SensorData, station_id: str, start_date_timestamp: float,
                       end_date_timestamp: float):
        # calculate the sensor's sample interval, std sample interval and sample rate of all data
        sensor.organize_and_update_stats()
        # get only the timestamps between the start and end timestamps
        df_timestamps = sensor.data_timestamps()
        if len(df_timestamps) > 0:
            window_indices = np.where(
                (start_date_timestamp <= df_timestamps)
                & (df_timestamps <= end_date_timestamp)
            )[0]
            # check if all the samples have been cut off
            if len(window_indices) < 1:
                if any(df_timestamps < start_date_timestamp):
                    last_before_start = np.argwhere(df_timestamps < start_date_timestamp)[-1][0]
                else:
                    last_before_start = None
                if any(df_timestamps > end_date_timestamp):
                    first_after_end = np.argwhere(df_timestamps > end_date_timestamp)[0][0]
                else:
                    first_after_end = None
                if last_before_start is not None and first_after_end is None:
                    sensor.data_df = sensor.data_df.iloc[last_before_start].to_frame().T
                    sensor.data_df["timestamps"] = start_date_timestamp
                elif last_before_start is None and first_after_end is not None:
                    sensor.data_df = sensor.data_df.iloc[first_after_end].to_frame().T
                    sensor.data_df["timestamps"] = end_date_timestamp
                elif last_before_start is not None and first_after_end is not None:
                    sensor.data_df = sensor.interpolate(last_before_start, first_after_end,
                                                        start_date_timestamp).to_frame().T
                elif self.debug:
                    print(
                        f"WARNING: Data window for {station_id} {sensor.type.name} "
                        f"sensor has truncated all data points"
                    )
            else:
                sensor.data_df = sensor.data_df.iloc[window_indices].reset_index(
                    drop=True
                )
                if sensor.is_sample_interval_invalid():
                    if self.debug:
                        print(
                            f"WARNING: Cannot fill gaps or pad {station_id} {sensor.type.name} "
                            f"sensor; it has undefined sample interval and sample rate!"
                        )
                else:  # GAP FILL and PAD DATA
                    sample_interval_micros = dtu.seconds_to_microseconds(sensor.sample_interval_s)
                    sensor.data_df = fill_gaps(
                        sensor.data_df,
                        sample_interval_micros + dtu.seconds_to_microseconds(sensor.sample_interval_std_s),
                        dtu.seconds_to_microseconds(self.gap_time_s),
                        DEFAULT_MAX_BRUTE_FORCE_GAP_TIMESTAMPS,
                        )
                    sensor.data_df = pad_data(
                        start_date_timestamp,
                        end_date_timestamp,
                        sensor.data_df,
                        sample_interval_micros,
                    )
        elif self.debug:
            print(f"WARNING: Data window for {station_id} {sensor.type.name} sensor has no data points!")

    def create_window_in_sensors(
        self, station: Station, start_date_timestamp: float, end_date_timestamp: float
    ):
        """
        truncate the sensors in the station to only contain data from start_date_timestamp to end_date_timestamp
        returns nothing, updates the station in place
        :param station: station object to truncate sensors of
        :param start_date_timestamp: timestamp in microseconds since epoch UTC of start of window
        :param end_date_timestamp: timestamp in microseconds since epoch UTC of end of window
        """
        self.process_sensor(station.audio_sensor(), station.id, start_date_timestamp, end_date_timestamp)
        for sensor_type, sensor in station.data.items():
            if sensor_type != SensorType.AUDIO:
                self.process_sensor(sensor, station.id, station.audio_sensor().first_data_timestamp(),
                                    station.audio_sensor().last_data_timestamp())
        # recalculate metadata
        new_meta = [meta for meta in station.metadata
                    if meta.packet_start_mach_timestamp < end_date_timestamp and
                    meta.packet_end_mach_timestamp > start_date_timestamp]
        station.metadata = new_meta
        station.first_data_timestamp = start_date_timestamp
        station.last_data_timestamp = end_date_timestamp

    def create_data_window(self):
        """
        updates the data window to contain only the data within the window parameters
        stations without audio or any data outside the window are removed
        """
        ids_to_pop = []
        r_f = io.ReadFilter()
        if self.start_datetime:
            r_f.with_start_dt(self.start_datetime)
        if self.end_datetime:
            r_f.with_end_dt(self.end_datetime)
        if self.station_ids:
            r_f.with_station_ids(self.station_ids)
        if self.extensions:
            r_f.with_extensions(self.extensions)
        if self.start_buffer_td:
            r_f.with_start_dt_buf(self.start_buffer_td)
        if self.end_buffer_td:
            r_f.with_end_dt_buf(self.end_buffer_td)
        if self.api_versions:
            r_f.with_api_versions(self.api_versions)
        self.stations = ApiReader(
            self.input_directory,
            self.structured_layout,
            r_f,
            self.debug,
        ).read_files_as_stations()
        if self.station_ids is None or len(self.station_ids) == 0:
            self.station_ids = set(self.stations.keys())
        for station in self.stations.values():
            if self.apply_correction:
                station.update_timestamps()
            # set the window start and end if they were specified, otherwise use the bounds of the data
            if self.start_datetime:
                start_datetime = dtu.datetime_to_epoch_microseconds_utc(self.start_datetime)
            else:
                start_datetime = station.first_data_timestamp
            if self.end_datetime:
                end_datetime = dtu.datetime_to_epoch_microseconds_utc(self.end_datetime)
            else:
                end_datetime = station.last_data_timestamp
            # TRUNCATE!
            self.create_window_in_sensors(station, start_datetime, end_datetime)
            ids_to_pop = check_audio_data(station, ids_to_pop, self.debug)
        # check for stations without data, then remove any stations that don't have audio data
        self.check_valid_ids()
        for ids in ids_to_pop:
            self.station_ids.remove(ids)


def check_audio_data(
    station: Station, ids_to_remove: List[str], debug: bool = False
) -> List[str]:
    """
    check if the station has audio data; if it does not, update the list of stations to remove
    :param station: station object to check for audio data
    :param ids_to_remove: list of station ids to remove from the data window
    :param debug: if True, output warning message, default False
    :return: an updated list of station ids to remove from the data window
    """
    station_id = station.id
    if not station.has_audio_sensor():
        if debug:
            print(f"WARNING: {station_id} doesn't have any audio data to read")
        ids_to_remove.append(station_id)
    return ids_to_remove


def pad_data(
    expected_start: float,
    expected_end: float,
    data_df: pd.DataFrame,
    sample_interval_micros: float,
) -> pd.DataFrame:
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
        num_missing_samples = np.floor(start_diff / sample_interval_micros)
        if num_missing_samples > 0:
            # add the gap data to the result dataframe
            result_df = result_df.append(
                create_dataless_timestamps_df(
                    first_data_timestamp,
                    sample_interval_micros,
                    data_df.columns,
                    num_missing_samples,
                    True
                ),
                ignore_index=True,
            )
    if expected_end > last_data_timestamp:
        last_diff = expected_end - last_data_timestamp
        num_missing_samples = np.floor(last_diff / sample_interval_micros)
        if num_missing_samples > 0:
            # add the gap data to the result dataframe
            result_df = result_df.append(
                create_dataless_timestamps_df(
                    last_data_timestamp,
                    sample_interval_micros,
                    data_df.columns,
                    num_missing_samples,
                ),
                ignore_index=True,
            )
    return result_df.sort_values("timestamps", ignore_index=True)


def fill_gaps(
    data_df: pd.DataFrame,
    sample_interval_micros: float,
    gap_time_micros: float,
    num_points_to_brute_force: int = DEFAULT_MAX_BRUTE_FORCE_GAP_TIMESTAMPS,
) -> pd.DataFrame:
    """
    fills gaps in the dataframe with np.nan by interpolating timestamps based on the mean expected sample interval
    :param data_df: dataframe with timestamps as column "timestamps"
    :param sample_interval_micros: sample interval in microseconds
    :param gap_time_micros: minimum amount of microseconds between data points that would indicate a gap
    :param num_points_to_brute_force: maximum number of points to calculate when filling a gap
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
                num_new_samples = (
                    np.ceil(timestamp_diffs[index] / sample_interval_micros) - 1
                )
                if timestamp_diffs[index] > gap_time_micros and num_new_samples > 0:
                    # add the gap data to the result dataframe
                    result_df = result_df.append(
                        create_dataless_timestamps_df(
                            data_time_stamps[index],
                            sample_interval_micros,
                            data_df.columns,
                            num_new_samples,
                        ),
                        ignore_index=True,
                    )
                    if len(result_df) >= expected_num_points:
                        break  # stop the for loop execution when enough points are added
        else:
            # too many points to check, divide and conquer using recursion!
            half_samples = int(num_points / 2)
            first_data_df = data_df.iloc[:half_samples].copy().reset_index(drop=True)
            second_data_df = data_df.iloc[half_samples:].copy().reset_index(drop=True)
            # give half the samples to each recursive call
            first_data_df = fill_gaps(
                first_data_df,
                sample_interval_micros,
                gap_time_micros,
                num_points_to_brute_force,
            )
            second_data_df = fill_gaps(
                second_data_df,
                sample_interval_micros,
                gap_time_micros,
                num_points_to_brute_force,
            )
            result_df = first_data_df.append(second_data_df, ignore_index=True)
    return result_df.sort_values("timestamps", ignore_index=True)


def create_dataless_timestamps_df(
    start_timestamp: float,
    sample_interval_micros: float,
    columns: pd.Index,
    num_samples_to_add: int,
    add_to_start: bool = False,
) -> pd.DataFrame:
    """
    Creates an empty dataframe with num_samples_to_add timestamps, using columns as the columns
    the first timestamp created is 1 sample_interval_s from the start_timestamp
    :param start_timestamp: timestamp in microseconds since epoch UTC to start calculating other timestamps from
    :param sample_interval_micros: fixed sample interval in microseconds since epoch UTC
    :param columns: dataframe the non-timestamp columns of the dataframe
    :param num_samples_to_add: the number of timestamps to create
    :param add_to_start: if True, subtracts sample_interval_s from start_timestamp, default False
    :return: dataframe with timestamps and no data
    """
    empty_df = pd.DataFrame([], columns=columns)
    if num_samples_to_add > 0:
        if add_to_start:
            sample_interval_micros = -sample_interval_micros
        new_timestamps = (
            start_timestamp + np.arange(1, num_samples_to_add + 1) * sample_interval_micros
        )
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
