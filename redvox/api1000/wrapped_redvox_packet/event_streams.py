"""
This module provides a wrapper for API M event streams which are used to record events derived from sensor data on
stations.
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

    def set_description(self, description: str) -> "Event":
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

    def set_string_payload(self, string_payload: Mapping[str]) -> "Event":
        """
        Sets the string payload.
        :param string_payload: Payload to set.
        :return: A modified instance of self.
        """
        check_type(string_payload, [Mapping])
        self.__string_payload.set_metadata(string_payload.get_metadata())
        return self

    def get_numeric_payload(self) -> Mapping[float]:
        """
        :return: The numeric event payload which maps string keys to numeric values.
        """
        return self.__numeric_payload

    def set_numeric_payload(self, numeric_payload: Mapping[float]) -> "Event":
        """
        Sets the numeric payload.
        :param numeric_payload: Payload to set.
        :return: A modified instance of self.
        """
        check_type(numeric_payload, [Mapping])
        self.__numeric_payload.set_metadata(numeric_payload.get_metadata())
        return self

    def get_boolean_payload(self) -> Mapping[bool]:
        """
        :return: The boolean event payload which maps string keys to boolean values.
        """
        return self.__boolean_payload

    def set_boolean_payload(self, boolean_payload: Mapping[bool]) -> "Event":
        """
        Sets the boolean payload.
        :param boolean_payload: Payload to set.
        :return: A modified instance of self.
        """
        check_type(boolean_payload, [Mapping])
        self.__boolean_payload.set_metadata(boolean_payload.get_metadata())
        return self

    def get_byte_payload(self) -> Mapping[bytes]:
        """
        :return: The byte event payload which maps string keys to bytes values.
        """
        return self.__byte_payload

    def set_byte_payload(self, byte_payload: Mapping[bytes]) -> "Event":
        """
        Sets the byte payload.
        :param byte_payload: Payload to set.
        :return: A modified instance of self.
        """
        check_type(byte_payload, [Mapping])
        self.__byte_payload.set_metadata(byte_payload.get_metadata())
        return self


class EventStream(ProtoBase[RedvoxPacketM.EventStream]):
    """
    A collection of Events.
    """

    def __init__(self, proto: RedvoxPacketM.EventStream):
        super().__init__(proto)
        self.__timestamps: TimingPayload = TimingPayload(proto.timestamps)
        self.__events: ProtoRepeatedMessage = ProtoRepeatedMessage(
            proto, proto.events, "events", Event, lambda event: event.get_proto()
        )

    def get_name(self) -> str:
        """
        :return: EventStream name.
        """
        return self._proto.name

    def set_name(self, name: str) -> "EventStream":
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

    def set_timestamps(self, timestamps: TimingPayload) -> "EventStream":
        """
        Sets the timing payload.
        :param timestamps: Timing payload to set.
        :return: A modified instance of self.
        """
        check_type(timestamps, [TimingPayload])
        self.get_proto().timestamps.CopyFrom(timestamps.get_proto())
        self.__timestamps = TimingPayload(self.get_proto().timestamps)
        return self

    def get_events(self) -> ProtoRepeatedMessage:
        """
        :return: List of Events.
        """
        return self.__events

    def set_events(self, events: ProtoRepeatedMessage) -> "EventStream":
        """
        Sets the Events from the provided ProtoRepeatedMessage.
        :param events: Events encoded in a ProtoRepeatedMessage.
        :return: A modified instance of self.
        """
        self.__events.clear_values()
        self.__events.append_values(events.get_values())
        return self
