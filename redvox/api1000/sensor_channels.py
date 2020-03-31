import redvox.api1000.common as common
import redvox.api1000.microphone_channel as microphone_channel
import redvox.api1000.single_channel as single_channel
import redvox.api1000.location_channel as location_channel
import redvox.api1000.xyz_channel as xyz_channel
# import redvox.api1000.image_channel as image_channel
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class SensorChannels(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels):
        super().__init__(proto)

    @staticmethod
    def new() -> 'SensorChannels':
        return SensorChannels(redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels())


