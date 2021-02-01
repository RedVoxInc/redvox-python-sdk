from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Callable, List, Optional, TypeVar

import requests
from dataclasses_json import dataclass_json

import redvox.common.file_statistics as file_stats
from redvox.cloud.api import post_req
from redvox.cloud.config import RedVoxConfig
from redvox.cloud.routes import RoutesV1
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc as us2dt

T = TypeVar("T")
R = TypeVar("R")


def _map_opt(opt: Optional[T], f: Callable[[T], R]) -> Optional[R]:
    if opt is not None:
        return f(opt)
    return None


@dataclass_json
@dataclass
class GpsDateTime:
    """
    Represents timestamp pairings in API 1000 data.
    """

    mach_dt: float
    gps_dt: Optional[float]

    def into_file_stat(self) -> file_stats.GpsDateTime:
        gps_dt: Optional[datetime] = _map_opt(self.gps_dt, us2dt)
        return file_stats.GpsDateTime(us2dt(self.mach_dt), gps_dt)


@dataclass_json
@dataclass
class StationStat:
    """
    A collection of station fields for a given API 900 or API 1000 packet.
    These are used for timing correction and gap detection.
    """

    station_id: str
    station_uuid: str
    app_start_dt: Optional[float]
    packet_start_dt: float
    server_recv_dt: Optional[float]
    gps_dts: Optional[List[GpsDateTime]]
    latency: Optional[float]
    offset: Optional[float]
    sample_rate_hz: Optional[float]
    packet_duration: Optional[float]

    def into_file_stat(self) -> file_stats.StationStat:
        return file_stats.StationStat(
            self.station_id,
            self.station_uuid,
            _map_opt(self.app_start_dt, us2dt),
            us2dt(self.packet_start_dt),
            _map_opt(self.server_recv_dt, us2dt),
            _map_opt(self.gps_dts, lambda dts: list(map(GpsDateTime.into_file_stat, dts))),
            self.latency,
            self.offset,
            self.sample_rate_hz,
            _map_opt(self.packet_duration, lambda dur: timedelta(microseconds=dur))
        )


@dataclass_json
@dataclass
class StationStatReq:
    auth_token: str
    start_ts_s: int
    end_ts_s: int
    station_ids: List[str]


@dataclass_json
@dataclass
class StationStatResp:
    station_stats: List["StationStat"]


def request_station_stats(
        redvox_config: RedVoxConfig,
        station_stat_req: StationStatReq,
        session: Optional[requests.Session] = None,
        timeout: Optional[float] = None,
) -> Optional[StationStatResp]:
    # noinspection Mypy
    handle_resp: Callable[
        [requests.Response], StationStatResp
    ] = lambda resp: StationStatResp.from_dict(resp.json())
    return post_req(
        redvox_config,
        RoutesV1.STATION_STATS,
        station_stat_req,
        handle_resp,
        session,
        timeout,
    )
