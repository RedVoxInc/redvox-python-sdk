"""
This module contains classes and methods for working with xyz unevenly sensors.
"""

import typing

import numpy

import redvox.api900.constants as constants
from redvox.api900.sensors.unevenly_sampled_channel import UnevenlySampledChannel
from redvox.api900.sensors.unevenly_sampled_sensor import UnevenlySampledSensor


class XyzUnevenlySampledSensor(UnevenlySampledSensor):
    """
    This class subclasses the UnevenlySampledSensor class and provides methods for working with channels that provide
    data in the X, Y, and Z dimensions.
    """

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel, x_type: int, y_type: int, z_type: int):
        """
        Initializes this class.
        :param unevenly_sampled_channel: An instance of an UnevenlySampledChannel.
        :param x_type: The X channel type enum.
        :param y_type: The Y channel type enum.
        :param z_type: The Z channel type enum.
        """
        super().__init__(unevenly_sampled_channel)
        self._unevenly_sampled_channel.set_channel_types([x_type, y_type, z_type])
        self._x_type = x_type
        self._y_type = y_type
        self._z_type = z_type

    def _payload_values(self) -> numpy.ndarray:
        """
        Returns this channel's payload as an interleaved payload of the form
        [[x_0, y_0, z_0], [x_1, y_1, z_1], ..., [x_n, y_n, z_n]].
        :return: This channel's payload as an interleaved payload.
        """
        return self._unevenly_sampled_channel.get_multi_payload([
            self._x_type,
            self._y_type,
            self._z_type
        ])

    def _set_payload_values(self,
                            x_values: typing.Union[typing.List, numpy.ndarray],
                            y_values: typing.Union[typing.List, numpy.ndarray],
                            z_values: typing.Union[typing.List, numpy.ndarray],
                            pl_type: constants.PayloadType) -> 'XyzUnevenlySampledSensor':
        """
        Sets the interleaved payload of this XYZ channel given the X, Y, Z values and payload type.
        :param x_values: The x values.
        :param y_values: The y values.
        :param z_values: The z values.
        :param pl_type: Payload type.
        :return: An instance of the sensor.
        """
        self._unevenly_sampled_channel.set_interleaved_payload([
            x_values,
            y_values,
            z_values
        ],
                                                               pl_type)
        return self

    def payload_values_x(self) -> numpy.ndarray:
        """
        Returns the x-component of this channel's payload.
        :return: The x-component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(self._x_type)

    def payload_values_y(self) -> numpy.ndarray:
        """
        Returns the y-component of this channel's payload.
        :return: The y-component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(self._y_type)

    def payload_values_z(self) -> numpy.ndarray:
        """
        Returns the z-component of this channel's payload.
        :return: The z-component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(self._z_type)

    def payload_values_x_mean(self) -> float:
        """
        Returns the x-component mean of this channel's payload.
        :return: The x-component mean of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(self._x_type)

    def payload_values_y_mean(self) -> float:
        """
        Returns the y-component mean of this channel's payload.
        :return: The y-component mean of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(self._y_type)

    def payload_values_z_mean(self) -> float:
        """
        Returns the z-component mean of this channel's payload.
        :return: The z-component mean of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(self._z_type)

    def payload_values_x_median(self) -> float:
        """
        Returns the x-component median of this channel's payload.
        :return: The x-component median of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(self._x_type)

    def payload_values_y_median(self) -> float:
        """
        Returns the y-component median of this channel's payload.
        :return: The y-component median of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(self._y_type)

    def payload_values_z_median(self) -> float:
        """
        Returns the z-component median of this channel's payload.
        :return: The z-component median of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(self._z_type)

    def payload_values_x_std(self) -> float:
        """
        Returns the x-component standard deviation of this channel's payload.
        :return: The x-component standard deviation of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(self._x_type)

    def payload_values_y_std(self) -> float:
        """
        Returns the y-component standard deviation of this channel's payload.
        :return: The y-component standard deviation of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(self._y_type)

    def payload_values_z_std(self) -> float:
        """
        Returns the z-component standard deviation of this channel's payload.
        :return: The z-component standard deviation of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(self._z_type)
