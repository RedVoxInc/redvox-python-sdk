"""
This module contains classes and methods for working with microphone sensors.
"""

import typing

import numpy

import redvox.api900.constants as constants
import redvox.api900.exceptions as exceptions
import redvox.api900.lib.api900_pb2 as api900_pb2
from redvox.api900.sensors.evenly_sampled_channel import EvenlySampledChannel
from redvox.api900.sensors.evenly_sampled_sensor import EvenlySampledSensor


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
