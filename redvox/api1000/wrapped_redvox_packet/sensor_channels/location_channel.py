import enum

import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2
import redvox.api1000.wrapped_redvox_packet.common as common


class LocationProvider(enum.Enum):
    NONE: int = 0
    USER: int = 1
    GPS: int = 2
    NETWORK: int = 3


class LocationChannel(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.LocationChannel):
        super().__init__(proto)
        self._timestamps: common.Payload = common.Payload(proto.timestamps)
        self._latitude_samples: common.Payload = common.Payload(proto.latitude_samples)
        self._longitude_samples: common.Payload = common.Payload(proto.longitude_samples)
        self._altitude_samples: common.Payload = common.Payload(proto.altitude_samples)
        self._speed_samples: common.Payload = common.Payload(proto.speed_samples)
        self._bearing_samples: common.Payload = common.Payload(proto.bearing_samples)
        self._horizontal_accuracy_samples: common.Payload = common.Payload(proto.horizontal_accuracy_samples)
        self._vertical_accuracy_samples: common.Payload = common.Payload(proto.vertical_accuracy_samples)
        self._speed_accuracy_samples: common.Payload = common.Payload(proto.speed_accuracy_samples)
        self._bearing_accuracy_samples: common.Payload = common.Payload(proto.bearing_accuracy_samples)

    @staticmethod
    def new() -> 'LocationChannel':
        return LocationChannel(redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.LocationChannel())

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'LocationChannel':
        common.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_timestamps(self) -> common.Payload:
        return self._timestamps

    def get_latitude_samples(self) -> common.Payload:
        return self._latitude_samples

    def get_longitude_samples(self) -> common.Payload:
        return self._longitude_samples

    def get_altitude_samples(self) -> common.Payload:
        return self._altitude_samples

    def get_speed_samples(self) -> common.Payload:
        return self._speed_samples

    def get_bearing_samples(self) -> common.Payload:
        return self._bearing_samples

    def get_horizontal_accuracy_samples(self) -> common.Payload:
        return self._horizontal_accuracy_samples

    def get_vertical_accuracy_samples(self) -> common.Payload:
        return self._vertical_accuracy_samples

    def get_speed_accuracy_samples(self) -> common.Payload:
        return self._speed_accuracy_samples

    def get_bearing_accuracy_samples(self) -> common.Payload:
        return self._bearing_accuracy_samples

    def get_location_permissions_granted(self) -> bool:
        return self._proto.location_permissions_granted

    def set_location_permissions_granted(self, location_permissions_granted: bool) -> 'LocationChannel':
        common.check_type(location_permissions_granted, [bool])
        self._proto.location_permissions_granted = location_permissions_granted
        return self

    def get_location_services_requested(self) -> bool:
        return self._proto.location_services_requested

    def set_location_services_requested(self, location_services_requested: bool) -> 'LocationChannel':
        common.check_type(location_services_requested, [bool])
        self._proto.location_services_requested = location_services_requested
        return self

    def get_location_services_enabled(self) -> bool:
        return self._proto.location_services_enabled

    def set_location_services_enabled(self, location_services_enabled: bool) -> 'LocationChannel':
        common.check_type(location_services_enabled, [bool])
        self._proto.location_services_enabled = location_services_enabled
        return self

    def get_location_provider(self) -> LocationProvider:
        return LocationProvider(self._proto.location_provider)

    def set_location_provider(self, location_provider: LocationProvider) -> 'LocationChannel':
        common.check_type(location_provider, [LocationProvider])
        self._proto.location_provider = redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.LocationChannel \
            .LocationProvider.Value(location_provider.name)
        return self
