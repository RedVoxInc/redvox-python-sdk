"""
Defines generic sensor data and metadata for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
"""

import enum
import numpy as np
import pandas as pd

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from redvox.api1000 import io as apim_io
from redvox.api900 import reader as api900_io
from redvox.common import file_statistics as fs
from redvox.common import date_time_utils as dtu
from redvox.api1000.wrapped_redvox_packet.sensors import xyz, single
from redvox.api1000.wrapped_redvox_packet import wrapped_packet as apim_wp
from obspy import read


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
        sample_rate: float, sample rate of the sensor, default np.nan
        is_sample_rate_fixed: bool, True if sample rate is constant, default False
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
        server_timestamp: float, server timestamp of when data was received by the server
        packet_app_start_timestamp: float, machine timestamp of when app started
        sensor_data_dict: dict, all SensorData associated with this sensor; keys are SensorType, default empty dict
        data_start_timestamp: float, machine timestamp of the start of the packet's data, default np.nan
        data_end_timestamp: float, machine timestamp of the end of the packet's data, default np.nan
        timesync: optional np.array of of timesync data, default None
        packet_best_latency: float, best latency of data, default np.nan
        packet_best_offset: float, best offset of data, default 0.0
    """
    server_timestamp: float
    packet_app_start_timestamp: float
    sensor_data_dict: Dict[SensorType, SensorData] = field(default_factory=dict)
    data_start_timestamp: float = np.nan
    data_end_timestamp: float = np.nan
    timesync: Optional[np.array] = None
    packet_best_latency: float = np.nan
    packet_best_offset: float = 0.0

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
        :return: the edited DataPacket
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
        :return: location sensor if it exists, None otherwise
        """
        if self.has_location_sensor():
            return self.sensor_data_dict[SensorType.LOCATION]
        return None

    def set_location_sensor(self, loc_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the location sensor; can remove location sensor by passing None
        :param loc_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_location_sensor():
            self._delete_sensor(SensorType.LOCATION)
        if loc_sensor is not None:
            self._add_sensor(SensorType.LOCATION, loc_sensor)
        return self

    def has_accelerometer_sensor(self) -> bool:
        """
        check if accelerometer sensor is in sensor_data_dict
        :return: True if accelerometer sensor exists
        """
        return SensorType.ACCELEROMETER in self.sensor_data_dict.keys()

    def accelerometer_sensor(self) -> Optional[SensorData]:
        """
        return the accelerometer sensor if it exists
        :return: accelerometer sensor if it exists, None otherwise
        """
        if self.has_accelerometer_sensor():
            return self.sensor_data_dict[SensorType.ACCELEROMETER]
        return None

    def set_accelerometer_sensor(self, acc_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the accelerometer sensor; can remove accelerometer sensor by passing None
        :param acc_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_accelerometer_sensor():
            self._delete_sensor(SensorType.ACCELEROMETER)
        if acc_sensor is not None:
            self._add_sensor(SensorType.ACCELEROMETER, acc_sensor)
        return self

    def has_magnetometer_sensor(self) -> bool:
        """
        check if magnetometer sensor is in sensor_data_dict
        :return: True if magnetometer sensor exists
        """
        return SensorType.MAGNETOMETER in self.sensor_data_dict.keys()

    def magnetometer_sensor(self) -> Optional[SensorData]:
        """
        return the magnetometer sensor if it exists
        :return: magnetometer sensor if it exists, None otherwise
        """
        if self.has_magnetometer_sensor():
            return self.sensor_data_dict[SensorType.MAGNETOMETER]
        return None

    def set_magnetometer_sensor(self, mag_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the magnetometer sensor; can remove magnetometer sensor by passing None
        :param mag_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_magnetometer_sensor():
            self._delete_sensor(SensorType.MAGNETOMETER)
        if mag_sensor is not None:
            self._add_sensor(SensorType.MAGNETOMETER, mag_sensor)
        return self

    def has_gyroscope_sensor(self) -> bool:
        """
        check if gyroscope sensor is in sensor_data_dict
        :return: True if gyroscope sensor exists
        """
        return SensorType.GYROSCOPE in self.sensor_data_dict.keys()

    def gyroscope_sensor(self) -> Optional[SensorData]:
        """
        return the gyroscope sensor if it exists
        :return: gyroscope sensor if it exists, None otherwise
        """
        if self.has_gyroscope_sensor():
            return self.sensor_data_dict[SensorType.GYROSCOPE]
        return None

    def set_gyroscope_sensor(self, gyro_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the gyroscope sensor; can remove gyroscope sensor by passing None
        :param gyro_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_gyroscope_sensor():
            self._delete_sensor(SensorType.GYROSCOPE)
        if gyro_sensor is not None:
            self._add_sensor(SensorType.GYROSCOPE, gyro_sensor)
        return self

    def has_barometer_sensor(self) -> bool:
        """
        check if barometer sensor is in sensor_data_dict
        :return: True if barometer sensor exists
        """
        return SensorType.PRESSURE in self.sensor_data_dict.keys()

    def barometer_sensor(self) -> Optional[SensorData]:
        """
        return the barometer sensor if it exists
        :return: barometer sensor if it exists, None otherwise
        """
        if self.has_barometer_sensor():
            return self.sensor_data_dict[SensorType.PRESSURE]
        return None

    def set_barometer_sensor(self, bar_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the barometer sensor; can remove barometer sensor by passing None
        :param bar_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_barometer_sensor():
            self._delete_sensor(SensorType.PRESSURE)
        if bar_sensor is not None:
            self._add_sensor(SensorType.PRESSURE, bar_sensor)
        return self

    def has_light_sensor(self) -> bool:
        """
        check if light sensor is in sensor_data_dict
        :return: True if light sensor exists
        """
        return SensorType.LIGHT in self.sensor_data_dict.keys()

    def light_sensor(self) -> Optional[SensorData]:
        """
        return the light sensor if it exists
        :return: light sensor if it exists, None otherwise
        """
        if self.has_light_sensor():
            return self.sensor_data_dict[SensorType.LIGHT]
        return None

    def set_light_sensor(self, light_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the light sensor; can remove light sensor by passing None
        :param light_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_light_sensor():
            self._delete_sensor(SensorType.LIGHT)
        if light_sensor is not None:
            self._add_sensor(SensorType.LIGHT, light_sensor)
        return self

    def has_infrared_sensor(self) -> bool:
        """
        check if infrared sensor is in sensor_data_dict
        :return: True if infrared sensor exists
        """
        return SensorType.INFRARED in self.sensor_data_dict.keys()

    def infrared_sensor(self) -> Optional[SensorData]:
        """
        return the infrared sensor if it exists
        :return: infrared sensor if it exists, None otherwise
        """
        if self.has_infrared_sensor():
            return self.sensor_data_dict[SensorType.INFRARED]
        return None

    def set_infrared_sensor(self, infrd_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the infrared sensor; can remove infrared sensor by passing None
        :param infrd_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_infrared_sensor():
            self._delete_sensor(SensorType.INFRARED)
        if infrd_sensor is not None:
            self._add_sensor(SensorType.INFRARED, infrd_sensor)
        return self

    def has_image_sensor(self) -> bool:
        """
        check if image sensor is in sensor_data_dict
        :return: True if image sensor exists
        """
        return SensorType.IMAGE in self.sensor_data_dict.keys()

    def image_sensor(self) -> Optional[SensorData]:
        """
        return the image sensor if it exists
        :return: image sensor if it exists, None otherwise
        """
        if self.has_image_sensor():
            return self.sensor_data_dict[SensorType.IMAGE]
        return None

    def set_image_sensor(self, img_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the image sensor; can remove image sensor by passing None
        :param img_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_image_sensor():
            self._delete_sensor(SensorType.IMAGE)
        if img_sensor is not None:
            self._add_sensor(SensorType.IMAGE, img_sensor)
        return self

    def has_ambient_temperature_sensor(self) -> bool:
        """
        check if ambient temperature sensor is in sensor_data_dict
        :return: True if ambient temperature sensor exists
        """
        return SensorType.TEMPERATURE in self.sensor_data_dict.keys()

    def ambient_temperature_sensor(self) -> Optional[SensorData]:
        """
        return the ambient temperature sensor if it exists
        :return: image ambient temperature if it exists, None otherwise
        """
        if self.has_ambient_temperature_sensor():
            return self.sensor_data_dict[SensorType.TEMPERATURE]
        return None

    def set_ambient_temperature_sensor(self, amtemp_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the ambient temperature sensor; can remove ambient temperature sensor by passing None
        :param amtemp_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_ambient_temperature_sensor():
            self._delete_sensor(SensorType.TEMPERATURE)
        if amtemp_sensor is not None:
            self._add_sensor(SensorType.TEMPERATURE, amtemp_sensor)
        return self

    def has_gravity_sensor(self) -> bool:
        """
        check if gravity sensor is in sensor_data_dict
        :return: True if gravity sensor exists
        """
        return SensorType.GRAVITY in self.sensor_data_dict.keys()

    def gravity_sensor(self) -> Optional[SensorData]:
        """
        return the gravity sensor if it exists
        :return: gravity sensor if it exists, None otherwise
        """
        if self.has_gravity_sensor():
            return self.sensor_data_dict[SensorType.GRAVITY]
        return None

    def set_gravity_sensor(self, grav_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the gravity sensor; can remove gravity sensor by passing None
        :param grav_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_gravity_sensor():
            self._delete_sensor(SensorType.GRAVITY)
        if grav_sensor is not None:
            self._add_sensor(SensorType.GRAVITY, grav_sensor)
        return self

    def has_linear_acceleration_sensor(self) -> bool:
        """
        check if linear acceleration sensor is in sensor_data_dict
        :return: True if linear acceleration sensor exists
        """
        return SensorType.LINEAR_ACCELERATION in self.sensor_data_dict.keys()

    def linear_acceleration_sensor(self) -> Optional[SensorData]:
        """
        return the linear acceleration sensor if it exists
        :return: linear acceleration sensor if it exists, None otherwise
        """
        if self.has_linear_acceleration_sensor():
            return self.sensor_data_dict[SensorType.LINEAR_ACCELERATION]
        return None

    def set_linear_acceleration_sensor(self, linacc_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the linear acceleration sensor; can remove linear acceleration sensor by passing None
        :param linacc_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_linear_acceleration_sensor():
            self._delete_sensor(SensorType.LINEAR_ACCELERATION)
        if linacc_sensor is not None:
            self._add_sensor(SensorType.LINEAR_ACCELERATION, linacc_sensor)
        return self

    def has_orientation_sensor(self) -> bool:
        """
        check if orientation sensor is in sensor_data_dict
        :return: True if orientation sensor exists
        """
        return SensorType.ORIENTATION in self.sensor_data_dict.keys()

    def orientation_sensor(self) -> Optional[SensorData]:
        """
        return the orientation sensor if it exists
        :return: orientation sensor if it exists, None otherwise
        """
        if self.has_orientation_sensor():
            return self.sensor_data_dict[SensorType.ORIENTATION]
        return None

    def set_orientation_sensor(self, orient_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the orientation sensor; can remove orientation sensor by passing None
        :param orient_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_orientation_sensor():
            self._delete_sensor(SensorType.ORIENTATION)
        if orient_sensor is not None:
            self._add_sensor(SensorType.ORIENTATION, orient_sensor)
        return self

    def has_proximity_sensor(self) -> bool:
        """
        check if proximity sensor is in sensor_data_dict
        :return: True if proximity sensor exists
        """
        return SensorType.PROXIMITY in self.sensor_data_dict.keys()

    def proximity_sensor(self) -> Optional[SensorData]:
        """
        return the proximity sensor if it exists
        :return: proximity sensor if it exists, None otherwise
        """
        if self.has_proximity_sensor():
            return self.sensor_data_dict[SensorType.PROXIMITY]
        return None

    def set_proximity_sensor(self, prox_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the proximity sensor; can remove proximity sensor by passing None
        :param prox_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_proximity_sensor():
            self._delete_sensor(SensorType.PROXIMITY)
        if prox_sensor is not None:
            self._add_sensor(SensorType.PROXIMITY, prox_sensor)
        return self

    def has_relative_humidity_sensor(self) -> bool:
        """
        check if relative humidity sensor is in sensor_data_dict
        :return: True if linear relative humidity sensor exists
        """
        return SensorType.RELATIVE_HUMIDITY in self.sensor_data_dict.keys()

    def relative_humidity_sensor(self) -> Optional[SensorData]:
        """
        return the relative humidity sensor if it exists
        :return: relative humidity sensor if it exists, None otherwise
        """
        if self.has_relative_humidity_sensor():
            return self.sensor_data_dict[SensorType.RELATIVE_HUMIDITY]
        return None

    def set_relative_humidity_sensor(self, relhum_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the relative humidity sensor; can remove relative humidity sensor by passing None
        :param relhum_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_relative_humidity_sensor():
            self._delete_sensor(SensorType.RELATIVE_HUMIDITY)
        if relhum_sensor is not None:
            self._add_sensor(SensorType.RELATIVE_HUMIDITY, relhum_sensor)
        return self

    def has_rotation_vector_sensor(self) -> bool:
        """
        check if rotation vector sensor is in sensor_data_dict
        :return: True if rotation vector sensor exists
        """
        return SensorType.ROTATION_VECTOR in self.sensor_data_dict.keys()

    def rotation_vector_sensor(self) -> Optional[SensorData]:
        """
        return the rotation vector sensor if it exists
        :return: rotation vector sensor if it exists, None otherwise
        """
        if self.has_rotation_vector_sensor():
            return self.sensor_data_dict[SensorType.ROTATION_VECTOR]
        return None

    def set_rotation_vector_sensor(self, rotvec_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the rotation vector sensor; can remove rotation vector sensor by passing None
        :param rotvec_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_rotation_vector_sensor():
            self._delete_sensor(SensorType.ROTATION_VECTOR)
        if rotvec_sensor is not None:
            self._add_sensor(SensorType.ROTATION_VECTOR, rotvec_sensor)
        return self

    def has_compressed_audio_sensor(self) -> bool:
        """
        check if compressed audio sensor is in sensor_data_dict
        :return: True if compressed audio sensor exists
        """
        return SensorType.COMPRESSED_AUDIO in self.sensor_data_dict.keys()

    def compressed_audio_sensor(self) -> Optional[SensorData]:
        """
        return the compressed audio sensor if it exists
        :return: compressed audio sensor if it exists, None otherwise
        """
        if self.has_compressed_audio_sensor():
            return self.sensor_data_dict[SensorType.COMPRESSED_AUDIO]
        return None

    def set_compressed_audio_sensor(self, compaudio_sensor: Optional[SensorData]) -> 'DataPacket':
        """
        sets the compressed audio sensor; can remove compressed audio sensor by passing None
        :param compaudio_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_compressed_audio_sensor():
            self._delete_sensor(SensorType.COMPRESSED_AUDIO)
        if compaudio_sensor is not None:
            self._add_sensor(SensorType.COMPRESSED_AUDIO, compaudio_sensor)
        return self


@dataclass
class StationTiming:
    """
    Generic StationTiming class for API-independent analysis
    Properties:
        start_timestamp: float, timestamp when station started recording
        episode_start_timestamp_s: float, timestamp of start of segment of interest in seconds since epoch UTC
        episode_end_timestamp_s: float, timestamp of end of segment of interest in seconds since epoch UTC
        audio_sample_rate_hz: float, sample rate in hz of audio sensor
        station_first_data_timestamp: float, first timestamp chronologically of the data
        station_best_latency: float, best latency of data, default np.nan
        station_best_offset: float, best offset of data, default 0.0
    """
    station_start_timestamp: float
    episode_start_timestamp_s: int
    episode_end_timestamp_s: int
    audio_sample_rate_hz: float
    station_first_data_timestamp: float
    station_best_latency: float = np.nan
    station_best_offset: float = 0.0


@dataclass
class StationMetadata:
    """
    Generic StationMetadata class for API-independent analysis
    Properties:
        station_id: str, id of the station
        station_make: str, maker of the station
        station_model: str, model of the station
        station_os: optional str, operating system of the station, default None
        station_os_version: optional str, station OS version, default None
        station_app: optional str, the name of the recording software used by the station, default None
        station_app_version: optional str, the recording software version, default None
        is_mic_scrambled: optional bool, True if mic data is scrambled, default False
        timing_data: optional StationTiming metadata, default None
        station_calib: optional float, station calibration value, default None
        station_network_name: optional str, name/code of network station belongs to, default None
        station_name: optional str, name/code of station, default None
        station_location_name: optional str, name/code of location station is at, default None
        station_channel_name: optional str, name/code of channel station is recording, default None
        station_channel_encoding: optional str, name/code of channel encoding method, default None
    """
    station_id: str
    station_make: str
    station_model: str
    station_os: Optional[str] = None
    station_os_version: Optional[str] = None
    station_app: Optional[str] = None
    station_app_version: Optional[str] = None
    is_mic_scrambled: Optional[bool] = False
    timing_data: Optional[StationTiming] = None
    station_calib: Optional[float] = None
    station_network_name: Optional[str] = None
    station_name: Optional[str] = None
    station_location_name: Optional[str] = None
    station_channel_name: Optional[str] = None
    station_channel_encoding: Optional[str] = None


@dataclass
class Station:
    """
    generic station for api-independent stuff
    Properties:
        station_metadata: StationMetadata
        station_data: list, all DataPackets associated with this station, default empty list
    """
    station_metadata: StationMetadata
    station_data: List[DataPacket] = field(default_factory=list)


def _calc_evenly_sampled_timestamps(start: float, samples: int, rate_hz: float) -> np.array:
    """
    given a start time, calculates samples amount of evenly spaced timestamps at rate_hz
    :param start: float, start timestamp
    :param samples: int, number of samples
    :param rate_hz: float, sample rate in hz
    :return: np.array with evenly spaced timestamps starting at start
    """
    return np.array(start + dtu.seconds_to_microseconds(np.arange(0, samples) / rate_hz))


def read_api900_non_mic_sensor(sensor: api900_io.RedvoxSensor, packet_length_s: float, column_id: str) -> SensorData:
    """
    read a sensor that does not have mic data from an api900 data packet
    :param sensor: the non-mic api900 sensor to read
    :param packet_length_s: float, the length of the data packet in seconds
    :param column_id: string, used to name the columns
    :return: generic SensorData object
    """
    timestamps = sensor.timestamps_microseconds_utc()
    if type(sensor) in [api900_io.AccelerometerSensor, api900_io.MagnetometerSensor, api900_io.GyroscopeSensor]:
        data_for_df = np.transpose([sensor.payload_values_x(), sensor.payload_values_y(), sensor.payload_values_z()])
        columns = [f"{column_id}_x", f"{column_id}_y", f"{column_id}_z"]
    else:
        data_for_df = np.transpose(sensor.payload_values())
        columns = [column_id]
    return SensorData(sensor.sensor_name(), pd.DataFrame(data_for_df, index=timestamps, columns=columns),
                      packet_length_s / len(timestamps), False)


def read_api900_wrapped_packet(wrapped_packet: api900_io.WrappedRedvoxPacket) -> Dict[SensorType, SensorData]:
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
        timestamps = _calc_evenly_sampled_timestamps(
            wrapped_packet.microphone_sensor().first_sample_timestamp_epoch_microseconds_utc(),
            fs.get_num_points_from_sample_rate(sample_rate_hz), sample_rate_hz)
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
    api900_packet = api900_io.read_rdvxz_file(directory)
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
    reads in api900 data from a directory and returns a list of stations
    note that the param descriptions are taken directly from api900.reader.read_rdvxz_file_range
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
    all_data = api900_io.read_rdvxz_file_range(directory, start_timestamp_utc_s, end_timestamp_utc_s, redvox_ids,
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
                                     packet.start_timestamp_us_utc(), int(packet.end_timestamp_us_utc()),
                                     time_sync, packet.best_latency(), packet.best_offset())
            packet_list.append(packet_data)

        # create the Station data object
        all_stations.append(Station(metadata, packet_list))

    return all_stations


def read_apim_xyz_sensor(sensor: xyz, packet_length_s: float, column_id: str) -> SensorData:
    """
    read a sensor that has xyz data channels from an api M data packet
    :param sensor: the xyz api M sensor to read
    :param packet_length_s: float, the length of the data packet in seconds
    :param column_id: string, used to name the columns
    :return: generic SensorData object
    """
    timestamps = sensor.get_timestamps().get_timestamps()
    data_for_df = np.transpose([sensor.get_x_samples().get_values(),
                                sensor.get_y_samples().get_values(),
                                sensor.get_z_samples().get_values()])
    columns = [f"{column_id}_x", f"{column_id}_y", f"{column_id}_z"]
    return SensorData(sensor.get_sensor_description(), pd.DataFrame(data_for_df, index=timestamps, columns=columns),
                      packet_length_s / len(timestamps), False)


def read_apim_single_sensor(sensor: single, packet_length_s: float, column_id: str) -> SensorData:
    """
    read a sensor that has a single data channel from an api M data packet
    :param sensor: the single channel api M sensor to read
    :param packet_length_s: float, the length of the data packet in seconds
    :param column_id: string, used to name the columns
    :return: generic SensorData object
    """
    timestamps = sensor.get_timestamps().get_timestamps()
    data_for_df = np.transpose([sensor.get_samples().get_values()])
    columns = [column_id]
    return SensorData(sensor.get_sensor_description(), pd.DataFrame(data_for_df, index=timestamps, columns=columns),
                      packet_length_s / len(timestamps), False)


def load_apim_wrapped_packet(wrapped_packet: apim_wp.WrappedRedvoxPacketM) -> Dict[SensorType, SensorData]:
    """
    reads the data from a wrapped api M redvox packet into a dictionary of generic data
    :param wrapped_packet: a wrapped api M redvox packet
    :return: a dictionary containing all the sensor data
    """
    packet_length_s: float = wrapped_packet.get_timing_information().get_packet_end_mach_timestamp() - \
        wrapped_packet.get_timing_information().get_packet_start_mach_timestamp()
    data_dict: Dict[SensorType, SensorData] = {}
    sensors = wrapped_packet.get_sensors()
    # there are 16 api M sensors
    if sensors.has_audio():
        sample_rate_hz = sensors.get_audio().get_sample_rate()
        data_for_df = sensors.get_audio().get_samples().get_values()
        timestamps = _calc_evenly_sampled_timestamps(sensors.get_audio().get_first_sample_timestamp(),
                                                     len(data_for_df), sample_rate_hz)
        data_dict[SensorType.AUDIO] = SensorData(sensors.get_audio().get_sensor_description(),
                                                 pd.DataFrame(data_for_df, index=timestamps, columns=["microphone"]),
                                                 sample_rate_hz, True)
    if sensors.has_compress_audio():
        sample_rate_hz = sensors.get_compressed_audio().get_sample_rate()
        data_for_df = sensors.get_compressed_audio().get_samples().get_values()
        timestamps = _calc_evenly_sampled_timestamps(sensors.get_compressed_audio().get_first_sample_timestamp(),
                                                     len(data_for_df), sample_rate_hz)
        data_dict[SensorType.COMPRESSED_AUDIO] = SensorData(sensors.get_compressed_audio().get_sensor_description(),
                                                            pd.DataFrame(data_for_df, index=timestamps,
                                                                         columns=["compressed_audio"]),
                                                            sample_rate_hz, True)
    if sensors.has_accelerometer():
        data_dict[SensorType.ACCELEROMETER] = read_apim_xyz_sensor(sensors.get_accelerometer(),
                                                                   packet_length_s, "accelerometer")
    if sensors.has_magnetometer():
        data_dict[SensorType.MAGNETOMETER] = read_apim_xyz_sensor(sensors.get_magnetometer(),
                                                                  packet_length_s, "magnetometer")
    if sensors.has_linear_acceleration():
        data_dict[SensorType.LINEAR_ACCELERATION] = read_apim_xyz_sensor(sensors.get_linear_acceleration(),
                                                                         packet_length_s, "linear_accel")
    if sensors.has_orientation():
        data_dict[SensorType.ORIENTATION] = read_apim_xyz_sensor(sensors.get_orientation(),
                                                                 packet_length_s, "orientation")
    if sensors.has_rotation_vector():
        data_dict[SensorType.ROTATION_VECTOR] = read_apim_xyz_sensor(sensors.get_rotation_vector(),
                                                                     packet_length_s, "rotation_vector")
    if sensors.has_gyroscope():
        data_dict[SensorType.GYROSCOPE] = read_apim_xyz_sensor(sensors.get_gyroscope(), packet_length_s, "gyroscope")
    if sensors.has_gravity():
        data_dict[SensorType.GRAVITY] = read_apim_xyz_sensor(sensors.get_gravity(), packet_length_s, "gravity")
    if sensors.has_pressure():
        data_dict[SensorType.PRESSURE] = read_apim_single_sensor(sensors.get_pressure(), packet_length_s, "barometer")
    if sensors.has_light():
        data_dict[SensorType.LIGHT] = read_apim_single_sensor(sensors.get_light(), packet_length_s, "light")
    if sensors.has_proximity():
        data_dict[SensorType.PROXIMITY] = read_apim_single_sensor(sensors.get_proximity(), packet_length_s, "proximity")
    if sensors.has_ambient_temperature():
        data_dict[SensorType.TEMPERATURE] = read_apim_single_sensor(sensors.get_ambient_temperature(),
                                                                    packet_length_s, "ambient_temp")
    if sensors.has_relative_humidity():
        data_dict[SensorType.RELATIVE_HUMIDITY] = read_apim_single_sensor(sensors.get_relative_humidity(),
                                                                          packet_length_s, "rel_humidity")
    if sensors.has_image():
        timestamps = sensors.get_image().get_timestamps().get_timestamps()
        data_for_df = sensors.get_image().get_samples()
        data_dict[SensorType.IMAGE] = SensorData(sensors.get_image().get_sensor_description(),
                                                 pd.DataFrame(data_for_df, index=timestamps, columns=["image"]),
                                                 packet_length_s / len(timestamps), False)
    if sensors.has_location():
        timestamps = sensors.get_location().get_timestamps().get_timestamps()
        data_for_df = np.transpose([sensors.get_location().get_latitude_samples().get_values(),
                                    sensors.get_location().get_longitude_samples().get_values(),
                                    sensors.get_location().get_altitude_samples().get_values(),
                                    sensors.get_location().get_speed_samples().get_values(),
                                    sensors.get_location().get_bearing_samples().get_values(),
                                    sensors.get_location().get_horizontal_accuracy_samples().get_values(),
                                    sensors.get_location().get_vertical_accuracy_samples().get_values(),
                                    sensors.get_location().get_speed_samples().get_values(),
                                    sensors.get_location().get_bearing_accuracy_samples().get_values()])
        columns = ["latitude", "longitude", "altitude", "speed", "bearing",
                   "horizonal_accuracy", "vertical_accuracy", "speed_accuracy", "bearing_accuracy"]
        data_dict[SensorType.LOCATION] = SensorData(sensors.get_location().get_sensor_description(),
                                                    pd.DataFrame(data_for_df, index=timestamps, columns=columns),
                                                    packet_length_s / len(timestamps), False)
    return data_dict


def load_station_from_apim(directory: str, start_timestamp_utc_s: Optional[int] = None,
                           end_timestamp_utc_s: Optional[int] = None) -> Station:
    """
    reads in station data from a single api M file
    :param directory: string of the file to read from
    :param start_timestamp_utc_s: The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: The end timestamp as seconds since the epoch UTC.
    :return: a station Object
    """
    read_packet = apim_io.read_rdvxm_file(directory)
    # set station metadata and timing based on first packet
    timing = StationTiming(read_packet.get_timing_information().get_app_start_mach_timestamp(),
                           start_timestamp_utc_s, end_timestamp_utc_s,
                           read_packet.get_sensors().get_audio().get_sample_rate(),
                           read_packet.get_sensors().get_audio().get_first_sample_timestamp(),
                           read_packet.get_timing_information().get_best_latency(),
                           read_packet.get_timing_information().get_best_offset())
    metadata = StationMetadata(read_packet.get_station_information().get_id(),
                               read_packet.get_station_information().get_make(),
                               read_packet.get_station_information().get_model(),
                               read_packet.get_station_information().get_os().name,
                               read_packet.get_station_information().get_os_version(), "Redvox",
                               read_packet.get_station_information().get_app_version(),
                               read_packet.get_station_information().get_app_settings().get_scramble_audio_data(),
                               timing)
    # add data from packets
    time_sync = np.array(read_packet.get_timing_information().get_synch_exchanges().get_values())
    data_dict = load_apim_wrapped_packet(read_packet)
    packet_data = DataPacket(read_packet.get_timing_information().get_server_acquisition_arrival_timestamp(),
                             read_packet.get_timing_information().get_app_start_mach_timestamp(), data_dict,
                             read_packet.get_timing_information().get_packet_start_mach_timestamp(),
                             read_packet.get_timing_information().get_packet_end_mach_timestamp(),
                             time_sync, read_packet.get_timing_information().get_best_latency(),
                             read_packet.get_timing_information().get_best_offset())
    packet_list: List[DataPacket] = [packet_data]
    return Station(metadata, packet_list)


def load_from_file_range_api_m(directory: str,
                               start_timestamp_utc_s: Optional[int] = None,
                               end_timestamp_utc_s: Optional[int] = None,
                               redvox_ids: Optional[List[str]] = None,
                               structured_layout: bool = False) -> List[Station]:
    """
    reads in api M data from a directory and returns a list of stations
    :param directory: The root directory of the data. If structured_layout is False, then this directory will
                      contain various unorganized .rdvxz files. If structured_layout is True, then this directory
                      must be the root api1000 directory of the structured files.
    :param start_timestamp_utc_s: The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: The end timestamp as seconds since the epoch UTC.
    :param redvox_ids: An optional list of redvox_ids to filter against, default empty list
    :param structured_layout: An optional value to define if this is loading structured data, default False.
    :return: a list of Station objects that contain the data
    """
    all_stations: List[Station] = []
    all_data = apim_io.read_structured(directory, start_timestamp_utc_s, end_timestamp_utc_s, redvox_ids,
                                       structured_layout)
    for read_packets in all_data.all_wrapped_packets:
        # set station metadata and timing based on first packet
        timing = StationTiming(read_packets.start_mach_timestamp,
                               start_timestamp_utc_s, end_timestamp_utc_s, read_packets.audio_sample_rate,
                               read_packets.wrapped_packets[0].get_sensors().get_audio().get_first_sample_timestamp(),
                               read_packets.wrapped_packets[0].get_timing_information().get_best_latency(),
                               read_packets.wrapped_packets[0].get_timing_information().get_best_offset())
        metadata = StationMetadata(read_packets.redvox_id,
                                   read_packets.wrapped_packets[0].get_station_information().get_make(),
                                   read_packets.wrapped_packets[0].get_station_information().get_model(),
                                   read_packets.wrapped_packets[0].get_station_information().get_os().name,
                                   read_packets.wrapped_packets[0].get_station_information().get_os_version(),
                                   "Redvox",
                                   read_packets.wrapped_packets[0].get_station_information().get_app_version(),
                                   read_packets.wrapped_packets[0].get_station_information().get_app_settings().
                                   get_scramble_audio_data(),
                                   timing)
        # add data from packets
        packet_list: List[DataPacket] = []
        for packet in read_packets.wrapped_packets:
            time_sync = np.array(packet.get_timing_information().get_synch_exchanges().get_values())
            data_dict = load_apim_wrapped_packet(packet)
            packet_data = DataPacket(packet.get_timing_information().get_server_acquisition_arrival_timestamp(),
                                     packet.get_timing_information().get_app_start_mach_timestamp(), data_dict,
                                     packet.get_timing_information().get_packet_start_mach_timestamp(),
                                     packet.get_timing_information().get_packet_end_mach_timestamp(),
                                     time_sync, packet.get_timing_information().get_best_latency(),
                                     packet.get_timing_information().get_best_offset())
            packet_list.append(packet_data)

        # create the Station data object
        all_stations.append(Station(metadata, packet_list))
    return all_stations


def load_from_mseed(directory: str) -> List[Station]:
    """
    load station data from a miniseed file
    :param directory: the location of the miniseed file
    :return: a list of Station objects that contain the data
    """
    stations: List[Station] = []
    st = read(directory)
    for data_stream in st:
        record_info = data_stream.meta
        start_time = int(dtu.seconds_to_microseconds(data_stream.meta["starttime"].timestamp))
        end_time = int(dtu.seconds_to_microseconds(data_stream.meta["endtime"].timestamp))
        station_timing = StationTiming(np.nan, start_time, end_time, record_info["sampling_rate"], start_time)
        metadata = StationMetadata(record_info["network"] + record_info["station"] + "_" + record_info["location"],
                                   "mb3_make", "mb3_model", "mb3_os", "mb3_os_vers", "mb3_recorder",
                                   "mb3_recorder_version", False, station_timing, record_info["calib"],
                                   record_info["network"], record_info["station"], record_info["location"],
                                   record_info["channel"], record_info["mseed"]["encoding"])
        sample_rate_hz = record_info["sampling_rate"]
        data_for_df = data_stream.data
        timestamps = _calc_evenly_sampled_timestamps(start_time, int(record_info["npts"]), sample_rate_hz)
        sensor_data = SensorData(record_info["channel"], pd.DataFrame(data_for_df, index=timestamps, columns=["BDF"]),
                                 record_info["sampling_rate"], True)
        data_packet = DataPacket(np.nan, start_time, {SensorType.AUDIO: sensor_data}, start_time, end_time)
        stations.append(Station(metadata, [data_packet]))
    return stations
