"""
Read Redvox data from a single directory
Data files can be either API 900 or API 1000 data formats
The ReadResult object converts api900 data into api 1000 format
"""
from typing import List, Optional, Set, Dict
from datetime import datetime, timedelta

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api900 import reader as api900_io
from redvox.common import api_conversions as ac
from redvox.common import io
from redvox.common.station import Station


DEFAULT_GAP_TIME_S: float = 0.25        # default length of a gap in seconds


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
        index_summary: io.IndexSummary of the filtered data
        gap_time_s: int, minimum amount of seconds between data points to be considered a gap.  Default GAP_TIME_S
        apply_correction: bool, if True, apply timing correction values based on the data in the packets.  Default True
        debug: bool, if True, output additional information during function execution.  Default False.
    """
    def __init__(self, base_dir: str, structured_dir: bool = False, start_dt: Optional[datetime] = None,
                 end_dt: Optional[datetime] = None, start_dt_buf: Optional[timedelta] = None,
                 end_dt_buf: Optional[timedelta] = None, station_ids: Optional[Set[str]] = None,
                 extensions: Optional[Set[str]] = None, api_versions: Optional[Set[io.ApiVersion]] = None,
                 gap_time_s: int = DEFAULT_GAP_TIME_S, apply_timing_correction: bool = True, debug: bool = False):
        """
        Initialize the ApiReader object
        :param base_dir: directory containing the files to read
        :param structured_dir: if True, base_dir contains a specific directory structure used by the respective
                                api formats.  If False, base_dir only has the data files.  Default False.
        :param start_dt: optional starting datetime to filter from.  If None, get all data in base_dir.  Default None
        :param end_dt: optional ending datetime to filter from.  If None, get all data in base_dir.  Default None
        :param start_dt_buf: optional timedelta buffer to combine with start_dt.
                                If None, use the default in io.ReadFilter.  Default None
        :param end_dt_buf: optional timedelta buffer to combine with end_dt.
                            If None, use the default in io.ReadFilter.  Default None
        :param station_ids: optional set of station_ids to filter on.  If None, get all data in base_dir.  Default None
        :param extensions: optional set of file extensions to filter on.  If None, get all data in base_dir.
                            Default None
        :param api_versions: optional set of api versions to filter on.  If None, get all data in base_dir.
                            Default None
        :param gap_time_s: minimum number of seconds between data points to be considered a gap.
                            Default defined as DEFAULT_GAP_TIME_S
        :param apply_timing_correction: if True, adjust timestamps in the resulting WrappedRedvoxPacketM objects
                                        based on the packets' data.  Default True
        :param debug: if True, output additional statements during function execution.  Default False.
        """
        self.filter = io.ReadFilter(start_dt=start_dt, end_dt=end_dt, station_ids=station_ids)
        if start_dt_buf:
            self.filter = self.filter.with_start_dt_buf(start_dt_buf)
        if end_dt_buf:
            self.filter = self.filter.with_end_dt_buf(end_dt_buf)
        if extensions:
            self.filter = self.filter.with_extensions(extensions)
        if api_versions:
            self.filter = self.filter.with_api_versions(api_versions)
        self.base_dir = base_dir
        self.structured_dir = structured_dir
        self.gap_time_s = gap_time_s
        self.apply_correction = apply_timing_correction
        self.debug = debug
        self.files_index = self.get_all_files()
        self.index_summary = io.IndexSummary.from_index(self.files_index)

    def get_all_files(self) -> io.Index:
        """
        get all files in the base dir of the ApiReader
        :return: index with all the files that match the filter
        """
        if self.structured_dir:
            index = io.index_structured(self.base_dir, self.filter)
        else:
            index = io.index_unstructured(self.base_dir, self.filter)
        return index

    def read_files(self) -> Dict[str, List[WrappedRedvoxPacketM]]:
        """
        read the all files in the index
        :return: dictionary of id: list of WrappedRedvoxPacketM, converted from API 900 if necessary
        """
        result: Dict[str, List[WrappedRedvoxPacketM]] = {}
        for path in self.files_index.entries:
            if path.extension == ".rdvxz":
                data = api900_io.wrap(api900_io.read_file(path.full_path, True))
                result[data.redvox_id()].append(ac.convert_api_900_to_1000(data))
            elif path.extension == ".rdvxm":
                data = WrappedRedvoxPacketM.from_compressed_path(path.full_path)
                result[data.get_station_information().get_id()].append(data)
        return result

    def read_files_by_id(self, get_id: str) -> Optional[List[WrappedRedvoxPacketM]]:
        """
        return the files that have the id requested
        :param get_id: the id to filter on
        :return: the list of data with the requested id, or None if the id can't be found
        """
        result: List[WrappedRedvoxPacketM] = []
        for path in self.files_index.entries:
            if path.extension == ".rdvxz":
                data = api900_io.wrap(api900_io.read_file(path.full_path, True))
                if data.redvox_id() == get_id:
                    result.append(ac.convert_api_900_to_1000(data))
            elif path.extension == ".rdvxm":
                data = WrappedRedvoxPacketM.from_compressed_path(path.full_path)
                if data.get_station_information().get_id() == get_id:
                    result.append(data)
        if len(result) == 0:
            return None
        return result

    def get_station_by_id(self, get_id: str) -> Station:
        """
        get a station representation of the data with the requested id
        :param get_id: the id to filter on
        :return: a station containing the data of the packets with the requested id
        """
        return Station(self.read_files_by_id(get_id))
