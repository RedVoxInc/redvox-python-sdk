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
from redvox.common import file_statistics as fs


class SensorType(enum.Enum):
    """
    Enumeration of possible types of sensors to read data from
    """
    UNKNOWN_SENSOR = 0          # unknown sensor
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
    INFRARED = 17               # lux????


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
    sample_rate: float = np.nan
    is_sample_rate_fixed: bool = False

    def sensor_timestamps(self) -> List[str]:
        """
        get the timestamps from the dataframe
        :return: a list of timestamps
        """
        return self.data_df.index.to_list()

    def first_data_timestamp(self) -> int:
        """
        get the first timestamp of the data
        :return: timestamp of the first data point
        """
        return self.data_df.index[0]

    def num_samples(self) -> int:
        """
        get the number of samples in the dataframe
        :return: the number of rows in the dataframe
        """
        return self.data_df.shape[0]

    def sensor_data_fields(self) -> List[str]:
        """
        get the data fields of the sensor
        :return: the names of the data fields of the sensor
        """
        return self.data_df.columns.to_list()


@dataclass
class DataPacket:
    """
    Generic DataPacket class for API-independent analysis
    Properties:
        server_timestamp: int, server timestamp of when data was received by the server
        packet_app_start_timestamp: float, machine timestamp of when app started
        sensor_data_dict: dict, all SensorData associated with this sensor; keys are SensorType
        packet_start_timestamp: int, machine timestamp of the start of the packet
        packet_end_timestamp: int, machine timestamp of the end of the packet
        timesync: optional np.array of of timesync data
        packet_best_latency: optional float, best latency of data
        packet_best_offset: optional int, best offset of data
    """
    server_timestamp: int
    packet_app_start_timestamp: int
    sensor_data_dict: Dict[SensorType, SensorData] = field(default_factory=dict)
    packet_start_timestamp: int = 0
    packet_end_timestamp: int = 1
    timesync: Optional[np.array] = None
    packet_best_latency: Optional[float] = None
    packet_best_offset: Optional[int] = 0

    def _delete_sensor(self, sensor_type: SensorType):
        """
        removes a sensor from the data packet if it exists
        :param sensor_type: the sensor to remove
        """
        if sensor_type in self.sensor_data_dict.keys():
            self.sensor_data_dict.pop(sensor_type)

    def _add_sensor(self, sensor_type: SensorType, sensor: SensorData):
        """
        adds a sensor to the sensor_data_dict
        :param sensor_type: the type of sensor to add
        :param sensor: the sensor data to add
        """
        if sensor_type in self.sensor_data_dict.keys():
            raise ValueError(f"Cannot add sensor type ({sensor_type.name}) that already exists in packet!")
        else:
            self.sensor_data_dict[sensor_type] = sensor

    def has_audio_sensor(self) -> bool:
        """
        check if audio sensor is in sensor_data_dict
        :return: True if audio sensor exists
        """
        return SensorType.AUDIO in self.sensor_data_dict.keys()

    def audio_sensor(self) -> Optional[SensorData]:
        """
        return the audio sensor if it exists
        :return: audio sensor if it exists, None otherwise
        """
        if self.has_audio_sensor():
            return self.sensor_data_dict[SensorType.AUDIO]
        return None

    def set_audio_sensor(self, audio_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the audio sensor; can remove audio sensor by passing None
        :param audio_sensor: the SensorData to set or None
        """
        if self.has_audio_sensor():
            self._delete_sensor(SensorType.AUDIO)
        if audio_sensor is not None:
            self._add_sensor(SensorType.AUDIO, audio_sensor)
        return self

    def has_location_sensor(self) -> bool:
        """
        check if location sensor is in sensor_data_dict
        :return: True if location sensor exists
        """
        return SensorType.LOCATION in self.sensor_data_dict.keys()

    def location_sensor(self) -> Optional[SensorData]:
        """
        return the location sensor if it exists
        :return: audio location if it exists, None otherwise
        """
        if self.has_location_sensor():
            return self.sensor_data_dict[SensorType.LOCATION]
        return None


@dataclass
class StationTiming:
    """
    Generic StationTiming class for API-independent analysis
    Properties:
        start_timestamp: int, timestamp when station started recording
        episode_start_timestamp: int, timestamp of start of segment of interest
        episode_end_timestamp: int, timestamp of end of segment of interest
        audio_sample_rate_hz: float, sample rate in hz of audio sensor
        station_first_data_timestamp: int, first timestamp chronologically of the data
        station_best_latency: optional float, best latency of data
        station_best_offset: optional int, best offset of data
    """
    station_start_timestamp: int
    episode_start_timestamp: int
    episode_end_timestamp: int
    audio_sample_rate_hz: float
    station_first_data_timestamp: int
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
        is_mic_scrambled: bool, True if mic data is scrambled
        timing_data: StationTiming metadata
    """
    station_id: str
    station_make: str
    station_model: str
    station_os: str
    station_os_version: str
    station_app: str
    station_app_version: str
    is_mic_scrambled: bool
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
    station_data: List[DataPacket] = field(default_factory=dict)


def read_api900_non_mic_sensor(sensor: reader.RedvoxSensor, packet_length_s: float, column_id: str) -> SensorData:
    """
    read a sensor that does not have mic data from an api900 data packet
    :param sensor: the non-mic api900 sensor to read
    :param packet_length_s: float, the length of the data packet in seconds
    :param column_id: string, used to name the columns
    :return: generic SensorData object
    """
    timestamps = sensor.timestamps_microseconds_utc()
    if type(sensor) in [reader.AccelerometerSensor, reader.MagnetometerSensor, reader.GyroscopeSensor]:
        data_for_df = np.transpose([sensor.payload_values_x(), sensor.payload_values_y(), sensor.payload_values_z()])
        columns = [f"{column_id}_x", f"{column_id}_y", f"{column_id}_z"]
    else:
        data_for_df = np.transpose(sensor.payload_values())
        columns = [column_id]
    return SensorData(sensor.sensor_name(), pd.DataFrame(data_for_df, index=timestamps, columns=columns),
                      packet_length_s / len(timestamps), False)


def read_api900_wrapped_packet(wrapped_packet: reader.WrappedRedvoxPacket) -> Dict[SensorType, SensorData]:
    """
    reads the data from a wrapped api900 redvox packet into a dictionary of generic data
    :param wrapped_packet: a wrapped api900 redvox packet
    :return: a dictionary containing all the sensor data
    """
    packet_length_s: float = wrapped_packet.duration_s()
    data_dict: Dict[SensorType, SensorData] = {}
    # there are 9 api900 sensors
    if wrapped_packet.has_microphone_sensor():
        sample_rate_hz = wrapped_packet.microphone_sensor().sample_rate_hz()
        data_for_df = wrapped_packet.microphone_sensor().payload_values()
        timestamps = np.transpose(wrapped_packet.microphone_sensor().first_sample_timestamp_epoch_microseconds_utc() +
                                  (np.arange(0, fs.get_num_points_from_sample_rate(sample_rate_hz)) / sample_rate_hz))
        data_dict[SensorType.AUDIO] = SensorData(wrapped_packet.microphone_sensor().sensor_name(),
                                                 pd.DataFrame(data_for_df, index=timestamps, columns=["microphone"]),
                                                 sample_rate_hz, True)
    if wrapped_packet.has_accelerometer_sensor():
        data_dict[SensorType.ACCELEROMETER] = read_api900_non_mic_sensor(wrapped_packet.accelerometer_sensor(),
                                                                         packet_length_s, "accelerometer")
    if wrapped_packet.has_magnetometer_sensor():
        data_dict[SensorType.MAGNETOMETER] = read_api900_non_mic_sensor(wrapped_packet.magnetometer_sensor(),
                                                                        packet_length_s, "magnetometer")
    if wrapped_packet.has_gyroscope_sensor():
        data_dict[SensorType.GYROSCOPE] = read_api900_non_mic_sensor(wrapped_packet.gyroscope_sensor(),
                                                                     packet_length_s, "gyroscope")
    if wrapped_packet.has_barometer_sensor():
        data_dict[SensorType.PRESSURE] = read_api900_non_mic_sensor(wrapped_packet.barometer_sensor(),
                                                                    packet_length_s, "barometer")
    if wrapped_packet.has_light_sensor():
        data_dict[SensorType.LIGHT] = read_api900_non_mic_sensor(wrapped_packet.light_sensor(),
                                                                 packet_length_s, "light")
    if wrapped_packet.has_infrared_sensor():
        data_dict[SensorType.INFRARED] = read_api900_non_mic_sensor(wrapped_packet.infrared_sensor(),
                                                                    packet_length_s, "infrared")
    if wrapped_packet.has_image_sensor():
        data_dict[SensorType.IMAGE] = read_api900_non_mic_sensor(wrapped_packet.image_sensor(),
                                                                 packet_length_s, "image")
    if wrapped_packet.has_location_sensor():
        timestamps = wrapped_packet.location_sensor().timestamps_microseconds_utc()
        data_for_df = np.transpose([wrapped_packet.location_sensor().payload_values_latitude(),
                                    wrapped_packet.location_sensor().payload_values_longitude(),
                                    wrapped_packet.location_sensor().payload_values_altitude(),
                                    wrapped_packet.location_sensor().payload_values_speed(),
                                    wrapped_packet.location_sensor().payload_values_accuracy()])
        columns = ["latitude", "longitude", "altitude", "speed", "accuracy"]
        data_dict[SensorType.LOCATION] = SensorData(wrapped_packet.location_sensor().sensor_name(),
                                                    pd.DataFrame(data_for_df, index=timestamps, columns=columns),
                                                    packet_length_s / len(timestamps), False)
    return data_dict


def load_station_from_api900(directory: str, start_timestamp_utc_s: Optional[int] = None,
                             end_timestamp_utc_s: Optional[int] = None) -> Station:
    """
    reads in station data from a single api900 file
    :param directory: string of the file to read from
    :param start_timestamp_utc_s: The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: The end timestamp as seconds since the epoch UTC.
    :return: a station Object
    """
    api900_packet = reader.read_rdvxz_file(directory)
    # set station metadata and timing based on first packet
    timing = StationTiming(api900_packet.mach_time_zero(), start_timestamp_utc_s, end_timestamp_utc_s,
                           api900_packet.microphone_sensor().sample_rate_hz(),
                           api900_packet.app_file_start_timestamp_epoch_microseconds_utc(),
                           api900_packet.best_latency(), api900_packet.best_offset())
    metadata = StationMetadata(api900_packet.redvox_id(), api900_packet.device_make(), api900_packet.device_model(),
                               api900_packet.device_os(), api900_packet.device_os_version(),
                               "Redvox", api900_packet.app_version(), api900_packet.is_scrambled(), timing)
    data_dict = read_api900_wrapped_packet(api900_packet)
    packet_data = DataPacket(api900_packet.server_timestamp_epoch_microseconds_utc(),
                             api900_packet.app_file_start_timestamp_machine(), data_dict,
                             api900_packet.start_timestamp_us_utc(), int(api900_packet.end_timestamp_us_utc()),
                             api900_packet.time_synchronization_sensor().payload_values(),
                             api900_packet.best_latency(), api900_packet.best_offset())
    packet_list: List[DataPacket] = [packet_data]
    return Station(metadata, packet_list)


def load_file_range_from_api900(directory: str,
                                start_timestamp_utc_s: Optional[int] = None,
                                end_timestamp_utc_s: Optional[int] = None,
                                redvox_ids: Optional[List[str]] = None,
                                structured_layout: bool = False,
                                concat_continuous_segments: bool = True) -> List[Station]:
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
                                   "Redvox", wrapped_packets[0].app_version(), wrapped_packets[0].is_scrambled(),
                                   timing)
        # add data from packets
        packet_list: List[DataPacket] = []
        for packet in wrapped_packets:
            if packet.has_time_synchronization_sensor():
                time_sync = packet.time_synchronization_sensor().payload_values()
            else:
                time_sync = None
            data_dict = read_api900_wrapped_packet(packet)
            packet_data = DataPacket(packet.server_timestamp_epoch_microseconds_utc(),
                                     packet.app_file_start_timestamp_machine(), data_dict,
                                     packet.start_timestamp_us_utc(), packet.end_timestamp_us_utc(),
                                     time_sync, packet.best_latency(), packet.best_offset())
            packet_list.append(packet_data)

        # create the Station data object
        all_stations.append(Station(metadata, packet_list))

    return all_stations
