import unittest
import numpy as np
import redvox.api1000.common.common as common
import redvox.api1000.wrapped_redvox_packet.sensors.location as location


class TestLocation(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_location_sensor: location.Location = location.Location.new()
        self.non_empty_location_sensor: location.Location = location.Location.new()
        self.non_empty_location_sensor.get_timestamps().set_default_unit()
        self.non_empty_location_sensor.get_timestamps().set_timestamps(np.array([1000, 2000, 3500, 5000]), True)
        self.non_empty_location_sensor.get_latitude_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        self.non_empty_location_sensor.get_latitude_samples().set_values(np.array([0, 1, 1, 0]), True)
        self.non_empty_location_sensor.get_longitude_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        self.non_empty_location_sensor.get_longitude_samples().set_values(np.array([1, 1, 0, 0]), True)
        self.non_empty_location_sensor.get_altitude_samples().set_unit(common.Unit.METERS)
        self.non_empty_location_sensor.get_altitude_samples().set_values(np.array([0, 1, 2, 3]), True)
        self.non_empty_location_sensor.get_speed_samples().set_unit(common.Unit.METERS_PER_SECOND)
        self.non_empty_location_sensor.get_speed_samples().set_values(np.array([0, 0, 1, 0]), True)
        self.non_empty_location_sensor.get_bearing_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        self.non_empty_location_sensor.get_bearing_samples().set_values(np.array([0, 90, 180, 270]), True)
        self.non_empty_location_sensor.get_horizontal_accuracy_samples().set_unit(common.Unit.METERS)
        self.non_empty_location_sensor.get_horizontal_accuracy_samples().set_values(np.array([10, 10, 10, 10]), True)
        self.non_empty_location_sensor.get_vertical_accuracy_samples().set_unit(common.Unit.METERS)
        self.non_empty_location_sensor.get_vertical_accuracy_samples().set_values(np.array([10, 10, 10, 10]), True)
        self.non_empty_location_sensor.get_speed_accuracy_samples().set_unit(common.Unit.METERS_PER_SECOND)
        self.non_empty_location_sensor.get_speed_accuracy_samples().set_values(np.array([10, 10, 10, 10]), True)
        self.non_empty_location_sensor.get_bearing_accuracy_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        self.non_empty_location_sensor.get_bearing_accuracy_samples().set_values(np.array([10, 10, 10, 10]), True)
        self.non_empty_location_sensor.get_overall_best_location().get_latitude_longitude_timestamp().set_mach(1.0)
        self.non_empty_location_sensor.get_overall_best_location().get_latitude_longitude_timestamp().set_gps(2.0)

    def test_get_overall_best_location(self):
        self.assertEqual(2.0,
                         self.non_empty_location_sensor.get_overall_best_location().
                         get_latitude_longitude_timestamp().get_gps())

    def test_validate_location(self):
        error_list = location.validate_location(self.non_empty_location_sensor)
        self.assertEqual(error_list, [])
        error_list = location.validate_location(self.empty_location_sensor)
        self.assertNotEqual(error_list, [])
