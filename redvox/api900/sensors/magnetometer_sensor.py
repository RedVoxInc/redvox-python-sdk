"""
This module contains classes and methods for working with magnetometer sensors.
"""

import typing

import numpy

import redvox.api900.constants as constants
import redvox.api900.lib.api900_pb2 as api900_pb2
from redvox.api900.sensors.unevenly_sampled_channel import UnevenlySampledChannel
from redvox.api900.sensors.xyz_unevenly_sampled_sensor import XyzUnevenlySampledSensor


class MagnetometerSensor(XyzUnevenlySampledSensor):
    """
    Initializes this class.
    :param unevenly_sampled_channel: An instance of an UnevenlySampledChanel which contains magnetometer
    X, Y, and Z payload components.
    """

    def __init__(self, unevenly_sampled_channel: typing.Optional[UnevenlySampledChannel] = None):
        super().__init__(unevenly_sampled_channel,
                         api900_pb2.MAGNETOMETER_X,
                         api900_pb2.MAGNETOMETER_Y,
                         api900_pb2.MAGNETOMETER_Z)

    def _payload_values(self) -> numpy.ndarray:
        """
        returns the sensor payload as a numpy ndarray
        :return: magnetometer payload as a numpy ndarray
        """
        return self._unevenly_sampled_channel.get_multi_payload([
            api900_pb2.MAGNETOMETER_X,
            api900_pb2.MAGNETOMETER_Y,
            api900_pb2.MAGNETOMETER_Z
        ])

    def set_payload_values(self,
                           x_values: typing.Union[typing.List[float], numpy.ndarray],
                           y_values: typing.Union[typing.List[float], numpy.ndarray],
                           z_values: typing.Union[typing.List[float], numpy.ndarray]) -> 'MagnetometerSensor':
        """
        Sets this channel's payload with the provided equal length x, y, and z payload values.
        :param x_values: The x values.
        :param y_values: The y values.
        :param z_values: The z values.
        :return: An instance of the sensor.
        """
        self._set_payload_values(x_values, y_values, z_values, constants.PayloadType.FLOAT64_PAYLOAD)
        return self
