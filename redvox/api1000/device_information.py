import enum

import redvox.api1000.common as common
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class AudioSamplingRate(enum.Enum):
    HZ_80: int = 0
    HZ_800: int = 1
    HZ_8000: int = 2


class AudioSourceTuning(enum.Enum):
    INFRASOUND: int = 0
    LOW_AUDIO: int = 1
    AUDIO: int = 2


class InputSensor(enum.Enum):
    BAROMETER: int = 0
    ACCELEROMETER: int = 1
    ACCELEROMETER_FAST: int = 2
    MAGNETOMETER: int = 3
    MAGNETOMETER_FAST: int = 4
    GYROSCOPE: int = 5
    GYROSCOPE_FAST: int = 6
    LUMINOSITY: int = 7


class AppSettings(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.DeviceInformation.AppSettings):
        super().__init__(proto)

    @staticmethod
    def new() -> 'AppSettings':
        return AppSettings(redvox_api_1000_pb2.RedvoxPacket1000.DeviceInformation.AppSettings())

    def get_audio_sampling_rate(self) -> AudioSamplingRate:
        return AudioSamplingRate(self._proto.audio_sampling_rate)

    def set_audio_sampling_rate(self, audio_sampling_rate: AudioSamplingRate) -> 'AppSettings':
        common.check_type(audio_sampling_rate, [AudioSamplingRate])

        self._proto.audio_sampling_rate = redvox_api_1000_pb2.RedvoxPacket1000.DeviceInformation.AppSettings.AudioSamplingRate.Value(
            audio_sampling_rate.name)
        return self

    def get_audio_source_tuning(self) -> AudioSourceTuning:
        return AudioSourceTuning(self._proto.audio_source_tuning)

    def set_audio_source_tuning(self, audio_source_tuning: AudioSourceTuning) -> 'AppSettings':
        common.check_type(audio_source_tuning, [AudioSourceTuning])

        self._proto.audio_source_tuning = redvox_api_1000_pb2.RedvoxPacket1000.DeviceInformation.AppSettings.AudioSourceTuning.Value(
            audio_source_tuning.name)
        return self

    def get_automatically_record(self) -> bool:
        return self._proto.automatically_record

    def set_automatically_record(self, automatically_record: bool) -> 'AppSettings':
        common.check_type(automatically_record, [bool])
        self._proto.automatically_record = automatically_record
        return self

    def get_launch_at_power_up(self) -> bool:
        return self._proto.launch_at_power_up

    def set_launch_at_power_up(self, launch_at_power_up: bool) -> 'AppSettings':
        common.check_type(launch_at_power_up, [bool])
        self._proto.launch_at_power_up = launch_at_power_up
        return self

    def get_redvox_id(self) -> str:
        return self._proto.redvox_id

    def set_redvox_id(self, redvox_id: str) -> 'AppSettings':
        common.check_type(redvox_id, [str])
        self._proto.redvox_id = redvox_id
        return self

    def get_push_to_server(self) -> bool:
        return self._proto.push_to_server

    def set_push_to_server(self, push_to_server: bool) -> 'AppSettings':
        common.check_type(push_to_server, [bool])
        self._proto.push_to_server = push_to_server
        return self

    def get_publish_data_as_private(self) -> bool:
        return self._proto.publish_data_as_private

    def set_publish_data_as_private(self, publish_data_as_private: bool) -> 'AppSettings':
        common.check_type(publish_data_as_private, [bool])
        self._proto.publish_data_as_private = publish_data_as_private
        return self

    def get_scramble_voice_data(self) -> bool:
        return self._proto.scramble_voice_data

    def set_scramble_voice_data(self, scramble_voice_data: bool) -> 'AppSettings':
        common.check_type(scramble_voice_data, [bool])
        self._proto.scramble_voice_data = scramble_voice_data
        return self

    def get_provide_backfill(self) -> bool:
        return self._proto.provide_backfill

    def set_provide_backfill(self, provide_backfill: bool) -> 'AppSettings':
        common.check_type(provide_backfill, [bool])
        self._proto.provide_backfill = provide_backfill
        return self

    def get_use_custom_time_sync_server(self) -> bool:
        return self._proto.use_custom_time_sync_server

    def set_use_custom_time_sync_server(self, use_custom_time_sync_server: bool) -> 'AppSettings':
        common.check_type(use_custom_time_sync_server, [bool])
        self._proto.use_custom_time_sync_server = use_custom_time_sync_server
        return self

    def get_time_sync_server_url(self) -> str:
        return self._proto.time_sync_server_url

    def set_time_sync_server_url(self, time_sync_server_url: str) -> 'AppSettings':
        common.check_type(time_sync_server_url, [str])
        self._proto.time_sync_server_url = time_sync_server_url
        return self

    def get_use_custom_data_server(self) -> bool:
        return self._proto.use_custom_data_server

    def set_use_custom_data_server(self, use_custom_data_server: bool) -> 'AppSettings':
        common.check_type(use_custom_data_server, [bool])
        self._proto.use_custom_data_server = use_custom_data_server
        return self

    def get_data_server_url(self) -> str:
        return self._proto.data_server_url

    def set_data_server_url(self, data_server_url: str) -> 'AppSettings':
        common.check_type(data_server_url, [str])
        self._proto.data_server_url = data_server_url
        return self

    def get_auto_delete_data_files(self) -> bool:
        return self._proto.auto_delete_data_files

    def set_auto_delete_data_files(self, auto_delete_data_files: bool) -> 'AppSettings':
        common.check_type(auto_delete_data_files, [bool])
        self._proto.auto_delete_data_files = auto_delete_data_files
        return self

    def get_storage_space_allowance(self) -> float:
        return self._proto.storage_space_allowance

    def set_storage_space_allowance(self, storage_space_allowance: float) -> 'AppSettings':
        common.check_type(storage_space_allowance, [int, float])

        self._proto.storage_space_allowance = storage_space_allowance
        return self

    def get_use_sd_card_for_data_storage(self) -> bool:
        return self._proto.use_sd_card_for_data_storage

    def set_use_sd_card_for_data_storage(self, use_sd_card_for_data_storage: bool) -> 'AppSettings':
        common.check_type(use_sd_card_for_data_storage, [bool])
        self._proto.use_sd_card_for_data_storage = use_sd_card_for_data_storage
        return self

    def get_use_location_services(self) -> bool:
        return self._proto.use_location_services

    def set_use_location_services(self, use_location_services: bool) -> 'AppSettings':
        common.check_type(use_location_services, [bool])
        self._proto.use_location_services = use_location_services
        return self

    def get_use_latitude(self) -> float:
        return self._proto.use_latitude

    def set_use_latitude(self, use_latitude: float) -> 'AppSettings':
        common.check_type(use_latitude, [int, float])

        self._proto.use_latitude = use_latitude
        return self

    def get_use_longitude(self) -> float:
        return self._proto.use_longitude

    def set_use_longitude(self, use_longitude: float) -> 'AppSettings':
        common.check_type(use_longitude, [int, float])

        self._proto.use_longitude = use_longitude
        return self


class NetworkType(enum.Enum):
    WIFI: int = 0
    CELLULAR: int = 1
    NONE: int = 2


class OsType(enum.Enum):
    ANDROID: int = 0
    IOS: int = 1
    LINUX: int = 2
    WINDOWS: int = 3


class DeviceInformation(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.DeviceInformation):
        super().__init__(proto)
        self._app_settings: AppSettings = AppSettings(proto.app_settings)

    @staticmethod
    def new() -> 'DeviceInformation':
        return DeviceInformation(redvox_api_1000_pb2.RedvoxPacket1000.DeviceInformation())

    def get_device_id(self) -> str:
        return self._proto.device_id

    def set_device_id(self, device_id: str) -> 'DeviceInformation':
        common.check_type(device_id, [str])
        self._proto.device_id = device_id
        return self

    def get_device_uuid(self) -> str:
        return self._proto.device_uuid

    def set_device_uuid(self, device_uuid: str) -> 'DeviceInformation':
        common.check_type(device_uuid, [str])
        self._proto.device_uuid = device_uuid
        return self

    def get_device_make(self) -> str:
        return self._proto.device_make

    def set_device_make(self, device_make: str) -> 'DeviceInformation':
        common.check_type(device_make, [str])
        self._proto.device_make = device_make
        return self

    def get_device_model(self) -> str:
        return self._proto.device_model

    def set_device_model(self, device_model: str) -> 'DeviceInformation':
        common.check_type(device_model, [str])
        self._proto.device_model = device_model
        return self

    def get_device_os(self) -> OsType:
        return OsType(self._proto.device_os)

    def set_device_os(self, os: OsType) -> 'DeviceInformation':
        common.check_type(os, [OsType])
        self._proto.device_os = redvox_api_1000_pb2.RedvoxPacket1000.DeviceInformation.OsType.Value(os.name)
        return self

    def get_device_os_version(self) -> str:
        return self._proto.device_os_version

    def set_device_os_version(self, device_os_version: str) -> 'DeviceInformation':
        common.check_type(device_os_version, [str])
        self._proto.device_os_version = device_os_version
        return self

    def get_device_app_version(self) -> str:
        return self._proto.device_app_version

    def set_device_app_version(self, device_app_version: str) -> 'DeviceInformation':
        common.check_type(device_app_version, [str])
        self._proto.device_app_version = device_app_version
        return self

    def get_app_settings(self) -> AppSettings:
        return self._app_settings

    def set_app_settings(self, app_settings: AppSettings) -> 'DeviceInformation':
        common.check_type(app_settings, [AppSettings])
        self._app_settings = app_settings
        return self

    def get_network_type(self) -> NetworkType:
        return NetworkType(self._proto.network_type)

    def set_network_type(self, network_type: NetworkType) -> 'DeviceInformation':
        common.check_type(network_type, [NetworkType])
        self._proto.network_type = redvox_api_1000_pb2.RedvoxPacket1000.DeviceInformation.NetworkType.Value(
            network_type.name)
        return self

    def get_network_strength_db(self) -> float:
        return self._proto.network_strength_db

    def set_network_strength_db(self, network_strength_db: float) -> 'DeviceInformation':
        common.check_type(network_strength_db, [int, float])
        self._proto.network_strength_db = network_strength_db
        return self

    def get_device_temp_c(self) -> float:
        return self._proto.device_temp_c

    def set_device_temp_c(self, device_temp_c: float) -> 'DeviceInformation':
        common.check_type(device_temp_c, [int, float])
        self._proto.device_temp_c = device_temp_c
        return self

    def get_device_battery_percent(self) -> float:
        return self._proto.device_battery_percent

    def set_device_battery_percent(self, device_battery_percent: float) -> 'DeviceInformation':
        common.check_type(device_battery_percent, [int, float])
        self._proto.device_battery_percent = device_battery_percent
        return self

