"""
This module contains classes and methods for working with time synchronization sensors.
"""

import typing

import numpy

import redvox.api900.constants as constants
import redvox.api900.lib.api900_pb2 as api900_pb2
import redvox.api900.migrations as migrations
import redvox.api900.reader_utils as reader_utils
from redvox.api900.sensors.unevenly_sampled_channel import UnevenlySampledChannel


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
        return migrations.maybe_get_float(
            self._unevenly_sampled_channel.get_payload(api900_pb2.TIME_SYNCHRONIZATION))

    def set_payload_values(self, payload: typing.Union[typing.List[int], numpy.ndarray]) -> 'TimeSynchronizationSensor':
        """
        Sets the time synch channel's payload.
        :param payload: The payload.
        :return: An instance of the sensor.
        """
        self._unevenly_sampled_channel.set_payload(migrations.maybe_set_int(payload),
                                                   constants.PayloadType.INT64_PAYLOAD)
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
        return reader_utils.get_metadata_as_dict(self._unevenly_sampled_channel.metadata)

    def set_metadata_as_dict(self, metadata_dict: typing.Dict[str, str]) -> 'TimeSynchronizationSensor':
        """
        Sets the metadata.
        :param metadata_dict: Metadata to set.
        :return: An instance of self.
        """
        self.set_metadata(reader_utils.metadata_dict_to_list(metadata_dict))
        return self

    def __str__(self):
        return str(self._unevenly_sampled_channel)

    def __eq__(self, other) -> bool:
        return isinstance(other, TimeSynchronizationSensor) and len(self.diff(other)) == 0

    # pylint: disable=W0212
    def diff(self, other: 'TimeSynchronizationSensor') -> typing.List[str]:
        """
        Compares two time synchronization sensors for differences.
        :param other: The other sensor to compare with.
        :return: A list of differences or an empty list if there are none.
        """
        diffs = map(lambda tuple2: reader_utils.diff(tuple2[0], tuple2[1]), [
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
