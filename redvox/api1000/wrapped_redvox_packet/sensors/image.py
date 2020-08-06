import enum
import redvox.api1000.common.generic
import redvox.api1000.common.common as common
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2

from redvox.api1000.common.decorators import wrap_enum
from redvox.api1000.common.typing import check_type
from typing import List


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

    def write_image(self, out_file: str, index: int = 0):
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
        out_file = out_file + "." + self.get_image_codec().name.lower()
        with open(out_file, 'wb') as image_out:
            data_as_bytes: bytes = self.get_samples()[index]
            image_out.write(data_as_bytes)


def validate_image(image_sensor: Image) -> List[str]:
    errors_list = common.validate_timing_payload(image_sensor.get_timestamps())
    if image_sensor.get_image_codec() not in ImageCodec.__members__.values():
        errors_list.append("Image sensor image codec is unknown")
    return errors_list
