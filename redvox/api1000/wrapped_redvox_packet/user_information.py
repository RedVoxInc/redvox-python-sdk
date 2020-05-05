import redvox.api1000.common.typing
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
# import redvox.api1000.common.common as common

# from typing import List

import redvox.api1000.common.generic


class UserInformation(
    redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.UserInformation]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.UserInformation):
        super().__init__(proto)

    @staticmethod
    def new() -> 'UserInformation':
        return UserInformation(redvox_api_m_pb2.RedvoxPacketM.UserInformation())

    def get_auth_email(self) -> str:
        return self._proto.auth_email

    def set_auth_email(self, auth_email: str) -> 'UserInformation':
        redvox.api1000.common.typing.check_type(auth_email, [str])
        self._proto.auth_email = auth_email
        return self

    def get_auth_token(self) -> str:
        return self._proto.auth_token

    def set_auth_token(self, auth_token: str) -> 'UserInformation':
        redvox.api1000.common.typing.check_type(auth_token, [str])
        self._proto.auth_token = auth_token
        return self

    def get_firebase_token(self) -> str:
        return self._proto.firebase_token

    def set_firebase_token(self, firebase_token: str) -> 'UserInformation':
        redvox.api1000.common.typing.check_type(firebase_token, [str])
        self._proto.firebase_token = firebase_token
        return self


# def validate_user_information(user_info: UserInformation) -> List[str]:
#     errors_list = []
#     if user_info.get_firebase_token() == "":
#         errors_list.append("User information firebase token missing")
#     return errors_list
