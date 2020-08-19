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
    packet_best_latency: Optional[float] = np.nan
    packet_best_offset: Optional[float] = 0.0

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
    audio_sample_rate_hz: float
    station_first_data_timestamp: float
    episode_start_timestamp_s: Optional[int] = np.nan
    episode_end_timestamp_s: Optional[int] = np.nan
    station_best_latency: Optional[float] = np.nan
    station_best_offset: Optional[float] = 0.0


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
