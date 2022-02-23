from typing import List, Optional, Dict
from dataclasses import dataclass, field
from pathlib import Path
import os

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from dataclasses_json import dataclass_json

from redvox.api1000.common.mapping import Mapping
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.api1000.wrapped_redvox_packet import event_streams as es
from redvox.common.errors import RedVoxExceptions
from redvox.common import offset_model as om
from redvox.common.io import FileSystemWriter as Fsw, FileSystemSaveMode
import redvox.common.event_stream_io as io


class EventStream:
    """
    stores event stream data gathered from a single station.
    ALL timestamps in microseconds since epoch UTC unless otherwise stated
    """
    def __init__(self, name: str = "event",
                 schema: Optional[Dict[str, list]] = None,
                 save_mode: FileSystemSaveMode = FileSystemSaveMode.MEM,
                 base_dir: str = "."):
        """
        initialize EventStream for a station

        :param name: name of the EventStream.  Default "event"
        :param schema: a structured dictionary of the data table schema.  Dictionary must look like:
                    {"string": [s_values], "numeric": [n_values], "boolean": [o_values], "byte": [b_values]}
                    where [*_values] is a list of strings and can be empty.  Default None
        :param save_mode: FileSystemSaveMode that determines how data is saved.
                            Default FileSystemSaveMode.MEM (use RAM).  Other options are DISK (save to directory)
                            and TEMP (save to temporary directory)
        :param base_dir: the location of the parquet file that holds the data.  Not used if save_data is False.
                            Default current directory (".")
        """
        self.name = name
        self.timestamps_metadata = {}
        self.metadata = {}

        self._errors = RedVoxExceptions("EventStream")
        self._is_timestamps_corrected = False
        self._fs_writer = Fsw(f"event_{name}", "parquet", base_dir, save_mode)
        self._data = None
        self._schema = {"string": [], "numeric": [], "boolean": [], "byte": []}
        if schema is not None:
            self.set_schema(schema)

    def as_dict(self) -> dict:
        """
        :return: EventStream as a dictionary
        """
        return {
            "name": self.name,
            "metadata": self.metadata,
            "timestamps_metadata": self.timestamps_metadata,
            "is_timestamps_corrected": self._is_timestamps_corrected,
            "schema": self._schema,
            "file_path": self.full_path(),
            "errors": self._errors.as_dict()
        }

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

    def __set_schema(self, name: str, value: str):
        self._schema[name].append(value)

    def _get_tbl_schema(self) -> Dict[str, list]:
        """
        :return: the dictionary used to create the EventStream data object
        """
        if self._data:
            result = {}
            for f in self._data.schema.names:
                result[f] = []
        else:
            result = {"timestamps": [], "unaltered_timestamps": []}
            for t, s in self._schema.items():
                for k in s:
                    result[k] = []
        return result

    def read_events(self, eventstream: es.EventStream):
        """
        read the payloads of each event in the eventstream and separate the data by payload type

        :param eventstream: stream of events to process
        """
        self.name = eventstream.get_name()
        self._fs_writer.file_name = f"event_{self.name}"
        num_events = eventstream.get_events().get_count()
        if num_events > 1:
            tbl = self._get_tbl_schema()
            self.timestamps_metadata = eventstream.get_timestamps().get_metadata()
            self.metadata = eventstream.get_metadata()
            first_event = eventstream.get_events().get_values()[0]
            for t, c in map(self.__get_keys, ["string", "numeric", "boolean", "byte"],
                            [first_event.get_string_payload(), first_event.get_numeric_payload(),
                             first_event.get_boolean_payload(), first_event.get_byte_payload()]):
                for k in c:
                    self.add_to_schema(t, k)
                    tbl[k] = []
            for i in range(num_events):
                tbl["timestamps"].append(eventstream.get_timestamps().get_timestamps()[i])
                tbl["unaltered_timestamps"].append(eventstream.get_timestamps().get_timestamps()[i])
                evnt = eventstream.get_events().get_values()[i]
                for items in map(self.__get_items, [evnt.get_string_payload(), evnt.get_numeric_payload(),
                                                    evnt.get_boolean_payload(), evnt.get_byte_payload()]):
                    for c, st in items:
                        tbl[c].append(st)
            self._data = pa.Table.from_pydict(tbl)

    def read_raw(self, stream: RedvoxPacketM.EventStream) -> 'EventStream':
        """
        read the contents of a protobuf stream

        :param stream: the protobuf stream to read
        """
        self.name = stream.name
        self._fs_writer.file_name = f"event_{self.name}"
        num_events = len(stream.events)
        if num_events > 1:
            tbl = self._get_tbl_schema()
            self.timestamps_metadata = stream.timestamps.metadata
            self.metadata = stream.metadata
            first_event = stream.events[0]
            for t, c in map(EventStream.__get_keys_raw, ["string", "numeric", "boolean", "byte"],
                            [first_event.string_payload, first_event.numeric_payload,
                             first_event.boolean_payload, first_event.byte_payload]):
                for k in c:
                    self.add_to_schema(t, k)
                    tbl[k] = []
            for i in range(num_events):
                tbl["timestamps"].append(stream.timestamps.timestamps[i])
                tbl["unaltered_timestamps"].append(stream.timestamps.timestamps[i])
                evnt = stream.events[i]
                for items in map(EventStream.__get_items_raw, [evnt.string_payload, evnt.numeric_payload,
                                                               evnt.boolean_payload, evnt.byte_payload]):
                    for c, st in items:
                        tbl[c].append(st)
            self._data = pa.Table.from_pydict(tbl)
        return self

    def read_from_dir(self, file: str):
        """
        read a pyarrow table from a file on disk

        :param file: full path to the file to read
        """
        try:
            tbl = pq.read_table(file)
            if tbl.schema.names == self._get_tbl_schema():
                self._data = tbl
        except FileNotFoundError:
            self._errors.append("No data file was found; this event is empty.")
            self._data = None

    def get_string_schema(self) -> List[str]:
        """
        :return: the column names of string typed data as a list of strings
        """
        return self._schema["string"]

    def get_numeric_schema(self) -> List[str]:
        """
        :return: the column names of numeric typed data as a list of strings
        """
        return self._schema["numeric"]

    def get_boolean_schema(self) -> List[str]:
        """
        :return: the column names of boolean typed data as a list of strings
        """
        return self._schema["boolean"]

    def get_byte_schema(self) -> List[str]:
        """
        :return: the column names of byte typed data as a list of strings
        """
        return self._schema["byte"]

    def get_schema(self) -> dict:
        """
        :return: the schema of the EventStream
        """
        return self._schema

    def get_string_values(self) -> pa.Table:
        """
        :return: the string data as a pyarrow table
        """
        return self._data.select(self.get_string_schema()) if self._data else pa.Table.from_pydict({})

    def get_numeric_values(self) -> pa.Table:
        """
        :return: the numeric data as a pyarrow table
        """
        return self._data.select(self.get_numeric_schema()) if self._data else pa.Table.from_pydict({})

    def get_boolean_values(self) -> pa.Table:
        """
        :return: the boolean data as a pyarrow table
        """
        return self._data.select(self.get_boolean_schema()) if self._data else pa.Table.from_pydict({})

    def get_byte_values(self) -> pa.Table:
        """
        :return: the byte data as a pyarrow table
        """
        return self._data.select(self.get_byte_schema()) if self._data else pa.Table.from_pydict({})

    def _check_for_name(self, column_name: str, schema: List[str]) -> bool:
        """
        :param column_name: name of column to check for
        :param schema: list of allowed names
        :return: True if column_name is in schema, sets error and returns False if not
        """
        if column_name not in schema:
            self._errors.append(f"WARNING: Column {column_name} does not exist; try one of {schema}")
            return False
        return True

    def __get_column_data(self, schema: List[str], column_name: str) -> np.array:
        """
        :param schema: list of column names to search
        :param column_name: column name to get
        :return: the data as an np.array; if empty, column name or data doesn't exist
        """
        return self._data[column_name].to_numpy() if self._check_for_name(column_name, schema) else np.array([])

    def get_string_column(self, column_name: str) -> np.array:
        """
        :param column_name: name of string payload to retrieve
        :return: string data from the column specified
        """
        return self.__get_column_data(self.get_string_schema(), column_name)

    def get_numeric_column(self, column_name: str) -> np.array:
        """
        :param column_name: name of numeric payload to retrieve
        :return: numeric data from the column specified
        """
        return self.__get_column_data(self.get_numeric_schema(), column_name)

    def get_boolean_column(self, column_name: str) -> np.array:
        """
        :param column_name: name of boolean payload to retrieve
        :return: boolean data from the column specified
        """
        return self.__get_column_data(self.get_boolean_schema(), column_name)

    def get_byte_column(self, column_name: str) -> np.array:
        """
        :param column_name: name of byte payload to retrieve
        :return: bytes data from the column specified
        """
        return self.__get_column_data(self.get_byte_schema(), column_name)

    def set_schema(self, schema: Dict[str, list]):
        """
        sets the schema of the EventStream using a specially structured dictionary.
        Structure is:

        {"string": [s_values], "numeric": [n_values], "boolean": [o_values], "byte": [b_values]}

        where [*_values] is a list of strings and can be empty

        :param schema: specially structured dictionary of data table schema
        """
        if schema.keys() != self._schema.keys():
            self._errors.append(f"Attempted to add invalid schema with keys {list(schema.keys())} to EventStreams.\n"
                                f"Valid keys are: {list(self._schema.keys())}")
        else:
            self._schema = schema

    def add_to_schema(self, key: str, value: str):
        """
        adds a value to the schema, under the specified key

        :param key: one of "string", "numeric", "boolean", or "byte"
        :param value: the name of the column to add to the schema
        """
        if key not in self._schema.keys():
            self._errors.append("Attempted to add an unknown key to the EventStream schema.\n"
                                f"You must use one of {self._schema.keys()}.")
        else:
            self._schema[key].append(value)

    def add(self, other_stream: es.EventStream):
        """
        adds a Redvox Api1000 EventStream with the same name to the data

        :param other_stream: another EventStream with the same name
        """
        if self.name != other_stream.get_name():
            self._errors.append(f"Attempted to add a stream with a different name ({other_stream.get_name()})")
        else:
            self.timestamps_metadata = {**self.timestamps_metadata, **other_stream.get_timestamps().get_metadata()}
            self.metadata = {**self.metadata, **other_stream.get_metadata()}
            num_events = other_stream.get_events().get_count()
            if num_events > 1:
                tbl = self._get_tbl_schema()
                for i in range(num_events):
                    tbl["timestamps"].append(other_stream.get_timestamps().get_timestamps()[i])
                    tbl["unaltered_timestamps"].append(other_stream.get_timestamps().get_timestamps()[i])
                    evnt = other_stream.get_events().get_values()[i]
                    for items in map(self.__get_items, [evnt.get_string_payload(), evnt.get_numeric_payload(),
                                                        evnt.get_boolean_payload(), evnt.get_byte_payload()]):
                        for c, st in items:
                            tbl[c].append(st)
                self._data = pa.concat_tables([self._data, pa.Table.from_pydict(tbl)])

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
            if num_events > 1:
                tbl = self._get_tbl_schema()
                for i in range(num_events):
                    tbl["timestamps"].append(other_stream.timestamps.timestamps[i])
                    tbl["unaltered_timestamps"].append(other_stream.timestamps.timestamps[i])
                    evnt = other_stream.events[i]
                    for items in map(EventStream.__get_items_raw, [evnt.string_payload, evnt.numeric_payload,
                                                                   evnt.boolean_payload, evnt.byte_payload]):
                        for c, st in items:
                            tbl[c].append(st)
                self._data = pa.concat_tables([self._data, pa.Table.from_pydict(tbl)])

    def append(self, other_stream: "EventStream"):
        """
        add another EventStream onto the calling one if they have the same name

        :param other_stream: other stream to add to current
        """
        if other_stream.name == self.name:
            self._data = pa.concat_tables([self._data, other_stream._data])
            self.timestamps_metadata = {**self.timestamps_metadata, **other_stream.timestamps_metadata}
            self.metadata = {**self.metadata, **other_stream.metadata}
            self._errors.extend_error(other_stream.errors())

    def timestamps(self) -> np.array:
        """
        :return: the timestamps as a numpy array; returns empty array if no timestamps exist
        """
        if "timestamps" in self.data().schema.names:
            return self.data()["timestamps"].to_numpy()
        else:
            return np.array([])

    def unaltered_timestamps(self) -> np.array:
        """
        :return: the unaltered timestamps as a numpy array; returns empty array if no timestamps exist
        """
        if "unaltered_timestamps" in self.data().schema.names:
            return self.data()["unaltered_timestamps"].to_numpy()
        else:
            return np.array([])

    def update_timestamps(self, offset_model: om.OffsetModel, use_model_function: bool = False):
        """
        updates the timestamps of the data points

        :param offset_model: model used to update the timestamps
        :param use_model_function: if True, use the model's slope function to update the timestamps.
                                    otherwise uses the best offset (model's intercept value).  Default False
        """
        if self._data is not None and self._data.num_rows > 0:
            timestamps = pa.array(offset_model.update_timestamps(self._data["timestamps"].to_numpy(),
                                                                 use_model_function))
            self._data.set_column(0, "timestamps", timestamps)

    def default_json_file_name(self) -> str:
        """
        :return: default event stream json file name (event_[event.name]): note there is no extension
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

    def set_file_name(self, new_file: Optional[str] = None):
        """
        * set the pyarrow file name or use the default: event_{EventStream.name}
        * Do not give an extension

        :param new_file: optional file name to change to; default None (use default name)
        """
        self._fs_writer.file_name = new_file if new_file else f"event_{self.name}"

    def full_file_name(self) -> str:
        """
        :return: full name of parquet file containing the data
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

    def write_table(self):
        """
        writes the event stream data to disk.
        """
        if self._data is not None:
            pq.write_table(self._data, self.full_path())

    def data(self) -> pa.Table:
        """
        :return: the data as a pyarrow table
        """
        if self._data is None:
            if self.is_save_to_disk():
                self._data = pq.read_table(self.full_path())
            else:
                return pa.Table.from_pydict({})
        return self._data

    @staticmethod
    def from_json_file(file_dir: str, file_name: str) -> "EventStream":
        """
        :param file_dir: full path to containing directory for the file
        :param file_name: name of file and extension to load data from
        :return: EventStream from json file
        """
        if file_name is None:
            file_name = io.get_json_file(file_dir)
            if file_name is None:
                result = EventStream("Empty")
                result.append_error("JSON file to load EventStream from not found.")
                return result
        json_data = io.json_file_to_dict(os.path.join(file_dir, f"{file_name}.json"))
        if "name" in json_data.keys():
            result = EventStream(json_data["name"], json_data["schema"], FileSystemSaveMode.DISK, file_dir)
            result.metadata = json_data["metadata"]
            result.timestamps_metadata = json_data["timestamps_metadata"]
            result.set_errors(RedVoxExceptions.from_dict(json_data["errors"]))
            result.read_from_dir(json_data["file_path"])
        else:
            result = EventStream("Empty")
            result.append_error(f"Loading from {file_name} failed; missing EventStream name.")
        return result

    def to_json_file(self, file_name: Optional[str] = None) -> Path:
        """
        saves the EventStream as a json file

        :param file_name: the optional base file name.  Do not include a file extension.
                            If None, a default file name is created using this format:
                            event_[event.name].json
        :return: path to json file
        """
        if self._fs_writer.file_extension == "parquet" and self._data is not None:
            self.write_table()
        return io.to_json_file(self, file_name)

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
class EventStreams:
    """
    stores multiple event streams per station
    ALL timestamps in microseconds since epoch UTC unless otherwise stated
    """
    streams: List[EventStream] = field(default_factory=lambda: [])
    save_mode: FileSystemSaveMode = FileSystemSaveMode.MEM
    base_dir: str = "."
    debug: bool = False

    def list_for_dict(self) -> list:
        """
        :return: the name of files that store event streams
        """
        return [s.file_name() for s in self.streams]

    def read_from_packet(self, packet: RedvoxPacketM):
        """
        read the eventstream payload from a single Redvox Api1000 packet

        :param packet: packet to read data from
        """
        for st in packet.event_streams:
            if st.name in self.get_stream_names():
                self.get_stream(st.name).add_raw(st)
            else:
                self.streams.append(EventStream(save_mode=self.save_mode, base_dir=self.base_dir).read_raw(st))

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
            self.get_stream(other_stream.name).append(other_stream)
        else:
            self.streams.append(other_stream)

    def append_streams(self, other_streams: "EventStreams"):
        """
        append another EventStreams object to an existing EventStreams object

        :param other_streams: EventStreams to add
        """
        for s in other_streams.streams:
            self.append(s)

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

    def save_streams(self):
        """
        saves all streams to disk

        note: use the function set_save_dir() to change where events are saved
        """
        for s in self.streams:
            s.to_json_file()

    def set_save_dir(self, new_dir: str):
        """
        change the directory where events are saved to

        :param new_dir: new directory path
        """
        self.base_dir = new_dir
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

    @staticmethod
    def from_dir(base_dir: str, file_names: List[str]) -> "EventStreams":
        """
        :param base_dir: directory containing EventStream files
        :param file_names: the names of .json files containing EventStream data

        :return: EventStreams object from a directory
        """
        return EventStreams([EventStream.from_json_file(base_dir, e) for e in file_names],
                            save_mode=FileSystemSaveMode.DISK, base_dir=base_dir)
