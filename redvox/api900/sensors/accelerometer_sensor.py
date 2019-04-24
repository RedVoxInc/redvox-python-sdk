"""
This module contains classes and methods for working with accelerometer sensors.
"""

import typing

import numpy

import redvox.api900.constants as constants
import redvox.api900.lib.api900_pb2 as api900_pb2
from redvox.api900.sensors.unevenly_sampled_channel import UnevenlySampledChannel
from redvox.api900.sensors.xyz_unevenly_sampled_sensor import XyzUnevenlySampledSensor


class AccelerometerSensor(XyzUnevenlySampledSensor):
    """High-level wrapper around accelerometer channels."""

    def __init__(self, unevenly_sampled_channel: typing.Optional[UnevenlySampledChannel] = None):
        """
        Initializes this class.
        :param unevenly_sampled_channel: An instance of an UnevenlySampledChanel which contains accelerometer
        X, Y, and Z payload components.
        """
        super().__init__(unevenly_sampled_channel,
                         api900_pb2.ACCELEROMETER_X,
                         api900_pb2.ACCELEROMETER_Y,
                         api900_pb2.ACCELEROMETER_Z)

    def _payload_values(self) -> numpy.ndarray:
        """
        returns the sensor payload as a numpy ndarray
        :return: accelerometer payload as a numpy ndarray
        """
        return self._unevenly_sampled_channel.get_multi_payload([
            api900_pb2.ACCELEROMETER_X,
            api900_pb2.ACCELEROMETER_Y,
            api900_pb2.ACCELEROMETER_Z
        ])

    def set_payload_values(self,
                           x_values: typing.Union[typing.List[float], numpy.ndarray],
                           y_values: typing.Union[typing.List[float], numpy.ndarray],
                           z_values: typing.Union[typing.List[float], numpy.ndarray]) -> 'AccelerometerSensor':
        """
        Sets this channel's payload with the provided equal length x, y, and z payload values.
        :param x_values: The x values.
        :param y_values: The y values.
        :param z_values: The z values.
        :return: An instance of the sensor.
        """
        self._set_payload_values(x_values, y_values, z_values, constants.PayloadType.FLOAT64_PAYLOAD)
        return self
