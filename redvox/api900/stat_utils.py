"""
utilities to calculate std deviation, mean, and median for arrays
"""

from typing import Tuple

# noinspection Mypy
import numpy


def calc_utils(values: numpy.array) -> Tuple[float, float, float]:
    """
    returns the std deviation, the mean, and the median of an array
    :param values: array to calculate
    :return: std deviation, mean, median
    """
    mean = numpy.mean(values, dtype=float)
    stddev = numpy.std(values, dtype=float)
    median = numpy.median(values)
    return stddev, mean, median


def calc_utils_timeseries(values: numpy.array) -> Tuple[float, float, float]:
    """
    returns the std deviation, mean and median of an array representing uneven timestamps
    creates a new array that contains the differences between two consecutive timestamps
    :param values: array containing uneven timestamps
    :return: std deviation, mean, median
    """
    if len(values) == 1:
        return 0.0, 0.0, 0.0

    values = numpy.diff(values)  # calculate differences
    mean = numpy.mean(values)
    stddev = numpy.std(values)
    median = numpy.median(values)
    return stddev, mean, median
