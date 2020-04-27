import redvox.api1000.common.typing
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.common.common as common
import redvox.api1000.common.generic


class PacketInformation(
    redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.PacketInformation]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.PacketInformation):
        super().__init__(proto)

    @staticmethod
    def new() -> 'PacketInformation':
        return PacketInformation(redvox_api_m_pb2.RedvoxPacketM.PacketInformation())

    def get_is_backfilled(self) -> bool:
        return self._proto.is_backfilled

    def set_is_backfilled(self, is_backfilled: bool) -> 'PacketInformation':
        redvox.api1000.common.typing.check_type(is_backfilled, [bool])
        self._proto.is_backfilled = is_backfilled
        return self

    def get_is_private(self) -> bool:
        return self._proto.is_private

    def set_is_private(self, is_private: bool) -> 'PacketInformation':
        redvox.api1000.common.typing.check_type(is_private, [bool])
        self._proto.is_private = is_private
        return self
