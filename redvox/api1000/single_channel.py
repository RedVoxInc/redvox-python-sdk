from typing import Any, Dict, Optional

import numpy as np

import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2
import redvox.api1000.summary_statistics as summary_statistics
import redvox.api1000.common as common


class SingleChannel:
    def __init__(self, proto: redvox_api_1000_pb2.SingleChannel):
        self._proto = proto

    @staticmethod
    def new() -> 'SingleChannel':
        return SingleChannel(redvox_api_1000_pb2.SingleChannel())

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'SingleChannel':
        if not isinstance(sensor_description, str):
            raise errors.SingleChannelError(f"A string is required, but a "
                                            f"{type(sensor_description)}={sensor_description} was provided")

        self._proto.sensor_description = sensor_description
        return self

    def get_mean_sample_rate_hz(self) -> float:
        return self._proto.mean_sample_rate_hz

    def set_mean_sample_rate_hz(self, mean_sample_rate_hz: float) -> 'SingleChannel':
        if not common.is_protobuf_numerical_type(mean_sample_rate_hz):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but a "
                                                f"{type(mean_sample_rate_hz)}={mean_sample_rate_hz} was provided")

        self._proto.mean_sample_rate_hz = mean_sample_rate_hz
        return self

    def get_sample_ts_us(self) -> np.ndarray:
        return np.array(self._proto.sample_ts_us)

    def set_sample_ts_us(self, sample_ts_us: np.ndarray,
                         update_sample_rate_statistics: bool = True,
                         update_mean_sample_rate: bool = True) -> 'SingleChannel':
        if not common.is_protobuf_repeated_numerical_type(sample_ts_us):
            raise errors.SingleChannelError(f"A numpy array of floats or integers is required, but a "
                                            f"{type(sample_ts_us)}={sample_ts_us} was provided")

        self._proto.sample_ts_us[:] = list(sample_ts_us)

        if update_mean_sample_rate:
            self.set_mean_sample_rate_hz(common.mean_sample_rate_hz_from_sample_ts_us(sample_ts_us))

        if update_sample_rate_statistics:
            self.recompute_sample_rate_statistics()

        return self

    def append_sample_ts_us(self, sample_ts_us: np.ndarray,
                            update_summary_statistics: bool = True,
                            update_mean_sample_rate: bool = True) -> 'SingleChannel':
        if not common.is_protobuf_repeated_numerical_type(sample_ts_us):
            raise errors.SingleChannelError(f"A numpy array of floats or integers is required, but a "
                                            f"{type(sample_ts_us)}={sample_ts_us} was provided")

        self._proto.sample_ts_us.extend(list(sample_ts_us))

        if update_summary_statistics:
            self.recompute_sample_rate_statistics()

        if update_mean_sample_rate:
            self.set_mean_sample_rate_hz(common.mean_sample_rate_hz_from_sample_ts_us(self.get_sample_ts_us()))

        return self

    def clear_sample_ts_us(self):
        self._proto.sample_ts_us[:] = []
        return self

    def get_samples(self) -> np.ndarray:
        return np.array(self._proto.samples)

    def set_samples(self, samples: np.ndarray, update_summary_statistics: bool = True) -> 'SingleChannel':
        if not common.is_protobuf_repeated_numerical_type(samples):
            raise errors.SingleChannelError(f"A numpy array of floats or integers is required, but a "
                                            f"{type(samples)}={samples} was provided")

        self._proto.samples[:] = list(samples)

        if update_summary_statistics:
            self.recompute_sample_statistics()

        return self

    def append_samples(self, samples: np.ndarray, update_summary_statistics: bool = True) -> 'SingleChannel':
        if not common.is_protobuf_repeated_numerical_type(samples):
            raise errors.SingleChannelError(f"A numpy array of floats or integers is required, but a "
                                            f"{type(samples)}={samples} was provided")

        self._proto.samples.extend(list(samples))

        if update_summary_statistics:
            self.recompute_sample_statistics()

        return self

    def clear_samples(self) -> 'SingleChannel':
        self._proto.samples[:] = []
        return self

    def get_sample_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.sample_statistics)

    def set_sample_statistics(self, sample_statistics: summary_statistics.SummaryStatistics) -> 'SingleChannel':
        if not isinstance(sample_statistics, summary_statistics.SummaryStatistics):
            raise errors.SingleChannelError(f"Expected an instance of SummaryStatistics, but was provided a "
                                            f"{type(sample_statistics)}={sample_statistics}")

        self._proto.sample_statistics.Clear()
        self._proto.sample_statistics.CopyFrom(sample_statistics._proto)

        return self

    def recompute_sample_statistics(self) -> 'SingleChannel':
        self.get_sample_statistics().update_from_values(self.get_samples())
        return self

    def get_sample_rate_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.sample_rate_statistics)

    def set_sample_rate_statistics(self, sample_rate_statistics: summary_statistics.SummaryStatistics) -> 'SingleChannel':
        if not isinstance(sample_rate_statistics, summary_statistics.SummaryStatistics):
            raise errors.SingleChannelError(f"Expected an instance of SummaryStatistics, but was provided a "
                                            f"{type(sample_rate_statistics)}={sample_rate_statistics}")

        self._proto.sample_rate_statistics.Clear()
        self._proto.sample_rate_statistics.CopyFrom(sample_rate_statistics._proto)

        return self

    def recompute_sample_rate_statistics(self) -> 'SingleChannel':
        self.get_sample_rate_statistics().update_from_values(self.get_sample_ts_us())
        return self

    def get_metadata(self) -> Dict[str, str]:
        return common.get_metadata(self._proto.metadata)

    def set_metadata(self, metadata: Dict[str, str]) -> 'SingleChannel':
        err_value: Optional[Any] = common.set_metadata(self._proto.metadata, metadata)

        if err_value is not None:
            raise errors.SingleChannelError("All keys and values in metadata must be strings, but "
                                            f"{type(err_value)}={err_value} was supplied")

        return self

    def append_metadata(self, key: str, value: str) -> 'SingleChannel':
        err_value: Optional[Any] = common.append_metadata(self._proto.metadata, key, value)

        if err_value is not None:
            raise errors.SingleChannelError("All keys and values in metadata must be strings, but "
                                            f"{type(err_value)}={err_value} was supplied")

        return self

    def as_json(self) -> str:
        return common.as_json(self._proto)

    def __str__(self):
        return self.as_json()
