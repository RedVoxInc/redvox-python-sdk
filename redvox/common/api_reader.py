"""
Read Redvox data from a single directory
Data files can be either API 900 or API 1000 data formats
"""
from typing import List, Optional
from datetime import timedelta
import multiprocessing
import multiprocessing.pool
from itertools import repeat
from multiprocessing import cpu_count, Manager, Process, Queue
import queue

import pyarrow as pa

import redvox.settings as settings
import redvox.api1000.proto.redvox_api_m_pb2 as api_m
from redvox.common import offset_model
from redvox.common import api_conversions as ac
from redvox.common import io
from redvox.common import file_statistics as fs
from redvox.common.parallel_utils import maybe_parallel_map
from redvox.common.station import Station
from redvox.common.station_wpa import StationPa
from redvox.common.errors import RedVoxExceptions


id_py_stct = pa.struct([("id", pa.string()), ("uuid", pa.string()), ("start_time", pa.float64()),
                        ])
meta_py_stct = pa.struct([("api", pa.float64()), ("sub_api", pa.float64()), ("make", pa.string()),
                          ("model", pa.string()), ("os", pa.int64()), ("os_version", pa.string()),
                          ("app", pa.string()), ("app_version", pa.string()), ("is_private", pa.bool_()),
                          ("packet_duration_s", pa.float64()), ("station_description", pa.string()),
                          ])


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
        :param debug: if True, output additional statements during function execution.  Default False.
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

        diff_s = diff_e = timedelta(seconds=0)

        # if our filtered files do not encompass the request even when the packet times are updated
        # try getting 1.5 times the difference of the expected start/end and the start/end of the data
        insufficient_str = ""
        if self.filter.start_dt and timing_offsets.adjusted_start > self.filter.start_dt:
            insufficient_str += f" {self.filter.start_dt} (start)"
            # diff_s = self.filter.start_dt_buf + 1.5 * (timing_offsets.adjusted_start - self.filter.start_dt)
            new_end = self.filter.start_dt - self.filter.start_dt_buf
            new_start = new_end - 1.5 * (timing_offsets.adjusted_start - self.filter.start_dt)
            new_index = self._apply_filter(io.ReadFilter()
                                           .with_start_dt(new_start)
                                           .with_end_dt(new_end)
                                           .with_extensions(self.filter.extensions)
                                           .with_api_versions(self.filter.api_versions)
                                           .with_station_ids(set(station_index.summarize().station_ids()))
                                           .with_start_dt_buf(diff_s)
                                           .with_end_dt_buf(diff_e))
            if len(new_index.entries) > 0:
                station_index.append(new_index.entries)
                stats.extend(fs.extract_stats(new_index))
        if self.filter.end_dt and timing_offsets.adjusted_end < self.filter.end_dt:
            insufficient_str += f" {self.filter.end_dt} (end)"
            # diff_e = self.filter.end_dt_buf + 1.5 * (self.filter.end_dt - timing_offsets.adjusted_end)
            new_start = self.filter.end_dt + self.filter.end_dt_buf
            new_end = new_start + 1.5 * (self.filter.end_dt - timing_offsets.adjusted_end)
            new_index = self._apply_filter(io.ReadFilter()
                                           .with_start_dt(new_start)
                                           .with_end_dt(new_end)
                                           .with_extensions(self.filter.extensions)
                                           .with_api_versions(self.filter.api_versions)
                                           .with_station_ids(set(station_index.summarize().station_ids()))
                                           .with_start_dt_buf(diff_s)
                                           .with_end_dt_buf(diff_e))
            if len(new_index.entries) > 0:
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

    def _stations_by_index(self, findex: io.Index) -> Station:
        """
        :param findex: index with files to build a station with
        :return: Station built from files in findex
        """
        return Station(self.read_files_in_index(findex))

    def get_stations(self, pool: Optional[multiprocessing.pool.Pool] = None) -> List[Station]:
        """
        :param pool: optional multiprocessing pool
        :return: List of all stations in the ApiReader
        """
        return list(maybe_parallel_map(pool,
                                       self._stations_by_index,
                                       self.files_index,
                                       chunk_size=1
                                       )
                    )

    def get_station_by_id(self, get_id: str) -> Optional[List[Station]]:
        """
        :param get_id: the id to filter on
        :return: list of all stations with the requested id or None if id can't be found
        """
        result = [s for s in self.get_stations() if s.id == get_id]
        if len(result) < 1:
            return None
        return result

    def _stations_wpa_by_index_fs(self, findex: io.Index, correct_timestamps: bool = False,
                                  use_model_correction: bool = True,
                                  base_dir: str = "", save_files: bool = False) -> StationPa:
        """
        :param findex: index with files to build a station with
        :param correct_timestamps: if True, correct timestamps as soon as they're available.  Default False
        :param use_model_correction: if True, use OffsetModel functions for time correction, add OffsetModel
                                        best offset (intercept value) otherwise.  Default True
        :param base_dir: base directory to write data parquet files to.  Default "" (current directory)
        :param save_files: if True, save files to disk, otherwise delete when finished.  Default False
        :return: Station built from files in findex, without building the data from parquet
        """
        stpa = StationPa.create_from_packets(self.read_files_in_index(findex), correct_timestamps,
                                             use_model_correction, base_dir, save_files)
        return stpa

    def download_process(self, input_queue: Queue, result_queue: Queue, correct_timestamps: bool = False,
                         use_model_correction: bool = True, base_dir: str = "", save_files: bool = False
                         ) -> None:
        """
        A function that runs in a separate process for creating stations.
        :param input_queue: A shared queue containing the list of items to be downloaded.
        :param result_queue: A queue used to send results from the process to the caller.
        :param correct_timestamps: if True, correct timestamps as soon as they're available.  Default False
        :param use_model_correction: if True, use OffsetModel functions for time correction, add OffsetModel
                                        best offset (intercept value) otherwise.  Default True
        :param base_dir: base directory to write data parquet files to.  Default "" (current directory)
        :param save_files: if True, save files to disk, otherwise delete when finished.  Default False
        """
        try:
            # While there is still data in the queue, retrieve it.
            while True:
                files_index = input_queue.get_nowait()
                try:
                    st = StationPa.create_from_packets(self.read_files_in_index(files_index), correct_timestamps,
                                                       use_model_correction, base_dir, save_files)
                    result_queue.put(st, True, None)
                except FileExistsError:
                    print(f"File already exists, skipping...")
                    continue
        # Thrown when the queue is empty
        except queue.Empty:
            return

    def download_files(self, num_processes: int = cpu_count(), correct_timestamps: bool = False,
                       use_model_correction: bool = True, base_dir: str = "", save_files: bool = False):
        """
        Create stations in parallel.
        :param num_processes: Number of processes to create for downloading data.
        :param correct_timestamps: if True, correct timestamps as soon as possible, default False
        :param use_model_correction: if True, use OffsetModel functions for time correction, add OffsetModel
                                        best offset (intercept value) otherwise.  Default True
        :param base_dir: base directory to write data parquet files to.  Default "" (current directory)
        :param save_files: if True, save files to disk, otherwise delete when finished.  Default False
        """
        manager: Manager = Manager()
        station_queue: Queue = manager.Queue(len(self.files_index))
        result_queue: Queue = manager.Queue(len(self.files_index))
        processes: List[Process] = []

        # Add all URLs to shared queue
        for findex in self.files_index:
            station_queue.put(findex)

        # Create the process pool
        for _ in range(num_processes):
            process: Process = Process(
                target=self.download_process, args=(station_queue, result_queue, correct_timestamps,
                                                    use_model_correction, base_dir, save_files)
            )
            processes.append(process)
            process.start()

        # Wait for all processes in pool to finish
        for process in processes:
            process.join()

        result = []
        try:
            while True:
                x = result_queue.get_nowait()
                result.append(x)
        except queue.Empty:
            return result

    def get_stations_wpa_fs(self,
                            # pool: Optional[multiprocessing.pool.Pool] = None,
                            correct_timestamps: bool = False,
                            use_model_correction: bool = True,
                            base_dir: str = "", save_files: bool = False) -> List[StationPa]:
        """
        # :param pool: optional multiprocessing pool
        :param correct_timestamps: if True, correct timestamps as soon as possible, default False
        :param use_model_correction: if True, use OffsetModel functions for time correction, add OffsetModel
                                        best offset (intercept value) otherwise.  Default True
        :param base_dir: base directory to write data parquet files to.  Default "" (current directory)
        :param save_files: if True, save files to disk, otherwise delete when finished.  Default False
        :return: List of all stations in the ApiReader, without building the data from parquet
        """
        # return list(maybe_parallel_smap(pool,
        #                                 self._stations_wpa_by_index_fs,
        #                                 [self.files_index, repeat(base_dir), repeat(save_files)],
        #                                 chunk_size=1
        #                                 )
        #             )
        if settings.is_parallelism_enabled():
            return self.download_files(correct_timestamps=correct_timestamps,
                                       use_model_correction=use_model_correction,
                                       base_dir=base_dir, save_files=save_files)
        return list(map(self._stations_wpa_by_index_fs, self.files_index, repeat(correct_timestamps),
                        repeat(use_model_correction), repeat(base_dir), repeat(save_files)))

    def _stations_wpa_by_index(self, findex: io.Index) -> StationPa:
        """
        :param findex: index with files to build a station with
        :return: Station built from files in findex
        """
        stpa = StationPa.create_from_packets(self.read_files_in_index(findex))
        return stpa

    def get_stations_wpa(self, pool: Optional[multiprocessing.pool.Pool] = None) -> List[StationPa]:
        """
        :param pool: optional multiprocessing pool
        :return: List of all stations in the ApiReader
        """
        return list(maybe_parallel_map(pool,
                                       self._stations_wpa_by_index,
                                       self.files_index,
                                       chunk_size=1
                                       )
                    )

    def get_station_wpa_by_id(self, get_id: str) -> Optional[List[StationPa]]:
        """
        :param get_id: the id to filter on
        :return: list of all stations with the requested id or None if id can't be found
        """
        result = [s for s in self.get_stations_wpa() if s.get_id() == get_id]
        if len(result) < 1:
            return None
        return result
