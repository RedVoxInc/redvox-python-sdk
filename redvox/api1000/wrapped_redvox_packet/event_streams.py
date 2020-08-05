from redvox.api1000.common.common import TimingPayload
from redvox.api1000.common.generic import ProtoBase, ProtoRepeatedMessage
from redvox.api1000.common.mapping import Mapping
from redvox.api1000.common.typing import check_type
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM


class Event(ProtoBase[RedvoxPacketM.EventStream.Event]):
    def __init__(self, proto: RedvoxPacketM.EventStream.Event):
        super().__init__(proto)
        self.__string_payload: Mapping[str] = Mapping(proto.string_payload, str)
        self.__numeric_payload: Mapping[float] = Mapping(proto.numeric_payload, float)
        self.__boolean_payload: Mapping[bool] = Mapping(proto.boolean_payload, bool)
        self.__byte_payload: Mapping[bytes] = Mapping(proto.byte_payload, bytes)

    def get_description(self) -> str:
        return self._proto.description

    def set_description(self, description: str) -> 'Event':
        check_type(description, [str])
        self._proto.description = description
        return self

    def get_string_payload(self) -> Mapping[str]:
        return self.__string_payload

    def get_numeric_payload(self) -> Mapping[float]:
        return self.__numeric_payload

    def get_boolean_payload(self) -> Mapping[bool]:
        return self.__boolean_payload

    def get_byte_payload(self) -> Mapping[bytes]:
        return self.__byte_payload


class EventStream(ProtoBase[RedvoxPacketM.EventStream]):
    def __init__(self, proto: RedvoxPacketM.EventStream):
        super().__init__(proto)
        self.__timestamps: TimingPayload = TimingPayload(proto.timestamps)
        self.__events: ProtoRepeatedMessage = ProtoRepeatedMessage(
            proto,
            proto.events,
            "events",
            lambda event_proto: Event(event_proto),
            lambda event: event.get_proto()
        )

    def get_name(self) -> str:
        return self._proto.name

    def set_name(self, name: str) -> 'EventStream':
        check_type(name, [str])
        self._proto.name = name
        return self

    def get_timestamps(self) -> TimingPayload:
        return self.__timestamps

    def get_events(self) -> ProtoRepeatedMessage:
        return self.__events
