"""
This module contains classes and functions for interacting with the RedVox Cloud API authentication endpoints.
"""

from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json
import requests

from redvox.cloud.api import ApiConfig
from redvox.cloud.routes import RoutesV1


@dataclass_json
@dataclass
class AuthReq:
    """
    An authentication request.
    """
    email: str
    password: str


@dataclass_json
@dataclass
class AuthResp:
    """
    An authentication response.
    """
    status: int
    auth_token: Optional[str]

    def is_success(self) -> bool:
        return self.status == 200 and self.auth_token is not None and len(self.auth_token) > 0


@dataclass_json
@dataclass
class ValidateTokenReq:
    """
    A token validation request.
    """
    auth_token: str


@dataclass_json
@dataclass
class ValidateTokenResp:
    """
    A verified token response.
    """
    aud: str
    exp: str
    iat: str
    iss: str
    nbf: str
    sub: str
    tier: str


@dataclass_json
@dataclass
class RefreshTokenReq:
    """
    A token validation request.
    """
    auth_token: str


@dataclass_json
@dataclass
class RefreshTokenResp:
    """
    A token validation request.
    """
    auth_token: Optional[str]


def authenticate_user(api_config: ApiConfig,
                      authentication_request: AuthReq) -> AuthResp:
    """
    Attempts to authenticate a RedVox user.
    :param api_config: Api configuration.
    :param authentication_request: An instance of an authentication request.
    :return: An instance of an authentication response.
    """
    url: str = api_config.url(RoutesV1.AUTH_USER)
    # noinspection Mypy
    resp: requests.Response = requests.post(url, json=authentication_request.to_dict())

    if resp.status_code == 200:
        # noinspection Mypy
        return AuthResp.from_dict(resp.json())
    else:
        return AuthResp(resp.status_code, None)


def validate_token(api_config: ApiConfig,
                   validate_token_req: ValidateTokenReq) -> Optional[ValidateTokenResp]:
    """
    Attempt to validate the provided auth token.
    :param api_config: The Api config.
    :param validate_token_req: A validation token req.
    :return: A ValidateTokenResp when the token is valid, None otherwise.
    """
    url: str = api_config.url(RoutesV1.VALIDATE_TOKEN)
    # noinspection Mypy
    resp: requests.Response = requests.post(url, json=validate_token_req.to_dict())
    if resp.status_code == 200:
        # noinspection Mypy
        return ValidateTokenResp.from_dict(resp.json())
    else:
        return None


def refresh_token(api_config: ApiConfig,
                  refresh_token_req: RefreshTokenReq) -> Optional[RefreshTokenResp]:
    """
    Attemp to refresh the given authentication token.
    :param api_config: The Api config.
    :param refresh_token_req: The request.
    :return: An instance of a RefreshTokenResp.
    """
    url: str = api_config.url(RoutesV1.REFRESH_TOKEN)
    # noinspection Mypy
    resp: requests.Response = requests.post(url, json=refresh_token_req.to_dict())
    if resp.status_code == 200:
        # noinspection Mypy
        return RefreshTokenResp.from_dict(resp.json())
    else:
        return None
