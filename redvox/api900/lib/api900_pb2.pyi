from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ChannelType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    MICROPHONE: _ClassVar[ChannelType]
    BAROMETER: _ClassVar[ChannelType]
    LATITUDE: _ClassVar[ChannelType]
    LONGITUDE: _ClassVar[ChannelType]
    SPEED: _ClassVar[ChannelType]
    ALTITUDE: _ClassVar[ChannelType]
    RESERVED_0: _ClassVar[ChannelType]
    RESERVED_1: _ClassVar[ChannelType]
    RESERVED_2: _ClassVar[ChannelType]
    TIME_SYNCHRONIZATION: _ClassVar[ChannelType]
    ACCURACY: _ClassVar[ChannelType]
    ACCELEROMETER_X: _ClassVar[ChannelType]
    ACCELEROMETER_Y: _ClassVar[ChannelType]
    ACCELEROMETER_Z: _ClassVar[ChannelType]
    MAGNETOMETER_X: _ClassVar[ChannelType]
    MAGNETOMETER_Y: _ClassVar[ChannelType]
    MAGNETOMETER_Z: _ClassVar[ChannelType]
    GYROSCOPE_X: _ClassVar[ChannelType]
    GYROSCOPE_Y: _ClassVar[ChannelType]
    GYROSCOPE_Z: _ClassVar[ChannelType]
    OTHER: _ClassVar[ChannelType]
    LIGHT: _ClassVar[ChannelType]
    IMAGE: _ClassVar[ChannelType]
    INFRARED: _ClassVar[ChannelType]
MICROPHONE: ChannelType
BAROMETER: ChannelType
LATITUDE: ChannelType
LONGITUDE: ChannelType
SPEED: ChannelType
ALTITUDE: ChannelType
RESERVED_0: ChannelType
RESERVED_1: ChannelType
RESERVED_2: ChannelType
TIME_SYNCHRONIZATION: ChannelType
ACCURACY: ChannelType
ACCELEROMETER_X: ChannelType
ACCELEROMETER_Y: ChannelType
ACCELEROMETER_Z: ChannelType
MAGNETOMETER_X: ChannelType
MAGNETOMETER_Y: ChannelType
MAGNETOMETER_Z: ChannelType
GYROSCOPE_X: ChannelType
GYROSCOPE_Y: ChannelType
GYROSCOPE_Z: ChannelType
OTHER: ChannelType
LIGHT: ChannelType
IMAGE: ChannelType
INFRARED: ChannelType

class RedvoxPacket(_message.Message):
    __slots__ = ["api", "uuid", "redvox_id", "authenticated_email", "authentication_token", "firebase_token", "is_backfilled", "is_private", "is_scrambled", "device_make", "device_model", "device_os", "device_os_version", "app_version", "battery_level_percent", "device_temperature_c", "acquisition_server", "time_synchronization_server", "authentication_server", "app_file_start_timestamp_epoch_microseconds_utc", "app_file_start_timestamp_machine", "server_timestamp_epoch_microseconds_utc", "evenly_sampled_channels", "unevenly_sampled_channels", "metadata"]
    API_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    REDVOX_ID_FIELD_NUMBER: _ClassVar[int]
    AUTHENTICATED_EMAIL_FIELD_NUMBER: _ClassVar[int]
    AUTHENTICATION_TOKEN_FIELD_NUMBER: _ClassVar[int]
    FIREBASE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    IS_BACKFILLED_FIELD_NUMBER: _ClassVar[int]
    IS_PRIVATE_FIELD_NUMBER: _ClassVar[int]
    IS_SCRAMBLED_FIELD_NUMBER: _ClassVar[int]
    DEVICE_MAKE_FIELD_NUMBER: _ClassVar[int]
    DEVICE_MODEL_FIELD_NUMBER: _ClassVar[int]
    DEVICE_OS_FIELD_NUMBER: _ClassVar[int]
    DEVICE_OS_VERSION_FIELD_NUMBER: _ClassVar[int]
    APP_VERSION_FIELD_NUMBER: _ClassVar[int]
    BATTERY_LEVEL_PERCENT_FIELD_NUMBER: _ClassVar[int]
    DEVICE_TEMPERATURE_C_FIELD_NUMBER: _ClassVar[int]
    ACQUISITION_SERVER_FIELD_NUMBER: _ClassVar[int]
    TIME_SYNCHRONIZATION_SERVER_FIELD_NUMBER: _ClassVar[int]
    AUTHENTICATION_SERVER_FIELD_NUMBER: _ClassVar[int]
    APP_FILE_START_TIMESTAMP_EPOCH_MICROSECONDS_UTC_FIELD_NUMBER: _ClassVar[int]
    APP_FILE_START_TIMESTAMP_MACHINE_FIELD_NUMBER: _ClassVar[int]
    SERVER_TIMESTAMP_EPOCH_MICROSECONDS_UTC_FIELD_NUMBER: _ClassVar[int]
    EVENLY_SAMPLED_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    UNEVENLY_SAMPLED_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    api: int
    uuid: str
    redvox_id: str
    authenticated_email: str
    authentication_token: str
    firebase_token: str
    is_backfilled: bool
    is_private: bool
    is_scrambled: bool
    device_make: str
    device_model: str
    device_os: str
    device_os_version: str
    app_version: str
    battery_level_percent: float
    device_temperature_c: float
    acquisition_server: str
    time_synchronization_server: str
    authentication_server: str
    app_file_start_timestamp_epoch_microseconds_utc: int
    app_file_start_timestamp_machine: int
    server_timestamp_epoch_microseconds_utc: int
    evenly_sampled_channels: _containers.RepeatedCompositeFieldContainer[EvenlySampledChannel]
    unevenly_sampled_channels: _containers.RepeatedCompositeFieldContainer[UnevenlySampledChannel]
    metadata: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, api: _Optional[int] = ..., uuid: _Optional[str] = ..., redvox_id: _Optional[str] = ..., authenticated_email: _Optional[str] = ..., authentication_token: _Optional[str] = ..., firebase_token: _Optional[str] = ..., is_backfilled: bool = ..., is_private: bool = ..., is_scrambled: bool = ..., device_make: _Optional[str] = ..., device_model: _Optional[str] = ..., device_os: _Optional[str] = ..., device_os_version: _Optional[str] = ..., app_version: _Optional[str] = ..., battery_level_percent: _Optional[float] = ..., device_temperature_c: _Optional[float] = ..., acquisition_server: _Optional[str] = ..., time_synchronization_server: _Optional[str] = ..., authentication_server: _Optional[str] = ..., app_file_start_timestamp_epoch_microseconds_utc: _Optional[int] = ..., app_file_start_timestamp_machine: _Optional[int] = ..., server_timestamp_epoch_microseconds_utc: _Optional[int] = ..., evenly_sampled_channels: _Optional[_Iterable[_Union[EvenlySampledChannel, _Mapping]]] = ..., unevenly_sampled_channels: _Optional[_Iterable[_Union[UnevenlySampledChannel, _Mapping]]] = ..., metadata: _Optional[_Iterable[str]] = ...) -> None: ...

class Int32Payload(_message.Message):
    __slots__ = ["payload"]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, payload: _Optional[_Iterable[int]] = ...) -> None: ...

class UInt32Payload(_message.Message):
    __slots__ = ["payload"]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, payload: _Optional[_Iterable[int]] = ...) -> None: ...

class Int64Payload(_message.Message):
    __slots__ = ["payload"]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, payload: _Optional[_Iterable[int]] = ...) -> None: ...

class UInt64Payload(_message.Message):
    __slots__ = ["payload"]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, payload: _Optional[_Iterable[int]] = ...) -> None: ...

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

class BytePayload(_message.Message):
    __slots__ = ["bytePayloadType", "payload"]
    class BytePayloadType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        BYTES: _ClassVar[BytePayload.BytePayloadType]
        UINT8: _ClassVar[BytePayload.BytePayloadType]
        UNINT16: _ClassVar[BytePayload.BytePayloadType]
        UNINT24: _ClassVar[BytePayload.BytePayloadType]
        UINT32: _ClassVar[BytePayload.BytePayloadType]
        UINT64: _ClassVar[BytePayload.BytePayloadType]
        INT8: _ClassVar[BytePayload.BytePayloadType]
        INT16: _ClassVar[BytePayload.BytePayloadType]
        INT24: _ClassVar[BytePayload.BytePayloadType]
        INT32: _ClassVar[BytePayload.BytePayloadType]
        INT64: _ClassVar[BytePayload.BytePayloadType]
        FLOAT32: _ClassVar[BytePayload.BytePayloadType]
        FLOAT64: _ClassVar[BytePayload.BytePayloadType]
        OTHER: _ClassVar[BytePayload.BytePayloadType]
    BYTES: BytePayload.BytePayloadType
    UINT8: BytePayload.BytePayloadType
    UNINT16: BytePayload.BytePayloadType
    UNINT24: BytePayload.BytePayloadType
    UINT32: BytePayload.BytePayloadType
    UINT64: BytePayload.BytePayloadType
    INT8: BytePayload.BytePayloadType
    INT16: BytePayload.BytePayloadType
    INT24: BytePayload.BytePayloadType
    INT32: BytePayload.BytePayloadType
    INT64: BytePayload.BytePayloadType
    FLOAT32: BytePayload.BytePayloadType
    FLOAT64: BytePayload.BytePayloadType
    OTHER: BytePayload.BytePayloadType
    BYTEPAYLOADTYPE_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    bytePayloadType: BytePayload.BytePayloadType
    payload: bytes
    def __init__(self, bytePayloadType: _Optional[_Union[BytePayload.BytePayloadType, str]] = ..., payload: _Optional[bytes] = ...) -> None: ...

class EvenlySampledChannel(_message.Message):
    __slots__ = ["channel_types", "sensor_name", "sample_rate_hz", "first_sample_timestamp_epoch_microseconds_utc", "byte_payload", "uint32_payload", "uint64_payload", "int32_payload", "int64_payload", "float32_payload", "float64_payload", "value_means", "value_stds", "value_medians", "metadata"]
    CHANNEL_TYPES_FIELD_NUMBER: _ClassVar[int]
    SENSOR_NAME_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_HZ_FIELD_NUMBER: _ClassVar[int]
    FIRST_SAMPLE_TIMESTAMP_EPOCH_MICROSECONDS_UTC_FIELD_NUMBER: _ClassVar[int]
    BYTE_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    UINT32_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    UINT64_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    INT32_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    INT64_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    FLOAT32_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    FLOAT64_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    VALUE_MEANS_FIELD_NUMBER: _ClassVar[int]
    VALUE_STDS_FIELD_NUMBER: _ClassVar[int]
    VALUE_MEDIANS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    channel_types: _containers.RepeatedScalarFieldContainer[ChannelType]
    sensor_name: str
    sample_rate_hz: float
    first_sample_timestamp_epoch_microseconds_utc: int
    byte_payload: BytePayload
    uint32_payload: UInt32Payload
    uint64_payload: UInt64Payload
    int32_payload: Int32Payload
    int64_payload: Int64Payload
    float32_payload: Float32Payload
    float64_payload: Float64Payload
    value_means: _containers.RepeatedScalarFieldContainer[float]
    value_stds: _containers.RepeatedScalarFieldContainer[float]
    value_medians: _containers.RepeatedScalarFieldContainer[float]
    metadata: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, channel_types: _Optional[_Iterable[_Union[ChannelType, str]]] = ..., sensor_name: _Optional[str] = ..., sample_rate_hz: _Optional[float] = ..., first_sample_timestamp_epoch_microseconds_utc: _Optional[int] = ..., byte_payload: _Optional[_Union[BytePayload, _Mapping]] = ..., uint32_payload: _Optional[_Union[UInt32Payload, _Mapping]] = ..., uint64_payload: _Optional[_Union[UInt64Payload, _Mapping]] = ..., int32_payload: _Optional[_Union[Int32Payload, _Mapping]] = ..., int64_payload: _Optional[_Union[Int64Payload, _Mapping]] = ..., float32_payload: _Optional[_Union[Float32Payload, _Mapping]] = ..., float64_payload: _Optional[_Union[Float64Payload, _Mapping]] = ..., value_means: _Optional[_Iterable[float]] = ..., value_stds: _Optional[_Iterable[float]] = ..., value_medians: _Optional[_Iterable[float]] = ..., metadata: _Optional[_Iterable[str]] = ...) -> None: ...

class UnevenlySampledChannel(_message.Message):
    __slots__ = ["channel_types", "sensor_name", "timestamps_microseconds_utc", "byte_payload", "uint32_payload", "uint64_payload", "int32_payload", "int64_payload", "float32_payload", "float64_payload", "sample_interval_mean", "sample_interval_std", "sample_interval_median", "value_means", "value_stds", "value_medians", "metadata"]
    CHANNEL_TYPES_FIELD_NUMBER: _ClassVar[int]
    SENSOR_NAME_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMPS_MICROSECONDS_UTC_FIELD_NUMBER: _ClassVar[int]
    BYTE_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    UINT32_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    UINT64_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    INT32_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    INT64_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    FLOAT32_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    FLOAT64_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_INTERVAL_MEAN_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_INTERVAL_STD_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_INTERVAL_MEDIAN_FIELD_NUMBER: _ClassVar[int]
    VALUE_MEANS_FIELD_NUMBER: _ClassVar[int]
    VALUE_STDS_FIELD_NUMBER: _ClassVar[int]
    VALUE_MEDIANS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    channel_types: _containers.RepeatedScalarFieldContainer[ChannelType]
    sensor_name: str
    timestamps_microseconds_utc: _containers.RepeatedScalarFieldContainer[int]
    byte_payload: BytePayload
    uint32_payload: UInt32Payload
    uint64_payload: UInt64Payload
    int32_payload: Int32Payload
    int64_payload: Int64Payload
    float32_payload: Float32Payload
    float64_payload: Float64Payload
    sample_interval_mean: float
    sample_interval_std: float
    sample_interval_median: float
    value_means: _containers.RepeatedScalarFieldContainer[float]
    value_stds: _containers.RepeatedScalarFieldContainer[float]
    value_medians: _containers.RepeatedScalarFieldContainer[float]
    metadata: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, channel_types: _Optional[_Iterable[_Union[ChannelType, str]]] = ..., sensor_name: _Optional[str] = ..., timestamps_microseconds_utc: _Optional[_Iterable[int]] = ..., byte_payload: _Optional[_Union[BytePayload, _Mapping]] = ..., uint32_payload: _Optional[_Union[UInt32Payload, _Mapping]] = ..., uint64_payload: _Optional[_Union[UInt64Payload, _Mapping]] = ..., int32_payload: _Optional[_Union[Int32Payload, _Mapping]] = ..., int64_payload: _Optional[_Union[Int64Payload, _Mapping]] = ..., float32_payload: _Optional[_Union[Float32Payload, _Mapping]] = ..., float64_payload: _Optional[_Union[Float64Payload, _Mapping]] = ..., sample_interval_mean: _Optional[float] = ..., sample_interval_std: _Optional[float] = ..., sample_interval_median: _Optional[float] = ..., value_means: _Optional[_Iterable[float]] = ..., value_stds: _Optional[_Iterable[float]] = ..., value_medians: _Optional[_Iterable[float]] = ..., metadata: _Optional[_Iterable[str]] = ...) -> None: ...

class RedvoxPacketResponse(_message.Message):
    __slots__ = ["type", "checksum", "errors", "metadata"]
    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        OK: _ClassVar[RedvoxPacketResponse.Type]
        ERROR: _ClassVar[RedvoxPacketResponse.Type]
    OK: RedvoxPacketResponse.Type
    ERROR: RedvoxPacketResponse.Type
    class Error(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        NOT_AUTHENTICATED: _ClassVar[RedvoxPacketResponse.Error]
        OTHER: _ClassVar[RedvoxPacketResponse.Error]
    NOT_AUTHENTICATED: RedvoxPacketResponse.Error
    OTHER: RedvoxPacketResponse.Error
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    ERRORS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    type: RedvoxPacketResponse.Type
    checksum: int
    errors: _containers.RepeatedScalarFieldContainer[RedvoxPacketResponse.Error]
    metadata: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, type: _Optional[_Union[RedvoxPacketResponse.Type, str]] = ..., checksum: _Optional[int] = ..., errors: _Optional[_Iterable[_Union[RedvoxPacketResponse.Error, str]]] = ..., metadata: _Optional[_Iterable[str]] = ...) -> None: ...
