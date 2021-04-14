"""
This module provides access to the timing station statistics through the RedVox Cloud API.
"""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Callable, List, Optional, TypeVar

import requests
from dataclasses_json import dataclass_json

import redvox.common.file_statistics as file_stats
from redvox.cloud.api import post_req
from redvox.cloud.config import RedVoxConfig
from redvox.cloud.routes import RoutesV1
from redvox.common.date_time_utils import (
    datetime_from_epoch_microseconds_utc as us2dt,
    datetime_to_epoch_microseconds_utc as dt2us,
)

T = TypeVar("T")
R = TypeVar("R")


def _map_opt(opt: Optional[T], f: Callable[[T], R]) -> Optional[R]:
    """
    Maps an optional with the given function.
    :param opt: The optional top map.
    :param f: The mapping function.
    :return: The mapped value or None.
    """
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
        """
        :return: Converts this into the file_statistics module representation.
        """
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
        """
        :return: Converts this into the file_statistics module representation.
        """
        return file_stats.StationStat(
            self.station_id,
            self.station_uuid,
            _map_opt(self.app_start_dt, us2dt),
            us2dt(self.packet_start_dt),
            _map_opt(self.server_recv_dt, us2dt),
            _map_opt(
                self.gps_dts, lambda dts: list(map(GpsDateTime.into_file_stat, dts))
            ),
            self.latency,
            (self.packet_start_dt + (self.packet_duration / 2.0)),
            self.offset,
            self.sample_rate_hz,
            _map_opt(self.packet_duration, lambda dur: timedelta(microseconds=dur)),
        )


@dataclass_json
@dataclass
class StationStatReq:
    """
    A StationStatReq container.
    """

    auth_token: str
    start_ts_s: int
    end_ts_s: int
    station_ids: List[str]
    secret_token: Optional[str] = None


@dataclass
class StationStatsResp:
    """
    A response type converted into the file_statistics module representation.
    """

    station_stats: List[file_stats.StationStat]


@dataclass_json
@dataclass
class StationStatResp:
    """
    A response contain StationStat instances.
    """

    station_stats: List[StationStat]

    def into_station_stats_resp(self) -> StationStatsResp:
        return StationStatsResp(
            list(map(StationStat.into_file_stat, self.station_stats))
        )


def request_station_stats(
    redvox_config: RedVoxConfig,
    station_stat_req: StationStatReq,
    session: Optional[requests.Session] = None,
    timeout: Optional[float] = None,
) -> Optional[StationStatsResp]:
    """
    Requests timing statistics with the given parameters.
    :param redvox_config: The cloud configuration.
    :param station_stat_req: The request.
    :param session: The optional session.
    :param timeout: The optional timeout.
    :return: A StationStatsResp.
    """
    # noinspection Mypy
    handle_resp: Callable[
        [requests.Response], StationStatResp
    ] = lambda resp: StationStatResp.from_dict(resp.json()).into_station_stats_resp()
    return post_req(
        redvox_config,
        RoutesV1.STATION_STATS,
        station_stat_req,
        handle_resp,
        session,
        timeout,
    )
