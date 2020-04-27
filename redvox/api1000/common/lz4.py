import lz4.frame


def compress(data: bytes, compression_level: int = 16) -> bytes:
    return lz4.frame.compress(data, compression_level=compression_level, return_bytearray=True)


def decompress(data: bytes) -> bytes:
    return lz4.frame.decompress(data, True)
