import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from typing import Tuple

MIN_VALID_LATENCY_MICROS = 100              # minimum value of latency before it's unreliable
DEFAULT_SAMPLES = 3                         # default number of samples per bin
MIN_SAMPLES = 3                             # minimum number of samples per 5 minutes for reliable data
MIN_TIMESYNC_DURATION_MIN = 5               # minimum number of minutes of data required to produce reliable results


class OffsetModel:
    """
    Offset model which represents the change in offset over a period of time
    Properties:
        start_time: float, start timestamp of model in microseconds since epoch UTC
        end_time: float, end timestamp of model in microseconds since epoch UTC
        k_bins: int, the number of data bins used to create the model
        n_samples: int, the number of samples per data bin; 3 is the minimum to create a balanced line
        slope: float, the slope of the change in offset
        intercept: float, the offset at start_time
    """
    def __init__(self, latencies: np.ndarray, offsets: np.ndarray, times: np.ndarray,
                 start_time: float, end_time: float, n_samples: int = DEFAULT_SAMPLES):
        """
        Create an OffsetModel
        :param latencies: latencies within the time specified
        :param offsets: offsets that correspond to the latencies
        :param times: timestamps that correspond to the latencies
        :param start_time: model's start timestamp in microseconds since epoch utc
        :param end_time: model's end timestamp in microseconds since epoch utc
        :param n_samples: number of samples per bin, default 3
        """
        self.start_time = start_time
        self.end_time = end_time
        self.k_bins = get_bins_per_5min(start_time, end_time)
        self.n_samples = n_samples
        latencies = np.where(latencies < MIN_VALID_LATENCY_MICROS, np.nan, latencies)
        use_model = timesync_quality_check(latencies, start_time, end_time)
        if use_model:
            self.slope, self.intercept = get_offset_function(latencies, offsets, times, self.k_bins,
                                                             n_samples, start_time, end_time)
            use_model = self.slope != 0.0
        # if data or model is not sufficient, use the offset corresponding to lowest latency:
        if not use_model:
            self.slope = 0.0
            if all(np.nan_to_num(latencies) == 0.0):
                self.intercept = 0.0
            else:
                best_latency = np.nanmin(latencies[np.nonzero(latencies)])
                self.intercept = offsets[np.argwhere(latencies == best_latency)[0][0]]

    @staticmethod
    def empty_model() -> "OffsetModel":
        """
        :return: an empty model with default values
        """
        return OffsetModel(np.array([]), np.array([]), np.array([]), 0, 0)

    def get_offset_at_new_time(self, new_time: float) -> float:
        """
        Get's offset at new_time time based on the offset model.
        :param new_time: The time of corresponding to the new offset
        :return: new offset corresponding to the new_time
        """
        return get_offset_at_new_time(new_time, self.slope, self.intercept, self.start_time)

    def update_time(self, new_time: float) -> float:
        """
        update new_time time based on the offset model.
        :param new_time: The time to update
        :return: updated new_time
        """
        return new_time + self.get_offset_at_new_time(new_time)


# Method to get number of bins
def get_bins_per_5min(start_time: float, end_time: float) -> int:
    """
    Calculates number of bins needed for roughly 5 minute bins.
        k_bins = int((end_time - start_time) / (300 * 1e6) + 1)
    :param start_time: the time used to compute the intercept (offset) and time bins; use start time of first packet
    :param end_time: the time used to compute the time bins; use start time of last packet + packet duration
    :return: number of bins to use for offset model
    """

    # Divide the duration by 5 minutes
    return int((end_time - start_time) / (1e6 * 300) + 1)


# min max scaling for the weights
def minmax_scale(data: np.ndarray) -> np.ndarray:
    """
    Returns scaled data by subtracting the min value and dividing by (max - min) value.
    :param data: the data to be scaled
    :return: scaled data
    """
    # Use np.nanmin and np.nanmax to avoid issues with nan values
    return (data - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data))


# The Weighted Linear Regression Function for offsets
def offset_weighted_linear_regression(latencies: np.ndarray, offsets: np.ndarray,
                                      times: np.ndarray) -> Tuple[float, float]:
    """
    Computes and returns the slope and intercept for the offset function (offset = slope * time + intercept)
    The intercept is based on first UTC time 0, all units are in microseconds
    :param latencies: array of the best latencies per packet
    :param offsets: array of offsets corresponding to the best latencies per packet
    :param times: array of device times corresponding to the best latencies per packet
    :return:  slope, intercept
    """

    if all(np.isnan(latencies)):
        return 0.0, 0.0

    # Compute the weights for the linear regression by the latencies
    latencies_ms = latencies / 1e3
    weights = latencies_ms ** -2
    norm_weights = minmax_scale(weights)

    # Set up the weighted linear regression
    wls = LinearRegression()
    wls.fit(X=times.reshape(-1, 1),
            y=offsets.reshape(-1, 1),
            sample_weight=norm_weights)

    # return the slope and intercept
    return wls.coef_[0][0], wls.intercept_[0]


# Function to correct the intercept value
def get_offset_at_new_time(new_time: float, slope: float, intercept: float, model_time: float) -> float:
    """
    Get's offset at new_time time based on the offset model.
    :param new_time: The time of corresponding to the new offset
    :param slope: slope of the offset model
    :param intercept: the intercept of the offset model relative to the model_time
    :param model_time: the time corresponding to the intercept of the offset model
    :return: new offset corresponding to the new_time
    """
    # get the time difference
    time_diff = new_time - model_time

    # apply the offset model to get new intercept
    new_offset = slope * time_diff + intercept

    return new_offset


# Function to get the subset data frame to do the weighted linear regression
def get_binned_df(full_df: pd.DataFrame, bin_times: np.ndarray, n_samples: float) -> pd.DataFrame:
    """
    Returns a subset of the full_df with n_samples per binned times.
    nan latencies values will be ignored.
    :param full_df: pandas DataFrame containing latencies, offsets, and times.
    :param bin_times: array of edge times for each bin
    :param n_samples: number of samples to take per bin
    :return: binned_df
    """

    # Initialize the data frame
    binned_df = pd.DataFrame()

    # Loop through each bin and get the n smallest samples
    for i in range(len(bin_times)-1):
        # select the time range
        select_df = full_df[full_df['times'] < bin_times[i + 1]]
        select_df = select_df[select_df['times'] > bin_times[i]]

        # select n_samples smallest values (ignores nan values)
        n_smallest = select_df.nsmallest(n_samples, 'latencies')

        # append the n_smallest entries
        binned_df = binned_df.append(n_smallest)

    # Sort the binned_df by time
    binned_df = binned_df.sort_values(by=['times'])

    return binned_df


# The main function
def get_offset_function(latencies: np.ndarray, offsets: np.ndarray, times: np.ndarray,
                        k_bins: int, n_samples: int, start_time: float, end_time: float) -> Tuple[float, float]:
    """
    Computes and returns the slope and intercept for the offset function (offset = slope * time + intercept)
    The data is binned by k_bins in equally spaced times, the n_samples best latencies are taken to be used to get
    the weighted linear regression. The slope and intercept is then returned as the offset model.
    The intercept is offset at first_start_time.
    :param latencies: array of the best latencies per packet
    :param offsets: array of offsets corresponding to the best latencies per packet
    :param times: array of device times corresponding to the best latencies per packet
    :param k_bins: number of bins to separate the latencies
    :param n_samples: number of points to use per bins
    :param start_time: the time used to compute the intercept (offset) and time bins; use start time of first packet
    :param end_time: the time used to compute the time bins; use start time of last packet + packet duration
    :return: slope, intercept
    """

    # Organize the data into a data frame
    full_df = pd.DataFrame(data=times, columns=['times'])
    full_df['latencies'] = latencies
    full_df['offsets'] = offsets

    # Get the index for the separations (add +1 to k_bins so that there would be k_bins bins)
    bin_times = np.linspace(start_time, end_time, k_bins + 1)

    # Make the dataframe with the data with n_samples per bins
    binned_df = get_binned_df(full_df=full_df,
                              bin_times=bin_times,
                              n_samples=n_samples)

    # Compute the weighted linear regression
    slope, zero_intercept = offset_weighted_linear_regression(latencies=binned_df['latencies'].values,
                                                              offsets=binned_df['offsets'].values,
                                                              times=binned_df['times'].values)

    # Get offset relative to the first time
    intercept = get_offset_at_new_time(new_time=start_time,
                                       slope=slope,
                                       intercept=zero_intercept,
                                       model_time=0)

    return slope, intercept


def timesync_quality_check(latencies: np.ndarray, start_time: float, end_time: float, debug: bool = False) -> bool:
    """
    Checks quality of timesync data to determine if offset model should be used.
    The following list is the quality check:
        If timesync duration is longer than 5 min
        If there are 3 latency values (non-nan) per 5 minutes on average
    Returns False if the data quality is not up to "standards".
    :param latencies: array of the best latencies per packet
    :param start_time: the time used to compute the intercept (offset) and time bins; use start time of first packet
    :param end_time: the time used to compute the time bins; use start time of last packet + packet duration
    :param debug: if True, reason for failing quality check is printed, default False
    :return: True if timesync data passes all quality checks, False otherwise
    """

    # Check the Duration of the signal of interest
    duration_min = (end_time - start_time) / (1e6 * 60)

    if duration_min < MIN_TIMESYNC_DURATION_MIN:
        if debug:
            print(f'Timesync data duration less than {MIN_TIMESYNC_DURATION_MIN} min')
        return False

    # Check average number of points per 5 min (pretty arbitrary, but maybe 3 points per 5 min)
    points_per_5min = 5 * np.count_nonzero(~np.isnan(latencies)) / duration_min

    if points_per_5min < MIN_SAMPLES:
        if debug:
            print(f'Less than {MIN_SAMPLES} of timesync data per 5 min')
        return False

    # Return True if it meets the above criteria
    return True
