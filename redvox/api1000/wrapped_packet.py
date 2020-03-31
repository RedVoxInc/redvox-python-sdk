"""
This module provides a high level API for creating, reading, and editing RedVox compliant API 1000 files.
"""

import os.path
from typing import Optional

import numpy as np

import redvox.api1000.common as common
import redvox.api1000.device_information as _device_information
import redvox.api1000.errors as errors
import redvox.api1000.location_channel as _location_channel
import redvox.api1000.microphone_channel as _microphone_channel
import redvox.api1000.packet_information as _packet_information
import redvox.api1000.single_channel as _single_channel
import redvox.api1000.server_information as _server_information
import redvox.api1000.timing_information as _timing_information
import redvox.api1000.xyz_channel as _xyz_channel
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2
import redvox.api1000.user_information as _user_information


class WrappedRedvoxPacketApi1000(common.ProtoBase):
    def __init__(self, redvox_proto: redvox_api_1000_pb2.RedvoxPacket1000):
        super().__init__(redvox_proto)

        self._user_information: _user_information.UserInformation = _user_information.UserInformation(
            redvox_proto.user_information)

        self._device_information: _device_information.DeviceInformation = _device_information.DeviceInformation(
            redvox_proto.device_information)

        self._packet_information: _packet_information.PacketInformation = _packet_information.PacketInformation(
            redvox_proto.packet_information)

        self._timing_information: _timing_information.TimingInformation = _timing_information.TimingInformation(
            redvox_proto.timing_information)

        self._server_information: _server_information.ServerInformation = _server_information.ServerInformation(
            redvox_proto.server_information)

    @staticmethod
    def new() -> 'WrappedRedvoxPacketApi1000':
        return WrappedRedvoxPacketApi1000(redvox_api_1000_pb2.RedvoxPacket1000())

    @staticmethod
    def from_compressed_bytes(data: bytes) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(data, bytes):
            raise errors.WrappedRedvoxPacketApi1000Error(f"Expected bytes, but instead received {type(data)}")

        uncompressed_data: bytes = common.lz4_decompress(data)
        proto: redvox_api_1000_pb2.RedvoxPacket1000 = redvox_api_1000_pb2.RedvoxPacket1000()
        proto.ParseFromString(uncompressed_data)
        return WrappedRedvoxPacketApi1000(proto)

    @staticmethod
    def from_compressed_path(rdvxz_path: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(rdvxz_path, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"Expected a string, but instead received {type(rdvxz_path)}")

        if not os.path.isfile(rdvxz_path):
            raise errors.WrappedRedvoxPacketApi1000Error(f"Path to file={rdvxz_path} does not exist.")

        with open(rdvxz_path, "rb") as rdvxz_in:
            compressed_bytes: bytes = rdvxz_in.read()
            return WrappedRedvoxPacketApi1000.from_compressed_bytes(compressed_bytes)

    def default_filename(self, extension: Optional[str] = None) -> str:
        device_id: str = self.get_device_id()
        device_id_len: int = len(device_id)
        if device_id_len < 10:
            device_id = f"{'0' * (10 - device_id_len)}{device_id}"
        ts_s: int = round(self.get_packet_start_ts_us_mach() / 1_000_000.0)

        filename: str = f"{device_id}_{ts_s}_m"

        if extension is not None:
            filename = f"{filename}.{extension}"

        return filename

    def write_compressed_to_file(self, base_dir: str, filename: Optional[str] = None):
        if filename is None:
            filename: str = self.default_filename(".rdvxz")

        if not os.path.isdir(base_dir):
            raise errors.WrappedRedvoxPacketApi1000Error(f"Base directory={base_dir} does not exist.")

        with open(os.path.join(base_dir, filename), "wb") as compressed_out:
            compressed_out.write(self.as_compressed_bytes())

    def write_json_to_file(self, base_dir: str, filename: Optional[str] = None):
        if filename is None:
            filename: str = self.default_filename(".json")

        if not os.path.isdir(base_dir):
            raise errors.WrappedRedvoxPacketApi1000Error(f"Base directory={base_dir} does not exist.")

        with open(os.path.join(base_dir, filename), "w") as json_out:
            json_out.write(self.as_json())

    # Top-level packet fields
    def get_api(self) -> int:
        return self._proto.api

    def set_api(self, api: int) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(api, int):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a {type(api)}={api} was "
                                                         f"provided")
        self._proto.api = api
        return self

    def get_user_information(self) -> _user_information.UserInformation:
        pass

    def set_user_information(self) -> 'WrappedRedvoxPacketApi1000':
        pass

    def new_user_information(self) -> _user_information.UserInformation:
        pass

    def get_device_information(self) -> _device_information.DeviceInformation:
        pass

    def set_device_information(self) -> 'WrappedRedvoxPacketApi1000':
        pass

    def new_device_information(self) -> _device_information.DeviceInformation:
        pass

    def get_packet_information(self) -> _packet_information.PacketInformation:
        pass

    def set_packet_information(self) -> 'WrappedRedvoxPacketApi1000':
        pass

    def new_packet_information(self) -> _packet_information.PacketInformation:
        pass

    def get_server_information(self) -> _server_information.ServerInformation:
        pass

    def set_server_information(self) -> 'WrappedRedvoxPacketApi1000':
        pass

    def new_server_information(self) -> _server_information.ServerInformation:
        pass

    # Channels
