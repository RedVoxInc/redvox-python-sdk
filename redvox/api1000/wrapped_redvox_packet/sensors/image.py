"""
This module provides functionality for working with API M image sensors.
"""

import enum
import os.path
from typing import List, Optional

import redvox.api1000.common.common as common
from redvox.api1000.common.decorators import wrap_enum
import redvox.api1000.common.generic
from redvox.api1000.common.typing import check_type
from redvox.api1000.errors import ApiMImageChannelError
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2


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


class Image(
    redvox.api1000.common.generic.ProtoBase[
        redvox_api_m_pb2.RedvoxPacketM.Sensors.Image
    ]
):
    """
    This class encapsulates metadata and data associated with the image sensor.
    """

    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.Image):
        super().__init__(proto)
        self._timestamps: common.TimingPayload = common.TimingPayload(proto.timestamps)

    @staticmethod
    def new() -> "Image":
        """
        :return: A new, empty Image sensor instance
        """
        return Image(redvox_api_m_pb2.RedvoxPacketM.Sensors.Image())

    def get_image_codec(self) -> ImageCodec:
        """
        :return: Returns the codec that was used to store the images.
        """
        # noinspection Mypy
        # pylint: disable=E1101
        return ImageCodec.from_proto(self._proto.image_codec)

    def get_file_ext(self) -> str:
        """
        :return: The file extension for the given codec.
        """
        return self.get_image_codec().name.lower()

    def set_image_codec(self, codec: ImageCodec) -> "Image":
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

    def set_sensor_description(self, sensor_description: str) -> "Image":
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

    def set_timestamps(self, timestamps: common.TimingPayload) -> "Image":
        """
        Sets the timestamps.
        :param timestamps: Timestamps to set.
        :return: A modified instance of self.
        """
        check_type(timestamps, [common.TimingPayload])
        self.get_proto().timestamps.CopyFrom(timestamps.get_proto())
        self._timestamps = common.TimingPayload(self.get_proto().timestamps)
        return self

    def get_samples(self) -> List[bytes]:
        """
        :return: Returns each image as collection of bytes.
        """
        return list(self.get_proto().samples)

    def set_samples(self, images: List[bytes]) -> "Image":
        """
        Set images.
        :param images: List of bytes objects representing each image.
        :return: A modified instance of self
        """
        # check_type(images, [List[bytes]])
        self._proto.samples[:] = images
        return self

    def append_value(self, image: bytes) -> "Image":
        """
        Appends a single image to this sensors list of images.
        :param image: Image to append as serialized bytes.
        :return: A modified instance of self
        """
        check_type(image, [bytes])
        self._proto.samples.append(image)
        return self

    def append_values(self, images: List[bytes]) -> "Image":
        """
        Appends multiple images to this sensor's image payload.
        :param images: Images to append as a list of bytes objects.
        :return: A modified instance of self
        """
        check_type(images, [List])
        self._proto.samples.extend(list(images))
        return self

    def clear_values(self) -> "Image":
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

    def write_image(
        self, index: int, base_dir: str = ".", out_file: Optional[str] = None
    ) -> str:
        """
        Writes an image to disk.
        :param base_dir: Base directory to write image to (default: ".")
        :param out_file: Optional file name (sans extension) (default: timestamp of image)
        :param index: Index of image to be written.
        :return: Path of written file.
        """
        if index < 0 or index >= self.get_num_images():
            raise ApiMImageChannelError(
                f"Index={index} must be > 0 and < {self.get_num_images()}"
            )

        ext: str = self.get_file_ext()
        base_name: str = (
            str(int(self._timestamps.get_timestamps()[index]))
            if out_file is None
            else out_file
        )
        file_name: str = f"{base_name}.{ext}"
        file_path: str = os.path.join(base_dir, file_name)

        with open(file_path, "wb") as image_out:
            img_bytes: bytes = self.get_samples()[index]
            image_out.write(img_bytes)

        return file_path

    def write_images(
        self, indices: Optional[List[int]] = None, base_dir: str = "."
    ) -> List[str]:
        """
        Write multiple images to disk.
        :param base_dir: Base directory to write images to (default: ".").
        :param indices: Optional list of indices for images to write. If this is None, all images will be written.
        :return: List of written file paths.
        """

        indices = (
            indices if indices is not None else list(range(0, self.get_num_images()))
        )
        return list(map(lambda i: self.write_image(i, base_dir), indices))

    def gallery(self):
        """
        Opens a simple image gallery for viewing images in packet
        """
        try:
            import redvox.api1000.gui.image_viewer as image_viewer
            image_viewer.start_gui(self)
        except ImportError:
            import warnings
            warnings.warn("GUI dependencies are not installed. Install the 'GUI' extra to enable this functionality.")


def validate_image(image_sensor: Image) -> List[str]:
    """
    Validates the image sensor.
    :param image_sensor: Image sensor to validate.
    :return: A list of validation errors.
    """
    errors_list = common.validate_timing_payload(image_sensor.get_timestamps())
    if image_sensor.get_image_codec() not in ImageCodec.__members__.values():
        errors_list.append("Image sensor image codec is unknown")
    return errors_list
