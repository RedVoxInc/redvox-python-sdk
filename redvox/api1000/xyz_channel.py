from typing import Any, Dict, Optional

import numpy as np

import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2
import redvox.api1000.summary_statistics as summary_statistics
import redvox.api1000.common as common


class XyzChannel:
    def __init__(self, proto: redvox_api_1000_pb2.XyzChannel):
        self._proto = proto

    @staticmethod
    def new() -> 'XyzChannel':
        return XyzChannel(redvox_api_1000_pb2.XyzChannel())

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'XyzChannel':
        if not isinstance(sensor_description, str):
            raise errors.XyzChannelError(f"A string is required, but a "
                                            f"{type(sensor_description)}={sensor_description} was provided")

        self._proto.sensor_description = sensor_description
        return self

    def get_mean_sample_rate_hz(self) -> float:
        return self._proto.mean_sample_rate_hz

    def set_mean_sample_rate_hz(self, mean_sample_rate_hz: float) -> 'XyzChannel':
        if not common.is_protobuf_numerical_type(mean_sample_rate_hz):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but a "
                                                f"{type(mean_sample_rate_hz)}={mean_sample_rate_hz} was provided")

        self._proto.mean_sample_rate_hz = mean_sample_rate_hz
        return self

    def get_sample_ts_us(self) -> np.ndarray:
        return np.array(self._proto.sample_ts_us)

    def set_sample_ts_us(self, sample_ts_us: np.ndarray,
                         update_sample_rate_statistics: bool = True,
                         update_mean_sample_rate: bool = True) -> 'XyzChannel':
        if not common.is_protobuf_repeated_numerical_type(sample_ts_us):
            raise errors.XyzChannelError(f"A numpy array of floats or integers is required, but a "
                                            f"{type(sample_ts_us)}={sample_ts_us} was provided")

        self._proto.sample_ts_us[:] = list(sample_ts_us)

        if update_mean_sample_rate:
            self.set_mean_sample_rate_hz(common.mean_sample_rate_hz_from_sample_ts_us(sample_ts_us))

        if update_sample_rate_statistics:
            self.recompute_sample_rate_statistics()

        return self

    def append_sample_ts_us(self, sample_ts_us: np.ndarray,
                            update_summary_statistics: bool = True,
                            update_mean_sample_rate: bool = True) -> 'XyzChannel':
        if not common.is_protobuf_repeated_numerical_type(sample_ts_us):
            raise errors.XyzChannelError(f"A numpy array of floats or integers is required, but a "
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

    def get_x_samples(self) -> np.ndarray:
        return np.array(self._proto.x_samples)

    def set_x_samples(self, x_samples: np.ndarray, update_summary_statistics: bool = True) -> 'XyzChannel':
        if not common.is_protobuf_repeated_numerical_type(x_samples):
            raise errors.XyzChannelError(f"A numpy array of floats or integers is required, but a "
                                            f"{type(x_samples)}={x_samples} was provided")

        self._proto.x_samples[:] = list(x_samples)

        if update_summary_statistics:
            self.recompute_x_sample_statistics()

        return self

    def append_x_samples(self, x_samples: np.ndarray, update_summary_statistics: bool = True) -> 'XyzChannel':
        if not common.is_protobuf_repeated_numerical_type(x_samples):
            raise errors.XyzChannelError(f"A numpy array of floats or integers is required, but a "
                                            f"{type(x_samples)}={x_samples} was provided")

        self._proto.x_samples.extend(list(x_samples))

        if update_summary_statistics:
            self.recompute_x_sample_statistics()

        return self

    def clear_x_samples(self) -> 'XyzChannel':
        self._proto.x_samples[:] = []
        return self

    def get_y_samples(self) -> np.ndarray:
        return np.array(self._proto.y_samples)

    def set_y_samples(self, y_samples: np.ndarray, update_summary_statistics: bool = True) -> 'XyzChannel':
        if not common.is_protobuf_repeated_numerical_type(y_samples):
            raise errors.XyzChannelError(f"A numpy array of floats or integers is required, but a "
                                         f"{type(y_samples)}={y_samples} was provided")

        self._proto.y_samples[:] = list(y_samples)

        if update_summary_statistics:
            self.recompute_y_sample_statistics()

        return self

    def append_y_samples(self, y_samples: np.ndarray, update_summary_statistics: bool = True) -> 'XyzChannel':
        if not common.is_protobuf_repeated_numerical_type(y_samples):
            raise errors.XyzChannelError(f"A numpy array of floats or integers is required, but a "
                                         f"{type(y_samples)}={y_samples} was provided")

        self._proto.y_samples.extend(list(y_samples))

        if update_summary_statistics:
            self.recompute_y_sample_statistics()

        return self

    def clear_y_samples(self) -> 'XyzChannel':
        self._proto.y_samples[:] = []
        return self

    def get_z_samples(self) -> np.ndarray:
        return np.array(self._proto.z_samples)

    def set_z_samples(self, z_samples: np.ndarray, update_summary_statistics: bool = True) -> 'XyzChannel':
        if not common.is_protobuf_repeated_numerical_type(z_samples):
            raise errors.XyzChannelError(f"A numpy array of floats or integers is required, but a "
                                         f"{type(z_samples)}={z_samples} was provided")

        self._proto.z_samples[:] = list(z_samples)

        if update_summary_statistics:
            self.recompute_z_sample_statistics()

        return self

    def append_z_samples(self, z_samples: np.ndarray, update_summary_statistics: bool = True) -> 'XyzChannel':
        if not common.is_protobuf_repeated_numerical_type(z_samples):
            raise errors.XyzChannelError(f"A numpy array of floats or integers is required, but a "
                                         f"{type(z_samples)}={z_samples} was provided")

        self._proto.z_samples.extend(list(z_samples))

        if update_summary_statistics:
            self.recompute_z_sample_statistics()

        return self

    def clear_z_samples(self) -> 'XyzChannel':
        self._proto.z_samples[:] = []
        return self

    def get_x_sample_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.x_sample_statistics)

    def set_x_sample_statistics(self, x_sample_statistics: summary_statistics.SummaryStatistics) -> 'XyzChannel':
        if not isinstance(x_sample_statistics, summary_statistics.SummaryStatistics):
            raise errors.XyzChannelError(f"Expected an instance of SummaryStatistics, but was provided a "
                                            f"{type(x_sample_statistics)}={x_sample_statistics}")

        self._proto.x_sample_statistics.Clear()
        self._proto.x_sample_statistics.CopyFrom(x_sample_statistics._proto)

        return self

    def get_y_sample_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.y_sample_statistics)

    def set_y_sample_statistics(self, y_sample_statistics: summary_statistics.SummaryStatistics) -> 'XyzChannel':
        if not isinstance(y_sample_statistics, summary_statistics.SummaryStatistics):
            raise errors.XyzChannelError(f"Expected an instance of SummaryStatistics, but was provided a "
                                         f"{type(y_sample_statistics)}={y_sample_statistics}")

        self._proto.y_sample_statistics.Clear()
        self._proto.y_sample_statistics.CopyFrom(y_sample_statistics._proto)

        return self

    def get_z_sample_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.z_sample_statistics)

    def set_z_sample_statistics(self, z_sample_statistics: summary_statistics.SummaryStatistics) -> 'XyzChannel':
        if not isinstance(z_sample_statistics, summary_statistics.SummaryStatistics):
            raise errors.XyzChannelError(f"Expected an instance of SummaryStatistics, but was provided a "
                                         f"{type(z_sample_statistics)}={z_sample_statistics}")

        self._proto.z_sample_statistics.Clear()
        self._proto.z_sample_statistics.CopyFrom(z_sample_statistics._proto)

        return self

    def recompute_x_sample_statistics(self) -> 'XyzChannel':
        self.get_x_sample_statistics().update_from_values(self.get_x_samples())
        return self

    def recompute_y_sample_statistics(self) -> 'XyzChannel':
        self.get_y_sample_statistics().update_from_values(self.get_y_samples())
        return self

    def recompute_z_sample_statistics(self) -> 'XyzChannel':
        self.get_z_sample_statistics().update_from_values(self.get_z_samples())
        return self

    def recompute_sample_statistics(self) -> 'XyzChannel':
        return self.recompute_x_sample_statistics().recompute_y_sample_statistics().recompute_z_sample_statistics()

    def get_sample_rate_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.sample_rate_statistics)

    def set_sample_rate_statistics(self, sample_rate_statistics: summary_statistics.SummaryStatistics) -> 'XyzChannel':
        if not isinstance(sample_rate_statistics, summary_statistics.SummaryStatistics):
            raise errors.XyzChannelError(f"Expected an instance of SummaryStatistics, but was provided a "
                                            f"{type(sample_rate_statistics)}={sample_rate_statistics}")

        self._proto.sample_rate_statistics.Clear()
        self._proto.sample_rate_statistics.CopyFrom(sample_rate_statistics._proto)

        return self

    def recompute_sample_rate_statistics(self) -> 'XyzChannel':
        self.get_sample_rate_statistics().update_from_values(self.get_sample_ts_us())
        return self

    def get_metadata(self) -> Dict[str, str]:
        return common.get_metadata(self._proto.metadata)

    def set_metadata(self, metadata: Dict[str, str]) -> 'XyzChannel':
        err_value: Optional[Any] = common.set_metadata(self._proto.metadata, metadata)

        if err_value is not None:
            raise errors.XyzChannelError("All keys and values in metadata must be strings, but "
                                            f"{type(err_value)}={err_value} was supplied")

        return self

    def append_metadata(self, key: str, value: str) -> 'XyzChannel':
        err_value: Optional[Any] = common.append_metadata(self._proto.metadata, key, value)

        if err_value is not None:
            raise errors.XyzChannelError("All keys and values in metadata must be strings, but "
                                            f"{type(err_value)}={err_value} was supplied")

        return self

    def as_json(self) -> str:
        return common.as_json(self._proto)

    def __str__(self):
        return self.as_json()
