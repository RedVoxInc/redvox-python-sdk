"""
Support for computing statistics
Requires numpy
"""

from typing import List, Union

import numpy as np


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
