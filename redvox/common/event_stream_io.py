"""
This module provides IO primitives for working with EventStream data.
"""
from pathlib import Path
import json
import os
from typing import (
    Optional,
    TYPE_CHECKING,
)

from redvox.common.io import get_json_file, json_file_to_dict, json_to_dict


if TYPE_CHECKING:
    from redvox.common.event_stream import Event, EventStream, EventStreams


def event_to_json(event: "Event", ) -> str:
    """
    :param event: event to save
    :return: Event as json string
    """
    return json.dumps(event.as_dict())


def event_to_json_file(event: "Event",
                       file_name: Optional[str] = None) -> Path:
    """
    saves the Event as json and data in the same directory.

    :param event: Event to save
    :param file_name: the optional base file name.  Do not include a file extension.
                        If None, uses the default event_[id].json
    :return: path to json file
    """
    _file_name: str = (
        file_name
        if file_name is not None
        else event.default_json_file_name()
    )

    file_path: Path = event.fs_writer().json_path()
    with open(file_path, "w") as f_p:
        f_p.write(event_to_json(event))
        return file_path.resolve(False)


def eventstream_to_json(event_stream: "EventStream", ) -> str:
    """
    :return: EventStream as json string
    """
    return json.dumps(event_stream.as_dict())


def eventstream_to_json_file(event_stream: "EventStream",
                             file_dir: str = ".",
                             file_name: Optional[str] = None) -> Path:
    """
    saves the EventStream as json and data in the same directory.

    :param event_stream: EventStream to save
    :param file_dir: the directory to save the file into.  default current directory (".")
    :param file_name: the optional base file name.  Do not include a file extension.
                        If None, uses the default eventstream_[eventstream.name].json
    :return: path to json file
    """
    _file_name: str = (
        file_name
        if file_name is not None
        else f"eventstream_{event_stream.name}"
    )

    file_path: Path = Path(os.path.join(file_dir, f"{_file_name}.json"))
    with open(file_path, "w") as f_p:
        f_p.write(eventstream_to_json(event_stream))
        return file_path.resolve(False)


def eventstreams_to_json(event_streams: "EventStreams", ) -> str:
    """
    :return: EventStreams as json string
    """
    return json.dumps(event_streams.as_dict())


def eventstreams_to_json_file(event_streams: "EventStreams",
                              file_dir: str = ".",
                              file_name: Optional[str] = None) -> Path:
    """
    saves the EventStreams as json and data in the same directory.

    :param event_streams: EventStreams to save
    :param file_dir: the directory to save the file into.  default current directory (".")
    :param file_name: the optional base file name.  Do not include a file extension.
                        If None, uses the default eventstreams.json
    :return: path to json file
    """
    _file_name: str = (
        file_name
        if file_name is not None
        else "eventstreams"
    )

    file_path: Path = Path(os.path.join(file_dir, f"{_file_name}.json"))
    with open(file_path, "w") as f_p:
        f_p.write(eventstreams_to_json(event_streams))
        return file_path.resolve(False)
