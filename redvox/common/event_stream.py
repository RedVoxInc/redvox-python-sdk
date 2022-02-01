from typing import List, Optional, Dict
from dataclasses import dataclass

import numpy as np
import pyarrow as pa
from dataclasses_json import dataclass_json

from redvox.api1000.wrapped_redvox_packet import event_streams as es


class EventStream:
    """
    stores event stream data gathered from a single station.
    ALL timestamps in microseconds since epoch UTC unless otherwise stated
    """
    def __init__(self, eventstream: es.EventStream):
        """
        initialize EventStream for a station

        :param eventstream: protobuf EventStream to convert
        """
        self.name = eventstream.get_name()
        self.timestamps_count = eventstream.get_timestamps().get_timestamps_count()
        self.timestamps_mean = eventstream.get_timestamps().get_timestamp_statistics().get_mean()
        self.timestamps_std = eventstream.get_timestamps().get_timestamp_statistics().get_standard_deviation()
        self.timestamps_min = eventstream.get_timestamps().get_timestamp_statistics().get_min()
        self.timestamps_max = eventstream.get_timestamps().get_timestamp_statistics().get_max()
        self.timestamps_range = eventstream.get_timestamps().get_timestamp_statistics().get_range()
        self.timestamps_metadata = eventstream.get_timestamps().get_metadata()
        self.mean_sample_rate_hz = eventstream.get_timestamps().get_mean_sample_rate()
        self.std_sample_rate_hz = eventstream.get_timestamps().get_stdev_sample_rate()
        self.metadata = eventstream.get_metadata()
        self._data = self.read_events(eventstream)

    @staticmethod
    def read_events(eventstream: es.EventStream) -> pa.Table:
        """
        :param eventstream: stream of events to process
        :return: events as a pyarrow table
        """
        tbl = {"timestamps": [], "unaltered_timestamps": []}
        first_event = eventstream.get_events().get_values()[0]
        for c, v in first_event.get_string_payload:
            tbl[c] = []
        for c, v in first_event.get_numeric_payload:
            tbl[c] = []
        for c, v in first_event.get_boolean_payload:
            tbl[c] = []
        for c, v in first_event.get_byte_payload:
            tbl[c] = []
        num_events = eventstream.get_events().get_count()
        for i in range(num_events):
            tbl["timestamps"].append(eventstream.get_timestamps().get_timestamps()[i])
            tbl["unaltered_timestamps"].append(eventstream.get_timestamps().get_timestamps()[i])
            evnt = eventstream.get_events().get_values()[i]
            for c, st in evnt.get_string_payload:
                tbl[c].append(st)
            for c, st in evnt.get_numeric_payload:
                tbl[c].append(st)
            for c, st in evnt.get_boolean_payload:
                tbl[c].append(st)
            for c, st in evnt.get_byte_payload:
                tbl[c].append(st)
            for c, st in evnt.get_metadata():
                tbl[c].append(st)
        return pa.Table.from_pydict(tbl)

    def data(self) -> pa.Table:
        """
        :return: the data as a pyarrow table
        """
        return self._data

    def set_data(self, eventstream: es.EventStream):
        """
        sets the data using the values from eventstream

        :param eventstream: the protobuf eventstream to read
        """
        self.read_events(eventstream)
        self.timestamps_count = eventstream.get_timestamps().get_timestamps_count()
        self.timestamps_mean = eventstream.get_timestamps().get_timestamp_statistics().get_mean()
        self.timestamps_std = eventstream.get_timestamps().get_timestamp_statistics().get_standard_deviation()
        self.timestamps_min = eventstream.get_timestamps().get_timestamp_statistics().get_min()
        self.timestamps_max = eventstream.get_timestamps().get_timestamp_statistics().get_max()
        self.timestamps_range = eventstream.get_timestamps().get_timestamp_statistics().get_range()
        self.mean_sample_rate_hz = eventstream.get_timestamps().get_mean_sample_rate()
        self.std_sample_rate_hz = eventstream.get_timestamps().get_stdev_sample_rate()


@dataclass_json()
@dataclass
class EventStreams:
    """
    stores multiple event streams per station
    ALL timestamps in microseconds since epoch UTC unless otherwise stated
    """
    streams: List[EventStream]
