from redvox.api900 import reader
from redvox.api900.exceptions import ReaderException
from redvox.tests import *

import unittest

from numpy import array, array_equal


class TestTimeSynchronizationSensor(unittest.TestCase):
    def setUp(self):
        self.example_packet = reader.read_rdvxz_file(test_data("example.rdvxz"))
        self.example_sensor = self.example_packet.time_synchronization_sensor()
        self.empty_sensor = reader.TimeSynchronizationSensor()

    def test_get_payload_values(self):
        self.assertTrue(array_equal([-10, 0, 10, 20, 15, -6, 0], self.example_sensor.payload_values()))
        self.assertTrue(array_equal([], self.empty_sensor.payload_values()))

    def test_set_payload_values(self):
        self.example_sensor.set_payload_values([1, 2, 3])
        self.empty_sensor.set_payload_values(array([1, 2, 3]))
        self.assertTrue(array_equal([1, 2, 3], self.example_sensor.payload_values()))
        self.assertTrue(array_equal([1, 2, 3], self.empty_sensor.payload_values()))

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
        other_sensor = self.example_packet.clone().time_synchronization_sensor()
        self.assertEqual(self.example_sensor, other_sensor)
        other_sensor.set_payload_values([1])
        self.assertNotEqual(self.example_sensor, other_sensor)

    def test_diff(self):
        other_sensor = self.example_packet.clone().time_synchronization_sensor()
        self.assertEqual([], self.example_sensor.diff(other_sensor))
        other_sensor.set_payload_values([1])
        self.assertEqual(['[-10   0  10  20  15  -6   0] != [1]'], self.example_sensor.diff(other_sensor))
