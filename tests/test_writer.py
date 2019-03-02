import numpy

from redvox.api900.lib import api900_pb2
import redvox.api900.reader as rar
import tests.test_high_level_api
import unittest
import os


class WriteAndSetModules(unittest.TestCase):
    def test_write(self):
        self.interleavedchanneltest()
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

        mic = rar.MicrophoneSensor()
        micchan = rar.EvenlySampledChannel()
        micchan.protobuf_channel = wrapped_packet.evenly_sampled_channels[0].protobuf_channel
        micchan.sample_rate_hz = wrapped_packet.evenly_sampled_channels[0].sample_rate_hz
        micchan.first_sample_timestamp_epoch_microseconds_utc = \
            wrapped_packet.evenly_sampled_channels[0].first_sample_timestamp_epoch_microseconds_utc
        mic.set_channel(micchan)

        protoboy = rar.EvenlySampledChannel()
        mic_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        protoboy.set_deinterleaved_payload([mic_data], micchan.get_payload_type())
        protoboy.channel_types = [api900_pb2.MICROPHONE]
        protoboy.sensor_name = "I/INTERNAL mic"
        protoboy.first_sample_timestamp_epoch_microseconds_utc = 1532656864354001
        protoboy.sample_rate_hz = 80.0

        protoboy2 = rar.UnevenlySampledChannel()
        protoboy2.set_payload([19.0, 155.0, 1.0, 25.0, 10.0,
                               20.0, 156.0, 2.0, 26.0, 11.0,
                               21.0, 157.0, 3.0, 27.0, 12.0,
                               22.0, 158.0, 4.0, 28.0, 13.0,
                               23.0, 159.0, 5.0, 29.0, 14.0], 5, "float64_payload")
        protoboy2.channel_types = [api900_pb2.LATITUDE,
                                   api900_pb2.LONGITUDE,
                                   api900_pb2.SPEED,
                                   api900_pb2.ALTITUDE,
                                   api900_pb2.ACCURACY]
        protoboy2.sensor_name = "LOCATORATOR"
        protoboy2.timestamps_microseconds_utc = [1, 2, 3, 4, 5]

        newpacket.add_channel(micchan)
        newpacket.add_channel(wrapped_packet.unevenly_sampled_channels[4])
        newpacket.add_channel(wrapped_packet.unevenly_sampled_channels[5])
        newpacket.edit_channel(api900_pb2.BAROMETER, wrapped_packet.unevenly_sampled_channels[-1])
        newpacket.delete_channel(api900_pb2.ACCELEROMETER_Y)
        newpacket.add_channel(wrapped_packet.get_channel(api900_pb2.BAROMETER))

        self.assertRaises(rar.ReaderException, protoboy.set_deinterleaved_payload, [], "byte_payload")
        self.assertRaises(rar.ReaderException, protoboy.set_deinterleaved_payload, [[1, 2, 3], [4, 5], [6]],
                          "byte_payload")
        # add a channel type that already exists
        self.assertRaises(ValueError, newpacket.add_channel, protoboy2)
        # delete a channel that doesn't exist
        self.assertRaises(TypeError, newpacket.delete_channel, api900_pb2.INFRARED)
        # edit a channel that doesn't exist
        self.assertRaises(TypeError, newpacket.edit_channel, api900_pb2.INFRARED,
                          wrapped_packet.unevenly_sampled_channels[3])

        # rar.write_file("write_test.rdvxz", newpacket.redvox_packet)

        # with open("write_test.rdvxz", "rb") as fin2:
        #    new_bytes = fin2.read()
        # wrapped = rar.wrap(rar.read_buffer(new_bytes))
        # write_buf = wrapped.compressed_buffer()

    def interleavedchanneltest(self):
        ilc = rar.EvenlySampledChannel()
        ilc.sensor_name = "test Mic"
        ilc.channel_types = [api900_pb2.MICROPHONE]
        mic_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ilc.set_deinterleaved_payload([mic_data], "int32_payload")
        ilc.first_sample_timestamp_epoch_microseconds_utc = 1532656864354001
        ilc.sample_rate_hz = 80.0
        ilc.metadata = ["a", "b", "c", "d"]

        print(ilc.channel_types)
        print(ilc.get_channel_type_names())
        print(ilc.sensor_name)
        print(ilc.payload)
        print(ilc.value_means)
        print(ilc.value_stds)
        print(ilc.value_medians)
        print(ilc.metadata)
        print(ilc.metadata_as_dict())
        print(ilc.protobuf_channel)


if __name__ == '__main__':
    unittest.main()
