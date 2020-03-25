import enum

import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2
import redvox.api1000.common as common


class LocationProvider(enum.Enum):
    NONE: int = 0
    USER: int = 1
    GPS: int = 2
    NETWORK: int = 3


class LocationChannel(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.LocationChannel):
        super().__init__(proto)
        self._sample_ts_us: common.Samples = common.Samples(self._proto.sample_ts_us, self._proto.sample_ts_statistics)
        self._latitude_samples: common.Samples = common.Samples(self._proto.latitude_samples, self._proto.latitude_sample_statistics)
        self._longitude_samples: common.Samples = common.Samples(self._proto.longitude_samples, self._proto.longitude_sample_statistics)
        self._altitude_samples: common.Samples = common.Samples(self._proto.altitude_samples, self._proto.accuracy_sample_statistics)
        self._speed_samples: common.Samples = common.Samples(self._proto.speed_samples, self._proto.speed_sample_statistics)
        self._accuracy_samples: common.Samples = common.Samples(self._proto.accuracy_Samples, self._proto.accuracy_sample_statistics)

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

    def get_location_permissions_granted(self) -> bool:
        return self._proto.location_permissions_granted

    def set_location_permissions_granted(self, location_permissions_granted: bool) -> 'LocationChannel':
        if not isinstance(location_permissions_granted, bool):
            raise errors.LocationChannelError(f"A bool is required, but a "
                                              f"{type(location_permissions_granted)}={location_permissions_granted} "
                                              f"was provided")

        self._proto.location_permissions_granted = location_permissions_granted
        return self

    def get_location_services_requested(self) -> bool:
        return self._proto.location_services_requested

    def set_location_services_requested(self, location_services_requested: bool) -> 'LocationChannel':
        if not isinstance(location_services_requested, bool):
            raise errors.LocationChannelError(f"A bool is required, but a "
                                              f"{type(location_services_requested)}={location_services_requested} "
                                              f"was provided")

        self._proto.location_services_requested = location_services_requested
        return self

    def get_location_services_enabled(self) -> bool:
        return self._proto.location_services_enabled

    def set_location_services_enabled(self, location_services_enabled: bool) -> 'LocationChannel':
        if not isinstance(location_services_enabled, bool):
            raise errors.LocationChannelError(f"A bool is required, but a "
                                              f"{type(location_services_enabled)}={location_services_enabled} "
                                              f"was provided")

        self._proto.location_services_enabled = location_services_enabled
        return self

    def get_location_provider(self) -> LocationProvider:
        return LocationProvider(self._proto.location_provider)

    def set_location_provider(self, location_provider: LocationProvider) -> 'LocationChannel':
        if not isinstance(location_provider, LocationProvider):
            raise errors.LocationChannelError(f"A LocationProvider is required, but a "
                                              f"{type(location_provider)}={location_provider} "
                                              f"was provided")

        self._proto.location_provider = redvox_api_1000_pb2.LocationChannel.LocationProvider.Value(location_provider.name)
        return self

    def get_sample_ts_us(self) -> common.Samples:
        return self._sample_ts_us

    def get_mean_sample_rate_hz(self) -> float:
        return common.mean_sample_rate_hz_from_sample_ts_us(self.get_sample_ts_us().get_samples())

    def get_latitude_samples(self) -> common.Samples:
        return self._latitude_samples

    def get_longitude_samples(self) -> common.Samples:
        return self._longitude_samples

    def get_altitude_samples(self) -> common.Samples:
        return self._altitude_samples

    def get_speed_samples(self) -> common.Samples:
        return self._speed_samples

    def get_accuracy_samples(self) -> common.Samples:
        return self._accuracy_samples

    
    


