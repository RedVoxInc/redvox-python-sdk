"""
Defines generic sensor data and metadata for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
"""
import enum
import numpy as np
import pandas as pd
from typing import List
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
        self.name: str = sensor_name
        self.data_df: pd.DataFrame = sensor_data
        self.sample_rate: float = sample_rate
        self.sample_interval_s: float = sample_interval_s
        self.sample_interval_std_s: float = sample_interval_std_s
        self.is_sample_rate_fixed: bool = is_sample_rate_fixed
        self.sort_by_data_timestamps()

    def copy(self) -> 'SensorData':
        """
        :return: An exact copy of the SensorData object
        """
        return SensorData(self.name, self.data_df.copy(), self.sample_rate, self.sample_interval_s,
                          self.sample_interval_std_s, self.is_sample_rate_fixed)

    def is_sample_interval_invalid(self) -> bool:
        """
        :return: True if sample interval is np.nan or equal to 0.0
        """
        return np.isnan(self.sample_interval_s) or self.sample_interval_s == 0.0

    def append_data(self, new_data: pd.DataFrame) -> 'SensorData':
        """
        append the new data to the dataframe, updating the sample interval and sample rate if its not fixed
            only considers non-nan values for the interval and sample rate
        the new_data has timestamps completely before or after the existing timestamps
        :return: the updated SensorData object
        """
        timestamps = np.array(self.data_timestamps())
        new_timestamps = new_data["timestamps"].to_numpy()
        self.data_df = pd.concat([self.data_df, new_data], ignore_index=True)
        self.sort_by_data_timestamps()
        if not self.is_sample_rate_fixed:
            if len(new_timestamps) > 1:
                if self.is_sample_interval_invalid():
                    self.sample_interval_s = dtu.microseconds_to_seconds(float(np.mean(np.diff(new_timestamps))))
                    self.sample_interval_std_s = dtu.microseconds_to_seconds(float(np.std(np.diff(new_timestamps))))
                else:
                    self.sample_interval_s = dtu.microseconds_to_seconds(float(np.mean(
                        np.concatenate([np.diff(timestamps), np.diff(new_timestamps)]))))
                    self.sample_interval_std_s = dtu.microseconds_to_seconds(float(np.std(
                        np.concatenate([np.diff(timestamps), np.diff(new_timestamps)]))))
            else:
                self.sample_interval_s = dtu.microseconds_to_seconds(float(np.mean(np.diff(self.data_timestamps()))))
                self.sample_interval_std_s = dtu.microseconds_to_seconds(float(np.std(np.diff(self.data_timestamps()))))
        self.sample_rate = np.nan if self.is_sample_interval_invalid() else 1 / self.sample_interval_s
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
