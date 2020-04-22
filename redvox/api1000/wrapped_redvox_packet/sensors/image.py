import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.wrapped_redvox_packet.common as common

from typing import List


class Image(common.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.Sensors.Image]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.Image):
        super().__init__(proto)

    @staticmethod
    def new() -> 'Image':
        return Image(redvox_api_m_pb2.RedvoxPacketM.Sensors.Image())


# todo: finish when image sensor is finished
def validate_image(image_sensor: Image) -> List[str]:
    errors_list = []
    return errors_list
