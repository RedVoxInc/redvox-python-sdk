"""
This module contains classes and methods for working with location sensors.
"""

import typing

import numpy

import redvox.api900.constants as constants
import redvox.api900.lib.api900_pb2 as api900_pb2
from redvox.api900.sensors.unevenly_sampled_channel import UnevenlySampledChannel
from redvox.api900.sensors.unevenly_sampled_sensor import UnevenlySampledSensor


# pylint: disable=R0904
class LocationSensor(UnevenlySampledSensor):
    """
    High-level wrapper around location channels.
    """

    def __init__(self, unevenly_sampled_channel: typing.Optional[UnevenlySampledChannel] = None):
        """
        Initialize this channel
        :param unevenly_sampled_channel: Instance of UnevenlySampledChannel containing location data
        """
        super().__init__(unevenly_sampled_channel)
        self._unevenly_sampled_channel.set_channel_types([
            api900_pb2.LATITUDE,
            api900_pb2.LONGITUDE,
            api900_pb2.ALTITUDE,
            api900_pb2.SPEED,
            api900_pb2.ACCURACY
        ])

    def _payload_values(self):
        """
        Return the location payload as an interleaved payload with the following format:
        [[latitude_0, longitude_0, altitude_0, speed_0, accuracy_0],
         [latitude_1, longitude_1, altitude_1, speed_1, accuracy_1],
         ...,
         [latitude_n, longitude_n, altitude_n, speed_n, accuracy_n],]
        :return: array containing interleaved values of the 5 channels
        """
        return self._unevenly_sampled_channel.get_multi_payload([
            api900_pb2.LATITUDE,
            api900_pb2.LONGITUDE,
            api900_pb2.ALTITUDE,
            api900_pb2.SPEED,
            api900_pb2.ACCURACY
        ])

    # pylint: disable=R0913
    def set_payload_values(self,
                           latitude_payload: typing.Union[typing.List[float], numpy.ndarray],
                           longitude_payload: typing.Union[typing.List[float], numpy.ndarray],
                           altitude_payload: typing.Union[typing.List[float], numpy.ndarray],
                           speed_payload: typing.Union[typing.List[float], numpy.ndarray],
                           accuracy_payload: typing.Union[typing.List[float], numpy.ndarray]) -> 'LocationSensor':
        """
        Sets the location sensor's payload. Note that if one of the below channels don't exist, you must still provide
        a zero-filled payload that is the same length as all other paylods.
        :param latitude_payload: The latitude payload.
        :param longitude_payload: The longitude payload.
        :param altitude_payload: The altitude payload.
        :param speed_payload: The speed payload
        :param accuracy_payload: The accuracy payload.
        :return: An instance of the sensor.
        """
        self._unevenly_sampled_channel.set_interleaved_payload([latitude_payload,
                                                                longitude_payload,
                                                                altitude_payload,
                                                                speed_payload,
                                                                accuracy_payload],
                                                               constants.PayloadType.FLOAT64_PAYLOAD)
        return self

    def payload_values_latitude(self):
        """
        Returns the latitude component of this channel's payload.
        :return: The latitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.LATITUDE)

    def payload_values_longitude(self):
        """
        Returns the longitude component of this channel's payload.
        :return: The longitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.LONGITUDE)

    def payload_values_altitude(self):
        """
        Returns the altitude component of this channel's payload.
        :return: The altitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.ALTITUDE)

    def payload_values_speed(self):
        """
        Returns the speed component of this channel's payload.
        :return: The speed component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.SPEED)

    def payload_values_accuracy(self):
        """
        Returns the accuracy component of this channel's payload.
        :return: The accuracy component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.ACCURACY)

    def payload_values_latitude_mean(self) -> float:
        """
        Returns the mean latitude component of this channel's payload.
        :return: The mean latitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(api900_pb2.LATITUDE)

    def payload_values_longitude_mean(self) -> float:
        """
        Returns the mean longitude component of this channel's payload.
        :return: The mean longitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(api900_pb2.LONGITUDE)

    def payload_values_altitude_mean(self) -> float:
        """
        Returns the mean altitude component of this channel's payload.
        :return: The mean altitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(api900_pb2.ALTITUDE)

    def payload_values_speed_mean(self) -> float:
        """
        Returns the mean speed component of this channel's payload.
        :return: The mean speed component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(api900_pb2.SPEED)

    def payload_values_accuracy_mean(self) -> float:
        """
        Returns the mean accuracy component of this channel's payload.
        :return: The mean accuracy component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_mean(api900_pb2.ACCURACY)

    def payload_values_latitude_median(self) -> float:
        """
        Returns the median latitude component of this channel's payload.
        :return: The median latitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(api900_pb2.LATITUDE)

    def payload_values_longitude_median(self) -> float:
        """
        Returns the median longitude component of this channel's payload.
        :return: The median longitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(api900_pb2.LONGITUDE)

    def payload_values_altitude_median(self) -> float:
        """
        Returns the median altitude component of this channel's payload.
        :return: The median altitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(api900_pb2.ALTITUDE)

    def payload_values_speed_median(self) -> float:
        """
        Returns the median speed component of this channel's payload.
        :return: The median speed component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(api900_pb2.SPEED)

    def payload_values_accuracy_median(self) -> float:
        """
        Returns the median accuracy component of this channel's payload.
        :return: The median accuracy component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_median(api900_pb2.ACCURACY)

    def payload_values_latitude_std(self) -> float:
        """
        Returns the standard deviation latitude component of this channel's payload.
        :return: The standard deviation latitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(api900_pb2.LATITUDE)

    def payload_values_longitude_std(self) -> float:
        """
        Returns the standard deviation longitude component of this channel's payload.
        :return: The standard deviation longitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(api900_pb2.LONGITUDE)

    def payload_values_altitude_std(self) -> float:
        """
        Returns the standard deviation altitude component of this channel's payload.
        :return: The standard deviation altitude component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(api900_pb2.ALTITUDE)

    def payload_values_speed_std(self) -> float:
        """
        Returns the standard deviation speed component of this channel's payload.
        :return: The standard deviation speed component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(api900_pb2.SPEED)

    def payload_values_accuracy_std(self) -> float:
        """
        Returns the standard deviation accuracy component of this channel's payload.
        :return: The standard deviation accuracy component of this channel's payload.
        """
        return self._unevenly_sampled_channel.get_value_std(api900_pb2.ACCURACY)
