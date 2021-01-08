"""
This module provides several primitives for reading and filtering RedVox data.

Generally, methods in this module should not be used directly, but instead these provide building blocks
 for higher-level IO operations.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from glob import glob
import os.path
from pathlib import Path
from typing import Iterator, List, Optional, Set

from redvox.api1000.common.common import check_type
from redvox.api1000.common.lz4 import decompress
import redvox.api1000.proto.redvox_api_m_pb2 as pb
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

    def with_extension(self, extension: str) -> 'ReadFilter':
        """
        Filters against a known file extension.
        :param extension: Extension to filter against
        :return: A modified instance of this filter
        """
        check_type(extension, [str])
        self.extension = extension
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

    def filter_dt(self, date_time: datetime) -> bool:
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

    def filter_path(self, path: str) -> bool:
        """
        Tests a given file system path against this filter.
        :param path: Path to test.
        :return: True if the path is accepted, False otherwise
        """
        check_type(path, [str])
        _path: Path = Path(path)
        ext: str = "".join(_path.suffixes)
        station_ts: str = _path.stem
        split: List[str] = station_ts.split("_")
        station_id: str = split[0]
        timestamp: float = float(split[1])
        date_time: datetime = dt_us(timestamp)

        if not self.filter_dt(date_time):
            return False

        if self.station_ids is not None and station_id not in self.station_ids:
            return False

        if self.extension is not None and self.extension != ext:
            return False

        return True


# We need to parse the API M structured directory structure. Here, we enumerate the valid values for the various
# levels in the hierarchy.
__VALID_YEARS: Set[str] = {f"{i:04}" for i in range(2018, 2031)}
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
    subdirs: Iterator[str] = map(lambda p: Path(p).name, glob(os.path.join(base_dir, "*", "")))
    return sorted(list(filter(valid_choices.__contains__, subdirs)))


def index_structured(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> Iterator[str]:
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
                    if not read_filter.filter_dt(datetime(int(year),
                                                          int(month),
                                                          int(day),
                                                          int(hour))):
                        continue

                    paths: List[str] = glob(os.path.join(base_dir,
                                                         year,
                                                         month,
                                                         day,
                                                         hour,
                                                         f"*{read_filter.extension}"))
                    # Filter paths that match the predicate
                    valid_path: str
                    for valid_path in filter(read_filter.filter_path, paths):
                        yield valid_path


def index_unstructured(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> Iterator[str]:
    """
    Returns the list of file paths that match the given filter for unstructured data.
    :param base_dir: Directory containing unstructured data.
    :param read_filter: An (optional) ReadFilter for specifying station IDs and time windows.
    :return: An iterator of valid paths.
    """
    check_type(base_dir, [str])
    check_type(read_filter, [ReadFilter])
    pattern: str = os.path.join(base_dir, f"*{read_filter.extension}")
    paths: List[str] = glob(os.path.join(base_dir, pattern))
    return filter(read_filter.filter_path, paths)


def decompress_bufs(bufs: Iterator[bytes]) -> Iterator[bytes]:
    """
    Decompresses a stream of byte buffers.
    :param bufs: Stream to decompress.
    :return: A stream of decompressed byte buffers.
    """
    return map(decompress, bufs)


def read_path_buf(path: str) -> bytes:
    """
    Returns the bytes stored at the provided file path.
    :param path: Path to load bytes from.
    :return: The bytes stored at the provided file path.
    """
    with open(path, "rb") as fin:
        return fin.read()


def read_path_bufs(paths: Iterator[str]) -> Iterator[bytes]:
    """
    Streams multiple byte buffers (each representing a single RedVox file).
    :param paths: A stream of paths to read.
    :return: A stream of byte buffers.
    """
    return map(read_path_buf, paths)


def decompress_paths(paths: Iterator[str]) -> Iterator[bytes]:
    """
    Reads and decompresses a stream of file paths representing API M data.
    :param paths: A stream of paths to read and decompress.
    :return: A stream of bytes representing the decompressed packet content.
    """
    return decompress_bufs(read_path_bufs(paths))


def deserialize_bufs(bufs: Iterator[bytes]) -> Iterator[pb.RedvoxPacketM]:
    """
    Deserializes a stream of buffers into a stream of RedvoxPacketM protobuf types.
    :param bufs: A stream of buffers to deserialize.
    :return: A stream of protobuf RedvoxPacketM objects.
    """
    buf: bytes
    for buf in bufs:
        proto: pb.RedvoxPacketM = pb.RedvoxPacketM()
        proto.ParseFromString(buf)
        yield proto


def wrap_protos(protos: Iterator[pb.RedvoxPacketM]) -> Iterator[WrappedRedvoxPacketM]:
    """
    Transforms a stream of protobuf RedvoxPacketM objects into a stream of WrappedRedvoxPacketM objects.
    :param protos: A stream of protobuf encoded RedvoxPacketM objects.
    :return: A stream of WrappedRedvoxPacketM objects.
    """
    proto: pb.RedvoxPacketM
    for proto in protos:
        yield WrappedRedvoxPacketM(proto)


def read_bufs(bufs: Iterator[bytes]) -> Iterator[WrappedRedvoxPacketM]:
    """
    Converts a stream of compressed serialized buffers into a stream of WrappedRedvoxPacketM objects.
    :param bufs: A stream of compressed serialized buffers.
    :return: A stream of WrappedRedvoxPacketM objects.
    """
    decompressed_bufs: Iterator[bytes] = decompress_bufs(bufs)
    protos: Iterator[pb.RedvoxPacketM] = deserialize_bufs(decompressed_bufs)
    return wrap_protos(protos)


def read_path(path: str) -> bytes:
    """
    Reads and decompressed and individual path.
    :param path: The path to read and decompress.
    :return: The bytes associated with the decompressed file.
    """
    with open(path, "rb") as fin:
        buf: bytes = fin.read()
        return decompress(buf)


def read_paths(paths: Iterator[str]) -> Iterator[WrappedRedvoxPacketM]:
    """
    Reads, decompresses, deserialized, and wraps RedVox data.
    :param paths: A stream of file paths to transform.
    :return: A stream of WrappedRedvoxPacketM packets.
    """
    bufs_iter = map(read_path, paths)
    protos_iter = deserialize_bufs(bufs_iter)
    return wrap_protos(protos_iter)
