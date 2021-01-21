"""
This module encapsulates available sensor types.
"""

from typing import Optional, List

import redvox.api1000.common.common as common
import redvox.api1000.common.typing
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.common.generic
import redvox.api1000.wrapped_redvox_packet.sensors.audio as audio
import redvox.api1000.wrapped_redvox_packet.sensors.image as image
import redvox.api1000.wrapped_redvox_packet.sensors.location as location
import redvox.api1000.wrapped_redvox_packet.sensors.single as single
import redvox.api1000.wrapped_redvox_packet.sensors.xyz as xyz


class Sensors(
    redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.Sensors]
):
    """
    This class encapsulated available API M sensors.
    """

    # These are used for checking if a field is present or not
    __ACCELEROMETER_FIELD_NAME: str = "accelerometer"
    __AMBIENT_TEMPERATURE_FIELD_NAME: str = "ambient_temperature"
    __AUDIO_FIELD_NAME: str = "audio"
    __COMPRESSED_AUDIO_FIELD_NAME: str = "compressed_audio"
    __GRAVITY_FIELD_NAME: str = "gravity"
    __GYROSCOPE_FIELD_NAME: str = "gyroscope"
    __IMAGE_FIELD_NAME: str = "image"
    __LIGHT_FIELD_NAME: str = "light"
    __LINEAR_ACCELERATION_FIELD_NAME: str = "linear_acceleration"
    __LOCATION_FIELD_NAME: str = "location"
    __MAGNETOMETER_FIELD_NAME: str = "magnetometer"
    __ORIENTATION_FIELD_NAME: str = "orientation"
    __PRESSURE_FIELD_NAME: str = "pressure"
    __PROXIMITY_FIELD_NAME: str = "proximity"
    __RELATIVE_HUMIDITY_FIELD_NAME: str = "relative_humidity"
    __ROTATION_VECTOR: str = "rotation_vector"
    __VELOCITY: str = "velocity"

    def __init__(self, sensors_proto: redvox_api_m_pb2.RedvoxPacketM.Sensors):
        super().__init__(sensors_proto)
        self._accelerometer: xyz.Xyz = xyz.Xyz(sensors_proto.accelerometer)
        self._ambient_temperature: single.Single = single.Single(
            sensors_proto.ambient_temperature
        )
        self._audio: audio.Audio = audio.Audio(sensors_proto.audio)
        self._compressed_audio: audio.CompressedAudio = audio.CompressedAudio(
            sensors_proto.compressed_audio
        )
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
        self._relative_humidity: single.Single = single.Single(
            sensors_proto.relative_humidity
        )
        self._rotation_vector: xyz.Xyz = xyz.Xyz(sensors_proto.rotation_vector)
        self._velocity: xyz.Xyz = xyz.Xyz(sensors_proto.velocity)

    @staticmethod
    def new() -> "Sensors":
        """
        :return: A new, empty Sensors instance
        """
        return Sensors(redvox_api_m_pb2.RedvoxPacketM.Sensors())

    def has_accelerometer(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__ACCELEROMETER_FIELD_NAME)

    def get_accelerometer(self) -> Optional[xyz.Xyz]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._accelerometer if self.has_accelerometer() else None

    def new_accelerometer(self) -> xyz.Xyz:
        """
        :return: A new empty sensor
        """
        self.remove_accelerometer()
        self.get_proto().accelerometer.SetInParent()
        self._accelerometer = xyz.Xyz(self.get_proto().accelerometer)
        self._accelerometer.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._accelerometer.set_unit_xyz(common.Unit.METERS_PER_SECOND_SQUARED)
        return self._accelerometer

    def set_accelerometer(self, accelerometer: xyz.Xyz) -> "Sensors":
        """
        Sets the channel
        :param accelerometer: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(accelerometer, [xyz.Xyz])
        self.get_proto().accelerometer.CopyFrom(accelerometer.get_proto())
        self._accelerometer = xyz.Xyz(self.get_proto().accelerometer)
        return self

    def remove_accelerometer(self) -> "Sensors":
        """
        Removes this channel
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__ACCELEROMETER_FIELD_NAME)
        return self

    def validate_accelerometer(self) -> bool:
        """
        Checks if there are no errors with the accelerometer and it contains at least 1 data entry
        :return: True if no errors
        """
        # noinspection PyTypeChecker
        return (
            len(
                xyz.validate_xyz(
                    self._accelerometer, common.Unit.METERS_PER_SECOND_SQUARED
                )
            )
            < 1
            and self._accelerometer.get_x_samples().get_values_count() > 0
        )

    def has_ambient_temperature(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__AMBIENT_TEMPERATURE_FIELD_NAME)

    def get_ambient_temperature(self) -> Optional[single.Single]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._ambient_temperature if self.has_ambient_temperature() else None

    def new_ambient_temperature(self) -> single.Single:
        """
        :return: A new empty sensor
        """
        self.remove_ambient_temperature()
        self.get_proto().ambient_temperature.SetInParent()
        self._ambient_temperature = single.Single(self.get_proto().ambient_temperature)
        self._ambient_temperature.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._ambient_temperature.get_samples().set_unit(common.Unit.DEGREES_CELSIUS)
        return self._ambient_temperature

    def set_ambient_temperature(self, ambient_temperature: single.Single) -> "Sensors":
        """
        Sets the channel
        :param ambient_temperature: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(ambient_temperature, [single.Single])
        self.get_proto().ambient_temperature.CopyFrom(ambient_temperature.get_proto())
        self._ambient_temperature = single.Single(self.get_proto().ambient_temperature)
        return self

    def remove_ambient_temperature(self) -> "Sensors":
        """
        Removes this channel
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__AMBIENT_TEMPERATURE_FIELD_NAME)
        return self

    def validate_ambient_temperature(self) -> bool:
        """
        Checks if there are no errors with the ambient temperature sensor and it contains at least 1 data entry
        :return: True if no errors
        """
        # noinspection PyTypeChecker
        return (
            len(
                single.validate_single(
                    self._ambient_temperature, common.Unit.DEGREES_CELSIUS
                )
            )
            < 1
            and self._ambient_temperature.get_samples().get_values_count() > 0
        )

    def has_audio(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__AUDIO_FIELD_NAME)

    def get_audio(self) -> Optional[audio.Audio]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._audio if self.has_audio() else None

    def new_audio(self) -> audio.Audio:
        """
        :return: A new empty sensor
        """
        self.remove_audio()
        self.get_proto().audio.SetInParent()
        self._audio = audio.Audio(self.get_proto().audio)
        # noinspection PyTypeChecker
        self._audio.get_samples().set_unit(common.Unit.LSB_PLUS_MINUS_COUNTS)
        return self._audio

    def set_audio(self, _audio: audio.Audio) -> "Sensors":
        """
        Sets the channel
        :param _audio: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(_audio, [audio.Audio])
        self.get_proto().audio.CopyFrom(_audio.get_proto())
        self._audio = audio.Audio(self.get_proto().audio)
        return self

    def remove_audio(self) -> "Sensors":
        """
        Removes this channel
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__AUDIO_FIELD_NAME)
        return self

    def validate_audio(self) -> bool:
        """
        Checks if there are no errors with the audio sensor and it contains at least 1 data entry
        :return: True if no errors
        """
        return (
            len(audio.validate_audio(self._audio)) < 1
            and self._audio.get_samples().get_values_count() > 0
        )

    def has_compressed_audio(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__COMPRESSED_AUDIO_FIELD_NAME)

    def get_compressed_audio(self) -> Optional[audio.CompressedAudio]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._compressed_audio if self.has_compressed_audio() else None

    def new_compressed_audio(self) -> audio.CompressedAudio:
        """
        :return: A new empty sensor
        """
        self.remove_compressed_audio()
        self.get_proto().compressed_audio.SetInParent()
        self._compressed_audio = audio.CompressedAudio(
            self.get_proto().compressed_audio
        )
        return self._compressed_audio

    def set_compressed_audio(
        self, compressed_audio: audio.CompressedAudio
    ) -> "Sensors":
        """
        Sets the channel
        :param compressed_audio: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(
            compressed_audio, [audio.CompressedAudio]
        )
        # noinspection Mypy
        self.get_proto().compressed_audio.CopyFrom(compressed_audio.get_proto())
        self._compressed_audio = audio.CompressedAudio(
            self.get_proto().compressed_audio
        )
        return self

    def remove_compressed_audio(self) -> "Sensors":
        """
        Removes this channel
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__COMPRESSED_AUDIO_FIELD_NAME)
        return self

    def validate_compressed_audio(self) -> bool:
        """
        Checks if there are no errors with the compressed audio sensor and it contains at least 1 data entry
        :return: True if no errors
        """
        return len(audio.validate_compressed_audio(self._compressed_audio)) < 1

    def has_gravity(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker,Mypy
        return self.get_proto().HasField(Sensors.__GRAVITY_FIELD_NAME)

    def get_gravity(self) -> Optional[xyz.Xyz]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._gravity if self.has_gravity() else None

    def new_gravity(self) -> xyz.Xyz:
        """
        :return: A new empty sensor
        """
        self.remove_gravity()
        self.get_proto().gravity.SetInParent()
        self._gravity = xyz.Xyz(self.get_proto().gravity)
        self._gravity.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._gravity.set_unit_xyz(common.Unit.METERS_PER_SECOND_SQUARED)
        return self._gravity

    def set_gravity(self, gravity: xyz.Xyz) -> "Sensors":
        """
        Sets the channel
        :param gravity: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(gravity, [xyz.Xyz])
        self.get_proto().gravity.CopyFrom(gravity.get_proto())
        self._gravity = xyz.Xyz(self.get_proto().gravity)
        return self

    def remove_gravity(self) -> "Sensors":
        """
        Removes this channel
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__GRAVITY_FIELD_NAME)
        return self

    def validate_gravity(self) -> bool:
        """
        Checks if there are no errors with the gravity sensor and it contains at least 1 data entry
        :return: True if no errors
        """
        # noinspection PyTypeChecker
        return (
            len(xyz.validate_xyz(self._gravity, common.Unit.METERS_PER_SECOND_SQUARED))
            < 1
            and self._gravity.get_x_samples().get_values_count() > 0
        )

    def has_gyroscope(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__GYROSCOPE_FIELD_NAME)

    def get_gyroscope(self) -> Optional[xyz.Xyz]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._gyroscope if self.has_gyroscope() else None

    def new_gyroscope(self) -> xyz.Xyz:
        """
        :return: A new empty sensor
        """
        self.remove_gyroscope()
        self.get_proto().gyroscope.SetInParent()
        self._gyroscope = xyz.Xyz(self.get_proto().gyroscope)
        self._gyroscope.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._gyroscope.set_unit_xyz(common.Unit.RADIANS_PER_SECOND)
        return self._gyroscope

    def set_gyroscope(self, gyroscope: xyz.Xyz) -> "Sensors":
        """
        Sets the channel
        :param gyroscope: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(gyroscope, [xyz.Xyz])
        self.get_proto().gyroscope.CopyFrom(gyroscope.get_proto())
        self._gyroscope = xyz.Xyz(self.get_proto().gyroscope)
        return self

    def remove_gyroscope(self) -> "Sensors":
        """
        Removes this sensor
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__GYROSCOPE_FIELD_NAME)
        return self

    def validate_gyroscope(self) -> bool:
        """
        Checks if there are no errors with the gyroscope and it contains at least 1 data entry
        :return: True if no errors
        """
        # noinspection PyTypeChecker
        return (
            len(xyz.validate_xyz(self._gyroscope, common.Unit.RADIANS_PER_SECOND)) < 1
            and self._gyroscope.get_x_samples().get_values_count() > 0
        )

    def has_image(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__IMAGE_FIELD_NAME)

    def get_image(self) -> Optional[image.Image]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._image if self.has_image() else None

    def new_image(self) -> image.Image:
        """
        :return: A new empty sensor
        """
        self.remove_image()
        self.get_proto().image.SetInParent()
        self._image = image.Image(self.get_proto().image)
        # noinspection PyTypeChecker
        self._image.set_image_codec(image.ImageCodec.PNG)
        return self._image

    def set_image(self, _image: image.Image) -> "Sensors":
        """
        Sets the channel
        :param _image: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(_image, [image.Image])
        self.get_proto().image.CopyFrom(_image.get_proto())
        self._image = image.Image(self.get_proto().image)
        return self

    def remove_image(self) -> "Sensors":
        """
        Removes this sensor
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__IMAGE_FIELD_NAME)
        return self

    def validate_image(self) -> bool:
        """
        Checks if there are no errors with the image sensor and it contains at least 1 data entry
        :return: True if no errors
        """
        return (
            len(image.validate_image(self._image)) < 1
            and self._image.get_num_images() > 0
        )

    def has_light(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__LIGHT_FIELD_NAME)

    def get_light(self) -> Optional[single.Single]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._light if self.has_light() else None

    def new_light(self) -> single.Single:
        """
        :return: A new empty sensor
        """
        self.remove_light()
        self.get_proto().light.SetInParent()
        self._light = single.Single(self.get_proto().light)
        self._light.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._light.get_samples().set_unit(common.Unit.LUX)
        return self._light

    def set_light(self, light: single.Single) -> "Sensors":
        """
        Sets the channel
        :param light: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(light, [single.Single])
        self.get_proto().light.CopyFrom(light.get_proto())
        self._light = single.Single(self.get_proto().light)
        return self

    def remove_light(self) -> "Sensors":
        """
        Removes this sensor
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__LIGHT_FIELD_NAME)
        return self

    def validate_light(self) -> bool:
        """
        Checks if there are no errors with the light sensor and it contains at least 1 data entry
        :return: True if no errors
        """
        # noinspection PyTypeChecker
        return (
            len(single.validate_single(self._light, common.Unit.LUX)) < 1
            and self._light.get_samples().get_values_count() > 0
        )

    def has_linear_acceleration(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__LINEAR_ACCELERATION_FIELD_NAME)

    def get_linear_acceleration(self) -> Optional[xyz.Xyz]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._linear_acceleration if self.has_linear_acceleration() else None

    def new_linear_acceleration(self) -> xyz.Xyz:
        """
        :return: A new empty sensor
        """
        self.remove_linear_acceleration()
        self.get_proto().linear_acceleration.SetInParent()
        self._linear_acceleration = xyz.Xyz(self.get_proto().linear_acceleration)
        self._linear_acceleration.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._linear_acceleration.set_unit_xyz(common.Unit.METERS_PER_SECOND_SQUARED)
        return self._linear_acceleration

    def set_linear_acceleration(self, linear_acceleration: xyz.Xyz) -> "Sensors":
        """
        Sets the channel
        :param linear_acceleration: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(linear_acceleration, [xyz.Xyz])
        self.get_proto().linear_acceleration.CopyFrom(linear_acceleration.get_proto())
        self._linear_acceleration = xyz.Xyz(self.get_proto().linear_acceleration)
        return self

    def remove_linear_acceleration(self) -> "Sensors":
        """
        Removes this sensor
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__LINEAR_ACCELERATION_FIELD_NAME)
        return self

    def validate_linear_acceleration(self) -> bool:
        """
        Checks if there are no errors with the linear acceleration sensor and it contains at least 1 data entry
        :return: True if no errors
        """
        # noinspection PyTypeChecker
        return (
            len(
                xyz.validate_xyz(
                    self._linear_acceleration, common.Unit.METERS_PER_SECOND_SQUARED
                )
            )
            < 1
            and self._linear_acceleration.get_x_samples().get_values_count() > 0
        )

    def has_location(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__LOCATION_FIELD_NAME)

    def get_location(self) -> Optional[location.Location]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._location if self.has_location() else None

    def new_location(self) -> location.Location:
        """
        :return: A new empty sensor
        """
        self.remove_location()
        self.get_proto().location.SetInParent()
        self._location = location.Location(self.get_proto().location)
        self._location.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._location.get_latitude_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        # noinspection PyTypeChecker
        self._location.get_longitude_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        # noinspection PyTypeChecker
        self._location.get_altitude_samples().set_unit(common.Unit.METERS)
        # noinspection PyTypeChecker
        self._location.get_speed_samples().set_unit(common.Unit.METERS_PER_SECOND)
        # noinspection PyTypeChecker
        self._location.get_bearing_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        # noinspection PyTypeChecker
        self._location.get_horizontal_accuracy_samples().set_unit(common.Unit.METERS)
        # noinspection PyTypeChecker
        self._location.get_vertical_accuracy_samples().set_unit(common.Unit.METERS)
        # noinspection PyTypeChecker
        self._location.get_speed_accuracy_samples().set_unit(
            common.Unit.METERS_PER_SECOND
        )
        # noinspection PyTypeChecker
        self._location.get_bearing_accuracy_samples().set_unit(
            common.Unit.DECIMAL_DEGREES
        )
        return self._location

    def set_location(self, _location: location.Location) -> "Sensors":
        """
        Sets the channel
        :param _location: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(_location, [location.Location])
        self.get_proto().location.CopyFrom(_location.get_proto())
        self._location = location.Location(self.get_proto().location)
        return self

    def remove_location(self) -> "Sensors":
        """
        Removes this sensor
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__LOCATION_FIELD_NAME)
        return self

    def validate_location(self) -> bool:
        """
        Checks if there are no errors with the location
        :return: True if no errors
        """
        return len(location.validate_location(self._location)) < 1

    def has_magnetometer(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__MAGNETOMETER_FIELD_NAME)

    def get_magnetometer(self) -> Optional[xyz.Xyz]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._magnetometer if self.has_magnetometer() else None

    def new_magnetometer(self) -> xyz.Xyz:
        """
        :return: A new empty sensor
        """
        self.remove_magnetometer()
        self.get_proto().magnetometer.SetInParent()
        self._magnetometer = xyz.Xyz(self.get_proto().magnetometer)
        self._magnetometer.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._magnetometer.set_unit_xyz(common.Unit.MICROTESLA)
        return self._magnetometer

    def set_magnetometer(self, magnetometer: xyz.Xyz) -> "Sensors":
        """
        Sets the channel
        :param magnetometer: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(magnetometer, [xyz.Xyz])
        self.get_proto().magnetometer.CopyFrom(magnetometer.get_proto())
        self._magnetometer = xyz.Xyz(self.get_proto().magnetometer)
        return self

    def remove_magnetometer(self) -> "Sensors":
        """
        Removes this sensor
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__MAGNETOMETER_FIELD_NAME)
        return self

    def validate_magnetometer(self) -> bool:
        """
        Checks if there are no errors with the magnetometer and it contains at least 1 data entry
        :return: True if no errors
        """
        # noinspection PyTypeChecker
        return (
            len(xyz.validate_xyz(self._magnetometer, common.Unit.MICROTESLA)) < 1
            and self._magnetometer.get_x_samples().get_values_count() > 0
        )

    def has_orientation(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__ORIENTATION_FIELD_NAME)

    def get_orientation(self) -> Optional[xyz.Xyz]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._orientation if self.has_orientation() else None

    def new_orientation(self) -> xyz.Xyz:
        """
        :return: A new empty sensor
        """
        self.remove_orientation()
        self.get_proto().orientation.SetInParent()
        self._orientation = xyz.Xyz(self.get_proto().orientation)
        self._orientation.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._orientation.set_unit_xyz(common.Unit.RADIANS)
        return self._orientation

    def set_orientation(self, orientation: xyz.Xyz) -> "Sensors":
        """
        Sets the channel
        :param orientation: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(orientation, [xyz.Xyz])
        self.get_proto().orientation.CopyFrom(orientation.get_proto())
        self._orientation = xyz.Xyz(self.get_proto().orientation)
        return self

    def remove_orientation(self) -> "Sensors":
        """
        Removes this sensor
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__ORIENTATION_FIELD_NAME)
        return self

    def validate_orientation(self) -> bool:
        """
        Checks if there are no errors with the orientation sensor and it contains at least 1 data entry
        :return: True if no errors
        """
        # noinspection PyTypeChecker
        return (
            len(xyz.validate_xyz(self._orientation, common.Unit.RADIANS)) < 1
            and self._orientation.get_x_samples().get_values_count() > 0
        )

    def has_pressure(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__PRESSURE_FIELD_NAME)

    def get_pressure(self) -> Optional[single.Single]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._pressure if self.has_pressure() else None

    def new_pressure(self) -> single.Single:
        """
        :return: A new empty sensor
        """
        self.remove_pressure()
        self.get_proto().pressure.SetInParent()
        self._pressure = single.Single(self.get_proto().pressure)
        self._pressure.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._pressure.get_samples().set_unit(common.Unit.KILOPASCAL)
        return self._pressure

    def set_pressure(self, pressure: single.Single) -> "Sensors":
        """
        Sets the channel
        :param pressure: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(pressure, [single.Single])
        self.get_proto().pressure.CopyFrom(pressure.get_proto())
        self._pressure = single.Single(self.get_proto().pressure)
        return self

    def remove_pressure(self) -> "Sensors":
        """
        Removes this sensor
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__PRESSURE_FIELD_NAME)
        return self

    def validate_pressure(self) -> bool:
        """
        Checks if there are no errors with the pressure sensor and it contains at least 1 data entry
        :return: True if no errors
        """
        # noinspection PyTypeChecker
        return (
            len(single.validate_single(self._pressure, common.Unit.KILOPASCAL)) < 1
            and self._pressure.get_samples().get_values_count() > 0
        )

    def has_proximity(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__PROXIMITY_FIELD_NAME)

    def get_proximity(self) -> Optional[single.Single]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._proximity if self.has_proximity() else None

    def new_proximity(self) -> single.Single:
        """
        :return: A new empty sensor
        """
        self.remove_proximity()
        self.get_proto().proximity.SetInParent()
        self._proximity = single.Single(self.get_proto().proximity)
        self._proximity.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._proximity.get_samples().set_unit(common.Unit.CENTIMETERS)
        return self._proximity

    def set_proximity(self, proximity: single.Single) -> "Sensors":
        """
        Sets the channel
        :param proximity: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(proximity, [single.Single])
        self.get_proto().proximity.CopyFrom(proximity.get_proto())
        self._proximity = single.Single(self.get_proto().proximity)
        return self

    def remove_proximity(self) -> "Sensors":
        """
        Removes this sensor
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__PROXIMITY_FIELD_NAME)
        return self

    def validate_proximity(self) -> bool:
        """
        Checks if there are no errors with the proximity sensor and it contains at least 1 data entry
        :return: True if no errors
        """
        # noinspection PyTypeChecker
        return (
            len(single.validate_single(self._proximity, common.Unit.CENTIMETERS)) < 1
            and self._proximity.get_samples().get_values_count() > 0
        )

    def has_relative_humidity(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__RELATIVE_HUMIDITY_FIELD_NAME)

    def get_relative_humidity(self) -> Optional[single.Single]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._relative_humidity if self.has_relative_humidity() else None

    def new_relative_humidity(self) -> single.Single:
        """
        :return: A new empty sensor
        """
        self.remove_relative_humidity()
        self.get_proto().relative_humidity.SetInParent()
        self._relative_humidity = single.Single(self.get_proto().relative_humidity)
        self._relative_humidity.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._relative_humidity.get_samples().set_unit(common.Unit.PERCENTAGE)
        return self._relative_humidity

    def set_relative_humidity(self, relative_humidity: single.Single) -> "Sensors":
        """
        Sets the channel
        :param relative_humidity: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(relative_humidity, [single.Single])
        self.get_proto().relative_humidity.CopyFrom(relative_humidity.get_proto())
        self._relative_humidity = single.Single(self.get_proto().relative_humidity)
        return self

    def remove_relative_humidity(self) -> "Sensors":
        """
        Removes this sensor
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__RELATIVE_HUMIDITY_FIELD_NAME)
        return self

    def validate_relative_humidity(self) -> bool:
        """
        Checks if there are no errors with the relative_humidity sensor and it contains at least 1 data entry
        :return: True if no errors
        """
        # noinspection PyTypeChecker
        return (
            len(single.validate_single(self._relative_humidity, common.Unit.PERCENTAGE))
            < 1
            and self._relative_humidity.get_samples().get_values_count() > 0
        )

    def has_rotation_vector(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__ROTATION_VECTOR)

    def get_rotation_vector(self) -> Optional[xyz.Xyz]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._rotation_vector if self.has_rotation_vector() else None

    def new_rotation_vector(self) -> xyz.Xyz:
        """
        :return: A new empty sensor
        """
        self.remove_rotation_vector()
        self.get_proto().rotation_vector.SetInParent()
        self._rotation_vector = xyz.Xyz(self.get_proto().rotation_vector)
        self._rotation_vector.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._rotation_vector.set_unit_xyz(common.Unit.UNITLESS)
        return self._rotation_vector

    def set_rotation_vector(self, rotation_vector: xyz.Xyz) -> "Sensors":
        """
        Sets the channel
        :param rotation_vector: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(rotation_vector, [xyz.Xyz])
        self.get_proto().rotation_vector.CopyFrom(rotation_vector.get_proto())
        self._rotation_vector = xyz.Xyz(self.get_proto().rotation_vector)
        return self

    def remove_rotation_vector(self) -> "Sensors":
        """
        Removes this sensor
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__ROTATION_VECTOR)
        return self

    def validate_rotation_vector(self) -> bool:
        """
        Checks if there are no errors with the rotation vector sensor and it contains at least 1 data entry
        :return: True if no errors
        """
        # noinspection PyTypeChecker
        return (
            len(xyz.validate_xyz(self._rotation_vector, common.Unit.UNITLESS)) < 1
            and self._rotation_vector.get_x_samples().get_values_count() > 0
        )

    def has_velocity(self) -> bool:
        """
        :return: If this packet contains this channel
        """
        # noinspection PyTypeChecker
        return self.get_proto().HasField(Sensors.__VELOCITY)

    def get_velocity(self) -> Optional[xyz.Xyz]:
        """
        :return: The this sensor if it exists otherwise None
        """
        return self._velocity if self.has_velocity() else None

    def new_velocity(self) -> xyz.Xyz:
        """
        :return: A new empty sensor
        """
        self.remove_velocity()
        self.get_proto().velocity.SetInParent()
        self._velocity = xyz.Xyz(self.get_proto().velocity)
        self._velocity.get_timestamps().set_default_unit()
        # noinspection PyTypeChecker
        self._velocity.set_unit_xyz(common.Unit.METERS_PER_SECOND)
        return self._velocity

    def set_velocity(self, velocity: xyz.Xyz) -> "Sensors":
        """
        Sets the channel
        :param velocity: Channel to set
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(velocity, [xyz.Xyz])
        self.get_proto().velocity.CopyFrom(velocity.get_proto())
        self._velocity = xyz.Xyz(self.get_proto().velocity)
        return self

    def remove_velocity(self) -> "Sensors":
        """
        Removes this sensor
        :return: A modified instance of self
        """
        # noinspection PyTypeChecker
        self.get_proto().ClearField(Sensors.__VELOCITY)
        return self

    def validate_velocity(self) -> bool:
        """
        Checks if there are no errors with the sensor and it contains at least 1 data entry
        :return: True if no errors
        """
        # noinspection PyTypeChecker
        return (
            len(xyz.validate_xyz(self._velocity, common.Unit.METERS_PER_SECOND)) < 1
            and self._velocity.get_x_samples().get_values_count() > 0
        )


def validate_sensors(sensors_list: Sensors) -> List[str]:
    """
    Validates sensors.
    :param sensors_list: Sensors to validate
    :return: A list of validated errors
    """
    # audio is the only sensor that every packet must have
    errors_list = []
    if not sensors_list.has_audio() and not sensors_list.has_compressed_audio():
        errors_list.append("Sensors list missing audio sensor")
    else:
        if sensors_list.has_audio():
            errors_list.extend(audio.validate_audio(sensors_list.get_audio()))
        if sensors_list.has_compressed_audio():
            errors_list.extend(
                audio.validate_compressed_audio(sensors_list.get_compressed_audio())
            )
    if sensors_list.has_accelerometer():
        errors_list.extend(
            xyz.validate_xyz(
                sensors_list.get_accelerometer(), common.Unit.METERS_PER_SECOND_SQUARED
            )
        )
    if sensors_list.has_ambient_temperature():
        errors_list.extend(
            single.validate_single(
                sensors_list.get_ambient_temperature(), common.Unit.DEGREES_CELSIUS
            )
        )
    if sensors_list.has_gravity():
        errors_list.extend(
            xyz.validate_xyz(
                sensors_list.get_gravity(), common.Unit.METERS_PER_SECOND_SQUARED
            )
        )
    if sensors_list.has_gyroscope():
        errors_list.extend(
            xyz.validate_xyz(
                sensors_list.get_gyroscope(), common.Unit.RADIANS_PER_SECOND
            )
        )
    if sensors_list.has_image():
        errors_list.extend(image.validate_image(sensors_list.get_image()))
    if sensors_list.has_light():
        errors_list.extend(
            single.validate_single(sensors_list.get_light(), common.Unit.LUX)
        )
    if sensors_list.has_linear_acceleration():
        errors_list.extend(
            xyz.validate_xyz(
                sensors_list.get_linear_acceleration(),
                common.Unit.METERS_PER_SECOND_SQUARED,
            )
        )
    if sensors_list.has_location():
        errors_list.extend(location.validate_location(sensors_list.get_location()))
    if sensors_list.has_magnetometer():
        errors_list.extend(
            xyz.validate_xyz(sensors_list.get_magnetometer(), common.Unit.MICROTESLA)
        )
    if sensors_list.has_orientation():
        errors_list.extend(
            xyz.validate_xyz(sensors_list.get_orientation(), common.Unit.RADIANS)
        )
    if sensors_list.has_pressure():
        errors_list.extend(
            single.validate_single(sensors_list.get_pressure(), common.Unit.KILOPASCAL)
        )
    if sensors_list.has_proximity():
        errors_list.extend(
            single.validate_single(
                sensors_list.get_proximity(), common.Unit.CENTIMETERS
            )
        )
    if sensors_list.has_relative_humidity():
        errors_list.extend(
            single.validate_single(
                sensors_list.get_relative_humidity(), common.Unit.PERCENTAGE
            )
        )
    if sensors_list.has_rotation_vector():
        errors_list.extend(
            xyz.validate_xyz(sensors_list.get_rotation_vector(), common.Unit.UNITLESS)
        )
    if sensors_list.has_velocity():
        errors_list.extend(
            xyz.validate_xyz(sensors_list.get_velocity(), common.Unit.METERS_PER_SECOND)
        )
    return errors_list
