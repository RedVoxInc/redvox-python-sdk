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
        self.non_empty_microphone_channel.get_metadata().set_metadata({"foo": "bar"})

    def test_get_proto_empty(self):
        empty_proto = self.empty_microphone_channel.get_proto()
        self.assertEqual(empty_proto.sample_rate, 0.0)
        self.assertEqual(empty_proto.metadata, {})

    def test_get_proto(self):
        full_proto = self.non_empty_microphone_channel.get_proto()
        self.assertEqual(full_proto.sample_rate, 10.0)
        self.assertEqual(len(full_proto.metadata), 1)

    def test_get_metadata(self):
        meta_data = self.non_empty_microphone_channel.get_metadata()
        self.assertEqual(meta_data.get_metadata_count(), 1)

    def test_as_json(self):
        json = self.non_empty_microphone_channel.as_json()
        self.assertTrue(len(json) > 0)

    def test_as_dict(self):
        test_dict = self.non_empty_microphone_channel.as_dict()
        self.assertEqual(test_dict["sampleRate"], 10.0)
        self.assertEqual(test_dict["sensorDescription"], "foo")

    def test_as_bytes(self):
        test_bytes = self.non_empty_microphone_channel.as_bytes()
        self.assertTrue(len(test_bytes) > 0)

    def test_as_compressed_bytes(self):
        compressed_bytes = self.non_empty_microphone_channel.as_compressed_bytes()
        self.assertTrue(len(compressed_bytes) > 0)


class TestCommonMetadata(unittest.TestCase):
    def setUp(self) -> None:
        self.meta_dict = common.Metadata({"foo": "bar", "baz": "number", "test": "data"})
        self.empty_dict = common.Metadata({})

    def test_get_metadata_count(self):
        count = self.meta_dict.get_metadata_count()
        self.assertEqual(count, 3)
        zero_count = self.empty_dict.get_metadata_count()
        self.assertEqual(zero_count, 0)

    def test_get_metadata(self):
        meta_data = self.meta_dict.get_metadata()
        self.assertEqual(meta_data["foo"], "bar")
        self.assertEqual(meta_data["baz"], "number")

    def test_set_metadata(self):
        self.meta_dict.set_metadata({"oof": "rab", "zab": "numbers"})
        count = self.meta_dict.get_metadata_count()
        self.assertEqual(count, 2)
        meta_data = self.meta_dict.get_metadata()
        self.assertEqual(meta_data["oof"], "rab")

    def test_append_metadata(self):
        self.meta_dict.append_metadata("bing", "bong")
        count = self.meta_dict.get_metadata_count()
        self.assertEqual(count, 4)

    def test_clear_metadata(self):
        self.meta_dict.clear_metadata()
        count = self.meta_dict.get_metadata_count()
        self.assertEqual(count, 0)
        meta_data = self.meta_dict.get_metadata()
        self.assertEqual(meta_data, {})


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


class TestSummaryStatistics(unittest.TestCase):
    def setUp(self) -> None:
        self.data_values = np.array([10, 20, 30, 40])
        self.empty_stats = common.SummaryStatistics.new()
        self.non_empty_stats = common.SummaryStatistics.new()
        self.non_empty_stats.update_from_values(self.data_values)

    def test_get_set_count(self):
        count = self.non_empty_stats.get_count()
        self.assertEqual(count, 4)
        zero_count = self.empty_stats.get_count()
        self.assertEqual(zero_count, 0)
        self.empty_stats.set_count(100)
        zero_count = self.empty_stats.get_count()
        self.assertEqual(zero_count, 100)

    def test_get_set_mean(self):
        mean = self.non_empty_stats.get_mean()
        self.assertEqual(mean, 25)
        zero_mean = self.empty_stats.get_mean()
        self.assertEqual(zero_mean, 0)
        self.empty_stats.set_mean(100)
        zero_mean = self.empty_stats.get_mean()
        self.assertEqual(zero_mean, 100)

    def test_get_set_median(self):
        median = self.non_empty_stats.get_median()
        self.assertEqual(median, 25)
        zero_median = self.empty_stats.get_median()
        self.assertEqual(zero_median, 0)
        self.empty_stats.set_median(100)
        zero_median = self.empty_stats.get_median()
        self.assertEqual(zero_median, 100)

    def test_get_set_mode(self):
        mode = self.non_empty_stats.get_mode()
        self.assertEqual(mode, 10)
        zero_mode = self.empty_stats.get_mode()
        self.assertEqual(zero_mode, 0)
        self.empty_stats.set_mode(100)
        zero_mode = self.empty_stats.get_mode()
        self.assertEqual(zero_mode, 100)

    def test_get_set_variance(self):
        variance = self.non_empty_stats.get_variance()
        self.assertEqual(variance, 125)
        zero_variance = self.empty_stats.get_variance()
        self.assertEqual(zero_variance, 0)
        self.empty_stats.set_variance(100)
        zero_variance = self.empty_stats.get_variance()
        self.assertEqual(zero_variance, 100)

    def test_get_set_min(self):
        min_val = self.non_empty_stats.get_min()
        self.assertEqual(min_val, 10)
        zero_min = self.empty_stats.get_min()
        self.assertEqual(zero_min, 0)
        self.empty_stats.set_min(100)
        zero_min = self.empty_stats.get_min()
        self.assertEqual(zero_min, 100)

    def test_get_set_max(self):
        max_val = self.non_empty_stats.get_max()
        self.assertEqual(max_val, 40)
        zero_max = self.empty_stats.get_max()
        self.assertEqual(zero_max, 0)
        self.empty_stats.set_max(100)
        zero_max = self.empty_stats.get_max()
        self.assertEqual(zero_max, 100)

    def test_get_set_range(self):
        data_range = self.non_empty_stats.get_range()
        self.assertEqual(data_range, 30)
        zero_range = self.empty_stats.get_range()
        self.assertEqual(zero_range, 0)
        self.empty_stats.set_range(100)
        zero_range = self.empty_stats.get_range()
        self.assertEqual(zero_range, 100)

    def test_update_from_values(self):
        new_vals = np.array([100, 200, 300])
        self.non_empty_stats.update_from_values(new_vals)
        self.assertEqual(self.non_empty_stats.get_mean(), 200)
        self.assertEqual(self.non_empty_stats.get_min(), 100)
        self.assertEqual(self.non_empty_stats.get_range(), 200)

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
