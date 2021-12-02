"""
This module creates specific time-bounded segments of data for users
combines the base data files into a single composite object based on the user parameters
"""
from pathlib import Path
from typing import Optional, Set, List, Dict, Iterable
from datetime import timedelta

import multiprocessing
import multiprocessing.pool
import pickle
import numpy as np

import redvox
from redvox.common import date_time_utils as dtu
from redvox.common import io
from redvox.common import data_window_io as dw_io
from redvox.common.parallel_utils import maybe_parallel_map
from redvox.common.station_old import Station
from redvox.common.sensor_data_old import SensorType, SensorData
from redvox.common.api_reader import ApiReader
from redvox.common.data_window_configuration_old import DataWindowConfig
from redvox.common import gap_and_pad_utils_old as gpu
from redvox.common.errors import RedVoxExceptions

DEFAULT_START_BUFFER_TD: timedelta = timedelta(minutes=2.0)  # default padding to start time of data
DEFAULT_END_BUFFER_TD: timedelta = timedelta(minutes=2.0)  # default padding to end time of data
# minimum default length of time in seconds for data to be off by to be considered suspicious
DATA_DROP_DURATION_S: float = 0.2


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
                        If None, uses the last timestamp of the filtered data + 1.  Default None
        start_buffer_td: timedelta, the amount of time to include before the start_datetime when filtering data.
                            Negative values are converted to 0.  Default DEFAULT_START_BUFFER_TD (2 minutes)
        end_buffer_td: timedelta, the amount of time to include after the end_datetime when filtering data.
                            Negative values are converted to 0.  Default DEFAULT_END_BUFFER_TD (2 minutes)
        drop_time_s: float, the minimum amount of seconds between data files that would indicate a gap.
                     Negative values are converted to default value.  Default DATA_DROP_DURATION_S (0.2 seconds)
        apply_correction: bool, if True, update the timestamps in the data based on best station offset.  Default True
        use_model_correction: bool, if True, use the offset model's correction functions, otherwise use the best
                                offset.  Default True
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
            debug: bool = False,
            use_model_correction: bool = True,
    ):
        """
        Initialize the DataWindow

        :param input_dir: directory that contains the files to read data from.  REQUIRED
        :param structured_layout: if True, the input_directory contains specially named and organized directories of
                                    data.  Default True
        :param start_datetime: optional start datetime of the window.  If None, uses the first timestamp of the
                                filtered data.  Default None
        :param end_datetime: optional non-inclusive end datetime of the window.  If None, uses the last timestamp of
                                the filtered data + 1.  Default None
        :param start_buffer_td: the amount of time to include before the start_datetime when filtering data.
                                Negative values are converted to 0.  Default 2 minutes
        :param end_buffer_td: the amount of time to include after the end_datetime when filtering data.
                                Negative values are converted to 0.  Default 2 minutes
        :param station_ids: optional station ids to filter on. If empty or None, get any ids found in the input
                            directory.  Default None
        :param drop_time_s: the minimum amount of seconds between data files that would indicate a gap.
                            Negative values are converted to default value.  Default 0.2 seconds
        :param extensions: optional set of file extensions to filter on.  If None, gets as much data as it can in the
                            input directory.  Default None
        :param api_versions: optional set of api versions to filter on.  If None, get as much data as it can in
                                the input directory.  Default None
        :param apply_correction: if True, update the timestamps in the data based on best station offset.  Default True
        :param copy_edge_points: Determines how new points are created. Valid values are DataPointCreationMode.NAN,
                                    DataPointCreationMode.COPY, and DataPointCreationMode.INTERPOLATE.  Default COPY
        :param use_model_correction: if True, use the offset model's correction functions, otherwise use the best
                                        offset.  Default True
        :param debug: if True, outputs additional information during initialization. Default False
        """
        self.errors = RedVoxExceptions("DataWindow")
        self.input_directory: str = input_dir
        self.structured_layout: bool = structured_layout
        self.start_datetime: Optional[dtu.datetime] = start_datetime
        self.end_datetime: Optional[dtu.datetime] = end_datetime
        self.start_buffer_td: timedelta = start_buffer_td if start_buffer_td > timedelta(seconds=0) \
            else timedelta(seconds=0)
        self.end_buffer_td: timedelta = end_buffer_td if end_buffer_td > timedelta(seconds=0) else timedelta(seconds=0)
        self.drop_time_s: float = drop_time_s if drop_time_s > 0 else DATA_DROP_DURATION_S
        self.station_ids: Optional[Set[str]] = set(station_ids) if station_ids else None
        self.extensions: Optional[Set[str]] = extensions
        self.api_versions: Optional[Set[io.ApiVersion]] = api_versions
        self.apply_correction: bool = apply_correction
        self.copy_edge_points = copy_edge_points
        self.use_model_correction = use_model_correction
        self.sdk_version: str = redvox.VERSION
        self.debug: bool = debug
        self.stations: List[Station] = []
        if start_datetime and end_datetime and (end_datetime <= start_datetime):
            self.errors.append("DataWindow will not work when end datetime is before or equal to start datetime.\n"
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
            config.drop_time_seconds,
            station_ids,
            extensions,
            api_versions,
            config.apply_correction,
            gpu.DataPointCreationMode[config.edge_points_mode],
            config.debug,
            config.use_model_correction,
        )

    @staticmethod
    def deserialize(path: str) -> "DataWindow":
        """
        Decompresses and deserializes a DataWindow written to disk.

        :param path: Path to the serialized and compressed data window.
        :return: An instance of a DataWindow.
        """
        return dw_io.deserialize_data_window_old(path)

    def serialize(self, base_dir: str = ".", file_name: Optional[str] = None, compression_factor: int = 4) -> Path:
        """
        Serializes and compresses this DataWindow to a file.

        :param base_dir: The base directory to write the serialized file to (default=.).
        :param file_name: The optional file name. If None, a default filename with the following format is used:
                          [start_ts]_[end_ts]_[num_stations].pkl.lz4
        :param compression_factor: A value between 1 and 12. Higher values provide better compression, but take
        longer. (default=4).
        :return: The path to the written file.
        """
        return dw_io.serialize_data_window_old(self, base_dir, file_name, compression_factor)

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
        return dw_io.data_window_to_json_file_old(self, base_dir, file_name, compression_format)

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
        return dw_io.data_window_to_json_old(self, compressed_file_base_dir, compressed_file_name, compression_format)

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
            dw_io.json_file_to_data_window_old(base_dir, file_name), dw_base_dir, start_dt, end_dt, station_ids)

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
        return DataWindow.from_json_dict(dw_io.json_to_dict(json_str), dw_base_dir,
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
            self.errors.append(f"Attempted to get station {station_id}, "
                               f"but that station is not in this data window!")
        return None

    def _add_sensor_to_window(self, station: Station):
        self.errors.extend_error(station.errors)
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
        r_f.with_start_dt_buf(self.start_buffer_td)
        r_f.with_end_dt_buf(self.end_buffer_td)

        # get the data to convert into a window
        a_r = ApiReader(self.input_directory, self.structured_layout, r_f, pool=_pool)

        self.errors.extend_error(a_r.errors)

        if not self.station_ids:
            self.station_ids = a_r.index_summary.station_ids()
        # Parallel update
        # Apply timing correction in parallel by station
        sts = a_r.get_stations()
        if not self.use_model_correction:
            for tss in sts:
                tss.use_model_correction = self.use_model_correction
        if self.apply_correction:
            for st in maybe_parallel_map(_pool, Station.update_timestamps,
                                         iter(sts), chunk_size=1):
                self._add_sensor_to_window(st)
        else:
            [self._add_sensor_to_window(s) for s in sts]
        # check for stations without data
        self._check_for_audio()
        self._check_valid_ids()

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
        if len(remove) > 0:
            self.stations = [s for s in self.stations if s.id not in remove]
            self.station_ids = [s for s in self.station_ids if s not in remove]

    def _check_valid_ids(self):
        """
        if there are stations, searches the station_ids for any ids not in the data collected
        and creates an error message for each id requested but has no data
        if there are no stations, creates a single error message declaring no data found
        """
        if len(self.stations) < 1:
            if len(self.station_ids) > 1:
                add_ids = f"for all stations {self.station_ids} "
            else:
                add_ids = ""
            self.errors.append(f"No data matching criteria {add_ids}in {self.input_directory}"
                               f"\nPlease adjust parameters of DataWindow")
        elif len(self.station_ids) > 0:
            for ids in self.station_ids:
                if ids.zfill(10) not in [i.id for i in self.stations]:
                    self.errors.append(
                        f"Requested {ids} but there is no data to read for that station"
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
        :param start_date_timestamp: start of data window according to data
        :param end_date_timestamp: end of data window according to data
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
                    self.errors.append(f"Data window for {station_id} "
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
                        f"Data window for {station_id} {sensor.type.name} "
                        f"sensor has truncated all data points"
                    )
            else:
                sensor.data_df = sensor.data_df.iloc[start_index:end_index].reset_index(
                    drop=True
                )
                # if sensor is audio or location, we want nan'd edge points
                if sensor.type in [SensorType.LOCATION, SensorType.AUDIO]:
                    new_point_mode = gpu.DataPointCreationMode["NAN"]
                else:
                    new_point_mode = self.copy_edge_points
                # add in the data points at the edges of the window if there are defined start and/or end times
                if not is_audio:
                    end_sample_interval = end_date_timestamp - sensor.last_data_timestamp()
                    end_samples_to_add = 1
                    start_sample_interval = start_date_timestamp - sensor.first_data_timestamp()
                    start_samples_to_add = 1
                else:
                    end_sample_interval = dtu.seconds_to_microseconds(sensor.sample_interval_s)
                    start_sample_interval = -end_sample_interval
                    if self.end_datetime:
                        end_samples_to_add = int((dtu.datetime_to_epoch_microseconds_utc(self.end_datetime)
                                                  - sensor.last_data_timestamp()) / end_sample_interval)
                    else:
                        end_samples_to_add = 0
                    if self.start_datetime:
                        start_samples_to_add = int((sensor.first_data_timestamp() -
                                                    dtu.datetime_to_epoch_microseconds_utc(self.start_datetime))
                                                   / end_sample_interval)
                    else:
                        start_samples_to_add = 0
                # add to end
                sensor.data_df = gpu.add_data_points_to_df(dataframe=sensor.data_df,
                                                           start_index=sensor.num_samples() - 1,
                                                           sample_interval_micros=end_sample_interval,
                                                           num_samples_to_add=end_samples_to_add,
                                                           point_creation_mode=new_point_mode)
                # add to begin
                sensor.data_df = gpu.add_data_points_to_df(dataframe=sensor.data_df, start_index=0,
                                                           sample_interval_micros=start_sample_interval,
                                                           num_samples_to_add=start_samples_to_add,
                                                           point_creation_mode=new_point_mode)
                sensor.data_df.sort_values("timestamps", inplace=True, ignore_index=True)
        else:
            self.errors.append(f"Data window for {station_id} {sensor.type.name} "
                               f"sensor has no data points!")

    def print_errors(self):
        """
        prints errors to screen
        """
        self.errors.print()
