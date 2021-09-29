"""
This module provides IO primitives for working with data windows.
"""
from dataclasses import dataclass
import os.path
from pathlib import Path
import pickle
import json
from typing import (
    Dict,
    Optional,
    TYPE_CHECKING,
)

import lz4.frame

from redvox.common.date_time_utils import (
    datetime_to_epoch_microseconds_utc as us_dt,
)


if TYPE_CHECKING:
    from redvox.common.data_window import DataWindow
    from redvox.common.data_window_wpa import DataWindowArrow


def json_to_data_window(json_str: str) -> Dict:
    """
    load a data window from json string

    :param json_str: json string to read
    :return: a dictionary of a data window
    """
    return json.loads(json_str)


@dataclass
class DataWindowSerializationResult:
    path: str
    serialized_bytes: int
    compressed_bytes: int


def serialize_data_window(
        data_window: "DataWindow",
        base_dir: str = ".",
        file_name: Optional[str] = None,
        compression_factor: int = 4,
) -> Path:
    """
    Serializes and compresses a DataWindow to a file.

    :param data_window: The data window to serialize and compress.
    :param base_dir: The base directory to write the serialized file to (default=.).
    :param file_name: The optional file name. If None, a default filename with the following format is used:
                      [start_ts]_[end_ts]_[num_stations].pkl.lz4
    :param compression_factor: A value between 1 and 12. Higher values provide better compression, but take longer.
                               (default=4).
    :return: The path to the written file.
    """

    _file_name: str = (
        file_name
        if file_name is not None
        else f"{int(data_window.start_datetime.timestamp())}"
             f"_{int(data_window.end_datetime.timestamp())}"
             f"_{len(data_window.station_ids)}.pkl.lz4"
    )

    file_path: Path = Path(base_dir).joinpath(_file_name)

    with lz4.frame.open(
            file_path, "wb", compression_level=compression_factor
    ) as compressed_out:
        pickle.dump(data_window, compressed_out)
        compressed_out.flush()
        return file_path.resolve(False)


def deserialize_data_window(path: str) -> "DataWindow":
    """
    Decompresses and deserializes a DataWindow written to disk.

    :param path: Path to the serialized and compressed data window.
    :return: An instance of a DataWindow.
    """
    with lz4.frame.open(path, "rb") as compressed_in:
        return pickle.load(compressed_in)


def json_file_to_data_window(base_dir: str, file_name: str) -> Dict:
    """
    load a data window from json written to disk

    :param base_dir: directory where json file is saved
    :param file_name: name of json file to load
    :return: a dictionary representing a json-ified data window
    """
    with open(Path(base_dir).joinpath(file_name), "r") as r_f:
        return json_to_data_window(r_f.read())


def data_window_to_json(
        data_win: "DataWindow",
        base_dir: str = ".",
        file_name: Optional[str] = None,
        compression_format: str = "lz4",
) -> str:
    """
    Converts a data window to json format

    :param data_win: the data window object to convert
    :param base_dir: the base directory to write the data file to
    :param file_name: the data object's optional base file name.  Do not include a file extension.
                        If None, a default file name is created using this format:
                        [start_ts]_[end_ts]_[num_stations].[compression_type]
    :param compression_format: the compression format to use.  default lz4
    :return: The path to the written file
    """
    _file_name: str = (
        file_name
        if file_name is not None
        else f"{int(data_win.start_datetime.timestamp())}"
             f"_{int(data_win.end_datetime.timestamp())}"
             f"_{len(data_win.station_ids)}"
    )
    base_dir = os.path.join(base_dir, "dw")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    if compression_format == "lz4":
        _ = str(
            serialize_data_window(
                data_win, base_dir, _file_name + ".pkl.lz4"
            ).resolve()
        )
    else:
        dfp = os.path.join(base_dir, _file_name + ".pkl")
        with open(dfp, "wb") as compressed_out:
            pickle.dump(data_win, compressed_out)
    data_win_dict = {
        "start_datetime": us_dt(data_win.start_datetime)
        if data_win.start_datetime
        else None,
        "end_datetime": us_dt(data_win.end_datetime) if data_win.end_datetime else None,
        "station_ids": list(data_win.station_ids),
        "compression_format": compression_format,
        "file_name": _file_name,
    }
    return json.dumps(data_win_dict)


def data_window_to_json_file(
        data_window: "DataWindow",
        base_dir: str = ".",
        file_name: Optional[str] = None,
        compression_format: str = "lz4",
) -> Path:
    """
    Converts a data window to json format.

    :param data_window: the data window object to convert
    :param base_dir: the base directory to write the json file to
    :param file_name: the optional base file name.  Do not include a file extension.
                        If None, a default file name is created using this format:
                        [start_ts]_[end_ts]_[num_stations].json
    :param compression_format: the type of compression to use.  default lz4
    :return: The path to the written file
    """
    _file_name: str = (
        file_name
        if file_name is not None
        else f"{int(data_window.start_datetime.timestamp())}"
             f"_{int(data_window.end_datetime.timestamp())}"
             f"_{len(data_window.station_ids)}"
    )
    file_path: Path = Path(base_dir).joinpath(f"{_file_name}.json")
    with open(file_path, "w") as f_p:
        f_p.write(
            data_window_to_json(
                data_window, base_dir, file_name, compression_format
            )
        )
        return file_path.resolve(False)


def data_window_as_json(
        data_window: "DataWindowArrow"
) -> str:
    """
    Converts the DataWindow's metadata into a JSON dictionary

    :param data_window: The data window to convert
    :return: The data window's metadata as a JSON dictionary
    """
    return json.dumps(data_window.as_dict())


def data_window_to_json_wpa(
        data_window: "DataWindowArrow",
        base_dir: str = ".",
        file_name: Optional[str] = None,
) -> Path:
    """
    Converts the DataWindow into a JSON metadata file

    :param data_window: The data window to convert.
    :param base_dir: The base directory to write the JSON file to (default=.).
    :param file_name: The optional file name. If None, a default filename with the following format is used:
                      [event_name].json
    :return: The path to the written metadata file.
    """
    _file_name = file_name if file_name is not None else data_window.event_name
    os.makedirs(base_dir, exist_ok=True)
    for s in data_window.stations():
        s.to_json_file()
    file_path: Path = Path(base_dir).joinpath(f"{_file_name}.json")
    with open(file_path, "w") as f:
        f.write(data_window.to_json())
        return file_path.resolve(False)


def json_file_to_data_window_wpa(file_path: str) -> Dict:
    """
    load a specifically named DataWindow as a dictionary from a directory

    :param file_path: full path of file to load
    :return: the dictionary of the DataWindow if it exists, or None otherwise
    """
    with open(file_path, "r") as f_p:
        return json_to_data_window(f_p.read())


def serialize_data_window_wpa(
        data_window: "DataWindowArrow",
        base_dir: str = ".",
        file_name: Optional[str] = None,
        compression_factor: int = 4,
) -> Path:
    """
    Serializes and compresses a DataWindow to a file and creates a JSON metadata file for the compressed file.

    :param data_window: The data window to serialize and compress.
    :param base_dir: The base directory to write the serialized file to (default=.).
    :param file_name: The optional file name. If None, a default filename with the following format is used:
                      [start_ts]_[end_ts]_[event_name].pkl.lz4
    :param compression_factor: A value between 1 and 12. Higher values provide better compression, but take longer.
                               (default=4).
    :return: The path to the written compressed file.
    """

    _file_name: str = (
        file_name
        if file_name is not None
        else f"{int(data_window.get_start_date())}"
             f"_{int(data_window.get_end_date())}"
             f"_{len(data_window.event_name)}.pkl.lz4"
    )

    json_path: Path = Path(data_window.files_dir).joinpath(data_window.event_name + ".json")
    with open(json_path, "w") as f:
        f.write(data_window.to_json())
        json_path.resolve(False)

    file_path: Path = Path(base_dir).joinpath(_file_name)

    with lz4.frame.open(
            file_path, "wb", compression_level=compression_factor
    ) as compressed_out:
        pickle.dump(data_window, compressed_out)
        compressed_out.flush()
        return file_path.resolve(False)


def deserialize_data_window_wpa(path: str) -> "DataWindowArrow":
    """
    Decompresses and deserializes a DataWindow written to disk.

    :param path: Path to the serialized and compressed data window.
    :return: An instance of a DataWindow.
    """
    with lz4.frame.open(path, "rb") as compressed_in:
        return pickle.load(compressed_in)
