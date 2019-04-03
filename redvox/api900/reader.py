# pylint: disable=too-many-lines
"""
This module provides functions and classes for working with RedVox API 900 data.
"""

import collections
import glob
import json
import os
import struct
import typing

# noinspection PyPackageRequirements
import google.protobuf.internal.containers as containers
# noinspection PyPackageRequirements
import google.protobuf.json_format as json_format
import lz4.block
import numpy

import redvox.api900.constants as constants
import redvox.api900.date_time_utils as date_time_utils
import redvox.api900.exceptions as exceptions
import redvox.api900.lib.api900_pb2 as api900_pb2
import redvox.api900.stat_utils


def _calculate_uncompressed_size(buf: bytes) -> int:
    """
    Given a buffer, calculate the original size of the uncompressed packet by looking at the first four bytes.
    :param buf: Buffer where first 4 big endian bytes contain the size of the original uncompressed packet.
    :return: The total number of bytes in the original uncompressed packet.
    """
    return struct.unpack(">I", buf[:4])[0]


def _uncompressed_size_bytes(size: int) -> bytes:
    """
    Given the size of the original uncompressed file, return the size as an array of 4 bytes.
    :param size: The size to convert.
    :return: The 4 bytes representing the size.
    """
    return struct.pack(">I", size)


def _lz4_decompress(buf: bytes) -> bytes:
    """
    Decompresses an API 900 compressed buffer.
    :param buf: The buffer to decompress.
    :return: The uncompressed buffer.
    """
    uncompressed_size = _calculate_uncompressed_size(buf)

    if uncompressed_size <= 0:
        raise exceptions.ReaderException("uncompressed size [{}] must be > 0".format(uncompressed_size))

    return lz4.block.decompress(buf[4:], uncompressed_size=_calculate_uncompressed_size(buf))


# noinspection PyArgumentList
def _lz4_compress(buf: bytes) -> bytes:
    """
    Compresses a buffer using LZ4. The compressed buffer is then prepended with the 4 bytes indicating the original
    size of uncompressed buffer.
    :param buf: The buffer to compress.
    :return: The compressed buffer with 4 bytes prepended indicated the original size of the uncompressed buffer.
    """
    uncompressed_size = _uncompressed_size_bytes(len(buf))
    compressed = lz4.block.compress(buf, store_size=False)
    return uncompressed_size + compressed


def _write_file(file: str, redvox_packet: api900_pb2.RedvoxPacket):
    """
    Writes a redvox file.  Specify the correct file type in the file string.
    :param file: str, File to write
    :param redvox_packet: protobuf packet to write
    :return: Nothing, compressed file is written to disk
    """
    buffer = _lz4_compress(redvox_packet.SerializeToString())
    with open(file, "wb") as f:
        f.write(buffer)


def _to_json(redvox_packet: api900_pb2.RedvoxPacket) -> str:
    """
    Converts a protobuf encoded API 900 RedVox packet into JSON.
    :param redvox_packet: The protobuf encoded packet.
    :return: A string containing JSON of this packet.
    """
    return json_format.MessageToJson(redvox_packet)


def _from_json(redvox_packet_json: str) -> api900_pb2.RedvoxPacket:
    """
    Converts a JSON packet representing an API 900 packet into a protobuf encoded RedVox API 900 packet.
    :param redvox_packet_json: A string containing the json representing the packet.
    :return: A Python instance of an encoded API 900 packet.
    """
    return json_format.Parse(redvox_packet_json, api900_pb2.RedvoxPacket())


def _payload_type(channel: typing.Union[api900_pb2.EvenlySampledChannel,
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


def _extract_payload(channel: typing.Union[api900_pb2.EvenlySampledChannel,
                                           api900_pb2.UnevenlySampledChannel]) -> numpy.ndarray:
    """
    Given an evenly or unevenly sampled channel, extracts the entire payload.

    This will return a payload of either ints or floats and is type agnostic when it comes to the underlying
    protobuf type.
    :param channel: The protobuf channel to extract the payload from.
    :return: A numpy array of either floats or ints.
    """
    payload_type_str = _payload_type(channel)

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


def _repeated_to_list(repeated: typing.Union[containers.RepeatedCompositeFieldContainer,
                                             containers.RepeatedScalarFieldContainer]) -> typing.List:
    """
    Transforms a repeated protobuf field into a list.
    :param repeated: The repeated field to transform.
    :return: A list of the repeated items.
    """
    return repeated[0:len(repeated)]


def _repeated_to_array(repeated: typing.Union[containers.RepeatedCompositeFieldContainer,
                                              containers.RepeatedScalarFieldContainer]) -> numpy.ndarray:
    """
    Transforms a repeated protobuf field into a numpy array.
    :param repeated: The repeated field to transform.
    :return: A numpy array of the repeated items.
    """
    return numpy.array(_repeated_to_list(repeated))


def _deinterleave_array(ndarray: numpy.ndarray, offset: int, step: int) -> numpy.ndarray:
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
        return _empty_array()

    return ndarray[offset::step]


def _to_array(values: typing.Union[typing.List, numpy.ndarray]) -> numpy.ndarray:
    """
    Takes either a list or a numpy array and returns a numpy array if the parameter was a list.
    :param values: Values to convert into numpy array if values are in a list.
    :return: A numpy array of the passed in values.
    """
    if isinstance(values, typing.List):
        return numpy.array(values)
    return values


def _interleave_arrays(arrays: typing.List[numpy.ndarray]) -> numpy.ndarray:
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


def _implements_diff(val) -> bool:
    """
    Checks if a value implements the diff method.
    :param val: Value to check
    :return: True is the value implements diff, False otherwise.
    """
    diff_atr = getattr(val, "diff", None)
    if callable(diff_atr):
        return True

    return False


def _diff(val1, val2) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    Determines if the two values are different.
    :param val1: The first value to check.
    :param val2: The second value to check.
    :return: False, None if the values are the same or True, and a string displaying the differences when different.
    """
    if type(val1) != type(val2):
        return True, "type {} != type {}".format(type(val1), type(val2))

    if _implements_diff(val1) and _implements_diff(val2):
        diffs = val1.diff(val2)
        if len(diffs) == 0:
            return False, None
        else:
            return True, "%s" % list(diffs)

    if isinstance(val1, numpy.ndarray) and isinstance(val2, numpy.ndarray):
        if numpy.array_equal(val1, val2):
            return False, None
        else:
            return True, "{} != {}".format(val1, val2)

    if val1 != val2:
        return True, "{} != {}".format(val1, val2)

    return False, None


def _safe_index_of(lst: typing.List, val: typing.Any) -> int:
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


def _empty_array() -> numpy.ndarray:
    """Returns an empty numpy array.
    :return: An empty numpy array.
    """
    return numpy.array([])


def _empty_evenly_sampled_channel() -> api900_pb2.EvenlySampledChannel:
    """
    Returns an empty protobuf EvenlySampledChannel
    :return: empty EvenlySampledChannel
    """
    obj = api900_pb2.EvenlySampledChannel()
    return obj


def _empty_unevenly_sampled_channel() -> api900_pb2.UnevenlySampledChannel:
    """
    Returns an empty protobuf UnevenlySampledChannel
    :return: empty UnevenlySampledChannel
    """
    obj = api900_pb2.UnevenlySampledChannel()
    return obj


def _channel_type_name_from_enum(enum_constant: int) -> str:
    """
    Returns the name of a channel type given its enumeration constant.
    :param enum_constant: The constant to turn into a name.
    :return: The name of the channel.
    """
    return api900_pb2.ChannelType.Name(enum_constant)


def _get_metadata(metadata: typing.List[str], k: str) -> str:
    """
    Given a meta-data key, extract the value.
    :param metadata: List of metadata to extract value from.
    :param k: The meta-data key.
    :return: The value corresponding to the key or an empty string.
    """
    if len(metadata) % 2 != 0:
        raise exceptions.ReaderException("metadata list must contain an even number of items")

    idx = _safe_index_of(metadata, k)
    if idx < 0:
        return ""

    return metadata[idx + 1]


def _get_metadata_as_dict(metadata: typing.List[str]) -> typing.Dict[str, str]:
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


def _metadata_dict_to_list(metadata_dict: typing.Dict[str, str]) -> typing.List[str]:
    """
    Converts a dictionary containing metadata into a list of metadata.
    :param metadata_dict: The dictionary of metadata.
    :return: A list of metadata.
    """
    metadata_list = []
    for key, value in metadata_dict.items():
        metadata_list.extend([key, value])
    return metadata_list


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

    def __init__(self, channel: typing.Optional[typing.Union[api900_pb2.EvenlySampledChannel,
                                                             api900_pb2.UnevenlySampledChannel]] = None):
        """
        Initializes this interleaved channel object.
        :param channel: Either a protobuf evenly or unevenly sampled channel.
        note: value_means, value_medians, value_stds, and channel_type_index are only set during initialization or
            when payload is altered
        payload should only be altered by set_payload or set_deinterleaved_payload due to the extra data values that are
            required to correctly set the protobuf_channel
        """
        if channel is None:
            self.protobuf_channel = None
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
                    api900_pb2.UnevenlySampledChannel]] = _repeated_to_list(channel.channel_types)
            """List of channel type constant enumerations"""

            self.payload: numpy.ndarray = _extract_payload(channel)
            """This channels payload as a numpy array of either floats or ints"""

            self.metadata: typing.List[str] = _repeated_to_list(channel.metadata)
            """This channels list of metadata"""

            self.value_means: numpy.ndarray = _repeated_to_array(channel.value_means)
            """Interleaved array of mean values"""

            self.value_stds: numpy.ndarray = _repeated_to_array(channel.value_stds)
            """Interleaved array of standard deviations of values"""

            self.value_medians: numpy.ndarray = _repeated_to_array(channel.value_medians)
            """Interleaves array of median values"""

            self.channel_type_index: typing.Dict[api900_pb2.ChannelType, int] = {self.channel_types[i]: i for
                                                                                 i in
                                                                                 range(
                                                                                         len(
                                                                                                 self.channel_types))}
            """Contains a mapping of channel type to index in channel_types array"""

    def set_channel_types(self, types: typing.List[typing.Union[api900_pb2.EvenlySampledChannel,
                                                                api900_pb2.UnevenlySampledChannel]]):
        """
        sets the channel_types to the list given
        :param types: a list of channel types
        """
        del self.protobuf_channel.channel_types[:]
        for ctype in types:
            self.protobuf_channel.channel_types.append(ctype)
        self.channel_types = _repeated_to_list(self.protobuf_channel.channel_types)
        self.channel_type_index = {self.channel_types[i]: i for i in range(len(self.channel_types))}

    def get_channel_type_names(self) -> typing.List[str]:
        """
        Returns the list of channel_types as a list of names instead of enumeration constants.
        :return: The list of channel_types as a list of names instead of enumeration constants.
        """
        return list(map(_channel_type_name_from_enum, self.channel_types))

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
        self.channel_types = _repeated_to_list(channel.channel_types)
        self.payload = _extract_payload(channel)
        self.metadata = _repeated_to_list(channel.metadata)
        self.value_means = _repeated_to_array(channel.value_means)
        self.value_stds = _repeated_to_array(channel.value_stds)
        self.value_medians = _repeated_to_array(channel.value_medians)
        self.channel_type_index = {self.channel_types[i]: i for i in range(len(self.channel_types))}

    def has_payload(self, channel_type: int) -> bool:
        """
        Returns if channel contains a non-empty specified payload.
        :param channel_type: The channel to check for a payload for.
        :return: Whether this channel contains the specified payload.
        """
        return self.has_channel(channel_type) and len(self.payload) > 0

    def set_payload(self,
                    payload_values: typing.Union[numpy.ndarray, typing.List],
                    pl_type: constants.PayloadType,
                    should_compute_stats=True):
        """
        sets the payload to an interleaved channel with step number of arrays interleaved together.
        :param should_compute_stats: Whether the statistics should be computed or not (optional default to True)
        :param payload_values: Interleaved payload values
        :param pl_type: payload type
        """
        # if len(payload_values) < 1:
        #     raise exceptions.ReaderException("Channel must not be empty and number of arrays must not be less than
        #     1.")

        # Convert to numpy array is necessary
        payload_values = _to_array(payload_values)

        # clear all other payloads
        self.protobuf_channel.byte_payload.ClearField("payload")
        self.protobuf_channel.uint32_payload.ClearField("payload")
        self.protobuf_channel.uint64_payload.ClearField("payload")
        self.protobuf_channel.int32_payload.ClearField("payload")
        self.protobuf_channel.int64_payload.ClearField("payload")
        self.protobuf_channel.float32_payload.ClearField("payload")
        self.protobuf_channel.float64_payload.ClearField("payload")

        # set the payload based on the type of data
        if pl_type == constants.PayloadType.BYTE_PAYLOAD:
            self.protobuf_channel.byte_payload.payload = payload_values
        elif pl_type == constants.PayloadType.UINT32_PAYLOAD:
            self.protobuf_channel.uint32_payload.payload.extend(payload_values)
        elif pl_type == constants.PayloadType.UINT64_PAYLOAD:
            self.protobuf_channel.uint64_payload.payload.extend(payload_values)
        elif pl_type == constants.PayloadType.INT32_PAYLOAD:
            self.protobuf_channel.int32_payload.payload.extend(payload_values)
        elif pl_type == constants.PayloadType.INT64_PAYLOAD:
            self.protobuf_channel.int64_payload.payload.extend(payload_values)
        elif pl_type == constants.PayloadType.FLOAT32_PAYLOAD:
            self.protobuf_channel.float32_payload.payload.extend(payload_values)
        elif pl_type == constants.PayloadType.FLOAT64_PAYLOAD:
            self.protobuf_channel.float64_payload.payload.extend(payload_values)
        else:
            raise TypeError("Unknown payload type to set.")

        if len(payload_values) < 1:
            self.payload = payload_values
        else:
            self.payload = _extract_payload(self.protobuf_channel)

            # calculate the means, std devs, and medians
            if should_compute_stats:
                self.update_stats()

    def set_interleaved_payload(self,
                                payloads: typing.List[typing.Union[typing.List, numpy.ndarray]],
                                pl_type: constants.PayloadType,
                                should_compute_stats: bool = True):
        """
        Interleaves multiple payloads together and sets the interleaved payload.
        :param payloads: Payloads of the same length to be interleaved.
        :param pl_type: The payload type
        :param should_compute_stats: Whether or not payload stats should be calculated.
        """
        interleaved = _interleave_arrays(list(map(_to_array, payloads)))
        self.set_payload(interleaved, pl_type, should_compute_stats)

    def get_payload(self, channel_type: int) -> numpy.ndarray:
        """
        Returns a deinterleaved payload of a given channel type or an empty array.
        :param channel_type: The channel type to extract/deinterleave from the payload.
        :return: A numpy array of floats or ints of a single channel type.
        """
        idx = self.channel_index(channel_type)
        if idx < 0:
            return _empty_array()
        try:
            return _deinterleave_array(self.payload, idx, len(self.channel_types))
        except exceptions.ReaderException:
            return _empty_array()

    def get_payload_type(self) -> str:
        """
        Returns the internal protobuf payload type.
        :return: The internal protobuf payload type.
        """
        return _payload_type(self.protobuf_channel)

    def get_multi_payload(self, channel_types: typing.List[int]) -> numpy.ndarray:
        """
        Returns an interleaved payload with the given channel types.
        :param channel_types: Channel types to interleave into a single payload.
        :return: A numpy array of an interleaved payload.
        """
        channel_types_len = len(channel_types)
        if channel_types_len == 0:
            return _empty_array()
        elif channel_types_len == 1:
            return self.get_payload(channel_types[0])

        payloads = list(map(self.get_payload, channel_types))
        return _interleave_arrays(payloads)

    def get_value_mean(self, channel_type: int) -> float:
        """
        Returns the mean value for a single channel type.
        :param channel_type: The channel type to extract the mean from.
        :return: The mean value.
        """
        idx = self.channel_index(channel_type)
        if idx < 0 or len(self.value_means) == 0:
            raise exceptions.ReaderException("mean DNE, is the payload empty?")

        return self.value_means[idx]

    def get_value_std(self, channel_type: int) -> float:
        """
        Returns the standard deviation value for a single channel type.
        :param channel_type: The channel type to extract the std from.
        :return: The standard deviation.
        """
        idx = self.channel_index(channel_type)
        if idx < 0 or len(self.value_stds) == 0:
            raise exceptions.ReaderException("std DNE, is the payload empty?")

        return self.value_stds[idx]

    def get_value_median(self, channel_type: int) -> float:
        """
        Returns the median value for a single channel type.
        :param channel_type: The channel type to extract the median from.
        :return:The median value.
        """
        idx = self.channel_index(channel_type)
        if idx < 0 or len(self.value_medians) == 0:
            raise exceptions.ReaderException("median DNE, is the payload empty?")

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
            std, mean, median = redvox.api900.stat_utils.calc_utils(_deinterleave_array(channel, i, step))
            self.protobuf_channel.value_means.append(mean)
            self.protobuf_channel.value_stds.append(std)
            self.protobuf_channel.value_medians.append(median)
        self.value_stds = _repeated_to_array(self.protobuf_channel.value_stds)
        self.value_means = _repeated_to_array(self.protobuf_channel.value_means)
        self.value_medians = _repeated_to_array(self.protobuf_channel.value_medians)

    def set_sensor_name(self, name: str):
        """
        sets the sensor name
        :param name: name of sensor
        """
        self.sensor_name = name
        self.protobuf_channel.sensor_name = name

    def set_metadata(self, data: typing.List[str]):
        """
        sets the metadata
        :param data: metadata as list of strings
        """
        del self.protobuf_channel.metadata[:]
        for meta in data:
            self.protobuf_channel.metadata.append(meta)
        self.metadata = _repeated_to_list(self.protobuf_channel.metadata)

    def metadata_as_dict(self) -> typing.Dict[str, str]:
        """
        Returns any metadata as a dictionary of key-pair values.
        :return: Any metadata as a dictionary of key-pair values.
        """
        return _get_metadata_as_dict(self.metadata)

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
                                                 _channel_type_name_from_enum,
                                                 self.channel_types)),
                                         len(self.payload),
                                         _payload_type(
                                                 self.protobuf_channel))


class EvenlySampledChannel(InterleavedChannel):
    """
    An evenly sampled channel is an interleaved channel that also has a channel with an even sampling rate.
    """

    def __init__(self, channel: typing.Optional[api900_pb2.EvenlySampledChannel] = None):
        """
        Initializes this evenly sampled channel.
        :param channel: A protobuf evenly sampled channel.
        """
        if channel is None:
            channel = _empty_evenly_sampled_channel()

        InterleavedChannel.__init__(self, channel)
        self.sample_rate_hz: float = channel.sample_rate_hz
        """The sample rate in hz of this evenly sampled channel"""

        # pylint: disable=invalid-name
        self.first_sample_timestamp_epoch_microseconds_utc: int = \
            channel.first_sample_timestamp_epoch_microseconds_utc
        """The timestamp of the first sample"""

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
        self.protobuf_channel.sample_rate_hz = rate

    def set_first_sample_timestamp_epoch_microseconds_utc(self, time: int):
        """
        set the epoch in microseconds
        :param time: time in microseconds since epoch utc
        """
        self.first_sample_timestamp_epoch_microseconds_utc = time
        self.protobuf_channel.first_sample_timestamp_epoch_microseconds_utc = time

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

    def __init__(self, channel: typing.Optional[api900_pb2.UnevenlySampledChannel] = None):
        """
        Initializes this unevenly sampled channel.
        :param channel: A protobuf unevenly sampled channel.
        """
        if channel is None:
            channel = _empty_unevenly_sampled_channel()

        InterleavedChannel.__init__(self, channel)
        self.timestamps_microseconds_utc: numpy.ndarray = _repeated_to_array(channel.timestamps_microseconds_utc)
        """Numpy array of timestamps epoch microseconds utc for each sample"""

        self.sample_interval_mean: float = channel.sample_interval_mean
        """The mean sample interval"""

        self.sample_interval_std: float = channel.sample_interval_std
        """The standard deviation of the sample interval"""

        self.sample_interval_median: float = channel.sample_interval_median
        """The median sample interval"""

    def set_channel(self, channel: api900_pb2.UnevenlySampledChannel):
        """
        sets the channel to an unevenly sampled channel
        :param channel: unevenly sampled channel
        """
        super().set_channel(channel)
        self.timestamps_microseconds_utc = _repeated_to_array(channel.timestamps_microseconds_utc)
        self.sample_interval_std, self.sample_interval_mean, self.sample_interval_median = \
            redvox.api900.stat_utils.calc_utils_timeseries(self.timestamps_microseconds_utc)

    def set_timestamps_microseconds_utc(self, timestamps: typing.Union[typing.List[int], numpy.ndarray]):
        """
        set the timestamps in microseconds from utc
        :param timestamps: array of timestamps
        """
        timestamps = _to_array(timestamps)
        self.timestamps_microseconds_utc = timestamps
        self.protobuf_channel.timestamps_microseconds_utc[:] = timestamps

        if len(timestamps) > 0:
            self.sample_interval_std, self.sample_interval_mean, self.sample_interval_median = \
                redvox.api900.stat_utils.calc_utils_timeseries(timestamps)
        else:
            self.sample_interval_mean = 0.0
            self.sample_interval_median = 0.0
            self.sample_interval_std = 0.0

        self.protobuf_channel.sample_interval_std = self.sample_interval_std
        self.protobuf_channel.sample_interval_mean = self.sample_interval_mean
        self.protobuf_channel.sample_interval_median = self.sample_interval_median

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

    def __init__(self, evenly_sampled_channel: typing.Optional[EvenlySampledChannel] = None):
        """
        Initializes this class.
        :param evenly_sampled_channel: an instance of an EvenlySampledChannel
        """
        if evenly_sampled_channel is None:
            self._evenly_sampled_channel = EvenlySampledChannel()
        else:
            self._evenly_sampled_channel: EvenlySampledChannel = evenly_sampled_channel
            """A reference to the original unevenly sampled channel"""

    def _get_channel_type_names(self) -> typing.List[str]:
        """
        Returns the list of channel_types as a list of names instead of enumeration constants.
        :return: The list of channel_types as a list of names instead of enumeration constants.
        """
        return list(map(_channel_type_name_from_enum, self._evenly_sampled_channel.channel_types))

    def _concat_metadata(self, evenly_sampled_sensor: 'EvenlySampledSensor') -> 'EvenlySampledSensor':
        concat_meta = []
        concat_meta.extend(self.metadata())
        concat_meta.extend(evenly_sampled_sensor.metadata())
        return self.set_metadata(concat_meta)

    def sample_rate_hz(self) -> float:
        """
        Returns the sample rate in Hz of this evenly sampled channel.
        :return: The sample rate in Hz of this evenly sampled channel.
        """
        return self._evenly_sampled_channel.sample_rate_hz

    def set_sample_rate_hz(self, rate: float) -> 'EvenlySampledSensor':
        """
        sets the sample rate
        :param rate: sample rate in hz
        :return: An instance of the sensor.
        """
        self._evenly_sampled_channel.set_sample_rate_hz(rate)
        return self

    # pylint: disable=invalid-name
    def first_sample_timestamp_epoch_microseconds_utc(self) -> int:
        """
        Return the first sample timestamp in microseconds since the epoch UTC.
        :return: The first sample timestamp in microseconds since the epoch UTC.
        """
        return self._evenly_sampled_channel.first_sample_timestamp_epoch_microseconds_utc

    def set_first_sample_timestamp_epoch_microseconds_utc(self, time: int) -> 'EvenlySampledSensor':
        """
        sets the sample timestamp in microseconds since utc
        :param time: microseconds since utc
        :return: An instance of the sensor.
        """
        self._evenly_sampled_channel.set_first_sample_timestamp_epoch_microseconds_utc(time)
        return self

    def sensor_name(self) -> str:
        """
        Returns the sensor name associated with this evenly sampled chanel
        :return: The sensor name associated with this evenly sampled chanel
        """
        return self._evenly_sampled_channel.sensor_name

    def set_sensor_name(self, name: str) -> 'EvenlySampledSensor':
        """
        sets the sensor name
        :param name: name of sensor
        :return: An instance of the sensor.
        """
        self._evenly_sampled_channel.set_sensor_name(name)
        return self

    def payload_type(self) -> str:
        """
        Returns the internal protobuf payload type.
        :return: The internal protobuf payload type.
        """
        return self._evenly_sampled_channel.get_payload_type()

    def metadata(self) -> typing.List[str]:
        """
        Returns this channel's metadata (if there is any) as a Python list.
        :return: This channel's metadata (if there is any) as a Python list.
        """
        return self._evenly_sampled_channel.metadata

    def set_metadata(self, data: typing.List[str]) -> 'EvenlySampledSensor':
        """
        sets the metadata
        :param data: metadata as list of strings
        :return: An instance of the sensor.
        """
        self._evenly_sampled_channel.set_metadata(data)
        return self

    def metadata_as_dict(self) -> typing.Dict[str, str]:
        """
        Returns this channel's metadata (if there is any) as a Python dictionary.
        :return: This channel's metadata (if there is any) as a Python dictionary.
        """
        return _get_metadata_as_dict(self._evenly_sampled_channel.metadata)

    def set_metadata_as_dict(self, metadata_dict: typing.Dict[str, str]) -> 'EvenlySampledSensor':
        self.set_metadata(_metadata_dict_to_list(metadata_dict))
        return self

    def __str__(self):
        return str(self._evenly_sampled_channel)

    def __eq__(self, other):
        return isinstance(other, EvenlySampledSensor) and len(self.diff(other)) == 0

    def diff(self, other: 'EvenlySampledSensor') -> typing.List[str]:
        """
        Compares two evenly sampled sensors for differences.
        :param other: The other sensor to compare with.
        :return: A list of differences or an empty list if there are none.
        """
        diffs = map(lambda tuple2: _diff(tuple2[0], tuple2[1]), [
            (self._get_channel_type_names(), other._get_channel_type_names()),
            (self.sensor_name(), other.sensor_name()),
            (self.sample_rate_hz(), other.sample_rate_hz()),
            (self.first_sample_timestamp_epoch_microseconds_utc(),
             other.first_sample_timestamp_epoch_microseconds_utc()),
            (self.payload_type(), other.payload_type()),
            (self.metadata(), other.metadata()),
            (self._evenly_sampled_channel.payload, other._evenly_sampled_channel.payload)
        ])
        # Filter only out only the differences
        diffs = filter(lambda tuple2: tuple2[0], diffs)
        # Extract the difference string
        diffs = map(lambda tuple2: tuple2[1], diffs)
        return list(diffs)


class UnevenlySampledSensor:
    """
    An UnevenlySampledSensor provides a high level abstraction over an UnevenlySampledChannel.

    This class exposes top level fields within API 900 unevenly sampled channels.
    Composition is used instead of inheritance to hide the complexities of the underlying class.
    """

    def __init__(self, unevenly_sampled_channel: typing.Optional[UnevenlySampledChannel] = None):
        """
        Initializes this class.
        :param unevenly_sampled_channel: an instance of a UnevenlySampledChannel
        """
        if unevenly_sampled_channel is None:
            self._unevenly_sampled_channel = UnevenlySampledChannel()
        else:
            self._unevenly_sampled_channel: UnevenlySampledChannel = unevenly_sampled_channel

    def _get_channel_type_names(self) -> typing.List[str]:
        """
        Returns the list of channel_types as a list of names instead of enumeration constants.
        :return: The list of channel_types as a list of names instead of enumeration constants.
        """
        return list(map(_channel_type_name_from_enum, self._unevenly_sampled_channel.channel_types))

    def _can_concat(self, unevenly_sampled_sensor: 'UnevenlySampledSensor') -> bool:
        if unevenly_sampled_sensor is None:
            raise exceptions.ConcatenationException("Other sensor is None.")

        if self.timestamps_microseconds_utc()[-1] > unevenly_sampled_sensor.timestamps_microseconds_utc()[0]:
            raise exceptions.ConcatenationException("Second sensor comes after first in time")

        if self.sensor_name() != unevenly_sampled_sensor.sensor_name():
            raise exceptions.ConcatenationException("Sensor names do not match. self=%s, other=%s" % (
                self.sensor_name(), unevenly_sampled_sensor.sensor_name()
            ))

        return True

    def _concat_timestamps(self, unevenly_sampled_sensor: 'UnevenlySampledSensor') -> 'UnevenlySampledSensor':
        return self.set_timestamps_microseconds_utc(numpy.concatenate([
            self.timestamps_microseconds_utc(),
            unevenly_sampled_sensor.timestamps_microseconds_utc()
        ]))

    def _concat_metadata(self, unevenly_sampled_sensor: 'UnevenlySampledSensor') -> 'UnevenlySampledSensor':
        concat_meta = []
        concat_meta.extend(self.metadata())
        concat_meta.extend(unevenly_sampled_sensor.metadata())
        return self.set_metadata(concat_meta)

    def sensor_name(self) -> str:
        """
        Returns the sensor name associated with this unevenly sampled channel.
        :return: The sensor name associated with this unevenly sampled channel.
        """
        return self._unevenly_sampled_channel.sensor_name

    def set_sensor_name(self, name: str) -> 'UnevenlySampledSensor':
        """
        Sets the sensor name
        :param name: name of the sensor
        :return: An instance of the sensor.
        """
        self._unevenly_sampled_channel.set_sensor_name(name)
        return self

    def payload_type(self) -> str:
        """
        Returns the internal protobuf payload type.
        :return: The internal protobuf payload type.
        """
        return self._unevenly_sampled_channel.get_payload_type()

    def timestamps_microseconds_utc(self) -> numpy.ndarray:
        """
        Returns a list of ascending timestamps that associate with each sample value
        :return: A list of ascending timestamps that associate with each sample value
        """
        return self._unevenly_sampled_channel.timestamps_microseconds_utc

    def set_timestamps_microseconds_utc(self, timestamps: typing.Union[
        numpy.ndarray, typing.List[int]]) -> 'UnevenlySampledSensor':
        """
        set the time stamps
        :param timestamps: a list of ascending timestamps that associate with each sample value
        :return: An instance of the sensor.
        """
        timestamps = _to_array(timestamps)

        self._unevenly_sampled_channel.set_timestamps_microseconds_utc(timestamps)
        return self

    def sample_interval_mean(self) -> float:
        """
        Returns the mean sample interval for this unevenly sampled sensor channel.
        :return: The mean sample interval for this unevenly sampled sensor channel.
        """
        return self._unevenly_sampled_channel.sample_interval_mean

    def sample_interval_median(self) -> float:
        """
        Returns the median sample interval for this unevenly sampled sensor channel.
        :return: The median sample interval for this unevenly sampled sensor channel.
        """
        return self._unevenly_sampled_channel.sample_interval_median

    def sample_interval_std(self) -> float:
        """
        Returns the standard deviation sample interval for this unevenly sampled sensor channel.
        :return: The standard deviation sample interval for this unevenly sampled sensor channel.
        """
        return self._unevenly_sampled_channel.sample_interval_std

    def metadata(self) -> typing.List[str]:
        """
        Returns this channel's metadata (if there is any) as a Python list.
        :return: This channel's metadata (if there is any) as a Python list.
        """
        return self._unevenly_sampled_channel.metadata

    def set_metadata(self, data: typing.List[str]) -> 'UnevenlySampledSensor':
        """
        sets the metadata
        :param data: metadata as list of strings
        :return: An instance of the sensor.
        """
        self._unevenly_sampled_channel.set_metadata(data)
        return self

    def metadata_as_dict(self) -> typing.Dict[str, str]:
        """
        Returns this channel's metadata (if there is any) as a Python dictionary.
        :return: This channel's metadata (if there is any) as a Python dictionary.
        """
        return _get_metadata_as_dict(self._unevenly_sampled_channel.metadata)

    def set_metadata_as_dict(self, metadata_dict: typing.Dict[str, str]) -> 'UnevenlySampledSensor':
        """
        Sets the metadata using a dictionary.
        :param metadata_dict: Metadata to set.
        :return: An instance of itself.
        """
        self.set_metadata(_metadata_dict_to_list(metadata_dict))
        return self

    def __str__(self) -> str:
        return str(self._unevenly_sampled_channel)

    def __eq__(self, other) -> bool:
        return isinstance(other, UnevenlySampledSensor) and len(self.diff(other)) == 0

    def diff(self, other: 'UnevenlySampledSensor') -> typing.List[str]:
        """
        Compares two unevenly sampled sensors for differences.
        :param other: The other sensor to compare with.
        :return: A list odifferences or an empty list if there are none.
        """
        diffs = map(lambda tuple2: _diff(tuple2[0], tuple2[1]), [
            (self._get_channel_type_names(), other._get_channel_type_names()),
            (self.sensor_name(), other.sensor_name()),
            (self.timestamps_microseconds_utc(), other.timestamps_microseconds_utc()),
            (self.payload_type(), other.payload_type()),
            (self.metadata(), other.metadata()),
            (self._unevenly_sampled_channel.payload, other._unevenly_sampled_channel.payload)
        ])
        # Filter only out only the differences
        diffs = filter(lambda tuple2: tuple2[0], diffs)
        # Extract the difference string
        diffs = map(lambda tuple2: tuple2[1], diffs)
        return list(diffs)


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
        self._unevenly_sampled_channel.set_channel_types([x_type, y_type, z_type])
        self._x_type = x_type
        self._y_type = y_type
        self._z_type = z_type

    def _payload_values(self) -> numpy.ndarray:
        """
        Returns this channel's payload as an interleaved payload of the form
        [[x_0, y_0, z_0], [x_1, y_1, z_1], ..., [x_n, y_n, z_n]].
        :return: This channel's payload as an interleaved payload.
        """
        return self._unevenly_sampled_channel.get_multi_payload([
            self._x_type,
            self._y_type,
            self._z_type
        ])

    def _set_payload_values(self,
                            x_values: typing.Union[typing.List, numpy.ndarray],
                            y_values: typing.Union[typing.List, numpy.ndarray],
                            z_values: typing.Union[typing.List, numpy.ndarray],
                            pl_type: constants.PayloadType) -> 'XyzUnevenlySampledSensor':
        """
        Sets the interleaved payload of this XYZ channel given the X, Y, Z values and payload type.
        :param x_values: The x values.
        :param y_values: The y values.
        :param z_values: The z values.
        :param pl_type: Payload type.
        :return: An instance of the sensor.
        """
        self._unevenly_sampled_channel.set_interleaved_payload([
            x_values,
            y_values,
            z_values
        ],
                pl_type)
        return self

    def payload_values_x(self) -> numpy.ndarray:
        """
        Returns the x-component of this channel's payload.
        :return: The x-component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(self._x_type)

    def payload_values_y(self) -> numpy.ndarray:
        """
        Returns the y-component of this channel's payload.
        :return: The y-component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(self._y_type)

    def payload_values_z(self) -> numpy.ndarray:
        """
        Returns the z-component of this channel's payload.
        :return: The z-component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(self._z_type)

    def payload_values_x_mean(self) -> float:
        """
        Returns the x-component mean of this channel's payload.
        :return: The x-component mean of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(self._x_type)

    def payload_values_y_mean(self) -> float:
        """
        Returns the y-component mean of this channel's payload.
        :return: The y-component mean of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(self._y_type)

    def payload_values_z_mean(self) -> float:
        """
        Returns the z-component mean of this channel's payload.
        :return: The z-component mean of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(self._z_type)

    def payload_values_x_median(self) -> float:
        """
        Returns the x-component median of this channel's payload.
        :return: The x-component median of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(self._x_type)

    def payload_values_y_median(self) -> float:
        """
        Returns the y-component median of this channel's payload.
        :return: The y-component median of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(self._y_type)

    def payload_values_z_median(self) -> float:
        """
        Returns the z-component median of this channel's payload.
        :return: The z-component median of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(self._z_type)

    def payload_values_x_std(self) -> float:
        """
        Returns the x-component standard deviation of this channel's payload.
        :return: The x-component standard deviation of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(self._x_type)

    def payload_values_y_std(self) -> float:
        """
        Returns the y-component standard deviation of this channel's payload.
        :return: The y-component standard deviation of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(self._y_type)

    def payload_values_z_std(self) -> float:
        """
        Returns the z-component standard deviation of this channel's payload.
        :return: The z-component standard deviation of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(self._z_type)


class MicrophoneSensor(EvenlySampledSensor):
    """
    High-level wrapper around microphone channels.
    """

    def __init__(self, evenly_sampled_channel: typing.Optional[EvenlySampledChannel] = None):
        """
        Initialized this channel.
        :param evenly_sampled_channel: An instance of an EvenlySampledChannel with microphone data.
        """
        if evenly_sampled_channel is None:
            evenly_sampled_channel = EvenlySampledChannel()

        super().__init__(evenly_sampled_channel)
        self._evenly_sampled_channel.set_channel_types([api900_pb2.MICROPHONE])

    def concat(self, microphone_sensor: 'MicrophoneSensor') -> 'MicrophoneSensor':
        if self._can_concat(microphone_sensor):
            return self._concat_metadata(microphone_sensor).set_payload_values(numpy.concatenate([self.payload_values(),
                                                                                                  microphone_sensor.payload_values()]))

    def set_payload_values(self,
                           microphone_payload: typing.Union[typing.List[int], numpy.ndarray]) -> 'MicrophoneSensor':
        """
        Sets the microphone channels payload values.
        :param microphone_payload: Payload values.
        :return: An instance of the sensor.
        """
        self._evenly_sampled_channel.set_payload(microphone_payload, constants.PayloadType.INT32_PAYLOAD)
        return self

    def payload_values(self) -> numpy.ndarray:
        """
        Returns the microphone payload as a numpy ndarray of integers.
        :return: The microphone payload as a numpy ndarray of integers.
        """
        return self._evenly_sampled_channel.get_payload(api900_pb2.MICROPHONE)

    def payload_mean(self) -> float:
        """Returns the mean of this channel's payload.
        :return: The mean of this channel's payload.
        """
        return self._evenly_sampled_channel.get_value_mean(api900_pb2.MICROPHONE)

    # Currently, our Android and iOS devices don't calculate a median value, so we calculate it here
    # If the payload is set manually, the median value is calculated by the API
    def payload_median(self) -> numpy.float64:
        """Returns the median of this channel's payload.
        :return: The median of this channel's payload.
        """
        payload_values = self.payload_values()

        if len(payload_values) <= 0:
            raise exceptions.ReaderException("Can't obtain median value of empty array")

        median = numpy.median(self.payload_values())

        if isinstance(median, numpy.ndarray):
            return median[0]
        elif isinstance(median, numpy.float64):
            return median
        else:
            raise exceptions.ReaderException("Unknown type %s" % str(type(median)))

    def payload_std(self) -> float:
        """Returns the standard deviation of this channel's payload.
        :return: The standard deviation of this channel's payload.
        """
        return self._evenly_sampled_channel.get_value_std(api900_pb2.MICROPHONE)


class BarometerSensor(UnevenlySampledSensor):
    """
    High-level wrapper around barometer channels.
    """

    def __init__(self, unevenly_sampled_channel: typing.Optional[UnevenlySampledChannel] = None):
        """
        Initialize this channel
        :param unevenly_sampled_channel: Instance of UnevenlySampledChannel with barometer data
        """
        super().__init__(unevenly_sampled_channel)
        self._unevenly_sampled_channel.set_channel_types([api900_pb2.BAROMETER])

    def concat(self, barometer_sensor: 'BarometerSensor') -> 'BarometerSensor':
        if self._can_concat(barometer_sensor):
            concat_values = numpy.concatenate([self.payload_values(), barometer_sensor.payload_values()])
            return self._concat_timestamps(barometer_sensor) \
                ._concat_metadata(barometer_sensor) \
                .set_payload_values(concat_values)

    def payload_values(self) -> numpy.ndarray:
        """
        Returns this channels payload as a numpy ndarray of floats.
        :return: This channels payload as a numpy ndarray of floats.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.BAROMETER)

    def set_payload_values(self, values: typing.Union[typing.List[float], numpy.ndarray]) -> 'BarometerSensor':
        """
        Sets the barometer sensor's payload.
        :param values:  Payload values.
        :return: An instance of the sensor.
        """
        self._unevenly_sampled_channel.set_payload(values, constants.PayloadType.FLOAT64_PAYLOAD)
        return self

    def payload_mean(self) -> float:
        """Returns the mean of this channel's payload.
        :return: The mean of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(api900_pb2.BAROMETER)

    def payload_median(self) -> float:
        """Returns the median of this channel's payload.
        :return: The median of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(api900_pb2.BAROMETER)

    def payload_std(self) -> float:
        """Returns the standard deviation of this channel's payload.
        :return: The standard deviation of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(api900_pb2.BAROMETER)


# pylint: disable=R0904
class LocationSensor(UnevenlySampledSensor):
    """
    High-level wrapper around location channels.
    """

    def __init__(self, unevenly_sampled_channel: typing.Optional[UnevenlySampledChannel] = None):
        """
        Initialize this channel
        :param unevenly_sampled_channel: Instance of UnevenlySampledChannel containing location data
        """
        super().__init__(unevenly_sampled_channel)
        self._unevenly_sampled_channel.set_channel_types([
            api900_pb2.LATITUDE,
            api900_pb2.LONGITUDE,
            api900_pb2.ALTITUDE,
            api900_pb2.SPEED,
            api900_pb2.ACCURACY
        ])

    def _payload_values(self):
        """
        Return the location payload as an interleaved payload with the following format:
        [[latitude_0, longitude_0, altitude_0, speed_0, accuracy_0],
         [latitude_1, longitude_1, altitude_1, speed_1, accuracy_1],
         ...,
         [latitude_n, longitude_n, altitude_n, speed_n, accuracy_n],]
        :return: array containing interleaved values of the 5 channels
        """
        return self._unevenly_sampled_channel.get_multi_payload([
            api900_pb2.LATITUDE,
            api900_pb2.LONGITUDE,
            api900_pb2.ALTITUDE,
            api900_pb2.SPEED,
            api900_pb2.ACCURACY
        ])

    def concat(self, location_sensor: 'LocationSensor') -> 'LocationSensor':
        concat_latitude = numpy.concatenate([self.payload_values_latitude(), location_sensor.payload_values_latitude()])
        concat_longitude = numpy.concatenate(
                [self.payload_values_longitude(), location_sensor.payload_values_longitude()])
        concat_altitude = numpy.concatenate([self.payload_values_altitude(), location_sensor.payload_values_altitude()])
        concat_speed = numpy.concatenate([self.payload_values_speed(), location_sensor.payload_values_speed()])
        concat_accuracy = numpy.concatenate([self.payload_values_accuracy(), location_sensor.payload_values_accuracy()])
        return self._concat_timestamps(location_sensor)._concat_metadata(location_sensor) \
            .set_payload_values(concat_latitude,
                                concat_longitude,
                                concat_altitude,
                                concat_speed,
                                concat_accuracy)

    def set_payload_values(self,
                           latitude_payload: typing.Union[typing.List[float], numpy.ndarray],
                           longitude_payload: typing.Union[typing.List[float], numpy.ndarray],
                           altitude_payload: typing.Union[typing.List[float], numpy.ndarray],
                           speed_payload: typing.Union[typing.List[float], numpy.ndarray],
                           accuracy_payload: typing.Union[typing.List[float], numpy.ndarray]) -> 'LocationSensor':
        """
        Sets the location sensor's payload. Note that if one of the below channels don't exist, you must still provide
        a zero-filled payload that is the same length as all other paylods.
        :param latitude_payload: The latitude payload.
        :param longitude_payload: The longitude payload.
        :param altitude_payload: The altitude payload.
        :param speed_payload: The speed payload
        :param accuracy_payload: The accuracy payload.
        :return: An instance of the sensor.
        """
        self._unevenly_sampled_channel.set_interleaved_payload([latitude_payload,
                                                                longitude_payload,
                                                                altitude_payload,
                                                                speed_payload,
                                                                accuracy_payload],
                                                               constants.PayloadType.FLOAT64_PAYLOAD)
        return self

    def payload_values_latitude(self):
        """
        Returns the latitude component of this channel's payload.
        :return: The latitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.LATITUDE)

    def payload_values_longitude(self):
        """
        Returns the longitude component of this channel's payload.
        :return: The longitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.LONGITUDE)

    def payload_values_altitude(self):
        """
        Returns the altitude component of this channel's payload.
        :return: The altitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.ALTITUDE)

    def payload_values_speed(self):
        """
        Returns the speed component of this channel's payload.
        :return: The speed component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.SPEED)

    def payload_values_accuracy(self):
        """
        Returns the accuracy component of this channel's payload.
        :return: The accuracy component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.ACCURACY)

    def payload_values_latitude_mean(self) -> float:
        """
        Returns the mean latitude component of this channel's payload.
        :return: The mean latitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(api900_pb2.LATITUDE)

    def payload_values_longitude_mean(self) -> float:
        """
        Returns the mean longitude component of this channel's payload.
        :return: The mean longitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(api900_pb2.LONGITUDE)

    def payload_values_altitude_mean(self) -> float:
        """
        Returns the mean altitude component of this channel's payload.
        :return: The mean altitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(api900_pb2.ALTITUDE)

    def payload_values_speed_mean(self) -> float:
        """
        Returns the mean speed component of this channel's payload.
        :return: The mean speed component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(api900_pb2.SPEED)

    def payload_values_accuracy_mean(self) -> float:
        """
        Returns the mean accuracy component of this channel's payload.
        :return: The mean accuracy component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(api900_pb2.ACCURACY)

    def payload_values_latitude_median(self) -> float:
        """
        Returns the median latitude component of this channel's payload.
        :return: The median latitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(api900_pb2.LATITUDE)

    def payload_values_longitude_median(self) -> float:
        """
        Returns the median longitude component of this channel's payload.
        :return: The median longitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(api900_pb2.LONGITUDE)

    def payload_values_altitude_median(self) -> float:
        """
        Returns the median altitude component of this channel's payload.
        :return: The median altitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(api900_pb2.ALTITUDE)

    def payload_values_speed_median(self) -> float:
        """
        Returns the median speed component of this channel's payload.
        :return: The median speed component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(api900_pb2.SPEED)

    def payload_values_accuracy_median(self) -> float:
        """
        Returns the median accuracy component of this channel's payload.
        :return: The median accuracy component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(api900_pb2.ACCURACY)

    def payload_values_latitude_std(self) -> float:
        """
        Returns the standard deviation latitude component of this channel's payload.
        :return: The standard deviation latitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(api900_pb2.LATITUDE)

    def payload_values_longitude_std(self) -> float:
        """
        Returns the standard deviation longitude component of this channel's payload.
        :return: The standard deviation longitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(api900_pb2.LONGITUDE)

    def payload_values_altitude_std(self) -> float:
        """
        Returns the standard deviation altitude component of this channel's payload.
        :return: The standard deviation altitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(api900_pb2.ALTITUDE)

    def payload_values_speed_std(self) -> float:
        """
        Returns the standard deviation speed component of this channel's payload.
        :return: The standard deviation speed component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(api900_pb2.SPEED)

    def payload_values_accuracy_std(self) -> float:
        """
        Returns the standard deviation accuracy component of this channel's payload.
        :return: The standard deviation accuracy component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(api900_pb2.ACCURACY)


class TimeSynchronizationSensor:
    """High-level wrapper around time synchronization exchange.

    It should be noted that this class only exposes a single method, payload values.
    """

    def __init__(self, unevenly_sampled_channel: typing.Optional[UnevenlySampledChannel] = None):
        """
        Initialized this class.
        :param unevenly_sampled_channel: An unevenly sampled channel with time synchronization payload.
        """
        if unevenly_sampled_channel is None:
            self._unevenly_sampled_channel = UnevenlySampledChannel()
        else:
            self._unevenly_sampled_channel = UnevenlySampledChannel(unevenly_sampled_channel.protobuf_channel)
        self._unevenly_sampled_channel.set_channel_types([api900_pb2.TIME_SYNCHRONIZATION])

    def concat(self, time_synchonization_sensor: 'TimeSynchronizationSensor') -> 'TimeSynchronizationSensor':
        return self.set_payload_values(numpy.concatenate([self.payload_values(),
                                                          time_synchonization_sensor.payload_values()]))

    def payload_type(self) -> str:
        """
        Returns the internal protobuf payload type.
        :return: The internal protobuf payload type.
        """
        return self._unevenly_sampled_channel.get_payload_type()

    def payload_values(self) -> numpy.ndarray:
        """
        Returns the time synchronization exchanges as a numpy ndarray of integers.
        :return: The time synchronization exchanges as a numpy ndarray of integers.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.TIME_SYNCHRONIZATION)

    def set_payload_values(self, payload: typing.Union[typing.List[int], numpy.ndarray]) -> 'TimeSynchronizationSensor':
        """
        Sets the time synch channel's payload.
        :param payload: The payload.
        :return: An instance of the sensor.
        """
        self._unevenly_sampled_channel.set_payload(payload, constants.PayloadType.INT64_PAYLOAD)
        return self

    def metadata(self) -> typing.List[str]:
        """
        Returns this channel's metadata (if there is any) as a Python list.
        :return: This channel's metadata (if there is any) as a Python list.
        """
        return self._unevenly_sampled_channel.metadata

    def set_metadata(self, data: typing.List[str]) -> 'TimeSynchronizationSensor':
        """
        sets the metadata
        :param data: metadata as list of strings
        :return: An instance of itself.
        """
        self._unevenly_sampled_channel.set_metadata(data)
        return self

    def metadata_as_dict(self) -> typing.Dict[str, str]:
        """
        Returns this channel's metadata (if there is any) as a Python dictionary.
        :return: This channel's metadata (if there is any) as a Python dictionary.
        """
        return _get_metadata_as_dict(self._unevenly_sampled_channel.metadata)

    def set_metadata_as_dict(self, metadata_dict: typing.Dict[str, str]) -> 'TimeSynchronizationSensor':
        """
        Sets the metadata.
        :param metadata_dict: Metadata to set.
        :return: An instance of self.
        """
        self.set_metadata(_metadata_dict_to_list(metadata_dict))
        return self

    def __str__(self):
        return str(self._unevenly_sampled_channel)

    def __eq__(self, other) -> bool:
        return isinstance(other, TimeSynchronizationSensor) and len(self.diff(other)) == 0

    def diff(self, other: 'TimeSynchronizationSensor') -> typing.List[str]:
        """
        Compares two time synchronization sensors for differences.
        :param other: The other sensor to compare with.
        :return: A list of differences or an empty list if there are none.
        """
        diffs = map(lambda tuple2: _diff(tuple2[0], tuple2[1]), [
            (self._unevenly_sampled_channel.channel_types, other._unevenly_sampled_channel.channel_types),
            (self.payload_type(), other.payload_type()),
            (self.metadata(), other.metadata()),
            (self._unevenly_sampled_channel.payload, other._unevenly_sampled_channel.payload)
        ])
        # Filter only out only the differences
        diffs = filter(lambda tuple2: tuple2[0], diffs)
        # Extract the difference string
        diffs = map(lambda tuple2: tuple2[1], diffs)
        return list(diffs)


class AccelerometerSensor(XyzUnevenlySampledSensor):
    """High-level wrapper around accelerometer channels."""

    def __init__(self, unevenly_sampled_channel: typing.Optional[UnevenlySampledChannel] = None):
        """
        Initializes this class.
        :param unevenly_sampled_channel: An instance of an UnevenlySampledChanel which contains accelerometer
        X, Y, and Z payload components.
        """
        super().__init__(unevenly_sampled_channel,
                         api900_pb2.ACCELEROMETER_X,
                         api900_pb2.ACCELEROMETER_Y,
                         api900_pb2.ACCELEROMETER_Z)

    def _payload_values(self) -> numpy.ndarray:
        """
        returns the sensor payload as a numpy ndarray
        :return: accelerometer payload as a numpy ndarray
        """
        return self._unevenly_sampled_channel.get_multi_payload([
            api900_pb2.ACCELEROMETER_X,
            api900_pb2.ACCELEROMETER_Y,
            api900_pb2.ACCELEROMETER_Z
        ])

    def concat(self, accelerometer_sensor: 'AccelerometerSensor') -> 'AccelerometerSensor':
        concat_x = numpy.concatenate([self.payload_values_x(), accelerometer_sensor.payload_values_x()])
        concat_y = numpy.concatenate([self.payload_values_y(), accelerometer_sensor.payload_values_y()])
        concat_z = numpy.concatenate([self.payload_values_z(), accelerometer_sensor.payload_values_z()])
        return self._concat_timestamps(accelerometer_sensor) \
            ._concat_metadata(accelerometer_sensor) \
            .set_payload_values(concat_x, concat_y, concat_z)

    def set_payload_values(self,
                           x_values: typing.Union[typing.List[float], numpy.ndarray],
                           y_values: typing.Union[typing.List[float], numpy.ndarray],
                           z_values: typing.Union[typing.List[float], numpy.ndarray]) -> 'AccelerometerSensor':
        """
        Sets this channel's payload with the provided equal length x, y, and z payload values.
        :param x_values: The x values.
        :param y_values: The y values.
        :param z_values: The z values.
        :return: An instance of the sensor.
        """
        self._set_payload_values(x_values, y_values, z_values, constants.PayloadType.FLOAT64_PAYLOAD)
        return self


class MagnetometerSensor(XyzUnevenlySampledSensor):
    """
    Initializes this class.
    :param unevenly_sampled_channel: An instance of an UnevenlySampledChanel which contains magnetometer
    X, Y, and Z payload components.
    """

    def __init__(self, unevenly_sampled_channel: typing.Optional[UnevenlySampledChannel] = None):
        super().__init__(unevenly_sampled_channel,
                         api900_pb2.MAGNETOMETER_X,
                         api900_pb2.MAGNETOMETER_Y,
                         api900_pb2.MAGNETOMETER_Z)

    def _payload_values(self) -> numpy.ndarray:
        """
        returns the sensor payload as a numpy ndarray
        :return: magnetometer payload as a numpy ndarray
        """
        return self._unevenly_sampled_channel.get_multi_payload([
            api900_pb2.MAGNETOMETER_X,
            api900_pb2.MAGNETOMETER_Y,
            api900_pb2.MAGNETOMETER_Z
        ])

    def concat(self, magnetometer_sensor: 'MagnetometerSensor') -> 'MagnetometerSensor':
        concat_x = numpy.concatenate([self.payload_values_x(), magnetometer_sensor.payload_values_x()])
        concat_y = numpy.concatenate([self.payload_values_y(), magnetometer_sensor.payload_values_y()])
        concat_z = numpy.concatenate([self.payload_values_z(), magnetometer_sensor.payload_values_z()])
        return self._concat_timestamps(magnetometer_sensor)._concat_metadata(magnetometer_sensor) \
            .set_payload_values(concat_x, concat_y, concat_z)

    def set_payload_values(self,
                           x_values: typing.Union[typing.List[float], numpy.ndarray],
                           y_values: typing.Union[typing.List[float], numpy.ndarray],
                           z_values: typing.Union[typing.List[float], numpy.ndarray]) -> 'MagnetometerSensor':
        """
        Sets this channel's payload with the provided equal length x, y, and z payload values.
        :param x_values: The x values.
        :param y_values: The y values.
        :param z_values: The z values.
        :return: An instance of the sensor.
        """
        self._set_payload_values(x_values, y_values, z_values, constants.PayloadType.FLOAT64_PAYLOAD)
        return self


class GyroscopeSensor(XyzUnevenlySampledSensor):
    """
    Initializes this class.
    :param unevenly_sampled_channel: An instance of an UnevenlySampledChanel which contains gyroscope
    X, Y, and Z payload components.
    """

    def __init__(self, unevenly_sampled_channel: typing.Optional[UnevenlySampledChannel] = None):
        super().__init__(unevenly_sampled_channel,
                         api900_pb2.GYROSCOPE_X,
                         api900_pb2.GYROSCOPE_Y,
                         api900_pb2.GYROSCOPE_Z)

    def _payload_values(self) -> numpy.ndarray:
        """
        returns the sensor payload as a numpy ndarray
        :return: gyroscope payload as a numpy ndarray
        """
        return self._unevenly_sampled_channel.get_multi_payload([
            api900_pb2.GYROSCOPE_X,
            api900_pb2.GYROSCOPE_Y,
            api900_pb2.GYROSCOPE_Z
        ])

    def concat(self, gyroscope_sensor: 'GyroscopeSensor') -> 'GyroscopeSensor':
        concat_x = numpy.concatenate([self.payload_values_x(), gyroscope_sensor.payload_values_x()])
        concat_y = numpy.concatenate([self.payload_values_y(), gyroscope_sensor.payload_values_y()])
        concat_z = numpy.concatenate([self.payload_values_z(), gyroscope_sensor.payload_values_z()])
        return self._concat_timestamps(gyroscope_sensor)._concat_metadata(gyroscope_sensor) \
            .set_payload_values(concat_x, concat_y, concat_z)

    def set_payload_values(self,
                           x_values: typing.Union[typing.List[float], numpy.ndarray],
                           y_values: typing.Union[typing.List[float], numpy.ndarray],
                           z_values: typing.Union[typing.List[float], numpy.ndarray]) -> 'GyroscopeSensor':
        """
        Sets this channel's payload with the provided equal length x, y, and z payload values.
        :param x_values: The x values.
        :param y_values: The y values.
        :param z_values: The z values.
        :return: An instance of the sensor.
        """
        self._set_payload_values(x_values, y_values, z_values, constants.PayloadType.FLOAT64_PAYLOAD)
        return self


class LightSensor(UnevenlySampledSensor):
    """High-level wrapper around light channels."""

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        """
        Initializes this class
        :param unevenly_sampled_channel: Instance of UnevenlySampledChannel with light sensor payload
        """
        super().__init__(unevenly_sampled_channel)
        self._unevenly_sampled_channel.set_channel_types([api900_pb2.LIGHT])

    def concat(self, light_sensor: 'LightSensor') -> 'LightSensor':
        if self._can_concat(light_sensor):
            concat_values = numpy.concatenate([self.payload_values(), light_sensor.payload_values()])
            return self._concat_timestamps(light_sensor)._concat_metadata(light_sensor) \
                .set_payload_values(concat_values)

    def payload_values(self) -> numpy.ndarray:
        """
        Returns a numpy ndarray of floats representing this light sensor's payload.
        :return: A numpy ndarray of floats representing this light sensor's payload.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.LIGHT)

    def set_payload_values(self, values: typing.Union[typing.List[float], numpy.ndarray]) -> 'LightSensor':
        """
        Sets this channel's payload values.
        :param values: Payload values.
        :return: An instance of the sensor.
        """
        self._unevenly_sampled_channel.set_payload(values, constants.PayloadType.FLOAT64_PAYLOAD)
        return self

    def payload_mean(self) -> float:
        """
        The mean of this channel's payload.
        :return: Mean of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(api900_pb2.LIGHT)

    def payload_median(self) -> float:
        """
        The median of this channel's payload.
        :return: Median of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(api900_pb2.LIGHT)

    def payload_std(self) -> float:
        """
        The standard deviation of this channel's payload.
        :return: Standard deviation of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(api900_pb2.LIGHT)


class InfraredSensor(UnevenlySampledSensor):
    """High-level wrapper around light channels."""

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        """
        Initializes this class
        :param unevenly_sampled_channel: UnevenlySampledChannel with infrared sensor payload
        """
        super().__init__(unevenly_sampled_channel)
        self._unevenly_sampled_channel.set_channel_types([api900_pb2.INFRARED])

    def concat(self, infrared_sensor: 'InfraredSensor') -> 'InfraredSensor':
        if self._can_concat(infrared_sensor):
            concat_values = numpy.concatenate([self.payload_values(), infrared_sensor.payload_values()])
            return self._concat_timestamps(infrared_sensor)._concat_metadata(infrared_sensor) \
                .set_payload_values(concat_values)

    def payload_values(self) -> numpy.ndarray:
        """
        Returns a numpy ndarray of floats representing this sensor's payload.
        :return: A numpy ndarray of floats representing this sensor's payload.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.INFRARED)

    def set_payload_values(self, values: typing.Union[typing.List[float], numpy.ndarray]) -> 'InfraredSensor':
        """
        Sets this channel's payload values.
        :param values: Payload values.
        :return: An instance of the sensor.
        """
        self._unevenly_sampled_channel.set_payload(values, constants.PayloadType.FLOAT64_PAYLOAD)
        return self

    def payload_mean(self) -> float:
        """
        The mean of this channel's payload.
        :return: Mean of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(api900_pb2.INFRARED)

    def payload_median(self) -> float:
        """
        The median of this channel's payload.
        :return: Median of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(api900_pb2.INFRARED)

    def payload_std(self) -> float:
        """
        The standard deviation of this channel's payload.
        :return: Standard deviation of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(api900_pb2.INFRARED)


class ImageSensor(UnevenlySampledSensor):
    """High-level wrapper around image channels."""

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        """
        Initializes this ImageSensor.
        :param unevenly_sampled_channel: The image channel.
        """
        super().__init__(unevenly_sampled_channel)
        self._unevenly_sampled_channel.set_channel_types([api900_pb2.IMAGE])

        self.image_offsets: typing.List[int] = self.parse_offsets()
        """A list of image byte offsets into the payload of this sensor channel."""

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
        return self._unevenly_sampled_channel.get_payload(api900_pb2.IMAGE)

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
        return "{}\nnum images: {}\nbyte offsets: {}".format(self._unevenly_sampled_channel,
                                                             self.num_images(),
                                                             self.image_offsets)


class WrappedRedvoxPacketSummary:
    def __init__(self, wrapped_redvox_packet: 'WrappedRedvoxPacket'):
        microphone_sensor = wrapped_redvox_packet.microphone_channel()
        self.start_time_us = wrapped_redvox_packet.app_file_start_timestamp_machine()
        self.end_time_us = self.start_time_us + date_time_utils.seconds_to_microseconds(len(microphone_sensor.payload_values()) / microphone_sensor.sample_rate_hz())
        self.duration_us = self.end_time_us - self.start_time_us
        self.mic_sample_rate_hz = microphone_sensor.sample_rate_hz()
        self.has_microphone_sensor = wrapped_redvox_packet.has_microphone_channel()
        self.microphone_sensor_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.microphone_channel, MicrophoneSensor.payload_values)
        self.has_barometer_sensor = wrapped_redvox_packet.has_barometer_channel()
        self.barometer_sensor_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.barometer_channel, BarometerSensor.payload_values)
        self.has_time_synchronization_sensor = wrapped_redvox_packet.has_time_synchronization_channel()
        self.time_synchronization_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.time_synchronization_channel, TimeSynchronizationSensor.payload_values)
        self.has_location_sensor = wrapped_redvox_packet.has_location_channel()
        self.location_sensor_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.location_channel, LocationSensor.payload_values_latitude)
        self.has_accelerometer_sensor = wrapped_redvox_packet.has_accelerometer_channel()
        self.accelerometer_sensor_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.accelerometer_channel, AccelerometerSensor.payload_values_x)
        self.has_gyroscope_sensor = wrapped_redvox_packet.has_gyroscope_channel()
        self.gyroscope_sensor_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.gyroscope_channel, GyroscopeSensor.payload_values_x)
        self.has_magnetometer_sensor = wrapped_redvox_packet.has_magnetometer_channel()
        self.magnetometer_sensor_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.magnetometer_channel, MagnetometerSensor.payload_values_x)
        self.has_light_sensor = wrapped_redvox_packet.has_light_channel()
        self.light_sensor_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.light_channel, LightSensor.payload_values)
        self.has_infrared_sensor = wrapped_redvox_packet.has_infrared_channel()
        self.infrared_sensor_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.infrared_channel, InfraredSensor.payload_values)
        
    def _get_num_samples(self,
                         wrapped_redvox_packet: 'WrappedRedvoxPacket',
                         sensor_fn,
                         payload_fn):
        sensor = sensor_fn(wrapped_redvox_packet)
        if sensor is None:
            return 0
        else:
            return len(payload_fn(sensor))

    def __str__(self) -> str:
        return json.dumps(self.__dict__)


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
            self._redvox_packet = api900_pb2.RedvoxPacket()
            self._evenly_sampled_channels = list()
            self._unevenly_sampled_channels = list()
            self._metadata_list = list()
            self._channel_cache = {}

        else:
            self._redvox_packet: api900_pb2.RedvoxPacket = redvox_packet
            """Protobuf api 900 redvox packet"""

            self._evenly_sampled_channels: typing.List[EvenlySampledChannel] = list(
                    map(EvenlySampledChannel, _repeated_to_array(redvox_packet.evenly_sampled_channels)))
            """List of evenly sampled channels"""

            self._unevenly_sampled_channels: typing.List[UnevenlySampledChannel] = list(
                    map(UnevenlySampledChannel, _repeated_to_array(redvox_packet.unevenly_sampled_channels)))
            """List of unevenly sampled channels"""

            self._metadata_list: typing.List[str] = _repeated_to_list(redvox_packet.metadata)
            """List of metadata"""

            self._channel_cache: typing.Dict[int, typing.Union[EvenlySampledChannel, UnevenlySampledChannel]] = {}
            """Holds a mapping of channel type to channel for O(1) access."""

            # Initialize channel cache
            for evenly_sampled_channel in self._evenly_sampled_channels:
                for channel_type in evenly_sampled_channel.channel_types:
                    self._channel_cache[channel_type] = evenly_sampled_channel

            for unevenly_sampled_channel in self._unevenly_sampled_channels:
                for channel_type in unevenly_sampled_channel.channel_types:
                    self._channel_cache[channel_type] = unevenly_sampled_channel

    def redvox_packet(self) -> api900_pb2.RedvoxPacket:
        """
        returns the protobuf redvox packet
        :return: protobuf redvox packet
        """
        return self._redvox_packet

    def _evenly_sampled_channels(self) -> typing.List[EvenlySampledChannel]:
        """
        returns the evenly sampled channels as a copied list to avoid built in functions making untracked changes
        :return: list of evenly sampled channels
        """
        return self._evenly_sampled_channels.copy()

    def _unevenly_sampled_channels(self) -> typing.List[UnevenlySampledChannel]:
        """
        returns the unevenly sampled channels as a copied list to avoid built in functions making untracked changes
        :return: list of unevenly sampled channels
        """
        return self._unevenly_sampled_channels.copy()

    def _refresh_channels(self):
        """
        takes the redvox packet and rebuilds the channel cache from it
        """
        self._evenly_sampled_channels = list(map(EvenlySampledChannel,
                                                 _repeated_to_array(self._redvox_packet.evenly_sampled_channels)))
        self._unevenly_sampled_channels = list(map(UnevenlySampledChannel,
                                                   _repeated_to_array(self._redvox_packet.unevenly_sampled_channels)))
        self._channel_cache = {}
        for evenly_sampled_channel in self._evenly_sampled_channels:
            for channel_type in evenly_sampled_channel.channel_types:
                self._channel_cache[channel_type] = evenly_sampled_channel
        for unevenly_sampled_channel in self._unevenly_sampled_channels:
            for channel_type in unevenly_sampled_channel.channel_types:
                self._channel_cache[channel_type] = unevenly_sampled_channel

    def _add_channel(self, channel: typing.Union[EvenlySampledChannel, UnevenlySampledChannel]):
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

    def _edit_channel(self, channel_type: int, channel: typing.Union[EvenlySampledChannel, UnevenlySampledChannel]):
        """
        removes the channel with the given type and adds the channel supplied
        :param channel_type: type of channel to remove
        :param channel: the channel to add
        """
        index, sampling = self._find_channel(channel_type)
        if index is not None and sampling is not None:
            if type(channel) == EvenlySampledChannel:
                del self._redvox_packet.evenly_sampled_channels[index]
                self._add_channel_redvox_packet(channel)
            elif type(channel) == UnevenlySampledChannel:
                del self._redvox_packet.unevenly_sampled_channels[index]
                self._add_channel_redvox_packet(channel)
            else:
                raise TypeError("Channel type to edit is unknown!")
            self._refresh_channels()
        else:
            raise TypeError("Unknown channel type specified for edit.")

    def _delete_channel(self, channel_type: int):
        """
        deletes the channel type specified
        :param channel_type: a channel to remove
        """
        index, sampling = self._find_channel(channel_type)
        if index is not None and sampling is not None:
            if sampling == EvenlySampledChannel:
                del self._redvox_packet.evenly_sampled_channels[index]
            else:
                del self._redvox_packet.unevenly_sampled_channels[index]
            self._refresh_channels()
        else:
            raise TypeError("Unknown channel type to remove from packet.")

    def _find_channel(self, channel_type: int) -> (int, typing.Union[EvenlySampledChannel, UnevenlySampledChannel]):
        """
        returns the index of the channel and the kind of sampled array its in
        :return: the index in the even or uneven array and the name of the array
        """
        if self._has_channel(channel_type):
            for idx in range(len(self._evenly_sampled_channels)):
                if channel_type in self._evenly_sampled_channels[idx].channel_types:
                    return idx, EvenlySampledChannel
            for idx in range(len(self._unevenly_sampled_channels)):
                if channel_type in self._unevenly_sampled_channels[idx].channel_types:
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
            newchan = self._redvox_packet.evenly_sampled_channels.add()
            newchan.sample_rate_hz = channel.sample_rate_hz
            newchan.first_sample_timestamp_epoch_microseconds_utc = \
                channel.first_sample_timestamp_epoch_microseconds_utc
        elif type(channel) == UnevenlySampledChannel:
            newchan = self._redvox_packet.unevenly_sampled_channels.add()
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
        elif pl_type is None:
            pass
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

    def _get_channel_types(self) -> typing.List[typing.List[int]]:
        """
        Returns a list of channel type enumerations. This is a list of lists, and allows us to easily view
        interleaved channels.
        :return: A list of channel type enumerations.
        """
        channel_types = []
        for evenly_sampled_channel in self._evenly_sampled_channels:
            channel_types.append(evenly_sampled_channel.channel_types)

        for unevenly_sampled_channel in self._unevenly_sampled_channels:
            channel_types.append(unevenly_sampled_channel.channel_types)

        return channel_types

    def _get_channel_type_names(self) -> typing.List[typing.List[str]]:
        """
        Returns a list of channel type names. This is a list of lists, and allows us to easily view
        interleaved channels.
        :return: A list of channel type names. This is a list of lists, and allows us to easily view
        interleaved channels.
        """
        names = []
        for channel_types in self._get_channel_types():
            names.append(list(map(_channel_type_name_from_enum, channel_types)))
        return names

    def _get_channel(self, channel_type: int) -> typing.Union[EvenlySampledChannel, UnevenlySampledChannel, None]:
        """
        Returns a channel from this packet according to the channel type.
        :param channel_type: The channel type to search for.
        :return: A high level channel wrapper or None.
        """
        if channel_type in self._channel_cache:
            return self._channel_cache[channel_type]

        return None

    def _has_channel(self, channel_type: int) -> bool:
        """
        Returns True if this packet contains a channel with this type otherwise False.
        :param channel_type: Channel type to search for.
        :return: True is this packet contains a channel with this type otherwise False.
        """
        return channel_type in self._channel_cache

    def _has_channels(self, channel_types: typing.List[int]) -> bool:
        """
        Checks that this packet contains all of the provided channels.
        :param channel_types: Channel types that this packet must contain.
        :return: True if this packet contains all provided channel types, False otherwise.
        """
        has_channel_results = map(self._has_channel, channel_types)
        for has_channel_result in has_channel_results:
            if not has_channel_result:
                return False
        return True

    def to_json(self) -> str:
        """
        Converts the protobuf packet stored in this wrapped packet to JSON.
        :return: The JSON representation of the protobuf encoded packet.
        """
        return _to_json(self._redvox_packet)

    def compressed_buffer(self) -> bytes:
        """
        Returns the compressed buffer associated with this packet.
        :return: The compressed buffer associated with this packet.
        """
        return _lz4_compress(self._redvox_packet.SerializeToString())

    def default_filename(self, extension: str = "rdvxz") -> str:
        """
        Constructs a default filename from the packet's metadata.
        :param extension: An optional extension to use.
        :return: A default filename from the packet's metadata.
        """
        return "%s_%d.%s" % (self.redvox_id(), int(round(self.app_file_start_timestamp_machine() / 1000.0)), extension)

    def write_rdvxz(self, directory: str, filename: typing.Optional[str] = None):
        """
        Writes a compressed .rdvxz file to the specified directory.
        :param directory: The directory to write the file to.
        :param filename: An optional filename (the default filename will be used if one is not provided).
        """
        filename = self.default_filename() if filename is None else filename
        path = os.path.join(directory, filename)
        with open(path, "wb") as rdvxz_out:
            rdvxz_out.write(self.compressed_buffer())

    def write_json(self, directory: str, filename: typing.Optional[str] = None):
        """
        Writes a RedVox compliant .json file to the specified directory.
        :param directory: The directory to write the file to.
        :param filename: An optional filename (the default filename will be used if one is not provided).
        """
        filename = self.default_filename(extension="json") if filename is None else filename
        path = os.path.join(directory, filename)
        with open(path, "w") as json_out:
            json_out.write(self.to_json())

    def clone(self) -> 'WrappedRedvoxPacket':
        """
        Returns a clone of this WrappedRedvoxPacket.
        :return: A clone of this WrappedRedvoxPacket.
        """
        return read_rdvxz_buffer(self.compressed_buffer())

    def _is_same_sensor(self,
                        wrapped_redvox_packet: 'WrappedRedvoxPacket',
                        sensor_fn,
                        compare_names: bool = True,
                        compare_sample_rates: bool = False) -> bool:

        sensor_1 = sensor_fn(self)
        sensor_2 = sensor_fn(wrapped_redvox_packet)

        # If only one of the sensors is None and the other isn't, they're not the same.
        if len(list(filter(lambda sensor: sensor is None, [sensor_1, sensor_2]))) == 1:
            raise exceptions.ConcatenationException("One sensor is None while the other isn't. self=%s, other=%s" % (
                sensor_1, sensor_2
            ))

        # If the names are different, then they are different sensors
        if compare_names and sensor_1.sensor_name() != sensor_2.sensor_name():
            raise exceptions.ConcatenationException("Sensor names are not the same. self=%s, other=%s" % (
                sensor_1.sensor_name(), sensor_2.sensor_name()
            ))

        if compare_sample_rates and sensor_1.sample_rate_hz() != sensor_2.sample_rate_hz():
            raise exceptions.ConcatenationException("Sample rates are not the same. self=%f, other=%f" % (
                sensor_1.sample_rate_hz(), sensor_2.sample_rate_hz()
            ))

        return True

    def _can_concat(self, wrapped_redvox_packet: 'WrappedRedvoxPacket') -> bool:
        """
        Returns if two packets can be concatenated.
        :param wrapped_redvox_packet: The other packet to test.
        :return: True if they can, False otherwise.
        """
        # Make sure the second packet has same device information
        if self.redvox_id() != wrapped_redvox_packet.redvox_id() or self.uuid() != wrapped_redvox_packet.uuid():
            raise exceptions.ConcatenationException("Devices are not the same. %s:%s != %s:%s" % (
                self.redvox_id(),
                self.uuid(),
                wrapped_redvox_packet.redvox_id(),
                wrapped_redvox_packet.uuid()))

        # Make sure second packet comes after this packet
        if wrapped_redvox_packet.app_file_start_timestamp_machine() < self.app_file_start_timestamp_machine():
            raise exceptions.ConcatenationException("Timestamps are not in order. This packet=%d, other=%d." % (
                self.app_file_start_timestamp_machine(), wrapped_redvox_packet.app_file_start_timestamp_machine()
            ))

        # Ensure same sensor channels exist for each packet
        if self.has_microphone_channel():
            if not wrapped_redvox_packet.has_microphone_channel():
                raise exceptions.ConcatenationException("Packets have difference microphone sensors")

        self._is_same_sensor(wrapped_redvox_packet, WrappedRedvoxPacket.microphone_channel, compare_sample_rates=True)
        self._is_same_sensor(wrapped_redvox_packet, WrappedRedvoxPacket.barometer_channel)
        self._is_same_sensor(wrapped_redvox_packet, WrappedRedvoxPacket.location_channel)
        self._is_same_sensor(wrapped_redvox_packet, WrappedRedvoxPacket.time_synchronization_channel,
                             compare_names=False)
        self._is_same_sensor(wrapped_redvox_packet, WrappedRedvoxPacket.gyroscope_channel)
        self._is_same_sensor(wrapped_redvox_packet, WrappedRedvoxPacket.accelerometer_channel)
        self._is_same_sensor(wrapped_redvox_packet, WrappedRedvoxPacket.magnetometer_channel)
        self._is_same_sensor(wrapped_redvox_packet, WrappedRedvoxPacket.light_channel)
        self._is_same_sensor(wrapped_redvox_packet, WrappedRedvoxPacket.infrared_channel)

        return True

    def concat(self, wrapped_redvox_packet: 'WrappedRedvoxPacket') -> 'WrappedRedvoxPacket':
        """
        Concatenates one WrappedRedvoxPacket with another.

        :param wrapped_redvox_packet: Packet to concat with.
        :return: This packet concatenated with the next.
        """
        if self._can_concat(wrapped_redvox_packet):
            if self.has_microphone_channel():
                self.microphone_channel().concat(wrapped_redvox_packet.microphone_channel())

            if self.has_barometer_channel():
                self.barometer_channel().concat(wrapped_redvox_packet.barometer_channel())

            if self.has_location_channel():
                self.location_channel().concat(wrapped_redvox_packet.location_channel())

            if self.has_time_synchronization_channel():
                self.time_synchronization_channel().concat(wrapped_redvox_packet.time_synchronization_channel())

            if self.has_accelerometer_channel():
                self.accelerometer_channel().concat(wrapped_redvox_packet.accelerometer_channel())

            if self.has_gyroscope_channel():
                self.gyroscope_channel().concat(wrapped_redvox_packet.gyroscope_channel())

            if self.has_magnetometer_channel():
                self.magnetometer_channel().concat(wrapped_redvox_packet.magnetometer_channel())

            if self.has_light_channel():
                self.light_channel().concat(wrapped_redvox_packet.light_channel())

            if self.has_infrared_channel():
                self.infrared_channel().concat(wrapped_redvox_packet.infrared_channel())

        return self

    # Start of packet level API getters and setters
    def api(self) -> int:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.api

    def set_api(self, version: int) -> 'WrappedRedvoxPacket':
        """
        sets the api version number
        :param version: version number
        """
        self._redvox_packet.api = version
        return self

    def uuid(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.uuid

    def set_uuid(self, uid: str) -> 'WrappedRedvoxPacket':
        """
        sets the uuid
        :param uid: uuid string
        """
        self._redvox_packet.uuid = uid
        return self

    def redvox_id(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.redvox_id

    def set_redvox_id(self, rid: str) -> 'WrappedRedvoxPacket':
        """
        sets the redvox id
        :param rid: redvox id string
        """
        self._redvox_packet.redvox_id = rid
        return self

    def authenticated_email(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.authenticated_email

    def set_authenticated_email(self, email: str) -> 'WrappedRedvoxPacket':
        """
        sets the authenticated email
        :param email: authenticated email string
        """
        self._redvox_packet.authenticated_email = email
        return self

    def authentication_token(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.authentication_token

    def set_authentication_token(self, token: str) -> 'WrappedRedvoxPacket':
        """
        sets the authentication token
        :param token: authentication token string
        """
        self._redvox_packet.authentication_token = token
        return self

    def firebase_token(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.firebase_token

    def set_firebase_token(self, token: str) -> 'WrappedRedvoxPacket':
        """
        sets the firebase token
        :param token: firebase token string
        """
        self._redvox_packet.firebase_token = token
        return self

    def is_backfilled(self) -> bool:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.is_backfilled

    def set_is_backfilled(self, tof: bool) -> 'WrappedRedvoxPacket':
        """
        sets the is_backfilled flag
        :param tof: true or false
        """
        self._redvox_packet.is_backfilled = tof
        return self

    def is_private(self) -> bool:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.is_private

    def set_is_private(self, tof: bool) -> 'WrappedRedvoxPacket':
        """
        sets the is_private flag
        :param tof: true or false
        """
        self._redvox_packet.is_private = tof
        return self

    def is_scrambled(self) -> bool:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.is_scrambled

    def set_is_scrambled(self, tof: bool) -> 'WrappedRedvoxPacket':
        """
        sets the is_scrambled flag
        :param tof: true or false
        """
        self._redvox_packet.is_scrambled = tof
        return self

    def device_make(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.device_make

    def set_device_make(self, make: str) -> 'WrappedRedvoxPacket':
        """
        sets the make of the device
        :param make: make of the device string
        """
        self._redvox_packet.device_make = make
        return self

    def device_model(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.device_model

    def set_device_model(self, model: str) -> 'WrappedRedvoxPacket':
        """
        sets the model of the device
        :param model: model of the device string
        """
        self._redvox_packet.device_model = model
        return self

    def device_os(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.device_os

    def set_device_os(self, device_os: str) -> 'WrappedRedvoxPacket':
        """
        sets the device operating system
        :param device_os: operating system string
        """
        self._redvox_packet.device_os = device_os
        return self

    def device_os_version(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.device_os_version

    def set_device_os_version(self, version: str) -> 'WrappedRedvoxPacket':
        """
        sets the device OS version
        :param version: device OS version string
        """
        self._redvox_packet.device_os_version = version
        return self

    def app_version(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.app_version

    def set_app_version(self, version: str) -> 'WrappedRedvoxPacket':
        """
        sets the app version number
        :param version: app version string
        """
        self._redvox_packet.app_version = version
        return self

    def battery_level_percent(self) -> float:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.battery_level_percent

    def set_battery_level_percent(self, percent: float) -> 'WrappedRedvoxPacket':
        """
        sets the percentage of battery left
        :param percent: percentage of battery left
        """
        self._redvox_packet.battery_level_percent = percent
        return self

    def device_temperature_c(self) -> float:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.device_temperature_c

    def set_device_temperature_c(self, temp: float) -> 'WrappedRedvoxPacket':
        """
        sets the device temperature in degrees Celsius
        :param temp: temperature in degrees Celsius
        """
        self._redvox_packet.device_temperature_c = temp
        return self

    def acquisition_server(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.acquisition_server

    def set_acquisition_server(self, server: str) -> 'WrappedRedvoxPacket':
        """
        sets the acquisition server url
        :param server: url to acquisition server
        """
        self._redvox_packet.acquisition_server = server
        return self

    # pylint: disable=invalid-name
    def time_synchronization_server(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.time_synchronization_server

    def set_time_synchronization_server(self, server: str) -> 'WrappedRedvoxPacket':
        """
        sets the time synchronization server url
        :param server: url to time synchronization server
        """
        self._redvox_packet.time_synchronization_server = server
        return self

    def authentication_server(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.authentication_server

    def set_authentication_server(self, server: str) -> 'WrappedRedvoxPacket':
        """
        sets the authentication server url
        :param server: url to authentication server
        """
        self._redvox_packet.authentication_server = server
        return self

    # pylint: disable=invalid-name
    def app_file_start_timestamp_epoch_microseconds_utc(self) -> int:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.app_file_start_timestamp_epoch_microseconds_utc

    def set_app_file_start_timestamp_epoch_microseconds_utc(self, time: int) -> 'WrappedRedvoxPacket':
        """
        sets the timestamp of packet creation
        :param time: time when packet was created in microseconds since utc epoch
        """
        self._redvox_packet.app_file_start_timestamp_epoch_microseconds_utc = time
        return self

    # pylint: disable=invalid-name
    def app_file_start_timestamp_machine(self) -> int:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.app_file_start_timestamp_machine

    def set_app_file_start_timestamp_machine(self, time: int) -> 'WrappedRedvoxPacket':
        """
        sets the internal machine timestamp of packet creation
        :param time: time when packet was created on local machine
        """
        self._redvox_packet.app_file_start_timestamp_machine = time
        return self

    # pylint: disable=invalid-name
    def server_timestamp_epoch_microseconds_utc(self) -> int:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.server_timestamp_epoch_microseconds_utc

    def set_server_timestamp_epoch_microseconds_utc(self, time: int) -> 'WrappedRedvoxPacket':
        """
        sets the server timestamp when the packet was received
        :param time: time when packet was received by server
        """
        self._redvox_packet.server_timestamp_epoch_microseconds_utc = time
        return self

    def metadata(self) -> typing.List[str]:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._metadata_list

    def set_metadata(self, data: typing.List[str]) -> 'WrappedRedvoxPacket':
        """
        sets the metadata
        :param data: metadata as list of strings
        """
        self._metadata_list = data
        self._redvox_packet.metadata[:] = data
        return self

    def _clear_metadata(self):
        """
        removes all of the packet level metadata from packet
        """
        del self._redvox_packet.metadata[:]
        self._metadata_list.clear()

    def metadata_as_dict(self) -> typing.Dict[str, str]:
        """
        Return this packet's metadata as a key-value Python dictionary.
        :return: This packet's metadata as a key-value Python dictionary.
        """
        return _get_metadata_as_dict(self._metadata_list)

    def set_metadata_as_dict(self, metadata_dict: typing.Dict[str, str]) -> 'WrappedRedvoxPacket':
        self.set_metadata(_metadata_dict_to_list(metadata_dict))
        return self

    # Sensor channels
    def has_microphone_channel(self) -> bool:
        """
        Returns if this packet has a microphone channel.
        :return: If this packet has a microphone channel.
        """
        return self._has_channel(api900_pb2.MICROPHONE)

    def microphone_channel(self) -> typing.Optional[MicrophoneSensor]:
        """
        Returns the high-level microphone channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level microphone channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_microphone_channel():
            return MicrophoneSensor(self._get_channel(api900_pb2.MICROPHONE))

        return None

    def set_microphone_channel(self, microphone_sensor: typing.Optional[MicrophoneSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packets microphone sensor. A channel can be removed by passing in None.
        :param microphone_sensor: An optional instance of a microphone sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_microphone_channel():
            self._delete_channel(api900_pb2.MICROPHONE)

        if microphone_sensor is not None:
            self._add_channel(microphone_sensor._evenly_sampled_channel)

        return self

    def has_barometer_channel(self) -> bool:
        """
        Returns if this packet has a barometer channel.
        :return: If this packet has a barometer channel.
        """
        return self._has_channel(api900_pb2.BAROMETER)

    def barometer_channel(self) -> typing.Optional[BarometerSensor]:
        """
        Returns the high-level barometer channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level barometer channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_barometer_channel():
            return BarometerSensor(self._get_channel(api900_pb2.BAROMETER))

        return None

    def set_barometer_channel(self, barometer_sensor: typing.Optional[BarometerSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packets barometer sensor. A channel can be removed by passing in None.
        :param barometer_sensor: An optional instance of a barometer sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_barometer_channel():
            self._delete_channel(api900_pb2.BAROMETER)

        if barometer_sensor is not None:
            self._add_channel(barometer_sensor._unevenly_sampled_channel)

        return self

    def has_location_channel(self) -> bool:
        """
        Returns if this packet has a location channel.
        :return: If this packet has a location channel.
        """
        return (self._has_channels(
                [api900_pb2.LATITUDE, api900_pb2.LONGITUDE, api900_pb2.ALTITUDE, api900_pb2.SPEED,
                 api900_pb2.ACCURACY]) or
                self._has_channels([api900_pb2.LATITUDE, api900_pb2.LONGITUDE]))

    def location_channel(self) -> typing.Optional[LocationSensor]:
        """
        Returns the high-level location channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level location channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_location_channel():
            return LocationSensor(self._get_channel(api900_pb2.LATITUDE))

        return None

    def set_location_channel(self, location_sensor: typing.Optional[LocationSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's location sensor. A channel can be removed by passing in None.
        :param location_sensor: An optional instance of a location sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_location_channel():
            self._delete_channel(api900_pb2.LATITUDE)

        if location_sensor is not None:
            self._add_channel(location_sensor._unevenly_sampled_channel)

        return self

    # pylint: disable=invalid-name,C1801
    def has_time_synchronization_channel(self) -> bool:
        """
        Returns if this packet has a time synchronization channel.
        :return: If this packet has a time synchronization channel.
        """
        if self._has_channel(api900_pb2.TIME_SYNCHRONIZATION):
            ch = TimeSynchronizationSensor(self._get_channel(api900_pb2.TIME_SYNCHRONIZATION))
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
            return TimeSynchronizationSensor(self._get_channel(api900_pb2.TIME_SYNCHRONIZATION))

        return None

    def set_time_synchronization_channel(self, time_synchronization_sensor: typing.Optional[
        TimeSynchronizationSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's time sync sensor. A channel can be removed by passing in None.
        :param time_synchronization_sensor: An optional instance of a time sync sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_time_synchronization_channel():
            self._delete_channel(api900_pb2.TIME_SYNCHRONIZATION)

        if time_synchronization_sensor is not None:
            self._add_channel(time_synchronization_sensor._unevenly_sampled_channel)

        return self

    def has_accelerometer_channel(self) -> bool:
        """
        Returns if this packet has an accelerometer channel.
        :return: If this packet has an accelerometer channel.
        """
        return self._has_channels([api900_pb2.ACCELEROMETER_X, api900_pb2.ACCELEROMETER_Y, api900_pb2.ACCELEROMETER_Z])

    def accelerometer_channel(self) -> typing.Optional[AccelerometerSensor]:
        """
        Returns the high-level accelerometer channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level accelerometer channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_accelerometer_channel():
            return AccelerometerSensor(self._get_channel(api900_pb2.ACCELEROMETER_X))

        return None

    def set_accelerometer_channel(self,
                                  accelerometer_sensor: typing.Optional[AccelerometerSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's accelerometer sensor. A channel can be removed by passing in None.
        :param accelerometer_sensor: An optional instance of a accelerometer sensor.
        """
        if self.has_accelerometer_channel():
            self._delete_channel(api900_pb2.ACCELEROMETER_X)

        if accelerometer_sensor is not None:
            self._add_channel(accelerometer_sensor._unevenly_sampled_channel)

        return self

    def has_magnetometer_channel(self) -> bool:
        """
        Returns if this packet has a magnetometer channel.
        :return: If this packet has a magnetometer channel.
        """
        return self._has_channels([api900_pb2.MAGNETOMETER_X, api900_pb2.MAGNETOMETER_Y, api900_pb2.MAGNETOMETER_Z])

    def magnetometer_channel(self) -> typing.Optional[MagnetometerSensor]:
        """
        Returns the high-level magnetometer channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level magnetometer channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_magnetometer_channel():
            return MagnetometerSensor(self._get_channel(api900_pb2.MAGNETOMETER_X))

        return None

    def set_magnetometer_channel(self,
                                 magnetometer_sensor: typing.Optional[MagnetometerSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's magnetomer sensor. A channel can be removed by passing in None.
        :param magnetometer_sensor: An optional instance of a magnetometer sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_magnetometer_channel():
            self._delete_channel(api900_pb2.MAGNETOMETER_X)

        if magnetometer_sensor is not None:
            self._add_channel(magnetometer_sensor._unevenly_sampled_channel)

        return self

    def has_gyroscope_channel(self) -> bool:
        """
        Returns if this packet has a gyroscope channel.
        :return: If this packet has a gyroscope channel.
        """
        return self._has_channels([api900_pb2.GYROSCOPE_X, api900_pb2.GYROSCOPE_Y, api900_pb2.GYROSCOPE_Z])

    def gyroscope_channel(self) -> typing.Optional[GyroscopeSensor]:
        """
        Returns the high-level gyroscope channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level gyroscope channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_gyroscope_channel():
            return GyroscopeSensor(self._get_channel(api900_pb2.GYROSCOPE_X))

        return None

    def set_gyroscope_channel(self, gyroscope_sensor: typing.Optional[GyroscopeSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's gyroscope sensor. A channel can be removed by passing in None.
        :param gyroscope_sensor: An optional instance of a gyroscope sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_gyroscope_channel():
            self._delete_channel(api900_pb2.GYROSCOPE_X)

        if gyroscope_sensor is not None:
            self._add_channel(gyroscope_sensor._unevenly_sampled_channel)

        return self

    def has_light_channel(self) -> bool:
        """
        Returns if this packet has a light channel.
        :return: If this packet has a light channel.
        """
        return self._has_channel(api900_pb2.LIGHT)

    def light_channel(self) -> typing.Optional[LightSensor]:
        """
        Returns the high-level light channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level light channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_light_channel():
            return LightSensor(self._get_channel(api900_pb2.LIGHT))

        return None

    def set_light_channel(self, light_sensor: typing.Optional[LightSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's light sensor. A channel can be removed by passing in None.
        :param light_sensor: An optional instance of a light sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_light_channel():
            self._delete_channel(api900_pb2.LIGHT)

        if light_sensor is not None:
            self._add_channel(light_sensor._unevenly_sampled_channel)

        return self

    def has_infrared_channel(self) -> bool:
        """
        Returns if this packet has an infrared channel.
        :return: If this packlet has an infrared channel.
        """
        return self._has_channel(api900_pb2.INFRARED)

    def infrared_channel(self) -> typing.Optional[InfraredSensor]:
        """
        Returns the high-level infrared channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level infrared channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_infrared_channel():
            return InfraredSensor(self._get_channel(api900_pb2.INFRARED))

        return None

    def set_infrared_channel(self, infrared_sensor: typing.Optional[InfraredSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's infrared sensor. A channel can be removed by passing in None.
        :param infrared_sensor: An optional instance of a infrared sensor.
        """
        if self.has_infrared_channel():
            self._delete_channel(api900_pb2.INFRARED)

        if infrared_sensor is not None:
            self._add_channel(infrared_sensor._unevenly_sampled_channel)

        return self

    def has_image_channel(self) -> bool:
        """
        Returns if this packet has an image channel.
        :return: If this packlet has an image channel.
        """
        return self._has_channel(api900_pb2.IMAGE)

    def image_channel(self) -> typing.Optional[ImageSensor]:
        """
        Returns the high-level image channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level image channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_image_channel():
            return ImageSensor(self._get_channel(api900_pb2.IMAGE))

        return None

    def set_image_channel(self, image_sensor: typing.Optional[ImageSensor]):
        """
        Set's the image channel.
        :param image_sensor: Image sensor.
        """
        if self.has_image_channel():
            self._delete_channel(api900_pb2.IMAGE)

        if image_sensor is not None:
            self._add_channel(image_sensor._unevenly_sampled_channel)

    def __str__(self):
        """
        Returns protobuf's String representation of this packet.
        :return: Protobuf's String representation of this packet.
        """
        return str(self._redvox_packet)

    def __eq__(self, other):
        return isinstance(other, WrappedRedvoxPacket) and len(self.diff(other)) == 0

    def diff(self, other: 'WrappedRedvoxPacket') -> typing.List[str]:
        """
        Finds the differences (if any) between two WrappedRedvoxPackets.
        :param other: The other wrapped redvox packet to compare to.
        :return: A list of differences or an empty list if there are none.
        """
        diffs = map(lambda tuple2: _diff(tuple2[0], tuple2[1]), [
            (self.api(), other.api()),
            (self.redvox_id(), other.redvox_id()),
            (self.uuid(), other.uuid()),
            (self.authenticated_email(), other.authenticated_email()),
            (self.authentication_token(), other.authentication_token()),
            (self.firebase_token(), other.firebase_token()),
            (self.is_backfilled(), other.is_backfilled()),
            (self.is_private(), other.is_private()),
            (self.is_scrambled(), other.is_scrambled()),
            (self.device_make(), other.device_make()),
            (self.device_model(), other.device_model()),
            (self.device_os(), other.device_os()),
            (self.device_os_version(), other.device_os_version()),
            (self.app_version(), other.app_version()),
            (self.battery_level_percent(), other.battery_level_percent()),
            (self.device_temperature_c(), other.device_temperature_c()),
            (self.acquisition_server(), other.acquisition_server()),
            (self.time_synchronization_server(), other.time_synchronization_server()),
            (self.authentication_server(), other.authentication_server()),
            (self.app_file_start_timestamp_epoch_microseconds_utc(),
             other.app_file_start_timestamp_epoch_microseconds_utc()),
            (self.app_file_start_timestamp_machine(), other.app_file_start_timestamp_machine()),
            (self.server_timestamp_epoch_microseconds_utc(),
             other.server_timestamp_epoch_microseconds_utc()),
            (self.metadata(), other.metadata()),
            (self.microphone_channel(), other.microphone_channel()),
            (self.barometer_channel(), other.barometer_channel()),
            (self.location_channel(), other.location_channel()),
            (self.time_synchronization_channel(), other.time_synchronization_channel()),
            (self.accelerometer_channel(), other.accelerometer_channel()),
            (self.magnetometer_channel(), other.magnetometer_channel()),
            (self.gyroscope_channel(), other.gyroscope_channel()),
            (self.light_channel(), other.light_channel()),
            (self.infrared_channel(), other.infrared_channel())
        ])
        # Filter only out only the differences
        diffs = filter(lambda tuple2: tuple2[0], diffs)
        # Extract the difference string
        diffs = map(lambda tuple2: tuple2[1], diffs)
        return list(diffs)


def wrap(redvox_packet: api900_pb2.RedvoxPacket) -> WrappedRedvoxPacket:
    """Shortcut for wrapping a protobuf packet with our higher level wrapper.

    Args:
        redvox_packet: The redvox packet to wrap.

    Returns:
        A wrapper redvox packet.
    """
    return WrappedRedvoxPacket(redvox_packet)


def read_buffer(buf: bytes, is_compressed: bool = True) -> api900_pb2.RedvoxPacket:
    """
    Deserializes a serialized protobuf RedvoxPacket buffer.
    :param buf: Buffer to deserialize.
    :param is_compressed: Whether or not the buffer is compressed or decompressed.
    :return: Deserialized protobuf redvox packet.
    """
    buffer = _lz4_decompress(buf) if is_compressed else buf
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
        return wrap(_from_json(json_in.read()))


def read_json_string(json: str) -> WrappedRedvoxPacket:
    """
    Reads a RedVox compliant API 900 json string and returns a WrappedRedvoxPacket.
    :param json: RedVox API 900 compliant json string.
    :return: A WrappedRedvoxPacket.
    """
    return wrap(_from_json(json))


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
