from typing import List, Tuple, Optional, Dict
import enum
from math import modf
from dataclasses import dataclass, field

from dataclasses_json import dataclass_json
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

from redvox.common import date_time_utils as dtu
from redvox.common.errors import RedVoxExceptions
from redvox.api1000.wrapped_redvox_packet.sensors.audio import AudioCodec
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
from redvox.api1000.wrapped_redvox_packet.sensors.image import ImageCodec
from redvox.api1000.wrapped_redvox_packet.station_information import \
    NetworkType, PowerState, CellServiceState, WifiWakeLock, ScreenState

# default maximum number of points required to brute force calculating gap timestamps
DEFAULT_MAX_BRUTE_FORCE_GAP_TIMESTAMPS: int = 5000
# percent of packet duration/sample rate required for gap to be considered a whole unit
DEFAULT_GAP_UPPER_LIMIT: float = 0.8
# percent of packet duration/sample rate required for gap to be considered nothing
DEFAULT_GAP_LOWER_LIMIT: float = 0.02
# columns for audio table
AUDIO_DF_COLUMNS = ["timestamps", "unaltered_timestamps", "microphone"]
# columns that cannot be interpolated
NON_INTERPOLATED_COLUMNS = ["compressed_audio", "image"]
# columns that are not numeric but can be interpolated
NON_NUMERIC_COLUMNS = ["location_provider", "image_codec", "audio_codec", "network_type",
                       "power_state", "cell_service", "wifi_wake_lock", "screen_state"]


# noinspection Mypy,DuplicatedCode
class DataPointCreationMode(enum.Enum):
    """
    Type of data point to create
    """

    NAN: int = 0
    COPY: int = 1
    INTERPOLATE: int = 2

    @staticmethod
    def list_names() -> List[str]:
        return [n.name for n in DataPointCreationMode]


@dataclass_json
@dataclass
class GapPadResult:
    """
    The result of filling gaps or padding a time series
    """
    result: Optional[pa.Table] = None
    gaps: List[Tuple[float, float]] = field(default_factory=lambda: [])
    errors: RedVoxExceptions = field(default_factory=lambda: RedVoxExceptions("GapPadResult"))

    def add_error(self, error: str):
        """
        add an error to the result
        :param error: error message to add
        """
        self.errors.append(error)


@dataclass_json
@dataclass
class AudioWithGaps:
    """
    Represents methods of reconstructing audio data with or without gaps in it

    Properties:
        sample_interval_micros: microseconds between sample points

        metadata: list of start times in microseconds since epoch UTC and the data to add

        gaps: the list of start and end points of gaps (the start and end are actual data points)

        errors: the errors encountered while getting the data
    """
    sample_interval_micros: float
    metadata: Optional[List[Tuple[float, pa.Table]]] = None
    gaps: List[Tuple[float, float]] = field(default_factory=lambda: [])
    errors: RedVoxExceptions = field(default_factory=lambda: RedVoxExceptions("AudioWithGaps"))

    def create_timestamps(self) -> pa.Table:
        """
        :return: converts the audio metadata into a data table
        """
        result_array = [[], [], []]
        for m in self.metadata:
            timestamps = calc_evenly_sampled_timestamps(m[0], m[1].num_rows, self.sample_interval_micros)
            result_array[0].extend(timestamps)
            result_array[1].extend(timestamps)
            result_array[2].extend(m[1]["microphone"].to_numpy())
        for gs, ge in self.gaps:
            num_samples = int((ge - gs) / self.sample_interval_micros) - 1
            timestamps = calc_evenly_sampled_timestamps(gs + self.sample_interval_micros, num_samples,
                                                        self.sample_interval_micros)
            gap_array = [timestamps, np.full(len(timestamps), np.nan)]
            result_array[0].extend(gap_array[0])
            result_array[1].extend(gap_array[0])
            result_array[2].extend(gap_array[1])
        ptable = pa.Table.from_pydict(dict(zip(AUDIO_DF_COLUMNS, result_array)))
        return pc.take(ptable, pc.sort_indices(ptable, sort_keys=[("timestamps", "ascending")]))

    def add_error(self, error: str):
        """
        add an error to the result
        :param error: error message to add
        """
        self.errors.append(error)


def calc_evenly_sampled_timestamps(
        start: float, samples: int, sample_interval_micros: float
) -> np.array:
    """
    given a start time, calculates samples amount of evenly spaced timestamps at rate_hz

    :param start: float, start timestamp in microseconds
    :param samples: int, number of samples
    :param sample_interval_micros: float, sample interval in microseconds
    :return: np.array with number of samples timestamps, evenly spaced starting at start
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


def fill_gaps(
        arrow_df: pa.Table,
        gaps: List[Tuple[float, float]],
        sample_interval_micros: float,
        copy: bool = False
) -> Tuple[pa.Table, List[Tuple[float, float]]]:
    """
    fills gaps in the table with np.nan or interpolated values by interpolating timestamps based on the
    calculated sample interval

    :param arrow_df: pyarrow table with data.  first column is "timestamps"
    :param gaps: list of tuples of known non-inclusive start and end timestamps of the gaps
    :param sample_interval_micros: known sample interval of the data points
    :param copy: if True, copy the data points, otherwise interpolate from edges, default False
    :return: table without gaps and the list of gaps
    """
    # extract the necessary information to compute gap size and gap timestamps
    data_time_stamps = arrow_df["timestamps"].to_numpy()
    if len(data_time_stamps) > 1:
        data_duration = data_time_stamps[-1] - data_time_stamps[0]
        expected_samples = (np.floor(data_duration / sample_interval_micros)
                            + (1 if data_duration % sample_interval_micros >=
                               sample_interval_micros * DEFAULT_GAP_UPPER_LIMIT else 0)) + 1
        if expected_samples > len(data_time_stamps):
            if copy:
                pcm = DataPointCreationMode["COPY"]
            else:
                pcm = DataPointCreationMode["NAN"]
            # make it safe to alter the gap values
            my_gaps = check_gap_list(gaps, data_time_stamps[0], data_time_stamps[-1])
            for gap in my_gaps:
                # if timestamps are around gaps, we have to update the values
                before_start = np.argwhere([t <= gap[0] for t in data_time_stamps])
                after_end = np.argwhere([t >= gap[1] for t in data_time_stamps])
                if len(before_start) > 0:
                    before_start = before_start[-1][0]
                    # sim = gap[0] - data_time_stamps[before_start]
                    # result_df = add_data_points_to_df(result_df, before_start, sim, point_creation_mode=pcm)
                    gap = (data_time_stamps[before_start], gap[1])
                else:
                    before_start = None
                if len(after_end) > 0:
                    after_end = after_end[0][0]
                    # sim = gap[1] - data_time_stamps[after_end]
                    gap = (gap[0], data_time_stamps[after_end])
                else:
                    after_end = None
                num_new_points = int((gap[1] - gap[0]) / sample_interval_micros) - 1
                if before_start is not None:
                    arrow_df = add_data_points_to_df(arrow_df, before_start, sample_interval_micros,
                                                     num_new_points, pcm)
                elif after_end is not None:
                    arrow_df = add_data_points_to_df(arrow_df, after_end, -sample_interval_micros,
                                                     num_new_points, pcm)
        indic = pc.sort_indices(arrow_df, sort_keys=[("timestamps", "ascending")])
        return arrow_df.take(indic), gaps
    return arrow_df, gaps


def fill_audio_gaps2(
        packet_data: List[Tuple[float, pa.Table]],
        sample_interval_micros: float,
        gap_upper_limit: float = DEFAULT_GAP_UPPER_LIMIT,
        gap_lower_limit: float = DEFAULT_GAP_LOWER_LIMIT
) -> AudioWithGaps:
    """
    fills gaps in the table with np.nan by interpolating timestamps based on the expected sample interval
      * ignores gaps with duration less than or equal to packet length * gap_lower_limit
      * converts gaps with duration greater than or equal to packet length * gap_upper_limit into a multiple of
        packet length

    :param packet_data: list of tuples, each tuple containing two pieces of packet information:
                        packet_start_timestamps; float of packet start timestamp in microseconds
                        and audio_data; pa.Table of data points
    :param sample_interval_micros: sample interval in microseconds
    :param gap_upper_limit: percentage of packet length required to confirm gap is at least 1 packet,
                            default DEFAULT_GAP_UPPER_LIMIT
    :param gap_lower_limit: percentage of packet length required to disregard gap, default DEFAULT_GAP_LOWER_LIMIT
    :return: list of timestamps of the non-inclusive start and end of the gaps
    """
    last_data_timestamp = packet_data[0][0]
    gaps = []
    result = AudioWithGaps(sample_interval_micros, packet_data)
    for packet in packet_data:
        samples_in_packet = packet[1].num_rows
        start_ts = packet[0]
        packet_length = sample_interval_micros * samples_in_packet
        # check if start_ts is close to the last timestamp in data_timestamps
        last_timestamp_diff = start_ts - last_data_timestamp
        if last_timestamp_diff > gap_lower_limit * packet_length:
            fractional_packet, num_packets = modf(last_timestamp_diff /
                                                  (samples_in_packet * sample_interval_micros))
            if fractional_packet >= gap_upper_limit and num_packets < 1:
                num_samples = samples_in_packet * (num_packets + 1)
            else:
                num_samples = np.max([np.floor((fractional_packet + num_packets) * samples_in_packet), 1])
            gap_start = last_data_timestamp
            last_data_timestamp += (num_samples + 1) * sample_interval_micros
            gaps.append((gap_start, last_data_timestamp))
        elif last_timestamp_diff < -gap_lower_limit * packet_length:
            result.add_error(f"Packet start timestamp: {dtu.microseconds_to_seconds(start_ts)} "
                             f"is before last timestamp of previous "
                             f"packet: {dtu.microseconds_to_seconds(last_data_timestamp)}")
        last_data_timestamp += (samples_in_packet + 1) * sample_interval_micros
    result.gaps = gaps
    return result


def fill_audio_gaps(
        packet_data: List[Tuple[float, pa.Table]],
        sample_interval_micros: float,
        gap_upper_limit: float = DEFAULT_GAP_UPPER_LIMIT,
        gap_lower_limit: float = DEFAULT_GAP_LOWER_LIMIT
) -> GapPadResult:
    """
    fills gaps in the table with np.nan by interpolating timestamps based on the expected sample interval
      * ignores gaps with duration less than or equal to packet length * gap_lower_limit
      * converts gaps with duration greater than or equal to packet length * gap_upper_limit into a multiple of
        packet length

    :param packet_data: list of tuples, each tuple containing two pieces of packet information:
                        packet_start_timestamps; float of packet start timestamp in microseconds
                        and audio_data; pa.Table of data points
    :param sample_interval_micros: sample interval in microseconds
    :param gap_upper_limit: percentage of packet length required to confirm gap is at least 1 packet,
                            default DEFAULT_GAP_UPPER_LIMIT
    :param gap_lower_limit: percentage of packet length required to disregard gap, default DEFAULT_GAP_LOWER_LIMIT
    :return: table without gaps and the list of timestamps of the non-inclusive start and end of the gaps
    """
    result_array = [[], [], []]
    last_data_timestamp: Optional[float] = None
    gaps = []
    result = GapPadResult()
    for packet in packet_data:
        samples_in_packet = packet[1].num_rows
        start_ts = packet[0]
        packet_length = sample_interval_micros * samples_in_packet
        if last_data_timestamp:
            last_data_timestamp += sample_interval_micros
            # check if start_ts is close to the last timestamp in data_timestamps
            last_timestamp_diff = start_ts - last_data_timestamp
            if last_timestamp_diff > gap_lower_limit * packet_length:
                fractional_packet, num_packets = modf(last_timestamp_diff /
                                                      (samples_in_packet * sample_interval_micros))
                if fractional_packet >= gap_upper_limit:
                    num_samples = samples_in_packet * (num_packets + 1)
                else:
                    num_samples = np.max([np.floor((fractional_packet + num_packets) * samples_in_packet), 1])
                gap_ts = calc_evenly_sampled_timestamps(last_data_timestamp, num_samples, sample_interval_micros)
                gap_array = [gap_ts, np.full(len(gap_ts), np.nan)]
                start_ts = gap_ts[-1] + sample_interval_micros
                gaps.append((last_data_timestamp, start_ts))
                result_array[0].extend(gap_array[0])
                result_array[1].extend(gap_array[0])
                result_array[2].extend(gap_array[1])
            elif last_timestamp_diff < -gap_lower_limit * packet_length:
                result.add_error(f"Packet start timestamp: {dtu.microseconds_to_seconds(start_ts)} "
                                 f"is before last timestamp of previous "
                                 f"packet: {dtu.microseconds_to_seconds(last_data_timestamp)}")
                # return result
        estimated_ts = calc_evenly_sampled_timestamps(start_ts, samples_in_packet, sample_interval_micros)
        last_data_timestamp = estimated_ts[-1]
        result_array[0].extend(estimated_ts)
        result_array[1].extend(estimated_ts)
        result_array[2].extend(packet[1]["microphone"].to_numpy())
    result.result = pa.Table.from_pydict(dict(zip(AUDIO_DF_COLUMNS, result_array)))
    result.gaps = gaps
    return result


def add_data_points_to_df(data_table: pa.Table,
                          start_index: int,
                          sample_interval_micros: float,
                          num_samples_to_add: int = 1,
                          point_creation_mode: DataPointCreationMode = DataPointCreationMode.COPY,
                          ) -> pa.Table:
    """
    adds data points to the end of the table, starting from the index specified.
        Note:
            * table must not be empty
            * start_index must be non-negative and less than the length of table
            * num_samples_to_add must be greater than 0
            * sample_interval_micros cannot be 0
            * points are added onto the end and the result is not sorted
        Options for point_creation_mode are:
            * NAN: default values and nans
            * COPY: copies of the start data point
            * INTERPOLATE: interpolated values between start data point and adjacent point

    :param data_table: pyarrow table to add dataless timestamps to
    :param start_index: index of the table to use as starting point for creating new values
    :param sample_interval_micros: sample interval in microseconds of the timestamps; use negative values to
                                    add points before the start_index
    :param num_samples_to_add: the number of timestamps to create, default 1
    :param point_creation_mode: the mode of point creation to use
    :return: updated table with synthetic data points
    """
    if len(data_table) > start_index and len(data_table) > 0 and num_samples_to_add > 0 \
            and sample_interval_micros != 0.:
        start_timestamp = data_table["timestamps"][start_index].as_py()
        # create timestamps for every point that needs to be added
        new_timestamps = start_timestamp + np.arange(1, num_samples_to_add + 1) * sample_interval_micros
        if point_creation_mode == DataPointCreationMode.COPY:
            # copy the start point
            copy_row = data_table.slice(start_index, 1).to_pydict()
            for t in new_timestamps:
                copy_row["timestamps"] = [t]
                # for k in copy_row.keys():
                #     new_dict[k].append(copy_row[k])
            empty_df = pa.Table.from_pydict(copy_row)
        elif point_creation_mode == DataPointCreationMode.INTERPOLATE:
            # use the start point and the next point as the edges for interpolation
            start_point = data_table.slice(start_index, 1).to_pydict()
            numeric_start = start_point[[col for col in data_table.schema.names
                                         if col not in NON_INTERPOLATED_COLUMNS + NON_NUMERIC_COLUMNS]]
            non_numeric_start = start_point[[col for col in data_table.schema.names if col in NON_NUMERIC_COLUMNS]]
            end_point = data_table.slice(start_index + (1 if sample_interval_micros > 0 else -1), 1).to_pydict()
            numeric_end = end_point[[col for col in data_table.schema.names
                                     if col not in NON_INTERPOLATED_COLUMNS + NON_NUMERIC_COLUMNS]]
            non_numeric_end = end_point[[col for col in data_table.schema.names if col in NON_NUMERIC_COLUMNS]]
            if np.abs(start_point["timestamps"] - new_timestamps[0]) \
                    <= np.abs(end_point["timestamps"] - new_timestamps[0]):
                non_numeric_diff = non_numeric_start
            else:
                non_numeric_diff = non_numeric_end
            numeric_diff = numeric_end - numeric_start
            numeric_diff = \
                (numeric_diff / numeric_diff["timestamps"]) * \
                (new_timestamps - numeric_start) + numeric_start
            # merge dicts (python 3.5 to 3.8)
            empty_df = pa.Table.from_pydict({**numeric_diff, **non_numeric_diff})
            # merge dicts (python 3.9):
            # empty_df = pa.Table.from_pydict(numeric_diff | non_numeric_diff)
        else:
            # add nans and defaults
            empty_dict: Dict[str, List] = {}
            for k in data_table.schema.names:
                empty_dict[k] = []
            for column_index in data_table.schema.names:
                if column_index == "timestamps":
                    empty_dict[column_index] = new_timestamps
                elif column_index == "location_provider":
                    empty_dict[column_index] = [LocationProvider["UNKNOWN"].value for i in range(num_samples_to_add)]
                elif column_index == "image_codec":
                    empty_dict[column_index] = [ImageCodec["UNKNOWN"].value for i in range(num_samples_to_add)]
                elif column_index == "audio_codec":
                    empty_dict[column_index] = [AudioCodec["UNKNOWN"].value for i in range(num_samples_to_add)]
                elif column_index == "network_type":
                    empty_dict[column_index] = [NetworkType["UNKNOWN_NETWORK"].value for i in range(num_samples_to_add)]
                elif column_index == "power_state":
                    empty_dict[column_index] = [PowerState["UNKNOWN_POWER_STATE"].value
                                                for i in range(num_samples_to_add)]
                elif column_index == "cell_service":
                    empty_dict[column_index] = [CellServiceState["UNKNOWN"].value for i in range(num_samples_to_add)]
                elif column_index == "wifi_wake_lock":
                    empty_dict[column_index] = [WifiWakeLock["NONE"].value for i in range(num_samples_to_add)]
                elif column_index == "screen_state":
                    empty_dict[column_index] = [ScreenState["UNKNOWN_SCREEN_STATE"].value
                                                for i in range(num_samples_to_add)]
                else:
                    empty_dict[column_index] = np.full(num_samples_to_add, np.nan).tolist()
            empty_df = pa.Table.from_pydict(empty_dict)
        data_table = pa.concat_tables([data_table, empty_df])

    return data_table
