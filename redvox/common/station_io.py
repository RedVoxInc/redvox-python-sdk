"""
This module provides IO primitives for working with station data.
"""
from pathlib import Path
import json
import os
from typing import (
    Dict,
    Optional,
    TYPE_CHECKING,
)


if TYPE_CHECKING:
    from redvox.common.station_wpa import StationPa


def to_json(station: "StationPa",) -> str:
    """
    :return: station as json string
    """
    return json.dumps(station.as_dict())


def to_json_file(station: "StationPa",
                 file_name: Optional[str] = None) -> Path:
    """
    saves the station as json and data in the same directory.

    :param station: Station to save
    :param file_name: the optional base file name.  Do not include a file extension.
                        If None, uses the default [id]_[startdate].json
    :return: path to json file
    """
    _file_name: str = (
        file_name
        if file_name is not None
        else station.default_station_json_file_name()
    )

    # write the sensor objects, using the default values
    for datas in station.data():
        datas.to_json_file()

    ts_dir = os.path.join(station.save_dir(), "timesync")
    os.makedirs(ts_dir, exist_ok=True)
    station.timesync_data().to_json_file()

    file_path: Path = Path(station.save_dir()).joinpath(station.fs_writer().json_file_name())
    with open(file_path, "w") as f_p:
        f_p.write(to_json(station))
        return file_path.resolve(False)


def from_json(file_path: str) -> Dict:
    """
    convert contents of json file to Station dictionary

    :param file_path: full path of file to load data from.
    :return: Dictionary of Station
    """
    with open(file_path, "r") as f_p:
        return json.loads(f_p.read())
