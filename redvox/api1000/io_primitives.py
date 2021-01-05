from multiprocessing.pool import Pool
from typing import Iterator

from redvox.api1000.common.lz4 import decompress
import redvox.api1000.proto.redvox_api_m_pb2 as pb
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM


def decompress_bufs(bufs: Iterator[bytes], parallel: bool = False) -> Iterator[bytes]:
    if parallel:
        pool: Pool = Pool()
        return pool.imap_unordered(decompress, bufs)
    else:
        buf: bytes
        for buf in bufs:
            yield decompress(buf)


def read_path(path: str) -> bytes:
    with open(path, "rb") as fin:
        return fin.read()


def decompress_paths(paths: Iterator[str], parallel: bool = False) -> Iterator[bytes]:
    if parallel:
        pool: Pool = Pool()
        return decompress_bufs(pool.imap_unordered(read_path, paths), parallel)
    else:
        path: str
        for path in paths:
            buf: bytes = read_path(path)
            yield decompress(buf)


def deserialize_bufs(bufs: Iterator[bytes]) -> Iterator[pb.RedvoxPacketM]:
    buf: bytes
    for buf in bufs:
        proto: pb.RedvoxPacketM = pb.RedvoxPacketM()
        proto.ParseFromString(buf)
        yield proto


def wrap_protos(protos: Iterator[pb.RedvoxPacketM]) -> Iterator[WrappedRedvoxPacketM]:
    proto: pb.RedvoxPacketM
    for proto in protos:
        yield WrappedRedvoxPacketM(proto)
