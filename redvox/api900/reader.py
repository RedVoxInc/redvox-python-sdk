# pylint: disable=too-many-lines
"""
This module provides functions and classes for working with RedVox API 900 data.
"""

import collections
import glob
import os
import os.path
import typing

import redvox.api900.lib.api900_pb2 as api900_pb2
import redvox.api900.concat as concat
import redvox.api900.date_time_utils as date_time_utils
import redvox.api900.reader_utils as reader_utils

# For backwards compatibility, we want to expose as much as we can from this file since everything used to live in this
# file. This will allow old code that referenced everything through this module to still function. Someday "soon" we
# should probably deprecate this.
from redvox.api900.wrapped_redvox_packet import WrappedRedvoxPacket
from redvox.api900.sensors.interleaved_channel import InterleavedChannel
from redvox.api900.sensors.unevenly_sampled_channel import UnevenlySampledChannel
from redvox.api900.sensors.evenly_sampled_channel import EvenlySampledChannel
from redvox.api900.sensors.evenly_sampled_sensor import EvenlySampledSensor
from redvox.api900.sensors.unevenly_sampled_sensor import UnevenlySampledSensor
from redvox.api900.sensors.xyz_unevenly_sampled_sensor import XyzUnevenlySampledSensor
from redvox.api900.sensors.microphone_sensor import MicrophoneSensor
from redvox.api900.sensors.barometer_sensor import BarometerSensor
from redvox.api900.sensors.location_sensor import LocationSensor
from redvox.api900.sensors.time_synchronization_sensor import TimeSynchronizationSensor
from redvox.api900.sensors.accelerometer_sensor import AccelerometerSensor
from redvox.api900.sensors.magnetometer_sensor import MagnetometerSensor
from redvox.api900.sensors.gyroscope_sensor import GyroscopeSensor
from redvox.api900.sensors.light_sensor import LightSensor
from redvox.api900.sensors.infrared_sensor import InfraredSensor
from redvox.api900.sensors.image_sensor import ImageSensor

WrappedRedvoxPackets = typing.List[WrappedRedvoxPacket]
RedvoxSensor = typing.Union[
    EvenlySampledSensor,
    UnevenlySampledSensor,
    MicrophoneSensor,
    BarometerSensor,
    LocationSensor,
    TimeSynchronizationSensor,
    AccelerometerSensor,
    GyroscopeSensor,
    MagnetometerSensor,
    LightSensor,
    InfraredSensor,
    ImageSensor
]
RedvoxSensors = typing.List[RedvoxSensor]


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
    buffer = reader_utils.lz4_decompress(buf) if is_compressed else buf
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


def _is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False


def _is_valid_redvox_filename(filename: str) -> bool:
    return len(filename) == 30 \
            and _is_int(filename[0:10]) \
            and filename[10:11] == "_" \
            and _is_int(filename[11:24]) \
            and filename[24:len(filename)] == ".rdvxz"


def _is_path_in_set(path: str,
                    start_timestamp_utc_s: int,
                    end_timestamp_utc_s: int,
                    redvox_ids: typing.Set[str]) -> bool:
    filename = path.split(os.sep)[-1]

    if not _is_valid_redvox_filename(filename):
        return False

    timestamp = int(date_time_utils.milliseconds_to_seconds(float(filename[11:24])))

    if not (start_timestamp_utc_s <= timestamp <= end_timestamp_utc_s):
        return False

    redvox_id = filename[0:10]
    if redvox_id not in redvox_ids:
        print("reject due id", redvox_id, redvox_ids)
        return False

    return True


def _get_structured_paths(directory: str,
                          start_timestamp_utc_s: int,
                          end_timestamp_utc_s: int,
                          redvox_ids: typing.Set[str]) -> typing.List[str]:
    paths = []
    for (year, month, day) in date_time_utils.DateIterator(start_timestamp_utc_s, end_timestamp_utc_s):
        all_paths = glob.glob(os.path.join(directory, year, month, day, "*.rdvxz"))
        valid_paths = list(
            filter(lambda path: _is_path_in_set(path, start_timestamp_utc_s, end_timestamp_utc_s, redvox_ids),
                   all_paths))
        paths.extend(valid_paths)

    return paths


T = typing.TypeVar("T")
TT = typing.TypeVar("TT")


def _group_by(grouping_fn: typing.Callable[[T], TT],
              items: typing.Iterable[T]) -> typing.Dict[TT, typing.List[T]]:
    grouped = collections.defaultdict(list)

    for item in items:
        grouped[grouping_fn(item)].append(item)

    return grouped


def _id_uuid(wrapped_redvox_packet: WrappedRedvoxPacket) -> str:
    return "%s:%s" % (wrapped_redvox_packet.redvox_id(),
                      wrapped_redvox_packet.uuid())


def read_rdvxz_file_range(directory: str,
                          start_timestamp_utc_s: int,
                          end_timestamp_utc_s: int,
                          redvox_ids: typing.List[str],
                          structured_layout: bool = False,
                          concat_continuous_segments: bool = True) -> typing.Dict[
    str, typing.List[WrappedRedvoxPacket]]:
    while directory.endswith("/") or directory.endswith("\\"):
        directory = directory[:-1]

    if structured_layout:
        paths = _get_structured_paths(directory,
                                      start_timestamp_utc_s,
                                      end_timestamp_utc_s,
                                      set(redvox_ids))
    else:
        all_paths = glob.glob(os.path.join(directory, "*.rdvxz"))
        paths = list(
            filter(lambda path: _is_path_in_set(path, start_timestamp_utc_s, end_timestamp_utc_s, set(redvox_ids)),
                   all_paths))

    wrapped_redvox_packets = map(read_rdvxz_file, paths)
    grouped = _group_by(_id_uuid, wrapped_redvox_packets)
    for packets in grouped.values():
        packets.sort(key=WrappedRedvoxPacket.app_file_start_timestamp_machine)

    if not concat_continuous_segments:
        return grouped

    for id_uuid in grouped:
        grouped[id_uuid] = concat.concat_wrapped_redvox_packets(grouped[id_uuid])

    return grouped


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
        return wrap(reader_utils.from_json(json_in.read()))


def read_json_string(json: str) -> WrappedRedvoxPacket:
    """
    Reads a RedVox compliant API 900 json string and returns a WrappedRedvoxPacket.
    :param json: RedVox API 900 compliant json string.
    :return: A WrappedRedvoxPacket.
    """
    return wrap(reader_utils.from_json(json))


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
