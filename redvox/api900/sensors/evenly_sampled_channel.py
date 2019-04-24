"""
This module contains classes and methods for working with evenly sampled channels.
"""

import typing

import redvox.api900.lib.api900_pb2 as api900_pb2
import redvox.api900.reader_utils as reader_utils
import redvox.api900.sensors.interleaved_channel as interleaved_channel


class EvenlySampledChannel(interleaved_channel.InterleavedChannel):
    """
    An evenly sampled channel is an interleaved channel that also has a channel with an even sampling rate.
    """

    def __init__(self, channel: typing.Optional[api900_pb2.EvenlySampledChannel] = None):
        """
        Initializes this evenly sampled channel.
        :param channel: A protobuf evenly sampled channel.
        """
        if channel is None:
            channel = reader_utils.empty_evenly_sampled_channel()

        interleaved_channel.InterleavedChannel.__init__(self, channel)
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

    # pylint: disable=C0103
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
