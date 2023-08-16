"""
This module creates specific time-bounded segments of data for users
combines the base data files into a single composite object based on the user parameters
"""
from pathlib import Path
from typing import Optional, Set, List, Dict, Iterable
from datetime import timedelta
from dataclasses import dataclass
from dataclasses_json import dataclass_json
import shutil
import os
import inspect

import pprint
import multiprocessing
import multiprocessing.pool
import numpy as np
import pyarrow as pa

import redvox
from redvox.common import run_me, io, data_window_io as dw_io, date_time_utils as dtu, gap_and_pad_utils as gpu
from redvox.common.data_window_configuration import DataWindowConfigFile
from redvox.common.parallel_utils import maybe_parallel_map
from redvox.common.station import Station, STATION_ID_LENGTH
from redvox.common.sensor_data import SensorType, SensorData
from redvox.common.api_reader_dw import ApiReaderDw
from redvox.common.errors import RedVoxExceptions

DEFAULT_START_BUFFER_TD: timedelta = timedelta(minutes=2.0)  # default padding to start time of data
DEFAULT_END_BUFFER_TD: timedelta = timedelta(minutes=2.0)  # default padding to end time of data
# minimum default length of time in seconds for data to be off by to be considered suspicious
DATA_DROP_DURATION_S: float = 0.2


@dataclass_json
@dataclass
class EventOrigin:
    """
    The origin event's latitude, longitude, altitude and their standard deviations, the device used to measure
    the location data and the radius of the event

    Properties:
        provider: str, source of the location data (i.e. "GPS" or "NETWORK"), default "UNKNOWN"

        latitude: float, best estimate of latitude in degrees, default np.nan

        latitude_std: float, standard deviation of best estimate of latitude, default np.nan

        longitude: float, best estimate of longitude in degrees, default np.nan

        longitude_std: float, standard deviation of best estimate of longitude, default np.nan

        altitude: float, best estimate of altitude in meters, default np.nan

        altitude_std: float, standard deviation of best estimate of altitude, default np.nan

        event_radius_m: float, radius of event in meters, default 0.0
    """

    provider: str = "UNKNOWN"
    latitude: float = np.nan
    latitude_std: float = np.nan
    longitude: float = np.nan
    longitude_std: float = np.nan
    altitude: float = np.nan
    altitude_std: float = np.nan
    event_radius_m: float = 0.0


class DataWindowConfig:
    """
    Configuration of DataWindow properties

    Properties:
        input_dir: str, the directory that contains all the data.  REQUIRED

        structured_layout: bool, if True, the input_dir contains specially named and organized
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
        If empty or None, get any ids found in the input directory.  You may pass in any iterable, as long as it can be
        turned into a set.  Default None

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
        use_model_correction: bool = True,
        copy_edge_points: gpu.DataPointCreationMode = gpu.DataPointCreationMode.COPY,
    ):
        self.input_dir: str = input_dir
        self.structured_layout: bool = structured_layout
        self.start_datetime: Optional[dtu.datetime] = start_datetime
        self.end_datetime: Optional[dtu.datetime] = end_datetime
        self.start_buffer_td: timedelta = (
            start_buffer_td if start_buffer_td > timedelta(seconds=0) else timedelta(seconds=0)
        )
        self.end_buffer_td: timedelta = end_buffer_td if end_buffer_td > timedelta(seconds=0) else timedelta(seconds=0)
        self.drop_time_s: float = drop_time_s if drop_time_s > 0 else DATA_DROP_DURATION_S
        self.station_ids: Optional[Set[str]] = set(station_ids) if station_ids else None
        self.extensions: Optional[Set[str]] = extensions
        self.api_versions: Optional[Set[io.ApiVersion]] = api_versions
        self.apply_correction: bool = apply_correction
        self.use_model_correction = use_model_correction
        self.copy_edge_points = copy_edge_points

    def __repr__(self):
        return (
            f"input_dir: {self.input_dir}, "
            f"structured_layout: {self.structured_layout}, "
            f"start_datetime: {self.start_datetime.__repr__()}, "
            f"end_datetime: {self.end_datetime.__repr__()}, "
            f"start_buffer_td: {self.start_buffer_td.__repr__()}, "
            f"end_buffer_td: {self.end_buffer_td.__repr__()}, "
            f"drop_time_s: {self.drop_time_s}, "
            f"station_ids: {list(self.station_ids) if self.station_ids else []}, "
            f"extensions: {list(self.extensions) if self.extensions else []}, "
            f"api_versions: {[a_v.value for a_v in self.api_versions] if self.api_versions else []}, "
            f"apply_correction: {self.apply_correction}, "
            f"use_model_correction: {self.use_model_correction}, "
            f"copy_edge_points: {self.copy_edge_points.value}"
        )

    def __str__(self):
        return (
            f"input_dir: {self.input_dir}, "
            f"structured_layout: {self.structured_layout}, "
            f"start_datetime: "
            f"{self.start_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if self.start_datetime else None}, "
            f"end_datetime: {self.end_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if self.end_datetime else None}, "
            f"start_buffer_td (in s): {self.start_buffer_td.total_seconds()}, "
            f"end_buffer_td (in s): {self.end_buffer_td.total_seconds()}, "
            f"drop_time_s: {self.drop_time_s}, "
            f"station_ids: {list(self.station_ids) if self.station_ids else []}, "
            f"extensions: {list(self.extensions) if self.extensions else []}, "
            f"api_versions: {[a_v.value for a_v in self.api_versions] if self.api_versions else []}, "
            f"apply_correction: {self.apply_correction}, "
            f"use_model_correction: {self.use_model_correction}, "
            f"copy_edge_points: {self.copy_edge_points.name}"
        )

    def to_dict(self) -> Dict:
        return {
            "input_dir": self.input_dir,
            "structured_layout": self.structured_layout,
            "start_datetime": dtu.datetime_to_epoch_microseconds_utc(self.start_datetime)
            if self.start_datetime
            else None,
            "end_datetime": dtu.datetime_to_epoch_microseconds_utc(self.end_datetime) if self.end_datetime else None,
            "start_buffer_td": self.start_buffer_td.total_seconds(),
            "end_buffer_td": self.end_buffer_td.total_seconds(),
            "drop_time_s": self.drop_time_s,
            "station_ids": list(self.station_ids) if self.station_ids else [],
            "extensions": list(self.extensions) if self.extensions else [],
            "api_versions": [a_v.value for a_v in self.api_versions] if self.api_versions else [],
            "apply_correction": self.apply_correction,
            "use_model_correction": self.use_model_correction,
            "copy_edge_points": self.copy_edge_points.value,
        }

    @staticmethod
    def from_dict(data_dict: Dict) -> "DataWindowConfig":
        return DataWindowConfig(
            data_dict["input_dir"],
            data_dict["structured_layout"],
            dtu.datetime_from_epoch_microseconds_utc(data_dict["start_datetime"])
            if data_dict["start_datetime"]
            else None,
            dtu.datetime_from_epoch_microseconds_utc(data_dict["end_datetime"]) if data_dict["end_datetime"] else None,
            timedelta(seconds=data_dict["start_buffer_td"]),
            timedelta(seconds=data_dict["end_buffer_td"]),
            data_dict["drop_time_s"],
            data_dict["station_ids"],
            set(data_dict["extensions"]),
            set([io.ApiVersion.from_str(v) for v in data_dict["api_versions"]]),
            data_dict["apply_correction"],
            data_dict["use_model_correction"],
            gpu.DataPointCreationMode(data_dict["copy_edge_points"]),
        )


class DataWindow:
    """
    Holds the data for a given time window; adds interpolated timestamps to fill gaps and pad the start and end values

    If a start time is given, data starting from that time will be included.

    If an end time is given, data up to but not including that time will be included.

    Refer to the DataWindowConfig class for more details on DataWindow parameters.

    Properties:
        event_name: str, name of the DataWindow.  defaults to "dw"

        event_origin: Optional EventOrigin which describes the physical location and radius of the
        origin event.  Default empty EventOrigin (no valid data)

        config: optional DataWindowConfig with information on how to construct DataWindow from
        Redvox (.rdvx*) files.  Default None

        sdk_version: str, the version of the Redvox SDK used to create the DataWindow

        debug: bool, if True, outputs additional information during initialization. Default False

    Protected:
        _fs_writer: DataWindowFileSystemWriter; includes event_name, output directory (Default "."),
        output type (options: "PARQUET", "LZ4", "JSON", "NONE".  Default NONE), and option to make a
        runme.py example file (Default False)

        _stations: List of Stations that belong to the DataWindow

        _errors: RedVoxExceptions; contains a list of all errors encountered by the DataWindow
    """

    def __init__(
        self,
        event_name: str = "dw",
        event_origin: Optional[EventOrigin] = None,
        config: Optional[DataWindowConfig] = None,
        output_dir: str = ".",
        out_type: str = "NONE",
        make_runme: bool = False,
        debug: bool = False,
    ):
        """
        Initialize the DataWindow.

        If no config is passed, the DataWindow will not process any data.

        :param event_name: name of the DataWindow.  defaults to "dw"
        :param event_origin: Optional EventOrigin which describes the physical location and radius of the
                                origin event.  Default empty EventOrigin (no valid data)
        :param config: Optional DataWindowConfig which describes how to extract data from Redvox files.
                        Default None
        :param output_dir: output directory for saving files.  Default "." (current directory)
        :param out_type: type of file to save the DataWindow as.  Options: "PARQUET", "LZ4", "JSON", "NONE".
                            Default "NONE" (no saving)
        :param make_runme: if True, saves an example runme.py file with the data.  Default False
        :param debug: if True, outputs additional information during initialization.  Default False
        """
        self.event_name: str = event_name
        self.event_origin: EventOrigin = event_origin if event_origin else EventOrigin()
        self._fs_writer = dw_io.DataWindowFileSystemWriter(self.event_name, out_type, output_dir, make_runme)
        self.debug: bool = debug
        self._sdk_version: str = redvox.VERSION
        self._errors = RedVoxExceptions("DataWindow")
        self._stations: List[Station] = []
        self._config = config
        if config:
            if config.start_datetime and config.end_datetime and (config.end_datetime <= config.start_datetime):
                self._errors.append(
                    "DataWindow will not work when end datetime is before or equal to start datetime.\n"
                    f"Your times: {config.end_datetime} <= {config.start_datetime}"
                )
            else:
                self.create_data_window()
        if self.debug:
            self.print_errors()

    def __repr__(self):
        return (
            f"event_name: {self.event_name}, "
            f"event_origin: {self.event_origin.__repr__()}, "
            f"config: {self._config.__repr__()}, "
            f"output_dir: {os.path.abspath(self.save_dir())}, "
            f"out_type: {self._fs_writer.file_extension}, "
            f"make_runme: {self._fs_writer.make_run_me}, "
            f"sdk_version: {self._sdk_version}, "
            f"debug: {self.debug}"
        )

    def __str__(self):
        return (
            f"event_name: {self.event_name}, "
            f"event_origin: {self.event_origin.__str__()}, "
            f"config: {self._config.__str__()}, "
            f"output_dir: {os.path.abspath(self.save_dir())}, "
            f"out_type: {self._fs_writer.file_extension}, "
            f"make_runme: {self._fs_writer.make_run_me}, "
            f"sdk_version: {self._sdk_version}, "
            f"debug: {self.debug}"
        )

    def save_dir(self) -> str:
        """
        :return: directory data is saved to (empty string means saving to memory)
        """
        return self._fs_writer.save_dir()

    def set_save_dir(self, new_save_dir: Optional[str] = "."):
        """
        :param new_save_dir: directory to save data to; default current directory, or "."
        """
        self._fs_writer.base_dir = new_save_dir

    def is_make_runme(self) -> bool:
        """
        :return: if DataWindow will be saved with a runme file
        """
        return self._fs_writer.make_run_me

    def set_make_runme(self, make_runme: bool = False):
        """
        :param make_runme: if True, DataWindow will create a runme file when saved.  Default False
        """
        self._fs_writer.make_run_me = make_runme

    def fs_writer(self) -> dw_io.DataWindowFileSystemWriter:
        """
        :return: DataWindowFileSystemWriter for DataWindow
        """
        return self._fs_writer

    def out_type(self) -> str:
        """
        :return: string of the output type of the DataWindow
        """
        return self._fs_writer.file_extension

    def set_out_type(self, new_out_type: str):
        """
        set the output type of the DataWindow.  options are "NONE", "PARQUET", "LZ4" and "JSON".
        Invalid values become "NONE"

        :param new_out_type: new output type of the DataWindow
        """
        self._fs_writer.set_extension(new_out_type)

    def as_dict(self) -> Dict:
        """
        :return: DataWindow properties as dictionary
        """
        return {
            "event_name": self.event_name,
            "event_origin": self.event_origin.to_dict(),
            "start_time": self.start_date(),
            "end_time": self.end_date(),
            "base_dir": self.save_dir(),
            "stations": [s.default_station_json_file_name() for s in self._stations],
            "config": self._config.to_dict(),
            "debug": self.debug,
            "errors": self._errors.as_dict(),
            "sdk_version": self._sdk_version,
            "out_type": self._fs_writer.file_extension,
            "make_runme": self._fs_writer.make_run_me,
        }

    def pretty(self) -> str:
        """
        :return: DataWindow as dictionary, but easier to read
        """
        # noinspection Mypy
        return pprint.pformat(self.as_dict())

    @staticmethod
    def from_config(config: DataWindowConfigFile) -> "DataWindow":
        """
        Use a config file to create a DataWindow

        :param config: DataWindowConfigFile to load from
        :return: DataWindow
        """
        event_origin = EventOrigin(
            config.origin_provider,
            config.origin_latitude,
            config.origin_latitude_std,
            config.origin_longitude,
            config.origin_longitude_std,
            config.origin_altitude,
            config.origin_altitude_std,
            config.origin_event_radius_m,
        )
        dw_config = DataWindowConfig(
            config.input_directory,
            config.structured_layout,
            config.start_dt(),
            config.end_dt(),
            config.start_buffer_td(),
            config.end_buffer_td(),
            config.drop_time_seconds,
            config.station_ids,
            config.extensions,
            config.api_versions,
            config.apply_correction,
            config.use_model_correction,
            config.copy_edge_points(),
        )
        return DataWindow(
            config.event_name,
            event_origin,
            dw_config,
            config.output_dir,
            config.output_type,
            config.make_runme,
            config.debug,
        )

    @staticmethod
    def from_config_file(file: str) -> "DataWindow":
        """
        Loads a configuration file to create the DataWindow

        :param file: full path to config file
        :return: DataWindow
        """
        return DataWindow.from_config(DataWindowConfigFile.from_path(file))

    @staticmethod
    def deserialize(path: str) -> "DataWindow":
        """
        Decompresses and deserializes a DataWindow written to disk.

        :param path: Path to the serialized and compressed DataWindow.
        :return: An instance of a DataWindow.
        """
        return dw_io.deserialize_data_window(path)

    def serialize(self, compression_factor: int = 4) -> Path:
        """
        Serializes and compresses this DataWindow to a file.
        Uses the event_name and out_dir to name the file.

        :param compression_factor: A value between 1 and 12. Higher values provide better compression, but take
        longer. (default=4).
        :return: The path to the written file.
        """
        return dw_io.serialize_data_window(self, self.save_dir(), f"{self.event_name}.pkl.lz4", compression_factor)

    def _to_json_file(self) -> Path:
        """
        Converts the DataWindow metadata into a JSON file and compresses the DataWindow and writes it to disk.

        :return: The path to the written file
        """
        return dw_io.data_window_to_json(self, self.save_dir())

    def to_json(self) -> str:
        """
        :return: The DataWindow metadata into a JSON string.
        """
        return dw_io.data_window_as_json(self)

    @staticmethod
    def from_json(json_str: str) -> "DataWindow":
        """
        Read the DataWindow from a JSON string.  If file is improperly formatted, raises a ValueError.

        :param json_str: the JSON to read
        :return: The DataWindow as defined by the JSON
        """
        return DataWindow.from_json_dict(dw_io.json_to_dict(json_str))

    @staticmethod
    def from_json_dict(json_dict: Dict) -> "DataWindow":
        """
        Reads a JSON dictionary and loads the data into the DataWindow.
        If dictionary is improperly formatted, raises a ValueError.

        :param json_dict: the dictionary to read
        :return: The DataWindow as defined by the JSON
        """
        if (
            "out_type" not in json_dict.keys()
            or json_dict["out_type"].upper() not in dw_io.DataWindowOutputType.list_names()
        ):
            raise ValueError(
                "Dictionary loading type is invalid or unknown.  "
                'Check the value of "out_type"; it must be one of: '
                f"{dw_io.DataWindowOutputType.list_non_none_names()}"
            )
        else:
            out_type = dw_io.DataWindowOutputType.str_to_type(json_dict["out_type"])
            if out_type == dw_io.DataWindowOutputType.PARQUET or out_type == dw_io.DataWindowOutputType.JSON:
                dwin = DataWindow(
                    json_dict["event_name"],
                    EventOrigin.from_dict(json_dict["event_origin"]),
                    None,
                    json_dict["base_dir"],
                    json_dict["out_type"],
                    json_dict["make_runme"],
                    json_dict["debug"],
                )
                dwin._config = DataWindowConfig.from_dict(json_dict["config"])
                dwin._errors = RedVoxExceptions.from_dict(json_dict["errors"])
                dwin._sdk_version = json_dict["sdk_version"]
                for st in json_dict["stations"]:
                    dwin.add_station(Station.from_json_file(os.path.join(json_dict["base_dir"], st), f"{st}.json"))
            elif out_type == dw_io.DataWindowOutputType.LZ4:
                dwin = DataWindow.deserialize(os.path.join(json_dict["base_dir"], f"{json_dict['event_name']}.pkl.lz4"))
            else:
                dwin = DataWindow()
            return dwin

    def save(self) -> Path:
        """
        save the DataWindow to disk if saving is enabled
        if saving is not enabled, adds an error to the DataWindow and returns an empty path.

        :return: the path to where the files exist; an empty path means no files were saved
        """
        if self._fs_writer.is_save_disk():
            if self._fs_writer.is_use_disk() and self._fs_writer.make_run_me:
                shutil.copyfile(
                    os.path.abspath(inspect.getfile(run_me)), os.path.join(self._fs_writer.save_dir(), "runme.py")
                )
            if self._fs_writer.file_extension in ["parquet", "json"]:
                return self._to_json_file()
            elif self._fs_writer.file_extension == "lz4":
                return self.serialize()
        else:
            self._errors.append("Saving not enabled.")
            print("WARNING: Cannot save data window without knowing extension.")
            return Path()

    @staticmethod
    def load(file_path: str) -> "DataWindow":
        """
        load from json metadata and lz4 compressed file or directory of files.

        If you have a pkl.lz4 file, use the deserialize() method instead.

        :param file_path: full path of json metadata file to load
        :return: DataWindow from json metadata
        """
        cur_path = os.getcwd()
        path_dir = os.path.dirname(file_path)
        if path_dir:
            os.chdir(os.path.dirname(file_path))
        result = DataWindow.from_json_dict(dw_io.json_file_to_data_window(file_path))
        os.chdir(cur_path)
        return result

    def config(self) -> DataWindowConfig:
        """
        :return: settings used to create the DataWindow
        """
        return self._config

    def sdk_version(self) -> str:
        """
        :return: sdk version used to create the DataWindow
        """
        return self._sdk_version

    def set_sdk_version(self, version: str):
        """
        :param version: the sdk version to set
        """
        self._sdk_version = version

    def start_date(self) -> float:
        """
        :return: minimum start timestamp of the data or np.nan if no data
        """
        if len(self._stations) > 0:
            return np.min([s.first_data_timestamp() for s in self._stations])
        return np.nan

    def end_date(self) -> float:
        """
        :return: maximum end timestamp of the data or np.nan if no data
        """
        if len(self._stations) > 0:
            return np.max([s.last_data_timestamp() for s in self._stations])
        return np.nan

    def stations(self) -> List[Station]:
        """
        :return: list of stations in the DataWindow
        """
        return self._stations

    def station_ids(self) -> List[str]:
        """
        :return: ids of stations in the DataWindow
        """
        return [s.id() for s in self._stations]

    def add_station(self, station: Station):
        """
        add a station to the DataWindow

        :param station: Station to add
        """
        self._stations.append(station)

    def remove_station(self, station_id: Optional[str] = None, start_date: Optional[float] = None):
        """
        Remove the first station from the DataWindow, or a specific station if given the id and/or start date.

        * If an id is given, the first station with that id will be removed.
        * If a start date is given, the removed station will start at or after the start date.
        * Start date is in microseconds since epoch UTC.

        :param station_id: id of station to remove
        :param start_date: start date that is at or before the station to remove
        """
        id_removals = []
        sd_removals = []
        if station_id is None and start_date is None:
            self._stations.pop()
        else:
            if station_id is not None:
                for s in range(len(self._stations)):
                    if self._stations[s].id == station_id:
                        id_removals.append(s)
            if start_date is not None:
                for s in range(len(self._stations)):
                    if self._stations[s].start_date() >= start_date:
                        sd_removals.append(s)
            if len(id_removals) > 0 and start_date is None:
                self._stations.pop(id_removals.pop())
            elif len(sd_removals) > 0 and station_id is None:
                self._stations.pop(sd_removals.pop())
            elif len(id_removals) > 0 and len(sd_removals) > 0:
                for a in id_removals:
                    for b in sd_removals:
                        if a == b:
                            self._stations.pop(a)
                            return
                        if a < b:
                            continue

    def first_station(self, station_id: Optional[str] = None) -> Optional[Station]:
        """
        :param station_id: optional station id to filter on
        :return: first station matching params; if no params given, gets first station in list.
                    returns None if no station with given station_id exists.
        """
        if len(self._stations) < 1:
            self._errors.append(f"Attempted to get a station, but there are no stations in the data window!")
            if self.debug:
                print(f"Attempted to get a station, but there are no stations in the data window!")
            return None
        elif station_id:
            result = [s for s in self._stations if s.get_key().check_key(station_id, None, None)]
            if len(result) > 0:
                return result[0]
            self._errors.append(f"Attempted to get station {station_id}, but that station is not in this data window!")
            if self.debug:
                print(f"Attempted to get station {station_id}, but that station is not in this data window!")
            return None
        return self._stations[0]

    def get_station(
        self, station_id: str, station_uuid: Optional[str] = None, start_timestamp: Optional[float] = None
    ) -> Optional[List[Station]]:
        """
        Get stations from the DataWindow.  Must give at least the station's id.  Other parameters may be None,
        which means the value will be ignored when searching.  Results will match all non-None parameters given.

        :param station_id: station id to get data for
        :param station_uuid: station uuid, default None
        :param start_timestamp: station start timestamp in microseconds since UTC epoch, default None
        :return: A list of valid stations or None if the station cannot be found
        """
        result = [s for s in self._stations if s.get_key().check_key(station_id, station_uuid, start_timestamp)]
        if len(result) > 0:
            return result
        self._errors.append(f"Attempted to get station {station_id}, but that station is not in this data window!")
        if self.debug:
            print(f"Attempted to get station {station_id}, but that station is not in this data window!")
        return None

    def create_data_window(self, pool: Optional[multiprocessing.pool.Pool] = None):
        """
        updates the DataWindow to contain only the data within the window parameters
        stations without audio or any data outside the window are removed
        """
        # Let's create and manage a single pool of workers that we can utilize throughout
        # the instantiation of the data window.
        _pool: multiprocessing.pool.Pool = multiprocessing.Pool() if pool is None else pool

        r_f = io.ReadFilter()
        if self._config.start_datetime:
            r_f.with_start_dt(self._config.start_datetime)
        if self._config.end_datetime:
            r_f.with_end_dt(self._config.end_datetime)
        if self._config.station_ids:
            r_f.with_station_ids(self._config.station_ids)
        if self._config.extensions:
            r_f.with_extensions(self._config.extensions)
        else:
            self._config.extensions = r_f.extensions
        if self._config.api_versions:
            r_f.with_api_versions(self._config.api_versions)
        else:
            self._config.api_versions = r_f.api_versions
        r_f.with_start_dt_buf(self._config.start_buffer_td)
        r_f.with_end_dt_buf(self._config.end_buffer_td)

        if self.debug:
            print("Reading files from disk.  This may take a few minutes to complete.")

        # get the data to convert into a window
        a_r = ApiReaderDw(
            self._config.input_dir,
            self._config.structured_layout,
            r_f,
            correct_timestamps=self._config.apply_correction,
            use_model_correction=self._config.use_model_correction,
            dw_base_dir=self.save_dir(),
            dw_save_mode=self._fs_writer.save_mode(),
            debug=self.debug,
            pool=_pool,
        )

        # self._errors.extend_error(a_r.errors)

        if self._fs_writer.is_use_mem() and a_r.dw_save_mode != self._fs_writer.save_mode():
            if self.debug:
                print("Estimated size of files exceeds available memory.")
                print("Automatically using temporary directory to store data.")
            self._fs_writer.set_use_temp(True)

        # Parallel update
        # Apply timing correction in parallel by station
        sts = a_r.get_stations()
        if self.debug:
            print("number of stations loaded: ", len(sts))
        for st in maybe_parallel_map(_pool, lambda s: s, iter(sts), chunk_size=1):
            self.create_window_in_sensors(st, self._config.start_datetime, self._config.end_datetime)
            if self.debug:
                print("station processed: ", st.id())

        # check for stations without data
        self._check_for_audio()
        self._check_valid_ids()

        # update the default data window name if we have data and the default name exists
        if self.event_name == "dw" and len(self._stations) > 0:
            self.event_name = f"dw_{int(self.start_date())}_{len(self._stations)}"

        # must update the start and end in order for the data to be saved
        # update remaining data window values if they're still default
        if not self._config.start_datetime and len(self._stations) > 0:
            self._config.start_datetime = dtu.datetime_from_epoch_microseconds_utc(
                np.min([t.first_data_timestamp() for t in self._stations])
            )
        # end_datetime is non-inclusive, so it must be greater than our latest timestamp
        if not self._config.end_datetime and len(self._stations) > 0:
            self._config.end_datetime = dtu.datetime_from_epoch_microseconds_utc(
                np.max([t.last_data_timestamp() for t in self._stations]) + 1
            )

        # If the pool was created by this function, then it needs to managed by this function.
        if pool is None:
            _pool.close()

    def _check_for_audio(self):
        """
        removes any station without audio data from the DataWindow
        """
        remove = []
        for s in self._stations:
            if not s.has_audio_sensor():
                remove.append(s.get_key())
        if len(remove) > 0:
            self._stations = [s for s in self._stations if s.get_key() not in remove]

    def _check_valid_ids(self):
        """
        if there are stations, searches the config's station_ids for any ids not in the data collected
        and creates an error message for each id requested but has no data
        if there are no stations, creates a single error message declaring no data found
        """
        if len(self._stations) < 1 and self._config.station_ids:
            if len(self._config.station_ids) > 1:
                add_ids = f"for all stations {self._config.station_ids} "
            else:
                add_ids = ""
            self._errors.append(
                f"No data matching criteria {add_ids}in {self._config.input_dir}"
                f"\nPlease adjust parameters of DataWindow"
            )
        elif len(self._stations) > 0 and self._config.station_ids:
            for ids in self._config.station_ids:
                if ids.zfill(STATION_ID_LENGTH) not in [i.id() for i in self._stations]:
                    self._errors.append(f"Requested {ids} but there is no data to read for that station")

    def create_window_in_sensors(
        self,
        station: Station,
        start_datetime: Optional[dtu.datetime] = None,
        end_datetime: Optional[dtu.datetime] = None,
    ):
        """
        truncate the sensors in the station to only contain data from start_datetime to end_datetime.

        if the start and/or end are not specified, uses the audio start and end to truncate the other sensors.

        returns nothing, updates the station in place

        :param station: station object to truncate sensors of
        :param start_datetime: datetime of start of window, default None
        :param end_datetime: datetime of end of window, default None
        """
        start_datetime = dtu.datetime_to_epoch_microseconds_utc(start_datetime) if start_datetime else 0
        end_datetime = dtu.datetime_to_epoch_microseconds_utc(end_datetime if end_datetime else dtu.datetime.max)
        self.process_sensor(station.audio_sensor(), station.id(), start_datetime, end_datetime)
        if station.has_audio_data():
            for sensor in [s for s in station.data() if s.type() != SensorType.AUDIO]:
                self.process_sensor(
                    sensor,
                    station.id(),
                    station.audio_sensor().first_data_timestamp(),
                    station.audio_sensor().last_data_timestamp(),
                )
            # recalculate metadata
            station.update_first_and_last_data_timestamps()
            station.set_packet_metadata(
                [
                    meta
                    for meta in station.packet_metadata()
                    if meta.packet_start_mach_timestamp < station.last_data_timestamp()
                    and meta.packet_end_mach_timestamp >= station.first_data_timestamp()
                ]
            )
            station.event_data().create_event_window(station.first_data_timestamp(), station.last_data_timestamp())
            if self._fs_writer.is_save_disk():
                station.set_save_mode(io.FileSystemSaveMode.DISK)
                station.set_save_dir(self.save_dir() if self._fs_writer.is_use_disk() else self._fs_writer.get_temp())
            self._stations.append(station)

    def process_sensor(
        self, sensor: SensorData, station_id: str, start_date_timestamp: float, end_date_timestamp: float
    ):
        """
        process a sensor to fit within the DataWindow.  Updates sensor in place, returns nothing.

        :param sensor: sensor to process
        :param station_id: station id
        :param start_date_timestamp: start of DataWindow
        :param end_date_timestamp: end of DataWindow
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
            is_audio = sensor.type() == SensorType.AUDIO
            if end_index <= start_index:
                self._errors.append(
                    f"Data window for {station_id} {'Audio' if is_audio else sensor.type().name} "
                    f"sensor has truncated all data points"
                )
                # adjust data window to match the conditions of the remaining data
                if is_audio:
                    sensor.empty_data_table()
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
                        sensor.interpolate(
                            start_date_timestamp,
                            last_before_start,
                            1,
                            self._config.copy_edge_points == gpu.DataPointCreationMode.COPY,
                        )
                    )
            else:
                _arrow = sensor.pyarrow_table().slice(start_index, end_index - start_index)
                # if sensor is audio or location, we want nan'd edge points
                if sensor.type() in [SensorType.LOCATION, SensorType.AUDIO]:
                    new_point_mode = gpu.DataPointCreationMode.NAN
                else:
                    new_point_mode = self._config.copy_edge_points
                # add in the data points at the edges of the window if there are defined start and/or end times
                slice_start = _arrow["timestamps"].to_numpy()[0]
                slice_end = _arrow["timestamps"].to_numpy()[-1]
                if not is_audio:
                    end_sample_interval = end_date_timestamp - slice_end
                    end_samples_to_add = 1
                    start_sample_interval = start_date_timestamp - slice_start
                    start_samples_to_add = 1
                else:
                    end_sample_interval = dtu.seconds_to_microseconds(sensor.sample_interval_s())
                    start_sample_interval = -end_sample_interval
                    if self._config.end_datetime:
                        end_samples_to_add = int(
                            (dtu.datetime_to_epoch_microseconds_utc(self._config.end_datetime) - slice_end)
                            / end_sample_interval
                        )
                    else:
                        end_samples_to_add = 0
                    if self._config.start_datetime:
                        start_samples_to_add = int(
                            (slice_start - dtu.datetime_to_epoch_microseconds_utc(self._config.start_datetime))
                            / end_sample_interval
                        )
                    else:
                        start_samples_to_add = 0
                # add to end
                _arrow = gpu.add_data_points_to_df(
                    data_table=_arrow,
                    start_index=_arrow.num_rows - 1,
                    sample_interval_micros=end_sample_interval,
                    num_samples_to_add=end_samples_to_add,
                    point_creation_mode=new_point_mode,
                )
                # add to begin
                _arrow = gpu.add_data_points_to_df(
                    data_table=_arrow,
                    start_index=0,
                    sample_interval_micros=start_sample_interval,
                    num_samples_to_add=start_samples_to_add,
                    point_creation_mode=new_point_mode,
                )
                sensor.sort_by_data_timestamps(_arrow)
        else:
            self._errors.append(f"Data window for {station_id} {sensor.type().name} " f"sensor has no data points!")

    def print_errors(self):
        """
        prints errors to screen
        """
        self._errors.print()
        for stn in self._stations:
            stn.print_errors()
