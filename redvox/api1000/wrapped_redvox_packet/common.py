"""
Provides common classes and methods for interacting with API 1000 protobuf data.
"""

import enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Tuple, Union

from google.protobuf.json_format import MessageToDict, MessageToJson
import lz4.frame
import numpy as np
import scipy.stats

import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_1000_pb2
import redvox.common.date_time_utils as dt_utils

NAN: float = float("NaN")

EMPTY_ARRAY: np.ndarray = np.array([])


class Unit(enum.Enum):
    METERS_PER_SECOND_SQUARED = 0
    KILOPASCAL = 1
    RADIANS_PER_SECOND = 2
    DECIMAL_DEGREES = 3
    METERS = 4
    METERS_PER_SECOND = 5
    MICROTESLA = 6
    LSB_PLUS_MINUS_COUNTS = 7
    MICROSECONDS_SINCE_UNIX_EPOCH = 8
    DECIBEL = 9
    DEGREES_CELSIUS = 10
    BYTE = 11
    PERCENTAGE = 12
    RADIANS = 13
    MICROAMPERES = 14
    CENTIMETERS = 15
    NORMALIZED_COUNTS = 16
    LUX = 17

    @staticmethod
    def from_proto(unit: redvox_api_1000_pb2.RedvoxPacketM.Unit) -> 'Unit':
        return Unit(unit)

    def into_proto(self) -> redvox_api_1000_pb2.RedvoxPacketM.Unit:
        return redvox_api_1000_pb2.RedvoxPacketM.Unit.Value(self.name)


def check_type(value: Any,
               valid_types: List[Any],
               exception: Optional[Callable[[str], errors.ApiMError]] = None,
               additional_info: Optional[str] = None) -> None:
    for valid_type in valid_types:
        if isinstance(value, valid_type):
            return None

    type_names: List[str] = list(map(lambda valid_type: f"'{valid_type.__name__}'", valid_types))
    message: str = f"Expected type(s) {' or '.join(type_names)}," \
                   f" but found '{type(value).__name__}'."

    if additional_info is not None:
        message += f" ({additional_info})"

    if exception is not None:
        raise exception(message)
    else:
        raise errors.ApiMTypeError(message)


def none_or_empty(value: Optional[Union[List, str, np.ndarray]]) -> bool:
    if value is None:
        return True

    return len(value) == 0


def is_protobuf_numerical_type(value: Any) -> bool:
    return isinstance(value, int) or isinstance(value, float)


def is_protobuf_repeated_numerical_type(values: Any) -> bool:
    if not isinstance(values, np.ndarray):
        return False

    if len(values) == 0:
        return True

    value = values.flat[0]
    return isinstance(value, np.floating) or isinstance(value, np.integer)


def lz4_compress(data: bytes) -> bytes:
    return lz4.frame.compress(data, compression_level=16, return_bytearray=True)


def lz4_decompress(data: bytes) -> bytes:
    return lz4.frame.decompress(data, True)


class Metadata:
    def __init__(self, metadata_proto):
        self._metadata_proto = metadata_proto

    def get_metadata_count(self) -> int:
        return len(self._metadata_proto)

    def get_metadata(self) -> Dict[str, str]:
        metadata_dict: Dict[str, str] = dict()
        for key, value in self._metadata_proto.items():
            metadata_dict[key] = value
        return metadata_dict

    def set_metadata(self, metadata: Dict[str, str]) -> 'Metadata':
        for key, value in metadata.items():
            check_type(key, [str])
            check_type(value, [str])

        self._metadata_proto.clear()
        for key, value in metadata.items():
            self._metadata_proto[key] = value

        return self

    def append_metadata(self, key: str, value: str) -> 'Metadata':
        check_type(key, [str])
        check_type(value, [str])

        self._metadata_proto[key] = value
        return self

    def clear_metadata(self) -> 'Metadata':
        self._metadata_proto.clear()
        return self


T = TypeVar('T')
P = TypeVar('P')


class ProtoBase(Generic[P]):
    def __init__(self, proto: P):
        self._proto: P = proto
        self._metadata: Metadata = Metadata(self._proto.metadata)

    def get_proto(self) -> P:
        return self._proto

    def get_metadata(self) -> Metadata:
        return self._metadata

    def as_json(self) -> str:
        return MessageToJson(self._proto, True)

    def as_dict(self) -> Dict:
        return MessageToDict(self._proto, True)

    def as_bytes(self) -> bytes:
        return self._proto.SerializeToString()

    def as_compressed_bytes(self) -> bytes:
        data: bytes = self.as_bytes()
        return lz4_compress(data)

    def __str__(self):
        return self.as_json()


class SummaryStatistics(ProtoBase[redvox_api_1000_pb2.RedvoxPacketM.SummaryStatistics]):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacketM.SummaryStatistics):
        super().__init__(proto)

    @staticmethod
    def new() -> 'SummaryStatistics':
        proto: redvox_api_1000_pb2.RedvoxPacketM.SummaryStatistics = redvox_api_1000_pb2.RedvoxPacketM.SummaryStatistics()
        return SummaryStatistics(proto)

    def get_count(self) -> float:
        return self._proto.count

    def set_count(self, count: float) -> 'SummaryStatistics':
        check_type(count, [int, float])

        self._proto.count = count
        return self

    def get_mean(self) -> float:
        return self._proto.mean

    def set_mean(self, mean: float) -> 'SummaryStatistics':
        check_type(mean, [int, float])

        self._proto.mean = mean
        return self

    def get_median(self) -> float:
        return self._proto.median

    def set_median(self, median: float) -> 'SummaryStatistics':
        check_type(median, [int, float])

        self._proto.median = median
        return self

    def get_mode(self) -> float:
        return self._proto.mode

    def set_mode(self, mode: float) -> 'SummaryStatistics':
        check_type(mode, [int, float])

        self._proto.mode = mode
        return self

    def get_variance(self) -> float:
        return self._proto.variance

    def set_variance(self, variance: float) -> 'SummaryStatistics':
        check_type(variance, [int, float])

        self._proto.variance = variance
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
        self._proto.median = np.median(values)
        self._proto.mode = scipy.stats.mode(values)[0]
        self._proto.variance = values.var()
        self._proto.min = values.min()
        self._proto.max = values.max()
        self._proto.range = self._proto.max - self._proto.min
        return self


def validate_summary_statistics(stats: SummaryStatistics) -> List[str]:
    errors_list = []
    if stats.get_count() < 1:
        errors_list.append("Less than 1 element detected; statistics are invalid.")
    return errors_list


class SamplePayload(ProtoBase[redvox_api_1000_pb2.RedvoxPacketM.SamplePayload]):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacketM.SamplePayload):
        super().__init__(proto)
        self._summary_statistics: SummaryStatistics = SummaryStatistics(proto.value_statistics)

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


def validate_sample_payload(sample_payload: SamplePayload) -> List[str]:
    errors_list = []
    # if not sample_payload.get_proto().HasField("unit"):
    #     errors_list.append("Sample payload unit type is missing")
    if sample_payload.get_unit() not in Unit.__members__.values():
        errors_list.append("Sample payload unit type is unknown")
    # if not sample_payload.get_proto().HasField("values") or
    if sample_payload.get_values_count() < 1:
        errors_list.append("Sample payload values are missing")
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


class ProtoRepeatedMessage(Generic[P, T]):
    def __init__(self,
                 parent_proto,
                 repeated_field_proto,
                 repeated_field_name: str,
                 from_proto: Callable[[P], T],
                 to_proto: Callable[[T], P]):
        self._parent_proto = parent_proto
        self._repeated_field_proto = repeated_field_proto
        self._repeated_field_name = repeated_field_name
        self._from_proto: Callable[[P], T] = from_proto
        self._to_proto: Callable[[T], P] = to_proto

    def get_count(self) -> int:
        return len(self._repeated_field_proto)

    def get_values(self) -> List[T]:
        return list(map(self._from_proto, self._repeated_field_proto))

    def set_values(self, values: List[T]) -> 'ProtoRepeatedMessage[P, T]':
        return self.clear_values().append_values(values)

    def append_values(self, values: List[T]) -> 'ProtoRepeatedMessage[P, T]':
        self._repeated_field_proto.extend(list(map(self._to_proto, values)))
        return self

    def clear_values(self) -> 'ProtoRepeatedMessage[P, T]':
        self._parent_proto.ClearField(self._repeated_field_name)
        return self


class TimingPayload(ProtoBase[redvox_api_1000_pb2.RedvoxPacketM.TimingPayload]):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacketM.TimingPayload):
        super().__init__(proto)
        self._timestamp_statistics: SummaryStatistics = SummaryStatistics(proto.timestamp_statistics)

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
    return errors_list
