"""
Defines generic station metadata for API-independent analysis
all timestamps are floats in microseconds unless otherwise stated
"""
from dataclasses import dataclass
from typing import Tuple, Optional, List

import numpy as np

from redvox.common.offset_model import OffsetModel
from redvox.api1000.wrapped_redvox_packet.station_information import OsType
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
# from redvox.api1000.wrapped_redvox_packet import event_streams as es


def validate_station_key_list(data_packets: List[WrappedRedvoxPacketM], debug: bool = False) -> bool:
    """
    Checks for consistency in the data packets.  Returns False if discrepancies are found.
    If debug is True, will output the discrepancies.
    :param data_packets: list of WrappedRedvoxPacketM to look at
    :param debug: bool, if True, output any discrepancies found, default False
    :return: True if no discrepancies found.  False otherwise
    """
    if len(data_packets) < 2:
        return True
    k = np.transpose([[t.get_station_information().get_id(),
                       t.get_station_information().get_uuid(),
                       t.get_timing_information().get_app_start_mach_timestamp(),
                       t.get_api(),
                       t.get_sub_api(),
                       t.get_station_information().get_make(),
                       t.get_station_information().get_model(),
                       t.get_station_information().get_os().value,
                       t.get_station_information().get_os_version(),
                       t.get_station_information().get_app_version(),
                       t.get_station_information().get_is_private(),
                       t.get_packet_duration_s()] for t in data_packets])

    k = {"ids": k[0], "uuids": k[1], "station_start_times": k[2], "apis": k[3],
         "sub_apis": k[4], "makes": k[5], "models": k[6], "os": k[7], "os_versions": k[8],
         "app_versions": k[9], "privates": k[10], "durations": k[11]}

    for key, value in k.items():
        result = np.unique(value)
        if len(result) > 1:
            if debug:
                print(f"WARNING: {data_packets[0].get_station_information().get_id()} "
                      f"{key} contains multiple unique values: {result}.")
                print("Current solution is to alter your query to omit or focus on this station.")
            return False  # stop processing, one bad key is enough

    return True  # if here, everything is consistent


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


# todo add event streams?
class StationMetadata:
    """
    A container for all the packet metadata consistent across all packets
    Properties:
        api: float, api version, default np.nan
        sub_api: float, sub api version, default np.nan
        make: str, station make, default empty string
        model: str, station model, default empty string
        os: OsType enum, station OS, default OsType.UNKNOWN_OS
        os_version: str, station OS version, default empty string
        app: str, station app, default empty string
        app_version: str, station app version, default empty string
        is_private: bool, is station data private, default False
        packet_duration_s: float, duration of the packet in seconds, default np.nan
        station_description: str, description of the station, default empty string
        other_metadata: dict, str: str of other metadata from the packet, default empty list
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
            self.station_description = packet.get_station_information().get_description()
        else:
            self.api = np.nan
            self.sub_api = np.nan
            self.make = ""
            self.model = ""
            self.os = OsType.UNKNOWN_OS
            self.os_version = ""
            self.app_version = ""
            self.is_private = False
            self.packet_duration_s = np.nan
            self.station_description = ""

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
            and self.packet_duration_s == other_metadata.packet_duration_s \
            and self.station_description == other_metadata.station_description


class StationPacketMetadata:
    """
    A container for all the packet metadata that isn't consistent across all packets
    Properties:
        packet_start_mach_timestamp: float, machine timestamp of packet start in microseconds since epoch UTC
        packet_end_mach_timestamp: float, machine timestamp of packet end in microseconds since epoch UTC
        packet_start_os_timestamp: float, os timestamp of packet start in microseconds since epoch UTC
        packet_end_os_timestamp: float, os timestamp of packet end in microseconds since epoch UTC
        timing_info_score: float, quality of timing information
        other_metadata: dict, str: str of other metadata from the packet
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
        updates the timestamps in the metadata using the offset model
        :param om: OffsetModel to apply to data
        """
        self.packet_start_mach_timestamp = om.update_time(self.packet_start_mach_timestamp)
        self.packet_end_mach_timestamp = om.update_time(self.packet_end_mach_timestamp)
        self.packet_start_os_timestamp = om.update_time(self.packet_start_os_timestamp)
        self.packet_end_os_timestamp = om.update_time(self.packet_end_os_timestamp)
