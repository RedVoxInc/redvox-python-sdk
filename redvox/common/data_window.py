"""
This module creates specific time-bounded segments of data for users
combine the data packets into a new data packet based on the user parameters
"""
from pathlib import Path
from typing import Optional, Set, List, Dict, Iterable
from datetime import timedelta
from dataclasses import dataclass, field

import redvox
from dataclasses_json import dataclass_json
import multiprocessing
import multiprocessing.pool
import pickle

import numpy as np

from redvox.common import date_time_utils as dtu
from redvox.common import io
from redvox.common.parallel_utils import maybe_parallel_map
from redvox.common.station import Station
from redvox.common.sensor_data import SensorType, SensorData
from redvox.common.api_reader import ApiReader
from redvox.common.data_window_configuration import DataWindowConfig
from redvox.common import gap_and_pad_utils as gpu

DEFAULT_START_BUFFER_TD: timedelta = timedelta(minutes=2.0)  # default padding to start time of data
DEFAULT_END_BUFFER_TD: timedelta = timedelta(minutes=2.0)  # default padding to end time of data
# minimum default length of time in seconds for data to be off by to be considered suspicious
DATA_DROP_DURATION_S: float = 0.2


@dataclass_json()
@dataclass
class DataWindowExceptions:
    """
    all the errors go here
    """
    errors: List[str] = field(default_factory=list)

    def get(self) -> List[str]:
        """
        :return: the list of errors
        """
        return self.errors

    def append(self, msg: str):
        """
        append an error message to the list of errors

        :param msg: error message to add
        """
        self.errors.append(msg)

    def extend(self, msgs: List[str]):
        """
        extend a list of error messages to the list of errors

        :param msgs: error messages to add
        """
        self.errors.extend(msgs)

    def print(self):
        """
        print all errors
        """
        if len(self.errors) > 0:
            print("Errors encountered while creating data window:")
            for error in self.errors:
                print(error)


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
        end_datetime: optional datetime, non-inclusive end datetime of the window.
                        If None, uses the last timestamp of the filtered data.  Default None
        start_buffer_td: timedelta, the amount of time to include before the start_datetime when filtering data.
                            Default DEFAULT_START_BUFFER_TD
        end_buffer_td: timedelta, the amount of time to include after the end_datetime when filtering data.
                            Default DEFAULT_END_BUFFER_TD
        drop_time_s: float, the minimum amount of seconds between data files that would indicate a gap.
                     Default DATA_DROP_DURATION_S
        apply_correction: bool, if True, update the timestamps in the data based on best station offset.  Default True
        copy_edge_points: enumeration of DataPointCreationMode.  Determines how new points are created.
                            Valid values are NAN, COPY, and INTERPOLATE.  Default COPY
        debug: bool, if True, outputs additional information during initialization. Default False
        errors: DataWindowExceptions, class containing a list of all errors encountered by the data window.
        stations: list of Stations, the results of reading the data from input_directory
        sdk_version: str, the version of the Redvox SDK used to create the data window
    """
    def __init__(
        self,
        input_dir: str,
        structured_layout: bool = True,
        start_datetime: Optional[dtu.datetime] = None,
        end_datetime: Optional[dtu.datetime] = None,
        start_buffer_td: timedelta = DEFAULT_START_BUFFER_TD,
        end_buffer_td: timedelta = DEFAULT_END_BUFFER_TD,
        drop_time_s: float = DATA_DROP_DURATION_S,
        station_ids: Optional[Iterable[str]] = None,
        extensions: Optional[Set[str]] = None,
        api_versions: Optional[Set[io.ApiVersion]] = None,
        apply_correction: bool = True,
        copy_edge_points: gpu.DataPointCreationMode = gpu.DataPointCreationMode.COPY,
        debug: bool = False
    ):
        self.errors = DataWindowExceptions()
        self.input_directory: str = input_dir
        self.structured_layout: bool = structured_layout
        self.start_datetime: Optional[dtu.datetime] = start_datetime
        self.end_datetime: Optional[dtu.datetime] = end_datetime
        self.start_buffer_td: timedelta = start_buffer_td
        self.end_buffer_td: timedelta = end_buffer_td
        self.drop_time_s: float = drop_time_s
        self.station_ids: Optional[Set[str]]
        if station_ids:
            self.station_ids = set(station_ids)
        else:
            self.station_ids = None
        self.extensions: Optional[Set[str]] = extensions
        self.api_versions: Optional[Set[io.ApiVersion]] = api_versions
        self.apply_correction: bool = apply_correction
        self.copy_edge_points = copy_edge_points
        self.sdk_version: str = redvox.VERSION
        self.debug: bool = debug
        self.stations: List[Station] = []
        if start_datetime and end_datetime and (end_datetime <= start_datetime):
            self.errors.append("Data Window will not work when end datetime is before or equal to start datetime.\n"
                               f"Your times: {end_datetime} <= {start_datetime}")
        else:
            self.create_data_window()
        if debug:
            self.print_errors()

    @staticmethod
    def from_config_file(file: str) -> "DataWindow":
        """
        Loads a configuration file to create the DataWindow

        :param file: full path to config file
        :return: a data window
        """
        return DataWindow.from_config(DataWindowConfig.from_path(file))

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
        if config.edge_points_mode not in gpu.DataPointCreationMode.list_names():
            config.edge_points_mode = "COPY"
        return DataWindow(
            config.input_directory,
            config.structured_layout,
            start_time,
            end_time,
            dtu.timedelta(seconds=config.start_padding_seconds),
            dtu.timedelta(seconds=config.end_padding_seconds),
            DATA_DROP_DURATION_S,
            station_ids,
            extensions,
            api_versions,
            config.apply_correction,
            gpu.DataPointCreationMode[config.edge_points_mode],
            config.debug,
        )

    @staticmethod
    def deserialize(path: str) -> "DataWindow":
        """
        Decompresses and deserializes a DataWindow written to disk.

        :param path: Path to the serialized and compressed data window.
        :return: An instance of a DataWindowFast.
        """
        return io.deserialize_data_window(path)

    def serialize(self, base_dir: str = ".", file_name: Optional[str] = None, compression_factor: int = 4) -> Path:
        """
        Serializes and compresses this DataWindowFast to a file.

        :param base_dir: The base directory to write the serialized file to (default=.).
        :param file_name: The optional file name. If None, a default filename with the following format is used:
                          [start_ts]_[end_ts]_[num_stations].pkl.lz4
        :param compression_factor: A value between 1 and 12. Higher values provide better compression, but take
        longer. (default=4).
        :return: The path to the written file.
        """
        return io.serialize_data_window(self, base_dir, file_name, compression_factor)

    def to_json_file(self, base_dir: str = ".", file_name: Optional[str] = None,
                     compression_format: str = "lz4") -> Path:
        """
        Converts the data window metadata into a JSON file and compresses the data window and writes it to disk.

        :param base_dir: base directory to write the json file to.  Default . (local directory)
        :param file_name: the optional file name.  Do not include a file extension.
                            If None, a default file name is created using this format:
                            [start_ts]_[end_ts]_[num_stations].json
        :param compression_format: the type of compression to use on the data window object.  default lz4
        :return: The path to the written file
        """
        return io.data_window_to_json_file(self, base_dir, file_name, compression_format)

    def to_json(self, compressed_file_base_dir: str = ".", compressed_file_name: Optional[str] = None,
                compression_format: str = "lz4") -> str:
        """
        Converts the data window metadata into a JSON string, then compresses the data window and writes it to disk.

        :param compressed_file_base_dir: base directory to write the json file to.  Default . (local directory)
        :param compressed_file_name: the optional file name.  Do not include a file extension.
                                        If None, a default file name is created using this format:
                                        [start_ts]_[end_ts]_[num_stations].[compression_format]
        :param compression_format: the type of compression to use on the data window object.  default lz4
        :return: The json string
        """
        return io.data_window_to_json(self, compressed_file_base_dir, compressed_file_name, compression_format)

    @staticmethod
    def from_json_file(base_dir: str, file_name: str,
                       dw_base_dir: Optional[str] = None,
                       start_dt: Optional[dtu.datetime] = None,
                       end_dt: Optional[dtu.datetime] = None,
                       station_ids: Optional[Iterable[str]] = None) -> Optional["DataWindow"]:
        """
        Reads a JSON file and checks if:
            * The requested times are within the JSON file's times
            * The requested stations are a subset of the JSON file's stations

        :param base_dir: the base directory containing the json file
        :param file_name: the file name of the json file.  Do not include extensions
        :param dw_base_dir: optional directory containing the compressed data window file.
                            If not given, assume in subdirectory "dw".  default None
        :param start_dt: the start datetime to check against.  if not given, assumes True.  default None
        :param end_dt: the end datetime to check against.  if not given, assumes True.  default None
        :param station_ids: the station ids to check against.  if not given, assumes True.  default None
        :return: the data window if it suffices, otherwise None
        """
        if not dw_base_dir:
            dw_base_dir = Path(base_dir).joinpath("dw")
        file_name += ".json"
        return DataWindow.from_json_dict(
            io.json_file_to_data_window(base_dir, file_name), dw_base_dir, start_dt, end_dt, station_ids)

    @staticmethod
    def from_json(json_str: str, dw_base_dir: str,
                  start_dt: Optional[dtu.datetime] = None,
                  end_dt: Optional[dtu.datetime] = None,
                  station_ids: Optional[Iterable[str]] = None) -> Optional["DataWindow"]:
        """
        Reads a JSON string and checks if:
            * The requested times are within the JSON file's times
            * The requested stations are a subset of the JSON file's stations

        :param json_str: the JSON to read
        :param dw_base_dir: directory containing the compressed data window file
        :param start_dt: the start datetime to check against.  if not given, assumes True.  default None
        :param end_dt: the end datetime to check against.  if not given, assumes True.  default None
        :param station_ids: the station ids to check against.  if not given, assumes True.  default None
        :return: the data window if it suffices, otherwise None
        """
        return DataWindow.from_json_dict(io.json_to_data_window(json_str), dw_base_dir,
                                         start_dt, end_dt, station_ids)

    @staticmethod
    def from_json_dict(json_dict: Dict,
                       dw_base_dir: str,
                       start_dt: Optional[dtu.datetime] = None,
                       end_dt: Optional[dtu.datetime] = None,
                       station_ids: Optional[Iterable[str]] = None) -> Optional["DataWindow"]:
        """
        Reads a JSON string and checks if:
            * The requested times are within the JSON file's times
            * The requested stations are a subset of the JSON file's stations

        :param json_dict: the dictionary to read
        :param dw_base_dir: base directory for the compressed data window file
        :param start_dt: optional start datetime to check against.  if not given, assumes True.  default None
        :param end_dt: optional end datetime to check against.  if not given, assumes True.  default None
        :param station_ids: optional station ids to check against.  if not given, assumes True.  default None
        :return: the data window if it suffices, otherwise None
        """
        if start_dt and json_dict["start_datetime"] >= dtu.datetime_to_epoch_microseconds_utc(start_dt):
            return None
        if end_dt and json_dict["end_datetime"] < dtu.datetime_to_epoch_microseconds_utc(end_dt):
            return None
        if station_ids and not all(a in json_dict["station_ids"] for a in station_ids):
            return None
        comp_dw_path = str(Path(dw_base_dir).joinpath(json_dict["file_name"]))
        if json_dict["compression_format"] == "lz4":
            return DataWindow.deserialize(comp_dw_path + ".pkl.lz4")
        else:
            with open(comp_dw_path + ".pkl", 'rb') as fp:
                return pickle.load(fp)

    def get_station(self, station_id: str, station_uuid: Optional[str] = None,
                    start_timestamp: Optional[float] = None) -> Optional[List[Station]]:
        """
        Get stations from the data window.  Must give at least the station's id.  Other parameters may be None,
        which means the value will be ignored when searching.  Results will match all non-None parameters given.

        :param station_id: station id
        :param station_uuid: station uuid, default None
        :param start_timestamp: station start timestamp in microseconds since UTC epoch, default None
        :return: A list of valid stations or None if the station cannot be found
        """
        result = [s for s in self.stations if s.get_key().check_key(station_id, station_uuid, start_timestamp)]
        if len(result) > 0:
            return result
        if self.debug:
            self.errors.append(f"Warning: Attempted to get station {station_id}, "
                               f"but that station is not in this data window!")
        return None

    def _add_sensor_to_window(self, station: Station):
        self.errors.extend(station.errors.get())
        # set the window start and end if they were specified, otherwise use the bounds of the data
        self.create_window_in_sensors(station, self.start_datetime, self.end_datetime)

    def create_data_window(self, pool: Optional[multiprocessing.pool.Pool] = None):
        """
        updates the data window to contain only the data within the window parameters
        stations without audio or any data outside the window are removed
        """
        # Let's create and manage a single pool of workers that we can utilize throughout
        # the instantiation of the data window.
        _pool: multiprocessing.pool.Pool = multiprocessing.Pool() if pool is None else pool

        r_f = io.ReadFilter()
        if self.start_datetime:
            r_f.with_start_dt(self.start_datetime)
        if self.end_datetime:
            r_f.with_end_dt(self.end_datetime)
        if self.station_ids:
            r_f.with_station_ids(self.station_ids)
        if self.extensions:
            r_f.with_extensions(self.extensions)
        else:
            self.extensions = r_f.extensions
        if self.api_versions:
            r_f.with_api_versions(self.api_versions)
        else:
            self.api_versions = r_f.api_versions
        if self.start_buffer_td:
            r_f.with_start_dt_buf(self.start_buffer_td)
        else:
            self.start_buffer_td = r_f.start_dt_buf
        if self.end_buffer_td:
            r_f.with_end_dt_buf(self.end_buffer_td)
        else:
            self.end_buffer_td = r_f.end_dt_buf

        # get the data to convert into a window
        a_r = ApiReader(self.input_directory, self.structured_layout, r_f, self.debug, _pool)

        if not self.station_ids:
            self.station_ids = a_r.index_summary.station_ids()
        # Parallel update
        # Apply timing correction in parallel by station
        if self.apply_correction:
            for st in maybe_parallel_map(_pool, Station.update_timestamps,
                                         iter(a_r.get_stations()), chunk_size=1):
                self._add_sensor_to_window(st)
        else:
            [self._add_sensor_to_window(s) for s in a_r.get_stations()]

        # check for stations without data
        self._check_for_audio()
        self._check_valid_ids()

        if len(self.stations) < 1 and self.station_ids:
            self.errors.append(f"No data found for selected stations: {self.station_ids}")
            # else:
            #     self.errors.append(f"No data found in directory {self.input_directory}")

        # update remaining data window values if they're still default
        if not self.start_datetime and len(self.stations) > 0:
            self.start_datetime = dtu.datetime_from_epoch_microseconds_utc(
                np.min([t.first_data_timestamp for t in self.stations]))
        # end_datetime is non-inclusive, so it must be greater than our latest timestamp
        if not self.end_datetime and len(self.stations) > 0:
            self.end_datetime = dtu.datetime_from_epoch_microseconds_utc(
                np.max([t.last_data_timestamp for t in self.stations]) + 1)

        # If the pool was created by this function, then it needs to managed by this function.
        if pool is None:
            _pool.close()

    def _check_for_audio(self):
        """
        removes any station and station id without audio data from the data window
        """
        remove = []
        for s in self.stations:
            if not s.has_audio_sensor():
                remove.append(s.id)
        self.stations = [s for s in self.stations if s.id not in remove]
        self.station_ids = [s for s in self.station_ids if s not in remove]

    def _check_valid_ids(self):
        """
        searches the data window station_ids for any ids not in the data collected
        outputs a message for each id requested but has no data
        """
        for ids in self.station_ids:
            if ids not in [i.id for i in self.stations] and self.debug:
                self.errors.append(
                    f"WARNING: Requested {ids} but there is no data to read for that station"
                )

    def create_window_in_sensors(
            self, station: Station, start_datetime: Optional[dtu.datetime] = None,
            end_datetime: Optional[dtu.datetime] = None
    ):
        """
        truncate the sensors in the station to only contain data from start_date_timestamp to end_date_timestamp
        if the start and/or end are not specified, keeps all audio data that fits and uses it
        to truncate the other sensors.
        returns nothing, updates the station in place

        :param station: station object to truncate sensors of
        :param start_datetime: datetime of start of window, default None
        :param end_datetime: datetime of end of window, default None
        """
        if start_datetime:
            start_datetime = dtu.datetime_to_epoch_microseconds_utc(start_datetime)
        else:
            start_datetime = 0
        if end_datetime:
            end_datetime = dtu.datetime_to_epoch_microseconds_utc(end_datetime)
        else:
            end_datetime = dtu.datetime_to_epoch_microseconds_utc(dtu.datetime.max)
        self.process_sensor(station.audio_sensor(), station.id, start_datetime, end_datetime)
        for sensor in [s for s in station.data if s.type != SensorType.AUDIO]:
            self.process_sensor(sensor, station.id, station.audio_sensor().first_data_timestamp(),
                                station.audio_sensor().last_data_timestamp())
        # recalculate metadata
        station.first_data_timestamp = station.audio_sensor().first_data_timestamp()
        station.last_data_timestamp = station.audio_sensor().data_timestamps()[-1]
        station.packet_metadata = [meta for meta in station.packet_metadata
                                   if meta.packet_start_mach_timestamp < station.last_data_timestamp and
                                   meta.packet_end_mach_timestamp >= station.first_data_timestamp]
        self.stations.append(station)

    def process_sensor(self, sensor: SensorData, station_id: str, start_date_timestamp: float,
                       end_date_timestamp: float):
        """
        process a non audio sensor to fit within the data window.  Updates sensor in place, returns nothing.

        :param sensor: sensor to process
        :param station_id: station id
        :param start_date_timestamp: start of data window
        :param end_date_timestamp: end of data window
        """
        if sensor.num_samples() > 0:
            # get only the timestamps between the start and end timestamps
            before_start = np.where(sensor.data_timestamps() < start_date_timestamp)[0]
            after_end = np.where(end_date_timestamp <= sensor.data_timestamps())[0]
            # start_index is inclusive of window start
            if len(before_start) > 0:
                last_before_start = before_start[-1]
                start_index = last_before_start + 1
            else:
                last_before_start = None
                start_index = 0
            # end_index is non-inclusive of window end
            if len(after_end) > 0:
                first_after_end = after_end[0]
                end_index = first_after_end
            else:
                first_after_end = None
                end_index = sensor.num_samples()
            # check if all the samples have been cut off
            is_audio = sensor.type == SensorType.AUDIO
            if end_index <= start_index:
                if is_audio:
                    self.errors.append(f"WARNING: Data window for {station_id} "
                                       f"Audio sensor has truncated all data points")
                elif last_before_start is not None and first_after_end is None:
                    sensor.data_df = sensor.data_df.iloc[[last_before_start]]
                    sensor.data_df["timestamps"] = [start_date_timestamp]
                elif last_before_start is None and first_after_end is not None:
                    sensor.data_df = sensor.data_df.iloc[[first_after_end]]
                    sensor.data_df["timestamps"] = [end_date_timestamp]
                elif last_before_start is not None and first_after_end is not None:
                    sensor.data_df = sensor.interpolate(start_date_timestamp, last_before_start, 1,
                                                        self.copy_edge_points == gpu.DataPointCreationMode.COPY
                                                        ).to_frame().T
                else:
                    self.errors.append(
                        f"WARNING: Data window for {station_id} {sensor.type.name} "
                        f"sensor has truncated all data points"
                    )
            else:
                sensor.data_df = sensor.data_df.iloc[start_index:end_index].reset_index(
                    drop=True
                )
                # if sensor is audio or location, we want nan'd edge points
                if is_audio or sensor.type == SensorType.LOCATION:
                    new_point_mode = gpu.DataPointCreationMode["NAN"]
                else:
                    new_point_mode = self.copy_edge_points
                # add in the data points at the edges of the window if there are defined start and/or end times
                # or the sensor is not audio
                if not is_audio or self.end_datetime:
                    sensor.data_df = gpu.add_data_points_to_df(sensor.data_df, sensor.num_samples() - 1,
                                                               end_date_timestamp - sensor.last_data_timestamp(),
                                                               point_creation_mode=new_point_mode)

                if not is_audio or self.start_datetime:
                    sensor.data_df = gpu.add_data_points_to_df(sensor.data_df, 0,
                                                               start_date_timestamp - sensor.first_data_timestamp(),
                                                               point_creation_mode=new_point_mode)
                sensor.data_df.sort_values("timestamps", inplace=True, ignore_index=True)
        else:
            self.errors.append(f"WARNING: Data window for {station_id} {sensor.type.name} "
                               f"sensor has no data points!")

    def print_errors(self):
        """
        prints errors to screen
        """
        self.errors.print()


# class DataWindow:
#     """
#     Holds the data for a given time window; adds interpolated timestamps to fill gaps and pad start and end values
#     Properties:
#         input_directory: string, directory that contains the files to read data from.  REQUIRED
#         structured_layout: bool, if True, the input_directory contains specially named and organized
#                             directories of data.  Default True
#         station_ids: optional set of strings, representing the station ids to filter on.
#                         If empty or None, get any ids found in the input directory.  Default None
#         extensions: optional set of strings, representing file extensions to filter on.
#                         If None, gets as much data as it can in the input directory.  Default None
#         api_versions: optional set of ApiVersions, representing api versions to filter on.
#                         If None, get as much data as it can in the input directory.  Default None
#         start_datetime: optional datetime, start datetime of the window.
#                         If None, uses the first timestamp of the filtered data.  Default None
#         end_datetime: optional datetime, end datetime of the window.
#                         If None, uses the last timestamp of the filtered data.  Default None
#         start_buffer_td: timedelta, the amount of time to include before the start_datetime when filtering data.
#                             Default DEFAULT_START_BUFFER_TD
#         end_buffer_td: float, the amount of time to include after the end_datetime when filtering data.
#                             Default DEFAULT_END_BUFFER_TD
#         gap_time_s: float, the minimum amount of seconds between data points that would indicate a gap.
#                     Default DEFAULT_GAP_TIME_S
#         apply_correction: bool, if True, update the timestamps in the data based on best station offset.  Default True
#         copy_edge_points: bool, if True, points on the edge of the data window are copies of the closest point
#                             within the window.  If False, edge points are interpolated from adjacent points.
#                             Default False
#         errors: DataWindowExceptions, class containing a list of all errors encountered by the data window.
#         stations: dictionary of Id:Station, the results of reading the data from input_directory
#         debug: bool, if True, outputs additional information during initialization. Default False
#     """
#
#     def __init__(
#             self,
#             input_dir: str,
#             structured_layout: bool = True,
#             start_datetime: Optional[dtu.datetime] = None,
#             end_datetime: Optional[dtu.datetime] = None,
#             start_buffer_td: timedelta = DEFAULT_START_BUFFER_TD,
#             end_buffer_td: timedelta = DEFAULT_END_BUFFER_TD,
#             gap_time_s: float = 0.25,
#             station_ids: Optional[Iterable[str]] = None,
#             extensions: Optional[Set[str]] = None,
#             api_versions: Optional[Set[io.ApiVersion]] = None,
#             apply_correction: bool = True,
#             copy_edge_points: bool = True,
#             debug: bool = False
#     ):
#         """
#         initialize the data window with params
#         :param input_dir: string, directory that contains the files to read data from
#         :param structured_layout: bool, if True, the input_directory contains specially named and organized
#                                     directories of data.  Default True
#         :param start_datetime: optional start datetime of the window. If None, uses the first timestamp of the
#                                 filtered data. Default None
#         :param end_datetime: optional end datetime of the window. If None, uses the last timestamp of the filtered
#                                 data.  Default None
#         :param start_buffer_td: the amount of time to include before the start_datetime when filtering data.
#                                 Default DEFAULT_START_BUFFER_TD
#         :param end_buffer_td: the amount of time to include after the end_datetime when filtering data.
#                                 Default DEFAULT_END_BUFFER_TD
#         :param gap_time_s: the minimum amount of seconds between data points that would indicate a gap.
#                             Default DEFAULT_GAP_TIME_S
#         :param station_ids: optional iterable of station ids to filter on. If empty or None, get any ids found in the
#                             input directory.  Default None
#         :param extensions: optional set of file extensions to filter on.  If None, get all data in the input directory.
#                             Default None
#         :param api_versions: optional set of api versions to filter on.  If None, get all data in the input directory.
#                                 Default None
#         :param apply_correction: if True, update the timestamps in the data based on best station offset.
#                                     Default True
#         :param copy_edge_points: if True, points on the edge of the data window are copies of the closest data point
#                                     within the window.  If False, edge points are interpolated from the adjacent points.
#                                     Default True.
#         :param debug: bool, if True, outputs warnings and additional information, default False
#         """
#
#         self.errors: DataWindowExceptions = DataWindowExceptions()
#         self.input_directory: str = input_dir
#         if start_datetime and end_datetime and (end_datetime <= start_datetime):
#             self.errors.append("Data Window cannot process end datetimes that are before start datetimes: "
#                                f"{end_datetime} <= {start_datetime}")
#         else:
#             self.structured_layout: bool = structured_layout
#             self.start_datetime: Optional[dtu.datetime] = start_datetime
#             self.end_datetime: Optional[dtu.datetime] = end_datetime
#             self.start_buffer_td: timedelta = start_buffer_td
#             self.end_buffer_td: timedelta = end_buffer_td
#             self.gap_time_s: float = gap_time_s
#             self.station_ids: Optional[Set[str]]
#             if station_ids:
#                 self.station_ids = set(station_ids)
#             else:
#                 self.station_ids = None
#             self.extensions: Optional[Set[str]] = extensions
#             self.api_versions: Optional[Set[io.ApiVersion]] = api_versions
#             self.apply_correction: bool = apply_correction
#             self.copy_edge_points: bool = copy_edge_points
#             self.debug: bool = debug
#             self.stations: Dict[str, Station] = {}
#             self.create_data_window()
#         self.errors.print()
#
#     @staticmethod
#     def from_config_file(file: str) -> "DataWindow":
#         """
#         Loads a configuration file to create the DataWindow
#         :param file: full path to config file
#         :return: a data window
#         """
#         return DataWindow.from_config(DataWindowConfig.from_path(file))
#
#     @staticmethod
#     def from_config(config: DataWindowConfig) -> "DataWindow":
#         """
#         Loads a configuration to create the DataWindow
#         :param config: DataWindow configuration object
#         :return: a data window
#         """
#         if config.start_year:
#             start_time = dtu.datetime(
#                 year=config.start_year,
#                 month=config.start_month,
#                 day=config.start_day,
#                 hour=config.start_hour,
#                 minute=config.start_minute,
#                 second=config.start_second,
#             )
#         else:
#             start_time = None
#         if config.end_year:
#             end_time = dtu.datetime(
#                 year=config.end_year,
#                 month=config.end_month,
#                 day=config.end_day,
#                 hour=config.end_hour,
#                 minute=config.end_minute,
#                 second=config.end_second,
#             )
#         else:
#             end_time = None
#         if config.api_versions:
#             api_versions = set([io.ApiVersion.from_str(v) for v in config.api_versions])
#         else:
#             api_versions = None
#         if config.extensions:
#             extensions = set(config.extensions)
#         else:
#             extensions = None
#         if config.station_ids:
#             station_ids = set(config.station_ids)
#         else:
#             station_ids = None
#         return DataWindow(
#             config.input_directory,
#             config.structured_layout,
#             start_time,
#             end_time,
#             dtu.timedelta(seconds=config.start_padding_seconds),
#             dtu.timedelta(seconds=config.end_padding_seconds),
#             config.drop_time_s,
#             station_ids,
#             extensions,
#             api_versions,
#             config.apply_correction,
#             config.debug,
#         )
#
#     @staticmethod
#     def deserialize(path: str) -> "DataWindow":
#         """
#         Decompresses and deserializes a DataWindow written to disk.
#         :param path: Path to the serialized and compressed data window.
#         :return: An instance of a DataWindow.
#         """
#         return io.deserialize_data_window(path)
#
#     def serialize(self, base_dir: str = ".", file_name: Optional[str] = None, compression_factor: int = 4) -> Path:
#         """
#         Serializes and compresses this DataWindow to a file.
#         :param base_dir: The base directory to write the serialized file to (default=.).
#         :param file_name: The optional file name. If None, a default filename with the following format is used:
#                           [start_ts]_[end_ts]_[num_stations].pkl.lz4
#         :param compression_factor: A value between 1 and 12. Higher values provide better compression, but take longer.
#                                    (default=4).
#         :return: The path to the written file.
#         """
#         return io.serialize_data_window(self, base_dir, file_name, compression_factor)
#
#     def to_json_file(self, base_dir: str = ".", file_name: Optional[str] = None,
#                      compression_format: str = "lz4") -> Path:
#         """
#         Converts the data window into a JSON file and writes it to disk.
#         :param base_dir: base directory to write the json file to.  Default . (local directory)
#         :param file_name: the optional file name.  Do not include a file extension.
#                             If None, a default file name is created using this format:
#                             [start_ts]_[end_ts]_[num_stations].json
#         :param compression_format: the type of compression to use on the data window object.  default lz4
#         :return: The path to the written file
#         """
#         return io.data_window_to_json_file(self, base_dir, file_name, compression_format)
#
#     def to_json(self, compressed_file_base_dir: str = ".", compressed_file_name: Optional[str] = None,
#                 compression_format: str = "lz4") -> str:
#         """
#         Converts the data window into a JSON string
#         :param compressed_file_base_dir: base directory to write the json file to.  Default . (local directory)
#         :param compressed_file_name: the optional file name.  Do not include a file extension.
#                                         If None, a default file name is created using this format:
#                                         [start_ts]_[end_ts]_[num_stations].[compression_format]
#         :param compression_format: the type of compression to use on the data window object.  default lz4
#         :return: The json string
#         """
#         return io.data_window_to_json(self, compressed_file_base_dir, compressed_file_name, compression_format)
#
#     @staticmethod
#     def from_json_file(path: str, start_dt: Optional[dtu.datetime] = None,
#                        end_dt: Optional[dtu.datetime] = None,
#                        station_ids: Optional[Iterable[str]] = None) -> Optional["DataWindow"]:
#         """
#         Reads a JSON file and checks if:
#             * The requested times are within the JSON file's times
#             * The requested stations are a subset of the JSON file's stations
#         :param path: the path to the JSON file to read
#         :param start_dt: the start datetime to check against.  if not given, assumes True.  default None
#         :param end_dt: the end datetime to check against.  if not given, assumes True.  default None
#         :param station_ids: the station ids to check against.  if not given, assumes True.  default None
#         :return: the data window if it suffices, otherwise None
#         """
#         return DataWindow.from_json_dict(io.json_file_to_data_window(path), start_dt, end_dt, station_ids)
#
#     @staticmethod
#     def from_json(json_str: str, start_dt: Optional[dtu.datetime] = None,
#                   end_dt: Optional[dtu.datetime] = None,
#                   station_ids: Optional[Iterable[str]] = None) -> Optional["DataWindow"]:
#         """
#         Reads a JSON string and checks if:
#             * The requested times are within the JSON file's times
#             * The requested stations are a subset of the JSON file's stations
#         :param json_str: the JSON to read
#         :param start_dt: the start datetime to check against.  if not given, assumes True.  default None
#         :param end_dt: the end datetime to check against.  if not given, assumes True.  default None
#         :param station_ids: the station ids to check against.  if not given, assumes True.  default None
#         :return: the data window if it suffices, otherwise None
#         """
#         return DataWindow.from_json_dict(io.json_to_data_window(json_str), start_dt, end_dt, station_ids)
#
#     @staticmethod
#     def from_json_dict(json_dict: Dict, start_dt: Optional[dtu.datetime] = None,
#                        end_dt: Optional[dtu.datetime] = None,
#                        station_ids: Optional[Iterable[str]] = None) -> Optional["DataWindow"]:
#         """
#         Reads a JSON string and checks if:
#             * The requested times are within the JSON file's times
#             * The requested stations are a subset of the JSON file's stations
#         :param json_dict: the dictionary to read
#         :param start_dt: the start datetime to check against.  if not given, assumes True.  default None
#         :param end_dt: the end datetime to check against.  if not given, assumes True.  default None
#         :param station_ids: the station ids to check against.  if not given, assumes True.  default None
#         :return: the data window if it suffices, otherwise None
#         """
#         if start_dt and json_dict["start_datetime"] > dtu.datetime_to_epoch_microseconds_utc(start_dt):
#             return None
#         if end_dt and json_dict["end_datetime"] < dtu.datetime_to_epoch_microseconds_utc(end_dt):
#             return None
#         if station_ids and not all(a in json_dict["station_ids"] for a in station_ids):
#             return None
#         if json_dict["compression_format"] == "lz4":
#             return DataWindow.deserialize(json_dict["file_path"])
#         else:
#             with open(json_dict["file_path"], 'rb') as fp:
#                 return pickle.load(fp)
#
#     def _has_time_window(self) -> bool:
#         """
#         Returns true if there is a start or end datetime in the settings
#         :return: True if start_datetime or end_datetime exists
#         """
#         return self.start_datetime is not None or self.end_datetime is not None
#
#     def get_station(self, station_id: str) -> Optional[Station]:
#         """
#         Get a single station from the data window
#         :param station_id: the id of the station to get
#         :return: A single station or None if the station cannot be found
#         """
#         if station_id in self.stations.keys():
#             return self.stations[station_id]
#         if self.debug:
#             print(f"Warning: Attempted to get station {station_id}, but that station is not in this data window!")
#         return None
#
#     def get_all_stations(self) -> List[Station]:
#         """
#         :return: all stations in the data window as a list
#         """
#         return list(self.stations.values())
#
#     def get_all_station_ids(self) -> List[str]:
#         """
#         :return: A list of all station ids with data
#         """
#         return list(self.stations.keys())
#
#     def check_valid_ids(self):
#         """
#         searches the data window station_ids for any ids not in the data collected
#         adds a message for each id requested but has no data to the errors object
#         """
#         for ids in self.station_ids:
#             if ids not in self.stations.keys() and self.debug:
#                 self.errors.append(f"WARNING: Requested {ids} but there is no data to read for that station")
#
#     def process_sensor(self, sensor: SensorData, station_id: str, start_date_timestamp: float,
#                        end_date_timestamp: float):
#         """
#         process a non audio sensor to fit within the data window.  Updates sensor in place, returns nothing.
#         :param sensor: sensor to process
#         :param station_id: station id
#         :param start_date_timestamp: start of data window
#         :param end_date_timestamp: end of data window
#         """
#         # calculate the sensor's sample interval, std sample interval and sample rate of all data
#         sensor.organize_and_update_stats()
#         # get only the timestamps between the start and end timestamps
#         df_timestamps = sensor.data_timestamps()
#         if len(df_timestamps) > 0:
#             before_start = np.where(df_timestamps < start_date_timestamp)[0]
#             after_end = np.where(end_date_timestamp <= df_timestamps)[0]
#             if len(before_start) > 0:
#                 last_before_start = before_start[-1]
#                 start_index = last_before_start + 1
#             else:
#                 last_before_start = None
#                 start_index = 0
#             if len(after_end) > 0:
#                 first_after_end = after_end[0]
#                 end_index = first_after_end
#             else:
#                 first_after_end = None
#                 end_index = sensor.num_samples()
#             # check if all the samples have been cut off
#             if end_index < start_index or start_index >= len(df_timestamps):
#                 if last_before_start is not None and first_after_end is None:
#                     sensor.data_df = sensor.data_df.iloc[[last_before_start]]
#                     sensor.data_df["timestamps"] = [start_date_timestamp]
#                 elif last_before_start is None and first_after_end is not None:
#                     sensor.data_df = sensor.data_df.iloc[[first_after_end]]
#                     sensor.data_df["timestamps"] = [end_date_timestamp]
#                 elif last_before_start is not None and first_after_end is not None:
#                     sensor.data_df = sensor.interpolate(start_date_timestamp,
#                                                         last_before_start,
#                                                         first_after_end - last_before_start,
#                                                         ).to_frame().T
#                 elif self.debug:
#                     self.errors.append(
#                         f"WARNING: Data window for {station_id} {sensor.type.name} "
#                         f"sensor has truncated all data points"
#                     )
#             else:
#                 # update existing points immediately beyond the edge to be at the edge using interpolation.
#                 if last_before_start is not None:
#                     sensor.data_df.iloc[last_before_start] = sensor.interpolate(start_date_timestamp,
#                                                                                 last_before_start,
#                                                                                 1)
#                     start_index -= 1
#                 else:
#                     sensor.data_df = pd.concat([sensor.interpolate(start_date_timestamp, start_index).to_frame().T,
#                                                 sensor.data_df])
#                     end_index += 1
#                 if first_after_end is not None:
#                     sensor.data_df.iloc[first_after_end] = sensor.interpolate(end_date_timestamp,
#                                                                               first_after_end,
#                                                                               -1)
#                 else:
#                     sensor.data_df = pd.concat([sensor.data_df,
#                                                 sensor.interpolate(end_date_timestamp, end_index-1).to_frame().T])
#                 end_index += 1
#                 sensor.data_df = sensor.data_df.iloc[start_index:end_index].reset_index(
#                     drop=True
#                 )
#                 if sensor.is_sample_interval_invalid():
#                     if self.debug:
#                         self.errors.append(
#                             f"WARNING: Cannot fill gaps or pad {station_id} {sensor.type.name} "
#                             f"sensor; it has undefined sample interval and sample rate!"
#                         )
#                 # else:  # GAP FILL and PAD DATA
#                 #     sample_interval_micros = dtu.seconds_to_microseconds(sensor.sample_interval_s)
#                 #     sensor.data_df = gpu.fill_gaps(sensor.data_df, [], sample_interval_micros=sample_interval_micros)
#         elif self.debug:
#             self.errors.append(f"WARNING: Data window for {station_id} {sensor.type.name} sensor has no data points!")
#
#     def process_audio_sensor(self, station: Station, start_date_timestamp: float, end_date_timestamp: float):
#         sensor = station.audio_sensor()
#         df_timestamps = sensor.data_timestamps()
#         if len(df_timestamps) > 0:
#             before_start = np.where(df_timestamps < start_date_timestamp)[0]
#             after_end = np.where(end_date_timestamp <= df_timestamps)[0]
#             if len(before_start) > 0:
#                 start_index = before_start[-1] + 1
#             else:
#                 start_index = 0
#             if len(after_end) > 0:
#                 end_index = after_end[0] - 1
#             else:
#                 end_index = sensor.num_samples() - 1
#             # check if all the samples have been cut off
#             if end_index < start_index and self.debug:
#                 self.errors.append(f"WARNING: Data window for {station.id} Audio sensor has truncated all data points")
#             else:
#                 sensor.data_df = sensor.data_df.iloc[start_index:end_index+1].reset_index(
#                     drop=True
#                 )
#                 if sensor.is_sample_interval_invalid():
#                     if self.debug:
#                         self.errors.append(
#                             f"WARNING: Cannot fill gaps or pad {station.id} Audio "
#                             f"sensor; it has undefined sample interval and sample rate!"
#                         )
#                 else:  # PAD DATA
#                     sample_interval_micros = dtu.seconds_to_microseconds(sensor.sample_interval_s)
#                     sensor.data_df = gpu.pad_data(
#                         start_date_timestamp,
#                         end_date_timestamp,
#                         sensor.data_df,
#                         sample_interval_micros,
#                     )
#         elif self.debug:
#             self.errors.append(f"WARNING: Data window for {station.id} Audio sensor has no data points!")
#
#     def create_window_in_sensors(
#             self, station: Station, start_date_timestamp: float, end_date_timestamp: float
#     ):
#         """
#         truncate the sensors in the station to only contain data from start_date_timestamp to end_date_timestamp
#         returns nothing, updates the station in place
#         :param station: station object to truncate sensors of
#         :param start_date_timestamp: timestamp in microseconds since epoch UTC of start of window
#         :param end_date_timestamp: timestamp in microseconds since epoch UTC of end of window
#         """
#         self.process_audio_sensor(station, start_date_timestamp, end_date_timestamp)
#         for sensor in station.data:
#             if sensor.type != SensorType.AUDIO:
#                 self.process_sensor(sensor, station.id, station.audio_sensor().first_data_timestamp(),
#                                     station.audio_sensor().last_data_timestamp())
#         # recalculate metadata
#         new_meta = [meta for meta in station.packet_metadata
#                     if meta.packet_start_mach_timestamp < end_date_timestamp and
#                     meta.packet_end_mach_timestamp > start_date_timestamp]
#         station.packet_metadata = new_meta
#         station.first_data_timestamp = station.audio_sensor().first_data_timestamp()
#         station.last_data_timestamp = station.audio_sensor().data_timestamps()[-1]
#
#     def create_data_window(self, pool: Optional[multiprocessing.pool.Pool] = None):
#         """
#         updates the data window to contain only the data within the window parameters
#         stations without audio or any data outside the window are removed
#         """
#
#         # Let's create and manage a single pool of workers that we can utilize throughout
#         # the instantiation of the data window.
#         _pool: multiprocessing.pool.Pool = multiprocessing.Pool() if pool is None else pool
#
#         ids_to_pop = []
#         r_f = io.ReadFilter()
#         if self.start_datetime:
#             r_f.with_start_dt(self.start_datetime)
#         if self.end_datetime:
#             r_f.with_end_dt(self.end_datetime)
#         if self.station_ids:
#             r_f.with_station_ids(self.station_ids)
#         if self.extensions:
#             r_f.with_extensions(self.extensions)
#         else:
#             self.extensions = r_f.extensions
#         if self.api_versions:
#             r_f.with_api_versions(self.api_versions)
#         else:
#             self.api_versions = r_f.api_versions
#         if self.start_buffer_td:
#             r_f.with_start_dt_buf(self.start_buffer_td)
#         else:
#             self.start_buffer_td = r_f.start_dt_buf
#         if self.end_buffer_td:
#             r_f.with_end_dt_buf(self.end_buffer_td)
#         else:
#             self.end_buffer_td = r_f.end_dt_buf
#         # get the data to convert into a window
#         stations = ApiReader(
#             self.input_directory,
#             self.structured_layout,
#             r_f,
#             self.debug,
#             pool=_pool,
#         ).get_stations()
#
#         # Parallel update
#         # Apply timing correction in parallel by station
#         if self.apply_correction:
#             # stations = _pool.map(Station.update_timestamps, stations)
#             stations = list(maybe_parallel_map(_pool, Station.update_timestamps, iter(stations), chunk_size=1))
#
#         for station in stations:
#             if station.id:
#                 ids_to_pop = check_audio_data(station, ids_to_pop, self.debug)
#                 if station.id not in ids_to_pop:
#                     # set the window start and end if they were specified, otherwise use the bounds of the data
#                     if self.start_datetime:
#                         start_datetime = dtu.datetime_to_epoch_microseconds_utc(self.start_datetime)
#                     else:
#                         start_datetime = station.first_data_timestamp
#                     if self.end_datetime:
#                         end_datetime = dtu.datetime_to_epoch_microseconds_utc(self.end_datetime)
#                     else:
#                         end_datetime = station.last_data_timestamp
#                     # TRUNCATE!
#                     self.create_window_in_sensors(station, start_datetime, end_datetime)
#                     ids_to_pop = check_audio_data(station, ids_to_pop, self.debug)
#                     if station.id not in ids_to_pop:
#                         self.stations[station.id] = station
#
#         # update remaining data window values if they're still default
#         if not self.station_ids or len(self.station_ids) == 0:
#             self.station_ids = set(self.stations.keys())
#         # remove station ids without audio data
#         for ids in ids_to_pop:
#             self.stations.pop(ids)
#         if not self.start_datetime and len(self.stations.keys()) > 0:
#             self.start_datetime = dtu.datetime_from_epoch_microseconds_utc(
#                 np.min([t.first_data_timestamp for t in self.stations.values()]))
#         if not self.end_datetime and len(self.stations.keys()) > 0:
#             self.end_datetime = dtu.datetime_from_epoch_microseconds_utc(
#                 np.max([t.last_data_timestamp for t in self.stations.values()]))
#
#         # check for stations without data
#         self.check_valid_ids()
#
#         # If the pool was created by this function, then it needs to managed by this function.
#         if pool is None:
#             _pool.close()
#
#
# def check_audio_data(
#         station: Station, ids_to_remove: List[str], debug: bool = False
# ) -> List[str]:
#     """
#     check if the station has audio data; if it does not, update the list of stations to remove
#
#     :param station: station object to check for audio data
#     :param ids_to_remove: list of station ids to remove from the data window
#     :param debug: if True, output warning message, default False
#     :return: an updated list of station ids to remove from the data window
#     """
#     if not station.has_audio_sensor():
#         if debug:
#             print(f"WARNING: {station.id} doesn't have any audio data to read")
#         ids_to_remove.append(station.id)
#     return ids_to_remove
