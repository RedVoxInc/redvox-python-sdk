"""
This module provides convenience types for RedVox data types.
"""

import typing

import redvox.api900.reader as reader

WrappedRedvoxPackets = typing.List[reader.WrappedRedvoxPacket]
RedvoxSensor = typing.Union[
    reader.EvenlySampledSensor,
    reader.UnevenlySampledSensor,
    reader.MicrophoneSensor,
    reader.BarometerSensor,
    reader.LocationSensor,
    reader.TimeSynchronizationSensor,
    reader.AccelerometerSensor,
    reader.GyroscopeSensor,
    reader.MagnetometerSensor,
    reader.LightSensor,
    reader.InfraredSensor,
    reader.ImageSensor
]
RedvoxSensors = typing.List[RedvoxSensor]
