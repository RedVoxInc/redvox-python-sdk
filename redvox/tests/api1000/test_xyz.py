import unittest
import numpy as np
import redvox.api1000.common.common as common
import redvox.api1000.wrapped_redvox_packet.sensors.xyz as xyz


class TestXyz(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_xyz_sensor: xyz.Xyz = xyz.Xyz.new()
        self.non_empty_xyz_sensor: xyz.Xyz = xyz.Xyz.new()
        self.non_empty_xyz_sensor.set_sensor_description("Xyzometer")
        self.non_empty_xyz_sensor.get_timestamps().set_default_unit()
        self.non_empty_xyz_sensor.get_timestamps().set_timestamps(np.array([1000, 2000, 3500, 5000]), True)
        self.non_empty_xyz_sensor.get_x_samples().set_unit(common.Unit.METERS_PER_SECOND_SQUARED)
        self.non_empty_xyz_sensor.get_x_samples().set_values(np.array([0, 1, 2, 3]), True)
        self.non_empty_xyz_sensor.get_y_samples().set_unit(common.Unit.METERS_PER_SECOND_SQUARED)
        self.non_empty_xyz_sensor.get_y_samples().set_values(np.array([3, 2, 1, 0]), True)
        self.non_empty_xyz_sensor.get_z_samples().set_unit(common.Unit.METERS_PER_SECOND_SQUARED)
        self.non_empty_xyz_sensor.get_z_samples().set_values(np.array([0, 1, 2, 3]), True)

    def test_validate_xyz(self):
        error_list = xyz.validate_xyz(self.non_empty_xyz_sensor)
        self.assertEqual(error_list, [])
        error_list = xyz.validate_xyz(self.empty_xyz_sensor)
        self.assertNotEqual(error_list, [])
