from datetime import datetime
from glob import glob
from pathlib import PurePath
from typing import Any, Iterator, List, Optional, Set, Union
import os.path

from redvox.common.versioning import ApiVersion
from redvox.api1000.common.typing import check_type
from redvox.common.io.types import ReadFilter, IndexEntry, Index
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api900.wrapped_redvox_packet import WrappedRedvoxPacket
from redvox.api900.reader import read_rdvxz_file


def not_none(v: Any) -> bool:
    return v is not None


# We need to parse the API M structured directory structure. Here, we enumerate the valid values for the various
# levels in the hierarchy.
__VALID_YEARS: Set[str] = {f"{i:04}" for i in range(2015, 2031)}
__VALID_MONTHS: Set[str] = {f"{i:02}" for i in range(1, 13)}
__VALID_DATES: Set[str] = {f"{i:02}" for i in range(1, 32)}
__VALID_HOURS: Set[str] = {f"{i:02}" for i in range(0, 24)}


def __list_subdirs(base_dir: str, valid_choices: Set[str]) -> List[str]:
    """
    Lists sub-directors in a given base directory that match the provided choices.
    :param base_dir: Base dir to find sub dirs in.
    :param valid_choices: A list of valid directory names.
    :return: A list of valid subdirs.
    """
    subdirs: Iterator[str] = map(lambda p: PurePath(p).name, glob(os.path.join(base_dir, "*", "")))
    return sorted(list(filter(valid_choices.__contains__, subdirs)))


def index_structured_api_900(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> Index:
    """
    This parses a structured API 900 directory structure and identifies files that match the provided filter.
    :param base_dir: Base directory (should be named api900)
    :param read_filter: Filter to filter files with
    :return: A list of wrapped packets on an empty list if none match the filter or none are found
    """
    for year in __list_subdirs(base_dir, __VALID_YEARS):
        for month in __list_subdirs(os.path.join(base_dir, year), __VALID_MONTHS):
            for day in __list_subdirs(os.path.join(base_dir, year, month), __VALID_DATES):
                # Before scanning for *.rdvxm files, let's see if the current year, month, day, are in the
                # filter's range. If not, we can short circuit and skip getting the *.rdvxz files.
                if not read_filter.apply_dt(datetime(int(year),
                                                     int(month),
                                                     int(day))):
                    continue

                path_descriptors: List[IndexEntry] = []

                extension: str
                for extension in read_filter.extensions:
                    paths: List[str] = glob(os.path.join(base_dir,
                                                         year,
                                                         month,
                                                         day,
                                                         f"*{extension}"))
                    descriptors: Iterator[IndexEntry] = filter(not_none, map(IndexEntry.from_path, paths))
                    path_descriptors.extend(descriptors)

                return Index(path_descriptors)


def index_structured_api_1000(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> Index:
    """
    This parses a structured API M directory structure and identifies files that match the provided filter.
    :param base_dir: Base directory (should be named api1000)
    :param read_filter: Filter to filter files with
    :return: A list of wrapped packets on an empty list if none match the filter or none are found
    """
    for year in __list_subdirs(base_dir, __VALID_YEARS):
        for month in __list_subdirs(os.path.join(base_dir, year), __VALID_MONTHS):
            for day in __list_subdirs(os.path.join(base_dir, year, month), __VALID_DATES):
                for hour in __list_subdirs(os.path.join(base_dir, year, month, day), __VALID_HOURS):
                    # Before scanning for *.rdvxm files, let's see if the current year, month, day, hour are in the
                    # filter's range. If not, we can short circuit and skip getting the *.rdvxm files.
                    if not read_filter.apply_dt(datetime(int(year),
                                                         int(month),
                                                         int(day),
                                                         int(hour))):
                        continue

                    path_descriptors: List[IndexEntry] = []

                    extension: str
                    for extension in read_filter.extensions:
                        paths: List[str] = glob(os.path.join(base_dir,
                                                             year,
                                                             month,
                                                             day,
                                                             hour,
                                                             f"*{extension}"))
                        descriptors: Iterator[IndexEntry] = filter(not_none, map(IndexEntry.from_path, paths))
                        path_descriptors.extend(descriptors)

                    return Index(path_descriptors)


def index_structured(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> Index:
    base_path: PurePath = PurePath(base_dir)

    # API 900
    if base_path.name == "api900":
        return index_structured_api_900(base_dir, read_filter)
    # API 1000
    elif base_path.name == "api1000":
        return index_structured_api_1000(base_dir, read_filter)
    # Maybe parent to one or both?
    else:
        path_descriptors: List[IndexEntry] = []
        subdirs: List[str] = __list_subdirs(base_dir, {"api900", "api1000"})

        if "api900" in subdirs:
            path_descriptors.extend(index_structured_api_900(str(base_path.joinpath("api900"))))

        if "api1000" in subdirs:
            path_descriptors.extend(index_structured_api_1000(str(base_path.joinpath("api1000"))))

        return Index(path_descriptors)


def index_unstructured(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> Index:
    """
    Returns the list of file paths that match the given filter for unstructured data.
    :param base_dir: Directory containing unstructured data.
    :param read_filter: An (optional) ReadFilter for specifying station IDs and time windows.
    :return: An iterator of valid paths.
    """
    check_type(base_dir, [str])
    check_type(read_filter, [ReadFilter])

    path_descriptors: List[IndexEntry] = []

    extension: str
    for extension in read_filter.extensions:
        pattern: str = str(PurePath(base_dir).joinpath(f"*{extension}"))
        paths: List[str] = glob(os.path.join(base_dir, pattern))
        descriptors: Iterator[IndexEntry] = filter(not_none, map(IndexEntry.from_path, paths))
        path_descriptors.extend(descriptors)

    return Index(path_descriptors)

