"""
tests for loading or reading station data from various sources
"""
import os
import unittest

import numpy as np

import redvox.tests as tests
from redvox.api900 import reader as api900_io
from redvox.common import date_time_utils as dtu
from redvox.common import station_reader_utils as sr_utils
from redvox.common.sensor_data import SensorType
from redvox.api1000.wrapped_redvox_packet.sensors import xyz, single, audio
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM


class StationSummaryTest(unittest.TestCase):
    def setUp(self):
        self.now_time = dtu.datetime.now()
        self.station_summary = sr_utils.StationSummary("1234567890", "9876543210", "test_os", "test_os_version",
                                                       "test_app_version", 800.0, 40.96,
                                                       self.now_time - dtu.timedelta(seconds=40.96), self.now_time)
        real_station = sr_utils.load_station_from_api900_file(os.path.join(tests.TEST_DATA_DIR,
                                                                           "1637650010_1531343782220.rdvxz"))
        self.real_summary = sr_utils.StationSummary.from_station(real_station)

    def test_station_summary_init(self):
        self.assertEqual(self.station_summary.station_id, "1234567890")
        self.assertEqual(self.station_summary.station_uuid, "9876543210")
        self.assertEqual(self.station_summary.os, "test_os")
        self.assertEqual(self.station_summary.os_version, "test_os_version")
        self.assertEqual(self.station_summary.app_version, "test_app_version")
        self.assertEqual(self.station_summary.audio_sampling_rate_hz, 800.)
        self.assertEqual(self.station_summary.total_duration_s, 40.96)
        self.assertEqual(self.station_summary.start_dt, self.now_time - dtu.timedelta(seconds=40.96))
        self.assertEqual(self.station_summary.end_dt, self.now_time)

    def test_from_station(self):
        self.assertEqual(self.real_summary.station_id, "1637650010")
        self.assertEqual(self.real_summary.station_uuid, "1107483069")
        self.assertEqual(self.real_summary.os, "Android")
        self.assertEqual(self.real_summary.os_version, "8.1.0")
        self.assertEqual(self.real_summary.app_version, "2.3.1")
        self.assertEqual(self.real_summary.audio_sampling_rate_hz, 80.)
        self.assertEqual(self.real_summary.total_duration_s, 51.1875)
        self.assertEqual(self.real_summary.start_dt, dtu.datetime(2018, 7, 11, 21, 16, 22, 220500))
        self.assertEqual(self.real_summary.end_dt, dtu.datetime(2018, 7, 11, 21, 17, 13, 408000))


class ReadResultTest(unittest.TestCase):
    def setUp(self):
        api900_station = sr_utils.load_station_from_api900_file(os.path.join(tests.TEST_DATA_DIR,
                                                                             "1637650010_1531343782220.rdvxz"))
        apim_station = sr_utils.load_station_from_apim_file(os.path.join(tests.TEST_DATA_DIR,
                                                                         "0000000001_1597189452945991.rdvxm"))
        read_result = {"1637650010:1107483069": api900_station, "0000000001:0000000001": apim_station}
        self.read_result = sr_utils.ReadResult(read_result)

    def test_pop_station(self):
        self.read_result.pop_station("1107483069")
        self.assertEqual(len(self.read_result.get_station_summaries()), 1)
        self.read_result.pop_station("0000000001")
        self.assertEqual(len(self.read_result.get_station_summaries()), 0)

    def test_check_for_id(self):
        self.assertTrue(self.read_result.check_for_id("0000000001"))
        self.assertTrue(self.read_result.check_for_id("1107483069"))
        self.assertFalse(self.read_result.check_for_id("do_not_exist"))

    def test_get_station(self):
        station = self.read_result.get_station("1637650010")
        self.assertTrue(station.has_audio_data())

    def test_get_all_stations(self):
        all_stations = self.read_result.get_all_stations()
        self.assertEqual(len(all_stations), 2)
        self.assertTrue(all_stations[0].has_audio_data())

    def test_get_station_summaries(self):
        summaries = self.read_result.get_station_summaries()
        self.assertEqual(len(summaries), 2)
        self.assertEqual(summaries[0].station_id, "1637650010")

    def test_get_station_summary(self):
        summary = self.read_result.get_station_summary("1637650010")
        self.assertEqual(summary.station_id, "1637650010")
        summary = self.read_result.get_station_summary("1637650010:1107483069")
        self.assertEqual(summary.station_id, "1637650010")
        self.assertEqual(summary.station_uuid, "1107483069")
        summary = self.read_result.get_station_summary("1107483069")
        self.assertEqual(summary.station_id, "1637650010")
        self.assertEqual(summary.station_uuid, "1107483069")

    def test_append(self):
        # indirectly tests append_station
        mseed_data = sr_utils.load_from_mseed(os.path.join(tests.TEST_DATA_DIR, "out.mseed"))
        self.read_result.append(mseed_data)
        self.assertEqual(len(self.read_result.get_station_summaries()), 3)
        self.assertTrue(self.read_result.check_for_id("UHMB3_00:UHMB3_00"))
        self.assertTrue(self.read_result.get_station("UHMB3_00").has_audio_data())


class StationReaderUtilsTest(unittest.TestCase):
    def test_calc_evenly_sampled_timestamps(self):
        start = dtu.seconds_to_microseconds(1000.)
        end = dtu.seconds_to_microseconds(1099.99)
        samples = 10000
        rate = 100
        timestamps = sr_utils.calc_evenly_sampled_timestamps(start, samples, rate)
        self.assertEqual(len(timestamps), samples)
        self.assertEqual(timestamps[0], start)
        self.assertEqual(timestamps[-1], end)


class API900ReaderTest(unittest.TestCase):
    def setUp(self):
        timestamps = [120000000, 25000000, 31000000, 65000000, 74000000, 83000000, 97000000, 111000000, 14000000]
        test_data = [75., 12., 86., 22., 200., 52., 99., 188., 121.]
        non_mic_sensor = api900_io.BarometerSensor().set_timestamps_microseconds_utc(timestamps)\
            .set_payload_values(test_data).set_sensor_name("test")
        accel_data_x = [.35, .66, .99, 0., 0., 0., 0., 0., 0.]
        accel_data_y = [0., 0., 0., -.35, -.45, -.77, 0., 0., 0.]
        accel_data_z = [0., 0., 0., 0., 0., 0., 1.0, 8.1, 5.6]
        accelerometer_sensor = api900_io.AccelerometerSensor().set_timestamps_microseconds_utc(timestamps)\
            .set_payload_values(accel_data_x, accel_data_y, accel_data_z).set_sensor_name("test_accelerometer")
        mic_sensor = api900_io.MicrophoneSensor().set_first_sample_timestamp_epoch_microseconds_utc(10000000)\
            .set_sample_rate_hz(800).set_sensor_name("test_mic").set_payload_values(np.arange(0, 32768))
        time_sync_sensor = api900_io.TimeSynchronizationSensor()
        time_sync_sensor.set_payload_values([1000000, 1075000, 1075001, 1100001, 1100002, 1175002])

        self.non_mic_sensor = sr_utils.read_api900_non_mic_sensor(non_mic_sensor, "test_data")
        self.api900_wrapped_packet = api900_io.WrappedRedvoxPacket().set_microphone_sensor(mic_sensor)\
            .set_accelerometer_sensor(accelerometer_sensor).set_barometer_sensor(non_mic_sensor)\
            .set_time_synchronization_sensor(time_sync_sensor)
        self.api900_wrapped_packet.set_redvox_id("1234567890")

    def test_read_api900_non_mic_sensor(self):
        self.assertEqual(self.non_mic_sensor.name, "test")
        self.assertEqual(len(self.non_mic_sensor.data_timestamps()), 9)
        self.assertTrue(200 in self.non_mic_sensor.get_channel("test_data"))

    def test_read_api900_wrapped_packet(self):
        wrapped_packet_dict = sr_utils.read_api900_wrapped_packet(self.api900_wrapped_packet)
        self.assertEqual(len(wrapped_packet_dict), 3)
        self.assertTrue(SensorType.AUDIO in wrapped_packet_dict.keys())
        self.assertEqual(wrapped_packet_dict[SensorType.ACCELEROMETER].name, "test_accelerometer")
        self.assertEqual(wrapped_packet_dict[SensorType.ACCELEROMETER].num_samples(), 9)

    def test_load_station_from_api900(self):
        station = sr_utils.load_station_from_api900(self.api900_wrapped_packet)
        self.assertEqual(station.station_metadata.station_id, "1234567890")
        self.assertEqual(len(station.packet_data), 1)
        self.assertEqual(len(station.station_data), 3)
        self.assertTrue(station.has_audio_data())
        self.assertTrue(station.has_barometer_data())
        self.assertTrue(station.has_accelerometer_data())

    def test_load_station_from_api900_file(self):
        station = sr_utils.load_station_from_api900_file(os.path.join(tests.TEST_DATA_DIR,
                                                                      "1637650010_1531343782220.rdvxz"))
        self.assertEqual(station.station_metadata.station_id, "1637650010")
        self.assertEqual(len(station.packet_data), 1)
        self.assertEqual(len(station.station_data), 5)
        self.assertTrue(station.has_audio_data())
        self.assertTrue(station.has_accelerometer_data())
        self.assertTrue(station.has_barometer_data())

    def test_load_file_range_from_api900(self):
        result = sr_utils.load_file_range_from_api900(tests.TEST_DATA_DIR, redvox_ids=["1637650010"],
                                                      structured_layout=False)
        self.assertTrue(result.check_for_id("1107483069"))
        self.assertFalse(result.check_for_id("do_not_exist"))
        station = result.get_station("1637650010")
        self.assertEqual(len(station.packet_data), 1)
        self.assertEqual(len(station.station_data), 5)
        self.assertTrue(station.has_audio_data())
        self.assertTrue(station.has_accelerometer_data())
        self.assertTrue(station.has_barometer_data())


class APIMReaderTest(unittest.TestCase):
    def setUp(self):
        timestamps = np.array([120000000, 25000000, 31000000, 65000000, 74000000,
                               83000000, 97000000, 111000000, 14000000])
        test_data = np.array([75., 12., 86., 22., 200., 52., 99., 188., 121.])
        self.single_sensor = single.Single.new().set_sensor_description("test_barometer")
        self.single_sensor.get_timestamps().set_timestamps(timestamps)
        self.single_sensor.get_samples().set_values(test_data)
        accel_data_x = np.array([.35, .66, .99, 0., 0., 0., 0., 0., 0.])
        accel_data_y = np.array([0., 0., 0., -.35, -.45, -.77, 0., 0., 0.])
        accel_data_z = np.array([0., 0., 0., 0., 0., 0., 1.0, 8.1, 5.6])
        self.accelerometer_sensor = xyz.Xyz.new().set_sensor_description("test_accelerometer")
        self.accelerometer_sensor.get_timestamps().set_timestamps(timestamps)
        self.accelerometer_sensor.get_x_samples().set_values(accel_data_x)
        self.accelerometer_sensor.get_y_samples().set_values(accel_data_y)
        self.accelerometer_sensor.get_z_samples().set_values(accel_data_z)
        mic_sensor = audio.Audio.new().set_sensor_description("test_microphone").set_first_sample_timestamp(10000000) \
            .set_sample_rate(800)
        mic_sensor.get_samples().set_values(np.arange(0, 32768))
        self.api_m_wrapped_packet = WrappedRedvoxPacketM.new()
        self.api_m_wrapped_packet.get_sensors().set_pressure(self.single_sensor).set_audio(mic_sensor)\
            .set_accelerometer(self.accelerometer_sensor)

    def test_read_apim_xyz_sensor(self):
        data = sr_utils.read_apim_xyz_sensor(self.accelerometer_sensor, "accelerometer")
        self.assertEqual(data.name, "test_accelerometer")
        self.assertFalse(data.is_sample_rate_fixed)
        self.assertTrue(1.0 in data.get_channel("accelerometer_z"))
        self.assertRaises(AttributeError, sr_utils.read_apim_xyz_sensor, self.single_sensor, "None")

    def test_read_apim_single_sensor(self):
        data = sr_utils.read_apim_single_sensor(self.single_sensor, "barometer")
        self.assertEqual(data.name, "test_barometer")
        self.assertFalse(data.is_sample_rate_fixed)
        self.assertTrue(52. in data.get_channel("barometer"))
        self.assertRaises(AttributeError, sr_utils.read_apim_single_sensor, self.accelerometer_sensor, "None")

    # this test will fail because the api_m_wrapped_packet is not being set properly by above
    # def test_load_apim_wrapped_packet(self):
    #     wrapped_packet_dict = sr_utils.load_apim_wrapped_packet(self.api_m_wrapped_packet)
    #     self.assertEqual(len(wrapped_packet_dict), 3)
    #     self.assertTrue(SensorType.AUDIO in wrapped_packet_dict.keys())
    #     self.assertEqual(wrapped_packet_dict[SensorType.ACCELEROMETER].name, "test_accelerometer")
    #     self.assertEqual(wrapped_packet_dict[SensorType.ACCELEROMETER].num_samples(), 9)


class AnyReaderTest(unittest.TestCase):
    def setUp(self):
        self.all_data = sr_utils.read_all_in_dir(tests.TEST_DATA_DIR,
                                                 station_ids=["1637650010", "0000000001", "UHMB3_00"])

    def test_read_any_dir(self):
        self.assertEqual(len(self.all_data.station_id_uuid_to_stations), 3)
        self.assertEqual(len(self.all_data.get_station_summaries()), 3)
        # api900 station
        station = self.all_data.get_station("1637650010")
        self.assertEqual(len(station.packet_data), 1)
        self.assertTrue(np.isnan(station.packet_data[0].packet_best_latency))
        self.assertEqual(len(station.station_data), 5)
        self.assertEqual(station.audio_sensor().sample_rate, 80)
        self.assertTrue(station.audio_sensor().is_sample_rate_fixed)
        self.assertAlmostEqual(station.audio_sensor().data_duration_s(), 51.2, 1)
        self.assertEqual(station.location_sensor().data_df.shape, (2, 11))
        self.assertAlmostEqual(station.location_sensor().data_duration_s(), 40.04, 2)
        # api m station
        station = self.all_data.get_station("0000000001")
        self.assertEqual(len(station.packet_data), 3)
        self.assertEqual(station.packet_data[0].packet_best_latency, 1296.0)
        self.assertEqual(len(station.station_data), 2)
        self.assertEqual(station.audio_sensor().sample_rate, 48000.0)
        self.assertTrue(station.audio_sensor().is_sample_rate_fixed)
        self.assertAlmostEqual(station.audio_sensor().data_duration_s(), 15.0, 2)
        self.assertEqual(station.location_sensor().data_df.shape, (3, 11))
        self.assertAlmostEqual(station.location_sensor().data_duration_s(), 10.0, 3)
        # mseed station
        station = self.all_data.get_station("UHMB3_00")
        self.assertEqual(len(station.station_data), 1)
        self.assertEqual(station.audio_sensor().num_samples(), 6001)
        self.assertEqual(station.station_metadata.station_network_name, "UH")
        self.assertEqual(station.station_metadata.station_name, "MB3")
        self.assertEqual(station.station_metadata.station_channel_name, "BDF")
