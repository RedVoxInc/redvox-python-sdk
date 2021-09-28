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
