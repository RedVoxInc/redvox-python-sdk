"""
This module contains classes and methods for working with unevenly sampled sensors.
"""

import typing

import numpy

import redvox.api900.migrations as migrations
from redvox.api900.sensors.unevenly_sampled_channel import UnevenlySampledChannel
import redvox.api900.reader_utils as reader_utils


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
        return list(map(reader_utils.channel_type_name_from_enum, self._unevenly_sampled_channel.channel_types))

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
        return migrations.maybe_get_float(self._unevenly_sampled_channel.timestamps_microseconds_utc)

    def set_timestamps_microseconds_utc(self, timestamps: typing.Union[
            numpy.ndarray, typing.List[int]]) -> 'UnevenlySampledSensor':
        """
        set the time stamps
        :param timestamps: a list of ascending timestamps that associate with each sample value
        :return: An instance of the sensor.
        """
        timestamps = migrations.maybe_set_int(reader_utils.to_array(timestamps))

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
        return reader_utils.get_metadata_as_dict(self._unevenly_sampled_channel.metadata)

    def set_metadata_as_dict(self, metadata_dict: typing.Dict[str, str]) -> 'UnevenlySampledSensor':
        """
        Sets the metadata using a dictionary.
        :param metadata_dict: Metadata to set.
        :return: An instance of itself.
        """
        self.set_metadata(reader_utils.metadata_dict_to_list(metadata_dict))
        return self

    def __str__(self) -> str:
        return str(self._unevenly_sampled_channel)

    def __eq__(self, other) -> bool:
        return isinstance(other, UnevenlySampledSensor) and len(self.diff(other)) == 0

    # pylint: disable=W0212
    def diff(self, other: 'UnevenlySampledSensor') -> typing.List[str]:
        """
        Compares two unevenly sampled sensors for differences.
        :param other: The other sensor to compare with.
        :return: A list odifferences or an empty list if there are none.
        """
        diffs = map(lambda tuple2: reader_utils.diff(tuple2[0], tuple2[1]), [
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
