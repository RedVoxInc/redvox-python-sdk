import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2
import redvox.api1000.wrapped_redvox_packet.common as common


class AudioChannel(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.AudioChannel):
        super().__init__(proto)
        self._samples: common.Payload = common.Payload(proto.samples)

    @staticmethod
    def new() -> 'AudioChannel':
        proto: redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.AudioChannel \
            = redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.AudioChannel()
        return AudioChannel(proto)

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'AudioChannel':
        common.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_first_sample_timestamp(self) -> float:
        return self._proto.first_sample_timestamp

    def set_first_sample_timestamp(self, first_sample_timestamp: float) -> 'AudioChannel':
        common.check_type(first_sample_timestamp, [float, int])
        self._proto.first_sample_timestamp = first_sample_timestamp
        return self

    def get_sample_rate_hz(self) -> float:
        return self._proto.sample_rate_hz

    def set_sample_rate_hz(self, sample_rate_hz: float) -> 'AudioChannel':
        common.check_type(sample_rate_hz, [int, float])
        self._proto.sample_rate_hz = sample_rate_hz
        return self

    def get_is_scrambled(self) -> bool:
        return self._proto.is_scrambled

    def set_is_scrambled(self, is_scrambled: bool) -> 'AudioChannel':
        common.check_type(is_scrambled, [bool])
        self._proto.is_scrambled = is_scrambled
        return self

    def get_samples(self) -> common.Payload:
        return self._samples


