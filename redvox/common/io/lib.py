from glob import glob
from typing import Iterator, List, Optional
import os.path

from redvox.api1000.common.typing import check_type
from redvox.common.io.types import ReadFilter, PathDescriptor


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
        pass

    # pattern: str = os.path.join(base_dir, f"*{read_filter.extension}")
    # paths: List[str] = glob(os.path.join(base_dir, pattern))
    # path_descriptors: Iterator[Optional[PathDescriptor]] = map()
    # return filter(read_filter.apply, paths)

    return path_descriptors
