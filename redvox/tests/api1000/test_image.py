import os
import numpy as np
import unittest
import redvox.api1000.wrapped_redvox_packet.sensors.image as image


class TestImage(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_image_sensor: image.Image = image.Image.new()
        self.non_empty_image_sensor: image.Image = image.Image.new()
        with open('/home/redvox/Development/redvox-api900-python-reader/redvox/tests/test_data/redvox_logo.png', "rb") \
                as image_in:
            data_as_bytes: bytes = image_in.read()
            self.non_empty_image_sensor.set_samples([data_as_bytes, data_as_bytes])
        self.non_empty_image_sensor.set_image_codec(image.ImageCodec.PNG)
        self.non_empty_image_sensor.get_timestamps().set_default_unit()
        self.non_empty_image_sensor.get_timestamps().set_timestamps(np.array([1000, 2000]), True)

    def test_write_image(self):
        self.non_empty_image_sensor.write_image(
            "/home/redvox/Development/redvox-api900-python-reader/redvox/tests/test_data/redvox_logo_out")
        with open('/home/redvox/Development/redvox-api900-python-reader/redvox/tests/test_data/redvox_logo.png', "rb") \
                as image_in:
            in_bytes: bytes = image_in.read()
            with open('/home/redvox/Development/redvox-api900-python-reader/redvox/tests/test_data/redvox_logo_out.png', "rb") \
                    as image_out:
                out_bytes: bytes = image_out.read()
                self.assertEqual(in_bytes, out_bytes)
        os.remove('/home/redvox/Development/redvox-api900-python-reader/redvox/tests/test_data/redvox_logo_out.png')

    def test_validate_image(self):
        error_list = image.validate_image(self.non_empty_image_sensor)
        self.assertEqual(error_list, [])
        error_list = image.validate_image(self.empty_image_sensor)
        self.assertNotEqual(error_list, [])
