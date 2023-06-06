"""
Session Models
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Callable, Tuple

import requests
from dataclasses_json import dataclass_json

from redvox.cloud.api import post_req
from redvox.cloud.config import RedVoxConfig
from redvox.cloud.routes import RoutesV3


@dataclass_json
@dataclass
class TimeSyncData:
    ts: float
    lat: float
    off: float


@dataclass_json
@dataclass
class FirstLastBufTimeSync:
    fst: List[Tuple[int, TimeSyncData]]
    fst_max_size: int
    lst: List[Tuple[int, TimeSyncData]]
    lst_max_size: int


@dataclass_json
@dataclass
class Timing:
    first_data_ts: float
    last_data_ts: float
    n_ex: int
    mean_lat: float
    mean_off: float
    fst_lst: FirstLastBufTimeSync


@dataclass_json
@dataclass
class WelfordAggregator:
    m2: float
    mean: float
    cnt: int


@dataclass_json
@dataclass
class Stats:
    min: float
    max: float
    welford: WelfordAggregator


@dataclass_json
@dataclass
class Sensor:
    name: str
    description: str
    sample_rate_stats: Stats


@dataclass_json
@dataclass
class Session:
    id: str
    uuid: str
    desc: str
    start_ts: int
    client: str
    client_ver: str
    session_ver: str
    app: str
    api: int
    sub_api: int
    make: str
    model: str
    app_ver: str
    owner: str
    private: bool
    packet_dur: float
    sensors: List[Sensor]
    n_pkts: int
    timing: Timing
    sub: List[str]

    def session_key(self) -> str:
        return f"{self.id}:{self.uuid}:{self.start_ts}"


@dataclass_json
@dataclass
class Location:
    lat: float
    lng: float
    alt: float


@dataclass_json
@dataclass
class FirstLastBufLocation:
    fst: List[Tuple[int, Location]]
    fst_max_size: int
    lst: List[Tuple[int, Location]]
    lst_max_size: int


@dataclass_json
@dataclass
class LocationStat:
    fst_lst: FirstLastBufLocation
    lat: Stats
    lng: Stats
    alt: Stats


@dataclass_json
@dataclass
class DynamicSession:
    n_pkts: int
    location: Dict[str, LocationStat]
    battery: Stats
    temperature: Stats

    session_key: str
    start_ts: int
    end_ts: int
    dur: str
    sub: List[str]


@dataclass_json
@dataclass
class SessionModelsReq:
    auth_token: str
    id_uuids: Optional[List[str]]
    owner: Optional[str]
    start_ts: Optional[int]
    end_ts: Optional[int]
    include_public: bool


@dataclass_json
@dataclass
class SessionModelsResp:
    err: Optional[str]
    sessions: List[Session]


@dataclass_json
@dataclass
class DynamicSessionModelReq:
    auth_token: str
    session_key: str
    start_ts: int
    end_ts: int


@dataclass_json
@dataclass
class DynamicSessionModelResp:
    err: Optional[str]
    dynamic_session: Optional[DynamicSession]


def request_sessions(
    redvox_config: RedVoxConfig,
    req: SessionModelsReq,
    session: Optional[requests.Session] = None,
    timeout: Optional[float] = None,
) -> SessionModelsResp:
    # noinspection Mypy
    handle_resp: Callable[
        [requests.Response], SessionModelsResp
    ] = lambda resp: SessionModelsResp.from_dict(resp.json())
    return post_req(
        redvox_config,
        RoutesV3.SESSION_MODELS,
        req,
        handle_resp,
        session,
        timeout,
    )


def request_dynamic_session(
    redvox_config: RedVoxConfig,
    req: DynamicSessionModelReq,
    session: Optional[requests.Session] = None,
    timeout: Optional[float] = None,
) -> DynamicSessionModelResp:
    # noinspection Mypy
    handle_resp: Callable[
        [requests.Response], DynamicSessionModelResp
    ] = lambda resp: DynamicSessionModelResp.from_dict(resp.json())
    return post_req(
        redvox_config,
        RoutesV3.DYNAMIC_SESSION_MODEL,
        req,
        handle_resp,
        session,
        timeout,
    )
