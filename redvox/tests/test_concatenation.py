"""
This modules provides test for concatenating sensors and packets.
"""

import redvox.api900.concat as concat
import redvox.api900.reader as reader
import redvox.tests.utils as test_utils

import unittest


class TestConcatenation(unittest.TestCase):
    def setUp(self):
        self.example_packet = reader.read_rdvxz_file(test_utils.test_data("example.rdvxz"))
        self.cloned_packet = self.example_packet.clone()

    def test_partial_hash_sensor_correct(self):
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.microphone_channel()),
                         concat._partial_hash_sensor(self.cloned_packet.microphone_channel()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.barometer_channel()),
                         concat._partial_hash_sensor(self.cloned_packet.barometer_channel()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.time_synchronization_channel()),
                         concat._partial_hash_sensor(self.cloned_packet.time_synchronization_channel()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.location_channel()),
                         concat._partial_hash_sensor(self.cloned_packet.location_channel()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.gyroscope_channel()),
                         concat._partial_hash_sensor(self.cloned_packet.gyroscope_channel()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.accelerometer_channel()),
                         concat._partial_hash_sensor(self.cloned_packet.accelerometer_channel()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.magnetometer_channel()),
                         concat._partial_hash_sensor(self.cloned_packet.magnetometer_channel()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.light_channel()),
                         concat._partial_hash_sensor(self.cloned_packet.light_channel()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.infrared_channel()),
                         concat._partial_hash_sensor(self.cloned_packet.infrared_channel()))

    def test_partial_hash_sensor_api_change(self):
        self.cloned_packet.microphone_channel().set_sample_rate_hz(81.0)
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.microphone_channel()),
                            concat._partial_hash_sensor(self.cloned_packet.microphone_channel()))

    def test_partial_hash_sensor_name_change(self):
        self.cloned_packet.microphone_channel().set_sensor_name("foo")
        self.cloned_packet.barometer_channel().set_sensor_name("foo")
        self.cloned_packet.location_channel().set_sensor_name("foo")
        self.cloned_packet.accelerometer_channel().set_sensor_name("foo")
        self.cloned_packet.magnetometer_channel().set_sensor_name("foo")
        self.cloned_packet.gyroscope_channel().set_sensor_name("foo")
        self.cloned_packet.light_channel().set_sensor_name("foo")
        self.cloned_packet.infrared_channel().set_sensor_name("foo")

        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.microphone_channel()),
                            concat._partial_hash_sensor(self.cloned_packet.microphone_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.barometer_channel()),
                            concat._partial_hash_sensor(self.cloned_packet.barometer_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.location_channel()),
                            concat._partial_hash_sensor(self.cloned_packet.location_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.accelerometer_channel()),
                            concat._partial_hash_sensor(self.cloned_packet.accelerometer_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.gyroscope_channel()),
                            concat._partial_hash_sensor(self.cloned_packet.gyroscope_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.magnetometer_channel()),
                            concat._partial_hash_sensor(self.cloned_packet.magnetometer_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.light_channel()),
                            concat._partial_hash_sensor(self.cloned_packet.light_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.infrared_channel()),
                            concat._partial_hash_sensor(self.cloned_packet.infrared_channel()))

    def test_partial_hash_sensor_with_nones(self):
        self.assertEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(None))
        self.assertEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(None))
        self.assertEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(None))
        self.assertEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(None))
        self.assertEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(None))
        self.assertEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(None))
        self.assertEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(None))
        self.assertEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(None))
        self.assertEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.microphone_channel()), concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.barometer_channel()), concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.location_channel()), concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.time_synchronization_channel()), concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.accelerometer_channel()), concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.magnetometer_channel()), concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.gyroscope_channel()), concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.light_channel()), concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.infrared_channel()), concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(self.example_packet.microphone_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(self.example_packet.barometer_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(self.example_packet.location_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(self.example_packet.time_synchronization_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(self.example_packet.gyroscope_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(self.example_packet.accelerometer_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(self.example_packet.magnetometer_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(self.example_packet.light_channel()))
        self.assertNotEqual(concat._partial_hash_sensor(None), concat._partial_hash_sensor(self.example_packet.infrared_channel()))

    def test_partial_hash_packet_correct(self):
        self.assertEqual(concat._partial_hash_packet(self.example_packet),
                         concat._partial_hash_packet(self.cloned_packet))

    def test_partial_hash_packet_change_redvox_id(self):
        self.cloned_packet.set_redvox_id("foo")
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet),
                            concat._partial_hash_packet(self.cloned_packet))

    def test_partial_hash_packet_change_redvox_uuid(self):
        self.cloned_packet.set_uuid("foo")
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet),
                            concat._partial_hash_packet(self.cloned_packet))

    def test_partial_hash_packet_change_sample_rate(self):
        self.cloned_packet.microphone_channel().set_sample_rate_hz(81.0)
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet),
                            concat._partial_hash_packet(self.cloned_packet))

    def test_partial_hash_packet_change_sensors(self):
        self.cloned_packet.microphone_channel().set_sensor_name("foo")
        self.cloned_packet.barometer_channel().set_sensor_name("foo")
        self.cloned_packet.location_channel().set_sensor_name("foo")
        self.cloned_packet.accelerometer_channel().set_sensor_name("foo")
        self.cloned_packet.magnetometer_channel().set_sensor_name("foo")
        self.cloned_packet.gyroscope_channel().set_sensor_name("foo")
        self.cloned_packet.light_channel().set_sensor_name("foo")
        self.cloned_packet.infrared_channel().set_sensor_name("foo")

        self.assertNotEqual(concat._partial_hash_packet(self.example_packet),
                            concat._partial_hash_packet(self.cloned_packet))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet),
                            concat._partial_hash_packet(self.cloned_packet))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet),
                            concat._partial_hash_packet(self.cloned_packet))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet),
                            concat._partial_hash_packet(self.cloned_packet))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet),
                            concat._partial_hash_packet(self.cloned_packet))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet),
                            concat._partial_hash_packet(self.cloned_packet))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet),
                            concat._partial_hash_packet(self.cloned_packet))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet),
                            concat._partial_hash_packet(self.cloned_packet))

    def test_partial_hash_packet_with_nones(self):
        self.assertEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(None))
        self.assertEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(None))
        self.assertEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(None))
        self.assertEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(None))
        self.assertEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(None))
        self.assertEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(None))
        self.assertEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(None))
        self.assertEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(None))
        self.assertEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(None))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet), concat._partial_hash_packet(None))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet), concat._partial_hash_packet(None))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet), concat._partial_hash_packet(None))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet), concat._partial_hash_packet(None))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet), concat._partial_hash_packet(None))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet), concat._partial_hash_packet(None))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet), concat._partial_hash_packet(None))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet), concat._partial_hash_packet(None))
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet), concat._partial_hash_packet(None))
        self.assertNotEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(self.example_packet))
        self.assertNotEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(self.example_packet))
        self.assertNotEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(self.example_packet))
        self.assertNotEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(self.example_packet))
        self.assertNotEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(self.example_packet))
        self.assertNotEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(self.example_packet))
        self.assertNotEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(self.example_packet))
        self.assertNotEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(self.example_packet))
        self.assertNotEqual(concat._partial_hash_packet(None), concat._partial_hash_packet(self.example_packet))

    def test_packet_len_s(self):
        self.example_packet.microphone_channel().set_sample_rate_hz(80.0)
        self.example_packet.microphone_channel().set_payload_values(list(range(80)))
        self.assertAlmostEqual(1.0, concat._packet_len_s(self.example_packet))

        self.example_packet.microphone_channel().set_sample_rate_hz(800.0)
        self.example_packet.microphone_channel().set_payload_values(list(range(800)))
        self.assertAlmostEqual(1.0, concat._packet_len_s(self.example_packet))

        self.example_packet.microphone_channel().set_sample_rate_hz(8000.0)
        self.example_packet.microphone_channel().set_payload_values(list(range(8000)))
        self.assertAlmostEqual(1.0, concat._packet_len_s(self.example_packet))

        self.example_packet.microphone_channel().set_sample_rate_hz(8000.0)
        self.example_packet.microphone_channel().set_payload_values(list(range(16000)))
        self.assertAlmostEqual(2.0, concat._packet_len_s(self.example_packet))

    def test_concat_empty(self):
        self.assertEqual([], concat.concat_wrapped_redvox_packets([]))

    def test_concat_one(self):
        self.assertEqual([self.example_packet], concat.concat_wrapped_redvox_packets([self.example_packet]))


