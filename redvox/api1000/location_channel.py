import enum
from typing import Any, Dict, Optional

import numpy as np

import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2
import redvox.api1000.summary_statistics as summary_statistics
import redvox.api1000.common as common


class LocationProvider(enum.Enum):
    NONE: int = 0
    USER: int = 1
    GPS: int = 2
    NETWORK: int = 3


class LocationChannel:
    def __init__(self, proto: redvox_api_1000_pb2.LocationChannel):
        self._proto = proto

    @staticmethod
    def new() -> 'LocationChannel':
        return LocationChannel(redvox_api_1000_pb2.LocationChannel())

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'LocationChannel':
        if not isinstance(sensor_description, str):
            raise errors.LocationChannelError(f"A string is required, but a "
                                              f"{type(sensor_description)}={sensor_description} was provided")

        self._proto.sensor_description = sensor_description
        return self

    def get_mean_sample_rate_hz(self) -> float:
        return self._proto.mean_sample_rate_hz

    def set_mean_sample_rate_hz(self, mean_sample_rate_hz: float) -> 'LocationChannel':
        if not common.is_protobuf_numerical_type(mean_sample_rate_hz):
            raise errors.SummaryStatisticsError(f"A float or integer is required, but a "
                                                f"{type(mean_sample_rate_hz)}={mean_sample_rate_hz} was provided")

        self._proto.mean_sample_rate_hz = mean_sample_rate_hz
        return self

    def get_sample_ts_us(self) -> np.ndarray:
        return np.array(self._proto.sample_ts_us)

    def set_sample_ts_us(self, sample_ts_us: np.ndarray,
                         update_sample_rate_statistics: bool = True,
                         update_mean_sample_rate: bool = True) -> 'LocationChannel':
        if not common.is_protobuf_repeated_numerical_type(sample_ts_us):
            raise errors.LocationChannelError(f"A numpy array of floats or integers is required, but a "
                                              f"{type(sample_ts_us)}={sample_ts_us} was provided")

        self._proto.sample_ts_us[:] = list(sample_ts_us)

        if update_mean_sample_rate:
            self.set_mean_sample_rate_hz(common.mean_sample_rate_hz_from_sample_ts_us(sample_ts_us))

        if update_sample_rate_statistics:
            self.recompute_sample_rate_statistics()

        return self

    def append_sample_ts_us(self, sample_ts_us: np.ndarray,
                            update_summary_statistics: bool = True,
                            update_mean_sample_rate: bool = True) -> 'LocationChannel':
        if not common.is_protobuf_repeated_numerical_type(sample_ts_us):
            raise errors.LocationChannelError(f"A numpy array of floats or integers is required, but a "
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

    def get_latitude_samples(self) -> np.ndarray:
        return np.array(self._proto.latitude_samples)

    def set_latitude_samples(self, latitude_samples: np.ndarray, update_summary_statistics: bool = True) -> 'LocationChannel':
        if not common.is_protobuf_repeated_numerical_type(latitude_samples):
            raise errors.LocationChannelError(f"A numpy array of floats or integers is required, but a "
                                              f"{type(latitude_samples)}={latitude_samples} was provided")

        self._proto.latitude_samples[:] = list(latitude_samples)

        if update_summary_statistics:
            self.recompute_latitude_sample_statistics()

        return self

    def append_latitude_samples(self, latitude_samples: np.ndarray, update_summary_statistics: bool = True) -> 'LocationChannel':
        if not common.is_protobuf_repeated_numerical_type(latitude_samples):
            raise errors.LocationChannelError(f"A numpy array of floats or integers is required, but a "
                                              f"{type(latitude_samples)}={latitude_samples} was provided")

        self._proto.latitude_samples.extend(list(latitude_samples))

        if update_summary_statistics:
            self.recompute_latitude_sample_statistics()

        return self

    def clear_latitude_samples(self) -> 'LocationChannel':
        self._proto.latitude_samples[:] = []
        return self

    def get_longitude_samples(self) -> np.ndarray:
        return np.array(self._proto.longitude_samples)

    def set_longitude_samples(self, longitude_samples: np.ndarray, update_summary_statistics: bool = True) -> 'LocationChannel':
        if not common.is_protobuf_repeated_numerical_type(longitude_samples):
            raise errors.LocationChannelError(f"A numpy array of floats or integers is required, but a "
                                              f"{type(longitude_samples)}={longitude_samples} was provided")

        self._proto.longitude_samples[:] = list(longitude_samples)

        if update_summary_statistics:
            self.recompute_longitude_sample_statistics()

        return self

    def append_longitude_samples(self, longitude_samples: np.ndarray, update_summary_statistics: bool = True) -> 'LocationChannel':
        if not common.is_protobuf_repeated_numerical_type(longitude_samples):
            raise errors.LocationChannelError(f"A numpy array of floats or integers is required, but a "
                                              f"{type(longitude_samples)}={longitude_samples} was provided")

        self._proto.longitude_samples.extend(list(longitude_samples))

        if update_summary_statistics:
            self.recompute_longitude_sample_statistics()

        return self

    def clear_longitude_samples(self) -> 'LocationChannel':
        self._proto.longitude_samples[:] = []
        return self

    def get_altitude_samples(self) -> np.ndarray:
        return np.array(self._proto.altitude_samples)

    def set_altitude_samples(self, altitude_samples: np.ndarray, update_summary_statistics: bool = True) -> 'LocationChannel':
        if not common.is_protobuf_repeated_numerical_type(altitude_samples):
            raise errors.LocationChannelError(f"A numpy array of floats or integers is required, but a "
                                              f"{type(altitude_samples)}={altitude_samples} was provided")

        self._proto.altitude_samples[:] = list(altitude_samples)

        if update_summary_statistics:
            self.recompute_altitude_sample_statistics()

        return self

    def append_altitude_samples(self, altitude_samples: np.ndarray, update_summary_statistics: bool = True) -> 'LocationChannel':
        if not common.is_protobuf_repeated_numerical_type(altitude_samples):
            raise errors.LocationChannelError(f"A numpy array of floats or integers is required, but a "
                                              f"{type(altitude_samples)}={altitude_samples} was provided")

        self._proto.altitude_samples.extend(list(altitude_samples))

        if update_summary_statistics:
            self.recompute_altitude_sample_statistics()

        return self

    def clear_altitude_samples(self) -> 'LocationChannel':
        self._proto.altitude_samples[:] = []
        return self

    def get_speed_samples(self) -> np.ndarray:
        return np.array(self._proto.speed_samples)

    def set_speed_samples(self, speed_samples: np.ndarray, update_summary_statistics: bool = True) -> 'LocationChannel':
        if not common.is_protobuf_repeated_numerical_type(speed_samples):
            raise errors.LocationChannelError(f"A numpy array of floats or integers is required, but a "
                                              f"{type(speed_samples)}={speed_samples} was provided")

        self._proto.speed_samples[:] = list(speed_samples)

        if update_summary_statistics:
            self.recompute_speed_sample_statistics()

        return self

    def append_speed_samples(self, speed_samples: np.ndarray, update_summary_statistics: bool = True) -> 'LocationChannel':
        if not common.is_protobuf_repeated_numerical_type(speed_samples):
            raise errors.LocationChannelError(f"A numpy array of floats or integers is required, but a "
                                              f"{type(speed_samples)}={speed_samples} was provided")

        self._proto.speed_samples.extend(list(speed_samples))

        if update_summary_statistics:
            self.recompute_speed_sample_statistics()

        return self

    def clear_speed_samples(self) -> 'LocationChannel':
        self._proto.speed_samples[:] = []
        return self

    def get_accuracy_samples(self) -> np.ndarray:
        return np.array(self._proto.accuracy_samples)

    def set_accuracy_samples(self, accuracy_samples: np.ndarray, update_summary_statistics: bool = True) -> 'LocationChannel':
        if not common.is_protobuf_repeated_numerical_type(accuracy_samples):
            raise errors.LocationChannelError(f"A numpy array of floats or integers is required, but a "
                                              f"{type(accuracy_samples)}={accuracy_samples} was provided")

        self._proto.accuracy_samples[:] = list(accuracy_samples)

        if update_summary_statistics:
            self.recompute_accuracy_sample_statistics()

        return self

    def append_accuracy_samples(self, accuracy_samples: np.ndarray, update_summary_statistics: bool = True) -> 'LocationChannel':
        if not common.is_protobuf_repeated_numerical_type(accuracy_samples):
            raise errors.LocationChannelError(f"A numpy array of floats or integers is required, but a "
                                              f"{type(accuracy_samples)}={accuracy_samples} was provided")

        self._proto.accuracy_samples.extend(list(accuracy_samples))

        if update_summary_statistics:
            self.recompute_accuracy_sample_statistics()

        return self

    def clear_accuracy_samples(self) -> 'LocationChannel':
        self._proto.accuracy_samples[:] = []
        return self

    def get_latitude_sample_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.latitude_sample_statistics)

    def set_latitude_sample_statistics(self, latitude_sample_statistics: summary_statistics.SummaryStatistics) -> 'LocationChannel':
        if not isinstance(latitude_sample_statistics, summary_statistics.SummaryStatistics):
            raise errors.LocationChannelError(f"Expected an instance of SummaryStatistics, but was provided a "
                                              f"{type(latitude_sample_statistics)}={latitude_sample_statistics}")

        self._proto.latitude_sample_statistics.Clear()
        self._proto.latitude_sample_statistics.CopyFrom(latitude_sample_statistics._proto)

        return self

    def recompute_latitude_sample_statistics(self) -> 'LocationChannel':
        self.get_latitude_sample_statistics().update_from_values(self.get_latitude_samples())
        return self

    def get_longitude_sample_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.longitude_sample_statistics)

    def set_longitude_sample_statistics(self, longitude_sample_statistics: summary_statistics.SummaryStatistics) -> 'LocationChannel':
        if not isinstance(longitude_sample_statistics, summary_statistics.SummaryStatistics):
            raise errors.LocationChannelError(f"Expected an instance of SummaryStatistics, but was provided a "
                                              f"{type(longitude_sample_statistics)}={longitude_sample_statistics}")

        self._proto.longitude_sample_statistics.Clear()
        self._proto.longitude_sample_statistics.CopyFrom(longitude_sample_statistics._proto)

        return self

    def recompute_longitude_sample_statistics(self) -> 'LocationChannel':
        self.get_longitude_sample_statistics().update_from_values(self.get_longitude_samples())
        return self

    def get_altitude_sample_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.altitude_sample_statistics)

    def set_altitude_sample_statistics(self, altitude_sample_statistics: summary_statistics.SummaryStatistics) -> 'LocationChannel':
        if not isinstance(altitude_sample_statistics, summary_statistics.SummaryStatistics):
            raise errors.LocationChannelError(f"Expected an instance of SummaryStatistics, but was provided a "
                                              f"{type(altitude_sample_statistics)}={altitude_sample_statistics}")

        self._proto.altitude_sample_statistics.Clear()
        self._proto.altitude_sample_statistics.CopyFrom(altitude_sample_statistics._proto)

        return self

    def recompute_altitude_sample_statistics(self) -> 'LocationChannel':
        self.get_altitude_sample_statistics().update_from_values(self.get_altitude_samples())
        return self

    def get_speed_sample_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.speed_sample_statistics)

    def set_speed_sample_statistics(self, speed_sample_statistics: summary_statistics.SummaryStatistics) -> 'LocationChannel':
        if not isinstance(speed_sample_statistics, summary_statistics.SummaryStatistics):
            raise errors.LocationChannelError(f"Expected an instance of SummaryStatistics, but was provided a "
                                              f"{type(speed_sample_statistics)}={speed_sample_statistics}")

        self._proto.speed_sample_statistics.Clear()
        self._proto.speed_sample_statistics.CopyFrom(speed_sample_statistics._proto)

        return self

    def recompute_speed_sample_statistics(self) -> 'LocationChannel':
        self.get_speed_sample_statistics().update_from_values(self.get_speed_samples())
        return self

    def get_accuracy_sample_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.accuracy_sample_statistics)

    def set_accuracy_sample_statistics(self, accuracy_sample_statistics: summary_statistics.SummaryStatistics) -> 'LocationChannel':
        if not isinstance(accuracy_sample_statistics, summary_statistics.SummaryStatistics):
            raise errors.LocationChannelError(f"Expected an instance of SummaryStatistics, but was provided a "
                                              f"{type(accuracy_sample_statistics)}={accuracy_sample_statistics}")

        self._proto.accuracy_sample_statistics.Clear()
        self._proto.accuracy_sample_statistics.CopyFrom(accuracy_sample_statistics._proto)

        return self

    def recompute_accuracy_sample_statistics(self) -> 'LocationChannel':
        self.get_accuracy_sample_statistics().update_from_values(self.get_accuracy_samples())
        return self

    def recompute_sample_statistics(self) -> 'LocationChannel':
        return self.recompute_latitude_sample_statistics()\
            .recompute_longitude_sample_statistics()\
            .recompute_altitude_sample_statistics()\
            .recompute_speed_sample_statistics()\
            .recompute_accuracy_sample_statistics()

    def get_sample_rate_statistics(self) -> summary_statistics.SummaryStatistics:
        return summary_statistics.SummaryStatistics(self._proto.sample_rate_statistics)

    def set_sample_rate_statistics(self,
                                   sample_rate_statistics: summary_statistics.SummaryStatistics) -> 'LocationChannel':
        if not isinstance(sample_rate_statistics, summary_statistics.SummaryStatistics):
            raise errors.LocationChannelError(f"Expected an instance of SummaryStatistics, but was provided a "
                                              f"{type(sample_rate_statistics)}={sample_rate_statistics}")

        self._proto.sample_rate_statistics.Clear()
        self._proto.sample_rate_statistics.CopyFrom(sample_rate_statistics._proto)

        return self

    def recompute_sample_rate_statistics(self) -> 'LocationChannel':
        self.get_sample_rate_statistics().update_from_values(self.get_sample_ts_us())
        return self

    def get_metadata(self) -> Dict[str, str]:
        return common.get_metadata(self._proto.metadata)

    def set_metadata(self, metadata: Dict[str, str]) -> 'LocationChannel':
        err_value: Optional[Any] = common.set_metadata(self._proto.metadata, metadata)

        if err_value is not None:
            raise errors.LocationChannelError("All keys and values in metadata must be strings, but "
                                              f"{type(err_value)}={err_value} was supplied")

        return self

    def append_metadata(self, key: str, value: str) -> 'LocationChannel':
        err_value: Optional[Any] = common.append_metadata(self._proto.metadata, key, value)

        if err_value is not None:
            raise errors.LocationChannelError("All keys and values in metadata must be strings, but "
                                              f"{type(err_value)}={err_value} was supplied")

        return self

    def as_json(self) -> str:
        return common.as_json(self._proto)

    def __str__(self):
        return self.as_json()
