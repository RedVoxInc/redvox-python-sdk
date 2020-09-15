import enum
import os.path
import redvox.api1000.common.generic
import redvox.api1000.common.common as common
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2

from redvox.api1000.common.decorators import wrap_enum
from redvox.api1000.common.typing import check_type
from typing import List, Optional

from redvox.api1000.errors import ApiMImageChannelError


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
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.Image):
        super().__init__(proto)
        self._timestamps: common.TimingPayload = common.TimingPayload(proto.timestamps)

    @staticmethod
    def new() -> 'Image':
        return Image(redvox_api_m_pb2.RedvoxPacketM.Sensors.Image())

    def get_image_codec(self) -> ImageCodec:
        return ImageCodec.from_proto(self._proto.image_codec)

    def set_image_codec(self, codec: ImageCodec) -> 'Image':
        check_type(codec, [ImageCodec])
        self._proto.image_codec = codec.into_proto()
        return self

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'Image':
        redvox.api1000.common.typing.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_timestamps(self) -> common.TimingPayload:
        return self._timestamps

    def get_samples(self) -> List[bytes]:
        return list(self.get_proto().samples)

    def set_samples(self, images: List[bytes]) -> 'Image':
        # check_type(images, [List[bytes]])
        self._proto.samples[:] = images
        return self

    def append_value(self, images: bytes) -> 'Image':
        check_type(images, [bytes])
        self._proto.samples.append(images)
        return self

    def append_values(self, images: List[bytes]) -> 'Image':
        check_type(images, [List[bytes]])
        self._proto.samples.extend(list(images))
        return self

    def clear_values(self) -> 'Image':
        self._proto.samples[:] = []
        return self

    def get_num_images(self) -> int:
        return len(self.get_samples())

    def write_image(self,
                    base_dir: str = ".",
                    out_file: Optional[str] = None,
                    index: int = 0) -> str:
        """
        Writes an image to disk.
        :param base_dir: Base directory to write image to (default: ".")
        :param out_file: Optional file name (sans extension) (default: timestamp of image)
        :param index: Index of image to be written.
        :return: Path of written file.
        """
        if index < 0 or index >= self.get_num_images() - 1:
            raise ApiMImageChannelError(f"Index={index} must be > 0 and <= {self.get_num_images() - 1}")

        ext: str = self.get_image_codec().name.lower()
        base_name: str = self._timestamps.get_timestamps()[index] if out_file is None else out_file
        file_name: str = f"{base_name}.{ext}"
        file_path: str = os.path.join(base_dir, file_name)

        with open(file_path, 'wb') as image_out:
            img_bytes: bytes = self.get_samples()[index]
            image_out.write(img_bytes)

        return file_path

    def write_images(self,
                     base_dir: str = ".",
                     indices: Optional[List[int]] = None) -> List[str]:
        """
        Write multiple images to disk.
        :param base_dir: Base directory to write images to (default: ".").
        :param indices: Optional list of indices for images to write. If this is None, all images will be written.
        :return: List of written file paths.
        """

        indices = indices if indices is not None else list(range(0, self.get_num_images()))
        return list(map(lambda i: self.write_image(base_dir, index=i), indices))


def validate_image(image_sensor: Image) -> List[str]:
    errors_list = common.validate_timing_payload(image_sensor.get_timestamps())
    if image_sensor.get_image_codec() not in ImageCodec.__members__.values():
        errors_list.append("Image sensor image codec is unknown")
    return errors_list
