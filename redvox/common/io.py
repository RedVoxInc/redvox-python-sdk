from datetime import datetime
from glob import glob
from pathlib import PurePath
from typing import Any, Iterator, List, Optional, Set, Union
import os.path

from redvox.common.versioning import ApiVersion
from redvox.api1000.common.typing import check_type
from redvox.common.io.types import ReadFilter, IndexEntry, Index
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api900.wrapped_redvox_packet import WrappedRedvoxPacket
from redvox.api900.reader import read_rdvxz_file
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import reduce, total_ordering
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, TYPE_CHECKING, Union

from redvox.api1000.common.common import check_type
from redvox.common.versioning import check_version, ApiVersion
from redvox.common.date_time_utils import (
    datetime_from_epoch_microseconds_utc as dt_us,
    datetime_from_epoch_milliseconds_utc as dt_ms
)

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api900.wrapped_redvox_packet import WrappedRedvoxPacket
from redvox.api900.reader import read_rdvxz_file

if TYPE_CHECKING:
    from redvox.api1000.wrapped_redvox_packet.station_information import OsType

@total_ordering
@dataclass
class IndexEntry:
    full_path: str
    station_id: str
    date_time: datetime
    extension: str
    api_version: ApiVersion

    @staticmethod
    def from_path(path_str: str) -> Optional['IndexEntry']:
        api_version: ApiVersion = check_version(path_str)
        path: Path = Path(path_str)
        name: str = path.stem
        ext: str = path.suffix

        split_name = name.split("_")

        if len(split_name) != 2:
            return None

        station_id: str = split_name[0]
        ts_str: str = split_name[1]
        timestamp: Optional[int] = _is_int(ts_str)

        if _is_int(station_id) is None or timestamp is None:
            return None

        date_time: datetime
        if api_version == ApiVersion.API_1000:
            date_time = dt_us(timestamp)
        else:
            date_time = dt_ms(timestamp)

        return IndexEntry(str(path.resolve(strict=True)),
                          station_id,
                          date_time,
                          ext,
                          api_version)

    def read(self) -> Optional[Union[WrappedRedvoxPacketM, WrappedRedvoxPacket]]:
        if self.api_version == ApiVersion.API_900:
            return read_rdvxz_file(self.full_path)
        elif self.api_version == ApiVersion.API_1000:
            return WrappedRedvoxPacketM.from_compressed_path(self.full_path)
        else:
            return None

    def __lt__(self, other: 'IndexEntry') -> bool:
        return self.full_path.__lt__(other.full_path)

    def __eq__(self, other: 'IndexEntry') -> bool:
        return self.full_path == other.full_path


@dataclass
class Index:
    entries: List[IndexEntry]

    def stream(self, filt_fn=lambda _: True) -> Iterator[Union[WrappedRedvoxPacket, WrappedRedvoxPacketM]]:
        return filter(filt_fn, filter(_not_none, map(IndexEntry.read, self.entries)))

    def stream_api_900(self, filt_fn=lambda _: True) -> Iterator[WrappedRedvoxPacket]:
        return self.stream(lambda entry: entry.api_version == ApiVersion.API_900 and filt_fn(entry))

    def stream_api_1000(self, filt_fn=lambda _: True) -> Iterator[WrappedRedvoxPacketM]:
        return self.stream(lambda entry: entry.api_version == ApiVersion.API_1000 and filt_fn(entry))

    def read(self, filt_fn=lambda _: True) -> List[Union[WrappedRedvoxPacket, WrappedRedvoxPacketM]]:
        return list(self.stream(filt_fn))

    def read_api_900(self, filt_fn=lambda _: True) -> List[WrappedRedvoxPacket]:
        return list(self.stream_api_900(filt_fn))

    def read_api_1000(self, filt_fn=lambda _: True) -> List[WrappedRedvoxPacketM]:
        return list(self.stream_api_1000(filt_fn))


@dataclass
class ReadFilter:
    """
    Filter RedVox files from the file system.
    """
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    station_ids: Optional[Set[str]] = None
    extensions: Set[str] = field(default_factory=lambda: {".rdvxm", ".rdvxz"})
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

    def apply(self, path_descriptor: IndexEntry) -> bool:
        check_type(path_descriptor, [IndexEntry])

        if not self.apply_dt(path_descriptor.date_time):
            return False

        if self.station_ids is not None and path_descriptor.station_id not in self.station_ids:
            return False

        if self.extensions is not None and f".{path_descriptor.extension}" not in self.extensions:
            return False

        return True


# noinspection DuplicatedCode
# @dataclass
# class StationSummary:
#     """
#     Contains a summary of each stations data read result.
#     """
#     station_id: str
#     station_uuid: str
#     auth_id: str
#     api_version: ApiVersion
#     # pylint: disable=C0103
#     os: 'OsType'
#     os_version: str
#     app_version: str
#     audio_sampling_rate: float
#     total_packets: int
#     total_duration: timedelta
#     start_dt: datetime
#     end_dt: datetime
#
#     @staticmethod
#     def from_packets(packets: List['WrappedRedvoxPacketM']) -> 'StationSummary':
#         """
#         Generates a station summary from the provided packets.
#         :param packets: Packets to generate summary from.
#         :return: An instance of a StationSummary.
#         """
#         first_packet: 'WrappedRedvoxPacketM' = packets[0]
#         last_packet: 'WrappedRedvoxPacketM' = packets[-1]
#         total_duration: timedelta = reduce(lambda acc, packet: acc + packet.get_packet_duration(),
#                                            packets,
#                                            timedelta(seconds=0.0))
#         start_dt: datetime = dt_us(first_packet.get_timing_information().get_packet_start_mach_timestamp())
#         end_dt: datetime = dt_us(last_packet.get_timing_information().get_packet_start_mach_timestamp()) + \
#                            last_packet.get_packet_duration()
#
#         station_info = first_packet.get_station_information()
#         audio = first_packet.get_sensors().get_audio()
#         return StationSummary(
#             station_info.get_id(),
#             station_info.get_uuid(),
#             station_info.get_auth_id(),
#             station_info.get_os(),
#             station_info.get_os_version(),
#             station_info.get_app_version(),
#             audio.get_sample_rate() if audio is not None else float("NaN"),
#             len(packets),
#             total_duration,
#             start_dt,
#             end_dt
#         )


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
        # self.__station_summaries: List[StationSummary] = []

        for id_uuid, packets in self.station_id_uuid_to_packets.items():
            split_id_uuid: List[str] = id_uuid.split(":")
            self.__station_id_to_id_uuid[split_id_uuid[0]] = id_uuid
            # self.__station_summaries.append(StationSummary.from_packets(packets))

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

    # def get_station_summaries(self) -> List[StationSummary]:
    #     """
    #     :return: A list of StationSummaries contained in this ReadResult
    #     """
    #     return self.__station_summaries

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


# We need to parse the API M structured directory structure. Here, we enumerate the valid values for the various
# levels in the hierarchy.
__VALID_YEARS: Set[str] = {f"{i:04}" for i in range(2015, 2031)}
__VALID_MONTHS: Set[str] = {f"{i:02}" for i in range(1, 13)}
__VALID_DATES: Set[str] = {f"{i:02}" for i in range(1, 32)}
__VALID_HOURS: Set[str] = {f"{i:02}" for i in range(0, 24)}


def __list_subdirs(base_dir: str, valid_choices: Set[str]) -> List[str]:
    """
    Lists sub-directors in a given base directory that match the provided choices.
    :param base_dir: Base dir to find sub dirs in.
    :param valid_choices: A list of valid directory names.
    :return: A list of valid subdirs.
    """
    subdirs: Iterator[str] = map(lambda p: PurePath(p).name, glob(os.path.join(base_dir, "*", "")))
    return sorted(list(filter(valid_choices.__contains__, subdirs)))


def index_structured_api_900(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> Index:
    """
    This parses a structured API 900 directory structure and identifies files that match the provided filter.
    :param base_dir: Base directory (should be named api900)
    :param read_filter: Filter to filter files with
    :return: A list of wrapped packets on an empty list if none match the filter or none are found
    """
    for year in __list_subdirs(base_dir, __VALID_YEARS):
        for month in __list_subdirs(os.path.join(base_dir, year), __VALID_MONTHS):
            for day in __list_subdirs(os.path.join(base_dir, year, month), __VALID_DATES):
                # Before scanning for *.rdvxm files, let's see if the current year, month, day, are in the
                # filter's range. If not, we can short circuit and skip getting the *.rdvxz files.
                if not read_filter.apply_dt(datetime(int(year),
                                                     int(month),
                                                     int(day))):
                    continue

                path_descriptors: List[IndexEntry] = []

                extension: str
                for extension in read_filter.extensions:
                    paths: List[str] = glob(os.path.join(base_dir,
                                                         year,
                                                         month,
                                                         day,
                                                         f"*{extension}"))
                    descriptors: Iterator[IndexEntry] = filter(not_none, map(IndexEntry.from_path, paths))
                    path_descriptors.extend(descriptors)

                return Index(sort(path_descriptors))


def index_structured_api_1000(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> Index:
    """
    This parses a structured API M directory structure and identifies files that match the provided filter.
    :param base_dir: Base directory (should be named api1000)
    :param read_filter: Filter to filter files with
    :return: A list of wrapped packets on an empty list if none match the filter or none are found
    """
    for year in __list_subdirs(base_dir, __VALID_YEARS):
        for month in __list_subdirs(os.path.join(base_dir, year), __VALID_MONTHS):
            for day in __list_subdirs(os.path.join(base_dir, year, month), __VALID_DATES):
                for hour in __list_subdirs(os.path.join(base_dir, year, month, day), __VALID_HOURS):
                    # Before scanning for *.rdvxm files, let's see if the current year, month, day, hour are in the
                    # filter's range. If not, we can short circuit and skip getting the *.rdvxm files.
                    if not read_filter.apply_dt(datetime(int(year),
                                                         int(month),
                                                         int(day),
                                                         int(hour))):
                        continue

                    path_descriptors: List[IndexEntry] = []

                    extension: str
                    for extension in read_filter.extensions:
                        paths: List[str] = glob(os.path.join(base_dir,
                                                             year,
                                                             month,
                                                             day,
                                                             hour,
                                                             f"*{extension}"))
                        descriptors: Iterator[IndexEntry] = filter(not_none, map(IndexEntry.from_path, paths))
                        path_descriptors.extend(descriptors)

                    return Index(sorted(path_descriptors))


def index_structured(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> Index:
    base_path: PurePath = PurePath(base_dir)

    # API 900
    if base_path.name == "api900":
        return index_structured_api_900(base_dir, read_filter)
    # API 1000
    elif base_path.name == "api1000":
        return index_structured_api_1000(base_dir, read_filter)
    # Maybe parent to one or both?
    else:
        path_descriptors: List[IndexEntry] = []
        subdirs: List[str] = __list_subdirs(base_dir, {"api900", "api1000"})

        if "api900" in subdirs:
            path_descriptors.extend(index_structured_api_900(str(base_path.joinpath("api900"))))

        if "api1000" in subdirs:
            path_descriptors.extend(index_structured_api_1000(str(base_path.joinpath("api1000"))))

        return Index(sorted(path_descriptors))


def index_unstructured(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> Index:
    """
    Returns the list of file paths that match the given filter for unstructured data.
    :param base_dir: Directory containing unstructured data.
    :param read_filter: An (optional) ReadFilter for specifying station IDs and time windows.
    :return: An iterator of valid paths.
    """
    check_type(base_dir, [str])
    check_type(read_filter, [ReadFilter])

    path_descriptors: List[IndexEntry] = []

    extension: str
    for extension in read_filter.extensions:
        pattern: str = str(PurePath(base_dir).joinpath(f"*{extension}"))
        paths: List[str] = glob(os.path.join(base_dir, pattern))
        descriptors: Iterator[IndexEntry] = filter(not_none, map(IndexEntry.from_path, paths))
        path_descriptors.extend(descriptors)

    return Index(sorted(path_descriptors))

