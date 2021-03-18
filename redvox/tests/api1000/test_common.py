import unittest

import numpy as np

import redvox.api1000.common.lz4
import redvox.api1000.common.common as common
import redvox.api1000.common.generic
import redvox.api1000.common.metadata
import redvox.api1000.common.typing
import redvox.api1000.wrapped_redvox_packet.sensors.audio as microphone


class TestCommonProtoBase(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_microphone_channel: microphone.Audio = microphone.Audio.new()
        self.non_empty_microphone_channel: microphone.Audio = microphone.Audio.new()
        self.non_empty_microphone_channel.get_samples().set_unit(common.Unit['DECIBEL'])
        self.non_empty_microphone_channel.get_samples().set_values(np.array([100.0, 50, 10.25], dtype=int))
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
        self.meta_dict = redvox.api1000.common.metadata.Metadata({"foo": "bar", "baz": "number", "test": "data"})
        self.empty_dict = redvox.api1000.common.metadata.Metadata({})

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


class TestCommonSample(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_sample_payload = common.SamplePayload.new()
        self.non_empty_sample_payload = common.SamplePayload.new()
        self.non_empty_sample_payload.set_unit(common.Unit.METERS)
        self.non_empty_sample_payload.set_values(np.array([10, 20, 30, 40]), True)

    def test_get_set_unit(self):
        unit = self.non_empty_sample_payload.get_unit()
        self.assertEqual(unit, common.Unit.METERS)
        zero_unit = self.empty_sample_payload.get_unit()
        self.assertEqual(zero_unit, common.Unit.UNKNOWN)
        self.empty_sample_payload.set_unit(common.Unit.METERS)
        zero_unit = self.empty_sample_payload.get_unit()
        self.assertEqual(zero_unit, common.Unit.METERS)

    def test_get_values_count(self):
        value_count = self.non_empty_sample_payload.get_values_count()
        self.assertEqual(value_count, 4)
        zero_count = self.empty_sample_payload.get_values_count()
        self.assertEqual(zero_count, 0)

    def test_get_set_values(self):
        values = self.non_empty_sample_payload.get_values()
        self.assertEqual(values[0], 10)
        self.assertEqual(len(values), 4)
        zero_values = self.empty_sample_payload.get_values()
        self.assertEqual(len(zero_values), 0)
        self.empty_sample_payload.set_values(np.array([5, 4, 3, 2, 1]))
        zero_values = self.empty_sample_payload.get_values()
        self.assertEqual(zero_values[0], 5)
        self.assertEqual(len(zero_values), 5)

    def test_append_value(self):
        self.non_empty_sample_payload.append_value(50, True)
        values = self.non_empty_sample_payload.get_values()
        self.assertEqual(values[-1], 50)
        self.assertEqual(len(values), 5)

    def test_append_values(self):
        self.non_empty_sample_payload.append_values(np.array([50, 60, 70]), True)
        values = self.non_empty_sample_payload.get_values()
        self.assertEqual(values[-1], 70)
        self.assertEqual(len(values), 7)

    def test_clear_values(self):
        self.non_empty_sample_payload.clear_values()
        zero_values = self.non_empty_sample_payload.get_values()
        self.assertEqual(len(zero_values), 0)
        zero_count = self.non_empty_sample_payload.get_values_count()
        self.assertEqual(zero_count, 0)

    def test_get_summary_statistics(self):
        stats = self.non_empty_sample_payload.get_summary_statistics()
        self.assertEqual(stats.get_count(), 4)
        self.assertEqual(stats.get_mean(), 25)
        zero_stats = self.empty_sample_payload.get_summary_statistics()
        self.assertEqual(zero_stats.get_count(), 0)
        self.assertEqual(zero_stats.get_mean(), 0)

    def test_validate_sample_payload(self):
        error_list = common.validate_sample_payload(self.non_empty_sample_payload)
        self.assertEqual(error_list, [])
        error_list = common.validate_sample_payload(self.empty_sample_payload)
        self.assertNotEqual(error_list, [])


class TestCommonTiming(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_time_payload = common.TimingPayload.new()
        self.non_empty_time_payload = common.TimingPayload.new()
        self.non_empty_time_payload.set_default_unit()
        self.non_empty_time_payload.set_timestamps(np.array([1000, 2000, 3500, 5000]), True)

    def test_get_set_unit(self):
        unit = self.non_empty_time_payload.get_unit()
        self.assertEqual(unit, common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        zero_unit = self.empty_time_payload.get_unit()
        self.assertEqual(zero_unit, common.Unit.UNKNOWN)
        self.empty_time_payload.set_unit(common.Unit.METERS)
        zero_unit = self.empty_time_payload.get_unit()
        self.assertEqual(zero_unit, common.Unit.METERS)

    def test_get_timestamps_count(self):
        count = self.non_empty_time_payload.get_timestamps_count()
        self.assertEqual(count, 4)
        zero_count = self.empty_time_payload.get_timestamps_count()
        self.assertEqual(zero_count, 0)

    def test_get_set_timestamps(self):
        timestamps = self.non_empty_time_payload.get_timestamps()
        self.assertEqual(timestamps[0], 1000)
        self.assertEqual(len(timestamps), 4)
        zero_timestamps = self.empty_time_payload.get_timestamps()
        self.assertEqual(len(zero_timestamps), 0)
        self.empty_time_payload.set_timestamps(np.array([100, 500, 900, 2000]))
        zero_timestamps = self.empty_time_payload.get_timestamps()
        self.assertEqual(zero_timestamps[0], 100)
        self.assertEqual(len(zero_timestamps), 4)

    def test_append_timestamp(self):
        self.non_empty_time_payload.append_timestamp(6700, True)
        values = self.non_empty_time_payload.get_timestamps()
        self.assertEqual(values[-1], 6700)
        self.assertEqual(len(values), 5)

    def test_append_timestamps(self):
        self.non_empty_time_payload.append_timestamps(np.array([6500, 8200, 9900]), True)
        values = self.non_empty_time_payload.get_timestamps()
        self.assertEqual(values[-1], 9900)
        self.assertEqual(len(values), 7)

    def test_clear_timestamps(self):
        self.non_empty_time_payload.clear_timestamps()
        zero_values = self.non_empty_time_payload.get_timestamps()
        self.assertEqual(len(zero_values), 0)
        zero_count = self.non_empty_time_payload.get_timestamps_count()
        self.assertEqual(zero_count, 0)

    def test_get_timestamp_statistics(self):
        stats = self.non_empty_time_payload.get_timestamp_statistics()
        self.assertEqual(stats.get_count(), 4)
        self.assertEqual(stats.get_mean(), 2875)
        zero_stats = self.empty_time_payload.get_timestamp_statistics()
        self.assertEqual(zero_stats.get_count(), 0)
        self.assertEqual(zero_stats.get_mean(), 0)

    def test_get_set_mean_sample_rate(self):
        sample_rate = self.non_empty_time_payload.get_mean_sample_rate()
        self.assertEqual(sample_rate, 750)
        zero_sample_rate = self.empty_time_payload.get_mean_sample_rate()
        self.assertEqual(zero_sample_rate, 0)
        self.empty_time_payload.set_mean_sample_rate(1000)
        zero_sample_rate = self.empty_time_payload.get_mean_sample_rate()
        self.assertEqual(zero_sample_rate, 1000)

    def test_get_set_stdev_sample_rate(self):
        sample_rate = self.non_empty_time_payload.get_stdev_sample_rate()
        self.assertAlmostEqual(sample_rate, 132.58, 2)
        zero_sample_rate = self.empty_time_payload.get_stdev_sample_rate()
        self.assertEqual(zero_sample_rate, 0)
        self.empty_time_payload.set_stdev_sample_rate(1000)
        zero_sample_rate = self.empty_time_payload.get_stdev_sample_rate()
        self.assertEqual(zero_sample_rate, 1000)

    def test_validate_timing_payload(self):
        error_list = common.validate_timing_payload(self.non_empty_time_payload)
        self.assertEqual(error_list, [])
        self.non_empty_time_payload.set_timestamps(np.array([40, 20, 99]))
        error_list = common.validate_timing_payload(self.non_empty_time_payload)
        self.assertNotEqual(error_list, [])
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

    def test_get_set_std_dev(self):
        std_dev = self.non_empty_stats.get_standard_deviation()
        self.assertAlmostEqual(std_dev, 11.18, 2)
        zero_std_dev = self.empty_stats.get_standard_deviation()
        self.assertEqual(zero_std_dev, 0)
        self.empty_stats.set_standard_deviation(100)
        zero_std_dev = self.empty_stats.get_standard_deviation()
        self.assertEqual(zero_std_dev, 100)

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
        self.assertTrue(redvox.api1000.common.typing.none_or_empty(None))

    def test_none_or_empty_str(self):
        self.assertTrue(redvox.api1000.common.typing.none_or_empty(""))
        self.assertFalse(redvox.api1000.common.typing.none_or_empty("foo"))

    def test_none_or_empty_list(self):
        self.assertTrue(redvox.api1000.common.typing.none_or_empty([]))
        self.assertFalse(redvox.api1000.common.typing.none_or_empty([1]))

    def test_none_or_empty_array(self):
        self.assertTrue(redvox.api1000.common.typing.none_or_empty(common.EMPTY_ARRAY))
        self.assertFalse(redvox.api1000.common.typing.none_or_empty(np.array([1])))

    def test_lz4_compress_decompress(self):
        data = list(range(1000))
        data = list(map(str, data))
        data = "".join(data)
        data = data * 1000

        h = hash(data)
        compressed = redvox.api1000.common.lz4.compress(data.encode())
        decompressed = redvox.api1000.common.lz4.decompress(compressed)
        data = decompressed.decode()
        nh = hash(data)

        self.assertEqual(h, nh)
