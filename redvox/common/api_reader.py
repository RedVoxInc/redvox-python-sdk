"""
Read Redvox data from a single directory
Data files can be either API 900 or API 1000 data formats
The ReadResult object converts api900 data into api 1000 format
"""
from typing import List, Optional

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api900 import reader as api900_io
from redvox.common import api_conversions as ac
from redvox.common import io


class ApiReader:
    def __init__(self, read_filter: io.ReadFilter, base_dir: str, structured_dir: bool = False):
        self.filter = read_filter
        self.base_dir = base_dir
        self.structured_dir = structured_dir
        self.files_index = self.get_all_files()

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

    def read_files(self) -> List[WrappedRedvoxPacketM]:
        """
        read the files in the index of all files
        :return: list of WrappedRedvoxPacketM, converted from API 900 if necessary
        """
        api_m_data: List[WrappedRedvoxPacketM] = []
        for path in self.files_index.entries:
            if path.extension == ".rdvxz":
                data = api900_io.wrap(api900_io.read_file(path.full_path, True))
                api_m_data.append(ac.convert_api_900_to_1000(data))
            elif path.extension == ".rdvxm":
                api_m_data.append(WrappedRedvoxPacketM.from_compressed_path(path.full_path))

        return api_m_data


def get_data_by_id(data_list: List[WrappedRedvoxPacketM], get_id: str) -> Optional[List[WrappedRedvoxPacketM]]:
    """
    return the data that has the id requested
    only used as a test to check batch requests for specific ids; ideally the filter handles everything
    :param data_list: the list of data to read
    :param get_id: the id to filter on
    :return: the list of data with the requested id, or None if the id can't be found
    """
    result: List[WrappedRedvoxPacketM] = []
    for data in data_list:
        if data.get_station_information().get_id() == get_id:
            result.append(data)
    if len(result) == 0:
        return None
    return result
