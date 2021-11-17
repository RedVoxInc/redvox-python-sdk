"""
Defines generic sensor data and data for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
"""
import enum
from typing import List, Union

import numpy as np
import pandas as pd

import redvox.common.date_time_utils as dtu
from redvox.common import offset_model as om
from redvox.common.errors import RedVoxExceptions
from redvox.common.gap_and_pad_utils import calc_evenly_sampled_timestamps
from redvox.api1000.wrapped_redvox_packet.station_information import (
    NetworkType,
    PowerState,
    CellServiceState,
)
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
from redvox.api1000.wrapped_redvox_packet.sensors.image import ImageCodec
from redvox.api1000.wrapped_redvox_packet.sensors.audio import AudioCodec

# columns that cannot be interpolated
NON_INTERPOLATED_COLUMNS = ["compressed_audio", "image"]
# columns that are not numeric but can be interpolated
NON_NUMERIC_COLUMNS = ["location_provider", "image_codec", "audio_codec",
                       "network_type", "power_state", "cell_service"]


class SensorType(enum.Enum):
    """
    Enumeration of possible types of sensors to read data from
    """

    UNKNOWN_SENSOR = 0  # unknown sensor
    ACCELEROMETER = 1  # meters/second^2
    AMBIENT_TEMPERATURE = 2  # degrees Celsius
    AUDIO = 3  # normalized counts
    COMPRESSED_AUDIO = 4  # bytes (codec specific)
    GRAVITY = 5  # meters/second^2
    GYROSCOPE = 6  # radians/second
    IMAGE = 7  # bytes (codec specific)
    LIGHT = 8  # lux
    LINEAR_ACCELERATION = 9  # meters/second^2
    LOCATION = 10  # See standard
    MAGNETOMETER = 11  # microtesla
    ORIENTATION = 12  # radians
    PRESSURE = 13  # kilopascal
    PROXIMITY = 14  # on, off, cm
    RELATIVE_HUMIDITY = 15  # percentage
    ROTATION_VECTOR = 16  # Unitless
    INFRARED = 17  # this is proximity
    STATION_HEALTH = 18
    # battery charge and current level, phone internal temperature, network source and strength,
    # available RAM of the system, cell service status, amount of hard disk space left, power charging state
    BEST_LOCATION = 19  # See standard

    @staticmethod
    def type_from_str(type_str: str) -> "SensorType":
        """
        converts a string to a sensor type
        :param type_str: string to convert
        :return: a sensor type, UNKNOWN_SENSOR is the default for invalid inputs
        """
        if (
                type_str.lower() == "audio"
                or type_str.lower() == "mic"
                or type_str.lower() == "microphone"
        ):
            return SensorType.AUDIO
        elif type_str.lower() == "accelerometer" or type_str.lower() == "accel":
            return SensorType.ACCELEROMETER
        elif type_str.lower() == "ambient_temperature":
            return SensorType.AMBIENT_TEMPERATURE
        elif type_str.lower() == "compressed_audio":
            return SensorType.COMPRESSED_AUDIO
        elif type_str.lower() == "gravity":
            return SensorType.GRAVITY
        elif type_str.lower() == "gyroscope" or type_str.lower() == "gyro":
            return SensorType.GYROSCOPE
        elif type_str.lower() == "image":
            return SensorType.IMAGE
        elif type_str.lower() == "light":
            return SensorType.LIGHT
        elif (
                type_str.lower() == "linear_acceleration"
                or type_str.lower() == "linear_accel"
        ):
            return SensorType.LINEAR_ACCELERATION
        elif type_str.lower() == "location" or type_str.lower() == "loc":
            return SensorType.LOCATION
        elif type_str.lower() == "best_location" or type_str.lower() == "best_loc":
            return SensorType.BEST_LOCATION
        elif type_str.lower() == "magnetometer" or type_str.lower() == "mag":
            return SensorType.MAGNETOMETER
        elif type_str.lower() == "orientation":
            return SensorType.ORIENTATION
        elif (
                type_str.lower() == "pressure"
                or type_str.lower() == "bar"
                or type_str.lower() == "barometer"
        ):
            return SensorType.PRESSURE
        elif type_str.lower() == "proximity" or type_str.lower() == "infrared":
            return SensorType.PROXIMITY
        elif type_str.lower() == "relative_humidity":
            return SensorType.RELATIVE_HUMIDITY
        elif type_str.lower() == "rotation_vector":
            return SensorType.ROTATION_VECTOR
        else:
            return SensorType.UNKNOWN_SENSOR


class SensorData:
    """
    Generic SensorData class for API-independent analysis
    Properties:
        name: string, name of sensor
        type: SensorType, enumerated type of sensor
        data_df: dataframe of the sensor data; always has timestamps as the first column,
                    the other columns are the data fields
        sample_rate_hz: float, sample rate in Hz of the sensor, default np.nan, usually 1/sample_interval_s
        sample_interval_s: float, mean duration in seconds between samples, default np.nan, usually 1/sample_rate
        sample_interval_std_s: float, standard deviation in seconds between samples, default np.nan
        is_sample_rate_fixed: bool, True if sample rate is constant, default False
        timestamps_altered: bool, True if timestamps in the sensor have been altered from their original values
                            default False
    """

    def __init__(
            self,
            sensor_name: str,
            sensor_data: pd.DataFrame,
            sensor_type: SensorType = SensorType.UNKNOWN_SENSOR,
            sample_rate_hz: float = np.nan,
            sample_interval_s: float = np.nan,
            sample_interval_std_s: float = np.nan,
            is_sample_rate_fixed: bool = False,
            are_timestamps_altered: bool = False,
            calculate_stats: bool = False
    ):
        """
        initialize the sensor data with params
        :param sensor_name: name of the sensor
        :param sensor_type: enumerated type of the sensor, default SensorType.UNKNOWN_SENSOR
        :param sensor_data: dataframe with the timestamps and sensor data; first column is always the timestamps,
                            the other columns are the data channels in the sensor
        :param sample_rate_hz: sample rate in hz of the data
        :param sample_interval_s: sample interval in seconds of the data
        :param sample_interval_std_s: std dev of sample interval in seconds of the data
        :param is_sample_rate_fixed: if True, sample rate is constant for all data, default False
        :param are_timestamps_altered: if True, timestamps in the sensor have been altered from their
                                        original values, default False
        :param calculate_stats: if True, calculate sample_rate, sample_interval_s, and sample_interval_std_s
                                default False
        """
        if "timestamps" not in sensor_data.columns:
            raise AttributeError(
                'SensorData requires the data frame to contain a column titled "timestamps"'
            )
        self.name: str = sensor_name
        self.type: SensorType = sensor_type
        self.data_df: pd.DataFrame = sensor_data.infer_objects()
        self.sample_rate_hz: float = sample_rate_hz
        self.sample_interval_s: float = sample_interval_s
        self.sample_interval_std_s: float = sample_interval_std_s
        self.is_sample_rate_fixed: bool = is_sample_rate_fixed
        self.timestamps_altered: bool = are_timestamps_altered
        self.errors: RedVoxExceptions = RedVoxExceptions("Sensor")
        if calculate_stats:
            self.organize_and_update_stats()
        else:
            self.sort_by_data_timestamps()

    def print_errors(self):
        """
        prints errors to screen
        """
        self.errors.print()

    def is_sample_interval_invalid(self) -> bool:
        """
        :return: True if sample interval is np.nan or equal to 0.0
        """
        return np.isnan(self.sample_interval_s) or self.sample_interval_s == 0.0

    def organize_and_update_stats(self) -> "SensorData":
        """
        sorts the data by timestamps, then if the sample rate is not fixed, recalculates the sample rate, interval,
            and interval std dev.  If there is only one value, sets the sample rate, interval, and interval std dev
            to np.nan.  Updates the SensorData object with the new values
        :return: updated version of self
        """
        self.sort_by_data_timestamps()
        if not self.is_sample_rate_fixed:
            if self.num_samples() > 1:
                timestamp_diffs = np.diff(self.data_timestamps())
                self.sample_interval_s = dtu.microseconds_to_seconds(
                    float(np.mean(timestamp_diffs))
                )
                self.sample_interval_std_s = dtu.microseconds_to_seconds(
                    float(np.std(timestamp_diffs))
                )
                self.sample_rate_hz = (
                    np.nan
                    if self.is_sample_interval_invalid()
                    else 1 / self.sample_interval_s
                )
            else:
                self.sample_interval_s = np.nan
                self.sample_interval_std_s = np.nan
                self.sample_rate_hz = np.nan
        return self

    def append_data(
            self, new_data: pd.DataFrame, recalculate_stats: bool = False
    ) -> "SensorData":
        """
        append the new data to the dataframe, update the sensor's stats on demand if it doesn't have a fixed
            sample rate, then return the updated SensorData object
        :param new_data: Dataframe containing data to add to the sensor's dataframe
        :param recalculate_stats: if True and the sensor does not have a fixed sample rate, sort the timestamps,
                                    recalculate the sample rate, interval, and interval std dev, default False
        :return: the updated SensorData object
        """
        self.data_df = self.data_df.append(new_data, ignore_index=True)
        if recalculate_stats and not self.is_sample_rate_fixed:
            self.organize_and_update_stats()
        return self

    def sensor_type_as_str(self) -> str:
        """
        gets the sensor type as a string
        :return: sensor type of the sensor as a string
        """
        return self.type.name

    def samples(self) -> np.ndarray:
        """
        gets the samples of dataframe
        :return: the data values of the dataframe as a numpy ndarray
        """
        return self.data_df.iloc[:, 2:].T.to_numpy()

    def get_data_channel(self, channel_name: str) -> Union[np.array, List[str]]:
        """
        gets the data channel specified, raises an error and lists valid fields if channel_name is not in the dataframe
        :param channel_name: the name of the channel to get data for
        :return: the data values of the channel as a numpy array or list of strings for enumerated channels
        """
        if channel_name not in self.data_df.columns:
            raise ValueError(
                f"WARNING: {channel_name} does not exist; try one of {self.data_channels()}"
            )
        if channel_name == "location_provider":
            return [LocationProvider(c).name for c in self.data_df[channel_name]]
        elif channel_name == "image_codec":
            return [ImageCodec(c).name for c in self.data_df[channel_name]]
        elif channel_name == "audio_codec":
            return [AudioCodec(c).name for c in self.data_df[channel_name]]
        elif channel_name == "network_type":
            return [NetworkType(c).name for c in self.data_df[channel_name]]
        elif channel_name == "power_state":
            return [PowerState(c).name for c in self.data_df[channel_name]]
        elif channel_name == "cell_service":
            return [CellServiceState(c).name for c in self.data_df[channel_name]]
        return self.data_df[channel_name].to_numpy()

    def get_valid_data_channel_values(self, channel_name: str) -> np.array:
        """
        gets all non-nan values from the channel specified
        :param channel_name: the name of the channel to get data for
        :return: non-nan values of the channel as a numpy array
        """
        channel_data = self.get_data_channel(channel_name)
        return channel_data[~np.isnan(channel_data)]

    def data_timestamps(self) -> np.array:
        """
        :return: the timestamps as a numpy array
        """
        return self.data_df["timestamps"].to_numpy(dtype=float)

    def unaltered_data_timestamps(self) -> np.array:
        """
        :return: the unaltered timestamps as a numpy array
        """
        return self.data_df["unaltered_timestamps"].to_numpy(dtype=float)

    def first_data_timestamp(self) -> float:
        """
        :return: timestamp of the first data point
        """
        return self.data_df["timestamps"].iloc[0]

    def last_data_timestamp(self) -> float:
        """
        :return: timestamp of the last data point
        """
        return self.data_df["timestamps"].iloc[-1]

    def num_samples(self) -> int:
        """
        :return: the number of rows (samples) in the dataframe
        """
        return self.data_df.shape[0]

    def data_channels(self) -> List[str]:
        """
        :return: a list of the names of the columns (data channels) of the dataframe
        """
        return self.data_df.columns.to_list()

    def update_data_timestamps(self, offset_model: om.OffsetModel, use_model_function: bool = True):
        """
        updates the timestamps of the data points
        :param offset_model: model used to update the timestamps
        :param use_model_function: if True, use the offset model's correction function to correct time,
                                    otherwise use best offset (model's intercept value).  default True
        """
        slope = dtu.seconds_to_microseconds(self.sample_interval_s) * (1 + offset_model.slope) \
            if use_model_function else dtu.seconds_to_microseconds(self.sample_interval_s)
        if self.type == SensorType.AUDIO:
            # use the model to update the first timestamp or add the best offset (model's intercept value)
            self.data_df["timestamps"] = \
                calc_evenly_sampled_timestamps(offset_model.update_time(self.first_data_timestamp(),
                                                                        use_model_function),
                                               self.num_samples(),
                                               slope)
        else:
            self.data_df["timestamps"] = offset_model.update_timestamps(self.data_timestamps(), use_model_function)
        time_diffs = np.floor(np.diff(self.data_timestamps()))
        if len(time_diffs) > 1:
            self.sample_interval_s = dtu.microseconds_to_seconds(slope)
            if self.sample_interval_s > 0:
                self.sample_rate_hz = 1 / self.sample_interval_s
                self.sample_interval_std_s = dtu.microseconds_to_seconds(np.std(time_diffs))
        self.timestamps_altered = True

    def sort_by_data_timestamps(self, ascending: bool = True):
        """
        sorts the data based on timestamps
        :param ascending: if True, timestamps are sorted in ascending order
        """
        self.data_df = self.data_df.sort_values("timestamps", ascending=ascending)

    def interpolate(self, interpolate_timestamp: float, first_point: int, second_point: int = 0,
                    copy: bool = True) -> pd.Series:
        """
        interpolates two points at the intercept value.  the two points must be consecutive in the dataframe
        :param interpolate_timestamp: timestamp to interpolate other values
        :param first_point: index of first point
        :param second_point: delta to second point, default 0 (same as first point)
        :param copy: if True, copies the values of the first point, default True
        :return: pd.Series of interpolated points
        """
        start_point = self.data_df.iloc[first_point]
        numeric_start = start_point[[col for col in self.data_df.columns
                                     if col not in NON_INTERPOLATED_COLUMNS + NON_NUMERIC_COLUMNS]]
        non_numeric_start = start_point[[col for col in self.data_df.columns if col in NON_NUMERIC_COLUMNS]]
        if not copy and second_point:
            end_point = self.data_df.iloc[first_point + second_point]
            numeric_end = end_point[[col for col in self.data_df.columns
                                     if col not in NON_INTERPOLATED_COLUMNS + NON_NUMERIC_COLUMNS]]
            non_numeric_end = end_point[[col for col in self.data_df.columns if col in NON_NUMERIC_COLUMNS]]
            first_closer = \
                np.abs(start_point["timestamps"] - interpolate_timestamp) \
                <= np.abs(end_point["timestamps"] - interpolate_timestamp)
            if first_closer:
                non_numeric_diff = non_numeric_start
            else:
                non_numeric_diff = non_numeric_end
            # if copy:
            #     if first_closer:
            #         numeric_diff = numeric_start
            #     else:
            #         numeric_diff = numeric_end
            # else:
            numeric_diff = numeric_end - numeric_start
            numeric_diff = \
                (numeric_diff / numeric_diff["timestamps"]) * \
                (interpolate_timestamp - numeric_start) + numeric_start
        else:
            numeric_diff = numeric_start
            non_numeric_diff = non_numeric_start
        numeric_diff["timestamps"] = interpolate_timestamp
        return pd.concat([numeric_diff, non_numeric_diff])


class AudioSensor(SensorData):
    """
    Audio specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.AUDIO, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_microphone_data(self):
        return super().get_data_channel('microphone')

    def get_valid_microphone_data(self):
        return super().get_valid_data_channel_values('microphone')


class CompressedAudioSensor(SensorData):
    """
    Compressed-audio specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.COMPRESSED_AUDIO, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_compressed_audio_data(self):
        return super().get_data_channel('compressed_audio')

    def get_valid_compressed_audio_data(self):
        return super().get_valid_data_channel_values('compressed_audio')

    def get_audio_codec_data(self):
        return super().get_data_channel('audio_codec')

    def get_valid_audio_codec_data(self):
        return super().get_valid_data_channel_values('audio_codec')


class ImageSensor(SensorData):
    """
    Image specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.IMAGE, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_image_data(self):
        return super().get_data_channel('image')

    def get_valid_image_data(self):
        return super().get_valid_data_channel_values('image')

    def get_image_codec_data(self):
        return super().get_data_channel('image_codec')

    def get_valid_image_codec_data(self):
        return super().get_valid_data_channel_values('image_codec')


class PressureSensor(SensorData):
    """
    Pressure specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.PRESSURE, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_pressure_data(self):
        return super().get_data_channel('pressure')

    def get_valid_pressure_data(self):
        return super().get_valid_data_channel_values('pressure')


class LightSensor(SensorData):
    """
    Light specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.LIGHT, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_light_data(self):
        return super().get_data_channel('light')

    def get_valid_light_data(self):
        return super().get_valid_data_channel_values('light')


class ProximitySensor(SensorData):
    """
    Proximity specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.PROXIMITY, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_proximity_data(self):
        return super().get_data_channel('proximity')

    def get_valid_proximity_data(self):
        return super().get_valid_data_channel_values('proximity')


class AmbientTemperatureSensor(SensorData):
    """
    Ambient-temperature specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.AMBIENT_TEMPERATURE, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_ambient_temperature_data(self):
        return super().get_data_channel('ambient_temp')

    def get_valid_ambient_temperature_data(self):
        return super().get_valid_data_channel_values('ambient_temp')


class RelativeHumiditySensor(SensorData):
    """
    Relative-humidity specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.RELATIVE_HUMIDITY, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_relative_humidity_data(self):
        return super().get_data_channel('rel_humidity')

    def get_valid_relative_humidity_data(self):
        return super().get_valid_data_channel_values('rel_humidity')


class AccelerometerSensor(SensorData):
    """
    Accelerometer specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.ACCELEROMETER, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_accelerometer_x_data(self):
        return super().get_data_channel('accelerometer_x')

    def get_valid_accelerometer_x_data(self):
        return super().get_valid_data_channel_values('accelerometer_x')

    def get_accelerometer_y_data(self):
        return super().get_data_channel('accelerometer_y')

    def get_valid_accelerometer_y_data(self):
        return super().get_valid_data_channel_values('accelerometer_y')

    def get_accelerometer_z_data(self):
        return super().get_data_channel('accelerometer_z')

    def get_valid_accelerometer_z_data(self):
        return super().get_valid_data_channel_values('accelerometer_z')


class MagnetometerSensor(SensorData):
    """
    Magnetometer specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.MAGNETOMETER, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_magnetometer_x_data(self):
        return super().get_data_channel('magnetometer_x')

    def get_valid_magnetometer_x_data(self):
        return super().get_valid_data_channel_values('magnetometer_x')

    def get_magnetometer_y_data(self):
        return super().get_data_channel('magnetometer_y')

    def get_valid_magnetometer_y_data(self):
        return super().get_valid_data_channel_values('magnetometer_y')

    def get_magnetometer_z_data(self):
        return super().get_data_channel('magnetometer_z')

    def get_valid_magnetometer_z_data(self):
        return super().get_valid_data_channel_values('magnetometer_z')


class LinearAccelerationSensor(SensorData):
    """
    Linear-acceleration specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.LINEAR_ACCELERATION, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_linear_acceleration_x_data(self):
        return super().get_data_channel('linear_accel_x')

    def get_valid_linear_acceleration_x_data(self):
        return super().get_valid_data_channel_values('linear_accel_x')

    def get_linear_acceleration_y_data(self):
        return super().get_data_channel('linear_accel_y')

    def get_valid_linear_acceleration_y_data(self):
        return super().get_valid_data_channel_values('linear_accel_y')

    def get_linear_acceleration_z_data(self):
        return super().get_data_channel('linear_accel_z')

    def get_valid_linear_acceleration_z_data(self):
        return super().get_valid_data_channel_values('linear_accel_z')


class OrientationSensor(SensorData):
    """
    Orientation specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.ORIENTATION, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_orientation_x_data(self):
        return super().get_data_channel('orientation_x')

    def get_valid_orientation_x_data(self):
        return super().get_valid_data_channel_values('orientation_x')

    def get_orientation_y_data(self):
        return super().get_data_channel('orientation_y')

    def get_valid_orientation_y_data(self):
        return super().get_valid_data_channel_values('orientation_y')

    def get_orientation_z_data(self):
        return super().get_data_channel('orientation_z')

    def get_valid_orientation_z_data(self):
        return super().get_valid_data_channel_values('orientation_z')


class RotationVectorSensor(SensorData):
    """
    Rotation-vector specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.ROTATION_VECTOR, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_rotation_vector_x_data(self):
        return super().get_data_channel('rotation_vector_x')

    def get_valid_rotation_vector_x_data(self):
        return super().get_valid_data_channel_values('rotation_vector_x')

    def get_rotation_vector_y_data(self):
        return super().get_data_channel('rotation_vector_y')

    def get_valid_rotation_vector_y_data(self):
        return super().get_valid_data_channel_values('rotation_vector_y')

    def get_rotation_vector_z_data(self):
        return super().get_data_channel('rotation_vector_z')

    def get_valid_rotation_vector_z_data(self):
        return super().get_valid_data_channel_values('rotation_vector_z')


class GyroscopeSensor(SensorData):
    """
    Gyroscope specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.GYROSCOPE, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_gyroscope_x_data(self):
        return super().get_data_channel('gyroscope_x')

    def get_valid_gyroscope_x_data(self):
        return super().get_valid_data_channel_values('gyroscope_x')

    def get_gyroscope_y_data(self):
        return super().get_data_channel('gyroscope_y')

    def get_valid_gyroscope_y_data(self):
        return super().get_valid_data_channel_values('gyroscope_y')

    def get_gyroscope_z_data(self):
        return super().get_data_channel('gyroscope_z')

    def get_valid_gyroscope_z_data(self):
        return super().get_valid_data_channel_values('gyroscope_z')


class GravitySensor(SensorData):
    """
    Gravity specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.GRAVITY, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_gravity_x_data(self):
        return super().get_data_channel('gravity_x')

    def get_valid_gravity_x_data(self):
        return super().get_valid_data_channel_values('gravity_x')

    def get_gravity_y_data(self):
        return super().get_data_channel('gravity_y')

    def get_valid_gravity_y_data(self):
        return super().get_valid_data_channel_values('gravity_y')

    def get_gravity_z_data(self):
        return super().get_data_channel('gravity_z')

    def get_valid_gravity_z_data(self):
        return super().get_valid_data_channel_values('gravity_z')


class LocationSensor(SensorData):
    """
    Location specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.LOCATION, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_gps_timestamps_data(self):
        return super().get_data_channel('gps_timestamps')

    def get_valid_gps_timestamps_data(self):
        return super().get_valid_data_channel_values('gps_timestamps')

    def get_latitude_data(self):
        return super().get_data_channel('latitude')

    def get_valid_latitude_data(self):
        return super().get_valid_data_channel_values('latitude')

    def get_longitude_data(self):
        return super().get_data_channel('longitude')

    def get_valid_longitude_data(self):
        return super().get_valid_data_channel_values('longitude')

    def get_altitude_data(self):
        return super().get_data_channel('altitude')

    def get_valid_altitude_data(self):
        return super().get_valid_data_channel_values('altitude')

    def get_speed_data(self):
        return super().get_data_channel('speed')

    def get_valid_speed_data(self):
        return super().get_valid_data_channel_values('speed')

    def get_bearing_data(self):
        return super().get_data_channel('bearing')

    def get_valid_bearing_data(self):
        return super().get_valid_data_channel_values('bearing')

    def get_horizontal_accuracy_data(self):
        return super().get_data_channel('horizontal_accuracy')

    def get_valid_horizontal_accuracy_data(self):
        return super().get_valid_data_channel_values('horizontal_accuracy')

    def get_vertical_accuracy_data(self):
        return super().get_data_channel('vertical_accuracy')

    def get_valid_vertical_accuracy_data(self):
        return super().get_valid_data_channel_values('vertical_accuracy')

    def get_speed_accuracy_data(self):
        return super().get_data_channel('speed_accuracy')

    def get_valid_speed_accuracy_data(self):
        return super().get_valid_data_channel_values('speed_accuracy')

    def get_bearing_accuracy_data(self):
        return super().get_data_channel('bearing_accuracy')

    def get_valid_bearing_accuracy_data(self):
        return super().get_valid_data_channel_values('bearing_accuracy')

    def get_location_provider_data(self):
        return super().get_data_channel('location_provider')

    def get_valid_location_provider_data(self):
        return super().get_valid_data_channel_values('location_provider')


class BestLocationSensor(SensorData):
    """
    Best-location specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.BEST_LOCATION, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_gps_timestamps_data(self):
        return super().get_data_channel('gps_timestamps')

    def get_valid_gps_timestamps_data(self):
        return super().get_valid_data_channel_values('gps_timestamps')

    def get_latitude_data(self):
        return super().get_data_channel('latitude')

    def get_valid_latitude_data(self):
        return super().get_valid_data_channel_values('latitude')

    def get_longitude_data(self):
        return super().get_data_channel('longitude')

    def get_valid_longitude_data(self):
        return super().get_valid_data_channel_values('longitude')

    def get_altitude_data(self):
        return super().get_data_channel('altitude')

    def get_valid_altitude_data(self):
        return super().get_valid_data_channel_values('altitude')

    def get_speed_data(self):
        return super().get_data_channel('speed')

    def get_valid_speed_data(self):
        return super().get_valid_data_channel_values('speed')

    def get_bearing_data(self):
        return super().get_data_channel('bearing')

    def get_valid_bearing_data(self):
        return super().get_valid_data_channel_values('bearing')

    def get_horizontal_accuracy_data(self):
        return super().get_data_channel('horizontal_accuracy')

    def get_valid_horizontal_accuracy_data(self):
        return super().get_valid_data_channel_values('horizontal_accuracy')

    def get_vertical_accuracy_data(self):
        return super().get_data_channel('vertical_accuracy')

    def get_valid_vertical_accuracy_data(self):
        return super().get_valid_data_channel_values('vertical_accuracy')

    def get_speed_accuracy_data(self):
        return super().get_data_channel('speed_accuracy')

    def get_valid_speed_accuracy_data(self):
        return super().get_valid_data_channel_values('speed_accuracy')

    def get_bearing_accuracy_data(self):
        return super().get_data_channel('bearing_accuracy')

    def get_valid_bearing_accuracy_data(self):
        return super().get_valid_data_channel_values('bearing_accuracy')

    def get_location_provider_data(self):
        return super().get_data_channel('location_provider')

    def get_valid_location_provider_data(self):
        return super().get_valid_data_channel_values('location_provider')


class StationHealthSensor(SensorData):
    """
    Station-health specific functions
    """
    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame,
                 sample_rate_hz: float = np.nan,
                 sample_interval_s: float = np.nan,
                 sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False,
                 are_timestamps_altered: bool = False,
                 calculate_stats: bool = False):
        super().__init__(sensor_name, sensor_data, SensorType.STATION_HEALTH, sample_rate_hz, sample_interval_s,
                         sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered, calculate_stats)

    def get_battery_charge_remaining_data(self):
        return super().get_data_channel('battery_charge_remaining')

    def get_valid_battery_charge_remaining_data(self):
        return super().get_valid_data_channel_values('battery_charge_remaining')

    def get_battery_current_strength_data(self):
        return super().get_data_channel('battery_current_strength')

    def get_valid_battery_current_strength_data(self):
        return super().get_valid_data_channel_values('battery_current_strength')

    def get_internal_temp_c_data(self):
        return super().get_data_channel('internal_temp_c')

    def get_valid_internal_temp_c_data(self):
        return super().get_valid_data_channel_values('internal_temp_c')

    def get_network_type_data(self):
        return super().get_data_channel('network_type')

    def get_valid_network_type_data(self):
        return super().get_valid_data_channel_values('network_type')

    def get_network_strength_data(self):
        return super().get_data_channel('network_strength')

    def get_valid_network_strength_data(self):
        return super().get_valid_data_channel_values('network_strength')

    def get_power_state_data(self):
        return super().get_data_channel('power_state')

    def get_valid_power_state_data(self):
        return super().get_valid_data_channel_values('power_state')

    def get_avail_ram_data(self):
        return super().get_data_channel('avail_ram')

    def get_valid_avail_ram_data(self):
        return super().get_valid_data_channel_values('avail_ram')

    def get_avail_disk_data(self):
        return super().get_data_channel('avail_disk')

    def get_valid_avail_disk_data(self):
        return super().get_valid_data_channel_values('avail_disk')

    def get_cell_service_data(self):
        return super().get_data_channel('cell_service')

    def get_valid_cell_service_data(self):
        return super().get_valid_data_channel_values('cell_service')

    def get_cpu_utilization_data(self):
        return super().get_data_channel('cpu_utilization')

    def get_valid_cpu_utilization_data(self):
        return super().get_valid_data_channel_values('cpu_utilization')

    def get_wifi_wake_lock_data(self):
        return super().get_data_channel('wifi_wake_lock')

    def get_valid_wifi_wake_lock_data(self):
        return super().get_valid_data_channel_values('wifi_wake_lock')

    def get_screen_state_data(self):
        return super().get_data_channel('screen_state')

    def get_valid_screen_state_data(self):
        return super().get_valid_data_channel_values('screen_state')

    def get_screen_brightness_data(self):
        return super().get_data_channel('screen_brightness')

    def get_valid_screen_brightness_data(self):
        return super().get_valid_data_channel_values('screen_brightness')
