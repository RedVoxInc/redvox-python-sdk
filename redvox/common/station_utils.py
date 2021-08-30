"""
Defines generic station metadata for API-independent analysis
all timestamps are floats in microseconds unless otherwise stated
"""
from dataclasses import dataclass
from typing import Tuple, Optional, List, Dict

import numpy as np

from redvox.common.offset_model import OffsetModel
from redvox.api1000.wrapped_redvox_packet.station_information import OsType
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.common.errors import RedVoxExceptions

# from redvox.api1000.wrapped_redvox_packet import event_streams as es
import redvox.api1000.proto.redvox_api_m_pb2 as api_m


def validate_station_key_list(
    data_packets: List[api_m.RedvoxPacketM], errors: RedVoxExceptions
) -> bool:
    """
    Checks for consistency in the data packets.  Returns False if discrepancies are found.
    If debug is True, will output the discrepancies.

    :param data_packets: list of WrappedRedvoxPacketM to look at
    :param errors: RedVoxExceptions detailing errors found while validating
    :return: True if no discrepancies found.  False otherwise
    """
    my_errors = RedVoxExceptions("StationKeyValidation")
    if len(data_packets) < 2:
        return True
    j: np.ndarray = np.transpose(
        [
            [
                t.station_information.id,
                t.station_information.uuid,
                t.timing_information.app_start_mach_timestamp,
                t.api,
                t.sub_api,
                t.station_information.make,
                t.station_information.model,
                t.station_information.os,
                t.station_information.os_version,
                t.station_information.app_version,
                t.station_information.is_private,
                len(t.sensors.audio.samples.values) / t.sensors.audio.sample_rate,
                ]
            for t in data_packets
        ]
    )

    k: Dict[str, np.ndarray] = {
        "ids": j[0],
        "uuids": j[1],
        "station_start_times": j[2],
        "apis": j[3],
        "sub_apis": j[4],
        "makes": j[5],
        "models": j[6],
        "os": j[7],
        "os_versions": j[8],
        "app_versions": j[9],
        "privates": j[10],
        "durations": j[11],
    }

    for key, value in k.items():
        result = np.unique(value)
        if len(result) > 1:
            my_errors.append(
                f"WARNING: {data_packets[0].station_information.id} "
                f"{key} contains multiple unique values: {result}.\n"
                "Please update your query to focus on one of these values."
            )

    if my_errors.get_num_errors() > 0:
        errors.extend_error(my_errors)
        return False

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
        """
        :return: the key as a tuple
        """
        return self.id, self.uuid, self.start_timestamp_micros

    def check_key(self, station_id: Optional[str] = None, station_uuid: Optional[str] = None,
                  start_timestamp: Optional[float] = None) -> bool:
        """
        check if the key has the values specified.  If the parameter is None, any value will match.
        Note that NAN is a valid value for start_timestamps, but any station with start_timestamp = NAN
        will not match any value, including another NAN.

        :param station_id: station id, default None
        :param station_uuid: station uuid, default None
        :param start_timestamp: station start timestamp in microseconds since UTC epoch, default None
        :return: True if all parameters match key values
        """
        if station_id is not None and station_id != self.id:
            # print(f"Id {station_id} does not equal station's id: {self.id}")
            return False
        if station_uuid is not None and station_uuid != self.uuid:
            # print(f"Uuid {station_uuid} does not equal station's uuid: {self.uuid}")
            return False
        if start_timestamp is not None and (start_timestamp != self.start_timestamp_micros
                                            or np.isnan(start_timestamp) or np.isnan(self.start_timestamp_micros)):
            # print(f"Start timestamp {start_timestamp} does not equal station's "
            #       f"start timestamp: {self.start_timestamp_micros}")
            return False
        return True

    def compare_key(self, other_key: "StationKey") -> bool:
        """
        compare key to another station's key

        :param other_key: another station's key
        :return: True if the keys match
        """
        return self.check_key(other_key.id, other_key.uuid, other_key.start_timestamp_micros)


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

    def __init__(self, app: str, packet: Optional[api_m.RedvoxPacketM] = None):
        """
        initialize the metadata

        :param app: app name
        :param packet: Optional WrappedRedvoxPacketM to read data from
        """
        self.app = app
        self.other_metadata = {}
        if packet:
            self.api = packet.api
            self.sub_api = packet.sub_api
            self.make = packet.station_information.make
            self.model = packet.station_information.model
            self.os: OsType = OsType(packet.station_information.os)
            self.os_version = packet.station_information.os_version
            self.app_version = packet.station_information.app_version
            self.is_private = packet.station_information.is_private
            self.packet_duration_s = (
                    len(packet.sensors.audio.samples.values)
                    / packet.sensors.audio.sample_rate
            )
            self.station_description = packet.station_information.description
        else:
            self.api = np.nan
            self.sub_api = np.nan
            self.make = ""
            self.model = ""
            self.os: OsType = OsType["UNKNOWN_OS"]
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
        return (
                self.app == other_metadata.app
                and self.api == other_metadata.api
                and self.sub_api == other_metadata.sub_api
                and self.make == other_metadata.make
                and self.model == other_metadata.model
                and self.os == other_metadata.os
                and self.os_version == other_metadata.os_version
                and self.app_version == other_metadata.app_version
                and self.is_private == other_metadata.is_private
                and self.packet_duration_s == other_metadata.packet_duration_s
                and self.station_description == other_metadata.station_description
        )

    def as_dict(self) -> dict:
        """
        :return: dictionary representation of the metadata
        """
        return {
            "app": self.app,
            "api": self.api,
            "sub_api": self.sub_api,
            "make": self.make,
            "model": self.model,
            "os": self.os.name,
            "os_version": self.os_version,
            "app_version": self.app_version,
            "is_private": self.is_private,
            "packet_duration_s": self.packet_duration_s,
            "station_description": self.station_description,
            "other_metadata": self.other_metadata
        }

    @staticmethod
    def from_dict(md_dict: dict) -> "StationMetadata":
        """
        :param md_dict: metadata dictionary
        :return: StationMetadata from dictionary
        """
        result = StationMetadata(md_dict["app"])
        result.api = md_dict["api"]
        result.sub_api = md_dict["sub_api"]
        result.make = md_dict["make"]
        result.model = md_dict["model"]
        result.os = OsType[md_dict["os"]]
        result.os_version = md_dict["os_version"]
        result.app_version = md_dict["app_version"]
        result.is_private = md_dict["is_private"]
        result.packet_duration_s = md_dict["packet_duration_s"]
        result.station_description = md_dict["station_description"]
        result.other_metadata = md_dict["other_metadata"]
        return result


class StationMetadataWrapped:
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

    def __init__(self, app: str, packet: Optional[WrappedRedvoxPacketM] = None):
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
            self.station_description = (
                packet.get_station_information().get_description()
            )
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

    def validate_metadata(self, other_metadata: "StationMetadataWrapped") -> bool:
        """
        :param other_metadata: another StationMetadata object to compare
        :return: True if other_metadata is equal to the calling metadata
        """
        return (
                self.app == other_metadata.app
                and self.api == other_metadata.api
                and self.sub_api == other_metadata.sub_api
                and self.make == other_metadata.make
                and self.model == other_metadata.model
                and self.os == other_metadata.os
                and self.os_version == other_metadata.os_version
                and self.app_version == other_metadata.app_version
                and self.is_private == other_metadata.is_private
                and self.packet_duration_s == other_metadata.packet_duration_s
                and self.station_description == other_metadata.station_description
        )


class StationPacketMetadata:
    """
    A container for all the packet metadata that isn't consistent across all packets

    Properties:
        packet_start_mach_timestamp: float, machine timestamp of packet start in microseconds since epoch UTC

        packet_end_mach_timestamp: float, machine timestamp of packet end in microseconds since epoch UTC

        packet_start_os_timestamp: float, os timestamp of packet start in microseconds since epoch UTC

        packet_end_os_timestamp: float, os timestamp of packet end in microseconds since epoch UTC

        server_packet_received_timestamp: float, timestamp from server when packet was received in
        microseconds since epoch UTC

        timing_info_score: float, quality of timing information

        other_metadata: dict, str: str of other metadata from the packet
    """

    def __init__(self, packet: Optional[api_m.RedvoxPacketM] = None):
        """
        initialize the metadata

        :param packet: Optional WrappedRedvoxPacketM to read data from
        """
        self.other_metadata = {}
        if packet:
            self.packet_start_mach_timestamp = (
                packet.timing_information.packet_start_mach_timestamp
            )
            self.packet_end_mach_timestamp = (
                packet.timing_information.packet_end_mach_timestamp
            )
            self.packet_start_os_timestamp = (
                packet.timing_information.packet_start_os_timestamp
            )
            self.packet_end_os_timestamp = (
                packet.timing_information.packet_end_os_timestamp
            )
            self.server_packet_receive_timestamp = packet.timing_information.server_acquisition_arrival_timestamp
            self.timing_info_score = packet.timing_information.score
        else:
            self.packet_start_mach_timestamp = np.nan
            self.packet_end_mach_timestamp = np.nan
            self.packet_start_os_timestamp = np.nan
            self.packet_end_os_timestamp = np.nan
            self.server_packet_receive_timestamp = np.nan
            self.timing_info_score = np.nan

    def update_timestamps(self, om: OffsetModel, use_model_function: bool = True):
        """
        updates the timestamps in the metadata using the offset model

        :param om: OffsetModel to apply to data
        :param use_model_function: if True, use the offset model's correction function to correct time,
                                    otherwise use best offset (model's intercept value).  default True
        """
        self.packet_start_mach_timestamp = om.update_time(self.packet_start_mach_timestamp, use_model_function)
        self.packet_end_mach_timestamp = om.update_time(self.packet_end_mach_timestamp, use_model_function)
        self.packet_start_os_timestamp = om.update_time(self.packet_start_os_timestamp, use_model_function)
        self.packet_end_os_timestamp = om.update_time(self.packet_end_os_timestamp, use_model_function)

    @staticmethod
    def from_dict(pmd_dict: dict) -> "StationPacketMetadata":
        """
        :param pmd_dict: dictionary with StationPacketMetadata
        :return: StationPacketMetadata from dictionary
        """
        result = StationPacketMetadata()
        result.other_metadata = pmd_dict["other_metadata"]
        result.packet_start_mach_timestamp = pmd_dict["packet_start_mach_timestamp"]
        result.packet_end_mach_timestamp = pmd_dict["packet_end_mach_timestamp"]
        result.packet_start_os_timestamp = pmd_dict["packet_start_os_timestamp"]
        result.packet_end_os_timestamp = pmd_dict["packet_end_os_timestamp"]
        result.server_packet_receive_timestamp = pmd_dict["server_packet_receive_timestamp"]
        result.timing_info_score = pmd_dict["timing_info_score"]
        return result


class StationPacketMetadataWrapped:
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

    def __init__(self, packet: Optional[WrappedRedvoxPacketM] = None):
        """
        initialize the metadata

        :param packet: Optional WrappedRedvoxPacketM to read data from
        """
        self.other_metadata = {}
        if packet:
            self.packet_start_mach_timestamp = (
                packet.get_timing_information().get_packet_start_mach_timestamp()
            )
            self.packet_end_mach_timestamp = (
                packet.get_timing_information().get_packet_end_mach_timestamp()
            )
            self.packet_start_os_timestamp = (
                packet.get_timing_information().get_packet_start_os_timestamp()
            )
            self.packet_end_os_timestamp = (
                packet.get_timing_information().get_packet_end_os_timestamp()
            )
            self.timing_info_score = packet.get_timing_information().get_score()
        else:
            self.packet_start_mach_timestamp = np.nan
            self.packet_end_mach_timestamp = np.nan
            self.packet_start_os_timestamp = np.nan
            self.packet_end_os_timestamp = np.nan
            self.timing_info_score = np.nan

    def update_timestamps(self, om: OffsetModel, use_model_function: bool = True):
        """
        updates the timestamps in the metadata using the offset model

        :param om: OffsetModel to apply to data
        :param use_model_function: if True, use the offset model's correction function to correct time,
                                    otherwise use best offset (model's intercept value).  default True
        """
        self.packet_start_mach_timestamp = om.update_time(self.packet_start_mach_timestamp, use_model_function)
        self.packet_end_mach_timestamp = om.update_time(self.packet_end_mach_timestamp, use_model_function)
        self.packet_start_os_timestamp = om.update_time(self.packet_start_os_timestamp, use_model_function)
        self.packet_end_os_timestamp = om.update_time(self.packet_end_os_timestamp, use_model_function)
