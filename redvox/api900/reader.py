"""
This module provides functions and classes for working with api900 protobuf data.
"""

import struct
import typing

import google.protobuf.internal.containers as containers
import lz4.block
import numpy

import redvox.api900.api900_pb2


class ReaderException(Exception):
    """
    Custom exception type for API900 reader errors.
    """

    def __init__(self, msg: str = "ReaderException"):
        super(ReaderException, self).__init__(msg)


def calculate_uncompressed_size(buf: bytes) -> int:
    """
    Given a buffer, calculate the original size of the uncompressed packet by looking at the first four bytes.
    :param buf: Buffer where first 4 big endian bytes contain the size of the original uncompressed packet.
    :return: The total number of bytes in the original uncompressed packet.
    """
    return struct.unpack(">I", buf[:4])[0]


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


def read_buffer(buf: bytes, is_compressed: bool = True) -> redvox.api900.api900_pb2.RedvoxPacket:
    """
    Deserializes a serialized protobuf RedvoxPacket buffer.
    :param buf: Buffer to deserialize.
    :param is_compressed: Whether or not the buffer is compressed or decompressed.
    :return: Deserialized protobuf redvox packet.
    """
    buffer = lz4_decompress(buf) if is_compressed else buf
    redvox_packet = redvox.api900.api900_pb2.RedvoxPacket()
    redvox_packet.ParseFromString(buffer)
    return redvox_packet


def read_file(file: str, is_compressed: bool = None) -> redvox.api900.api900_pb2.RedvoxPacket:
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


def extract_payload(channel: typing.Union[redvox.api900.api900_pb2.EvenlySampledChannel,
                                          redvox.api900.api900_pb2.UnevenlySampledChannel]) -> numpy.ndarray:
    """
    Given an evenly on unevenly sampled channel, extracts the entire payload.

    This will return a payload of either ints or floats and is type agnostic when it comes to the underlying
    protobuf type.
    :param channel: The protobuf channel to extract the payload from.
    :return: A numpy array of either floats or ints.
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
    Finds the index of an item in a list and instead of throwing an exception returns -1 when the  item DNE.
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


def channel_type_name_from_enum(enum_constant: int) -> str:
    """
    Returns the name of a channel type given its enumeration constant.
    :param enum_constant: The constant to turn into a name.
    :return: The name of the channel.
    """
    return redvox.api900.api900_pb2.ChannelType.Name(enum_constant)


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
    else:
        return metadata[idx + 1]


def get_metadata_as_dict(metadata: typing.List[str]) -> typing.Dict[str, str]:
    """
    Since the metadata is inherently key-value, it may be useful to turn the metadata list into a python dictionary.
    :param metadata: The metadata list.
    :return: Metadata as a python dictionary.
    """
    if len(metadata) == 0:
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

    def __init__(self, channel: typing.Union[redvox.api900.api900_pb2.EvenlySampledChannel,
                                             redvox.api900.api900_pb2.UnevenlySampledChannel]):
        """
        Initializes this interleaved channel object.
        :param channel: Either a protobuf evenly or unevenly sampled channel.
        """
        self.protobuf_channel: typing.Union[redvox.api900.api900_pb2.EvenlySampledChannel,
                                            redvox.api900.api900_pb2.UnevenlySampledChannel] = channel
        """Reference to the original protobuf channel"""

        self.sensor_name: str = channel.sensor_name
        """Provided sensor name"""

        self.channel_types: typing.List[
            typing.Union[
                redvox.api900.api900_pb2.EvenlySampledChannel,
                redvox.api900.api900_pb2.UnevenlySampledChannel]] = repeated_to_list(channel.channel_types)
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

        self.channel_type_index: typing.Dict[redvox.api900.api900_pb2.ChannelType, int] = {self.channel_types[i]: i for
                                                                                           i in
                                                                                           range(
                                                                                                   len(
                                                                                                           self.channel_types))}
        """Contains a mapping of channel type to index in channel_types array"""

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

    def has_payload(self, channel_type: int) -> bool:
        """
        Returns if channel contains a non-empty specified payload.
        :param channel_type: The channel to check for a payload for.
        :return: Whether this channel contains the specified payload.
        """
        return self.has_channel(channel_type) and len(self.payload) > 0

    def get_payload(self, channel_type: int) -> numpy.ndarray:
        """
        Returns a deinterleaved payload of a given channel type or an empty array.
        :param channel_type: The channel type to extract/deinterleave from the payload.
        :return: A numpy array of floats or ints of a single channel type.
        """
        idx = self.channel_index(channel_type)
        if idx < 0:
            return empty_array()
        else:
            return deinterleave_array(self.payload, idx, len(self.channel_types))

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
        else:
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
        else:
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
        else:
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
        else:
            return self.value_medians[idx]

    def __str__(self) -> str:
        """
        Returns a string representation of this interleaved channel.
        :return: A string representation of this interleaved chanel.
        """
        return "sensor_name: {}\nchannel_types: {}\nlen(payload): {}".format(self.sensor_name,
                                                                             list(map(channel_type_name_from_enum,
                                                                                      self.channel_types)),
                                                                             len(self.payload))


class EvenlySampledChannel(InterleavedChannel):
    """
    An evenly sampled channel is an interleaved channel that also has a channel with an even sampling rate.
    """

    def __init__(self, channel: redvox.api900.api900_pb2.EvenlySampledChannel):
        """
        Initializes this evenly sampled channel.
        :param channel: A protobuf evenly sampled channel.
        """
        InterleavedChannel.__init__(self, channel)
        self.sample_rate_hz: float = channel.sample_rate_hz
        """The sample rate in hz of this evenly sampled channel"""

        self.first_sample_timestamp_epoch_microseconds_utc: int = channel.first_sample_timestamp_epoch_microseconds_utc
        """The timestamp of the first sample"""

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

    def __init__(self, channel: redvox.api900.api900_pb2.UnevenlySampledChannel):
        """
        Initializes this unevenly sampled channel.
        :param channel: A protobuf unevenly sampled channel.
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
        """
        Returns a string representation of this unevenly sampled channel.
        :return: A string representation of this unevenly sampled channel.
        """
        return "{}\nlen(timestamps_microseconds_utc): {}".format(super().__str__(),
                                                                 len(self.timestamps_microseconds_utc))


class WrappedRedvoxPacket:
    """
    This class provides convenience methods for accessing API 900 protobuf redvox packets.

    This packet contains a reference to the original packet which should be used to access all "top-level" fields. For
    accessing channels, this class can search for and return our high-level channel wrappers or can extract the payload
    directly.
    """

    def __init__(self, redvox_packet: redvox.api900.api900_pb2.RedvoxPacket):
        """
        Initializes this wrapped redvox packet.
        :param redvox_packet: A protobuf redvox packet.
        """
        self.redvox_packet: redvox.api900.api900_pb2.RedvoxPacket = redvox_packet
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

    def get_channel(self, channel_type: int) -> typing.Union[redvox.api900.api900_pb2.EvenlySampledChannel,
                                                             redvox.api900.api900_pb2.UnevenlySampledChannel]:
        """
        Returns a channel from this packet according to the channel type.
        :param channel_type: The channel type to search for.
        :return: A high level channel wrapper or None.
        """
        if channel_type in self._channel_cache:
            return self._channel_cache[channel_type]
        else:
            return None

    def has_channel(self, channel_type: int) -> bool:
        """
        Returns True is this packet contains a channel with this type otherwise False.
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
        has_channel_results = map(lambda channel_type: self.has_channel(channel_type), channel_types)
        for has_channel_result in has_channel_results:
            if not has_channel_result:
                return False
        return True

    # ---------- Microphone sensor methods
    def has_microphone_channel(self) -> bool:
        """
        Returns whether this wrapped packet contains a microphone channel.
        :return: True if this packet contains a microphone channel, False otherwise.
        """
        return self.has_channel(redvox.api900.api900_pb2.MICROPHONE)

    def get_microphone_channel(self) -> redvox.api900.api900_pb2.EvenlySampledChannel:
        """
        Returns the microphone evenly sampled channel.
        :raises ReaderException: If microphone channel DNE in this packet.
        :return: The microphone evenly sampled channel.
        """
        if self.has_microphone_channel():
            return self.get_channel(redvox.api900.api900_pb2.MICROPHONE)
        else:
            raise ReaderException("Redvox API 900 packet does not contain a microphone channel")

    def get_microphone_first_sample_timestamp_epoch_microseconds_utc(self) -> int:
        """
        Returns the timestamp of the first microphone sample as microseconds from the epoch UTC.
        :raises ReaderException: If microphone channel DNE in this packet.
        :return: The timestamp of the first microphone sample as microseconds from the epoch UTC.
        """
        return self.get_microphone_channel().first_sample_timestamp_epoch_microseconds_utc

    def get_microphone_sample_rate_hz(self) -> float:
        """Returns the sample rate in Hz of the microphone channel.
        :raises ReaderException: If microphone channel DNE in this packet.
        :return: The sample rate in Hz of the microphone channel.
        """
        return self.get_microphone_channel().sample_rate_hz

    def get_microphone_sensor_name(self) -> str:
        """Returns the microphone sensor name.
        :raises ReaderException: If microphone channel DNE in this packet.
        :return: The microphone sensor name.
        """
        return self.get_microphone_channel().sensor_name

    def get_microphone_payload(self) -> numpy.ndarray:
        """Returns the microphone payload as a numpy array of integers.
        :raises ReaderException: If microphone channel DNE in this packet.
        :return: The microphone payload as a numpy array of integers.
        """
        return self.get_microphone_channel().get_payload(redvox.api900.api900_pb2.MICROPHONE)

    def get_microphone_value_mean(self) -> float:
        """Returns the mean of the values in the microphone channel
        :raises ReaderException: If microphone channel DNE in this packet.
        :return:
        ."""
        return self.get_microphone_channel().get_value_mean(redvox.api900.api900_pb2.MICROPHONE)

    def get_microphone_value_median(self) -> float:
        """Returns the median of the values in the microphone channel.
        :raises ReaderException: If microphone channel DNE in this packet.
        :return:
        """
        return self.get_microphone_channel().get_value_median(redvox.api900.api900_pb2.MICROPHONE)

    def get_microphone_value_std(self) -> float:
        """Returns the standard deviation of the values in the microphone channel.
        :raises ReaderException: If microphone channel DNE in this packet.
        :return:
        """
        return self.get_microphone_channel().get_value_std(redvox.api900.api900_pb2.MICROPHONE)

    def get_microphone_metadata(self) -> typing.Dict[str, str]:
        """Returns metadata stored with the microphone channel as a key-value dictionary.
        :raises ReaderException: If microphone channel DNE in this packet.
        :return:
        """
        return get_metadata_as_dict(self.get_microphone_channel().metadata)

    # ---------- Barometer sensor methods
    def has_barometer_channel(self):
        """
        Returns whether this wrapped packet contains a barometer channel.
        :return: True if this packet contains a barometer channel, False otherwise.
        """
        return self.has_channel(redvox.api900.api900_pb2.BAROMETER)

    def get_barometer_channel(self) -> redvox.api900.api900_pb2.UnevenlySampledChannel:
        """
        Returns the barometer unevenly sampled channel.
        :raises ReaderException: If barometer channel DNE in this packet.
        :return: The barometer unevenly sampled channel.
        """
        if self.has_microphone_channel():
            return self.get_channel(redvox.api900.api900_pb2.BAROMETER)
        else:
            raise ReaderException("Redvox AIP 900 packet does not contain a barometer channel")

    def get_barometer_sensor_name(self) -> str:
        """Returns the barometer sensor name.
        :raises ReaderException: If barometer channel DNE in this packet.
        :return: The barometer sensor name.
        """
        return self.get_barometer_channel().sensor_name

    def get_barometer_payload_timestamps(self) -> numpy.ndarray:
        """Returns the timestamps associated with each barometer sample.
        :raises ReaderException: If barometer channel DNE in this packet.
        :return: The timestamps associated with each barometer sample as a numpy ndarray.
        """
        return self.get_barometer_channel().timestamps_microseconds_utc

    def get_barometer_payload_values(self) -> numpy.ndarray:
        """Returns the values associated with each barometer sample.
        :raises ReaderException: If barometer channel DNE in this packet.
        :return: The values associated with each barometer sample as a numpy ndarray.
        """
        return self.get_barometer_channel().get_payload(redvox.api900.api900_pb2.BAROMETER)

    def get_barometer_payload(self) -> numpy.ndarray:
        """Returns a 2D numpy array where each sub-array contains the sample timestamp and the barometer value.
        I.e.:
        [[timestamp_0, barometer_0],
         [timestamp_1, barometer_1],
         [timestamp_2, barometer_2],
         ...,
         [timestamp_n, barometer_n]]
        :raises ReaderException: If barometer channel DNE in this packet.
        :raises ReaderException: If the length of the timestamps and values are not the same.
        :return: The timestamps associated with each barometer sample as a numpy ndarray.
        """
        timestamps = self.get_barometer_payload_timestamps()
        values = self.get_barometer_payload_values()

        if len(timestamps) != len(values):
            raise ReaderException("Barometer channel len(timestamps) != len(values)")

        return numpy.column_stack((timestamps, values))

    def get_barometer_sample_interval_mean(self) -> float:
        """
        Returns the mean sample interval of the barometer channel.
        :return: The mean sample interval of the barometer channel.
        """
        return self.get_barometer_channel().sample_interval_mean

    def get_barometer_sample_interval_median(self) -> float:
        """
        Returns the median sample interval of the barometer channel.
        :return: The median sample interval of the barometer channel.
        """
        return self.get_barometer_channel().sample_interval_median

    def get_barometer_sample_interval_std(self) -> float:
        """
        Returns the standard deviation sample interval of the barometer channel.
        :return: The standard deviation sample interval of the barometer channel.
        """
        return self.get_barometer_channel().sample_interval_std

    def get_barometer_value_mean(self) -> float:
        """
        Returns the mean value of the barometer channel.
        :return: The mean value of the barometer channel.
        """
        return self.get_barometer_channel().get_value_mean(redvox.api900.api900_pb2.BAROMETER)

    def get_barometer_value_median(self) -> float:
        """
        Returns the median value of the barometer channel.
        :return: The median value of the barometer channel.
        """
        return self.get_barometer_channel().get_value_median(redvox.api900.api900_pb2.BAROMETER)

    def get_barometer_value_std(self) -> float:
        """
        Returns the standard deviation value of the barometer channel.
        :return: The standard deviation value of the barometer channel.
        """
        return self.get_barometer_channel().get_value_std(redvox.api900.api900_pb2.BAROMETER)

    # ---------- Location sensor methods
    def has_location_channel(self) -> bool:
        """
        Returns whether this packer contains a location channel.
        :return: True if this packet does contain a location channel, False otherwise.
        """
        return self.has_channels([redvox.api900.api900_pb2.LATITUDE,
                                  redvox.api900.api900_pb2.LONGITUDE,
                                  redvox.api900.api900_pb2.ALTITUDE,
                                  redvox.api900.api900_pb2.SPEED,
                                  redvox.api900.api900_pb2.ACCURACY])

    def get_location_channel(self) -> redvox.api900.api900_pb2.UnevenlySampledChannel:
        """
        Returns the location unevenly sampled channel.
        :raises ReaderException: If location channel DNE in this packet.
        :return: The location unevenly sampled channel.
        """
        if self.has_location_channel():
            return self.get_channel(redvox.api900.api900_pb2.LATITUDE)
        else:
            raise ReaderException("Redvox AIP 900 packet does not contain a location channel")

    def get_location_sensor_name(self) -> str:
        """Returns the location sensor name.
        :raises ReaderException: If location channel DNE in this packet.
        :return: The location sensor name.
        """
        return self.get_location_channel().sensor_name

    def get_location_payload_timestamps(self) -> numpy.ndarray:
        """Returns the timestamps associated with each location sample.
        :raises ReaderException: If location channel DNE in this packet.
        :return: The timestamps associated with each location sample as a numpy ndarray.
        """
        return self.get_location_channel().timestamps_microseconds_utc

    def get_location_payload_values(self) -> numpy.ndarray:
        """
        Returns the location values associated with each location sample.

        Each value is an array of values such that:

        [[latitude_0, longitude_0, altitude_0, speed_0, accuracy_0],
         [latitude_1, longitude_1, altitude_1, speed_1, accuracy_1],
         [latitude_2, longitude_2, altitude_2, speed_2, accuracy_2],
         ...,
         [latitude_n, longitude_n, altitude_n, speed_n, accuracy_n]]

        :raises ReaderException: If location channel DNE in this packet.
        :return: Location values.
        """
        return self.get_location_channel().get_multi_payload([
            redvox.api900.api900_pb2.LATITUDE,
            redvox.api900.api900_pb2.LONGITUDE,
            redvox.api900.api900_pb2.ALTITUDE,
            redvox.api900.api900_pb2.SPEED,
            redvox.api900.api900_pb2.ACCURACY
        ])

    def get_location_payload_values_latitude(self) -> numpy.ndarray:
        """Returns the latitude value associated with each location sample.
        :raises ReaderException: If location channel DNE in this packet.
        :return: The latitude value associated with each location sample.
        """
        return self.get_location_channel().get_payload(redvox.api900.api900_pb2.LATITUDE)

    def get_location_payload_values_longitude(self) -> numpy.ndarray:
        """Returns the longitude value associated with each location sample.
        :raises ReaderException: If location channel DNE in this packet.
        :return: The longitude value associated with each location sample.
        """
        return self.get_location_channel().get_payload(redvox.api900.api900_pb2.LONGITUDE)

    def get_location_payload_values_altitude(self) -> numpy.ndarray:
        """Returns the altitude value associated with each location sample.
        :raises ReaderException: If location channel DNE in this packet.
        :return: The altitude value associated with each location sample.
        """
        return self.get_location_channel().get_payload(redvox.api900.api900_pb2.ALTITUDE)

    def get_location_payload_values_speed(self) -> numpy.ndarray:
        """Returns the speed value associated with each location sample.
        :raises ReaderException: If location channel DNE in this packet.
        :return: The speed value associated with each location sample.
        """
        return self.get_location_channel().get_payload(redvox.api900.api900_pb2.SPEED)

    def get_location_payload_values_accuracy(self) -> numpy.ndarray:
        """Returns the accuracy value associated with each location sample.
        :raises ReaderException: If location channel DNE in this packet.
        :return: The accuracy value associated with each location sample.
        """
        return self.get_location_channel().get_payload(redvox.api900.api900_pb2.ACCURACY)

    def get_location_payload(self) -> numpy.ndarray:
        """
        Returns the payload of the location channel an array of arrays where each subarray consists of a timestamp for
        that sample followed by the payload values.

        The return format is described as follows:

        [[timestamp_0, latitude_0, longitude_0, altitude_0, speed_0, accuracy_0],
         [timestamp_1, latitude_1, longitude_1, altitude_1, speed_1, accuracy_1],
         [timestamp_2, latitude_2, longitude_2, altitude_2, speed_2, accuracy_2],
         ...,
         [timestamp_n, latitude_n, longitude_n, altitude_n, speed_n, accuracy_n]]

        :return: Location payload.
        """
        timestamps = self.get_location_payload_timestamps()
        values = self.get_location_payload_values()
        return numpy.column_stack((timestamps, values))

    # ---------- Time synchronization sensor methods
    def has_time_synchronization_channel(self):
        """
        Returns whether this wrapped packet contains a time synchronization channel.
        :return: True if this packet contains a time synchronization channel, False otherwise.
        """
        return self.has_channel(redvox.api900.api900_pb2.TIME_SYNCHRONIZATION)

    def get_time_synchronization_channel(self) -> redvox.api900.api900_pb2.UnevenlySampledChannel:
        """
        Returns the time_synchronization unevenly sampled channel.
        :raises ReaderException: If time_synchronization channel DNE in this packet.
        :return: The time_synchronization unevenly sampled channel.
        """
        if self.has_time_synchronization_channel():
            return self.get_channel(redvox.api900.api900_pb2.TIME_SYNCHRONIZATION)
        else:
            raise ReaderException("Redvox AIP 900 packet does not contain a barometer channel")

    def get_time_synchronization_payload(self) -> numpy.ndarray:
        """Returns the time synchronization exchange array.

        :raises ReaderException: If time synchronization channel DNE in this packet.
        :return: The time synchronization exchange array.
        """
        return self.get_time_synchronization_channel().get_payload(redvox.api900.api900_pb2.TIME_SYNCHRONIZATION)

    # ---------- Accelerometer sensor methods
    def has_accelerometer_channel(self) -> bool:
        """
        Returns whether or not this packet has an accelerometer channel.
        :return: True if this channel does have an accelerometer channel, False otherwise.
        """
        return self.has_channels([
            redvox.api900.api900_pb2.ACCELEROMETER_X,
            redvox.api900.api900_pb2.ACCELEROMETER_Y,
            redvox.api900.api900_pb2.ACCELEROMETER_Z])

    def get_accelerometer_channel(self) -> redvox.api900.api900_pb2.UnevenlySampledChannel:
        """
        Returns the accelerometer unevenly sampled channel.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The accelerometer unevenly sampled channel.
        """
        if self.has_accelerometer_channel():
            return self.get_channel(redvox.api900.api900_pb2.ACCELEROMETER_X)
        else:
            raise ReaderException("Redvox AIP 900 packet does not contain a accelerometer channel")

    def get_accelerometer_sensor_name(self) -> str:
        """Returns the accelerometer sensor name.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The accelerometer sensor name.
        """
        return self.get_accelerometer_channel().sensor_name

    def get_accelerometer_payload_timestamps(self) -> numpy.ndarray:
        """Returns the timestamps associated with each accelerometer sample.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The timestamps associated with each accelerometer sample as a numpy ndarray.
        """
        return self.get_accelerometer_channel().timestamps_microseconds_utc

    def get_accelerometer_payload_values(self) -> numpy.ndarray:
        """
        Returns the accelerometer values associated with each accelerometer sample.

        Each value is an array of values such that:

        [[accelerometer_x_0, accelerometer_y_0, accelerometer_z_0],
         [accelerometer_x_1, accelerometer_y_1, accelerometer_z_1],
         [accelerometer_x_2, accelerometer_y_2, accelerometer_z_2],
         ...,
         [accelerometer_x_n, accelerometer_y_n, accelerometer_z_n]]

        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: Accelerometer values.
        """
        return self.get_location_channel().get_multi_payload([
            redvox.api900.api900_pb2.ACCELEROMETER_X,
            redvox.api900.api900_pb2.ACCELEROMETER_Y,
            redvox.api900.api900_pb2.ACCELEROMETER_Z
        ])

    def get_accelerometer_payload_values_x(self) -> numpy.ndarray:
        """Returns the accelerometer_x value associated with each accelerometer sample.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The accelerometer value associated with each location sample.
        """
        return self.get_location_channel().get_payload(redvox.api900.api900_pb2.ACCELEROMETER_X)

    def get_accelerometer_payload_values_y(self) -> numpy.ndarray:
        """Returns the accelerometer_y value associated with each accelerometer sample.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The accelerometer value associated with each location sample.
        """
        return self.get_location_channel().get_payload(redvox.api900.api900_pb2.ACCELEROMETER_Y)

    def get_accelerometer_payload_values_z(self) -> numpy.ndarray:
        """Returns the accelerometer_z value associated with each accelerometer sample.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The accelerometer value associated with each location sample.
        """
        return self.get_location_channel().get_payload(redvox.api900.api900_pb2.ACCELEROMETER_Z)

    def get_accelerometer_payload(self) -> numpy.ndarray:
        """
        Returns the payload of the accelerometer channel an array of arrays where each subarray consists of a timestamp
        for that sample followed by the payload values.

        The return format is described as follows:

        [[timestamp_0, accelerometer_x_0, accelerometer_y_0, accelerometer_z_0],
         [timestamp_1, accelerometer_x_1, accelerometer_y_1, accelerometer_z_1],
         [timestamp_2, accelerometer_x_2, accelerometer_y_2, accelerometer_z_2],
         ...,
         [timestamp_n, accelerometer_x_n, accelerometer_y_n, accelerometer_z_n]]

        :return: Accelerometer payload.
        """
        timestamps = self.get_accelerometer_payload_timestamps()
        values = self.get_accelerometer_payload_values()
        return numpy.column_stack((timestamps, values))

    def get_accelerometer_sample_interval_mean(self) -> float:
        """Returns the mean sample interval for the accelerometer channel.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The mean sample interval for the accelerometer channel.
        """
        return self.get_accelerometer_channel().sample_interval_mean

    def get_accelerometer_sample_interval_median(self) -> float:
        """Returns the median sample interval for the accelerometer channel.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The median sample interval for the accelerometer channel.
        """
        return self.get_accelerometer_channel().sample_interval_median

    def get_accelerometer_sample_interval_std(self) -> float:
        """Returns the standard deviation sample interval for the accelerometer channel.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The standard deviation sample interval for the accelerometer channel.
        """
        return self.get_accelerometer_channel().sample_interval_std

    def get_accelerometer_x_value_mean(self):
        """Returns the mean value for the X axis in the accelerometer channel.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The mean value for the accelerometer x-axis channel.
        """
        return self.get_accelerometer_channel().get_value_mean(redvox.api900.api900_pb2.ACCELEROMETER_X)

    def get_accelerometer_y_value_mean(self):
        """Returns the mean value for the Y axis in the accelerometer channel.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The mean value for the accelerometer y-axis channel.
        """
        return self.get_accelerometer_channel().get_value_mean(redvox.api900.api900_pb2.ACCELEROMETER_Y)

    def get_accelerometer_z_value_mean(self):
        """Returns the mean value for the Z axis in the accelerometer channel.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The mean value for the accelerometer z-axis channel.
        """
        return self.get_accelerometer_channel().get_value_mean(redvox.api900.api900_pb2.ACCELEROMETER_Z)

    def get_accelerometer_x_value_median(self):
        """Returns the median value for the X axis in the accelerometer channel.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The median value for the accelerometer x-axis channel.
        """
        return self.get_accelerometer_channel().get_value_median(redvox.api900.api900_pb2.ACCELEROMETER_X)

    def get_accelerometer_y_value_median(self):
        """Returns the median value for the Y axis in the accelerometer channel.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The median value for the accelerometer y-axis channel.
        """
        return self.get_accelerometer_channel().get_value_median(redvox.api900.api900_pb2.ACCELEROMETER_Y)

    def get_accelerometer_z_value_median(self):
        """Returns the median value for the Z axis in the accelerometer channel.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The median value for the accelerometer z-axis channel.
        """
        return self.get_accelerometer_channel().get_value_median(redvox.api900.api900_pb2.ACCELEROMETER_Z)

    def get_accelerometer_x_value_std(self):
        """Returns the std value for the X axis in the accelerometer channel.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The std value for the accelerometer x-axis channel.
        """
        return self.get_accelerometer_channel().get_value_std(redvox.api900.api900_pb2.ACCELEROMETER_X)

    def get_accelerometer_y_value_std(self):
        """Returns the std value for the Y axis in the accelerometer channel.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The median value for the accelerometer y-axis channel.
        """
        return self.get_accelerometer_channel().get_value_std(redvox.api900.api900_pb2.ACCELEROMETER_Y)

    def get_accelerometer_z_value_std(self):
        """Returns the std value for the Z axis in the accelerometer channel.
        :raises ReaderException: If accelerometer channel DNE in this packet.
        :return: The std value for the accelerometer z-axis channel.
        """
        return self.get_accelerometer_channel().get_value_std(redvox.api900.api900_pb2.ACCELEROMETER_Z)

    # ---------- Magnetometer sensor methods
    def has_magnetometer_channels(self) -> bool:
        return self.has_channels([
            redvox.api900.api900_pb2.MAGNETOMETER_X,
            redvox.api900.api900_pb2.MAGNETOMETER_Y,
            redvox.api900.api900_pb2.MAGNETOMETER_Z])

    # ---------- Gyroscope sensor methods
    def has_gyroscope_channels(self) -> bool:
        return self.has_channels([
            redvox.api900.api900_pb2.GYROSCOPE_X,
            redvox.api900.api900_pb2.GYROSCOPE_Y,
            redvox.api900.api900_pb2.GYROSCOPE_Z])

    # ---------- Light sensor methods
    def has_light_channel(self) -> bool:
        return self.has_channel(redvox.api900.api900_pb2.LIGHT)

    def __str__(self) -> str:
        """
        Returns:
            The canonical protobuf representation.
        """
        return str(self.redvox_packet)


def wrap(redvox_packet: redvox.api900.api900_pb2.RedvoxPacket) -> WrappedRedvoxPacket:
    """Shortcut for wrapping a protobuf packet with our higher level wrapper.

    Args:
        redvox_packet: The redvox packet to wrap.

    Returns:
        A wrapper redvox packet.
    """
    return WrappedRedvoxPacket(redvox_packet)
