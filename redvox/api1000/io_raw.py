"""
This module provides low level aggregate read functionality for RedVox API M data.
"""

from collections import defaultdict
from datetime import datetime, timezone
from dataclasses import dataclass
from glob import glob
import os.path
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc as dt_us


@dataclass
class ReadFilter:
    """
    Filter API M files from the file system.
    """
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    station_ids: Optional[Set[str]] = None
    extension: str = ".rdvxm"

    def with_start_dt(self, start_dt: datetime) -> 'ReadFilter':
        """
        Adds a start datetime filter.
        :param start_dt: Start datetime that files should come after.
        :return: A modified instance of this filter
        """
        self.start_dt = start_dt
        return self

    def with_start_ts(self, start_ts: float) -> 'ReadFilter':
        """
        Adds a start time filter.
        :param start_ts: Start timestamp (microseconds)
        :return: A modified instance of this filter
        """
        return self.with_start_dt(dt_us(start_ts))

    def with_end_dt(self, end_dt: datetime) -> 'ReadFilter':
        """
        Adds an end datetime filter.
        :param end_dt: Filter for which packets should come before.
        :return: A modified instance of this filter
        """
        self.end_dt = end_dt
        return self

    def with_end_ts(self, end_ts: float) -> 'ReadFilter':
        """
        Like with_end_dt, but uses a microsecond timestamp.
        :param end_ts: Timestamp microseconds.
        :return: A modified instance of this filter
        """
        return self.with_end_dt(dt_us(end_ts))

    def with_station_ids(self, station_ids: Set[str]) -> 'ReadFilter':
        """
        Add a station id filter. Filters against provided station ids.
        :param station_ids: Station ids to filter against.
        :return: A modified instance of this filter
        """
        self.station_ids = station_ids
        return self

    def with_extension(self, extension: str) -> 'ReadFilter':
        """
        Filters against a known file extension.
        :param extension: Extension to filter against
        :return: A modified instance of this filter
        """
        self.extension = extension
        return self

    def filter_dt(self, dt: datetime) -> bool:
        """
        Tests if a given datetime passes this filter.
        :param dt: Datetime to test
        :return: True if the datetime is included, False otherwise
        """
        if self.start_dt is not None and dt < self.start_dt:
            return False

        if self.end_dt is not None and dt > self.end_dt:
            return False

        return True

    def filter_path(self, path: str) -> bool:
        """
        Tests a given file system path against this filter.
        :param path: Path to test.
        :return: True if the path is accepted, False otherwise
        """
        _path: Path = Path(path)
        ext: str = "".join(_path.suffixes)
        station_ts: str = _path.stem
        split: List[str] = station_ts.split("_")
        station_id: str = split[0]
        ts: float = float(split[1])
        dt: datetime = dt_us(ts)

        if not self.filter_dt(dt):
            return False

        if self.station_ids is not None and station_id not in self.station_ids:
            return False

        if self.extension is not None and self.extension != ext:
            return False

        return True


class ReadResult:
    """
    Result of reading multiple API M files.
    """
    def __init__(self,
                 station_id_uuid_to_packets: Dict[str, List[WrappedRedvoxPacketM]]):
        """
        :param station_id_uuid_to_packets: station_id:station_uuid -> packets
        """
        self.station_id_uuid_to_packets: Dict[str, List[WrappedRedvoxPacketM]] = station_id_uuid_to_packets
        self.__station_id_to_id_uuid: Dict[str, str] = {}

        for id_uuid, packets in self.station_id_uuid_to_packets.items():
            s: List[str] = id_uuid.split(":")
            self.__station_id_to_id_uuid[s[0]] = s[1]

    @staticmethod
    def from_packets(packets: List[WrappedRedvoxPacketM]) -> 'ReadResult':
        """
        Constructs a read result from the provided packets.
        :param packets: Packets to construct read result from.
        :return: ReadResult from provided packets
        """
        station_id_uuid_to_packets: Dict[str, List[WrappedRedvoxPacketM]] = defaultdict(list)

        for packet in packets:
            station_info = packet.get_station_information()
            station_id: str = station_info.get_id()
            station_uuid: str = station_info.get_uuid()
            id_uuid: str = f"{station_id}:{station_uuid}"
            station_id_uuid_to_packets[id_uuid].append(packet)

        return ReadResult(station_id_uuid_to_packets)

    def __get_packets_for_station_id_uuid(self, station_id_uuid) -> List[WrappedRedvoxPacketM]:
        """
        Find packets given a station_id:uuid.
        :param station_id_uuid: Station id and uuid to get packets for.
        :return: A list of wrapped packets or an empty list if none match.
        """
        if station_id_uuid in self.station_id_uuid_to_packets:
            return self.station_id_uuid_to_packets[station_id_uuid]

        return []

    def __get_packets_for_station_id(self, station_id: str) -> List[WrappedRedvoxPacketM]:
        """
        Get packets for an associated station id.
        :param station_id: The station id.
        :return: A list of wrapped packets or an empty list if none provided.
        """
        if station_id in self.__station_id_to_id_uuid:
            return self.__get_packets_for_station_id_uuid(self.__station_id_to_id_uuid[station_id])

        return []

    def get_station_id_uuids(self) -> List[str]:
        """
        :return: A list of station_id:uuids contained in this ReadResult
        """
        return list(self.station_id_uuid_to_packets.keys())

    def get_packets_for_station_id(self, station_id: str) -> List[WrappedRedvoxPacketM]:
        """
        Gets packets either for the provided station_id or the provided station_id:uuid.
        :param station_id: station_id or station_id:uuid to get packets for.
        :return: A list of packets of an empty list of none provided.
        """
        if ":" in station_id:
            return self.__get_packets_for_station_id_uuid(station_id)
        else:
            return self.__get_packets_for_station_id(station_id)


# We need to parse the API M structured directory structure. Here, we enumerate the valid values for the various
# levels in the hierarchy.
__VALID_YEARS:  Set[str] = {f"{i:04}" for i in range(2018, 2031)}
__VALID_MONTHS: Set[str] = {f"{i:02}" for i in range(1, 13)}
__VALID_DATES:  Set[str] = {f"{i:02}" for i in range(1, 32)}
__VALID_HOURS:  Set[str] = {f"{i:02}" for i in range(0, 24)}


def __list_subdirs(base_dir: str, valid_choices: Set[str]) -> List[str]:
    """
    Lists sub-directors in a given base directory that match the provided choices.
    :param base_dir: Base dir to find sub dirs in.
    :param valid_choices: A list of valid directory names.
    :return: A list of valid subdirs.
    """
    subdirs: Iterator[str] = map(lambda p: Path(p).name, glob(os.path.join(base_dir, "*", "")))
    return sorted(list(filter(valid_choices.__contains__, subdirs)))


def __parse_structured_layout(base_dir: str,
                              read_filter: ReadFilter = ReadFilter()) -> List[str]:
    """
    This parses a structured API M directory structure and identifies files that match the provided filter.
    :param base_dir: Base directory (should be named api1000)
    :param read_filter: Filter to filter files with
    :return: A list of wrapped packets on an empty list if none match the filter or none are found
    """
    all_paths: List[str] = []
    for year in __list_subdirs(base_dir, __VALID_YEARS):
        for month in __list_subdirs(os.path.join(base_dir, year), __VALID_MONTHS):
            for day in __list_subdirs(os.path.join(base_dir, year, month), __VALID_DATES):
                for hour in __list_subdirs(os.path.join(base_dir, year, day), __VALID_HOURS):
                    # Before scanning for *.rdvxm files, let's see if the current year, month, day, hour are in the
                    # filter's range. If not, we can short circuit and skip getting the *.rdvxm files.
                    if not read_filter.filter_dt(datetime(int(year),
                                                          int(month),
                                                          int(day),
                                                          int(hour),
                                                          tzinfo=timezone.utc)):
                        continue

                    paths: List[str] = glob(os.path.join(base_dir,
                                                         year,
                                                         month,
                                                         day,
                                                         hour,
                                                         f"*.{read_filter.extension}"))
                    # Filer paths that match the predicate
                    valid_paths: List[str] = list(filter(lambda path: read_filter.filter_path(path), paths))
                    if len(valid_paths) > 0:
                        all_paths.extend(valid_paths)

    return all_paths


def read_bufs(bufs: List[bytes]) -> ReadResult:
    """
    Reads a list of API M packet buffers.
    :param bufs: Buffers to read.
    :return: A ReadResult of the read data.
    """
    wrapped_packets: List[WrappedRedvoxPacketM] = list(sorted(map(WrappedRedvoxPacketM.from_compressed_bytes, bufs)))
    return ReadResult.from_packets(wrapped_packets)


def read_structured(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> ReadResult:
    """
    Read structured API M data. Structured API data is stored using the following directory hierarchy.
        api1000/[YYYY]/[MM]/[DD]/[HH]/*.rdvxm
    :param base_dir: Base directory of structured data (should be named api1000)
    :param read_filter: Filter to apply to files.
    :return: A ReadResult
    """
    paths: List[str] = __parse_structured_layout(base_dir, read_filter)
    wrapped_packets: List[WrappedRedvoxPacketM] = list(sorted(map(WrappedRedvoxPacketM.from_compressed_path, paths)))
    return ReadResult.from_packets(wrapped_packets)


def read_unstructured(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> ReadResult:
    """
    Reads RedVox files from a provided directory.
    :param base_dir: Directory to read files from.
    :param read_filter: Filter to filter files with.
    :return: A ReadResult.
    """
    paths: List[str] = glob(os.path.join(base_dir, f"*.{read_filter.extension}"))
    paths = list(filter(lambda path: read_filter.filter_path(path), paths))
    wrapped_packets: List[WrappedRedvoxPacketM] = list(sorted(map(WrappedRedvoxPacketM.from_compressed_path, paths)))
    return ReadResult.from_packets(wrapped_packets)

