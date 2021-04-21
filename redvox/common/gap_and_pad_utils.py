from typing import List, Tuple, Optional

import pandas as pd
import numpy as np

from redvox.common import date_time_utils as dtu
from redvox.api1000.wrapped_redvox_packet.sensors.audio import AudioCodec
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
from redvox.api1000.wrapped_redvox_packet.sensors.image import ImageCodec
from redvox.api1000.wrapped_redvox_packet.station_information import NetworkType, PowerState, CellServiceState

# default maximum number of points required to brute force calculating gap timestamps
DEFAULT_MAX_BRUTE_FORCE_GAP_TIMESTAMPS: int = 5000
# percent of packet duration/sample rate required for gap to be considered a whole unit
DEFAULT_GAP_UPPER_LIMIT: float = 0.8
# percent of packet duration/sample rate required for gap to be considered nothing
DEFAULT_GAP_LOWER_LIMIT: float = 0.02
# columns for audio dataframe
AUDIO_DF_COLUMNS = ["timestamps", "unaltered_timestamps", "microphone"]
# columns that cannot be interpolated
NON_INTERPOLATED_COLUMNS = ["compressed_audio", "image"]
# columns that are not numeric but can be interpolated
NON_NUMERIC_COLUMNS = ["location_provider", "image_codec", "audio_codec",
                       "network_type", "power_state", "cell_service"]


def calc_evenly_sampled_timestamps(
        start: float, samples: int, sample_interval_micros: float
) -> np.array:
    """
    given a start time, calculates samples amount of evenly spaced timestamps at rate_hz

    :param start: float, start timestamp in microseconds
    :param samples: int, number of samples
    :param sample_interval_micros: float, sample interval in microseconds
    :return: np.array with evenly spaced timestamps starting at start
    """
    return start + (np.arange(0, samples) * sample_interval_micros)


def check_gap_list(gaps: List[Tuple[float, float]], start_timestamp: float = None,
                   end_timestamp: float = None) -> List[Tuple[float, float]]:
    """
    removes any gaps where end time <= start time, consolidates overlapping gaps, and ensures that no gap
    starts or ends before start_timestamp and starts or ends after end_timestamp.  All timestamps are in
    microseconds since epoch UTC

    :param gaps: list of gaps to check
    :param start_timestamp: lowest possible timestamp for a gap to start at
    :param end_timestamp: lowest possible timestamp for a gap to end at
    :return: list of correct, valid gaps
    """
    return_gaps: List[Tuple[float, float]] = []
    for gap in gaps:
        if start_timestamp:
            gap = (np.max([start_timestamp, gap[0]]), np.max([start_timestamp, gap[1]]))
        if end_timestamp:
            gap = (np.min([end_timestamp, gap[0]]), np.min([end_timestamp, gap[1]]))
        if gap[0] < gap[1]:
            if len(return_gaps) < 1:
                return_gaps.append(gap)
            for a, r_g in enumerate(return_gaps):
                if (gap[0] < r_g[0] and gap[1] < r_g[0]) or (gap[0] > r_g[1] and gap[1] > r_g[1]):
                    return_gaps.append(gap)
                    break
                else:
                    if gap[0] < r_g[0] < gap[1]:
                        r_g = (gap[0], r_g[1])
                    if gap[0] < r_g[1] < gap[1]:
                        r_g = (r_g[0], gap[1])
                    return_gaps[a] = r_g
    return return_gaps


def pad_data(
        expected_start: float,
        expected_end: float,
        data_df: pd.DataFrame,
        sample_interval_micros: float,
) -> pd.DataFrame:
    """
    Pad the start and end of the dataframe with np.nan

    :param expected_start: timestamp indicating start time of the data to pad from
    :param expected_end: timestamp indicating end time of the data to pad from
    :param data_df: dataframe with timestamps as column "timestamps"
    :param sample_interval_micros: constant sample interval in microseconds
    :return: dataframe padded with np.nans in front and back to meet full size of expected start and end
    """
    # extract the necessary information to pad the data
    data_time_stamps = data_df["timestamps"].to_numpy()
    first_data_timestamp = data_time_stamps[0]
    last_data_timestamp = data_time_stamps[-1]
    result_df = data_df.copy()
    result_before_update_length = len(result_df) - 1
    # FRONT/END GAP FILL!  calculate the samples missing based on inputs
    if expected_start < first_data_timestamp:
        start_diff = first_data_timestamp - expected_start
        num_missing_samples = int(start_diff / sample_interval_micros)
        if num_missing_samples > 0:
            # add the gap data to the result dataframe
            result_df = add_dataless_timestamps_to_df(
                result_df,
                0,
                sample_interval_micros,
                num_missing_samples,
                True
            )
    if expected_end > last_data_timestamp:
        last_diff = expected_end - last_data_timestamp
        num_missing_samples = int(last_diff / sample_interval_micros)
        if num_missing_samples > 0:
            # add the gap data to the result dataframe
            result_df = add_dataless_timestamps_to_df(
                result_df,
                result_before_update_length,
                sample_interval_micros,
                num_missing_samples
            )
    return result_df.sort_values("timestamps", ignore_index=True)


def fill_gaps(
        data_df: pd.DataFrame,
        gaps: List[Tuple[float, float]],
        sample_interval_micros: float = np.nan,
        interpolate: bool = False
) -> pd.DataFrame:
    """
    fills gaps in the dataframe with np.nan or interpolated values by interpolating timestamps based on the
    calculated sample interval

    :param data_df: dataframe with timestamps as column "timestamps"
    :param gaps: list of tuples of known non-inclusive start and end timestamps of the gaps
    :param sample_interval_micros: known sample interval of the data points, if not given,
                                    sample rate will be calculated from existing non-gap points.  default np.nan
    :param interpolate: if True, interpolate the data points, otherwise fill with np.nan or defaults for enums,
                        default False
    :return: dataframe without gaps
    """
    # extract the necessary information to compute gap size and gap timestamps
    data_time_stamps = data_df["timestamps"].to_numpy()
    result_df = data_df.copy()
    if len(data_time_stamps) > 1:
        gaps = check_gap_list(gaps, data_time_stamps[0], data_time_stamps[-1])
        sample_intervals: List[float] = []
        must_fill: List[Tuple[float, float]] = []
        # check every pair of consecutive timestamps;
        # if any of the values are within or around a gap, it is unreliable
        gap_start = None
        gap_end = None
        if len(gaps) > 0:
            for t in range(len(data_time_stamps) - 1):
                not_gap = True
                for g in gaps:
                    # if first timestamp is in gap, then compute to second timestamp
                    # if second timestamp is in gap, then compute from first timestamp
                    if data_time_stamps[t] > g[0] and data_time_stamps[t+1] < g[1]:
                        not_gap = False
                    elif data_time_stamps[t] <= g[0] and data_time_stamps[t+1] >= g[1]:
                        not_gap = False
                        gap_start = data_time_stamps[t]
                        gap_end = data_time_stamps[t+1]
                    elif g[0] < data_time_stamps[t] < g[1]:
                        not_gap = False
                        gap_end = data_time_stamps[t+1]
                    elif g[0] < data_time_stamps[t+1] < g[1]:
                        not_gap = False
                        gap_start = data_time_stamps[t]
                if not_gap:
                    sample_intervals.append(data_time_stamps[t+1] - data_time_stamps[t])
                elif gap_start and gap_end:
                    must_fill.append((gap_start, gap_end))
                    gap_start = None
                    gap_end = None
        elif not np.isnan(sample_interval_micros):
            for i, k in enumerate(np.diff(data_time_stamps)):
                if k > sample_interval_micros * (1 + DEFAULT_GAP_LOWER_LIMIT):
                    must_fill.append((data_time_stamps[i], data_time_stamps[i + 1]))
        if len(sample_intervals) > 0:
            if np.isnan(sample_interval_micros):
                sample_interval_micros: float = float(np.mean(sample_intervals))
        if not np.isnan(sample_interval_micros):
            # std_sample_interval = np.std(sample_intervals)
            data_duration = data_time_stamps[-1] - data_time_stamps[0]
            expected_samples = (np.floor(data_duration / sample_interval_micros)
                                + (1 if data_duration % sample_interval_micros >=
                                   sample_interval_micros * DEFAULT_GAP_UPPER_LIMIT else 0)) + 1
            if expected_samples > len(data_time_stamps):
                for f in must_fill:
                    if interpolate:
                        gap_df = result_df.loc[result_df["timestamps"].isin(f)]
                        gap_df = create_interpolated_timestamps_df(gap_df, sample_interval_micros)
                    else:
                        gap_df = create_dataless_timestamps_df(f[0], sample_interval_micros, result_df.columns,
                                                               int((f[1] - f[0]) / sample_interval_micros) - 1)
                    result_df = pd.concat([result_df, gap_df], ignore_index=True)
    return result_df.sort_values("timestamps", ignore_index=True)


def fill_audio_gaps(
        packet_data: List[Tuple[float, np.array, int]],
        sample_interval_micros: float,
        gap_upper_limit: float = DEFAULT_GAP_UPPER_LIMIT,
        gap_lower_limit: float = DEFAULT_GAP_LOWER_LIMIT
) -> (pd.DataFrame, List[Tuple[float, float]]):
    """
    fills gaps in the dataframe with np.nan by interpolating timestamps based on the expected sample interval
      * ignores gaps with duration less than or equal to packet length * gap_lower_limit
      * converts gaps with duration greater than or equal to packet length * gap_upper_limit into a multiple of
        packet length

    :param packet_data: list of tuples, each tuple containing three pieces of packet information:
        * packet_start_timestamps: float of packet start timestamp in microseconds
        * audio_data: array of data points
        * samples_per_packet: int, number of samples in the packet
    :param sample_interval_micros: sample interval in microseconds
    :param gap_upper_limit: percentage of packet length required to confirm gap is at least 1 packet,
                            default DEFAULT_GAP_UPPER_LIMIT
    :param gap_lower_limit: percentage of packet length required to disregard gap, default DEFAULT_GAP_LOWER_LIMIT
    :return: dataframe without gaps and the list of timestamps of the non-inclusive start and end of the gaps
    """
    result_df = pd.DataFrame(np.transpose([[], [], []]), columns=AUDIO_DF_COLUMNS)
    last_data_timestamp: Optional[float] = None
    gaps = []
    for packet in packet_data:
        samples_in_packet = packet[2]
        start_ts = packet[0]
        packet_length = sample_interval_micros * samples_in_packet
        if last_data_timestamp:
            # check if start_ts is close to the last timestamp in data_timestamps
            last_timestamp_diff = start_ts - last_data_timestamp
            if np.abs(last_timestamp_diff) < gap_lower_limit * packet_length:
                start_ts = last_data_timestamp + sample_interval_micros
            elif last_timestamp_diff < 0:
                raise ValueError(f"ERROR: Packet start timestamp: {dtu.microseconds_to_seconds(start_ts)} is before "
                                 f"last timestamp of previous "
                                 f"packet: {dtu.microseconds_to_seconds(last_data_timestamp)}")
            else:
                if last_timestamp_diff > gap_upper_limit * packet_length:
                    num_samples = samples_in_packet
                else:
                    num_samples = np.ceil(last_timestamp_diff / sample_interval_micros) - 1
                gap_df = create_dataless_timestamps_df(last_data_timestamp, sample_interval_micros,
                                                       result_df.columns, num_samples)
                start_ts = gap_df["timestamps"].iloc[-1] + sample_interval_micros
                gaps.append((last_data_timestamp, start_ts))
                result_df = pd.concat([result_df, gap_df])
        estimated_ts = calc_evenly_sampled_timestamps(start_ts, samples_in_packet, sample_interval_micros)
        result_df = pd.concat([result_df, pd.DataFrame(np.transpose([estimated_ts, estimated_ts, packet[1]]),
                                                       columns=AUDIO_DF_COLUMNS)], ignore_index=True)
        last_data_timestamp = estimated_ts[-1]
    return result_df.sort_values("timestamps", ignore_index=True), gaps


def add_dataless_timestamps_to_df(dataframe: pd.DataFrame,
                                  start_index: int,
                                  sample_interval_micros: float,
                                  num_samples_to_add: int,
                                  add_to_start: bool = False,) -> pd.DataFrame:
    """
    adds dataless timestamps directly to a dataframe that already contains data
      Note:
        * dataframe must not be empty
        * start_index must be non-negative and less than the length of dataframe
        * num_samples_to_add must be greater than 0
        * the points are added onto the end and the result is not sorted

    :param dataframe: dataframe to add dataless timestamps to
    :param start_index: index of the dataframe to use as starting point for creating new values
    :param sample_interval_micros: sample interval in microseconds of the timestamps
    :param num_samples_to_add: the number of timestamps to create
    :param add_to_start: if True, subtracts sample_interval_micros from start_timestamp, default False
    :return: updated dataframe with synthetic data points
    """
    if len(dataframe) > start_index and len(dataframe) > 0 and num_samples_to_add > 0:
        start_timestamp = dataframe["timestamps"].iloc[start_index]
        dataframe = dataframe.append(
            create_dataless_timestamps_df(start_timestamp, sample_interval_micros,
                                          dataframe.columns, num_samples_to_add, add_to_start),
            ignore_index=True)
    return dataframe


def create_interpolated_timestamps_df(
        end_points: pd.DataFrame,
        sample_interval_micros: float,
        gap_upper_limit: float = DEFAULT_GAP_UPPER_LIMIT,
) -> pd.DataFrame:
    """
    Creates a dataframe using the start and end data points to create data points separated by sample_interval_micros
    between the start and end points

    :param end_points: pd.Dataframe containing start and end points to gap fill on
    :param sample_interval_micros: sample interval in microseconds of the timestamps
    :param gap_upper_limit: fraction of sample interval required to confirm gap is at least 1 sample interval
                            default DEFAULT_GAP_UPPER_LIMIT
    :return: a dataframe consisting of the created data points
    """
    result_df = pd.DataFrame(columns=end_points.columns)
    numeric = end_points[[col for col in end_points.columns
                          if col not in NON_INTERPOLATED_COLUMNS + NON_NUMERIC_COLUMNS]]
    numeric_start = numeric.iloc[0]
    numeric_end = numeric.iloc[1]
    numeric_diff = numeric_end - numeric_start
    new_numeric = numeric_start.copy()
    non_numeric = end_points[[col for col in end_points.columns if col in NON_NUMERIC_COLUMNS]]
    non_numeric_start = non_numeric.iloc[0]
    non_numeric_end = non_numeric.iloc[1]
    # check if we have a gap that's more than 1 interval + the minimum duration of another interval
    while numeric_diff["timestamps"] > sample_interval_micros * (1 + gap_upper_limit):
        slope = numeric_diff / numeric_diff["timestamps"]
        new_numeric += slope * sample_interval_micros
        if np.abs(numeric_start["timestamps"] - new_numeric["timestamps"]) \
                <= np.abs(numeric_end["timestamps"] - new_numeric["timestamps"]):
            non_numeric_diff = non_numeric_start
        else:
            non_numeric_diff = non_numeric_end
        non_interpolated_columns = [col for col in NON_INTERPOLATED_COLUMNS if col in result_df.columns]
        if len(non_interpolated_columns) > 0:
            non_interpolated = pd.DataFrame([np.full(len(non_interpolated_columns), np.nan)],
                                            columns=[non_interpolated_columns])
            non_numeric_diff = pd.concat([non_numeric_diff, non_interpolated])
        result_df = result_df.append(pd.concat([new_numeric, non_numeric_diff]), ignore_index=True)
        numeric_diff = numeric_end - new_numeric
    return result_df


def create_dataless_timestamps_df(
        start_timestamp: float,
        sample_interval_micros: float,
        columns: pd.Index,
        num_samples_to_add: int,
        add_to_start: bool = False,
) -> pd.DataFrame:
    """
    Creates an empty dataframe with num_samples_to_add timestamps, using columns as the columns

    the first timestamp created is 1 sample_interval_s from the start_timestamp

    :param start_timestamp: timestamp in microseconds since epoch UTC to start calculating other timestamps from
    :param sample_interval_micros: fixed sample interval in microseconds since epoch UTC
    :param columns: dataframe the non-timestamp columns of the dataframe
    :param num_samples_to_add: the number of timestamps to create
    :param add_to_start: if True, subtracts sample_interval_s from start_timestamp, default False
    :return: dataframe with timestamps and no data
    """
    empty_df = pd.DataFrame(np.full([num_samples_to_add, len(columns)], np.nan), columns=columns)
    if num_samples_to_add > 0:
        if add_to_start:
            sample_interval_micros = -sample_interval_micros
        t = start_timestamp + np.arange(1, num_samples_to_add + 1) * sample_interval_micros
        for column_index in columns:
            if column_index == "timestamps":
                empty_df[column_index] = t
            elif column_index == "location_provider":
                empty_df[column_index] = [LocationProvider.UNKNOWN for i in range(num_samples_to_add)]
            elif column_index == "image_codec":
                empty_df[column_index] = [ImageCodec.UNKNOWN for i in range(num_samples_to_add)]
            elif column_index == "audio_codec":
                empty_df[column_index] = [AudioCodec.UNKNOWN for i in range(num_samples_to_add)]
            elif column_index == "network_type":
                empty_df[column_index] = [NetworkType.UNKNOWN_NETWORK for i in range(num_samples_to_add)]
            elif column_index == "power_state":
                empty_df[column_index] = [PowerState.UNKNOWN_POWER_STATE for i in range(num_samples_to_add)]
            elif column_index == "cell_service":
                empty_df[column_index] = [CellServiceState.UNKNOWN for i in range(num_samples_to_add)]
    return empty_df
