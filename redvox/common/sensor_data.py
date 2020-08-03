"""
Defines generic sensor data and metadata for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
"""

import enum
import numpy as np
import pandas as pd

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from redvox.api900 import reader


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
        sensor_data_dict: dict, all SensorData associated with this sensor; keys are SensorType
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
        station_first_timestamp: int, first timestamp chronologically of the data
        station_best_latency: optional float, best latency of data
        station_best_offset: optional int, best offset of data
    """
    station_start_timestamp: int
    episode_start_timestamp: int
    episode_end_timestamp: int
    audio_sample_rate_hz: float
    station_first_timestamp: int
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
    sensor_dict: Dict[int, DataPacket] = field(default_factory=dict)


def api900_sensor_to_df(sensor: reader.RedvoxSensor) -> SensorData:
    """
    read the data from an api900 sensor into a generic SensorData object
    :param sensor: the api900 sensor to read data from
    :return: a SensorData object
    """
    if sensor.:



def read_api900_wrapped_packet(wrapped_packet: reader.WrappedRedvoxPacket) -> Dict[SensorType, SensorData]:
    """
    reads the data from a wrapped api900 redvox packet into a dictionary of generic data
    :param wrapped_packet: a wrapped api900 redvox packet
    :return: a dictionary containing all the sensor data
    """
    data_dict: Dict[SensorType, SensorData] = {}
    # there are 9 api900 sensors
    if wrapped_packet.has_microphone_sensor():
        data_dict[SensorType.AUDIO] = SensorData(wrapped_packet.microphone_sensor().sensor_name(),
                                                 pd.DataFrame(wrapped_packet.microphone_sensor().payload_values(),
                                                              index=["mic_data"]).T,
                                                 wrapped_packet.microphone_sensor().sample_rate_hz(), True)
    if wrapped_packet.has_accelerometer_sensor():
        data_dict[SensorType.ACCELEROMETER] = SensorData(wrapped_packet.accelerometer_sensor().sensor_name(),
                                                         pd.DataFrame(wrapped_packet.accelerometer_sensor().))
    return data_dict


def load_file_range_from_api900(directory: str,
                                start_timestamp_utc_s: Optional[int] = None,
                                end_timestamp_utc_s: Optional[int] = None,
                                redvox_ids: Optional[List[str]] = None,
                                structured_layout: bool = False,
                                concat_continuous_segments: bool = True) -> List['Station']:
    """
    reads in data from a directory and returns a list of stations
    note that the param descriptions are taken directly from reader.read_rdvxz_file_range
    :param directory: The root directory of the data. If structured_layout is False, then this directory will
                      contain various unorganized .rdvxz files. If structured_layout is True, then this directory
                      must be the root api900 directory of the structured files.
    :param start_timestamp_utc_s: The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: The end timestamp as seconds since the epoch UTC.
    :param redvox_ids: An optional list of redvox_ids to filter against (default=[]).
    :param structured_layout: An optional value to define if this is loading structured data (default=False).
    :param concat_continuous_segments: An optional value to define if this function should concatenate rdvxz files
                                       into multiple continuous rdvxz files separated at gaps.
    :return: a list of Station objects that contain the data
    """
    all_stations: List[Station] = []
    all_data = reader.read_rdvxz_file_range(directory, start_timestamp_utc_s, end_timestamp_utc_s, redvox_ids,
                                            structured_layout, concat_continuous_segments)
    for redvox_id, wrapped_packets in all_data.items():
        # set station metadata and timing based on first packet
        timing = StationTiming(wrapped_packets[0].mach_time_zero(), start_timestamp_utc_s, end_timestamp_utc_s,
                               wrapped_packets[0].microphone_sensor().sample_rate_hz(),
                               wrapped_packets[0].app_file_start_timestamp_epoch_microseconds_utc(),
                               wrapped_packets[0].best_latency(), wrapped_packets[0].best_offset())
        metadata = StationMetadata(redvox_id, wrapped_packets[0].device_make(), wrapped_packets[0].device_model(),
                                   wrapped_packets[0].device_os(), wrapped_packets[0].device_os_version(),
                                   "Redvox", wrapped_packets[0].app_version(), timing)
        # add data from packets
        packet_dict: Dict[int, DataPacket] = {}
        for packet in wrapped_packets:
            data_dict = read_api900_wrapped_packet(packet)
            packet_data = DataPacket(packet.server_timestamp_epoch_microseconds_utc(), data_dict,
                                     packet.start_timestamp_us_utc(), packet.end_timestamp_us_utc(),
                                     packet.time_synchronization_sensor().payload_values(),
                                     packet.best_latency(), packet.best_offset())
            packet_dict[packet_data.packet_start_timestamp] = packet_data

        # create the Station data object
        all_stations.append(Station(metadata, packet_dict))

    return all_stations
