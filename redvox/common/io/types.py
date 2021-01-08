from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import reduce
from pathlib import PurePath
from typing import Dict, List, Optional, Set, TYPE_CHECKING, Any

from redvox.api1000.common.common import check_type
from redvox.common.date_time_utils import (
    datetime_from_epoch_microseconds_utc as dt_us,
    datetime_from_epoch_milliseconds_utc as dt_ms
)

if TYPE_CHECKING:
    from redvox.api1000.wrapped_redvox_packet.station_information import OsType
    from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
    from redvox.common.versioning import check_version


class ApiVersion(Enum):
    """
    Enumerates the API versions this SDK supports.
    """
    API_900: str = "API_900"
    API_1000: str = "API_1000"
    UNKNOWN: str = "UNKNOWN"


def _is_int(v: Any) -> bool:
    try:
        int(v)
        return True
    except ValueError:
        return False


@dataclass
class PathDescriptor:
    station_id: str
    date_time: datetime
    extension: str
    api_version: ApiVersion

    @staticmethod
    def from_path(path_str: str) -> Optional['PathDescriptor']:
        api_version: ApiVersion = check_version(path_str)
        path: PurePath = PurePath(path_str)
        name: str = path.stem
        ext: str = path.suffix

        split_name = name.split("_")

        if len(split_name) != 2:
            return None

        station_id: str = split_name[0]
        ts_str: str = split_name[1]

        if not _is_int(station_id) or not _is_int(ts_str):
            return None

        ts: int = int(ts_str)
        dt: datetime
        if api_version == ApiVersion.API_1000:
            dt = dt_us(ts)
        else:
            dt = dt_ms(ts)

        return PathDescriptor(station_id, dt, ext, api_version)


@dataclass
class ReadFilter:
    """
    Filter RedVox files from the file system.
    """
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    station_ids: Optional[Set[str]] = None
    extensions: Set[str] = field(default={".rdvxm", ".rdvxz"})
    start_dt_buf: timedelta = timedelta(minutes=2.0)
    end_dt_buf: timedelta = timedelta(minutes=2.0)

    def with_start_dt(self, start_dt: datetime) -> 'ReadFilter':
        """
        Adds a start datetime filter.
        :param start_dt: Start datetime that files should come after.
        :return: A modified instance of this filter
        """
        check_type(start_dt, [datetime])
        self.start_dt = start_dt
        return self

    def with_start_ts(self, start_ts: float) -> 'ReadFilter':
        """
        Adds a start time filter.
        :param start_ts: Start timestamp (microseconds)
        :return: A modified instance of this filter
        """
        check_type(start_ts, [int, float])
        return self.with_start_dt(dt_us(start_ts))

    def with_end_dt(self, end_dt: datetime) -> 'ReadFilter':
        """
        Adds an end datetime filter.
        :param end_dt: Filter for which packets should come before.
        :return: A modified instance of this filter
        """
        check_type(end_dt, [datetime])
        self.end_dt = end_dt
        return self

    def with_end_ts(self, end_ts: float) -> 'ReadFilter':
        """
        Like with_end_dt, but uses a microsecond timestamp.
        :param end_ts: Timestamp microseconds.
        :return: A modified instance of this filter
        """
        check_type(end_ts, [int, float])
        return self.with_end_dt(dt_us(end_ts))

    def with_station_ids(self, station_ids: Set[str]) -> 'ReadFilter':
        """
        Add a station id filter. Filters against provided station ids.
        :param station_ids: Station ids to filter against.
        :return: A modified instance of this filter
        """
        check_type(station_ids, [Set])
        self.station_ids = station_ids
        return self

    def with_extensions(self, extensions: Set[str]) -> 'ReadFilter':
        """
        Filters against a known file extension.
        :param extensions: One or more extensions to filter against
        :return: A modified instance of this filter
        """
        check_type(extensions, [Set])
        self.extensions = extensions
        return self

    def with_start_dt_buf(self, start_dt_buf: timedelta) -> 'ReadFilter':
        """
        Modifies the time buffer prepended to the start time.
        :param start_dt_buf: Amount of time to buffer before start time.
        :return: A modified instance of self.
        """
        check_type(start_dt_buf, [timedelta])
        self.start_dt_buf = start_dt_buf
        return self

    def with_end_dt_buf(self, end_dt_buf: timedelta) -> 'ReadFilter':
        """
        Modifies the time buffer appended to the end time.
        :param end_dt_buf: Amount of time to buffer after end time.
        :return: A modified instance of self.
        """
        check_type(end_dt_buf, [timedelta])
        self.end_dt_buf = end_dt_buf
        return self

    def apply_dt(self, date_time: datetime) -> bool:
        """
        Tests if a given datetime passes this filter.
        :param date_time: Datetime to test
        :return: True if the datetime is included, False otherwise
        """
        check_type(date_time, [datetime])
        if self.start_dt is not None and date_time < (self.start_dt - self.start_dt_buf):
            return False

        if self.end_dt is not None and date_time > (self.end_dt + self.end_dt_buf):
            return False

        return True

    def apply(self, path_descriptor: PathDescriptor) -> bool:
        check_type(path_descriptor, [PathDescriptor])

        if not self.apply_dt(path_descriptor.date_time):
            return False

        if self.station_ids is not None and path_descriptor.station_id not in self.station_ids:
            return False

        if self.extensions is not None and f".{path_descriptor.extension}" not in self.extensions:
            return False

        return True


# noinspection DuplicatedCode
@dataclass
class StationSummary:
    """
    Contains a summary of each stations data read result.
    """
    station_id: str
    station_uuid: str
    auth_id: str
    # pylint: disable=C0103
    os: 'OsType'
    os_version: str
    app_version: str
    audio_sampling_rate: float
    total_packets: int
    total_duration: timedelta
    start_dt: datetime
    end_dt: datetime

    @staticmethod
    def from_packets(packets: List['WrappedRedvoxPacketM']) -> 'StationSummary':
        """
        Generates a station summary from the provided packets.
        :param packets: Packets to generate summary from.
        :return: An instance of a StationSummary.
        """
        first_packet: 'WrappedRedvoxPacketM' = packets[0]
        last_packet: 'WrappedRedvoxPacketM' = packets[-1]
        total_duration: timedelta = reduce(lambda acc, packet: acc + packet.get_packet_duration(),
                                           packets,
                                           timedelta(seconds=0.0))
        start_dt: datetime = dt_us(first_packet.get_timing_information().get_packet_start_mach_timestamp())
        end_dt: datetime = dt_us(last_packet.get_timing_information().get_packet_start_mach_timestamp()) + \
                           last_packet.get_packet_duration()

        station_info = first_packet.get_station_information()
        audio = first_packet.get_sensors().get_audio()
        return StationSummary(
            station_info.get_id(),
            station_info.get_uuid(),
            station_info.get_auth_id(),
            station_info.get_os(),
            station_info.get_os_version(),
            station_info.get_app_version(),
            audio.get_sample_rate() if audio is not None else float("NaN"),
            len(packets),
            total_duration,
            start_dt,
            end_dt
        )


class ReadResult:
    """
    Result of reading multiple API M files.
    """

    def __init__(self,
                 station_id_uuid_to_packets: Dict[str, List['WrappedRedvoxPacketM']]):
        """
        :param station_id_uuid_to_packets: station_id:station_uuid -> packets
        """
        self.station_id_uuid_to_packets: Dict[str, List['WrappedRedvoxPacketM']] = station_id_uuid_to_packets
        self.__station_id_to_id_uuid: Dict[str, str] = {}
        self.__station_summaries: List[StationSummary] = []

        for id_uuid, packets in self.station_id_uuid_to_packets.items():
            split_id_uuid: List[str] = id_uuid.split(":")
            self.__station_id_to_id_uuid[split_id_uuid[0]] = id_uuid
            self.__station_summaries.append(StationSummary.from_packets(packets))

    @staticmethod
    def from_packets(packets: List['WrappedRedvoxPacketM']) -> 'ReadResult':
        """
        Constructs a read result from the provided packets.
        :param packets: Packets to construct read result from.
        :return: ReadResult from provided packets
        """
        check_type(packets, [List])
        station_id_uuid_to_packets: Dict[str, List['WrappedRedvoxPacketM']] = defaultdict(list)

        for packet in packets:
            station_info = packet.get_station_information()
            station_id: str = station_info.get_id()
            station_uuid: str = station_info.get_uuid()
            id_uuid: str = f"{station_id}:{station_uuid}"
            station_id_uuid_to_packets[id_uuid].append(packet)

        return ReadResult(station_id_uuid_to_packets)

    def __get_packets_for_station_id_uuid(self, station_id_uuid) -> List['WrappedRedvoxPacketM']:
        """
        Find packets given a station_id:uuid.
        :param station_id_uuid: Station id and uuid to get packets for.
        :return: A list of wrapped packets or an empty list if none match.
        """
        if station_id_uuid in self.station_id_uuid_to_packets:
            return self.station_id_uuid_to_packets[station_id_uuid]

        return []

    def __get_packets_for_station_id(self, station_id: str) -> List['WrappedRedvoxPacketM']:
        """
        Get packets for an associated station id.
        :param station_id: The station id.
        :return: A list of wrapped packets or an empty list if none provided.
        """
        if station_id in self.__station_id_to_id_uuid:
            return self.__get_packets_for_station_id_uuid(self.__station_id_to_id_uuid[station_id])

        return []

    def get_station_summaries(self) -> List[StationSummary]:
        """
        :return: A list of StationSummaries contained in this ReadResult
        """
        return self.__station_summaries

    def get_packets_for_station_id(self, station_id: str) -> List['WrappedRedvoxPacketM']:
        """
        Gets packets either for the provided station_id or the provided station_id:uuid.
        :param station_id: station_id or station_id:uuid to get packets for.
        :return: A list of packets of an empty list of none provided.
        """
        check_type(station_id, [str])
        if ":" in station_id:
            return self.__get_packets_for_station_id_uuid(station_id)
        else:
            return self.__get_packets_for_station_id(station_id)
