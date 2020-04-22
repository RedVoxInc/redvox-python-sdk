import enum

import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.wrapped_redvox_packet.common as common

from typing import List


class LocationProvider(enum.Enum):
    NONE: int = 0
    USER: int = 1
    GPS: int = 2
    NETWORK: int = 3


class Location(common.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.Sensors.Location]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.Location):
        super().__init__(proto)
        self._timestamps: common.TimingPayload = common.TimingPayload(proto.timestamps)
        self._latitude_samples: common.SamplePayload = common.SamplePayload(proto.latitude_samples)
        self._longitude_samples: common.SamplePayload = common.SamplePayload(proto.longitude_samples)
        self._altitude_samples: common.SamplePayload = common.SamplePayload(proto.altitude_samples)
        self._speed_samples: common.SamplePayload = common.SamplePayload(proto.speed_samples)
        self._bearing_samples: common.SamplePayload = common.SamplePayload(proto.bearing_samples)
        self._horizontal_accuracy_samples: common.SamplePayload = common.SamplePayload(proto.horizontal_accuracy_samples)
        self._vertical_accuracy_samples: common.SamplePayload = common.SamplePayload(proto.vertical_accuracy_samples)
        self._speed_accuracy_samples: common.SamplePayload = common.SamplePayload(proto.speed_accuracy_samples)
        self._bearing_accuracy_samples: common.SamplePayload = common.SamplePayload(proto.bearing_accuracy_samples)

    @staticmethod
    def new() -> 'Location':
        return Location(redvox_api_m_pb2.RedvoxPacketM.Sensors.Location())

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'Location':
        common.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_timestamps(self) -> common.TimingPayload:
        return self._timestamps

    def get_latitude_samples(self) -> common.SamplePayload:
        return self._latitude_samples

    def get_longitude_samples(self) -> common.SamplePayload:
        return self._longitude_samples

    def get_altitude_samples(self) -> common.SamplePayload:
        return self._altitude_samples

    def get_speed_samples(self) -> common.SamplePayload:
        return self._speed_samples

    def get_bearing_samples(self) -> common.SamplePayload:
        return self._bearing_samples

    def get_horizontal_accuracy_samples(self) -> common.SamplePayload:
        return self._horizontal_accuracy_samples

    def get_vertical_accuracy_samples(self) -> common.SamplePayload:
        return self._vertical_accuracy_samples

    def get_speed_accuracy_samples(self) -> common.SamplePayload:
        return self._speed_accuracy_samples

    def get_bearing_accuracy_samples(self) -> common.SamplePayload:
        return self._bearing_accuracy_samples

    def get_location_permissions_granted(self) -> bool:
        return self._proto.location_permissions_granted

    def set_location_permissions_granted(self, location_permissions_granted: bool) -> 'Location':
        common.check_type(location_permissions_granted, [bool])
        self._proto.location_permissions_granted = location_permissions_granted
        return self

    def get_location_services_requested(self) -> bool:
        return self._proto.location_services_requested

    def set_location_services_requested(self, location_services_requested: bool) -> 'Location':
        common.check_type(location_services_requested, [bool])
        self._proto.location_services_requested = location_services_requested
        return self

    def get_location_services_enabled(self) -> bool:
        return self._proto.location_services_enabled

    def set_location_services_enabled(self, location_services_enabled: bool) -> 'Location':
        common.check_type(location_services_enabled, [bool])
        self._proto.location_services_enabled = location_services_enabled
        return self

    def get_location_provider(self) -> LocationProvider:
        return LocationProvider(self._proto.location_provider)

    def set_location_provider(self, location_provider: LocationProvider) -> 'Location':
        common.check_type(location_provider, [LocationProvider])
        self._proto.location_provider = redvox_api_m_pb2.RedvoxPacketM.Sensors.Location \
            .LocationProvider.Value(location_provider.name)
        return self


def validate_location(loc_sensor: Location) -> List[str]:
    errors_list = common.validate_timing_payload(loc_sensor.get_timestamps())
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_latitude_samples()))
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_longitude_samples()))
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_altitude_samples()))
    # any of the below can be turned off as needed
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_speed_samples()))
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_bearing_samples()))
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_horizontal_accuracy_samples()))
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_vertical_accuracy_samples()))
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_speed_accuracy_samples()))
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_bearing_accuracy_samples()))

    return errors_list
