from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

ACCELEROMETER_X: ChannelType
ACCELEROMETER_Y: ChannelType
ACCELEROMETER_Z: ChannelType
ACCURACY: ChannelType
ALTITUDE: ChannelType
BAROMETER: ChannelType
DESCRIPTOR: _descriptor.FileDescriptor
GYROSCOPE_X: ChannelType
GYROSCOPE_Y: ChannelType
GYROSCOPE_Z: ChannelType
IMAGE: ChannelType
INFRARED: ChannelType
LATITUDE: ChannelType
LIGHT: ChannelType
LONGITUDE: ChannelType
MAGNETOMETER_X: ChannelType
MAGNETOMETER_Y: ChannelType
MAGNETOMETER_Z: ChannelType
MICROPHONE: ChannelType
OTHER: ChannelType
RESERVED_0: ChannelType
RESERVED_1: ChannelType
RESERVED_2: ChannelType
SPEED: ChannelType
TIME_SYNCHRONIZATION: ChannelType

class BytePayload(_message.Message):
    __slots__ = ["bytePayloadType", "payload"]
    class BytePayloadType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    BYTEPAYLOADTYPE_FIELD_NUMBER: _ClassVar[int]
    BYTES: BytePayload.BytePayloadType
    FLOAT32: BytePayload.BytePayloadType
    FLOAT64: BytePayload.BytePayloadType
    INT16: BytePayload.BytePayloadType
    INT24: BytePayload.BytePayloadType
    INT32: BytePayload.BytePayloadType
    INT64: BytePayload.BytePayloadType
    INT8: BytePayload.BytePayloadType
    OTHER: BytePayload.BytePayloadType
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    UINT32: BytePayload.BytePayloadType
    UINT64: BytePayload.BytePayloadType
    UINT8: BytePayload.BytePayloadType
    UNINT16: BytePayload.BytePayloadType
    UNINT24: BytePayload.BytePayloadType
    bytePayloadType: BytePayload.BytePayloadType
    payload: bytes
    def __init__(self, bytePayloadType: _Optional[_Union[BytePayload.BytePayloadType, str]] = ..., payload: _Optional[bytes] = ...) -> None: ...

class EvenlySampledChannel(_message.Message):
    __slots__ = ["byte_payload", "channel_types", "first_sample_timestamp_epoch_microseconds_utc", "float32_payload", "float64_payload", "int32_payload", "int64_payload", "metadata", "sample_rate_hz", "sensor_name", "uint32_payload", "uint64_payload", "value_means", "value_medians", "value_stds"]
    BYTE_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_TYPES_FIELD_NUMBER: _ClassVar[int]
    FIRST_SAMPLE_TIMESTAMP_EPOCH_MICROSECONDS_UTC_FIELD_NUMBER: _ClassVar[int]
    FLOAT32_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    FLOAT64_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    INT32_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    INT64_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_HZ_FIELD_NUMBER: _ClassVar[int]
    SENSOR_NAME_FIELD_NUMBER: _ClassVar[int]
    UINT32_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    UINT64_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    VALUE_MEANS_FIELD_NUMBER: _ClassVar[int]
    VALUE_MEDIANS_FIELD_NUMBER: _ClassVar[int]
    VALUE_STDS_FIELD_NUMBER: _ClassVar[int]
    byte_payload: BytePayload
    channel_types: _containers.RepeatedScalarFieldContainer[ChannelType]
    first_sample_timestamp_epoch_microseconds_utc: int
    float32_payload: Float32Payload
    float64_payload: Float64Payload
    int32_payload: Int32Payload
    int64_payload: Int64Payload
    metadata: _containers.RepeatedScalarFieldContainer[str]
    sample_rate_hz: float
    sensor_name: str
    uint32_payload: UInt32Payload
    uint64_payload: UInt64Payload
    value_means: _containers.RepeatedScalarFieldContainer[float]
    value_medians: _containers.RepeatedScalarFieldContainer[float]
    value_stds: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, channel_types: _Optional[_Iterable[_Union[ChannelType, str]]] = ..., sensor_name: _Optional[str] = ..., sample_rate_hz: _Optional[float] = ..., first_sample_timestamp_epoch_microseconds_utc: _Optional[int] = ..., byte_payload: _Optional[_Union[BytePayload, _Mapping]] = ..., uint32_payload: _Optional[_Union[UInt32Payload, _Mapping]] = ..., uint64_payload: _Optional[_Union[UInt64Payload, _Mapping]] = ..., int32_payload: _Optional[_Union[Int32Payload, _Mapping]] = ..., int64_payload: _Optional[_Union[Int64Payload, _Mapping]] = ..., float32_payload: _Optional[_Union[Float32Payload, _Mapping]] = ..., float64_payload: _Optional[_Union[Float64Payload, _Mapping]] = ..., value_means: _Optional[_Iterable[float]] = ..., value_stds: _Optional[_Iterable[float]] = ..., value_medians: _Optional[_Iterable[float]] = ..., metadata: _Optional[_Iterable[str]] = ...) -> None: ...

class Float32Payload(_message.Message):
    __slots__ = ["payload"]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, payload: _Optional[_Iterable[float]] = ...) -> None: ...

class Float64Payload(_message.Message):
    __slots__ = ["payload"]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, payload: _Optional[_Iterable[float]] = ...) -> None: ...

class Int32Payload(_message.Message):
    __slots__ = ["payload"]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, payload: _Optional[_Iterable[int]] = ...) -> None: ...

class Int64Payload(_message.Message):
    __slots__ = ["payload"]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, payload: _Optional[_Iterable[int]] = ...) -> None: ...

class RedvoxPacket(_message.Message):
    __slots__ = ["acquisition_server", "api", "app_file_start_timestamp_epoch_microseconds_utc", "app_file_start_timestamp_machine", "app_version", "authenticated_email", "authentication_server", "authentication_token", "battery_level_percent", "device_make", "device_model", "device_os", "device_os_version", "device_temperature_c", "evenly_sampled_channels", "firebase_token", "is_backfilled", "is_private", "is_scrambled", "metadata", "redvox_id", "server_timestamp_epoch_microseconds_utc", "time_synchronization_server", "unevenly_sampled_channels", "uuid"]
    ACQUISITION_SERVER_FIELD_NUMBER: _ClassVar[int]
    API_FIELD_NUMBER: _ClassVar[int]
    APP_FILE_START_TIMESTAMP_EPOCH_MICROSECONDS_UTC_FIELD_NUMBER: _ClassVar[int]
    APP_FILE_START_TIMESTAMP_MACHINE_FIELD_NUMBER: _ClassVar[int]
    APP_VERSION_FIELD_NUMBER: _ClassVar[int]
    AUTHENTICATED_EMAIL_FIELD_NUMBER: _ClassVar[int]
    AUTHENTICATION_SERVER_FIELD_NUMBER: _ClassVar[int]
    AUTHENTICATION_TOKEN_FIELD_NUMBER: _ClassVar[int]
    BATTERY_LEVEL_PERCENT_FIELD_NUMBER: _ClassVar[int]
    DEVICE_MAKE_FIELD_NUMBER: _ClassVar[int]
    DEVICE_MODEL_FIELD_NUMBER: _ClassVar[int]
    DEVICE_OS_FIELD_NUMBER: _ClassVar[int]
    DEVICE_OS_VERSION_FIELD_NUMBER: _ClassVar[int]
    DEVICE_TEMPERATURE_C_FIELD_NUMBER: _ClassVar[int]
    EVENLY_SAMPLED_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    FIREBASE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    IS_BACKFILLED_FIELD_NUMBER: _ClassVar[int]
    IS_PRIVATE_FIELD_NUMBER: _ClassVar[int]
    IS_SCRAMBLED_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    REDVOX_ID_FIELD_NUMBER: _ClassVar[int]
    SERVER_TIMESTAMP_EPOCH_MICROSECONDS_UTC_FIELD_NUMBER: _ClassVar[int]
    TIME_SYNCHRONIZATION_SERVER_FIELD_NUMBER: _ClassVar[int]
    UNEVENLY_SAMPLED_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    acquisition_server: str
    api: int
    app_file_start_timestamp_epoch_microseconds_utc: int
    app_file_start_timestamp_machine: int
    app_version: str
    authenticated_email: str
    authentication_server: str
    authentication_token: str
    battery_level_percent: float
    device_make: str
    device_model: str
    device_os: str
    device_os_version: str
    device_temperature_c: float
    evenly_sampled_channels: _containers.RepeatedCompositeFieldContainer[EvenlySampledChannel]
    firebase_token: str
    is_backfilled: bool
    is_private: bool
    is_scrambled: bool
    metadata: _containers.RepeatedScalarFieldContainer[str]
    redvox_id: str
    server_timestamp_epoch_microseconds_utc: int
    time_synchronization_server: str
    unevenly_sampled_channels: _containers.RepeatedCompositeFieldContainer[UnevenlySampledChannel]
    uuid: str
    def __init__(self, api: _Optional[int] = ..., uuid: _Optional[str] = ..., redvox_id: _Optional[str] = ..., authenticated_email: _Optional[str] = ..., authentication_token: _Optional[str] = ..., firebase_token: _Optional[str] = ..., is_backfilled: bool = ..., is_private: bool = ..., is_scrambled: bool = ..., device_make: _Optional[str] = ..., device_model: _Optional[str] = ..., device_os: _Optional[str] = ..., device_os_version: _Optional[str] = ..., app_version: _Optional[str] = ..., battery_level_percent: _Optional[float] = ..., device_temperature_c: _Optional[float] = ..., acquisition_server: _Optional[str] = ..., time_synchronization_server: _Optional[str] = ..., authentication_server: _Optional[str] = ..., app_file_start_timestamp_epoch_microseconds_utc: _Optional[int] = ..., app_file_start_timestamp_machine: _Optional[int] = ..., server_timestamp_epoch_microseconds_utc: _Optional[int] = ..., evenly_sampled_channels: _Optional[_Iterable[_Union[EvenlySampledChannel, _Mapping]]] = ..., unevenly_sampled_channels: _Optional[_Iterable[_Union[UnevenlySampledChannel, _Mapping]]] = ..., metadata: _Optional[_Iterable[str]] = ...) -> None: ...

class RedvoxPacketResponse(_message.Message):
    __slots__ = ["checksum", "errors", "metadata", "type"]
    class Error(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    ERROR: RedvoxPacketResponse.Type
    ERRORS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    NOT_AUTHENTICATED: RedvoxPacketResponse.Error
    OK: RedvoxPacketResponse.Type
    OTHER: RedvoxPacketResponse.Error
    TYPE_FIELD_NUMBER: _ClassVar[int]
    checksum: int
    errors: _containers.RepeatedScalarFieldContainer[RedvoxPacketResponse.Error]
    metadata: _containers.RepeatedScalarFieldContainer[str]
    type: RedvoxPacketResponse.Type
    def __init__(self, type: _Optional[_Union[RedvoxPacketResponse.Type, str]] = ..., checksum: _Optional[int] = ..., errors: _Optional[_Iterable[_Union[RedvoxPacketResponse.Error, str]]] = ..., metadata: _Optional[_Iterable[str]] = ...) -> None: ...

class UInt32Payload(_message.Message):
    __slots__ = ["payload"]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, payload: _Optional[_Iterable[int]] = ...) -> None: ...

class UInt64Payload(_message.Message):
    __slots__ = ["payload"]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, payload: _Optional[_Iterable[int]] = ...) -> None: ...

class UnevenlySampledChannel(_message.Message):
    __slots__ = ["byte_payload", "channel_types", "float32_payload", "float64_payload", "int32_payload", "int64_payload", "metadata", "sample_interval_mean", "sample_interval_median", "sample_interval_std", "sensor_name", "timestamps_microseconds_utc", "uint32_payload", "uint64_payload", "value_means", "value_medians", "value_stds"]
    BYTE_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_TYPES_FIELD_NUMBER: _ClassVar[int]
    FLOAT32_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    FLOAT64_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    INT32_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    INT64_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_INTERVAL_MEAN_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_INTERVAL_MEDIAN_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_INTERVAL_STD_FIELD_NUMBER: _ClassVar[int]
    SENSOR_NAME_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMPS_MICROSECONDS_UTC_FIELD_NUMBER: _ClassVar[int]
    UINT32_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    UINT64_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    VALUE_MEANS_FIELD_NUMBER: _ClassVar[int]
    VALUE_MEDIANS_FIELD_NUMBER: _ClassVar[int]
    VALUE_STDS_FIELD_NUMBER: _ClassVar[int]
    byte_payload: BytePayload
    channel_types: _containers.RepeatedScalarFieldContainer[ChannelType]
    float32_payload: Float32Payload
    float64_payload: Float64Payload
    int32_payload: Int32Payload
    int64_payload: Int64Payload
    metadata: _containers.RepeatedScalarFieldContainer[str]
    sample_interval_mean: float
    sample_interval_median: float
    sample_interval_std: float
    sensor_name: str
    timestamps_microseconds_utc: _containers.RepeatedScalarFieldContainer[int]
    uint32_payload: UInt32Payload
    uint64_payload: UInt64Payload
    value_means: _containers.RepeatedScalarFieldContainer[float]
    value_medians: _containers.RepeatedScalarFieldContainer[float]
    value_stds: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, channel_types: _Optional[_Iterable[_Union[ChannelType, str]]] = ..., sensor_name: _Optional[str] = ..., timestamps_microseconds_utc: _Optional[_Iterable[int]] = ..., byte_payload: _Optional[_Union[BytePayload, _Mapping]] = ..., uint32_payload: _Optional[_Union[UInt32Payload, _Mapping]] = ..., uint64_payload: _Optional[_Union[UInt64Payload, _Mapping]] = ..., int32_payload: _Optional[_Union[Int32Payload, _Mapping]] = ..., int64_payload: _Optional[_Union[Int64Payload, _Mapping]] = ..., float32_payload: _Optional[_Union[Float32Payload, _Mapping]] = ..., float64_payload: _Optional[_Union[Float64Payload, _Mapping]] = ..., sample_interval_mean: _Optional[float] = ..., sample_interval_std: _Optional[float] = ..., sample_interval_median: _Optional[float] = ..., value_means: _Optional[_Iterable[float]] = ..., value_stds: _Optional[_Iterable[float]] = ..., value_medians: _Optional[_Iterable[float]] = ..., metadata: _Optional[_Iterable[str]] = ...) -> None: ...

class ChannelType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
