import os
import timeit
import pickle
from pathlib import Path

from redvox.common import data_window as dw


def demo():
    # settings.set_parallelism_enabled(True)
    path = "/Users/tyler/Documents/skyfall2full/"
    save_path10 = "/Users/tyler/Documents/pyarrowreadertest/large_test"

    dw_config = dw.DataWindowConfig(path, structured_layout=True)

    s = timeit.default_timer()
    dwa = dw.DataWindow("small_test_no_save", config=dw_config, out_type="NONE")
    e = timeit.default_timer()
    print("nosave", e-s)

    s = timeit.default_timer()
    dwaz = dw.DataWindow("large_test_lz4", config=dw_config, output_dir=save_path10, out_type="LZ4")
    e = timeit.default_timer()
    print("lz4", e-s)
    dwaz.save()

    s = timeit.default_timer()
    drws = dw.DataWindow("large_test", config=dw_config, output_dir=save_path10, out_type="PARQUET")
    e = timeit.default_timer()
    print("parquet", e-s)
    drws.save()

    s = timeit.default_timer()
    drws = dw.DataWindow.load(os.path.join(save_path10, "large_test.json"))
    e = timeit.default_timer()
    print("load parquet", e-s)

    s = timeit.default_timer()
    dwaz = dw.DataWindow.deserialize(os.path.join(save_path10, "large_test_lz4.pkl.lz4"))
    e = timeit.default_timer()
    print("load lz4", e-s)

    print("memory used by lz4:     ", pickle.dumps(dwaz).__sizeof__())
    print("memory used by nosave:  ", pickle.dumps(dwa).__sizeof__())
    print("memory used by parquet: ", pickle.dumps(drws).__sizeof__())

    total_size = 0
    for f in Path(save_path10).rglob('*.parquet'):
        total_size += os.path.getsize(f)
    print(f"size of parquet on disk: {total_size} B")
    print(f"size of lz4 on disk:     {os.path.getsize(os.path.join(save_path10, 'large_test_lz4.pkl.lz4'))} B")


if __name__ == "__main__":
    demo()
