import redvox.api1000.wrapped_redvox_packet.common as common
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class XyzChannel(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.XyzChannel):
        super().__init__(proto)
        self._timestamps: common.Payload = common.Payload(proto.timestamps)
        self._x_samples: common.Payload = common.Payload(proto.x_samples)
        self._y_samples: common.Payload = common.Payload(proto.y_samples)
        self._z_samples: common.Payload = common.Payload(proto.z_samples)

    @staticmethod
    def new() -> 'XyzChannel':
        return XyzChannel(redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.XyzChannel())

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'XyzChannel':
        common.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_timestamps(self) -> common.Payload:
        return self._timestamps

    def get_x_samples(self) -> common.Payload:
        return self._x_samples

    def get_y_samples(self) -> common.Payload:
        return self._y_samples

    def get_z_samples(self) -> common.Payload:
        return self._z_samples


