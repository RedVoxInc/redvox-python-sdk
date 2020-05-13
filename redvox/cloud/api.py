"""
This module contains methods for interacting with the RedVox cloud based API.
"""
from dataclasses import dataclass
from typing import List, Optional

from dataclasses_json import dataclass_json
import requests


@dataclass
class ApiConfig:
    """
    Provides a configuration for the base API URL.
    """
    protocol: str
    host: str
    port: int

    def url(self, end_point: str) -> str:
        """
        Formats the API URL.
        :param end_point: Endpoint to use.
        :return: The formatted API URL.
        """
        return f"{self.protocol}://{self.host}:{self.port}{end_point}"


@dataclass_json
@dataclass
class AuthenticationRequest:
    """
    An authentication request.
    """
    email: str
    password: str


@dataclass_json
@dataclass
class AuthenticationResponse:
    """
    An authentication response.
    """
    status: int
    auth_token: Optional[str]


def authenticate_user(api_config: ApiConfig,
                      authentication_request: AuthenticationRequest) -> AuthenticationResponse:
    """
    Attempts to authenticate a RedVox user.
    :param api_config: Api configuration.
    :param authentication_request: An instance of an authentication request.
    :return: An instance of an authentication response.
    """
    url: str = api_config.url("/api/v1/auth")
    resp: requests.Response = requests.post(url, json=authentication_request.to_dict())

    if resp.status_code == 200:
        return AuthenticationResponse.from_dict(resp.json())
    else:
        return AuthenticationResponse(resp.status_code, None)


@dataclass_json
@dataclass
class TimingRequest:
    """
    Request for timing metadata.
    """
    auth_token: str
    auth_id: str
    start_ts_s: int
    end_ts_s: int
    station_ids: List[str]
    secret_token: Optional[str] = None


@dataclass_json
@dataclass
class TimingMeta:
    """
    Timing metadata extracted from an individual packet.
    """
    station_id: str
    start_ts_os: float
    start_ts_mach: float
    server_ts: float
    mach_time_zero: float
    best_latency: float
    best_offset: float


@dataclass_json
@dataclass
class TimingMetaResponse:
    """
    Response of obtaining timing metadta.
    """
    items: List[TimingMeta]


def get_timing_metadata(api_config: ApiConfig,
                        timing_req: TimingRequest) -> TimingMetaResponse:
    """
    Retrieve timing metadata.
    :param api_config: An instance of the API configuration.
    :param timing_req: An instance of a timing request.
    :return: An instance of a timing response.
    """
    url: str = api_config.url("/api/v1/time")
    resp: requests.Response = requests.post(url, json=timing_req.to_dict())
    if resp.status_code == 200:
        return TimingMetaResponse(resp.json())
    else:
        return TimingMetaResponse(list())


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


def validate_token(api_config: ApiConfig,
                   validate_token_req: ValidateTokenReq) -> Optional[ValidateTokenResp]:
    """
    Attempt to validate the provided auth token.
    :param api_config: The Api config.
    :param validate_token_req: A validation token req.
    :return: A ValidateTokenResp when the token is valid, None otherwise.
    """
    url: str = api_config.url("/api/v1/auth/validate_token")
    resp: requests.Response = requests.post(url, json=validate_token_req.to_dict())
    if resp.status_code == 200:
        return ValidateTokenResp.from_dict(resp.json())
    else:
        return None


@dataclass_json
@dataclass
class ReportDataReq:
    """
    A request for a signed URL to a RedVox report distribution.
    """
    auth_token: str
    report_id: str
    secret_token: Optional[str] = None


@dataclass_json
@dataclass
class ReportDataResp:
    """
    Response for a report signed URL.
    """
    signed_url: str


def get_report_dist_signed_url(api_config: ApiConfig,
                               report_data_req: ReportDataReq) -> Optional[ReportDataResp]:
    """
    Makes an API call to generate a signed URL of a RedVox report.
    :param api_config: An API config.
    :param report_data_req: The request.
    :return: The response.
    """
    url: str = api_config.url("/api/v1/report_data_req")
    resp: requests.Response = requests.post(url, json=report_data_req.to_dict())
    if resp.status_code == 200:
        return ReportDataResp.from_dict(resp.json())
    else:
        return None

