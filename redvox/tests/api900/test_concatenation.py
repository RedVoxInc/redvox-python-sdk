"""
This modules provides test for concatenating sensors and packets.
"""
import unittest

import redvox.api900.concat as concat
import redvox.api900.exceptions as exceptions
import redvox.api900.reader as reader
import redvox.api900.qa.gap_detection as gap_detection
import redvox.tests as test_utils

import numpy as np


class TestConcatenation(unittest.TestCase):
    def setUp(self):
        self.example_packet = reader.read_rdvxz_file(test_utils.test_data("example.rdvxz"))
        self.cloned_packet = self.example_packet.clone()

    def reset_clone(self):
        self.cloned_packet = self.example_packet.clone()

    def test_partial_hash_sensor_correct(self):
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.microphone_sensor()),
                         concat._partial_hash_sensor(self.cloned_packet.microphone_sensor()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.barometer_sensor()),
                         concat._partial_hash_sensor(self.cloned_packet.barometer_sensor()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.time_synchronization_sensor()),
                         concat._partial_hash_sensor(self.cloned_packet.time_synchronization_sensor()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.location_sensor()),
                         concat._partial_hash_sensor(self.cloned_packet.location_sensor()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.gyroscope_sensor()),
                         concat._partial_hash_sensor(self.cloned_packet.gyroscope_sensor()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.accelerometer_sensor()),
                         concat._partial_hash_sensor(self.cloned_packet.accelerometer_sensor()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.magnetometer_sensor()),
                         concat._partial_hash_sensor(self.cloned_packet.magnetometer_sensor()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.light_sensor()),
                         concat._partial_hash_sensor(self.cloned_packet.light_sensor()))
        self.assertEqual(concat._partial_hash_sensor(self.example_packet.infrared_sensor()),
                         concat._partial_hash_sensor(self.cloned_packet.infrared_sensor()))

    def test_partial_hash_sensor_api_change(self):
        self.cloned_packet.microphone_sensor().set_sample_rate_hz(81.0)
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.microphone_sensor()),
                            concat._partial_hash_sensor(self.cloned_packet.microphone_sensor()))

    def test_partial_hash_sensor_name_change(self):
        self.cloned_packet.microphone_sensor().set_sensor_name("foo")
        self.cloned_packet.barometer_sensor().set_sensor_name("foo")
        self.cloned_packet.location_sensor().set_sensor_name("foo")
        self.cloned_packet.accelerometer_sensor().set_sensor_name("foo")
        self.cloned_packet.magnetometer_sensor().set_sensor_name("foo")
        self.cloned_packet.gyroscope_sensor().set_sensor_name("foo")
        self.cloned_packet.light_sensor().set_sensor_name("foo")
        self.cloned_packet.infrared_sensor().set_sensor_name("foo")

        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.microphone_sensor()),
                            concat._partial_hash_sensor(self.cloned_packet.microphone_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.barometer_sensor()),
                            concat._partial_hash_sensor(self.cloned_packet.barometer_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.location_sensor()),
                            concat._partial_hash_sensor(self.cloned_packet.location_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.accelerometer_sensor()),
                            concat._partial_hash_sensor(self.cloned_packet.accelerometer_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.gyroscope_sensor()),
                            concat._partial_hash_sensor(self.cloned_packet.gyroscope_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.magnetometer_sensor()),
                            concat._partial_hash_sensor(self.cloned_packet.magnetometer_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.light_sensor()),
                            concat._partial_hash_sensor(self.cloned_packet.light_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.infrared_sensor()),
                            concat._partial_hash_sensor(self.cloned_packet.infrared_sensor()))

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
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.microphone_sensor()),
                            concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.barometer_sensor()),
                            concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.location_sensor()),
                            concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.time_synchronization_sensor()),
                            concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.accelerometer_sensor()),
                            concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.magnetometer_sensor()),
                            concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.gyroscope_sensor()),
                            concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.light_sensor()),
                            concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(self.example_packet.infrared_sensor()),
                            concat._partial_hash_sensor(None))
        self.assertNotEqual(concat._partial_hash_sensor(None),
                            concat._partial_hash_sensor(self.example_packet.microphone_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(None),
                            concat._partial_hash_sensor(self.example_packet.barometer_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(None),
                            concat._partial_hash_sensor(self.example_packet.location_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(None),
                            concat._partial_hash_sensor(self.example_packet.time_synchronization_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(None),
                            concat._partial_hash_sensor(self.example_packet.gyroscope_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(None),
                            concat._partial_hash_sensor(self.example_packet.accelerometer_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(None),
                            concat._partial_hash_sensor(self.example_packet.magnetometer_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(None),
                            concat._partial_hash_sensor(self.example_packet.light_sensor()))
        self.assertNotEqual(concat._partial_hash_sensor(None),
                            concat._partial_hash_sensor(self.example_packet.infrared_sensor()))

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
        self.cloned_packet.microphone_sensor().set_sample_rate_hz(81.0)
        self.assertNotEqual(concat._partial_hash_packet(self.example_packet),
                            concat._partial_hash_packet(self.cloned_packet))

    def test_partial_hash_packet_change_sensors(self):
        self.cloned_packet.microphone_sensor().set_sensor_name("foo")
        self.cloned_packet.barometer_sensor().set_sensor_name("foo")
        self.cloned_packet.location_sensor().set_sensor_name("foo")
        self.cloned_packet.accelerometer_sensor().set_sensor_name("foo")
        self.cloned_packet.magnetometer_sensor().set_sensor_name("foo")
        self.cloned_packet.gyroscope_sensor().set_sensor_name("foo")
        self.cloned_packet.light_sensor().set_sensor_name("foo")
        self.cloned_packet.infrared_sensor().set_sensor_name("foo")

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
        self.example_packet.microphone_sensor().set_sample_rate_hz(80.0)
        self.example_packet.microphone_sensor().set_payload_values(list(range(80)))
        self.assertAlmostEqual(1.0, concat._packet_len_s(self.example_packet))

        self.example_packet.microphone_sensor().set_sample_rate_hz(800.0)
        self.example_packet.microphone_sensor().set_payload_values(list(range(800)))
        self.assertAlmostEqual(1.0, concat._packet_len_s(self.example_packet))

        self.example_packet.microphone_sensor().set_sample_rate_hz(8000.0)
        self.example_packet.microphone_sensor().set_payload_values(list(range(8000)))
        self.assertAlmostEqual(1.0, concat._packet_len_s(self.example_packet))

        self.example_packet.microphone_sensor().set_sample_rate_hz(8000.0)
        self.example_packet.microphone_sensor().set_payload_values(list(range(16000)))
        self.assertAlmostEqual(2.0, concat._packet_len_s(self.example_packet))

    def test_identify_gaps_empty(self):
        self.assertEqual([], gap_detection.identify_time_gaps([], 5.0))

    def test_identify_gaps_single(self):
        self.assertEqual([], gap_detection.identify_time_gaps([self.example_packet], 5.0))

    def test_identify_gaps_by_time(self):
        basic_packet = self.example_packet \
            .set_barometer_sensor(None) \
            .set_time_synchronization_sensor(None) \
            .set_location_sensor(None) \
            .set_accelerometer_sensor(None) \
            .set_gyroscope_sensor(None) \
            .set_magnetometer_sensor(None) \
            .set_light_sensor(None) \
            .set_infrared_sensor(None)

        basic_packet.set_app_file_start_timestamp_machine(0) \
            .microphone_sensor().set_payload_values(list(range(10))) \
            .set_sample_rate_hz(1.0) \
            .set_first_sample_timestamp_epoch_microseconds_utc(0)

        cloned_basic_packet = basic_packet.clone()
        cloned_basic_packet.set_app_file_start_timestamp_machine(10_000_000) \
            .microphone_sensor() \
            .set_first_sample_timestamp_epoch_microseconds_utc(10_000_000)

        cloned_basic_packet_2 = basic_packet.clone()
        cloned_basic_packet_2.set_app_file_start_timestamp_machine(20_000_000) \
            .microphone_sensor() \
            .set_first_sample_timestamp_epoch_microseconds_utc(20_000_000)

        self.assertEqual([], gap_detection.identify_time_gaps([basic_packet, cloned_basic_packet, cloned_basic_packet_2], 5.0))

        cloned_basic_packet_2.set_app_file_start_timestamp_machine(25_000_000) \
            .microphone_sensor() \
            .set_first_sample_timestamp_epoch_microseconds_utc(25_000_000)
        self.assertEqual([], gap_detection.identify_time_gaps([basic_packet, cloned_basic_packet, cloned_basic_packet_2], 5.0))

        cloned_basic_packet_2.set_app_file_start_timestamp_machine(26_000_000) \
            .microphone_sensor() \
            .set_first_sample_timestamp_epoch_microseconds_utc(26_000_000)
        self.assertEqual(2, gap_detection.identify_time_gaps([basic_packet, cloned_basic_packet, cloned_basic_packet_2], 5.0)[0].index)

        cloned_basic_packet = basic_packet.clone()
        cloned_basic_packet.set_app_file_start_timestamp_machine(16_000_000) \
            .microphone_sensor() \
            .set_first_sample_timestamp_epoch_microseconds_utc(16_000_000)

        cloned_basic_packet_2 = basic_packet.clone()
        cloned_basic_packet_2.set_app_file_start_timestamp_machine(26_000_000) \
            .microphone_sensor() \
            .set_first_sample_timestamp_epoch_microseconds_utc(26_000_000)
        self.assertEqual(1, gap_detection.identify_time_gaps([basic_packet, cloned_basic_packet, cloned_basic_packet_2], 5.0)[0].index)

        cloned_basic_packet = basic_packet.clone()
        cloned_basic_packet.set_app_file_start_timestamp_machine(16_000_000) \
            .microphone_sensor() \
            .set_first_sample_timestamp_epoch_microseconds_utc(16_000_000)

        cloned_basic_packet_2 = basic_packet.clone()
        cloned_basic_packet_2.set_app_file_start_timestamp_machine(32_000_000) \
            .microphone_sensor() \
            .set_first_sample_timestamp_epoch_microseconds_utc(32_000_000)

        gaps = gap_detection.identify_time_gaps([basic_packet, cloned_basic_packet, cloned_basic_packet_2], 5.0)
        self.assertEqual(1, gaps[0].index)
        self.assertEqual(2, gaps[1].index)

    def test_sensor_diff_none(self):
        self.assertEqual(concat._identify_sensor_changes([self.example_packet, self.cloned_packet]), [])

    def test_sensor_differences_sample_rate_change(self):
        self.cloned_packet.microphone_sensor().set_sample_rate_hz(81.0)
        self.assertEqual(concat._identify_sensor_changes([self.cloned_packet, self.example_packet]), [1])

    def test_sensor_diff_sensor_name(self):
        self.cloned_packet.microphone_sensor().set_sensor_name("diffname")
        self.assertEqual(concat._identify_sensor_changes([self.cloned_packet, self.example_packet]), [1])

    def test_sensor_diff_id(self):
        self.cloned_packet.set_redvox_id("diffid")
        self.assertEqual(concat._identify_sensor_changes([self.cloned_packet, self.example_packet]), [1])

    def test_sensor_diff_uuid(self):
        self.cloned_packet.set_uuid("diffuuid")
        self.assertEqual(concat._identify_sensor_changes([self.cloned_packet, self.example_packet]), [1])

    def test_sensor_diff_missing(self):
        self.cloned_packet.set_barometer_sensor(None)
        self.assertEqual(concat._identify_sensor_changes([self.cloned_packet, self.example_packet, self.cloned_packet]), [1, 2])

    def test_concat_numpy_single(self):
        self.assertTrue(np.array_equal(self.example_packet.microphone_sensor().payload_values(),
                                       concat._concat_numpy([self.example_packet.microphone_sensor()],
                                                            reader.MicrophoneSensor.payload_values)))
        self.assertTrue(np.array_equal(self.example_packet.barometer_sensor().payload_values(),
                                       concat._concat_numpy([self.example_packet.barometer_sensor()],
                                                            reader.BarometerSensor.payload_values)))

    def test_concat_numpy(self):
        self.assertTrue(np.array_equal([-10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0],
                                       concat._concat_numpy([self.example_packet.microphone_sensor(),
                                                             self.example_packet.microphone_sensor()],
                                                            reader.MicrophoneSensor.payload_values)))
        self.assertTrue(np.array_equal([1, 2, 3, 1, 2, 3, 1, 2, 3],
                                       concat._concat_numpy([self.example_packet.gyroscope_sensor(),
                                                             self.example_packet.gyroscope_sensor(),
                                                             self.example_packet.gyroscope_sensor()],
                                                            reader.GyroscopeSensor.payload_values_x)))

        self.assertTrue(np.array_equal([4, 5, 6, 4, 5, 6],
                                       concat._concat_numpy([self.example_packet.gyroscope_sensor(),
                                                             self.example_packet.gyroscope_sensor()],
                                                            reader.GyroscopeSensor.payload_values_y)))

        self.assertTrue(np.array_equal([7, 8, 9, 7, 8, 9],
                                       concat._concat_numpy([self.example_packet.gyroscope_sensor(),
                                                             self.example_packet.gyroscope_sensor()],
                                                            reader.GyroscopeSensor.payload_values_z)))

    def test_concat_lists_single(self):
        self.assertEqual(["a", "b", "c", "d"],
                         concat._concat_lists([self.example_packet.infrared_sensor()],
                                              reader.InfraredSensor.metadata))

    def test_concat_lists(self):
        self.assertEqual(["a", "b", "c", "d", "a", "b", "c", "d"],
                         concat._concat_lists([self.example_packet.infrared_sensor(),
                                               self.example_packet.infrared_sensor()],
                                              reader.InfraredSensor.metadata))

        self.assertEqual(["a", "b", "c", "d", "a", "b", "c", "d", "a", "b", "c", "d"],
                         concat._concat_lists([self.example_packet.infrared_sensor(),
                                               self.example_packet.infrared_sensor(),
                                               self.example_packet.infrared_sensor()],
                                              reader.InfraredSensor.metadata))

    def test_concat_continuous_empty(self):
        with self.assertRaises(IndexError):
            concat._concat_continuous_data([])

    def test_concat_continuous_single(self):
        self.assertEqual(self.example_packet,
                         concat._concat_continuous_data([self.example_packet]))

    def test_concat_continuous_two(self):
        concatted = concat._concat_continuous_data([self.example_packet, self.example_packet])
        self.assertTrue(np.array_equal(concatted.microphone_sensor().payload_values(),
                                       [-10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0]))
        self.assertEqual(concatted.microphone_sensor().metadata(),
                         ["foo", "bar", "foo", "bar"])
        self.assertTrue(np.array_equal(concatted.barometer_sensor().timestamps_microseconds_utc(),
                                       [0, 5, 11, 15, 22, 27, 31, 0, 5, 11, 15, 22, 27, 31]))
        self.assertTrue(np.array_equal(concatted.barometer_sensor().payload_values(),
                                       [-10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0]))
        self.assertTrue(np.array_equal(concatted.time_synchronization_sensor().payload_values(),
                                       [-10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0]))
        self.assertTrue(np.array_equal(concatted.location_sensor().timestamps_microseconds_utc(),
                                       [1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.location_sensor().payload_values_latitude(),
                                       [1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.location_sensor().payload_values_longitude(),
                                       [4, 5, 6, 4, 5, 6]))
        self.assertTrue(np.array_equal(concatted.location_sensor().payload_values_altitude(),
                                       [7, 8, 9, 7, 8, 9]))
        self.assertTrue(np.array_equal(concatted.location_sensor().payload_values_speed(),
                                       [10, 11, 12, 10, 11, 12]))
        self.assertTrue(np.array_equal(concatted.location_sensor().payload_values_accuracy(),
                                       [13, 14, 15, 13, 14, 15]))
        self.assertTrue(np.array_equal(concatted.accelerometer_sensor().timestamps_microseconds_utc(),
                                       [1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.accelerometer_sensor().payload_values_x(),
                                       [1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.accelerometer_sensor().payload_values_y(),
                                       [4, 5, 6, 4, 5, 6]))
        self.assertTrue(np.array_equal(concatted.accelerometer_sensor().payload_values_z(),
                                       [7, 8, 9, 7, 8, 9]))
        self.assertTrue(np.array_equal(concatted.gyroscope_sensor().timestamps_microseconds_utc(),
                                       [1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.gyroscope_sensor().payload_values_x(),
                                       [1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.gyroscope_sensor().payload_values_y(),
                                       [4, 5, 6, 4, 5, 6]))
        self.assertTrue(np.array_equal(concatted.gyroscope_sensor().payload_values_z(),
                                       [7, 8, 9, 7, 8, 9]))
        self.assertTrue(np.array_equal(concatted.accelerometer_sensor().timestamps_microseconds_utc(),
                                       [1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.magnetometer_sensor().payload_values_x(),
                                       [1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.magnetometer_sensor().payload_values_y(),
                                       [4, 5, 6, 4, 5, 6]))
        self.assertTrue(np.array_equal(concatted.magnetometer_sensor().payload_values_z(),
                                       [7, 8, 9, 7, 8, 9]))
        self.assertTrue(np.array_equal(concatted.light_sensor().timestamps_microseconds_utc(),
                                       [0, 5, 11, 15, 22, 27, 31, 0, 5, 11, 15, 22, 27, 31]))
        self.assertTrue(np.array_equal(concatted.light_sensor().payload_values(),
                                       [-10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0]))
        self.assertTrue(np.array_equal(concatted.infrared_sensor().timestamps_microseconds_utc(),
                                       [0, 5, 11, 15, 22, 27, 31, 0, 5, 11, 15, 22, 27, 31]))
        self.assertTrue(np.array_equal(concatted.infrared_sensor().payload_values(),
                                       [-10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0]))
        self.assertEqual(concatted.infrared_sensor().metadata(),
                         ["a", "b", "c", "d", "a", "b", "c", "d"])

    def test_concat_continuous_three(self):
        concatted = concat._concat_continuous_data([self.example_packet, self.example_packet, self.example_packet])
        self.assertTrue(np.array_equal(concatted.microphone_sensor().payload_values(),
                                       [-10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0]))
        self.assertEqual(concatted.microphone_sensor().metadata(),
                         ["foo", "bar", "foo", "bar", "foo", "bar"])
        self.assertTrue(np.array_equal(concatted.barometer_sensor().timestamps_microseconds_utc(),
                                       [0, 5, 11, 15, 22, 27, 31, 0, 5, 11, 15, 22, 27, 31, 0, 5, 11, 15, 22, 27, 31]))
        self.assertTrue(np.array_equal(concatted.barometer_sensor().payload_values(),
                                       [-10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0]))
        self.assertTrue(np.array_equal(concatted.time_synchronization_sensor().payload_values(),
                                       [-10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0]))
        self.assertTrue(np.array_equal(concatted.location_sensor().timestamps_microseconds_utc(),
                                       [1, 2, 3, 1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.location_sensor().payload_values_latitude(),
                                       [1, 2, 3, 1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.location_sensor().payload_values_longitude(),
                                       [4, 5, 6, 4, 5, 6, 4, 5, 6]))
        self.assertTrue(np.array_equal(concatted.location_sensor().payload_values_altitude(),
                                       [7, 8, 9, 7, 8, 9, 7, 8, 9]))
        self.assertTrue(np.array_equal(concatted.location_sensor().payload_values_speed(),
                                       [10, 11, 12, 10, 11, 12, 10, 11, 12]))
        self.assertTrue(np.array_equal(concatted.location_sensor().payload_values_accuracy(),
                                       [13, 14, 15, 13, 14, 15, 13, 14, 15]))
        self.assertTrue(np.array_equal(concatted.accelerometer_sensor().timestamps_microseconds_utc(),
                                       [1, 2, 3, 1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.accelerometer_sensor().payload_values_x(),
                                       [1, 2, 3, 1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.accelerometer_sensor().payload_values_y(),
                                       [4, 5, 6, 4, 5, 6, 4, 5, 6]))
        self.assertTrue(np.array_equal(concatted.accelerometer_sensor().payload_values_z(),
                                       [7, 8, 9, 7, 8, 9, 7, 8, 9]))
        self.assertTrue(np.array_equal(concatted.gyroscope_sensor().timestamps_microseconds_utc(),
                                       [1, 2, 3, 1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.gyroscope_sensor().payload_values_x(),
                                       [1, 2, 3, 1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.gyroscope_sensor().payload_values_y(),
                                       [4, 5, 6, 4, 5, 6, 4, 5, 6]))
        self.assertTrue(np.array_equal(concatted.gyroscope_sensor().payload_values_z(),
                                       [7, 8, 9, 7, 8, 9, 7, 8, 9]))
        self.assertTrue(np.array_equal(concatted.accelerometer_sensor().timestamps_microseconds_utc(),
                                       [1, 2, 3, 1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.magnetometer_sensor().payload_values_x(),
                                       [1, 2, 3, 1, 2, 3, 1, 2, 3]))
        self.assertTrue(np.array_equal(concatted.magnetometer_sensor().payload_values_y(),
                                       [4, 5, 6, 4, 5, 6, 4, 5, 6]))
        self.assertTrue(np.array_equal(concatted.magnetometer_sensor().payload_values_z(),
                                       [7, 8, 9, 7, 8, 9, 7, 8, 9]))
        self.assertTrue(np.array_equal(concatted.light_sensor().timestamps_microseconds_utc(),
                                       [0, 5, 11, 15, 22, 27, 31, 0, 5, 11, 15, 22, 27, 31, 0, 5, 11, 15, 22, 27, 31]))
        self.assertTrue(np.array_equal(concatted.light_sensor().payload_values(),
                                       [-10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0]))
        self.assertTrue(np.array_equal(concatted.infrared_sensor().timestamps_microseconds_utc(),
                                       [0, 5, 11, 15, 22, 27, 31, 0, 5, 11, 15, 22, 27, 31, 0, 5, 11, 15, 22, 27, 31]))
        self.assertTrue(np.array_equal(concatted.infrared_sensor().payload_values(),
                                       [-10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0, -10, 0, 10, 20, 15, -6, 0]))
        self.assertEqual(concatted.infrared_sensor().metadata(),
                         ["a", "b", "c", "d", "a", "b", "c", "d", "a", "b", "c", "d"])

    def test_concat_empty(self):
        self.assertEqual([], concat.concat_wrapped_redvox_packets([]))

    def test_concat_one(self):
        self.assertEqual([self.example_packet], concat.concat_wrapped_redvox_packets([self.example_packet]))

    def test_concat_diff_device(self):
        self.cloned_packet.set_redvox_id("foo")
        with self.assertRaises(exceptions.ConcatenationException):
            concat.concat_wrapped_redvox_packets([self.example_packet, self.cloned_packet])
        self.reset_clone()

        self.cloned_packet.set_uuid("foo")
        with self.assertRaises(exceptions.ConcatenationException):
            concat.concat_wrapped_redvox_packets([self.example_packet, self.cloned_packet])
        self.reset_clone()

        self.cloned_packet.set_redvox_id("foo")
        self.cloned_packet.set_uuid("foo")
        with self.assertRaises(exceptions.ConcatenationException):
            concat.concat_wrapped_redvox_packets([self.example_packet, self.cloned_packet])

        with self.assertRaises(exceptions.ConcatenationException):
            concat.concat_wrapped_redvox_packets([self.example_packet, self.example_packet, self.cloned_packet])

    def test_concat_non_monotonic(self):
        with self.assertRaises(exceptions.ConcatenationException):
            concat.concat_wrapped_redvox_packets([self.example_packet, self.example_packet])
