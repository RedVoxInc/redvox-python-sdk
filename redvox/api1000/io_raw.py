"""
This module provides low level aggregate read functionality for RedVox API M data.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import reduce
from typing import Dict, Iterator, List

from redvox.api1000.common.common import check_type
import redvox.api1000.io_lib as io_lib
from redvox.api1000.wrapped_redvox_packet.station_information import OsType
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc as dt_us


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
    os: OsType
    os_version: str
    app_version: str
    audio_sampling_rate: float
    total_packets: int
    total_duration: timedelta
    start_dt: datetime
    end_dt: datetime

    @staticmethod
    def from_packets(packets: List[WrappedRedvoxPacketM]) -> 'StationSummary':
        """
        Generates a station summary from the provided packets.
        :param packets: Packets to generate summary from.
        :return: An instance of a StationSummary.
        """
        first_packet: WrappedRedvoxPacketM = packets[0]
        last_packet: WrappedRedvoxPacketM = packets[-1]
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
                 station_id_uuid_to_packets: Dict[str, List[WrappedRedvoxPacketM]]):
        """
        :param station_id_uuid_to_packets: station_id:station_uuid -> packets
        """
        self.station_id_uuid_to_packets: Dict[str, List[WrappedRedvoxPacketM]] = station_id_uuid_to_packets
        self.__station_id_to_id_uuid: Dict[str, str] = {}
        self.__station_summaries: List[StationSummary] = []

        for id_uuid, packets in self.station_id_uuid_to_packets.items():
            split_id_uuid: List[str] = id_uuid.split(":")
            self.__station_id_to_id_uuid[split_id_uuid[0]] = id_uuid
            self.__station_summaries.append(StationSummary.from_packets(packets))

    @staticmethod
    def from_packets(packets: List[WrappedRedvoxPacketM]) -> 'ReadResult':
        """
        Constructs a read result from the provided packets.
        :param packets: Packets to construct read result from.
        :return: ReadResult from provided packets
        """
        check_type(packets, [List])
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

    def get_station_summaries(self) -> List[StationSummary]:
        """
        :return: A list of StationSummaries contained in this ReadResult
        """
        return self.__station_summaries

    def get_packets_for_station_id(self, station_id: str) -> List[WrappedRedvoxPacketM]:
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


def read_bufs(bufs: List[bytes], parallel: bool = False) -> ReadResult:
    """
    Reads a list of API M packet buffers.
    :param bufs: Buffers to read.
    :return: A ReadResult of the read data.
    """
    check_type(bufs, [List])
    wrapped_packets: List[WrappedRedvoxPacketM] = list(sorted(io_lib.read_bufs(bufs, parallel)))
    return ReadResult.from_packets(wrapped_packets)


def read_structured(base_dir: str,
                    read_filter: io_lib.ReadFilter = io_lib.ReadFilter(),
                    parallel: bool = False) -> ReadResult:
    """
    Read structured API M data. Structured API data is stored using the following directory hierarchy.
        api1000/[YYYY]/[MM]/[DD]/[HH]/*.rdvxm
    :param base_dir: Base directory of structured data (should be named api1000)
    :param read_filter: Filter to apply to files.
    :return: A ReadResult
    """
    check_type(base_dir, [str])
    check_type(read_filter, [io_lib.ReadFilter])
    paths: Iterator[str] = io_lib.index_structured(base_dir, read_filter)
    wrapped_packets: List[WrappedRedvoxPacketM] = list(sorted(io_lib.read_paths(paths, parallel)))
    return ReadResult.from_packets(wrapped_packets)


def read_unstructured(base_dir: str,
                      read_filter: io_lib.ReadFilter = io_lib.ReadFilter(),
                      parallel: bool = False) -> ReadResult:
    """
    Reads RedVox files from a provided directory.
    :param base_dir: Directory to read files from.
    :param read_filter: Filter to filter files with.
    :return: A ReadResult.
    """
    check_type(base_dir, [str])
    check_type(read_filter, [io_lib.ReadFilter])
    paths: Iterator[str] = io_lib.index_unstructured(base_dir, read_filter)
    wrapped_packets: List[WrappedRedvoxPacketM] = list(sorted(io_lib.read_paths(paths, parallel)))
    return ReadResult.from_packets(wrapped_packets)


def stream_structured(base_dir: str,
                      read_filter: io_lib.ReadFilter = io_lib.ReadFilter(),
                      parallel: bool = False) -> Iterator[WrappedRedvoxPacketM]:
    """
    Lazily loads API M data from a structured layout.
    :param base_dir: Directory to read files from.
    :param read_filter: Filter to filter files with.
    :return: An iterator that reads and loads one WrappedRedvoxPacketM at a time.
    """
    check_type(base_dir, [str])
    check_type(read_filter, [io_lib.ReadFilter])
    paths: Iterator[str] = io_lib.index_structured(base_dir, read_filter)
    return io_lib.read_paths(paths, parallel)


def stream_unstructured(base_dir: str,
                        read_filter: io_lib.ReadFilter = io_lib.ReadFilter(),
                        parallel: bool = False) -> Iterator[WrappedRedvoxPacketM]:
    """
    Lazily loads API M data from an unstructured layout.
    :param base_dir: Directory to read files from.
    :param read_filter: Filter to filter files with.
    :return: An iterator that reads and loads one WrappedRedvoxPacketM at a time.
    """
    check_type(base_dir, [str])
    check_type(read_filter, [io_lib.ReadFilter])
    paths: Iterator[str] = io_lib.index_unstructured(base_dir, read_filter)
    return io_lib.read_paths(paths, parallel)
