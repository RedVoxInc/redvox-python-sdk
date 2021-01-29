"""
This module contains classes and functions for interacting with the RedVox Cloud API authentication endpoints.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from dataclasses_json import dataclass_json
import requests

from redvox.cloud.api import post_req
from redvox.cloud.config import RedVoxConfig
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
    claims: Optional["ValidateTokenResp"]

    def is_success(self) -> bool:
        """
        :return: Returns true if the auth response was a success, false otherwise.
        """
        return (
            self.status == 200
            and self.auth_token is not None
            and len(self.auth_token) > 0
        )


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
    claims: Optional[ValidateTokenResp]


def authenticate_user(
    redvox_config: RedVoxConfig,
    authentication_request: AuthReq,
    session: Optional[requests.Session] = None,
    timeout: Optional[float] = None,
) -> AuthResp:
    """
    Attempts to authenticate a RedVox user.
    :param redvox_config: Api configuration.
    :param authentication_request: An instance of an authentication request.
    :param session: An (optional) session for re-using an HTTP client.
    :param timeout: An (optional) timeout.
    :return: An instance of an authentication response.
    """
    # noinspection Mypy
    # pylint: disable=E1101
    handle_resp: Callable[
        [requests.Response], AuthResp
    ] = lambda resp: AuthResp.from_dict(resp.json())
    res: Optional[AuthResp] = post_req(
        redvox_config,
        RoutesV1.AUTH_USER,
        authentication_request,
        handle_resp,
        session,
        timeout,
    )

    return res if res else AuthResp(401, None, None)


def validate_token(
    redvox_config: RedVoxConfig,
    validate_token_req: ValidateTokenReq,
    session: Optional[requests.Session] = None,
    timeout: Optional[float] = None,
) -> Optional[ValidateTokenResp]:
    """
    Attempt to validate the provided auth token.
    :param redvox_config: The Api config.
    :param validate_token_req: A validation token req.
    :param session: An (optional) session for re-using an HTTP client.
    :param timeout: An (optional) timeout.
    :return: A ValidateTokenResp when the token is valid, None otherwise.
    """
    # noinspection Mypy
    # pylint: disable=E1101
    handle_resp: Callable[
        [requests.Response], ValidateTokenResp
    ] = lambda resp: ValidateTokenResp.from_dict(resp.json())
    return post_req(
        redvox_config,
        RoutesV1.VALIDATE_TOKEN,
        validate_token_req,
        handle_resp,
        session,
        timeout,
    )


def refresh_token(
    redvox_config: RedVoxConfig,
    refresh_token_req: RefreshTokenReq,
    session: Optional[requests.Session] = None,
    timeout: Optional[float] = None,
) -> Optional[RefreshTokenResp]:
    """
    Attempt to refresh the given authentication token.
    :param redvox_config: The Api config.
    :param refresh_token_req: The request.
    :param session: An (optional) session for re-using an HTTP client.
    :param timeout: An (optional) timeout.
    :return: An instance of a RefreshTokenResp.
    """
    # noinspection Mypy
    # pylint: disable=E1101
    handle_resp: Callable[
        [requests.Response], RefreshTokenResp
    ] = lambda resp: RefreshTokenResp.from_dict(resp.json())
    return post_req(
        redvox_config,
        RoutesV1.REFRESH_TOKEN,
        refresh_token_req,
        handle_resp,
        session,
        timeout,
    )
