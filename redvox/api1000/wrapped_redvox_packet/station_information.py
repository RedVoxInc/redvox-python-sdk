import enum
from typing import List

import redvox.api1000.wrapped_redvox_packet.common as common
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class AudioSamplingRate(enum.Enum):
    HZ_80: int = 0
    HZ_800: int = 1
    HZ_8000: int = 2
    HZ_16000: int = 3
    HZ_48000: int = 4

    @staticmethod
    def from_proto(audio_sample_rate: redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.AudioSamplingRate) -> 'AudioSamplingRate':
        return AudioSamplingRate(audio_sample_rate)

    def into_proto(self) -> redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.AudioSamplingRate:
        return redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.AudioSamplingRate.Value(self.name)


class AudioSourceTuning(enum.Enum):
    INFRASOUND: int = 0
    LOW_AUDIO: int = 1
    AUDIO: int = 2

    @staticmethod
    def from_proto(audio_source_tuning: redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.AudioSourceTuning) -> 'AudioSourceTuning':
        return AudioSourceTuning(audio_source_tuning)

    def into_proto(self) -> redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.AudioSourceTuning:
        return redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.AudioSourceTuning.Value(self.name)


class InputSensor(enum.Enum):
    BAROMETER: int = 0
    ACCELEROMETER: int = 1
    ACCELEROMETER_FAST: int = 2
    MAGNETOMETER: int = 3
    MAGNETOMETER_FAST: int = 4
    GYROSCOPE: int = 5
    GYROSCOPE_FAST: int = 6
    LUMINOSITY: int = 7

    @staticmethod
    def from_proto(input_sensor: redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.InputSensor) -> 'InputSensor':
        return InputSensor(input_sensor)

    def into_proto(self) -> redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.InputSensor:
        return redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.InputSensor.Value(self.name)


class AppSettings(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings):
        super().__init__(proto)

    @staticmethod
    def new() -> 'AppSettings':
        return AppSettings(redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings())

    def get_audio_sampling_rate(self) -> AudioSamplingRate:
        return AudioSamplingRate(self._proto.audio_sampling_rate_hz)

    def set_audio_sampling_rate(self, audio_sampling_rate_hz: AudioSamplingRate) -> 'AppSettings':
        common.check_type(audio_sampling_rate_hz, [AudioSamplingRate])

        self._proto.audio_sampling_rate_hz = redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.AudioSamplingRate.Value(
            audio_sampling_rate_hz.name)
        return self

    def get_audio_source_tuning(self) -> AudioSourceTuning:
        return AudioSourceTuning(self._proto.audio_source_tuning)

    def set_audio_source_tuning(self, audio_source_tuning: AudioSourceTuning) -> 'AppSettings':
        common.check_type(audio_source_tuning, [AudioSourceTuning])

        self._proto.audio_source_tuning = redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.AudioSourceTuning.Value(
            audio_source_tuning.name)
        return self

    def get_additional_input_sensors(self) -> List[InputSensor]:
        additional_input_sensors: List[
            redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.InputSensor] = self._proto.additional_input_sensors
        return list(map(lambda sensor: InputSensor(sensor), additional_input_sensors))

    def set_additional_input_sensors(self, additional_input_sensors: List[InputSensor]) -> 'AppSettings':
        proto_sensors: List[redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.InputSensor] = list(map(
            lambda sensor: redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.AppSettings.InputSensor.Value(
                sensor.name), additional_input_sensors))
        self._proto.additional_input_sensors[:] = proto_sensors
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


class StationInformation(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.StationInformation):
        super().__init__(proto)
        self._app_settings: AppSettings = AppSettings(proto.app_settings)
        self._station_information_timestamps = common.Payload(proto.station_information_timestamps)
        self._network_strength: common.Payload = common.Payload(proto.network_strength)
        self._temperature: common.Payload = common.Payload(proto.temperature)
        self._battery: common.Payload = common.Payload(proto.battery)
        self._available_ram: common.Payload = common.Payload(proto.available_ram)
        self._available_disk: common.Payload = common.Payload(proto.available_disk)
        self._cpu_utilization: common.Payload = common.Payload(proto.cpu_utilization)

    @staticmethod
    def new() -> 'StationInformation':
        return StationInformation(redvox_api_1000_pb2.RedvoxPacket1000.StationInformation())

    def get_id(self) -> str:
        return self._proto.id

    def set_id(self, _id: str) -> 'StationInformation':
        common.check_type(_id, [str])
        self._proto.id = _id
        return self

    def get_uuid(self) -> str:
        return self._proto.uuid

    def set_uuid(self, uuid: str) -> 'StationInformation':
        common.check_type(uuid, [str])
        self._proto.uuid = uuid
        return self

    def get_make(self) -> str:
        return self._proto.make

    def set_make(self, make: str) -> 'StationInformation':
        common.check_type(make, [str])
        self._proto.make = make
        return self

    def get_model(self) -> str:
        return self._proto.model

    def set_model(self, model: str) -> 'StationInformation':
        common.check_type(model, [str])
        self._proto.model = model
        return self

    def get_os(self) -> OsType:
        return OsType(self._proto.os)

    def set_os(self, os: OsType) -> 'StationInformation':
        common.check_type(os, [OsType])
        self._proto.os = redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.OsType.Value(os.name)
        return self

    def get_os_version(self) -> str:
        return self._proto.os_version

    def set_os_version(self, os_version: str) -> 'StationInformation':
        common.check_type(os_version, [str])
        self._proto.os_version = os_version
        return self

    def get_app_version(self) -> str:
        return self._proto.app_version

    def set_app_version(self, app_version: str) -> 'StationInformation':
        common.check_type(app_version, [str])
        self._proto.app_version = app_version
        return self

    def get_app_settings(self) -> AppSettings:
        return self._app_settings

    def get_network_type(self) -> NetworkType:
        return NetworkType(self._proto.network_type)

    def set_network_type(self, network_type: NetworkType) -> 'StationInformation':
        common.check_type(network_type, [NetworkType])
        self._proto.network_type = redvox_api_1000_pb2.RedvoxPacket1000.StationInformation.NetworkType.Value(
            network_type.name)
        return self

    def get_station_information_timestamps(self) -> common.Payload:
        return self._station_information_timestamps

    def get_network_strength(self) -> common.Payload:
        return self._network_strength

    def get_temperature(self) -> common.Payload:
        return self._temperature

    def get_battery(self) -> common.Payload:
        return self._battery

    def get_available_ram(self) -> common.Payload:
        return self._available_ram

    def get_available_disk(self) -> common.Payload:
        return self._available_disk

    def get_cpu_utilization(self) -> common.Payload:
        return self._cpu_utilization
