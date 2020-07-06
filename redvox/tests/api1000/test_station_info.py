import unittest
import numpy as np
import redvox.api1000.wrapped_redvox_packet.station_information as station


class TestAppSettings(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_app_settings: station.AppSettings = station.AppSettings.new()
        self.non_empty_app_settings: station.AppSettings = station.AppSettings.new()
        self.non_empty_app_settings.get_additional_input_sensors().append_values([station.InputSensor.PRESSURE])
        self.non_empty_app_settings.set_audio_sampling_rate(station.AudioSamplingRate["HZ_80"])
        self.non_empty_app_settings.set_station_id("test_station")

    def test_validate_app_settings(self):
        error_list = station.validate_app_settings(self.non_empty_app_settings)
        self.assertEqual(error_list, [])
        error_list = station.validate_app_settings(self.empty_app_settings)
        self.assertNotEqual(error_list, [])


class TestStationMetrics(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_station_metrics: station.StationMetrics = station.StationMetrics.new()
        self.non_empty_station_metrics: station.StationMetrics = station.StationMetrics.new()
        self.non_empty_station_metrics.get_timestamps().set_default_unit()
        self.non_empty_station_metrics.get_timestamps().set_timestamps(np.array([1000, 2000, 3500, 5000]), True)

    def test_validate_station_metrics(self):
        error_list = station.validate_station_metrics(self.non_empty_station_metrics)
        self.assertEqual(error_list, [])
        error_list = station.validate_station_metrics(self.empty_station_metrics)
        self.assertNotEqual(error_list, [])


class TestStationInfo(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_station_info: station.StationInformation = station.StationInformation.new()
        self.non_empty_station_info: station.StationInformation = station.StationInformation.new()
        self.non_empty_station_info.set_id("test_station")
        self.non_empty_station_info.set_uuid("1234567890")
        self.non_empty_station_info.get_app_settings().get_additional_input_sensors().append_values(
            [station.InputSensor.AUDIO])
        self.non_empty_station_info.get_app_settings().set_audio_sampling_rate(station.AudioSamplingRate["HZ_80"])
        self.non_empty_station_info.get_app_settings().set_station_id("test_station")
        self.non_empty_station_info.get_station_metrics().get_timestamps().set_default_unit()
        self.non_empty_station_info.get_station_metrics().get_timestamps().set_timestamps(
            np.array([1000, 2000, 3500, 5000]), True)

    def test_validate_station_info(self):
        error_list = station.validate_station_information(self.non_empty_station_info)
        self.assertEqual(error_list, [])
        error_list = station.validate_station_information(self.empty_station_info)
        self.assertNotEqual(error_list, [])
