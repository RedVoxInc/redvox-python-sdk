"""
This module contains methods for interacting with the RedVox cloud based API.
"""
from dataclasses import dataclass
from typing import List, Optional

from dataclasses_json import dataclass_json
import requests


@dataclass
class ApiConfig:
    protocol: str
    host: str
    port: int

    def url(self, end_point: str) -> str:
        return f"{self.protocol}://{self.host}:{self.port}{end_point}"


@dataclass_json
@dataclass
class AuthenticationRequest:
    email: str
    password: str


@dataclass_json
@dataclass
class AuthenticationResponse:
    status: int
    auth_token: Optional[str]


def authenticate_user(api_config: ApiConfig,
                      authentication_request: AuthenticationRequest) -> AuthenticationResponse:
    url: str = api_config.url("/api/v1/auth")
    resp: requests.Response = requests.post(url, json=authentication_request.to_dict())

    if resp.status_code == 200:
        return AuthenticationResponse.from_dict(resp.json())
    else:
        return AuthenticationResponse(resp.status_code, None)


@dataclass_json
@dataclass
class TimingRequest:
    auth_token: str
    auth_id: str
    start_ts_s: int
    end_ts_s: int
    station_ids: List[str]
    secret_token: Optional[str] = None


@dataclass_json
@dataclass
class TimingMeta:
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
    items: List[TimingMeta]


def get_timing_metadata(api_config: ApiConfig,
                        timing_req: TimingRequest) -> TimingMetaResponse:
    url: str = api_config.url("/api/v1/time")
    resp: requests.Response = requests.post(url, json=timing_req.to_dict())
    if resp.status_code == 200:
        return TimingMetaResponse(resp.json())
    else:
        return TimingMetaResponse(list())


@dataclass_json
@dataclass
class ValidateTokenReq:
    auth_token: str


@dataclass_json
@dataclass
class ValidateTokenResp:
    aud: str
    exp: str
    iat: str
    iss: str
    nbf: str
    sub: str
    tier: str


def validate_token(api_config: ApiConfig,
                   validate_token_req: ValidateTokenReq) -> Optional[ValidateTokenResp]:
    url: str = api_config.url("/api/v1/auth/validate_token")
    resp: requests.Response = requests.post(url, json=validate_token_req.to_dict())
    if resp.status_code == 200:
        return ValidateTokenResp.from_dict(resp.json())
    else:
        return None


@dataclass_json
@dataclass
class ReportDataReq:
    auth_token: str
    report_id: str
    secret_token: Optional[str] = None


@dataclass_json
@dataclass
class ReportDataResp:
    signed_url: str


def get_report_dist_signed_url(api_config: ApiConfig,
                               report_data_req: ReportDataReq) -> Optional[ReportDataResp]:
    url: str = api_config.url("/api/v1/report_data_req")
    resp: requests.Response = requests.post(url, json=report_data_req.to_dict())
    if resp.status_code == 200:
        return ReportDataResp.from_dict(resp.json())
    else:
        return None

