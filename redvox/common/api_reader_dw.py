"""
Read Redvox data from a single directory
Data files can be either API 900 or API 1000 data formats
"""
from typing import List, Optional
import multiprocessing.pool

import redvox.settings as settings
from redvox.common import io
from redvox.common.api_reader import ApiReader
from redvox.common.parallel_utils import maybe_parallel_map
from redvox.common.station import Station


class ApiReaderDw(ApiReader):
    def __init__(self,
                 base_dir: str,
                 structured_dir: bool = False,
                 read_filter: io.ReadFilter = None,
                 correct_timestamps: bool = False,
                 use_model_correction: bool = True,
                 dw_base_dir: str = ".",
                 save_files: bool = False,
                 debug: bool = False,
                 pool: Optional[multiprocessing.pool.Pool] = None):
        """
        initialize API reader for data window

        :param base_dir: directory containing the files to read
        :param structured_dir: if True, base_dir contains a specific directory structure used by the respective
                                api formats.  If False, base_dir only has the data files.  Default False.
        :param read_filter: ReadFilter for the data files, if None, get everything.  Default None
        :param correct_timestamps: if True, correct the timestamps of the data.  Default False
        :param use_model_correction: if True, use the offset model of the station to correct the timestamps.
                                        if correct_timestamps is False, this value doesn't matter.  Default True
        :param dw_base_dir: the directory to save DataWindow files to.  if save_files is False, this value doesn't
                            matter.  default "." (current directory)
        :param save_files: if True, save the data.  Default False
        :param debug: if True, output program warnings/errors during function execution.  Default False.
        """
        super().__init__(base_dir, structured_dir, read_filter, debug, pool)
        self.correct_timestamps = correct_timestamps
        self.use_model_correction = use_model_correction
        self.dw_base_dir = dw_base_dir
        self.save_files = save_files
        self._stations = self._read_stations()

    def _stations_by_index(self, findex: io.Index) -> Station:
        """
        :param findex: index with files to build a station with
        :return: Station built from files in findex, without building the data from parquet
        """
        stpa = Station.create_from_packets(self.read_files_in_index(findex), self.correct_timestamps,
                                           self.use_model_correction, self.dw_base_dir, self.save_files)
        if self.debug:
            print(f"station {stpa.id()} files read: {len(findex.entries)}")
        return stpa

    def get_stations(self, pool: Optional[multiprocessing.pool.Pool] = None) -> List[Station]:
        """
        :return: a list of stations read by the ApiReader
        """
        return self._stations

    def _read_stations(self, pool: Optional[multiprocessing.pool.Pool] = None) -> List[Station]:
        """
        :param pool: optional multiprocessing pool
        :return: List of all stations in the ApiReader, without building the data from parquet
        """
        if settings.is_parallelism_enabled():
            return list(maybe_parallel_map(pool, self._stations_by_index,
                                           self.files_index,
                                           chunk_size=1
                                           ))
        return list(map(self._stations_by_index, self.files_index))

    def get_station_by_id(self, get_id: str) -> Optional[List[Station]]:
        """
        :param get_id: the id to filter on
        :return: list of all stations with the requested id or None if id can't be found
        """
        result = [s for s in self._stations if s.id() == get_id]
        if len(result) < 1:
            return None
        return result
