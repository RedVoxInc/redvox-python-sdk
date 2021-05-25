"""
Read Redvox data from a single directory
Data files can be either API 900 or API 1000 data formats
The ReadResult object converts api900 data into api 1000 format
"""
from collections import defaultdict
from typing import List, Optional, Dict, Iterator
from datetime import timedelta
import multiprocessing
import multiprocessing.pool

import numpy as np

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.common import offset_model
from redvox.common import api_conversions as ac
from redvox.common import io
from redvox.common import file_statistics as fs
from redvox.common.parallel_utils import maybe_parallel_map
from redvox.common.station import Station


class ApiReaderOld:
    """
    Reads data from api 900 or api 1000 format, converting all data read into WrappedRedvoxPacketM for
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
        self.files_index = self._get_all_files(_pool)
        self.index_summary = io.IndexSummary.from_index(self.files_index)

        if pool is None:
            _pool.close()

    def _get_all_files(
        self, pool: Optional[multiprocessing.pool.Pool] = None
    ) -> io.Index:
        """
        get all files in the base dir of the ApiReader
        :return: index with all the files that match the filter
        """
        _pool: multiprocessing.pool.Pool = (
            multiprocessing.Pool() if pool is None else pool
        )
        index = io.Index()
        # this guarantees that all ids we search for are valid
        all_index = self._apply_filter(pool=_pool)
        for station_id in all_index.summarize().station_ids():
            station_filter = self.filter.clone()
            checked_index = self._check_station_stats(
                station_filter.with_station_ids({station_id}),
                pool=_pool
            )
            index.append(checked_index.entries)

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
        request_filter: io.ReadFilter,
        pool: Optional[multiprocessing.pool.Pool] = None,
    ) -> io.Index:
        """
        recursively check the filter's results; if resulting index has enough information in it,
        return it, otherwise search for more data.
        The filter should only request one station
        :param request_filter: filter representing the requested information
        :return: Index that includes as much information as possible that fits the request
        """
        _pool: multiprocessing.pool.Pool = multiprocessing.Pool() if pool is None else pool
        index = self._apply_filter(request_filter)
        # if there are no restrictions on time or we found nothing, return the index
        if (
            (not self.filter.start_dt and not self.filter.end_dt)
            or (not request_filter.start_dt and not request_filter.end_dt)
            or len(index.entries) < 1
        ):
            return index
        stats = fs.extract_stats(index, pool=_pool)
        # Close pool if created here
        if pool is None:
            _pool.close()

        timing_offsets: Optional[offset_model.TimingOffsets] = offset_model.compute_offsets(stats)

        # punt if duration or other important values are invalid or if the latency array was empty
        if timing_offsets is None:
            return index

        # if our filtered files encompass the request even when the packet times are updated, return the index
        if (not self.filter.start_dt or timing_offsets.adjusted_start <= self.filter.start_dt) and (
            not self.filter.end_dt or timing_offsets.adjusted_end >= self.filter.end_dt
        ):
            return index
        # we have to update our filter to get more information
        new_filter = request_filter.clone()
        no_more_start = True
        no_more_end = True
        # check if there is a packet just beyond the request times
        if self.filter.start_dt and timing_offsets.adjusted_start > self.filter.start_dt:
            beyond_start = (
                self.filter.start_dt - np.abs(timing_offsets.start_offset) - stats[0].packet_duration
            )
            start_filter = (
                request_filter.clone()
                .with_start_dt(beyond_start)
                .with_end_dt(stats[0].packet_start_dt)
                .with_end_dt_buf(timedelta(seconds=0))
            )
            start_index = self._apply_filter(start_filter)
            # if the beyond check produces an earlier start date time,
            #  then update filter, otherwise flag result as no more data to obtain
            if (
                len(start_index.entries) > 0
                and start_index.entries[0].date_time < index.entries[0].date_time
            ):
                new_filter.with_start_dt(beyond_start)
                no_more_start = False
        if self.filter.end_dt and timing_offsets.adjusted_end < self.filter.end_dt:
            beyond_end = self.filter.end_dt + np.abs(timing_offsets.end_offset)
            end_filter = (
                request_filter.clone()
                .with_start_dt(stats[-1].packet_start_dt + stats[-1].packet_duration)
                .with_end_dt(beyond_end)
                .with_start_dt_buf(timedelta(seconds=0))
            )
            end_index = self._apply_filter(end_filter)
            # if the beyond check produces a later end date time,
            #  then update filter, otherwise flag result as no more data to obtain
            if (
                len(end_index.entries) > 0
                and end_index.entries[-1].date_time > index.entries[-1].date_time
            ):
                new_filter.with_end_dt(beyond_end)
                no_more_end = False
        # if there is no more data to obtain from either end, return the original index
        if no_more_start and no_more_end:
            return index
        # check the updated index
        _pool = multiprocessing.Pool() if pool is None else pool
        ret = self._check_station_stats(new_filter, pool=_pool)
        if pool is None:
            _pool.close()
        return ret

    def read_files(self) -> Dict[str, List[WrappedRedvoxPacketM]]:
        """
        read all the files in the index
        :return: dictionary of id: list of WrappedRedvoxPacketM, converted from API 900 if necessary
        """
        result: Dict[str, List[WrappedRedvoxPacketM]] = defaultdict(list)

        # Iterate over the API 900 packets in a memory efficient way
        # and convert to API 1000
        # noinspection PyTypeChecker
        for packet_900 in self.files_index.stream(
            io.ReadFilter.empty().with_api_versions({io.ApiVersion.API_900})
        ):
            # noinspection Mypy
            result[packet_900.redvox_id()].append(
                ac.convert_api_900_to_1000(packet_900)
            )

        # Grab the API 1000 packets
        # noinspection PyTypeChecker
        for packet in self.files_index.stream(
            io.ReadFilter.empty().with_api_versions({io.ApiVersion.API_1000})
        ):
            # noinspection Mypy
            result[packet.get_station_information().get_id()].append(packet)

        return result

    # noinspection PyTypeChecker
    def read_files_by_id(self, get_id: str) -> Optional[List[WrappedRedvoxPacketM]]:
        """
        :param get_id: the id to filter on
        :return: the list of packets with the requested id, or None if the id can't be found
        """

        result: List[WrappedRedvoxPacketM] = []

        # Iterate over the API 900 packets in a memory efficient way
        # and convert to API 1000
        for packet_900 in self.files_index.stream(
            io.ReadFilter.empty()
            .with_api_versions({io.ApiVersion.API_900})
            .with_station_ids({get_id})
        ):
            # noinspection Mypy
            result.append(ac.convert_api_900_to_1000(packet_900))

        # Grab the API 1000 packets
        for packet in self.files_index.stream(
            io.ReadFilter.empty()
            .with_api_versions({io.ApiVersion.API_1000})
            .with_station_ids({get_id})
        ):
            # noinspection Mypy
            result.append(packet)

        if len(result) == 0:
            return None

        return result

    def get_stations(
        self, pool: Optional[multiprocessing.pool.Pool] = None
    ) -> List[Station]:
        """
        :return: a list of all stations represented by the data packets
        """
        station_ids: List[str] = self.index_summary.station_ids()
        stations_opt: Iterator[Optional[Station]] = maybe_parallel_map(
            pool,
            self.get_station_by_id,
            iter(station_ids),
            lambda: len(station_ids) > 2,
            chunk_size=1
        )
        # _pool: multiprocessing.pool.Pool = (
        #     multiprocessing.Pool() if pool is None else pool
        # )
        #
        # stations_opt: List[Optional[Station]] = _pool.map(
        #     self.get_station_by_id, station_ids
        # )
        # if pool is None:
        #     _pool.close()
        # noinspection Mypy
        return list(filter(lambda station: station is not None, stations_opt))

    def read_files_as_stations(
        self, pool: Optional[multiprocessing.pool.Pool] = None
    ) -> Dict[str, Station]:
        """
        :return: a dictionary of all station_id to station pairs represented by the data packets
        """
        _pool: multiprocessing.pool.Pool = (
            multiprocessing.Pool() if pool is None else pool
        )
        stations: List[Station] = self.get_stations(pool=_pool)
        if pool is None:
            _pool.close()
        return {station.id: station for station in stations}

    def get_station_by_id(self, get_id: str) -> Optional[Station]:
        """
        :param get_id: the id to filter on
        :return: a station containing the data of the packets with the requested id or None if id can't be found
        """
        return Station(self.read_files_by_id(get_id))
