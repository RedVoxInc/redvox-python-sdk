"""
This module provides a wrapper for API M event streams which are used to record events derived from sensor data on stations.
"""

from redvox.api1000.common.common import TimingPayload
from redvox.api1000.common.generic import ProtoBase, ProtoRepeatedMessage
from redvox.api1000.common.mapping import Mapping
from redvox.api1000.common.typing import check_type
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM


class Event(ProtoBase[RedvoxPacketM.EventStream.Event]):
    """
    Represents a single Event
    """
    def __init__(self, proto: RedvoxPacketM.EventStream.Event):
        super().__init__(proto)
        self.__string_payload: Mapping[str] = Mapping(proto.string_payload, str)
        self.__numeric_payload: Mapping[float] = Mapping(proto.numeric_payload, float)
        self.__boolean_payload: Mapping[bool] = Mapping(proto.boolean_payload, bool)
        self.__byte_payload: Mapping[bytes] = Mapping(proto.byte_payload, bytes)

    def get_description(self) -> str:
        """
        :return: The event description.
        """
        return self._proto.description

    def set_description(self, description: str) -> 'Event':
        """
        Sets the event description.
        :param description: Description to set.
        :return: A modified instance of self
        """
        check_type(description, [str])
        self._proto.description = description
        return self

    def get_string_payload(self) -> Mapping[str]:
        """
        :return: The string event payload which maps string keys to string values.
        """
        return self.__string_payload

    def get_numeric_payload(self) -> Mapping[float]:
        """
        :return: The numeric event payload which maps string keys to numeric values.
        """
        return self.__numeric_payload

    def get_boolean_payload(self) -> Mapping[bool]:
        """
        :return: The boolean event payload which maps string keys to boolean values.
        """
        return self.__boolean_payload

    def get_byte_payload(self) -> Mapping[bytes]:
        """
        :return: The byte event payload which maps string keys to bytes values.
        """
        return self.__byte_payload


class EventStream(ProtoBase[RedvoxPacketM.EventStream]):
    """
    A collection of Events.
    """
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
        """
        :return: EventStream name.
        """
        return self._proto.name

    def set_name(self, name: str) -> 'EventStream':
        """
        Sets the name of this event stream.
        :param name: Name to set.
        :return: A modified instance of self.
        """
        check_type(name, [str])
        self._proto.name = name
        return self

    def get_timestamps(self) -> TimingPayload:
        """
        :return: Timestamps associated with each event.
        """
        return self.__timestamps

    def get_events(self) -> ProtoRepeatedMessage:
        """
        :return: List of Events.
        """
        return self.__events
