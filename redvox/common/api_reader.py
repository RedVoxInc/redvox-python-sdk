"""
Read Redvox data from a single directory
Data files can be either API 900 or API 1000 data formats
The ReadResult object converts api900 data into api 1000 format
"""
from collections import defaultdict
from typing import List, Optional, Dict
from datetime import timedelta

import numpy as np

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api900 import reader as api900_io
from redvox.common import api_conversions as ac
from redvox.common import io
from redvox.common import file_statistics as fs
from redvox.common.station import Station


DEFAULT_GAP_TIME_S: float = 0.25  # default length of a gap in seconds


class ApiReader:
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
        files_stats: list of Fs.StationStat for the stations in the filter
        index_summary: io.IndexSummary of the filtered data
        gap_time_s: int, minimum amount of seconds between data points to be considered a gap.  Default GAP_TIME_S
        apply_correction: bool, if True, apply timing correction values based on the data in the packets.  Default True
        debug: bool, if True, output additional information during function execution.  Default False.
    """

    def __init__(
        self,
        base_dir: str,
        structured_dir: bool = False,
        read_filter: io.ReadFilter = None,
        debug: bool = False,
    ):
        """
        Initialize the ApiReader object
        :param base_dir: directory containing the files to read
        :param structured_dir: if True, base_dir contains a specific directory structure used by the respective
                                api formats.  If False, base_dir only has the data files.  Default False.
        :param read_filter: ReadFilter for the data files, if None, get everything.  Default None
        :param debug: if True, output additional statements during function execution.  Default False.
        """
        if read_filter:
            self.filter = read_filter
            if self.filter.station_ids:
                self.filter.station_ids = set(self.filter.station_ids)
        else:
            self.filter = io.ReadFilter()
        self.base_dir = base_dir
        self.structured_dir = structured_dir
        self.debug = debug
        self.files_index = self._get_all_files()
        self.index_summary = io.IndexSummary.from_index(self.files_index)

    def _get_all_files(self) -> io.Index:
        """
        get all files in the base dir of the ApiReader
        :return: index with all the files that match the filter
        """
        # values required:
        # best latency and offset per packet
        # we need the offset for the first and last packet
        # actual time = packet_time + offset
        # real_offset = drift * time_from_start_rec + offset_of_start_rec
        # default offset is 0
        # for confidence: get backfill metric: server_rec_dt - packet_start_dt.  api900 is 2 minutes for backfill
        # database values: id, drift value, offset_station_start
        # check for historic model of known offset slope for each device; create if doesn't exist
        # reference historic model when calculating offset; if device doesn't have values, use the model
        # timing calibration on app set up/background process
        # phone can store its own drift model; send the critical values to the server
        # model confidence metric
        index = io.Index()
        all_index = self._apply_filter()
        for station_id in all_index.summarize().station_ids():
            station_filter = self.filter.clone()
            station_filter = station_filter.with_station_ids({station_id})
            checked_index = self._check_station_stats(station_filter)
            index.append(checked_index.entries)
        return index

    def _apply_filter(self, reader_filter: Optional[io.ReadFilter] = None) -> io.Index:
        """
        apply the filter of the reader, or another filter if specified
        :param reader_filter: optional filter; if None, use the reader's filter, default None
        :return: index of the filtered files
        """
        if not reader_filter:
            reader_filter = self.filter
        if self.structured_dir:
            index = io.index_structured(self.base_dir, reader_filter)
        else:
            index = io.index_unstructured(self.base_dir, reader_filter)
        return index

    def _check_station_stats(self, request_filter: io.ReadFilter) -> io.Index:
        """
        recursively check the filter's results; if resulting index has enough information in it,
        return it, otherwise search for more data.
        The filter should only request one station
        :param request_filter: filter representing the requested information
        :return: Index that includes as much information as possible that fits the request
        """
        index = self._apply_filter(request_filter)
        if len(index.entries) < 1:
            return index
        stats = fs.extract_stats(index)
        if stats[0].packet_duration == 0.0 or not stats[0].packet_duration:
            return index
        # get the model and calculate the revised start and end offsets
        # model = create_model_function
        latencies = [
            st.latency
            for st in stats
            if st.latency is not None and not np.isnan(st.latency)
        ]
        # no latencies means no correction means we're done
        if len(latencies) < 1:
            return index
        i = np.argwhere([st.latency for st in stats] == np.min(latencies))[0][0]
        avg_offset = timedelta(microseconds=stats[i].offset)
        # revise packet's times to real times and compare to requested values
        revised_start = (
            stats[0].packet_start_dt + avg_offset
        )  # model.revised_start_offset
        revised_end = (
            stats[-1].packet_start_dt + stats[-1].packet_duration + avg_offset
        )  # model.revised_end_offset
        if not request_filter.start_dt:
            request_filter = request_filter.with_start_dt(revised_start)
        if not request_filter.end_dt:
            request_filter = request_filter.with_end_dt(revised_end)
        # if our filtered files encompass the request even when the packet times are updated, return the index
        if (not self.filter.start_dt or revised_start <= self.filter.start_dt) and (
            not self.filter.end_dt or revised_end >= self.filter.end_dt
        ):
            return index
        # we have to update our filter to get more information
        new_filter = request_filter.clone()
        # add an extra packet to the filter times value to ensure we don't miss any data
        revised_start = request_filter.start_dt - stats[0].packet_duration
        revised_end = request_filter.end_dt + stats[-1].packet_duration
        # remove the offset so that you have the correct packet times to search for
        new_filter = (
            new_filter.with_start_dt(revised_start - avg_offset)
            .with_start_dt_buf(stats[0].packet_duration)
            .with_end_dt(revised_end - avg_offset)
        )
        idx = self._apply_filter(new_filter)
        sts = fs.extract_stats(idx)
        if (
            revised_start <= self.filter.start_dt
            or sts[0].packet_start_dt == stats[0].packet_start_dt
        ) and (
            revised_end >= self.filter.end_dt
            or sts[-1].packet_start_dt == stats[0].packet_start_dt
        ):
            return idx
        return self._check_station_stats(new_filter)

    def read_files(self) -> Dict[str, List[WrappedRedvoxPacketM]]:
        """
        read the all files in the index
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

    def get_stations(self) -> List[Station]:
        """
        :return: a list of all stations represented by the data packets
        """
        return [Station(packets) for packets in self.read_files().values()]

    def read_files_as_stations(self) -> Dict[str, Station]:
        """
        :return: a dictionary of all station_id to station pairs represented by the data packets
        """
        return {s_id: Station(packets) for s_id, packets in self.read_files().items()}

    def get_station_by_id(self, get_id: str) -> Optional[Station]:
        """
        :param get_id: the id to filter on
        :return: a station containing the data of the packets with the requested id or None if id can't be found
        """
        return Station(self.read_files_by_id(get_id))
