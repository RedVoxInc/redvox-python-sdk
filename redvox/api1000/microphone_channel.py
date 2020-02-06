from typing import Any, Dict, Optional

import numpy as np

import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2
import redvox.api1000.summary_statistics as summary_statistics
import redvox.api1000.common as common


class MicrophoneChannel:
    def __init__(self, proto: redvox_api_1000_pb2.MicrophoneChannel):
        self._proto: redvox_api_1000_pb2.MicrophoneChannel = proto
        self._samples: common.Samples = common.Samples(self._proto.samples, self._proto.sample_statistics)
        self._metadata: common.Metadata = common.Metadata(self._proto.metadata)

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

    def get_samples(self) -> common.Samples:
        return self._samples

    def get_metadata(self) -> common.Metadata:
        return self._metadata

    def as_json(self) -> str:
        return common.as_json(self._proto)

    def __str__(self):
        return self.as_json()
