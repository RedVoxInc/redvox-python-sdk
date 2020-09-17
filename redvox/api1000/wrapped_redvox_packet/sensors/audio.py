"""
This module encapsulates audio sensor metadata and data.
"""

import enum
from datetime import timedelta

import numpy as np
import redvox.api1000.common.typing
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.common.common as common
import redvox.api1000.common.generic
from redvox.api1000.wrapped_redvox_packet.station_information import AudioSamplingRate
from redvox.api1000.common.decorators import wrap_enum

from typing import List


class Audio(redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.Sensors.Audio]):
    """
    This class encapsulates audio metadata and data.
    """
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.Audio):
        super().__init__(proto)
        self._samples: common.SamplePayload = common.SamplePayload(proto.samples)

    @staticmethod
    def new() -> 'Audio':
        """
        :return: A new, empty Audio sensor instance.
        """
        proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.Audio \
            = redvox_api_m_pb2.RedvoxPacketM.Sensors.Audio()
        return Audio(proto)

    def get_sensor_description(self) -> str:
        """
        :return: This sensor's description.
        """
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'Audio':
        """
        Sets this sensor's description.
        :param sensor_description: Description to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_first_sample_timestamp(self) -> float:
        """
        :return: The machine timestamp associated with the first audio sample.
        """
        return self._proto.first_sample_timestamp

    def set_first_sample_timestamp(self, first_sample_timestamp: float) -> 'Audio':
        """
        Sets the machine timestamp that corresponds to the first audio sample.
        :param first_sample_timestamp: Timestamp to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(first_sample_timestamp, [float, int])
        self._proto.first_sample_timestamp = first_sample_timestamp
        return self

    def get_sample_rate(self) -> float:
        """
        :return: The sampling rate in Hz
        """
        return self._proto.sample_rate

    def set_sample_rate(self, sample_rate: float) -> 'Audio':
        """
        Sets the sampling rate.
        :param sample_rate: Sampling rate Hz.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(sample_rate, [int, float])
        self._proto.sample_rate = sample_rate
        return self

    def get_bits_of_precision(self) -> float:
        """
        :return: Returns the bits of precision or dynamic range of the audio samples.
        """
        return self._proto.bits_of_precision

    def set_bits_of_precision(self, bits_of_precision: float) -> 'Audio':
        """
        Set the bits or precision (dynamic range) of the audio samples.
        :param bits_of_precision: Bits of precision
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(bits_of_precision, [int, float])
        self._proto.bits_of_precision = bits_of_precision
        return self

    def get_is_scrambled(self) -> bool:
        """
        :return: If this audio has been scrambled to remove potential voice data.
        """
        return self._proto.is_scrambled

    def set_is_scrambled(self, is_scrambled: bool) -> 'Audio':
        """
        Sets if the audio has been scrambled or not.
        :param is_scrambled: True if scrambled, False otherwise
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(is_scrambled, [bool])
        self._proto.is_scrambled = is_scrambled
        return self

    def get_encoding(self) -> str:
        """
        :return: The audio encoding scheme as defined by the app.
        """
        return self._proto.encoding

    def set_encoding(self, encoding: str) -> 'Audio':
        """
        Sets the audio encoding scheme.
        :param encoding: Encoding to use.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(encoding, [str])
        self._proto.encoding = encoding
        return self

    def get_samples(self) -> common.SamplePayload:
        """
        :return: The sample payload associated with the audio sensor.
        """
        return self._samples

    def set_samples(self, audio_samples: common.SamplePayload) -> 'Audio':
        """
        Sets the SamplePayload associated with the audio sensor.
        :param audio_samples:
        :return:
        """
        self._samples.set_unit(audio_samples.get_unit())
        self._samples.set_values(audio_samples.get_values())
        return self

    def get_num_samples(self) -> int:
        """
        :return: The number of audio samples stored in this packet.
        """
        return self.get_samples().get_values_count()

    def get_duration(self) -> timedelta:
        """
        :return: Duration of this packet represented as a timedelta
        """
        return timedelta(seconds=self.get_duration_s())

    def get_duration_s(self) -> float:
        """
        calculate the duration of the audio data in seconds
        :return: duration of audio data in seconds
        """
        return float(self.get_num_samples()) / self.get_sample_rate()


def validate_audio(audio_sensor: Audio) -> List[str]:
    """
    Validates the audio sensor.
    :param audio_sensor: Audio sensor to validate.
    :return: A list of validation errors.
    """
    # todo: add default audio unit, normalization factor if needed
    errors_list = common.validate_sample_payload(audio_sensor.get_samples(), "Audio")
    if audio_sensor.get_samples().get_values_count() > 0:
        if np.min(audio_sensor.get_samples().get_values()) < -1.0:
            errors_list.append("Audio minimum value of samples cannot be less than -1.0")
        if np.max(audio_sensor.get_samples().get_values()) > 1.0:
            errors_list.append("Audio maximum value of samples cannot be greater than 1.0")
    if audio_sensor.get_first_sample_timestamp() == 0:
        errors_list.append("Audio first sample timestamp is default value")
    if AudioSamplingRate.from_sampling_rate(audio_sensor.get_sample_rate()) is None:
        errors_list.append("Audio sample rate is not a valid value")
    return errors_list


# noinspection Mypy
@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio.AudioCodec)
class AudioCodec(enum.Enum):
    """
    Audio codec used for compressed audio streams
    """
    UNKNOWN: int = 0
    FLAC: int = 1


class CompressedAudio(
        redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio]):
    """
    Encapsulates metadata and data for compressed audio streams.
    """
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio):
        super().__init__(proto)

    @staticmethod
    def new() -> 'CompressedAudio':
        """
        :return: A new, empty CompressedAudio sensor instance
        """
        proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio \
            = redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio()
        return CompressedAudio(proto)

    def get_sensor_description(self) -> str:
        """
        :return: This sensor's description.
        """
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'CompressedAudio':
        """
        Sets this sensor's description.
        :param sensor_description: Description to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_first_sample_timestamp(self) -> float:
        """
        :return: The machine timestamp associated with the first audio sample.
        """
        return self._proto.first_sample_timestamp

    def set_first_sample_timestamp(self, first_sample_timestamp: float) -> 'CompressedAudio':
        """
        Sets the machine timestamp that corresponds to the first audio sample.
        :param first_sample_timestamp: Timestamp to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(first_sample_timestamp, [float, int])
        self._proto.first_sample_timestamp = first_sample_timestamp
        return self

    def get_sample_rate(self) -> float:
        """
        :return: The sampling rate in Hz
        """
        return self._proto.sample_rate

    def set_sample_rate(self, sample_rate: float) -> 'CompressedAudio':
        """
        Sets the sampling rate.
        :param sample_rate: Sampling rate Hz.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(sample_rate, [int, float])
        self._proto.sample_rate = sample_rate
        return self

    def get_is_scrambled(self) -> bool:
        """
        :return: If this audio has been scrambled to remove potential voice data.
        """
        return self._proto.is_scrambled

    def set_is_scrambled(self, is_scrambled: bool) -> 'CompressedAudio':
        """
        Sets if the audio has been scrambled or not.
        :param is_scrambled: True if scrambled, False otherwise
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(is_scrambled, [bool])
        self._proto.is_scrambled = is_scrambled
        return self

    def get_audio_bytes(self) -> bytes:
        """
        :return: The compressed bytes that make up the audio stream
        """
        return self._proto.audio_bytes

    def set_audio_bytes(self, audio_bytes: bytes) -> 'CompressedAudio':
        """
        Set the bytes that make up the compressed audio stream
        :param audio_bytes:
        :return:
        """
        redvox.api1000.common.typing.check_type(audio_bytes, [bytes])
        self._proto.audio_bytes = audio_bytes
        return self

    def get_audio_codec(self) -> AudioCodec:
        """
        :return: The audio codec used to compress the audio
        """
        # noinspection Mypy
        return self._proto.audio_codec

    def set_audio_codec(self, audio_codec: AudioCodec) -> 'CompressedAudio':
        """
        Sets the audio codec used to compress this audio stream
        :param audio_codec: Audio codec used to compress this stream
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(audio_codec, [AudioCodec])
        self.get_proto().audio_codec = \
            redvox_api_m_pb2.RedvoxPacketM.Sensors.CompressedAudio.AudioCodec.Value(audio_codec.name)
        return self


def validate_compress_audio(compress_audio: CompressedAudio) -> List[str]:
    """
    Validates compressed audio.
    :param compress_audio: CompressedAudio to validate.
    :return: A list of validation errors.
    """
    errors_list = []
    if len(compress_audio.get_audio_bytes()) < 1:
        errors_list.append("Compressed Audio sample audio bytes is empty.")
    if compress_audio.get_first_sample_timestamp() == 0:
        errors_list.append("Compressed Audio first sample timestamp is default value")
    if AudioSamplingRate.from_sampling_rate(compress_audio.get_sample_rate()) is None:
        errors_list.append("Compressed Audio sample rate is not a valid value")
    return errors_list
