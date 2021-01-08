"""
Read Redvox data from a single directory
Data files can be either API 900 or API 1000 data formats
The ReadResult object converts api900 data into api 1000 format
"""
import os
from glob import glob
from typing import List

from redvox.api1000 import io_raw as apim_io_raw
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api900 import reader as api900_io
from redvox.common import api_conversions as ac


def read_all_in_unstructured_dir(base_dir: str) -> apim_io_raw.ReadResult:
    converted_data: List[WrappedRedvoxPacketM] = []
    api_900_data = api900_io.read_rdvxz_file_range(base_dir, structured_layout=False, concat_continuous_segments=False)
    for ids in api_900_data.keys():
        for packet in api_900_data[ids]:
            converted_data.append(ac.convert_api_900_to_1000(packet))

    api_m_filter = apim_io_raw.ReadFilter()
    pattern: str = os.path.join(base_dir, f"*{api_m_filter.extension}")
    paths: List[str] = glob(os.path.join(base_dir, pattern))
    paths = list(filter(api_m_filter.filter_path, paths))
    api_m_data: List[WrappedRedvoxPacketM] = apim_io_raw.__deserialize_paths(paths)

    # combine api900 and api m
    api_m_data.extend(converted_data)

    return apim_io_raw.ReadResult.from_packets(api_m_data)


def read_all_in_structured_dir_io_raw(base_dir: str) -> apim_io_raw.ReadResult:
    converted_data: List[WrappedRedvoxPacketM] = []
    api_900_data = api900_io.read_rdvxz_file_range(os.path.join(base_dir, "api900"),
                                                   structured_layout=True, concat_continuous_segments=False)
    for ids in api_900_data.keys():
        for packet in api_900_data[ids]:
            converted_data.append(ac.convert_api_900_to_1000(packet))

    # apim_io_raw.check_type(base_dir, [str])
    # api_900_filter = apim_io_raw.ReadFilter(extension=".rdvxz")
    # apim_io_raw.check_type(api_900_filter, [apim_io_raw.ReadFilter])
    # paths: List[str] = __parse_structured_layout_rdvxz(os.path.join(base_dir, "api900"), api_900_filter)
    # api_900_data: List[WrappedRedvoxPacketM] = apim_io_raw.__deserialize_paths(paths)

    api_m_filter = apim_io_raw.ReadFilter()
    paths: List[str] = apim_io_raw.__parse_structured_layout(os.path.join(base_dir, "api1000"), api_m_filter)
    api_m_data: List[WrappedRedvoxPacketM] = apim_io_raw.__deserialize_paths(paths)

    # combine api900 and api m
    api_m_data.extend(converted_data)

    return apim_io_raw.ReadResult.from_packets(api_m_data)
