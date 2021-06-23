"""
This module provides utility functions for determining statistics of well structured RedVox data.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Iterator, List, Optional, Tuple, TYPE_CHECKING, Union
import math
import multiprocessing
from multiprocessing.pool import Pool

import numpy as np

from redvox.common.timesync import TimeSyncData
from redvox.common.parallel_utils import maybe_parallel_map

# noinspection Mypy
if TYPE_CHECKING:
    from redvox.api1000.wrapped_redvox_packet.sensors.audio import Audio
    from redvox.api1000.wrapped_redvox_packet.sensors.location import Location
    from redvox.api1000.wrapped_redvox_packet.sensors.sensors import Sensors
    from redvox.api1000.wrapped_redvox_packet.station_information import (
        StationInformation,
    )
    from redvox.api1000.wrapped_redvox_packet.timing_information import (
        TimingInformation,
    )
    from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
    from redvox.api900.wrapped_redvox_packet import WrappedRedvoxPacket

# noinspection Mypy
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc as us2dt

# noinspection Mypy
import redvox.common.io as io

SAMPLE_RATE_HZ: np.ndarray = np.array(
    [80, 800, 8000, 16000]
)  # list of accepted sample rates in Hz
BASE_NUMBER_POINTS: int = (
    4096  # the number of points to sample at the first sample rate
)
NUM_POINTS_FACTOR: int = 2 ** 3  # the multiplier of points per increased sample rate

# total multiplier of base number of points, 1 multiplier per sample rate
POINTS_FACTOR_ARRAY: np.ndarray = np.array(
    [1, NUM_POINTS_FACTOR, NUM_POINTS_FACTOR ** 2, 2 * NUM_POINTS_FACTOR ** 2]
)

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
    except Exception as ex:
        raise ValueError(
            f"Sample rate {sample_rate} for mic data not recognized."
        ) from ex

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
    except Exception as ex:
        raise ValueError(
            f"Unknown sample rate {sample_rate} given to compute number of data points!"
        ) from ex


def get_duration_seconds_from_sample_rate(sample_rate: Union[float, int]) -> float:
    """
    Returns the duration of a packet in seconds given a sample rate

    :param sample_rate: A valid sample rate from the constants above
    :return: the duration of the packet in seconds
    """
    try:
        position: int = np.where(SAMPLE_RATE_HZ == sample_rate)[0][0]
        return DURATION_SECONDS[position]
    except Exception as ex:
        raise ValueError(
            f"Unknown sample rate {sample_rate} given to compute duration!"
        ) from ex


def _map_opt(
    opt: Optional[Any], apply: Callable[[Optional[Any]], Optional[Any]]
) -> Optional[Any]:
    """
    Maps an optional with the given function. If the optional is None, None is returned.

    :param opt: The optional to map.
    :param apply: The function to apply to the optional if a value is present.
    :return: The mapped value.
    """
    if opt is None:
        return None

    return apply(opt)


def _map_opt_numeric(
    fn: Callable[[Optional[Any]], Optional[Any]],
    opt: Optional[Any],
) -> Optional[Any]:
    """
    Maps an optional with the given function. If the optional is None, None is returned.

    :param fn: The function to apply to the optional if a value is present.
    :param opt: The optional to map.
    :return: The mapped value.
    """
    if opt is None or math.isnan(opt):
        return None

    return fn(opt)


def _partition_list(lst: List[Any], chunks: int) -> List[Any]:
    """
    Partitions a list into k "chunks" of approximately equal length.
    Adapted from: Adopted from: https://stackoverflow.com/questions/2130016/splitting-a-list-into-n-parts-of-approximately-equal-length/37414115#37414115

    :param lst:
    :param chunks:
    :return:
    """
    n: int = len(lst)
    k: int = chunks
    return [
        lst[i * (n // k) + min(i, n % k) : (i + 1) * (n // k) + min(i + 1, n % k)]
        for i in range(k)
    ]


@dataclass
class GpsDateTime:
    """
    Represents timestamp pairings in API 1000 data.
    """

    mach_dt: datetime
    gps_dt: Optional[datetime]


def dur2td(us: float) -> timedelta:
    return timedelta(microseconds=us)


@dataclass
class StationStat:
    """
    A collection of station fields for a given API 900 or API 1000 packet.
    These are used for timing correction and gap detection.
    """

    station_id: str
    station_uuid: str
    app_start_dt: Optional[datetime]
    packet_start_dt: datetime
    server_recv_dt: Optional[datetime]
    gps_dts: Optional[List[GpsDateTime]]
    latency: Optional[float]
    best_latency_timestamp: Optional[float]
    offset: Optional[float]
    sample_rate_hz: Optional[float]
    packet_duration: Optional[timedelta]

    @staticmethod
    def from_native(native) -> "StationStat":
        return StationStat(
            native.station_id,
            native.station_uuid,
            _map_opt_numeric(us2dt, native.app_start_dt),
            _map_opt_numeric(us2dt, native.packet_start_dt),
            _map_opt_numeric(us2dt, native.server_recv_dt),
            None,
            native.latency,
            native.best_latency_timestamp,
            native.offset,
            native.sample_rate_hz,
            _map_opt_numeric(dur2td, native.packet_duration),
        )

    @staticmethod
    def from_api_900(packet: "WrappedRedvoxPacket") -> "StationStat":
        """
        Extracts the required fields from an API 900 packet.

        :param packet: API 900 packet to extract fields from.
        :return: An instance of StationStat.
        """
        mtz: Optional[float] = packet.mach_time_zero()

        best_offset = packet.best_offset()
        best_latency = packet.best_latency()
        if packet.has_time_synchronization_sensor():
            tsd = TimeSyncData(
                packet.redvox_id(),
                time_sync_exchanges_list=list(
                    packet.time_synchronization_sensor().payload_values()
                ),
                packet_start_timestamp=packet.app_file_start_timestamp_machine(),
                packet_end_timestamp=packet.end_timestamp_us_utc(),
                server_acquisition_timestamp=packet.server_timestamp_epoch_microseconds_utc(),
            )
            if not best_offset or not best_latency:
                best_offset = tsd.best_offset
                best_latency = tsd.best_latency
            best_latency_timestamp = tsd.get_best_latency_timestamp()
        else:
            best_latency_timestamp = np.nan

        # noinspection Mypy
        return StationStat(
            packet.redvox_id(),
            packet.uuid(),
            _map_opt(mtz, us2dt),
            us2dt(packet.app_file_start_timestamp_machine()),
            us2dt(packet.server_timestamp_epoch_microseconds_utc()),
            None,
            best_latency,
            best_latency_timestamp,
            best_offset,
            packet.microphone_sensor().sample_rate_hz()
            if packet.has_microphone_sensor()
            else np.nan,
            timedelta(seconds=packet.duration_s())
            if packet.has_microphone_sensor()
            else 0.0,
        )

    # noinspection Mypy
    @staticmethod
    def from_api_1000(packet: "WrappedRedvoxPacketM") -> "StationStat":
        """
        Extracts the required fields from an API 1000 packet.

        :param packet: API 1000 packet to extract fields from.
        :return: An instance of StationStat.
        """
        station_info: "StationInformation" = packet.get_station_information()
        timing_info: "TimingInformation" = packet.get_timing_information()
        sensors: "Sensors" = packet.get_sensors()
        location_sensor: Optional["Location"] = sensors.get_location()
        audio_sensor: Optional["Audio"] = sensors.get_audio()

        # Optionally extract the GPS timestamps if the location sensor is available
        gps_timestamps: Optional[List[GpsDateTime]] = None
        if location_sensor is not None:
            gps_timestamps = []
            _gps_timestamps = location_sensor.get_timestamps_gps().get_timestamps()
            _gps_timestamps_len = len(_gps_timestamps)
            for i, ts in enumerate(location_sensor.get_timestamps().get_timestamps()):
                # A GPS timestamp isn't always present in the location sensor. We can handle that here.
                gps_ts: Optional[datetime] = (
                    us2dt(_gps_timestamps[i])
                    if (i < _gps_timestamps_len and not np.isnan(_gps_timestamps[i]))
                    else None
                )
                gps_timestamps.append(GpsDateTime(us2dt(ts), gps_ts))

        best_offset = timing_info.get_best_offset()
        best_latency = timing_info.get_best_latency()
        if len(timing_info.get_synch_exchange_array()) > 0:
            tsd = TimeSyncData(
                station_info.get_id(),
                time_sync_exchanges_list=timing_info.get_synch_exchange_array(),
                packet_start_timestamp=timing_info.get_packet_start_mach_timestamp(),
                packet_end_timestamp=timing_info.get_packet_end_mach_timestamp(),
                server_acquisition_timestamp=timing_info.get_server_acquisition_arrival_timestamp(),
            )
            if not best_offset or not best_latency:
                best_offset = tsd.best_offset
                best_latency = tsd.best_latency
            best_latency_timestamp = tsd.get_best_latency_timestamp()
        else:
            best_latency_timestamp = np.nan

        return StationStat(
            station_info.get_id(),
            station_info.get_uuid(),
            us2dt(timing_info.get_app_start_mach_timestamp()),
            us2dt(timing_info.get_packet_start_mach_timestamp()),
            us2dt(timing_info.get_server_acquisition_arrival_timestamp()),
            gps_timestamps,
            best_latency,
            best_latency_timestamp,
            best_offset,
            _map_opt(audio_sensor, lambda sensor: sensor.get_sample_rate()),
            packet.get_packet_duration(),
        )


# noinspection PyTypeChecker,DuplicatedCode
def extract_stats_serial(index: io.Index) -> List[StationStat]:
    """
    Extracts StationStat information from packets stored in the provided index.

    :param index: Index of packets to extract information from.
    :return: A list of StationStat objects.
    """
    # noinspection Mypy
    stats_900: Iterator[StationStat] = map(
        StationStat.from_api_900,
        index.stream(io.ReadFilter(api_versions={io.ApiVersion.API_900})),
    )
    # noinspection Mypy
    stats_1000: Iterator[StationStat] = map(
        StationStat.from_api_1000,
        index.stream(io.ReadFilter(api_versions={io.ApiVersion.API_1000})),
    )
    return list(stats_900) + list(stats_1000)


def extract_stats_parallel(
    index: io.Index, pool: Optional[multiprocessing.pool.Pool] = None
) -> List[StationStat]:
    """
    Extracts StationStat information in parallel from packets stored in the provided index.

    :param index: Index of packets to extract information from.
    :param pool: optional multiprocessing pool.
    :return: A list of StationStat objects.
    """
    # Partition the index entries by number of cores
    num_cores: int = multiprocessing.cpu_count()
    partitioned: List[List[io.IndexEntry]] = _partition_list(index.entries, num_cores)
    indices: List[io.Index] = list(map(lambda entries: io.Index(entries), partitioned))

    # Run da buggahs in parallel
    # _pool: multiprocessing.pool.Pool = multiprocessing.Pool() if pool is None else pool
    # nested: List[List[StationStat]] = _pool.map(extract_stats_serial, indices)
    # if pool is None:
    #     _pool.close()
    nested: Iterator[List[StationStat]] = maybe_parallel_map(
        pool,
        extract_stats_serial,
        iter(indices),
        lambda: len(indices) > 128,
        chunk_size=64,
    )
    return [item for sublist in nested for item in sublist]


ExtractStatsFn: Callable[[io.Index, Optional[Pool]], List[StationStat]]

try:
    # noinspection PyUnresolvedReferences
    import redvox_native

    def extract_stats_native(
        index: io.Index, pool: Optional[Pool] = None
    ) -> List[StationStat]:
        # To native index
        native_index = index.to_native()
        # Get native stats
        # noinspection PyUnresolvedReferences
        native_stats = redvox_native.extract_stats(native_index)
        # To py result
        return list(map(StationStat.from_native, native_stats))

    ExtractStatsFn = extract_stats_native
except ImportError:
    ExtractStatsFn = extract_stats_parallel


def extract_stats(
    index: io.Index,
    pool: Optional[multiprocessing.pool.Pool] = None,
) -> List[StationStat]:
    """
    Extracts StationStat information from packets stored in the provided index.

    :param index: Index of packets to extract information from.
    :param pool: optional multiprocessing pool.
    :return: A list of StationStat objects.
    """
    return ExtractStatsFn(index, pool)
