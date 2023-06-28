"""
This module contains classes and functions that support SessionModel.
"""
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from bisect import insort
import enum

import numpy as np

from redvox.common.offset_model import OffsetModel
from redvox.common.timesync import TimeSync
from redvox.common.stats_helper import WelfordStatsContainer


class SensorModel:
    """
    A simple representation of a Sensor.  Sample rate data is in Hz

    Properties:
        name: str, name of the Sensor

        description: str, description of the Sensor

        sample_rate_stats: WelfordStatsContainer used to calculate the mean, std deviation, variance, etc. of the
        sensor's sample rate
    """
    def __init__(self, name: str, desc: str, mean_sample_rate: float):
        """
        initialize SensorModel

        :param name: name of the sensor
        :param desc: description of the sensor
        :param mean_sample_rate: mean sample rate of the sensor in Hz
        """
        self.name: str = name
        self.description: str = desc
        self.sample_rate_stats: WelfordStatsContainer = WelfordStatsContainer()
        self.sample_rate_stats.update(mean_sample_rate)

    def __repr__(self):
        return f"name: {self.name}, " \
               f"description: {self.description}, " \
               f"sample_rate_stats: {self.sample_rate_stats}"

    def to_dict(self) -> Dict:
        """
        :return: sensor model as dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "sample_rate_stats": self.sample_rate_stats.to_dict()
        }

    @staticmethod
    def from_dict(source: dict) -> "SensorModel":
        """
        :param source: dictionary to read
        :return: SensorModel from dictionary
        """
        result = SensorModel(source["name"], source["description"], 0)
        result.sample_rate_stats = WelfordStatsContainer.from_dict(source["sample_rate_stats"])
        return result

    def update(self, new_mean_sr: float):
        """
        adds a new mean sample rate to the SensorModel

        :param new_mean_sr: new mean sample rate to add
        """
        self.sample_rate_stats.update(new_mean_sr)

    def finalized(self) -> Tuple[float, float]:
        """
        :return: the mean and variance of the sample rate stats
        """
        return self.sample_rate_stats.finalized()


class FirstLastBuffer:
    """
    Holds data in two fixed size queues.  You can put more than the maximum capacity of elements into a
    queue, but it will remove elements until it reaches the capacity.

    Properties:
        capacity: int, maximum size of the queue

        data: List of Tuples; Tuples consist of timestamp in microseconds since epoch UTC
        and the actual data being stored

        debug: bool, if True, will output additional messages when errors occur.  Default False
    """
    def __init__(self, capacity: int, debug: bool = False):
        """
        Initialize the queue.
        Remember to only put the same type of data points into the queue.

        :param capacity: size of the queue
        :param debug: if True, output additional messages when errors occur, default False
        """
        self.capacity: int = capacity
        self.first_data: List[Tuple] = [] * (capacity + 1)
        self.last_data: List[Tuple] = [] * (capacity + 1)
        self.debug: bool = debug

    def __repr__(self):
        return f"capacity: {self.capacity}, " \
               f"first_data: {self.first_data}, " \
               f"last_data: {self.last_data}"

    def __str__(self):
        return f"capacity: {self.capacity}, " \
               f"\nfirst_data: [\n{self.first_data_as_string()}], " \
               f"\nlast_data: [\n{self.last_data_as_string()}]\n"

    def to_dict(self) -> dict:
        """
        :return: FirstLastBuffer as a dictionary
        """
        return {
            "capacity": self.capacity,
            "first_data": self.first_data,
            "last_data": self.last_data
        }

    @staticmethod
    def from_dict(data: dict) -> "FirstLastBuffer":
        """
        :param data: dictionary to read from
        :return: FirstLastBuffer defined by the dictionary
        """
        result = FirstLastBuffer(data["capacity"])
        result.first_data = data["first_data"]
        result.last_data = data["last_data"]
        return result

    def first_data_as_string(self) -> str:
        """
        :return: string representation of the first_data queue
        """
        return self._data_as_string(self.first_data)

    def last_data_as_string(self) -> str:
        """
        :return: string representation of the last_data queue
        """
        return self._data_as_string(self.last_data)

    @staticmethod
    def _data_as_string(data_list: List[Tuple]) -> str:
        """
        :param data_list: the list of tuples to return as a string
        :return: list as a string
        """
        result = ""
        for t, v in data_list:
            result += f"{t}: {str(v)}\n"
        return result

    @staticmethod
    def __ordered_insert(buffer: List, value: Tuple):
        """
        inserts the value into the buffer using the timestamp as the key

        :param value: value to add.  Must include a timestamp and the same data type as the other buffer elements
        """
        if len(buffer) < 1:
            buffer.append(value)
        else:
            insort(buffer, value)

    def add(self, timestamp: float, value):
        """
        add a value into one or more queues.
        If a queue is not full, the value is added automatically
        If the first_data queue is full, the value is only added if it comes before the last element.
        If the last_data queue is full, the value is only added if it comes after the first element.

        :param timestamp: timestamp in microseconds since epoch UTC to add.
        :param value: value to add.  Must be the same type of data as the other elements in the queue.
        """
        if len(self.first_data) < self.capacity or timestamp < self.first_data[-1][0]:
            self.__ordered_insert(self.first_data, (timestamp, value))
            while len(self.first_data) > self.capacity:
                self.first_data.pop()
        if len(self.last_data) < self.capacity or timestamp > self.last_data[0][0]:
            self.__ordered_insert(self.last_data, (timestamp, value))
            while len(self.last_data) > self.capacity:
                self.last_data.pop(0)


class TimeSyncModel:
    """
    TimeSync data used to build models
    All times and timestamps are in microseconds since epoch UTC

    Properties:
        first_timesync_timestamp: float, the first timestamp of the TimeSync data.  Default infinity

        last_timesync_timestamp: float, the last timestamp of the TimeSync data.  Default 0.0

        mean_latency: float, the mean latency of the TimeSync data.  Default 0.0

        mean_offset: float, the mean offset of the TimeSync data.  Default 0.0

        num_exchanges: int, number of exchanges in the TimeSync data.  Default 0

        first_last_timesync_data: FirstLastBuffer of TimeSync data, a fixed size list of timesync exchanges used to
                                    calculate the offset model.
    """
    def __init__(self,
                 capacity: int,
                 first_timesync_timestamp: float = float("inf"),
                 last_timesync_timestamp: float = 0.0,
                 mean_latency: float = 0.0,
                 mean_offset: float = 0.0,
                 num_exchanges: int = 0
                 ):
        """
        Initialize the TimeSyncModel

        :param capacity: the number of data points to keep in each of the first and last data buffers
        :param first_timesync_timestamp: the first timestamp of the TimeSync data.  Default infinity
        :param last_timesync_timestamp: the last timestamp of the TimeSync data.  Default 0.0
        :param mean_latency: the mean latency of the TimeSync data.  Default 0.0
        :param mean_offset: the mean offset of the TimeSync data.  Default 0.0
        :param num_exchanges: the number of exchanges in the TimeSync data.  Default 0
        """
        self.first_timesync_timestamp = first_timesync_timestamp
        self.last_timesync_timestamp = last_timesync_timestamp
        self.mean_latency = mean_latency
        self.mean_offset = mean_offset
        self.num_exchanges = num_exchanges
        self.first_last_timesync_data: FirstLastBuffer = FirstLastBuffer(capacity)

    def __repr__(self):
        return f"first_timesync_timestamp: {self.first_timesync_timestamp}, " \
               f"last_timesync_timestamp: {self.last_timesync_timestamp}, " \
               f"mean_latency: {self.mean_latency}, " \
               f"mean_offset: {self.mean_offset}, " \
               f"num_exchanges: {self.num_exchanges}, " \
               f"first_last_timesync_data: {self.first_last_timesync_data.to_dict()}"

    def to_dict(self) -> dict:
        """
        :return: TimeSyncModel as a dictionary
        """
        return {
            "first_timesync_timestamp": self.first_timesync_timestamp,
            "last_timesync_timestamp": self.last_timesync_timestamp,
            "mean_latency": self.mean_latency,
            "mean_offset": self.mean_offset,
            "num_exchanges": self.num_exchanges,
            "first_last_timesync_data": self.first_last_timesync_data.to_dict()
        }

    @staticmethod
    def from_dict(source: dict) -> "TimeSyncModel":
        """
        :param source: dictionary to read from
        :return: TimeSyncModel from dictionary
        """
        flb = FirstLastBuffer.from_dict(source["first_last_timesync_data"])
        result = TimeSyncModel(0, source["first_timesync_timestamp"],
                               source["last_timesync_timestamp"], source["mean_latency"], source["mean_offset"],
                               source["num_exchanges"])
        result.first_last_timesync_data = flb
        return result

    def update_model(self, ts: TimeSync):
        """
        Use a TimeSync object to update the TimeSyncModel

        :param ts: TimeSync object to update the model with
        """
        if ts.num_tri_messages() > 0:
            self.num_exchanges += ts.num_tri_messages()
            self.mean_latency = \
                (self.mean_latency * self.num_exchanges + ts.best_latency()) / (self.num_exchanges + 1)
            self.mean_offset = \
                (self.mean_offset * self.num_exchanges + ts.best_offset()) / (self.num_exchanges + 1)
            _ts_latencies = ts.latencies().flatten()
            _ts_offsets = ts.offsets().flatten()
            _ts_timestamps = ts.get_device_exchanges_timestamps()
            if ts.data_start_timestamp() < self.first_timesync_timestamp:
                self.first_timesync_timestamp = ts.data_start_timestamp()
            if ts.data_end_timestamp() > self.last_timesync_timestamp:
                self.last_timesync_timestamp = ts.data_end_timestamp()
            # add data to the buffers
            for i in range(len(_ts_timestamps)):
                self.first_last_timesync_data.add(_ts_timestamps[i], (_ts_latencies[i], _ts_offsets[i]))

    def create_offset_model(self) -> OffsetModel:
        """
        :return: OffsetModel using the data in the TimeSyncModel
        """
        latencies = []
        offsets = []
        timestamps = []
        for n in self.first_last_timesync_data.first_data:
            latencies.append(n[1][0])
            offsets.append(n[1][0])
            timestamps.append(n[0])
        for n in self.first_last_timesync_data.last_data:
            latencies.append(n[1][0])
            offsets.append(n[1][0])
            timestamps.append(n[0])
        return OffsetModel(np.array(latencies), np.array(offsets), np.array(timestamps),
                           self.first_timesync_timestamp, self.last_timesync_timestamp,
                           min_samples_per_bin=1)


class LocationModel:
    """
    Location data used to build models
    All times and timestamps are in microseconds since epoch UTC

    Properties:
        latitudes: WelfordStatsContainer for latitude values

        longitudes: WelfordStatsContainer for longitude values

        altitudes: WelfordStatsContainer for altitude values

        first_last_location_data: FirstLastBuffer of Location data, a fixed size list of location data points.
    """
    def __init__(self, capacity: int):
        """
        initialize a LocationModel

        :param capacity: int, number of data points to store in the first and last buffers.
        """
        self.latitudes = WelfordStatsContainer()
        self.longitudes = WelfordStatsContainer()
        self.altitudes = WelfordStatsContainer()
        self.first_last_location_data = FirstLastBuffer(capacity)

    def __repr__(self):
        return f"latitudes: {self.latitudes}, " \
               f"longitudes: {self.longitudes}, " \
               f"altitudes: {self.altitudes}, " \
               f"first_last_location_data: {self.first_last_location_data}"

    def __str__(self):
        return f"latitudes: {self.latitudes}, " \
               f"longitudes: {self.longitudes}, " \
               f"altitudes: {self.altitudes}, " \
               f"location data: {self.first_last_location_data}"

    def to_dict(self) -> dict:
        """
        :return: LocationModel as a dictionary
        """
        return {
            "latitudes": self.latitudes.to_dict(),
            "longitudes": self.longitudes.to_dict(),
            "altitudes": self.altitudes.to_dict(),
            "first_last_location_data": self.first_last_location_data.to_dict(),
        }

    @staticmethod
    def from_dict(source: dict) -> "LocationModel":
        """
        :param source: dictionary to read from
        :return: LocationModel
        """
        flb = FirstLastBuffer.from_dict(source["first_last_location_data"])
        result = LocationModel(0)
        result.latitudes = WelfordStatsContainer.from_dict(source["latitudes"])
        result.longitudes = WelfordStatsContainer.from_dict(source["longitudes"])
        result.altitudes = WelfordStatsContainer.from_dict(source["altitudes"])
        result.first_last_location_data = flb
        return result

    def update_location(self, lat: float, lon: float, alt: float, timestamp: float):
        """
        Add a location to the LocationStats

        :param lat: float, latitude in degrees
        :param lon: float, longitude in degrees
        :param alt: float, altitude in meters
        :param timestamp: float, timestamp of location in microseconds since epoch UTC
        """
        self.latitudes.update(lat)
        self.longitudes.update(lon)
        self.altitudes.update(alt)
        self.first_last_location_data.add(timestamp, (lat, lon, alt))

    def finalized_latitude(self) -> Tuple[float, float]:
        """
        :return: the mean and variance of the latitude
        """
        return self.latitudes.finalized()

    def finalized_longitude(self) -> Tuple[float, float]:
        """
        :return: the mean and variance of the longitude
        """
        return self.longitudes.finalized()

    def finalized_altitude(self) -> Tuple[float, float]:
        """
        :return: the mean and variance of the altitude
        """
        return self.altitudes.finalized()


class MetricsSessionModel:
    """
    Metrics stored by the SessionModel
    """
    def __init__(self, capacity: int):
        """
        initialize the metrics stored by the session model

        :param capacity: int, number of data points to store
        """
        self.capacity: int = capacity
        self.location: Dict[str, LocationModel] = {}
        self.battery: WelfordStatsContainer = WelfordStatsContainer()
        self.temperature: WelfordStatsContainer = WelfordStatsContainer()

    def __repr__(self):
        return f"location: {self.location}, " \
               f"battery: {self.battery}, " \
               f"temperature: {self.temperature}"

    def __str__(self):
        return f"location: {self.location}, " \
               f"battery percent: {self.battery}, " \
               f"temperature (C): {self.temperature}"

    def to_dict(self) -> dict:
        """
        :return: MetricsSessionModel as a dictionary
        """
        return {
            "capacity": self.capacity,
            "location": {n: m.to_dict() for n, m in self.location.items()},
            "battery": self.battery.to_dict(),
            "temperature": self.temperature.to_dict()
        }

    @staticmethod
    def from_dict(source: dict) -> "MetricsSessionModel":
        """
        :param source: dictionary to read from
        :return: MetricsSessionModel from dictionary
        """
        result = MetricsSessionModel(source["capacity"])
        result.location = {n: LocationModel.from_dict(m) for n, m in source["location"].items()}
        result.battery = WelfordStatsContainer.from_dict(source["battery"])
        result.temperature = WelfordStatsContainer.from_dict(source["temperature"])
        return result

    def add_location(self, source: str, lat: float, lon: float, alt: float, timestamp: float):
        """
        add a location from the named source to the session model

        :param source: str, name of the location data source
        :param lat: float, latitude in degrees
        :param lon: float, longitude in degrees
        :param alt: float, altitude in meters
        :param timestamp: float, timestamp of location in microseconds since epoch UTC
        """
        if source not in self.location.keys():
            self.location[source] = LocationModel(self.capacity)
        self.location[source].update_location(lat, lon, alt, timestamp)

    def add_battery(self, data: float):
        """
        add battery data to the session model

        :param data: float, battery percentage to add
        """
        self.battery.update(data)

    def add_temperature(self, data: float):
        """
        add temperature data to the session model

        :param data: float, temperature in Celsius to add
        """
        self.temperature.update(data)
