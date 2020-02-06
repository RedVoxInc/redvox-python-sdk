import abc
from typing import Any, Dict, List, Optional, Union

import numpy as np
from google.protobuf.json_format import MessageToDict, MessageToJson

import redvox.api1000.summary_statistics as summary_statistics
import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2

NAN: float = float("NaN")


# RepeatedField = redvox_api_1000_pb2.google___protobuf___internal___containers___RepeatedScalarFieldContainer
# MapField = redvox_api_1000_pb2.typing___MutableMapping


class Samples:
    def __init__(self, samples_proto, sample_statistics_proto: redvox_api_1000_pb2.SummaryStatistics):
        self._samples_proto = samples_proto
        self._sample_statistics: summary_statistics.SummaryStatistics = summary_statistics.SummaryStatistics(
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
            pass

        return self

    def append_sample(self, sample: float, recompute_sample_statistics: bool = False) -> 'Samples':
        if not is_protobuf_numerical_type(sample):
            raise errors.Api1000TypeError(f"Expected a float or int, but instead found a {type(sample)}")

        self._samples_proto.append(sample)

        if recompute_sample_statistics:
            pass

        return self

    def clear_samples(self, recompute_sample_statistics: bool = True) -> 'Samples':
        self._samples_proto[:] = []

        if recompute_sample_statistics:
            pass

        return self

    def get_sample_statistics(self) -> summary_statistics.SummaryStatistics:
        return self._sample_statistics

    def set_sample_statistics(self, sample_statistics: summary_statistics.SummaryStatistics) -> 'Samples':
        if not isinstance(sample_statistics, summary_statistics.SummaryStatistics):
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


def none_or_empty(value: Union[List, str, np.ndarray]) -> bool:
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


def get_metadata(mutable_mapping) -> Dict[str, str]:
    metadata_dict: Dict[str, str] = dict()
    for key in mutable_mapping:
        metadata_dict[key] = mutable_mapping[key]
    return metadata_dict


def set_metadata(mutable_mapping,
                 metadata: Dict[str, str]) -> Optional[Any]:
    for key, value in metadata.items():
        if not isinstance(key, str):
            return key

        if not isinstance(value, str):
            return value

    mutable_mapping.clear()
    for key, value in metadata.items():
        mutable_mapping[key] = value

    return None


def append_metadata(mutable_mapping, key: str, value: str) -> Optional[Any]:
    if not isinstance(key, str):
        return key

    if not isinstance(value, str):
        return value

    mutable_mapping[key] = value

    return None


def as_json(value):
    return MessageToJson(value, True)


def as_dict(value) -> Dict:
    return MessageToDict(value, True)


def mean_sample_rate_hz_from_sample_ts_us(sample_ts_us: np.ndarray) -> float:
    sample_ts_s: np.ndarray = sample_ts_us / 1_000_000.0
    diffs: np.ndarray = np.diff(sample_ts_s)
    sample_rates_hz: np.ndarray = 1.0 / diffs
    return sample_rates_hz.mean()


if __name__ == "__main__":
    ts = np.array([0.0, 10_000_000.0, 20_000_000.0, 30_000_000.0])
    print(mean_sample_rate_hz_from_sample_ts_us(ts))
