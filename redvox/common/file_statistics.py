"""
This module provides utility functions for determining statistics of well structured RedVox data.
"""

from typing import Tuple, Union

import numpy as np

SAMPLE_RATE_HZ: np.ndarray = np.array([80, 800, 8000, 16000])  # list of accepted sample rates in Hz
BASE_NUMBER_POINTS: int = 4096  # the number of points to sample at the first sample rate
NUM_POINTS_FACTOR: int = 2**3  # the multiplier of points per increased sample rate

# total multiplier of base number of points, 1 multiplier per sample rate
POINTS_FACTOR_ARRAY: np.ndarray = np.array([1, NUM_POINTS_FACTOR, NUM_POINTS_FACTOR**2, 2*NUM_POINTS_FACTOR**2])

# total number of points per sample rate
DURATION_TOTAL_POINTS: np.ndarray = np.array(POINTS_FACTOR_ARRAY * BASE_NUMBER_POINTS)

# expected duration of packets in seconds
DURATION_SECONDS: np.ndarray = np.divide(DURATION_TOTAL_POINTS, SAMPLE_RATE_HZ)


def get_file_stats(sample_rate: Union[float, int]) -> Tuple[int, float]:
    """
    Get the number of samples in a decoder file and its duration in seconds.
    :param sample_rate: int or float, sample rate
    :returns: number of samples in file as int and file time duration in seconds as float
    """
    try:
        position: int = np.where(SAMPLE_RATE_HZ == sample_rate)[0][0]
    except Exception:
        raise ValueError(f'Sample rate {sample_rate} for mic data not recognized.')

    return DURATION_TOTAL_POINTS[position], DURATION_SECONDS[position]


def get_num_points_from_sample_rate(sample_rate: Union[float, int]) -> int:
    """
    Returns the number of data points in a packet given a sample rate
    :param sample_rate: A valid sample rate from the constants above
    :return: the number of data points in the packet in seconds
    """
    try:
        position: int = np.where(SAMPLE_RATE_HZ == sample_rate)[0][0]
        return DURATION_TOTAL_POINTS[position]
    except Exception:
        raise ValueError(f"Unknown sample rate {sample_rate} given to compute number of data points!")


def get_duration_seconds_from_sample_rate(sample_rate: Union[float, int]) -> float:
    """
    Returns the duration of a packet in seconds given a sample rate
    :param sample_rate: A valid sample rate from the constants above
    :return: the duration of the packet in seconds
    """
    try:
        position: int = np.where(SAMPLE_RATE_HZ == sample_rate)[0][0]
        return DURATION_SECONDS[position]
    except Exception:
        raise ValueError(f"Unknown sample rate {sample_rate} given to compute duration!")
