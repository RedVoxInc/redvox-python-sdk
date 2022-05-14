"""
Read Redvox data from a single directory
Data files can be either API 900 or API 1000 data formats
"""
from typing import List, Optional
from datetime import timedelta, datetime
import multiprocessing
import multiprocessing.pool

import pyarrow as pa
import psutil

import redvox.settings as settings
import redvox.api1000.proto.redvox_api_m_pb2 as api_m
from redvox.common import offset_model, io,\
    api_conversions as ac,\
    file_statistics as fs
from redvox.common.parallel_utils import maybe_parallel_map
from redvox.common.station import Station
from redvox.common.errors import RedVoxExceptions


id_py_stct = pa.struct([("id", pa.string()), ("uuid", pa.string()), ("start_time", pa.float64()),
                        ])
meta_py_stct = pa.struct([("api", pa.float64()), ("sub_api", pa.float64()), ("make", pa.string()),
                          ("model", pa.string()), ("os", pa.int64()), ("os_version", pa.string()),
                          ("app", pa.string()), ("app_version", pa.string()), ("is_private", pa.bool_()),
                          ("packet_duration_s", pa.float64()), ("station_description", pa.string()),
                          ])


PERCENT_FREE_MEM_USE = .8  # Percentage of total free memory to use when creating stations (1. is 100%)


class ApiReader:
    """
    Reads data from api 900 or api 1000 format, converting all data read into RedvoxPacketM for
    ease of comparison and use.

    Properties:
        filter: io.ReadFilter with the station ids, start and end time, start and end time padding, and
        types of files to read

        base_dir: str of the directory containing all the files to read

        structured_dir: bool, if True, the base_dir contains a specific directory structure used by the
        respective api formats.  If False, base_dir only has the data files.  Default False.

        files_index: io.Index of the files that match the filter that are in base_dir

        index_summary: io.IndexSummary of the filtered data

        debug: bool, if True, output additional information during function execution.  Default False.
    """

    def __init__(
        self,
        base_dir: str,
        structured_dir: bool = False,
        read_filter: io.ReadFilter = None,
        debug: bool = False,
        pool: Optional[multiprocessing.pool.Pool] = None,
    ):
        """
        Initialize the ApiReader object

        :param base_dir: directory containing the files to read
        :param structured_dir: if True, base_dir contains a specific directory structure used by the respective
                                api formats.  If False, base_dir only has the data files.  Default False.
        :param read_filter: ReadFilter for the data files, if None, get everything.  Default None
        :param debug: if True, output program warnings/errors during function execution.  Default False.
        """
        _pool: multiprocessing.pool.Pool = (
            multiprocessing.Pool() if pool is None else pool
        )

        if read_filter:
            self.filter = read_filter
            if self.filter.station_ids:
                self.filter.station_ids = set(self.filter.station_ids)
        else:
            self.filter = io.ReadFilter()
        self.base_dir = base_dir
        self.structured_dir = structured_dir
        self.debug = debug
        self.errors = RedVoxExceptions("APIReader")
        self.files_index = self._get_all_files(_pool)
        self.index_summary = io.IndexSummary.from_index(self._flatten_files_index())
        if len(self.files_index) > 0:
            mem_split_factor = len(self.files_index) if settings.is_parallelism_enabled() else 1
            self.chunk_limit = psutil.virtual_memory().available * PERCENT_FREE_MEM_USE / mem_split_factor
            max_file_size = max([fe.decompressed_file_size_bytes for fi in self.files_index for fe in fi.entries])
            total_est_size = max_file_size * sum([len(fi.entries) for fi in self.files_index])
            if max_file_size > self.chunk_limit:
                raise MemoryError(f"System requires {max_file_size} bytes of memory to process a file but only has "
                                  f"{self.chunk_limit} available.  Please free or add more RAM.")
            elif total_est_size / mem_split_factor > self.chunk_limit:
                raise MemoryError(f"{total_est_size} of data requested, but only {self.chunk_limit} available; "
                                  f"please reduce the amount of data you are requesting.")
            if debug:
                if mem_split_factor == 1:
                    print(f"{len(self.files_index)} stations have {int(self.chunk_limit)} "
                          f"bytes for loading files in memory.")
                else:
                    print(f"{mem_split_factor} stations each have "
                          f"{int(self.chunk_limit)} bytes for loading files in memory.")
        else:
            self.chunk_limit = 0

        if debug:
            self.errors.print()

        if pool is None:
            _pool.close()

    def _flatten_files_index(self):
        """
        :return: flattened version of files_index
        """
        result = io.Index()
        for i in self.files_index:
            result.append(i.entries)
        return result

    def _get_all_files(
        self, pool: Optional[multiprocessing.pool.Pool] = None
    ) -> List[io.Index]:
        """
        get all files in the base dir of the ApiReader

        :return: index with all the files that match the filter
        """
        _pool: multiprocessing.pool.Pool = (
            multiprocessing.Pool() if pool is None else pool
        )
        index: List[io.Index] = []
        # this guarantees that all ids we search for are valid
        all_index = self._apply_filter(pool=_pool)
        for station_id in all_index.summarize().station_ids():
            id_index = all_index.get_index_for_station_id(station_id)
            checked_index = self._check_station_stats(id_index, pool=_pool)
            index.extend(checked_index)

        if pool is None:
            _pool.close()

        return index

    def _apply_filter(
        self,
        reader_filter: Optional[io.ReadFilter] = None,
        pool: Optional[multiprocessing.pool.Pool] = None,
    ) -> io.Index:
        """
        apply the filter of the reader, or another filter if specified

        :param reader_filter: optional filter; if None, use the reader's filter, default None
        :return: index of the filtered files
        """
        _pool: multiprocessing.pool.Pool = (
            multiprocessing.Pool() if pool is None else pool
        )
        if not reader_filter:
            reader_filter = self.filter
        if self.structured_dir:
            index = io.index_structured(self.base_dir, reader_filter, pool=_pool)
        else:
            index = io.index_unstructured(self.base_dir, reader_filter, pool=_pool)
        if pool is None:
            _pool.close()
        return index

    def _redo_index(self, station_ids: set, new_start: datetime, new_end: datetime):
        """
        Redo the index for files using new start and end dates.  removes any buffer time at the start and end of the
        new query.  Returns the updated index or None

        :param station_ids: set of ids to get
        :param new_start: new start time to get data from
        :param new_end: new end time to get data from
        :return: Updated index or None
        """
        diff_s = diff_e = timedelta(seconds=0)
        new_index = self._apply_filter(io.ReadFilter()
                                       .with_start_dt(new_start)
                                       .with_end_dt(new_end)
                                       .with_extensions(self.filter.extensions)
                                       .with_api_versions(self.filter.api_versions)
                                       .with_station_ids(station_ids)
                                       .with_start_dt_buf(diff_s)
                                       .with_end_dt_buf(diff_e))
        if len(new_index.entries) > 0:
            return new_index
        return None

    def _check_station_stats(
            self,
            station_index: io.Index,
            pool: Optional[multiprocessing.pool.Pool] = None,
    ) -> List[io.Index]:
        """
        check the index's results; if it has enough information, return it, otherwise search for more data.
        The index should only request one station id
        If the station was restarted during the request period, a new group of indexes will be created
        to represent the change in station metadata.

        :param station_index: index representing the requested information
        :return: List of Indexes that includes as much information as possible that fits the request
        """
        _pool: multiprocessing.pool.Pool = multiprocessing.Pool() if pool is None else pool
        # if we found nothing, return the index
        if len(station_index.entries) < 1:
            return [station_index]

        stats = fs.extract_stats(station_index, pool=_pool)
        # Close pool if created here
        if pool is None:
            _pool.close()

        timing_offsets: Optional[offset_model.TimingOffsets] = offset_model.compute_offsets(stats)

        # punt if duration or other important values are invalid or if the latency array was empty
        if timing_offsets is None:
            return [station_index]

        # if our filtered files do not encompass the request even when the packet times are updated
        # try getting 1.5 times the difference of the expected start/end and the start/end of the data
        insufficient_str = ""
        if (self.filter.start_dt and timing_offsets.adjusted_start > self.filter.start_dt) or \
                (self.filter.end_dt and timing_offsets.adjusted_start >= self.filter.end_dt):
            insufficient_str += f" {self.filter.start_dt} (start)"
            new_end = self.filter.start_dt - self.filter.start_dt_buf
            new_start = new_end - 1.5 * (timing_offsets.adjusted_start - self.filter.start_dt)
            new_index = self._redo_index(set(station_index.summarize().station_ids()), new_start, new_end)
            if new_index:
                station_index.append(new_index.entries)
                stats.extend(fs.extract_stats(new_index))

        if (self.filter.end_dt and timing_offsets.adjusted_end < self.filter.end_dt) or \
                (self.filter.start_dt and timing_offsets.adjusted_end <= self.filter.start_dt):
            insufficient_str += f" {self.filter.end_dt} (end)"
            new_start = self.filter.end_dt + self.filter.end_dt_buf
            new_end = new_start + 1.5 * (self.filter.end_dt - timing_offsets.adjusted_end)
            new_index = self._redo_index(set(station_index.summarize().station_ids()), new_start, new_end)
            if new_index:
                station_index.append(new_index.entries)
                stats.extend(fs.extract_stats(new_index))

        if len(insufficient_str) > 0:
            self.errors.append(f"Data for {station_index.summarize().station_ids()} exists, "
                               f"but not at:{insufficient_str}")

        results = {}
        keys = []

        for v, e in enumerate(stats):
            key = e.app_start_dt
            if key not in keys:
                keys.append(key)
                results[key] = io.Index()

            results[key].append(entries=[station_index.entries[v]])

        return list(results.values())

    def _split_workload(self, findex: io.Index) -> List[io.Index]:
        """
        takes an index and splits it into chunks based on a size limit
        while running_total + next_file_size < limit, adds files to a chunk (Index)
        if limit is exceeded, adds the chunk and puts the next file into a new chunk

        :param findex: index of files to split
        :return: list of Index to process
        """
        packet_list = []
        chunk_queue = 0
        chunk_list = []
        for f in findex.entries:
            chunk_queue += f.decompressed_file_size_bytes
            if chunk_queue > self.chunk_limit:
                packet_list.append(io.Index(chunk_list))
                chunk_queue = 0
                chunk_list = []
            chunk_list.append(f)
        packet_list.append(io.Index(chunk_list))
        return packet_list

    @staticmethod
    def read_files_in_index(indexf: io.Index) -> List[api_m.RedvoxPacketM]:
        """
        read all the files in the index

        :return: list of RedvoxPacketM, converted from API 900 if necessary
        """
        result: List[api_m.RedvoxPacketM] = []

        # Iterate over the API 900 packets in a memory efficient way
        # and convert to API 1000
        # noinspection PyTypeChecker
        for packet_900 in indexf.stream_raw(
                io.ReadFilter.empty().with_api_versions({io.ApiVersion.API_900})
        ):
            # noinspection Mypy
            result.append(
                ac.convert_api_900_to_1000_raw(packet_900)
            )

        # Grab the API 1000 packets
        # noinspection PyTypeChecker
        for packet in indexf.stream_raw(
                io.ReadFilter.empty().with_api_versions({io.ApiVersion.API_1000})
        ):
            # noinspection Mypy
            result.append(packet)

        return result

    # noinspection PyTypeChecker
    def read_files_by_id(self, station_id: str) -> Optional[List[api_m.RedvoxPacketM]]:
        """
        :param station_id: the id to filter on
        :return: the list of packets with the requested id, or None if the id can't be found
        """

        result: List[api_m.RedvoxPacketM] = []

        # Iterate over the API 900 packets in a memory efficient way
        # and convert to API 1000
        for packet_900 in self._flatten_files_index().stream_raw(
            io.ReadFilter.empty()
            .with_api_versions({io.ApiVersion.API_900})
            .with_station_ids({station_id})
        ):
            # noinspection Mypy
            result.append(ac.convert_api_900_to_1000_raw(packet_900))

        # Grab the API 1000 packets
        for packet in self._flatten_files_index().stream_raw(
            io.ReadFilter.empty()
            .with_api_versions({io.ApiVersion.API_1000})
            .with_station_ids({station_id})
        ):
            # noinspection Mypy
            result.append(packet)

        if len(result) == 0:
            return None

        return result

    def _station_by_index(self, findex: io.Index) -> Station:
        """
        :param findex: index with files to build a station with
        :return: Station built from files in findex
        """
        return Station.create_from_packets(self.read_files_in_index(findex))

    def get_stations(self, pool: Optional[multiprocessing.pool.Pool] = None) -> List[Station]:
        """
        :param pool: optional multiprocessing pool
        :return: List of all stations in the ApiReader
        """
        return list(maybe_parallel_map(pool,
                                       self._station_by_index,
                                       self.files_index,
                                       chunk_size=1
                                       )
                    )

    def get_station_by_id(self, get_id: str) -> Optional[List[Station]]:
        """
        :param get_id: the id to filter on
        :return: list of all stations with the requested id or None if id can't be found
        """
        result = [s for s in self.get_stations() if s.id() == get_id]
        if len(result) < 1:
            return None
        return result
