from typing import Callable, Optional
from multiprocessing.pool import Pool

import redvox.common.io as io_py

INDEX_STRUCTURED_FN: Callable[[str, Optional[io_py.ReadFilter], Optional[Pool]], io_py.Index]
INDEX_UNSTRUCTURED_FN: Callable[[str, Optional[io_py.ReadFilter], Optional[bool], Optional[Pool]], io_py.Index]


def __into_read_filter_native(read_filter):
    pass


def __into_index_entry_py(index_entry) -> io_py.IndexEntry:
    pass


def __into_index_py(index) -> io_py.Index:
    pass


try:
    import redvox_native


    def __index_structured_native(base_dir: str, read_filter: Optional[io_py.ReadFilter],
                                  pool: Optional[Pool]) -> io_py.Index:
        read_filter = __into_read_filter_native(read_filter)
        return __into_index_py(redvox_native.index_structured(base_dir, read_filter))


    def __index_unstructured_native(base_dir: str, read_filter: Optional[io_py.ReadFilter], sort: Optional[bool],
                                    pool: Optional[Pool]) -> io_py.Index:
        read_filter = __into_read_filter_native(read_filter)
        return __into_index_py(redvox_native.index_unstructured(base_dir, read_filter, sort))


    INDEX_STRUCTURED_FN = __index_structured_native
    INDEX_UNSTRUCTURED_FN = __index_unstructured_native
except ImportError:
    INDEX_STRUCTURED_FN = io_py.index_structured
    INDEX_UNSTRUCTURED_FN = io_py.index_unstructured


def index_structured(base_dir: str, read_filter: Optional[io_py.ReadFilter],
                     pool: Optional[Pool] = None) -> io_py.Index:
    return INDEX_STRUCTURED_FN(base_dir, read_filter, pool)


def index_unstructured(base_dir: str,
                       read_filter: Optional[io_py.ReadFilter],
                       sort: Optional[bool] = False,
                       pool: Optional[Pool] = None):
    return INDEX_UNSTRUCTURED_FN(base_dir, read_filter, sort, pool)
