import unittest
import redvox.api1000.wrapped_redvox_packet.common as common
import redvox.api1000.wrapped_redvox_packet.sensors.image as image


class TestImage(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_image_sensor: image.Image = image.Image.new()
        self.non_empty_image_sensor: image.Image = image.Image.new()
        # todo: add non-empty image initialization

    def test_validate_image(self):
        # todo: add non-empty image validation
        error_list = image.validate_image(self.empty_image_sensor)
        self.assertNotEqual(error_list, [])
