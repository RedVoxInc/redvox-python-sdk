"""
This module provides a high level API for creating, reading, and editing RedVox compliant API 1000 files.
"""

import os.path
from typing import Optional, List
from google.protobuf import json_format

import redvox.api1000.common.lz4
import redvox.api1000.common.typing
import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
# import redvox.api1000.common.common as common
import redvox.api1000.common.generic
import redvox.api1000.wrapped_redvox_packet.sensors.sensors as _sensors
import redvox.api1000.wrapped_redvox_packet.station_information as _station_information
import redvox.api1000.wrapped_redvox_packet.timing_information as _timing_information


class WrappedRedvoxPacketM(
    redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM]):
    def __init__(self, redvox_proto: redvox_api_m_pb2.RedvoxPacketM):
        super().__init__(redvox_proto)

        self._station_information: _station_information.StationInformation = _station_information.StationInformation(
            redvox_proto.station_information)

        self._timing_information: _timing_information.TimingInformation = _timing_information.TimingInformation(
            redvox_proto.timing_information)

        self._sensors: _sensors.Sensors = _sensors.Sensors(redvox_proto.sensors)

    @staticmethod
    def new() -> 'WrappedRedvoxPacketM':
        """
        Returns a new default instance of a WrappedRedvoxPacketApi1000.
        :return: A new default instance of a WrappedRedvoxPacketApi1000.
        """
        return WrappedRedvoxPacketM(redvox_api_m_pb2.RedvoxPacketM())

    @staticmethod
    def from_compressed_bytes(data: bytes) -> 'WrappedRedvoxPacketM':
        """
        Deserializes the byte content of an API M encoded .rdvxz file.
        :param data: The compressed bytes to deserialize.
        :return: An instance of a WrappedRedvoxPacketAPi1000.
        """
        redvox.api1000.common.typing.check_type(data, [bytes])
        uncompressed_data: bytes = redvox.api1000.common.lz4.decompress(data)
        proto: redvox_api_m_pb2.RedvoxPacketM = redvox_api_m_pb2.RedvoxPacketM()
        proto.ParseFromString(uncompressed_data)
        return WrappedRedvoxPacketM(proto)

    @staticmethod
    def from_compressed_path(rdvxm_path: str) -> 'WrappedRedvoxPacketM':
        """
        Deserialize an API M encoded .rdvxz file from the specified file system path.
        :param rdvxm_path: Path to the API M encoded file.
        :return: An instance of a WrappedRedvoxPacketApi1000.
        """
        redvox.api1000.common.typing.check_type(rdvxm_path, [str])

        if not os.path.isfile(rdvxm_path):
            raise errors.WrappedRedvoxPacketMError(f"Path to file={rdvxm_path} does not exist.")

        with open(rdvxm_path, "rb") as rdvxz_in:
            compressed_bytes: bytes = rdvxz_in.read()
            return WrappedRedvoxPacketM.from_compressed_bytes(compressed_bytes)

    @staticmethod
    def from_json(json_str: str) -> 'WrappedRedvoxPacketM':
        """
        read json packet representing an API 1000 packet
        :param json_str: contains the json representing the packet
        :return: An instance of a WrappedRedvoxPacketM
        """
        return WrappedRedvoxPacketM(json_format.Parse(json_str, redvox_api_m_pb2.RedvoxPacketM()))

    @staticmethod
    def from_json_path(json_path: str) -> 'WrappedRedvoxPacketM':
        """
        read json from a file representing an api 1000 packet
        :param json_path: the path to the file to read
        :return: wrapped redvox packet api 1000
        """
        with open(json_path, "r") as json_in:
            return WrappedRedvoxPacketM.from_json(json_in.read())

    def default_filename(self, extension: Optional[str] = None) -> str:
        """
        Returns the default filename for a given packet.
        :param extension: An (optional) file extension to add to the default file name.
        :return: The default filename for this packet.
        """
        station_id: str = self.get_station_information().get_id()
        station_id_len: int = len(station_id)
        if station_id_len < 10:
            station_id = f"{'0' * (10 - station_id_len)}{station_id}"
        timestamp: int = round(self.get_timing_information().get_packet_start_mach_timestamp())

        filename: str = f"{station_id}_{timestamp}"

        if extension is not None:
            filename = f"{filename}.{extension}"

        return filename

    def write_compressed_to_file(self, base_dir: str, filename: Optional[str] = None) -> str:
        if filename is None:
            filename = self.default_filename("rdvxm")

        if not os.path.isdir(base_dir):
            raise errors.WrappedRedvoxPacketMError(f"Base directory={base_dir} does not exist.")

        out_path: str = os.path.join(base_dir, filename)
        with open(out_path, "wb") as compressed_out:
            compressed_out.write(self.as_compressed_bytes())

        return out_path

    def write_json_to_file(self, base_dir: str, filename: Optional[str] = None) -> str:
        if filename is None:
            filename = self.default_filename("m.json")

        if not os.path.isdir(base_dir):
            raise errors.WrappedRedvoxPacketMError(f"Base directory={base_dir} does not exist.")

        out_path: str = os.path.join(base_dir, filename)
        with open(out_path, "w") as json_out:
            json_out.write(self.as_json())

        return out_path

    def validate(self) -> List[str]:
        return validate_wrapped_packet(self)

    # Top-level packet fields
    def get_api(self) -> float:
        return self._proto.api

    def set_api(self, api: float) -> 'WrappedRedvoxPacketM':
        redvox.api1000.common.typing.check_type(api, [int, float])
        self._proto.api = api
        return self

    def get_station_information(self) -> _station_information.StationInformation:
        return self._station_information

    def get_timing_information(self) -> _timing_information.TimingInformation:
        return self._timing_information

    def get_sensors(self) -> _sensors.Sensors:
        return self._sensors

    def update_timestamps(self, delta_offset: float = None) -> 'WrappedRedvoxPacketM':
        if delta_offset is None:
            delta_offset = self.get_timing_information().get_best_offset()
        redvox.api1000.common.typing.check_type(delta_offset, [float])
        # create new wrapped packet to hold changed data
        updated = WrappedRedvoxPacketM(self.get_proto())
        if self.get_proto().HasField("timing_information"):
            # update timing information timestamps
            updated.get_timing_information().set_packet_start_mach_timestamp(
                self.get_timing_information().get_packet_start_mach_timestamp() + delta_offset)
            updated.get_timing_information().set_packet_end_mach_timestamp(
                self.get_timing_information().get_packet_end_mach_timestamp() + delta_offset)
            updated.get_timing_information().set_packet_start_os_timestamp(
                self.get_timing_information().get_packet_start_os_timestamp() + delta_offset)
            updated.get_timing_information().set_packet_end_os_timestamp(
                self.get_timing_information().get_packet_end_os_timestamp() + delta_offset)
            updated.get_timing_information().set_app_start_mach_timestamp(
                self.get_timing_information().get_app_start_mach_timestamp() + delta_offset)
        if self.get_sensors().get_proto().HasField("audio"):
            # update audio first sample timestamp
            updated.get_sensors().get_audio().set_first_sample_timestamp(
                self.get_sensors().get_audio().get_first_sample_timestamp() + delta_offset)
        # if self.get_sensors().get_proto().HasField("compressed_audio"):
            # update compressed audio first sample timestamp
        # update timestamp payloads
        if self.get_station_information().get_station_metrics().get_proto().HasField("timestamps"):
            updated.get_station_information().get_station_metrics().get_timestamps().set_timestamps(
                self.get_station_information().get_station_metrics().get_timestamps().get_timestamps() + delta_offset,
                True)
        if self.get_sensors().get_accelerometer().get_proto().HasField("timestamps"):
            updated.get_sensors().get_accelerometer().get_timestamps().set_timestamps(
                self.get_sensors().get_accelerometer().get_timestamps().get_timestamps() + delta_offset, True)
        if self.get_sensors().get_ambient_temperature().get_proto().HasField("timestamps"):
            updated.get_sensors().get_ambient_temperature().get_timestamps().set_timestamps(
                self.get_sensors().get_ambient_temperature().get_timestamps().get_timestamps() + delta_offset, True)
        if self.get_sensors().get_gravity().get_proto().HasField("timestamps"):
            updated.get_sensors().get_gravity().get_timestamps().set_timestamps(
                self.get_sensors().get_gravity().get_timestamps().get_timestamps() + delta_offset, True)
        if self.get_sensors().get_gyroscope().get_proto().HasField("timestamps"):
            updated.get_sensors().get_gyroscope().get_timestamps().set_timestamps(
                self.get_sensors().get_gyroscope().get_timestamps().get_timestamps() + delta_offset, True)
        if self.get_sensors().get_image().get_proto().HasField("timestamps"):
            updated.get_sensors().get_image().get_timestamps().set_timestamps(
                self.get_sensors().get_image().get_timestamps().get_timestamps() + delta_offset, True)
        if self.get_sensors().get_light().get_proto().HasField("timestamps"):
            updated.get_sensors().get_light().get_timestamps().set_timestamps(
                self.get_sensors().get_light().get_timestamps().get_timestamps() + delta_offset, True)
        if self.get_sensors().get_linear_acceleration().get_proto().HasField("timestamps"):
            updated.get_sensors().get_linear_acceleration().get_timestamps().set_timestamps(
                self.get_sensors().get_linear_acceleration().get_timestamps().get_timestamps() + delta_offset, True)
        if self.get_sensors().get_location().get_proto().HasField("timestamps"):
            updated.get_sensors().get_location().get_timestamps().set_timestamps(
                self.get_sensors().get_location().get_timestamps().get_timestamps() + delta_offset, True)
        if self.get_sensors().get_magnetometer().get_proto().HasField("timestamps"):
            updated.get_sensors().get_magnetometer().get_timestamps().set_timestamps(
                self.get_sensors().get_magnetometer().get_timestamps().get_timestamps() + delta_offset, True)
        if self.get_sensors().get_orientation().get_proto().HasField("timestamps"):
            updated.get_sensors().get_orientation().get_timestamps().set_timestamps(
                self.get_sensors().get_orientation().get_timestamps().get_timestamps() + delta_offset, True)
        if self.get_sensors().get_pressure().get_proto().HasField("timestamps"):
            updated.get_sensors().get_pressure().get_timestamps().set_timestamps(
                self.get_sensors().get_pressure().get_timestamps().get_timestamps() + delta_offset, True)
        if self.get_sensors().get_proximity().get_proto().HasField("timestamps"):
            updated.get_sensors().get_proximity().get_timestamps().set_timestamps(
                self.get_sensors().get_proximity().get_timestamps().get_timestamps() + delta_offset, True)
        if self.get_sensors().get_relative_humidity().get_proto().HasField("timestamps"):
            updated.get_sensors().get_relative_humidity().get_timestamps().set_timestamps(
                self.get_sensors().get_relative_humidity().get_timestamps().get_timestamps() + delta_offset, True)
        if self.get_sensors().get_rotation_vector().get_proto().HasField("timestamps"):
            updated.get_sensors().get_rotation_vector().get_timestamps().set_timestamps(
                self.get_sensors().get_rotation_vector().get_timestamps().get_timestamps() + delta_offset, True)
        return updated


def validate_wrapped_packet(wrapped_packet: WrappedRedvoxPacketM) -> List[str]:
    errors_list = _station_information.validate_station_information(wrapped_packet.get_station_information())
    errors_list.extend(_timing_information.validate_timing_information(wrapped_packet.get_timing_information()))
    errors_list.extend(_sensors.validate_sensors(wrapped_packet.get_sensors()))
    if wrapped_packet.get_api() != 1000:
        errors_list.append("Wrapped packet api is not 1000")
    return errors_list
