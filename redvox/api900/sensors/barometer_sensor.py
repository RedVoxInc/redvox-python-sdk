"""
This module contains classes and methods for working with barometer sensors.
"""

import typing

import numpy

import redvox.api900.constants as constants
import redvox.api900.lib.api900_pb2 as api900_pb2
from redvox.api900.sensors.unevenly_sampled_channel import UnevenlySampledChannel
from redvox.api900.sensors.unevenly_sampled_sensor import UnevenlySampledSensor


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
