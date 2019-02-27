"""
utilities to calculate std deviation, mean, and median for arrays
"""
import numpy


def calc_utils(values: numpy.array) -> (float, float, float):
    """
    returns the std deviation, the mean, and the median of an array
    :param values: array to calculate
    :return: std deviation, mean, median
    """
    stddev = numpy.std(values, dtype=float)
    mean = numpy.mean(values, dtype=float)
    median = numpy.median(values)
    return stddev, mean, median
