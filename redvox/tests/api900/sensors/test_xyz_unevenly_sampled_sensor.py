from redvox.api900 import reader
from redvox.api900.exceptions import ReaderException
from redvox.tests import *

import unittest

from numpy import array, array_equal


class TestXyzUnevenlySampledSensor(unittest.TestCase):
    def setUp(self):
        self.example_sensor = reader.read_rdvxz_file(test_data("example.rdvxz")).gyroscope_sensor()
        self.empty_sensor = reader.GyroscopeSensor()

    def test_get_payload_values_x(self):
        self.assertTrue(array_equal([1, 2, 3], self.example_sensor.payload_values_x()))
        self.assertTrue(array_equal([], self.empty_sensor.payload_values_x()))

    def test_get_payload_values_y(self):
        self.assertTrue(array_equal([4, 5, 6], self.example_sensor.payload_values_y()))
        self.assertTrue(array_equal([], self.empty_sensor.payload_values_y()))

    def test_get_payload_values_z(self):
        self.assertTrue(array_equal([7, 8, 9], self.example_sensor.payload_values_z()))
        self.assertTrue(array_equal([], self.empty_sensor.payload_values_z()))

    def test_get_payload_values_x_mean(self):
        self.assertAlmostEqual(2.0, self.example_sensor.payload_values_x_mean())

        with self.assertRaises(ReaderException):
            self.assertAlmostEqual(2.0, self.empty_sensor.payload_values_x_mean())

    def test_get_payload_values_x_median(self):
        self.assertAlmostEqual(2, self.example_sensor.payload_values_x_median())

        with self.assertRaises(ReaderException):
            self.assertAlmostEqual(2.0, self.empty_sensor.payload_values_x_median())

    def test_get_payload_values_x_std(self):
        self.assertAlmostEqual(0.8164965809, self.example_sensor.payload_values_x_std())

        with self.assertRaises(ReaderException):
            self.assertAlmostEqual(2.0, self.empty_sensor.payload_values_x_std())

    def test_get_payload_values_y_mean(self):
        self.assertAlmostEqual(5.0, self.example_sensor.payload_values_y_mean())

        with self.assertRaises(ReaderException):
            self.assertAlmostEqual(2.0, self.empty_sensor.payload_values_y_mean())

    def test_get_payload_values_y_median(self):
        self.assertAlmostEqual(5, self.example_sensor.payload_values_y_median())

        with self.assertRaises(ReaderException):
            self.assertAlmostEqual(2.0, self.empty_sensor.payload_values_y_median())

    def test_get_payload_values_y_std(self):
        self.assertAlmostEqual(0.8164965809, self.example_sensor.payload_values_y_std())

        with self.assertRaises(ReaderException):
            self.assertAlmostEqual(2.0, self.empty_sensor.payload_values_y_std())

    def test_get_payload_values_z_mean(self):
        self.assertAlmostEqual(8.0, self.example_sensor.payload_values_z_mean())

        with self.assertRaises(ReaderException):
            self.assertAlmostEqual(2.0, self.empty_sensor.payload_values_z_mean())

    def test_get_payload_values_z_median(self):
        self.assertAlmostEqual(8, self.example_sensor.payload_values_z_median())

        with self.assertRaises(ReaderException):
            self.assertAlmostEqual(2.0, self.empty_sensor.payload_values_z_median())

    def test_get_payload_values_z_std(self):
        self.assertAlmostEqual(0.8164965809, self.example_sensor.payload_values_z_std())

        with self.assertRaises(ReaderException):
            self.assertAlmostEqual(2.0, self.empty_sensor.payload_values_z_std())
