"""
This module provides functions and classes for working with api900 protobuf data.
"""

import api900.api900_pb2

import struct
import typing

import google.protobuf.internal.containers as containers
import lz4.block
import numpy


class ReaderException(Exception):
    def __init__(self, msg: str = "ReaderException"):
        super(ReaderException, self).__init__(msg)


def calculate_uncompressed_size(buf: bytes) -> int:
    """Given a buffer, calculate the original size of the uncompressed packet by looking at the first four bytes.

    Args:
        buf: Buffer where first 4 bytes contain the size of the original uncompressed packet.
            The bytes are encoded big endian.


    Returns:
        The total number of bytes in the original uncompressed packet.

    """
    return struct.unpack(">I", buf[:4])[0]


def lz4_decompress(buf: bytes) -> bytes:
    """Decompresses an API 900 compressed buffer.

    Args:
        buf: The buffer to decompress.

    Returns: The uncompressed buffer.

    """

    uncompressed_size = calculate_uncompressed_size(buf)

    if uncompressed_size <= 0:
        raise ReaderException("uncompressed size [{}] must be > 0".format(uncompressed_size))

    return lz4.block.decompress(buf[4:], uncompressed_size=calculate_uncompressed_size(buf))


def read_buffer(buf: bytes, is_compressed: bool = True) -> api900.api900_pb2.RedvoxPacket:
    """Deserializes a serialized protobuf RedvoxPacket buffer.

    Args:
        buf: Buffer to deserialize.
        is_compressed: Whether or not the buffer is compressed or decompressed.

    Returns:
        Deserialized protobuf redvox packet.

    """
    buffer = lz4_decompress(buf) if is_compressed else buf
    redvox_packet = api900.api900_pb2.RedvoxPacket()
    redvox_packet.ParseFromString(buffer)
    return redvox_packet


def read_file(file: str, is_compressed: bool = None) -> api900.api900_pb2.RedvoxPacket:
    """Deserializes a serialized protobuf RedvoxPacket file.

    Args:
        file: File to deserialize.
        is_compressed: Whether or not the file is compressed or decompressed.

    Returns:
        Deserialized protobuf redvox packet.

    """
    file_ext = file.split(".")[-1]

    if is_compressed is None:
        _is_compressed = True if file_ext == "rdvxz" else False
    else:
        _is_compressed = is_compressed
    with open(file, "rb") as fin:
        return read_buffer(fin.read(), _is_compressed)


def extract_payload(channel: typing.Union[api900.api900_pb2.EvenlySampledChannel,
                                          api900.api900_pb2.UnevenlySampledChannel]) -> numpy.ndarray:
    """
    Given an evenly on unevenly sampled channel, extracts the entire payload.

    This will return a payload of either ints or floats and is type agnostic when it comes to the underlying
    protobuf type.

    Args:
        channel: The protobuf channel to extract the payload from.

    Returns:
        A numpy array of either floats or ints.
    """
    payload_type = channel.WhichOneof("payload")

    if payload_type == "byte_payload":
        payload = channel.byte_payload.payload
    elif payload_type == "uint32_payload":
        payload = channel.uint32_payload.payload
    elif payload_type == "uint64_payload":
        payload = channel.uint64_payload.payload
    elif payload_type == "int32_payload":
        payload = channel.int32_payload.payload
    elif payload_type == "int64_payload":
        payload = channel.int64_payload.payload
    elif payload_type == "float32_payload":
        payload = channel.float32_payload.payload
    elif payload_type == "float64_payload":
        payload = channel.float64_payload.payload
    else:
        raise ReaderException("unsupported payload type {}".format(payload_type))

    return numpy.array(payload)


def repeated_to_list(repeated: typing.Union[containers.RepeatedCompositeFieldContainer,
                                            containers.RepeatedScalarFieldContainer]) -> typing.List:
    """Transforms a repeated protobuf field into a list.
    
    Args:
        repeated: The repeated field to transform.

    Returns:
        A list of the repeated items.

    """
    return repeated[0:len(repeated)]


def repeated_to_array(repeated: typing.Union[containers.RepeatedCompositeFieldContainer,
                                             containers.RepeatedScalarFieldContainer]) -> numpy.ndarray:
    """Transforms a repeated protobuf field into a numpy array.

    Args:
        repeated: The repeated field to transform.

    Returns:
        An array of the repeated items.

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


    Args:
        ndarray: The interleaved.
        offset: The offset into the array.
        step: The step size.

    Returns:
        A numpy array of a single channel type.
    """

    if len(ndarray) == 0:
        raise ReaderException("empty array")

    if offset < 0 or offset >= len(ndarray):
        raise ReaderException("offset {} out of range [{},{})".format(offset, 0, len(ndarray)))

    if offset >= step:
        raise ReaderException("offset {} must be smaller than step {}".format(offset, step))

    if step <= 0 or step > len(ndarray):
        raise ReaderException("step {} out of range [{},{})".format(step, 0, len(ndarray)))

    if len(ndarray) % step != 0:
        raise ReaderException("step {} is not a multiple of {}".format(step, len(ndarray)))

    return ndarray[offset::step]


def interleave_arrays(arrays: typing.List[numpy.ndarray]) -> numpy.ndarray:
    """Interleaves multiple arrays together.

    Args:
        arrays: Arrays to interleave.

    Returns:
        Interleaved arrays.
    """

    if len(arrays) < 2:
        raise ReaderException("At least 2 arrays are required for interleaving")

    if len(set(map(len, arrays))) > 1:
        raise ReaderException("all arrays must be same size")

    total_arrays = len(arrays)
    total_elements = sum(map(lambda array: array.size, arrays))
    r = numpy.empty((total_elements,), dtype=arrays[0].dtype)
    for i in range(total_arrays):
        r[i::total_arrays] = arrays[i]

    return r


def safe_index_of(lst: typing.List, v: typing.Any) -> int:
    """Finds the index of an item in a list and instead of throwing an exception returns -1 when the  item DNE.

    Args:
        lst: List to search through.
        v: The value to find the index of.

    Returns:
        The index of the first value v found or -1.
    """
    try:
        return lst.index(v)
    except ValueError:
        return -1


def empty_array() -> numpy.ndarray:
    """Returns an empty numpy array.

    Returns:
        An empty numpy array.
    """
    return numpy.array([])


def channel_type_name_from_enum(enum_constant: int) -> str:
    """Returns the name of a channel type given its enumeration constant.

    Args:
        enum_constant: The constant to turn into a name.

    Returns:
        The name of the channel.
    """
    return api900.api900_pb2.ChannelType.Name(enum_constant)


def get_metadata(metadata: typing.List[str], k: str) -> str:
    """ Given a meta-data key, extract the value.

    Args:
        metadata: List of metadata to extract value from.
        k: The meta-data key.

    Returns:
        The value corresponding to the key or an empty string "".
    """

    if len(metadata) % 2 != 0:
        raise ReaderException("metadata list must contain an even number of items")

    idx = safe_index_of(metadata, k)
    if idx < 0:
        return ""
    else:
        return metadata[idx + 1]


def get_metadata_as_dict(metadata: typing.List[str]) -> typing.Dict[str, str]:
    """Since the metadata is inherently key-value, it may be useful to turn the metadata list into a python dictionary.

    Args:
        metadata: The metadata list.

    Returns:
        Metadata as a python dictionary.
    """

    if len(metadata) == 0:
        return {}

    if len(metadata) % 2 != 0:
        raise ReaderException("metadata list must contain an even number of items")

    metadata_dict = {}
    metadata_copy = metadata.copy()
    while len(metadata_copy) >= 2:
        k = metadata_copy.pop(0)
        v = metadata_copy.pop(0)
        if k not in metadata_dict:
            metadata_dict[k] = v
    return metadata_dict


class InterleavedChannel:
    """
    This class represents an interleaved channel.

    An interleaved channel contains multiple channel types in a single payload. This is useful for situations where
    a sensor produces several values for a single timestamp. For example, a GPS will produce a LATITUDE, LONGITUDE,
    ALTITUDE, and SPEED values with every update. An interleaved channel is an encoding that encodes multiple channel
    types into a single payload.

    Every channel has a field channel_types that list the channel types contained within the payload. For a GPS sensor,
    the channel_types array would look like [LATITUDE, LONGITUDE, ALTITUDE, SPEED]. The location of the channel type
    in channel_types determines the offset into the payload and the length of channel_types determines the step size.
    As such, this hypothetical GPS channel payload be encoded as:

    [LAT0, LNG0, ALT0, SPD0, LAT1, LNG1, ALT1, SPD1, ..., LATn, LNGn, ALTn, SPDn]

    This class provides methods for working with interleaved channels as well as accessing interleaved statistic values.
    """

    def __init__(self, channel: typing.Union[api900.api900_pb2.EvenlySampledChannel,
                                             api900.api900_pb2.UnevenlySampledChannel]):
        """Initializes this interleaved channel object.

        Args:
            channel: Either a protobuf evenly or unevenly sampled channel.
        """
        self.protobuf_channel: typing.Union[api900.api900_pb2.EvenlySampledChannel,
                                            api900.api900_pb2.UnevenlySampledChannel] = channel
        """Reference to the original protobuf channel"""

        self.sensor_name: str = channel.sensor_name
        """Provided sensor name"""

        self.channel_types: typing.List[
            typing.Union[
                api900.api900_pb2.EvenlySampledChannel,
                api900.api900_pb2.UnevenlySampledChannel]] = repeated_to_list(channel.channel_types)
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

        self.channel_type_index: typing.Dict[api900.api900_pb2.ChannelType, int] = {self.channel_types[i]: i for i in
                                                                                    range(len(self.channel_types))}
        """Contains a mapping of channel type to index in channel_types array"""

    def get_channel_type_names(self) -> typing.List[str]:
        """Returns the list of channel_types as a list of names instead of enumeration constants.

        Returns:
            Returns the list of channel_types as a list of names instead of enumeration constants.
        """
        return list(map(channel_type_name_from_enum, self.channel_types))

    def channel_index(self, channel_type: int) -> int:
        """Returns the index of a channel type or -1 if it DNE.

        Args:
            channel_type:

        Returns:

        """
        return self.channel_type_index[channel_type] if channel_type in self.channel_type_index else -1

    def has_channel(self, channel_type: int) -> bool:
        """Returns if channel type exists with in this channel.

        Args:
            channel_type: The channel type to seach for.

        Returns:
            True if it exists otherwise False
        """
        return channel_type in self.channel_type_index

    def has_payload(self, channel_type: int) -> bool:
        """Returns if channel contains a non-empty specified payload.

        Args:
            channel_type: The channel to check for a payload for.

        Returns: Whether this channel contains the specified payload.

        """
        return self.has_channel(channel_type) and len(self.payload) > 0

    def get_payload(self, channel_type: int) -> numpy.ndarray:
        """Returns a deinterleaved payload of a given channel type or an empty array.

        Args:
            channel_type: The channel type to extract/deinterleave from the payload.

        Returns:
            A numpy array of floats or ints of a single channel type.
        """
        idx = self.channel_index(channel_type)
        if idx < 0:
            return empty_array()
        else:
            return deinterleave_array(self.payload, idx, len(self.channel_types))

    def get_multi_payload(self, channel_types: typing.List[int]) -> numpy.ndarray:
        channel_types_len = len(channel_types)
        if channel_types_len == 0:
            return empty_array()
        elif channel_types_len == 1:
            return self.get_payload(channel_types[0])
        else:
            payloads = list(map(self.get_payload, channel_types))
            return interleave_arrays(payloads)

    def get_value_mean(self, channel_type: int) -> float:
        """Returns the mean value for a single channel type.

        Args:
            channel_type: The channel type to extract the mean from.

        Returns:
            The mean value or 0.0 if the mean value DNE.
        """
        idx = self.channel_index(channel_type)
        if idx < 0:
            return 0.0
        else:
            return self.value_means[idx]

    def get_value_std(self, channel_type: int) -> float:
        """Returns the standard deviation value for a single channel type.

        Args:
            channel_type: The channel type to extract the mean from.

        Returns:
            The standard deviation value or 0.0 if the standard deviation value DNE.
        """
        idx = self.channel_index(channel_type)
        if idx < 0:
            return 0.0
        else:
            return self.value_stds[idx]

    def get_value_median(self, channel_type: int) -> float:
        """Returns the median value for a single channel type.

        Args:
            channel_type: The channel type to extract the mean from.

        Returns:
            The median value or 0.0 if the median value DNE.
        """
        idx = self.channel_index(channel_type)
        if idx < 0:
            return 0.0
        else:
            return self.value_medians[idx]

    def __str__(self) -> str:
        return "sensor_name: {}\nchannel_types: {}\nlen(payload): {}".format(self.sensor_name,
                                                                             list(map(channel_type_name_from_enum,
                                                                                      self.channel_types)),
                                                                             len(self.payload))


class EvenlySampledChannel(InterleavedChannel):
    """
    An evenly sampled channel is an interleaved channel that also has a channel with an even sampling rate.
    """

    def __init__(self, channel: api900.api900_pb2.EvenlySampledChannel):
        """Initializes this evenly sampled channel.

        Args:
            channel: A protobuf evenly sampled channel.
        """
        InterleavedChannel.__init__(self, channel)
        self.sample_rate_hz: float = channel.sample_rate_hz
        """The sample rate in hz of this evenly sampled channel"""

        self.first_sample_timestamp_epoch_microseconds_utc: int = channel.first_sample_timestamp_epoch_microseconds_utc
        """The timestamp of the first sample"""

    def __str__(self) -> str:
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

    def __init__(self, channel: api900.api900_pb2.UnevenlySampledChannel):
        """Initializes this unevenly sampled channel.

        Args:
            channel: A protobuf unevenly sampled channel.
        """
        InterleavedChannel.__init__(self, channel)
        self.timestamps_microseconds_utc: numpy.ndarray = repeated_to_array(channel.timestamps_microseconds_utc)
        """Numpy array of timestamps epoch microseconds utc for each sample"""

        self.sample_interval_mean: float = channel.sample_interval_mean
        """The mean sample interval"""

        self.sample_interval_std: float = channel.sample_interval_std
        """The standard deviation of the sample interval"""

        self.sample_interval_median: float = channel.sample_interval_median
        """The median sample interval"""

    def __str__(self) -> str:
        return "{}\nlen(timestamps_microseconds_utc): {}".format(super().__str__(),
                                                                 len(self.timestamps_microseconds_utc))


class WrappedRedvoxPacket:
    """
    This class provides convenience methods for accessing API 900 protobuf redvox packets.

    This packet contains a reference to the original packet which should be used to access all "top-level" fields. For
    accessing channels, this class can search for and return our high-level channel wrappers or can extract the payload
    directly.
    """

    def __init__(self, redvox_packet: api900.api900_pb2.RedvoxPacket):
        """Initializes this wrapped redvox packet.

        Args:
            redvox_packet: A protobuf redvox packet.
        """

        self.redvox_packet: api900.api900_pb2.RedvoxPacket = redvox_packet
        """Protobuf api 900 redvox packet"""

        self.evenly_sampled_channels: typing.List[EvenlySampledChannel] = list(
            map(lambda even_channel:
                EvenlySampledChannel(even_channel),
                repeated_to_array(redvox_packet.evenly_sampled_channels)))
        """List of evenly sampled channels"""
        self.unevenly_sampled_channels: typing.List[UnevenlySampledChannel] = list(
            map(lambda uneven_channel: UnevenlySampledChannel(uneven_channel),
                repeated_to_array(redvox_packet.unevenly_sampled_channels)))
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

    def get_channel_types(self) -> typing.List[typing.List[int]]:
        """
        Returns:
            Returns a list of channel type enumerations. This is a list of lists, and allows us to easily view
            interleaved channels.
        """
        channel_types = []
        for evenly_sampled_channel in self.evenly_sampled_channels:
            channel_types.append(evenly_sampled_channel.channel_types)

        for unevenly_sampled_channel in self.unevenly_sampled_channels:
            channel_types.append(unevenly_sampled_channel.channel_types)

        return channel_types

    def get_channel_type_names(self) -> typing.List[typing.List[str]]:
        """
        Returns:
            Returns a list of channel type names. This is a list of lists, and allows us to easily view
            interleaved channels.
        """
        names = []
        for channel_types in self.get_channel_types():
            names.append(list(map(channel_type_name_from_enum, channel_types)))
        return names

    def get_channel(self, channel_type: int) -> typing.Union[api900.api900_pb2.EvenlySampledChannel,
                                                             api900.api900_pb2.UnevenlySampledChannel]:
        """Returns a channel from this packet according to the channel type.

        Args:
            channel_type: The channel type to search for.

        Returns:
            A high level channel wrapper or None.
        """
        if channel_type in self._channel_cache:
            return self._channel_cache[channel_type]
        else:
            return None

    def has_channel(self, channel_type: int) -> bool:
        """Returns True is this packet contains a channel with this type otherwise False.

        Args:
            channel_type: Channel type to search for.

        Returns:

        """
        return channel_type in self._channel_cache

    def print_meta(self):
        """Prints a string representation of the redvox packet without payload data displayed."""
        pass

    def __str__(self) -> str:
        """
        Returns:
            The canonical protobuf representation.
        """
        return str(self.redvox_packet)


def wrap(redvox_packet: api900.api900_pb2.RedvoxPacket) -> WrappedRedvoxPacket:
    """Shortcut for wrapping a protobuf packet with our higher level wrapper.

    Args:
        redvox_packet: The redvox packet to wrap.

    Returns:
        A wrapper redvox packet.
    """
    return WrappedRedvoxPacket(redvox_packet)
