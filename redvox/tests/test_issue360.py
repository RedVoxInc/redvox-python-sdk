from redvox.common.api_reader import ApiReader
from redvox.common.data_window import DataWindow
import shutil
from time import time
import os
from os import listdir
from os.path import isfile, join
import numpy as np
from pathlib import Path

from redvox.common import data_window_wpa as dwpa
from redvox.common import data_window_io as dw_io


def main():
    """
    input_dir = "/Users/yusukehatanaka/Desktop/DATA/20200222_GoodComms/"
    dw = DataWindow(
        input_dir=input_dir,
    )
    stations = dw.station_ids
    print(stations)

    for station in stations:
        print(f"processing {station}")
        _ = DataWindow(
            input_dir=input_dir,
            station_ids=[station]
        )
        print('==================================')
    """
    # ['1637199002', '1637610029',
    # '1637662003', '1637610028',
    # '1637110701', '1637199003']
    path = "/Users/yusukehatanaka/Desktop/DATA/20200222_GoodComms/"
    save_path = "/Users/yusukehatanaka/Desktop/DATA/issue_360/"
    if os.path.exists(save_path):
        # os.rmdir(save_path)
        shutil.rmtree(save_path)
    os.mkdir(save_path)
    dw_config = dwpa.DataWindowConfigWpa(
        input_dir=path
    )

    drws = dwpa.DataWindowArrow(
        "single_station_no_save",
        config=dw_config,
        out_dir=save_path,
        out_type="PARQUET"
    )
    drws.save()
    file_bytes = sum(file.stat().st_size for file in Path(save_path).rglob('*'))
    print(file_bytes)

    print(drws.station_ids())
    for station in drws.station_ids():
        sample_rate = drws.get_station(station)[0].audio_sample_rate_nominal_hz()
        print(f"station: {station}, SR: {sample_rate}")

    print(folder_size(save_path))


def folder_size(path='.'):
    total = 0
    for entry in os.scandir(path):
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir():
            total += folder_size(entry.path)
    return total


if __name__ == '__main__':
    main()
