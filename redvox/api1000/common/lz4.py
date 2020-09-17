"""
This module handles compression and decompression of API M data.
"""

import lz4.frame


def compress(data: bytes, compression_level: int = 12) -> bytes:
    """
    Compresses the provided data using the LZ4 frame protocol.
    :param data: The bytes to compress.
    :param compression_level: A value between 0 and 12 where 0 os faster but less compression and 12 is slower, but
                              provides more compression.
    :return: Compressed bytes.
    """
    return lz4.frame.compress(data, compression_level=compression_level, return_bytearray=True)


def decompress(data: bytes) -> bytes:
    """
    Decompresses the provided data using the LZ4 frame protocol.
    :param data: Data to decompress.
    :return: The decompressed bytes.
    """
    return lz4.frame.decompress(data, True)
