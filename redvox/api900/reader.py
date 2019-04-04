# pylint: disable=too-many-lines
"""
This module provides functions and classes for working with RedVox API 900 data.
"""

import collections
import glob
import typing

import redvox.api900.lib.api900_pb2 as api900_pb2
import redvox.api900.reader_utils as reader_utils
from redvox.api900.wrapped_redvox_packet import WrappedRedvoxPacket


def wrap(redvox_packet: api900_pb2.RedvoxPacket) -> WrappedRedvoxPacket:
    """
    Wraps a protobuf packet in a WrappedRedocPacket.
    :param redvox_packet: Protobuf packet to wrap.
    :return: A WrappedRedvoxPacket.
    """
    return WrappedRedvoxPacket(redvox_packet)


def read_buffer(buf: bytes, is_compressed: bool = True) -> api900_pb2.RedvoxPacket:
    """
    Deserializes a serialized protobuf RedvoxPacket buffer.
    :param buf: Buffer to deserialize.
    :param is_compressed: Whether or not the buffer is compressed or decompressed.
    :return: Deserialized protobuf redvox packet.
    """
    buffer = reader_utils._lz4_decompress(buf) if is_compressed else buf
    redvox_packet = api900_pb2.RedvoxPacket()
    redvox_packet.ParseFromString(buffer)
    return redvox_packet


def read_file(file: str, is_compressed: bool = None) -> api900_pb2.RedvoxPacket:
    """
    Deserializes a serialized protobuf RedvoxPacket file.
    :param file: File to deserialize.
    :param is_compressed: Whether or not the file is compressed or decompressed.
    :return: Deserialized protobuf redvox packet.
    """
    file_ext = file.split(".")[-1]

    if is_compressed is None:
        _is_compressed = True if file_ext == "rdvxz" else False
    else:
        _is_compressed = is_compressed
    with open(file, "rb") as fin:
        return read_buffer(fin.read(), _is_compressed)


def read_rdvxz_file(path: str) -> WrappedRedvoxPacket:
    """
    Reads a .rdvxz file from the specified path and returns a WrappedRedvoxPacket.
    :param path: The path of the file.
    :return: A WrappedRedvoxPacket.
    """
    return wrap(read_file(path))


def read_rdvxz_file_range(directory: str,
                          start_timestamp_utc_s: int,
                          end_timestamp_utc_s: int,
                          device_ids: typing.List[str],
                          structured_layout: bool = False,
                          concat_continuous_segments: bool = True) -> typing.List[WrappedRedvoxPacket]:
    pass


def read_rdvxz_buffer(buf: bytes) -> WrappedRedvoxPacket:
    """
    Reads a .rdvxz file from the provided buffer and returns a WrappedRedvoxPacket.
    :param buf: The buffer of bytes consisting of a compressed .rdvxz file.
    :return: A WrappedRedvoxPacket.
    """
    return wrap(read_buffer(buf))


def read_json_file(path: str) -> WrappedRedvoxPacket:
    """
    Reads a RedVox compliant API 900 .json file from the provided path and returns a WrappedRedvoxPacket.
    :param path: Path to the RedVox compliant API 900 .json file.
    :return: A WrappedRedvoxPacket.
    """
    with open(path, "r") as json_in:
        return wrap(reader_utils._from_json(json_in.read()))


def read_json_string(json: str) -> WrappedRedvoxPacket:
    """
    Reads a RedVox compliant API 900 json string and returns a WrappedRedvoxPacket.
    :param json: RedVox API 900 compliant json string.
    :return: A WrappedRedvoxPacket.
    """
    return wrap(reader_utils._from_json(json))


def read_directory(directory_path: str) -> typing.Dict[str, typing.List[WrappedRedvoxPacket]]:
    """
    Reads .rdvxz files from a directory and returns a dictionary from redvox_id -> a list of sorted wrapped redvox
    packets that belong to that device.
    :param directory_path: The path to the directory containing .rdvxz files.
    :return: A dictionary representing a mapping from redvox_id to its packets.
    """

    # Make sure the directory ends with a trailing slash "/"
    if directory_path[-1] != "/":
        directory_path = directory_path + "/"

    file_paths = sorted(glob.glob(directory_path + "*.rdvxz"))
    protobuf_packets = map(read_file, file_paths)
    wrapped_packets = list(map(wrap, protobuf_packets))
    grouped = collections.defaultdict(list)

    for wrapped_packet in wrapped_packets:
        grouped[wrapped_packet.redvox_id()].append(wrapped_packet)

    return grouped
