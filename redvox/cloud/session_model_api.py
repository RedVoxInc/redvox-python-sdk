"""
Session Models and API calls.

Sessions represent a summary of a single station from when it starts recording to when it stops recording.

Sessions are further subdivided into dynamic sessions. A single session contains keys to daily dynamic sessions.
Daily dynamic sessions contain keys to hourly dynamic sessions.
Hourly dynamic sessions contain keys to individual packets.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Callable, Tuple, TYPE_CHECKING

import requests
from dataclasses_json import dataclass_json

from redvox.api1000.wrapped_redvox_packet.station_information import StationInformation
from redvox.api1000.wrapped_redvox_packet.timing_information import TimingInformation
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.cloud.api import post_req
from redvox.cloud.config import RedVoxConfig
from redvox.cloud.routes import RoutesV3
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc as us2dt
from redvox.common.errors import RedVoxError

if TYPE_CHECKING:
    from redvox.cloud.client import CloudClient


@dataclass_json
@dataclass
class TimeSyncData:
    """
    Summarized time synchronization data.
    """

    ts: float
    lat: float
    off: float


@dataclass_json
@dataclass
class FirstLastBufTimeSync:
    """
    A bounded buffer that stores the first and last N samples of time synchronization data.
    """

    fst: List[Tuple[int, TimeSyncData]]
    fst_max_size: int
    lst: List[Tuple[int, TimeSyncData]]
    lst_max_size: int


@dataclass_json
@dataclass
class Timing:
    """
    High-level timing information.
    """

    first_data_ts: float
    last_data_ts: float
    n_ex: int
    mean_lat: float
    mean_off: float
    fst_lst: FirstLastBufTimeSync

    def first_data_dt(self) -> datetime:
        """
        :return: The datatime that represents the first datum.
        """
        return us2dt(self.first_data_ts)

    def last_data_dt(self) -> datetime:
        """
        :return: The datatime that represents the last datum.
        """
        return us2dt(self.last_data_ts)


@dataclass_json
@dataclass
class WelfordAggregator:
    """
    Fields required for computing the online Welford algorithm.
    See: https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Welford's_online_algorithm
    """

    m2: float
    mean: float
    cnt: int

    def finalize(self) -> Tuple[float, float, float]:
        """
        Computes the running variance.
        :return: A tuple containing the mean, variance, and sample variance.
        """
        if self.cnt < 2:
            raise RedVoxError("Not enough values to compute statistics from")
        variance: float = self.m2 / float(self.cnt)
        sample_variance: float = self.m2 / float(self.cnt - 1)
        return self.mean, variance, sample_variance


@dataclass_json
@dataclass
class Stats:
    """
    Contains the minimum and maximum values of a collection as well as the statistics provided by Welford's online
    algorithm.
    """

    min: float
    max: float
    welford: WelfordAggregator


@dataclass_json
@dataclass
class Sensor:
    """
    Describes a station's sensor.
    """

    name: str
    description: str
    sample_rate_stats: Stats


@dataclass_json
@dataclass
class Session:
    """
    Describes a single station's recording session.
    """

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
        """
        :return: The key associated with this session.
        """
        return f"{self.id}:{self.uuid}:{self.start_ts}"

    def query_dynamic_session(
        self, client: "CloudClient", sub: str
    ) -> "DynamicSessionModelResp":
        """
        Queries a dynamic session that is associated with this session.
        :param client: An instance of the cloud client.
        :param sub: The dynamic session key/
        :return: A DynamicSessionModelResp.
        """
        ts_parts: List[int] = list(map(int, sub.split(":")))
        return client.request_dynamic_session_model(
            self.session_key(), ts_parts[0], ts_parts[1]
        )


@dataclass_json
@dataclass
class Location:
    """
    Described a single location.
    """

    lat: float
    lng: float
    alt: float


@dataclass_json
@dataclass
class FirstLastBufLocation:
    """
    A bounded buffer that stores the first and last location points.
    """

    fst: List[Tuple[int, Location]]
    fst_max_size: int
    lst: List[Tuple[int, Location]]
    lst_max_size: int


@dataclass_json
@dataclass
class LocationStat:
    """
    Location statistics.
    """

    fst_lst: FirstLastBufLocation
    lat: Stats
    lng: Stats
    alt: Stats


@dataclass_json
@dataclass
class DynamicSession:
    """
    A dynamic session belongs to a parent session, but instead of representing an entire recording, dynamic sessions
    represent a chunk of time. Either daily or hourly dynamic sessions are supported.
    """

    n_pkts: int
    location: Dict[str, LocationStat]
    battery: Stats
    temperature: Stats

    session_key: str
    start_ts: int
    end_ts: int
    dur: str
    sub: List[str]

    def query_dynamic_session(
        self, client: "CloudClient", sub: str
    ) -> "DynamicSessionModelResp":
        """
        Queries a dynamic session that is associated with this session.
        :param client: An instance of the cloud client.
        :param sub: The dynamic session key.
        :return: A DynamicSessionModelResp.
        """
        ts_parts: List[int] = list(map(int, sub.split(":")))
        return client.request_dynamic_session_model(
            self.session_key, ts_parts[0], ts_parts[1]
        )

    # TODO
    def query_packet(self, client: "CloudClient", sub: str):
        """
        Queries individual packets assuming this is an hourly dynamic session.
        :param client: An instance of the cloud client.
        :param sub: The packet key.
        :return: TODO
        """
        raise RedVoxError("Method not yet implemented")


@dataclass_json
@dataclass
class SessionModelReq:
    """
    Request object for directly querying sessions.
    """

    auth_token: str
    session_key: str


@dataclass_json
@dataclass
class SessionModelResp:
    """
    Response of directly queried session.
    """

    err: Optional[str]
    session: Optional[Session]


@dataclass_json
@dataclass
class SessionModelsReq:
    """
    Request object for querying a range of sessions.
    """

    auth_token: str
    id_uuids: Optional[List[str]] = None
    owner: Optional[str] = None
    start_ts: Optional[int] = None
    end_ts: Optional[int] = None
    include_public: bool = False


@dataclass_json
@dataclass
class SessionModelsResp:
    """
    Response object from querying a range of sessions.
    """

    err: Optional[str]
    sessions: List[Session]


@dataclass_json
@dataclass
class DynamicSessionModelReq:
    """
    Request object for querying a dynamic session.
    """

    auth_token: str
    session_key: str
    start_ts: int
    end_ts: int


@dataclass_json
@dataclass
class DynamicSessionModelResp:
    """
    Response object of querying a dynamic session.
    """

    err: Optional[str]
    dynamic_session: Optional[DynamicSession]


def request_session(
    redvox_config: RedVoxConfig,
    req: SessionModelReq,
    session: Optional[requests.Session] = None,
    timeout: Optional[float] = None,
) -> SessionModelResp:
    """
    Requests a single session given the session key.
    :param redvox_config: An instance of the cloud configuration.
    :param req: The session model request.
    :param session: An optional HTTP client session.
    :param timeout: An optional timeout.
    :return: An instance of the SessionModelResp.
    """
    # noinspection Mypy
    handle_resp: Callable[
        [requests.Response], SessionModelResp
    ] = lambda resp: SessionModelResp.from_dict(resp.json())
    return post_req(
        redvox_config,
        RoutesV3.SESSION_MODEL,
        req,
        handle_resp,
        session,
        timeout,
    )


def request_sessions(
    redvox_config: RedVoxConfig,
    req: SessionModelsReq,
    session: Optional[requests.Session] = None,
    timeout: Optional[float] = None,
) -> SessionModelsResp:
    """
    Requests a range of sessions.
    :param redvox_config: An instance of the cloud configuration.
    :param req: The sessions model request.
    :param session: An optional HTTP client session.
    :param timeout: An optional timeout.
    :return: An instance of the SessionModelsResp.
    """
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
    """
    Requests a single dynamic session given the dynamic session key.
    :param redvox_config: An instance of the cloud configuration.
    :param req: The dynamic session model request.
    :param session: An optional HTTP client session.
    :param timeout: An optional timeout.
    :return: An instance of the DynamicSessionModelResp.
    """
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


def session_key_from_packet(packet: WrappedRedvoxPacketM) -> str:
    """
    Constructs a session key given a RedVox packet.
    :param packet: The packet to construct a session key from.
    :return: A session key.
    """
    station_info: StationInformation = packet.get_station_information()
    if (
        station_info is None
        or station_info.get_id() == ""
        or station_info.get_uuid() == ""
    ):
        raise RedVoxError("Missing required station information")
    timing_info: TimingInformation = packet.get_timing_information()
    if timing_info is None or timing_info.get_app_start_mach_timestamp() == 0:
        raise RedVoxError("Missing required timing information")

    start_ts: int = round(timing_info.get_app_start_mach_timestamp())
    return f"{station_info.get_id()}:{station_info.get_uuid()}:{start_ts}"
