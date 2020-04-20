import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.wrapped_redvox_packet.common as common


class Image(common.ProtoBase):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.Image):
        super().__init__(proto)

    @staticmethod
    def new() -> 'Image':
        return Image(redvox_api_m_pb2.RedvoxPacketM.Sensors.Image())
