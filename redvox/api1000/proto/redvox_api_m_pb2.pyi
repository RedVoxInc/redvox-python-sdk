from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RedvoxPacketM(_message.Message):
    __slots__ = ["api", "sub_api", "station_information", "timing_information", "sensors", "event_streams", "metadata"]
    class Unit(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        UNKNOWN: _ClassVar[RedvoxPacketM.Unit]
        METERS_PER_SECOND_SQUARED: _ClassVar[RedvoxPacketM.Unit]
        KILOPASCAL: _ClassVar[RedvoxPacketM.Unit]
        RADIANS_PER_SECOND: _ClassVar[RedvoxPacketM.Unit]
        DECIMAL_DEGREES: _ClassVar[RedvoxPacketM.Unit]
        METERS: _ClassVar[RedvoxPacketM.Unit]
        METERS_PER_SECOND: _ClassVar[RedvoxPacketM.Unit]
        MICROTESLA: _ClassVar[RedvoxPacketM.Unit]
        LSB_PLUS_MINUS_COUNTS: _ClassVar[RedvoxPacketM.Unit]
        MICROSECONDS_SINCE_UNIX_EPOCH: _ClassVar[RedvoxPacketM.Unit]
        DECIBEL: _ClassVar[RedvoxPacketM.Unit]
        DEGREES_CELSIUS: _ClassVar[RedvoxPacketM.Unit]
        BYTE: _ClassVar[RedvoxPacketM.Unit]
        PERCENTAGE: _ClassVar[RedvoxPacketM.Unit]
        RADIANS: _ClassVar[RedvoxPacketM.Unit]
        MICROAMPERES: _ClassVar[RedvoxPacketM.Unit]
        CENTIMETERS: _ClassVar[RedvoxPacketM.Unit]
        NORMALIZED_COUNTS: _ClassVar[RedvoxPacketM.Unit]
        LUX: _ClassVar[RedvoxPacketM.Unit]
        UNITLESS: _ClassVar[RedvoxPacketM.Unit]
        PCM: _ClassVar[RedvoxPacketM.Unit]
    UNKNOWN: RedvoxPacketM.Unit
    METERS_PER_SECOND_SQUARED: RedvoxPacketM.Unit
    KILOPASCAL: RedvoxPacketM.Unit
    RADIANS_PER_SECOND: RedvoxPacketM.Unit
    DECIMAL_DEGREES: RedvoxPacketM.Unit
    METERS: RedvoxPacketM.Unit
    METERS_PER_SECOND: RedvoxPacketM.Unit
    MICROTESLA: RedvoxPacketM.Unit
    LSB_PLUS_MINUS_COUNTS: RedvoxPacketM.Unit
    MICROSECONDS_SINCE_UNIX_EPOCH: RedvoxPacketM.Unit
    DECIBEL: RedvoxPacketM.Unit
    DEGREES_CELSIUS: RedvoxPacketM.Unit
    BYTE: RedvoxPacketM.Unit
    PERCENTAGE: RedvoxPacketM.Unit
    RADIANS: RedvoxPacketM.Unit
    MICROAMPERES: RedvoxPacketM.Unit
    CENTIMETERS: RedvoxPacketM.Unit
    NORMALIZED_COUNTS: RedvoxPacketM.Unit
    LUX: RedvoxPacketM.Unit
    UNITLESS: RedvoxPacketM.Unit
    PCM: RedvoxPacketM.Unit
    class MetadataEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class StationInformation(_message.Message):
        __slots__ = ["id", "uuid", "description", "auth_id", "make", "model", "os", "os_version", "app_version", "is_private", "app_settings", "station_metrics", "service_urls", "metadata"]
        class OsType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = []
            UNKNOWN_OS: _ClassVar[RedvoxPacketM.StationInformation.OsType]
            ANDROID: _ClassVar[RedvoxPacketM.StationInformation.OsType]
            IOS: _ClassVar[RedvoxPacketM.StationInformation.OsType]
            OSX: _ClassVar[RedvoxPacketM.StationInformation.OsType]
            LINUX: _ClassVar[RedvoxPacketM.StationInformation.OsType]
            WINDOWS: _ClassVar[RedvoxPacketM.StationInformation.OsType]
        UNKNOWN_OS: RedvoxPacketM.StationInformation.OsType
        ANDROID: RedvoxPacketM.StationInformation.OsType
        IOS: RedvoxPacketM.StationInformation.OsType
        OSX: RedvoxPacketM.StationInformation.OsType
        LINUX: RedvoxPacketM.StationInformation.OsType
        WINDOWS: RedvoxPacketM.StationInformation.OsType
        class MetricsRate(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = []
            UNKNOWN: _ClassVar[RedvoxPacketM.StationInformation.MetricsRate]
            ONCE_PER_SECOND: _ClassVar[RedvoxPacketM.StationInformation.MetricsRate]
            ONCE_PER_PACKET: _ClassVar[RedvoxPacketM.StationInformation.MetricsRate]
        UNKNOWN: RedvoxPacketM.StationInformation.MetricsRate
        ONCE_PER_SECOND: RedvoxPacketM.StationInformation.MetricsRate
        ONCE_PER_PACKET: RedvoxPacketM.StationInformation.MetricsRate
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        class ServiceUrls(_message.Message):
            __slots__ = ["auth_server", "synch_server", "acquisition_server", "metadata"]
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            AUTH_SERVER_FIELD_NUMBER: _ClassVar[int]
            SYNCH_SERVER_FIELD_NUMBER: _ClassVar[int]
            ACQUISITION_SERVER_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            auth_server: str
            synch_server: str
            acquisition_server: str
            metadata: _containers.ScalarMap[str, str]
            def __init__(self, auth_server: _Optional[str] = ..., synch_server: _Optional[str] = ..., acquisition_server: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class StationMetrics(_message.Message):
            __slots__ = ["timestamps", "network_type", "cell_service_state", "network_strength", "temperature", "battery", "battery_current", "available_ram", "available_disk", "cpu_utilization", "power_state", "wifi_wake_lock", "screen_state", "screen_brightness", "metadata"]
            class NetworkType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
                UNKNOWN_NETWORK: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.NetworkType]
                NO_NETWORK: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.NetworkType]
                WIFI: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.NetworkType]
                CELLULAR: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.NetworkType]
                WIRED: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.NetworkType]
            UNKNOWN_NETWORK: RedvoxPacketM.StationInformation.StationMetrics.NetworkType
            NO_NETWORK: RedvoxPacketM.StationInformation.StationMetrics.NetworkType
            WIFI: RedvoxPacketM.StationInformation.StationMetrics.NetworkType
            CELLULAR: RedvoxPacketM.StationInformation.StationMetrics.NetworkType
            WIRED: RedvoxPacketM.StationInformation.StationMetrics.NetworkType
            class WifiWakeLock(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
                NONE: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock]
                HIGH_PERF: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock]
                LOW_LATENCY: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock]
                OTHER: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock]
            NONE: RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock
            HIGH_PERF: RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock
            LOW_LATENCY: RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock
            OTHER: RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock
            class CellServiceState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
                UNKNOWN: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.CellServiceState]
                EMERGENCY: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.CellServiceState]
                NOMINAL: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.CellServiceState]
                OUT_OF_SERVICE: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.CellServiceState]
                POWER_OFF: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.CellServiceState]
            UNKNOWN: RedvoxPacketM.StationInformation.StationMetrics.CellServiceState
            EMERGENCY: RedvoxPacketM.StationInformation.StationMetrics.CellServiceState
            NOMINAL: RedvoxPacketM.StationInformation.StationMetrics.CellServiceState
            OUT_OF_SERVICE: RedvoxPacketM.StationInformation.StationMetrics.CellServiceState
            POWER_OFF: RedvoxPacketM.StationInformation.StationMetrics.CellServiceState
            class PowerState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
                UNKNOWN_POWER_STATE: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.PowerState]
                UNPLUGGED: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.PowerState]
                CHARGING: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.PowerState]
                CHARGED: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.PowerState]
            UNKNOWN_POWER_STATE: RedvoxPacketM.StationInformation.StationMetrics.PowerState
            UNPLUGGED: RedvoxPacketM.StationInformation.StationMetrics.PowerState
            CHARGING: RedvoxPacketM.StationInformation.StationMetrics.PowerState
            CHARGED: RedvoxPacketM.StationInformation.StationMetrics.PowerState
            class ScreenState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
                UNKNOWN_SCREEN_STATE: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.ScreenState]
                ON: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.ScreenState]
                OFF: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.ScreenState]
                HEADLESS: _ClassVar[RedvoxPacketM.StationInformation.StationMetrics.ScreenState]
            UNKNOWN_SCREEN_STATE: RedvoxPacketM.StationInformation.StationMetrics.ScreenState
            ON: RedvoxPacketM.StationInformation.StationMetrics.ScreenState
            OFF: RedvoxPacketM.StationInformation.StationMetrics.ScreenState
            HEADLESS: RedvoxPacketM.StationInformation.StationMetrics.ScreenState
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
            NETWORK_TYPE_FIELD_NUMBER: _ClassVar[int]
            CELL_SERVICE_STATE_FIELD_NUMBER: _ClassVar[int]
            NETWORK_STRENGTH_FIELD_NUMBER: _ClassVar[int]
            TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
            BATTERY_FIELD_NUMBER: _ClassVar[int]
            BATTERY_CURRENT_FIELD_NUMBER: _ClassVar[int]
            AVAILABLE_RAM_FIELD_NUMBER: _ClassVar[int]
            AVAILABLE_DISK_FIELD_NUMBER: _ClassVar[int]
            CPU_UTILIZATION_FIELD_NUMBER: _ClassVar[int]
            POWER_STATE_FIELD_NUMBER: _ClassVar[int]
            WIFI_WAKE_LOCK_FIELD_NUMBER: _ClassVar[int]
            SCREEN_STATE_FIELD_NUMBER: _ClassVar[int]
            SCREEN_BRIGHTNESS_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            timestamps: RedvoxPacketM.TimingPayload
            network_type: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.StationInformation.StationMetrics.NetworkType]
            cell_service_state: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.StationInformation.StationMetrics.CellServiceState]
            network_strength: RedvoxPacketM.SamplePayload
            temperature: RedvoxPacketM.SamplePayload
            battery: RedvoxPacketM.SamplePayload
            battery_current: RedvoxPacketM.SamplePayload
            available_ram: RedvoxPacketM.SamplePayload
            available_disk: RedvoxPacketM.SamplePayload
            cpu_utilization: RedvoxPacketM.SamplePayload
            power_state: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.StationInformation.StationMetrics.PowerState]
            wifi_wake_lock: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock]
            screen_state: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.StationInformation.StationMetrics.ScreenState]
            screen_brightness: RedvoxPacketM.SamplePayload
            metadata: _containers.ScalarMap[str, str]
            def __init__(self, timestamps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., network_type: _Optional[_Iterable[_Union[RedvoxPacketM.StationInformation.StationMetrics.NetworkType, str]]] = ..., cell_service_state: _Optional[_Iterable[_Union[RedvoxPacketM.StationInformation.StationMetrics.CellServiceState, str]]] = ..., network_strength: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., temperature: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., battery: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., battery_current: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., available_ram: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., available_disk: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., cpu_utilization: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., power_state: _Optional[_Iterable[_Union[RedvoxPacketM.StationInformation.StationMetrics.PowerState, str]]] = ..., wifi_wake_lock: _Optional[_Iterable[_Union[RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock, str]]] = ..., screen_state: _Optional[_Iterable[_Union[RedvoxPacketM.StationInformation.StationMetrics.ScreenState, str]]] = ..., screen_brightness: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class AppSettings(_message.Message):
            __slots__ = ["audio_sampling_rate", "samples_per_window", "audio_source_tuning", "additional_input_sensors", "automatically_record", "launch_at_power_up", "station_id", "station_description", "push_to_server", "publish_data_as_private", "scramble_audio_data", "provide_backfill", "remove_sensor_dc_offset", "fft_overlap", "use_custom_time_sync_server", "time_sync_server_url", "use_custom_data_server", "data_server_url", "use_custom_auth_server", "auth_server_url", "auto_delete_data_files", "storage_space_allowance", "use_sd_card_for_data_storage", "use_location_services", "use_latitude", "use_longitude", "use_altitude", "metrics_rate", "metadata"]
            class FftOverlap(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
                UNKNOWN: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.FftOverlap]
                PERCENT_25: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.FftOverlap]
                PERCENT_50: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.FftOverlap]
                PERCENT_75: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.FftOverlap]
            UNKNOWN: RedvoxPacketM.StationInformation.AppSettings.FftOverlap
            PERCENT_25: RedvoxPacketM.StationInformation.AppSettings.FftOverlap
            PERCENT_50: RedvoxPacketM.StationInformation.AppSettings.FftOverlap
            PERCENT_75: RedvoxPacketM.StationInformation.AppSettings.FftOverlap
            class AudioSamplingRate(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
                UNKNOWN_SAMPLING_RATE: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate]
                HZ_80: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate]
                HZ_800: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate]
                HZ_8000: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate]
                HZ_16000: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate]
                HZ_48000: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate]
            UNKNOWN_SAMPLING_RATE: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            HZ_80: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            HZ_800: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            HZ_8000: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            HZ_16000: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            HZ_48000: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            class AudioSourceTuning(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
                UNKNOWN_TUNING: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning]
                INFRASOUND_TUNING: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning]
                LOW_AUDIO_TUNING: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning]
                AUDIO_TUNING: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning]
            UNKNOWN_TUNING: RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning
            INFRASOUND_TUNING: RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning
            LOW_AUDIO_TUNING: RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning
            AUDIO_TUNING: RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning
            class InputSensor(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
                UNKNOWN_SENSOR: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                ACCELEROMETER: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                ACCELEROMETER_FAST: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                AMBIENT_TEMPERATURE: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                AUDIO: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                COMPRESSED_AUDIO: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                GRAVITY: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                GYROSCOPE: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                GYROSCOPE_FAST: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                IMAGE_PER_SECOND: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                IMAGE_PER_PACKET: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                LIGHT: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                LINEAR_ACCELERATION: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                LOCATION: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                MAGNETOMETER: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                MAGNETOMETER_FAST: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                ORIENTATION: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                PRESSURE: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                PROXIMITY: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                RELATIVE_HUMIDITY: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                ROTATION_VECTOR: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
                VELOCITY: _ClassVar[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
            UNKNOWN_SENSOR: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            ACCELEROMETER: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            ACCELEROMETER_FAST: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            AMBIENT_TEMPERATURE: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            AUDIO: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            COMPRESSED_AUDIO: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            GRAVITY: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            GYROSCOPE: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            GYROSCOPE_FAST: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            IMAGE_PER_SECOND: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            IMAGE_PER_PACKET: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            LIGHT: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            LINEAR_ACCELERATION: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            LOCATION: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            MAGNETOMETER: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            MAGNETOMETER_FAST: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            ORIENTATION: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            PRESSURE: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            PROXIMITY: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            RELATIVE_HUMIDITY: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            ROTATION_VECTOR: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            VELOCITY: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            AUDIO_SAMPLING_RATE_FIELD_NUMBER: _ClassVar[int]
            SAMPLES_PER_WINDOW_FIELD_NUMBER: _ClassVar[int]
            AUDIO_SOURCE_TUNING_FIELD_NUMBER: _ClassVar[int]
            ADDITIONAL_INPUT_SENSORS_FIELD_NUMBER: _ClassVar[int]
            AUTOMATICALLY_RECORD_FIELD_NUMBER: _ClassVar[int]
            LAUNCH_AT_POWER_UP_FIELD_NUMBER: _ClassVar[int]
            STATION_ID_FIELD_NUMBER: _ClassVar[int]
            STATION_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            PUSH_TO_SERVER_FIELD_NUMBER: _ClassVar[int]
            PUBLISH_DATA_AS_PRIVATE_FIELD_NUMBER: _ClassVar[int]
            SCRAMBLE_AUDIO_DATA_FIELD_NUMBER: _ClassVar[int]
            PROVIDE_BACKFILL_FIELD_NUMBER: _ClassVar[int]
            REMOVE_SENSOR_DC_OFFSET_FIELD_NUMBER: _ClassVar[int]
            FFT_OVERLAP_FIELD_NUMBER: _ClassVar[int]
            USE_CUSTOM_TIME_SYNC_SERVER_FIELD_NUMBER: _ClassVar[int]
            TIME_SYNC_SERVER_URL_FIELD_NUMBER: _ClassVar[int]
            USE_CUSTOM_DATA_SERVER_FIELD_NUMBER: _ClassVar[int]
            DATA_SERVER_URL_FIELD_NUMBER: _ClassVar[int]
            USE_CUSTOM_AUTH_SERVER_FIELD_NUMBER: _ClassVar[int]
            AUTH_SERVER_URL_FIELD_NUMBER: _ClassVar[int]
            AUTO_DELETE_DATA_FILES_FIELD_NUMBER: _ClassVar[int]
            STORAGE_SPACE_ALLOWANCE_FIELD_NUMBER: _ClassVar[int]
            USE_SD_CARD_FOR_DATA_STORAGE_FIELD_NUMBER: _ClassVar[int]
            USE_LOCATION_SERVICES_FIELD_NUMBER: _ClassVar[int]
            USE_LATITUDE_FIELD_NUMBER: _ClassVar[int]
            USE_LONGITUDE_FIELD_NUMBER: _ClassVar[int]
            USE_ALTITUDE_FIELD_NUMBER: _ClassVar[int]
            METRICS_RATE_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            audio_sampling_rate: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            samples_per_window: float
            audio_source_tuning: RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning
            additional_input_sensors: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
            automatically_record: bool
            launch_at_power_up: bool
            station_id: str
            station_description: str
            push_to_server: bool
            publish_data_as_private: bool
            scramble_audio_data: bool
            provide_backfill: bool
            remove_sensor_dc_offset: bool
            fft_overlap: RedvoxPacketM.StationInformation.AppSettings.FftOverlap
            use_custom_time_sync_server: bool
            time_sync_server_url: str
            use_custom_data_server: bool
            data_server_url: str
            use_custom_auth_server: bool
            auth_server_url: str
            auto_delete_data_files: bool
            storage_space_allowance: float
            use_sd_card_for_data_storage: bool
            use_location_services: bool
            use_latitude: float
            use_longitude: float
            use_altitude: float
            metrics_rate: RedvoxPacketM.StationInformation.MetricsRate
            metadata: _containers.ScalarMap[str, str]
            def __init__(self, audio_sampling_rate: _Optional[_Union[RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate, str]] = ..., samples_per_window: _Optional[float] = ..., audio_source_tuning: _Optional[_Union[RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning, str]] = ..., additional_input_sensors: _Optional[_Iterable[_Union[RedvoxPacketM.StationInformation.AppSettings.InputSensor, str]]] = ..., automatically_record: bool = ..., launch_at_power_up: bool = ..., station_id: _Optional[str] = ..., station_description: _Optional[str] = ..., push_to_server: bool = ..., publish_data_as_private: bool = ..., scramble_audio_data: bool = ..., provide_backfill: bool = ..., remove_sensor_dc_offset: bool = ..., fft_overlap: _Optional[_Union[RedvoxPacketM.StationInformation.AppSettings.FftOverlap, str]] = ..., use_custom_time_sync_server: bool = ..., time_sync_server_url: _Optional[str] = ..., use_custom_data_server: bool = ..., data_server_url: _Optional[str] = ..., use_custom_auth_server: bool = ..., auth_server_url: _Optional[str] = ..., auto_delete_data_files: bool = ..., storage_space_allowance: _Optional[float] = ..., use_sd_card_for_data_storage: bool = ..., use_location_services: bool = ..., use_latitude: _Optional[float] = ..., use_longitude: _Optional[float] = ..., use_altitude: _Optional[float] = ..., metrics_rate: _Optional[_Union[RedvoxPacketM.StationInformation.MetricsRate, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        ID_FIELD_NUMBER: _ClassVar[int]
        UUID_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        AUTH_ID_FIELD_NUMBER: _ClassVar[int]
        MAKE_FIELD_NUMBER: _ClassVar[int]
        MODEL_FIELD_NUMBER: _ClassVar[int]
        OS_FIELD_NUMBER: _ClassVar[int]
        OS_VERSION_FIELD_NUMBER: _ClassVar[int]
        APP_VERSION_FIELD_NUMBER: _ClassVar[int]
        IS_PRIVATE_FIELD_NUMBER: _ClassVar[int]
        APP_SETTINGS_FIELD_NUMBER: _ClassVar[int]
        STATION_METRICS_FIELD_NUMBER: _ClassVar[int]
        SERVICE_URLS_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        id: str
        uuid: str
        description: str
        auth_id: str
        make: str
        model: str
        os: RedvoxPacketM.StationInformation.OsType
        os_version: str
        app_version: str
        is_private: bool
        app_settings: RedvoxPacketM.StationInformation.AppSettings
        station_metrics: RedvoxPacketM.StationInformation.StationMetrics
        service_urls: RedvoxPacketM.StationInformation.ServiceUrls
        metadata: _containers.ScalarMap[str, str]
        def __init__(self, id: _Optional[str] = ..., uuid: _Optional[str] = ..., description: _Optional[str] = ..., auth_id: _Optional[str] = ..., make: _Optional[str] = ..., model: _Optional[str] = ..., os: _Optional[_Union[RedvoxPacketM.StationInformation.OsType, str]] = ..., os_version: _Optional[str] = ..., app_version: _Optional[str] = ..., is_private: bool = ..., app_settings: _Optional[_Union[RedvoxPacketM.StationInformation.AppSettings, _Mapping]] = ..., station_metrics: _Optional[_Union[RedvoxPacketM.StationInformation.StationMetrics, _Mapping]] = ..., service_urls: _Optional[_Union[RedvoxPacketM.StationInformation.ServiceUrls, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class TimingInformation(_message.Message):
        __slots__ = ["packet_start_os_timestamp", "packet_start_mach_timestamp", "packet_end_os_timestamp", "packet_end_mach_timestamp", "server_acquisition_arrival_timestamp", "app_start_mach_timestamp", "synch_exchanges", "best_latency", "best_offset", "score", "score_method", "unit", "metadata"]
        class TimingScoreMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = []
            UNKNOWN: _ClassVar[RedvoxPacketM.TimingInformation.TimingScoreMethod]
        UNKNOWN: RedvoxPacketM.TimingInformation.TimingScoreMethod
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        class SynchExchange(_message.Message):
            __slots__ = ["a1", "a2", "a3", "b1", "b2", "b3", "unit", "metadata"]
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            A1_FIELD_NUMBER: _ClassVar[int]
            A2_FIELD_NUMBER: _ClassVar[int]
            A3_FIELD_NUMBER: _ClassVar[int]
            B1_FIELD_NUMBER: _ClassVar[int]
            B2_FIELD_NUMBER: _ClassVar[int]
            B3_FIELD_NUMBER: _ClassVar[int]
            UNIT_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            a1: float
            a2: float
            a3: float
            b1: float
            b2: float
            b3: float
            unit: RedvoxPacketM.Unit
            metadata: _containers.ScalarMap[str, str]
            def __init__(self, a1: _Optional[float] = ..., a2: _Optional[float] = ..., a3: _Optional[float] = ..., b1: _Optional[float] = ..., b2: _Optional[float] = ..., b3: _Optional[float] = ..., unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        PACKET_START_OS_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        PACKET_START_MACH_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        PACKET_END_OS_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        PACKET_END_MACH_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        SERVER_ACQUISITION_ARRIVAL_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        APP_START_MACH_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        SYNCH_EXCHANGES_FIELD_NUMBER: _ClassVar[int]
        BEST_LATENCY_FIELD_NUMBER: _ClassVar[int]
        BEST_OFFSET_FIELD_NUMBER: _ClassVar[int]
        SCORE_FIELD_NUMBER: _ClassVar[int]
        SCORE_METHOD_FIELD_NUMBER: _ClassVar[int]
        UNIT_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        packet_start_os_timestamp: float
        packet_start_mach_timestamp: float
        packet_end_os_timestamp: float
        packet_end_mach_timestamp: float
        server_acquisition_arrival_timestamp: float
        app_start_mach_timestamp: float
        synch_exchanges: _containers.RepeatedCompositeFieldContainer[RedvoxPacketM.TimingInformation.SynchExchange]
        best_latency: float
        best_offset: float
        score: float
        score_method: RedvoxPacketM.TimingInformation.TimingScoreMethod
        unit: RedvoxPacketM.Unit
        metadata: _containers.ScalarMap[str, str]
        def __init__(self, packet_start_os_timestamp: _Optional[float] = ..., packet_start_mach_timestamp: _Optional[float] = ..., packet_end_os_timestamp: _Optional[float] = ..., packet_end_mach_timestamp: _Optional[float] = ..., server_acquisition_arrival_timestamp: _Optional[float] = ..., app_start_mach_timestamp: _Optional[float] = ..., synch_exchanges: _Optional[_Iterable[_Union[RedvoxPacketM.TimingInformation.SynchExchange, _Mapping]]] = ..., best_latency: _Optional[float] = ..., best_offset: _Optional[float] = ..., score: _Optional[float] = ..., score_method: _Optional[_Union[RedvoxPacketM.TimingInformation.TimingScoreMethod, str]] = ..., unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class Sensors(_message.Message):
        __slots__ = ["accelerometer", "ambient_temperature", "audio", "compressed_audio", "gravity", "gyroscope", "image", "light", "linear_acceleration", "location", "magnetometer", "orientation", "pressure", "proximity", "relative_humidity", "rotation_vector", "velocity", "metadata"]
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        class Audio(_message.Message):
            __slots__ = ["sensor_description", "first_sample_timestamp", "sample_rate", "bits_of_precision", "is_scrambled", "encoding", "samples", "metadata"]
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            SENSOR_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            FIRST_SAMPLE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
            SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
            BITS_OF_PRECISION_FIELD_NUMBER: _ClassVar[int]
            IS_SCRAMBLED_FIELD_NUMBER: _ClassVar[int]
            ENCODING_FIELD_NUMBER: _ClassVar[int]
            SAMPLES_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            sensor_description: str
            first_sample_timestamp: float
            sample_rate: float
            bits_of_precision: float
            is_scrambled: bool
            encoding: str
            samples: RedvoxPacketM.SamplePayload
            metadata: _containers.ScalarMap[str, str]
            def __init__(self, sensor_description: _Optional[str] = ..., first_sample_timestamp: _Optional[float] = ..., sample_rate: _Optional[float] = ..., bits_of_precision: _Optional[float] = ..., is_scrambled: bool = ..., encoding: _Optional[str] = ..., samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class CompressedAudio(_message.Message):
            __slots__ = ["sensor_description", "first_sample_timestamp", "sample_rate", "is_scrambled", "audio_bytes", "audio_codec", "metadata"]
            class AudioCodec(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
                UNKNOWN: _ClassVar[RedvoxPacketM.Sensors.CompressedAudio.AudioCodec]
                FLAC: _ClassVar[RedvoxPacketM.Sensors.CompressedAudio.AudioCodec]
            UNKNOWN: RedvoxPacketM.Sensors.CompressedAudio.AudioCodec
            FLAC: RedvoxPacketM.Sensors.CompressedAudio.AudioCodec
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            SENSOR_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            FIRST_SAMPLE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
            SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
            IS_SCRAMBLED_FIELD_NUMBER: _ClassVar[int]
            AUDIO_BYTES_FIELD_NUMBER: _ClassVar[int]
            AUDIO_CODEC_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            sensor_description: str
            first_sample_timestamp: float
            sample_rate: float
            is_scrambled: bool
            audio_bytes: bytes
            audio_codec: RedvoxPacketM.Sensors.CompressedAudio.AudioCodec
            metadata: _containers.ScalarMap[str, str]
            def __init__(self, sensor_description: _Optional[str] = ..., first_sample_timestamp: _Optional[float] = ..., sample_rate: _Optional[float] = ..., is_scrambled: bool = ..., audio_bytes: _Optional[bytes] = ..., audio_codec: _Optional[_Union[RedvoxPacketM.Sensors.CompressedAudio.AudioCodec, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class Single(_message.Message):
            __slots__ = ["sensor_description", "timestamps", "samples", "metadata"]
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            SENSOR_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
            SAMPLES_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            sensor_description: str
            timestamps: RedvoxPacketM.TimingPayload
            samples: RedvoxPacketM.SamplePayload
            metadata: _containers.ScalarMap[str, str]
            def __init__(self, sensor_description: _Optional[str] = ..., timestamps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class Location(_message.Message):
            __slots__ = ["sensor_description", "timestamps", "timestamps_gps", "latitude_samples", "longitude_samples", "altitude_samples", "speed_samples", "bearing_samples", "horizontal_accuracy_samples", "vertical_accuracy_samples", "speed_accuracy_samples", "bearing_accuracy_samples", "last_best_location", "overall_best_location", "location_permissions_granted", "location_services_requested", "location_services_enabled", "location_providers", "metadata"]
            class LocationProvider(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
                UNKNOWN: _ClassVar[RedvoxPacketM.Sensors.Location.LocationProvider]
                NONE: _ClassVar[RedvoxPacketM.Sensors.Location.LocationProvider]
                USER: _ClassVar[RedvoxPacketM.Sensors.Location.LocationProvider]
                GPS: _ClassVar[RedvoxPacketM.Sensors.Location.LocationProvider]
                NETWORK: _ClassVar[RedvoxPacketM.Sensors.Location.LocationProvider]
            UNKNOWN: RedvoxPacketM.Sensors.Location.LocationProvider
            NONE: RedvoxPacketM.Sensors.Location.LocationProvider
            USER: RedvoxPacketM.Sensors.Location.LocationProvider
            GPS: RedvoxPacketM.Sensors.Location.LocationProvider
            NETWORK: RedvoxPacketM.Sensors.Location.LocationProvider
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            class BestLocation(_message.Message):
                __slots__ = ["latitude_longitude_timestamp", "altitude_timestamp", "speed_timestamp", "bearing_timestamp", "latitude_longitude_unit", "altitude_unit", "speed_unit", "bearing_unit", "vertical_accuracy_unit", "horizontal_accuracy_unit", "speed_accuracy_unit", "bearing_accuracy_unit", "latitude", "longitude", "altitude", "speed", "bearing", "vertical_accuracy", "horizontal_accuracy", "speed_accuracy", "bearing_accuracy", "score", "method", "location_provider", "metadata"]
                class LocationScoreMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                    __slots__ = []
                    UNKNOWN_METHOD: _ClassVar[RedvoxPacketM.Sensors.Location.BestLocation.LocationScoreMethod]
                UNKNOWN_METHOD: RedvoxPacketM.Sensors.Location.BestLocation.LocationScoreMethod
                class MetadataEntry(_message.Message):
                    __slots__ = ["key", "value"]
                    KEY_FIELD_NUMBER: _ClassVar[int]
                    VALUE_FIELD_NUMBER: _ClassVar[int]
                    key: str
                    value: str
                    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
                class BestTimestamp(_message.Message):
                    __slots__ = ["unit", "mach", "gps", "metadata"]
                    class MetadataEntry(_message.Message):
                        __slots__ = ["key", "value"]
                        KEY_FIELD_NUMBER: _ClassVar[int]
                        VALUE_FIELD_NUMBER: _ClassVar[int]
                        key: str
                        value: str
                        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
                    UNIT_FIELD_NUMBER: _ClassVar[int]
                    MACH_FIELD_NUMBER: _ClassVar[int]
                    GPS_FIELD_NUMBER: _ClassVar[int]
                    METADATA_FIELD_NUMBER: _ClassVar[int]
                    unit: RedvoxPacketM.Unit
                    mach: float
                    gps: float
                    metadata: _containers.ScalarMap[str, str]
                    def __init__(self, unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., mach: _Optional[float] = ..., gps: _Optional[float] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
                LATITUDE_LONGITUDE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
                ALTITUDE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
                SPEED_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
                BEARING_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
                LATITUDE_LONGITUDE_UNIT_FIELD_NUMBER: _ClassVar[int]
                ALTITUDE_UNIT_FIELD_NUMBER: _ClassVar[int]
                SPEED_UNIT_FIELD_NUMBER: _ClassVar[int]
                BEARING_UNIT_FIELD_NUMBER: _ClassVar[int]
                VERTICAL_ACCURACY_UNIT_FIELD_NUMBER: _ClassVar[int]
                HORIZONTAL_ACCURACY_UNIT_FIELD_NUMBER: _ClassVar[int]
                SPEED_ACCURACY_UNIT_FIELD_NUMBER: _ClassVar[int]
                BEARING_ACCURACY_UNIT_FIELD_NUMBER: _ClassVar[int]
                LATITUDE_FIELD_NUMBER: _ClassVar[int]
                LONGITUDE_FIELD_NUMBER: _ClassVar[int]
                ALTITUDE_FIELD_NUMBER: _ClassVar[int]
                SPEED_FIELD_NUMBER: _ClassVar[int]
                BEARING_FIELD_NUMBER: _ClassVar[int]
                VERTICAL_ACCURACY_FIELD_NUMBER: _ClassVar[int]
                HORIZONTAL_ACCURACY_FIELD_NUMBER: _ClassVar[int]
                SPEED_ACCURACY_FIELD_NUMBER: _ClassVar[int]
                BEARING_ACCURACY_FIELD_NUMBER: _ClassVar[int]
                SCORE_FIELD_NUMBER: _ClassVar[int]
                METHOD_FIELD_NUMBER: _ClassVar[int]
                LOCATION_PROVIDER_FIELD_NUMBER: _ClassVar[int]
                METADATA_FIELD_NUMBER: _ClassVar[int]
                latitude_longitude_timestamp: RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp
                altitude_timestamp: RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp
                speed_timestamp: RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp
                bearing_timestamp: RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp
                latitude_longitude_unit: RedvoxPacketM.Unit
                altitude_unit: RedvoxPacketM.Unit
                speed_unit: RedvoxPacketM.Unit
                bearing_unit: RedvoxPacketM.Unit
                vertical_accuracy_unit: RedvoxPacketM.Unit
                horizontal_accuracy_unit: RedvoxPacketM.Unit
                speed_accuracy_unit: RedvoxPacketM.Unit
                bearing_accuracy_unit: RedvoxPacketM.Unit
                latitude: float
                longitude: float
                altitude: float
                speed: float
                bearing: float
                vertical_accuracy: float
                horizontal_accuracy: float
                speed_accuracy: float
                bearing_accuracy: float
                score: float
                method: RedvoxPacketM.Sensors.Location.BestLocation.LocationScoreMethod
                location_provider: RedvoxPacketM.Sensors.Location.LocationProvider
                metadata: _containers.ScalarMap[str, str]
                def __init__(self, latitude_longitude_timestamp: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp, _Mapping]] = ..., altitude_timestamp: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp, _Mapping]] = ..., speed_timestamp: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp, _Mapping]] = ..., bearing_timestamp: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp, _Mapping]] = ..., latitude_longitude_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., altitude_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., speed_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., bearing_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., vertical_accuracy_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., horizontal_accuracy_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., speed_accuracy_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., bearing_accuracy_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., latitude: _Optional[float] = ..., longitude: _Optional[float] = ..., altitude: _Optional[float] = ..., speed: _Optional[float] = ..., bearing: _Optional[float] = ..., vertical_accuracy: _Optional[float] = ..., horizontal_accuracy: _Optional[float] = ..., speed_accuracy: _Optional[float] = ..., bearing_accuracy: _Optional[float] = ..., score: _Optional[float] = ..., method: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation.LocationScoreMethod, str]] = ..., location_provider: _Optional[_Union[RedvoxPacketM.Sensors.Location.LocationProvider, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
            SENSOR_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
            TIMESTAMPS_GPS_FIELD_NUMBER: _ClassVar[int]
            LATITUDE_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            LONGITUDE_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            ALTITUDE_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            SPEED_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            BEARING_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            HORIZONTAL_ACCURACY_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            VERTICAL_ACCURACY_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            SPEED_ACCURACY_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            BEARING_ACCURACY_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            LAST_BEST_LOCATION_FIELD_NUMBER: _ClassVar[int]
            OVERALL_BEST_LOCATION_FIELD_NUMBER: _ClassVar[int]
            LOCATION_PERMISSIONS_GRANTED_FIELD_NUMBER: _ClassVar[int]
            LOCATION_SERVICES_REQUESTED_FIELD_NUMBER: _ClassVar[int]
            LOCATION_SERVICES_ENABLED_FIELD_NUMBER: _ClassVar[int]
            LOCATION_PROVIDERS_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            sensor_description: str
            timestamps: RedvoxPacketM.TimingPayload
            timestamps_gps: RedvoxPacketM.TimingPayload
            latitude_samples: RedvoxPacketM.DoubleSamplePayload
            longitude_samples: RedvoxPacketM.DoubleSamplePayload
            altitude_samples: RedvoxPacketM.SamplePayload
            speed_samples: RedvoxPacketM.SamplePayload
            bearing_samples: RedvoxPacketM.SamplePayload
            horizontal_accuracy_samples: RedvoxPacketM.SamplePayload
            vertical_accuracy_samples: RedvoxPacketM.SamplePayload
            speed_accuracy_samples: RedvoxPacketM.SamplePayload
            bearing_accuracy_samples: RedvoxPacketM.SamplePayload
            last_best_location: RedvoxPacketM.Sensors.Location.BestLocation
            overall_best_location: RedvoxPacketM.Sensors.Location.BestLocation
            location_permissions_granted: bool
            location_services_requested: bool
            location_services_enabled: bool
            location_providers: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.Sensors.Location.LocationProvider]
            metadata: _containers.ScalarMap[str, str]
            def __init__(self, sensor_description: _Optional[str] = ..., timestamps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., timestamps_gps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., latitude_samples: _Optional[_Union[RedvoxPacketM.DoubleSamplePayload, _Mapping]] = ..., longitude_samples: _Optional[_Union[RedvoxPacketM.DoubleSamplePayload, _Mapping]] = ..., altitude_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., speed_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., bearing_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., horizontal_accuracy_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., vertical_accuracy_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., speed_accuracy_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., bearing_accuracy_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., last_best_location: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation, _Mapping]] = ..., overall_best_location: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation, _Mapping]] = ..., location_permissions_granted: bool = ..., location_services_requested: bool = ..., location_services_enabled: bool = ..., location_providers: _Optional[_Iterable[_Union[RedvoxPacketM.Sensors.Location.LocationProvider, str]]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class Xyz(_message.Message):
            __slots__ = ["sensor_description", "timestamps", "x_samples", "y_samples", "z_samples", "metadata"]
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            SENSOR_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
            X_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            Y_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            Z_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            sensor_description: str
            timestamps: RedvoxPacketM.TimingPayload
            x_samples: RedvoxPacketM.SamplePayload
            y_samples: RedvoxPacketM.SamplePayload
            z_samples: RedvoxPacketM.SamplePayload
            metadata: _containers.ScalarMap[str, str]
            def __init__(self, sensor_description: _Optional[str] = ..., timestamps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., x_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., y_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., z_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class Image(_message.Message):
            __slots__ = ["sensor_description", "timestamps", "samples", "image_codec", "metadata"]
            class ImageCodec(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
                UNKNOWN: _ClassVar[RedvoxPacketM.Sensors.Image.ImageCodec]
                PNG: _ClassVar[RedvoxPacketM.Sensors.Image.ImageCodec]
                JPG: _ClassVar[RedvoxPacketM.Sensors.Image.ImageCodec]
                BMP: _ClassVar[RedvoxPacketM.Sensors.Image.ImageCodec]
            UNKNOWN: RedvoxPacketM.Sensors.Image.ImageCodec
            PNG: RedvoxPacketM.Sensors.Image.ImageCodec
            JPG: RedvoxPacketM.Sensors.Image.ImageCodec
            BMP: RedvoxPacketM.Sensors.Image.ImageCodec
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            SENSOR_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
            SAMPLES_FIELD_NUMBER: _ClassVar[int]
            IMAGE_CODEC_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            sensor_description: str
            timestamps: RedvoxPacketM.TimingPayload
            samples: _containers.RepeatedScalarFieldContainer[bytes]
            image_codec: RedvoxPacketM.Sensors.Image.ImageCodec
            metadata: _containers.ScalarMap[str, str]
            def __init__(self, sensor_description: _Optional[str] = ..., timestamps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., samples: _Optional[_Iterable[bytes]] = ..., image_codec: _Optional[_Union[RedvoxPacketM.Sensors.Image.ImageCodec, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        ACCELEROMETER_FIELD_NUMBER: _ClassVar[int]
        AMBIENT_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
        AUDIO_FIELD_NUMBER: _ClassVar[int]
        COMPRESSED_AUDIO_FIELD_NUMBER: _ClassVar[int]
        GRAVITY_FIELD_NUMBER: _ClassVar[int]
        GYROSCOPE_FIELD_NUMBER: _ClassVar[int]
        IMAGE_FIELD_NUMBER: _ClassVar[int]
        LIGHT_FIELD_NUMBER: _ClassVar[int]
        LINEAR_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
        LOCATION_FIELD_NUMBER: _ClassVar[int]
        MAGNETOMETER_FIELD_NUMBER: _ClassVar[int]
        ORIENTATION_FIELD_NUMBER: _ClassVar[int]
        PRESSURE_FIELD_NUMBER: _ClassVar[int]
        PROXIMITY_FIELD_NUMBER: _ClassVar[int]
        RELATIVE_HUMIDITY_FIELD_NUMBER: _ClassVar[int]
        ROTATION_VECTOR_FIELD_NUMBER: _ClassVar[int]
        VELOCITY_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        accelerometer: RedvoxPacketM.Sensors.Xyz
        ambient_temperature: RedvoxPacketM.Sensors.Single
        audio: RedvoxPacketM.Sensors.Audio
        compressed_audio: RedvoxPacketM.Sensors.CompressedAudio
        gravity: RedvoxPacketM.Sensors.Xyz
        gyroscope: RedvoxPacketM.Sensors.Xyz
        image: RedvoxPacketM.Sensors.Image
        light: RedvoxPacketM.Sensors.Single
        linear_acceleration: RedvoxPacketM.Sensors.Xyz
        location: RedvoxPacketM.Sensors.Location
        magnetometer: RedvoxPacketM.Sensors.Xyz
        orientation: RedvoxPacketM.Sensors.Xyz
        pressure: RedvoxPacketM.Sensors.Single
        proximity: RedvoxPacketM.Sensors.Single
        relative_humidity: RedvoxPacketM.Sensors.Single
        rotation_vector: RedvoxPacketM.Sensors.Xyz
        velocity: RedvoxPacketM.Sensors.Xyz
        metadata: _containers.ScalarMap[str, str]
        def __init__(self, accelerometer: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., ambient_temperature: _Optional[_Union[RedvoxPacketM.Sensors.Single, _Mapping]] = ..., audio: _Optional[_Union[RedvoxPacketM.Sensors.Audio, _Mapping]] = ..., compressed_audio: _Optional[_Union[RedvoxPacketM.Sensors.CompressedAudio, _Mapping]] = ..., gravity: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., gyroscope: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., image: _Optional[_Union[RedvoxPacketM.Sensors.Image, _Mapping]] = ..., light: _Optional[_Union[RedvoxPacketM.Sensors.Single, _Mapping]] = ..., linear_acceleration: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., location: _Optional[_Union[RedvoxPacketM.Sensors.Location, _Mapping]] = ..., magnetometer: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., orientation: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., pressure: _Optional[_Union[RedvoxPacketM.Sensors.Single, _Mapping]] = ..., proximity: _Optional[_Union[RedvoxPacketM.Sensors.Single, _Mapping]] = ..., relative_humidity: _Optional[_Union[RedvoxPacketM.Sensors.Single, _Mapping]] = ..., rotation_vector: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., velocity: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class EventStream(_message.Message):
        __slots__ = ["name", "timestamps", "events", "metadata"]
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        class Event(_message.Message):
            __slots__ = ["description", "string_payload", "numeric_payload", "boolean_payload", "byte_payload", "metadata"]
            class StringPayloadEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            class NumericPayloadEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: float
                def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
            class BooleanPayloadEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: bool
                def __init__(self, key: _Optional[str] = ..., value: bool = ...) -> None: ...
            class BytePayloadEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: bytes
                def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            STRING_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
            NUMERIC_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
            BOOLEAN_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
            BYTE_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            description: str
            string_payload: _containers.ScalarMap[str, str]
            numeric_payload: _containers.ScalarMap[str, float]
            boolean_payload: _containers.ScalarMap[str, bool]
            byte_payload: _containers.ScalarMap[str, bytes]
            metadata: _containers.ScalarMap[str, str]
            def __init__(self, description: _Optional[str] = ..., string_payload: _Optional[_Mapping[str, str]] = ..., numeric_payload: _Optional[_Mapping[str, float]] = ..., boolean_payload: _Optional[_Mapping[str, bool]] = ..., byte_payload: _Optional[_Mapping[str, bytes]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        NAME_FIELD_NUMBER: _ClassVar[int]
        TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
        EVENTS_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        name: str
        timestamps: RedvoxPacketM.TimingPayload
        events: _containers.RepeatedCompositeFieldContainer[RedvoxPacketM.EventStream.Event]
        metadata: _containers.ScalarMap[str, str]
        def __init__(self, name: _Optional[str] = ..., timestamps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., events: _Optional[_Iterable[_Union[RedvoxPacketM.EventStream.Event, _Mapping]]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class SamplePayload(_message.Message):
        __slots__ = ["unit", "values", "value_statistics", "metadata"]
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        UNIT_FIELD_NUMBER: _ClassVar[int]
        VALUES_FIELD_NUMBER: _ClassVar[int]
        VALUE_STATISTICS_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        unit: RedvoxPacketM.Unit
        values: _containers.RepeatedScalarFieldContainer[float]
        value_statistics: RedvoxPacketM.SummaryStatistics
        metadata: _containers.ScalarMap[str, str]
        def __init__(self, unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., values: _Optional[_Iterable[float]] = ..., value_statistics: _Optional[_Union[RedvoxPacketM.SummaryStatistics, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class DoubleSamplePayload(_message.Message):
        __slots__ = ["unit", "values", "value_statistics", "metadata"]
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        UNIT_FIELD_NUMBER: _ClassVar[int]
        VALUES_FIELD_NUMBER: _ClassVar[int]
        VALUE_STATISTICS_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        unit: RedvoxPacketM.Unit
        values: _containers.RepeatedScalarFieldContainer[float]
        value_statistics: RedvoxPacketM.SummaryStatistics
        metadata: _containers.ScalarMap[str, str]
        def __init__(self, unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., values: _Optional[_Iterable[float]] = ..., value_statistics: _Optional[_Union[RedvoxPacketM.SummaryStatistics, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class TimingPayload(_message.Message):
        __slots__ = ["unit", "timestamps", "timestamp_statistics", "mean_sample_rate", "stdev_sample_rate", "metadata"]
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        UNIT_FIELD_NUMBER: _ClassVar[int]
        TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
        TIMESTAMP_STATISTICS_FIELD_NUMBER: _ClassVar[int]
        MEAN_SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
        STDEV_SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        unit: RedvoxPacketM.Unit
        timestamps: _containers.RepeatedScalarFieldContainer[float]
        timestamp_statistics: RedvoxPacketM.SummaryStatistics
        mean_sample_rate: float
        stdev_sample_rate: float
        metadata: _containers.ScalarMap[str, str]
        def __init__(self, unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., timestamps: _Optional[_Iterable[float]] = ..., timestamp_statistics: _Optional[_Union[RedvoxPacketM.SummaryStatistics, _Mapping]] = ..., mean_sample_rate: _Optional[float] = ..., stdev_sample_rate: _Optional[float] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class SummaryStatistics(_message.Message):
        __slots__ = ["count", "mean", "standard_deviation", "min", "max", "range", "metadata"]
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        COUNT_FIELD_NUMBER: _ClassVar[int]
        MEAN_FIELD_NUMBER: _ClassVar[int]
        STANDARD_DEVIATION_FIELD_NUMBER: _ClassVar[int]
        MIN_FIELD_NUMBER: _ClassVar[int]
        MAX_FIELD_NUMBER: _ClassVar[int]
        RANGE_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        count: float
        mean: float
        standard_deviation: float
        min: float
        max: float
        range: float
        metadata: _containers.ScalarMap[str, str]
        def __init__(self, count: _Optional[float] = ..., mean: _Optional[float] = ..., standard_deviation: _Optional[float] = ..., min: _Optional[float] = ..., max: _Optional[float] = ..., range: _Optional[float] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    API_FIELD_NUMBER: _ClassVar[int]
    SUB_API_FIELD_NUMBER: _ClassVar[int]
    STATION_INFORMATION_FIELD_NUMBER: _ClassVar[int]
    TIMING_INFORMATION_FIELD_NUMBER: _ClassVar[int]
    SENSORS_FIELD_NUMBER: _ClassVar[int]
    EVENT_STREAMS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    api: float
    sub_api: float
    station_information: RedvoxPacketM.StationInformation
    timing_information: RedvoxPacketM.TimingInformation
    sensors: RedvoxPacketM.Sensors
    event_streams: _containers.RepeatedCompositeFieldContainer[RedvoxPacketM.EventStream]
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, api: _Optional[float] = ..., sub_api: _Optional[float] = ..., station_information: _Optional[_Union[RedvoxPacketM.StationInformation, _Mapping]] = ..., timing_information: _Optional[_Union[RedvoxPacketM.TimingInformation, _Mapping]] = ..., sensors: _Optional[_Union[RedvoxPacketM.Sensors, _Mapping]] = ..., event_streams: _Optional[_Iterable[_Union[RedvoxPacketM.EventStream, _Mapping]]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class EncryptedRedvoxPacketM(_message.Message):
    __slots__ = ["header", "packet"]
    class Header(_message.Message):
        __slots__ = ["station_id", "station_uuid", "auth_token", "firebase_token", "auth_email"]
        STATION_ID_FIELD_NUMBER: _ClassVar[int]
        STATION_UUID_FIELD_NUMBER: _ClassVar[int]
        AUTH_TOKEN_FIELD_NUMBER: _ClassVar[int]
        FIREBASE_TOKEN_FIELD_NUMBER: _ClassVar[int]
        AUTH_EMAIL_FIELD_NUMBER: _ClassVar[int]
        station_id: str
        station_uuid: str
        auth_token: str
        firebase_token: str
        auth_email: str
        def __init__(self, station_id: _Optional[str] = ..., station_uuid: _Optional[str] = ..., auth_token: _Optional[str] = ..., firebase_token: _Optional[str] = ..., auth_email: _Optional[str] = ...) -> None: ...
    HEADER_FIELD_NUMBER: _ClassVar[int]
    PACKET_FIELD_NUMBER: _ClassVar[int]
    header: bytes
    packet: bytes
    def __init__(self, header: _Optional[bytes] = ..., packet: _Optional[bytes] = ...) -> None: ...

class AcquisitionRequest(_message.Message):
    __slots__ = ["auth_token", "firebase_token", "checksum", "is_encrypted", "payload", "seq_id"]
    AUTH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    FIREBASE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    IS_ENCRYPTED_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    SEQ_ID_FIELD_NUMBER: _ClassVar[int]
    auth_token: str
    firebase_token: str
    checksum: int
    is_encrypted: bool
    payload: bytes
    seq_id: int
    def __init__(self, auth_token: _Optional[str] = ..., firebase_token: _Optional[str] = ..., checksum: _Optional[int] = ..., is_encrypted: bool = ..., payload: _Optional[bytes] = ..., seq_id: _Optional[int] = ...) -> None: ...

class AcquisitionResponse(_message.Message):
    __slots__ = ["response_type", "checksum", "details", "resend", "seq_id"]
    class ResponseType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        UNKNOWN: _ClassVar[AcquisitionResponse.ResponseType]
        OK: _ClassVar[AcquisitionResponse.ResponseType]
        AUTH_ERROR: _ClassVar[AcquisitionResponse.ResponseType]
        DATA_ERROR: _ClassVar[AcquisitionResponse.ResponseType]
        OTHER_ERROR: _ClassVar[AcquisitionResponse.ResponseType]
    UNKNOWN: AcquisitionResponse.ResponseType
    OK: AcquisitionResponse.ResponseType
    AUTH_ERROR: AcquisitionResponse.ResponseType
    DATA_ERROR: AcquisitionResponse.ResponseType
    OTHER_ERROR: AcquisitionResponse.ResponseType
    RESPONSE_TYPE_FIELD_NUMBER: _ClassVar[int]
    CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    RESEND_FIELD_NUMBER: _ClassVar[int]
    SEQ_ID_FIELD_NUMBER: _ClassVar[int]
    response_type: AcquisitionResponse.ResponseType
    checksum: int
    details: str
    resend: bool
    seq_id: int
    def __init__(self, response_type: _Optional[_Union[AcquisitionResponse.ResponseType, str]] = ..., checksum: _Optional[int] = ..., details: _Optional[str] = ..., resend: bool = ..., seq_id: _Optional[int] = ...) -> None: ...

class SynchRequest(_message.Message):
    __slots__ = ["station_id", "station_uuid", "seq_id", "sub_seq_id"]
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    STATION_UUID_FIELD_NUMBER: _ClassVar[int]
    SEQ_ID_FIELD_NUMBER: _ClassVar[int]
    SUB_SEQ_ID_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    station_uuid: str
    seq_id: int
    sub_seq_id: int
    def __init__(self, station_id: _Optional[str] = ..., station_uuid: _Optional[str] = ..., seq_id: _Optional[int] = ..., sub_seq_id: _Optional[int] = ...) -> None: ...

class SynchResponse(_message.Message):
    __slots__ = ["station_id", "station_uuid", "seq_id", "sub_seq_id", "recv_ts_us", "send_ts_us"]
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    STATION_UUID_FIELD_NUMBER: _ClassVar[int]
    SEQ_ID_FIELD_NUMBER: _ClassVar[int]
    SUB_SEQ_ID_FIELD_NUMBER: _ClassVar[int]
    RECV_TS_US_FIELD_NUMBER: _ClassVar[int]
    SEND_TS_US_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    station_uuid: str
    seq_id: int
    sub_seq_id: int
    recv_ts_us: int
    send_ts_us: int
    def __init__(self, station_id: _Optional[str] = ..., station_uuid: _Optional[str] = ..., seq_id: _Optional[int] = ..., sub_seq_id: _Optional[int] = ..., recv_ts_us: _Optional[int] = ..., send_ts_us: _Optional[int] = ...) -> None: ...
