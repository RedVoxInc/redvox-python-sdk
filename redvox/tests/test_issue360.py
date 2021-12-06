import shutil
import os
from pathlib import Path
from redvox.common import data_window_wpa as dwpa


def main():
    # ['1637199002', '1637610029',
    # '1637662003', '1637610028',
    # '1637110701', '1637199003']
    path = "/Users/yusukehatanaka/Desktop/DATA/20200222_GoodComms/"
    # path = "/Users/yusukehatanaka/Desktop/DATA/20201006_SPX_F9" # throws error
    # path = "/Users/yusukehatanaka/Desktop/DATA/20201027_SDK_Example/"
    # path = "/Users/yusukehatanaka/Desktop/DATA/20180824_Hurricane_Lane"

    save_path = "/Users/yusukehatanaka/Desktop/DATA/issue_360/"
    if os.path.exists(save_path):
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
    # print(file_bytes)

    # print(drws.station_ids())
    for station in drws.station_ids():
        sample_rate = drws.get_station(station)[0].audio_sample_rate_nominal_hz()
        folder_per_station = [filename for filename in os.listdir(save_path) if filename.startswith(f"{station}")]
        print(
            f"station_id: {station}, " +
            f"num_bytes: {folder_size(save_path + folder_per_station[0])/1000} KB, " +
            f"SR: {sample_rate}"
        )


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
