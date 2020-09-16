from collections import defaultdict
from datetime import datetime
from dataclasses import dataclass
from glob import glob
import os.path
from pathlib import Path
from typing import Dict, List, Optional, Set

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.common import date_time_utils
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc as dt_us


@dataclass
class ReadFilter:
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    station_ids: Optional[Set[str]] = None
    extension: str = ".rdvxm"

    def with_start_dt(self, start_dt: datetime) -> 'ReadFilter':
        self.start_dt = start_dt
        return self

    def with_start_ts(self, start_ts: float) -> 'ReadFilter':
        return self.with_start_dt(dt_us(start_ts))

    def with_end_dt(self, end_dt: datetime) -> 'ReadFilter':
        self.end_dt = end_dt
        return self

    def with_end_ts(self, end_ts: float) -> 'ReadFilter':
        return self.with_end_dt(dt_us(end_ts))

    def with_station_ids(self, station_ids: Set[str]) -> 'ReadFilter':
        self.station_ids = station_ids
        return self

    def with_extension(self, extension: str) -> 'ReadFilter':
        self.extension = extension
        return self

    def filter_path(self, path: str) -> bool:
        _path: Path = Path(path)
        ext: str = "".join(_path.suffixes)
        station_ts: str = _path.stem
        split: List[str] = station_ts.split("_")
        station_id: str = split[0]
        ts: float = float(split[1])
        dt: datetime = dt_us(ts)

        if self.start_dt is not None and dt < self.start_dt:
            return False

        if self.end_dt is not None and dt > self.end_dt:
            return False

        if self.station_ids is not None and station_id not in self.station_ids:
            return False

        if self.extension is not None and self.extension != ext:
            return False

        return True


class ReadResult:
    def __init__(self,
                 station_id_uuid_to_packets: Dict[str, List[WrappedRedvoxPacketM]]):
        self.station_id_uuid_to_packets: Dict[str, List[WrappedRedvoxPacketM]] = station_id_uuid_to_packets
        self.__station_id_to_id_uuid: Dict[str, str] = {}

        for id_uuid, packets in self.station_id_uuid_to_packets.items():
            s: List[str] = id_uuid.split(":")
            self.__station_id_to_id_uuid[s[0]] = s[1]

    @staticmethod
    def empty() -> 'ReadResult':
        return ReadResult({})

    @staticmethod
    def from_packets(packets: List[WrappedRedvoxPacketM]) -> 'ReadResult':
        station_id_uuid_to_packets: Dict[str, List[WrappedRedvoxPacketM]] = defaultdict(list)

        for packet in packets:
            station_info = packet.get_station_information()
            station_id: str = station_info.get_id()
            station_uuid: str = station_info.get_uuid()
            id_uuid: str = f"{station_id}:{station_uuid}"
            station_id_uuid_to_packets[id_uuid].append(packet)

        return ReadResult(station_id_uuid_to_packets)

    def __get_packets_for_station_id_uuid(self, station_id_uuid) -> List[WrappedRedvoxPacketM]:
        if station_id_uuid in self.station_id_uuid_to_packets:
            return self.station_id_uuid_to_packets[station_id_uuid]

        return []

    def __get_packets_for_station_id(self, station_id: str) -> List[WrappedRedvoxPacketM]:
        if station_id in self.__station_id_to_id_uuid:
            return self.__get_packets_for_station_id_uuid(self.__station_id_to_id_uuid[station_id])

        return []

    def get_station_id_uuids(self) -> List[str]:
        return list(self.station_id_uuid_to_packets.keys())

    def get_packets_for_station_id(self, station_id: str) -> List[WrappedRedvoxPacketM]:
        if ":" in station_id:
            return self.__get_packets_for_station_id_uuid(station_id)
        else:
            return self.__get_packets_for_station_id(station_id)


def _get_structured_paths(directory: str) -> List[str]:
    """
    Given a base directory (which should end with api1000), find the paths of all structured API M redvox files.
    :param directory: The base directory path (which should end with api1000)
    :return: A list of paths in a structured layout of filtered API M redvox files.
    """
    paths: List[str] = []

    for (year, month, day, hour) in date_time_utils.DateIteratorAPIM(start_timestamp_utc_s, end_timestamp_utc_s):
        all_paths = glob.glob(os.path.join(directory, year, month, day, hour, f"*.{REDVOX_API_M_FILE_EXT}"))
        valid_paths = list(
            filter(lambda path: _is_path_in_set(path, start_timestamp_utc_s, end_timestamp_utc_s, redvox_ids),
                   all_paths))
        paths.extend(valid_paths)

    return paths


def read_bufs(bufs: List[bytes]) -> ReadResult:
    wrapped_packets: List[WrappedRedvoxPacketM] = list(sorted(map(WrappedRedvoxPacketM.from_compressed_bytes, bufs)))
    return ReadResult.from_packets(wrapped_packets)


def read_structured(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> ReadResult:
    pattern: str = os.path.join(base_dir, f"*.{read_filter.extension}")
    paths: List[str] = glob(pattern)
    paths = list(filter(lambda path: read_filter.filter_path(path), paths))
    wrapped_packets: List[WrappedRedvoxPacketM] = list(sorted(map(WrappedRedvoxPacketM.from_compressed_bytes, bufs)))


def read_unstructured(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> ReadResult:
    pattern: str = os.path.join(base_dir, f"*.{read_filter.extension}")
    paths: List[str] = glob(pattern)
    paths = list(filter(lambda path: read_filter.filter_path(path), paths))
    wrapped_packets: List[WrappedRedvoxPacketM] = list(sorted(map(WrappedRedvoxPacketM.from_compressed_path, paths)))
    return ReadResult.from_packets(wrapped_packets)
