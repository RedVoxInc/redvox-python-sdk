import unittest
import numpy as np
import pandas as pd

from redvox.common import station_utils
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider


class StationLocationTest(unittest.TestCase):
    def setUp(self):
        self.station_loc = station_utils.StationLocation(1000, 1000, 1000, 1000, "USER", 1,
                                                         19.67, -155.55, 10.0, 0.0, 0.0, 4.0, 0.0, 0.0, 0.0)
        self.empty_loc = station_utils.StationLocation()

    def test_station_location_init(self):
        self.assertEqual(self.station_loc.lat_lon_timestamp, 1000)
        self.assertEqual(self.station_loc.altitude_timestamp, 1000)
        self.assertEqual(self.station_loc.speed_timestamp, 1000)
        self.assertEqual(self.station_loc.bearing_timestamp, 1000)
        self.assertEqual(self.station_loc.provider, "USER")
        self.assertEqual(self.station_loc.score, 1)
        self.assertEqual(self.station_loc.latitude, 19.67)
        self.assertEqual(self.station_loc.longitude, -155.55)
        self.assertEqual(self.station_loc.altitude, 10.0)
        self.assertEqual(self.station_loc.speed, 0.0)
        self.assertEqual(self.station_loc.bearing, 0.0)
        self.assertEqual(self.station_loc.horizontal_accuracy, 4.0)
        self.assertEqual(self.station_loc.vertical_accuracy, 0.0)
        self.assertEqual(self.station_loc.speed_accuracy, 0.0)
        self.assertEqual(self.station_loc.bearing_accuracy, 0.0)

        self.assertTrue(np.isnan(self.empty_loc.lat_lon_timestamp))
        self.assertTrue(np.isnan(self.empty_loc.longitude))

    def test_update_timestamps(self):
        self.station_loc.update_timestamps(1000)
        self.assertEqual(self.station_loc.altitude_timestamp, 2000)
        self.station_loc.update_timestamps(-1500)
        self.assertEqual(self.station_loc.bearing_timestamp, 500)

    def test_is_empty(self):
        self.assertFalse(self.station_loc.is_empty())
        self.assertTrue(self.empty_loc.is_empty())

    def test_station_location_from_data(self):
        data = station_utils.station_location_from_data(
            pd.Series([10000, LocationProvider(3), 20.0, 150.0, 33.0, 0.0, 45.0, 12.0, 3.0, 0.0, 15.0],
                      index=["timestamps", "location_provider", "latitude", "longitude", "altitude", "speed",
                             "bearing", "horizontal_accuracy", "vertical_accuracy", "speed_accuracy",
                             "bearing_accuracy"]))
        self.assertEqual(data.lat_lon_timestamp, 10000)
        self.assertEqual(data.latitude, 20.0)


class LocationDataTest(unittest.TestCase):
    def setUp(self):
        station_loc = station_utils.StationLocation(1000, 1000, 1000, 1000, "USER", 1,
                                                    19.67, -155.55, 10.0, 0.0, 0.0, 4.0, 0.0, 0.0, 0.0)
        station_loc_2 = station_utils.StationLocation(5000, 5000, 5000, 5000, "USER", 1,
                                                      19.37, -155.05, 20.0, 0.0, 8.0, 16.0, 4.0, 0.0, 6.0)
        self.loc_data = station_utils.LocationData(station_loc, [station_loc_2, station_loc])
        self.first_loc = station_utils.StationLocation(lat_lon_timestamp=1000, latitude=10.0, longitude=105.0)
        self.second_loc = station_utils.StationLocation(lat_lon_timestamp=500, latitude=12.0, longitude=107.0)
        self.third_loc = station_utils.StationLocation(lat_lon_timestamp=2000, latitude=14.0, longitude=109.0)
        self.fourth_loc = station_utils.StationLocation(lat_lon_timestamp=5000, latitude=16.0, longitude=111.0)
        self.fifth_loc = station_utils.StationLocation(lat_lon_timestamp=5500, latitude=18.0, longitude=113.0)
        self.sixth_loc = station_utils.StationLocation(lat_lon_timestamp=7500, latitude=20.0, longitude=115.0)
        self.seventh_loc = station_utils.StationLocation(lat_lon_timestamp=100000, latitude=40.0, longitude=117.0)
        self.last_loc = station_utils.StationLocation(lat_lon_timestamp=9000, latitude=80.0, longitude=119.0)
        self.empty_loc = station_utils.StationLocation()
        self.window_start = 1500
        self.window_end = 7500

    def test_location_data_init(self):
        self.assertEqual(len(self.loc_data.all_locations), 2)
        self.assertEqual(self.loc_data.std_latitude, 0.0)
        self.assertEqual(self.loc_data.std_longitude, 0.0)
        self.assertEqual(self.loc_data.std_altitude, 0.0)
        self.assertEqual(self.loc_data.std_speed, 0.0)
        self.assertEqual(self.loc_data.std_bearing, 0.0)
        self.assertEqual(self.loc_data.std_horizontal_accuracy, 0.0)
        self.assertEqual(self.loc_data.std_latitude, 0.0)
        self.assertEqual(self.loc_data.std_vertical_accuracy, 0.0)
        self.assertEqual(self.loc_data.std_speed_accuracy, 0.0)
        self.assertEqual(self.loc_data.std_bearing_accuracy, 0.0)
        self.assertEqual(self.loc_data.std_latitude, 0.0)
        self.assertTrue(np.isnan(self.loc_data.mean_latitude))
        self.assertTrue(np.isnan(self.loc_data.mean_longitude))
        self.assertTrue(np.isnan(self.loc_data.mean_altitude))
        self.assertTrue(np.isnan(self.loc_data.mean_speed))
        self.assertTrue(np.isnan(self.loc_data.mean_bearing))
        self.assertTrue(np.isnan(self.loc_data.mean_horizontal_accuracy))
        self.assertTrue(np.isnan(self.loc_data.mean_vertical_accuracy))
        self.assertTrue(np.isnan(self.loc_data.mean_speed_accuracy))
        self.assertTrue(np.isnan(self.loc_data.mean_bearing_accuracy))
        self.assertEqual(self.loc_data.mean_provider, "None")

    def test_update_timestamps(self):
        self.loc_data.update_timestamps(4000)
        self.assertEqual(self.loc_data.best_location.lat_lon_timestamp, 5000)
        self.assertEqual(self.loc_data.all_locations[0].lat_lon_timestamp, 9000)
        self.loc_data.update_timestamps(-2000)
        self.assertEqual(self.loc_data.best_location.lat_lon_timestamp, 3000)
        self.assertEqual(self.loc_data.all_locations[0].lat_lon_timestamp, 7000)

    def test_get_sorted_all_locations(self):
        sorted_list = self.loc_data.get_sorted_all_locations()
        self.assertEqual(len(sorted_list), 2)
        self.assertEqual(sorted_list[0].lat_lon_timestamp, 1000)

    def test_calc_mean_and_std_from_locations(self):
        self.loc_data.calc_mean_and_std_from_locations()
        self.assertAlmostEqual(self.loc_data.mean_latitude, 19.52, 2)
        self.assertEqual(self.loc_data.mean_longitude, -155.3)
        self.assertEqual(self.loc_data.mean_altitude, 15.0)
        self.assertEqual(self.loc_data.mean_speed, 0.0)
        self.assertEqual(self.loc_data.mean_bearing, 4.0)
        self.assertEqual(self.loc_data.mean_horizontal_accuracy, 10.0)
        self.assertEqual(self.loc_data.mean_vertical_accuracy, 2.0)
        self.assertEqual(self.loc_data.mean_speed_accuracy, 0.0)
        self.assertEqual(self.loc_data.mean_bearing_accuracy, 3.0)
        self.assertAlmostEqual(self.loc_data.std_latitude, 0.15, 2)
        self.assertEqual(self.loc_data.std_longitude, 0.25)
        self.assertEqual(self.loc_data.std_altitude, 5.0)
        self.assertEqual(self.loc_data.std_speed, 0.0)
        self.assertEqual(self.loc_data.std_bearing, 4.0)
        self.assertEqual(self.loc_data.std_horizontal_accuracy, 6.0)
        self.assertEqual(self.loc_data.std_vertical_accuracy, 2.0)
        self.assertEqual(self.loc_data.std_speed_accuracy, 0.0)
        self.assertEqual(self.loc_data.std_bearing_accuracy, 3.0)

    def test_update_window_locations(self):
        loc_data = station_utils.LocationData(all_locations=[self.first_loc, self.second_loc, self.third_loc,
                                                             self.fourth_loc, self.fifth_loc, self.sixth_loc,
                                                             self.seventh_loc, self.last_loc])
        loc_data.update_window_locations(self.window_start, self.window_end)
        self.assertEqual(len(loc_data.all_locations), 5)
        self.assertEqual(loc_data.all_locations[0].lat_lon_timestamp, 2000)

    def test_update_window_locations_outside_before_after(self):
        loc_data = station_utils.LocationData(all_locations=[self.first_loc, self.seventh_loc, self.second_loc,
                                                             self.last_loc])
        loc_data.update_window_locations(self.window_start, self.window_end)
        self.assertEqual(len(loc_data.all_locations), 2)
        self.assertEqual(loc_data.all_locations[1].lat_lon_timestamp, 9000)

    def test_update_window_locations_only_before(self):
        loc_data = station_utils.LocationData(all_locations=[self.first_loc, self.first_loc, self.second_loc])
        loc_data.update_window_locations(self.window_start, self.window_end)
        self.assertEqual(len(loc_data.all_locations), 2)
        self.assertEqual(loc_data.all_locations[0].lat_lon_timestamp, 1000)

    def test_update_window_locations_only_one(self):
        loc_data = station_utils.LocationData(all_locations=[self.fourth_loc])
        loc_data.update_window_locations(self.window_start, self.window_end)
        self.assertEqual(len(loc_data.all_locations), 1)
        self.assertEqual(loc_data.all_locations[0].lat_lon_timestamp, 5000)

    def test_update_window_locations_add_too_many_early(self):
        loc_data = station_utils.LocationData(all_locations=[self.fourth_loc, self.first_loc, self.second_loc])
        loc_data.update_window_locations(self.window_start, self.window_end)
        self.assertEqual(len(loc_data.all_locations), 2)
        self.assertEqual(loc_data.all_locations[0].lat_lon_timestamp, 5000)

    def test_update_window_locations_add_empty_to_valid(self):
        loc_data = station_utils.LocationData(all_locations=[self.fourth_loc, self.empty_loc])
        loc_data.update_window_locations(self.window_start, self.window_end)
        self.assertEqual(len(loc_data.all_locations), 1)
        self.assertEqual(loc_data.all_locations[0].lat_lon_timestamp, 5000)


class DataPacketTest(unittest.TestCase):
    def setUp(self):
        station_loc = station_utils.StationLocation(1000, 1000, 1000, 1000, "USER", 1,
                                                    19.67, -155.55, 10.0, 0.0, 0.0, 4.0, 0.0, 0.0, 0.0)
        self.data_packet = station_utils.DataPacket(50000000., 500., 32768, 40.96, 1000., 40961000.,
                                                    np.array([10000., 12001., 12002., 13000., 13001., 15002.]),
                                                    500.0, 3000.0, best_location=station_loc)

    def test_data_packet_init(self):
        self.assertEqual(self.data_packet.server_timestamp, 50000000.)
        self.assertEqual(self.data_packet.packet_app_start_timestamp, 500.)
        self.assertEqual(self.data_packet.packet_num_audio_samples, 32768)
        self.assertEqual(self.data_packet.packet_duration_s, 40.96)
        self.assertEqual(self.data_packet.data_start_timestamp, 1000.)
        self.assertEqual(self.data_packet.data_end_timestamp, 40961000.)
        self.assertEqual(len(self.data_packet.timesync), 6)
        self.assertEqual(self.data_packet.packet_best_latency, 500.0)
        self.assertEqual(self.data_packet.packet_best_offset, 3000.0)
        self.assertTrue(np.isnan(self.data_packet.sample_interval_to_next_packet))
        self.assertEqual(self.data_packet.best_location.lat_lon_timestamp, 1000)

    def test_expected_sample_interval_s(self):
        self.assertEqual(self.data_packet.expected_sample_interval_s(), 0.00125)


class StationTimingTest(unittest.TestCase):
    def setUp(self):
        self.station_timing = station_utils.StationTiming(100., 800., 500., 1.0, 2.0, 500.0, 3000.0, 3500.0, 500.0)

    def test_station_timing_init(self):
        self.assertEqual(self.station_timing.station_start_timestamp, 100.)
        self.assertEqual(self.station_timing.audio_sample_rate_hz, 800.)
        self.assertEqual(self.station_timing.station_first_data_timestamp, 500.)
        self.assertEqual(self.station_timing.episode_start_timestamp_s, 1.)
        self.assertEqual(self.station_timing.episode_end_timestamp_s, 2.)
        self.assertEqual(self.station_timing.station_best_latency, 500.)
        self.assertEqual(self.station_timing.station_best_offset, 3000.)
        self.assertEqual(self.station_timing.station_mean_offset, 3500.)
        self.assertEqual(self.station_timing.station_std_offset, 500.)


class StationMetadataTest(unittest.TestCase):
    def setUp(self):
        station_timing = station_utils.StationTiming(100., 800., 500., 1.0, 2.0, 500.0, 3000.0, 3500.0, 500.0)
        self.metadata = station_utils.StationMetadata("1234567890", "test_make", "test_model", False, "test_os",
                                                      "test_os_version", "Redvox", "test_app_version", False,
                                                      station_timing, 1.0, "TEST", "test_name", "test_location_name",
                                                      "TST", "test_encoding")

    def test_station_metadata_init(self):
        self.assertEqual(self.metadata.station_id, "1234567890")
        self.assertEqual(self.metadata.station_uuid, "1234567890")
        self.assertEqual(self.metadata.station_make, "test_make")
        self.assertEqual(self.metadata.station_model, "test_model")
        self.assertFalse(self.metadata.station_timing_is_corrected)
        self.assertEqual(self.metadata.station_os, "test_os")
        self.assertEqual(self.metadata.station_os_version, "test_os_version")
        self.assertEqual(self.metadata.station_app, "Redvox")
        self.assertEqual(self.metadata.station_app_version, "test_app_version")
        self.assertFalse(self.metadata.is_mic_scrambled)
        self.assertEqual(self.metadata.station_calib, 1.0)
        self.assertEqual(self.metadata.station_network_name, "TEST")
        self.assertEqual(self.metadata.station_name, "test_name")
        self.assertEqual(self.metadata.station_location_name, "test_location_name")
        self.assertEqual(self.metadata.station_channel_name, "TST")
        self.assertEqual(self.metadata.station_channel_encoding, "test_encoding")
