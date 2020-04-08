import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2
import redvox.api1000.wrapped_redvox_packet.common as common


class ImageChannel(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.ImageChannel):
        super().__init__(proto)

    @staticmethod
    def new() -> 'ImageChannel':
        return ImageChannel(redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.ImageChannel())
