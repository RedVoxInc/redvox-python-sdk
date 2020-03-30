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

    # Server information
    def get_auth_server_url(self) -> str:
        return self._proto.auth_server_url

    def set_auth_server_url(self, auth_server_url: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(auth_server_url, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a "
                                                         f"{type(auth_server_url)}={auth_server_url} was "
                                                         f"provided")

        self._proto.auth_server_url = auth_server_url
        return self

    def get_synch_server_url(self) -> str:
        return self._proto.synch_server_url

    def set_synch_server_url(self, synch_server_url: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(synch_server_url, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a "
                                                         f"{type(synch_server_url)}={synch_server_url} was "
                                                         f"provided")

        self._proto.synch_server_url = synch_server_url
        return self

    def get_acquisition_server_url(self) -> str:
        return self._proto.acquisition_server_url

    def set_acquisition_server_url(self, acquisition_server_url: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(acquisition_server_url, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a "
                                                         f"{type(acquisition_server_url)}={acquisition_server_url} was "
                                                         f"provided")

        self._proto.acquisition_server_url = acquisition_server_url
        return self



    # Channels
    def new_microphone_channel(self) -> _microphone_channel.MicrophoneChannel:

        self.set_microphone_channel(_microphone_channel.MicrophoneChannel.new())

    def has_microphone_channel(self) -> bool:
        return self._proto.HasField("microphone_channel")

    def get_microphone_channel(self) -> _microphone_channel.MicrophoneChannel:
        if not self.has_microphone_channel():
            raise errors.WrappedRedvoxPacketApi1000Error("Packet does not contain a microphone channel")

        return _microphone_channel.MicrophoneChannel(self._proto.microphone_channel)

    def set_microphone_channel(self,
                               microphone_channel: _microphone_channel.MicrophoneChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(microphone_channel, _microphone_channel.MicrophoneChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a MicrophoneChannel is required, but a "
                                                         f"{type(microphone_channel)}={microphone_channel} was "
                                                         f"provided")
        self._proto.microphone_channel.CopyFrom(microphone_channel.get_proto())
        return self

    def has_barometer_channel(self) -> bool:
        return self._proto.HasField("barometer_channel")

    def set_barometer_channel(self, barometer_channel: _single_channel.SingleChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(barometer_channel, _single_channel.SingleChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a SingleChannel is required, but a "
                                                         f"{type(barometer_channel)}={barometer_channel} was "
                                                         f"provided")
        self._proto.barometer_channel.CopyFrom(barometer_channel.get_proto())
        return self

    def has_accelerometer_channel(self) -> bool:
        return self._proto.HasField("accelerometer_channel")

    def set_accelerometer_channel(self, accelerometer_channel: _xyz_channel.XyzChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(accelerometer_channel, _xyz_channel.XyzChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a XyzChannel is required, but a "
                                                         f"{type(accelerometer_channel)}={accelerometer_channel} was "
                                                         f"provided")
        self._proto.accelerometer_channel.CopyFrom(accelerometer_channel.get_proto())
        return self

    def has_gyroscope_channel(self) -> bool:
        return self._proto.HasField("gyroscope_channel")

    def set_gyroscope_channel(self, gyroscope_channel: _xyz_channel.XyzChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(gyroscope_channel, _xyz_channel.XyzChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a XyzChannel is required, but a "
                                                         f"{type(gyroscope_channel)}={gyroscope_channel} was "
                                                         f"provided")
        self._proto.gyroscope_channel.CopyFrom(gyroscope_channel.get_proto())
        return self

    def has_magnetometer_channel(self) -> bool:
        return self._proto.HasField("magnetometer_channel")

    def set_magnetometer_channel(self, magnetometer_channel: _xyz_channel.XyzChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(magnetometer_channel, _xyz_channel.XyzChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a XyzChannel is required, but a "
                                                         f"{type(magnetometer_channel)}={magnetometer_channel} was "
                                                         f"provided")
        self._proto.magnetometer_channel.CopyFrom(magnetometer_channel.get_proto())
        return self

    def has_light_channel(self) -> bool:
        return self._proto.HasField("light_channel")

    def set_light_channel(self, light_channel: _single_channel.SingleChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(light_channel, _single_channel.SingleChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a SingleChannel is required, but a "
                                                         f"{type(light_channel)}={light_channel} was "
                                                         f"provided")
        self._proto.light_channel.CopyFrom(light_channel.get_proto())
        return self

    def has_infrared_channel(self) -> bool:
        return self._proto.HasField("infrared_channel")

    def set_infrared_channel(self, infrared_channel: _single_channel.SingleChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(infrared_channel, _single_channel.SingleChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a SingleChannel is required, but a "
                                                         f"{type(infrared_channel)}={infrared_channel} was "
                                                         f"provided")
        self._proto.infrared_channel.CopyFrom(infrared_channel.get_proto())
        return self

    def has_location_channel(self) -> bool:
        return self._proto.HasField("location_channel")

    def set_location_channel(self, location_channel: _location_channel.LocationChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(location_channel, _location_channel.LocationChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a LocationChannel is required, but a "
                                                         f"{type(location_channel)}={location_channel} was "
                                                         f"provided")
        self._proto.location_channel.CopyFrom(location_channel.get_proto())
        return self
