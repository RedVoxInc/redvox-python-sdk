from redvox.api900 import reader
from redvox.tests import *
from redvox.tests import *

import unittest

from numpy import array, array_equal


class TestUnevenlySampledSensor(unittest.TestCase):
    def setUp(self):
        self.example_packet = reader.read_rdvxz_file(test_data("example.rdvxz"))
        self.example_sensor = self.example_packet.barometer_sensor()
        self.empty_sensor = reader.UnevenlySampledSensor()

    def test_get_sensor_name(self):
        self.assertEqual("example_barometer", self.example_sensor.sensor_name())
        self.assertEqual("", self.empty_sensor.sensor_name())

    def test_set_sensor_name(self):
        self.assertEqual("foo", self.example_sensor.set_sensor_name("foo").sensor_name())
        self.assertEqual("foo", self.empty_sensor.set_sensor_name("foo").sensor_name())

    def test_get_timestamps_microseconds_utc(self):
        self.assertTrue(array_equal([0, 5, 11, 15, 22, 27, 31], self.example_sensor.timestamps_microseconds_utc()))
        self.assertTrue(array_equal([], self.empty_sensor.timestamps_microseconds_utc()))

    def test_set_timestamps_microseconds_utc(self):
        self.example_sensor.set_timestamps_microseconds_utc([1, 2, 3])
        self.empty_sensor.set_timestamps_microseconds_utc([1, 2, 3])
        self.assertTrue(array_equal([1, 2, 3], self.example_sensor.timestamps_microseconds_utc()))
        self.assertTrue(array_equal([1, 2, 3], self.empty_sensor.timestamps_microseconds_utc()))
        self.example_sensor.set_timestamps_microseconds_utc(array([1, 2, 3]))
        self.empty_sensor.set_timestamps_microseconds_utc(array([1, 2, 3]))
        self.assertTrue(array_equal([1, 2, 3], self.example_sensor.timestamps_microseconds_utc()))
        self.assertTrue(array_equal([1, 2, 3], self.empty_sensor.timestamps_microseconds_utc()))

    def test_set_timestamps_microseconds_utc_empty(self):
        self.example_sensor.set_timestamps_microseconds_utc([])
        self.empty_sensor.set_timestamps_microseconds_utc([])
        self.assertTrue(array_equal([], self.example_sensor.timestamps_microseconds_utc()))
        self.assertTrue(array_equal([], self.empty_sensor.timestamps_microseconds_utc()))

    def test_get_sample_interval_mean(self):
        self.assertAlmostEqual(5.1666666666667, self.example_sensor.sample_interval_mean())
        self.assertAlmostEqual(0, self.empty_sensor.sample_interval_mean())

    def test_get_sample_interval_median(self):
        self.assertAlmostEqual(5, self.example_sensor.sample_interval_median())
        self.assertAlmostEqual(0, self.empty_sensor.sample_interval_median())

    def test_get_sample_interval_std(self):
        self.assertAlmostEqual(1.067187373, self.example_sensor.sample_interval_std())
        self.assertAlmostEqual(0, self.empty_sensor.sample_interval_std())

    def test_get_metadata(self):
        self.assertEqual([], self.example_sensor.metadata())
        self.assertEqual([], self.empty_sensor.metadata())

    def test_set_metadata(self):
        self.assertEqual(["a", "b"], self.example_sensor.set_metadata(["a", "b"]).metadata())
        self.assertEqual(["a", "b"], self.empty_sensor.set_metadata(["a", "b"]).metadata())

    def test_get_metadata_as_dict(self):
        self.assertEqual(0, len(self.example_sensor.metadata_as_dict()))
        self.assertEqual(0, len(self.empty_sensor.metadata_as_dict()))

    def test_set_metadata_as_dict(self):
        self.assertEqual("b", self.example_sensor.set_metadata_as_dict({"a": "b"}).metadata_as_dict()["a"])
        self.assertEqual("b", self.empty_sensor.set_metadata_as_dict({"a": "b"}).metadata_as_dict()["a"])

    def test_eq(self):
        other_sensor = self.example_packet.clone().barometer_sensor()
        self.assertEqual(self.example_sensor, other_sensor)
        other_sensor.set_sensor_name("foo")
        self.assertNotEqual(self.example_sensor, other_sensor)

    def test_diff(self):
        other_sensor = self.example_packet.clone().barometer_sensor()
        self.assertEqual([], self.example_sensor.diff(other_sensor))
        other_sensor.set_sensor_name("foo")
        self.assertEqual(["example_barometer != foo"], self.example_sensor.diff(other_sensor))
