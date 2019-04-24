"""
This module provides convenience types for RedVox data types.
"""

import typing

import redvox.api900.sensors.evenly_sampled_sensor as evenly_sampled_sensor
import redvox.api900.sensors.unevenly_sampled_sensor as unevenly_sampled_sensor
import redvox.api900.sensors.microphone_sensor as microphone_sensor
import redvox.api900.sensors.barometer_sensor as barometer_sensor
import redvox.api900.sensors.location_sensor as location_sensor
import redvox.api900.sensors.time_synchronization_sensor as time_synchronization_sensor
import redvox.api900.sensors.gyroscope_sensor as gyroscope_sensor
import redvox.api900.sensors.magnetometer_sensor as magnetometer_sensor
import redvox.api900.sensors.accelerometer_sensor as accelerometer_sensor
import redvox.api900.sensors.light_sensor as light_sensor
import redvox.api900.sensors.infrared_sensor as infrared_sensor
import redvox.api900.sensors.image_sensor as image_sensor


# pylint: disable=C0103
RedvoxSensor = typing.Union[
    evenly_sampled_sensor.EvenlySampledSensor,
    unevenly_sampled_sensor.UnevenlySampledSensor,
    microphone_sensor.MicrophoneSensor,
    barometer_sensor.BarometerSensor,
    location_sensor.LocationSensor,
    time_synchronization_sensor.TimeSynchronizationSensor,
    accelerometer_sensor.AccelerometerSensor,
    gyroscope_sensor.GyroscopeSensor,
    magnetometer_sensor.MagnetometerSensor,
    light_sensor.LightSensor,
    infrared_sensor.InfraredSensor,
    image_sensor.ImageSensor
]
# pylint: disable=C0103
RedvoxSensors = typing.List[RedvoxSensor]
