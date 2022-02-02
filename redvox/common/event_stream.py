from typing import List, Optional
from dataclasses import dataclass, field

import numpy as np
import pyarrow as pa
from dataclasses_json import dataclass_json

from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.api1000.wrapped_redvox_packet import event_streams as es
from redvox.common.errors import RedVoxExceptions


class EventStream:
    """
    stores event stream data gathered from a single station.
    ALL timestamps in microseconds since epoch UTC unless otherwise stated
    """
    def __init__(self, name: str):
        """
        initialize EventStream for a station

        :param name: name of the EventStream
        """
        self.name = name
        self.timestamps_metadata = {}
        self.metadata = {}
        self._errors = RedVoxExceptions("EventStream")
        self._string_data = pa.Table.from_pydict({})
        self._numeric_data = pa.Table.from_pydict({})
        self._boolean_data = pa.Table.from_pydict({})
        self._byte_data = pa.Table.from_pydict({})

    def read_events(self, eventstream: es.EventStream):
        """
        read the payloads of each event in the eventstream and separate the data by payload type

        :param eventstream: stream of events to process
        """
        self.name = eventstream.get_name()
        self.timestamps_metadata = eventstream.get_timestamps().get_metadata()
        self.metadata = eventstream.get_metadata()
        tbl = {"timestamps": [], "unaltered_timestamps": []}
        str_tbl = {}
        num_tbl = {}
        bool_tbl = {}
        byte_tbl = {}
        num_events = eventstream.get_events().get_count()
        if num_events > 1:
            first_event = eventstream.get_events().get_values()[0]
            for c, v in first_event.get_string_payload().get_metadata().items():
                str_tbl[c] = []
            for c, v in first_event.get_numeric_payload().get_metadata().items():
                num_tbl[c] = []
            for c, v in first_event.get_boolean_payload().get_metadata().items():
                bool_tbl[c] = []
            for c, v in first_event.get_byte_payload().get_metadata().items():
                byte_tbl[c] = []
            for i in range(num_events):
                tbl["timestamps"].append(eventstream.get_timestamps().get_timestamps()[i])
                tbl["unaltered_timestamps"].append(eventstream.get_timestamps().get_timestamps()[i])
                evnt = eventstream.get_events().get_values()[i]
                for c, st in evnt.get_string_payload().get_metadata().items():
                    str_tbl[c].append(st)
                for c, st in evnt.get_numeric_payload().get_metadata().items():
                    num_tbl[c].append(st)
                for c, st in evnt.get_boolean_payload().get_metadata().items():
                    bool_tbl[c].append(st)
                for c, st in evnt.get_byte_payload().get_metadata().items():
                    byte_tbl[c].append(st)
            if len(str_tbl) > 0:
                self._string_data = pa.Table.from_pydict({**tbl, **str_tbl})
            if len(num_tbl) > 0:
                self._numeric_data = pa.Table.from_pydict({**tbl, **num_tbl})
            if len(bool_tbl) > 0:
                self._boolean_data = pa.Table.from_pydict({**tbl, **bool_tbl})
            if len(byte_tbl) > 0:
                self._byte_data = pa.Table.from_pydict({**tbl, **byte_tbl})

    @staticmethod
    def read_raw(stream: RedvoxPacketM.EventStream) -> 'EventStream':
        """
        read the contents of a protobuf stream

        :param stream: the protobuf stream to read
        """
        tbl = {"timestamps": [], "unaltered_timestamps": []}
        str_tbl = {}
        num_tbl = {}
        bool_tbl = {}
        byte_tbl = {}
        num_events = len(stream.events)
        if num_events > 1:
            result = EventStream(stream.name)
            result.timestamps_metadata = stream.timestamps.metadata
            result.metadata = stream.metadata
            first_event = stream.events[0]
            for c in first_event.string_payload.keys():
                str_tbl[c] = []
            for c in first_event.numeric_payload.keys():
                num_tbl[c] = []
            for c in first_event.boolean_payload.keys():
                bool_tbl[c] = []
            for c in first_event.byte_payload.keys():
                byte_tbl[c] = []
            for i in range(num_events):
                tbl["timestamps"].append(stream.timestamps.timestamps[i])
                tbl["unaltered_timestamps"].append(stream.timestamps.timestamps[i])
                evnt = stream.events[i]
                for c, st in evnt.string_payload.items():
                    str_tbl[c].append(st)
                for c, st in evnt.numeric_payload.items():
                    num_tbl[c].append(st)
                for c, st in evnt.boolean_payload.items():
                    bool_tbl[c].append(st)
                for c, st in evnt.byte_payload.items():
                    byte_tbl[c].append(st)
            if len(str_tbl) > 0:
                result._string_data = pa.Table.from_pydict({**tbl, **str_tbl})
            if len(num_tbl) > 0:
                result._numeric_data = pa.Table.from_pydict({**tbl, **num_tbl})
            if len(bool_tbl) > 0:
                result._boolean_data = pa.Table.from_pydict({**tbl, **bool_tbl})
            if len(byte_tbl) > 0:
                result._byte_data = pa.Table.from_pydict({**tbl, **byte_tbl})
            return result
        return EventStream("Empty")

    def string_data(self) -> Optional[pa.Table]:
        """
        :return: the string data as a pyarrow table or None if there is no data
        """
        return self._string_data

    def numeric_data(self) -> Optional[pa.Table]:
        """
        :return: the numeric data as a pyarrow table or None if there is no data
        """
        return self._numeric_data

    def boolean_data(self) -> Optional[pa.Table]:
        """
        :return: the boolean data as a pyarrow table or None if there is no data
        """
        return self._boolean_data

    def byte_data(self) -> Optional[pa.Table]:
        """
        :return: the byte data as a pyarrow table or None if there is no data
        """
        return self._byte_data

    def get_string_channel(self, channel_name: str) -> List[str]:
        """
        :param channel_name: name of string payload to retrieve
        :return: string data from the channel specified
        """
        _arrow = self._string_data
        if channel_name not in _arrow.schema.names:
            self._errors.append(f"WARNING: {channel_name} does not exist; try one of {_arrow.schema.names}")
            return []
        return [c for c in _arrow[channel_name]]

    def get_numeric_channel(self, channel_name: str) -> np.array:
        """
        :param channel_name: name of numeric payload to retrieve
        :return: numeric data from the channel specified
        """
        _arrow = self._numeric_data
        if channel_name not in _arrow.schema.names:
            self._errors.append(f"WARNING: {channel_name} does not exist; try one of {_arrow.schema.names}")
            return []
        return _arrow[channel_name].to_numpy()

    def get_boolean_channel(self, channel_name: str) -> List[bool]:
        """
        :param channel_name: name of boolean payload to retrieve
        :return: boolean data from the channel specified
        """
        _arrow = self._boolean_data
        if channel_name not in _arrow.schema.names:
            self._errors.append(f"WARNING: {channel_name} does not exist; try one of {_arrow.schema.names}")
            return []
        return [c for c in _arrow[channel_name]]

    def get_byte_channel(self, channel_name: str) -> List[bytes]:
        """
        :param channel_name: name of byte payload to retrieve
        :return: bytes data from the channel specified
        """
        _arrow = self._byte_data
        if channel_name not in _arrow.schema.names:
            self._errors.append(f"WARNING: {channel_name} does not exist; try one of {_arrow.schema.names}")
            return []
        return [c for c in _arrow[channel_name]]

    def set_data(self, eventstream: es.EventStream):
        """
        sets the data using the values from eventstream

        :param eventstream: the protobuf eventstream to read
        """
        self.read_events(eventstream)

    def add(self, other_stream: es.EventStream):
        """
        adds an event stream with the same name to the data

        :param other_stream: another event stream with the same name
        """
        if self.name != other_stream.get_name():
            self._errors.append(f"Attempted to add a stream with a different name ({other_stream.get_name()})")
        else:
            self.timestamps_metadata = {**self.timestamps_metadata, **other_stream.get_timestamps().get_metadata()}
            self.metadata = {**self.metadata, **other_stream.get_metadata()}
            num_events = other_stream.get_events().get_count()
            if num_events > 0:
                tbl = {"timestamps": [], "unaltered_timestamps": []}
                str_tbl = {f: [] for f in self._string_data.schema.names}
                num_tbl = {f: [] for f in self._numeric_data.schema.names}
                bool_tbl = {f: [] for f in self._boolean_data.schema.names}
                byte_tbl = {f: [] for f in self._byte_data.schema.names}
                for i in range(num_events):
                    tbl["timestamps"].append(other_stream.get_timestamps().get_timestamps()[i])
                    tbl["unaltered_timestamps"].append(other_stream.get_timestamps().get_timestamps()[i])
                    evnt = other_stream.get_events().get_values()[i]
                    for c, st in evnt.get_string_payload().get_metadata().items():
                        str_tbl[c].append(st)
                    for c, st in evnt.get_numeric_payload().get_metadata().items():
                        num_tbl[c].append(st)
                    for c, st in evnt.get_boolean_payload().get_metadata().items():
                        bool_tbl[c].append(st)
                    for c, st in evnt.get_byte_payload().get_metadata().items():
                        byte_tbl[c].append(st)
                if len(str_tbl) > 0:
                    self._string_data = pa.concat_tables((self._string_data, pa.Table.from_pydict({**str_tbl, **tbl})))
                if len(num_tbl) > 0:
                    self._numeric_data = pa.concat_tables((self._numeric_data,
                                                           pa.Table.from_pydict({**num_tbl, **tbl})))
                if len(bool_tbl) > 0:
                    self._boolean_data = pa.concat_tables((self._boolean_data,
                                                           pa.Table.from_pydict({**bool_tbl, **tbl})))
                if len(byte_tbl) > 0:
                    self._byte_data = pa.concat_tables((self._byte_data, pa.Table.from_pydict({**byte_tbl, **tbl})))

    def add_raw(self, other_stream: RedvoxPacketM.EventStream):
        """
        add a protobuf EventStream with the same name to the data

        :param other_stream: a protobuf EventStream to add
        """
        if self.name != other_stream.name:
            self._errors.append(f"Attempted to add a stream with a different name ({other_stream.name})")
        else:
            self.timestamps_metadata = {**self.timestamps_metadata, **other_stream.timestamps.metadata}
            self.metadata = {**self.metadata, **other_stream.metadata}
            num_events = len(other_stream.events)
            if num_events > 0:
                tbl = {"timestamps": [], "unaltered_timestamps": []}
                str_tbl = {f: [] for f in self._string_data.schema.names}
                num_tbl = {f: [] for f in self._numeric_data.schema.names}
                bool_tbl = {f: [] for f in self._boolean_data.schema.names}
                byte_tbl = {f: [] for f in self._byte_data.schema.names}
                for i in range(num_events):
                    tbl["timestamps"].append(other_stream.timestamps.timestamps[i])
                    tbl["unaltered_timestamps"].append(other_stream.timestamps.timestamps[i])
                    evnt = other_stream.events[i]
                    for c, st in evnt.string_payload.items():
                        str_tbl[c].append(st)
                    for c, st in evnt.numeric_payload.items():
                        num_tbl[c].append(st)
                    for c, st in evnt.boolean_payload.items():
                        bool_tbl[c].append(st)
                    for c, st in evnt.byte_payload.items():
                        byte_tbl[c].append(st)
                if len(str_tbl) > 0:
                    self._string_data = pa.concat_tables((self._string_data, pa.Table.from_pydict({**str_tbl, **tbl})))
                if len(num_tbl) > 0:
                    self._numeric_data = pa.concat_tables((self._numeric_data,
                                                           pa.Table.from_pydict({**num_tbl, **tbl})))
                if len(bool_tbl) > 0:
                    self._boolean_data = pa.concat_tables((self._boolean_data,
                                                           pa.Table.from_pydict({**bool_tbl, **tbl})))
                if len(byte_tbl) > 0:
                    self._byte_data = pa.concat_tables((self._byte_data, pa.Table.from_pydict({**byte_tbl, **tbl})))

    def errors(self) -> RedVoxExceptions:
        """
        :return: errors of the sensor
        """
        return self._errors

    def print_errors(self):
        """
        print all errors to screen
        """
        self._errors.print()


@dataclass_json()
@dataclass
class EventStreams:
    """
    stores multiple event streams per station
    ALL timestamps in microseconds since epoch UTC unless otherwise stated
    """
    streams: List[EventStream] = field(default_factory=lambda: [])
    debug: bool = False

    def read_from_packets(self, packet: RedvoxPacketM):
        """
        read the eventstream payload from a single Redvox Api1000 packet

        :param packet: packet to read data from
        """
        for st in packet.event_streams:
            if st.name in self.get_stream_names():
                self.get_stream(st.name).add_raw(st)
            else:
                self.streams.append(EventStream.read_raw(st))

    def get_stream(self, stream_name: str) -> Optional[EventStream]:
        """
        :param stream_name: name of event stream to get
        :return: the EventStream that has the name specified or None if it doesn't exist
        """
        for s in self.streams:
            if s.name == stream_name:
                return s
        if self.debug:
            print(f"{stream_name} does not exist in streams.  Use one of {[self.get_stream_names()]}")
        return None

    def get_stream_names(self) -> List[str]:
        """
        :return: names of all streams
        """
        return [s.name for s in self.streams]
