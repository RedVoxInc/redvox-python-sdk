import redvox.api1000.wrapped_redvox_packet.common as common
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class SingleChannel(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.SingleChannel):
        super().__init__(proto)
        self._timestamps: common.Payload = common.Payload(proto.timestamps)
        self._samples: common.Payload = common.Payload(proto.samples)

    @staticmethod
    def new() -> 'SingleChannel':
        return SingleChannel(redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.SingleChannel())

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'SingleChannel':
        common.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_timestamps(self) -> common.Payload:
        return self._timestamps

    def get_samples(self) -> common.Payload:
        return self._samples
