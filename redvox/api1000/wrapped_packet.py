"""
This module provides a high level API for creating, reading, and editing RedVox compliant API 1000 files.
"""
import enum
from typing import Any, Dict, Optional

import numpy as np

import redvox.api1000.common as common
import redvox.api1000.errors as errors
import redvox.api1000.microphone_channel as _microphone_channel
import redvox.api1000.single_channel as _single_channel
import redvox.api1000.xyz_channel as _xyz_channel
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class NetworkType(enum.Enum):
    WIFI = 0
    CELLULAR = 1
    NONE = 2


class OsType(enum.Enum):
    ANDROID = 0
    IOS = 1
    LINUX = 2
    WINDOWS = 3


class WrappedRedvoxPacketApi1000:
    def __init__(self, redvox_proto: redvox_api_1000_pb2.RedvoxPacket1000):
        self._proto: redvox_api_1000_pb2.RedvoxPacket1000 = redvox_proto

    @staticmethod
    def new() -> 'WrappedRedvoxPacketApi1000':
        return WrappedRedvoxPacketApi1000(redvox_api_1000_pb2.RedvoxPacket1000())

    @staticmethod
    def from_compressed_bytes(data: bytes) -> 'WrappedRedvoxPacketApi1000':
        pass

    @staticmethod
    def from_compressed_path(rdvxz_path: str) -> 'WrappedRedvoxPacketApi1000':
        pass

    def to_compressed_bytes(self) -> bytes:
        pass

    def to_json(self) -> str:
        pass

    def to_dict(self) -> Dict:
        pass

    def write_compressed_to_file(self, base_dir: str, filename: Optional = None):
        pass

    def write_json_to_file(self, base_dir: str, filename: Optional = None):
        pass

    # API Version
    def get_api(self) -> int:
        return self._proto.api

    def set_api(self, api: int) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(api, int):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a {type(api)}={api} was "
                                                         f"provided")
        self._proto.api = api
        return self

    # User information
    def get_auth_email(self) -> str:
        return self._proto.auth_email

    def set_auth_email(self, auth_email: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(auth_email, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a {type(auth_email)}={auth_email} "
                                                         f"was provided")

        self._proto.auth_email = auth_email
        return self

    def get_auth_token(self) -> str:
        return self._proto.auth_token

    def set_auth_token(self, auth_token: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(auth_token, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a {type(auth_token)}={auth_token} "
                                                         f"was provided")

        self._proto.auth_token = auth_token
        return self

    def get_firebase_token(self) -> str:
        return self._proto.firebase_token

    def set_firebase_token(self, firebase_token: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(firebase_token, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a "
                                                         f"{type(firebase_token)}={firebase_token} was provided")

        self._proto.firebase_token = firebase_token
        return self

    # Device information
    def get_device_id(self) -> str:
        return self._proto.device_id

    def set_device_id(self, device_id: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(device_id, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a "
                                                         f"{type(device_id)}={device_id} was provided")

        self._proto.device_id = device_id
        return self

    def get_device_uuid(self) -> str:
        return self._proto.device_uuid

    def set_device_uuid(self, device_uuid: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(device_uuid, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a "
                                                         f"{type(device_uuid)}={device_uuid} was provided")

        self._proto.device_uuid = device_uuid
        return self

    def get_device_make(self) -> str:
        return self._proto.device_make

    def set_device_make(self, device_make: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(device_make, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a "
                                                         f"{type(device_make)}={device_make} was provided")

        self._proto.device_make = device_make
        return self

    def get_device_model(self) -> str:
        return self._proto.device_model

    def set_device_model(self, device_model: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(device_model, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a "
                                                         f"{type(device_model)}={device_model} was provided")

        self._proto.device_model = device_model
        return self

    def get_device_os(self) -> OsType:
        return OsType(self._proto.device_os)

    def set_device_os(self, os: OsType) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(os, OsType):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of OsType is required, but a {type(os)}={os} "
                                                         f"was provided")

        self._proto.device_os = redvox_api_1000_pb2.RedvoxPacket1000.OsType.Value(os.name)
        return self

    def get_device_os_version(self) -> str:
        return self._proto.device_os_version

    def set_device_os_version(self, device_os_version: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(device_os_version, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a "
                                                         f"{type(device_os_version)}={device_os_version} was provided")

        self._proto.device_os_version = device_os_version
        return self

    def get_device_app_version(self) -> str:
        return self._proto.device_app_version

    def set_device_app_version(self, device_app_version: str) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(device_app_version, str):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A string is required, but a "
                                                         f"{type(device_app_version)}={device_app_version} was "
                                                         f"provided")

        self._proto.device_app_version = device_app_version
        return self

    def get_device_temp_c(self) -> float:
        return self._proto.device_temp_c

    def set_device_temp_c(self, device_temp_c: float) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_numerical_type(device_temp_c):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a "
                                                         f"{type(device_temp_c)}={device_temp_c} was provided")
        self._proto.device_temp_c = device_temp_c
        return self

    def get_device_battery_percent(self) -> float:
        return self._proto.device_battery_percent

    def set_device_battery_percent(self, device_battery_percent: float) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_numerical_type(device_battery_percent):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a "
                                                         f"{type(device_battery_percent)}={device_battery_percent} was "
                                                         f"provided")
        self._proto.device_battery_percent = device_battery_percent
        return self

    def get_network_type(self) -> NetworkType:
        return NetworkType(self._proto.network_type)

    def set_network_type(self, network_type: OsType) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(network_type, NetworkType):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of NetworkType is required, but a "
                                                         f"{type(network_type)}={network_type} was provided")

        self._proto.network_type = redvox_api_1000_pb2.RedvoxPacket1000.NetworkType.Value(network_type.name)
        return self

    def get_network_strength_db(self) -> float:
        return self._proto.network_strength_db

    def set_network_strength_db(self, network_strength_db: float) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_numerical_type(network_strength_db):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a "
                                                         f"{type(network_strength_db)}={network_strength_db} was "
                                                         f"provided")
        self._proto.network_strength_db = network_strength_db
        return self

    # Packet information
    def get_is_backfilled(self) -> bool:
        return self._proto.is_backfilled

    def set_is_backfilled(self, is_backfilled: bool) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(is_backfilled, bool):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A boolean is required, but a "
                                                         f"{type(is_backfilled)}={is_backfilled} was provided")
        self._proto.is_backfilled = is_backfilled
        return self

    def get_is_private(self) -> bool:
        return self._proto.is_private

    def set_is_private(self, is_private: bool) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(is_private, bool):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A boolean is required, but a "
                                                         f"{type(is_private)}={is_private} was provided")
        self._proto.is_private = is_private
        return self

    def get_is_mic_scrambled(self) -> bool:
        return self._proto.is_mic_scrambled

    def set_is_mic_scrambled(self, is_mic_scrambled: bool) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(is_mic_scrambled, bool):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A boolean is required, but a "
                                                         f"{type(is_mic_scrambled)}={is_mic_scrambled} was provided")
        self._proto.is_mic_scrambled = is_mic_scrambled
        return self

    def get_uncompressed_size_bytes(self) -> float:
        return self._proto.uncompressed_size_bytes

    def set_uncompressed_size_bytes(self, uncompressed_size_bytes: float) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_numerical_type(uncompressed_size_bytes):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a "
                                                         f"{type(uncompressed_size_bytes)}={uncompressed_size_bytes} "
                                                         f"was provided")
        self._proto.uncompressed_size_bytes = uncompressed_size_bytes
        return self

    def get_compressed_size_bytes(self) -> float:
        return self._proto.compressed_size_bytes

    def set_compressed_size_bytes(self, compressed_size_bytes: float) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_numerical_type(compressed_size_bytes):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a "
                                                         f"{type(compressed_size_bytes)}={compressed_size_bytes} "
                                                         f"was provided")
        self._proto.compressed_size_bytes = compressed_size_bytes
        return self

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

    # Timing information
    def get_packet_start_ts_us_wall(self) -> float:
        return self._proto.packet_start_ts_us_wall

    def set_packet_start_ts_us_wall(self, packet_start_ts_us_wall: float) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_numerical_type(packet_start_ts_us_wall):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a "
                                                         f"{type(packet_start_ts_us_wall)}={packet_start_ts_us_wall} was "
                                                         f"provided")
        self._proto.packet_start_ts_us_wall = packet_start_ts_us_wall
        return self

    def get_packet_start_ts_us_mach(self) -> float:
        return self._proto.packet_start_ts_us_mach

    def set_packet_start_ts_us_mach(self, packet_start_ts_us_mach: float) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_numerical_type(packet_start_ts_us_mach):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a "
                                                         f"{type(packet_start_ts_us_mach)}={packet_start_ts_us_mach} was "
                                                         f"provided")
        self._proto.packet_start_ts_us_mach = packet_start_ts_us_mach
        return self

    def get_packet_end_ts_us_wall(self) -> float:
        return self._proto.packet_end_ts_us_wall

    def set_packet_end_ts_us_wall(self, packet_end_ts_us_wall: float) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_numerical_type(packet_end_ts_us_wall):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a "
                                                         f"{type(packet_end_ts_us_wall)}={packet_end_ts_us_wall} was "
                                                         f"provided")
        self._proto.packet_end_ts_us_wall = packet_end_ts_us_wall
        return self

    def get_packet_end_ts_us_mach(self) -> float:
        return self._proto.packet_end_ts_us_mach

    def set_packet_end_ts_us_mach(self, packet_end_ts_us_mach: float) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_numerical_type(packet_end_ts_us_mach):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a "
                                                         f"{type(packet_end_ts_us_mach)}={packet_end_ts_us_mach} was "
                                                         f"provided")
        self._proto.packet_end_ts_us_mach = packet_end_ts_us_mach
        return self

    def get_server_acquisition_arrival_ts_us(self) -> float:
        return self._proto.server_acquisition_arrival_ts_us

    def set_server_acquisition_arrival_ts_us(self, server_acquisition_arrival_ts_us: float) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_numerical_type(server_acquisition_arrival_ts_us):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a "
                                                         f"{type(server_acquisition_arrival_ts_us)}="
                                                         f"{server_acquisition_arrival_ts_us} was "
                                                         f"provided")
        self._proto.server_acquisition_arrival_ts_us = server_acquisition_arrival_ts_us
        return self

    def get_app_start_ts_us_mach(self) -> float:
        return self._proto.app_start_ts_us_mach

    def set_app_start_ts_us_mach(self, app_start_ts_us_mach: float) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_numerical_type(app_start_ts_us_mach):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a "
                                                         f"{type(app_start_ts_us_mach)}="
                                                         f"{app_start_ts_us_mach} was "
                                                         f"provided")
        self._proto.app_start_ts_us_mach = app_start_ts_us_mach
        return self

    def get_synch_params(self) -> np.ndarray:
        return np.array(self._proto.synch_params)

    def set_synch_params(self, synch_params: np.ndarray) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_repeated_numerical_type(synch_params):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A numpy array of floats or integers is required, but a "
                                                         f"{type(synch_params)}={synch_params} was provided")
        self._proto.synch_params[:] = list(synch_params)
        return self

    def append_synch_params(self, synch_params: np.ndarray) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_repeated_numerical_type(synch_params):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A numpy array of floats or integers is required, but a "
                                                         f"{type(synch_params)}={synch_params} was provided")
        self._proto.synch_params.extend(list(synch_params))
        return self

    def clear_synch_params(self) -> 'WrappedRedvoxPacketApi1000':
        self._proto.synch_params[:] = []
        return self

    def get_best_latency_us(self) -> float:
        return self._proto.best_latency_us

    def set_best_latency_us(self, best_latency_us: float) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_numerical_type(best_latency_us):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a "
                                                         f"{type(best_latency_us)}="
                                                         f"{best_latency_us} was "
                                                         f"provided")
        self._proto.best_latency_us = best_latency_us
        return self

    def get_best_offset_us(self) -> float:
        return self._proto.best_offset_us

    def set_best_offset_us(self, best_offset_us: float) -> 'WrappedRedvoxPacketApi1000':
        if not common.is_protobuf_numerical_type(best_offset_us):
            raise errors.WrappedRedvoxPacketApi1000Error(f"A float or integer is required, but a "
                                                         f"{type(best_offset_us)}="
                                                         f"{best_offset_us} was "
                                                         f"provided")
        self._proto.best_offset_us = best_offset_us
        return self

    # Channels
    def has_microphone_channel(self) -> bool:
        return self._proto.HasField("microphone_channel")

    def get_microphone_channel(self) -> _microphone_channel.MicrophoneChannel:
        if not self.has_microphone_channel():
            raise errors.WrappedRedvoxPacketApi1000Error("Packet does not contain a microphone channel")

        return _microphone_channel.MicrophoneChannel(self._proto.microphone_channel)

    def set_microphone_channel(self, microphone_channel: _microphone_channel.MicrophoneChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(microphone_channel, _microphone_channel.MicrophoneChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a MicrophoneChannel is required, but a "
                                                         f"{type(microphone_channel)}={microphone_channel} was "
                                                         f"provided")
        self._proto.microphone_channel.CopyFrom(microphone_channel._proto)
        return self

    def has_barometer_channel(self) -> bool:
        return self._proto.HasField("barometer_channel")

    def set_barometer_channel(self, barometer_channel: _single_channel.SingleChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(barometer_channel, _single_channel.SingleChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a SingleChannel is required, but a "
                                                         f"{type(barometer_channel)}={barometer_channel} was "
                                                         f"provided")
        self._proto.barometer_channel.CopyFrom(barometer_channel._proto)
        return self

    def has_accelerometer_channel(self) -> bool:
        return self._proto.HasField("accelerometer_channel")

    def set_accelerometer_channel(self, accelerometer_channel: _single_channel.SingleChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(accelerometer_channel, _xyz_channel.XyzChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a XyzChannel is required, but a "
                                                         f"{type(accelerometer_channel)}={accelerometer_channel} was "
                                                         f"provided")
        self._proto.accelerometer_channel.CopyFrom(accelerometer_channel._proto)
        return self

    def has_gyroscope_channel(self) -> bool:
        return self._proto.HasField("gyroscope_channel")

    def set_gyroscope_channel(self, gyroscope_channel: _single_channel.SingleChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(gyroscope_channel, _xyz_channel.XyzChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a XyzChannel is required, but a "
                                                         f"{type(gyroscope_channel)}={gyroscope_channel} was "
                                                         f"provided")
        self._proto.gyroscope_channel.CopyFrom(gyroscope_channel._proto)
        return self

    def has_magnetometer_channel(self) -> bool:
        return self._proto.HasField("magnetometer_channel")

    def set_magnetometer_channel(self, magnetometer_channel: _single_channel.SingleChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(magnetometer_channel, _xyz_channel.XyzChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a XyzChannel is required, but a "
                                                         f"{type(magnetometer_channel)}={magnetometer_channel} was "
                                                         f"provided")
        self._proto.magnetometer_channel.CopyFrom(magnetometer_channel._proto)
        return self

    def has_light_channel(self) -> bool:
        return self._proto.HasField("light_channel")

    def set_light_channel(self, light_channel: _single_channel.SingleChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(light_channel, _single_channel.SingleChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a SingleChannel is required, but a "
                                                         f"{type(light_channel)}={light_channel} was "
                                                         f"provided")
        self._proto.light_channel.CopyFrom(light_channel._proto)
        return self

    def has_infrared_channel(self) -> bool:
        return self._proto.HasField("infrared_channel")

    def set_infrared_channel(self, infrared_channel: _single_channel.SingleChannel) -> 'WrappedRedvoxPacketApi1000':
        if not isinstance(infrared_channel, _single_channel.SingleChannel):
            raise errors.WrappedRedvoxPacketApi1000Error(f"An instance of a SingleChannel is required, but a "
                                                         f"{type(infrared_channel)}={infrared_channel} was "
                                                         f"provided")
        self._proto.infrared_channel.CopyFrom(infrared_channel._proto)
        return self

    # Metadata
    def get_metadata(self) -> Dict[str, str]:
        return common.get_metadata(self._proto.metadata)

    def set_metadata(self, metadata: Dict[str, str]) -> 'WrappedRedvoxPacketApi1000':
        err_value: Optional[Any] = common.set_metadata(self._proto.metadata, metadata)

        if err_value is not None:
            raise errors.MicrophoneChannelError("All keys and values in metadata must be strings, but "
                                                f"{type(err_value)}={err_value} was supplied")

        return self

    def append_metadata(self, key: str, value: str) -> 'WrappedRedvoxPacketApi1000':
        err_value: Optional[Any] = common.append_metadata(self._proto.metadata, key, value)

        if err_value is not None:
            raise errors.MicrophoneChannelError("All keys and values in metadata must be strings, but "
                                                f"{type(err_value)}={err_value} was supplied")

        return self

    def as_json(self) -> str:
        return common.as_json(self._proto)

    def __str__(self):
        return str(self._proto)
