"""
Defines generic station metadata for API-independent analysis
all timestamps are floats in microseconds unless otherwise stated
"""
from dataclasses import dataclass
from typing import Tuple

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
        app_settings: AppSettings
        service_urls: ServiceUrls
        timing_information: TimingInformation
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
        self.app_settings = station_info.get_app_settings()
        self.service_urls = station_info.get_service_urls()
        self.timing_information = timing_info

    def update_timestamps(self, delta: float):
        """
        updates the timestamps in the metadata by adding delta microseconds
            negative delta values move timestamps backwards in time.
        :param delta: optional microseconds to add
        """
        self.timing_information.set_packet_start_mach_timestamp(
            self.timing_information.get_packet_start_mach_timestamp() + delta
        )
        self.timing_information.set_packet_end_mach_timestamp(
            self.timing_information.get_packet_end_mach_timestamp() + delta
        )
        self.timing_information.set_app_start_mach_timestamp(
            self.timing_information.get_app_start_mach_timestamp() + delta
        )
