"""
This module contains classes and enums for working with generic RedVox packet metadata through the cloud API.
"""
from dataclasses import dataclass
from typing import List, Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class AudioMetadata:
    sensor_name: Optional[str] = None
    sample_rate: Optional[float] = None
    first_sample_ts: Optional[int] = None
    payload_cnt: Optional[int] = None
    payload_mean: Optional[float] = None
    payload_std: Optional[float] = None
    payload_median: Optional[float] = None


@dataclass_json
@dataclass
class SingleMetadata:
    sensor_name: Optional[str] = None
    timestamps_microseconds_utc_count: Optional[int] = None
    payload_count: Optional[int] = None
    sample_interval_mean: Optional[float] = None
    sample_interval_std: Optional[float] = None
    sample_interval_median: Optional[float] = None
    value_mean: Optional[float] = None
    value_std: Optional[float] = None
    value_median: Optional[float] = None
    metadata: Optional[List[str]] = None


@dataclass_json
@dataclass
class XyzMetadata:
    sensor_name: Optional[str] = None
    timestamps_microseconds_utc_count: Optional[int] = None
    payload_count: Optional[int] = None
    sample_interval_mean: Optional[float] = None
    sample_interval_std: Optional[float] = None
    sample_interval_median: Optional[float] = None
    x_mean: Optional[float] = None
    x_std: Optional[float] = None
    x_median: Optional[float] = None
    y_mean: Optional[float] = None
    y_std: Optional[float] = None
    y_median: Optional[float] = None
    z_mean: Optional[float] = None
    z_std: Optional[float] = None
    z_median: Optional[float] = None
    metadata: Optional[List[str]] = None


@dataclass_json
@dataclass
class LocationMetadata:
    sensor_name: Optional[str] = None
    timestamps_microseconds_utc_count: Optional[int] = None
    payload_count: Optional[int] = None
    sample_interval_mean: Optional[float] = None
    sample_interval_std: Optional[float] = None
    sample_interval_median: Optional[float] = None
    latitude_mean: Optional[float] = None
    latitude_std: Optional[float] = None
    latitude_median: Optional[float] = None
    longitude_mean: Optional[float] = None
    longitude_std: Optional[float] = None
    longitude_median: Optional[float] = None
    altitude_mean: Optional[float] = None
    altitude_std: Optional[float] = None
    altitude_median: Optional[float] = None
    speed_mean: Optional[float] = None
    speed_std: Optional[float] = None
    speed_median: Optional[float] = None
    accuracy_mean: Optional[float] = None
    accuracy_std: Optional[float] = None
    accuracy_median: Optional[float] = None
    metadata: Optional[List[str]] = None


@dataclass_json
@dataclass
class PacketMetadataResult:
    api: Optional[int] = None
    station_id: Optional[str] = None
    station_uuid: Optional[str] = None
    auth_email: Optional[str] = None
    is_backfilled: Optional[bool] = None
    is_private: Optional[bool] = None
    is_scrambled: Optional[bool] = None
    station_make: Optional[str] = None
    station_model: Optional[str] = None
    station_os: Optional[str] = None
    station_os_version: Optional[str] = None
    station_app_version: Optional[str] = None
    battery_level: Optional[float] = None
    station_temperature: Optional[float] = None
    acquisition_url: Optional[str] = None
    synch_url: Optional[str] = None
    auth_url: Optional[str] = None
    os_ts: Optional[int] = None
    mach_ts: Optional[int] = None
    server_ts: Optional[int] = None
    data_key: Optional[str] = None
    mach_time_zero: Optional[float] = None
    best_latency: Optional[float] = None
    best_offset: Optional[float] = None
    audio_sensor: Optional[AudioMetadata] = None
    barometer_sensor: Optional[SingleMetadata] = None
    location_sensor: Optional[LocationMetadata] = None
    time_synchronization_sensor: Optional[SingleMetadata] = None
    accelerometer_sensor: Optional[XyzMetadata] = None
    magnetometer_sensor: Optional[XyzMetadata] = None
    gyroscope_sensor: Optional[XyzMetadata] = None
    light_sensor: Optional[SingleMetadata] = None
    proximity_sensor: Optional[SingleMetadata] = None


@dataclass_json
@dataclass
class AvailableMetadata:
    Api: str = "Api"
    StationId: str = "StationId"
    StationUuid: str = "StationUuid"
    AuthEmail: str = "AuthEmail"
    IsBackfilled: str = "IsBackfilled"
    IsPrivate: str = "IsPrivate"
    IsScrambled: str = "IsScrambled"
    StationMake: str = "StationMake"
    StationModel: str = "StationModel"
    StationOs: str = "StationOs"
    StationOsVersion: str = "StationOsVersion"
    StationAppVersion: str = "StationAppVersion"
    BatteryLevel: str = "BatteryLevel"
    StationTemperature: str = "StationTemperature"
    AcquisitionUrl: str = "AcquisitionUrl"
    SynchUrl: str = "SynchUrl"
    AuthUrl: str = "AuthUrl"
    OsTs: str = "OsTs"
    MachTs: str = "MachTs"
    ServerTs: str = "ServerTs"
    DataKey: str = "DataKey"
    MachTimeZero: str = "MachTimeZero"
    BestLatency: str = "BestLatency"
    BestOffset: str = "BestOffset"
    AudioSensor: str = "AudioSensor"
    BarometerSensor: str = "BarometerSensor"
    AccelerometerSensor: str = "AccelerometerSensor"
    GyroscopeSensor: str = "GyroscopeSensor"
    TimeSynchronizationSensor: str = "TimeSynchronizationSensor"
    MagnetometerSensor: str = "MagnetometerSensor"
    LightSensor: str = "LightSensor"
    ProximitySensor: str = "ProximitySensor"
    LocationSensor: str = "LocationSensor"


@dataclass_json
@dataclass
class MetadataReq:
    auth_token: str
    start_ts_s: int
    end_ts_s: int
    auth_emails: List[str]
    station_ids: List[str]
    fields: List[str]
    secret_token: Optional[str] = None


@dataclass_json
@dataclass
class MetadataResp:
    metadata: List[PacketMetadataResult]
