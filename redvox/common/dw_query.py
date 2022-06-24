"""
This module defines how to access data from DataWindows by adding the edge points
"""
from typing import List

import numpy as np

from redvox.common.station_utils import StationKey
from redvox.common.sensor_data import SensorType, NON_NUMERIC_COLUMNS, COLUMN_TO_ENUM_FN


class DataWindowQuery:
    """
    Holds the data for a given sensor of a data window with added timestamps at start and end of window

    Protected:
        _station_key: unique station identifier

        _sensor_name: name of sensor the data came from

        _sensor_type: type of sensor the data came from

        _data: the data as a dictionary
    """
    def __init__(
            self,
            station_key: StationKey,
            sensor_name: str,
            sensor_type: SensorType,
            data: dict
    ):
        """
        Initialize the DataWindowQuery

        :param station_key: StationKey of station to get data from
        :param sensor_name: name of sensor to get data from
        :param sensor_type: type of sensor to get data from
        :param data: the data
        """
        self._station_key: StationKey = station_key
        self._sensor_name: str = sensor_name
        self._sensor_type: SensorType = sensor_type
        self._data: dict = data

    def __repr__(self):
        return f"station_key: {self._station_key.__repr__()}, " \
               f"sensor_name: {self._sensor_name}, " \
               f"sensor_type: {self._sensor_type}, " \
               f"column_names: {self.get_column_names()}"

    def __str__(self):
        return f"station_key: {self._station_key.__str__()}, " \
               f"sensor_name: {self._sensor_name}, " \
               f"sensor_type: {self._sensor_type}, " \
               f"column_names: {self.get_column_names()}"

    def get_station_id(self) -> str:
        """
        :return: station id
        """
        return self._station_key.id

    def get_station_uuid(self) -> str:
        """
        :return: station uuid
        """
        return self._station_key.uuid

    def get_station_start_date(self) -> float:
        """
        :return: station start date
        """
        return self._station_key.start_timestamp_micros

    def sensor_name(self) -> str:
        """
        :return: sensor name
        """
        return self._sensor_name

    def sensor_type(self) -> SensorType:
        """
        :return: sensor type
        """
        return self._sensor_type

    def sensor_type_as_str(self) -> str:
        """
        :return: sensor type as str
        """
        return self._sensor_type.name

    def data(self) -> np.ndarray:
        """
        :return: all data as an numpy ndarray
        """
        return np.asarray([self._data[c] for c in self.get_column_names()])

    def get_timestamps(self) -> np.array:
        """
        :return: timestamps as numpy array
        """
        return self._data["timestamps"].to_numpy()

    def get_column_names(self) -> List[str]:
        """
        :return: a list of data column names
        """
        return [*self._data.keys()]

    def get_column(self, column_name: str) -> np.array:
        """
        :param column_name: name of data column
        :return: the data of the column as a numpy array or empty array if column_name doesn't exist
        """
        if column_name not in self._data.keys():
            print(f"WARNING: {column_name} does not exist; try one of {self.get_column_names}")
            return []
        if column_name in NON_NUMERIC_COLUMNS:
            return np.array([COLUMN_TO_ENUM_FN[column_name](c) for c in self._data[column_name]])
        return self._data[column_name].to_numpy()

