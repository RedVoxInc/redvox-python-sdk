import redvox.api1000.common as common
import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class UserInformation(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.UserInformation):
        super().__init__(proto)

        # User information
    def get_auth_email(self) -> str:
        return self._proto.auth_email

    def set_auth_email(self, auth_email: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(auth_email, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a {type(auth_email)}={auth_email} "
                                                         f"was provided")

        self._proto.auth_email = auth_email
        return self

    def get_auth_token(self) -> str:
        return self._proto.auth_token

    def set_auth_token(self, auth_token: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(auth_token, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a {type(auth_token)}={auth_token} "
                                                         f"was provided")

        self._proto.auth_token = auth_token
        return self

    def get_firebase_token(self) -> str:
        return self._proto.firebase_token

    def set_firebase_token(self, firebase_token: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(firebase_token, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a "
                                                         f"{type(firebase_token)}={firebase_token} was provided")

        self._proto.firebase_token = firebase_token
        return self
