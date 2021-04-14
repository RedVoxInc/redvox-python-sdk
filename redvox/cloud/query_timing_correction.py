"""
This module contains classes and routines for performing timing corrections on cloud based ranged queries.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING

from redvox.common.offset_model import compute_offsets

if TYPE_CHECKING:
    from redvox.cloud.station_stats import StationStatsResp
    from redvox.common.file_statistics import StationStat
    from redvox.common.offset_model import TimingOffsets
    from redvox.cloud.client import CloudClient


@dataclass
class CorrectedQuery:
    """
    A set of fields required for a corrected timing query.
    """
    station_id: str
    original_start_ts: float
    original_end_ts: float
    corrected_start_ts: float
    corrected_end_ts: float

    def start_offset(self) -> float:
        """
        Computes the start offset.
        :return: The start offset.
        """
        return self.corrected_start_ts - self.original_start_ts

    def end_offset(self) -> float:
        """
        Computes the end offset.
        :return: The end offset.
        """
        return self.corrected_end_ts - self.original_end_ts


def correct_query_timing(
    client: "CloudClient", start_ts: int, end_ts: int, station_ids: List[str]
) -> Optional[List[CorrectedQuery]]:
    """
    Corrects the timing for a given cloud range query.
    :param client: An instance of a cloud client.
    :param start_ts: The start of the query window.
    :param end_ts: The end of the query window.
    :param station_ids: A list of station IDs in the query.
    :return: A list of query corrections per station and per app start time.
    """

    station_stats_resp: Optional["StationStatsResp"] = client.request_station_stats(
        start_ts, end_ts, station_ids
    )

    station_stats: List[StationStat] = station_stats_resp.station_stats

    if station_stats_resp is None or len(station_stats) == 0:
        return None

    # Ensure sorted
    station_stats.sort(key=lambda stat: stat.packet_start_dt)

    # Group by station ID and then app start time
    grouped: Dict[str, Dict[datetime, List["StationStat"]]] = defaultdict(
        lambda: defaultdict(list)
    )

    station_stat: "StationStat"
    for station_stat in station_stats:
        grouped[station_stat.station_id][station_stat.app_start_dt].append(station_stat)

    # Compute new queries
    corrected_queries: List[CorrectedQuery] = []
    station_id: str
    for station_id in grouped:
        app_start_dt: datetime
        for app_start_dt in grouped[station_id]:
            stats: List["StationStat"] = grouped[station_id][app_start_dt]

            # No stats, return the original query
            if len(stats) == 0:
                corrected_queries.append(
                    CorrectedQuery(station_id, start_ts, end_ts, start_ts, end_ts)
                )
                continue

            # Compute new offsets
            timing_offsets: Optional["TimingOffsets"] = compute_offsets(stats)

            # No offsets, return the original query
            if timing_offsets is None:
                corrected_queries.append(
                    CorrectedQuery(station_id, start_ts, end_ts, start_ts, end_ts)
                )
                continue

            # Compute new offsets
            corrected_start_ts: float = (
                start_ts + timing_offsets.start_offset.total_seconds()
            )
            corrected_end_ts: float = end_ts + timing_offsets.end_offset.total_seconds()

            corrected_queries.append(
                CorrectedQuery(
                    station_id, start_ts, end_ts, corrected_start_ts, corrected_end_ts
                )
            )

    return corrected_queries
