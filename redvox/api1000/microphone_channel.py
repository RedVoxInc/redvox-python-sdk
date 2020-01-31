from typing import Any, Dict, Optional

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
            raise errors.MicrophoneChannelError(f"A string is required, but a "
                                                f"{type(sensor_description)}={sensor_description} was provided")

        self._proto.sensor_description = sensor_description
        return self

    def get_first_sample_ts_us(self) -> float:
        return self._proto.first_sample_ts_us

    def set_first_sample_ts_us(self, first_sample_ts_us: float) -> 'MicrophoneChannel':
        if not common.is_protobuf_numerical_type(first_sample_ts_us):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but a "
                                                f"{type(first_sample_ts_us)}={first_sample_ts_us} was provided")

        self._proto.first_sample_ts_us = first_sample_ts_us
        return self

    def get_sample_rate_hz(self) -> float:
        return self._proto.sample_rate_hz

    def set_sample_rate_hz(self, sample_rate_hz: float) -> 'MicrophoneChannel':
        if not common.is_protobuf_numerical_type(sample_rate_hz):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but a "
                                                f"{type(sample_rate_hz)}={sample_rate_hz} was provided")

        self._proto.sample_rate_hz = sample_rate_hz
        return self

    def get_samples(self) -> np.ndarray:
        return np.array(self._proto.samples)

    def set_samples(self, samples: np.ndarray, update_summary_statistics: bool = True) -> 'MicrophoneChannel':
        if not common.is_protobuf_repeated_numerical_type(samples):
            raise errors.MicrophoneChannelError(f"A numpy array of floats or integers is required, but a "
                                                f"{type(samples)}={samples} was provided")

        self._proto.samples[:] = list(samples)

        if update_summary_statistics:
            self.get_sample_statistics().update_from_values(samples)

        return self

    def append_samples(self, samples: np.ndarray, update_summary_statistics: bool = True) -> 'MicrophoneChannel':
        if not common.is_protobuf_repeated_numerical_type(samples):
            raise errors.MicrophoneChannelError(f"A numpy array of floats or integers is required, but a "
                                                f"{type(samples)}={samples} was provided")

        self._proto.samples.extend(list(samples))

        if update_summary_statistics:
            self.get_sample_statistics().update_from_values(self.get_samples())

        return self

    def clear_samples(self):
        self._proto.samples[:] = []

    def get_sample_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.sample_statistics)

    def set_sample_statistics(self, sample_statistics: summary_statistics.SummaryStatistics) -> 'MicrophoneChannel':
        if not isinstance(sample_statistics, summary_statistics.SummaryStatistics):
            raise errors.MicrophoneChannelError(f"Expected an instance of SummaryStatistics, but was provided a "
                                                f"{type(sample_statistics)}={sample_statistics}")

        self._proto.sample_statistics.Clear()
        self._proto.sample_statistics.CopyFrom(sample_statistics._proto)

        return self

    def recompute_sample_statistics(self) -> 'MicrophoneChannel':
        self.get_sample_statistics().update_from_values(self.get_samples())
        return self

    def get_metadata(self) -> Dict[str, str]:
        return common.get_metadata(self._proto.metadata)

    def set_metadata(self, metadata: Dict[str, str]) -> 'MicrophoneChannel':
        err_value: Optional[Any] = common.set_metadata(self._proto.metadata, metadata)

        if err_value is not None:
            raise errors.MicrophoneChannelError("All keys and values in metadata must be strings, but "
                                                f"{type(err_value)}={err_value} was supplied")

        return self

    def append_metadata(self, key: str, value: str) -> 'MicrophoneChannel':
        err_value: Optional[Any] = common.append_metadata(self._proto.metadata, key, value)

        if err_value is not None:
            raise errors.MicrophoneChannelError("All keys and values in metadata must be strings, but "
                                                f"{type(err_value)}={err_value} was supplied")

        return self

    def __str__(self):
        return str(self._proto)
