"""
Defines generic station metadata for API-independent analysis
all timestamps are floats in microseconds unless otherwise stated
"""
from dataclasses import dataclass
from typing import Tuple, Optional, List

import numpy as np

from redvox.common.offset_model import OffsetModel
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
# from redvox.api1000.wrapped_redvox_packet import event_streams as es


@dataclass
class StationKey:
    """
    A set of values that uniquely define a station
    Properties:
        id: str, id of the station
        uuid: str, uuid of the station
        start_timestamp_micros: float, starting time of the station in microseconds since epoch UTC
    """

    id: str
    uuid: str
    start_timestamp_micros: float

    def __repr__(self):
        return f"StationKey:\nid:{self.id}, uuid:{self.uuid}, start_timestamp:{self.start_timestamp_micros}"

    def get_key(self) -> Tuple[str, str, float]:
        return self.id, self.uuid, self.start_timestamp_micros


def validate_metadata_list(data_packets: List[WrappedRedvoxPacketM]) -> bool:
    """
    Check if all packets have the same metadata values
    :param data_packets: packets to check
    :return: True if all packets have the same metadata values
    """
    if len(data_packets) == 1 or (len(data_packets) > 1 and all(
            [t.get_api() == data_packets[0].get_api()
             and t.get_sub_api() == data_packets[0].get_sub_api()
             and t.get_station_information().get_make() == data_packets[0].get_station_information().get_make()
             and t.get_station_information().get_model() == data_packets[0].get_station_information().get_model()
             and t.get_station_information().get_os() == data_packets[0].get_station_information().get_os()
             and t.get_station_information().get_os_version()
             == data_packets[0].get_station_information().get_os_version()
             and t.get_station_information().get_app_version()
             == data_packets[0].get_station_information().get_app_version()
             and t.get_station_information().get_is_private()
             == data_packets[0].get_station_information().get_is_private()
             and t.get_packet_duration_s() == data_packets[0].get_packet_duration_s()
             for t in data_packets])):
        return True
    print("WARNING: Metadata in packets has changed; this may indicate a change in the station.")
    return False


# todo add event streams?
class StationMetadata:
    """
    A container for all the packet metadata consistent across all packets
    Properties:
        api: float, api version
        sub_api: float, sub api version
        make: str, station make
        model: str, station model
        os: str, station OS
        os_version: str, station OS version
        app: str, station app
        app_version: str, station app version
        is_private: bool, is station data private
        packet_duration_s: float, duration of the packet in seconds
    """

    def __init__(
        self,
        app: str,
        packet: Optional[WrappedRedvoxPacketM] = None
    ):
        """
        initialize the metadata
        :param app: app name
        :param packet: Optional WrappedRedvoxPacketM to read data from
        """
        self.app = app
        self.other_metadata = {}
        if packet:
            self.api = packet.get_api()
            self.sub_api = packet.get_sub_api()
            self.make = packet.get_station_information().get_make()
            self.model = packet.get_station_information().get_model()
            self.os = packet.get_station_information().get_os()
            self.os_version = packet.get_station_information().get_os_version()
            self.app_version = packet.get_station_information().get_app_version()
            self.is_private = packet.get_station_information().get_is_private()
            self.packet_duration_s = packet.get_packet_duration_s()
        else:
            self.api = np.nan
            self.sub_api = np.nan
            self.make = ""
            self.model = ""
            self.os = ""
            self.os_version = ""
            self.app_version = ""
            self.is_private = False
            self.packet_duration_s = np.nan

    def validate_metadata(self, other_metadata: "StationMetadata") -> bool:
        """
        :param other_metadata: another StationMetadata object to compare
        :return: True if other_metadata is equal to the calling metadata
        """
        return self.app == other_metadata.app \
            and self.api == other_metadata.api \
            and self.sub_api == other_metadata.sub_api \
            and self.make == other_metadata.make \
            and self.model == other_metadata.model \
            and self.os == other_metadata.os \
            and self.os_version == other_metadata.os_version \
            and self.app_version == other_metadata.app_version \
            and self.is_private == other_metadata.is_private \
            and self.packet_duration_s == other_metadata.packet_duration_s


class StationPacketMetadata:
    """
    A container for all the packet metadata that isn't consistent across all packets
    Properties:
        packet_start_mach_timestamp: float, machine timestamp of packet start in microseconds since epoch UTC
        packet_end_mach_timestamp: float, machine timestamp of packet end in microseconds since epoch UTC
        packet_start_os_timestamp: float, os timestamp of packet start in microseconds since epoch UTC
        packet_end_os_timestamp: float, os timestamp of packet end in microseconds since epoch UTC
        timing_info_score: float, quality of timing information
        other_metadata: dict str: str, other metadata from the packet
    """

    def __init__(
            self,
            packet: Optional[WrappedRedvoxPacketM] = None
    ):
        """
        initialize the metadata
        :param packet: Optional WrappedRedvoxPacketM to read data from
        """
        self.other_metadata = {}
        if packet:
            self.packet_start_mach_timestamp = packet.get_timing_information().get_packet_start_mach_timestamp()
            self.packet_end_mach_timestamp = packet.get_timing_information().get_packet_end_mach_timestamp()
            self.packet_start_os_timestamp = packet.get_timing_information().get_packet_start_os_timestamp()
            self.packet_end_os_timestamp = packet.get_timing_information().get_packet_end_os_timestamp()
            self.timing_info_score = packet.get_timing_information().get_score()
        else:
            self.packet_start_mach_timestamp = np.nan
            self.packet_end_mach_timestamp = np.nan
            self.packet_start_os_timestamp = np.nan
            self.packet_end_os_timestamp = np.nan
            self.timing_info_score = np.nan

    def update_timestamps(self, om: OffsetModel):
        """
        updates the timestamps in the metadata by adding delta microseconds
            negative delta values move timestamps backwards in time.
        :param om: OffsetModel to apply to data
        # :param delta: optional microseconds to add
        """
        self.packet_start_mach_timestamp = om.update_time(self.packet_start_mach_timestamp)
        self.packet_end_mach_timestamp = om.update_time(self.packet_end_mach_timestamp)
        self.packet_start_os_timestamp = om.update_time(self.packet_start_os_timestamp)
        self.packet_end_os_timestamp = om.update_time(self.packet_end_os_timestamp)
