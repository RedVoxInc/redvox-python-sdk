"""
This module provides utility functions that are used by the reader but generally will not be used directly by end
users.
"""

import struct
import typing

from google.protobuf import json_format
from google.protobuf.internal import containers
import lz4.block
import numpy


import redvox.api900.exceptions as exceptions
import redvox.api900.lib.api900_pb2 as api900_pb2


def calculate_uncompressed_size(buf: bytes) -> int:
    """
    Given a buffer, calculate the original size of the uncompressed packet by looking at the first four bytes.
    :param buf: Buffer where first 4 big endian bytes contain the size of the original uncompressed packet.
    :return: The total number of bytes in the original uncompressed packet.
    """
    return struct.unpack(">I", buf[:4])[0]


def uncompressed_size_bytes(size: int) -> bytes:
    """
    Given the size of the original uncompressed file, return the size as an array of 4 bytes.
    :param size: The size to convert.
    :return: The 4 bytes representing the size.
    """
    return struct.pack(">I", size)


def lz4_decompress(buf: bytes) -> bytes:
    """
    Decompresses an API 900 compressed buffer.
    :param buf: The buffer to decompress.
    :return: The uncompressed buffer.
    """
    uncompressed_size = calculate_uncompressed_size(buf)

    if uncompressed_size <= 0:
        raise exceptions.ReaderException("uncompressed size [{}] must be > 0".format(uncompressed_size))

    return lz4.block.decompress(buf[4:], uncompressed_size=calculate_uncompressed_size(buf))


# noinspection PyArgumentList
def lz4_compress(buf: bytes) -> bytes:
    """
    Compresses a buffer using LZ4. The compressed buffer is then prepended with the 4 bytes indicating the original
    size of uncompressed buffer.
    :param buf: The buffer to compress.
    :return: The compressed buffer with 4 bytes prepended indicated the original size of the uncompressed buffer.
    """
    uncompressed_size = uncompressed_size_bytes(len(buf))
    compressed = lz4.block.compress(buf, store_size=False)
    return uncompressed_size + compressed


def write_file(file: str, redvox_packet: api900_pb2.RedvoxPacket):
    """
    Writes a redvox file.  Specify the correct file type in the file string.
    :param file: str, File to write
    :param redvox_packet: protobuf packet to write
    :return: Nothing, compressed file is written to disk
    """
    buffer = lz4_compress(redvox_packet.SerializeToString())
    with open(file, "wb") as file_out:
        file_out.write(buffer)


def to_json(redvox_packet: api900_pb2.RedvoxPacket) -> str:
    """
    Converts a protobuf encoded API 900 RedVox packet into JSON.
    :param redvox_packet: The protobuf encoded packet.
    :return: A string containing JSON of this packet.
    """
    return json_format.MessageToJson(redvox_packet)


def from_json(redvox_packet_json: str) -> api900_pb2.RedvoxPacket:
    """
    Converts a JSON packet representing an API 900 packet into a protobuf encoded RedVox API 900 packet.
    :param redvox_packet_json: A string containing the json representing the packet.
    :return: A Python instance of an encoded API 900 packet.
    """
    return json_format.Parse(redvox_packet_json, api900_pb2.RedvoxPacket())


def payload_type(channel: typing.Union[api900_pb2.EvenlySampledChannel,
                                       api900_pb2.UnevenlySampledChannel]) -> str:
    """
    Given a channel, return the internal protobuf string representation of the payload's data type.
    :param channel: The channel to check the data type of.
    :return: The internal protobuf string representation of the payload's data type.
    """
    if channel is None:
        return "No channel to hold payload"

    return channel.WhichOneof("payload")


def extract_payload(channel: typing.Union[api900_pb2.EvenlySampledChannel,
                                          api900_pb2.UnevenlySampledChannel]) -> numpy.ndarray:
    """
    Given an evenly or unevenly sampled channel, extracts the entire payload.

    This will return a payload of either ints or floats and is type agnostic when it comes to the underlying
    protobuf type.
    :param channel: The protobuf channel to extract the payload from.
    :return: A numpy array of either floats or ints.
    """
    payload_type_str = payload_type(channel)

    if payload_type_str == "byte_payload":
        payload = channel.byte_payload.payload
        return numpy.frombuffer(payload, numpy.uint8)
    elif payload_type_str == "uint32_payload":
        payload = channel.uint32_payload.payload
    elif payload_type_str == "uint64_payload":
        payload = channel.uint64_payload.payload
    elif payload_type_str == "int32_payload":
        payload = channel.int32_payload.payload
    elif payload_type_str == "int64_payload":
        payload = channel.int64_payload.payload
    elif payload_type_str == "float32_payload":
        payload = channel.float32_payload.payload
    elif payload_type_str == "float64_payload":
        payload = channel.float64_payload.payload
    else:
        return numpy.array([])
        # raise exceptions.ReaderException("unsupported payload type {}".format(payload_type_str))

    return numpy.array(payload)


def repeated_to_list(repeated: typing.Union[containers.RepeatedCompositeFieldContainer,
                                            containers.RepeatedScalarFieldContainer]) -> typing.List:
    """
    Transforms a repeated protobuf field into a list.
    :param repeated: The repeated field to transform.
    :return: A list of the repeated items.
    """
    return repeated[0:len(repeated)]


def repeated_to_array(repeated: typing.Union[containers.RepeatedCompositeFieldContainer,
                                             containers.RepeatedScalarFieldContainer]) -> numpy.ndarray:
    """
    Transforms a repeated protobuf field into a numpy array.
    :param repeated: The repeated field to transform.
    :return: A numpy array of the repeated items.
    """
    return numpy.array(repeated_to_list(repeated))


def deinterleave_array(ndarray: numpy.ndarray, offset: int, step: int) -> numpy.ndarray:
    """
    Extracts a single channel type from an interleaved array.

    An interleaved channel contains multiple channel types in a single payload. This is useful for situations where
    a sensor produces several values for a single timestamp. For example, a GPS will produce a LATITUDE, LONGITUDE,
    ALTITUDE, and SPEED values with every update. An interleaved channel is an encoding that encodes multiple channel
    types into a single payload.

    Every channel has a field channel_types that list the channel types contained within the payload. For a GPS sensor,
    the channel_types array would look like [LATITUDE, LONGITUDE, ALTITUDE, SPEED]. The location of the channel type
    in channel_types determines the offset into the payload and the length of channel_types determines the step size.
    As such, a GPS channel payload would contain the following values:

    [LAT0, LNG0, ALT0, SPD0, LAT1, LNG1, ALT1, SPD1, ..., LATn, LNGn, ALTn, SPDn]

    This function will "deinterleave" the encoding and provide an array of a single channel type.

    :param ndarray: Interleaved array.
    :param offset: Offset into the array.
    :param step: The step size.
    :return: A numpy array of a single channel type.
    """

    if offset < 0 or offset >= len(ndarray):
        raise exceptions.ReaderException("offset {} out of range [{},{})".format(offset, 0, len(ndarray)))

    if offset >= step:
        raise exceptions.ReaderException("offset {} must be smaller than step {}".format(offset, step))

    if step <= 0 or step > len(ndarray):
        raise exceptions.ReaderException("step {} out of range [{},{})".format(step, 0, len(ndarray)))

    if len(ndarray) % step != 0:
        raise exceptions.ReaderException("step {} is not a multiple of {}".format(step, len(ndarray)))

    # pylint: disable=C1801
    if len(ndarray) == 0:
        return empty_array()

    return ndarray[offset::step]


def to_array(values: typing.Union[typing.List, numpy.ndarray]) -> numpy.ndarray:
    """
    Takes either a list or a numpy array and returns a numpy array if the parameter was a list.
    :param values: Values to convert into numpy array if values are in a list.
    :return: A numpy array of the passed in values.
    """
    if isinstance(values, typing.List):
        return numpy.array(values)
    return values


def interleave_arrays(arrays: typing.List[numpy.ndarray]) -> numpy.ndarray:
    """
    Interleaves multiple arrays together.
    :param arrays: Arrays to interleave.
    :return: Interleaved arrays.
    """
    if len(arrays) < 2:
        raise exceptions.ReaderException("At least 2 arrays are required for interleaving")

    if len(set(map(len, arrays))) > 1:
        raise exceptions.ReaderException("all arrays must be same size")

    total_arrays = len(arrays)
    total_elements = sum(map(lambda array: array.size, arrays))
    interleaved_array = numpy.empty((total_elements,), dtype=arrays[0].dtype)
    for i in range(total_arrays):
        interleaved_array[i::total_arrays] = arrays[i]

    return interleaved_array


def implements_diff(val) -> bool:
    """
    Checks if a value implements the diff method.
    :param val: Value to check
    :return: True is the value implements diff, False otherwise.
    """
    diff_atr = getattr(val, "diff", None)
    if callable(diff_atr):
        return True

    return False


# pylint: disable=R0911
def diff(val1, val2) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    Determines if the two values are different.
    :param val1: The first value to check.
    :param val2: The second value to check.
    :return: False, None if the values are the same or True, and a string displaying the differences when different.
    """
    # pylint: disable=C0123
    if type(val1) != type(val2):
        return True, "type {} != type {}".format(type(val1), type(val2))

    if implements_diff(val1) and implements_diff(val2):
        diffs = val1.diff(val2)
        if len(diffs) == 0:
            return False, None

        return True, "%s" % list(diffs)

    if isinstance(val1, numpy.ndarray) and isinstance(val2, numpy.ndarray):
        if numpy.array_equal(val1, val2):
            return False, None

        return True, "{} != {}".format(val1, val2)

    if val1 != val2:
        return True, "{} != {}".format(val1, val2)

    return False, None


def safe_index_of(lst: typing.List, val: typing.Any) -> int:
    """
    Finds the index of an item in a list and instead of throwing an exception returns -1 when the item DNE.
    :param lst: List to search through.
    :param val: The value to find the index of.
    :return: The index of the first value v found or -1.
    """
    try:
        return lst.index(val)
    except ValueError:
        return -1


def empty_array() -> numpy.ndarray:
    """Returns an empty numpy array.
    :return: An empty numpy array.
    """
    return numpy.array([])


def empty_evenly_sampled_channel() -> api900_pb2.EvenlySampledChannel:
    """
    Returns an empty protobuf EvenlySampledChannel
    :return: empty EvenlySampledChannel
    """
    obj = api900_pb2.EvenlySampledChannel()
    return obj


def empty_unevenly_sampled_channel() -> api900_pb2.UnevenlySampledChannel:
    """
    Returns an empty protobuf UnevenlySampledChannel
    :return: empty UnevenlySampledChannel
    """
    obj = api900_pb2.UnevenlySampledChannel()
    return obj


def channel_type_name_from_enum(enum_constant: int) -> str:
    """
    Returns the name of a channel type given its enumeration constant.
    :param enum_constant: The constant to turn into a name.
    :return: The name of the channel.
    """
    return api900_pb2.ChannelType.Name(enum_constant)


def get_metadata(metadata: typing.List[str], k: str) -> str:
    """
    Given a meta-data key, extract the value.
    :param metadata: List of metadata to extract value from.
    :param k: The meta-data key.
    :return: The value corresponding to the key or an empty string.
    """
    if len(metadata) % 2 != 0:
        raise exceptions.ReaderException("metadata list must contain an even number of items")

    idx = safe_index_of(metadata, k)
    if idx < 0:
        return ""

    return metadata[idx + 1]


def get_metadata_as_dict(metadata: typing.List[str]) -> typing.Dict[str, str]:
    """
    Since the metadata is inherently key-value, it may be useful to turn the metadata list into a python dictionary.
    :param metadata: The metadata list.
    :return: Metadata as a python dictionary.
    """
    if not metadata:
        return {}

    if len(metadata) % 2 != 0:
        raise exceptions.ReaderException("metadata list must contain an even number of items")

    metadata_dict = {}
    metadata_copy = metadata.copy()
    while len(metadata_copy) >= 2:
        metadata_key = metadata_copy.pop(0)
        metadata_value = metadata_copy.pop(0)
        if metadata_key not in metadata_dict:
            metadata_dict[metadata_key] = metadata_value
    return metadata_dict


def metadata_dict_to_list(metadata_dict: typing.Dict[str, str]) -> typing.List[str]:
    """
    Converts a dictionary containing metadata into a list of metadata.
    :param metadata_dict: The dictionary of metadata.
    :return: A list of metadata.
    """
    metadata_list = []
    for key, value in metadata_dict.items():
        metadata_list.extend([key, value])
    return metadata_list
