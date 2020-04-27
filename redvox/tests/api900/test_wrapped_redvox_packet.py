import os
import unittest

from redvox.api900 import reader
from redvox.api900.exceptions import ReaderException
import redvox.api900.migrations as migrations
from redvox.tests import test_data, TEST_DATA_DIR

import numpy


class TestWrappedRedvoxPacket(unittest.TestCase):
    def setUp(self):
        self.example_packet = reader.read_rdvxz_file(test_data("example.rdvxz"))
        self.empty_packet = reader.WrappedRedvoxPacket()

    def tearDown(self):
        pass

    def test_get_api(self):
        self.assertEqual(900, self.example_packet.api())
        self.assertEqual(0, self.empty_packet.api())

    def test_set_api(self):
        self.example_packet.set_api(901)
        self.empty_packet.set_api(901)
        self.assertEqual(901, self.example_packet.api())
        self.assertEqual(901, self.empty_packet.api())

    def test_get_redvox_id(self):
        self.assertEqual("0000000001", self.example_packet.redvox_id())
        self.assertEqual("", self.empty_packet.redvox_id())

    def test_set_redvox_id(self):
        self.example_packet.set_redvox_id("foo")
        self.empty_packet.set_redvox_id("foo")
        self.assertEqual("foo", self.example_packet.redvox_id())
        self.assertEqual("foo", self.empty_packet.redvox_id())

    def test_get_uuid(self):
        self.assertEqual("123456789", self.example_packet.uuid())
        self.assertEqual("", self.empty_packet.uuid())

    def test_set_uuid(self):
        self.example_packet.set_uuid("foo")
        self.empty_packet.set_uuid("foo")
        self.assertEqual("foo", self.example_packet.uuid())
        self.assertEqual("foo", self.empty_packet.uuid())

    def test_get_authenticated_email(self):
        self.assertEqual("foo@bar.baz", self.example_packet.authenticated_email())
        self.assertEqual("", self.empty_packet.authenticated_email())

    def test_set_authenticated_email(self):
        self.example_packet.set_authenticated_email("john.doe@gmail.com")
        self.empty_packet.set_authenticated_email("john.doe@gmail.com")
        self.assertEqual("john.doe@gmail.com", self.example_packet.authenticated_email())
        self.assertEqual("john.doe@gmail.com", self.empty_packet.authenticated_email())

    def test_get_authentication_token(self):
        self.assertEqual("redacted-000000", self.example_packet.authentication_token())
        self.assertEqual("", self.empty_packet.authentication_token())

    def test_set_authentication_token(self):
        self.example_packet.set_authentication_token("foo")
        self.empty_packet.set_authentication_token("foo")
        self.assertEqual("foo", self.example_packet.authentication_token())
        self.assertEqual("foo", self.empty_packet.authentication_token())

    def test_get_firebase_token(self):
        self.assertEqual("example_firebase_token", self.example_packet.firebase_token())
        self.assertEqual("", self.empty_packet.firebase_token())

    def test_set_firebase_token(self):
        self.example_packet.set_firebase_token("foo")
        self.empty_packet.set_firebase_token("foo")
        self.assertEqual("foo", self.example_packet.firebase_token())
        self.assertEqual("foo", self.empty_packet.firebase_token())

    def test_get_battery_level_percent(self):
        self.assertAlmostEqual(77.5, self.example_packet.battery_level_percent())
        self.assertEqual(0.0, self.empty_packet.battery_level_percent())

    def test_set_battery_level_percent(self):
        self.example_packet.set_battery_level_percent(100.0)
        self.empty_packet.set_battery_level_percent(100.0)
        self.assertAlmostEqual(100.0, self.example_packet.battery_level_percent())
        self.assertAlmostEqual(100.0, self.empty_packet.battery_level_percent())

    def test_get_device_temperature_c(self):
        self.assertAlmostEqual(21.100000381469727, self.example_packet.device_temperature_c())
        self.assertEqual(0.0, self.empty_packet.device_temperature_c())

    def test_set_device_temperature_c(self):
        self.example_packet.set_device_temperature_c(100.0)
        self.empty_packet.set_device_temperature_c(100.0)
        self.assertAlmostEqual(100.0, self.example_packet.device_temperature_c())
        self.assertAlmostEqual(100.0, self.empty_packet.device_temperature_c())

    def test_get_is_private(self):
        self.assertTrue(self.example_packet.is_private())
        self.assertFalse(self.empty_packet.is_private())

    def test_set_is_private(self):
        self.example_packet.set_is_private(False)
        self.empty_packet.set_is_private(True)
        self.assertFalse(self.example_packet.is_private())
        self.assertTrue(self.empty_packet.is_private())

    def test_get_is_backfilled(self):
        self.assertFalse(self.example_packet.is_backfilled())
        self.assertFalse(self.empty_packet.is_backfilled())

    def test_set_is_backfilled(self):
        self.example_packet.set_is_backfilled(True)
        self.empty_packet.set_is_backfilled(True)
        self.assertTrue(self.example_packet.is_backfilled())
        self.assertTrue(self.empty_packet.is_backfilled())

    def test_get_is_scrambled(self):
        self.assertFalse(self.example_packet.is_scrambled())
        self.assertFalse(self.empty_packet.is_scrambled())

    def test_set_is_scrambled(self):
        self.example_packet.set_is_scrambled(True)
        self.empty_packet.set_is_scrambled(True)
        self.assertTrue(self.example_packet.is_scrambled())
        self.assertTrue(self.empty_packet.is_scrambled())

    def test_get_device_make(self):
        self.assertEqual("example_make", self.example_packet.device_make())
        self.assertEqual("", self.empty_packet.device_make())

    def test_set_device_make(self):
        self.example_packet.set_device_make("foo")
        self.empty_packet.set_device_make("foo")
        self.assertEqual("foo", self.example_packet.device_make())
        self.assertEqual("foo", self.empty_packet.device_make())

    def test_get_device_model(self):
        self.assertEqual("example_model", self.example_packet.device_model())
        self.assertEqual("", self.empty_packet.device_model())

    def test_set_device_model(self):
        self.example_packet.set_device_model("foo")
        self.empty_packet.set_device_model("foo")
        self.assertEqual("foo", self.example_packet.device_model())
        self.assertEqual("foo", self.empty_packet.device_model())

    def test_get_device_os(self):
        self.assertEqual("Android", self.example_packet.device_os())
        self.assertEqual("", self.empty_packet.device_os())

    def test_set_device_os(self):
        self.example_packet.set_device_os("foo")
        self.empty_packet.set_device_os("foo")
        self.assertEqual("foo", self.example_packet.device_os())
        self.assertEqual("foo", self.empty_packet.device_os())

    def test_get_device_os_version(self):
        self.assertEqual("8.0.0", self.example_packet.device_os_version())
        self.assertEqual("", self.empty_packet.device_os_version())

    def test_set_device_os_version(self):
        self.example_packet.set_device_os_version("foo")
        self.empty_packet.set_device_os_version("foo")
        self.assertEqual("foo", self.example_packet.device_os_version())
        self.assertEqual("foo", self.empty_packet.device_os_version())

    def test_get_app_version(self):
        self.assertEqual("2.4.2", self.example_packet.app_version())
        self.assertEqual("", self.empty_packet.app_version())

    def test_set_app_version(self):
        self.example_packet.set_app_version("foo")
        self.empty_packet.set_app_version("foo")
        self.assertEqual("foo", self.example_packet.app_version())
        self.assertEqual("foo", self.empty_packet.app_version())

    def test_get_acquisition_server(self):
        self.assertEqual("wss://redvox.io/acquisition/v900", self.example_packet.acquisition_server())
        self.assertEqual("", self.empty_packet.acquisition_server())

    def test_set_acquisition_server(self):
        self.example_packet.set_acquisition_server("foo")
        self.empty_packet.set_acquisition_server("foo")
        self.assertEqual("foo", self.example_packet.acquisition_server())
        self.assertEqual("foo", self.empty_packet.acquisition_server())

    def test_get_time_synchronization_server(self):
        self.assertEqual("wss://redvox.io/synch/v2", self.example_packet.time_synchronization_server())
        self.assertEqual("", self.empty_packet.time_synchronization_server())

    def test_set_time_synchronization_server(self):
        self.example_packet.set_time_synchronization_server("foo")
        self.empty_packet.set_time_synchronization_server("foo")
        self.assertEqual("foo", self.example_packet.time_synchronization_server())
        self.assertEqual("foo", self.empty_packet.time_synchronization_server())

    def test_get_authentication_server(self):
        self.assertEqual("https://redvox.io/login/mobile", self.example_packet.authentication_server())
        self.assertEqual("", self.empty_packet.authentication_server())

    def test_set_authentication_server(self):
        self.example_packet.set_authentication_server("foo")
        self.empty_packet.set_authentication_server("foo")
        self.assertEqual("foo", self.example_packet.authentication_server())
        self.assertEqual("foo", self.empty_packet.authentication_server())

    def test_get_app_file_start_timestamp_epoch_microseconds_utc(self):
        self.assertEqual(1552075743960135, self.example_packet.app_file_start_timestamp_epoch_microseconds_utc())
        self.assertEqual(0, self.empty_packet.app_file_start_timestamp_epoch_microseconds_utc())

    def test_set_app_file_start_timestamp_epoch_microseconds_utc(self):
        self.example_packet.set_app_file_start_timestamp_epoch_microseconds_utc(100)
        self.empty_packet.set_app_file_start_timestamp_epoch_microseconds_utc(100)
        self.assertEqual(100, self.example_packet.app_file_start_timestamp_epoch_microseconds_utc())
        self.assertEqual(100, self.empty_packet.app_file_start_timestamp_epoch_microseconds_utc())

    def test_get_app_file_start_timestamp_machine(self):
        self.assertEqual(1552075743960136, self.example_packet.app_file_start_timestamp_machine())
        self.assertEqual(0, self.empty_packet.app_file_start_timestamp_machine())

    def test_set_app_file_start_timestamp_machine(self):
        self.example_packet.set_app_file_start_timestamp_machine(100)
        self.empty_packet.set_app_file_start_timestamp_machine(100)
        self.assertEqual(100, self.example_packet.app_file_start_timestamp_machine())
        self.assertEqual(100, self.empty_packet.app_file_start_timestamp_machine())

    def test_get_server_timestamp_epoch_microseconds_utc(self):
        self.assertEqual(1552075743960139, self.example_packet.server_timestamp_epoch_microseconds_utc())
        self.assertEqual(0, self.empty_packet.server_timestamp_epoch_microseconds_utc())

    def test_set_server_timestamp_epoch_microseconds_utc(self):
        self.example_packet.set_server_timestamp_epoch_microseconds_utc(100)
        self.empty_packet.set_server_timestamp_epoch_microseconds_utc(100)
        self.assertEqual(100, self.example_packet.server_timestamp_epoch_microseconds_utc())
        self.assertEqual(100, self.empty_packet.server_timestamp_epoch_microseconds_utc())

    def test_get_metadata(self):
        self.assertEqual(["bar", "baz"], self.example_packet.metadata())
        self.assertEqual([], self.empty_packet.metadata())

    def test_set_metadata(self):
        self.example_packet.set_metadata(["foo", "bar"])
        self.empty_packet.set_metadata(["foo", "bar"])
        self.assertEqual(["foo", "bar"], self.example_packet.metadata())
        self.assertEqual(["foo", "bar"], self.empty_packet.metadata())

    def test_set_metadata_empty(self):
        self.example_packet.set_metadata([])
        self.assertEqual([], self.example_packet.metadata())

    def test_set_metadata_single(self):
        self.example_packet.set_metadata(["foo"])
        self.assertEqual(["foo"], self.example_packet.metadata())

    def test_get_metadata_as_dict(self):
        self.assertEqual("baz", self.example_packet.metadata_as_dict()["bar"])
        self.assertEqual(0, len(self.empty_packet.metadata_as_dict()))

    def test_get_metadata_as_dict_malformed(self):
        self.example_packet.set_metadata(["foo"])
        with self.assertRaises(ReaderException):
            self.example_packet.metadata_as_dict()

    def test_set_metadata_as_dict(self):
        self.example_packet.set_metadata_as_dict({"foo": "bar"})
        self.assertEqual("bar", self.example_packet.metadata_as_dict()["foo"])

    def test_add_metadata(self):
        self.example_packet.set_metadata_as_dict({"foo": "bar"})
        self.example_packet.add_metadata("baz", "buz")
        self.example_packet.add_metadata("1", 2)
        self.assertEqual(self.example_packet.metadata_as_dict(),
                         {"foo": "bar",
                          "baz": "buz",
                          "1": "2"})

    def test_mach_time_zero(self):
        self.assertEqual(None, self.example_packet.mach_time_zero())
        self.example_packet.set_mach_time_zero(100)
        self.assertEqual(100, self.example_packet.mach_time_zero())

    def test_mach_time_zero_incorrect_location(self):
        self.assertEqual(None, self.example_packet.mach_time_zero())
        self.example_packet.location_sensor().set_metadata_as_dict({"machTimeZero": "200"})
        self.assertEqual(200, self.example_packet.mach_time_zero())


    def test_best_latency(self):
        self.assertEqual(self.example_packet.best_latency(), None)
        self.example_packet.set_best_latency(100)
        self.assertEqual(self.example_packet.best_latency(), 100)

    def test_best_offset(self):
        self.assertEqual(self.example_packet.best_latency(), None)
        self.example_packet.set_best_offset(100)
        self.assertEqual(self.example_packet.best_offset(), 100)

    def test_is_synch_corrected(self):
        self.assertFalse(self.example_packet.is_synch_corrected())
        self.example_packet.set_is_synch_corrected(False)
        self.assertFalse(self.example_packet.is_synch_corrected())
        self.example_packet.set_is_synch_corrected(True)
        self.assertTrue(self.example_packet.is_synch_corrected())

    def test_has_microphone_sensor(self):
        self.assertTrue(self.example_packet.has_microphone_sensor())
        self.assertFalse(self.empty_packet.has_microphone_sensor())

    def test_get_microphone_sensor(self):
        self.assertEqual("example_mic", self.example_packet.microphone_sensor().sensor_name())
        self.assertIsNone(self.empty_packet.microphone_sensor())

    def test_set_microphone_sensor(self):
        sensor = reader.MicrophoneSensor().set_sensor_name("foo")
        self.example_packet.set_microphone_sensor(sensor)
        self.empty_packet.set_microphone_sensor(sensor)
        self.assertEqual("foo", self.example_packet.microphone_sensor().sensor_name())
        self.assertEqual("foo", self.empty_packet.microphone_sensor().sensor_name())

    def test_set_microphone_sensor_none(self):
        self.example_packet.set_microphone_sensor(None)
        self.empty_packet.set_microphone_sensor(None)
        self.assertFalse(self.example_packet.has_microphone_sensor())
        self.assertFalse(self.empty_packet.has_microphone_sensor())
        self.assertIsNone(self.example_packet.microphone_sensor())
        self.assertIsNone(self.empty_packet.microphone_sensor())

    def test_has_barometer_sensor(self):
        self.assertTrue(self.example_packet.has_barometer_sensor())
        self.assertFalse(self.empty_packet.has_barometer_sensor())

    def test_get_barometer_sensor(self):
        self.assertEqual("example_barometer", self.example_packet.barometer_sensor().sensor_name())
        self.assertIsNone(self.empty_packet.barometer_sensor())

    def test_set_barometer_sensor(self):
        sensor = reader.BarometerSensor().set_sensor_name("foo")
        self.example_packet.set_barometer_sensor(sensor)
        self.empty_packet.set_barometer_sensor(sensor)
        self.assertEqual("foo", self.example_packet.barometer_sensor().sensor_name())
        self.assertEqual("foo", self.empty_packet.barometer_sensor().sensor_name())

    def test_set_barometer_sensor_none(self):
        self.example_packet.set_barometer_sensor(None)
        self.empty_packet.set_barometer_sensor(None)
        self.assertFalse(self.example_packet.has_barometer_sensor())
        self.assertFalse(self.empty_packet.has_barometer_sensor())
        self.assertIsNone(self.example_packet.barometer_sensor())
        self.assertIsNone(self.empty_packet.barometer_sensor())

    def test_has_location_sensor(self):
        self.assertTrue(self.example_packet.has_location_sensor())
        self.assertFalse(self.empty_packet.has_location_sensor())

    def test_get_location_sensor(self):
        self.assertEqual("example_gps", self.example_packet.location_sensor().sensor_name())
        self.assertIsNone(self.empty_packet.location_sensor())

    def test_set_location_sensor(self):
        sensor = reader.LocationSensor().set_sensor_name("foo")
        self.example_packet.set_location_sensor(sensor)
        self.empty_packet.set_location_sensor(sensor)
        self.assertEqual("foo", self.example_packet.location_sensor().sensor_name())
        self.assertEqual("foo", self.empty_packet.location_sensor().sensor_name())

    def test_set_location_sensor_none(self):
        self.example_packet.set_location_sensor(None)
        self.empty_packet.set_location_sensor(None)
        self.assertFalse(self.example_packet.has_location_sensor())
        self.assertFalse(self.empty_packet.has_location_sensor())
        self.assertIsNone(self.example_packet.location_sensor())
        self.assertIsNone(self.empty_packet.location_sensor())

    def test_has_time_synchronization_sensor(self):
        self.assertTrue(self.example_packet.has_time_synchronization_sensor())
        self.assertFalse(self.empty_packet.has_time_synchronization_sensor())

    def test_get_time_synchronization_sensor(self):
        self.assertEqual(7, len(self.example_packet.time_synchronization_sensor().payload_values()))
        self.assertIsNone(self.empty_packet.time_synchronization_sensor())

    def test_set_time_synchronization_sensor(self):
        sensor = reader.TimeSynchronizationSensor().set_payload_values([1, 2, 3])
        self.example_packet.set_time_synchronization_sensor(sensor)
        self.empty_packet.set_time_synchronization_sensor(sensor)
        self.assertTrue(numpy.array_equal(numpy.array([1, 2, 3]), self.example_packet.time_synchronization_sensor().payload_values()))
        self.assertTrue(numpy.array_equal(numpy.array([1, 2, 3]), self.empty_packet.time_synchronization_sensor().payload_values()))

    def test_set_time_synchronization_sensor_none(self):
        self.example_packet.set_time_synchronization_sensor(None)
        self.empty_packet.set_time_synchronization_sensor(None)
        self.assertFalse(self.example_packet.has_time_synchronization_sensor())
        self.assertFalse(self.empty_packet.has_time_synchronization_sensor())
        self.assertIsNone(self.example_packet.time_synchronization_sensor())
        self.assertIsNone(self.empty_packet.time_synchronization_sensor())

    def test_has_accelerometer_sensor(self):
        self.assertTrue(self.example_packet.has_accelerometer_sensor())
        self.assertFalse(self.empty_packet.has_accelerometer_sensor())

    def test_get_accelerometer_sensor(self):
        self.assertEqual("example_accelerometer", self.example_packet.accelerometer_sensor().sensor_name())
        self.assertIsNone(self.empty_packet.accelerometer_sensor())

    def test_set_accelerometer_sensor(self):
        sensor = reader.AccelerometerSensor().set_sensor_name("foo")
        self.example_packet.set_accelerometer_sensor(sensor)
        self.empty_packet.set_accelerometer_sensor(sensor)
        self.assertEqual("foo", self.example_packet.accelerometer_sensor().sensor_name())
        self.assertEqual("foo", self.empty_packet.accelerometer_sensor().sensor_name())

    def test_set_accelerometer_sensor_none(self):
        self.example_packet.set_accelerometer_sensor(None)
        self.empty_packet.set_accelerometer_sensor(None)
        self.assertFalse(self.example_packet.has_accelerometer_sensor())
        self.assertFalse(self.empty_packet.has_accelerometer_sensor())
        self.assertIsNone(self.example_packet.accelerometer_sensor())
        self.assertIsNone(self.empty_packet.accelerometer_sensor())

    def test_has_magnetometer_sensor(self):
        self.assertTrue(self.example_packet.has_magnetometer_sensor())
        self.assertFalse(self.empty_packet.has_magnetometer_sensor())

    def test_get_magnetometer_sensor(self):
        self.assertEqual("example_magnetometer", self.example_packet.magnetometer_sensor().sensor_name())
        self.assertIsNone(self.empty_packet.magnetometer_sensor())

    def test_set_magnetometer_sensor(self):
        sensor = reader.MagnetometerSensor().set_sensor_name("foo")
        self.example_packet.set_magnetometer_sensor(sensor)
        self.empty_packet.set_magnetometer_sensor(sensor)
        self.assertEqual("foo", self.example_packet.magnetometer_sensor().sensor_name())
        self.assertEqual("foo", self.empty_packet.magnetometer_sensor().sensor_name())

    def test_set_magnetometer_sensor_none(self):
        self.example_packet.set_magnetometer_sensor(None)
        self.empty_packet.set_magnetometer_sensor(None)
        self.assertFalse(self.example_packet.has_magnetometer_sensor())
        self.assertFalse(self.empty_packet.has_magnetometer_sensor())
        self.assertIsNone(self.example_packet.magnetometer_sensor())
        self.assertIsNone(self.empty_packet.magnetometer_sensor())

    def test_has_gyroscope_sensor(self):
        self.assertTrue(self.example_packet.has_gyroscope_sensor())
        self.assertFalse(self.empty_packet.has_gyroscope_sensor())

    def test_get_gyroscope_sensor(self):
        self.assertEqual("example_gyroscope", self.example_packet.gyroscope_sensor().sensor_name())
        self.assertIsNone(self.empty_packet.gyroscope_sensor())

    def test_set_gyroscope_sensor(self):
        sensor = reader.GyroscopeSensor().set_sensor_name("foo")
        self.example_packet.set_gyroscope_sensor(sensor)
        self.empty_packet.set_gyroscope_sensor(sensor)
        self.assertEqual("foo", self.example_packet.gyroscope_sensor().sensor_name())
        self.assertEqual("foo", self.empty_packet.gyroscope_sensor().sensor_name())

    def test_set_gyroscope_sensor_none(self):
        self.example_packet.set_gyroscope_sensor(None)
        self.empty_packet.set_gyroscope_sensor(None)
        self.assertFalse(self.example_packet.has_gyroscope_sensor())
        self.assertFalse(self.empty_packet.has_gyroscope_sensor())
        self.assertIsNone(self.example_packet.gyroscope_sensor())
        self.assertIsNone(self.empty_packet.gyroscope_sensor())

    def test_has_light_sensor(self):
        self.assertTrue(self.example_packet.has_light_sensor())
        self.assertFalse(self.empty_packet.has_light_sensor())

    def test_get_light_sensor(self):
        self.assertEqual("example_light", self.example_packet.light_sensor().sensor_name())
        self.assertIsNone(self.empty_packet.light_sensor())

    def test_set_light_sensor(self):
        sensor = reader.LightSensor().set_sensor_name("foo")
        self.example_packet.set_light_sensor(sensor)
        self.empty_packet.set_light_sensor(sensor)
        self.assertEqual("foo", self.example_packet.light_sensor().sensor_name())
        self.assertEqual("foo", self.empty_packet.light_sensor().sensor_name())

    def test_set_light_sensor_none(self):
        self.example_packet.set_light_sensor(None)
        self.empty_packet.set_light_sensor(None)
        self.assertFalse(self.example_packet.has_light_sensor())
        self.assertFalse(self.empty_packet.has_light_sensor())
        self.assertIsNone(self.example_packet.light_sensor())
        self.assertIsNone(self.empty_packet.light_sensor())

    def test_has_infrared_sensor(self):
        self.assertTrue(self.example_packet.has_infrared_sensor())
        self.assertFalse(self.empty_packet.has_infrared_sensor())

    def test_get_infrared_sensor(self):
        self.assertEqual("example_infrared", self.example_packet.infrared_sensor().sensor_name())
        self.assertIsNone(self.empty_packet.infrared_sensor())

    def test_set_infrared_sensor(self):
        sensor = reader.InfraredSensor().set_sensor_name("foo")
        self.example_packet.set_infrared_sensor(sensor)
        self.empty_packet.set_infrared_sensor(sensor)
        self.assertEqual("foo", self.example_packet.infrared_sensor().sensor_name())
        self.assertEqual("foo", self.empty_packet.infrared_sensor().sensor_name())

    def test_set_infrared_sensor_none(self):
        self.example_packet.set_infrared_sensor(None)
        self.empty_packet.set_infrared_sensor(None)
        self.assertFalse(self.example_packet.has_infrared_sensor())
        self.assertFalse(self.empty_packet.has_infrared_sensor())
        self.assertIsNone(self.example_packet.infrared_sensor())
        self.assertIsNone(self.empty_packet.infrared_sensor())

    def test_to_json(self):
        json = self.example_packet.to_json()
        self.assertTrue('"api": 900' in json)

    def test_compressed_buffer(self):
        self.assertEqual(self.example_packet,
                         reader.read_rdvxz_buffer(self.example_packet.compressed_buffer()))

    def test_default_filename(self):
        self.assertEqual("0000000001_1552075743960.rdvxz", self.example_packet.default_filename())
        self.assertEqual("_0.rdvxz", self.empty_packet.default_filename())

    def test_eq(self):
        self.assertEqual(self.example_packet, self.example_packet)
        self.assertEqual(self.empty_packet, self.empty_packet)
        self.assertNotEqual(self.example_packet, self.empty_packet)

        cloned = self.example_packet.clone()
        self.assertEqual(self.example_packet, cloned)
        cloned.set_is_private(False)

        self.assertNotEqual(self.example_packet, cloned)
        self.assertNotEqual(self.example_packet, self.example_packet.clone().microphone_sensor().set_sensor_name("foo"))

    def test_clone(self):
        cloned = self.example_packet.clone()
        self.assertTrue(self.example_packet == cloned)
        self.assertEqual(0, len(self.example_packet.diff(cloned)))

    def test_diff(self):
        cloned_packet = self.example_packet.clone()
        cloned_packet.set_api(901)
        cloned_packet_2 = self.example_packet.clone()
        cloned_packet_2.set_microphone_sensor(None)
        self.assertEqual([], self.example_packet.diff(self.example_packet))
        if migrations.are_migrations_enabled():
            self.assertEqual(["900.0 != 901.0"], self.example_packet.diff(cloned_packet))
        else:
            self.assertEqual(["900 != 901"], self.example_packet.diff(cloned_packet))
        self.assertTrue(len(self.example_packet.diff(cloned_packet_2)) > 0)

    def test_write_rdvxz(self):
        self.example_packet.write_rdvxz(TEST_DATA_DIR, "test.rdvxz")
        self.example_packet.write_rdvxz(TEST_DATA_DIR)
        self.assertEqual(self.example_packet, reader.read_rdvxz_file(test_data("test.rdvxz")))
        self.assertEqual(self.example_packet, reader.read_rdvxz_file(test_data("0000000001_1552075743960.rdvxz")))
        os.remove(test_data("test.rdvxz"))
        os.remove(test_data("0000000001_1552075743960.rdvxz"))

    def test_write_json(self):
        self.example_packet.write_json(TEST_DATA_DIR, "test.json")
        self.example_packet.write_json(TEST_DATA_DIR)
        self.assertEqual(self.example_packet, reader.read_json_file(test_data("test.json")))
        self.assertEqual(self.example_packet, reader.read_json_file(test_data("0000000001_1552075743960.json")))
        os.remove(test_data("test.json"))
        os.remove(test_data("0000000001_1552075743960.json"))
































