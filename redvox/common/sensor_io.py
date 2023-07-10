"""
This module provides IO primitives for working with sensor data.
"""
from pathlib import Path
import json
from typing import (
    Optional,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from redvox.common.sensor_data import SensorData


def to_json(
    sensor: "SensorData",
) -> str:
    """
    :return: sensor as json string
    """
    return json.dumps(sensor.as_dict())


def to_json_file(sensor: "SensorData", file_name: Optional[str] = None) -> Path:
    """
    saves the sensor as json and data in the same directory.

    :param sensor: SensorData to save
    :param file_name: the optional base file name.  Do not include a file extension.
                        If None, a default file name is created using this format:
                        [sensor_type]_[first_timestamp].json
    :return: path to json file
    """
    _file_name: str = file_name if file_name is not None else sensor.file_name()
    file_path: Path = sensor.fs_writer().json_path()
    with open(file_path, "w") as f_p:
        f_p.write(to_json(sensor))
        return file_path.resolve(False)
