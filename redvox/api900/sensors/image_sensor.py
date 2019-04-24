"""
This module contains classes and methods for working with image sensors.
"""

import typing

import numpy

import redvox.api900.lib.api900_pb2 as api900_pb2
from redvox.api900.sensors.unevenly_sampled_channel import UnevenlySampledChannel
from redvox.api900.sensors.unevenly_sampled_sensor import UnevenlySampledSensor


class ImageSensor(UnevenlySampledSensor):
    """High-level wrapper around image channels."""

    def __init__(self, unevenly_sampled_channel: UnevenlySampledChannel = None):
        """
        Initializes this ImageSensor.
        :param unevenly_sampled_channel: The image channel.
        """
        super().__init__(unevenly_sampled_channel)
        self._unevenly_sampled_channel.set_channel_types([api900_pb2.IMAGE])

        self._image_offsets: typing.List[int] = self.parse_offsets()
        """A list of image byte offsets into the payload of this sensor channel."""

    def parse_offsets(self) -> typing.List[int]:
        """
        Parses the metadata of this channel to extract the image byte offsets into the payload.
        :return: A list of image byte offsets.
        """
        meta = self.metadata_as_dict()
        if "images" in meta:
            offsets_line = meta["images"].replace("[", "").replace("]", "")
            try:
                return list(map(int, offsets_line.split(",")))
            except ValueError:
                return []
        else:
            return []

    def image_offsets(self) -> typing.List[int]:
        """
        Returns the byte offsets for each image in the payload.
        :return: The byte offsets for each image in the payload.
        """
        return self._image_offsets

    def payload_values(self) -> numpy.ndarray:
        """
        Returns a numpy ndarray of uint8s representing this sensor's payload. This byte blob may contain multiple
        images. The byte offset of each image should be stored in this channels metadata as images="[offset_0,
        offset_1, ..., offset_n]".
        :return: A numpy ndarray of floats representing this sensor's payload.
        """
        return self._unevenly_sampled_channel.get_payload(api900_pb2.IMAGE)

    def num_images(self) -> int:
        """
        Returns the number of images in this packet's image channel.
        :return: The number of images in this packet's image channel.
        """
        return len(self._image_offsets)

    def get_image_bytes(self, idx: int) -> numpy.ndarray:
        """
        Return the bytes associated with an image at this channel's given image index.
        :param idx: The image from this channel to retrieve (starting from 0).
        :return: A numpy array of uint8s representing the bytes of a selected image.
        """
        if idx < 0 or idx >= self.num_images():
            raise RuntimeError("idx must be between 0 and the total number of images available in this packet %s" %
                               str(self.num_images()))

        if idx == self.num_images() - 1:
            return self.payload_values()[self._image_offsets[idx]:]

        return self.payload_values()[self._image_offsets[idx]:self._image_offsets[idx + 1]]

    def write_image_to_file(self, idx: int, path: str):
        """
        Writes an image to a file with a given file name.
        :param idx: The index of the image in this channel (starting at 0).
        :param path: The full path and file name to save this image as.
        """
        self.get_image_bytes(idx).tofile(path)

    def default_filename(self, idx: int) -> str:
        """
        Returns the default file name for the image at the given index by using the timestamp of the image.
        :param idx: The index of the image in this channel (starting at 0).
        :return: A default filename of the format timestamp.jpg.
        """
        return "{}.jpg".format(self.timestamps_microseconds_utc()[idx])

    def write_all_images_to_directory(self, directory: str = "."):
        """
        Write all images in this packet to the provided directory using default filenames.
        :param directory: The directory to write the images to.
        """
        for i in range(self.num_images()):
            self.write_image_to_file(i, "{}/{}".format(directory, self.default_filename(i)))

    def get_image_offsets(self) -> typing.List[int]:
        """
        Returns the byte offsets for each image in the payload.
        :return: The byte offsets for each image in the payload.
        """
        return self._image_offsets

    def __str__(self):
        """Provide image information in str of this instance"""
        return "{}\nnum images: {}\nbyte offsets: {}".format(self._unevenly_sampled_channel,
                                                             self.num_images(),
                                                             self._image_offsets)
