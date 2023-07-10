"""
This module provides IO primitives for working with data windows.
"""
from dataclasses import dataclass
import os.path
from pathlib import Path
import pickle
import json
import enum

from typing import (
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
)

import lz4.frame

from redvox.common.io import FileSystemWriter, FileSystemSaveMode, json_to_dict


if TYPE_CHECKING:
    from redvox.common.data_window import DataWindow


class DataWindowOutputType(enum.Enum):
    """
    Type of file to create when exporting DataWindow
    """

    NONE: int = 0
    LZ4: int = 1
    PARQUET: int = 2
    JSON: int = 3

    @staticmethod
    def list_names() -> List[str]:
        """
        :return: list of possible values for OutputType
        """
        return [n.name for n in DataWindowOutputType]

    @staticmethod
    def list_non_none_names() -> List[str]:
        """
        :return: List of possible non-None values for OutputType
        """
        return [n.name for n in DataWindowOutputType if n != DataWindowOutputType.NONE]

    @staticmethod
    def str_to_type(str_type: str) -> "DataWindowOutputType":
        """
        converts the string to the corresponding OutputType
        if the type given is not in list_non_none_names(), returns NONE value

        :param str_type: string to convert
        :return: DataWindowOutputType matching string given or NONE
        """
        str_type = str_type.upper()
        if str_type in DataWindowOutputType.list_non_none_names():
            return DataWindowOutputType[str_type]
        return DataWindowOutputType["NONE"]


class DataWindowFileSystemWriter(FileSystemWriter):
    """
    This class holds the FileSystemWriter info for DataWindows.  Extends the FileSystemWriter from io.py

    Properties:
        file_name: str, the name of the file (do not include extension)

        file_ext: str, the extension used by the file (do not include the .)  Default "NONE"

        base_dir: str, the directory to save the file to.  Default "." (current dir)

        make_run_me: bool, if True, makes a sample runme.py file when saving to disk.  default False

        orig_path: str, the current working directory when the object is initialized

    Protected:
        _save_mode: FileSystemSaveMode, determines how files get saved

        _temp_dir: TemporaryDirectory, temporary directory for large files when not saving to disk
    """

    def __init__(self, file_name: str, file_ext: str = "none", base_dir: str = ".", make_run_me: bool = False):
        """
        initialize DataWindowFileSystemWriter

        :param file_name: name of file
        :param file_ext: extension of file, default "none"
        :param base_dir: directory to save file to, default "." (current dir)
        :param make_run_me: if True, add a runme.py file to the saved files.  Default False
        """
        self.orig_path = os.getcwd()
        if not os.path.exists(base_dir):
            os.makedirs(base_dir, exist_ok=True)
        os.chdir(base_dir)
        super().__init__(
            file_name,
            file_ext,
            ".",
            FileSystemSaveMode.DISK
            if DataWindowOutputType.str_to_type(file_ext) != DataWindowOutputType.NONE
            else FileSystemSaveMode.MEM,
        )
        self.make_run_me = make_run_me

    def set_extension(self, ext: str):
        """
        change the file extension.  Valid values are "PARQUET", "LZ4", "JSON" and "NONE".  Invalid values become "NONE"

        :param ext: extension to change to
        """
        self.file_extension = DataWindowOutputType.str_to_type(ext).name.lower()


@dataclass
class DataWindowSerializationResult:
    path: str
    serialized_bytes: int
    compressed_bytes: int


def data_window_as_json(data_window: "DataWindow") -> str:
    """
    Converts the DataWindow's metadata into a JSON dictionary

    :param data_window: The data window to convert
    :return: The data window's metadata as a JSON dictionary
    """
    return json.dumps(data_window.as_dict())


def data_window_to_json(
    data_window: "DataWindow",
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
        f.write(data_window_as_json(data_window))
        return file_path.resolve(False)


def json_file_to_data_window(file_path: str) -> Dict:
    """
    load a specifically named DataWindow as a dictionary from a directory

    :param file_path: full path of file to load
    :return: the dictionary of the DataWindow if it exists, or None otherwise
    """
    with open(file_path, "r") as f_p:
        return json_to_dict(f_p.read())


def serialize_data_window(
    data_window: "DataWindow",
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
        else f"{int(data_window.start_date())}"
        f"_{int(data_window.end_date())}"
        f"_{len(data_window.event_name)}.pkl.lz4"
    )

    json_path: Path = data_window.fs_writer().json_path()
    with open(json_path, "w") as f:
        f.write(data_window.to_json())
        json_path.resolve(False)

    file_path: Path = Path(base_dir).joinpath(_file_name)

    with lz4.frame.open(file_path, "wb", compression_level=compression_factor) as compressed_out:
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
