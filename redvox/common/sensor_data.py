"""
Defines generic sensor data and metadata for API-independent analysis
"""

import numpy as np
import pandas as pd

from typing import List, Dict
from dataclasses import dataclass, field


@dataclass
class SensorData:
    """
    Generic SensorData class for API-independent analysis
    Properties:
        name: string, name of sensor
        sample_rate: float, sample rate of the sensor
        is_sample_rate_fixed: bool, True if sample rate is constant
        data_df: dataframe of the sensor data; timestamps (??? type) are the index, columns are the data fields
    """
    name: str
    sample_rate: float
    is_sample_rate_fixed: bool
    data_df: pd.DataFrame

    # todo: define what type timestamps are
    def sensor_timestamps(self) -> List[str]:
        return self.data_df.index.to_list()

    def num_samples(self) -> int:
        return self.data_df.shape[0]

    def sensor_data_fields(self) -> List[str]:
        return self.data_df.columns.to_list()


@dataclass
class SensorMetadata:
    """
    Generic SensorMetadata class for API-independent analysis
    Properties:
        start_time: int, timestamp when station started recording
        station_make: str, maker of the station
        station_model: str, model of the station
        station_os: str, operating system of the station
        station_os_version: str, station OS version
        station_app: str, the name of the recording software used by the station
        station_app_version: str, the recording software version
        timesync: dict, time synchronization object
    """
    start_time: int
    station_make: str
    station_model: str
    station_os: str
    station_os_version: str
    station_app: str
    station_app_version: str
    timesync: dict = field(default_factory=dict)


@dataclass
class Station:
    """
    generic station for api-independent stuff
    Properties:
        sensor_data_dict: dict, all SensorData associated with this sensor; keys are SensorData.name
        sensor_metadata: SensorMetadata
    """
    sensor_metadata: SensorMetadata
    sensor_data_dict: Dict[str, SensorData] = field(default_factory=dict)

