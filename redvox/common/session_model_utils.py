from typing import List, Optional, Tuple
from dataclasses import dataclass

import numpy as np


@dataclass
class LocationStat:
    """
    Stores the stats of a single location source.

    Variance and standard deviation tuples are optional arguments and will be set to 0 if none are given.
    If one is given when initialized, but not the other, the proper relational function will be applied to the
    existing value to get the other.

    If both are given, nothing is done to either value; we assume the user has provided the correct values.

    properties:
        source_name: str, name of the source of the location data.  Default empty string

        count: int, number of data points for that source.  Default 0

        means: Tuple of float, the mean of the latitude, longitude, and altitude.  Default tuple of np.nan

        variance: Optional Tuple of float, the variance of the latitude, longitude, and altitude.  Default tuple of 0

        std_dev: Optional Tuple of float, the standard deviations of latitude, longitude, and altitude.
        Default tuple of 0.
    """
    source_name: str = ""
    count: int = 0
    means: Tuple[float, float, float] = (np.nan, np.nan, np.nan)
    variance: Optional[Tuple[float, float, float]] = None
    std_dev: Optional[Tuple[float, float, float]] = None

    def __post_init__(self):
        """
        ensures the variance and std_dev values are correctly set
        """
        if self.variance is None and self.std_dev:
            self.variance = (self.std_dev[0] * self.std_dev[0],
                             self.std_dev[1] * self.std_dev[1],
                             self.std_dev[2] * self.std_dev[2])
        elif self.std_dev is None and self.variance:
            self.std_dev = tuple(np.sqrt(self.variance))
        elif self.std_dev is None and self.variance is None:
            self.variance = (0., 0., 0.)
            self.std_dev = (0., 0., 0.)

    def __str__(self):
        return f"source_name: {self.source_name}, " \
               f"count: {self.count}, " \
               f"means (lat, lon, alt): {self.means}, " \
               f"std_dev (lat, lon, alt): {self.std_dev}, " \
               f"variance (lat, lon, alt): {self.variance}"

    def as_dict(self) -> dict:
        """
        :return: LocationStat as a dictionary
        """
        return {
            "source_name": self.source_name,
            "count": self.count,
            "means": self.means,
            "variance": self.variance,
            "std_dev": self.std_dev,
        }

    @staticmethod
    def from_dict(data: dict) -> "LocationStat":
        """
        LocationStat from dictionary
        :param data: dictionary of LocationStat values
        """
        return LocationStat(data["source_name"], data["count"], data["means"], data["variance"], data["std_dev"])


class LocationStats:
    """
    Stores the stats of all locations

    protected:
        _location_stats: all the location stats, default empty list
    """
    def __init__(self, loc_stats: Optional[List[LocationStat]] = None):
        """
        initialize the stats

        :param loc_stats: the list of stats to start with, default None
        """
        self._location_stats: List[LocationStat] = [] if loc_stats is None else loc_stats

    def __repr__(self):
        return f"_location_stats: {[n for n in self._location_stats]}"

    def __str__(self):
        return f"stats: {[n.__str__() for n in self._location_stats]}"

    def as_dict(self) -> dict:
        """
        :return: LocationStats as a dictionary
        """
        return {"location_stats": [n.as_dict() for n in self._location_stats]}

    @staticmethod
    def from_dict(data: dict) -> "LocationStats":
        """
        Read LocationData from a LocationStats dictionary

        :param data: dictionary to read from
        """
        return LocationStats([LocationStat.from_dict(n) for n in data["location_stats"]])

    def add_loc_stat(self, new_loc: LocationStat):
        """
        adds a LocationStat to the stats

        :param new_loc: LocationStat to add
        """
        self._location_stats.append(new_loc)

    def get_all_stats(self) -> List[LocationStat]:
        """
        :return: all location stats
        """
        return self._location_stats.copy()

    def get_sources(self) -> List[str]:
        """
        :return: the sources of all location stats
        """
        return [n.source_name for n in self._location_stats]

    def get_stats_for_source(self, source: str) -> Optional[LocationStat]:
        """
        :param source: source name to get
        :return: LocationStat of source requested or None if source doesn't exist
        """
        for n in self._location_stats:
            if n.source_name == source:
                return n
        return None

    def has_source(self, source: str) -> bool:
        """
        :param source: the source name to check for
        :return: True if the source name is in the stats, False otherwise
        """
        for n in self._location_stats:
            if n.source_name == source:
                return True
        return False

    def add_count_by_source(self, source: str, val_to_add: int) -> Optional[LocationStat]:
        """
        :param source: the source name to update count for
        :param val_to_add: the number of new points to add to the count
        :return: the LocationStat with the same source name as the input, or None if the source doesn't exist
        """
        for n in self._location_stats:
            if n.source_name == source:
                n.count += val_to_add
                return n
        return None

    def add_means_by_source(self, source: str, val_to_add: int,
                            means_to_add: Tuple[float, float, float]) -> Optional[LocationStat]:
        """
        :param source: the source name to update count and means for
        :param val_to_add: the number of new points to add to the count
        :param means_to_add: the means of the location to add
        :return: the updated LocationStat with the same source name as the input, or None if the source doesn't exist
        """
        for n in self._location_stats:
            if n.source_name == source:
                n.count += val_to_add
                n.means = tuple(map(lambda i, j: i + ((j - i) / n.count), n.means, means_to_add))
                return n
        return None

    @staticmethod
    def _update_variances(num_old_samples: int, old_vari: float, old_mean: float,
                          num_new_samples: int, new_vari: float, new_mean: float) -> float:
        """
        adds new variance to old variance to get variance of total set

        :param num_old_samples: number of old samples
        :param old_vari: old variance
        :param num_new_samples: number of new samples
        :param new_vari: new variance
        :return: variance of total set
        """
        if num_old_samples + num_new_samples == 0:
            return 0.
        combined_mean = (num_old_samples * old_mean + num_new_samples * new_mean) / (num_old_samples + num_new_samples)
        return ((num_old_samples * (old_vari + np.power((old_mean - combined_mean), 2))
                 + num_new_samples * (new_vari + np.power((new_mean - combined_mean), 2)))
                / (num_old_samples + num_new_samples))

    def add_variance_by_source(self, source: str, val_to_add: int,
                               means_to_add: Tuple[float, float, float],
                               varis_to_add: Tuple[float, float, float]) -> LocationStat:
        """
        Adds data to a LocationStat with the same source, or creates a new LocationStat if source is not found.

        :param source: the source name to update count, means, and std dev for
        :param val_to_add: the number of new points to add to the count
        :param means_to_add: the means of the location to add
        :param varis_to_add: the variances of the location to add
        :return: the updated LocationStat with the same source name as the input
        """
        n = self.get_stats_for_source(source)
        if n is None:
            self.add_loc_stat(LocationStat(source, val_to_add, means_to_add, varis_to_add))
            return self._location_stats[-1]
        else:
            n.variance = (self._update_variances(n.count, n.variance[0], n.means[0],
                                                 val_to_add, varis_to_add[0], means_to_add[0]),
                          self._update_variances(n.count, n.variance[1], n.means[1],
                                                 val_to_add, varis_to_add[1], means_to_add[1]),
                          self._update_variances(n.count, n.variance[2], n.means[2],
                                                 val_to_add, varis_to_add[2], means_to_add[2]))
            n.std_dev = tuple(np.sqrt(n.variance))
            self.add_means_by_source(source, val_to_add, means_to_add)
            return n

    def add_std_dev_by_source(self, source: str, val_to_add: int,
                              means_to_add: Tuple[float, float, float],
                              stds_to_add: Tuple[float, float, float]) -> LocationStat:
        """
        Adds data to a LocationStat with the same source, or creates a new LocationStat if source is not found.

        :param source: the source name to update count, means, and std dev for
        :param val_to_add: the number of new points to add to the count
        :param means_to_add: the means of the location to add
        :param stds_to_add: the std devs of the location to add
        :return: the updated LocationStat with the same source name as the input
        """
        return self.add_variance_by_source(source, val_to_add, means_to_add,
                                           (stds_to_add[0]*stds_to_add[0],
                                            stds_to_add[1]*stds_to_add[1],
                                            stds_to_add[2]*stds_to_add[2]))


class CircularQueue:
    """
    Holds data in a fixed size queue that overwrites the oldest entry if allowed.

    Properties:
        capacity: int, size of the queue

        data: List, the actual data being stored

        head: int, index of the head of the queue.  Default 0

        tail: int, index of the tail of the queue.  Default -1

        size: int, number of actual data points in the queue.  Default 0.  Cannot be more than capacity.

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
        self.data: List = [None] * capacity
        self.head: int = 0
        self.tail: int = -1
        self.size: int = 0
        self.debug: bool = debug

    def __repr__(self):
        return f"capacity: {self.capacity}, " \
               f"head: {self.head}, " \
               f"tail: {self.tail}, " \
               f"size: {self.size}, " \
               f"data: {self.data}"

    def __str__(self):
        return f"capacity: {self.capacity}, " \
               f"head: {self.head}, " \
               f"tail: {self.tail}, " \
               f"size: {self.size}, " \
               f"data: {self.look_at_data()}"

    def as_dict(self) -> dict:
        """
        :return: CircularQueue as a dictionary
        """
        return {
            "capacity": self.capacity,
            "head": self.head,
            "tail": self.tail,
            "size": self.size,
            "data": self.data
        }

    @staticmethod
    def from_dict(data: dict) -> "CircularQueue":
        """
        :param data: dictionary to read from
        :return: CircularQueue defined by the dictionary
        """
        result = CircularQueue(data["capacity"])
        result.head = data["head"]
        result.tail = data["tail"]
        result.size = data["size"]
        result.data = data["data"]
        return result

    def _update_index(self, index: int):
        return (index + 1) % self.capacity

    def is_full(self) -> bool:
        return self.size == self.capacity

    def is_empty(self) -> bool:
        return self.size == 0

    def add(self, data: any, limit_size: bool = False):
        """
        adds data to the buffer.  Overwrites values unless limit_size is True

        :param data: data to add
        :param limit_size: if True, will not overwrite data if the buffer is full
        """
        if limit_size and self.is_full():
            if self.debug:
                print("Cannot add to full buffer.")
        else:
            self.tail = self._update_index(self.tail)
            self.data[self.tail] = data
            self.size = int(np.minimum(self.size + 1, self.capacity))
            if self.size == self.capacity and self.tail == self.head:
                self.head = self._update_index(self.head)

    def remove(self) -> any:
        """
        removes the head of the queue

        :return: data removed from the queue
        """
        if self.is_empty():
            if self.debug:
                print("Cannot remove from empty buffer.")
            return None
        result = self.data[self.head]
        self.head = self._update_index(self.head)
        self.size -= 1
        return result

    def peek(self) -> any:
        """
        :return: the data at the head index
        """
        if self.is_empty():
            if self.debug:
                print("Cannot look at empty buffer.")
            return None
        return self.data[self.head]

    def peek_tail(self) -> any:
        """
        :return: the data at the tail index
        """
        if self.is_empty():
            if self.debug:
                print("Cannot look at empty buffer.")
            return None
        return self.data[self.tail]

    def peek_index(self, index: int) -> any:
        """
        converts the index to be within the buffer's capacity if necessary

        :param index: index to look at
        :return: element at index
        """
        if self.is_empty():
            if self.debug:
                print("Cannot look at empty buffer.")
            return None
        return self.data[index % self.capacity]

    def look_at_data(self) -> List:
        """
        :return: all data in the queue as a list
        """
        if self.is_empty():
            if self.debug:
                print("Buffer is empty.")
            return []
        index = self.head
        result = []
        for i in range(self.size):
            result.append(self.data[index])
            index = self._update_index(index)
        return result
