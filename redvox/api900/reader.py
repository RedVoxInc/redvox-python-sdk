# pylint: disable=too-many-lines
"""
This module provides functions and classes for working with RedVox API 900 data.
"""

import collections
import glob
import struct
import typing

# noinspection PyPackageRequirements
import google.protobuf.internal.containers as containers
# noinspection PyPackageRequirements
import google.protobuf.json_format as json_format
import lz4.block
import numpy
import redvox.api900.stat_utils

from redvox.api900.lib import api900_pb2


class ReaderException(Exception):
    """Custom reader exception"""
    pass


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
        raise ReaderException("uncompressed size [{}] must be > 0".format(uncompressed_size))

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


def read_buffer(buf: bytes, is_compressed: bool = True) -> api900_pb2.RedvoxPacket:
    """
    Deserializes a serialized protobuf RedvoxPacket buffer.
    :param buf: Buffer to deserialize.
    :param is_compressed: Whether or not the buffer is compressed or decompressed.
    :return: Deserialized protobuf redvox packet.
    """
    buffer = lz4_decompress(buf) if is_compressed else buf
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


def write_file(file: str, redvox_packet: api900_pb2.RedvoxPacket):
    """
    Writes a redvox file.  Specify the correct file type in the file string.
    :param file: str, File to write
    :param redvox_packet: protobuf packet to write
    :return: Nothing, compressed file is written to disk
    """
    buffer = lz4_compress(redvox_packet.SerializeToString())
    with open(file, "wb") as f:
        f.write(buffer)


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
    else:
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
        raise ReaderException("unsupported payload type {}".format(payload_type_str))

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
        raise ReaderException("offset {} out of range [{},{})".format(offset, 0, len(ndarray)))

    if offset >= step:
        raise ReaderException("offset {} must be smaller than step {}".format(offset, step))

    if step <= 0 or step > len(ndarray):
        raise ReaderException("step {} out of range [{},{})".format(step, 0, len(ndarray)))

    if len(ndarray) % step != 0:
        raise ReaderException("step {} is not a multiple of {}".format(step, len(ndarray)))

    # pylint: disable=C1801
    if len(ndarray) == 0:
        return empty_array()

    return ndarray[offset::step]


def interleave_arrays(arrays: typing.List[numpy.ndarray]) -> numpy.ndarray:
    """
    Interleaves multiple arrays together.
    :param arrays: Arrays to interleave.
    :return: Interleaved arrays.
    """
    if len(arrays) < 2:
        raise ReaderException("At least 2 arrays are required for interleaving")

    if len(set(map(len, arrays))) > 1:
        raise ReaderException("all arrays must be same size")

    total_arrays = len(arrays)
    total_elements = sum(map(lambda array: array.size, arrays))
    interleaved_array = numpy.empty((total_elements,), dtype=arrays[0].dtype)
    for i in range(total_arrays):
        interleaved_array[i::total_arrays] = arrays[i]

    return interleaved_array


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
    obj.byte_payload.payload = b''
    return obj


def empty_unevenly_sampled_channel() -> api900_pb2.UnevenlySampledChannel:
    """
    Returns an empty protobuf UnevenlySampledChannel
    :return: empty UnevenlySampledChannel
    """
    obj = api900_pb2.UnevenlySampledChannel()
    obj.byte_payload.payload = b''
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
        raise ReaderException("metadata list must contain an even number of items")

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
        raise ReaderException("metadata list must contain an even number of items")

    metadata_dict = {}
    metadata_copy = metadata.copy()
    while len(metadata_copy) >= 2:
        metadata_key = metadata_copy.pop(0)
        metadata_value = metadata_copy.pop(0)
        if metadata_key not in metadata_dict:
            metadata_dict[metadata_key] = metadata_value
    return metadata_dict


# pylint: disable=R0902
class InterleavedChannel:
    """
    This class represents an interleaved channel.

    An interleaved channel contains multiple channel types in a single payload. This is useful for situations where
    a sensor produces several values for a single timestamp. For example, a GPS will produce a LATITUDE, LONGITUDE,
    ALTITUDE, and SPEED values with every update. An interleaved channel encodes all four of those channel types
    into a single payload.

    Every channel has a field channel_types that list the channel types contained within the payload. For a GPS sensor,
    the channel_types array would look like [LATITUDE, LONGITUDE, ALTITUDE, SPEED]. The location of the channel type
    in channel_types determines the offset into the payload and the length of channel_types determines the step size.
    As such, this hypothetical GPS channel payload be encoded as:

    [LAT0, LNG0, ALT0, SPD0, LAT1, LNG1, ALT1, SPD1, ..., LATn, LNGn, ALTn, SPDn]

    This class provides methods for working with interleaved channels as well as accessing interleaved statistic values.
    """

    def __init__(self, channel: typing.Union[api900_pb2.EvenlySampledChannel,
                                             api900_pb2.UnevenlySampledChannel] = None):
        """
        Initializes this interleaved channel object.
        :param channel: Either a protobuf evenly or unevenly sampled channel.
        note: value_means, value_medians, value_stds, and channel_type_index are only set during initialization or
            when payload is altered
        payload should only be altered by set_payload or set_deinterleaved_payload due to the extra data values that are
            required to correctly set the protobuf_channel
        """
        if channel is None:
            self.protobuf_channel = empty_evenly_sampled_channel()
            self.sensor_name = None
            self.channel_types = [0]
            self.payload = [0]
            self.metadata = []
            self.value_means = []
            self.value_stds = []
            self.value_medians = []
            self.channel_type_index = []
        else:
            self.protobuf_channel: typing.Union[api900_pb2.EvenlySampledChannel,
                                                api900_pb2.UnevenlySampledChannel] = channel
            """Reference to the original protobuf channel"""

            self.sensor_name: str = channel.sensor_name
            """Provided sensor name"""

            self.channel_types: typing.List[
                typing.Union[
                    api900_pb2.EvenlySampledChannel,
                    api900_pb2.UnevenlySampledChannel]] = repeated_to_list(channel.channel_types)
            """List of channel type constant enumerations"""

            self.payload: numpy.ndarray = extract_payload(channel)
            """This channels payload as a numpy array of either floats or ints"""

            self.metadata: typing.List[str] = repeated_to_list(channel.metadata)
            """This channels list of metadata"""

            self.value_means: numpy.ndarray = repeated_to_array(channel.value_means)
            """Interleaved array of mean values"""

            self.value_stds: numpy.ndarray = repeated_to_array(channel.value_stds)
            """Interleaved array of standard deviations of values"""

            self.value_medians: numpy.ndarray = repeated_to_array(channel.value_medians)
            """Interleaves array of median values"""

            self.channel_type_index: typing.Dict[api900_pb2.ChannelType, int] = {self.channel_types[i]: i for
                                                                                 i in
                                                                                 range(
                                                                                         len(
                                                                                                 self.channel_types))}
            """Contains a mapping of channel type to index in channel_types array"""

    def create(self, sensor_name: str, metadata: typing.List[str],
               channel_types: typing.List[typing.Union[api900_pb2.EvenlySampledChannel,
                                                       api900_pb2.UnevenlySampledChannel]],
               pyld_type: str, payload: numpy.array, payload_steps: int = None):
        """
        Create an interleaved channel using native components
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param payload_steps: number of arrays interleaved
        :param pyld_type: payload type
        :param channel_types: list of payload types
        :param metadata: metadata
        :return self: the interleaved channel with all values set
        """
        self.sensor_name = sensor_name
        self.set_channel_types(channel_types)
        self.set_metadata(metadata)
        self.set_payload(payload, payload_steps, pyld_type)
        return self

    def create_from_deinterleaved_arrays(self, sensor_name: str, metadata: typing.List[str],
                                         channel_types: typing.List[typing.Union[api900_pb2.EvenlySampledChannel,
                                                                                 api900_pb2.UnevenlySampledChannel]],
                                         pyld_type: str, payload: typing.List[numpy.array]):
        """
        Create an interleaved channel using native components
        :param sensor_name: the sensor name
        :param payload: list of numpy arrays to interleave
        :param pyld_type: payload type
        :param channel_types: list of payload types
        :param metadata: metadata
        :return self: the interleaved channel with all values set
        """
        self.create(sensor_name, metadata, channel_types, pyld_type, interleave_arrays(payload), len(payload))
        return self

    def set_channel_types(self, types: typing.List[typing.Union[api900_pb2.EvenlySampledChannel,
                                                                api900_pb2.UnevenlySampledChannel]]):
        """
        sets the channel_types to the list given
        :param types: a list of channel types
        """
        del self.protobuf_channel.channel_types[:]
        for ctype in types:
            self.protobuf_channel.channel_types.append(ctype)
        self.channel_types = repeated_to_list(self.protobuf_channel.channel_types)
        self.channel_type_index = {self.channel_types[i]: i for i in range(len(self.channel_types))}

    def get_channel_type_names(self) -> typing.List[str]:
        """
        Returns the list of channel_types as a list of names instead of enumeration constants.
        :return: The list of channel_types as a list of names instead of enumeration constants.
        """
        return list(map(channel_type_name_from_enum, self.channel_types))

    def channel_index(self, channel_type: int) -> int:
        """
        Returns the index of a channel type or -1 if it DNE.
        :param channel_type: The channel type to search for.
        :return: The index of the channel or -1 if it DNE.
        """
        return self.channel_type_index[channel_type] if channel_type in self.channel_type_index else -1

    def has_channel(self, channel_type: int) -> bool:
        """
        Returns if channel type exists with in this channel.
        :param channel_type: The channel type to search for.
        :return: True if it exist, False otherwise.
        """
        return channel_type in self.channel_type_index

    def set_channel(self, channel: typing.Union[api900_pb2.EvenlySampledChannel,
                                                api900_pb2.UnevenlySampledChannel]):
        """
        Sets the protobuf channel
        :param channel: protobuf channel
        """
        self.protobuf_channel = channel
        self.sensor_name = channel.sensor_name
        self.channel_types = repeated_to_list(channel.channel_types)
        self.payload = extract_payload(channel)
        self.metadata = repeated_to_list(channel.metadata)
        self.value_means = repeated_to_array(channel.value_means)
        self.value_stds = repeated_to_array(channel.value_stds)
        self.value_medians = repeated_to_array(channel.value_medians)
        self.channel_type_index = {self.channel_types[i]: i for i in range(len(self.channel_types))}

    def has_payload(self, channel_type: int) -> bool:
        """
        Returns if channel contains a non-empty specified payload.
        :param channel_type: The channel to check for a payload for.
        :return: Whether this channel contains the specified payload.
        """
        return self.has_channel(channel_type) and len(self.payload) > 0

    def set_payload(self, channel: numpy.array, step: int, pl_type: str):
        """
        sets the payload to an interleaved channel with step number of arrays interleaved together.  The step value is
        only used for error checking before saving the array
        :param channel: interleaved channel
        :param step: number of arrays inside interleaved channel
        :param pl_type: payload type as string
        """
        if len(channel) < 1 or step < 1:
            raise ValueError("Channel must not be empty and number of arrays must not be less than 1.")
        elif step > len(channel):
            raise ValueError("Channel size must be greater than or equal to number of arrays.")
        elif len(channel) % step != 0:
            raise ValueError("Channel size must be a multiple of the number of arrays.")
        # clear all other payloads
        self.protobuf_channel.byte_payload.ClearField("payload")
        self.protobuf_channel.uint32_payload.ClearField("payload")
        self.protobuf_channel.uint64_payload.ClearField("payload")
        self.protobuf_channel.int32_payload.ClearField("payload")
        self.protobuf_channel.int64_payload.ClearField("payload")
        self.protobuf_channel.float32_payload.ClearField("payload")
        self.protobuf_channel.float64_payload.ClearField("payload")
        # set the payload based on the type of data
        if pl_type == "byte_payload":
            self.protobuf_channel.byte_payload.payload = channel
        elif pl_type == "uint32_payload":
            self.protobuf_channel.uint32_payload.payload.extend(channel)
        elif pl_type == "uint64_payload":
            self.protobuf_channel.uint64_payload.payload.extend(channel)
        elif pl_type == "int32_payload":
            self.protobuf_channel.int32_payload.payload.extend(channel)
        elif pl_type == "int64_payload":
            self.protobuf_channel.int64_payload.payload.extend(channel)
        elif pl_type == "float32_payload":
            self.protobuf_channel.float32_payload.payload.extend(channel)
        elif pl_type == "float64_payload":
            self.protobuf_channel.float64_payload.payload.extend(channel)
        else:
            raise TypeError("Unknown payload type to set.")
        self.payload = extract_payload(self.protobuf_channel)
        # calculate the means, std devs, and medians
        self.update_stats()

    def set_deinterleaved_payload(self, channels: typing.List[numpy.array], pl_type: str):
        """
        interleaves the channels and sets the payload to the combined array
        :param channels: a list of arrays with the same length
        :param pl_type: payload type as string
        """
        if len(channels) == 1:
            self.set_payload(channels[0], 1, pl_type)
        else:
            channel = interleave_arrays(channels)
            self.set_payload(channel, len(channels), pl_type)

    def get_payload(self, channel_type: int) -> numpy.ndarray:
        """
        Returns a deinterleaved payload of a given channel type or an empty array.
        :param channel_type: The channel type to extract/deinterleave from the payload.
        :return: A numpy array of floats or ints of a single channel type.
        """
        idx = self.channel_index(channel_type)
        if idx < 0:
            return empty_array()
        try:
            return deinterleave_array(self.payload, idx, len(self.channel_types))
        except ReaderException:
            return empty_array()

    def get_payload_type(self) -> str:
        """
        Returns the internal protobuf payload type.
        :return: The internal protobuf payload type.
        """
        return payload_type(self.protobuf_channel)

    def get_multi_payload(self, channel_types: typing.List[int]) -> numpy.ndarray:
        """
        Returns an interleaved payload with the given channel types.
        :param channel_types: Channel types to interleave into a single payload.
        :return: A numpy array of an interleaved payload.
        """
        channel_types_len = len(channel_types)
        if channel_types_len == 0:
            return empty_array()
        elif channel_types_len == 1:
            return self.get_payload(channel_types[0])

        payloads = list(map(self.get_payload, channel_types))
        return interleave_arrays(payloads)

    def get_value_mean(self, channel_type: int) -> float:
        """
        Returns the mean value for a single channel type.
        :param channel_type: The channel type to extract the mean from.
        :return: The mean value or 0.0 if the mean value DNE.
        """
        idx = self.channel_index(channel_type)
        if idx < 0:
            return 0.0

        return self.value_means[idx]

    def get_value_std(self, channel_type: int) -> float:
        """
        Returns the standard deviation value for a single channel type.
        :param channel_type: The channel type to extract the std from.
        :return: The standard deviation value or 0.0 if the standard deviation value DNE.
        """
        idx = self.channel_index(channel_type)
        if idx < 0:
            return 0.0

        return self.value_stds[idx]

    def get_value_median(self, channel_type: int) -> float:
        """
        Returns the median value for a single channel type.
        :param channel_type: The channel type to extract the median from.
        :return:The median value or 0.0 if the median value DNE.
        """
        idx = self.channel_index(channel_type)
        if idx < 0:
            return 0.0

        return self.value_medians[idx]

    def update_stats(self):
        """
        updates mean, std and median for all values
        """
        channel = self.payload
        step = len(self.channel_types)
        del self.protobuf_channel.value_means[:]
        del self.protobuf_channel.value_stds[:]
        del self.protobuf_channel.value_medians[:]
        for i in range(step):
            std, mean, median = redvox.api900.stat_utils.calc_utils(deinterleave_array(channel, i, step))
            self.protobuf_channel.value_means.append(mean)
            self.protobuf_channel.value_stds.append(std)
            self.protobuf_channel.value_medians.append(median)
        self.value_stds = repeated_to_array(self.protobuf_channel.value_stds)
        self.value_means = repeated_to_array(self.protobuf_channel.value_means)
        self.value_medians = repeated_to_array(self.protobuf_channel.value_medians)

    def set_sensor_name(self, name: str):
        """
        sets the sensor name
        :param name: name of sensor
        """
        self.sensor_name = name

    def set_metadata(self, data: typing.List[str]):
        """
        sets the metadata
        :param data: metadata as list of strings
        """
        del self.protobuf_channel.metadata[:]
        for meta in data:
            self.protobuf_channel.metadata.append(meta)
        self.metadata = repeated_to_list(self.protobuf_channel.metadata)

    def metadata_as_dict(self) -> typing.Dict[str, str]:
        """
        Returns any metadata as a dictionary of key-pair values.
        :return: Any metadata as a dictionary of key-pair values.
        """
        return get_metadata_as_dict(self.metadata)

    def __str__(self) -> str:
        """
        Returns a string representation of this interleaved channel.
        :return: A string representation of this interleaved chanel.
        """
        return "sensor_name: {}\n" \
               "channel_types: {}\n" \
               "len(payload): {}\n" \
               "payload_type: {}".format(self.sensor_name,
                                         list(map(
                                                 channel_type_name_from_enum,
                                                 self.channel_types)),
                                         len(self.payload),
                                         payload_type(
                                                 self.protobuf_channel))


class EvenlySampledChannel(InterleavedChannel):
    """
    An evenly sampled channel is an interleaved channel that also has a channel with an even sampling rate.
    """

    def __init__(self, channel: api900_pb2.EvenlySampledChannel = None):
        """
        Initializes this evenly sampled channel.
        :param channel: A protobuf evenly sampled channel.
        """
        if channel is None:
            InterleavedChannel.__init__(self, empty_evenly_sampled_channel())
            self.sample_rate_hz = None
            self.first_sample_timestamp_epoch_microseconds_utc = None
        else:
            InterleavedChannel.__init__(self, channel)
            self.sample_rate_hz: float = channel.sample_rate_hz
            """The sample rate in hz of this evenly sampled channel"""

            # pylint: disable=invalid-name
            self.first_sample_timestamp_epoch_microseconds_utc: int = \
                channel.first_sample_timestamp_epoch_microseconds_utc
            """The timestamp of the first sample"""

    def even_create(self, sensor_name: str, metadata: typing.List[str],
                    channel_types: typing.List[typing.Union[api900_pb2.EvenlySampledChannel,
                                                            api900_pb2.UnevenlySampledChannel]],
                    pyld_type: str, payload: numpy.array, payload_steps: int, rate: float, time: int):
        """
        Create an evenly sampled channel using native components
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param payload_steps: number of arrays interleaved
        :param pyld_type: payload type
        :param channel_types: list of payload types
        :param metadata: metadata
        :param rate: sample rate in hz
        :param time: timestamp of first sample in microsecond since epoch utc
        :return self: the evenly sampled channel with all values set
        """
        super().create(sensor_name, metadata, channel_types, pyld_type, payload, payload_steps)
        self.sample_rate_hz = rate
        self.first_sample_timestamp_epoch_microseconds_utc = time
        return self

    def even_create_from_deinterleaved_arrays(
            self, sensor_name: str, metadata: typing.List[str],
            channel_types: typing.List[typing.Union[api900_pb2.EvenlySampledChannel,
                                                    api900_pb2.UnevenlySampledChannel]],
            pyld_type: str, payload: typing.List[numpy.array], rate: float, time: int):
        """
        Create an evenly sampled channel using native components
        :param sensor_name: the sensor name
        :param payload: list of numpy arrays to interleave
        :param pyld_type: payload type
        :param channel_types: list of payload types
        :param metadata: metadata
        :param rate: sample rate in hz
        :param time: timestamp of first sample in microsecond since epoch utc
        :return self: the evenly sampled channel with all values set
        """
        self.even_create(sensor_name, metadata, channel_types, pyld_type, interleave_arrays(payload),
                         len(payload), rate, time)
        return self

    def set_channel(self, channel: api900_pb2.EvenlySampledChannel):
        """
        sets the channel to an evenly sampled channel
        :param channel: evenly sampled channel
        """
        super().set_channel(channel)
        self.sample_rate_hz = channel.sample_rate_hz
        self.first_sample_timestamp_epoch_microseconds_utc = channel.first_sample_timestamp_epoch_microseconds_utc

    def set_sample_rate_hz(self, rate: float):
        """
        sets the sample rate
        :param rate: sample rate in hz
        """
        self.sample_rate_hz = rate

    def set_first_sample_timestamp_epoch_microseconds_utc(self, time: int):
        """
        set the epoch in microseconds
        :param time: time in microseconds since epoch utc
        """
        self.first_sample_timestamp_epoch_microseconds_utc = time

    def __str__(self) -> str:
        """
        Returns a string representation of this evenly sampled channel.
        :return: A string representation of this evenly sampled channel.
        """
        return "{}\nsample_rate_hz: {}\nfirst_sample_timestamp_epoch_microseconds_utc: {}".format(
                super(EvenlySampledChannel, self).__str__(),
                self.sample_rate_hz,
                self.first_sample_timestamp_epoch_microseconds_utc)


class UnevenlySampledChannel(InterleavedChannel):
    """
    An unevenly sampled channel is an interleaved channel that contains sampled payload which includes a list of
    corresponding timestamps for each sample.

    This class also adds easy access to statistics for timestamps.
    """

    def __init__(self, channel: api900_pb2.UnevenlySampledChannel = None):
        """
        Initializes this unevenly sampled channel.
        :param channel: A protobuf unevenly sampled channel.
        """
        if channel is None:
            InterleavedChannel.__init__(self, empty_unevenly_sampled_channel())
            self.timestamps_microseconds_utc = empty_array()
            self.sample_interval_mean = None
            self.sample_interval_std = None
            self.sample_interval_median = None
        else:
            InterleavedChannel.__init__(self, channel)
            self.timestamps_microseconds_utc: numpy.ndarray = repeated_to_array(channel.timestamps_microseconds_utc)
            """Numpy array of timestamps epoch microseconds utc for each sample"""

            self.sample_interval_mean: float = channel.sample_interval_mean
            """The mean sample interval"""

            self.sample_interval_std: float = channel.sample_interval_std
            """The standard deviation of the sample interval"""

            self.sample_interval_median: float = channel.sample_interval_median
            """The median sample interval"""

    def uneven_create(self, sensor_name: str, metadata: typing.List[str],
                      channel_types: typing.List[typing.Union[api900_pb2.EvenlySampledChannel,
                                                              api900_pb2.UnevenlySampledChannel]],
                      pyld_type: str, payload: numpy.array, payload_steps: int, timestamps: numpy.ndarray):
        """
        Create an unevenly sampled channel using native components
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param payload_steps: number of arrays interleaved
        :param pyld_type: payload type
        :param channel_types: list of payload types
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the unevenly sampled channel with all values set
        """
        super().create(sensor_name, metadata, channel_types, pyld_type, payload, payload_steps)
        self.set_timestamps_microseconds_utc(timestamps)
        return self

    def uneven_create_from_deinterleaved_arrays(
            self, sensor_name: str, metadata: typing.List[str],
            channel_types: typing.List[typing.Union[api900_pb2.EvenlySampledChannel,
                                                    api900_pb2.UnevenlySampledChannel]],
            pyld_type: str, payload: typing.List[numpy.array], timestamps: numpy.ndarray):
        """
        Create an unevenly sampled channel using native components
        :param sensor_name: the sensor name
        :param payload: list of numpy arrays to interleave
        :param pyld_type: payload type
        :param channel_types: list of payload types
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the unevenly sampled channel with all values set
        """
        self.uneven_create(sensor_name, metadata, channel_types, pyld_type, interleave_arrays(payload),
                           len(payload), timestamps)
        return self

    def set_channel(self, channel: api900_pb2.UnevenlySampledChannel):
        """
        sets the channel to an unevenly sampled channel
        :param channel: unevenly sampled channel
        """
        super().set_channel(channel)
        self.timestamps_microseconds_utc = repeated_to_array(channel.timestamps_microseconds_utc)
        self.sample_interval_std, self.sample_interval_mean, self.sample_interval_median = \
            redvox.api900.stat_utils.calc_utils_timeseries(self.timestamps_microseconds_utc)

    def set_timestamps_microseconds_utc(self, timestamps: numpy.ndarray):
        """
        set the timestamps in microseconds from utc
        :param timestamps: array of timestamps
        """
        self.timestamps_microseconds_utc = timestamps
        self.sample_interval_std, self.sample_interval_mean, self.sample_interval_median = \
            redvox.api900.stat_utils.calc_utils_timeseries(timestamps)

    def __str__(self) -> str:
        """
        Returns a string representation of this unevenly sampled channel.
        :return: A string representation of this unevenly sampled channel.
        """
        return "{}\nlen(timestamps_microseconds_utc): {}".format(super().__str__(),
                                                                 len(self.timestamps_microseconds_utc))


class EvenlySampledSensor:
    """
    An EvenlySampledSensor provides a high level abstraction over an EvenlySampledChannel.

    This class exposes top level fields within API 900 evenly sampled channels.
    Composition is used instead of inheritance to hide the complexities of the underlying class.
    """

    def __init__(self, evenly_sampled_channel: EvenlySampledChannel = None):
        """
        Initializes this class.
        :param evenly_sampled_channel: an instance of an EvenlySampledChannel
        """
        if evenly_sampled_channel is None:
            self.evenly_sampled_channel = EvenlySampledChannel()
        else:
            self.evenly_sampled_channel: EvenlySampledChannel = evenly_sampled_channel
            """A reference to the original unevenly sampled channel"""

    def create(self, sensor_name: str, metadata: typing.List[str],
               channel_types: typing.List[typing.Union[api900_pb2.EvenlySampledChannel,
                                                       api900_pb2.UnevenlySampledChannel]],
               pyld_type: str, payload: numpy.array, payload_steps: int, rate: float, time: int):
        """
        Create an evenly sampled sensor using native components
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param payload_steps: number of arrays interleaved
        :param pyld_type: payload type
        :param channel_types: list of payload types
        :param metadata: metadata
        :param rate: sample rate in hz
        :param time: timestamp of first sample in microsecond since epoch utc
        :return self: the evenly sampled sensor with all values set
        """
        self.evenly_sampled_channel.even_create(sensor_name, metadata, channel_types, pyld_type, payload,
                                                payload_steps, rate, time)
        return self

    def create_from_deinterleaved_arrays(self, sensor_name: str, metadata: typing.List[str],
                                         channel_types: typing.List[typing.Union[api900_pb2.EvenlySampledChannel,
                                                                                 api900_pb2.UnevenlySampledChannel]],
                                         pyld_type: str, payload: typing.List[numpy.array], rate: float, time: int):
        """
        Create an evenly sampled sensor using native components
        :param sensor_name: the sensor name
        :param payload: list of numpy arrays to interleave
        :param pyld_type: payload type
        :param channel_types: list of payload types
        :param metadata: metadata
        :param rate: sample rate in hz
        :param time: timestamp of first sample in microsecond since epoch utc
        :return self: the evenly sampled sensor with all values set
        """
        self.create(sensor_name, metadata, channel_types, pyld_type, interleave_arrays(payload), len(payload),
                    rate, time)
        return self

    def set_channel(self, channel: EvenlySampledChannel):
        """
        sets the evenly sampled channel of the sensor
        :param channel: an evenly sampled channel
        """
        self.evenly_sampled_channel.set_channel(channel.protobuf_channel)

    def get_channel_type_names(self) -> typing.List[str]:
        """
        Returns the list of channel_types as a list of names instead of enumeration constants.
        :return: The list of channel_types as a list of names instead of enumeration constants.
        """
        return list(map(channel_type_name_from_enum, self.evenly_sampled_channel.channel_types))

    def sample_rate_hz(self) -> float:
        """
        Returns the sample rate in Hz of this evenly sampled channel.
        :return: The sample rate in Hz of this evenly sampled channel.
        """
        return self.evenly_sampled_channel.sample_rate_hz

    def set_sample_rate_hz(self, rate: float):
        """
        sets the sample rate
        :param rate: sample rate in hz
        """
        self.evenly_sampled_channel.set_sample_rate_hz(rate)

    # pylint: disable=invalid-name
    def first_sample_timestamp_epoch_microseconds_utc(self) -> int:
        """
        Return the first sample timestamp in microseconds since the epoch UTC.
        :return: The first sample timestamp in microseconds since the epoch UTC.
        """
        return self.evenly_sampled_channel.first_sample_timestamp_epoch_microseconds_utc

    def set_first_sample_timestamp_epoch_microseconds_utc(self, time: int):
        """
        sets the sample timestamp in microseconds since utc
        :param time: microseconds since utc
        """
        self.evenly_sampled_channel.set_first_sample_timestamp_epoch_microseconds_utc(time)

    def sensor_name(self) -> str:
        """
        Returns the sensor name associated with this evenly sampled chanel
        :return: The sensor name associated with this evenly sampled chanel
        """
        return self.evenly_sampled_channel.sensor_name

    def set_sensor_name(self, name: str):
        """
        sets the sensor name
        :param name: name of sensor
        """
        self.evenly_sampled_channel.set_sensor_name(name)

    def payload_type(self) -> str:
        """
        Returns the internal protobuf payload type.
        :return: The internal protobuf payload type.
        """
        return self.evenly_sampled_channel.get_payload_type()

    def metadata(self) -> typing.List[str]:
        """
        Returns this channel's metadata (if there is any) as a Python list.
        :return: This channel's metadata (if there is any) as a Python list.
        """
        return self.evenly_sampled_channel.metadata

    def set_metadata(self, data: typing.List[str]):
        """
        sets the metadata
        :param data: metadata as list of strings
        """
        self.evenly_sampled_channel.set_metadata(data)

    def metadata_as_dict(self) -> typing.Dict[str, str]:
        """
        Returns this channel's metadata (if there is any) as a Python dictionary.
        :return: This channel's metadata (if there is any) as a Python dictionary.
        """
        return get_metadata_as_dict(self.evenly_sampled_channel.metadata)

    def __str__(self):
        return str(self.evenly_sampled_channel)


class UnevenlySampledSensor:
    """
    An UnevenlySampledSensor provides a high level abstraction over an UnevenlySampledChannel.

    This class exposes top level fields within API 900 unevenly sampled channels.
    Composition is used instead of inheritance to hide the complexities of the underlying class.
    """

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        """
        Initializes this class.
        :param unevenly_sampled_channel: an instance of a UnevenlySampledChannel
        """
        if unevenly_sampled_channel is None:
            self.unevenly_sampled_channel = UnevenlySampledChannel()
        else:
            self.unevenly_sampled_channel: UnevenlySampledChannel = unevenly_sampled_channel

    def create(self, sensor_name: str, metadata: typing.List[str],
               channel_types: typing.List[typing.Union[api900_pb2.EvenlySampledChannel,
                                                       api900_pb2.UnevenlySampledChannel]],
               pyld_type: str, payload: numpy.array, payload_steps: int, timestamps: numpy.ndarray):
        """
        Create an unevenly sampled channel using native components
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param payload_steps: number of arrays interleaved
        :param pyld_type: payload type
        :param channel_types: list of payload types
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the unevenly sampled sensor with all values set
        """
        self.unevenly_sampled_channel.uneven_create(sensor_name, metadata, channel_types, pyld_type, payload,
                                                    payload_steps, timestamps)
        return self

    def create_from_deinterleaved_arrays(self, sensor_name: str, metadata: typing.List[str],
                                         channel_types: typing.List[typing.Union[api900_pb2.EvenlySampledChannel,
                                                                                 api900_pb2.UnevenlySampledChannel]],
                                         pyld_type: str, payload: typing.List[numpy.array], timestamps: numpy.ndarray):
        """
        Create an unevenly sampled channel using native components
        :param sensor_name: the sensor name
        :param payload: list of numpy arrays to interleave
        :param pyld_type: payload type
        :param channel_types: list of payload types
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the unevenly sampled sensor with all values set
        """
        self.create(sensor_name, metadata, channel_types, pyld_type, interleave_arrays(payload),
                    len(payload), timestamps)
        return self

    def set_channel(self, channel: UnevenlySampledChannel):
        """
        sets the unevenly sampled channel of the sensor
        :param channel: an unevenly sampled channel
        """
        self.unevenly_sampled_channel.set_channel(channel.protobuf_channel)

    def get_channel_type_names(self) -> typing.List[str]:
        """
        Returns the list of channel_types as a list of names instead of enumeration constants.
        :return: The list of channel_types as a list of names instead of enumeration constants.
        """
        return list(map(channel_type_name_from_enum, self.unevenly_sampled_channel.channel_types))

    def sensor_name(self) -> str:
        """
        Returns the sensor name associated with this unevenly sampled channel.
        :return: The sensor name associated with this unevenly sampled channel.
        """
        return self.unevenly_sampled_channel.sensor_name

    def set_sensor_name(self, name: str):
        """
        Sets the sensor name
        :param name: name of the sensor
        """
        self.unevenly_sampled_channel.set_sensor_name(name)

    def payload_type(self) -> str:
        """
        Returns the internal protobuf payload type.
        :return: The internal protobuf payload type.
        """
        return self.unevenly_sampled_channel.get_payload_type()

    def timestamps_microseconds_utc(self) -> numpy.ndarray:
        """
        Returns a list of ascending timestamps that associate with each sample value
        :return: A list of ascending timestamps that associate with each sample value
        """
        return self.unevenly_sampled_channel.timestamps_microseconds_utc

    def set_timestamps_microseconds_utc(self, timestamps: numpy.ndarray):
        """
        set the time stamps
        :param timestamps: a list of ascending timestamps that associate with each sample value
        """
        self.unevenly_sampled_channel.set_timestamps_microseconds_utc(timestamps)

    def sample_interval_mean(self) -> float:
        """
        Returns the mean sample interval for this unevenly sampled sensor channel.
        :return: The mean sample interval for this unevenly sampled sensor channel.
        """
        return self.unevenly_sampled_channel.sample_interval_mean

    def sample_interval_median(self) -> float:
        """
        Returns the median sample interval for this unevenly sampled sensor channel.
        :return: The median sample interval for this unevenly sampled sensor channel.
        """
        return self.unevenly_sampled_channel.sample_interval_median

    def sample_interval_std(self) -> float:
        """
        Returns the standard deviation sample interval for this unevenly sampled sensor channel.
        :return: The standard deviation sample interval for this unevenly sampled sensor channel.
        """
        return self.unevenly_sampled_channel.sample_interval_std

    def metadata(self) -> typing.List[str]:
        """
        Returns this channel's metadata (if there is any) as a Python list.
        :return: This channel's metadata (if there is any) as a Python list.
        """
        return self.unevenly_sampled_channel.metadata

    def set_metadata(self, data: typing.List[str]):
        """
        sets the metadata
        :param data: metadata as list of strings
        """
        self.unevenly_sampled_channel.set_metadata(data)

    def metadata_as_dict(self) -> typing.Dict[str, str]:
        """
        Returns this channel's metadata (if there is any) as a Python dictionary.
        :return: This channel's metadata (if there is any) as a Python dictionary.
        """
        return get_metadata_as_dict(self.unevenly_sampled_channel.metadata)

    def __str__(self):
        return str(self.unevenly_sampled_channel)


class XyzUnevenlySampledSensor(UnevenlySampledSensor):
    """
    This class subclasses the UnevenlySampledSensor class and provides methods for working with channels that provide
    data in the X, Y, and Z dimensions.
    """

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel, x_type: int, y_type: int, z_type: int):
        """
        Initializes this class.
        :param unevenly_sampled_channel: An instance of an UnevenlySampledChannel.
        :param x_type: The X channel type enum.
        :param y_type: The Y channel type enum.
        :param z_type: The Z channel type enum.
        """
        super().__init__(unevenly_sampled_channel)
        self.unevenly_sampled_channel.set_channel_types([x_type, y_type, z_type])
        self.x_type = x_type
        self.y_type = y_type
        self.z_type = z_type

    def xyz_create(self, sensor_name: str, metadata: typing.List[str], x_type: int, y_type: int, z_type: int,
                   pyld_type: str, payload: numpy.array, timestamps: numpy.ndarray):
        """
        Create an unevenly sampled sensor using native components
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param pyld_type: payload type
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :param x_type: The X channel type enum.
        :param y_type: The Y channel type enum.
        :param z_type: The Z channel type enum.
        :return self: the xyz unevenly sampled sensor with all values set
        """
        super().create(sensor_name, metadata, [x_type, y_type, z_type], pyld_type, payload, 3, timestamps)
        return self

    def xyz_create_from_deinterleaved_arrays(self, sensor_name: str, metadata: typing.List[str],
                                             x_type: int, y_type: int, z_type: int, pyld_type: str,
                                             payload: typing.List[numpy.array], timestamps: numpy.ndarray):
        """
        Create an unevenly sampled sensor using native components
        :param sensor_name: the sensor name
        :param payload: list of numpy arrays to interleave
        :param pyld_type: payload type
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :param x_type: The X channel type enum.
        :param y_type: The Y channel type enum.
        :param z_type: The Z channel type enum.
        :return self: the xyz unevenly sampled sensor with all values set
        """
        self.xyz_create(sensor_name, metadata, x_type, y_type, z_type, pyld_type, interleave_arrays(payload),
                        timestamps)
        return self

    def set_xyz_channel(self, channel: UnevenlySampledChannel, x_type: int, y_type: int, z_type: int):
        """
        sets the channel to an instance of an unevenly sampled sensor
        :param channel: An instance of an UnevenlySampledChannel.
        :param x_type: The X channel type enum.
        :param y_type: The Y channel type enum.
        :param z_type: The Z channel type enum.
        """
        super().set_channel(channel)
        self.unevenly_sampled_channel.channel_types = [x_type, y_type, z_type]
        self.x_type = x_type
        self.y_type = y_type
        self.z_type = z_type

    def x_type(self) -> int:
        """
        returns the x type enumerator
        :return: This sensor's x type enum value
        """
        return self.x_type

    def set_x_type(self, chan_type: int):
        """
        sets the x type
        :param chan_type: channel type enumeration
        """
        self.x_type = chan_type
        self.unevenly_sampled_channel.channel_types = [self.x_type, self.y_type, self.z_type]

    def x_type_name(self) -> str:
        """
        returns the x type enum as a string
        :return: x type name as string
        """
        return channel_type_name_from_enum(self.x_type)

    def y_type(self) -> int:
        """
        returns the y type enumerator
        :return: This sensor's y type enum value
        """
        return self.y_type

    def set_y_type(self, chan_type: int):
        """
        sets the y type
        :param chan_type: channel type enumeration
        """
        self.y_type = chan_type
        self.unevenly_sampled_channel.channel_types = [self.x_type, self.y_type, self.z_type]

    def y_type_name(self) -> str:
        """
        returns the y type enum as a string
        :return: y type name as string
        """
        return channel_type_name_from_enum(self.y_type)

    def z_type(self) -> int:
        """
        returns the z type enumerator
        :return: This sensor's z type enum value
        """
        return self.z_type

    def set_z_type(self, chan_type: int):
        """
        sets the z type
        :param chan_type: channel type enumeration
        """
        self.z_type = chan_type
        self.unevenly_sampled_channel.channel_types = [self.x_type, self.y_type, self.z_type]

    def z_type_name(self) -> str:
        """
        returns the z type enum as a string
        :return: z type name as string
        """
        return channel_type_name_from_enum(self.z_type)

    def payload_values(self) -> numpy.ndarray:
        """
        Returns this channel's payload as an interleaved payload of the form
        [[x_0, y_0, z_0], [x_1, y_1, z_1], ..., [x_n, y_n, z_n]].
        :return: This channel's payload as an interleaved payload.
        """
        return self.unevenly_sampled_channel.get_multi_payload([
            self.x_type,
            self.y_type,
            self.z_type
        ])

    def payload_values_x(self) -> numpy.ndarray:
        """
        Returns the x-component of this channel's payload.
        :return: The x-component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_payload(self.x_type)

    def payload_values_y(self) -> numpy.ndarray:
        """
        Returns the y-component of this channel's payload.
        :return: The y-component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_payload(self.y_type)

    def payload_values_z(self) -> numpy.ndarray:
        """
        Returns the z-component of this channel's payload.
        :return: The z-component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_payload(self.z_type)

    def payload_values_x_mean(self) -> float:
        """
        Returns the x-component mean of this channel's payload.
        :return: The x-component mean of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_mean(self.x_type)

    def payload_values_y_mean(self) -> float:
        """
        Returns the y-component mean of this channel's payload.
        :return: The y-component mean of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_mean(self.y_type)

    def payload_values_z_mean(self) -> float:
        """
        Returns the z-component mean of this channel's payload.
        :return: The z-component mean of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_mean(self.z_type)

    def payload_values_x_median(self) -> float:
        """
        Returns the x-component median of this channel's payload.
        :return: The x-component median of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_median(self.x_type)

    def payload_values_y_median(self) -> float:
        """
        Returns the y-component median of this channel's payload.
        :return: The y-component median of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_median(self.y_type)

    def payload_values_z_median(self) -> float:
        """
        Returns the z-component median of this channel's payload.
        :return: The z-component median of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_median(self.z_type)

    def payload_values_x_std(self) -> float:
        """
        Returns the x-component standard deviation of this channel's payload.
        :return: The x-component standard deviation of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_std(self.x_type)

    def payload_values_y_std(self) -> float:
        """
        Returns the y-component standard deviation of this channel's payload.
        :return: The y-component standard deviation of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_std(self.y_type)

    def payload_values_z_std(self) -> float:
        """
        Returns the z-component standard deviation of this channel's payload.
        :return: The z-component standard deviation of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_std(self.z_type)


class MicrophoneSensor(EvenlySampledSensor):
    """
    High-level wrapper around microphone channels.
    """

    def __init__(self, evenly_sampled_channel: EvenlySampledChannel = None):
        """
        Initialized this channel.
        :param evenly_sampled_channel: An instance of an EvenlySampledChannel with microphone data.
        """
        super().__init__(evenly_sampled_channel)
        self.evenly_sampled_channel.set_channel_types([api900_pb2.MICROPHONE])

    def create_microphone(self, sensor_name: str, metadata: typing.List[str], payload: numpy.array,
                          rate: float, time: int):
        """
        Create a microphone sensor, using int32 as payload type
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param metadata: metadata
        :param rate: sample rate in hz
        :param time: timestamp of first sample in microsecond since epoch utc
        :return self: the microphone sensor with all values set
        """
        super().create(sensor_name, metadata, [api900_pb2.MICROPHONE], "int32_payload", payload, 1, rate, time)
        return self

    def payload_values(self) -> numpy.ndarray:
        """
        Returns the microphone payload as a numpy ndarray of integers.
        :return: The microphone payload as a numpy ndarray of integers.
        """
        return self.evenly_sampled_channel.get_payload(api900_pb2.MICROPHONE)

    def payload_mean(self) -> float:
        """Returns the mean of this channel's payload.
        :return: The mean of this channel's payload.
        """
        return self.evenly_sampled_channel.get_value_mean(api900_pb2.MICROPHONE)

    # Currently, our Android and iOS devices don't calculate a median value, so we calculate it here
    # If the payload is set manually, the median value is calculated by the API
    def payload_median(self) -> numpy.float64:
        """Returns the median of this channel's payload.
        :return: The median of this channel's payload.
        """
        payload_values = self.payload_values()

        if len(payload_values) <= 0:
            raise ReaderException("Can't obtain median value of empty array")

        median = numpy.median(self.payload_values())

        if isinstance(median, numpy.ndarray):
            return median[0]
        elif isinstance(median, numpy.float64):
            return median
        else:
            raise ReaderException("Unknown type %s" % str(type(median)))

    def payload_std(self) -> float:
        """Returns the standard deviation of this channel's payload.
        :return: The standard deviation of this channel's payload.
        """
        return self.evenly_sampled_channel.get_value_std(api900_pb2.MICROPHONE)


class BarometerSensor(UnevenlySampledSensor):
    """
    High-level wrapper around barometer channels.
    """

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        """
        Initialize this channel
        :param unevenly_sampled_channel: Instance of UnevenlySampledChannel with barometer data
        """
        super().__init__(unevenly_sampled_channel)
        self.unevenly_sampled_channel.set_channel_types([api900_pb2.BAROMETER])

    def create_barometer(self, sensor_name: str, metadata: typing.List[str], payload: numpy.array,
                         timestamps: numpy.ndarray):
        """
        Create a barometer sensor using float64 as payload type
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the barometer sensor with all values set
        """
        super().create(sensor_name, metadata, [api900_pb2.BAROMETER], "float64_payload", payload, 1, timestamps)
        return self

    def payload_values(self) -> numpy.ndarray:
        """
        Returns this channels payload as a numpy ndarray of floats.
        :return: This channels payload as a numpy ndarray of floats.
        """
        return self.unevenly_sampled_channel.get_payload(api900_pb2.BAROMETER)

    def payload_mean(self) -> float:
        """Returns the mean of this channel's payload.
        :return: The mean of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_mean(api900_pb2.BAROMETER)

    def payload_median(self) -> float:
        """Returns the median of this channel's payload.
        :return: The median of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_median(api900_pb2.BAROMETER)

    def payload_std(self) -> float:
        """Returns the standard deviation of this channel's payload.
        :return: The standard deviation of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_std(api900_pb2.BAROMETER)


# pylint: disable=R0904
class LocationSensor(UnevenlySampledSensor):
    """
    High-level wrapper around location channels.
    """

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        """
        Initialize this channel
        :param unevenly_sampled_channel: Instance of UnevenlySampledChannel containing location data
        """
        super().__init__(unevenly_sampled_channel)
        self.unevenly_sampled_channel.set_channel_types([
            api900_pb2.LATITUDE,
            api900_pb2.LONGITUDE,
            api900_pb2.ALTITUDE,
            api900_pb2.SPEED,
            api900_pb2.ACCURACY
        ])

    def create_location(self, sensor_name: str, metadata: typing.List[str], payload: numpy.array,
                        timestamps: numpy.ndarray):
        """
        Create a location sensor using float64 as payload type
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the location sensor with all values set
        """
        super().create(sensor_name, metadata,
                       [api900_pb2.LATITUDE,
                        api900_pb2.LONGITUDE,
                        api900_pb2.ALTITUDE,
                        api900_pb2.SPEED,
                        api900_pb2.ACCURACY],
                       "float64_payload", payload, 5, timestamps)
        return self

    def create_location_from_deinterleaved_arrays(self, sensor_name: str, metadata: typing.List[str],
                                                  payload: typing.List[numpy.array], timestamps: numpy.ndarray):
        """
        Create a location sensor using float64 as payload type
        :param sensor_name: the sensor name
        :param payload: list of numpy arrays to interleave
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the location sensor with all values set
        """
        super().create_from_deinterleaved_arrays(sensor_name, metadata,
                                                 [api900_pb2.LATITUDE,
                                                  api900_pb2.LONGITUDE,
                                                  api900_pb2.ALTITUDE,
                                                  api900_pb2.SPEED,
                                                  api900_pb2.ACCURACY],
                                                 "float64_payload", payload, timestamps)
        return self

    def payload_values(self):
        """
        Return the location payload as an interleaved payload with the following format:
        [[latitude_0, longitude_0, altitude_0, speed_0, accuracy_0],
         [latitude_1, longitude_1, altitude_1, speed_1, accuracy_1],
         ...,
         [latitude_n, longitude_n, altitude_n, speed_n, accuracy_n],]
        :return: array containing interleaved values of the 5 channels
        """
        return self.unevenly_sampled_channel.get_multi_payload([
            api900_pb2.LATITUDE,
            api900_pb2.LONGITUDE,
            api900_pb2.ALTITUDE,
            api900_pb2.SPEED,
            api900_pb2.ACCURACY
        ])

    def payload_values_latitude(self):
        """
        Returns the latitude component of this channel's payload.
        :return: The latitude component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_payload(api900_pb2.LATITUDE)

    def payload_values_longitude(self):
        """
        Returns the longitude component of this channel's payload.
        :return: The longitude component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_payload(api900_pb2.LONGITUDE)

    def payload_values_altitude(self):
        """
        Returns the altitude component of this channel's payload.
        :return: The altitude component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_payload(api900_pb2.ALTITUDE)

    def payload_values_speed(self):
        """
        Returns the speed component of this channel's payload.
        :return: The speed component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_payload(api900_pb2.SPEED)

    def payload_values_accuracy(self):
        """
        Returns the accuracy component of this channel's payload.
        :return: The accuracy component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_payload(api900_pb2.ACCURACY)

    def payload_values_latitude_mean(self) -> float:
        """
        Returns the mean latitude component of this channel's payload.
        :return: The mean latitude component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_mean(api900_pb2.LATITUDE)

    def payload_values_longitude_mean(self) -> float:
        """
        Returns the mean longitude component of this channel's payload.
        :return: The mean longitude component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_mean(api900_pb2.LONGITUDE)

    def payload_values_altitude_mean(self) -> float:
        """
        Returns the mean altitude component of this channel's payload.
        :return: The mean altitude component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_mean(api900_pb2.ALTITUDE)

    def payload_values_speed_mean(self) -> float:
        """
        Returns the mean speed component of this channel's payload.
        :return: The mean speed component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_mean(api900_pb2.SPEED)

    def payload_values_accuracy_mean(self) -> float:
        """
        Returns the mean accuracy component of this channel's payload.
        :return: The mean accuracy component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_mean(api900_pb2.ACCURACY)

    def payload_values_latitude_median(self) -> float:
        """
        Returns the median latitude component of this channel's payload.
        :return: The median latitude component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_median(api900_pb2.LATITUDE)

    def payload_values_longitude_median(self) -> float:
        """
        Returns the median longitude component of this channel's payload.
        :return: The median longitude component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_median(api900_pb2.LONGITUDE)

    def payload_values_altitude_median(self) -> float:
        """
        Returns the median altitude component of this channel's payload.
        :return: The median altitude component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_median(api900_pb2.ALTITUDE)

    def payload_values_speed_median(self) -> float:
        """
        Returns the median speed component of this channel's payload.
        :return: The median speed component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_median(api900_pb2.SPEED)

    def payload_values_accuracy_median(self) -> float:
        """
        Returns the median accuracy component of this channel's payload.
        :return: The median accuracy component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_median(api900_pb2.ACCURACY)

    def payload_values_latitude_std(self) -> float:
        """
        Returns the standard deviation latitude component of this channel's payload.
        :return: The standard deviation latitude component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_std(api900_pb2.LATITUDE)

    def payload_values_longitude_std(self) -> float:
        """
        Returns the standard deviation longitude component of this channel's payload.
        :return: The standard deviation longitude component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_std(api900_pb2.LONGITUDE)

    def payload_values_altitude_std(self) -> float:
        """
        Returns the standard deviation altitude component of this channel's payload.
        :return: The standard deviation altitude component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_std(api900_pb2.ALTITUDE)

    def payload_values_speed_std(self) -> float:
        """
        Returns the standard deviation speed component of this channel's payload.
        :return: The standard deviation speed component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_std(api900_pb2.SPEED)

    def payload_values_accuracy_std(self) -> float:
        """
        Returns the standard deviation accuracy component of this channel's payload.
        :return: The standard deviation accuracy component of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_std(api900_pb2.ACCURACY)


class TimeSynchronizationSensor():
    """High-level wrapper around time synchronization exchange.

    It should be noted that this class only exposes a single method, payload values.
    """

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        """
        Initialized this class.
        :param unevenly_sampled_channel: An unevenly sampled channel with time synchronization payload.
        """
        if unevenly_sampled_channel is None:
            self.unevenly_sampled_channel = UnevenlySampledChannel()
        else:
            self.unevenly_sampled_channel = UnevenlySampledChannel(unevenly_sampled_channel.protobuf_channel)
        self.unevenly_sampled_channel.set_channel_types([api900_pb2.TIME_SYNCHRONIZATION])

    def create_time(self, sensor_name: str, metadata: typing.List[str], payload: numpy.array):
        """
        Create a time synchronization sensor using int64 as payload type
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param metadata: metadata
        :return self: the time synchronization sensor with all values set
        """
        self.unevenly_sampled_channel.uneven_create(sensor_name, metadata, [api900_pb2.TIME_SYNCHRONIZATION],
                                                    "int64_payload", payload, 1, empty_array())
        return self

    def payload_type(self) -> str:
        """
        Returns the internal protobuf payload type.
        :return: The internal protobuf payload type.
        """
        return self.unevenly_sampled_channel.get_payload_type()

    def payload_values(self) -> numpy.ndarray:
        """
        Returns the time synchronization exchanges as a numpy ndarray of integers.
        :return: The time synchronization exchanges as a numpy ndarray of integers.
        """
        return self.unevenly_sampled_channel.get_payload(api900_pb2.TIME_SYNCHRONIZATION)

    def metadata(self) -> typing.List[str]:
        """
        Returns this channel's metadata (if there is any) as a Python list.
        :return: This channel's metadata (if there is any) as a Python list.
        """
        return self.unevenly_sampled_channel.metadata

    def set_metadata(self, data: typing.List[str]):
        """
        sets the metadata
        :param data: metadata as list of strings
        """
        self.unevenly_sampled_channel.set_metadata(data)

    def metadata_as_dict(self) -> typing.Dict[str, str]:
        """
        Returns this channel's metadata (if there is any) as a Python dictionary.
        :return: This channel's metadata (if there is any) as a Python dictionary.
        """
        return get_metadata_as_dict(self.unevenly_sampled_channel.metadata)

    def __str__(self):
        return str(self.unevenly_sampled_channel)


class AccelerometerSensor(XyzUnevenlySampledSensor):
    """High-level wrapper around accelerometer channels."""

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        """
        Initializes this class.
        :param unevenly_sampled_channel: An instance of an UnevenlySampledChanel which contains accelerometer
        X, Y, and Z payload components.
        """
        super().__init__(unevenly_sampled_channel,
                         api900_pb2.ACCELEROMETER_X,
                         api900_pb2.ACCELEROMETER_Y,
                         api900_pb2.ACCELEROMETER_Z)

    def create_accelerometer(self, sensor_name: str, metadata: typing.List[str], payload: numpy.array,
                             timestamps: numpy.ndarray):
        """
        Create an accelerometer sensor using float64 as datatype
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the accelerometer sensor with all values set
        """
        super().xyz_create(sensor_name, metadata, api900_pb2.ACCELEROMETER_X, api900_pb2.ACCELEROMETER_Y,
                           api900_pb2.ACCELEROMETER_Z, "float64_payload", payload, timestamps)
        return self

    def create_accelerometer_from_deinterleaved_arrays(self, sensor_name: str, metadata: typing.List[str],
                                                       payload: typing.List[numpy.array], timestamps: numpy.ndarray):
        """
        Create an accelerometer sensor using float64 as datatype
        :param sensor_name: the sensor name
        :param payload: list of numpy arrays to interleave
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the accelerometer sensor with all values set
        """
        super().xyz_create_from_deinterleaved_arrays(sensor_name, metadata, api900_pb2.ACCELEROMETER_X,
                                                     api900_pb2.ACCELEROMETER_Y, api900_pb2.ACCELEROMETER_Z,
                                                     "float64_payload", payload, timestamps)
        return self

    def payload_values(self) -> numpy.ndarray:
        """
        returns the sensor payload as a numpy ndarray
        :return: accelerometer payload as a numpy ndarray
        """
        return self.unevenly_sampled_channel.get_multi_payload([
            api900_pb2.ACCELEROMETER_X,
            api900_pb2.ACCELEROMETER_Y,
            api900_pb2.ACCELEROMETER_Z
        ])


class MagnetometerSensor(XyzUnevenlySampledSensor):
    """
    Initializes this class.
    :param unevenly_sampled_channel: An instance of an UnevenlySampledChanel which contains magnetometer
    X, Y, and Z payload components.
    """

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        super().__init__(unevenly_sampled_channel,
                         api900_pb2.MAGNETOMETER_X,
                         api900_pb2.MAGNETOMETER_Y,
                         api900_pb2.MAGNETOMETER_Z)

    def create_magnetometer(self, sensor_name: str, metadata: typing.List[str], payload: numpy.array,
                             timestamps: numpy.ndarray):
        """
        Create a magnetometer sensor using float64 as datatype
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the magnetometer sensor with all values set
        """
        super().xyz_create(sensor_name, metadata, api900_pb2.MAGNETOMETER_X, api900_pb2.MAGNETOMETER_Y,
                           api900_pb2.MAGNETOMETER_Z, "float64_payload", payload, timestamps)
        return self

    def create_magnetometer_from_deinterleaved_arrays(self, sensor_name: str, metadata: typing.List[str],
                                                      payload: typing.List[numpy.array], timestamps: numpy.ndarray):
        """
        Create a magnetometer sensor using float64 as datatype
        :param sensor_name: the sensor name
        :param payload: list of numpy arrays to interleave
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the magnetometer sensor with all values set
        """
        super().xyz_create_from_deinterleaved_arrays(sensor_name, metadata, api900_pb2.MAGNETOMETER_X,
                                                     api900_pb2.MAGNETOMETER_Y, api900_pb2.MAGNETOMETER_Z,
                                                     "float64_payload", payload, timestamps)
        return self

    def payload_values(self) -> numpy.ndarray:
        """
        returns the sensor payload as a numpy ndarray
        :return: magnetometer payload as a numpy ndarray
        """
        return self.unevenly_sampled_channel.get_multi_payload([
            api900_pb2.MAGNETOMETER_X,
            api900_pb2.MAGNETOMETER_Y,
            api900_pb2.MAGNETOMETER_Z
        ])


class GyroscopeSensor(XyzUnevenlySampledSensor):
    """
    Initializes this class.
    :param unevenly_sampled_channel: An instance of an UnevenlySampledChanel which contains gyroscope
    X, Y, and Z payload components.
    """

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        super().__init__(unevenly_sampled_channel,
                         api900_pb2.GYROSCOPE_X,
                         api900_pb2.GYROSCOPE_Y,
                         api900_pb2.GYROSCOPE_Z)

    def create_gyroscope(self, sensor_name: str, metadata: typing.List[str], payload: numpy.array,
                         timestamps: numpy.ndarray):
        """
        Create a gyroscope sensor using float64 as datatype
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the gyrocope sensor with all values set
        """
        super().xyz_create(sensor_name, metadata, api900_pb2.GYROSCOPE_X, api900_pb2.GYROSCOPE_Y,
                           api900_pb2.GYROSCOPE_Z, "float64_payload", payload, timestamps)
        return self

    def create_gyroscope_from_deinterleaved_arrays(self, sensor_name: str, metadata: typing.List[str],
                                                   payload: typing.List[numpy.array], timestamps: numpy.ndarray):
        """
        Create a gyroscope sensor using float64 as datatype
        :param sensor_name: the sensor name
        :param payload: list of numpy arrays to interleave
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the gyroscope sensor with all values set
        """
        super().xyz_create_from_deinterleaved_arrays(sensor_name, metadata, api900_pb2.GYROSCOPE_X,
                                                     api900_pb2.GYROSCOPE_Y, api900_pb2.GYROSCOPE_Z,
                                                     "float64_payload", payload, timestamps)
        return self

    def payload_values(self) -> numpy.ndarray:
        """
        returns the sensor payload as a numpy ndarray
        :return: gyroscope payload as a numpy ndarray
        """
        return self.unevenly_sampled_channel.get_multi_payload([
            api900_pb2.GYROSCOPE_X,
            api900_pb2.GYROSCOPE_Y,
            api900_pb2.GYROSCOPE_Z
        ])


class LightSensor(UnevenlySampledSensor):
    """High-level wrapper around light channels."""

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        """
        Initializes this class
        :param unevenly_sampled_channel: Instance of UnevenlySampledChannel with light sensor payload
        """
        super().__init__(unevenly_sampled_channel)
        self.unevenly_sampled_channel.set_channel_types([api900_pb2.LIGHT])

    def create_light(self, sensor_name: str, metadata: typing.List[str], payload: numpy.array,
                     timestamps: numpy.ndarray):
        """
        Create a light sensor using float64 as payload type
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the light sensor with all values set
        """
        super().create(sensor_name, metadata, [api900_pb2.LIGHT], "float64_payload", payload, 1, timestamps)
        return self

    def payload_values(self) -> numpy.ndarray:
        """
        Returns a numpy ndarray of floats representing this light sensor's payload.
        :return: A numpy ndarray of floats representing this light sensor's payload.
        """
        return self.unevenly_sampled_channel.get_payload(api900_pb2.LIGHT)

    def payload_mean(self) -> float:
        """
        The mean of this channel's payload.
        :return: Mean of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_mean(api900_pb2.LIGHT)

    def payload_median(self) -> float:
        """
        The median of this channel's payload.
        :return: Median of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_median(api900_pb2.LIGHT)

    def payload_std(self) -> float:
        """
        The standard deviation of this channel's payload.
        :return: Standard deviation of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_std(api900_pb2.LIGHT)


class InfraredSensor(UnevenlySampledSensor):
    """High-level wrapper around light channels."""

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        """
        Initializes this class
        :param unevenly_sampled_channel: UnevenlySampledChannel with infrared sensor payload
        """
        super().__init__(unevenly_sampled_channel)
        self.unevenly_sampled_channel.set_channel_types([api900_pb2.INFRARED])

    def create_infrared(self, sensor_name: str, metadata: typing.List[str], payload: numpy.array,
                        timestamps: numpy.ndarray):
        """
        Create an infrared sensor using float64 as payload type
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the infrared sensor with all values set
        """
        super().create(sensor_name, metadata, [api900_pb2.INFRARED], "float64_payload", payload, 1, timestamps)
        return self

    def payload_values(self) -> numpy.ndarray:
        """
        Returns a numpy ndarray of floats representing this sensor's payload.
        :return: A numpy ndarray of floats representing this sensor's payload.
        """
        return self.unevenly_sampled_channel.get_payload(api900_pb2.INFRARED)

    def payload_mean(self) -> float:
        """
        The mean of this channel's payload.
        :return: Mean of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_mean(api900_pb2.INFRARED)

    def payload_median(self) -> float:
        """
        The median of this channel's payload.
        :return: Median of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_median(api900_pb2.INFRARED)

    def payload_std(self) -> float:
        """
        The standard deviation of this channel's payload.
        :return: Standard deviation of this channel's payload.
        """
        return self.unevenly_sampled_channel.get_value_std(api900_pb2.INFRARED)


class ImageSensor(UnevenlySampledSensor):
    """High-level wrapper around image channels."""

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        """
        Initializes this ImageSensor.
        :param unevenly_sampled_channel: The image channel.
        """
        super().__init__(unevenly_sampled_channel)
        self.unevenly_sampled_channel.set_channel_types([api900_pb2.IMAGE])

        self.image_offsets: typing.List[int] = self.parse_offsets()
        """A list of image byte offsets into the payload of this sensor channel."""

    def create_image(self, sensor_name: str, metadata: typing.List[str], payload: numpy.array,
                     timestamps: numpy.ndarray):
        """
        Create an image sensor using float64 as payload type
        :param sensor_name: the sensor name
        :param payload: interleaved numpy array or deinterleaved list of numpy arrays
        :param metadata: metadata
        :param timestamps: list of sample timestamps in microseconds since epoch utc
        :return self: the image sensor with all values set
        """
        super().create(sensor_name, metadata, [api900_pb2.IMAGE], "float64_payload", payload, 1, timestamps)
        self.image_offsets = self.parse_offsets()
        return self

    def set_channel(self, channel: UnevenlySampledChannel):
        """
        Sets the channel to an unevenly sampled channel
        :param channel: Unevenly sampled channel with image payload
        """
        super().set_channel(channel)
        self.image_offsets = self.parse_offsets()

    def parse_offsets(self) -> typing.List[int]:
        """
        Parses the metadata of this channel to extract the image byte offsets into the payload.
        :return: A list of image byte offsets.
        """
        meta = self.metadata_as_dict()
        if "images" in meta:
            offsets_line = meta["images"].replace("[", "").replace("]", "")
            try:
                return list(map(int, offsets_line.split(",")))
            except ValueError:
                return []
        else:
            return []

    def image_offsets(self) -> typing.List[int]:
        """
        Returns the byte offsets for each image in the payload.
        :return: The byte offsets for each image in the payload.
        """
        return self.image_offsets

    def payload_values(self) -> numpy.ndarray:
        """
        Returns a numpy ndarray of uint8s representing this sensor's payload. This byte blob may contain multiple
        images. The byte offset of each image should be stored in this channels metadata as images="[offset_0,
        offset_1, ..., offset_n]".
        :return: A numpy ndarray of floats representing this sensor's payload.
        """
        return self.unevenly_sampled_channel.get_payload(api900_pb2.IMAGE)

    def num_images(self) -> int:
        """
        Returns the number of images in this packet's image channel.
        :return: The number of images in this packet's image channel.
        """
        return len(self.image_offsets)

    def get_image_bytes(self, idx: int) -> numpy.ndarray:
        """
        Return the bytes associated with an image at this channel's given image index.
        :param idx: The image from this channel to retrieve (starting from 0).
        :return: A numpy array of uint8s representing the bytes of a selected image.
        """
        if idx < 0 or idx >= self.num_images():
            raise RuntimeError("idx must be between 0 and the total number of images available in this packet %s" %
                               str(self.num_images()))

        if idx == self.num_images() - 1:
            return self.payload_values()[self.image_offsets[idx]:]

        return self.payload_values()[self.image_offsets[idx]:self.image_offsets[idx + 1]]

    def write_image_to_file(self, idx: int, path: str):
        """
        Writes an image to a file with a given file name.
        :param idx: The index of the image in this channel (starting at 0).
        :param path: The full path and file name to save this image as.
        """
        self.get_image_bytes(idx).tofile(path)

    def default_filename(self, idx: int) -> str:
        """
        Returns the default file name for the image at the given index by using the timestamp of the image.
        :param idx: The index of the image in this channel (starting at 0).
        :return: A default filename of the format timestamp.jpg.
        """
        return "{}.jpg".format(self.timestamps_microseconds_utc()[idx])

    def write_all_images_to_directory(self, directory: str = "."):
        """
        Write all images in this packet to the provided directory using default filenames.
        :param directory: The directory to write the images to.
        """
        for i in range(self.num_images()):
            self.write_image_to_file(i, "{}/{}".format(directory, self.default_filename(i)))

    def get_image_offsets(self) -> typing.List[int]:
        """
        Returns the byte offsets for each image in the payload.
        :return: The byte offsets for each image in the payload.
        """
        return self.image_offsets

    def __str__(self):
        """Provide image information in str of this instance"""
        return "{}\nnum images: {}\nbyte offsets: {}".format(self.unevenly_sampled_channel,
                                                             self.num_images(),
                                                             self.image_offsets)


# pylint: disable=R0904
class WrappedRedvoxPacket:
    """
    This class provides convenience methods for accessing API 900 protobuf redvox packets.

    This packet contains a reference to the original packet which should be used to access all "top-level" fields. For
    accessing channels, this class can search for and return our high-level channel wrappers or can extract the payload
    directly.
    """

    def __init__(self, redvox_packet: api900_pb2.RedvoxPacket = None):
        """
        Initializes this wrapped redvox packet.
        :param redvox_packet: A protobuf redvox packet.
        """
        if redvox_packet is None:
            self.redvox_packet = api900_pb2.RedvoxPacket()
            self.evenly_sampled_channels = list()
            self.unevenly_sampled_channels = list()
            self.metadata = list()
            self._channel_cache = {}

        else:
            self.redvox_packet: api900_pb2.RedvoxPacket = redvox_packet
            """Protobuf api 900 redvox packet"""

            self.evenly_sampled_channels: typing.List[EvenlySampledChannel] = list(
                    map(EvenlySampledChannel, repeated_to_array(redvox_packet.evenly_sampled_channels)))
            """List of evenly sampled channels"""

            self.unevenly_sampled_channels: typing.List[UnevenlySampledChannel] = list(
                    map(UnevenlySampledChannel, repeated_to_array(redvox_packet.unevenly_sampled_channels)))
            """List of unevenly sampled channels"""

            self.metadata: typing.List[str] = repeated_to_list(redvox_packet.metadata)
            """List of metadata"""

            self._channel_cache: typing.Dict[int, typing.Union[EvenlySampledChannel, UnevenlySampledChannel]] = {}
            """Holds a mapping of channel type to channel for O(1) access."""

            # Initialize channel cache
            for evenly_sampled_channel in self.evenly_sampled_channels:
                for channel_type in evenly_sampled_channel.channel_types:
                    self._channel_cache[channel_type] = evenly_sampled_channel

            for unevenly_sampled_channel in self.unevenly_sampled_channels:
                for channel_type in unevenly_sampled_channel.channel_types:
                    self._channel_cache[channel_type] = unevenly_sampled_channel

    def redvox_packet(self) -> api900_pb2.RedvoxPacket:
        """
        returns the protobuf redvox packet
        :return: protobuf redvox packet
        """
        return self.redvox_packet

    def evenly_sampled_channels(self) -> typing.List[EvenlySampledChannel]:
        """
        returns the evenly sampled channels as a copied list to avoid built in functions making untracked changes
        :return: list of evenly sampled channels
        """
        return self.evenly_sampled_channels.copy()

    def unevenly_sampled_channels(self) -> typing.List[UnevenlySampledChannel]:
        """
        returns the unevenly sampled channels as a copied list to avoid built in functions making untracked changes
        :return: list of unevenly sampled channels
        """
        return self.unevenly_sampled_channels.copy()

    def _refresh_channels(self):
        """
        takes the redvox packet and rebuilds the channel cache from it
        """
        self.evenly_sampled_channels = list(map(EvenlySampledChannel,
                                                repeated_to_array(self.redvox_packet.evenly_sampled_channels)))
        self.unevenly_sampled_channels = list(map(UnevenlySampledChannel,
                                                  repeated_to_array(self.redvox_packet.unevenly_sampled_channels)))
        self._channel_cache = {}
        for evenly_sampled_channel in self.evenly_sampled_channels:
            for channel_type in evenly_sampled_channel.channel_types:
                self._channel_cache[channel_type] = evenly_sampled_channel
        for unevenly_sampled_channel in self.unevenly_sampled_channels:
            for channel_type in unevenly_sampled_channel.channel_types:
                self._channel_cache[channel_type] = unevenly_sampled_channel

    def add_channel(self, channel: typing.Union[EvenlySampledChannel, UnevenlySampledChannel]):
        """
        Add a channel
        :param channel: channel to add
        """
        index, sample = self._find_channel(channel.channel_types[0])
        if index is None and sample is None:
            if type(channel) not in [EvenlySampledChannel, UnevenlySampledChannel]:
                raise TypeError("Channel type to add must be even or uneven.")
            else:
                self._add_channel_redvox_packet(channel)
                self._refresh_channels()
        else:
            raise ValueError("Cannot add a channel with a type that already exists in this packet.")

    def edit_channel(self, channel_type: int, channel: typing.Union[EvenlySampledChannel, UnevenlySampledChannel]):
        """
        removes the channel with the given type and adds the channel supplied
        :param channel_type: type of channel to remove
        :param channel: the channel to add
        """
        index, sampling = self._find_channel(channel_type)
        if index is not None and sampling is not None:
            if type(channel) == EvenlySampledChannel:
                del self.redvox_packet.evenly_sampled_channels[index]
                self._add_channel_redvox_packet(channel)
            elif type(channel) == UnevenlySampledChannel:
                del self.redvox_packet.unevenly_sampled_channels[index]
                self._add_channel_redvox_packet(channel)
            else:
                raise TypeError("Channel type to edit is unknown!")
            self._refresh_channels()
        else:
            raise TypeError("Unknown channel type specified for edit.")

    def delete_channel(self, channel_type: int):
        """
        deletes the channel type specified
        :param channel_type: a channel to remove
        """
        index, sampling = self._find_channel(channel_type)
        if index is not None and sampling is not None:
            if sampling == EvenlySampledChannel:
                del self.redvox_packet.evenly_sampled_channels[index]
            else:
                del self.redvox_packet.unevenly_sampled_channels[index]
            self._refresh_channels()
        else:
            raise TypeError("Unknown channel type to remove from packet.")

    def _find_channel(self, channel_type: int) -> (int, typing.Union[EvenlySampledChannel, UnevenlySampledChannel]):
        """
        returns the index of the channel and the kind of sampled array its in
        :return: the index in the even or uneven array and the name of the array
        """
        if self.has_channel(channel_type):
            for idx in range(len(self.evenly_sampled_channels)):
                if channel_type in self.evenly_sampled_channels[idx].channel_types:
                    return idx, EvenlySampledChannel
            for idx in range(len(self.unevenly_sampled_channels)):
                if channel_type in self.unevenly_sampled_channels[idx].channel_types:
                    return idx, UnevenlySampledChannel
            else:
                return None, None
        else:
            return None, None

    def _add_channel_redvox_packet(self, channel: typing.Union[EvenlySampledChannel, UnevenlySampledChannel]):
        """
        adds the channel to the redvox_packet
        :param channel: channel to add
        """
        if type(channel) == EvenlySampledChannel:
            newchan = self.redvox_packet.evenly_sampled_channels.add()
            newchan.sample_rate_hz = channel.sample_rate_hz
            newchan.first_sample_timestamp_epoch_microseconds_utc = \
                channel.first_sample_timestamp_epoch_microseconds_utc
        elif type(channel) == UnevenlySampledChannel:
            newchan = self.redvox_packet.unevenly_sampled_channels.add()
            for time in channel.timestamps_microseconds_utc:
                newchan.timestamps_microseconds_utc.append(time)
            newchan.sample_interval_mean = channel.sample_interval_mean
            newchan.sample_interval_std = channel.sample_interval_std
            newchan.sample_interval_median = channel.sample_interval_median
        else:
            raise TypeError("Channel type to add to redvox packet is unknown!")

        pl_type = channel.get_payload_type()
        if pl_type == "byte_payload":
            newchan.byte_payload.payload.extend(channel.payload)
        elif pl_type == "uint32_payload":
            newchan.uint32_payload.payload.extend(channel.payload)
        elif pl_type == "uint64_payload":
            newchan.uint64_payload.payload.extend(channel.payload)
        elif pl_type == "int32_payload":
            newchan.int32_payload.payload.extend(channel.payload)
        elif pl_type == "int64_payload":
            newchan.int64_payload.payload.extend(channel.payload)
        elif pl_type == "float32_payload":
            newchan.float32_payload.payload.extend(channel.payload)
        elif pl_type == "float64_payload":
            newchan.float64_payload.payload.extend(channel.payload)
        else:
            raise TypeError("Unknown payload type in channel to add.")

        for chan_type in channel.channel_types:
            newchan.channel_types.append(chan_type)
        newchan.sensor_name = channel.sensor_name
        for mean in channel.value_means:
            newchan.value_means.append(mean)
        for stds in channel.value_stds:
            newchan.value_stds.append(stds)
        for median in channel.value_medians:
            newchan.value_medians.append(median)
        for meta in channel.metadata:
            newchan.metadata.append(meta)

    def get_channel_types(self) -> typing.List[typing.List[int]]:
        """
        Returns a list of channel type enumerations. This is a list of lists, and allows us to easily view
        interleaved channels.
        :return: A list of channel type enumerations.
        """
        channel_types = []
        for evenly_sampled_channel in self.evenly_sampled_channels:
            channel_types.append(evenly_sampled_channel.channel_types)

        for unevenly_sampled_channel in self.unevenly_sampled_channels:
            channel_types.append(unevenly_sampled_channel.channel_types)

        return channel_types

    def get_channel_type_names(self) -> typing.List[typing.List[str]]:
        """
        Returns a list of channel type names. This is a list of lists, and allows us to easily view
        interleaved channels.
        :return: A list of channel type names. This is a list of lists, and allows us to easily view
        interleaved channels.
        """
        names = []
        for channel_types in self.get_channel_types():
            names.append(list(map(channel_type_name_from_enum, channel_types)))
        return names

    def get_channel(self, channel_type: int) -> typing.Union[EvenlySampledChannel, UnevenlySampledChannel, None]:
        """
        Returns a channel from this packet according to the channel type.
        :param channel_type: The channel type to search for.
        :return: A high level channel wrapper or None.
        """
        if channel_type in self._channel_cache:
            return self._channel_cache[channel_type]

        return None

    def has_channel(self, channel_type: int) -> bool:
        """
        Returns True if this packet contains a channel with this type otherwise False.
        :param channel_type: Channel type to search for.
        :return: True is this packet contains a channel with this type otherwise False.
        """
        return channel_type in self._channel_cache

    def has_channels(self, channel_types: typing.List[int]) -> bool:
        """
        Checks that this packet contains all of the provided channels.
        :param channel_types: Channel types that this packet must contain.
        :return: True if this packet contains all provided channel types, False otherwise.
        """
        has_channel_results = map(self.has_channel, channel_types)
        for has_channel_result in has_channel_results:
            if not has_channel_result:
                return False
        return True

    def to_json(self) -> str:
        """
        Converts the protobuf packet stored in this wrapped packet to JSON.
        :return: The JSON representation of the protobuf encoded packet.
        """
        return to_json(self.redvox_packet)

    def compressed_buffer(self) -> bytes:
        """
        Returns the compressed buffer associated with this packet.
        :return: The compressed buffer associated with this packet.
        """
        return lz4_compress(self.redvox_packet.SerializeToString())

    def api(self) -> int:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.api

    def set_api(self, version: int):
        """
        sets the api version number
        :param version: version number
        """
        self.redvox_packet.api = version

    def uuid(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.uuid

    def set_uuid(self, uid: str):
        """
        sets the uuid
        :param uid: uuid string
        """
        self.redvox_packet.uuid = uid

    def redvox_id(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.redvox_id

    def set_redvox_id(self, rid: str):
        """
        sets the redvox id
        :param rid: redvox id string
        """
        self.redvox_packet.redvox_id = rid

    def authenticated_email(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.authenticated_email

    def set_authenticated_email(self, email: str):
        """
        sets the authenticated email
        :param email: authenticated email string
        """
        self.redvox_packet.authenticated_email = email

    def authentication_token(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.authentication_token

    def set_authentication_token(self, token: str):
        """
        sets the authentication token
        :param token: authentication token string
        """
        self.redvox_packet.authentication_token = token

    def firebase_token(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.firebase_token

    def set_firebase_token(self, token: str):
        """
        sets the firebase token
        :param token: firebase token string
        """
        self.redvox_packet.firebase_token = token

    def is_backfilled(self) -> bool:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.is_backfilled

    def set_is_backfilled(self, tof: bool):
        """
        sets the is_backfilled flag
        :param tof: true or false
        """
        self.redvox_packet.is_backfilled = tof

    def is_private(self) -> bool:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.is_private

    def set_is_private(self, tof: bool):
        """
        sets the is_private flag
        :param tof: true or false
        """
        self.redvox_packet.is_private = tof

    def is_scrambled(self) -> bool:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.is_scrambled

    def set_is_scrambled(self, tof: bool):
        """
        sets the is_scrambled flag
        :param tof: true or false
        """
        self.redvox_packet.is_scrambled = tof

    def device_make(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.device_make

    def set_device_make(self, make: str):
        """
        sets the make of the device
        :param make: make of the device string
        """
        self.redvox_packet.device_make = make

    def device_model(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.device_model

    def set_device_model(self, model: str):
        """
        sets the model of the device
        :param model: model of the device string
        """
        self.redvox_packet.device_model = model

    def device_os(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.device_os

    def set_device_os(self, os: str):
        """
        sets the device operating system
        :param os: operating system string
        """
        self.redvox_packet.device_os = os

    def device_os_version(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.device_os_version

    def set_device_os_version(self, version: str):
        """
        sets the device OS version
        :param version: device OS version string
        """
        self.redvox_packet.device_os_version = version

    def app_version(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.app_version

    def set_app_version(self, version: str):
        """
        sets the app version number
        :param version: app version string
        """
        self.redvox_packet.app_version = version

    def battery_level_percent(self) -> float:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.battery_level_percent

    def set_battery_level_percent(self, percent: float):
        """
        sets the percentage of battery left
        :param percent: percentage of battery left
        """
        self.redvox_packet.battery_level_percent = percent

    def device_temperature_c(self) -> float:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.device_temperature_c

    def set_device_temperature_c(self, temp: float):
        """
        sets the device temperature in degrees Celsius
        :param temp: temperature in degrees Celsius
        """
        self.redvox_packet.device_temperature_c = temp

    def acquisition_server(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.acquisition_server

    def set_acquisition_server(self, server: str):
        """
        sets the acquisition server url
        :param server: url to acquisition server
        """
        self.redvox_packet.acquisition_server = server

    # pylint: disable=invalid-name
    def time_synchronization_server(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.time_synchronization_server

    def set_time_synchronization_server(self, server: str):
        """
        sets the time synchronization server url
        :param server: url to time synchronization server
        """
        self.redvox_packet.time_synchronization_server = server

    def authentication_server(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.authentication_server

    def set_authentication_server(self, server: str):
        """
        sets the authentication server url
        :param server: url to authentication server
        """
        self.redvox_packet.authentication_server = server

    # pylint: disable=invalid-name
    def app_file_start_timestamp_epoch_microseconds_utc(self) -> int:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.app_file_start_timestamp_epoch_microseconds_utc

    def set_app_file_start_timestamp_epoch_microseconds_utc(self, time: int):
        """
        sets the timestamp of packet creation
        :param time: time when packet was created in microseconds since utc epoch
        """
        self.redvox_packet.app_file_start_timestamp_epoch_microseconds_utc = time

    # pylint: disable=invalid-name
    def app_file_start_timestamp_machine(self) -> int:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.app_file_start_timestamp_machine

    def set_app_file_start_timestamp_machine(self, time: int):
        """
        sets the internal machine timestamp of packet creation
        :param time: time when packet was created on local machine
        """
        self.redvox_packet.app_file_start_timestamp_machine = time

    # pylint: disable=invalid-name
    def server_timestamp_epoch_microseconds_utc(self) -> int:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.redvox_packet.server_timestamp_epoch_microseconds_utc

    def set_server_timestamp_epoch_microseconds_utc(self, time: int):
        """
        sets the server timestamp when the packet was received
        :param time: time when packet was received by server
        """
        self.redvox_packet.server_timestamp_epoch_microseconds_utc = time

    def metadata(self) -> typing.List[str]:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self.metadata

    def set_metadata(self, data: typing.List[str]):
        """
        sets the metadata
        :param data: metadata as list of strings
        """
        self.metadata = data
        self.redvox_packet.metadata = data

    def clear_metadata(self):
        """
        removes all of the packet level metadata from packet
        """
        del self.redvox_packet.metadata[:]
        self.metadata.clear()

    def metadata_as_dict(self) -> typing.Dict[str, str]:
        """
        Return this packet's metadata as a key-value Python dictionary.
        :return: This packet's metadata as a key-value Python dictionary.
        """
        return get_metadata_as_dict(self.metadata)

    # Sensor channels
    def has_microphone_channel(self) -> bool:
        """
        Returns if this packet has a microphone channel.
        :return: If this packet has a microphone channel.
        """
        return self.has_channel(api900_pb2.MICROPHONE)

    def microphone_channel(self) -> typing.Optional[MicrophoneSensor]:
        """
        Returns the high-level microphone channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level microphone channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_microphone_channel():
            return MicrophoneSensor(self.get_channel(api900_pb2.MICROPHONE))

        return None

    def has_barometer_channel(self) -> bool:
        """
        Returns if this packet has a barometer channel.
        :return: If this packet has a barometer channel.
        """
        return self.has_channel(api900_pb2.BAROMETER)

    def barometer_channel(self) -> typing.Optional[BarometerSensor]:
        """
        Returns the high-level barometer channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level barometer channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_barometer_channel():
            return BarometerSensor(self.get_channel(api900_pb2.BAROMETER))

        return None

    def has_location_channel(self) -> bool:
        """
        Returns if this packet has a location channel.
        :return: If this packet has a location channel.
        """
        return (self.has_channels(
                [api900_pb2.LATITUDE, api900_pb2.LONGITUDE, api900_pb2.ALTITUDE, api900_pb2.SPEED,
                 api900_pb2.ACCURACY]) or
                self.has_channels([api900_pb2.LATITUDE, api900_pb2.LONGITUDE]))

    def location_channel(self) -> typing.Optional[LocationSensor]:
        """
        Returns the high-level location channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level location channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_location_channel():
            return LocationSensor(self.get_channel(api900_pb2.LATITUDE))

        return None

    # pylint: disable=invalid-name,C1801
    def has_time_synchronization_channel(self) -> bool:
        """
        Returns if this packet has a time synchronization channel.
        :return: If this packet has a time synchronization channel.
        """
        if self.has_channel(api900_pb2.TIME_SYNCHRONIZATION):
            ch = TimeSynchronizationSensor(self.get_channel(api900_pb2.TIME_SYNCHRONIZATION))
            return len(ch.payload_values()) > 0

        return False

    def time_synchronization_channel(self) -> typing.Optional[TimeSynchronizationSensor]:
        """
        Returns the high-level time synchronization channel API or None if this packet doesn't contain a channel of
        this type.
        :return: the high-level time synchronization channel API or None if this packet doesn't contain a channel of
        this type.
        """
        if self.has_time_synchronization_channel():
            return TimeSynchronizationSensor(self.get_channel(api900_pb2.TIME_SYNCHRONIZATION))

        return None

    def has_accelerometer_channel(self) -> bool:
        """
        Returns if this packet has an accelerometer channel.
        :return: If this packet has an accelerometer channel.
        """
        return self.has_channels([api900_pb2.ACCELEROMETER_X, api900_pb2.ACCELEROMETER_Y, api900_pb2.ACCELEROMETER_Z])

    def accelerometer_channel(self) -> typing.Optional[AccelerometerSensor]:
        """
        Returns the high-level accelerometer channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level accelerometer channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_accelerometer_channel():
            return AccelerometerSensor(self.get_channel(api900_pb2.ACCELEROMETER_X))

        return None

    def has_magnetometer_channel(self) -> bool:
        """
        Returns if this packet has a magnetometer channel.
        :return: If this packet has a magnetometer channel.
        """
        return self.has_channels([api900_pb2.MAGNETOMETER_X, api900_pb2.MAGNETOMETER_Y, api900_pb2.MAGNETOMETER_Z])

    def magnetometer_channel(self) -> typing.Optional[MagnetometerSensor]:
        """
        Returns the high-level magnetometer channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level magnetometer channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_magnetometer_channel():
            return MagnetometerSensor(self.get_channel(api900_pb2.MAGNETOMETER_X))

        return None

    def has_gyroscope_channel(self) -> bool:
        """
        Returns if this packet has a gyroscope channel.
        :return: If this packet has a gyroscope channel.
        """
        return self.has_channels([api900_pb2.GYROSCOPE_X, api900_pb2.GYROSCOPE_Y, api900_pb2.GYROSCOPE_Z])

    def gyroscope_channel(self) -> typing.Optional[GyroscopeSensor]:
        """
        Returns the high-level gyroscope channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level gyroscope channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_gyroscope_channel():
            return GyroscopeSensor(self.get_channel(api900_pb2.GYROSCOPE_X))

        return None

    def has_light_channel(self) -> bool:
        """
        Returns if this packet has a light channel.
        :return: If this packet has a light channel.
        """
        return self.has_channel(api900_pb2.LIGHT)

    def light_channel(self) -> typing.Optional[LightSensor]:
        """
        Returns the high-level light channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level light channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_light_channel():
            return LightSensor(self.get_channel(api900_pb2.LIGHT))

        return None

    def has_infrared_channel(self) -> bool:
        """
        Returns if this packet has an infrared channel.
        :return: If this packlet has an infrared channel.
        """
        return self.has_channel(api900_pb2.INFRARED)

    def infrared_channel(self) -> typing.Optional[InfraredSensor]:
        """
        Returns the high-level infrared channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level infrared channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_infrared_channel():
            return InfraredSensor(self.get_channel(api900_pb2.INFRARED))

        return None

    def has_image_channel(self) -> bool:
        """
        Returns if this packet has an image channel.
        :return: If this packlet has an image channel.
        """
        return self.has_channel(api900_pb2.IMAGE)

    def image_channel(self) -> typing.Optional[ImageSensor]:
        """
        Returns the high-level image channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level image channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_image_channel():
            return ImageSensor(self.get_channel(api900_pb2.IMAGE))

        return None

    def __str__(self):
        """
        Returns protobuf's String representation of this packet.
        :return: Protobuf's String representation of this packet.
        """
        return str(self.redvox_packet)


def wrap(redvox_packet: api900_pb2.RedvoxPacket) -> WrappedRedvoxPacket:
    """Shortcut for wrapping a protobuf packet with our higher level wrapper.

    Args:
        redvox_packet: The redvox packet to wrap.

    Returns:
        A wrapper redvox packet.
    """
    return WrappedRedvoxPacket(redvox_packet)


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

