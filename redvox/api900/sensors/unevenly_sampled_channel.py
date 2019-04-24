"""
This module contains classes and methods for working with unevenly sampled channels.
"""

import typing

import numpy

import redvox.api900.lib.api900_pb2 as api900_pb2
import redvox.api900.reader_utils as reader_utils
import redvox.api900.sensors.interleaved_channel as interleaved_channel
import redvox.api900.stat_utils as stat_utils


class UnevenlySampledChannel(interleaved_channel.InterleavedChannel):
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
            channel = reader_utils.empty_unevenly_sampled_channel()

        interleaved_channel.InterleavedChannel.__init__(self, channel)
        self.timestamps_microseconds_utc: numpy.ndarray = reader_utils.repeated_to_array(
            channel.timestamps_microseconds_utc)
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
        self.timestamps_microseconds_utc = reader_utils.repeated_to_array(channel.timestamps_microseconds_utc)
        self.sample_interval_std, self.sample_interval_mean, self.sample_interval_median = \
            stat_utils.calc_utils_timeseries(self.timestamps_microseconds_utc)

    def set_timestamps_microseconds_utc(self, timestamps: typing.Union[typing.List[int], numpy.ndarray]):
        """
        set the timestamps in microseconds from utc
        :param timestamps: array of timestamps
        """
        timestamps = reader_utils.to_array(timestamps)
        self.timestamps_microseconds_utc = timestamps
        self.protobuf_channel.timestamps_microseconds_utc[:] = timestamps

        if len(timestamps) > 0:
            self.sample_interval_std, self.sample_interval_mean, self.sample_interval_median = \
                stat_utils.calc_utils_timeseries(timestamps)
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
