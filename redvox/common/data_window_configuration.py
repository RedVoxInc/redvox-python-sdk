"""
This module provide type-safe data window configuration
"""

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Optional, List, MutableMapping

import pprint
import toml
import numpy as np

import redvox.common.date_time_utils as dtu
from redvox.common.gap_and_pad_utils import DataPointCreationMode


# defaults for configuration
DEFAULT_DROP_TIME_S: float = 0.2  # seconds between packets to be considered a gap
DEFAULT_START_PADDING_S: float = 120.0  # time to add before start time when searching
DEFAULT_END_PADDING_S: float = 120.0  # time to add after end time when searching


@dataclass_json
@dataclass
class DataWindowConfigFile:
    """
    Properties:
        event_name: str, name of the data window.  Default "dw"

        origin_provider: string, source of the location data (i.e. GPS or NETWORK), default UNKNOWN

        origin_latitude: float, best estimate of latitude in degrees, default np.nan

        origin_latitude_std: float, standard deviation of best estimate of latitude, default np.nan

        origin_longitude: float, best estimate of longitude in degrees, default np.nan

        origin_longitude_std: float, standard deviation of best estimate of longitude, default np.nan

        origin_altitude: float, best estimate of altitude in meters, default np.nan

        origin_altitude_std: float, standard deviation of best estimate of altitude, default np.nan

        origin_event_radius_m: float, radius of event in meters, default 0.0

        output_dir: str, directory to output the data to.  Default "." (current directory)

        output_type: str, type of file to output the data as.  Options are: "NONE", "PARQUET", "LZ4"
        Default "NONE" (no saving).

        make_runme: bool, if True, save a runme.py example file along with the data.  Default False

        input_directory: str, directory that contains the files to read data from.  REQUIRED

        structured_layout: bool, if True, the input_directory contains specially named and organized
        directories of data.  Default True

        station_ids: optional list of strings, list of station ids to filter on.
        If empty or None, get any ids found in the input directory.  Default None

        extensions: optional list of strings, representing file extensions to filter on.
        If None, gets as much data as it can in the input directory.  Default None

        api_versions: optional list of ApiVersions, representing api versions to filter on.
        If None, get as much data as it can in the input directory.  Default None

        start_year: optional int representing the year of the data window start time.  Default None

        start_month: optional int representing the month of the data window start time.  Default None

        start_day: optional int representing the day of the data window start time.  Default None

        start_hour: optional int representing the hour of the data window start time.  Default None

        start_minute: optional int representing the minute of the data window start time.  Default None

        start_second: optional int representing the second of the data window start time.  Default None

        end_year: optional int representing the year of the data window end time.  Default None

        end_month: optional int representing the month of the data window end time.  Default None

        end_day: optional int representing the day of the data window end time.  Default None

        end_hour: optional int representing the hour of the data window end time.  Default None

        end_minute: optional int representing the minute of the data window end time.  Default None

        end_second: optional int representing the second of the data window end time.  Default None

        start_padding_seconds: float representing the amount of seconds to include before the start datetime
        when filtering data.  Default DEFAULT_START_PADDING_S (120 seconds)

        end_padding_seconds: float representing the amount of seconds to include after the end datetime
        when filtering data.  Default DEFAULT_END_PADDING_S (120 seconds)

        drop_time_seconds: float representing the minimum amount of seconds between data packets that would indicate
        a gap.  Default DEFAULT_DROP_TIME_S (0.2 seconds)

        apply_correction: bool, if True, update the timestamps in the data based on best station offset.  Default True

        edge_points_mode: str, one of "NAN", "COPY", or "INTERPOLATE".  Determines behavior when creating points on
        the edge of the data window.  default "COPY"

        use_model_correction: bool, if True, use the offset model's correction functions, otherwise use the best
        offset.  Default True

        debug: bool, if True, output additional information when processing data window.  Default False
    """

    input_directory: str
    event_name: str = "dw"
    origin_provider: str = "UNKNOWN"
    origin_latitude: float = np.nan
    origin_latitude_std: float = np.nan
    origin_longitude: float = np.nan
    origin_longitude_std: float = np.nan
    origin_altitude: float = np.nan
    origin_altitude_std: float = np.nan
    origin_event_radius_m: float = 0.0
    output_dir: str = "."
    output_type: str = "NONE"
    make_runme: bool = False
    structured_layout: bool = True
    station_ids: Optional[List[str]] = None
    extensions: Optional[List[str]] = None
    api_versions: Optional[List[str]] = None
    start_year: Optional[int] = None
    start_month: Optional[int] = None
    start_day: Optional[int] = None
    start_hour: Optional[int] = None
    start_minute: Optional[int] = None
    start_second: Optional[int] = None
    end_year: Optional[int] = None
    end_month: Optional[int] = None
    end_day: Optional[int] = None
    end_hour: Optional[int] = None
    end_minute: Optional[int] = None
    end_second: Optional[int] = None
    start_padding_seconds: float = DEFAULT_START_PADDING_S
    end_padding_seconds: float = DEFAULT_END_PADDING_S
    drop_time_seconds: float = DEFAULT_DROP_TIME_S
    apply_correction: bool = True
    use_model_correction: bool = True
    edge_points_mode: str = "COPY"
    debug: bool = False

    @staticmethod
    def from_path(config_path: str) -> "DataWindowConfigFile":
        try:
            with open(config_path, "r") as config_in:
                config_dict: MutableMapping = toml.load(config_in)
                # noinspection Mypy
                return DataWindowConfigFile.from_dict(config_dict)
        except Exception as e:
            print(f"Error loading configuration at: {config_path}")
            raise e

    def pretty(self) -> str:
        # noinspection Mypy
        return pprint.pformat(self.to_dict())

    def start_dt(self) -> Optional[dtu.datetime]:
        if self.start_year is not None:
            return dtu.datetime(self.start_year, self.start_month, self.start_day,
                                self.start_hour, self.start_minute, self.start_second)
        return None

    def set_start_dt(self, start_dt: dtu.datetime):
        self.start_year = start_dt.year
        self.start_month = start_dt.month
        self.start_day = start_dt.day
        self.start_hour = start_dt.hour
        self.start_minute = start_dt.minute
        self.start_second = start_dt.second

    def end_dt(self) -> Optional[dtu.datetime]:
        if self.end_year is not None:
            return dtu.datetime(self.end_year, self.end_month, self.end_day,
                                self.end_hour, self.end_minute, self.end_second)
        return None

    def set_end_dt(self, end_dt: dtu.datetime):
        self.end_year = end_dt.year
        self.end_month = end_dt.month
        self.end_day = end_dt.day
        self.end_hour = end_dt.hour
        self.end_minute = end_dt.minute
        self.end_second = end_dt.second

    def start_buffer_td(self) -> dtu.timedelta:
        return dtu.timedelta(seconds=self.start_padding_seconds)

    def end_buffer_td(self) -> dtu.timedelta:
        return dtu.timedelta(seconds=self.end_padding_seconds)

    def copy_edge_points(self) -> DataPointCreationMode:
        return DataPointCreationMode[self.edge_points_mode]
