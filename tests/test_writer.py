from redvox.api900.lib import api900_pb2
from tests.utils import ArraysTestCase
import redvox.api900.reader as rar
import unittest


class WriteAndSetModules(ArraysTestCase):
    def test_write(self):
        with open("0000001314_1532656864354.rdvxz", "rb") as fin:
            as_bytes = fin.read()

        redvox_packet = rar.read_buffer(as_bytes)
        wrapped_packet = rar.wrap(redvox_packet)

        # SAMPLE HAS THESE CHANNELS:
        # [['MICROPHONE'],
        # ['TIME_SYNCHRONIZATION'],
        # ['MAGNETOMETER_X', 'MAGNETOMETER_Y', 'MAGNETOMETER_Z'],
        # ['GYROSCOPE_X', 'GYROSCOPE_Y', 'GYROSCOPE_Z'],
        # ['LIGHT'],
        # ['BAROMETER'],
        # ['ACCELEROMETER_X', 'ACCELEROMETER_Y', 'ACCELEROMETER_Z'],
        # ['LATITUDE', 'LONGITUDE', 'ALTITUDE', 'SPEED', 'ACCURACY']]

        newpacket = rar.WrappedRedvoxPacket()

        # Create channels, sensors, or packets empty or with existing data
        mic_chan = rar.EvenlySampledChannel()
        mic_sen = rar.MicrophoneSensor(wrapped_packet.get_channel(api900_pb2.MICROPHONE))
        time_sen = rar.TimeSynchronizationSensor(wrapped_packet.get_channel(api900_pb2.TIME_SYNCHRONIZATION))
        mag_sen = rar.MagnetometerSensor(wrapped_packet.unevenly_sampled_channels[1])
        gyro_sen = rar.GyroscopeSensor(wrapped_packet.unevenly_sampled_channels[-5])
        light_sen = rar.LightSensor(wrapped_packet.get_channel(api900_pb2.LIGHT))
        bar_sen = rar.BarometerSensor(wrapped_packet.get_channel(api900_pb2.BAROMETER))
        accel_sen = rar.AccelerometerSensor(wrapped_packet.unevenly_sampled_channels[-2])
        loc_sen = rar.LocationSensor(wrapped_packet.unevenly_sampled_channels[6])
        othr_sen = rar.InfraredSensor()
        img_sen = rar.ImageSensor()

        # Set properties on creation or individually.  Not all values can be directly set.
        mic_chan.sensor_name = "Test Microphone"
        mic_chan.sample_rate_hz = 42.0
        mic_chan.first_sample_timestamp_epoch_microseconds_utc = 1

        # Set payloads and channels; Setting payloads will update the means, std devs and medians of the individual
        # data arrays that form the entire payload.  You can set payloads using an interleaved array or with a list of
        # equally sized arrays.  Setting channels will update all properties.
        mic_chan.set_payload(wrapped_packet.evenly_sampled_channels[0].payload, 1,
                             wrapped_packet.evenly_sampled_channels[0].get_payload_type())
        # This does the same as above
        # mic_chan.set_deinterleaved_payload([wrapped_packet.get_channel(api900_pb2.MICROPHONE)],
        #                                    wrapped_packet.evenly_sampled_channels[0].get_payload_type())

        mic_chan.set_channel(wrapped_packet.evenly_sampled_channels[0].protobuf_channel)
        mic_chan.metadata = ["This", "is a Test Sensor Packet", "Don't", "Take this data too seriously"]
        mic_chan.update_stats()

        # Access functions.  Asserts used to ensure values set correctly:
        self.assertSampledArray(mic_chan.get_channel_payload(api900_pb2.MICROPHONE),
                                4096,
                                [0, 2048, 4095],
                                [201, -4666, -1867])
        self.assertEqual("int32_payload", mic_chan.get_payload_type())
        self.assertSampledArray(mic_chan.get_multi_payload([api900_pb2.MICROPHONE]),
                                4096,
                                [0, 2048, 4095],
                                [201, -4666, -1867])
        self.assertAlmostEqual(mic_chan.get_value_mean(api900_pb2.MICROPHONE), -127.91796875, 1)
        self.assertAlmostEqual(mic_chan.get_value_std(api900_pb2.MICROPHONE), 2455.820326625975, 3)
        self.assertAlmostEqual(mic_chan.get_value_median(api900_pb2.MICROPHONE), -123.0, 1)
        self.assertTrue("MICROPHONE" in mic_chan.get_channel_type_names())
        self.assertEqual(mic_chan.sensor_name, "I/INTERNAL MIC")
        self.assertAlmostEqual(mic_chan.sample_rate_hz, 80.0, 1)
        self.assertEqual(mic_chan.first_sample_timestamp_epoch_microseconds_utc, 1532656864354000)
        self.assertTrue(api900_pb2.MICROPHONE in mic_chan.channel_types)
        self.assertAlmostEqual(mic_chan.value_means[0], -127.91796875, 1)
        self.assertAlmostEqual(mic_chan.value_stds[0], 2455.820326625975, 3)
        self.assertAlmostEqual(mic_chan.value_medians[0], -123.0, 1)
        self.assertEqual(mic_chan.channel_index(api900_pb2.MICROPHONE), 0)
        self.assertTrue(mic_chan.has_channel(api900_pb2.MICROPHONE))
        self.assertFalse(mic_chan.has_channel(api900_pb2.BAROMETER))
        self.assertEqual(len(mic_chan.metadata), 4)
        self.assertListEqual(mic_chan.metadata,
                             ["This", "is a Test Sensor Packet", "Don't", "Take this data too seriously"])
        synthetic_dict = mic_chan.metadata_as_dict()
        self.assertEqual(len(synthetic_dict), 2)
        self.assertTrue("This" in synthetic_dict and "Don't" in synthetic_dict)
        self.assertEqual(synthetic_dict["This"], "is a Test Sensor Packet")
        self.assertEqual(synthetic_dict["Don't"], "Take this data too seriously")
        self.assertTrue(mic_chan.payload is not None)
        self.assertTrue(mic_chan.protobuf_channel is not None)

        # add channels to a packet
        newpacket.add_channel(mic_sen.evenly_sampled_channel)
        newpacket.add_channel(time_sen.unevenly_sampled_channel)
        newpacket.add_channel(mag_sen.unevenly_sampled_channel)
        newpacket.add_channel(gyro_sen.unevenly_sampled_channel)
        newpacket.add_channel(light_sen.unevenly_sampled_channel)
        newpacket.add_channel(bar_sen.unevenly_sampled_channel)
        newpacket.add_channel(accel_sen.unevenly_sampled_channel)
        newpacket.add_channel(loc_sen.unevenly_sampled_channel)

        # write to a file
        rar.write_file("write_test.rdvxz", newpacket.redvox_packet)


if __name__ == '__main__':
    unittest.main()
