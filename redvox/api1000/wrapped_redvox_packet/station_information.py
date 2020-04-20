import enum
from typing import List, Optional

import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.wrapped_redvox_packet.common as common


class AudioSamplingRate(enum.Enum):
    HZ_80: int = 0
    HZ_800: int = 1
    HZ_8000: int = 2
    HZ_16000: int = 3
    HZ_48000: int = 4

    @staticmethod
    def from_proto(audio_sample_rate: redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate) -> 'AudioSamplingRate':
        return AudioSamplingRate(audio_sample_rate)

    def into_proto(self) -> redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate:
        return redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate.Value(self.name)

    @staticmethod
    def from_sampling_rate(sampling_rate: float) -> Optional['AudioSamplingRate']:
        if sampling_rate == 80.0:
            return AudioSamplingRate['HZ_80']
        elif sampling_rate == 800.0:
            return AudioSamplingRate['HZ_800']
        elif sampling_rate == 8000.0:
            return AudioSamplingRate['HZ_8000']
        elif sampling_rate == 16000.0:
            return AudioSamplingRate['HZ_16000']
        elif sampling_rate == 48000.0:
            return AudioSamplingRate['HZ_48000']
        else:
            return None


class AudioSourceTuning(enum.Enum):
    INFRASOUND_TUNING: int = 0
    LOW_AUDIO_TUNING: int = 1
    AUDIO_TUNING: int = 2

    @staticmethod
    def from_proto(audio_source_tuning: redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning) -> 'AudioSourceTuning':
        return AudioSourceTuning(audio_source_tuning)

    def into_proto(self) -> redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning:
        return redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning.Value(self.name)


class InputSensor(enum.Enum):
    ACCELEROMETER = 0
    AMBIENT_TEMPERATURE = 1
    AUDIO = 2
    COMPRESSED_AUDIO = 3
    GRAVITY = 4
    GYROSCOPE = 5
    IMAGE = 6
    LIGHT = 7
    LINEAR_ACCELERATION = 8
    LOCATION = 9
    MAGNETOMETER = 10
    ORIENTATION = 11
    PRESSURE = 12
    PROXIMITY = 13
    RELATIVE_HUMIDITY = 14
    ROTATION_VECTOR = 15

    @staticmethod
    def from_proto(input_sensor: redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.InputSensor) -> 'InputSensor':
        return InputSensor(input_sensor)

    def into_proto(self) -> redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.InputSensor:
        return redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.InputSensor.Value(self.name)


class FftOverlap(enum.Enum):
    PERCENT_25 = 0
    PERCENT_50 = 1
    PERCENT_75 = 2

    @staticmethod
    def from_proto(fft_overlap: redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.FftOverlap) -> 'FftOverlap':
        return FftOverlap(fft_overlap)

    def into_proto(self) -> redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.FftOverlap:
        return redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.FftOverlap.Value(self.name)


class AppSettings(common.ProtoBase):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings):
        super().__init__(proto)

    @staticmethod
    def new() -> 'AppSettings':
        return AppSettings(redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings())

    def get_audio_sampling_rate(self) -> AudioSamplingRate:
        return AudioSamplingRate(self._proto.audio_sampling_rate)

    def set_audio_sampling_rate(self, audio_sampling_rate: AudioSamplingRate) -> 'AppSettings':
        common.check_type(audio_sampling_rate, [AudioSamplingRate])

        self._proto.audio_sampling_rate = redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate.Value(
            audio_sampling_rate.name)
        return self

    def get_audio_source_tuning(self) -> AudioSourceTuning:
        return AudioSourceTuning(self._proto.audio_source_tuning)

    def set_audio_source_tuning(self, audio_source_tuning: AudioSourceTuning) -> 'AppSettings':
        common.check_type(audio_source_tuning, [AudioSourceTuning])

        self._proto.audio_source_tuning = redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning.Value(
            audio_source_tuning.name)
        return self

    def get_additional_input_sensors(self) -> List[InputSensor]:
        additional_input_sensors: List[
            redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.InputSensor] = self._proto.additional_input_sensors
        return list(map(lambda sensor: InputSensor(sensor), additional_input_sensors))

    def set_additional_input_sensors(self, additional_input_sensors: List[InputSensor]) -> 'AppSettings':
        proto_sensors: List[redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.InputSensor] = list(map(
            lambda sensor: redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.InputSensor.Value(
                sensor.name), additional_input_sensors))
        self._proto.additional_input_sensors[:] = proto_sensors
        return self

    def get_fft_overlap(self) -> FftOverlap:
        return FftOverlap(self._proto.fft_overlap)

    def set_fft_overlap(self, fft_overlap: FftOverlap) -> 'AppSettings':
        common.check_type(fft_overlap, [FftOverlap])

        self._proto.fft_overlap = redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.FftOverlap.Value(
            fft_overlap.name)
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

    def get_station_id(self) -> str:
        return self._proto.station_id

    def set_station_id(self, station_id: str) -> 'AppSettings':
        common.check_type(station_id, [str])
        self._proto.station_id = station_id
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

    def get_scramble_audio_data(self) -> bool:
        return self._proto.scramble_audio_data

    def set_scramble_audio_data(self, scramble_audio_data: bool) -> 'AppSettings':
        common.check_type(scramble_audio_data, [bool])
        self._proto.scramble_audio_data = scramble_audio_data
        return self

    def get_provide_backfill(self) -> bool:
        return self._proto.provide_backfill

    def set_provide_backfill(self, provide_backfill: bool) -> 'AppSettings':
        common.check_type(provide_backfill, [bool])
        self._proto.provide_backfill = provide_backfill
        return self

    def get_remove_sensor_dc_offset(self) -> bool:
        return self._proto.remove_sensor_dc_offset

    def set_remove_sensor_dc_offset(self, remove_sensor_dc_offset: bool) -> 'AppSettings':
        common.check_type(remove_sensor_dc_offset, [bool])
        self._proto.remove_sensor_dc_offset = remove_sensor_dc_offset
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

    def get_use_altitude(self) -> float:
        return self._proto.use_altitude

    def set_use_altitude(self, use_altitude: float) -> 'AppSettings':
        common.check_type(use_altitude, [int, float])

        self._proto.use_altitude = use_altitude
        return self


class NetworkType(enum.Enum):
    NO_NETWORK: int = 0
    WIFI: int = 1
    CELLULAR: int = 2

    @staticmethod
    def from_proto(network_type: redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.NetworkType) -> 'NetworkType':
        return NetworkType(network_type)

    def into_proto(self) -> redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.NetworkType:
        return redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.NetworkType.Value(self.name)


class WifiWakeLock(enum.Enum):
    NONE: int = 0
    HIGH_PERF: int = 1
    LOW_LATENCY: int = 2
    OTHER: int = 3

    @staticmethod
    def from_proto(wifi_wake_lock: redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock) -> 'WifiWakeLock':
        return WifiWakeLock(wifi_wake_lock)

    def into_proto(self) -> redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock:
        return redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock.Value(self.name)


class CellServiceState(enum.Enum):
    UNKNOWN: int = 0
    EMERGENCY: int = 1
    NOMINAL: int = 2
    OUT_OF_SERVICE: int = 3
    POWER_OFF: int = 4

    @staticmethod
    def from_proto(cell_service_state: redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.CellServiceState) -> 'CellServiceState':
        return CellServiceState(cell_service_state)

    def into_proto(self) -> redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.CellServiceState:
        return redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.CellServiceState.Value(self.name)


class PowerState(enum.Enum):
    UNPLUGGED: int = 0
    CHARGING: int = 1
    CHARGED: int = 2

    @staticmethod
    def from_proto(power_state: redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.PowerState) -> 'PowerState':
        return PowerState(power_state)

    def into_proto(self) -> redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.PowerState:
        return redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.PowerState.Value(self.name)


class StationMetrics(common.ProtoBase):
    def __init__(self, station_metrics_proto: redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics):
        super().__init__(station_metrics_proto)
        self._timestamps = common.TimingPayload(station_metrics_proto.timestamps)
        self._network_strength: common.SamplePayload = common.SamplePayload(station_metrics_proto.network_strength)
        self._temperature: common.SamplePayload = common.SamplePayload(station_metrics_proto.temperature)
        self._battery: common.SamplePayload = common.SamplePayload(station_metrics_proto.battery)
        self._battery_current: common.SamplePayload = common.SamplePayload(station_metrics_proto.battery_current)
        self._available_ram: common.SamplePayload = common.SamplePayload(station_metrics_proto.available_ram)
        self._available_disk: common.SamplePayload = common.SamplePayload(station_metrics_proto.available_disk)
        self._cpu_utilization: common.SamplePayload = common.SamplePayload(station_metrics_proto.cpu_utilization)

    def get_timestamps(self) -> common.TimingPayload:
        return self._timestamps

    def get_network_type(self) -> List[NetworkType]:
        network_type: List[
            redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.NetworkType] = self._proto.network_type
        return list(map(lambda network: NetworkType(network), network_type))

    def set_network_type(self, network_type: List[NetworkType]) -> 'StationMetrics':
        network_types: List[redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.NetworkType] = list(map(
            lambda net_type: redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.NetworkType.Value(
                net_type.name), network_type))
        self._proto.network_type[:] = network_types
        return self

    def get_cell_service_state(self) -> List[CellServiceState]:
        cell_service_state: List[
            redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.CellServiceState] = self._proto.cell_service_state
        return list(map(lambda cell_service: CellServiceState(cell_service), cell_service_state))

    def set_cell_service_state(self, cell_service_state: List[CellServiceState]) -> 'StationMetrics':
        cell_states: List[redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.CellServiceState] = list(map(
            lambda cell_serv: redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.CellServiceState.Value(
                cell_serv.name), cell_service_state))
        self._proto.cell_service_state[:] = cell_states
        return self

    def get_power_state(self) -> List[PowerState]:
        power_state: List[
            redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.PowerState] = self._proto.power_state
        return list(map(lambda pow_state: PowerState(pow_state), power_state))

    def set_power_state(self, power_state: List[PowerState]) -> 'StationMetrics':
        power_states: List[redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.PowerState] = list(map(
            lambda pow_state: redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.PowerState.Value(
                pow_state.name), power_state))
        self._proto.power_state[:] = power_states
        return self

    def get_network_strength(self) -> common.SamplePayload:
        return self._network_strength

    def get_temperature(self) -> common.SamplePayload:
        return self._temperature

    def get_battery(self) -> common.SamplePayload:
        return self._battery

    def get_battery_current(self) -> common.SamplePayload:
        return self._battery_current

    def get_available_ram(self) -> common.SamplePayload:
        return self._available_ram

    def get_available_disk(self) -> common.SamplePayload:
        return self._available_disk

    def get_cpu_utilization(self) -> common.SamplePayload:
        return self._cpu_utilization

    def get_wifi_wake_loc(self) -> WifiWakeLock:
        return WifiWakeLock(self._proto.wifi_wake_lock)

    def set_wifi_wake_loc(self, wifi_wake_loc: WifiWakeLock) -> 'StationMetrics':
        common.check_type(wifi_wake_loc, [WifiWakeLock])
        self._proto.wifi_wake_loc = redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock.Value(
            wifi_wake_loc.name)
        return self


class OsType(enum.Enum):
    ANDROID: int = 0
    IOS: int = 1
    LINUX: int = 2
    WINDOWS: int = 3

    @staticmethod
    def from_proto(os_type: redvox_api_m_pb2.RedvoxPacketM.StationInformation.OsType) -> 'OsType':
        return OsType(os_type)

    def into_proto(self) -> redvox_api_m_pb2.RedvoxPacketM.StationInformation.OsType:
        return redvox_api_m_pb2.RedvoxPacketM.StationInformation.OsType.Value(self.name)


class StationInformation(common.ProtoBase):
    def __init__(self, station_information_proto: redvox_api_m_pb2.RedvoxPacketM.StationInformation):
        super().__init__(station_information_proto)
        self._app_settings: AppSettings = AppSettings(station_information_proto.app_settings)
        self._station_metrics: StationMetrics = StationMetrics(station_information_proto.station_metrics)

    @staticmethod
    def new() -> 'StationInformation':
        return StationInformation(redvox_api_m_pb2.RedvoxPacketM.StationInformation())

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
        self._proto.os = redvox_api_m_pb2.RedvoxPacketM.StationInformation.OsType.Value(os.name)
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

    def get_station_metrics(self) -> StationMetrics:
        return self._station_metrics
