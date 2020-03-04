from redvox.api900 import reader
from redvox.tests import *

import unittest


class TestEvenlySampledSensor(unittest.TestCase):
    def setUp(self):
        self.example_packet = reader.read_rdvxz_file(test_data("example.rdvxz"))
        self.example_sensor = self.example_packet.microphone_sensor()
        self.empty_sensor = reader.EvenlySampledSensor()

    def test_get_sensor_name(self):
        self.assertEqual("example_mic", self.example_sensor.sensor_name())
        self.assertEqual("", self.empty_sensor.sensor_name())

    def test_set_sensor_name(self):
        self.assertEqual("foo", self.example_sensor.set_sensor_name("foo").sensor_name())
        self.assertEqual("foo", self.empty_sensor.set_sensor_name("foo").sensor_name())

    def test_get_sample_rate_hz(self):
        self.assertAlmostEqual(80.0, self.example_sensor.sample_rate_hz())
        self.assertAlmostEqual(0.0, self.empty_sensor.sample_rate_hz())

    def test_set_sample_rate_hz(self):
        self.assertAlmostEqual(100.0, self.example_sensor.set_sample_rate_hz(100.0).sample_rate_hz())
        self.assertAlmostEqual(100.0, self.empty_sensor.set_sample_rate_hz(100.0).sample_rate_hz())

    def test_get_first_sample_timestamp_microseconds_utc(self):
        self.assertEqual(1552075743960137, self.example_sensor.first_sample_timestamp_epoch_microseconds_utc())
        self.assertEqual(0, self.empty_sensor.first_sample_timestamp_epoch_microseconds_utc())

    def test_set_first_sample_timestamp_microseconds_utc(self):
        self.assertEqual(100, self.example_sensor.set_first_sample_timestamp_epoch_microseconds_utc(
            100).first_sample_timestamp_epoch_microseconds_utc())
        self.assertEqual(100, self.empty_sensor.set_first_sample_timestamp_epoch_microseconds_utc(
            100).first_sample_timestamp_epoch_microseconds_utc())

    def test_get_metadata(self):
        self.assertEqual(["foo", "bar"], self.example_sensor.metadata())
        self.assertEqual([], self.empty_sensor.metadata())

    def test_set_metadata(self):
        self.assertEqual(["a", "b"], self.example_sensor.set_metadata(["a", "b"]).metadata())
        self.assertEqual(["a", "b"], self.empty_sensor.set_metadata(["a", "b"]).metadata())

    def test_get_metadata_as_dict(self):
        self.assertEqual("bar", self.example_sensor.metadata_as_dict()["foo"])
        self.assertEqual(0, len(self.empty_sensor.metadata_as_dict()))

    def test_set_metadata_as_dict(self):
        self.assertEqual("b", self.example_sensor.set_metadata_as_dict({"a": "b"}).metadata_as_dict()["a"])
        self.assertEqual("b", self.empty_sensor.set_metadata_as_dict({"a": "b"}).metadata_as_dict()["a"])

    def test_eq(self):
        other_sensor = self.example_packet.clone().microphone_sensor()
        self.assertEqual(self.example_sensor, other_sensor)
        other_sensor.set_sensor_name("foo")
        self.assertNotEqual(self.example_sensor, other_sensor)

    def test_diff(self):
        other_sensor = self.example_packet.clone().microphone_sensor()
        self.assertEqual([], self.example_sensor.diff(other_sensor))
        other_sensor.set_sensor_name("foo")
        self.assertEqual(["example_mic != foo"], self.example_sensor.diff(other_sensor))
