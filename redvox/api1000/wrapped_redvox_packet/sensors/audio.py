import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.wrapped_redvox_packet.common as common


class Audio(common.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.Sensors.Audio]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.Audio):
        super().__init__(proto)
        self._samples: common.SamplePayload = common.SamplePayload(proto.samples)

    @staticmethod
    def new() -> 'Audio':
        proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.Audio \
            = redvox_api_m_pb2.RedvoxPacketM.Sensors.Audio()
        return Audio(proto)

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'Audio':
        common.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_first_sample_timestamp(self) -> float:
        return self._proto.first_sample_timestamp

    def set_first_sample_timestamp(self, first_sample_timestamp: float) -> 'Audio':
        common.check_type(first_sample_timestamp, [float, int])
        self._proto.first_sample_timestamp = first_sample_timestamp
        return self

    def get_sample_rate(self) -> float:
        return self._proto.sample_rate

    def set_sample_rate(self, sample_rate: float) -> 'Audio':
        common.check_type(sample_rate, [int, float])
        self._proto.sample_rate = sample_rate
        return self

    def get_is_scrambled(self) -> bool:
        return self._proto.is_scrambled

    def set_is_scrambled(self, is_scrambled: bool) -> 'Audio':
        common.check_type(is_scrambled, [bool])
        self._proto.is_scrambled = is_scrambled
        return self

    def get_samples(self) -> common.SamplePayload:
        return self._samples


class CompressedAudio(common.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio):
        super().__init__(proto)
        # TODO

