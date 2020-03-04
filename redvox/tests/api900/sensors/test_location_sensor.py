from redvox.api900 import reader
from redvox.api900.exceptions import ReaderException
from redvox.tests import *

import unittest

from numpy import array, array_equal


class TestLocationSensor(unittest.TestCase):
    def setUp(self):
        self.example_sensor = reader.read_rdvxz_file(test_data("example.rdvxz")).location_sensor()
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
        self.assertAlmostEqual(2.0, self.example_sensor.payload_values_latitude_mean())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_latitude_mean()

    def test_get_payload_values_latitude_median(self):
        self.assertAlmostEqual(2.0, self.example_sensor.payload_values_latitude_median())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_latitude_median()

    def test_get_payload_values_latitude_std(self):
        self.assertAlmostEqual(0.8164965809, self.example_sensor.payload_values_latitude_std())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_latitude_std()

    def test_get_payload_values_longitude_mean(self):
        self.assertAlmostEqual(5.0, self.example_sensor.payload_values_longitude_mean())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_longitude_mean()

    def test_get_payload_values_longitude_median(self):
        self.assertAlmostEqual(5.0, self.example_sensor.payload_values_longitude_median())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_longitude_median()

    def test_get_payload_values_longitude_std(self):
        self.assertAlmostEqual(0.8164965809, self.example_sensor.payload_values_longitude_std())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_longitude_std()

    def test_get_payload_values_altitude_mean(self):
        self.assertAlmostEqual(8.0, self.example_sensor.payload_values_altitude_mean())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_altitude_mean()

    def test_get_payload_values_altitude_median(self):
        self.assertAlmostEqual(8.0, self.example_sensor.payload_values_altitude_median())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_altitude_median()

    def test_get_payload_values_altitude_std(self):
        self.assertAlmostEqual(0.8164965809, self.example_sensor.payload_values_altitude_std())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_altitude_std()

    def test_get_payload_values_speed_mean(self):
        self.assertAlmostEqual(11.0, self.example_sensor.payload_values_speed_mean())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_speed_mean()

    def test_get_payload_values_speed_median(self):
        self.assertAlmostEqual(11.0, self.example_sensor.payload_values_speed_median())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_speed_median()

    def test_get_payload_values_speed_std(self):
        self.assertAlmostEqual(0.8164965809, self.example_sensor.payload_values_speed_std())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_speed_std()

    def test_get_payload_values_accuracy_mean(self):
        self.assertAlmostEqual(14.0, self.example_sensor.payload_values_accuracy_mean())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_accuracy_mean()

    def test_get_payload_values_accuracy_median(self):
        self.assertAlmostEqual(14.0, self.example_sensor.payload_values_accuracy_median())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_accuracy_median()


    def test_get_payload_values_accuracy_std(self):
        self.assertAlmostEqual(0.8164965809, self.example_sensor.payload_values_accuracy_std())

        with self.assertRaises(ReaderException):
            self.empty_sensor.payload_values_accuracy_std()

