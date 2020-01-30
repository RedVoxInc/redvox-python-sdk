from typing import List, Union

import numpy as np

import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2
import redvox.api1000.summary_statistics as summary_statistics
import redvox.api1000.common as common


class MicrophoneChannel:
    def __init__(self, proto: redvox_api_1000_pb2.MicrophoneChannel):
        self._proto = proto

    @staticmethod
    def new() -> 'MicrophoneChannel':
        return MicrophoneChannel(redvox_api_1000_pb2.MicrophoneChannel())

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'MicrophoneChannel':
        if not isinstance(sensor_description, str):
            raise errors.MicrophoneChannelError("A string is required")

        self._proto.sensor_description = sensor_description
        return self

    def get_first_sample_ts_us(self) -> float:
        return self._proto.first_sample_ts_us

    def set_first_sample_ts_us(self, first_sample_ts_us: float) -> 'MicrophoneChannel':
        if not common.is_protobuf_numerical_type(first_sample_ts_us):
            raise errors.SummaryStatisticsError("A float or integer is required")

        self._proto.first_sample_ts_us = first_sample_ts_us
        return self

    def get_sample_rate_hz(self) -> float:
        return self._proto.sample_rate_hz

    def set_sample_rate_hz(self, sample_rate_hz: float) -> 'MicrophoneChannel':
        if not common.is_protobuf_numerical_type(sample_rate_hz):
            raise errors.SummaryStatisticsError("A float or integer is required")

        self._proto.sample_rate_hz = sample_rate_hz
        return self

    def get_samples(self) -> np.ndarray:
        return np.array(self._proto.samples)

    def set_samples(self, samples: Union[List[float], np.ndarray], update_summary_statistics: bool = True) -> 'MicrophoneChannel':
        pass

    def append_samples(self, samples: Union[List[float], np.ndarray], update_summary_statistics: bool = True) -> 'MicrophoneChannel':
        pass

    def get_sample_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.sample_statistics)

    def set_sample_statistics(self, sample_statistics: summary_statistics.SummaryStatistics) -> 'MicrophoneChannel':
        self._proto.sample_statistics = sample_statistics._proto
        return self

    def __str__(self):
        return str(self._proto)
