"""
This module provides classes to organize events recorded on a station.
It will ignore machine learning events.
"""
from typing import List, Optional, Dict, Union
from dataclasses import dataclass, field
from pathlib import Path
import enum
import os
import re

import numpy as np
from dataclasses_json import dataclass_json

from redvox.api1000.common.mapping import Mapping
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.api1000.wrapped_redvox_packet import event_streams as es
from redvox.api1000.wrapped_redvox_packet import ml
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.common.errors import RedVoxExceptions
from redvox.common import offset_model as om
from redvox.common.io import FileSystemWriter as Fsw, FileSystemSaveMode, json_file_to_dict
import redvox.common.event_stream_io as io


class EventDataTypes(enum.Enum):
    """
    Enumeration of data types for event data
    """

    STRING = 0  # string data
    NUMERIC = 1  # numeric data
    BOOLEAN = 2  # boolean data
    BYTE = 3  # bytes data

    @staticmethod
    def types_list() -> List["EventDataTypes"]:
        """
        :return: the values of EventDataTypes as a list in order of: STRING, NUMERIC, BOOLEAN, BYTE
        """
        return [EventDataTypes.STRING, EventDataTypes.NUMERIC, EventDataTypes.BOOLEAN, EventDataTypes.BYTE]


def get_empty_event_data_dict() -> dict:
    """
    :return: an empty data dictionary for event data
    """
    return {EventDataTypes.STRING: {}, EventDataTypes.NUMERIC: {}, EventDataTypes.BOOLEAN: {}, EventDataTypes.BYTE: {}}


class Event:
    """
    stores event data from Redvox Api1000 packets

    ALL timestamps in microseconds since epoch UTC unless otherwise stated
    """

    def __init__(
        self,
        timestamp: float,
        name: str = "event",
        data: Optional[Dict[EventDataTypes, dict]] = None,
        save_mode: FileSystemSaveMode = FileSystemSaveMode.MEM,
        base_dir: str = ".",
    ):
        """
        initialize Event

        :param timestamp: timestamp when Event occurred in microseconds since epoch UTC
        :param name: name of the Event.  Default "event"
        :param data: a structured dictionary of the data.  Dictionary must look like:
                    {EventDataTypes.STRING: {s_values}, EventDataTypes.NUMERIC: {n_values},
                    EventDataTypes.BOOLEAN: {o_values}, EventDataTypes.BYTE: {b_values}}
                    where {*_values} is a dictionary of string: data and can be empty.  Default None
        :param save_mode: FileSystemSaveMode that determines how data is saved.
                            Default FileSystemSaveMode.MEM (use RAM).  Other options are DISK (save to directory)
                            and TEMP (save to temporary directory)
        :param base_dir: the location of the parquet file that holds the data.  Not used if save_data is False.
                            Default current directory (".")
        """
        self.name = name
        self.metadata = {}
        self._errors = RedVoxExceptions("Event")
        self._fs_writer = Fsw(f"event_{name}", "json", base_dir, save_mode)
        self._timestamp = timestamp
        self._uncorrected_timestamp = timestamp
        self._data = get_empty_event_data_dict() if data is None else data

    def __repr__(self):
        return (
            f"name: {self.name}, "
            f"timestamp: {self._timestamp}, "
            f"uncorrected_timestamp: {self._uncorrected_timestamp}, "
            f"schema: {self.get_schema()}, "
            f"save_mode: {self._fs_writer.save_mode()}"
        )

    def __str__(self):
        return (
            f"name: {self.name}, "
            f"timestamp: {self._timestamp}, "
            f"uncorrected_timestamp: {self._uncorrected_timestamp}, "
            f"schema: {self.__schema_as_str()}"
        )

    def as_dict(self) -> dict:
        """
        :return: EventStream as a dictionary
        """
        return {
            "name": self.name,
            "timestamp": self._timestamp,
            "uncorrected_timestamp": self._uncorrected_timestamp,
            "metadata": self.metadata,
            "data": self.__data_as_dict(),
            "errors": self._errors.as_dict(),
        }

    def __data_as_dict(self) -> dict:
        return {
            EventDataTypes.STRING.name: self.get_string_values(),
            EventDataTypes.NUMERIC.name: self.get_numeric_values(),
            EventDataTypes.BOOLEAN.name: self.get_boolean_values(),
            EventDataTypes.BYTE.name: self.get_byte_values(),
        }

    def __schema_as_str(self) -> str:
        result = ""
        for f in self._data.keys():
            result += f"{f.name}: {list(self._data[f].keys())}"
            if f != EventDataTypes.BYTE:
                result += ", "
        return result

    @staticmethod
    def __get_items(payload: Mapping[str]):
        return payload.get_metadata().items()

    @staticmethod
    def __get_items_raw(payload):
        return payload.items()

    @staticmethod
    def __get_keys(ptype: str, payload: Mapping[str]):
        return ptype, payload.get_metadata().keys()

    @staticmethod
    def __get_keys_raw(ptype: str, payload):
        return ptype, payload.keys()

    @staticmethod
    def __get_data_from_event(event: es.Event):
        """
        load data from an Event;
        gets data in order of: string, numeric, boolean, byte

        :param event: event to load data from
        """
        return map(
            Event.__get_items,
            [
                event.get_string_payload(),
                event.get_numeric_payload(),
                event.get_boolean_payload(),
                event.get_byte_payload(),
            ],
        )

    @staticmethod
    def __get_data_from_event_raw(event: RedvoxPacketM.EventStream.Event):
        """
        load data from an Event;
        gets data in order of: string, numeric, boolean, byte

        :param event: event to load data from
        """
        return map(
            Event.__get_items_raw,
            [event.string_payload, event.numeric_payload, event.boolean_payload, event.byte_payload],
        )

    def _set_data(self, data: iter):
        """
        sets the data of the Event

        :param data: an iterable of data to insert
        """
        for g, h in map(lambda l, p: (l, p), data, EventDataTypes.types_list()):
            for k, v in g:
                self._data[h][k] = v

    def read_event(self, event: es.Event) -> "Event":
        """
        read the payloads of a Redvox Event, separate the data by payload type, then add it to the SDK Event

        :param event: event to process
        :return: updated self
        """
        self.name = event.get_description()
        self._fs_writer.file_name = f"event_{self.name}"
        self.metadata = event.get_metadata()
        self._set_data(self.__get_data_from_event(event))
        return self

    def read_raw(self, event: RedvoxPacketM.EventStream.Event) -> "Event":
        """
        read the contents of a Redvox Api1000 protobuf stream

        :param event: the protobuf stream to read
        """
        self.name = event.description
        self._fs_writer.file_name = f"event_{self.name}"
        self.metadata = dict(event.metadata)
        self._set_data(self.__get_data_from_event_raw(event))
        return self

    def get_string_schema(self) -> List[str]:
        """
        :return: the column names of string typed data as a list of strings
        """
        return self.get_schema()[EventDataTypes.STRING]

    def get_numeric_schema(self) -> List[str]:
        """
        :return: the column names of numeric typed data as a list of strings
        """
        return self.get_schema()[EventDataTypes.NUMERIC]

    def get_boolean_schema(self) -> List[str]:
        """
        :return: the column names of boolean typed data as a list of strings
        """
        return self.get_schema()[EventDataTypes.BOOLEAN]

    def get_byte_schema(self) -> List[str]:
        """
        :return: the column names of byte typed data as a list of strings
        """
        return self.get_schema()[EventDataTypes.BYTE]

    def get_schema(self) -> Dict[EventDataTypes, list]:
        """
        :return: the dictionary that summarizes the data names and types
        """
        result = {}
        for f in self._data.keys():
            result[f] = [k for k in self._data[f].keys()]
        return result

    def get_data_keys(self) -> List[str]:
        """
        :return: the keys of the data in the event
        """
        result = []
        for f in self._data.keys():
            result.extend([k for k in self._data[f].keys()])
        return result

    def get_string_values(self) -> dict:
        """
        :return: the string data as a dictionary
        """
        return self._data[EventDataTypes.STRING]

    def get_numeric_values(self) -> dict:
        """
        :return: the numeric data as a dictionary
        """
        return self._data[EventDataTypes.NUMERIC]

    def get_boolean_values(self) -> dict:
        """
        :return: the boolean data as a dictionary
        """
        return self._data[EventDataTypes.BOOLEAN]

    def get_byte_values(self) -> dict:
        """
        :return: the byte data as a dictionary
        """
        return self._data[EventDataTypes.BYTE]

    def get_string_item(self, data_key: str) -> Optional[str]:
        """
        get a string data value with a key matching data_key

        :param data_key: the name of the data value to look for
        :return: string data if it exists, None otherwise
        """
        strs = self.get_string_values()
        for s in strs.keys():
            if s == data_key:
                return strs[s]
        return None

    def get_numeric_item(self, data_key: str) -> Optional[float]:
        """
        get a numeric data value with a key matching data_key

        :param data_key: the name of the data value to look for
        :return: numeric data if it exists, None otherwise
        """
        nums = self.get_numeric_values()
        for s in nums.keys():
            if s == data_key:
                return nums[s]
        return None

    def get_boolean_item(self, data_key: str) -> Optional[bool]:
        """
        get a boolean data value with a key matching data_key

        :param data_key: the name of the data value to look for
        :return: boolean data if it exists, None otherwise
        """
        boos = self.get_boolean_values()
        for s in boos.keys():
            if s == data_key:
                return boos[s]
        return None

    def get_byte_item(self, data_key: str) -> Optional[str]:
        """
        get a byte data value with a key matching data_key

        :param data_key: the name of the data value to look for
        :return: byte data if it exists, None otherwise
        """
        byts = self.get_byte_values()
        for s in byts.keys():
            if s == data_key:
                return byts[s]
        return None

    def get_item(self, data_key: str) -> Union[List[str], str, bool, float]:
        """
        :param data_key: key of data to get
        :return: data with matching data_key or the list of all possible data keys
        """
        for r in [
            self.get_string_item(data_key),
            self.get_numeric_item(data_key),
            self.get_boolean_item(data_key),
            self.get_byte_item(data_key),
        ]:
            if r is not None:
                return r
        return self.get_data_keys()

    def get_classification(self, index: int = 0) -> dict:
        """
        get a classification from an event (anything that ends with "_X" where X is the index value)

        :param index: index of classification, default 0
        :return: dictionary of data
        """
        result = {}
        for s in self._data.keys():
            for b, v in self._data[s].items():
                match = re.search(f"_{index}$", b)
                if match is not None:
                    result[b] = v
        return result

    def get_string_column(self, column_name: str) -> Dict[str, str]:
        """
        note: data points in events are named [column_name]_[X], where [X] is an integer 0 or greater.
        this function will return all string data points with keys that start with [column_name]

        :param column_name: the name of the column of event data to get
        :return: a dictionary of string data
        """
        result = {}
        strs = self.get_string_values()
        for s, v in strs.items():
            match = re.match(f"{column_name}_*", s)
            if match is not None:
                result[s] = v
        return result

    def get_numeric_column(self, column_name: str) -> Dict[str, float]:
        """
        note: data points in events are named [column_name]_[X], where [X] is an integer 0 or greater.
        this function will return all numeric data points with keys that start with [column_name]

        :param column_name: the name of the column of event data to get
        :return: a dictionary of numeric data
        """
        result = {}
        strs = self.get_numeric_values()
        for s, v in strs.items():
            match = re.match(f"{column_name}_*", s)
            if match is not None:
                result[s] = v
        return result

    def get_boolean_column(self, column_name: str) -> Dict[str, str]:
        """
        note: data points in events are named [column_name]_[X], where [X] is an integer 0 or greater.
        this function will return all boolean data points with keys that start with [column_name]

        :param column_name: the name of the column of event data to get
        :return: a dictionary of boolean data
        """
        result = {}
        strs = self.get_boolean_values()
        for s, v in strs.items():
            match = re.match(f"{column_name}_*", s)
            if match is not None:
                result[s] = v
        return result

    def get_byte_column(self, column_name: str) -> Dict[str, str]:
        """
        note: data points in events are named [column_name]_[X], where [X] is an integer 0 or greater.
        this function will return all byte data points with keys that start with [column_name]

        :param column_name: the name of the column of event data to get
        :return: a dictionary of byte data
        """
        result = {}
        strs = self.get_byte_values()
        for s, v in strs.items():
            match = re.match(f"{column_name}_*", s)
            if match is not None:
                result[s] = v
        return result

    def get_timestamp(self) -> float:
        """
        :return: timestamp of the Event
        """
        return self._timestamp

    def get_uncorrected_timestamp(self) -> float:
        """
        :return: uncorrected timestamp of the Event
        """
        return self._uncorrected_timestamp

    def is_timestamp_corrected(self) -> bool:
        """
        :return: if timestamp of Event is updated
        """
        return self._timestamp != self._uncorrected_timestamp

    def update_timestamps(self, offset_model: om.OffsetModel, use_model_function: bool = False):
        """
        updates the timestamp of the Event

        :param offset_model: model used to update the timestamps
        :param use_model_function: if True, use the model's slope function to update the timestamps.
                                    otherwise uses the best offset (model's intercept value).  Default False
        """
        if self.is_timestamp_corrected():
            self._errors.append("Timestamps already corrected!")
        else:
            self._timestamp = offset_model.update_time(self._timestamp, use_model_function)

    def original_timestamps(self, offset_model: om.OffsetModel, use_model_function: bool = False):
        """
        undo the update to the timestamp of the Event

        :param offset_model: model used to update the timestamps
        :param use_model_function: if True, use the model's slope function to update the timestamps.
                                    otherwise uses the best offset (model's intercept value).  Default False
        """
        if not self.is_timestamp_corrected():
            self._errors.append("Timestamps already not corrected!")
        else:
            self._timestamp = offset_model.get_original_time(self._timestamp, use_model_function)

    def default_json_file_name(self) -> str:
        """
        :return: default event json file name (event_[event.name]): note there is no extension
        """
        return f"event_{self.name}"

    def is_save_to_disk(self) -> bool:
        """
        :return: True if sensor will be saved to disk
        """
        return self._fs_writer.is_save_disk()

    def set_save_to_disk(self, save: bool):
        """
        :param save: If True, save to disk
        """
        self._fs_writer.save_to_disk = save

    def set_save_mode(self, save_mode: FileSystemSaveMode):
        """
        set the save mode

        :param save_mode: new save mode
        """
        self._fs_writer.set_save_mode(save_mode)

    def save_mode(self) -> FileSystemSaveMode:
        """
        :return: the save mode
        """
        return self._fs_writer.save_mode()

    def set_file_name(self, new_file: Optional[str] = None):
        """
        * set the pyarrow file name or use the default: event_{Event.name}
        * Do not give an extension

        :param new_file: optional file name to change to; default None (use default name)
        """
        self._fs_writer.file_name = new_file if new_file else f"event_{self.name}"

    def full_file_name(self) -> str:
        """
        :return: full name of file containing the data
        """
        return self._fs_writer.full_name()

    def file_name(self) -> str:
        """
        :return: file name without extension
        """
        return self._fs_writer.file_name

    def set_save_dir(self, new_dir: Optional[str] = None):
        """
        set the pyarrow directory or use the default: "." (current directory)

        :param new_dir: the directory to change to; default None (use current directory)
        """
        self._fs_writer.base_dir = new_dir if new_dir else "."

    def save_dir(self) -> str:
        """
        :return: directory containing parquet files for the sensor
        """
        return self._fs_writer.save_dir()

    def full_path(self) -> str:
        """
        :return: the full path to the data file
        """
        return self._fs_writer.full_path()

    def fs_writer(self) -> Fsw:
        """
        :return: FileSystemWriter object
        """
        return self._fs_writer

    def has_data(self) -> bool:
        """
        :return: True if Event contains at least one data point
        """
        return sum([len(self._data[j].keys()) for j in EventDataTypes.types_list()]) > 0

    def data(self) -> dict:
        """
        :return: the data
        """
        return self._data

    @staticmethod
    def from_json_dict(json_dict: dict) -> "Event":
        """
        :param json_dict: json dictionary to parse
        :return: Event from json dict
        """
        if "timestamp" in json_dict.keys():
            data = get_empty_event_data_dict()
            data[EventDataTypes.STRING] = json_dict["data"]["STRING"]
            data[EventDataTypes.NUMERIC] = json_dict["data"]["NUMERIC"]
            data[EventDataTypes.BOOLEAN] = json_dict["data"]["BOOLEAN"]
            data[EventDataTypes.BYTE] = json_dict["data"]["BYTE"]
            result = Event(json_dict["timestamp"], json_dict["name"], data, FileSystemSaveMode.DISK)
            result.metadata = json_dict["metadata"]
            result._uncorrected_timestamp = json_dict["uncorrected_timestamp"]
            result.set_errors(RedVoxExceptions.from_dict(json_dict["errors"]))
        else:
            result = Event(np.nan, "Empty")
            result.append_error(f"Loading from json dict failed; missing Event timestamp.")
        return result

    @staticmethod
    def from_json_file(file_dir: str, file_name: str) -> "Event":
        """
        :param file_dir: full path to containing directory for the file
        :param file_name: name of file to load data from
        :return: Event from json file
        """
        json_data = json_file_to_dict(os.path.join(file_dir, f"{file_name}"))
        if "timestamp" in json_data.keys():
            data = get_empty_event_data_dict()
            data[EventDataTypes.STRING] = json_data["data"]["STRING"]
            data[EventDataTypes.NUMERIC] = json_data["data"]["NUMERIC"]
            data[EventDataTypes.BOOLEAN] = json_data["data"]["BOOLEAN"]
            data[EventDataTypes.BYTE] = json_data["data"]["BYTE"]
            result = Event(json_data["timestamp"], json_data["name"], data, FileSystemSaveMode.DISK, file_dir)
            result.metadata = json_data["metadata"]
            result._uncorrected_timestamp = json_data["uncorrected_timestamp"]
            result.set_errors(RedVoxExceptions.from_dict(json_data["errors"]))
        else:
            result = Event(np.nan, "Empty")
            result.append_error(f"Loading from {file_name} failed; missing Event timestamp.")
        return result

    def to_json_file(self, file_name: Optional[str] = None) -> Path:
        """
        saves the EventStream as a json file

        :param file_name: the optional base file name.  Do not include a file extension.
                            If None, a default file name is created using this format:
                            event_[event.name].json
        :return: path to json file
        """
        return io.event_to_json_file(self, file_name)

    def errors(self) -> RedVoxExceptions:
        """
        :return: errors of the sensor
        """
        return self._errors

    def set_errors(self, errors: RedVoxExceptions):
        """
        sets the errors of the Sensor

        :param errors: errors to set
        """
        self._errors = errors

    def append_error(self, error: str):
        """
        add an error to the Sensor

        :param error: error to add
        """
        self._errors.append(error)

    def print_errors(self):
        """
        print all errors to screen
        """
        self._errors.print()


@dataclass_json
@dataclass
class EventStream:
    """
    stores multiple events.

    ALL timestamps in microseconds since epoch UTC unless otherwise stated

    Properties:
        name: string; name of the EventStream.  Default "stream"

        events: List[Event]; all events in the stream.  Default empty list

        input_sample_rate: int; audio sample rate.  Default 0

        samples_per_window: int; samples per window of the events.  Default 0

        samples_per_hop: int; samples per hop of the events.  Default 0

        model_version: string; version of the model.  Default "0.0"

        metadata: Dict[str, str]; metadata as dict of strings.  Default empty dict

        debug: boolean; if True, outputs additional information at runtime.  Default False.
    """

    name: str = "stream"
    events: List[Event] = field(default_factory=lambda: [])
    input_sample_rate: int = 0
    samples_per_window: int = 0
    samples_per_hop: int = 0
    model_version: str = "n/a"
    metadata: Dict[str, str] = field(default_factory=lambda: {})
    debug: bool = False

    def __repr__(self):
        return (
            f"name: {self.name}, "
            f"events: {[s.__repr__() for s in self.events]}, "
            f"input_sample_rate: {self.input_sample_rate}, "
            f"samples_per_window: {self.samples_per_window}, "
            f"samples_per_hop: {self.samples_per_hop}, "
            f"model_version: {self.model_version}"
        )

    def __str__(self):
        return (
            f"name: {self.name}, "
            f"events: {[s.__str__() for s in self.events]}, "
            f"input_sample_rate: {self.input_sample_rate}, "
            f"samples_per_window: {self.samples_per_window}, "
            f"samples_per_hop: {self.samples_per_hop}, "
            f"model_version: {self.model_version}"
        )

    def as_dict(self) -> dict:
        """
        :return: EventStream as a dictionary
        """
        return {
            "name": self.name,
            "events": [e.as_dict() for e in self.events],
            "input_sample_rate": self.input_sample_rate,
            "samples_per_window": self.samples_per_window,
            "samples_per_hop": self.samples_per_hop,
            "model_version": self.model_version,
            "metadata": self.metadata,
        }

    def has_data(self):
        """
        :return: if there is at least one event
        """
        return len(self.events) > 0

    def has_events(self) -> bool:
        """
        :return: True if there are one or more events in the stream
        """
        return len(self.events) > 0

    def get_event(self, index: int = 0) -> Optional[Event]:
        """
        :param index: index of event to get.  Use negative values to select from the end of the list.
                        Default 0 (first event)
        :return: Event at the index, or None if the event/index doesn't exist
        """
        if 0 > index:
            index += len(self.events)
        if 0 <= index < len(self.events):
            return self.events[index]
        return None

    def get_data_column(self, column_name: str) -> list:
        """
        return a list of data with key column_name from each of the events
        if column_name doesn't exist, gets a list of valid column_names

        :param column_name: key of data to get
        :return: list of data named column_name or the list of all possible column names
        """
        result = []
        column_list = set()
        for r in self.events:
            val = r.get_item(column_name)
            if type(val) != list:
                result.append(val)
            else:
                for v in val:
                    column_list.add(v)
        if len(result) > 0:
            return result
        return list(column_list)

    @staticmethod
    def from_eventstream(
        stream: RedvoxPacketM.EventStream, save_mode: FileSystemSaveMode = FileSystemSaveMode.MEM, base_dir: str = "."
    ) -> "EventStream":
        """
        convert a Redvox Api1000 Packet EventStream into its sdk version

        :param stream: Redvox Api1000 Packet EventStream to read data from
        :param save_mode: FileSystemSaveMode that determines how Event data is saved.
                            Default FileSystemSaveMode.MEM (use RAM).  Other options are DISK (save to directory)
                            and TEMP (save to temporary directory)
        :param base_dir: the location of the parquet file that holds the Event data.  Not used if save_data is False.
                            Default current directory (".")
        :return: EventStream (sdk version)
        """
        result = EventStream(stream.name, metadata=dict(stream.metadata))
        if "input_sample_rate" in stream.metadata.keys():
            result.input_sample_rate = int(stream.metadata.get("input_sample_rate"))
        if "input_samples_per_window" in stream.metadata.keys():
            result.samples_per_window = int(stream.metadata.get("input_samples_per_window"))
        if "input_samples_per_hop" in stream.metadata.keys():
            result.samples_per_hop = int(stream.metadata.get("input_samples_per_hop"))
        if "model_version" in stream.metadata.keys():
            result.model_version = stream.metadata.get("model_version")
        result.add_events(stream, save_mode=save_mode, base_dir=base_dir)
        return result

    def add_events(
        self,
        stream: RedvoxPacketM.EventStream,
        save_mode: FileSystemSaveMode = FileSystemSaveMode.MEM,
        base_dir: str = ".",
    ):
        """
        add events from a Redvox Api1000 Packet EventStream with the same name.
        Does nothing if names do not match

        :param stream: stream of events to add
        :param save_mode: FileSystemSaveMode that determines how Event data is saved.
                            Default FileSystemSaveMode.MEM (use RAM).  Other options are DISK (save to directory)
                            and TEMP (save to temporary directory)
        :param base_dir: the location of the parquet file that holds the Event data.  Not used if save_data is False.
                            Default current directory (".")
        """
        if self.name == stream.name:
            timestamps = stream.timestamps.timestamps
            events = stream.events
            for i in range(len(timestamps)):
                self.events.append(Event(timestamps[i], save_mode=save_mode, base_dir=base_dir).read_raw(events[i]))
        elif self.debug:
            print(f"Stream name mismatch while adding to EventStream.  Expected {self.name}, got {stream.name}.")

    def sort_events(self, asc: bool = True):
        """
        sort the events in the stream via ascending or descending timestamp order

        :param asc: if True, data is sorted in ascending order
        """
        self.events.sort(key=lambda e: e.get_timestamp(), reverse=not asc)

    def num_events(self) -> int:
        """
        :return: number of events in stream
        """
        return len(self.events)

    def sample_rate_hz(self):
        """
        :return: sample rate of events in the stream in hz
        """
        return np.mean(np.diff([e.get_timestamp() for e in self.events]))

    def window_sample_rate_hz(self):
        """
        :return: idealized event sample window rate in hz
        """
        return self.input_sample_rate / self.samples_per_window

    def hop_sample_rate_hz(self):
        """
        :return: idealized event sample hop rate in hz
        """
        return self.input_sample_rate / self.samples_per_hop

    def create_event_window(self, start: float = -np.inf, end: float = np.inf):
        """
        removes any event in the stream that doesn't match start <= event < end
        adds empty events to beginning and end of data (as long as the corresponding input values are not infinity)
        default start is negative infinity, default end is infinity
        all times in microseconds since epoch UTC

        :param start: inclusive start time of events to keep
        :param end: exclusive end time of events to keep
        """
        self.events = [s for s in self.events if start <= s.get_timestamp() < end]
        if self.num_events() > 0:
            if start < self.events[0].get_timestamp() and not np.isinf(start):
                self.events.insert(0, Event(start, self.name))
            if not np.isinf(end):
                self.events.append(Event(end - 1, self.name))

    def get_file_names(self) -> List[str]:
        """
        :return: the names of the files which store the event data
        """
        return [e.file_name() for e in self.events]

    def save_streams(self):
        """
        saves all streams to disk

        note: use the function set_save_dir() to change where events are saved
        """
        for e in self.events:
            if e.is_save_to_disk():
                e.to_json_file()

    def set_save_dir(self, new_dir: str):
        """
        change the directory where events are saved to

        :param new_dir: new directory path
        """
        for e in self.events:
            e.set_save_dir(new_dir)

    def set_save_mode(self, new_save_mode: FileSystemSaveMode):
        """
        update the save mode for all EventStream

        :param new_save_mode: save mode to set
        """
        for e in self.events:
            e.set_save_mode(new_save_mode)

    def update_timestamps(self, offset_model: om.OffsetModel, use_model_function: bool = False):
        """
        update the timestamps in the data

        :param offset_model: model used to update the timestamps
        :param use_model_function: if True, use the model's slope function to update the timestamps.
                                    otherwise uses the best offset (model's intercept value).  Default False
        """
        for evnt in self.events:
            evnt.update_timestamps(offset_model, use_model_function)

    def original_timestamps(self, offset_model: om.OffsetModel, use_model_function: bool = False):
        """
        undo the update to the timestamps in the data

        :param offset_model: model used to update the timestamps
        :param use_model_function: if True, use the model's slope function to update the timestamps.
                                    otherwise uses the best offset (model's intercept value).  Default False
        """
        for evnt in self.events:
            evnt.original_timestamps(offset_model, use_model_function)

    @staticmethod
    def from_json_dict(json_dict: dict) -> "EventStream":
        """
        :param json_dict: json dict to parse
        :return: EventStream from json dict
        """
        if "name" in json_dict.keys():
            result = EventStream(
                json_dict["name"],
                [Event.from_json_dict(e) for e in json_dict["events"]],
                json_dict["input_sample_rate"],
                json_dict["samples_per_window"],
                json_dict["samples_per_hop"],
                json_dict["model_version"],
                json_dict["metadata"],
            )
        else:
            result = EventStream("Empty Stream; no name for identification")
        return result

    @staticmethod
    def from_json_file(file_dir: str, file_name: str) -> "EventStream":
        """
        :param file_dir: full path to containing directory for the file
        :param file_name: name of file to load data from
        :return: EventStream from json file
        """
        json_data = json_file_to_dict(os.path.join(file_dir, f"{file_name}"))
        if "name" in json_data.keys():
            result = EventStream(
                json_data["name"],
                json_data["events"],
                json_data["input_sample_rate"],
                json_data["samples_per_window"],
                json_data["samples_per_hop"],
                json_data["model_version"],
                json_data["metadata"],
            )
            result.set_save_mode(FileSystemSaveMode.DISK)
            result.set_save_dir(file_dir)
        else:
            result = EventStream("Empty Stream; no name for identification")
        return result

    def to_json_file(self, file_dir: str = ".", file_name: Optional[str] = None) -> Path:
        """
        saves the EventStream as a json file

        :param file_dir: the directory to save the file into.  default current directory (".")
        :param file_name: the optional base file name.  Do not include a file extension.
                            If None, a default file name is created using this format:
                            eventstream_[eventstream.name].json
        :return: path to json file
        """
        return io.eventstream_to_json_file(self, file_dir, file_name)

    def print_errors(self):
        """
        print all errors to screen
        """
        for e in self.events:
            e.print_errors()


@dataclass_json
@dataclass
class EventStreams:
    """
    stores multiple event streams per station.

    ALL timestamps in microseconds since epoch UTC unless otherwise stated

    Properties:
        streams: List[EventStream]; list of all EventStream.  Default empty list

        ml_data: Optional ExtractedMl from the packets.  Default None

        debug: bool; if True, output additional information during runtime.  Default False
    """

    streams: List[EventStream] = field(default_factory=lambda: [])
    ml_data: Optional[ml.ExtractedMl] = None
    debug: bool = False

    def __repr__(self):
        return f"streams: {[s.__repr__() for s in self.streams]}, ml_data: {self.ml_data}, debug: {self.debug}"

    def __str__(self):
        return f"streams: {[s.__str__() for s in self.streams]}, ml_data: {self.ml_data}"

    def as_dict(self) -> dict:
        """
        :return: EventStreams as dict
        """
        return {
            "streams": [s.as_dict() for s in self.streams],
            "ml_data": self.ml_data.to_dict() if self.ml_data else None,
        }

    def read_from_packet(self, packet: RedvoxPacketM):
        """
        read the eventstream payload from a single Redvox Api1000 packet

        :param packet: packet to read data from
        """
        for st in packet.event_streams:
            if st.name == ml.ML_EVENT_STREAM_NAME:
                if self.ml_data:
                    self.ml_data.windows.extend(ml.extract_ml_windows(_find_ml_event_stream(packet)))
                else:
                    self.ml_data = ml.extract_ml_from_packet(WrappedRedvoxPacketM(packet))
            else:
                if st.name in self.get_stream_names() and self.get_stream(st.name).has_data():
                    self.get_stream(st.name).add_events(st)
                else:
                    self.remove_stream(st.name)
                    self.streams.append(EventStream.from_eventstream(st))

    def read_from_packets_list(self, packets: List[RedvoxPacketM]):
        """
        read the eventstream payload from multiple Redvox Api1000 packets

        :param packets: packets to read data from
        """
        for p in packets:
            if type(p) == RedvoxPacketM:
                self.read_from_packet(p)

    def append(self, other_stream: EventStream):
        """
        append another EventStream to an existing EventStream or add to the list of EventStream

        :param other_stream: other EventStream to add
        """
        if other_stream.name in self.get_stream_names():
            self.get_stream(other_stream.name).add_events(other_stream)
        else:
            self.streams.append(other_stream)

    def append_ml(self, other_ml: ml.ExtractedMl):
        """
        append the windows from another extracted machine learning object or
        set the existing ML object if its empty.

        :param other_ml: other ExtractedMl to add
        """
        if self.ml_data:
            self.ml_data.windows.extend(other_ml.windows)
        else:
            self.ml_data = other_ml

    def append_streams(self, other_streams: "EventStreams"):
        """
        append another EventStreams object to an existing EventStreams object

        :param other_streams: EventStreams to add
        """
        for s in other_streams.streams:
            self.append(s)
        self.append_ml(other_streams.ml_data)

    def remove_stream(self, stream_name: str):
        """
        remove any stream with the same stream_name

        :param stream_name: name of stream to remove
        """
        self.streams = [s for s in self.streams if s.name != stream_name]

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

    def create_event_window(self, start: float = -np.inf, end: float = np.inf):
        """
        removes any event in the streams and ML that doesn't match start <= event < end
        default start is negative infinity, default end is infinity
        all times in microseconds since epoch UTC

        :param start: inclusive start time of events to keep
        :param end: exclusive end time of events to keep
        """
        for s in self.streams:
            s.create_event_window(start, end)
        if self.ml_data:
            self.ml_data.windows = [s for s in self.ml_data.windows if start <= s.timestamp < end]

    def set_save_dir(self, new_dir: str):
        """
        change the directory where events are saved to

        :param new_dir: new directory path
        """
        for s in self.streams:
            s.set_save_dir(new_dir)

    def set_save_mode(self, new_save_mode: FileSystemSaveMode):
        """
        update the save mode for all EventStream

        :param new_save_mode: save mode to set
        """
        for s in self.streams:
            s.set_save_mode(new_save_mode)

    def update_timestamps(self, offset_model: om.OffsetModel, use_model_function: bool = False):
        """
        update the timestamps in the data

        :param offset_model: model used to update the timestamps
        :param use_model_function: if True, use the model's slope function to update the timestamps.
                                    otherwise uses the best offset (model's intercept value).  Default False
        """
        for evnt in self.streams:
            evnt.update_timestamps(offset_model, use_model_function)
        if self.ml_data:
            for w in self.ml_data.windows:
                w.timestamp = offset_model.update_time(w.timestamp, use_model_function)

    def original_timestamps(self, offset_model: om.OffsetModel, use_model_function: bool = False):
        """
        undo the update to the timestamps in the data

        :param offset_model: model used to update the timestamps
        :param use_model_function: if True, use the model's slope function to update the timestamps.
                                    otherwise uses the best offset (model's intercept value).  Default False
        """
        for evnt in self.streams:
            evnt.original_timestamps(offset_model, use_model_function)
        if self.ml_data:
            for w in self.ml_data.windows:
                w.timestamp = offset_model.get_original_time(w.timestamp, use_model_function)

    @staticmethod
    def from_dict(in_dict: dict) -> "EventStreams":
        """
        :param in_dict: dictionary representing an EventStreams object
        :return: the EventStreams object from the dictionary
        """
        result = EventStreams()
        if "streams" in in_dict.keys():
            result.streams = [EventStream.from_json_dict(s) for s in in_dict["streams"]]
        if "ml_data" in in_dict.keys():
            result.ml_data = ml.ExtractedMl.from_dict(in_dict["ml_data"])
        return result

    @staticmethod
    def from_json_file(file_dir: str, file_name: str) -> "EventStreams":
        """
        :param file_dir: full path to containing directory for the file
        :param file_name: name of file to load data from
        :return: EventStreams from json file
        """
        return EventStreams.from_dict(json_file_to_dict(os.path.join(file_dir, f"{file_name}")))

    def to_json_file(self, file_dir: str = ".", file_name: Optional[str] = None) -> Path:
        """
        saves the EventStream as a json file

        :param file_dir: the directory to save the file into.  default current directory (".")
        :param file_name: the optional base file name.  Do not include a file extension.
                            If None, a default file name is created using this format:
                            eventstreams.json
        :return: path to json file
        """
        return io.eventstreams_to_json_file(self, file_dir, file_name)


def _find_ml_event_stream(packet: RedvoxPacketM) -> Optional[es.EventStream]:
    """
    Attempts to find an event stream with ML data.

    :param packet: The packet to search in.
    :return: An instance of the matching event stream or None.
    """
    stream: RedvoxPacketM.EventStream
    for stream in packet.event_streams:
        if stream.name == ml.ML_EVENT_STREAM_NAME:
            return es.EventStream(stream)
    return None


def _get_ml_from_packet(packet: RedvoxPacketM) -> Optional[ml.ExtractedMl]:
    """
    reads the machine learning payload from a single Redvox Api1000 packet

    :param packet: packet to read machine learning data from
    """
    stream: Optional[es.EventStream] = _find_ml_event_stream(packet)
    return None if stream is None else ml.extract_ml_from_event_stream(stream)
