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
        data_df: dataframe of the sensor data; timestamps are the index, columns are the data fields
        sample_rate: float, sample rate of the sensor
        is_sample_rate_fixed: bool, True if sample rate is constant
    """
    name: str
    data_df: pd.DataFrame
    sample_rate: float = 1.0
    is_sample_rate_fixed: bool = False

    def sensor_timestamps(self) -> List[str]:
        return self.data_df.index.to_list()

    def num_samples(self) -> int:
        return self.data_df.shape[0]

    def sensor_data_fields(self) -> List[str]:
        return self.data_df.columns.to_list()


@dataclass
class DataPacket:
    """
    Generic DataPacket class for API-independent analysis
    Properties:
        server_timestamp: int, server timestamp of when data was received by the server
        sensor_data_dict: dict, all SensorData associated with this sensor; keys are SensorData.name
        packet_start_timestamp: int, machine timestamp of the start of the packet
        packet_end_timestamp: int, machine timestamp of the end of the packet
        timesync: np.array of of timesync data
        packet_best_latency: optional float, best latency of data
        packet_best_offset: optional int, best offset of data
    """
    server_timestamp: int
    sensor_data_dict: Dict[SensorType, SensorData] = field(default_factory=dict)
    packet_start_timestamp: int = 0
    packet_end_timestamp: int = 1
    timesync: np.array = np.zeros(0)
    packet_best_latency: Optional[float] = None
    packet_best_offset: Optional[int] = 0


@dataclass
class StationTiming:
    """
    Generic StationTiming class for API-independent analysis
    Properties:
        start_timestamp: int, timestamp when station started recording
        episode_start_timestamp: int, timestamp of start of segment of interest
        episode_end_timestamp: int, timestamp of end of segment of interest
        audio_sample_rate_hz: int, sample rate in hz of audio sensor
        station_best_latency: optional float, best latency of data
        station_best_offset: optional int, best offset of data
    """
    station_start_timestamp: int
    episode_start_timestamp: int
    episode_end_timestamp: int
    audio_sample_rate_hz: float
    station_best_latency: Optional[float] = None
    station_best_offset: Optional[int] = 0


@dataclass
class StationMetadata:
    """
    Generic StationMetadata class for API-independent analysis
    Properties:
        station_id: str, id of the station
        station_make: str, maker of the station
        station_model: str, model of the station
        station_os: str, operating system of the station
        station_os_version: str, station OS version
        station_app: str, the name of the recording software used by the station
        station_app_version: str, the recording software version
        station_timing: StationTiming metadata
    """
    station_id: str
    station_make: str
    station_model: str
    station_os: str
    station_os_version: str
    station_app: str
    station_app_version: str
    timing_data: StationTiming


@dataclass
class Station:
    """
    generic station for api-independent stuff
    Properties:
        station_metadata: StationMetadata
        station_data: dict, all DataPackets associated with this station; keys are packet_start_timestamp of DataPacket
    """
    station_metadata: StationMetadata
    sensor_data_dict: Dict[int, DataPacket] = field(default_factory=dict)

