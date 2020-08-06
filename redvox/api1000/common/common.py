"""
Provides common classes and methods for interacting with various API 1000 protobuf data.
"""

import enum
from typing import List, Tuple, Optional

import numpy as np

import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.common.date_time_utils as dt_utils
from redvox.api1000.common.decorators import wrap_enum
from redvox.api1000.common.generic import ProtoBase
from redvox.api1000.common.typing import check_type, none_or_empty

NAN: float = float("NaN")

EMPTY_ARRAY: np.ndarray = np.array([])


@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.Unit)
class Unit(enum.Enum):
    """
    Standard units expected to be used within API M.
    """
    UNKNOWN: int = 0
    METERS_PER_SECOND_SQUARED: int = 1
    KILOPASCAL: int = 2
    RADIANS_PER_SECOND: int = 3
    DECIMAL_DEGREES: int = 4
    METERS: int = 5
    METERS_PER_SECOND: int = 6
    MICROTESLA: int = 7
    LSB_PLUS_MINUS_COUNTS: int = 8
    MICROSECONDS_SINCE_UNIX_EPOCH: int = 9
    DECIBEL: int = 10
    DEGREES_CELSIUS: int = 11
    BYTE: int = 12
    PERCENTAGE: int = 13
    RADIANS: int = 14
    MICROAMPERES: int = 15
    CENTIMETERS: int = 16
    NORMALIZED_COUNTS: int = 17
    LUX: int = 18
    UNITLESS: int = 19
    PCM: int = 20


class SummaryStatistics(ProtoBase[redvox_api_m_pb2.RedvoxPacketM.SummaryStatistics]):
    """
    Encapsulates the API M SummaryStatistics protobuf message type and provides automatic stat updates from values.
    """
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.SummaryStatistics):
        super().__init__(proto)

    @staticmethod
    def new() -> 'SummaryStatistics':
        """
        Returns a new SummaryStatistics instance backed by a default SummaryStatistics protobuf message.
        :return: A new SummaryStatistics instance backed by a default SummaryStatistics protobuf message.
        """
        proto: redvox_api_m_pb2.RedvoxPacketM.SummaryStatistics = \
            redvox_api_m_pb2.RedvoxPacketM.SummaryStatistics()
        return SummaryStatistics(proto)

    def get_count(self) -> float:
        """
        Returns the count of values that were used to calculate these statistics.
        :return: The count of values that were used to calculate these statistics.
        """
        return self._proto.count

    def set_count(self, count: float) -> 'SummaryStatistics':
        """
        Sets the count of values that were used to calculate these statistics.
        :param count:
        :return:
        """
        check_type(count, [int, float])

        self._proto.count = count
        return self

    def get_mean(self) -> float:
        return self._proto.mean

    def set_mean(self, mean: float) -> 'SummaryStatistics':
        check_type(mean, [int, float])

        self._proto.mean = mean
        return self

    def get_standard_deviation(self) -> float:
        return self._proto.standard_deviation

    def set_variance(self, standard_deviation: float) -> 'SummaryStatistics':
        check_type(standard_deviation, [int, float])

        self._proto.standard_deviation = standard_deviation
        return self

    def get_min(self) -> float:
        return self._proto.min

    def set_min(self, min_value: float) -> 'SummaryStatistics':
        check_type(min_value, [int, float])

        self._proto.min = min_value
        return self

    def get_max(self) -> float:
        return self._proto.max

    def set_max(self, max_value: float) -> 'SummaryStatistics':
        check_type(max_value, [int, float])

        self._proto.max = max_value
        return self

    def get_range(self) -> float:
        return self._proto.range

    def set_range(self, range_value: float) -> 'SummaryStatistics':
        check_type(range_value, [int, float])

        self._proto.range = range_value
        return self

    def update_from_values(self, values: np.ndarray) -> 'SummaryStatistics':
        check_type(values, [np.ndarray])

        if none_or_empty(values):
            raise errors.SummaryStatisticsError("No values supplied for updating statistics")

        self._proto.count = len(values)
        self._proto.mean = values.mean()
        self._proto.standard_deviation = values.std()
        # noinspection PyArgumentList
        self._proto.min = values.min()
        # noinspection PyArgumentList
        self._proto.max = values.max()
        self._proto.range = self._proto.max - self._proto.min
        return self


def validate_summary_statistics(stats: SummaryStatistics) -> List[str]:
    errors_list = []
    if stats.get_count() < 1:
        errors_list.append("Summary statistics contains less than 1 element")
    return errors_list


class SamplePayload(ProtoBase[redvox_api_m_pb2.RedvoxPacketM.SamplePayload]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.SamplePayload):
        super().__init__(proto)
        self._summary_statistics: SummaryStatistics = SummaryStatistics(proto.value_statistics)

    @staticmethod
    def new() -> 'SamplePayload':
        return SamplePayload(redvox_api_m_pb2.RedvoxPacketM.SamplePayload())

    def get_unit(self) -> Unit:
        return Unit.from_proto(self._proto.unit)

    def set_unit(self, unit: Unit) -> 'SamplePayload':
        check_type(unit, [Unit])
        self._proto.unit = unit.into_proto()
        return self

    def get_values_count(self) -> int:
        return len(self._proto.values)

    def get_values(self) -> np.ndarray:
        return np.array(self._proto.values)

    def set_values(self, values: np.ndarray, update_value_statistics: bool = False) -> 'SamplePayload':
        check_type(values, [np.ndarray])
        self._proto.values[:] = list(values)

        if update_value_statistics:
            self._summary_statistics.update_from_values(self.get_values())

        return self

    def append_value(self, value: float, update_value_statistics: bool = False) -> 'SamplePayload':
        check_type(value, [int, float])
        self._proto.values.append(value)

        if update_value_statistics:
            self._summary_statistics.update_from_values(self.get_values())

        return self

    def append_values(self, values: np.ndarray, update_value_statistics: bool = False) -> 'SamplePayload':
        check_type(values, [np.ndarray])
        self._proto.values.extend(list(values))

        if update_value_statistics:
            self._summary_statistics.update_from_values(self.get_values())

        return self

    def clear_values(self, update_value_statistics: bool = False) -> 'SamplePayload':
        self._proto.values[:] = []

        if update_value_statistics:
            self._summary_statistics.update_from_values(self.get_values())

        return self

    def get_summary_statistics(self) -> SummaryStatistics:
        return self._summary_statistics


def validate_sample_payload(sample_payload: SamplePayload, payload_name: Optional[str] = None,
                            payload_unit: Optional[Unit] = None) -> List[str]:
    errors_list = []
    if payload_unit is None:
        if sample_payload.get_unit() not in Unit.__members__.values():
            errors_list.append(f"{payload_name if payload_name else 'Sample'} payload unit type is unknown")
    else:
        if sample_payload.get_unit() != payload_unit:
            errors_list.append(f"{payload_name if payload_name else 'Sample'} payload unit type is not {payload_unit}")
    if sample_payload.get_values_count() < 1:
        errors_list.append(f"{payload_name if payload_name else 'Sample'} payload values are missing")
    return errors_list


def sampling_rate_statistics(timestamps: np.ndarray) -> Tuple[float, float]:
    """
    Calculates the mean sample rate in Hz and standard deviation of the sampling rate.
    :param timestamps:
    :return: A tuple containing (mean_sample_rate, stdev_sample_rate)
    """
    sample_interval: np.ndarray = np.diff(timestamps)
    mean_sample_interval: float = sample_interval.mean()
    stdev_sample_interval: float = sample_interval.std()

    if mean_sample_interval <= 0:
        return 0.0, 0.0

    mean_sample_rate: float = 1.0 / dt_utils.microseconds_to_seconds(mean_sample_interval)
    stdev_sample_rate: float = mean_sample_rate ** 2 * dt_utils.microseconds_to_seconds(stdev_sample_interval)

    return mean_sample_rate, stdev_sample_rate


class TimingPayload(ProtoBase[redvox_api_m_pb2.RedvoxPacketM.TimingPayload]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.TimingPayload):
        super().__init__(proto)
        self._timestamp_statistics: SummaryStatistics = SummaryStatistics(proto.timestamp_statistics)

    @staticmethod
    def new() -> 'TimingPayload':
        return TimingPayload(redvox_api_m_pb2.RedvoxPacketM.TimingPayload())

    def set_default_unit(self) -> 'TimingPayload':
        return self.set_unit(Unit.MICROSECONDS_SINCE_UNIX_EPOCH)

    def update_timing_statistics_from_timestamps(self) -> 'TimingPayload':
        timestamps: np.ndarray = self.get_timestamps()
        self._timestamp_statistics.update_from_values(timestamps)
        sampling_tuple: Tuple[float, float] = sampling_rate_statistics(timestamps)
        mean_sampling_rate: float = sampling_tuple[0]
        stdev_sampling_rate: float = sampling_tuple[1]
        self._proto.mean_sample_rate = mean_sampling_rate
        self._proto.stdev_sample_rate = stdev_sampling_rate
        return self

    def get_unit(self) -> Unit:
        return Unit.from_proto(self._proto.unit)

    def set_unit(self, unit: Unit) -> 'TimingPayload':
        check_type(unit, [Unit])
        self._proto.unit = unit.into_proto()
        return self

    def get_timestamps_count(self) -> int:
        return len(self._proto.timestamps)

    def get_timestamps(self) -> np.ndarray:
        return np.array(self._proto.timestamps)

    def set_timestamps(self, timestamps: np.ndarray, update_value_statistics: bool = False) -> 'TimingPayload':
        check_type(timestamps, [np.ndarray])
        self._proto.timestamps[:] = list(timestamps)

        if update_value_statistics:
            self.update_timing_statistics_from_timestamps()

        return self

    def append_timestamp(self, timestamp: float, update_value_statistics: bool = False) -> 'TimingPayload':
        check_type(timestamp, [int, float])
        self._proto.timestamps.append(timestamp)

        if update_value_statistics:
            self.update_timing_statistics_from_timestamps()

        return self

    def append_timestamps(self, values: np.ndarray, update_value_statistics: bool = False) -> 'TimingPayload':
        check_type(values, [np.ndarray])
        self._proto.timestamps.extend(list(values))

        if update_value_statistics:
            self.update_timing_statistics_from_timestamps()

        return self

    def clear_timestamps(self, update_value_statistics: bool = False) -> 'TimingPayload':
        self._proto.timestamps[:] = []

        if update_value_statistics:
            self.update_timing_statistics_from_timestamps()

        return self

    def get_timestamp_statistics(self) -> SummaryStatistics:
        return self._timestamp_statistics

    def get_mean_sample_rate(self) -> float:
        return self._proto.mean_sample_rate

    def set_mean_sample_rate(self, mean_sample_rate: float) -> 'TimingPayload':
        check_type(mean_sample_rate, [int, float])
        if mean_sample_rate < 0:
            raise errors.ApiMError("mean_sample_rate must be strictly positive")

        self._proto.mean_sample_rate = mean_sample_rate
        return self

    def get_stdev_sample_rate(self) -> float:
        return self._proto.stdev_sample_rate

    def set_stdev_sample_rate(self, stdev_sample_rate: float) -> 'TimingPayload':
        check_type(stdev_sample_rate, [int, float])
        if stdev_sample_rate < 0:
            raise errors.ApiMError("stdev_sample_rate must be strictly positive")

        self._proto.stdev_sample_rate = stdev_sample_rate
        return self


def validate_timing_payload(timing_payload: TimingPayload) -> List[str]:
    errors_list = []
    # if not timing_payload.get_proto().HasField("unit"):
    #     errors_list.append("Timing payload unit type is missing")
    if timing_payload.get_unit() != Unit.MICROSECONDS_SINCE_UNIX_EPOCH:
        errors_list.append("Timing payload units are not in microseconds since unix epoch")
    # if timing_payload.get_proto().HasField("timestamps"):
    if timing_payload.get_timestamps_count() < 1:
        errors_list.append("Timing payload timestamps are missing")
    else:
        # we have timestamps, but we have to confirm they always increase in value
        timestamps = timing_payload.get_timestamps()
        if any(timestamps[i] >= timestamps[i + 1] for i in range(len(timestamps) - 1)):
            errors_list.append("Timing payload contains timestamps in non-ascending order")
    return errors_list
