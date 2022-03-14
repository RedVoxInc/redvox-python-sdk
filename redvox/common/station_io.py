"""
This module provides IO primitives for working with station data.
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
    from redvox.common.station import Station


def to_json(station: "Station",) -> str:
    """
    :return: station as json string
    """
    return json.dumps(station.as_dict())


def to_json_file(station: "Station",
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

    # ts_dir = os.path.join(station.save_dir(), "timesync")
    os.makedirs(station.timesync_data().arrow_dir, exist_ok=True)
    station.timesync_data().to_json_file()

    # ev_dir = os.path.join(station.save_dir(), "events")
    os.makedirs(station.get_event_data_dir(), exist_ok=True)
    station.event_data().to_json_file(station.get_event_data_dir())

    file_path: Path = Path(station.save_dir()).joinpath(station.fs_writer().json_file_name())
    with open(file_path, "w") as f_p:
        f_p.write(to_json(station))
        return file_path.resolve(False)
