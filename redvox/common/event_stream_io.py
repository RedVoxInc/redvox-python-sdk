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
    from redvox.common.event_stream import EventStream


def to_json(event_stream: "EventStream",) -> str:
    """
    :return: EventStream as json string
    """
    return json.dumps(event_stream.as_dict())


def to_json_file(event_stream: "EventStream",
                 file_name: Optional[str] = None) -> Path:
    """
    saves the EventStream as json and data in the same directory.

    :param event_stream: EventStream to save
    :param file_name: the optional base file name.  Do not include a file extension.
                        If None, uses the default event_[id].json
    :return: path to json file
    """
    _file_name: str = (
        file_name
        if file_name is not None
        else event_stream.default_json_file_name()
    )

    file_path: Path = event_stream.fs_writer().json_path()
    with open(file_path, "w") as f_p:
        f_p.write(to_json(event_stream))
        return file_path.resolve(False)
