import unittest
import numpy as np
import redvox.api1000.common.common as common
import redvox.api1000.wrapped_redvox_packet.sensors.single as single


class TestSingle(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_single_sensor: single.Single = single.Single.new()
        self.non_empty_single_sensor: single.Single = single.Single.new()
        self.non_empty_single_sensor.set_sensor_description("Barometer")
        self.non_empty_single_sensor.get_timestamps().set_default_unit()
        self.non_empty_single_sensor.get_timestamps().set_timestamps(np.array([1000, 2000, 3500, 5000]), True)
        self.non_empty_single_sensor.get_samples().set_unit(common.Unit.KILOPASCAL)
        self.non_empty_single_sensor.get_samples().set_values(np.array([100, 101, 102, 103]), True)

    def test_validate_single(self):
        error_list = single.validate_single(self.non_empty_single_sensor)
        self.assertEqual(error_list, [])
        error_list = single.validate_single(self.empty_single_sensor)
        self.assertNotEqual(error_list, [])
