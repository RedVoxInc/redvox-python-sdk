import unittest
import numpy as np
import redvox.api1000.common.common as common
import redvox.api1000.wrapped_redvox_packet.sensors.location as loc


class TestLocation(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_loc_sensor: loc.Location = loc.Location.new()
        self.no_best_loc_sensor: loc.Location = loc.Location.new()
        self.no_best_loc_sensor.get_timestamps().set_default_unit()
        self.no_best_loc_sensor.get_timestamps().set_timestamps(np.array([1000, 2000, 3500, 5000]), True)
        self.no_best_loc_sensor.get_latitude_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        self.no_best_loc_sensor.get_latitude_samples().set_values(np.array([0, 1, 1, 0]), True)
        self.no_best_loc_sensor.get_longitude_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        self.no_best_loc_sensor.get_longitude_samples().set_values(np.array([1, 1, 0, 0]), True)
        self.no_best_loc_sensor.get_altitude_samples().set_unit(common.Unit.METERS)
        self.no_best_loc_sensor.get_altitude_samples().set_values(np.array([0, 1, 2, 3]), True)
        self.no_best_loc_sensor.get_speed_samples().set_unit(common.Unit.METERS_PER_SECOND)
        self.no_best_loc_sensor.get_speed_samples().set_values(np.array([0, 0, 1, 0]), True)
        self.no_best_loc_sensor.get_bearing_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        self.no_best_loc_sensor.get_bearing_samples().set_values(np.array([0, 90, 180, 270]), True)
        self.no_best_loc_sensor.get_horizontal_accuracy_samples().set_unit(common.Unit.METERS)
        self.no_best_loc_sensor.get_horizontal_accuracy_samples().set_values(np.array([10, 10, 10, 10]), True)
        self.no_best_loc_sensor.get_vertical_accuracy_samples().set_unit(common.Unit.METERS)
        self.no_best_loc_sensor.get_vertical_accuracy_samples().set_values(np.array([10, 10, 10, 10]), True)
        self.no_best_loc_sensor.get_speed_accuracy_samples().set_unit(common.Unit.METERS_PER_SECOND)
        self.no_best_loc_sensor.get_speed_accuracy_samples().set_values(np.array([10, 10, 10, 10]), True)
        self.no_best_loc_sensor.get_bearing_accuracy_samples().set_unit(common.Unit.DECIMAL_DEGREES)
        self.no_best_loc_sensor.get_bearing_accuracy_samples().set_values(np.array([10, 10, 10, 10]), True)
        self.no_best_loc_sensor.get_location_providers().set_values([loc.LocationProvider.USER,
                                                                     loc.LocationProvider.USER,
                                                                     loc.LocationProvider.USER,
                                                                     loc.LocationProvider.USER])
        self.only_best_loc_sensor: loc.Location = loc.Location.new()
        self.only_best_loc_sensor.set_overall_best_location(loc.BestLocation.new())
        self.only_best_loc_sensor.get_overall_best_location().get_latitude_longitude_timestamp().set_default_unit()
        self.only_best_loc_sensor.get_overall_best_location().get_latitude_longitude_timestamp().set_mach(1.0)
        self.only_best_loc_sensor.get_overall_best_location().get_latitude_longitude_timestamp().set_gps(2.0)
        self.only_best_loc_sensor.get_overall_best_location().set_latitude_longitude_unit(common.Unit.DECIMAL_DEGREES)
        self.only_best_loc_sensor.get_overall_best_location().set_latitude(1.0)
        self.only_best_loc_sensor.get_overall_best_location().set_longitude(1.0)

        self.non_empty_loc_sensor: loc.Location = self.no_best_loc_sensor
        self.non_empty_loc_sensor.set_overall_best_location(self.only_best_loc_sensor.get_overall_best_location())

    def test_get_overall_best_location(self):
        self.assertEqual(2.0,
                         self.only_best_loc_sensor.get_overall_best_location().
                         get_latitude_longitude_timestamp().get_gps())

    def test_validate_location(self):
        error_list = loc.validate_location(self.non_empty_loc_sensor)
        self.assertEqual(error_list, [])
        error_list = loc.validate_location(self.no_best_loc_sensor)
        self.assertEqual(error_list, [])
        error_list = loc.validate_location(self.only_best_loc_sensor)
        self.assertEqual(error_list, [])
        error_list = loc.validate_location(self.empty_loc_sensor)
        self.assertEqual(error_list, [])

    def test_invalidated_locations(self):
        self.non_empty_loc_sensor.get_latitude_samples().set_values(np.array([200, 1000, -8572, np.nan]), True)
        error_list = loc.validate_location(self.non_empty_loc_sensor)
        self.assertTrue(len(error_list) > 0)
        self.only_best_loc_sensor.get_overall_best_location().set_latitude_longitude_unit(common.Unit.METERS)
        error_list = loc.validate_location(self.only_best_loc_sensor)
        self.assertTrue(len(error_list) > 0)
