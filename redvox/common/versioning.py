"""
This module provides functionality for determining the version of RedVox compressed packets.
"""

from enum import Enum

LZ4_MAGIC: bytes = b'\x04"M\x18'


# noinspection PyTypeChecker
class ApiVersion(Enum):
    """
    Enumerates the API versions this SDK supports.
    """

    API_900: str = "API_900"
    API_1000: str = "API_1000"
    UNKNOWN: str = "UNKNOWN"

    # pylint: disable=W0143
    def __lt__(self, other: "ApiVersion") -> bool:
        return self.name < other.name

    @staticmethod
    def from_str(version: str) -> "ApiVersion":
        """
        :param version: version as string
        :return: enumerated value represented by string version
        """
        if version == "API_900" or version == "Api900":
            return ApiVersion.API_900
        elif version == "API_1000" or version == "Api1000":
            return ApiVersion.API_1000
        return ApiVersion.UNKNOWN


# noinspection PyTypeChecker
def check_version_buf(buf: bytes) -> ApiVersion:
    """
    Attempts to check the API version of a given RedVox buffer by looking for the LZ4 frame header which is only present
    in API M compressed data.

    :param buf: Buffer of RedVox data.
    :return: An enum that represents the API version of the file.
    """
    if buf[:4] == LZ4_MAGIC:
        return ApiVersion.API_1000
    return ApiVersion.API_900


# noinspection PyTypeChecker
def check_version(path: str) -> ApiVersion:
    """
    Attempts to check the API version of a given RedVox file by looking for the LZ4 frame header which is only present
    in API M compressed data.

    :param path: Path of file to check.
    :return: An enum that represents the API version of the file.
    """
    try:
        with open(path, "rb") as fin:
            return check_version_buf(fin.read(4))
    except FileNotFoundError:
        return ApiVersion.UNKNOWN
