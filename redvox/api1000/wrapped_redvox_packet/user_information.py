import redvox.api1000.wrapped_redvox_packet.common as common
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class UserInformation(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.UserInformation):
        super().__init__(proto)

    @staticmethod
    def new() -> 'UserInformation':
        return UserInformation(redvox_api_1000_pb2.RedvoxPacket1000.UserInformation())

    def get_auth_email(self) -> str:
        return self._proto.auth_email

    def set_auth_email(self, auth_email: str) -> 'UserInformation':
        common.check_type(auth_email, [str])

        self._proto.auth_email = auth_email
        return self

    def get_auth_token(self) -> str:
        return self._proto.auth_token

    def set_auth_token(self, auth_token: str) -> 'UserInformation':
        common.check_type(auth_token, [str])

        self._proto.auth_token = auth_token
        return self

    def get_firebase_token(self) -> str:
        return self._proto.firebase_token

    def set_firebase_token(self, firebase_token: str) -> 'UserInformation':
        common.check_type(firebase_token, [str])

        self._proto.firebase_token = firebase_token
        return self
