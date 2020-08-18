import enum

import redvox.api1000.common.typing
import redvox.api1000.common.common as common

from typing import List

import redvox.api1000.common.generic

from redvox.api1000.common.decorators import wrap_enum
from redvox.api1000.common.generic import ProtoBase, ProtoRepeatedMessage
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM


@wrap_enum(RedvoxPacketM.Sensors.Location.LocationProvider)
class LocationProvider(enum.Enum):
    UNKNOWN: int = 0
    NONE: int = 1
    USER: int = 2
    GPS: int = 3
    NETWORK: int = 4


@wrap_enum(RedvoxPacketM.Sensors.Location.BestLocation.LocationScoreMethod)
class LocationScoreMethod(enum.Enum):
    UNKNOWN_METHOD: int = 0


class BestTimestamp(
    redvox.api1000.common.generic.ProtoBase[RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp]
):
    def __init__(self, proto: RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp):
        super().__init__(proto)

    def get_unit(self) -> common.Unit:
        return common.Unit.from_proto(self._proto.unit)

    def set_default_unit(self) -> 'BestTimestamp':
        return self.set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)

    def set_unit(self, unit: common.Unit) -> 'BestTimestamp':
        redvox.api1000.common.typing.check_type(unit, [common.Unit])
        self._proto.unit = unit.into_proto()
        return self

    def get_mach(self) -> float:
        return self._proto.mach

    def set_mach(self, mach: float) -> 'BestTimestamp':
        redvox.api1000.common.typing.check_type(mach, [int, float])
        self._proto.mach = mach
        return self

    def get_gps(self) -> float:
        return self._proto.gps

    def set_gps(self, gps: float) -> 'BestTimestamp':
        redvox.api1000.common.typing.check_type(gps, [int, float])
        self._proto.gps = gps
        return self


class BestLocation(ProtoBase[RedvoxPacketM.Sensors.Location.BestLocation]):
    def __init__(self, proto: RedvoxPacketM.Sensors.Location.BestLocation):
        super().__init__(proto)
        self._latitude_longitude_timestamp: BestTimestamp = BestTimestamp(proto.latitude_longitude_timestamp)
        self._altitude_timestamp: BestTimestamp = BestTimestamp(proto.altitude_timestamp)
        self._speed_timestamp: BestTimestamp = BestTimestamp(proto.speed_timestamp)
        self._bearing_timestamp: BestTimestamp = BestTimestamp(proto.bearing_timestamp)

    def get_latitude_longitude_timestamp(self) -> BestTimestamp:
        return self._latitude_longitude_timestamp

    def get_altitude_timestamp(self) -> BestTimestamp:
        return self._altitude_timestamp

    def get_speed_timestamp(self) -> BestTimestamp:
        return self._speed_timestamp

    def get_bearing_timestamp(self) -> BestTimestamp:
        return self._bearing_timestamp

    def get_latitude_longitude_unit(self) -> common.Unit:
        return common.Unit.from_proto(self._proto.latitude_longitude_unit)

    def set_latitude_longitude_unit(self, unit: common.Unit) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(unit, [common.Unit])
        self._proto.latitude_longitude_unit = unit.into_proto()
        return self

    def get_altitude_unit(self) -> common.Unit:
        return common.Unit.from_proto(self._proto.altitude_unit)

    def set_altitude_unit(self, unit: common.Unit) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(unit, [common.Unit])
        self._proto.altitude_unit = unit.into_proto()
        return self

    def get_speed_unit(self) -> common.Unit:
        return common.Unit.from_proto(self._proto.speed_unit)

    def set_speed_unit(self, unit: common.Unit) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(unit, [common.Unit])
        self._proto.speed_unit = unit.into_proto()
        return self

    def get_bearing_unit(self) -> common.Unit:
        return common.Unit.from_proto(self._proto.bearing_unit)

    def set_bearing_unit(self, unit: common.Unit) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(unit, [common.Unit])
        self._proto.bearing_unit = unit.into_proto()
        return self

    def get_vertical_accuracy_unit(self) -> common.Unit:
        return common.Unit.from_proto(self._proto.vertical_accuracy_unit)

    def set_vertical_accuracy_unit(self, unit: common.Unit) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(unit, [common.Unit])
        self._proto.vertical_accuracy_unit = unit.into_proto()
        return self

    def get_horizontal_accuracy_unit(self) -> common.Unit:
        return common.Unit.from_proto(self._proto.horizontal_accuracy_unit)

    def set_horizontal_accuracy_unit(self, unit: common.Unit) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(unit, [common.Unit])
        self._proto.horizontal_accuracy_unit = unit.into_proto()
        return self

    def get_speed_accuracy_unit(self) -> common.Unit:
        return common.Unit.from_proto(self._proto.speed_accuracy_unit)

    def set_speed_accuracy_unit(self, unit: common.Unit) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(unit, [common.Unit])
        self._proto.speed_accuracy_unit = unit.into_proto()
        return self

    def get_bearing_accuracy_unit(self) -> common.Unit:
        return common.Unit.from_proto(self._proto.bearing_accuracy_unit)

    def set_bearing_accuracy_unit(self, unit: common.Unit) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(unit, [common.Unit])
        self._proto.bearing_accuracy_unit = unit.into_proto()
        return self

    def get_latitude(self) -> float:
        return self._proto.latitude

    def set_latitude(self, latitude: float) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(latitude, [int, float])
        self._proto.latitude = latitude
        return self

    def get_longitude(self) -> float:
        return self._proto.longitude

    def set_longitude(self, longitude: float) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(longitude, [int, float])
        self._proto.longitude = longitude
        return self

    def get_altitude(self) -> float:
        return self._proto.altitude

    def set_altitude(self, altitude: float) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(altitude, [int, float])
        self._proto.altitude = altitude
        return self

    def get_speed(self) -> float:
        return self._proto.speed

    def set_speed(self, speed: float) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(speed, [int, float])
        self._proto.speed = speed
        return self

    def get_bearing(self) -> float:
        return self._proto.bearing

    def set_bearing(self, bearing: float) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(bearing, [int, float])
        self._proto.bearing = bearing
        return self

    def get_vertical_accuracy(self) -> float:
        return self._proto.vertical_accuracy

    def set_vertical_accuracy(self, vertical_accuracy: float) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(vertical_accuracy, [int, float])
        self._proto.vertical_accuracy = vertical_accuracy
        return self

    def get_horizontal_accuracy(self) -> float:
        return self._proto.horizontal_accuracy

    def set_horizontal_accuracy(self, horizontal_accuracy: float) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(horizontal_accuracy, [int, float])
        self._proto.horizontal_accuracy = horizontal_accuracy
        return self

    def get_speed_accuracy(self) -> float:
        return self._proto.speed_accuracy

    def set_speed_accuracy(self, speed_accuracy: float) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(speed_accuracy, [int, float])
        self._proto.speed_accuracy = speed_accuracy
        return self

    def get_bearing_accuracy(self) -> float:
        return self._proto.bearing_accuracy

    def set_bearing_accuracy(self, bearing_accuracy: float) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(bearing_accuracy, [int, float])
        self._proto.bearing_accuracy = bearing_accuracy
        return self

    def get_score(self) -> float:
        return self._proto.score

    def set_score(self, score: float) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(score, [int, float])
        self._proto.score = score
        return self

    def get_method(self) -> LocationScoreMethod:
        return LocationScoreMethod.from_proto(self._proto.method)

    def set_method(self, method: LocationScoreMethod) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(method, [LocationScoreMethod])
        self._proto.method = method.into_proto()
        return self

    def get_location_provider(self) -> LocationProvider:
        return LocationProvider.from_proto(self._proto.location_provider)

    def set_location_provider(self, location_provider: LocationProvider) -> 'BestLocation':
        redvox.api1000.common.typing.check_type(location_provider, [LocationProvider])
        self._proto.location_provider = location_provider.into_proto()
        return self


class Location(redvox.api1000.common.generic.ProtoBase[RedvoxPacketM.Sensors.Location]):
    def __init__(self, proto: RedvoxPacketM.Sensors.Location):
        super().__init__(proto)
        self._timestamps: common.TimingPayload = common.TimingPayload(proto.timestamps)
        self._timestamps_gps: common.TimingPayload = common.TimingPayload(proto.timestamps_gps)
        self._latitude_samples: common.SamplePayload = common.SamplePayload(proto.latitude_samples)
        self._longitude_samples: common.SamplePayload = common.SamplePayload(proto.longitude_samples)
        self._altitude_samples: common.SamplePayload = common.SamplePayload(proto.altitude_samples)
        self._speed_samples: common.SamplePayload = common.SamplePayload(proto.speed_samples)
        self._bearing_samples: common.SamplePayload = common.SamplePayload(proto.bearing_samples)
        self._horizontal_accuracy_samples: common.SamplePayload = common.SamplePayload(
            proto.horizontal_accuracy_samples)
        self._vertical_accuracy_samples: common.SamplePayload = common.SamplePayload(proto.vertical_accuracy_samples)
        self._speed_accuracy_samples: common.SamplePayload = common.SamplePayload(proto.speed_accuracy_samples)
        self._bearing_accuracy_samples: common.SamplePayload = common.SamplePayload(proto.bearing_accuracy_samples)
        self._last_best_location: BestLocation = BestLocation(proto.last_best_location)
        self._overall_best_location: BestLocation = BestLocation(proto.overall_best_location)
        self._location_providers: ProtoRepeatedMessage = ProtoRepeatedMessage(
            proto,
            proto.location_providers,
            "location_providers",
            LocationProvider.from_proto,
            LocationProvider.into_proto,
        )

    @staticmethod
    def new() -> 'Location':
        return Location(RedvoxPacketM.Sensors.Location())

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'Location':
        redvox.api1000.common.typing.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_timestamps(self) -> common.TimingPayload:
        return self._timestamps

    def get_timestamps_gps(self) -> common.TimingPayload:
        return self._timestamps_gps

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

    def get_last_best_location(self) -> BestLocation:
        return self._last_best_location

    def get_overall_best_location(self) -> BestLocation:
        return self._overall_best_location

    def get_location_permissions_granted(self) -> bool:
        return self._proto.location_permissions_granted

    def set_location_permissions_granted(self, location_permissions_granted: bool) -> 'Location':
        redvox.api1000.common.typing.check_type(location_permissions_granted, [bool])
        self._proto.location_permissions_granted = location_permissions_granted
        return self

    def get_location_services_requested(self) -> bool:
        return self._proto.location_services_requested

    def set_location_services_requested(self, location_services_requested: bool) -> 'Location':
        redvox.api1000.common.typing.check_type(location_services_requested, [bool])
        self._proto.location_services_requested = location_services_requested
        return self

    def get_location_services_enabled(self) -> bool:
        return self._proto.location_services_enabled

    def set_location_services_enabled(self, location_services_enabled: bool) -> 'Location':
        redvox.api1000.common.typing.check_type(location_services_enabled, [bool])
        self._proto.location_services_enabled = location_services_enabled
        return self

    def get_location_providers(self) -> ProtoRepeatedMessage:
        return self._location_providers


def validate_location(loc_sensor: Location) -> List[str]:
    errors_list = common.validate_timing_payload(loc_sensor.get_timestamps())
    if loc_sensor.get_latitude_samples().get_unit() != common.Unit.DECIMAL_DEGREES:
        errors_list.append("Location sensor latitude units are not decimal degrees")
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_latitude_samples(), "Latitude"))

    if loc_sensor.get_longitude_samples().get_unit() != common.Unit.DECIMAL_DEGREES:
        errors_list.append("Location sensor longitude units are not decimal degrees")
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_longitude_samples(), "Longitude"))

    if loc_sensor.get_altitude_samples().get_unit() != common.Unit.METERS:
        errors_list.append("Location sensor altitude units are not meters")
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_altitude_samples(), "Altitude"))

    # todo: any of the below can be turned off as needed
    if loc_sensor.get_speed_samples().get_unit() != common.Unit.METERS_PER_SECOND:
        errors_list.append("Location sensor speed units are not meters per second")
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_speed_samples(), "Speed"))

    if loc_sensor.get_bearing_samples().get_unit() != common.Unit.DECIMAL_DEGREES:
        errors_list.append("Location sensor bearing units are not decimal degrees")
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_bearing_samples(), "Bearing"))

    if loc_sensor.get_horizontal_accuracy_samples().get_unit() != common.Unit.METERS:
        errors_list.append("Location sensor horizontal accuracy units are not meters")
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_horizontal_accuracy_samples(),
                                                      "Horizontal Accuracy"))

    if loc_sensor.get_vertical_accuracy_samples().get_unit() != common.Unit.METERS:
        errors_list.append("Location sensor vertical accuracy units are not meters")
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_vertical_accuracy_samples(),
                                                      "Vertical Accuracy"))

    if loc_sensor.get_speed_accuracy_samples().get_unit() != common.Unit.METERS_PER_SECOND:
        errors_list.append("Location sensor speed accuracy units are not meters per second")
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_speed_accuracy_samples(),
                                                      "Speed Accuracy"))

    if loc_sensor.get_bearing_accuracy_samples().get_unit() != common.Unit.DECIMAL_DEGREES:
        errors_list.append("Location sensor bearing accuracy units are not decimal degrees")
    errors_list.extend(common.validate_sample_payload(loc_sensor.get_bearing_accuracy_samples(),
                                                      "Bearing Accuracy"))

    return errors_list
