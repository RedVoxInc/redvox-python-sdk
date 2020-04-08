"""
Provides common classes and methods for interacting with API 1000 protobuf data.
"""

import enum
from typing import Any, Callable, Dict, List, Optional, Union

from google.protobuf.json_format import MessageToDict, MessageToJson
import lz4.frame
import numpy as np
import scipy.stats

import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2

NAN: float = float("NaN")

PROTO_TYPES = Union[redvox_api_1000_pb2.RedvoxPacket1000,
                    redvox_api_1000_pb2.RedvoxPacket1000.StationInformation,
                    redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings,
                    redvox_api_1000_pb2.RedvoxPacket1000.SummaryStatistics,
                    redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.AudioChannel,
                    redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.SingleChannel,
                    redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.XyzChannel,
                    redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.LocationChannel,
                    redvox_api_1000_pb2.RedvoxPacket1000.UserInformation]

EMPTY_ARRAY: np.ndarray = np.array([])


class Unit(enum.Enum):
    METERS_PER_SECOND_SQUARED: int = 0
    KILOPASCAL: int = 1
    RADIANS_PER_SECOND: int = 2
    DECIMAL_DEGREES: int = 3
    METERS: int = 4
    METERS_PER_SECOND: int = 5
    MICROTESLA: int = 6
    LSB_PLUS_MINUS_COUNTS: int = 7
    MICROSECONDS_SINCE_UNIX_EPOCH: int = 8
    DECIBEL: int = 9
    DEGREES_CELSIUS: int = 10
    BYTE: int = 11
    PERCENTAGE: int = 12

    @staticmethod
    def from_proto(unit: redvox_api_1000_pb2.RedvoxPacket1000.Unit) -> 'Unit':
        return Unit(unit)

    def into_proto(self) -> redvox_api_1000_pb2.RedvoxPacket1000.Unit:
        return redvox_api_1000_pb2.RedvoxPacket1000.Unit.Value(self.name)


def check_type(value: Any,
               valid_types: List[Any],
               exception: Optional[Callable[[str], errors.Api1000Error]] = None,
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
        raise errors.Api1000TypeError(message)


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


def mean_sample_rate_hz_from_sample_ts_us(sample_ts_us: np.ndarray) -> float:
    sample_ts_s: np.ndarray = sample_ts_us / 1_000_000.0
    diffs: np.ndarray = np.diff(sample_ts_s)
    sample_rates_hz: np.ndarray = 1.0 / diffs
    return sample_rates_hz.mean()


def lz4_compress(data: bytes) -> bytes:
    return lz4.frame.compress(data, compression_level=16, return_bytearray=True)


def lz4_decompress(data: bytes) -> bytes:
    return lz4.frame.decompress(data, True)


class ProtoBase:
    def __init__(self, proto):
        self._proto = proto
        self._metadata: 'Metadata' = Metadata(self._proto.metadata)

    def get_proto(self) -> PROTO_TYPES:
        return self._proto

    def get_metadata(self) -> 'Metadata':
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


class SummaryStatistics(ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.SummaryStatistics):
        super().__init__(proto)

    @staticmethod
    def new() -> 'SummaryStatistics':
        proto: redvox_api_1000_pb2.RedvoxPacket1000.SummaryStatistics = redvox_api_1000_pb2.RedvoxPacket1000.SummaryStatistics()
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

    def update_from_values(self, values: np.ndarray):
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


class Payload(ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.Payload):
        super().__init__(proto)
        self._summary_statistics: SummaryStatistics = SummaryStatistics(proto.value_statistics)

    def get_unit(self) -> Unit:
        return Unit.from_proto(self._proto.unit)

    def set_unit(self, unit: Unit) -> 'Payload':
        check_type(unit, [Unit])
        self._proto.unit = unit.into_proto()
        return self

    def get_values_count(self) -> int:
        return len(self._proto.values)

    def get_values(self) -> np.ndarray:
        return np.array(self._proto.values)

    def set_values(self, values: np.ndarray, update_value_statistics: bool = False) -> 'Payload':
        check_type(values, [np.ndarray])
        self._proto.values[:] = list(values)

        if update_value_statistics:
            self._summary_statistics.update_from_values(self.get_values())

        return self

    def append_value(self, value: float, update_value_statistics: bool = False) -> 'Payload':
        check_type(value, [int, float])
        self._proto.values.append(value)

        if update_value_statistics:
            self._summary_statistics.update_from_values(self.get_values())

        return self

    def append_values(self, values: np.ndarray, update_value_statistics: bool = False) -> 'Payload':
        check_type(values, [np.ndarray])
        self._proto.values.extend(list(values))

        if update_value_statistics:
            self._summary_statistics.update_from_values(self.get_values())

        return self

    def clear_values(self, update_value_statistics: bool = False) -> 'Payload':
        self._proto.values[:] = []

        if update_value_statistics:
            self._summary_statistics.update_from_values(self.get_values())

        return self

    def get_summary_statistics(self) -> SummaryStatistics:
        return self._summary_statistics
