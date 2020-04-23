import unittest

import numpy as np

import redvox.api1000.wrapped_redvox_packet.common as common
import redvox.api1000.wrapped_redvox_packet.sensors.audio as microphone


class TestCommonProtoBase(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_microphone_channel: microphone.Audio = microphone.Audio.new()
        self.non_empty_microphone_channel: microphone.Audio = microphone.Audio.new()
        self.non_empty_microphone_channel.get_samples().set_unit(common.Unit['DECIBEL'])
        self.non_empty_microphone_channel.get_samples().set_values(np.array([100.0, 50, 10.25], dtype=np.int))
        self.non_empty_microphone_channel.set_sensor_description("foo")
        self.non_empty_microphone_channel.set_sample_rate(10.0)
        self.non_empty_microphone_channel.set_first_sample_timestamp(1)
        # self.non_empty_microphone_channel.get_samples().set_samples(np.array(list(range(10))))
        self.non_empty_microphone_channel.get_metadata().set_metadata({"foo": "bar"})

    def test_get_proto_empty(self):
        pass


class TestCommonSamples(unittest.TestCase):
    def setUp(self) -> None:
        self.non_empty_common_payload = common.SamplePayload.new()
        self.non_empty_common_payload.set_unit(common.Unit.METERS)
        self.non_empty_common_payload.set_values(np.array([10, 20, 30, 40]), True)
        self.empty_common_payload = common.SamplePayload.new()

    def test_validate_common_payload(self):
        error_list = common.validate_sample_payload(self.non_empty_common_payload)
        self.assertEqual(error_list, [])
        error_list = common.validate_sample_payload(self.empty_common_payload)
        self.assertNotEqual(error_list, [])


class TestCommonTiming(unittest.TestCase):
    def setUp(self) -> None:
        self.non_empty_time_payload = common.TimingPayload.new()
        self.non_empty_time_payload.set_default_unit()
        self.non_empty_time_payload.set_timestamps(np.array([1000, 2000, 3500, 5000]), True)
        self.empty_time_payload = common.TimingPayload.new()

    def test_validate_timing_payload(self):
        error_list = common.validate_timing_payload(self.non_empty_time_payload)
        self.assertEqual(error_list, [])
        error_list = common.validate_timing_payload(self.empty_time_payload)
        self.assertNotEqual(error_list, [])


class TestCommonMetadata(unittest.TestCase):
    pass


class TestSummaryStatistics(unittest.TestCase):
    def setUp(self) -> None:
        self.data_values = np.array([10, 20, 30, 40])
        self.empty_stats = common.SummaryStatistics.new()
        self.non_empty_stats = common.SummaryStatistics.new()
        self.non_empty_stats.update_from_values(self.data_values)

    def test_validate_summary_statistics(self):
        error_list = common.validate_summary_statistics(self.non_empty_stats)
        self.assertEqual(error_list, [])
        error_list = common.validate_summary_statistics(self.empty_stats)
        self.assertNotEqual(error_list, [])


class TestCommonMethods(unittest.TestCase):
    def test_none_or_empty_none(self):
        self.assertTrue(common.none_or_empty(None))

    def test_none_or_empty_str(self):
        self.assertTrue(common.none_or_empty(""))
        self.assertFalse(common.none_or_empty("foo"))

    def test_none_or_empty_list(self):
        self.assertTrue(common.none_or_empty([]))
        self.assertFalse(common.none_or_empty([1]))

    def test_none_or_empty_array(self):
        self.assertTrue(common.none_or_empty(common.EMPTY_ARRAY))
        self.assertFalse(common.none_or_empty(np.array([1])))

    def test_is_protobuf_numerical_type_none(self):
        self.assertFalse(common.is_protobuf_numerical_type(None))

    def test_is_protobuf_numerical_type_ok(self):
        self.assertTrue(common.is_protobuf_numerical_type(1))
        self.assertTrue(common.is_protobuf_numerical_type(1.0))

    def test_is_protobuf_numerical_type_not_ok(self):
        self.assertFalse(common.is_protobuf_numerical_type("foo"))
        self.assertFalse(common.is_protobuf_numerical_type([]))
        self.assertFalse(common.is_protobuf_numerical_type(self))

    def test_is_protobuf_repeated_numerical_type(self):
        self.assertFalse(common.is_protobuf_repeated_numerical_type(None))
        self.assertFalse(common.is_protobuf_repeated_numerical_type(1))
        self.assertFalse(common.is_protobuf_repeated_numerical_type(1.0))
        self.assertFalse(common.is_protobuf_repeated_numerical_type("foo"))
        self.assertFalse(common.is_protobuf_repeated_numerical_type([]))
        self.assertTrue(common.is_protobuf_repeated_numerical_type(np.array([])))
        self.assertTrue(common.is_protobuf_repeated_numerical_type(np.array([1.0])))
        self.assertTrue(common.is_protobuf_repeated_numerical_type(np.array([1.0, 2.0])))

    # def test_mean_sample_rate_hz_from_sample_ts_us(self):
        # ts_us: np.ndarray = np.arange(0, 10_000_000, step=1_000_000)
        # self.assertAlmostEqual(1.0, common.mean_sample_rate_hz_from_sample_ts_us(ts_us), delta=0.001)

    def test_lz4_compress_decompress(self):
        data = list(range(1000))
        data = list(map(str, data))
        data = "".join(data)
        data = data * 1000

        h = hash(data)
        compressed = common.lz4_compress(data.encode())
        decompressed = common.lz4_decompress(compressed)
        data = decompressed.decode()
        nh = hash(data)

        self.assertEqual(h, nh)
