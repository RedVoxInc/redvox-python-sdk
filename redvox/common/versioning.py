from enum import Enum

LZ4_MAGIC: bytes = b'\x04"M\x18'


class ApiVersion(Enum):
    """
    Enumerates the API versions this SDK supports.
    """
    API_900: str = "API_900"
    API_1000: str = "API_1000"


# noinspection PyTypeChecker
def check_version(path: str) -> ApiVersion:
    """
    Attempts to check the API version of a given RedVox file by looking for the LZ4 frame header which is only present
    in API M compressed data.
    :param path: Path of file to check.
    :return: An enum that represents the API version of the file.
    """
    with open(path, "rb") as fin:
        header = fin.read(4)
        if header == LZ4_MAGIC:
            return ApiVersion.API_1000
        return ApiVersion.API_900
