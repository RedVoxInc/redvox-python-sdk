"""
Defines generic station metadata for API-independent analysis
all timestamps are floats in microseconds unless otherwise stated
"""
from dataclasses import dataclass
from typing import Tuple

from redvox.common.offset_model import OffsetModel
from redvox.api1000.wrapped_redvox_packet import (
    station_information as si,
    timing_information as ti,
    # event_streams as es,
)


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
    A container for all the packet metadata that doesn't fit in a sensor
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
        packet_start_mach_timestamp: float, machine timestamp of packet start in microseconds since epoch UTC
        packet_end_mach_timestamp: float, machine timestamp of packet end in microseconds since epoch UTC
        packet_start_os_timestamp: float, os timestamp of packet start in microseconds since epoch UTC
        packet_end_os_timestamp: float, os timestamp of packet end in microseconds since epoch UTC
        timing_info_score: float, quality of timing information
    """

    def __init__(
        self,
        api: float,
        sub_api: float,
        station_info: si.StationInformation,
        app: str,
        timing_info: ti.TimingInformation,
    ):
        """
        initialize the metadata
        :param api: api version
        :param sub_api: sub api version
        :param station_info: station information
        :param app: app name
        :param timing_info: timing information
        """
        self.api = api
        self.sub_api = sub_api
        self.make = station_info.get_make()
        self.model = station_info.get_model()
        self.os = station_info.get_os()
        self.os_version = station_info.get_os_version()
        self.app = app
        self.app_version = station_info.get_app_version()
        self.is_private = station_info.get_is_private()
        self.packet_start_mach_timestamp = timing_info.get_packet_start_mach_timestamp()
        self.packet_end_mach_timestamp = timing_info.get_packet_end_mach_timestamp()
        self.packet_start_os_timestamp = timing_info.get_packet_start_os_timestamp()
        self.packet_end_os_timestamp = timing_info.get_packet_end_os_timestamp()
        self.timing_info_score = timing_info.get_score()

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
