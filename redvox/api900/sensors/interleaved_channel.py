"""
This module contains classes and methods for working with interleaved channels.
"""

import typing

import numpy

import redvox.api900.constants as constants
import redvox.api900.exceptions as exceptions
import redvox.api900.lib.api900_pb2 as api900_pb2
import redvox.api900.migrations as migrations
import redvox.api900.reader_utils as reader_utils
import redvox.api900.stat_utils as stat_utils


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
                    api900_pb2.UnevenlySampledChannel]] = reader_utils.repeated_to_list(channel.channel_types)
            """List of channel type constant enumerations"""

            self.payload: numpy.ndarray = reader_utils.extract_payload(channel)
            """This channels payload as a numpy array of either floats or ints"""

            self.metadata: typing.List[str] = reader_utils.repeated_to_list(channel.metadata)
            """This channels list of metadata"""

            self.value_means: numpy.ndarray = reader_utils.repeated_to_array(channel.value_means)
            """Interleaved array of mean values"""

            self.value_stds: numpy.ndarray = reader_utils.repeated_to_array(channel.value_stds)
            """Interleaved array of standard deviations of values"""

            self.value_medians: numpy.ndarray = reader_utils.repeated_to_array(channel.value_medians)
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
        self.channel_types = reader_utils.repeated_to_list(self.protobuf_channel.channel_types)
        self.channel_type_index = {self.channel_types[i]: i for i in range(len(self.channel_types))}

    def get_channel_type_names(self) -> typing.List[str]:
        """
        Returns the list of channel_types as a list of names instead of enumeration constants.
        :return: The list of channel_types as a list of names instead of enumeration constants.
        """
        return list(map(reader_utils.channel_type_name_from_enum, self.channel_types))

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
        self.channel_types = reader_utils.repeated_to_list(channel.channel_types)
        self.payload = reader_utils.extract_payload(channel)
        self.metadata = reader_utils.repeated_to_list(channel.metadata)
        self.value_means = reader_utils.repeated_to_array(channel.value_means)
        self.value_stds = reader_utils.repeated_to_array(channel.value_stds)
        self.value_medians = reader_utils.repeated_to_array(channel.value_medians)
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
        payload_values = reader_utils.to_array(payload_values)

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
            self.payload = reader_utils.extract_payload(self.protobuf_channel)

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
        interleaved = reader_utils.interleave_arrays(list(map(reader_utils.to_array, payloads)))
        self.set_payload(interleaved, pl_type, should_compute_stats)

    def get_payload(self, channel_type: int) -> numpy.ndarray:
        """
        Returns a deinterleaved payload of a given channel type or an empty array.
        :param channel_type: The channel type to extract/deinterleave from the payload.
        :return: A numpy array of floats or ints of a single channel type.
        """
        idx = self.channel_index(channel_type)
        if idx < 0:
            return reader_utils.empty_array()
        try:
            payload: numpy.ndarray = reader_utils.deinterleave_array(self.payload, idx, len(self.channel_types))
            return migrations.maybe_get_float(payload)
        except exceptions.ReaderException:
            return reader_utils.empty_array()

    def get_payload_type(self) -> str:
        """
        Returns the internal protobuf payload type.
        :return: The internal protobuf payload type.
        """
        return reader_utils.payload_type(self.protobuf_channel)

    def get_multi_payload(self, channel_types: typing.List[int]) -> numpy.ndarray:
        """
        Returns an interleaved payload with the given channel types.
        :param channel_types: Channel types to interleave into a single payload.
        :return: A numpy array of an interleaved payload.
        """
        channel_types_len = len(channel_types)
        if channel_types_len == 0:
            return reader_utils.empty_array()
        elif channel_types_len == 1:
            return self.get_payload(channel_types[0])

        payloads = list(map(self.get_payload, channel_types))
        return reader_utils.interleave_arrays(payloads)

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
            std, mean, median = stat_utils.calc_utils(reader_utils.deinterleave_array(channel, i, step))
            self.protobuf_channel.value_means.append(mean)
            self.protobuf_channel.value_stds.append(std)
            self.protobuf_channel.value_medians.append(median)
        self.value_stds = reader_utils.repeated_to_array(self.protobuf_channel.value_stds)
        self.value_means = reader_utils.repeated_to_array(self.protobuf_channel.value_means)
        self.value_medians = reader_utils.repeated_to_array(self.protobuf_channel.value_medians)

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
        self.metadata = reader_utils.repeated_to_list(self.protobuf_channel.metadata)

    def metadata_as_dict(self) -> typing.Dict[str, str]:
        """
        Returns any metadata as a dictionary of key-pair values.
        :return: Any metadata as a dictionary of key-pair values.
        """
        return reader_utils.get_metadata_as_dict(self.metadata)

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
                                             reader_utils.channel_type_name_from_enum,
                                             self.channel_types)),
                                         len(self.payload),
                                         reader_utils.payload_type(
                                             self.protobuf_channel))
