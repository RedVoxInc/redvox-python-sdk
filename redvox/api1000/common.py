"""
Provides common classes and methods for interacting with API 1000 protobuf data.
"""

from typing import Any, Dict, List, Optional, Union

from google.protobuf.json_format import MessageToDict, MessageToJson
import lz4.frame
import numpy as np
import scipy.stats

import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2

NAN: float = float("NaN")

PROTO_TYPES = Union[redvox_api_1000_pb2.RedvoxPacket1000,
                    redvox_api_1000_pb2.RedvoxPacket1000.DeviceInformation,
                    redvox_api_1000_pb2.RedvoxPacket1000.DeviceInformation.AppSettings,
                    redvox_api_1000_pb2.RedvoxPacket1000.SummaryStatistics,
                    redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.MicrophoneChannel,
                    redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.SingleChannel,
                    redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.XyzChannel,
                    redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.LocationChannel,
                    redvox_api_1000_pb2.RedvoxPacket1000.UserInformation]

EMPTY_ARRAY: np.ndarray = np.array([])


class ProtoBase:
    def __init__(self, proto: PROTO_TYPES):
        self._proto: PROTO_TYPES = proto
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


class Samples:
    def __init__(self, samples_proto, sample_statistics_proto: redvox_api_1000_pb2.RedvoxPacket1000.SummaryStatistics):
        self._samples_proto = samples_proto
        self._sample_statistics: SummaryStatistics = SummaryStatistics(
                sample_statistics_proto)

    def get_samples_count(self) -> int:
        return len(self._samples_proto)

    def get_samples(self) -> np.ndarray:
        return np.array(self._samples_proto)

    def set_samples(self, samples: np.ndarray, recompute_sample_statistics: bool = True) -> 'Samples':
        if not is_protobuf_repeated_numerical_type(samples):
            raise errors.Api1000TypeError(f"Expected a numpy.ndarray, but instead found a {type(samples)}")

        self._samples_proto[:] = list(samples)

        if recompute_sample_statistics:
            self._sample_statistics.update_from_values(samples)

        return self

    def append_samples(self, samples: np.ndarray, recompute_sample_statistics: bool = False) -> 'Samples':
        if not is_protobuf_repeated_numerical_type(samples):
            raise errors.Api1000TypeError(f"Expected a numpy.ndarray, but instead found a {type(samples)}")

        self._samples_proto.extend(list(samples))

        if recompute_sample_statistics:
            self._sample_statistics.update_from_values(self.get_samples())

        return self

    def append_sample(self, sample: float, recompute_sample_statistics: bool = False) -> 'Samples':
        if not is_protobuf_numerical_type(sample):
            raise errors.Api1000TypeError(f"Expected a float or int, but instead found a {type(sample)}")

        self._samples_proto.append(sample)

        if recompute_sample_statistics:
            self._sample_statistics.update_from_values(self.get_samples())

        return self

    def clear_samples(self, recompute_sample_statistics: bool = True) -> 'Samples':
        self._samples_proto[:] = []

        if recompute_sample_statistics:
            self._sample_statistics.update_from_values(EMPTY_ARRAY)

        return self

    def get_sample_statistics(self) -> 'SummaryStatistics':
        return self._sample_statistics

    def set_sample_statistics(self, sample_statistics: 'SummaryStatistics') -> 'Samples':
        if not isinstance(sample_statistics, SummaryStatistics):
            raise errors.Api1000TypeError(f"Expected an instance of SummaryStatistics, but instead found a "
                                          f"{type(sample_statistics)}")

        self._sample_statistics = sample_statistics
        return self

    def recompute_sample_statistics(self) -> 'Samples':
        self._sample_statistics.update_from_values(self.get_samples())
        return self


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
            if not isinstance(key, str):
                raise errors.Api1000TypeError(f"Expected a string key, but found a {type(key)}")
            if not isinstance(value, str):
                raise errors.Api1000TypeError(f"Expected a string value, but found a {type(key)}")

        self._metadata_proto.clear()
        for key, value in metadata.items():
            self._metadata_proto[key] = value

        return self

    def append_metadata(self, key: str, value: str) -> 'Metadata':
        if not isinstance(key, str):
            raise errors.Api1000TypeError(f"Expected a string key, but found a {type(key)}")
        if not isinstance(value, str):
            raise errors.Api1000TypeError(f"Expected a string value, but found a {type(key)}")

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
        if not is_protobuf_numerical_type(count):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a {type(count)}={count} "
                                                f"was provided")

        self._proto.count = count
        return self

    def get_mean(self) -> float:
        return self._proto.mean

    def set_mean(self, mean: float) -> 'SummaryStatistics':
        if not is_protobuf_numerical_type(mean):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a {type(mean)}={mean} "
                                                f"was provided")

        self._proto.mean = mean
        return self

    def get_median(self) -> float:
        return self._proto.median

    def set_median(self, median: float) -> 'SummaryStatistics':
        if not is_protobuf_numerical_type(median):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a {type(median)}={median}"
                                                f" was provided")

        self._proto.median = median
        return self

    def get_mode(self) -> float:
        return self._proto.mode

    def set_mode(self, mode: float) -> 'SummaryStatistics':
        if not is_protobuf_numerical_type(mode):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a {type(mode)}={mode} "
                                                f"was provided")

        self._proto.mode = mode
        return self

    def get_variance(self) -> float:
        return self._proto.variance

    def set_variance(self, variance: float) -> 'SummaryStatistics':
        if not is_protobuf_numerical_type(variance):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a "
                                                f"{type(variance)}={variance} was provided")

        self._proto.variance = variance
        return self

    def get_min(self) -> float:
        return self._proto.min

    def set_min(self, min_value: float) -> 'SummaryStatistics':
        if not is_protobuf_numerical_type(min_value):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a "
                                                f"{type(min_value)}={min_value} was provided")

        self._proto.min = min_value
        return self

    def get_max(self) -> float:
        return self._proto.max

    def set_max(self, max_value: float) -> 'SummaryStatistics':
        if not is_protobuf_numerical_type(max_value):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a "
                                                f"{type(max_value)}={max_value} was provided")

        self._proto.max = max_value
        return self

    def get_range(self) -> float:
        return self._proto.range

    def set_range(self, range_value: float) -> 'SummaryStatistics':
        if not is_protobuf_numerical_type(range_value):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a "
                                                f"{type(range_value)}={range_value} was provided")

        self._proto.range = range_value
        return self

    def update_from_values(self, values: np.ndarray):
        if not is_protobuf_repeated_numerical_type(values):
            raise errors.SummaryStatisticsError(f"A string is required, but a {type(values)}={values} was provided")

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
