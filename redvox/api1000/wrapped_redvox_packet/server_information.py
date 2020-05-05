import redvox.api1000.common.common as common
import redvox.api1000.common.typing
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_1000_pb2

# from typing import List

import redvox.api1000.common.generic


class ServerInformation(
    redvox.api1000.common.generic.ProtoBase[redvox_api_1000_pb2.RedvoxPacketM.ServerInformation]):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacketM.ServerInformation):
        super().__init__(proto)

    @staticmethod
    def new() -> 'ServerInformation':
        return ServerInformation(redvox_api_1000_pb2.RedvoxPacketM.ServerInformation())

    def get_auth_server_url(self) -> str:
        return self._proto.auth_server_url

    def set_auth_server_url(self, auth_server_url: str) -> 'ServerInformation':
        redvox.api1000.common.typing.check_type(auth_server_url, [str])
        self._proto.auth_server_url = auth_server_url
        return self

    def get_synch_server_url(self) -> str:
        return self._proto.synch_server_url

    def set_synch_server_url(self, synch_server_url: str) -> 'ServerInformation':
        redvox.api1000.common.typing.check_type(synch_server_url, [str])
        self._proto.synch_server_url = synch_server_url
        return self

    def get_acquisition_server_url(self) -> str:
        return self._proto.acquisition_server_url

    def set_acquisition_server_url(self, acquisition_server_url: str) -> 'ServerInformation':
        redvox.api1000.common.typing.check_type(acquisition_server_url, [str])
        self._proto.acquisition_server_url = acquisition_server_url
        return self


# def validate_server_information(server_info: ServerInformation) -> List[str]:
    # errors_list = []
    # if server_info.get_auth_server_url() == "":
    #     errors_list.append("Server information auth server is missing")
    # if server_info.get_acquisition_server_url() == "":
    #     errors_list.append("Server information acquisition server is missing")
    # return errors_list
