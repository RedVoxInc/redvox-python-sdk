"""
Read Redvox data from a single directory
Data files can be either API 900 or API 1000 data formats
The ReadResult object converts api900 data into api 1000 format
"""
import os
from typing import List, Optional

from redvox.api1000 import io as apim_io, io_raw as apim_io_raw
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api900 import reader as api900_io
from redvox.common import api_conversions as ac


def load_file_range_from_api900(directory: str,
                                start_timestamp_utc_s: Optional[int] = None,
                                end_timestamp_utc_s: Optional[int] = None,
                                redvox_ids: Optional[List[str]] = None,
                                structured_layout: bool = False,
                                concat_continuous_segments: bool = True) -> apim_io.ReadResult:
    """
    reads in api900 data from a directory and returns a list of stations
    note that the param descriptions are taken directly from api900.reader.read_rdvxz_file_range
    :param directory: The root directory of the data. If structured_layout is False, then this directory will
                      contain various unorganized .rdvxz files. If structured_layout is True, then this directory
                      must be the root api900 directory of the structured files.
    :param start_timestamp_utc_s: The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: The end timestamp as seconds since the epoch UTC.
    :param redvox_ids: An optional list of redvox_ids to filter against (default=[]).
    :param structured_layout: An optional value to define if this is loading structured data (default=False).
    :param concat_continuous_segments: An optional value to define if this function should concatenate rdvxz files
                                       into multiple continuous rdvxz files separated at gaps.
    :return: a list of Station objects that contain the data
    """
    converted_result: List[apim_io.ReadWrappedPackets] = []
    all_data = api900_io.read_rdvxz_file_range(directory, start_timestamp_utc_s, end_timestamp_utc_s, redvox_ids,
                                               structured_layout, concat_continuous_segments)
    for ids in all_data.keys():
        converted_data: List[WrappedRedvoxPacketM] = []
        for packet in all_data[ids]:
            converted_data.append(ac.convert_api_900_to_1000(packet))
        converted_result.append(apim_io.ReadWrappedPackets(converted_data))
    return apim_io.ReadResult(start_timestamp_utc_s, end_timestamp_utc_s, converted_result)


def read_all_in_dir(directory: str,
                    start_timestamp_utc_s: Optional[int] = None,
                    end_timestamp_utc_s: Optional[int] = None,
                    station_ids: Optional[List[str]] = None,
                    structured_layout: bool = False) -> apim_io.ReadResult:
    """
    load all data files in the directory
    :param directory: string, location of all the files;
                        if structured_layout is True, the directory contains a root api1000 or api900 directory,
                        if structured_layout is False, the directory contains unsorted files
    :param start_timestamp_utc_s: optional int, The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: optional int, The end timestamp as seconds since the epoch UTC.
    :param station_ids: optional list of string station ids to filter against, default empty list
    :param structured_layout: optional bool to define if this is loading structured data, default False.
    :return: a ReadResult object containing the data requested
    """
    # create the object to store the data
    stations: apim_io.ReadResult = apim_io.ReadResult(start_timestamp_utc_s, end_timestamp_utc_s)
    # if structured_layout, there should be a specifically named folder in directory
    if structured_layout:
        if "api900" not in directory:
            api900_dir = os.path.join(directory, "api900")
        else:
            api900_dir = directory
        if "api1000" not in directory:
            apim_dir = os.path.join(directory, "api1000")
        else:
            apim_dir = directory
        # check if none of the paths exists
        if not (os.path.exists(api900_dir) or os.path.exists(apim_dir)):
            # no specially named directory found; raise error
            raise ValueError(f"{directory} does not contain api900 or api1000 directory.")
    else:
        # load files from unstructured layout; everything is sitting in the main directory
        api900_dir = directory
        apim_dir = directory

    # get api900 data
    api_900_data = load_file_range_from_api900(api900_dir, start_timestamp_utc_s, end_timestamp_utc_s,
                                               station_ids, structured_layout, False)
    for rwp in api_900_data.all_wrapped_packets:
        stations.add_result(rwp)
    # get api1000 data
    api_m_data = apim_io.read_structured(apim_dir, start_timestamp_utc_s, end_timestamp_utc_s, station_ids,
                                         structured_layout)
    for rwp in api_m_data.all_wrapped_packets:
        stations.add_result(rwp)
    return stations


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
