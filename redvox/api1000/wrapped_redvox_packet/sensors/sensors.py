"""
This module encapsulates available sensor types.
"""

import redvox.api1000.wrapped_redvox_packet.common as common
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.wrapped_redvox_packet.sensors.audio as audio
import redvox.api1000.wrapped_redvox_packet.sensors.image as image
import redvox.api1000.wrapped_redvox_packet.sensors.location as location
import redvox.api1000.wrapped_redvox_packet.sensors.single as single
import redvox.api1000.wrapped_redvox_packet.sensors.xyz as xyz


class Sensors(common.ProtoBase):
    def __init__(self, sensors_proto: redvox_api_m_pb2.RedvoxPacketM.Sensors):
        super().__init__(sensors_proto)
        self._accelerometer: xyz.Xyz = xyz.Xyz(sensors_proto.accelerometer)
        self._ambient_temperature: single.Single = single.Single(sensors_proto.ambient_temperature)
        self._audio: audio.Audio = audio.Audio(sensors_proto.audio)
        self._compressed_audio: audio.CompressedAudio = audio.CompressedAudio(sensors_proto.compressed_audio)
        self._gravity: xyz.Xyz = xyz.Xyz(sensors_proto.gravity)
        self._gyroscope: xyz.Xyz = xyz.Xyz(sensors_proto.gyroscope)
        self._image: image.Image = image.Image(sensors_proto.image)
        self._light: single.Single = single.Single(sensors_proto.light)
        self._linear_acceleration: xyz.Xyz = xyz.Xyz(sensors_proto.linear_acceleration)
        self._location: location.Location = location.Location(sensors_proto.location)
        self._magnetometer: xyz.Xyz = xyz.Xyz(sensors_proto.magnetometer)
        self._orientation: xyz.Xyz = xyz.Xyz(sensors_proto.orientation)
        self._pressure: single.Single = single.Single(sensors_proto.pressure)
        self._proximity: single.Single = single.Single(sensors_proto.proximity)
        self._relative_humidity: single.Single = single.Single(sensors_proto.relative_humidity)

    @staticmethod
    def new() -> 'Sensors':
        return Sensors(redvox_api_m_pb2.RedvoxPacketM.Sensors())

    def get_audio_channel(self) -> audio.Audio:
        return self._audio

    def get_barometer_channel(self) -> single.Single:
        return self._pressure

    def get_location_channel(self) -> location.Location:
        return self._location

    def get_accelerometer_channel(self) -> xyz.Xyz:
        return self._accelerometer

    def get_gyroscope_channel(self) -> xyz.Xyz:
        return self._gyroscope

    def get_magnetometer_channel(self) -> xyz.Xyz:
        return self._magnetometer

    def get_light_channel(self) -> single.Single:
        return self._light

    def get_proximity(self) -> single.Single:
        return self._proximity
