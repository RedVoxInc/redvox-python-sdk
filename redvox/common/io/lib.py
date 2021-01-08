from glob import glob
from pathlib import PurePath
from typing import Any, Iterator, List, Optional
import os.path

from redvox.api1000.common.typing import check_type
from redvox.common.io.types import ReadFilter, PathDescriptor


def not_none(v: Any) -> bool:
    return v is not None


def index_unstructured(base_dir: str, read_filter: ReadFilter = ReadFilter()) -> List[PathDescriptor]:
    """
    Returns the list of file paths that match the given filter for unstructured data.
    :param base_dir: Directory containing unstructured data.
    :param read_filter: An (optional) ReadFilter for specifying station IDs and time windows.
    :return: An iterator of valid paths.
    """
    check_type(base_dir, [str])
    check_type(read_filter, [ReadFilter])

    path_descriptors: List[PathDescriptor] = []

    extension: str
    for extension in read_filter.extensions:
        pattern: str = str(PurePath(base_dir).joinpath(f"*${extension}"))
        paths: List[str] = glob(os.path.join(base_dir, pattern))
        descriptors: Iterator[PathDescriptor] = filter(not_none, map(PathDescriptor.from_path, paths))
        path_descriptors.extend(descriptors)

    return path_descriptors
