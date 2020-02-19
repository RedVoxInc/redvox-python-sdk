from redvox.api900 import reader
from redvox.api900.exceptions import ReaderException
from redvox.tests import *

import unittest

from numpy import array, array_equal


class TestGyroscopeSensor(unittest.TestCase):
    def setUp(self):
        self.example_sensor = reader.read_rdvxz_file(test_data("example.rdvxz")).gyroscope_sensor()
        self.empty_sensor = reader.GyroscopeSensor()

    def test_set_payload_values(self):
        self.example_sensor.set_payload_values([1, 1, 1],
                                               [2, 2, 2],
                                               [3, 3, 3])

        self.empty_sensor.set_payload_values(array([1, 1, 1]),
                                             array([2, 2, 2]),
                                             array([3, 3, 3]))

        self.assertTrue(array_equal([1, 1, 1], self.example_sensor.payload_values_x()))
        self.assertTrue(array_equal([1, 1, 1], self.empty_sensor.payload_values_x()))

        self.assertTrue(array_equal([2, 2, 2], self.example_sensor.payload_values_y()))
        self.assertTrue(array_equal([2, 2, 2], self.empty_sensor.payload_values_y()))

        self.assertTrue(array_equal([3, 3, 3], self.example_sensor.payload_values_z()))
        self.assertTrue(array_equal([3, 3, 3], self.empty_sensor.payload_values_z()))

    def test_set_payload_values_bad_lengths(self):
        with self.assertRaises(ReaderException):
            self.example_sensor.set_payload_values([1, 1, 1], [2, 2], [3, 3, 3])

