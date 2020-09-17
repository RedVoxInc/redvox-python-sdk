import os
import numpy as np
import unittest
import redvox.api1000.wrapped_redvox_packet.sensors.image as image
import redvox.tests as test_utils


class TestImage(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_image_sensor: image.Image = image.Image.new()
        self.non_empty_image_sensor: image.Image = image.Image.new()
        with open(test_utils.test_data('redvox_logo.png'), "rb") as image_in:
            data_as_bytes: bytes = image_in.read()
            self.non_empty_image_sensor.set_samples([data_as_bytes, data_as_bytes])
        self.non_empty_image_sensor.set_image_codec(image.ImageCodec.PNG)
        self.non_empty_image_sensor.get_timestamps().set_default_unit()
        self.non_empty_image_sensor.get_timestamps().set_timestamps(np.array([1000, 2000]), True)

    def test_append_value(self):
        with open(test_utils.test_data('redvox_logo.png'), "rb") as image_in:
            data_as_bytes: bytes = image_in.read()
            self.non_empty_image_sensor.append_value(data_as_bytes)
        self.assertEqual(self.non_empty_image_sensor.get_num_images(), 3)

    # def test_write_image(self):
    #     self.non_empty_image_sensor.write_image(0, out_file="redvox_logo_out")
    #     with open(test_utils.test_data('redvox_logo.png'), "rb") \
    #             as image_in:
    #         in_bytes: bytes = image_in.read()
    #         with open(test_utils.test_data('redvox_logo_out.png'), "rb") \
    #                 as image_out:
    #             out_bytes: bytes = image_out.read()
    #             self.assertEqual(in_bytes, out_bytes)
    #     os.remove(test_utils.test_data('redvox_logo_out.png'))

    def test_validate_image(self):
        error_list = image.validate_image(self.non_empty_image_sensor)
        self.assertEqual(error_list, [])
        error_list = image.validate_image(self.empty_image_sensor)
        self.assertNotEqual(error_list, [])
