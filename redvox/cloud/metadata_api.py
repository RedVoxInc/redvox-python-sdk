"""
This module contains classes and enums for working with generic RedVox packet metadata through the cloud API.
"""
import requests
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from dataclasses_json import dataclass_json

from redvox.cloud.api import ApiConfig, post_req
from redvox.cloud.routes import RoutesV1


@dataclass_json
@dataclass
class AudioMetadata:
    """
    Metadata associated with audio sensors.
    """
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
    """
    Metadata associated with sensors that only contain a single dimensional channel of data
        (barometer, light, proximity).
    """
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
    """
    Metadata for sensors that have 3-dimensions of data (accelerometer, gyroscope, magenetometer)
    """
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
    """
    Metadata associated with the location sensor.
    """
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
    """
    Metadata associated with RedVox API 900 packets.
    """
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
    """
    Contains definitions for all available metadata that an be requested from the cloud api.
    """
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

    @staticmethod
    def all_available_metadata() -> List[str]:
        """
        Returns a list of all available metadata definitions.
        :return: A list of all available metadata definitions.
        """
        return [
            AvailableMetadata.Api,
            AvailableMetadata.StationId,
            AvailableMetadata.StationUuid,
            AvailableMetadata.AuthEmail,
            AvailableMetadata.IsBackfilled,
            AvailableMetadata.IsPrivate,
            AvailableMetadata.IsScrambled,
            AvailableMetadata.StationMake,
            AvailableMetadata.StationModel,
            AvailableMetadata.StationOs,
            AvailableMetadata.StationOsVersion,
            AvailableMetadata.StationAppVersion,
            AvailableMetadata.BatteryLevel,
            AvailableMetadata.StationTemperature,
            AvailableMetadata.AcquisitionUrl,
            AvailableMetadata.SynchUrl,
            AvailableMetadata.AuthUrl,
            AvailableMetadata.OsTs,
            AvailableMetadata.MachTs,
            AvailableMetadata.ServerTs,
            AvailableMetadata.DataKey,
            AvailableMetadata.MachTimeZero,
            AvailableMetadata.BestLatency,
            AvailableMetadata.BestOffset,
            AvailableMetadata.AudioSensor,
            AvailableMetadata.BarometerSensor,
            AvailableMetadata.AccelerometerSensor,
            AvailableMetadata.GyroscopeSensor,
            AvailableMetadata.TimeSynchronizationSensor,
            AvailableMetadata.MagnetometerSensor,
            AvailableMetadata.LightSensor,
            AvailableMetadata.ProximitySensor,
            AvailableMetadata.LocationSensor,
        ]


@dataclass_json
@dataclass
class MetadataReq:
    """
    The definition of a metadata request. Fields should include the definitions defined by AvailableMetadata.
    """
    auth_token: str
    start_ts_s: int
    end_ts_s: int
    station_ids: List[str]
    fields: List[str]
    secret_token: Optional[str] = None


@dataclass_json
@dataclass
class MetadataResp:
    """
    Response of a metadata request.
    """
    metadata: List[PacketMetadataResult]


@dataclass_json
@dataclass
class TimingMetaRequest:
    """
    Request for timing metadata.
    """
    auth_token: str
    start_ts_s: int
    end_ts_s: int
    station_ids: List[str]
    secret_token: Optional[str] = None


@dataclass_json
@dataclass
class TimingMeta:
    """
    Timing metadata extracted from an individual packet.
    """
    station_id: str
    start_ts_os: float
    start_ts_mach: float
    server_ts: float
    mach_time_zero: float
    best_latency: float
    best_offset: float


@dataclass_json
@dataclass
class TimingMetaResponse:
    """
    Response of obtaining timing metadta.
    """
    items: List[TimingMeta]


def request_timing_metadata(api_config: ApiConfig,
                            timing_req: TimingMetaRequest,
                            session: Optional[requests.Session] = None,
                            timeout: Optional[float] = None) -> TimingMetaResponse:
    """
    Retrieve timing metadata.
    :param api_config: An instance of the API configuration.
    :param timing_req: An instance of a timing request.
    :param session: An (optional) session for re-using an HTTP client.
    :return: An instance of a timing response.
    """

    def handle_resp(resp) -> TimingMetaResponse:
        json: List[Dict] = resp.json()
        # noinspection Mypy
        items: List[TimingMeta] = list(map(TimingMeta.from_dict, json))
        return TimingMetaResponse(items)

    res: Optional[TimingMetaResponse] = post_req(api_config,
                                                 RoutesV1.TIMING_METADATA_REQ,
                                                 timing_req,
                                                 handle_resp,
                                                 session,
                                                 timeout)

    return res if res else TimingMetaResponse([])


def request_metadata(api_config: ApiConfig,
                     packet_metadata_req: MetadataReq,
                     session: Optional[requests.Session] = None,
                     timeout: Optional[float] = None) -> Optional[MetadataResp]:
    """
    Requests generic metadata from the cloud API.
    :param api_config: An instance of the API config.
    :param packet_metadata_req: An instance of a metadata request.
    :param session: An (optional) session for re-using an HTTP client.
    :return: A metadata response on successful call or None if there is an error.
    """
    # noinspection Mypy
    handle_resp: Callable[[requests.Response], MetadataResp] = lambda resp: MetadataResp.from_dict(resp.json())
    return post_req(api_config,
                    RoutesV1.METADATA_REQ,
                    packet_metadata_req,
                    handle_resp,
                    session,
                    timeout)
