"""
Read Redvox data from a single directory
Data files can be either API 900 or API 1000 data formats
The ReadResult object converts api900 data into api 1000 format
"""
import os
from glob import glob
from typing import List

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api900 import reader as api900_io
from redvox.common import api_conversions as ac
from redvox.common.io import types as io_types, lib as io_lib


def read_all_in_dir(base_dir: str, io_filter: io_types.ReadFilter, structured: bool = False) -> io_types.ReadResult:
    if structured:
        paths = io_lib.index_structured(base_dir, io_filter)
    else:
        paths = io_lib.index_unstructured(base_dir, io_filter)
    api_m_data: List[WrappedRedvoxPacketM] = []
    for path in paths:
        if path.extension == ".rdvxz":
            data = api900_io.wrap(api900_io.read_file(path.full_path, True))
            api_m_data.append(ac.convert_api_900_to_1000(data))
        elif path.extension == ".rdvxm":
            api_m_data.append(WrappedRedvoxPacketM.from_compressed_path(path.full_path))

    return io_types.ReadResult.from_packets(api_m_data)
