"""
For use with DataWindow specifically.  Do NOT use with non-DataWindow objects
Read Redvox data from a single directory
Data files can be either API 900 or API 1000 data formats
"""
from typing import List, Optional
import multiprocessing.pool
import numpy as np

import redvox.settings as settings
from redvox.common import io
from redvox.common.api_reader import ApiReader
from redvox.common.parallel_utils import maybe_parallel_map
from redvox.common.station import Station


class ApiReaderDw(ApiReader):
    """
    For use with DataWindow specifically.  Do NOT use with non-DataWindow objects
    """
    def __init__(self,
                 base_dir: str,
                 structured_dir: bool = False,
                 read_filter: io.ReadFilter = None,
                 correct_timestamps: bool = False,
                 use_model_correction: bool = True,
                 dw_base_dir: str = ".",
                 dw_save_mode: io.FileSystemSaveMode = io.FileSystemSaveMode.TEMP,
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
        :param dw_base_dir: the directory to save DataWindow files to.  if save_mode is FileSystemSaveMode.MEM,
                            this value doesn't matter.  default "." (current directory)
        :param dw_save_mode: save method for the data window.  Default FileSystemSaveMode.TEMP which saves to a temp_dir
        :param debug: if True, output program warnings/errors during function execution.  Default False.
        """
        super().__init__(base_dir, structured_dir, read_filter, debug, pool)
        self.correct_timestamps = correct_timestamps
        self.use_model_correction = use_model_correction
        self.dw_base_dir = dw_base_dir
        self.dw_save_mode = dw_save_mode
        self.all_files_size = np.sum([idx.files_size() for idx in self.files_index])
        self._stations = self._read_stations()

    def _station_by_index(self, findex: io.Index) -> Station:
        """
        builds station using the index of files to read
        splits the index into smaller chunks if entire record cannot be held in memory

        :param findex: index with files to build a station with
        :return: Station built from files in findex, without building the data from parquet
        """
        split_list = self._split_workload(findex)
        use_temp_dir = True if len(split_list) > 1 else False

        if len(split_list) > 0:
            if self.debug and use_temp_dir:
                print("Writing data to disk; this may take a few minutes to complete.")
            stpa = Station.create_from_indexes(split_list,
                                               use_model_correction=self.use_model_correction,
                                               base_out_dir=self.dw_base_dir,
                                               use_temp_dir=use_temp_dir
                                               )
            if self.debug:
                print(f"station {stpa.id()} files read: {len(findex.entries)}")
                if len(split_list) > 1:
                    print(f"required making {len(split_list)} smaller segments due to memory restraints")
            if self.dw_save_mode == io.FileSystemSaveMode.MEM and use_temp_dir:
                self.dw_save_mode = io.FileSystemSaveMode.TEMP
            if self.correct_timestamps:
                stpa.set_correct_timestamps()
            return stpa
        self.errors.append("No files found to create station.")
        return Station()

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
        if settings.is_parallelism_enabled() and len(self.files_index) > 1:
            return list(maybe_parallel_map(pool, self._station_by_index,
                                           self.files_index,
                                           chunk_size=1
                                           ))
        return list(map(self._station_by_index, self.files_index))

    def get_station_by_id(self, get_id: str) -> Optional[List[Station]]:
        """
        :param get_id: the id to filter on
        :return: list of all stations with the requested id or None if id can't be found
        """
        result = [s for s in self._stations if s.id() == get_id]
        if len(result) < 1:
            return None
        return result
