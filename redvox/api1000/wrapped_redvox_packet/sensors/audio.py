import enum
import numpy as np
import redvox.api1000.common.typing
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.common.common as common
import redvox.api1000.common.generic
from redvox.api1000.wrapped_redvox_packet.station_information import AudioSamplingRate
from redvox.api1000.common.decorators import wrap_enum

from typing import List


class Audio(redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.Sensors.Audio]):
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
        redvox.api1000.common.typing.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_first_sample_timestamp(self) -> float:
        return self._proto.first_sample_timestamp

    def set_first_sample_timestamp(self, first_sample_timestamp: float) -> 'Audio':
        redvox.api1000.common.typing.check_type(first_sample_timestamp, [float, int])
        self._proto.first_sample_timestamp = first_sample_timestamp
        return self

    def get_sample_rate(self) -> float:
        return self._proto.sample_rate

    def set_sample_rate(self, sample_rate: float) -> 'Audio':
        redvox.api1000.common.typing.check_type(sample_rate, [int, float])
        self._proto.sample_rate = sample_rate
        return self

    def get_bits_of_precision(self) -> float:
        return self._proto.bits_of_precision

    def set_bits_of_precision(self, bits_of_precision: float) -> 'Audio':
        redvox.api1000.common.typing.check_type(bits_of_precision, [int, float])
        self._proto.bits_of_precision = bits_of_precision
        return self

    def get_is_scrambled(self) -> bool:
        return self._proto.is_scrambled

    def set_is_scrambled(self, is_scrambled: bool) -> 'Audio':
        redvox.api1000.common.typing.check_type(is_scrambled, [bool])
        self._proto.is_scrambled = is_scrambled
        return self

    def get_encoding(self) -> str:
        return self._proto.encoding

    def set_encoding(self, encoding: str) -> 'Audio':
        redvox.api1000.common.typing.check_type(encoding, [str])
        self._proto.encoding = encoding
        return self

    def get_samples(self) -> common.SamplePayload:
        return self._samples

    def set_samples(self, audio_samples: common.SamplePayload) -> 'Audio':
        self._samples.set_unit(audio_samples.get_unit())
        self._samples.set_values(audio_samples.get_values())
        return self


def validate_audio(audio_sensor: Audio) -> List[str]:
    # todo: add default audio unit, normalization factor if needed
    errors_list = common.validate_sample_payload(audio_sensor.get_samples(), "Audio")
    if len(audio_sensor.get_samples().get_values()) > 0:
        if np.min(audio_sensor.get_samples().get_values()) < -1.0:
            errors_list.append("Audio minimum value of samples cannot be less than -1.0")
        if np.max(audio_sensor.get_samples().get_values()) > 1.0:
            errors_list.append("Audio maximum value of samples cannot be greater than 1.0")
    if audio_sensor.get_first_sample_timestamp() == 0:
        errors_list.append("Audio first sample timestamp is default value")
    if AudioSamplingRate.from_sampling_rate(audio_sensor.get_sample_rate()) is None:
        errors_list.append("Audio sample rate is not a valid value")
    return errors_list


@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio.AudioCodec)
class AudioCodec(enum.Enum):
    UNKNOWN: int = 0
    FLAC: int = 1


class CompressedAudio(
    redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio):
        super().__init__(proto)

    @staticmethod
    def new() -> 'CompressedAudio':
        proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio \
            = redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio()
        return CompressedAudio(proto)

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'CompressedAudio':
        redvox.api1000.common.typing.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_first_sample_timestamp(self) -> float:
        return self._proto.first_sample_timestamp

    def set_first_sample_timestamp(self, first_sample_timestamp: float) -> 'CompressedAudio':
        redvox.api1000.common.typing.check_type(first_sample_timestamp, [float, int])
        self._proto.first_sample_timestamp = first_sample_timestamp
        return self

    def get_sample_rate(self) -> float:
        return self._proto.sample_rate

    def set_sample_rate(self, sample_rate: float) -> 'CompressedAudio':
        redvox.api1000.common.typing.check_type(sample_rate, [int, float])
        self._proto.sample_rate = sample_rate
        return self

    def get_is_scrambled(self) -> bool:
        return self._proto.is_scrambled

    def set_is_scrambled(self, is_scrambled: bool) -> 'CompressedAudio':
        redvox.api1000.common.typing.check_type(is_scrambled, [bool])
        self._proto.is_scrambled = is_scrambled
        return self

    def get_audio_bytes(self) -> bytes:
        return self._proto.audio_bytes

    def set_audio_bytes(self, audio_bytes: bytes) -> 'CompressedAudio':
        redvox.api1000.common.typing.check_type(audio_bytes, [bytes])
        self._proto.audio_bytes = audio_bytes
        return self

    def get_audio_codec(self) -> AudioCodec:
        return self._proto.audio_codec

    def set_audio_codec(self, audio_codec: AudioCodec) -> 'CompressedAudio':
        redvox.api1000.common.typing.check_type(audio_codec, [AudioCodec])
        self.get_proto().audio_codec = \
            redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio.AudioCodec.Value(audio_codec.name)
        return self


def validate_compress_audio(compress_audio: CompressedAudio) -> List[str]:
    errors_list = []
    if len(compress_audio.get_audio_bytes()) < 1:
        errors_list.append("Compressed Audio sample audio bytes is empty.")
    if compress_audio.get_first_sample_timestamp() == 0:
        errors_list.append("Compressed Audio first sample timestamp is default value")
    if AudioSamplingRate.from_sampling_rate(compress_audio.get_sample_rate()) is None:
        errors_list.append("Compressed Audio sample rate is not a valid value")
    return errors_list
