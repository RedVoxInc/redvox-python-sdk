"""
Defines generic sensor data and metadata for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
"""

import enum
import numpy as np
import pandas as pd

from typing import List, Dict, Optional
from dataclasses import dataclass, field


class SensorType(enum.Enum):
    ACCELEROMETER = 1           # meters/second^2
    TEMPERATURE = 2             # degrees Celsius
    AUDIO = 3                   # normalized counts
    COMPRESSED_AUDIO = 4        # bytes (codec specific)
    GRAVITY = 5                 # meters/second^2
    GYROSCOPE = 6               # radians/second
    IMAGE = 7                   # bytes (codec specific)
    LIGHT = 8                   # lux
    LINEAR_ACCELERATION = 9     # meters/second^2
    LOCATION = 10               # See standard
    MAGNETOMETER = 11           # microtesla
    ORIENTATION = 12            # radians
    PRESSURE = 13               # kilopascal
    PROXIMITY = 14              # on, off, cm
    RELATIVE_HUMIDITY = 15      # percentage
    ROTATION_VECTOR = 16        # Unitless


@dataclass
class SensorData:
    """
    Generic SensorData class for API-independent analysis
    Properties:
        name: string, name of sensor
        sample_rate: float, sample rate of the sensor
        is_sample_rate_fixed: bool, True if sample rate is constant
        data_df: dataframe of the sensor data; timestamps are the index, columns are the data fields
    """
    name: str
    sample_rate: float
    is_sample_rate_fixed: bool
    data_df: pd.DataFrame

    def sensor_timestamps(self) -> List[str]:
        return self.data_df.index.to_list()

    def num_samples(self) -> int:
        return self.data_df.shape[0]

    def sensor_data_fields(self) -> List[str]:
        return self.data_df.columns.to_list()


@dataclass
class TimingData:
    """
    Generic TimingData class for API-independent analysis
    Properties:
        start_timestamp: int, timestamp when station started recording
        server_timestamp: int, timestamp of when data was received at server
        app_start_timestamp: int, timestamp of when data packet/segment started
        app_end_timestamp: int, timestamp of when data packet/segment ended
        timesync: np.ndarray, time synchronization object
        best_latency: optional float, best latency of data
        best_offset: optional int, best offset of data
    """
    station_start_timestamp: int
    server_timestamp: int
    app_start_timestamp: int
    app_end_timestamp: int
    timesync: np.ndarray
    best_latency: Optional[float] = None
    best_offset: Optional[int] = None


@dataclass
class SensorMetadata:
    """
    Generic SensorMetadata class for API-independent analysis
    Properties:
        station_id: str, id of the station
        station_make: str, maker of the station
        station_model: str, model of the station
        station_os: str, operating system of the station
        station_os_version: str, station OS version
        station_app: str, the name of the recording software used by the station
        station_app_version: str, the recording software version
    """
    station_id: str
    station_make: str
    station_model: str
    station_os: str
    station_os_version: str
    station_app: str
    station_app_version: str


@dataclass
class Station:
    """
    generic station for api-independent stuff
    Properties:
        sensor_data_dict: dict, all SensorData associated with this sensor; keys are SensorData.name
        sensor_metadata: SensorMetadata
    """
    sensor_metadata: SensorMetadata
    timing_data: TimingData
    sensor_data_dict: Dict[SensorType, SensorData] = field(default_factory=dict)

