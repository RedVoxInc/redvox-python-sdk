"""
Defines generic sensor data and metadata for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
"""
import enum
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import redvox.common.date_time_utils as dtu


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
    INFRARED = 17               # this is proximity


@dataclass
class SensorData:
    """
    Generic SensorData class for API-independent analysis
    Properties:
        name: string, name of sensor
        data_df: dataframe of the sensor data; always has timestamps as the first column,
                    the other columns are the data fields
        sample_rate: float, sample rate in Hz of the sensor, default np.nan, usually 1/sample_interval_s
        sample_interval: float, mean duration in seconds between samples, default np.nan, usually 1/sample_rate
        is_sample_rate_fixed: bool, True if sample rate is constant, default False
    """
    name: str
    data_df: pd.DataFrame
    sample_rate: float = np.nan
    sample_interval_s: float = np.nan
    is_sample_rate_fixed: bool = False

    def copy(self) -> 'SensorData':
        """
        :return: An exact copy of the SensorData object
        """
        return SensorData(self.name, self.data_df.copy(), self.sample_rate, self.is_sample_rate_fixed)

    def is_sample_interval_invalid(self) -> bool:
        """
        :return: True if sample interval is np.nan or equal to 0.0
        """
        return np.isnan(self.sample_interval_s) or self.sample_interval_s == 0.0

    def append_data(self, new_data: pd.DataFrame) -> 'SensorData':
        """
        append the new data to the dataframe, updating the sample interval and sample rate if its not fixed
            only considers non-nan values for the interval and sample rate
        :return: the updated SensorData object
        """
        timestamps = np.array(self.data_timestamps())
        self.data_df = pd.concat([self.data_df, new_data], ignore_index=True)
        if not self.is_sample_rate_fixed:
            if len(new_data["timestamps"].to_numpy()) > 1:
                if np.isnan(self.sample_interval_s):
                    self.sample_interval_s = \
                        dtu.microseconds_to_seconds(float(np.mean(np.diff(new_data["timestamps"].to_numpy()))))
                else:
                    self.sample_interval_s = dtu.microseconds_to_seconds(float(np.mean(
                        np.concatenate([np.diff(timestamps), np.diff(new_data["timestamps"].to_numpy())]))))
            else:
                timestamps = np.array(self.data_timestamps())
                # try getting the sample interval based on the new ensemble
                if len(timestamps) > 1:
                    self.sample_interval_s = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
        if self.is_sample_interval_invalid():
            self.sample_rate = np.nan
        else:
            self.sample_rate = 1 / self.sample_interval_s
        return self

    def samples(self) -> np.ndarray:
        """
        gets the samples of dataframe
        :return: the data values of the dataframe as a numpy ndarray
        """
        return self.data_df.iloc[:, 1:].T.to_numpy(dtype=float)

    def get_channel(self, channel_name: str) -> np.array:
        """
        gets the channel specified
        :param channel_name: the name of the channel to get data for
        :return: the data values of the channel as a numpy array
        """
        if channel_name not in self.data_df.columns:
            raise ValueError(f"WARNING: {channel_name} does not exist; try one of {self.data_fields()}")
        return self.data_df[channel_name].to_numpy(dtype=float)

    def get_valid_channel_values(self, channel_name: str) -> np.array:
        """
        gets all non-nan values from the channel specified
        :param channel_name: the name of the channel to get data for
        :return: non-nan values of the channel as a numpy array
        """
        channel_data = self.get_channel(channel_name)
        return channel_data[~np.isnan(channel_data)]

    def data_timestamps(self) -> np.array:
        """
        get the timestamps from the dataframe
        :return: the timestamps as a numpy array
        """
        return self.data_df["timestamps"].to_numpy(dtype=float)

    def first_data_timestamp(self) -> float:
        """
        get the first timestamp of the data
        :return: timestamp of the first data point
        """
        return self.data_df["timestamps"].iloc[0]

    def last_data_timestamp(self) -> float:
        """
        get the last timestamp of the data
        :return: timestamp of the last data point
        """
        return self.data_df["timestamps"].iloc[-1]

    def num_samples(self) -> int:
        """
        get the number of samples in the dataframe
        :return: the number of rows in the dataframe
        """
        return self.data_df.shape[0]

    def data_duration_s(self) -> float:
        """
        calculate the duration in seconds of the dataframe: last - first timestamp if enough data, otherwise np.nan
        :return: duration in seconds of the dataframe
        """
        if self.num_samples() > 1:
            return dtu.microseconds_to_seconds(self.last_data_timestamp() - self.first_data_timestamp())
        return np.nan

    def data_fields(self) -> List[str]:
        """
        get the data fields of the sensor
        :return: a list of the names of the data fields of the sensor
        """
        return self.data_df.columns.to_list()

    def update_data_timestamps(self, time_delta: float):
        """
        adds the time_delta to the sensor's timestamps; use negative values to go backwards in time
        :param time_delta: time to add to sensor's timestamps
        """
        new_timestamps = self.data_timestamps() + time_delta
        self.data_df["timestamps"] = new_timestamps

    def sort_by_data_timestamps(self, ascending: bool = True):
        """
        sorts the data based on timestamps
        :param ascending: if True, timestamps are sorted in ascending order
        """
        self.data_df = self.data_df.sort_values("timestamps", ascending=ascending)


@dataclass
class DataPacket:
    """
    Generic DataPacket class for API-independent analysis
    Properties:
        server_timestamp: float, server timestamp of when data was received by the server
        packet_app_start_timestamp: float, machine timestamp of when app started
        packet_num_audio_samples: int, number of audio samples in the data packet, default 0
        packet_duration_s: float, duration of data packet in seconds, default 0.0
        data_start_timestamp: float, machine timestamp of the start of the packet's data, default np.nan
        data_end_timestamp: float, machine timestamp of the end of the packet's data, default np.nan
        timesync: optional np.array of of timesync data, default None
        packet_best_latency: float, best latency of data, default np.nan
        packet_best_offset: float, best offset of data, default 0.0
        sample_interval_to_next_packet: float, the length of time in microseconds between samples to reach the next
                                        packet's (in the station's data) start time, default np.nan
                                        does not have to match self.expected_sample_interval_s (when converted to same
                                        units), but ideally should be close to it
    """
    server_timestamp: float
    packet_app_start_timestamp: float
    packet_num_audio_samples: int = 0
    packet_duration_s: float = 0.0
    data_start_timestamp: float = np.nan
    data_end_timestamp: float = np.nan
    timesync: Optional[np.array] = None
    packet_best_latency: float = np.nan
    packet_best_offset: float = 0.0
    sample_interval_to_next_packet: float = np.nan

    def expected_sample_interval_s(self) -> float:
        """
        the packet's expected sample interval based on its own data
        :return: the packet's expected sample interval in seconds
        """
        return self.packet_duration_s / self.packet_num_audio_samples


@dataclass
class StationTiming:
    """
    Generic StationTiming class for API-independent analysis
    Properties:
        start_timestamp: float, timestamp when station started recording
        audio_sample_rate_hz: float, sample rate in hz of audio sensor
        station_first_data_timestamp: float, first timestamp chronologically of the data
        episode_start_timestamp_s: float, timestamp of start of segment of interest in seconds since epoch UTC,
                                    default np.nan
        episode_end_timestamp_s: float, timestamp of end of segment of interest in seconds since epoch UTC,
                                    default np.nan
        station_best_latency: float, best latency of data, default np.nan
        station_best_offset: float, best offset of data, default 0.0
    """
    station_start_timestamp: float
    audio_sample_rate_hz: float
    station_first_data_timestamp: float
    episode_start_timestamp_s: float = np.nan
    episode_end_timestamp_s: float = np.nan
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
        station_timing_is_corrected: bool, if True, the station's timestamps have been altered from their raw values
                                        default False
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
        station_uuid: optional str, uuid of the station, default is the same value as station_id
    """
    station_id: str
    station_make: str
    station_model: str
    station_timing_is_corrected: bool = False
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
    station_uuid: Optional[str] = None

    def __post_init__(self):
        """
        if the station_uuid is None, set it to be station_id
        """
        if not self.station_uuid:
            self.station_uuid = self.station_id


@dataclass
class Station:
    """
    generic station for api-independent stuff
    Properties:
        station_metadata: StationMetadata
        station_data: dict, all the data associated with this station, default empty dict
        packet_data: list, all DataPacket metadata associated with this station, default empty list
    """
    station_metadata: StationMetadata
    station_data: Dict[SensorType, SensorData] = field(default_factory=dict)
    packet_data: List[DataPacket] = field(default_factory=list)

    def append_station_data(self, new_station_data: Dict[SensorType, SensorData]):
        """
        append new station data to existing station data
        :param new_station_data: the dictionary of data to add
        """
        for sensor_type, sensor_data in new_station_data.items():
            self.append_sensor(sensor_type, sensor_data)

    def append_sensor(self, sensor_type: SensorType, sensor_data: SensorData):
        """
        append sensor data to an existing sensor_type or add a new sensor to the dictionary
        :param sensor_type: the sensor to append to
        :param sensor_data: the data to append
        """
        if sensor_type in self.station_data.keys():
            self.station_data[sensor_type] = self.station_data[sensor_type].append_data(sensor_data.data_df)
        else:
            self._add_sensor(sensor_type, sensor_data)

    def _delete_sensor(self, sensor_type: SensorType):
        """
        removes a sensor from the data packet if it exists
        :param sensor_type: the sensor to remove
        """
        if sensor_type in self.station_data.keys():
            self.station_data.pop(sensor_type)

    def _add_sensor(self, sensor_type: SensorType, sensor: SensorData):
        """
        adds a sensor to the sensor_data_dict
        :param sensor_type: the type of sensor to add
        :param sensor: the sensor data to add
        """
        if sensor_type in self.station_data.keys():
            raise ValueError(f"Cannot add sensor type ({sensor_type.name}) that already exists in packet!")
        else:
            self.station_data[sensor_type] = sensor

    def has_audio_sensor(self) -> bool:
        """
        check if audio sensor is in sensor_data_dict
        :return: True if audio sensor exists
        """
        return SensorType.AUDIO in self.station_data.keys()

    def has_audio_data(self) -> bool:
        """
        check if the audio sensor has any data
        :return: True if audio sensor has any data
        """
        return self.has_audio_sensor() and self.audio_sensor().num_samples() > 0

    def audio_sensor(self) -> Optional[SensorData]:
        """
        return the audio sensor if it exists
        :return: audio sensor if it exists, None otherwise
        """
        if self.has_audio_sensor():
            return self.station_data[SensorType.AUDIO]
        return None

    def set_audio_sensor(self, audio_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.LOCATION in self.station_data.keys()

    def has_location_data(self) -> bool:
        """
        check if the location sensor has any data
        :return: True if location sensor has any data
        """
        return self.has_location_sensor() and self.location_sensor().num_samples() > 0

    def location_sensor(self) -> Optional[SensorData]:
        """
        return the location sensor if it exists
        :return: location sensor if it exists, None otherwise
        """
        if self.has_location_sensor():
            return self.station_data[SensorType.LOCATION]
        return None

    def set_location_sensor(self, loc_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.ACCELEROMETER in self.station_data.keys()

    def has_accelerometer_data(self) -> bool:
        """
        check if the accelerometer sensor has any data
        :return: True if accelerometer sensor has any data
        """
        return self.has_accelerometer_sensor() and self.accelerometer_sensor().num_samples() > 0

    def accelerometer_sensor(self) -> Optional[SensorData]:
        """
        return the accelerometer sensor if it exists
        :return: accelerometer sensor if it exists, None otherwise
        """
        if self.has_accelerometer_sensor():
            return self.station_data[SensorType.ACCELEROMETER]
        return None

    def set_accelerometer_sensor(self, acc_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.MAGNETOMETER in self.station_data.keys()

    def has_magnetometer_data(self) -> bool:
        """
        check if the magnetometer sensor has any data
        :return: True if magnetometer sensor has any data
        """
        return self.has_magnetometer_sensor() and self.magnetometer_sensor().num_samples() > 0

    def magnetometer_sensor(self) -> Optional[SensorData]:
        """
        return the magnetometer sensor if it exists
        :return: magnetometer sensor if it exists, None otherwise
        """
        if self.has_magnetometer_sensor():
            return self.station_data[SensorType.MAGNETOMETER]
        return None

    def set_magnetometer_sensor(self, mag_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.GYROSCOPE in self.station_data.keys()

    def has_gyroscope_data(self) -> bool:
        """
        check if the gyroscope sensor has any data
        :return: True if gyroscope sensor has any data
        """
        return self.has_gyroscope_sensor() and self.gyroscope_sensor().num_samples() > 0

    def gyroscope_sensor(self) -> Optional[SensorData]:
        """
        return the gyroscope sensor if it exists
        :return: gyroscope sensor if it exists, None otherwise
        """
        if self.has_gyroscope_sensor():
            return self.station_data[SensorType.GYROSCOPE]
        return None

    def set_gyroscope_sensor(self, gyro_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.PRESSURE in self.station_data.keys()

    def has_barometer_data(self) -> bool:
        """
        check if the barometer sensor has any data
        :return: True if barometer sensor has any data
        """
        return self.has_barometer_sensor() and self.barometer_sensor().num_samples() > 0

    def barometer_sensor(self) -> Optional[SensorData]:
        """
        return the barometer sensor if it exists
        :return: barometer sensor if it exists, None otherwise
        """
        if self.has_barometer_sensor():
            return self.station_data[SensorType.PRESSURE]
        return None

    def set_barometer_sensor(self, bar_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.LIGHT in self.station_data.keys()

    def has_light_data(self) -> bool:
        """
        check if the light sensor has any data
        :return: True if light sensor has any data
        """
        return self.has_light_sensor() and self.light_sensor().num_samples() > 0

    def light_sensor(self) -> Optional[SensorData]:
        """
        return the light sensor if it exists
        :return: light sensor if it exists, None otherwise
        """
        if self.has_light_sensor():
            return self.station_data[SensorType.LIGHT]
        return None

    def set_light_sensor(self, light_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.INFRARED in self.station_data.keys()

    def has_infrared_data(self) -> bool:
        """
        check if the infrared sensor has any data
        :return: True if infrared sensor has any data
        """
        return self.has_infrared_sensor() and self.infrared_sensor().num_samples() > 0

    def infrared_sensor(self) -> Optional[SensorData]:
        """
        return the infrared sensor if it exists
        :return: infrared sensor if it exists, None otherwise
        """
        if self.has_infrared_sensor():
            return self.station_data[SensorType.INFRARED]
        return None

    def set_infrared_sensor(self, infrd_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.IMAGE in self.station_data.keys()

    def has_image_data(self) -> bool:
        """
        check if the image sensor has any data
        :return: True if image sensor has any data
        """
        return self.has_image_sensor() and self.image_sensor().num_samples() > 0

    def image_sensor(self) -> Optional[SensorData]:
        """
        return the image sensor if it exists
        :return: image sensor if it exists, None otherwise
        """
        if self.has_image_sensor():
            return self.station_data[SensorType.IMAGE]
        return None

    def set_image_sensor(self, img_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.TEMPERATURE in self.station_data.keys()

    def has_ambient_temperature_data(self) -> bool:
        """
        check if the ambient temperature sensor has any data
        :return: True if ambient temperature sensor has any data
        """
        return self.has_ambient_temperature_sensor() and self.ambient_temperature_sensor().num_samples() > 0

    def ambient_temperature_sensor(self) -> Optional[SensorData]:
        """
        return the ambient temperature sensor if it exists
        :return: image ambient temperature if it exists, None otherwise
        """
        if self.has_ambient_temperature_sensor():
            return self.station_data[SensorType.TEMPERATURE]
        return None

    def set_ambient_temperature_sensor(self, amtemp_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.GRAVITY in self.station_data.keys()

    def has_gravity_data(self) -> bool:
        """
        check if the gravity sensor has any data
        :return: True if gravity sensor has any data
        """
        return self.has_gravity_sensor() and self.gravity_sensor().num_samples() > 0

    def gravity_sensor(self) -> Optional[SensorData]:
        """
        return the gravity sensor if it exists
        :return: gravity sensor if it exists, None otherwise
        """
        if self.has_gravity_sensor():
            return self.station_data[SensorType.GRAVITY]
        return None

    def set_gravity_sensor(self, grav_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.LINEAR_ACCELERATION in self.station_data.keys()

    def has_linear_acceleration_data(self) -> bool:
        """
        check if the linear acceleration sensor has any data
        :return: True if linear acceleration sensor has any data
        """
        return self.has_linear_acceleration_sensor() and self.linear_acceleration_sensor().num_samples() > 0

    def linear_acceleration_sensor(self) -> Optional[SensorData]:
        """
        return the linear acceleration sensor if it exists
        :return: linear acceleration sensor if it exists, None otherwise
        """
        if self.has_linear_acceleration_sensor():
            return self.station_data[SensorType.LINEAR_ACCELERATION]
        return None

    def set_linear_acceleration_sensor(self, linacc_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.ORIENTATION in self.station_data.keys()

    def has_orientation_data(self) -> bool:
        """
        check if the orientation sensor has any data
        :return: True if orientation sensor has any data
        """
        return self.has_orientation_sensor() and self.orientation_sensor().num_samples() > 0

    def orientation_sensor(self) -> Optional[SensorData]:
        """
        return the orientation sensor if it exists
        :return: orientation sensor if it exists, None otherwise
        """
        if self.has_orientation_sensor():
            return self.station_data[SensorType.ORIENTATION]
        return None

    def set_orientation_sensor(self, orient_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.PROXIMITY in self.station_data.keys()

    def has_proximity_data(self) -> bool:
        """
        check if the proximity sensor has any data
        :return: True if proximity sensor has any data
        """
        return self.has_proximity_sensor() and self.proximity_sensor().num_samples() > 0

    def proximity_sensor(self) -> Optional[SensorData]:
        """
        return the proximity sensor if it exists
        :return: proximity sensor if it exists, None otherwise
        """
        if self.has_proximity_sensor():
            return self.station_data[SensorType.PROXIMITY]
        return None

    def set_proximity_sensor(self, prox_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.RELATIVE_HUMIDITY in self.station_data.keys()

    def has_relative_humidity_data(self) -> bool:
        """
        check if the relative humidity sensor has any data
        :return: True if relative humidity sensor has any data
        """
        return self.has_relative_humidity_sensor() and self.relative_humidity_sensor().num_samples() > 0

    def relative_humidity_sensor(self) -> Optional[SensorData]:
        """
        return the relative humidity sensor if it exists
        :return: relative humidity sensor if it exists, None otherwise
        """
        if self.has_relative_humidity_sensor():
            return self.station_data[SensorType.RELATIVE_HUMIDITY]
        return None

    def set_relative_humidity_sensor(self, relhum_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.ROTATION_VECTOR in self.station_data.keys()

    def has_rotation_vector_data(self) -> bool:
        """
        check if the rotation vector sensor has any data
        :return: True if rotation vector sensor has any data
        """
        return self.has_rotation_vector_sensor() and self.rotation_vector_sensor().num_samples() > 0

    def rotation_vector_sensor(self) -> Optional[SensorData]:
        """
        return the rotation vector sensor if it exists
        :return: rotation vector sensor if it exists, None otherwise
        """
        if self.has_rotation_vector_sensor():
            return self.station_data[SensorType.ROTATION_VECTOR]
        return None

    def set_rotation_vector_sensor(self, rotvec_sensor: Optional[SensorData]) -> 'Station':
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
        return SensorType.COMPRESSED_AUDIO in self.station_data.keys()

    def has_compressed_audio_data(self) -> bool:
        """
        check if the compressed audio sensor has any data
        :return: True if compressed audio sensor has any data
        """
        return self.has_compressed_audio_sensor() and self.compressed_audio_sensor().num_samples() > 0

    def compressed_audio_sensor(self) -> Optional[SensorData]:
        """
        return the compressed audio sensor if it exists
        :return: compressed audio sensor if it exists, None otherwise
        """
        if self.has_compressed_audio_sensor():
            return self.station_data[SensorType.COMPRESSED_AUDIO]
        return None

    def set_compressed_audio_sensor(self, compaudio_sensor: Optional[SensorData]) -> 'Station':
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

    def get_non_audio_sensors(self) -> Dict[SensorType, SensorData]:
        """
        returns all non-audio sensors in the station
        :return: dict of SensorType and SensorData of all non-audio sensors in the station
        """
        return {k: v for (k, v) in self.station_data.items() if SensorType.AUDIO not in k}

    def update_timestamps(self):
        """
        updates the timestamps in all SensorData objects using the station_best_offset of the station_timing
        """
        if self.station_metadata.station_timing_is_corrected:
            print("WARNING: Timestamps already corrected!")
        else:
            if not self.station_metadata.timing_data:
                print("WARNING: Station does not have timing data, assuming existing values are the correct ones!")
            else:
                delta = self.station_metadata.timing_data.station_best_offset
                for sensor in self.station_data.values():
                    sensor.update_data_timestamps(delta)
                for packet in self.packet_data:
                    packet.data_start_timestamp += delta
                    packet.data_end_timestamp += delta
                self.station_metadata.timing_data.station_first_data_timestamp += delta
            self.station_metadata.station_timing_is_corrected = True

    def revert_timestamps(self):
        """
        reverts the timestamps in all SensorData objects using the station_best_offset of the station_timing
        """
        if self.station_metadata.station_timing_is_corrected:
            if not self.station_metadata.timing_data:
                print("WARNING: Station does not have timing data, assuming existing values are the correct ones!")
            else:
                delta = self.station_metadata.timing_data.station_best_offset
                for sensor in self.station_data.values():
                    sensor.update_data_timestamps(-delta)
                for packet in self.packet_data:
                    packet.data_start_timestamp -= delta
                    packet.data_end_timestamp -= delta
                self.station_metadata.timing_data.station_first_data_timestamp -= delta
                self.station_metadata.station_timing_is_corrected = False
        else:
            print("WARNING: Cannot revert timestamps that are not corrected!")
