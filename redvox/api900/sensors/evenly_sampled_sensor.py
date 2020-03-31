"""
This module contains classes and methods for working with evenly sampled sensors.
"""

import typing

import redvox.api900.migrations as migrations
from redvox.api900.sensors.evenly_sampled_channel import EvenlySampledChannel
import redvox.api900.reader_utils as reader_utils


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
        return list(map(reader_utils.channel_type_name_from_enum, self._evenly_sampled_channel.channel_types))

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
        return migrations.maybe_get_float(self._evenly_sampled_channel.first_sample_timestamp_epoch_microseconds_utc)

    def set_first_sample_timestamp_epoch_microseconds_utc(self, time: int) -> 'EvenlySampledSensor':
        """
        sets the sample timestamp in microseconds since utc
        :param time: microseconds since utc
        :return: An instance of the sensor.
        """
        self._evenly_sampled_channel.set_first_sample_timestamp_epoch_microseconds_utc(migrations.maybe_set_int(time))
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
        return reader_utils.get_metadata_as_dict(self._evenly_sampled_channel.metadata)

    def set_metadata_as_dict(self, metadata_dict: typing.Dict[str, str]) -> 'EvenlySampledSensor':
        """
        Sets the metadata given a dictionary of key-pair values.
        :param metadata_dict: Dictionary to use to set metadata.
        :return: An instance of the sensor.
        """
        self.set_metadata(reader_utils.metadata_dict_to_list(metadata_dict))
        return self

    def __str__(self):
        return str(self._evenly_sampled_channel)

    def __eq__(self, other):
        return isinstance(other, EvenlySampledSensor) and len(self.diff(other)) == 0

    # pylint: disable=W0212
    def diff(self, other: 'EvenlySampledSensor') -> typing.List[str]:
        """
        Compares two evenly sampled sensors for differences.
        :param other: The other sensor to compare with.
        :return: A list of differences or an empty list if there are none.
        """
        diffs = map(lambda tuple2: reader_utils.diff(tuple2[0], tuple2[1]), [
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
