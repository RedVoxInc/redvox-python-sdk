"""
This module creates specific time-bounded segments of data for users
combines the base data files into a single composite object based on the user parameters
"""
from pathlib import Path
from typing import Optional, Set, List, Dict, Iterable, Tuple
from datetime import timedelta
import tempfile
from glob import glob
import os
import json

import multiprocessing
import multiprocessing.pool
import pickle
import numpy as np
import pyarrow as pa

import redvox
from redvox.common import date_time_utils as dtu
from redvox.common.date_time_utils import (
    datetime_to_epoch_microseconds_utc as us_dt,
)
from redvox.common import io
from redvox.common import data_window_io as dw_io
from redvox.common.parallel_utils import maybe_parallel_map
from redvox.common.station_wpa import StationPa
from redvox.common.sensor_data_with_pyarrow import SensorType, SensorDataPa
from redvox.common.api_reader import ApiReader
from redvox.common.data_window_configuration import DataWindowConfig
from redvox.common import gap_and_pad_utils_wpa as gpu
from redvox.common.errors import RedVoxExceptions

DEFAULT_START_BUFFER_TD: timedelta = timedelta(minutes=2.0)  # default padding to start time of data
DEFAULT_END_BUFFER_TD: timedelta = timedelta(minutes=2.0)  # default padding to end time of data
# minimum default length of time in seconds for data to be off by to be considered suspicious
DATA_DROP_DURATION_S: float = 0.2


class DataWindowResultLocation:
    """
    The data source, latitude, longitude, altitude and their standard deviations
    Properties:
        provider: string, source of the location data (i.e. GPS or NETWORK), default UNKNOWN
        latitude: float, best estimate of latitude, default np.nan
        latitude_std: float, standard deviation of best estimate of latitude, default np.nan
        longitude: float, best estimate of longitude, default np.nan
        longitude_std: float, standard deviation of best estimate of longitude, default np.nan
        altitude: float, best estimate of altitude, default np.nan
        altitude_std: float, standard deviation of best estimate of altitude, default np.nan
    """
    def __init__(self,
                 provider: str = "UNKNOWN",
                 lat: float = np.nan,
                 lat_std: float = np.nan,
                 lon: float = np.nan,
                 lon_std: float = np.nan,
                 alt: float = np.nan,
                 alt_std: float = np.nan):
        self.provider = provider
        self.latitude = lat
        self.longitude = lon
        self.altitude = alt
        self.latitude_std = lat_std
        self.longitude_std = lon_std
        self.altitude_std = alt_std

    def as_dict(self) -> Dict:
        """
        :return: self as dict
        """
        return {
            "provider": self.provider,
            "latitude": self.latitude,
            "latitude_std": self.latitude_std,
            "longitude": self.longitude,
            "longitude_std": self.longitude_std,
            "altitude": self.altitude,
            "altitude_std": self.altitude_std
        }


class DataWindowResult:
    """
    Holds the data for a given data window; used to find the data and to provide
    enough metadata to get an idea of what is contained in the window
    Properties:
        event_name: string, identifier for the event
        files_dir: string, directory where all the data files are
        start_time: datetime, start of the window
        end_time: datetime, end of the window
        event_origin: Tuple of floats, lat, lon, altitude of the origin
        event_radius: float, event radius in meters
        datawindow_metadata: dict, DataWindow metadata including original request
        stations:
            id: string, id of station
            is_time_corrected: bool, True if station's timestamps are updated.  default False
            best_latency: float, best latency of station in microseconds.  default np.nan
            best_offset: float, best offset of station in microseconds.  default 0
            location: Tuple of string, floats, location provider, lat, lon, alt and std devs for each
            gaps: List of Tuple of floats, timestamps of data points on the edge of data gaps.
            sensor: (values unique to a sensor are noted)
                name: str, name of sensor
                sample_rate (audio only): float, sample rate of sensor
    """
    def __init__(self,
                 event_name: str,
                 files_dir: str,
                 start_time: dtu.datetime,
                 end_time: dtu.datetime,
                 event_origin: DataWindowResultLocation,
                 event_radius: float,
                 data_window_meta: Dict,
                 stations: List[StationPa]):
        """
        initialize the result of a DataWindow

        :param event_name: the name of the event
        :param files_dir: the directory where the data files exist
        :param start_time: the start of the window in UTC
        :param end_time: the end of the window in UTC
        :param event_origin: the origin location of the event of interest
        :param event_radius: the effective radius of the event
        :param data_window_meta: metadata for DataWindow as a dictionary
        :param stations: the stations that recorded the event
        """
        self.event_name = event_name
        self.files_dir = files_dir
        self.start_time = start_time
        self.end_time = end_time
        self.event_origin = event_origin
        self.event_radius = event_radius
        self.datawindow_metadata = data_window_meta
        self.stations = stations

    def to_json(self) -> json:
        """
        :return: DataWindow as JSON
        """
        d: dict = {
            "event_name": self.event_name,
            "files_dir": self.files_dir,
            "start_time": us_dt(self.start_time),
            "end_time": us_dt(self.end_time),
            "event_origin": self.event_origin.as_dict(),
            "event_radius": self.event_radius,
            "datawindow_metadata": self.datawindow_metadata,
            "stations": [s.default_station_json_file_name() for s in self.stations]
        }
        return json.dumps(d)

    # todo: load json of datawindow, meaning datawindow has to set itself up first

    def write(self) -> Path:
        """
        write the data to directory self.files_dir
        """
        os.makedirs(self.files_dir, exist_ok=True)
        for s in self.stations:
            s.to_json_file()
        file_path: Path = Path(self.files_dir).joinpath(self.event_name + "_dw.json")
        with open(file_path, "w") as f:
            f.write(self.to_json())
            return file_path.resolve(False)


class DataWindowConfigWpa:
    """
    Properties:
        structured_layout: bool, if True, the input_directory contains specially named and organized
        directories of data.  Default True

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

        station_ids: optional set of strings, representing the station ids to filter on.
        If empty or None, get any ids found in the input directory.  Default None

        extensions: optional set of strings, representing file extensions to filter on.
        If None, gets as much data as it can in the input directory.  Default None

        api_versions: optional set of ApiVersions, representing api versions to filter on.
        If None, get as much data as it can in the input directory.  Default None

        apply_correction: bool, if True, update the timestamps in the data based on best station offset.  Default True

        copy_edge_points: enumeration of DataPointCreationMode.  Determines how new points are created.
        Valid values are NAN, COPY, and INTERPOLATE.  Default COPY

        use_model_correction: bool, if True, use the offset model's correction functions, otherwise use the best
        offset.  Default True
    """
    def __init__(
            self,
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
            use_model_correction: bool = True,
    ):
        self.structured_layout: bool = structured_layout
        self.start_datetime: Optional[dtu.datetime] = start_datetime
        self.end_datetime: Optional[dtu.datetime] = end_datetime
        self.start_buffer_td: timedelta = start_buffer_td if start_buffer_td > timedelta(seconds=0) \
            else timedelta(seconds=0)
        self.end_buffer_td: timedelta = end_buffer_td if end_buffer_td > timedelta(seconds=0) \
            else timedelta(seconds=0)
        self.drop_time_s: float = drop_time_s if drop_time_s > 0 else DATA_DROP_DURATION_S
        self.station_ids: Optional[Set[str]] = station_ids
        self.extensions: Optional[Set[str]] = extensions
        self.api_versions: Optional[Set[io.ApiVersion]] = api_versions
        self.apply_correction: bool = apply_correction
        self.use_model_correction = use_model_correction
        self.copy_edge_points = copy_edge_points

    def as_dict(self) -> dict:
        return {"structured_layout": self.structured_layout,
                "start_datetime": us_dt(self.start_datetime),
                "end_datetime": us_dt(self.end_datetime),
                "start_buffer_td": self.start_buffer_td.total_seconds(),
                "end_buffer_td": self.end_buffer_td.total_seconds(),
                "drop_time_s": self.drop_time_s,
                "station_ids": list(self.station_ids) if self.station_ids else [],
                "extensions": list(self.extensions) if self.extensions else [],
                "api_versions": [a_v.value for a_v in self.api_versions],
                "apply_correction": self.apply_correction,
                "use_model_correction": self.use_model_correction,
                "copy_edge_points": self.copy_edge_points.value
                }


class DataWindowArrow:
    """
    Holds the data for a given time window; adds interpolated timestamps to fill gaps and pad start and end values

    Properties:
        input_directory: string, directory that contains the files to read data from.  REQUIRED

        config: optional DataWindowConfigWpa with information on how to construct data window from
        Redvox (.rdvx*) files.  Default None

        sdk_version: str, the version of the Redvox SDK used to create the data window

        station_out_dir: str, output directory for station parquet files.  Default "" (current directory)

        save_station_files: bool, if True, save the station parquet files, otherwise delete them when finished.
        Default False

        errors: DataWindowExceptions, class containing a list of all errors encountered by the data window.

        debug: bool, if True, outputs additional information during initialization. Default False

    Protected:
        _stations: List of Stations that belong to the DataWindow
    """
    def __init__(
            self,
            input_dir: str,
            config: Optional[DataWindowConfigWpa] = None,
            station_out_dir: str = ".",
            save_station_files: bool = False,
            debug: bool = False,
    ):
        """
        Initialize the DataWindow

        :param input_dir: directory that contains the files to read data from.  REQUIRED
        :param config: Optional DataWindowConfigWpa which describes how to extract data from Redvox files.
                        if None, assumes we're loading from an existing data window object in input_dir.  Default None
        :param station_out_dir: output directory for station parquet files.  Default "." (current directory)
        :param save_station_files: if True, save the station parquet files, otherwise delete them when finished.
                                    Default False
        :param debug: if True, outputs additional information during initialization. Default False
        """
        self.input_directory: str = input_dir
        self.debug: bool = debug
        self.errors = RedVoxExceptions("DataWindow")
        self._stations: List[StationPa] = []
        self.save_station_files: bool = save_station_files
        if self.save_station_files:
            self.station_out_dir: str = station_out_dir
            self._temp_dir = None
        else:
            self._temp_dir = tempfile.TemporaryDirectory()
            self.station_out_dir = self._temp_dir.name
        if config:
            self.config = config
            self.sdk_version: str = redvox.VERSION
            self.data_window_results = None
            if config.start_datetime and config.end_datetime and (config.end_datetime <= config.start_datetime):
                self.errors.append("DataWindow will not work when end datetime is before or equal to start datetime.\n"
                                   f"Your times: {config.end_datetime} <= {config.start_datetime}")
            else:
                self.create_data_window()
        else:
            self.config = None
        if debug:
            self.print_errors()

    def __del__(self):
        if self._temp_dir:
            self._temp_dir.cleanup()

    def from_dir(self, input_dir: str):
        filelist = glob(os.path.join(input_dir, "*"))
        for f in filelist:
            self._stations.append(StationPa.create_from_dir(f, self.config.use_model_correction,
                                                            self.station_out_dir, self.save_station_files))

    @staticmethod
    def from_config_file(file: str) -> "DataWindowArrow":
        """
        Loads a configuration file to create the DataWindow

        :param file: full path to config file
        :return: a data window
        """
        return DataWindowArrow.from_config(DataWindowConfig.from_path(file))

    @staticmethod
    def from_config(config: DataWindowConfig) -> "DataWindowArrow":
        """
        Loads a configuration to create the DataWindow

        :param config: DataWindow configuration object
        :return: a data window
        """
        dwconfig = DataWindowConfigWpa()
        if config.start_year:
            dwconfig.start_time = dtu.datetime(
                year=config.start_year,
                month=config.start_month,
                day=config.start_day,
                hour=config.start_hour,
                minute=config.start_minute,
                second=config.start_second,
            )
        if config.end_year:
            dwconfig.end_time = dtu.datetime(
                year=config.end_year,
                month=config.end_month,
                day=config.end_day,
                hour=config.end_hour,
                minute=config.end_minute,
                second=config.end_second,
            )
        if config.api_versions:
            dwconfig.api_versions = set([io.ApiVersion.from_str(v) for v in config.api_versions])
        if config.extensions:
            dwconfig.extensions = set(config.extensions)
        if config.station_ids:
            dwconfig.station_ids = set(config.station_ids)
        if config.edge_points_mode not in gpu.DataPointCreationMode.list_names():
            dwconfig.edge_points_mode = "COPY"
        return DataWindowArrow(
            config.input_directory,
            dwconfig,
            # config.station_out
            # config.save_files
            debug=config.debug
        )

    def as_dict(self) -> Dict:
        return {"input_directory": self.input_directory,
                "config": self.config.as_dict(),
                "debug": self.debug,
                "errors": self.errors.as_dict(),
                "sdk_version": self.sdk_version,
                "save_station_files": self.save_station_files,
                "station_out_dir": "" if self._temp_dir else self.station_out_dir
                }

    def create_window_results(self, event_name: str, files_dir: str, event_location: DataWindowResultLocation,
                              event_radius: float) -> DataWindowResult:
        """
        create a DataWindowResult from a DataWindow

        :param event_name: name of the event
        :param files_dir: path to directory where all files will be written to
        :param event_location: coordinates of the source
        :param event_radius: radius of the event area
        :return: Summarized DataWindow object, with information written to files_dir
        """
        return DataWindowResult(event_name, files_dir, dtu.datetime_from_epoch_microseconds_utc(self.get_start_date()),
                                dtu.datetime_from_epoch_microseconds_utc(self.get_end_date()),
                                event_location, event_radius, self.as_dict(), self._stations)

    @staticmethod
    def deserialize(path: str) -> "DataWindowArrow":
        """
        Decompresses and deserializes a DataWindow written to disk.

        :param path: Path to the serialized and compressed data window.
        :return: An instance of a DataWindow.
        """
        return dw_io.deserialize_data_window(path)

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
        return dw_io.serialize_data_window(self, base_dir, file_name, compression_factor)

    def to_json_file(self, event_name: str, files_dir: str, event_location: DataWindowResultLocation,
                     event_radius: float) -> Path:
        """
        Converts the data window metadata into a JSON file and compresses the data window and writes it to disk.

        :param event_name: name of the event
        :param files_dir: path to directory where all files will be written to
        :param event_location: coordinates of the source
        :param event_radius: radius of the event area
        :return: The path to the written file
        """
        return self.create_window_results(event_name, files_dir, event_location, event_radius).write()
        # return dw_io.data_window_to_json_file(self, base_dir, file_name, compression_format)

    def to_json(self, event_name: str, files_dir: str, event_location: DataWindowResultLocation,
                event_radius: float) -> str:
        """
        Converts the data window metadata into a JSON string, then compresses the data window and writes it to disk.

        :param event_name: name of the event
        :param files_dir: path to directory where all files will be written to
        :param event_location: coordinates of the source
        :param event_radius: radius of the event area
        :return: The json string
        """
        return self.create_window_results(event_name, files_dir, event_location, event_radius).to_json()
        # return dw_io.data_window_to_json(self, compressed_file_base_dir, compressed_file_name, compression_format)

    @staticmethod
    def from_json_file(file_path: str,
                       # base_dir: str, file_name: str,
                       # dw_base_dir: Optional[str] = None,
                       # start_dt: Optional[dtu.datetime] = None,
                       # end_dt: Optional[dtu.datetime] = None,
                       # station_ids: Optional[Iterable[str]] = None
                       ) -> Optional["DataWindowArrow"]:
        """
        Reads a JSON file and checks if:
            * The requested times are within the JSON file's times
            * The requested stations are a subset of the JSON file's stations

        :param file_path: full path of file to load data from.
        :param base_dir: the base directory containing the json file
        :param file_name: the file name of the json file.  Do not include extensions
        :param dw_base_dir: optional directory containing the compressed data window file.
                            If not given, assume in subdirectory "dw".  default None
        :param start_dt: the start datetime to check against.  if not given, assumes True.  default None
        :param end_dt: the end datetime to check against.  if not given, assumes True.  default None
        :param station_ids: the station ids to check against.  if not given, assumes True.  default None
        :return: the data window if it suffices, otherwise None
        """
        with open(file_path, "r") as f_p:
            json_data = json.loads(f_p.read())
        return DataWindowArrow.from_json_dict(json_data)
        # if not dw_base_dir:
        #     dw_base_dir = Path(base_dir).joinpath("dw")
        # file_name += ".json"
        # return DataWindow.from_json_dict(
        #     dw_io.json_file_to_data_window(base_dir, file_name), dw_base_dir, start_dt, end_dt, station_ids)

    @staticmethod
    def from_json(json_str: str, dw_base_dir: str,
                  start_dt: Optional[dtu.datetime] = None,
                  end_dt: Optional[dtu.datetime] = None,
                  station_ids: Optional[Iterable[str]] = None) -> Optional["DataWindowArrow"]:
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
        return DataWindowArrow.from_json_dict(dw_io.json_to_data_window(json_str),  # dw_base_dir,
                                              start_dt, end_dt, station_ids)

    @staticmethod
    def from_json_dict(json_dict: Dict,
                       # dw_base_dir: str,
                       start_dt: Optional[dtu.datetime] = None,
                       end_dt: Optional[dtu.datetime] = None,
                       station_ids: Optional[Iterable[str]] = None) -> Optional["DataWindowArrow"]:
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
        dct = json_dict["datawindow_metadata"]
        dwin = DataWindowArrow(dct["input_directory"])
        dwin.config = dct["config"]
        dwin.debug = dct["debug"]
        dwin.errors = RedVoxExceptions.from_dict(dct["errors"])
        dwin.sdk_version = dct["sdk_version"]
        dwin.station_out_dir = dct["station_out_dir"]
        dwin.save_station_files = dct["save_station_files"]
        for st in json_dict["stations"]:
            dwin.add_station(StationPa.from_json_file(os.path.join(json_dict["files_dir"], st, f"{st}.json")))
        return dwin
        # if start_dt and json_dict["start_datetime"] >= dtu.datetime_to_epoch_microseconds_utc(start_dt):
        #     return None
        # if end_dt and json_dict["end_datetime"] < dtu.datetime_to_epoch_microseconds_utc(end_dt):
        #     return None
        # if station_ids and not all(a in json_dict["station_ids"] for a in station_ids):
        #     return None
        # comp_dw_path = str(Path(dw_base_dir).joinpath(json_dict["file_name"]))
        # if json_dict["compression_format"] == "lz4":
        #     return DataWindow.deserialize(comp_dw_path + ".pkl.lz4")
        # else:
        #     with open(comp_dw_path + ".pkl", 'rb') as fp:
        #         return pickle.load(fp)

    def get_start_date(self) -> float:
        """
        :return: minimum start timestamp of the data
        """
        return np.min([s.first_data_timestamp for s in self._stations])

    def get_end_date(self) -> float:
        """
        :return: maximum end timestamp of the data
        """
        return np.max([s.last_data_timestamp for s in self._stations])

    def stations(self) -> List[StationPa]:
        """
        :return: list of stations in the data window
        """
        return self._stations

    def station_ids(self) -> List[str]:
        """
        :return: ids of stations in the data window
        """
        return [s.get_id() for s in self._stations]

    def add_station(self, station: StationPa):
        """
        add a station to the data window
        :param station: Station to add
        """
        self._stations.append(station)

    def get_station(self, station_id: str, station_uuid: Optional[str] = None,
                    start_timestamp: Optional[float] = None) -> Optional[List[StationPa]]:
        """
        Get stations from the data window.  Must give at least the station's id.  Other parameters may be None,
        which means the value will be ignored when searching.  Results will match all non-None parameters given.

        :param station_id: station id
        :param station_uuid: station uuid, default None
        :param start_timestamp: station start timestamp in microseconds since UTC epoch, default None
        :return: A list of valid stations or None if the station cannot be found
        """
        result = [s for s in self._stations if s.get_key().check_key(station_id, station_uuid, start_timestamp)]
        if len(result) > 0:
            return result
        if self.debug:
            self.errors.append(f"Attempted to get station {station_id}, "
                               f"but that station is not in this data window!")
        return None

    def _add_sensor_to_window(self, station: StationPa):
        self.errors.extend_error(station.errors)
        # set the window start and end if they were specified, otherwise use the bounds of the data
        self.create_window_in_sensors(station, self.config.start_datetime, self.config.end_datetime)

    def create_data_window(self, pool: Optional[multiprocessing.pool.Pool] = None):
        """
        updates the data window to contain only the data within the window parameters
        stations without audio or any data outside the window are removed
        """
        # Let's create and manage a single pool of workers that we can utilize throughout
        # the instantiation of the data window.
        _pool: multiprocessing.pool.Pool = multiprocessing.Pool() if pool is None else pool

        r_f = io.ReadFilter()
        if self.config.start_datetime:
            r_f.with_start_dt(self.config.start_datetime)
        if self.config.end_datetime:
            r_f.with_end_dt(self.config.end_datetime)
        if self.config.station_ids:
            r_f.with_station_ids(self.config.station_ids)
        if self.config.extensions:
            r_f.with_extensions(self.config.extensions)
        else:
            self.config.extensions = r_f.extensions
        if self.config.api_versions:
            r_f.with_api_versions(self.config.api_versions)
        else:
            self.config.api_versions = r_f.api_versions
        r_f.with_start_dt_buf(self.config.start_buffer_td)
        r_f.with_end_dt_buf(self.config.end_buffer_td)

        # get the data to convert into a window
        a_r = ApiReader(self.input_directory, self.config.structured_layout, r_f, pool=_pool)

        self.errors.extend_error(a_r.errors)

        if not self.config.station_ids:
            self.station_ids = a_r.index_summary.station_ids()
        else:
            self.station_ids = self.config.station_ids
        # Parallel update
        # Apply timing correction in parallel by station

        if self.config.apply_correction:
            for st in maybe_parallel_map(_pool, StationPa.update_timestamps,
                                         iter(a_r.get_stations_wpa_fs(correct_timestamps=self.config.apply_correction,
                                             use_model_correction=self.config.use_model_correction,
                                                                      base_dir=self.station_out_dir,
                                                                      save_files=self.save_station_files)),
                                         chunk_size=1):
                self._add_sensor_to_window(st)
        else:
            [self._add_sensor_to_window(s) for s in
             a_r.get_stations_wpa_fs(correct_timestamps=self.config.apply_correction,
                                     use_model_correction=self.config.use_model_correction,
                                     base_dir=self.station_out_dir,
                                     save_files=self.save_station_files)]

        # check for stations without data
        self._check_for_audio()
        self._check_valid_ids()

        # update remaining data window values if they're still default
        if not self.config.start_datetime and len(self._stations) > 0:
            self.config.start_datetime = dtu.datetime_from_epoch_microseconds_utc(
                np.min([t.first_data_timestamp for t in self._stations]))
        # end_datetime is non-inclusive, so it must be greater than our latest timestamp
        if not self.config.end_datetime and len(self._stations) > 0:
            self.config.end_datetime = dtu.datetime_from_epoch_microseconds_utc(
                np.max([t.last_data_timestamp for t in self._stations]) + 1)

        # if self.save_station_files:
        #     self.data_window_results = DataWindowResult(self.event_name, self.station_out_dir, self.start_datetime,
        #                                                 self.end_datetime, self.)

        # If the pool was created by this function, then it needs to managed by this function.
        if pool is None:
            _pool.close()

    def _check_for_audio(self):
        """
        removes any station and station id without audio data from the data window
        """
        remove = []
        for s in self._stations:
            if not s.has_audio_sensor():
                remove.append(s.id)
        if len(remove) > 0:
            self._stations = [s for s in self._stations if s.id not in remove]
            self.station_ids = [s for s in self.station_ids if s not in remove]

    def _check_valid_ids(self):
        """
        if there are stations, searches the station_ids for any ids not in the data collected
        and creates an error message for each id requested but has no data
        if there are no stations, creates a single error message declaring no data found
        """
        if len(self._stations) < 1:
            if len(self.station_ids) > 1:
                add_ids = f"for all stations {self.station_ids} "
            else:
                add_ids = ""
            self.errors.append(f"No data matching criteria {add_ids}in {self.input_directory}"
                               f"\nPlease adjust parameters of DataWindow")
        elif len(self.station_ids) > 1:
            for ids in self.station_ids:
                if ids not in [i.get_id() for i in self._stations] and self.debug:
                    self.errors.append(
                        f"Requested {ids} but there is no data to read for that station"
                    )

    def create_window_in_sensors(
            self, station: StationPa, start_datetime: Optional[dtu.datetime] = None,
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
        self.process_sensor(station.audio_sensor(), station.get_id(), start_datetime, end_datetime)
        for sensor in [s for s in station.data() if s.type != SensorType.AUDIO]:
            self.process_sensor(sensor, station.get_id(), station.audio_sensor().first_data_timestamp(),
                                station.audio_sensor().last_data_timestamp())
        # recalculate metadata
        station.first_data_timestamp = station.audio_sensor().first_data_timestamp()
        station.last_data_timestamp = station.audio_sensor().data_timestamps()[-1]
        station.packet_metadata = [meta for meta in station.packet_metadata
                                   if meta.packet_start_mach_timestamp < station.last_data_timestamp and
                                   meta.packet_end_mach_timestamp >= station.first_data_timestamp]
        self._stations.append(station)

    def process_sensor(self, sensor: SensorDataPa, station_id: str, start_date_timestamp: float,
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
                    self.errors.append(f"Data window for {station_id} "
                                       f"Audio sensor has truncated all data points")
                elif last_before_start is not None and first_after_end is None:
                    first_entry = sensor.pyarrow_table().slice(last_before_start, 1).to_pydict()
                    first_entry["timestamps"] = [start_date_timestamp]
                    sensor.write_pyarrow_table(pa.Table.from_pydict(first_entry))
                elif last_before_start is None and first_after_end is not None:
                    last_entry = sensor.pyarrow_table().slice(first_after_end, 1).to_pydict()
                    last_entry["timestamps"] = [start_date_timestamp]
                    sensor.write_pyarrow_table(pa.Table.from_pydict(last_entry))
                elif last_before_start is not None and first_after_end is not None:
                    sensor.write_pyarrow_table(
                        sensor.interpolate(start_date_timestamp, last_before_start, 1,
                                           self.config.copy_edge_points == gpu.DataPointCreationMode.COPY))
                else:
                    self.errors.append(
                        f"Data window for {station_id} {sensor.type.name} "
                        f"sensor has truncated all data points"
                    )
            else:
                _arrow = sensor.pyarrow_table().slice(start_index, end_index-start_index)
                # if sensor is audio or location, we want nan'd edge points
                if sensor.type in [SensorType.LOCATION, SensorType.AUDIO]:
                    new_point_mode = gpu.DataPointCreationMode["NAN"]
                else:
                    new_point_mode = self.config.copy_edge_points
                # add in the data points at the edges of the window if there are defined start and/or end times
                if not is_audio:
                    end_sample_interval = end_date_timestamp - sensor.last_data_timestamp()
                    end_samples_to_add = 1
                    start_sample_interval = start_date_timestamp - sensor.first_data_timestamp()
                    start_samples_to_add = 1
                else:
                    end_sample_interval = dtu.seconds_to_microseconds(sensor.sample_interval_s)
                    start_sample_interval = -end_sample_interval
                    if self.config.end_datetime:
                        end_samples_to_add = int((dtu.datetime_to_epoch_microseconds_utc(self.config.end_datetime)
                                                  - sensor.last_data_timestamp()) / end_sample_interval)
                    else:
                        end_samples_to_add = 0
                    if self.config.start_datetime:
                        start_samples_to_add = int((sensor.first_data_timestamp() -
                                                    dtu.datetime_to_epoch_microseconds_utc(self.config.start_datetime))
                                                   / end_sample_interval)
                    else:
                        start_samples_to_add = 0
                # add to end
                _arrow = (gpu.add_data_points_to_df(dataframe=_arrow, start_index=sensor.num_samples() - 1,
                                                    sample_interval_micros=end_sample_interval,
                                                    num_samples_to_add=end_samples_to_add,
                                                    point_creation_mode=new_point_mode))
                # add to begin
                _arrow = (gpu.add_data_points_to_df(dataframe=_arrow, start_index=0,
                                                    sample_interval_micros=start_sample_interval,
                                                    num_samples_to_add=start_samples_to_add,
                                                    point_creation_mode=new_point_mode))
                sensor.sort_by_data_timestamps(_arrow)
        else:
            self.errors.append(f"Data window for {station_id} {sensor.type.name} "
                               f"sensor has no data points!")

    def print_errors(self):
        """
        prints errors to screen
        """
        self.errors.print()
