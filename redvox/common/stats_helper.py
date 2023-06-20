"""
Support for computing statistics
Requires numpy
"""

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import List, Union, Tuple

import numpy as np


@dataclass
@dataclass_json
class WelfordAggregator:
    """
    Helper class to compute Welford stats for a single data stream

    Properties:
        m2: float, aggregate squared distance from the mean.  Default 0.0

        mean: float, mean of the data.  Default 0.0

        count: int, number of data points.  Default 0
    """
    m2: float = 0.0
    mean: float = 0.0
    count: int = 0

    def update(self, val: float):
        """
        adds a new value to the WelfordAggregator

        :param val: value to add
        """
        self.count += 1
        delta = val - self.mean
        self.mean += delta / float(self.count)
        delta2 = val - self.mean
        self.m2 += delta * delta2

    def update_multiple(self, vals: List[float]):
        """
        adds each value from a list of values to the WelfordAggregator

        :param vals: list of values to add
        """
        for v in vals:
            self.update(v)

    def finalize(self) -> Tuple[float, float]:
        """
        Note: If the count of elements is less than 2, returns a tuple containing np.nan values

        :return: the mean, the m2 divided by the count as a tuple
        """
        if self.count < 2:
            return np.nan, np.nan
        return self.mean, self.m2 / float(self.count)


@dataclass
@dataclass_json
class WelfordStatsContainer:
    """
    Helper class to compute statistics for objects with a single data stream
    Stores the min, max and WelfordAggregator for the data

    Properties:
        min: float, minimum value of the data

        max: float, maximum value of the data

        welford: WelfordAggregator, collection of data used to compute mean, std deviation, variance, etc.
    """
    min: float = float("inf")
    max: float = -float("inf")
    welford: WelfordAggregator = WelfordAggregator()

    def update(self, val: float):
        """
        adds a new mean to the WelfordAggregator and updates the minimum and maximum values

        :param val: value to add
        """
        if val < self.min:
            self.min = val
        if val > self.max:
            self.max = val
        self.welford.update(val)

    def update_multiple(self, vals: List[float]):
        """
        adds many new means to the WelfordAggregator and updates the minimum and maximum values

        :param vals: values to add
        """
        for v in vals:
            self.update(v)

    def finalized(self) -> Tuple[float, float]:
        """
        :return: the mean and variance of the WelfordAggregator
        """
        return self.welford.finalize()


class StatsContainer:
    """
    Helper class to compute statistics for a set of objects
    Stores the mean, std dev, number of data points (count), and best value per set object
    Calculates mean of means, mean of variance, variance of means, total variance,
    and total std dev for the set of objects

    Properties:
        mean_array: the mean of each object in the set
        std_dev_array: the std_dev of each object in the set
        count_array: the number of elements in each object in the set
        best_value: the best value to represent the set
        container_id: a string that identifies the StatsContainer
    """

    def __init__(self, container_id: str) -> None:
        """
        Initialize the StatsContainer

        :param container_id: a string describing the container
        """
        self.mean_array: List[Union[float, int]] = []
        self.std_dev_array: List[Union[float, int]] = []
        self.count_array: List[Union[float, int]] = []
        self.best_value: float = 0.0
        self.container_id: str = container_id

    def mean_of_means(self) -> float:
        """
        :return: mean of all means
        """
        # convert non-numbers to 0s
        counts: np.ndarray = np.nan_to_num(self.count_array)
        if np.sum(counts) == 0:
            return np.nan
        # weight each mean by the number of elements in it
        total_means: np.ndarray = np.prod(
            [np.nan_to_num(self.mean_array), counts], axis=0
        )
        # if sum(counts) is 0, change sum(counts) to 1 to avoid divide by 0 errors
        return np.sum(total_means) / np.sum(counts)

    def mean_of_variance(self) -> float:
        """
        :return: mean of the variances
        """
        # convert non-numbers to 0s
        counts: np.ndarray = np.nan_to_num(self.count_array)
        if np.sum(counts) == 0:
            return np.nan
        std_devs: np.ndarray = np.nan_to_num(self.std_dev_array)
        # variance is std dev squared, which is then weighted by the number of elements for that variance
        total_vars: np.ndarray = np.prod([counts, std_devs, std_devs], axis=0)
        # if sum(counts) is 0, change sum(counts) to 1 to avoid divide by 0 errors
        return np.sum(total_vars) / np.sum(counts)

    def variance_of_means(self) -> float:
        """
        :return: variance of the means
        """
        counts: np.ndarray = np.nan_to_num(self.count_array)
        if np.sum(counts) == 0:
            return np.nan
        # get the difference of individual means and total mean
        mean_vars: np.ndarray = np.subtract(
            np.nan_to_num(self.mean_array), self.mean_of_means()
        )
        # square the differences then weight them by number of elements
        total: np.ndarray = np.prod([mean_vars, mean_vars, counts], axis=0)
        # if sum(counts) is 0, change sum(counts) to 1 to avoid divide by 0 errors
        return np.sum(total) / np.sum(counts)

    def total_variance(self) -> float:
        """
        :return: total variance of all elements
        """
        # mean of variances + variance of means = total variance
        return self.mean_of_variance() + self.variance_of_means()

    def total_std_dev(self) -> float:
        """
        :return: std dev of all elements (sqrt of total variance)
        """
        return np.sqrt(self.total_variance())  # std dev is square root of variance

    def add(
        self,
        mean: Union[float, int],
        std_dev: Union[float, int],
        count: Union[float, int],
    ) -> None:
        """
        Put an element into the arrays

        :param mean: a mean
        :param std_dev: the std dev for the mean
        :param count: how many values were used to calculate the mean
        """
        self.mean_array.append(mean)
        self.std_dev_array.append(std_dev)
        self.count_array.append(count)
