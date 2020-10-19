"""
This module provide type-safe data window configuration
"""

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Optional, Set, MutableMapping

import pprint
import toml

from redvox.common import date_time_utils as dtu


# defaults for configuration
DEFAULT_GAP_TIME_S: float = 0.25
DEFAULT_START_PADDING_S: float = 120.
DEFAULT_END_PADDING_S: float = 120.


@dataclass_json()
@dataclass
class DataWindowConfig:
    """
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
    """
    input_directory: str
    station_ids: Optional[Set[str]] = None
    start_datetime: Optional[dtu.datetime] = None
    end_datetime: Optional[dtu.datetime] = None
    start_padding_s: float = DEFAULT_START_PADDING_S
    end_padding_s: float = DEFAULT_END_PADDING_S
    gap_time_s: float = DEFAULT_GAP_TIME_S
    apply_correction: bool = True
    structured_layout: bool = True

    @staticmethod
    def from_path(config_path: str) -> 'DataWindowConfig':
        try:
            with open(config_path, "r") as config_in:
                config_dict: MutableMapping = toml.load(config_in)
                # noinspection Mypy
                return DataWindowConfig.from_dict(config_dict)
        except Exception as e:
            print(f"Error loading configuration at: {config_path}")
            raise e

    def pretty(self) -> str:
        # noinspection Mypy
        return pprint.pformat(self.to_dict())
