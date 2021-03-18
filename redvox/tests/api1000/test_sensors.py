import unittest
import numpy as np
import redvox.api1000.wrapped_redvox_packet.sensors.sensors as sensor
from redvox.api1000.common.common import Unit


class TestSensor(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_sensors: sensor.Sensors = sensor.Sensors.new()
        self.non_empty_sensors: sensor.Sensors = sensor.Sensors.new()
        self.non_empty_sensors.new_audio()
        self.non_empty_sensors.get_audio().get_samples().set_values(np.array([.1000, .50, .1025], dtype=int))
        self.non_empty_sensors.get_audio().set_sample_rate(80.0)
        self.non_empty_sensors.get_audio().set_first_sample_timestamp(1)
        self.non_empty_sensors.new_location()
        # self.non_empty_sensors.get_location().get_timestamps().set_default_unit()
        self.non_empty_sensors.get_location().get_timestamps().set_timestamps(np.array([1000, 2000, 3500, 5000]), True)
        self.non_empty_sensors.get_location().get_latitude_samples().set_values(np.array([0, 1, 1, 0]), True)
        self.non_empty_sensors.get_location().get_longitude_samples().set_values(np.array([1, 1, 0, 0]), True)
        self.non_empty_sensors.get_location().get_altitude_samples().set_values(np.array([0, 1, 2, 3]), True)
        self.non_empty_sensors.get_location().get_speed_samples().set_values(np.array([0, 0, 1, 0]), True)
        self.non_empty_sensors.get_location().get_bearing_samples().set_values(np.array([0, 90, 180, 270]), True)
        self.non_empty_sensors.get_location().get_horizontal_accuracy_samples().set_values(np.array([10, 10, 10, 10]),
                                                                                           True)
        self.non_empty_sensors.get_location().get_vertical_accuracy_samples().set_values(np.array([10, 10, 10, 10]),
                                                                                         True)
        self.non_empty_sensors.get_location().get_speed_accuracy_samples().set_values(np.array([10, 10, 10, 10]), True)
        self.non_empty_sensors.get_location().get_bearing_accuracy_samples().set_values(np.array([10, 10, 10, 10]),
                                                                                        True)
        self.non_empty_sensors.new_pressure()
        self.non_empty_sensors.get_pressure().set_sensor_description("Barometer")
        self.non_empty_sensors.get_pressure().get_timestamps().set_timestamps(np.array([1000, 2000, 3500, 5000]), True)
        self.non_empty_sensors.get_pressure().get_samples().set_values(np.array([100, 101, 102, 103]), True)
        self.non_empty_sensors.new_gyroscope()
        self.non_empty_sensors.get_gyroscope().set_sensor_description("Gyroscope")
        self.non_empty_sensors.get_gyroscope().get_timestamps().set_timestamps(np.array([1000, 2000, 3500, 5000]), True)
        self.non_empty_sensors.get_gyroscope().get_x_samples().set_values(np.array([0, 1, 2, 3]), True)
        self.non_empty_sensors.get_gyroscope().get_y_samples().set_values(np.array([3, 2, 1, 0]), True)
        self.non_empty_sensors.get_gyroscope().get_z_samples().set_values(np.array([0, 1, 2, 3]), True)

    def test_non_empty_sensor(self):
        self.assertEqual(self.non_empty_sensors.get_location().get_timestamps().get_timestamps()[0], 1000)
        self.assertEqual(self.non_empty_sensors.get_gyroscope().get_x_samples().get_unit(), Unit["RADIANS_PER_SECOND"])
        self.assertEqual(self.non_empty_sensors.get_relative_humidity(), None)
        self.non_empty_sensors.remove_gyroscope()
        self.assertEqual(self.non_empty_sensors.get_gyroscope(), None)
        self.assertFalse(self.non_empty_sensors.validate_velocity())
        self.assertTrue(self.non_empty_sensors.validate_audio())
        self.assertEqual(len(sensor.validate_sensors(self.non_empty_sensors)), 0)

    # todo: location sensors need to have best locations validated
    # def test_validate_sensors(self):
    #     error_list = sensor.validate_sensors(self.non_empty_sensors)
    #     self.assertEqual(error_list, [])
    #     error_list = sensor.validate_sensors(self.empty_sensors)
    #     self.assertNotEqual(error_list, [])
