from redvox.api900 import reader
from redvox.api900.reader import ReaderException
from redvox.tests.utils import *

import unittest

from numpy import array, array_equal


class TestLocationSensor(unittest.TestCase):
    def setUp(self):
        self.example_sensor = reader.read_rdvxz_file(test_data("example.rdvxz")).location_channel()
        self.empty_sensor = reader.LocationSensor()

    def test_set_payload_values(self):
        self.example_sensor.set_payload_values(
            [1.0, 1.0, 1.0],
            array([2.0, 2.0, 2.0]),
            [3.0, 3.0, 3.0],
            [4.0, 4.0, 4.0],
            [5.0, 5.0, 5.0])

        self.assertTrue(array_equal([1.0, 1.0, 1.0], self.example_sensor.payload_values_latitude()))
        self.assertTrue(array_equal([2.0, 2.0, 2.0], self.example_sensor.payload_values_longitude()))
        self.assertTrue(array_equal([3.0, 3.0, 3.0], self.example_sensor.payload_values_altitude()))
        self.assertTrue(array_equal([4.0, 4.0, 4.0], self.example_sensor.payload_values_speed()))
        self.assertTrue(array_equal([5.0, 5.0, 5.0], self.example_sensor.payload_values_accuracy()))

    def test_set_payload_values_bad(self):
        with self.assertRaises(ReaderException):
            self.example_sensor.set_payload_values(
                [1.0, 1.0, 1.0],
                [2.0, 2.0],
                [3.0, 3.0, 3.0],
                [4.0, 4.0, 4.0],
                [5.0, 5.0, 5.0])

    def test_get_payload_values_latitude_mean(self):
        pass

    def test_get_payload_values_latitude_median(self):
        pass

    def test_get_payload_values_latitude_std(self):
        pass

    def test_get_payload_values_longitude_mean(self):
        pass

    def test_get_payload_values_longitude_median(self):
        pass

    def test_get_payload_values_longitude_std(self):
        pass

    def test_get_payload_values_altitude_mean(self):
        pass

    def test_get_payload_values_altitude_median(self):
        pass

    def test_get_payload_values_altitude_std(self):
        pass

    def test_get_payload_values_speed_mean(self):
        pass

    def test_get_payload_values_speed_median(self):
        pass

    def test_get_payload_values_speed_std(self):
        pass

    def test_get_payload_values_accuracy_mean(self):
        pass

    def test_get_payload_values_accuracy_median(self):
        pass

    def test_get_payload_values_accuracy_std(self):
        pass
