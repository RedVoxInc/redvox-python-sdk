"""
This module provides IO primitives for working with timesync data.
"""
from pathlib import Path
import json
from typing import (
    Dict,
    Optional,
    TYPE_CHECKING,
)

from redvox.common.io import json_file_to_dict

import pyarrow.parquet as pq


if TYPE_CHECKING:
    from redvox.common.timesync import TimeSync


def to_json(timesync: "TimeSync",) -> str:
    """
    :return: timesync as json string
    """
    return json.dumps(timesync.as_dict())


def to_json_file(timesync: "TimeSync",
                 file_name: Optional[str] = None) -> Path:
    """
    saves the timesync as json and data in the same directory.

    :param timesync: TimeSync to save
    :param file_name: the optional base file name.  Do not include a file extension.
                        If None, uses the timesync's file name.
    :return: path to json file
    """
    _file_name: str = (
        file_name
        if file_name is not None
        else timesync.arrow_file
    )
    file_path: Path = Path(timesync.arrow_dir).joinpath(f"{_file_name}.json")
    pq.write_table(timesync.data_as_pyarrow(),
                   Path(timesync.arrow_dir).joinpath(f"{_file_name}.parquet"))
    with open(file_path, "w") as f_p:
        f_p.write(to_json(timesync))
        return file_path.resolve(False)
