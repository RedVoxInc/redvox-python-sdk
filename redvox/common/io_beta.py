from datetime import timedelta
from typing import Callable, Optional, Set, List
from multiprocessing.pool import Pool

from redvox.common.date_time_utils import datetime_to_epoch_microseconds_utc as dt2us
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc as us2dt
import redvox.common.io as io_py

__INDEX_STRUCTURED_FN: Callable[[str, io_py.ReadFilter, Optional[Pool]], io_py.Index]
__INDEX_UNSTRUCTURED_FN: Callable[
    [str, io_py.ReadFilter, bool, Optional[Pool]], io_py.Index
]


def __into_index_entry_py(entry) -> io_py.IndexEntry:
    return io_py.IndexEntry(
        entry.full_path,
        entry.station_id,
        us2dt(entry.date_time),
        entry.extension,
        io_py.ApiVersion.from_str(entry.api_version),
    )


def __into_index_py(index_native) -> io_py.Index:
    entries: List[io_py.IndexEntry] = list(
        map(__into_index_entry_py, index_native.entries)
    )
    return io_py.Index(entries)


def __map_opt(fn, v):
    if v is None:
        return None
    return fn(v)


def __dur2us(dur: timedelta) -> float:
    return dur.total_seconds() * 1_000_000.0


def __api_native(apis_py: Set[io_py.ApiVersion]) -> Set[str]:
    r: Set[str] = set()
    for api_py in apis_py:
        if api_py == io_py.ApiVersion.API_900:
            r.add("Api900")
            continue
        if api_py == io_py.ApiVersion.API_1000:
            r.add("Api1000")

    return r


try:
    # noinspection PyUnresolvedReferences
    import redvox_native

    def __into_read_filter_native(read_filter: io_py.ReadFilter):
        read_filter_native = redvox_native.ReadFilter()
        read_filter_native.start_dt = __map_opt(dt2us, read_filter.start_dt)
        read_filter_native.end_dt = __map_opt(dt2us, read_filter.end_dt)
        read_filter_native.start_dt_buf = __map_opt(__dur2us, read_filter.start_dt_buf)
        read_filter_native.end_dt_buf = __map_opt(__dur2us, read_filter.end_dt_buf)
        read_filter_native.station_ids = read_filter.station_ids
        read_filter_native.extensions = read_filter.extensions
        read_filter_native.api_versions = __map_opt(
            __api_native, read_filter.api_versions
        )

        return read_filter_native

    def __index_structured_native(
        base_dir: str, read_filter: io_py.ReadFilter, pool: Optional[Pool]
    ) -> io_py.Index:
        read_filter = __into_read_filter_native(read_filter)
        return __into_index_py(redvox_native.index_structured(base_dir, read_filter))

    def __index_unstructured_native(
        base_dir: str,
        read_filter: io_py.ReadFilter,
        sort: bool,
        pool: Optional[Pool],
    ) -> io_py.Index:
        read_filter = __into_read_filter_native(read_filter)
        return __into_index_py(
            redvox_native.index_unstructured(base_dir, read_filter, sort)
        )

    __INDEX_STRUCTURED_FN = __index_structured_native
    __INDEX_UNSTRUCTURED_FN = __index_unstructured_native
except ImportError:
    __INDEX_STRUCTURED_FN = io_py.index_structured
    __INDEX_UNSTRUCTURED_FN = io_py.index_unstructured


def index_structured(
    base_dir: str,
    read_filter: io_py.ReadFilter = io_py.ReadFilter(),
    pool: Optional[Pool] = None,
) -> io_py.Index:
    return __INDEX_STRUCTURED_FN(base_dir, read_filter, pool)


def index_unstructured(
    base_dir: str,
    read_filter: io_py.ReadFilter = io_py.ReadFilter(),
    sort: bool = True,
    pool: Optional[Pool] = None,
):
    return __INDEX_UNSTRUCTURED_FN(base_dir, read_filter, sort, pool)
