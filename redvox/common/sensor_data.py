"""
Defines generic sensor data and metadata for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
"""
import enum
from typing import List

import numpy as np
import pandas as pd

import redvox.common.date_time_utils as dtu


class SensorType(enum.Enum):
    """
    Enumeration of possible types of sensors to read data from
    """
    UNKNOWN_SENSOR = 0          # unknown sensor
    ACCELEROMETER = 1           # meters/second^2
    AMBIENT_TEMPERATURE = 2     # degrees Celsius
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
    STATION_HEALTH = 18
    # battery charge and current level, phone internal temperature, network source and strength,
    # available RAM of the system, cell service status, amount of hard disk space left, power charging state


class SensorData:
    """
    Generic SensorData class for API-independent analysis
    Properties:
        name: string, name of sensor
        data_df: dataframe of the sensor data; always has timestamps as the first column,
                    the other columns are the data fields
        sample_rate: float, sample rate in Hz of the sensor, default np.nan, usually 1/sample_interval_s
        sample_interval_s: float, mean duration in seconds between samples, default np.nan, usually 1/sample_rate
        sample_interval_std_s: float, standard deviation in seconds between samples, default np.nan
        is_sample_rate_fixed: bool, True if sample rate is constant, default False
    """

    def __init__(self, sensor_name: str, sensor_data: pd.DataFrame, sample_rate: float = np.nan,
                 sample_interval_s: float = np.nan, sample_interval_std_s: float = np.nan,
                 is_sample_rate_fixed: bool = False):
        """
        initialize the sensor data with params
        :param sensor_name: str, name of the sensor
        :param sensor_data: dataframe with the timestamps and sensor data
        :param sample_rate: float, sample rate in hz of the data
        :param sample_interval_s: float, sample interval in seconds of the data
        :param sample_interval_std_s: float, std dev of sample interval in seconds of the data
        :param is_sample_rate_fixed: bool, if True, sample rate is constant for all data, default False
        """
        if "timestamps" not in sensor_data.columns:
            raise AttributeError('SensorData requires the data frame to contain a column titled "timestamps"')
        self.name: str = sensor_name
        self.data_df: pd.DataFrame = sensor_data
        self.sample_rate: float = sample_rate
        self.sample_interval_s: float = sample_interval_s
        self.sample_interval_std_s: float = sample_interval_std_s
        self.is_sample_rate_fixed: bool = is_sample_rate_fixed
        self.sort_by_data_timestamps()
        # todo: store the non-consecutive timestamp indices (idk how to find those)

    def is_sample_interval_invalid(self) -> bool:
        """
        :return: True if sample interval is np.nan or equal to 0.0
        """
        return np.isnan(self.sample_interval_s) or self.sample_interval_s == 0.0

    def organize_and_update_stats(self):
        """
        sorts the data by timestamps, then if the sample rate is not fixed, recalculates the sample rate, interval,
            and interval std dev.  If there is only one value, sets the sample rate, interval, and interval std dev
            to np.nan.  Updates the SensorData object with the new values
        """
        self.sort_by_data_timestamps()
        if not self.is_sample_rate_fixed:
            if self.num_samples() > 1:
                timestamp_diffs = np.diff(self.data_timestamps())
                self.sample_interval_s = dtu.microseconds_to_seconds(float(np.mean(timestamp_diffs)))
                self.sample_interval_std_s = dtu.microseconds_to_seconds(float(np.std(timestamp_diffs)))
                self.sample_rate = np.nan if self.is_sample_interval_invalid() else 1 / self.sample_interval_s
            else:
                self.sample_interval_s = np.nan
                self.sample_interval_std_s = np.nan
                self.sample_rate = np.nan

    def append_data(self, new_data: pd.DataFrame, recalculate_stats: bool = False) -> 'SensorData':
        """
        append the new data to the dataframe, update the sensor's stats on demand if it doesn't have a fixed
            sample rate, then return the updated SensorData object
        :param new_data: Dataframe containing data to add to the sensor's dataframe
        :param recalculate_stats: bool, if True and the sensor does not have a fixed sample rate, sort the timestamps,
                                    recalculate the sample rate, interval, and interval std dev, default False
        :return: the updated SensorData object
        """
        self.data_df = self.data_df.append(new_data, ignore_index=True)
        if recalculate_stats and not self.is_sample_rate_fixed:
            self.organize_and_update_stats()
        return self

    def samples(self) -> np.ndarray:
        """
        gets the samples of dataframe
        :return: the data values of the dataframe as a numpy ndarray
        """
        return self.data_df.iloc[:, 1:].T.to_numpy()

    def get_channel(self, channel_name: str) -> np.array:
        """
        gets the channel specified, raises an error and lists valid channels if channel_name is not in the dataframe
        :param channel_name: the name of the channel to get data for
        :return: the data values of the channel as a numpy array or a list of strings if the channel is enumerated
        """
        if channel_name not in self.data_df.columns:
            raise ValueError(f"WARNING: {channel_name} does not exist; try one of {self.data_fields()}")
        return self.data_df[channel_name].to_numpy()

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
        return self.data_df["timestamps"].to_numpy(dtype=np.float)

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
        get the number of samples in the sensor's dataframe
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
        get the names of the data fields of the sensor
        :return: a list of the names of the columns of the dataframe
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
