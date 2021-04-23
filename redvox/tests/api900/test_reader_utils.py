import numpy

from redvox.api900.lib import api900_pb2
import redvox.api900.reader
import redvox.api900.reader_utils as reader_utils
import redvox.tests.api900.mock_packets as mock
from redvox.tests import ArraysTestCase

from redvox.api900.exceptions import ReaderException


class ModuleFunctionTests(ArraysTestCase):
    def setUp(self):
        super().setUp()
        self.base_packet = mock.base_packet()
        self.simple_mic_packet = mock.simple_mic_packet()
        self.simple_unevenly_sampled_packet = mock.simple_unevenly_sampled_packet()
        self.evenly_sampled_channel = api900_pb2.EvenlySampledChannel()
        self.unevenly_sampled_channel = api900_pb2.UnevenlySampledChannel()

    # Test getting of generic payloads
    # Evenly sampled channels
    def test_evenly_sampled_channel_uint32_payload(self):
        correct = [1, 2, 3, 4, 5]
        evenly_sampled_channel = mock.set_payload(self.evenly_sampled_channel, numpy.uint32, correct)
        self.assertArraysEqual(reader_utils.extract_payload(evenly_sampled_channel), numpy.array(correct))

    def test_evenly_sampled_channel_uint64_payload(self):
        correct = [1, 2, 3, 4, 5]
        evenly_sampled_channel = mock.set_payload(self.evenly_sampled_channel, numpy.uint64, correct)
        self.assertArraysEqual(reader_utils.extract_payload(evenly_sampled_channel), numpy.array(correct))

    def test_evenly_sampled_channel_int32_payload(self):
        correct = [1, 2, 3, 4, 5]
        evenly_sampled_channel = mock.set_payload(self.evenly_sampled_channel, numpy.int32, correct)
        self.assertArraysEqual(reader_utils.extract_payload(evenly_sampled_channel), numpy.array(correct))

    def test_evenly_sampled_channel_int64_payload(self):
        correct = [1, 2, 3, 4, 5]
        evenly_sampled_channel = mock.set_payload(self.evenly_sampled_channel, numpy.int64, correct)
        self.assertArraysEqual(reader_utils.extract_payload(evenly_sampled_channel), numpy.array(correct))

    def test_evenly_sampled_channel_float32_payload(self):
        correct = [1.0, 2.0, 3.0, 4.0, 5.0]
        evenly_sampled_channel = mock.set_payload(self.evenly_sampled_channel, numpy.float32, correct)
        self.assertArraysEqual(reader_utils.extract_payload(evenly_sampled_channel), numpy.array(correct))

    def test_evenly_sampled_channel_float64_payload(self):
        correct = [1.0, 2.0, 3.0, 4.0, 5.0]
        evenly_sampled_channel = mock.set_payload(self.evenly_sampled_channel, numpy.float64, correct)
        self.assertArraysEqual(reader_utils.extract_payload(evenly_sampled_channel), numpy.array(correct))

    # Unevenly sampled channels
    def test_unevenly_sampled_channel_uint32_payload(self):
        correct = [1, 2, 3, 4, 5]
        unevenly_sampled_channel = mock.set_payload(self.unevenly_sampled_channel, numpy.uint32, correct)
        self.assertArraysEqual(reader_utils.extract_payload(unevenly_sampled_channel), numpy.array(correct))

    def test_unevenly_sampled_channel_uint64_payload(self):
        correct = [1, 2, 3, 4, 5]
        unevenly_sampled_channel = mock.set_payload(self.unevenly_sampled_channel, numpy.uint64, correct)
        self.assertArraysEqual(reader_utils.extract_payload(unevenly_sampled_channel), numpy.array(correct))

    def test_unevenly_sampled_channel_int32_payload(self):
        correct = [1, 2, 3, 4, 5]
        unevenly_sampled_channel = mock.set_payload(self.unevenly_sampled_channel, numpy.int32, correct)
        self.assertArraysEqual(reader_utils.extract_payload(unevenly_sampled_channel), numpy.array(correct))

    def test_unevenly_sampled_channel_int64_payload(self):
        correct = [1, 2, 3, 4, 5]
        unevenly_sampled_channel = mock.set_payload(self.unevenly_sampled_channel, numpy.int64, correct)
        self.assertArraysEqual(reader_utils.extract_payload(unevenly_sampled_channel), numpy.array(correct))

    def test_unevenly_sampled_channel_float32_payload(self):
        correct = [1.0, 2.0, 3.0, 4.0, 5.0]
        unevenly_sampled_channel = mock.set_payload(self.unevenly_sampled_channel, numpy.float32, correct)
        self.assertArraysEqual(reader_utils.extract_payload(unevenly_sampled_channel), numpy.array(correct))

    def test_unevenly_sampled_channel_float64_payload(self):
        correct = [1.0, 2.0, 3.0, 4.0, 5.0]
        unevenly_sampled_channel = mock.set_payload(self.unevenly_sampled_channel, numpy.float64, correct)
        self.assertArraysEqual(reader_utils.extract_payload(unevenly_sampled_channel), numpy.array(correct))

    # Repeated utility functions
    def test_repeated_composite_to_list(self):
        repeated_composite = self.simple_mic_packet.evenly_sampled_channels
        as_list = reader_utils.repeated_to_list(repeated_composite)
        self.assertEqual(type(as_list), list)
        self.assertEqual(len(repeated_composite), len(as_list))

        for i in range(len(repeated_composite)):
            self.assertEqual(repeated_composite[i], as_list[i])

    def test_repeated_scalar_to_list(self):
        repeated_composite = self.simple_mic_packet.metadata
        as_list = reader_utils.repeated_to_list(repeated_composite)
        self.assertEqual(type(as_list), list)
        self.assertEqual(len(repeated_composite), len(as_list))

        for i in range(len(repeated_composite)):
            self.assertEqual(repeated_composite[i], as_list[i])

    def test_repeated_composite_to_list_empty(self):
        repeated_composite = self.simple_mic_packet.unevenly_sampled_channels
        as_list = reader_utils.repeated_to_list(repeated_composite)
        self.assertEqual(type(as_list), list)
        self.assertEqual(len(repeated_composite), 0)
        self.assertEqual(len(as_list), 0)

    def test_repeated_scalar_to_list_empty(self):
        repeated_scalar = self.simple_unevenly_sampled_packet.metadata
        as_list = reader_utils.repeated_to_list(repeated_scalar)
        self.assertEqual(type(as_list), list)
        self.assertEqual(len(repeated_scalar), 2)
        self.assertEqual(len(as_list), 2)

    # deinterleave_array
    def test_deinterleave_array_empty(self):
        self.assertRaises(redvox.api900.exceptions.ReaderException, reader_utils.deinterleave_array,
                          self.empty_array,
                          -1, 2)

    def test_deinterleave_array_bad_offsets(self):
        a = numpy.array([0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3])
        self.assertRaises(redvox.api900.exceptions.ReaderException, reader_utils.deinterleave_array, a, -1, 4)
        self.assertRaises(redvox.api900.exceptions.ReaderException, reader_utils.deinterleave_array, a, 4, 4)
        self.assertRaises(redvox.api900.exceptions.ReaderException, reader_utils.deinterleave_array, a, 30, 4)

    def test_deinterleave_array_bad_steps(self):
        a = numpy.array([0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3])
        self.assertRaises(redvox.api900.exceptions.ReaderException, reader_utils.deinterleave_array, a, 0, 0)
        self.assertRaises(redvox.api900.exceptions.ReaderException, reader_utils.deinterleave_array, a, 0, 5)

    def test_deinterleave_array_single(self):
        a = numpy.array([0])
        self.assertArraysEqual(reader_utils.deinterleave_array(a, 0, 1), a)
        b = numpy.array([0, 1])
        self.assertArraysEqual(reader_utils.deinterleave_array(b, 0, 1), b)
        c = numpy.array([0, 1, 2])
        self.assertArraysEqual(reader_utils.deinterleave_array(c, 0, 1), c)

    def test_deinterleave_array_double(self):
        a = numpy.array([0, 1])
        self.assertArraysEqual(reader_utils.deinterleave_array(a, 0, 2), numpy.array([0]))
        self.assertArraysEqual(reader_utils.deinterleave_array(a, 1, 2), numpy.array([1]))
        b = numpy.array([0, 1, 0, 1])
        self.assertArraysEqual(reader_utils.deinterleave_array(b, 0, 2), numpy.array([0, 0]))
        self.assertArraysEqual(reader_utils.deinterleave_array(b, 1, 2), numpy.array([1, 1]))
        c = numpy.array([0, 1, 0, 1, 0, 1])
        self.assertArraysEqual(reader_utils.deinterleave_array(c, 0, 2), numpy.array([0, 0, 0]))
        self.assertArraysEqual(reader_utils.deinterleave_array(c, 1, 2), numpy.array([1, 1, 1]))

    def test_deinterleave_array_triple(self):
        a = numpy.array([0, 1, 2])
        self.assertArraysEqual(reader_utils.deinterleave_array(a, 0, 3), numpy.array([0]))
        self.assertArraysEqual(reader_utils.deinterleave_array(a, 1, 3), numpy.array([1]))
        self.assertArraysEqual(reader_utils.deinterleave_array(a, 2, 3), numpy.array([2]))
        b = numpy.array([0, 1, 2, 0, 1, 2])
        self.assertArraysEqual(reader_utils.deinterleave_array(b, 0, 3), numpy.array([0, 0]))
        self.assertArraysEqual(reader_utils.deinterleave_array(b, 1, 3), numpy.array([1, 1]))
        self.assertArraysEqual(reader_utils.deinterleave_array(b, 2, 3), numpy.array([2, 2]))
        c = numpy.array([0, 1, 2, 0, 1, 2, 0, 1, 2])
        self.assertArraysEqual(reader_utils.deinterleave_array(c, 0, 3), numpy.array([0, 0, 0]))
        self.assertArraysEqual(reader_utils.deinterleave_array(c, 1, 3), numpy.array([1, 1, 1]))
        self.assertArraysEqual(reader_utils.deinterleave_array(c, 2, 3), numpy.array([2, 2, 2]))

    def test_interleave_arrays_empty(self):
        self.assertRaises(redvox.api900.exceptions.ReaderException, reader_utils.interleave_arrays, [])

    def test_interleave_arrays_single(self):
        self.assertRaises(redvox.api900.exceptions.ReaderException, reader_utils.interleave_arrays, [
            numpy.array([1, 2, 3])])

    def test_interleave_arrays_different_sizes(self):
        self.assertRaises(redvox.api900.exceptions.ReaderException, reader_utils.interleave_arrays, [
            self.empty_array,
            numpy.array([0])])
        self.assertRaises(redvox.api900.exceptions.ReaderException, reader_utils.interleave_arrays, [
            numpy.array([0, 1]),
            numpy.array([0])])
        self.assertRaises(redvox.api900.exceptions.ReaderException, reader_utils.interleave_arrays, [
            numpy.array([0, 1, 2]),
            numpy.array([0, 1, 2, 3, 4])])
        self.assertRaises(redvox.api900.exceptions.ReaderException, reader_utils.interleave_arrays, [
            numpy.array([0, 1]),
            numpy.array([0, 1]),
            numpy.array([0])])

    def test_interleave_arrays_double(self):
        a = numpy.array([0])
        b = numpy.array([1])
        self.assertArraysEqual(
            reader_utils.interleave_arrays([a, b]),
            numpy.array([0, 1]))
        c = numpy.array([0, 0])
        d = numpy.array([1, 1])
        self.assertArraysEqual(
            reader_utils.interleave_arrays([c, d]),
            numpy.array([0, 1, 0, 1]))
        e = numpy.array([0, 2, 4])
        f = numpy.array([1, 3, 5])
        self.assertArraysEqual(
            reader_utils.interleave_arrays([e, f]),
            numpy.array([0, 1, 2, 3, 4, 5]))

    def test_interleave_arrays_triple(self):
        a = numpy.array([0])
        b = numpy.array([1])
        c = numpy.array([2])
        self.assertArraysEqual(
            reader_utils.interleave_arrays([a, b, c]),
            numpy.array([0, 1, 2]))
        d = numpy.array([0, 0])
        e = numpy.array([1, 1])
        f = numpy.array([2, 2])
        self.assertArraysEqual(
            reader_utils.interleave_arrays([d, e, f]),
            numpy.array([0, 1, 2, 0, 1, 2]))
        g = numpy.array([0, 3, 6])
        h = numpy.array([1, 4, 7])
        i = numpy.array([2, 5, 8])
        self.assertArraysEqual(
            reader_utils.interleave_arrays([g, h, i]),
            numpy.array([0, 1, 2, 3, 4, 5, 6, 7, 8]))

    def test_safe_index_if_empty_list(self):
        li = []
        self.assertEqual(reader_utils.safe_index_of(li, None), -1)

    def test_safe_index_exists(self):
        li = ["a", "b", "c", "a"]
        self.assertEqual(reader_utils.safe_index_of(li, "a"), 0)
        self.assertEqual(reader_utils.safe_index_of(li, "b"), 1)
        self.assertEqual(reader_utils.safe_index_of(li, "c"), 2)
        self.assertEqual(reader_utils.safe_index_of(["c"], "c"), 0)

    def test_safe_index_dne(self):
        li = ["a", "b", "c", "a"]
        self.assertEqual(reader_utils.safe_index_of(li, 1), -1)
        self.assertEqual(reader_utils.safe_index_of(li, None), -1)
        self.assertEqual(reader_utils.safe_index_of(li, True), -1)
        self.assertEqual(reader_utils.safe_index_of(li, "d"), -1)

    def test_empty_array(self):
        self.assertArraysEqual(reader_utils.empty_array(), self.empty_array)

    def test_get_metadata_empty_list(self):
        metadata = []
        self.assertEqual(
            reader_utils.get_metadata(metadata, ""),
            "")

    def test_get_metadata_odd_sized_lists(self):
        self.assertRaises(
            redvox.api900.exceptions.ReaderException,
            reader_utils.get_metadata, ["a", "b", "c"], "a")

    def test_get_metadata_single_list(self):
        metadata = ["a"]
        self.assertRaises(
            redvox.api900.exceptions.ReaderException,
            reader_utils.get_metadata, metadata, "a")

    def test_get_metadata_one_kv(self):
        metadata = ["a", "b"]
        self.assertEqual(
            reader_utils.get_metadata(metadata, "a"),
            "b")

    def test_get_metadata_two_kv(self):
        metadata = ["a", "b", "c", "d"]
        self.assertEqual(
            reader_utils.get_metadata(metadata, "a"),
            "b")
        self.assertEqual(
            reader_utils.get_metadata(metadata, "c"),
            "d")

    def test_get_metadata_multi_kv(self):
        metadata = ["a", "b", "c", "d", "c", "f"]
        self.assertEqual(
            reader_utils.get_metadata(metadata, "a"),
            "b")
        self.assertEqual(
            reader_utils.get_metadata(metadata, "c"),
            "d")
        self.assertEqual(
            reader_utils.get_metadata(metadata, "b"),
            "c")

    def test_get_metadata_as_dict_empty(self):
        metadata = []
        self.assertEqual(
            reader_utils.get_metadata_as_dict(metadata),
            {})

    def test_get_metadata_as_dict_single_list(self):
        metadata = ["a"]
        self.assertRaises(
            redvox.api900.exceptions.ReaderException,
            reader_utils.get_metadata_as_dict, metadata)

    def test_get_metadata_as_dict_odd_sized_lists(self):
        metadata = ["a", "b", "c"]
        self.assertRaises(
            redvox.api900.exceptions.ReaderException,
            reader_utils.get_metadata_as_dict, metadata)

    def test_get_metadata_as_dict_one_kv(self):
        metadata = ["a", "b"]
        self.assertEqual(
            reader_utils.get_metadata_as_dict(metadata),
            {"a": "b"})

    def test_get_metadata_as_dict_multi_kv(self):
        metadata = ["a", "b", "c", "d", "c", "f"]
        self.assertEqual(
            reader_utils.get_metadata_as_dict(metadata),
            {"a": "b",
             "c": "d"})


class InterleavedChannelTests(ArraysTestCase):
    def setUp(self):
        super().setUp()
        self.mic_channel = redvox.api900.reader.InterleavedChannel(mock.simple_mic_packet().evenly_sampled_channels[0])
        self.gps_channel = redvox.api900.reader.InterleavedChannel(
            mock.simple_gps_packet().unevenly_sampled_channels[0])

    def test_init(self):
        self.assertEqual(self.mic_channel.protobuf_channel.sensor_name, "test microphone sensor name")
        self.assertEqual(self.gps_channel.protobuf_channel.sensor_name, "test gps sensor name")
        self.assertEqual(self.mic_channel.sensor_name, "test microphone sensor name")
        self.assertEqual(self.gps_channel.sensor_name, "test gps sensor name")

        self.assertArraysEqual(
            self.mic_channel.payload,
            numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
        self.assertEqual(self.mic_channel.metadata, ["a", "b", "c", "d"])
        self.assertArraysEqual(self.mic_channel.value_means, numpy.array([5.5]))
        self.assertArraysEqual(self.mic_channel.value_stds, numpy.array([3.0277]))
        self.assertArraysEqual(self.mic_channel.value_medians, numpy.array([5.5]))

        self.assertArraysEqual(
            self.gps_channel.payload,
            numpy.array([19.0, 155.0, 25.0, 1.0, 10.0,
                         20.0, 156.0, 26.0, 2.0, 11.0,
                         21.0, 157.0, 27.0, 3.0, 12.0,
                         22.0, 158.0, 28.0, 4.0, 13.0,
                         23.0, 159.0, 29.0, 5.0, 14.0]))
        self.assertEqual(self.gps_channel.metadata, [])
        self.assertArraysEqual(self.gps_channel.value_means, numpy.array([1, 2, 3, 4, 5]))
        self.assertArraysEqual(self.gps_channel.value_stds, numpy.array([1, 2, 3, 4, 5]))
        self.assertArraysEqual(self.gps_channel.value_medians, numpy.array([1, 2, 3, 4, 5]))

    def test_get_channel_type_names(self):
        self.assertEqual(self.mic_channel.get_channel_type_names(),
                         ["MICROPHONE"])
        self.assertEqual(self.gps_channel.get_channel_type_names(),
                         ["LATITUDE", "LONGITUDE", "ALTITUDE", "SPEED", "ACCURACY"])
        self.assertArraysEqual(
            self.mic_channel.payload,
            numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
        self.assertEqual(self.mic_channel.metadata, ["a", "b", "c", "d"])
        self.assertArraysEqual(self.mic_channel.value_means, numpy.array([5.5]))
        self.assertArraysEqual(self.mic_channel.value_stds, numpy.array([3.0277]))
        self.assertArraysEqual(self.mic_channel.value_medians, numpy.array([5.5]))

    def test_channel_index(self):
        self.assertEqual(self.mic_channel.channel_index(api900_pb2.MICROPHONE), 0)
        self.assertEqual(self.mic_channel.channel_index(api900_pb2.BAROMETER), -1)
        self.assertEqual(self.gps_channel.channel_index(api900_pb2.LATITUDE), 0)
        self.assertEqual(self.gps_channel.channel_index(api900_pb2.LONGITUDE), 1)
        self.assertEqual(self.gps_channel.channel_index(api900_pb2.ALTITUDE), 2)
        self.assertEqual(self.gps_channel.channel_index(api900_pb2.SPEED), 3)
        self.assertEqual(self.gps_channel.channel_index(api900_pb2.MICROPHONE), -1)

    def test_has_channel(self):
        self.assertEqual(self.mic_channel.has_channel(api900_pb2.MICROPHONE), True)
        self.assertEqual(self.mic_channel.has_channel(api900_pb2.BAROMETER), False)
        self.assertEqual(self.gps_channel.has_channel(api900_pb2.LATITUDE), True)
        self.assertEqual(self.gps_channel.has_channel(api900_pb2.LONGITUDE), True)
        self.assertEqual(self.gps_channel.has_channel(api900_pb2.SPEED), True)
        self.assertEqual(self.gps_channel.has_channel(api900_pb2.ALTITUDE), True)
        self.assertEqual(self.gps_channel.has_channel(api900_pb2.MICROPHONE), False)

    def test_get_payload_dne(self):
        self.assertArraysEqual(
            self.mic_channel.get_payload(api900_pb2.BAROMETER),
            self.empty_array)

    def test_get_payload_single(self):
        self.assertArraysEqual(
            self.mic_channel.get_payload(api900_pb2.MICROPHONE),
            numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))

    def test_get_payload_single_len(self):
        self.assertEqual(10, len(self.mic_channel.get_payload(api900_pb2.MICROPHONE),))

    def test_get_payload_interleaved(self):
        self.assertArraysEqual(
            self.gps_channel.get_payload(api900_pb2.LATITUDE),
            numpy.array([19.0, 20.0, 21.0, 22.0, 23.0]))
        self.assertArraysEqual(
            self.gps_channel.get_payload(api900_pb2.LONGITUDE),
            numpy.array([155.0, 156.0, 157.0, 158.0, 159.0]))
        self.assertArraysEqual(
            self.gps_channel.get_payload(api900_pb2.SPEED),
            numpy.array([1.0, 2.0, 3.0, 4.0, 5.0]))
        self.assertArraysEqual(
            self.gps_channel.get_payload(api900_pb2.ALTITUDE),
            numpy.array([25.0, 26.0, 27.0, 28.0, 29.0]))

    def test_get_payload_interleaved_dne(self):
        self.assertArraysEqual(
            self.gps_channel.get_payload(api900_pb2.BAROMETER),
            self.empty_array)

    def test_get_multi_payload_dne(self):
        self.assertArraysEqual(
            self.gps_channel.get_multi_payload([api900_pb2.BAROMETER]),
            self.empty_array)

    def test_get_multi_payload_single_dne(self):
        return self.assertRaises(
            redvox.api900.exceptions.ReaderException,
            self.gps_channel.get_multi_payload,
            [api900_pb2.LATITUDE, api900_pb2.BAROMETER])

    def test_get_multi_payload_single(self):
        self.assertArraysEqual(
            self.mic_channel.get_multi_payload([api900_pb2.MICROPHONE]),
            numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))

    def test_get_multi_payload_double(self):
        self.assertArraysEqual(
            self.gps_channel.get_multi_payload(
                [api900_pb2.LATITUDE, api900_pb2.LONGITUDE]),
            numpy.array([19.0, 155.0,
                         20.0, 156.0,
                         21.0, 157.0,
                         22.0, 158.0,
                         23.0, 159.0]))

        self.assertArraysEqual(
            self.gps_channel.get_multi_payload(
                [api900_pb2.LONGITUDE, api900_pb2.LATITUDE]),
            numpy.array([155.0, 19.0,
                         156.0, 20.0,
                         157.0, 21.0,
                         158.0, 22.0,
                         159.0, 23.0]))

        self.assertArraysEqual(
            self.gps_channel.get_multi_payload(
                [api900_pb2.LATITUDE, api900_pb2.ALTITUDE]),
            numpy.array([19.0, 25.0,
                         20.0, 26.0,
                         21.0, 27.0,
                         22.0, 28.0,
                         23.0, 29.0]))

        self.assertArraysEqual(
            self.gps_channel.get_multi_payload(
                [api900_pb2.ALTITUDE, api900_pb2.LONGITUDE]),
            numpy.array([25.0, 155.0,
                         26.0, 156.0,
                         27.0, 157.0,
                         28.0, 158.0,
                         29.0, 159.0]))

    def test_get_multi_payload_multi(self):
        self.assertArraysEqual(
            self.gps_channel.get_multi_payload([
                api900_pb2.LATITUDE,
                api900_pb2.LONGITUDE,
                api900_pb2.ALTITUDE]),
            numpy.array([19.0, 155.0, 25.0,
                         20.0, 156.0, 26.0,
                         21.0, 157.0, 27.0,
                         22.0, 158.0, 28.0,
                         23.0, 159.0, 29.0]))

        self.assertArraysEqual(
            self.gps_channel.get_multi_payload([
                api900_pb2.ALTITUDE,
                api900_pb2.SPEED,
                api900_pb2.LONGITUDE,
                api900_pb2.LATITUDE]),
            numpy.array([25.0, 1.0, 155.0, 19.0,
                         26.0, 2.0, 156.0, 20.0,
                         27.0, 3.0, 157.0, 21.0,
                         28.0, 4.0, 158.0, 22.0,
                         29.0, 5.0, 159.0, 23.0]))

    def test_get_value_mean_dne(self):
        with self.assertRaises(ReaderException):
            self.assertEqual(self.mic_channel.get_value_mean(api900_pb2.BAROMETER),
                             0.0)

    def test_get_value_mean_single(self):
        self.assertEqual(self.mic_channel.get_value_mean(api900_pb2.MICROPHONE),
                         5.5)

    def test_get_value_mean_multi(self):
        self.assertEqual(self.gps_channel.get_value_mean(api900_pb2.LATITUDE),
                         1)
        self.assertEqual(self.gps_channel.get_value_mean(api900_pb2.LONGITUDE),
                         2)
        self.assertEqual(self.gps_channel.get_value_mean(api900_pb2.ALTITUDE),
                         3)
        self.assertEqual(self.gps_channel.get_value_mean(api900_pb2.SPEED),
                         4)

    def test_get_value_std_dne(self):
        with self.assertRaises(ReaderException):
            self.assertEqual(self.mic_channel.get_value_std(api900_pb2.BAROMETER),
                             0.0)

    def test_get_value_std_single(self):
        self.assertEqual(self.mic_channel.get_value_std(api900_pb2.MICROPHONE),
                         3.0277)

    def test_get_value_std_multi(self):
        self.assertEqual(self.gps_channel.get_value_std(api900_pb2.LATITUDE),
                         1)
        self.assertEqual(self.gps_channel.get_value_std(api900_pb2.LONGITUDE),
                         2)
        self.assertEqual(self.gps_channel.get_value_std(api900_pb2.ALTITUDE),
                         3)
        self.assertEqual(self.gps_channel.get_value_std(api900_pb2.SPEED),
                         4)

    def test_get_value_median_dne(self):
        with self.assertRaises(ReaderException):
            self.assertEqual(self.mic_channel.get_value_median(api900_pb2.BAROMETER),
                             0.0)

    def test_get_value_median_single(self):
        self.assertEqual(self.mic_channel.get_value_median(api900_pb2.MICROPHONE),
                         5.5)

    def test_get_value_median_multi(self):
        self.assertEqual(self.gps_channel.get_value_median(api900_pb2.LATITUDE),
                         1)
        self.assertEqual(self.gps_channel.get_value_median(api900_pb2.LONGITUDE),
                         2)
        self.assertEqual(self.gps_channel.get_value_median(api900_pb2.ALTITUDE),
                         3)
        self.assertEqual(self.gps_channel.get_value_median(api900_pb2.SPEED),
                         4)

    def test_str(self):
        self.assertTrue("sensor_name: test microphone sensor name" in str(self.mic_channel))
        self.assertTrue("sensor_name: test gps sensor name" in str(self.gps_channel))


class EvenlySampledChannelTests(ArraysTestCase):
    def setUp(self):
        super().setUp()
        self.mic_channel = redvox.api900.reader.EvenlySampledChannel(
            mock.simple_mic_packet().evenly_sampled_channels[0])

    def test_init(self):
        self.assertEqual(self.mic_channel.sample_rate_hz, 80.0)
        self.assertEqual(self.mic_channel.first_sample_timestamp_epoch_microseconds_utc, 1519166348000000)

    def test_str(self):
        self.assertTrue("sensor_name: test microphone sensor name" in str(self.mic_channel))
        self.assertTrue("sample_rate_hz: 80.0" in str(self.mic_channel))


class UnevenlySampledChannelTests(ArraysTestCase):
    def setUp(self):
        super().setUp()
        self.gps_channel = redvox.api900.reader.UnevenlySampledChannel(
            mock.simple_gps_packet().unevenly_sampled_channels[0])

    def test_init(self):
        self.assertArraysEqual(
            self.gps_channel.timestamps_microseconds_utc,
            numpy.array([1, 2, 3, 4, 5]))
        self.assertEqual(self.gps_channel.sample_interval_mean, 1.0)
        self.assertEqual(self.gps_channel.sample_interval_std, 2.0)
        self.assertEqual(self.gps_channel.sample_interval_median, 3.0)

    def test_str(self):
        self.assertTrue("sensor_name: test gps sensor name" in str(self.gps_channel))
        self.assertTrue("len(timestamps_microseconds_utc): 5" in str(self.gps_channel))


class WrappedRedvoxPacketTests(ArraysTestCase):
    def setUp(self):
        super().setUp()
        self.mic_packet = redvox.api900.reader.WrappedRedvoxPacket(mock.simple_mic_packet())
        self.gps_packet = redvox.api900.reader.WrappedRedvoxPacket(mock.simple_gps_packet())
        self.multi_packet = redvox.api900.reader.WrappedRedvoxPacket(mock.multi_channel_packet())

    def test_init(self):
        self.assertEqual(self.mic_packet.redvox_packet().api, 900)
        self.assertEqual(self.gps_packet.redvox_packet().api, 900)
        self.assertEqual(self.multi_packet.redvox_packet().api, 900)

        self.assertEqual(len(self.mic_packet._evenly_sampled_channels_field), 1)
        self.assertEqual(len(self.gps_packet._evenly_sampled_channels_field), 0)
        self.assertEqual(len(self.multi_packet._evenly_sampled_channels_field), 1)

        self.assertEqual(len(self.mic_packet._unevenly_sampled_channels_field), 0)
        self.assertEqual(len(self.gps_packet._unevenly_sampled_channels_field), 1)
        self.assertEqual(len(self.multi_packet._unevenly_sampled_channels_field), 2)

        self.assertEqual(self.mic_packet.metadata(), ["foo", "bar", "a", "b", "c", "d"])
        self.assertEqual(self.gps_packet.metadata(), ["foo", "bar"])
        self.assertEqual(self.multi_packet.metadata(), ["foo", "bar"])

    def test_get_channel(self):
        self.assertEqual(self.mic_packet._get_channel(api900_pb2.MICROPHONE).sensor_name,
                         "test microphone sensor name")
        self.assertEqual(self.mic_packet._get_channel(api900_pb2.BAROMETER),
                         None)

        self.assertEqual(self.gps_packet._get_channel(api900_pb2.LATITUDE).sensor_name,
                         "test gps sensor name")
        self.assertEqual(self.gps_packet._get_channel(api900_pb2.LONGITUDE).sensor_name,
                         "test gps sensor name")
        self.assertEqual(self.gps_packet._get_channel(api900_pb2.SPEED).sensor_name,
                         "test gps sensor name")
        self.assertEqual(self.gps_packet._get_channel(api900_pb2.ALTITUDE).sensor_name,
                         "test gps sensor name")
        self.assertEqual(self.gps_packet._get_channel(api900_pb2.MICROPHONE), None)

        self.assertEqual(self.multi_packet._get_channel(api900_pb2.MICROPHONE).sensor_name,
                         "test microphone sensor name")
        self.assertEqual(self.multi_packet._get_channel(api900_pb2.LATITUDE).sensor_name,
                         "test gps sensor name")
        self.assertEqual(self.multi_packet._get_channel(api900_pb2.LONGITUDE).sensor_name,
                         "test gps sensor name")
        self.assertEqual(self.multi_packet._get_channel(api900_pb2.SPEED).sensor_name,
                         "test gps sensor name")
        self.assertEqual(self.multi_packet._get_channel(api900_pb2.ALTITUDE).sensor_name,
                         "test gps sensor name")
        self.assertEqual(self.multi_packet._get_channel(api900_pb2.OTHER).sensor_name,
                         "test other sensor name")

    def test_has_channel(self):
        self.assertTrue(self.mic_packet._has_channel(api900_pb2.MICROPHONE))
        self.assertFalse(self.mic_packet._has_channel(api900_pb2.BAROMETER))

        self.assertTrue(self.gps_packet._has_channel(api900_pb2.LATITUDE))
        self.assertTrue(self.gps_packet._has_channel(api900_pb2.LONGITUDE))
        self.assertTrue(self.gps_packet._has_channel(api900_pb2.SPEED))
        self.assertTrue(self.gps_packet._has_channel(api900_pb2.ALTITUDE))
        self.assertFalse(self.gps_packet._has_channel(api900_pb2.MICROPHONE))

        self.assertTrue(self.multi_packet._has_channel(api900_pb2.MICROPHONE))
        self.assertTrue(self.multi_packet._has_channel(api900_pb2.LATITUDE))
        self.assertTrue(self.multi_packet._has_channel(api900_pb2.LONGITUDE))
        self.assertTrue(self.multi_packet._has_channel(api900_pb2.SPEED))
        self.assertTrue(self.multi_packet._has_channel(api900_pb2.ALTITUDE))
        self.assertTrue(self.multi_packet._has_channel(api900_pb2.OTHER))
