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


def check_version_buf(buf: bytes) -> ApiVersion:
    """
    Attempts to check the API version of a given RedVox buffer by looking for the LZ4 frame header which is only present
    in API M compressed data.
    :param buf: Buffer of RedVox data.
    :return: An enum that represents the API version of the file.
    """
    if len(buf) < 4:
        return ApiVersion.UNKNOWN
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
    with open(path, "rb") as fin:
        return check_version_buf(fin.read(4))
