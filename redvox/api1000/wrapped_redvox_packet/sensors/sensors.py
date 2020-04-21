"""
This module encapsulates available sensor types.
"""

from typing import Optional

import redvox.api1000.wrapped_redvox_packet.common as common
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.wrapped_redvox_packet.sensors.audio as audio
import redvox.api1000.wrapped_redvox_packet.sensors.image as image
import redvox.api1000.wrapped_redvox_packet.sensors.location as location
import redvox.api1000.wrapped_redvox_packet.sensors.single as single
import redvox.api1000.wrapped_redvox_packet.sensors.xyz as xyz

_ACCELEROMETER_FIELD_NAME: str = "accelerometer"
_AMBIENT_TEMPERATURE_FIELD_NAME: str = "ambient_temperature"
_AUDIO_FIELD_NAME: str = "audio"
_COMPRESSED_AUDIO_FIELD_NAME: str = "compressed_audio"
_GRAVITY_FIELD_NAME: str = "gravity"
_GYROSCOPE_FIELD_NAME: str = "gyroscope"
_IMAGE_FIELD_NAME: str = "image"
_LIGHT_FIELD_NAME: str = "light"
_LINEAR_ACCELERATION_FIELD_NAME: str = "linear_acceleration"
_LOCATION_FIELD_NAME: str = "location"
_MAGNETOMETER_FIELD_NAME: str = "magnetometer"
_ORIENTATION_FIELD_NAME: str = "orientation"
_PRESSURE_FIELD_NAME: str = "pressure"
_PROXIMITY_FIELD_NAME: str = "proximity"
_RELATIVE_HUMIDITY_FIELD_NAME: str = "relative_humidty"


class Sensors(common.ProtoBase):
    def __init__(self, sensors_proto: redvox_api_m_pb2.RedvoxPacketM.Sensors):
        super().__init__(sensors_proto)
        self._accelerometer: xyz.Xyz = xyz.Xyz(sensors_proto.accelerometer)
        self._ambient_temperature: single.Single = single.Single(sensors_proto.ambient_temperature)
        self._audio: audio.Audio = audio.Audio(sensors_proto.audio)
        self._compressed_audio: audio.CompressedAudio = audio.CompressedAudio(sensors_proto.compressed_audio)
        self._gravity: xyz.Xyz = xyz.Xyz(sensors_proto.gravity)
        self._gyroscope: xyz.Xyz = xyz.Xyz(sensors_proto.gyroscope)
        self._image: image.Image = image.Image(sensors_proto.image)
        self._light: single.Single = single.Single(sensors_proto.light)
        self._linear_acceleration: xyz.Xyz = xyz.Xyz(sensors_proto.linear_acceleration)
        self._location: location.Location = location.Location(sensors_proto.location)
        self._magnetometer: xyz.Xyz = xyz.Xyz(sensors_proto.magnetometer)
        self._orientation: xyz.Xyz = xyz.Xyz(sensors_proto.orientation)
        self._pressure: single.Single = single.Single(sensors_proto.pressure)
        self._proximity: single.Single = single.Single(sensors_proto.proximity)
        self._relative_humidity: single.Single = single.Single(sensors_proto.relative_humidity)

    @staticmethod
    def new() -> 'Sensors':
        return Sensors(redvox_api_m_pb2.RedvoxPacketM.Sensors())

    def has_accelerometer(self) -> bool:
        return self._proto.HasField(_ACCELEROMETER_FIELD_NAME)

    def get_accelerometer(self) -> Optional[xyz.Xyz]:
        return self._accelerometer if self.has_accelerometer() else None

    def new_accelerometer(self) -> xyz.Xyz:
        accelerometer: xyz.Xyz = xyz.Xyz.new()
        accelerometer.get_timestamps().set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        accelerometer.set_unit_xyz(common.Unit.METERS_PER_SECOND_SQUARED)
        self.set_accelerometer(accelerometer)
        return accelerometer

    def set_accelerometer(self, accelerometer: xyz.Xyz) -> 'Sensors':
        common.check_type(accelerometer, [xyz.Xyz])
        self._proto.accelerometer.CopyFrom(accelerometer._proto)
        return self

    def remove_accelerometer(self) -> 'Sensors':
        self._proto.ClearField(_ACCELEROMETER_FIELD_NAME)
        return self

    def has_ambient_temperature(self) -> bool:
        return self._proto.HasField(_AMBIENT_TEMPERATURE_FIELD_NAME)

    def get_ambient_temperature(self) -> Optional[single.Single]:
        return self._ambient_temperature if self.has_ambient_temperature() else None

    def new_ambient_temperature(self) -> single.Single:
        ambient_temperature: single.Single = single.Single.new()
        ambient_temperature.get_timestamps().set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        ambient_temperature.get_samples().set_unit(common.Unit.DEGREES_CELSIUS)
        self.set_ambient_temperature(ambient_temperature)
        return ambient_temperature

    def set_ambient_temperature(self, ambient_temperature: single.Single) -> 'Sensors':
        common.check_type(ambient_temperature, [single.Single])
        self._proto.ambient_temperature.CopyFrom(ambient_temperature._proto)
        return self

    def remove_ambient_temperature(self) -> 'Sensors':
        self._proto.ClearField(_AMBIENT_TEMPERATURE_FIELD_NAME)
        return self

    def has_audio(self) -> bool:
        return self._proto.HasField(_AUDIO_FIELD_NAME)

    def get_audio(self) -> Optional[audio.Audio]:
        return self._audio if self.has_audio() else None

    def new_audio(self) -> audio.Audio:
        _audio: audio.Audio = audio.Audio.new()
        _audio.get_samples().set_unit(common.Unit.LSB_PLUS_MINUS_COUNTS)
        self.set_audio(_audio)
        return _audio

    def set_audio(self, _audio: audio.Audio) -> 'Sensors':
        common.check_type(_audio, [audio.Audio])
        self._proto.audio.CopyFrom(_audio._proto)
        return self

    def remove_audio(self) -> 'Sensors':
        self._proto.ClearField(_AUDIO_FIELD_NAME)
        return self

    def has_compress_audio(self) -> bool:
        return self._proto.HasField(_COMPRESSED_AUDIO_FIELD_NAME)

    def get_compressed_audio(self) -> Optional[audio.CompressedAudio]:
        return self._compressed_audio if self.has_compress_audio() else None

    def new_compressed_audio(self) -> audio.CompressedAudio:
        _audio: audio.CompressedAudio = audio.CompressedAudio.new()
        # _audio.get_samples().set_unit(common.Unit.LSB_PLUS_MINUS_COUNTS)
        # self.set_audio(_audio)
        return _audio

    def set_compressed_audio(self, compressed_audio: audio.CompressedAudio) -> 'Sensors':
        common.check_type(compressed_audio, [audio.Audio])
        self._proto.audio.CopyFrom(compressed_audio._proto)
        return self

    def remove_compressed_audio(self) -> 'Sensors':
        self._proto.ClearField(_COMPRESSED_AUDIO_FIELD_NAME)
        return self

    def has_gravity(self) -> bool:
        return self._proto.HasField(_GRAVITY_FIELD_NAME)

    def get_gravity(self) -> Optional[xyz.Xyz]:
        return self._gravity if self.has_gravity() else None

    def new_gravity(self) -> xyz.Xyz:
        gravity: xyz.Xyz = xyz.Xyz.new()
        gravity.get_timestamps().set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        gravity.set_unit_xyz(common.Unit.METERS_PER_SECOND_SQUARED)
        self.set_gravity(gravity)
        return gravity

    def set_gravity(self, gravity: xyz.Xyz) -> 'Sensors':
        common.check_type(gravity, [xyz.Xyz])
        self._proto.gravity.CopyFrom(gravity._proto)
        return self

    def remove_gravity(self) -> 'Sensors':
        self._proto.ClearField(_GRAVITY_FIELD_NAME)
        return self

    def has_gyroscope(self) -> bool:
        return self._proto.HasField(_GYROSCOPE_FIELD_NAME)

    def get_gyroscope(self) -> Optional[xyz.Xyz]:
        return self._gyroscope if self.has_gyroscope() else None

    def new_gyroscope(self) -> xyz.Xyz:
        gyroscope: xyz.Xyz = xyz.Xyz.new()
        gyroscope.get_timestamps().set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        gyroscope.set_unit_xyz(common.Unit.RADIANS_PER_SECOND)
        self.set_gyroscope(gyroscope)
        return gyroscope

    def set_gyroscope(self, gyroscope: xyz.Xyz) -> 'Sensors':
        common.check_type(gyroscope, [xyz.Xyz])
        self._proto.gyroscope.CopyFrom(gyroscope._proto)
        return self

    def remove_gyroscope(self) -> 'Sensors':
        self._proto.ClearField(_GYROSCOPE_FIELD_NAME)
        return self

    def has_image(self) -> bool:
        return self._proto.HasField(_IMAGE_FIELD_NAME)

    def get_image(self) -> Optional[image.Image]:
        return self._image if self.has_image() else None

    def new_image(self) -> image.Image:
        _image: image.Image = image.Image.new()
        # _image.get_timestamps().set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        self.set_image(_image)
        return _image

    def set_image(self, _image: image.Image) -> 'Sensors':
        common.check_type(_image, [image.Image])
        self._proto.image.CopyFrom(_image._proto)
        return self

    def remove_image(self) -> 'Sensors':
        self._proto.ClearField(_IMAGE_FIELD_NAME)
        return self

    def has_light(self) -> bool:
        return self._proto.HasField(_LIGHT_FIELD_NAME)

    def get_light(self) -> Optional[single.Single]:
        return self._light if self.has_light() else None

    def new_light(self) -> single.Single:
        light: single.Single = single.Single.new()
        light.get_timestamps().set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        light.get_samples().set_unit(common.Unit.LUX)
        self.set_light(light)
        return light

    def set_light(self, light: single.Single) -> 'Sensors':
        common.check_type(light, [single.Single])
        self._proto.light.CopyFrom(light._proto)
        return self

    def remove_light(self) -> 'Sensors':
        self._proto.ClearField(_LIGHT_FIELD_NAME)
        return self

    def has_linear_acceleration(self) -> bool:
        return self._proto.HasField(_LINEAR_ACCELERATION_FIELD_NAME)

    def get_linear_acceleration(self) -> Optional[xyz.Xyz]:
        return self._linear_acceleration if self.has_linear_acceleration() else None

    def new_linear_acceleration(self) -> xyz.Xyz:
        linear_acceleration: xyz.Xyz = xyz.Xyz.new()
        linear_acceleration.get_timestamps().set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        linear_acceleration.set_unit_xyz(common.Unit.METERS_PER_SECOND_SQUARED)
        self.set_linear_acceleration(linear_acceleration)
        return linear_acceleration

    def set_linear_acceleration(self, linear_acceleration: xyz.Xyz) -> 'Sensors':
        common.check_type(linear_acceleration, [xyz.Xyz])
        self._proto.linear_acceleration.CopyFrom(linear_acceleration._proto)
        return self

    def remove_linear_acceleration(self) -> 'Sensors':
        self._proto.ClearField(_LINEAR_ACCELERATION_FIELD_NAME)
        return self

    def has_location(self) -> bool:
        return self._proto.HasField(_LOCATION_FIELD_NAME)

    def get_location(self) -> Optional[location.Location]:
        return self._location if self.has_location() else None

    def new_location(self) -> location.Location:
        _location: location.Location = location.Location.new()
        _location.get_timestamps().set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        _location.get_latitude_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        _location.get_longitude_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        _location.get_altitude_samples().set_unit(common.Unit.METERS)
        _location.get_speed_samples().set_unit(common.Unit.METERS_PER_SECOND)
        _location.get_bearing_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        _location.get_horizontal_accuracy_samples().set_unit(common.Unit.METERS)
        _location.get_vertical_accuracy_samples().set_unit(common.Unit.METERS)
        _location.get_speed_accuracy_samples().set_unit(common.Unit.METERS_PER_SECOND)
        _location.get_bearing_accuracy_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        self.set_location(_location)
        return _location

    def set_location(self, _location: location.Location) -> 'Sensors':
        common.check_type(_location, [location.Location])
        self._proto.location.CopyFrom(_location._proto)
        return self

    def remove_location(self) -> 'Sensors':
        self._proto.ClearField(_LOCATION_FIELD_NAME)
        return self

    def has_magnetometer(self) -> bool:
        return self._proto.HasField(_MAGNETOMETER_FIELD_NAME)

    def get_magnetometer(self) -> Optional[xyz.Xyz]:
        return self._magnetometer if self.has_magnetometer() else None

    def new_magnetometer(self) -> xyz.Xyz:
        magnetometer: xyz.Xyz = xyz.Xyz.new()
        magnetometer.get_timestamps().set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        magnetometer.set_unit_xyz(common.Unit.MICROTESLA)
        self.set_magnetometer(magnetometer)
        return magnetometer

    def set_magnetometer(self, magnetometer: xyz.Xyz) -> 'Sensors':
        common.check_type(magnetometer, [xyz.Xyz])
        self._proto.magnetometer.CopyFrom(magnetometer._proto)
        return self

    def remove_magnetometer(self) -> 'Sensors':
        self._proto.ClearField(_MAGNETOMETER_FIELD_NAME)
        return self

    def has_orientation(self) -> bool:
        return self._proto.HasField(_ORIENTATION_FIELD_NAME)

    def get_orientation(self) -> Optional[xyz.Xyz]:
        return self._orientation if self.has_orientation() else None

    def new_orientation(self) -> xyz.Xyz:
        orientation: xyz.Xyz = xyz.Xyz.new()
        orientation.get_timestamps().set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        orientation.set_unit_xyz(common.Unit.RADIANS)
        self.set_orientation(orientation)
        return orientation

    def set_orientation(self, orientation: xyz.Xyz) -> 'Sensors':
        common.check_type(orientation, [xyz.Xyz])
        self._proto.orientation.CopyFrom(orientation._proto)
        return self

    def remove_orientation(self) -> 'Sensors':
        self._proto.ClearField(_ORIENTATION_FIELD_NAME)
        return self

    def has_pressure(self) -> bool:
        return self._proto.HasField(_PRESSURE_FIELD_NAME)

    def get_pressure(self) -> Optional[single.Single]:
        return self._pressure if self.has_pressure() else None

    def new_pressure(self) -> single.Single:
        pressure: single.Single = single.Single.new()
        pressure.get_timestamps().set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        pressure.get_samples().set_unit(common.Unit.KILOPASCAL)
        self.set_pressure(pressure)
        return pressure

    def set_pressure(self, pressure: single.Single) -> 'Sensors':
        common.check_type(pressure, [single.Single])
        self._proto.pressure.CopyFrom(pressure._proto)
        return self

    def remove_pressure(self) -> 'Sensors':
        self._proto.ClearField(_PRESSURE_FIELD_NAME)
        return self

    def has_proximity(self) -> bool:
        return self._proto.HasField(_PROXIMITY_FIELD_NAME)

    def get_proximity(self) -> Optional[single.Single]:
        return self._proximity if self.has_proximity() else None

    def new_proximity(self) -> single.Single:
        proximity: single.Single = single.Single.new()
        proximity.get_timestamps().set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        proximity.get_samples().set_unit(common.Unit.CENTIMETERS)
        self.set_proximity(proximity)
        return proximity

    def set_proximity(self, proximity: single.Single) -> 'Sensors':
        common.check_type(proximity, [single.Single])
        self._proto.proximity.CopyFrom(proximity._proto)
        return self

    def remove_proximity(self) -> 'Sensors':
        self._proto.ClearField(_PROXIMITY_FIELD_NAME)
        return self

    def has_relative_humidity(self) -> bool:
        return self._proto.HasField(_RELATIVE_HUMIDITY_FIELD_NAME)

    def get_relative_humidity(self) -> Optional[single.Single]:
        return self._relative_humidity if self.has_relative_humidity() else None

    def new_relative_humidity(self) -> single.Single:
        relative_humidity: single.Single = single.Single.new()
        relative_humidity.get_timestamps().set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        relative_humidity.get_samples().set_unit(common.Unit.PERCENTAGE)
        self.set_relative_humidity(relative_humidity)
        return relative_humidity

    def set_relative_humidity(self, relative_humidity: single.Single) -> 'Sensors':
        common.check_type(relative_humidity, [single.Single])
        self._proto.relative_humidity.CopyFrom(relative_humidity._proto)
        return self

    def remove_relative_humidity(self) -> 'Sensors':
        self._proto.ClearField(_RELATIVE_HUMIDITY_FIELD_NAME)
        return self


