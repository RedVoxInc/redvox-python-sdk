from enum import Enum

from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM


def wrap_enum(enum: Enum):
    def __wrap_enum(proto_type) -> Enum:
        setattr(enum, "into_proto", lambda self: proto_type.Value(self.name))
        return enum

    return __wrap_enum


# noinspection Mypy,DuplicatedCode
@wrap_enum(RedvoxPacketM.Sensors.Location.LocationProvider)
class LocationProvider(Enum):
    UNKNOWN: int = 0
    NONE: int = 1
    USER: int = 2
    GPS: int = 3
    NETWORK: int = 4

    # @staticmethod
    # def from_proto(proto: RedvoxPacketM.Sensors.Location.LocationProvider) -> 'LocationProvider':
    #     return LocationProvider(proto)
    #
    # def into_proto(self) -> RedvoxPacketM.Sensors.Location.LocationProvider:
    #     return RedvoxPacketM.Sensors.Location.LocationProvider.Value(self.name)


# noinspection PyTypeChecker
def main():
    native: LocationProvider = LocationProvider.USER
    proto: RedvoxPacketM.Sensors.Location.LocationProvider = native.into_proto()

    print(native, native.name, native.value)
    print(proto)

    # proto = RedvoxPacketM.Sensors.Location.LocationProvider.GPS
    # native = LocationProvider.from_proto(proto)
    #
    # print(native, native.name, native.value)
    # print(proto)


if __name__ == "__main__":
    main()
