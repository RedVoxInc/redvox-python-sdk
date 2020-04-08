import redvox.api1000.wrapped_redvox_packet.common as common
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2
import redvox.api1000.wrapped_redvox_packet.sensor_channels.image_channel as image_channel
import redvox.api1000.wrapped_redvox_packet.sensor_channels.location_channel as location_channel
import redvox.api1000.wrapped_redvox_packet.sensor_channels.audio_channel as microphone_channel
import redvox.api1000.wrapped_redvox_packet.sensor_channels.single_channel as single_channel
import redvox.api1000.wrapped_redvox_packet.sensor_channels.xyz_channel as xyz_channel


class SensorChannels(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels):
        super().__init__(proto)
        self._microphone_channel: microphone_channel.AudioChannel = microphone_channel.AudioChannel(proto.audio_channel)
        self._barometer_channel: single_channel.SingleChannel = single_channel.SingleChannel(proto.barometer_channel)
        self._location_channel: location_channel.LocationChannel = location_channel.LocationChannel(proto.location_channel)
        self._accelerometer_channel: xyz_channel.XyzChannel = xyz_channel.XyzChannel(proto.accelerometer_channel)
        self._gyroscope_channel: xyz_channel.XyzChannel = xyz_channel.XyzChannel(proto.gyroscope_channel)
        self._magnetometer_chanel: xyz_channel.XyzChannel = xyz_channel.XyzChannel(proto.magnetometer_channel)
        self._light_channel: single_channel.SingleChannel = single_channel.SingleChannel(proto.light_channel)
        self._infrared_channel: single_channel.SingleChannel = single_channel.SingleChannel(proto.infrared_channel)
        self._image_channel: image_channel.ImageChannel = image_channel.ImageChannel(proto.image_channel)

    @staticmethod
    def new() -> 'SensorChannels':
        return SensorChannels(redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels())

    def get_audio_channel(self) -> microphone_channel.AudioChannel:
        return self._microphone_channel

    def get_barometer_channel(self) -> single_channel.SingleChannel:
        return self._barometer_channel

    def get_location_channel(self) -> location_channel.LocationChannel:
        return self._location_channel

    def get_accelerometer_channel(self) -> xyz_channel.XyzChannel:
        return self._accelerometer_channel

    def get_gyroscope_channel(self) -> xyz_channel.XyzChannel:
        return self._gyroscope_channel

    def get_magnetometer_channel(self) -> xyz_channel.XyzChannel:
        return self._magnetometer_chanel

    def get_light_channel(self) -> single_channel.SingleChannel:
        return self._light_channel

    def get_infrared_channel(self) -> single_channel.SingleChannel:
        return self._infrared_channel

