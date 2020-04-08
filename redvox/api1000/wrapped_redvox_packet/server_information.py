import redvox.api1000.wrapped_redvox_packet.common as common
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class ServerInformation(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.ServerInformation):
        super().__init__(proto)

    @staticmethod
    def new() -> 'ServerInformation':
        return ServerInformation(redvox_api_1000_pb2.RedvoxPacket1000.ServerInformation())

    def get_auth_server_url(self) -> str:
        return self._proto.auth_server_url

    def set_auth_server_url(self, auth_server_url: str) -> 'ServerInformation':
        common.check_type(auth_server_url, [str])
        self._proto.auth_server_url = auth_server_url
        return self

    def get_synch_server_url(self) -> str:
        return self._proto.synch_server_url

    def set_synch_server_url(self, synch_server_url: str) -> 'ServerInformation':
        common.check_type(synch_server_url, [str])
        self._proto.synch_server_url = synch_server_url
        return self

    def get_acquisition_server_url(self) -> str:
        return self._proto.acquisition_server_url

    def set_acquisition_server_url(self, acquisition_server_url: str) -> 'ServerInformation':
        common.check_type(acquisition_server_url, [str])
        self._proto.acquisition_server_url = acquisition_server_url
        return self
