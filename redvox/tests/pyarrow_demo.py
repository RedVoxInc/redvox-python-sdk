import os
import timeit
import pickle

from redvox.common.data_window import DataWindow
from redvox.common import data_window_wpa as dwpa


# def print_station_stats(stations: list):
#     for og in stations:
#         print(og.first_data_timestamp)
#         print(og.last_data_timestamp)
#         print(og.audio_sensor().num_samples())
#         og.errors.print()
#         ppd = pickle.dumps(og).__sizeof__()
#         print(ppd)


def demo():
    # settings.set_parallelism_enabled(True)
    path = "/Users/tyler/Documents/skyfall2full/"
    save_path10 = "/Users/tyler/Documents/pyarrowreadertest/large_test"

    dw_config = dwpa.DataWindowConfigWpa(path,
                                         structured_layout=True,
                                         )

    s = timeit.default_timer()
    dwa = dwpa.DataWindowArrow("small_test_no_save", config=dw_config, out_type=dwpa.DataWindowOutputType["NONE"])
    e = timeit.default_timer()
    print("nosave", e-s)

    s = timeit.default_timer()
    dwaz = dwpa.DataWindowArrow("large_test_lz4", config=dw_config, out_dir=save_path10,
                                out_type=dwpa.DataWindowOutputType["LZ4"]
                                )
    e = timeit.default_timer()
    print("lz4", e-s)
    dwaz.save()

    s = timeit.default_timer()
    drws = dwpa.DataWindowArrow("large_test", config=dw_config, out_dir=save_path10,
                                out_type=dwpa.DataWindowOutputType["PARQUET"]
                                )
    e = timeit.default_timer()
    print("parquet", e-s)
    drws.save()

    s = timeit.default_timer()
    drws = dwpa.DataWindowArrow.from_json_file(save_path10, "large_test")
    e = timeit.default_timer()
    print("load parquet", e-s)

    s = timeit.default_timer()
    dwaz = dwpa.DataWindowArrow.deserialize(os.path.join(save_path10, "large_test_lz4.pkl.lz4"))
    e = timeit.default_timer()
    print("load lz4", e-s)

    print("size of lz4:     ", pickle.dumps(dwaz).__sizeof__())
    print("size of nosave:  ", pickle.dumps(dwa).__sizeof__())
    print("size of parquet: ", pickle.dumps(drws).__sizeof__())


if __name__ == "__main__":
    demo()
