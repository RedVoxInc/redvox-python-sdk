"""
This module provides access to underlying station information from RedVox API M data.
"""

import enum
from typing import List, Optional

import redvox.api1000.common.typing
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.common.common as common
import redvox.api1000.common.generic

from redvox.api1000.common.decorators import wrap_enum

_NETWORK_TYPE_FIELD_NAME: str = "network_type"
_CELL_SERVICE_STATE_FIELD_NAME: str = "cell_service_state"
_POWER_STATE_FIELD_NAME: str = "power_state"
_ADDITIONAL_INPUT_SENSORS_FIELD_NAME: str = "additional_input_sensors"
_WIFI_WAKE_LOCK_FIELD_NAME: str = "wifi_wake_lock"

InputSensorProto = redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.InputSensor


# noinspection Mypy
@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate)
class AudioSamplingRate(enum.Enum):
    """
    Sampling Rate as provided by the app settings.
    """
    UNKNOWN_SAMPLING_RATE: int = 0
    HZ_80: int = 1
    HZ_800: int = 2
    HZ_8000: int = 3
    HZ_16000: int = 4
    HZ_48000: int = 5

    @staticmethod
    def from_sampling_rate(sampling_rate: float) -> Optional['AudioSamplingRate']:
        """
        Convert from a numeric sampling rate into this enum.
        :param sampling_rate: Numeric sampling rate.
        :return: An instance of this enum.
        """
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
            return AudioSamplingRate['UNKNOWN_SAMPLING_RATE']


# noinspection Mypy
@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning)
class AudioSourceTuning(enum.Enum):
    """
    Audio source tuning from app settings
    """
    UNKNOWN_TUNING: int = 0
    INFRASOUND_TUNING: int = 1
    LOW_AUDIO_TUNING: int = 2
    AUDIO_TUNING: int = 3


# noinspection Mypy
@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.InputSensor)
class InputSensor(enum.Enum):
    """
    Input sensors provided to additional input sensors in the app settings.
    """
    UNKNOWN_SENSOR: int = 0
    ACCELEROMETER = 1
    AMBIENT_TEMPERATURE = 2
    AUDIO = 3
    COMPRESSED_AUDIO = 4
    GRAVITY = 5
    GYROSCOPE = 6
    IMAGE = 7
    LIGHT = 8
    LINEAR_ACCELERATION = 9
    LOCATION = 10
    MAGNETOMETER = 11
    ORIENTATION = 12
    PRESSURE = 13
    PROXIMITY = 14
    RELATIVE_HUMIDITY = 15
    ROTATION_VECTOR = 16


# noinspection Mypy
@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.FftOverlap)
class FftOverlap(enum.Enum):
    """
    FFT overlap provided by the app settings
    """
    UNKNOWN: int = 0
    PERCENT_25: int = 1
    PERCENT_50: int = 2
    PERCENT_75: int = 3


class AppSettings(
        redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings]):
    """
    Represents a copy of the App's settings.
    """

    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings):
        super().__init__(proto)
        # noinspection Mypy
        self._additional_input_sensors: redvox.api1000.common.generic.ProtoRepeatedMessage[
            InputSensorProto, InputSensor] = \
            redvox.api1000.common.generic.ProtoRepeatedMessage(
                proto,
                proto.additional_input_sensors,
                _ADDITIONAL_INPUT_SENSORS_FIELD_NAME,
                InputSensor.from_proto,
                InputSensor.into_proto
            )

    @staticmethod
    def new() -> 'AppSettings':
        """
        Creates a new, empty AppSettings instance
        :return: A new, empty AppSettings instance
        """
        return AppSettings(redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings())

    def get_audio_sampling_rate(self) -> AudioSamplingRate:
        """
        :return: Returns the sampling rate provided in the settings.
        """
        return AudioSamplingRate(self.get_proto().audio_sampling_rate)

    def set_audio_sampling_rate(self, audio_sampling_rate: AudioSamplingRate) -> 'AppSettings':
        """
        Sets the audio sampling rate.
        :param audio_sampling_rate: Rate to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(audio_sampling_rate, [AudioSamplingRate])

        self.get_proto().audio_sampling_rate = \
            redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate.Value(
                audio_sampling_rate.name)
        return self

    def get_samples_per_window(self) -> float:
        """
        :return: The number of samples per window as defined in the app settings.
        """
        return self.get_proto().samples_per_window

    def set_samples_per_window(self, samples_per_window: float) -> 'AppSettings':
        """
        Sets the number of samples per window for storage in the app settings.
        :param samples_per_window: Samples per window.
        :return: A modified instance of self.
        """
        redvox.api1000.common.typing.check_type(samples_per_window, [int, float])
        self.get_proto().samples_per_window = samples_per_window
        return self

    def get_audio_source_tuning(self) -> AudioSourceTuning:
        """
        :return: The AudioSourceTuning
        """
        return AudioSourceTuning(self.get_proto().audio_source_tuning)

    def set_audio_source_tuning(self, audio_source_tuning: AudioSourceTuning) -> 'AppSettings':
        """
        Sets the AudioSourceTuning.
        :param audio_source_tuning: Tuning to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(audio_source_tuning, [AudioSourceTuning])

        self.get_proto().audio_source_tuning = \
            redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning.Value(
                audio_source_tuning.name)
        return self

    def get_additional_input_sensors(self) -> redvox.api1000.common.generic.ProtoRepeatedMessage:
        """
        :return: Additional input sensors specified in the settings.
        """
        return self._additional_input_sensors

    def get_fft_overlap(self) -> FftOverlap:
        """
        :return: FFT overlap as specified in the settings
        """
        return FftOverlap(self.get_proto().fft_overlap)

    def set_fft_overlap(self, fft_overlap: FftOverlap) -> 'AppSettings':
        """
        Sets the fft overlap in the settings
        :param fft_overlap: Overlap to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(fft_overlap, [FftOverlap])

        self.get_proto().fft_overlap = redvox_api_m_pb2.RedvoxPacketM.StationInformation.AppSettings.FftOverlap.Value(
            fft_overlap.name)
        return self

    def get_automatically_record(self) -> bool:
        """
        :return: Is automatically record set in the settings?
        """
        return self.get_proto().automatically_record

    def set_automatically_record(self, automatically_record: bool) -> 'AppSettings':
        """
        Sets automatically record in the settings.
        :param automatically_record: Setting to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(automatically_record, [bool])
        self.get_proto().automatically_record = automatically_record
        return self

    def get_launch_at_power_up(self) -> bool:
        """
        :return: Is launch at power up set in settings?
        """
        return self.get_proto().launch_at_power_up

    def set_launch_at_power_up(self, launch_at_power_up: bool) -> 'AppSettings':
        """
        Sets launch at power up in settings.
        :param launch_at_power_up: Setting to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(launch_at_power_up, [bool])
        self.get_proto().launch_at_power_up = launch_at_power_up
        return self

    def get_station_id(self) -> str:
        """
        :return: Station id provided in settings
        """
        return self.get_proto().station_id

    def set_station_id(self, station_id: str) -> 'AppSettings':
        """
        Sets the station id in the settings.
        :param station_id: Station id to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(station_id, [str])
        self.get_proto().station_id = station_id
        return self

    def get_station_description(self) -> str:
        """
        :return: Station description set in settings.`
        """
        return self.get_proto().station_description

    def set_station_description(self, station_description: str) -> 'AppSettings':
        """
        Sets the station description in the settings.
        :param station_description: Description to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(station_description, [str])
        self.get_proto().station_description = station_description
        return self

    def get_push_to_server(self) -> bool:
        """
        :return: Is push to server set in the settings?
        """
        return self.get_proto().push_to_server

    def set_push_to_server(self, push_to_server: bool) -> 'AppSettings':
        """
        Sets push to server in the settings.
        :param push_to_server: Setting to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(push_to_server, [bool])
        self.get_proto().push_to_server = push_to_server
        return self

    def get_publish_data_as_private(self) -> bool:
        """
        :return: Is publish data as private set in the settings?
        """
        return self.get_proto().publish_data_as_private

    def set_publish_data_as_private(self, publish_data_as_private: bool) -> 'AppSettings':
        """
        Sets publish data as private in the settings.
        :param publish_data_as_private: Setting to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(publish_data_as_private, [bool])
        self.get_proto().publish_data_as_private = publish_data_as_private
        return self

    def get_scramble_audio_data(self) -> bool:
        """
        :return: Is scramble audio set in the settings?
        """
        return self.get_proto().scramble_audio_data

    def set_scramble_audio_data(self, scramble_audio_data: bool) -> 'AppSettings':
        """
        Sets scramble audio in the settings.
        :param scramble_audio_data: Setting to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(scramble_audio_data, [bool])
        self.get_proto().scramble_audio_data = scramble_audio_data
        return self

    def get_provide_backfill(self) -> bool:
        """
        :return: Is provide backfill set in the settings?
        """
        return self.get_proto().provide_backfill

    def set_provide_backfill(self, provide_backfill: bool) -> 'AppSettings':
        """
        Sets backfill in the settings.
        :param provide_backfill: Setting to set.
        :return: A modified instance of self.
        """
        redvox.api1000.common.typing.check_type(provide_backfill, [bool])
        self.get_proto().provide_backfill = provide_backfill
        return self

    def get_remove_sensor_dc_offset(self) -> bool:
        """
        :return: Is remove dc offset set in the settings?
        """
        return self.get_proto().remove_sensor_dc_offset

    def set_remove_sensor_dc_offset(self, remove_sensor_dc_offset: bool) -> 'AppSettings':
        """
        Sets remove DC offset in the settings.
        :param remove_sensor_dc_offset: Setting to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(remove_sensor_dc_offset, [bool])
        self.get_proto().remove_sensor_dc_offset = remove_sensor_dc_offset
        return self

    def get_use_custom_time_sync_server(self) -> bool:
        """
        :return: Is use custom sync server set in settings?
        """
        return self.get_proto().use_custom_time_sync_server

    def set_use_custom_time_sync_server(self, use_custom_time_sync_server: bool) -> 'AppSettings':
        """
        Sets use custom synch server in settings.
        :param use_custom_time_sync_server: Setting to set.
        :return: A modified instance of self.
        """
        redvox.api1000.common.typing.check_type(use_custom_time_sync_server, [bool])
        self.get_proto().use_custom_time_sync_server = use_custom_time_sync_server
        return self

    def get_time_sync_server_url(self) -> str:
        """
        :return: Custom synch url from settings.
        """
        return self.get_proto().time_sync_server_url

    def set_time_sync_server_url(self, time_sync_server_url: str) -> 'AppSettings':
        """
        Sets the custom synch url in the settings.
        :param time_sync_server_url: URL to set.
        :return: A modified instance of self.
        """
        redvox.api1000.common.typing.check_type(time_sync_server_url, [str])
        self.get_proto().time_sync_server_url = time_sync_server_url
        return self

    def get_use_custom_data_server(self) -> bool:
        """
        :return: Is use custom data server set in settings?
        """
        return self.get_proto().use_custom_data_server

    def set_use_custom_data_server(self, use_custom_data_server: bool) -> 'AppSettings':
        """
        Set use custom data server in settings.
        :param use_custom_data_server: Setting to set.
        :return: A modified instance of self.
        """
        redvox.api1000.common.typing.check_type(use_custom_data_server, [bool])
        self.get_proto().use_custom_data_server = use_custom_data_server
        return self

    def get_data_server_url(self) -> str:
        """
        :return: Custom data server url in settings.
        """
        return self.get_proto().data_server_url

    def set_data_server_url(self, data_server_url: str) -> 'AppSettings':
        """
        Sets custom data server url in settings.
        :param data_server_url: Url to set.
        :return: A modified instance of self.
        """
        redvox.api1000.common.typing.check_type(data_server_url, [str])
        self.get_proto().data_server_url = data_server_url
        return self

    def get_use_custom_auth_server(self) -> bool:
        """
        :return: Use custom auth server set in settings?
        """
        return self.get_proto().use_custom_auth_server

    def set_use_custom_auth_server(self, use_custom_auth_server: bool) -> 'AppSettings':
        """
        Set use custom auth server in settings.
        :param use_custom_auth_server: Setting to set.
        :return: Modified instance of self
        """
        redvox.api1000.common.typing.check_type(use_custom_auth_server, [bool])
        self.get_proto().use_custom_auth_server = use_custom_auth_server
        return self

    def get_auth_server_url(self) -> str:
        """
        :return: Custom auth server url from settings
        """
        return self.get_proto().auth_server_url

    def set_auth_server_url(self, auth_server_url: str) -> 'AppSettings':
        """
        Set custom auth server url in settings.
        :param auth_server_url: Url to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(auth_server_url, [str])
        self.get_proto().auth_server_url = auth_server_url
        return self

    def get_auto_delete_data_files(self) -> bool:
        """
        :return: Auto delete files set in settings?
        """
        return self.get_proto().auto_delete_data_files

    def set_auto_delete_data_files(self, auto_delete_data_files: bool) -> 'AppSettings':
        """
        Set auto delete data files in settings.
        :param auto_delete_data_files: Setting to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(auto_delete_data_files, [bool])
        self.get_proto().auto_delete_data_files = auto_delete_data_files
        return self

    def get_storage_space_allowance(self) -> float:
        """
        :return: Amount of storage space allowance set in settings.
        """
        return self.get_proto().storage_space_allowance

    def set_storage_space_allowance(self, storage_space_allowance: float) -> 'AppSettings':
        """
        Set storage space allowance in settings.
        :param storage_space_allowance: Allowance to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(storage_space_allowance, [int, float])

        self.get_proto().storage_space_allowance = storage_space_allowance
        return self

    def get_use_sd_card_for_data_storage(self) -> bool:
        """
        :return: Use SD card set in settings?
        """
        return self.get_proto().use_sd_card_for_data_storage

    def set_use_sd_card_for_data_storage(self, use_sd_card_for_data_storage: bool) -> 'AppSettings':
        """
        Set use SD card in settings.
        :param use_sd_card_for_data_storage: Setting to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(use_sd_card_for_data_storage, [bool])
        self.get_proto().use_sd_card_for_data_storage = use_sd_card_for_data_storage
        return self

    def get_use_location_services(self) -> bool:
        """
        :return: Use location services set in settings?
        """
        return self.get_proto().use_location_services

    def set_use_location_services(self, use_location_services: bool) -> 'AppSettings':
        """
        Sets use location services in settings.
        :param use_location_services: Setting to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(use_location_services, [bool])
        self.get_proto().use_location_services = use_location_services
        return self

    def get_use_latitude(self) -> float:
        """
        :return: Custom latitude provided in settings.
        """
        return self.get_proto().use_latitude

    def set_use_latitude(self, use_latitude: float) -> 'AppSettings':
        """
        Set custom latitude in settings.
        :param use_latitude: Latitude to set.
        :return: A modified instance of self.
        """
        redvox.api1000.common.typing.check_type(use_latitude, [int, float])

        self.get_proto().use_latitude = use_latitude
        return self

    def get_use_longitude(self) -> float:
        """
        :return: Custom longitude from settings.
        """
        return self.get_proto().use_longitude

    def set_use_longitude(self, use_longitude: float) -> 'AppSettings':
        """
        Sets custom longitude in settings.
        :param use_longitude: Longitude to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(use_longitude, [int, float])

        self.get_proto().use_longitude = use_longitude
        return self

    def get_use_altitude(self) -> float:
        """
        :return: Custom altitude set in settings
        """
        return self.get_proto().use_altitude

    def set_use_altitude(self, use_altitude: float) -> 'AppSettings':
        """
        Set custom altitude in settings.
        :param use_altitude: Altitude to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(use_altitude, [int, float])

        self.get_proto().use_altitude = use_altitude
        return self


def validate_app_settings(app_settings: AppSettings) -> List[str]:
    """
    Validates the app settings.
    :param app_settings: App settings to validate
    :return: List of validation errors
    """
    errors_list = []
    if app_settings.get_audio_sampling_rate() not in AudioSamplingRate:
        errors_list.append("App settings audio sample rate is not a valid sample rate")
    if app_settings.get_station_id() == "":
        errors_list.append("App settings station id is missing")
    return errors_list


# noinspection Mypy,DuplicatedCode
@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.NetworkType)
class NetworkType(enum.Enum):
    """
    Network type for station metrics
    """
    UNKNOWN_NETWORK: int = 0
    NO_NETWORK: int = 1
    WIFI: int = 2
    CELLULAR: int = 3
    WIRED: int = 4


# noinspection Mypy
@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock)
class WifiWakeLock(enum.Enum):
    """
    WiFi wake lock states for station metrics
    """
    NONE: int = 0
    HIGH_PERF: int = 1
    LOW_LATENCY: int = 2
    OTHER: int = 3


# noinspection Mypy
@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.CellServiceState)
class CellServiceState(enum.Enum):
    """
    Cell service state for station metrics
    """
    UNKNOWN: int = 0
    EMERGENCY: int = 1
    NOMINAL: int = 2
    OUT_OF_SERVICE: int = 3
    POWER_OFF: int = 4


# noinspection Mypy
@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics.PowerState)
class PowerState(enum.Enum):
    """
    Power state for station metrics
    """
    UNKNOWN_POWER_STATE: int = 0
    UNPLUGGED: int = 1
    CHARGING: int = 2
    CHARGED: int = 3


class StationMetrics(
        redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics]):
    """
    A collection of timestamps metrics relating to station state.
    """
    # noinspection Mypy
    def __init__(self, station_metrics_proto: redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics):
        super().__init__(station_metrics_proto)
        self._timestamps = common.TimingPayload(station_metrics_proto.timestamps).set_default_unit()
        self._network_type: redvox.api1000.common.generic.ProtoRepeatedMessage = \
            redvox.api1000.common.generic.ProtoRepeatedMessage(
                station_metrics_proto,
                station_metrics_proto.network_type,
                _NETWORK_TYPE_FIELD_NAME,
                NetworkType.from_proto,
                NetworkType.into_proto)
        self._cell_service_state: redvox.api1000.common.generic.ProtoRepeatedMessage = \
            redvox.api1000.common.generic.ProtoRepeatedMessage(
                station_metrics_proto,
                station_metrics_proto.cell_service_state,
                _CELL_SERVICE_STATE_FIELD_NAME,
                CellServiceState.from_proto,
                CellServiceState.into_proto)
        # noinspection PyTypeChecker
        self._network_strength: common.SamplePayload = common.SamplePayload(station_metrics_proto.network_strength) \
            .set_unit(common.Unit.DECIBEL)
        # noinspection PyTypeChecker
        self._temperature: common.SamplePayload = common.SamplePayload(station_metrics_proto.temperature) \
            .set_unit(common.Unit.DEGREES_CELSIUS)
        # noinspection PyTypeChecker
        self._battery: common.SamplePayload = common.SamplePayload(station_metrics_proto.battery) \
            .set_unit(common.Unit.PERCENTAGE)
        # noinspection PyTypeChecker
        self._battery_current: common.SamplePayload = common.SamplePayload(station_metrics_proto.battery_current) \
            .set_unit(common.Unit.MICROAMPERES)
        # noinspection PyTypeChecker
        self._available_ram: common.SamplePayload = common.SamplePayload(station_metrics_proto.available_ram) \
            .set_unit(common.Unit.BYTE)
        # noinspection PyTypeChecker
        self._available_disk: common.SamplePayload = common.SamplePayload(station_metrics_proto.available_disk) \
            .set_unit(common.Unit.BYTE)
        # noinspection PyTypeChecker
        self._cpu_utilization: common.SamplePayload = common.SamplePayload(station_metrics_proto.cpu_utilization) \
            .set_unit(common.Unit.PERCENTAGE)
        self._power_state: redvox.api1000.common.generic.ProtoRepeatedMessage = \
            redvox.api1000.common.generic.ProtoRepeatedMessage(
                station_metrics_proto,
                station_metrics_proto.power_state,
                _POWER_STATE_FIELD_NAME,
                PowerState.from_proto,
                PowerState.into_proto)
        self._wifi_wake_loc: redvox.api1000.common.generic.ProtoRepeatedMessage = \
            redvox.api1000.common.generic.ProtoRepeatedMessage(
                station_metrics_proto,
                station_metrics_proto.wifi_wake_lock,
                _WIFI_WAKE_LOCK_FIELD_NAME,
                WifiWakeLock.from_proto,
                WifiWakeLock.into_proto)

    @staticmethod
    def new() -> 'StationMetrics':
        """
        :return: A new, empty StationMetrics instance
        """
        return StationMetrics(redvox_api_m_pb2.RedvoxPacketM.StationInformation.StationMetrics())

    def get_timestamps(self) -> common.TimingPayload:
        """
        :return: Timestamps associated with each metric.
        """
        return self._timestamps

    def get_network_type(self) -> redvox.api1000.common.generic.ProtoRepeatedMessage:
        """
        :return: A payload of network types.
        """
        return self._network_type

    def get_cell_service_state(self) -> redvox.api1000.common.generic.ProtoRepeatedMessage:
        """
        :return: A payload of cell service state
        """
        return self._cell_service_state

    def get_network_strength(self) -> common.SamplePayload:
        """
        :return: A payload of network strengths
        """
        return self._network_strength

    def get_temperature(self) -> common.SamplePayload:
        """
        :return: A payload of temperatures
        """
        return self._temperature

    def get_battery(self) -> common.SamplePayload:
        """
        :return: A payload of battery remaining
        """
        return self._battery

    def get_battery_current(self) -> common.SamplePayload:
        """
        :return: A payload of battery current
        """
        return self._battery_current

    def get_available_ram(self) -> common.SamplePayload:
        """
        :return: A payload of available RAM
        """
        return self._available_ram

    def get_available_disk(self) -> common.SamplePayload:
        """
        :return: A payload of available disk
        """
        return self._available_disk

    def get_cpu_utilization(self) -> common.SamplePayload:
        """
        :return: A payload CPU utilization
        """
        return self._cpu_utilization

    def get_power_state(self) -> redvox.api1000.common.generic.ProtoRepeatedMessage:
        """
        :return: A payload of power states
        """
        return self._power_state

    def get_wifi_wake_loc(self) -> redvox.api1000.common.generic.ProtoRepeatedMessage:
        """
        :return: A payload of Wifi wake lock states
        """
        return self._wifi_wake_loc


class ServiceUrls(
        redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.StationInformation.ServiceUrls]):
    """
    A collection of URLs utilized while collecting, authenticating, and transmitting the data.
    """
    def __init__(self, service_urls_proto: redvox_api_m_pb2.RedvoxPacketM.StationInformation.ServiceUrls):
        super().__init__(service_urls_proto)

    @staticmethod
    def new() -> 'ServiceUrls':
        """
        :return: A new, empty ServiceUrls instance
        """
        return ServiceUrls(redvox_api_m_pb2.RedvoxPacketM.StationInformation.ServiceUrls())

    def get_auth_server(self) -> str:
        """
        :return: The authentication server URL.
        """
        return self.get_proto().auth_server

    def set_auth_server(self, _auth_server: str) -> 'ServiceUrls':
        """
        Sets the authentication server url
        :param _auth_server: Url to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(_auth_server, [str])
        self.get_proto().auth_server = _auth_server
        return self

    def get_synch_server(self) -> str:
        """
        :return: The time synchronization URL.
        """
        return self.get_proto().synch_server

    def set_synch_server(self, _synch_server: str) -> 'ServiceUrls':
        """
        Sets the time synchronization URL.
        :param _synch_server: URL to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(_synch_server, [str])
        self.get_proto().synch_server = _synch_server
        return self

    def get_acquisition_server(self) -> str:
        """
        :return: The data acquisition server URL
        """
        return self.get_proto().acquisition_server

    def set_acquisition_server(self, _acquisition_server: str) -> 'ServiceUrls':
        """
        Sets the data acquisition server URL
        :param _acquisition_server: URL to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(_acquisition_server, [str])
        self.get_proto().acquisition_server = _acquisition_server
        return self


def validate_station_metrics(station_metrics: StationMetrics) -> List[str]:
    """
    Validates the station metrics.
    :param station_metrics: Metrics to validate.
    :return: A list of validation errors.
    """
    # only check if timestamps are valid right now
    # todo: determine if other stuff needs to be validated as well
    return common.validate_timing_payload(station_metrics.get_timestamps())


# noinspection Mypy
@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.StationInformation.OsType)
class OsType(enum.Enum):
    """
    Type-safe OS enumeration for station info
    """
    UNKNOWN_OS: int = 0
    ANDROID: int = 1
    IOS: int = 2
    OSX: int = 3
    LINUX: int = 4
    WINDOWS: int = 5


class StationInformation(
        redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.StationInformation]):
    """
    A collection of station related metadata, settings, and metrics.
    """
    def __init__(self, station_information_proto: redvox_api_m_pb2.RedvoxPacketM.StationInformation):
        super().__init__(station_information_proto)
        self._app_settings: AppSettings = AppSettings(station_information_proto.app_settings)
        self._station_metrics: StationMetrics = StationMetrics(station_information_proto.station_metrics)
        self._service_urls: ServiceUrls = ServiceUrls(station_information_proto.service_urls)

    @staticmethod
    def new() -> 'StationInformation':
        """
        :return: A new, empty StationInformation instance
        """
        return StationInformation(redvox_api_m_pb2.RedvoxPacketM.StationInformation())

    def get_id(self) -> str:
        """
        :return: The station id
        """
        return self.get_proto().id

    def set_id(self, _id: str) -> 'StationInformation':
        """
        Sets the station id
        :param _id: Id to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(_id, [str])
        self.get_proto().id = _id
        return self

    def get_uuid(self) -> str:
        """
        :return: The station UUID
        """
        return self.get_proto().uuid

    def set_uuid(self, uuid: str) -> 'StationInformation':
        """
        Sets the station uuid.
        :param uuid: uuid to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(uuid, [str])
        self.get_proto().uuid = uuid
        return self

    def get_description(self) -> str:
        """
        :return: The station's description.
        """
        return self.get_proto().description

    def set_description(self, description: str) -> 'StationInformation':
        """
        Sets the station's description
        :param description: Description of the station
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(description, [str])
        self.get_proto().description = description
        return self

    def get_auth_id(self) -> str:
        """
        :return: The station's authentication id
        """
        return self.get_proto().auth_id

    def set_auth_id(self, auth_id: str) -> 'StationInformation':
        """
        Sets the station's authentication id
        :param auth_id: Authentication id to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(auth_id, [str])
        self.get_proto().auth_id = auth_id
        return self

    def get_make(self) -> str:
        """
        :return: The station's make
        """
        return self.get_proto().make

    def set_make(self, make: str) -> 'StationInformation':
        """
        Sets the station's make
        :param make: Make to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(make, [str])
        self.get_proto().make = make
        return self

    def get_model(self) -> str:
        """
        :return: The station's model
        """
        return self.get_proto().model

    def set_model(self, model: str) -> 'StationInformation':
        """
        Sets the station's model
        :param model: Model to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(model, [str])
        self.get_proto().model = model
        return self

    def get_os(self) -> OsType:
        """
        :return: The station's OS
        """
        return OsType(self.get_proto().os)

    def set_os(self, os: OsType) -> 'StationInformation':
        """
        Sets the station's OS
        :param os: OS to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(os, [OsType])
        self.get_proto().os = redvox_api_m_pb2.RedvoxPacketM.StationInformation.OsType.Value(os.name)
        return self

    def get_os_version(self) -> str:
        """
        :return: The station's OS version
        """
        return self.get_proto().os_version

    def set_os_version(self, os_version: str) -> 'StationInformation':
        """
        Sets the station's OS version
        :param os_version: OS version to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(os_version, [str])
        self.get_proto().os_version = os_version
        return self

    def get_app_version(self) -> str:
        """
        :return: The station's app version
        """
        return self.get_proto().app_version

    def set_app_version(self, app_version: str) -> 'StationInformation':
        """
        Sets the station's app version.
        :param app_version: App version to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(app_version, [str])
        self.get_proto().app_version = app_version
        return self

    def get_is_private(self) -> bool:
        """
        :return: If this station was recording privately.
        """
        return self.get_proto().is_private

    def set_is_private(self, is_private: bool) -> 'StationInformation':
        """
        Sets if this station is recording privately.
        :param is_private: True if private, False otherwise
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(is_private, [bool])
        self.get_proto().is_private = is_private
        return self

    def get_app_settings(self) -> AppSettings:
        """
        :return: This station's copy of its settings
        """
        return self._app_settings

    def get_station_metrics(self) -> StationMetrics:
        """
        :return: Metrics associated with this station.
        """
        return self._station_metrics

    def get_service_urls(self) -> ServiceUrls:
        """
        :return: URLs used to service this station.
        """
        return self._service_urls


def validate_station_information(station_info: StationInformation) -> List[str]:
    """
    Validates station information.
    :param station_info: Station information to validate.
    :return: A list of validation errors.
    """
    errors_list = validate_app_settings(station_info.get_app_settings())
    errors_list.extend(validate_station_metrics(station_info.get_station_metrics()))
    if station_info.get_id() == "":
        errors_list.append("Station information station id missing")
    if station_info.get_uuid() == "":
        errors_list.append("Station information station uuid missing")
    return errors_list
