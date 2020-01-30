import statistics
from typing import Dict, List

import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2
import redvox.api1000.common as common


class SummaryStatistics:
    def __init__(self, proto: redvox_api_1000_pb2.SummaryStatistics):
        self._proto: redvox_api_1000_pb2.SummaryStatistics = proto

    @staticmethod
    def new() -> 'SummaryStatistics':
        proto: redvox_api_1000_pb2.SummaryStatistics = redvox_api_1000_pb2.SummaryStatistics()
        return SummaryStatistics(proto)

    def get_count(self) -> float:
        return self._proto.count

    def set_count(self, count: float) -> 'SummaryStatistics':
        if not common.is_protobuf_numerical_type(count):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a {type(count)}={count} "
                                                f"was provided")

        self._proto.count = count
        return self

    def get_mean(self) -> float:
        return self._proto.mean

    def set_mean(self, mean: float) -> 'SummaryStatistics':
        if not common.is_protobuf_numerical_type(mean):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a {type(mean)}={mean} "
                                                f"was provided")

        self._proto.mean = mean
        return self

    def get_median(self) -> float:
        return self._proto.median

    def set_median(self, median: float) -> 'SummaryStatistics':
        if not common.is_protobuf_numerical_type(median):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a {type(median)}={median}"
                                                f" was provided")

        self._proto.median = median
        return self

    def get_mode(self) -> float:
        return self._proto.mode

    def set_mode(self, mode: float) -> 'SummaryStatistics':
        if not common.is_protobuf_numerical_type(mode):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a {type(mode)}={mode} "
                                                f"was provided")

        self._proto.mode = mode
        return self

    def get_variance(self) -> float:
        return self._proto.variance

    def set_variance(self, variance: float) -> 'SummaryStatistics':
        if not common.is_protobuf_numerical_type(variance):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a "
                                                f"{type(variance)}={variance} was provided")

        self._proto.variance = variance
        return self

    def get_min(self) -> float:
        return self._proto.min

    def set_min(self, min_value: float) -> 'SummaryStatistics':
        if not common.is_protobuf_numerical_type(min_value):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a "
                                                f"{type(min_value)}={min_value} was provided")

        self._proto.min = min_value
        return self

    def get_max(self) -> float:
        return self._proto.max

    def set_max(self, max_value: float) -> 'SummaryStatistics':
        if not common.is_protobuf_numerical_type(max_value):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a "
                                                f"{type(max_value)}={max_value} was provided")

        self._proto.max = max_value
        return self

    def get_range(self) -> float:
        return self._proto.range

    def set_range(self, range_value: float) -> 'SummaryStatistics':
        if not common.is_protobuf_numerical_type(range_value):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but instead a "
                                                f"{type(range_value)}={range_value} was provided")

        self._proto.range = range_value
        return self

    def get_metadata(self) -> Dict[str, str]:
        return common.get_metadata(self._proto.metadata)

    def set_metadata(self, metadata: Dict[str, str]) -> 'SummaryStatistics':
        for key, value in metadata.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise errors.SummaryStatisticsError(f"All keys and values in metadata must be strings, however a "
                                                    f"{}={} was provided")

        common.set_metadata(self._proto.metadata, metadata)
        return self

    def append_metadata(self, key: str, value: str) -> 'SummaryStatistics':
        if not isinstance(key, str) or not isinstance(value, str):
            raise errors.SummaryStatisticsError("All keys and values in metadata must be strings")

        self._proto.metadata[key] = value
        return self

    def update_from_values(self, values: List[float]):
        if not isinstance(values, list):
            raise errors.SummaryStatisticsError("Values must be a list")

        if common.none_or_empty(values):
            raise errors.SummaryStatisticsError("No values supplied for updating statistics")

        self._proto.count = len(values)
        self._proto.mean = statistics.mean(values)
        self._proto.median = statistics.median(values)

        try:
            self._proto.mode = statistics.mode(values)
        except statistics.StatisticsError:
            self._proto.mode = common.NAN

        try:
            self._proto.variance = statistics.variance(values)
        except statistics.StatisticsError:
            self._proto.variance = common.NAN

        self._proto.min = min(values)
        self._proto.max = max(values)
        self._proto.range = self._proto.max - self._proto.min

    def __str__(self) -> str:
        return str(self._proto)
