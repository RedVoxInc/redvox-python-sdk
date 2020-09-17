"""
This module provides functionality for working with API M image sensors.
"""

import enum
import redvox.api1000.common.generic
import redvox.api1000.common.common as common
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2

from redvox.api1000.common.decorators import wrap_enum
from redvox.api1000.common.typing import check_type
from typing import List, Optional


# noinspection Mypy
@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.Sensors.Image.ImageCodec)
class ImageCodec(enum.Enum):
    """
    Image Codecs for image data
    """
    UNKNOWN: int = 0
    PNG: int = 1
    JPG: int = 2
    BMP: int = 3


class Image(redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.Sensors.Image]):
    """
    This class encapsulates metadata and data associated with the image sensor.
    """
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.Image):
        super().__init__(proto)
        self._timestamps: common.TimingPayload = common.TimingPayload(proto.timestamps)

    @staticmethod
    def new() -> 'Image':
        """
        :return: A new, empty Image sensor instance
        """
        return Image(redvox_api_m_pb2.RedvoxPacketM.Sensors.Image())

    def get_image_codec(self) -> ImageCodec:
        """
        :return: Returns the codec that was used to store the images.
        """
        # noinspection Mypy
        return ImageCodec.from_proto(self._proto.image_codec)

    def set_image_codec(self, codec: ImageCodec) -> 'Image':
        """
        Sets the codec used to store the images.
        :param codec: Codec to set.
        :return: A modified instance of self
        """
        check_type(codec, [ImageCodec])
        # noinspection Mypy
        self._proto.image_codec = codec.into_proto()
        return self

    def get_sensor_description(self) -> str:
        """
        :return: The image sensor description.
        """
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'Image':
        """
        Sets the image sensor description.
        :param sensor_description: Description to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_timestamps(self) -> common.TimingPayload:
        """
        :return: Timestamp payload which contains a timestamp per image
        """
        return self._timestamps

    def get_samples(self) -> List[bytes]:
        """
        :return: Returns each image as collection of bytes.
        """
        return list(self.get_proto().samples)

    def set_samples(self, images: List[bytes]) -> 'Image':
        """
        Set images.
        :param images: List of bytes objects representing each image.
        :return: A modified instance of self
        """
        # check_type(images, [List[bytes]])
        self._proto.samples[:] = images
        return self

    def append_value(self, image: bytes) -> 'Image':
        """
        Appends a single image to this sensors list of images.
        :param image: Image to append as serialized bytes.
        :return: A modified instance of self
        """
        check_type(image, [bytes])
        self._proto.samples.append(image)
        return self

    def append_values(self, images: List[bytes]) -> 'Image':
        """
        Appends multiple images to this sensor's image payload.
        :param images: Images to append as a list of bytes objects.
        :return: A modified instance of self
        """
        check_type(images, [List[bytes]])
        self._proto.samples.extend(list(images))
        return self

    def clear_values(self) -> 'Image':
        """
        Clears all images from this sensor
        :return: A modified instance of self
        """
        self._proto.samples[:] = []
        return self

    def get_num_images(self) -> int:
        """
        :return: The total number of images stored in this packet
        """
        return len(self.get_samples())

    def write_image(self, out_file: Optional[str] = None, index: int = 0):
        """
        Prints the image at index in the data as out_file.image_codec, where image_codec is defined by the sensor
        :param out_file: the name of the output file
        :param index: the index of the image to print
        """
        # invalid indices get converted to the closest valid index
        if index < 0:
            index = 0
        elif index >= self.get_num_images():
            index = self.get_num_images() - 1
        # append the image codec to the file name
        if out_file is None:
            out_file = str(self._timestamps.get_timestamps()[index])
        out_file = out_file + "." + self.get_image_codec().name.lower()
        with open(out_file, 'wb') as image_out:
            data_as_bytes: bytes = self.get_samples()[index]
            image_out.write(data_as_bytes)


def validate_image(image_sensor: Image) -> List[str]:
    errors_list = common.validate_timing_payload(image_sensor.get_timestamps())
    if image_sensor.get_image_codec() not in ImageCodec.__members__.values():
        errors_list.append("Image sensor image codec is unknown")
    return errors_list
