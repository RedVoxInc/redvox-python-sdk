"""
This module provides IO primitives for working with session models.
"""
from pathlib import Path
import json
import os
import pickle
from typing import (
    Optional,
    TYPE_CHECKING,
)

from redvox.common.io import get_json_file, json_file_to_dict, json_to_dict

# two versions, one for reproducing the object and one for reporting/bulletins


if TYPE_CHECKING:
    from redvox.common.session_model import SessionModel


def to_json(session: "SessionModel",) -> str:
    """
    :return: station as json string
    """
    return json.dumps(session.as_dict())


def to_json_file(session: "SessionModel",
                 out_dir: str = ".",
                 file_name: Optional[str] = None) -> Path:
    """
    saves the SessionModel as json.

    :param session: SessionModel to save
    :param out_dir: path to save file at.  Defaults to "." (current directory)
    :param file_name: the optional base file name.  Do NOT include a file extension.
                        If None, uses the default [id]_[startdate].json
    :return: path to json file
    """
    _file_name: str = (
        file_name
        if file_name is not None
        else session.default_json_file_name()
    ) + ".json"

    file_path: Path = Path(out_dir).joinpath(_file_name)
    with open(file_path, "w") as f_p:
        f_p.write(to_json(session))
        return file_path.resolve(False)


def from_json_file(file_path: str) -> dict:
    """
    Returns a dictionary from the JSON string stored in the file at file_path

    :param file_path: the full name and path to a JSON SessionModel file
    :return: dictionary from JSON string of a SessionModel
    """
    with open(file_path, "r") as f_p:
        return json_to_dict(f_p.read())


def compress_session_model(
        session: "SessionModel",
        base_dir: str = ".",
        file_name: Optional[str] = None
) -> Path:
    """
    Compresses a SessionModel to a pkl file.

    :param session: The SessionModel to compress.
    :param base_dir: The base directory to write the serialized file to (default=.).
    :param file_name: The optional file name. Do not include the extension (it's always gonna be .pkl).
                      If None, a default filename with the following format is used: [id]_[start_ts]_model.pkl
    :return: The path to the written compressed file.
    """

    _file_name: str = (
        file_name
        if file_name is not None
        else f"{session.id}_{int(session.start_date)}_model"
    ) + ".pkl"

    file_path: Path = Path(base_dir).joinpath(_file_name)

    with open(file_path, "wb") as compressed_out:
        pickle.dump(session, compressed_out)
        compressed_out.flush()
        return file_path.resolve(False)


def decompress_session_model(path: str) -> "SessionModel":
    """
    Decompresses and deserializes a SessionModel written to disk.

    :param path: Path to the serialized and compressed SessionModel.
    :return: An instance of a SessionModel.
    """
    with open(path, "rb") as compressed_in:
        return pickle.load(compressed_in)