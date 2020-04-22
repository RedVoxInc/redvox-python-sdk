import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.wrapped_redvox_packet.common as common
from redvox.api1000.wrapped_redvox_packet.station_information import AudioSamplingRate

from typing import List


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

    def set_samples(self, audio_samples: common.SamplePayload) -> 'Audio':
        self._samples.set_unit(audio_samples.get_unit())
        self._samples.set_values(audio_samples.get_values())
        return self


def validate_audio(audio_sensor: Audio) -> List[str]:
    errors_list = common.validate_sample_payload(audio_sensor.get_samples())
    if audio_sensor.get_first_sample_timestamp() == 0:
        errors_list.append("Audio first sample timestamp is default value")
    # if not audio_sensor.get_proto().HasField("sample_rate"):
    #     errors_list.append("Audio sample rate is missing")
    if AudioSamplingRate.from_sampling_rate(audio_sensor.get_sample_rate()) is None:
        errors_list.append("Audio sample rate is not a valid value")
    return errors_list


class CompressedAudio(common.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio):
        super().__init__(proto)
        # TODO


def validate_compress_audio(compress_audio: CompressedAudio) -> List[str]:
    return []
    # todo: complete when compressed audio is complete
    # errors_list = common.validate_sample_payload(compress_audio.get_samples())
    # if compress_audio.get_first_sample_timestamp() == 0:
    #     errors_list.append("Audio first sample timestamp is default value")
    # if AudioSamplingRate.from_sampling_rate(compress_audio.get_sample_rate()) is None:
    #     errors_list.append("Audio sample rate is not a valid value")
    # check audio codec
