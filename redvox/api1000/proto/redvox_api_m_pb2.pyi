from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AcquisitionRequest(_message.Message):
    __slots__ = ["auth_token", "checksum", "firebase_token", "is_encrypted", "payload", "seq_id"]
    AUTH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    FIREBASE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    IS_ENCRYPTED_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    SEQ_ID_FIELD_NUMBER: _ClassVar[int]
    auth_token: str
    checksum: int
    firebase_token: str
    is_encrypted: bool
    payload: bytes
    seq_id: int
    def __init__(self, auth_token: _Optional[str] = ..., firebase_token: _Optional[str] = ..., checksum: _Optional[int] = ..., is_encrypted: bool = ..., payload: _Optional[bytes] = ..., seq_id: _Optional[int] = ...) -> None: ...

class AcquisitionResponse(_message.Message):
    __slots__ = ["checksum", "details", "resend", "response_type", "seq_id"]
    class ResponseType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    AUTH_ERROR: AcquisitionResponse.ResponseType
    CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    DATA_ERROR: AcquisitionResponse.ResponseType
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    OK: AcquisitionResponse.ResponseType
    OTHER_ERROR: AcquisitionResponse.ResponseType
    RESEND_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_TYPE_FIELD_NUMBER: _ClassVar[int]
    SEQ_ID_FIELD_NUMBER: _ClassVar[int]
    UNKNOWN: AcquisitionResponse.ResponseType
    checksum: int
    details: str
    resend: bool
    response_type: AcquisitionResponse.ResponseType
    seq_id: int
    def __init__(self, response_type: _Optional[_Union[AcquisitionResponse.ResponseType, str]] = ..., checksum: _Optional[int] = ..., details: _Optional[str] = ..., resend: bool = ..., seq_id: _Optional[int] = ...) -> None: ...

class EncryptedRedvoxPacketM(_message.Message):
    __slots__ = ["header", "packet"]
    class Header(_message.Message):
        __slots__ = ["auth_email", "auth_token", "firebase_token", "station_id", "station_uuid"]
        AUTH_EMAIL_FIELD_NUMBER: _ClassVar[int]
        AUTH_TOKEN_FIELD_NUMBER: _ClassVar[int]
        FIREBASE_TOKEN_FIELD_NUMBER: _ClassVar[int]
        STATION_ID_FIELD_NUMBER: _ClassVar[int]
        STATION_UUID_FIELD_NUMBER: _ClassVar[int]
        auth_email: str
        auth_token: str
        firebase_token: str
        station_id: str
        station_uuid: str
        def __init__(self, station_id: _Optional[str] = ..., station_uuid: _Optional[str] = ..., auth_token: _Optional[str] = ..., firebase_token: _Optional[str] = ..., auth_email: _Optional[str] = ...) -> None: ...
    HEADER_FIELD_NUMBER: _ClassVar[int]
    PACKET_FIELD_NUMBER: _ClassVar[int]
    header: bytes
    packet: bytes
    def __init__(self, header: _Optional[bytes] = ..., packet: _Optional[bytes] = ...) -> None: ...

class RedvoxPacketM(_message.Message):
    __slots__ = ["api", "event_streams", "metadata", "sensors", "station_information", "sub_api", "timing_information"]
    class Unit(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class DoubleSamplePayload(_message.Message):
        __slots__ = ["metadata", "unit", "value_statistics", "values"]
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        METADATA_FIELD_NUMBER: _ClassVar[int]
        UNIT_FIELD_NUMBER: _ClassVar[int]
        VALUES_FIELD_NUMBER: _ClassVar[int]
        VALUE_STATISTICS_FIELD_NUMBER: _ClassVar[int]
        metadata: _containers.ScalarMap[str, str]
        unit: RedvoxPacketM.Unit
        value_statistics: RedvoxPacketM.SummaryStatistics
        values: _containers.RepeatedScalarFieldContainer[float]
        def __init__(self, unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., values: _Optional[_Iterable[float]] = ..., value_statistics: _Optional[_Union[RedvoxPacketM.SummaryStatistics, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class EventStream(_message.Message):
        __slots__ = ["events", "metadata", "name", "timestamps"]
        class Event(_message.Message):
            __slots__ = ["boolean_payload", "byte_payload", "description", "metadata", "numeric_payload", "string_payload"]
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
            class NumericPayloadEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: float
                def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
            class StringPayloadEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            BOOLEAN_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
            BYTE_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
            DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            NUMERIC_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
            STRING_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
            boolean_payload: _containers.ScalarMap[str, bool]
            byte_payload: _containers.ScalarMap[str, bytes]
            description: str
            metadata: _containers.ScalarMap[str, str]
            numeric_payload: _containers.ScalarMap[str, float]
            string_payload: _containers.ScalarMap[str, str]
            def __init__(self, description: _Optional[str] = ..., string_payload: _Optional[_Mapping[str, str]] = ..., numeric_payload: _Optional[_Mapping[str, float]] = ..., boolean_payload: _Optional[_Mapping[str, bool]] = ..., byte_payload: _Optional[_Mapping[str, bytes]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        EVENTS_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
        events: _containers.RepeatedCompositeFieldContainer[RedvoxPacketM.EventStream.Event]
        metadata: _containers.ScalarMap[str, str]
        name: str
        timestamps: RedvoxPacketM.TimingPayload
        def __init__(self, name: _Optional[str] = ..., timestamps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., events: _Optional[_Iterable[_Union[RedvoxPacketM.EventStream.Event, _Mapping]]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class MetadataEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class SamplePayload(_message.Message):
        __slots__ = ["metadata", "unit", "value_statistics", "values"]
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        METADATA_FIELD_NUMBER: _ClassVar[int]
        UNIT_FIELD_NUMBER: _ClassVar[int]
        VALUES_FIELD_NUMBER: _ClassVar[int]
        VALUE_STATISTICS_FIELD_NUMBER: _ClassVar[int]
        metadata: _containers.ScalarMap[str, str]
        unit: RedvoxPacketM.Unit
        value_statistics: RedvoxPacketM.SummaryStatistics
        values: _containers.RepeatedScalarFieldContainer[float]
        def __init__(self, unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., values: _Optional[_Iterable[float]] = ..., value_statistics: _Optional[_Union[RedvoxPacketM.SummaryStatistics, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class Sensors(_message.Message):
        __slots__ = ["accelerometer", "ambient_temperature", "audio", "compressed_audio", "gravity", "gyroscope", "image", "light", "linear_acceleration", "location", "magnetometer", "metadata", "orientation", "pressure", "proximity", "relative_humidity", "rotation_vector", "velocity"]
        class Audio(_message.Message):
            __slots__ = ["bits_of_precision", "encoding", "first_sample_timestamp", "is_scrambled", "metadata", "sample_rate", "samples", "sensor_description"]
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            BITS_OF_PRECISION_FIELD_NUMBER: _ClassVar[int]
            ENCODING_FIELD_NUMBER: _ClassVar[int]
            FIRST_SAMPLE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
            IS_SCRAMBLED_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            SAMPLES_FIELD_NUMBER: _ClassVar[int]
            SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
            SENSOR_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            bits_of_precision: float
            encoding: str
            first_sample_timestamp: float
            is_scrambled: bool
            metadata: _containers.ScalarMap[str, str]
            sample_rate: float
            samples: RedvoxPacketM.SamplePayload
            sensor_description: str
            def __init__(self, sensor_description: _Optional[str] = ..., first_sample_timestamp: _Optional[float] = ..., sample_rate: _Optional[float] = ..., bits_of_precision: _Optional[float] = ..., is_scrambled: bool = ..., encoding: _Optional[str] = ..., samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class CompressedAudio(_message.Message):
            __slots__ = ["audio_bytes", "audio_codec", "first_sample_timestamp", "is_scrambled", "metadata", "sample_rate", "sensor_description"]
            class AudioCodec(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            AUDIO_BYTES_FIELD_NUMBER: _ClassVar[int]
            AUDIO_CODEC_FIELD_NUMBER: _ClassVar[int]
            FIRST_SAMPLE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
            FLAC: RedvoxPacketM.Sensors.CompressedAudio.AudioCodec
            IS_SCRAMBLED_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
            SENSOR_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            UNKNOWN: RedvoxPacketM.Sensors.CompressedAudio.AudioCodec
            audio_bytes: bytes
            audio_codec: RedvoxPacketM.Sensors.CompressedAudio.AudioCodec
            first_sample_timestamp: float
            is_scrambled: bool
            metadata: _containers.ScalarMap[str, str]
            sample_rate: float
            sensor_description: str
            def __init__(self, sensor_description: _Optional[str] = ..., first_sample_timestamp: _Optional[float] = ..., sample_rate: _Optional[float] = ..., is_scrambled: bool = ..., audio_bytes: _Optional[bytes] = ..., audio_codec: _Optional[_Union[RedvoxPacketM.Sensors.CompressedAudio.AudioCodec, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class Image(_message.Message):
            __slots__ = ["image_codec", "metadata", "samples", "sensor_description", "timestamps"]
            class ImageCodec(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            BMP: RedvoxPacketM.Sensors.Image.ImageCodec
            IMAGE_CODEC_FIELD_NUMBER: _ClassVar[int]
            JPG: RedvoxPacketM.Sensors.Image.ImageCodec
            METADATA_FIELD_NUMBER: _ClassVar[int]
            PNG: RedvoxPacketM.Sensors.Image.ImageCodec
            SAMPLES_FIELD_NUMBER: _ClassVar[int]
            SENSOR_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
            UNKNOWN: RedvoxPacketM.Sensors.Image.ImageCodec
            image_codec: RedvoxPacketM.Sensors.Image.ImageCodec
            metadata: _containers.ScalarMap[str, str]
            samples: _containers.RepeatedScalarFieldContainer[bytes]
            sensor_description: str
            timestamps: RedvoxPacketM.TimingPayload
            def __init__(self, sensor_description: _Optional[str] = ..., timestamps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., samples: _Optional[_Iterable[bytes]] = ..., image_codec: _Optional[_Union[RedvoxPacketM.Sensors.Image.ImageCodec, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class Location(_message.Message):
            __slots__ = ["altitude_samples", "bearing_accuracy_samples", "bearing_samples", "horizontal_accuracy_samples", "last_best_location", "latitude_samples", "location_permissions_granted", "location_providers", "location_services_enabled", "location_services_requested", "longitude_samples", "metadata", "overall_best_location", "sensor_description", "speed_accuracy_samples", "speed_samples", "timestamps", "timestamps_gps", "vertical_accuracy_samples"]
            class LocationProvider(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            class BestLocation(_message.Message):
                __slots__ = ["altitude", "altitude_timestamp", "altitude_unit", "bearing", "bearing_accuracy", "bearing_accuracy_unit", "bearing_timestamp", "bearing_unit", "horizontal_accuracy", "horizontal_accuracy_unit", "latitude", "latitude_longitude_timestamp", "latitude_longitude_unit", "location_provider", "longitude", "metadata", "method", "score", "speed", "speed_accuracy", "speed_accuracy_unit", "speed_timestamp", "speed_unit", "vertical_accuracy", "vertical_accuracy_unit"]
                class LocationScoreMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                    __slots__ = []
                class BestTimestamp(_message.Message):
                    __slots__ = ["gps", "mach", "metadata", "unit"]
                    class MetadataEntry(_message.Message):
                        __slots__ = ["key", "value"]
                        KEY_FIELD_NUMBER: _ClassVar[int]
                        VALUE_FIELD_NUMBER: _ClassVar[int]
                        key: str
                        value: str
                        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
                    GPS_FIELD_NUMBER: _ClassVar[int]
                    MACH_FIELD_NUMBER: _ClassVar[int]
                    METADATA_FIELD_NUMBER: _ClassVar[int]
                    UNIT_FIELD_NUMBER: _ClassVar[int]
                    gps: float
                    mach: float
                    metadata: _containers.ScalarMap[str, str]
                    unit: RedvoxPacketM.Unit
                    def __init__(self, unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., mach: _Optional[float] = ..., gps: _Optional[float] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
                class MetadataEntry(_message.Message):
                    __slots__ = ["key", "value"]
                    KEY_FIELD_NUMBER: _ClassVar[int]
                    VALUE_FIELD_NUMBER: _ClassVar[int]
                    key: str
                    value: str
                    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
                ALTITUDE_FIELD_NUMBER: _ClassVar[int]
                ALTITUDE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
                ALTITUDE_UNIT_FIELD_NUMBER: _ClassVar[int]
                BEARING_ACCURACY_FIELD_NUMBER: _ClassVar[int]
                BEARING_ACCURACY_UNIT_FIELD_NUMBER: _ClassVar[int]
                BEARING_FIELD_NUMBER: _ClassVar[int]
                BEARING_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
                BEARING_UNIT_FIELD_NUMBER: _ClassVar[int]
                HORIZONTAL_ACCURACY_FIELD_NUMBER: _ClassVar[int]
                HORIZONTAL_ACCURACY_UNIT_FIELD_NUMBER: _ClassVar[int]
                LATITUDE_FIELD_NUMBER: _ClassVar[int]
                LATITUDE_LONGITUDE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
                LATITUDE_LONGITUDE_UNIT_FIELD_NUMBER: _ClassVar[int]
                LOCATION_PROVIDER_FIELD_NUMBER: _ClassVar[int]
                LONGITUDE_FIELD_NUMBER: _ClassVar[int]
                METADATA_FIELD_NUMBER: _ClassVar[int]
                METHOD_FIELD_NUMBER: _ClassVar[int]
                SCORE_FIELD_NUMBER: _ClassVar[int]
                SPEED_ACCURACY_FIELD_NUMBER: _ClassVar[int]
                SPEED_ACCURACY_UNIT_FIELD_NUMBER: _ClassVar[int]
                SPEED_FIELD_NUMBER: _ClassVar[int]
                SPEED_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
                SPEED_UNIT_FIELD_NUMBER: _ClassVar[int]
                UNKNOWN_METHOD: RedvoxPacketM.Sensors.Location.BestLocation.LocationScoreMethod
                VERTICAL_ACCURACY_FIELD_NUMBER: _ClassVar[int]
                VERTICAL_ACCURACY_UNIT_FIELD_NUMBER: _ClassVar[int]
                altitude: float
                altitude_timestamp: RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp
                altitude_unit: RedvoxPacketM.Unit
                bearing: float
                bearing_accuracy: float
                bearing_accuracy_unit: RedvoxPacketM.Unit
                bearing_timestamp: RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp
                bearing_unit: RedvoxPacketM.Unit
                horizontal_accuracy: float
                horizontal_accuracy_unit: RedvoxPacketM.Unit
                latitude: float
                latitude_longitude_timestamp: RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp
                latitude_longitude_unit: RedvoxPacketM.Unit
                location_provider: RedvoxPacketM.Sensors.Location.LocationProvider
                longitude: float
                metadata: _containers.ScalarMap[str, str]
                method: RedvoxPacketM.Sensors.Location.BestLocation.LocationScoreMethod
                score: float
                speed: float
                speed_accuracy: float
                speed_accuracy_unit: RedvoxPacketM.Unit
                speed_timestamp: RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp
                speed_unit: RedvoxPacketM.Unit
                vertical_accuracy: float
                vertical_accuracy_unit: RedvoxPacketM.Unit
                def __init__(self, latitude_longitude_timestamp: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp, _Mapping]] = ..., altitude_timestamp: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp, _Mapping]] = ..., speed_timestamp: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp, _Mapping]] = ..., bearing_timestamp: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation.BestTimestamp, _Mapping]] = ..., latitude_longitude_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., altitude_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., speed_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., bearing_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., vertical_accuracy_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., horizontal_accuracy_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., speed_accuracy_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., bearing_accuracy_unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., latitude: _Optional[float] = ..., longitude: _Optional[float] = ..., altitude: _Optional[float] = ..., speed: _Optional[float] = ..., bearing: _Optional[float] = ..., vertical_accuracy: _Optional[float] = ..., horizontal_accuracy: _Optional[float] = ..., speed_accuracy: _Optional[float] = ..., bearing_accuracy: _Optional[float] = ..., score: _Optional[float] = ..., method: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation.LocationScoreMethod, str]] = ..., location_provider: _Optional[_Union[RedvoxPacketM.Sensors.Location.LocationProvider, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            ALTITUDE_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            BEARING_ACCURACY_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            BEARING_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            GPS: RedvoxPacketM.Sensors.Location.LocationProvider
            HORIZONTAL_ACCURACY_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            LAST_BEST_LOCATION_FIELD_NUMBER: _ClassVar[int]
            LATITUDE_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            LOCATION_PERMISSIONS_GRANTED_FIELD_NUMBER: _ClassVar[int]
            LOCATION_PROVIDERS_FIELD_NUMBER: _ClassVar[int]
            LOCATION_SERVICES_ENABLED_FIELD_NUMBER: _ClassVar[int]
            LOCATION_SERVICES_REQUESTED_FIELD_NUMBER: _ClassVar[int]
            LONGITUDE_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            NETWORK: RedvoxPacketM.Sensors.Location.LocationProvider
            NONE: RedvoxPacketM.Sensors.Location.LocationProvider
            OVERALL_BEST_LOCATION_FIELD_NUMBER: _ClassVar[int]
            SENSOR_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            SPEED_ACCURACY_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            SPEED_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
            TIMESTAMPS_GPS_FIELD_NUMBER: _ClassVar[int]
            UNKNOWN: RedvoxPacketM.Sensors.Location.LocationProvider
            USER: RedvoxPacketM.Sensors.Location.LocationProvider
            VERTICAL_ACCURACY_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            altitude_samples: RedvoxPacketM.SamplePayload
            bearing_accuracy_samples: RedvoxPacketM.SamplePayload
            bearing_samples: RedvoxPacketM.SamplePayload
            horizontal_accuracy_samples: RedvoxPacketM.SamplePayload
            last_best_location: RedvoxPacketM.Sensors.Location.BestLocation
            latitude_samples: RedvoxPacketM.DoubleSamplePayload
            location_permissions_granted: bool
            location_providers: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.Sensors.Location.LocationProvider]
            location_services_enabled: bool
            location_services_requested: bool
            longitude_samples: RedvoxPacketM.DoubleSamplePayload
            metadata: _containers.ScalarMap[str, str]
            overall_best_location: RedvoxPacketM.Sensors.Location.BestLocation
            sensor_description: str
            speed_accuracy_samples: RedvoxPacketM.SamplePayload
            speed_samples: RedvoxPacketM.SamplePayload
            timestamps: RedvoxPacketM.TimingPayload
            timestamps_gps: RedvoxPacketM.TimingPayload
            vertical_accuracy_samples: RedvoxPacketM.SamplePayload
            def __init__(self, sensor_description: _Optional[str] = ..., timestamps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., timestamps_gps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., latitude_samples: _Optional[_Union[RedvoxPacketM.DoubleSamplePayload, _Mapping]] = ..., longitude_samples: _Optional[_Union[RedvoxPacketM.DoubleSamplePayload, _Mapping]] = ..., altitude_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., speed_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., bearing_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., horizontal_accuracy_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., vertical_accuracy_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., speed_accuracy_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., bearing_accuracy_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., last_best_location: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation, _Mapping]] = ..., overall_best_location: _Optional[_Union[RedvoxPacketM.Sensors.Location.BestLocation, _Mapping]] = ..., location_permissions_granted: bool = ..., location_services_requested: bool = ..., location_services_enabled: bool = ..., location_providers: _Optional[_Iterable[_Union[RedvoxPacketM.Sensors.Location.LocationProvider, str]]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        class Single(_message.Message):
            __slots__ = ["metadata", "samples", "sensor_description", "timestamps"]
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            METADATA_FIELD_NUMBER: _ClassVar[int]
            SAMPLES_FIELD_NUMBER: _ClassVar[int]
            SENSOR_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
            metadata: _containers.ScalarMap[str, str]
            samples: RedvoxPacketM.SamplePayload
            sensor_description: str
            timestamps: RedvoxPacketM.TimingPayload
            def __init__(self, sensor_description: _Optional[str] = ..., timestamps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class Xyz(_message.Message):
            __slots__ = ["metadata", "sensor_description", "timestamps", "x_samples", "y_samples", "z_samples"]
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            METADATA_FIELD_NUMBER: _ClassVar[int]
            SENSOR_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
            X_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            Y_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            Z_SAMPLES_FIELD_NUMBER: _ClassVar[int]
            metadata: _containers.ScalarMap[str, str]
            sensor_description: str
            timestamps: RedvoxPacketM.TimingPayload
            x_samples: RedvoxPacketM.SamplePayload
            y_samples: RedvoxPacketM.SamplePayload
            z_samples: RedvoxPacketM.SamplePayload
            def __init__(self, sensor_description: _Optional[str] = ..., timestamps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., x_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., y_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., z_samples: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
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
        METADATA_FIELD_NUMBER: _ClassVar[int]
        ORIENTATION_FIELD_NUMBER: _ClassVar[int]
        PRESSURE_FIELD_NUMBER: _ClassVar[int]
        PROXIMITY_FIELD_NUMBER: _ClassVar[int]
        RELATIVE_HUMIDITY_FIELD_NUMBER: _ClassVar[int]
        ROTATION_VECTOR_FIELD_NUMBER: _ClassVar[int]
        VELOCITY_FIELD_NUMBER: _ClassVar[int]
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
        metadata: _containers.ScalarMap[str, str]
        orientation: RedvoxPacketM.Sensors.Xyz
        pressure: RedvoxPacketM.Sensors.Single
        proximity: RedvoxPacketM.Sensors.Single
        relative_humidity: RedvoxPacketM.Sensors.Single
        rotation_vector: RedvoxPacketM.Sensors.Xyz
        velocity: RedvoxPacketM.Sensors.Xyz
        def __init__(self, accelerometer: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., ambient_temperature: _Optional[_Union[RedvoxPacketM.Sensors.Single, _Mapping]] = ..., audio: _Optional[_Union[RedvoxPacketM.Sensors.Audio, _Mapping]] = ..., compressed_audio: _Optional[_Union[RedvoxPacketM.Sensors.CompressedAudio, _Mapping]] = ..., gravity: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., gyroscope: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., image: _Optional[_Union[RedvoxPacketM.Sensors.Image, _Mapping]] = ..., light: _Optional[_Union[RedvoxPacketM.Sensors.Single, _Mapping]] = ..., linear_acceleration: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., location: _Optional[_Union[RedvoxPacketM.Sensors.Location, _Mapping]] = ..., magnetometer: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., orientation: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., pressure: _Optional[_Union[RedvoxPacketM.Sensors.Single, _Mapping]] = ..., proximity: _Optional[_Union[RedvoxPacketM.Sensors.Single, _Mapping]] = ..., relative_humidity: _Optional[_Union[RedvoxPacketM.Sensors.Single, _Mapping]] = ..., rotation_vector: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., velocity: _Optional[_Union[RedvoxPacketM.Sensors.Xyz, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class StationInformation(_message.Message):
        __slots__ = ["app_settings", "app_version", "auth_id", "description", "id", "is_private", "make", "metadata", "model", "os", "os_version", "service_urls", "station_metrics", "uuid"]
        class MetricsRate(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = []
        class OsType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = []
        class AppSettings(_message.Message):
            __slots__ = ["additional_input_sensors", "audio_sampling_rate", "audio_source_tuning", "auth_server_url", "auto_delete_data_files", "automatically_record", "data_server_url", "fft_overlap", "launch_at_power_up", "metadata", "metrics_rate", "provide_backfill", "publish_data_as_private", "push_to_server", "remove_sensor_dc_offset", "samples_per_window", "scramble_audio_data", "station_description", "station_id", "storage_space_allowance", "time_sync_server_url", "use_altitude", "use_custom_auth_server", "use_custom_data_server", "use_custom_time_sync_server", "use_latitude", "use_location_services", "use_longitude", "use_sd_card_for_data_storage"]
            class AudioSamplingRate(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            class AudioSourceTuning(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            class FftOverlap(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            class InputSensor(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            ACCELEROMETER: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            ACCELEROMETER_FAST: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            ADDITIONAL_INPUT_SENSORS_FIELD_NUMBER: _ClassVar[int]
            AMBIENT_TEMPERATURE: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            AUDIO: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            AUDIO_SAMPLING_RATE_FIELD_NUMBER: _ClassVar[int]
            AUDIO_SOURCE_TUNING_FIELD_NUMBER: _ClassVar[int]
            AUDIO_TUNING: RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning
            AUTH_SERVER_URL_FIELD_NUMBER: _ClassVar[int]
            AUTOMATICALLY_RECORD_FIELD_NUMBER: _ClassVar[int]
            AUTO_DELETE_DATA_FILES_FIELD_NUMBER: _ClassVar[int]
            COMPRESSED_AUDIO: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            DATA_SERVER_URL_FIELD_NUMBER: _ClassVar[int]
            FFT_OVERLAP_FIELD_NUMBER: _ClassVar[int]
            GRAVITY: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            GYROSCOPE: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            GYROSCOPE_FAST: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            HZ_16000: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            HZ_48000: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            HZ_80: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            HZ_800: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            HZ_8000: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            IMAGE_PER_PACKET: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            IMAGE_PER_SECOND: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            INFRASOUND_TUNING: RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning
            LAUNCH_AT_POWER_UP_FIELD_NUMBER: _ClassVar[int]
            LIGHT: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            LINEAR_ACCELERATION: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            LOCATION: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            LOW_AUDIO_TUNING: RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning
            MAGNETOMETER: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            MAGNETOMETER_FAST: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            METADATA_FIELD_NUMBER: _ClassVar[int]
            METRICS_RATE_FIELD_NUMBER: _ClassVar[int]
            ORIENTATION: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            PERCENT_25: RedvoxPacketM.StationInformation.AppSettings.FftOverlap
            PERCENT_50: RedvoxPacketM.StationInformation.AppSettings.FftOverlap
            PERCENT_75: RedvoxPacketM.StationInformation.AppSettings.FftOverlap
            PRESSURE: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            PROVIDE_BACKFILL_FIELD_NUMBER: _ClassVar[int]
            PROXIMITY: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            PUBLISH_DATA_AS_PRIVATE_FIELD_NUMBER: _ClassVar[int]
            PUSH_TO_SERVER_FIELD_NUMBER: _ClassVar[int]
            RELATIVE_HUMIDITY: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            REMOVE_SENSOR_DC_OFFSET_FIELD_NUMBER: _ClassVar[int]
            ROTATION_VECTOR: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            SAMPLES_PER_WINDOW_FIELD_NUMBER: _ClassVar[int]
            SCRAMBLE_AUDIO_DATA_FIELD_NUMBER: _ClassVar[int]
            STATION_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
            STATION_ID_FIELD_NUMBER: _ClassVar[int]
            STORAGE_SPACE_ALLOWANCE_FIELD_NUMBER: _ClassVar[int]
            TIME_SYNC_SERVER_URL_FIELD_NUMBER: _ClassVar[int]
            UNKNOWN: RedvoxPacketM.StationInformation.AppSettings.FftOverlap
            UNKNOWN_SAMPLING_RATE: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            UNKNOWN_SENSOR: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            UNKNOWN_TUNING: RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning
            USE_ALTITUDE_FIELD_NUMBER: _ClassVar[int]
            USE_CUSTOM_AUTH_SERVER_FIELD_NUMBER: _ClassVar[int]
            USE_CUSTOM_DATA_SERVER_FIELD_NUMBER: _ClassVar[int]
            USE_CUSTOM_TIME_SYNC_SERVER_FIELD_NUMBER: _ClassVar[int]
            USE_LATITUDE_FIELD_NUMBER: _ClassVar[int]
            USE_LOCATION_SERVICES_FIELD_NUMBER: _ClassVar[int]
            USE_LONGITUDE_FIELD_NUMBER: _ClassVar[int]
            USE_SD_CARD_FOR_DATA_STORAGE_FIELD_NUMBER: _ClassVar[int]
            VELOCITY: RedvoxPacketM.StationInformation.AppSettings.InputSensor
            additional_input_sensors: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.StationInformation.AppSettings.InputSensor]
            audio_sampling_rate: RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate
            audio_source_tuning: RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning
            auth_server_url: str
            auto_delete_data_files: bool
            automatically_record: bool
            data_server_url: str
            fft_overlap: RedvoxPacketM.StationInformation.AppSettings.FftOverlap
            launch_at_power_up: bool
            metadata: _containers.ScalarMap[str, str]
            metrics_rate: RedvoxPacketM.StationInformation.MetricsRate
            provide_backfill: bool
            publish_data_as_private: bool
            push_to_server: bool
            remove_sensor_dc_offset: bool
            samples_per_window: float
            scramble_audio_data: bool
            station_description: str
            station_id: str
            storage_space_allowance: float
            time_sync_server_url: str
            use_altitude: float
            use_custom_auth_server: bool
            use_custom_data_server: bool
            use_custom_time_sync_server: bool
            use_latitude: float
            use_location_services: bool
            use_longitude: float
            use_sd_card_for_data_storage: bool
            def __init__(self, audio_sampling_rate: _Optional[_Union[RedvoxPacketM.StationInformation.AppSettings.AudioSamplingRate, str]] = ..., samples_per_window: _Optional[float] = ..., audio_source_tuning: _Optional[_Union[RedvoxPacketM.StationInformation.AppSettings.AudioSourceTuning, str]] = ..., additional_input_sensors: _Optional[_Iterable[_Union[RedvoxPacketM.StationInformation.AppSettings.InputSensor, str]]] = ..., automatically_record: bool = ..., launch_at_power_up: bool = ..., station_id: _Optional[str] = ..., station_description: _Optional[str] = ..., push_to_server: bool = ..., publish_data_as_private: bool = ..., scramble_audio_data: bool = ..., provide_backfill: bool = ..., remove_sensor_dc_offset: bool = ..., fft_overlap: _Optional[_Union[RedvoxPacketM.StationInformation.AppSettings.FftOverlap, str]] = ..., use_custom_time_sync_server: bool = ..., time_sync_server_url: _Optional[str] = ..., use_custom_data_server: bool = ..., data_server_url: _Optional[str] = ..., use_custom_auth_server: bool = ..., auth_server_url: _Optional[str] = ..., auto_delete_data_files: bool = ..., storage_space_allowance: _Optional[float] = ..., use_sd_card_for_data_storage: bool = ..., use_location_services: bool = ..., use_latitude: _Optional[float] = ..., use_longitude: _Optional[float] = ..., use_altitude: _Optional[float] = ..., metrics_rate: _Optional[_Union[RedvoxPacketM.StationInformation.MetricsRate, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        class ServiceUrls(_message.Message):
            __slots__ = ["acquisition_server", "auth_server", "metadata", "synch_server"]
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            ACQUISITION_SERVER_FIELD_NUMBER: _ClassVar[int]
            AUTH_SERVER_FIELD_NUMBER: _ClassVar[int]
            METADATA_FIELD_NUMBER: _ClassVar[int]
            SYNCH_SERVER_FIELD_NUMBER: _ClassVar[int]
            acquisition_server: str
            auth_server: str
            metadata: _containers.ScalarMap[str, str]
            synch_server: str
            def __init__(self, auth_server: _Optional[str] = ..., synch_server: _Optional[str] = ..., acquisition_server: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        class StationMetrics(_message.Message):
            __slots__ = ["available_disk", "available_ram", "battery", "battery_current", "cell_service_state", "cpu_utilization", "metadata", "network_strength", "network_type", "power_state", "screen_brightness", "screen_state", "temperature", "timestamps", "wifi_wake_lock"]
            class CellServiceState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            class NetworkType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            class PowerState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            class ScreenState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            class WifiWakeLock(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            class MetadataEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            AVAILABLE_DISK_FIELD_NUMBER: _ClassVar[int]
            AVAILABLE_RAM_FIELD_NUMBER: _ClassVar[int]
            BATTERY_CURRENT_FIELD_NUMBER: _ClassVar[int]
            BATTERY_FIELD_NUMBER: _ClassVar[int]
            CELLULAR: RedvoxPacketM.StationInformation.StationMetrics.NetworkType
            CELL_SERVICE_STATE_FIELD_NUMBER: _ClassVar[int]
            CHARGED: RedvoxPacketM.StationInformation.StationMetrics.PowerState
            CHARGING: RedvoxPacketM.StationInformation.StationMetrics.PowerState
            CPU_UTILIZATION_FIELD_NUMBER: _ClassVar[int]
            EMERGENCY: RedvoxPacketM.StationInformation.StationMetrics.CellServiceState
            HEADLESS: RedvoxPacketM.StationInformation.StationMetrics.ScreenState
            HIGH_PERF: RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock
            LOW_LATENCY: RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock
            METADATA_FIELD_NUMBER: _ClassVar[int]
            NETWORK_STRENGTH_FIELD_NUMBER: _ClassVar[int]
            NETWORK_TYPE_FIELD_NUMBER: _ClassVar[int]
            NOMINAL: RedvoxPacketM.StationInformation.StationMetrics.CellServiceState
            NONE: RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock
            NO_NETWORK: RedvoxPacketM.StationInformation.StationMetrics.NetworkType
            OFF: RedvoxPacketM.StationInformation.StationMetrics.ScreenState
            ON: RedvoxPacketM.StationInformation.StationMetrics.ScreenState
            OTHER: RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock
            OUT_OF_SERVICE: RedvoxPacketM.StationInformation.StationMetrics.CellServiceState
            POWER_OFF: RedvoxPacketM.StationInformation.StationMetrics.CellServiceState
            POWER_STATE_FIELD_NUMBER: _ClassVar[int]
            SCREEN_BRIGHTNESS_FIELD_NUMBER: _ClassVar[int]
            SCREEN_STATE_FIELD_NUMBER: _ClassVar[int]
            TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
            TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
            UNKNOWN: RedvoxPacketM.StationInformation.StationMetrics.CellServiceState
            UNKNOWN_NETWORK: RedvoxPacketM.StationInformation.StationMetrics.NetworkType
            UNKNOWN_POWER_STATE: RedvoxPacketM.StationInformation.StationMetrics.PowerState
            UNKNOWN_SCREEN_STATE: RedvoxPacketM.StationInformation.StationMetrics.ScreenState
            UNPLUGGED: RedvoxPacketM.StationInformation.StationMetrics.PowerState
            WIFI: RedvoxPacketM.StationInformation.StationMetrics.NetworkType
            WIFI_WAKE_LOCK_FIELD_NUMBER: _ClassVar[int]
            WIRED: RedvoxPacketM.StationInformation.StationMetrics.NetworkType
            available_disk: RedvoxPacketM.SamplePayload
            available_ram: RedvoxPacketM.SamplePayload
            battery: RedvoxPacketM.SamplePayload
            battery_current: RedvoxPacketM.SamplePayload
            cell_service_state: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.StationInformation.StationMetrics.CellServiceState]
            cpu_utilization: RedvoxPacketM.SamplePayload
            metadata: _containers.ScalarMap[str, str]
            network_strength: RedvoxPacketM.SamplePayload
            network_type: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.StationInformation.StationMetrics.NetworkType]
            power_state: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.StationInformation.StationMetrics.PowerState]
            screen_brightness: RedvoxPacketM.SamplePayload
            screen_state: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.StationInformation.StationMetrics.ScreenState]
            temperature: RedvoxPacketM.SamplePayload
            timestamps: RedvoxPacketM.TimingPayload
            wifi_wake_lock: _containers.RepeatedScalarFieldContainer[RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock]
            def __init__(self, timestamps: _Optional[_Union[RedvoxPacketM.TimingPayload, _Mapping]] = ..., network_type: _Optional[_Iterable[_Union[RedvoxPacketM.StationInformation.StationMetrics.NetworkType, str]]] = ..., cell_service_state: _Optional[_Iterable[_Union[RedvoxPacketM.StationInformation.StationMetrics.CellServiceState, str]]] = ..., network_strength: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., temperature: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., battery: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., battery_current: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., available_ram: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., available_disk: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., cpu_utilization: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., power_state: _Optional[_Iterable[_Union[RedvoxPacketM.StationInformation.StationMetrics.PowerState, str]]] = ..., wifi_wake_lock: _Optional[_Iterable[_Union[RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock, str]]] = ..., screen_state: _Optional[_Iterable[_Union[RedvoxPacketM.StationInformation.StationMetrics.ScreenState, str]]] = ..., screen_brightness: _Optional[_Union[RedvoxPacketM.SamplePayload, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        ANDROID: RedvoxPacketM.StationInformation.OsType
        APP_SETTINGS_FIELD_NUMBER: _ClassVar[int]
        APP_VERSION_FIELD_NUMBER: _ClassVar[int]
        AUTH_ID_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        ID_FIELD_NUMBER: _ClassVar[int]
        IOS: RedvoxPacketM.StationInformation.OsType
        IS_PRIVATE_FIELD_NUMBER: _ClassVar[int]
        LINUX: RedvoxPacketM.StationInformation.OsType
        MAKE_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        MODEL_FIELD_NUMBER: _ClassVar[int]
        ONCE_PER_PACKET: RedvoxPacketM.StationInformation.MetricsRate
        ONCE_PER_SECOND: RedvoxPacketM.StationInformation.MetricsRate
        OSX: RedvoxPacketM.StationInformation.OsType
        OS_FIELD_NUMBER: _ClassVar[int]
        OS_VERSION_FIELD_NUMBER: _ClassVar[int]
        SERVICE_URLS_FIELD_NUMBER: _ClassVar[int]
        STATION_METRICS_FIELD_NUMBER: _ClassVar[int]
        UNKNOWN: RedvoxPacketM.StationInformation.MetricsRate
        UNKNOWN_OS: RedvoxPacketM.StationInformation.OsType
        UUID_FIELD_NUMBER: _ClassVar[int]
        WINDOWS: RedvoxPacketM.StationInformation.OsType
        app_settings: RedvoxPacketM.StationInformation.AppSettings
        app_version: str
        auth_id: str
        description: str
        id: str
        is_private: bool
        make: str
        metadata: _containers.ScalarMap[str, str]
        model: str
        os: RedvoxPacketM.StationInformation.OsType
        os_version: str
        service_urls: RedvoxPacketM.StationInformation.ServiceUrls
        station_metrics: RedvoxPacketM.StationInformation.StationMetrics
        uuid: str
        def __init__(self, id: _Optional[str] = ..., uuid: _Optional[str] = ..., description: _Optional[str] = ..., auth_id: _Optional[str] = ..., make: _Optional[str] = ..., model: _Optional[str] = ..., os: _Optional[_Union[RedvoxPacketM.StationInformation.OsType, str]] = ..., os_version: _Optional[str] = ..., app_version: _Optional[str] = ..., is_private: bool = ..., app_settings: _Optional[_Union[RedvoxPacketM.StationInformation.AppSettings, _Mapping]] = ..., station_metrics: _Optional[_Union[RedvoxPacketM.StationInformation.StationMetrics, _Mapping]] = ..., service_urls: _Optional[_Union[RedvoxPacketM.StationInformation.ServiceUrls, _Mapping]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class SummaryStatistics(_message.Message):
        __slots__ = ["count", "max", "mean", "metadata", "min", "range", "standard_deviation"]
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        COUNT_FIELD_NUMBER: _ClassVar[int]
        MAX_FIELD_NUMBER: _ClassVar[int]
        MEAN_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        MIN_FIELD_NUMBER: _ClassVar[int]
        RANGE_FIELD_NUMBER: _ClassVar[int]
        STANDARD_DEVIATION_FIELD_NUMBER: _ClassVar[int]
        count: float
        max: float
        mean: float
        metadata: _containers.ScalarMap[str, str]
        min: float
        range: float
        standard_deviation: float
        def __init__(self, count: _Optional[float] = ..., mean: _Optional[float] = ..., standard_deviation: _Optional[float] = ..., min: _Optional[float] = ..., max: _Optional[float] = ..., range: _Optional[float] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class TimingInformation(_message.Message):
        __slots__ = ["app_start_mach_timestamp", "best_latency", "best_offset", "metadata", "packet_end_mach_timestamp", "packet_end_os_timestamp", "packet_start_mach_timestamp", "packet_start_os_timestamp", "score", "score_method", "server_acquisition_arrival_timestamp", "synch_exchanges", "unit"]
        class TimingScoreMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = []
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        class SynchExchange(_message.Message):
            __slots__ = ["a1", "a2", "a3", "b1", "b2", "b3", "metadata", "unit"]
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
            METADATA_FIELD_NUMBER: _ClassVar[int]
            UNIT_FIELD_NUMBER: _ClassVar[int]
            a1: float
            a2: float
            a3: float
            b1: float
            b2: float
            b3: float
            metadata: _containers.ScalarMap[str, str]
            unit: RedvoxPacketM.Unit
            def __init__(self, a1: _Optional[float] = ..., a2: _Optional[float] = ..., a3: _Optional[float] = ..., b1: _Optional[float] = ..., b2: _Optional[float] = ..., b3: _Optional[float] = ..., unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
        APP_START_MACH_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        BEST_LATENCY_FIELD_NUMBER: _ClassVar[int]
        BEST_OFFSET_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        PACKET_END_MACH_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        PACKET_END_OS_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        PACKET_START_MACH_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        PACKET_START_OS_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        SCORE_FIELD_NUMBER: _ClassVar[int]
        SCORE_METHOD_FIELD_NUMBER: _ClassVar[int]
        SERVER_ACQUISITION_ARRIVAL_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        SYNCH_EXCHANGES_FIELD_NUMBER: _ClassVar[int]
        UNIT_FIELD_NUMBER: _ClassVar[int]
        UNKNOWN: RedvoxPacketM.TimingInformation.TimingScoreMethod
        app_start_mach_timestamp: float
        best_latency: float
        best_offset: float
        metadata: _containers.ScalarMap[str, str]
        packet_end_mach_timestamp: float
        packet_end_os_timestamp: float
        packet_start_mach_timestamp: float
        packet_start_os_timestamp: float
        score: float
        score_method: RedvoxPacketM.TimingInformation.TimingScoreMethod
        server_acquisition_arrival_timestamp: float
        synch_exchanges: _containers.RepeatedCompositeFieldContainer[RedvoxPacketM.TimingInformation.SynchExchange]
        unit: RedvoxPacketM.Unit
        def __init__(self, packet_start_os_timestamp: _Optional[float] = ..., packet_start_mach_timestamp: _Optional[float] = ..., packet_end_os_timestamp: _Optional[float] = ..., packet_end_mach_timestamp: _Optional[float] = ..., server_acquisition_arrival_timestamp: _Optional[float] = ..., app_start_mach_timestamp: _Optional[float] = ..., synch_exchanges: _Optional[_Iterable[_Union[RedvoxPacketM.TimingInformation.SynchExchange, _Mapping]]] = ..., best_latency: _Optional[float] = ..., best_offset: _Optional[float] = ..., score: _Optional[float] = ..., score_method: _Optional[_Union[RedvoxPacketM.TimingInformation.TimingScoreMethod, str]] = ..., unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class TimingPayload(_message.Message):
        __slots__ = ["mean_sample_rate", "metadata", "stdev_sample_rate", "timestamp_statistics", "timestamps", "unit"]
        class MetadataEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        MEAN_SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        STDEV_SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
        TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
        TIMESTAMP_STATISTICS_FIELD_NUMBER: _ClassVar[int]
        UNIT_FIELD_NUMBER: _ClassVar[int]
        mean_sample_rate: float
        metadata: _containers.ScalarMap[str, str]
        stdev_sample_rate: float
        timestamp_statistics: RedvoxPacketM.SummaryStatistics
        timestamps: _containers.RepeatedScalarFieldContainer[float]
        unit: RedvoxPacketM.Unit
        def __init__(self, unit: _Optional[_Union[RedvoxPacketM.Unit, str]] = ..., timestamps: _Optional[_Iterable[float]] = ..., timestamp_statistics: _Optional[_Union[RedvoxPacketM.SummaryStatistics, _Mapping]] = ..., mean_sample_rate: _Optional[float] = ..., stdev_sample_rate: _Optional[float] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
    API_FIELD_NUMBER: _ClassVar[int]
    BYTE: RedvoxPacketM.Unit
    CENTIMETERS: RedvoxPacketM.Unit
    DECIBEL: RedvoxPacketM.Unit
    DECIMAL_DEGREES: RedvoxPacketM.Unit
    DEGREES_CELSIUS: RedvoxPacketM.Unit
    EVENT_STREAMS_FIELD_NUMBER: _ClassVar[int]
    KILOPASCAL: RedvoxPacketM.Unit
    LSB_PLUS_MINUS_COUNTS: RedvoxPacketM.Unit
    LUX: RedvoxPacketM.Unit
    METADATA_FIELD_NUMBER: _ClassVar[int]
    METERS: RedvoxPacketM.Unit
    METERS_PER_SECOND: RedvoxPacketM.Unit
    METERS_PER_SECOND_SQUARED: RedvoxPacketM.Unit
    MICROAMPERES: RedvoxPacketM.Unit
    MICROSECONDS_SINCE_UNIX_EPOCH: RedvoxPacketM.Unit
    MICROTESLA: RedvoxPacketM.Unit
    NORMALIZED_COUNTS: RedvoxPacketM.Unit
    PCM: RedvoxPacketM.Unit
    PERCENTAGE: RedvoxPacketM.Unit
    RADIANS: RedvoxPacketM.Unit
    RADIANS_PER_SECOND: RedvoxPacketM.Unit
    SENSORS_FIELD_NUMBER: _ClassVar[int]
    STATION_INFORMATION_FIELD_NUMBER: _ClassVar[int]
    SUB_API_FIELD_NUMBER: _ClassVar[int]
    TIMING_INFORMATION_FIELD_NUMBER: _ClassVar[int]
    UNITLESS: RedvoxPacketM.Unit
    UNKNOWN: RedvoxPacketM.Unit
    api: float
    event_streams: _containers.RepeatedCompositeFieldContainer[RedvoxPacketM.EventStream]
    metadata: _containers.ScalarMap[str, str]
    sensors: RedvoxPacketM.Sensors
    station_information: RedvoxPacketM.StationInformation
    sub_api: float
    timing_information: RedvoxPacketM.TimingInformation
    def __init__(self, api: _Optional[float] = ..., sub_api: _Optional[float] = ..., station_information: _Optional[_Union[RedvoxPacketM.StationInformation, _Mapping]] = ..., timing_information: _Optional[_Union[RedvoxPacketM.TimingInformation, _Mapping]] = ..., sensors: _Optional[_Union[RedvoxPacketM.Sensors, _Mapping]] = ..., event_streams: _Optional[_Iterable[_Union[RedvoxPacketM.EventStream, _Mapping]]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class SynchRequest(_message.Message):
    __slots__ = ["seq_id", "station_id", "station_uuid", "sub_seq_id"]
    SEQ_ID_FIELD_NUMBER: _ClassVar[int]
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    STATION_UUID_FIELD_NUMBER: _ClassVar[int]
    SUB_SEQ_ID_FIELD_NUMBER: _ClassVar[int]
    seq_id: int
    station_id: str
    station_uuid: str
    sub_seq_id: int
    def __init__(self, station_id: _Optional[str] = ..., station_uuid: _Optional[str] = ..., seq_id: _Optional[int] = ..., sub_seq_id: _Optional[int] = ...) -> None: ...

class SynchResponse(_message.Message):
    __slots__ = ["recv_ts_us", "send_ts_us", "seq_id", "station_id", "station_uuid", "sub_seq_id"]
    RECV_TS_US_FIELD_NUMBER: _ClassVar[int]
    SEND_TS_US_FIELD_NUMBER: _ClassVar[int]
    SEQ_ID_FIELD_NUMBER: _ClassVar[int]
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    STATION_UUID_FIELD_NUMBER: _ClassVar[int]
    SUB_SEQ_ID_FIELD_NUMBER: _ClassVar[int]
    recv_ts_us: int
    send_ts_us: int
    seq_id: int
    station_id: str
    station_uuid: str
    sub_seq_id: int
    def __init__(self, station_id: _Optional[str] = ..., station_uuid: _Optional[str] = ..., seq_id: _Optional[int] = ..., sub_seq_id: _Optional[int] = ..., recv_ts_us: _Optional[int] = ..., send_ts_us: _Optional[int] = ...) -> None: ...
