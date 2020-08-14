"""
Location Analyzer test module
"""

import unittest
import os
import pandas as pd
import numpy as np
import redvox.api900.location_analyzer as la
import redvox.api900.reader as reader
from redvox.tests import LA_TEST_DATA_DIR

SURVEY_LAT = 19.72833   # lat degrees of survey point
SURVEY_LON = -156.0592  # lon degrees of survey point
SURVEY_ALT = 11.9       # altitude in meters of survey point
SURVEY_BAR = 101.61     # barometer reading of survey point
SEA_PRESSURE = 101.92   # A fair estimate of the sea level pressure (in Hawaii)

SURVEY = {"lat": SURVEY_LAT, "lon": SURVEY_LON, "alt": SURVEY_ALT, "bar": SURVEY_BAR, "sea_bar": SEA_PRESSURE}
blacklist_point1 = {"lat": 19.735, "lon": -156.035, "alt": 26}
blacklist_point2 = {"lat": 19.700, "lon": -156.008, "alt": 143}
BLACKLIST = [blacklist_point1, blacklist_point2]


class LoadRedvoxTestFiles(unittest.TestCase):
    def setUp(self) -> None:
        self.redvox_packets = reader.read_rdvxz_file_range(LA_TEST_DATA_DIR)
        self.wrapped_packets = list(self.redvox_packets.values())


class DataHolderClassTests(unittest.TestCase):
    def setUp(self) -> None:
        self.new_dh = la.DataHolder("test")
        self.new_dh.set_data([12, -6, 0.0])

    def test_dh_init(self):
        self.assertEqual(self.new_dh.id, "test")
        self.assertIsNone(self.new_dh.best_value)

    def test_dh_add(self):
        self.new_dh.add(101.1)
        self.assertEqual(self.new_dh.get_len_data(), 4)

    def test_dh_set_data(self):
        self.new_dh.set_data([-300, 2.5, 0.0])
        self.assertEqual(self.new_dh.get_len_data(), 3)
        self.assertEqual(self.new_dh.get_data()[0], -300)

    def test_dh_replace_zeroes_with_epsilon(self):
        self.new_dh.replace_zeroes_with_epsilon()
        self.assertNotEqual(self.new_dh.get_data()[2], 0.0)

    def test_dh_get_mean(self):
        mean = self.new_dh.get_mean()
        self.assertAlmostEqual(mean, 2.0, 3)

    def test_dh_get_std(self):
        std = self.new_dh.get_std()
        self.assertAlmostEqual(std, 7.483, 3)


class GPSDataHolderClassTests(unittest.TestCase):
    def setUp(self) -> None:
        data = [[1., 2., 3.], [1., 2., 3.], [10., 15., 20.], [100., 50., 15.]]
        bar = la.DataHolder("test")
        bar.set_data([12, -6, 0.0])
        self.new_gps = la.GPSDataHolder("test", "iOS", data, 800.0, bar)

    def test_gps_empty_init(self):
        new_gps = la.GPSDataHolder("test", "testOS")
        self.assertIsNone(new_gps.barometer)
        self.assertEqual(new_gps.id, "test")
        self.assertEqual(new_gps.os_type, "testOS")
        self.assertEqual(new_gps.mic_samp_rate_hz, 80.0)
        self.assertEqual(new_gps.best_data_index, 0.0)

    def test_gps_data_init(self):
        data = [[1., 2.], [1., 2.], [10., 15.], [100., 50.]]
        new_gps = la.GPSDataHolder("test", "testOS", data)
        self.assertEqual(new_gps.gps_df.size, 8)

    def test_gps_mic_init(self):
        new_gps = la.GPSDataHolder("test", "testOS", mic_samp_rate_hz=80.0)
        self.assertEqual(new_gps.mic_samp_rate_hz, 80.0)

    def test_gps_bar_init(self):
        new_dh = la.DataHolder("test")
        new_dh.set_data([12, -6, 0.0, 5.0])
        new_gps = la.GPSDataHolder("test", "testOS", bar=new_dh)
        self.assertEqual(new_gps.get_size(), (0, 4))
        self.assertEqual(new_gps.barometer.get_data()[3], 5.0)

    def test_gps_clone(self):
        new_gps = self.new_gps.clone()
        self.assertEqual(new_gps.gps_df.size, 12)
        self.assertEqual(new_gps.mic_samp_rate_hz, 800.0)
        self.assertEqual(new_gps.get_size(), (3, 3))

    def test_gps_set_data(self):
        data = [[-1., 2., 3., 1.5], [1., -2., 3., 4.2], [-10., 15., 20., 0.35], [100., 50., 15., 1.]]
        self.new_gps.set_data(data)
        self.assertEqual(self.new_gps.gps_df.size, 16)
        self.assertEqual(self.new_gps.get_size(), (4, 3))

    def test_gps_set_metadata(self):
        new_id = "new test"
        new_os = "new os"
        new_mic_sr = 80.0
        self.new_gps.set_metadata(new_id, new_os, new_mic_sr)
        self.assertEqual(self.new_gps.id, "new test")
        self.assertEqual(self.new_gps.os_type, "new os")
        self.assertEqual(self.new_gps.mic_samp_rate_hz, 80.0)

    def test_gps_get_mean_all(self):
        means = self.new_gps.get_mean_all()
        self.assertEqual(len(means), 5)
        self.assertEqual(means["lat"], 2.0)
        self.assertAlmostEqual(means["bar"], 2, 3)

    def test_gps_get_std_all(self):
        stds = self.new_gps.get_std_all()
        self.assertEqual(len(stds), 5)
        self.assertEqual(stds["alt"], 5.0)
        self.assertAlmostEqual(stds["bar"], 7.483, 3)

    def test_gps_set_barometer(self):
        bar = [101.1, 101.325, 101.90, 101.5]
        self.new_gps.set_barometer(bar)
        self.assertEqual(self.new_gps.get_size(), (3, 4))
        self.assertAlmostEqual(self.new_gps.barometer.get_mean(), 101.456, 3)


class RedVoxLocationAnalyzerClassTests(LoadRedvoxTestFiles):
    def setUp(self) -> None:
        super().setUp()
        self.new_la = la.LocationAnalyzer(self.wrapped_packets, SURVEY, BLACKLIST)

    def test_la_empty_init(self):
        new_la = la.LocationAnalyzer()
        self.assertIsNone(new_la.invalid_points)
        self.assertIsNone(new_la.get_real_location())
        self.assertEqual(new_la.valid_gps_data, [])
        self.assertEqual(new_la.all_gps_data, [])

    def test_la_survey_init(self):
        new_la = la.LocationAnalyzer(real_location=SURVEY)
        self.assertIsNone(new_la.invalid_points)
        self.assertEqual(new_la.valid_gps_data, [])
        self.assertEqual(new_la.all_gps_data, [])
        self.assertEqual(new_la.get_real_location()["lat"], SURVEY_LAT)
        self.assertEqual(new_la.get_real_location()["lon"], SURVEY_LON)

    def test_la_blacklist_init(self):
        new_la = la.LocationAnalyzer(invalid_points=BLACKLIST)
        self.assertIsNone(new_la.get_real_location())
        self.assertEqual(new_la.valid_gps_data, [])
        self.assertEqual(new_la.all_gps_data, [])
        self.assertEqual(len(new_la.invalid_points), 2)
        self.assertEqual(new_la.invalid_points[0], blacklist_point1)

    def test_la_packet_init(self):
        new_la = la.LocationAnalyzer(self.wrapped_packets)
        self.assertIsNone(new_la.invalid_points)
        self.assertIsNone(new_la.get_real_location())
        self.assertEqual(new_la.all_stations_mean_df.shape, (2, 5))
        self.assertEqual(new_la.all_stations_std_df.shape, (2, 5))
        self.assertEqual(len(new_la.all_gps_data), 2)

    def test_la_set_real_location(self):
        new_la = la.LocationAnalyzer()
        new_la.set_real_location(SURVEY)
        self.assertEqual(new_la.get_real_location()["lat"], SURVEY_LAT)
        self.assertEqual(new_la.get_real_location()["lon"], SURVEY_LON)

    def test_la_get_real_location(self):
        new_la = la.LocationAnalyzer(real_location=SURVEY)
        surveyed_point = new_la.get_real_location()
        self.assertEqual(surveyed_point["lat"], SURVEY_LAT)
        self.assertEqual(surveyed_point["bar"], SURVEY_BAR)

    def test_la_get_loc_from_packets(self):
        new_la = la.LocationAnalyzer()
        for w_p in self.wrapped_packets:
            new_la.get_loc_from_packets(w_p)
        self.assertEqual(new_la.all_stations_mean_df.shape, (2, 5))
        self.assertEqual(new_la.all_stations_std_df.shape, (2, 5))
        self.assertEqual(len(new_la.all_gps_data), 2)

    def test_la_analyze_data(self):
        self.new_la.analyze_data()
        self.assertEqual(self.new_la.all_stations_mean_df.shape, (2, 5))
        self.assertEqual(self.new_la.all_stations_std_df.shape, (2, 5))
        self.assertEqual(self.new_la.all_stations_closest_df.shape, (2, 6))

        zero_gps = la.GPSDataHolder("zeroes", "iOS", [[0.0], [0.0], [0.0], [0.0]])
        zero_gps.barometer = la.DataHolder("barometer")
        zero_gps.barometer.set_data([SURVEY_BAR])
        self.new_la.all_gps_data = [zero_gps]
        self.new_la.set_real_location({"lat": 0.1, "lon": 0.1, "alt": 1.0,  "bar": SURVEY_BAR, "sea_bar": SEA_PRESSURE})
        self.new_la.analyze_data()
        self.assertEqual(self.new_la.all_stations_mean_df.shape, (1, 5))
        self.assertEqual(self.new_la.all_stations_std_df.shape, (1, 5))
        self.assertEqual(self.new_la.all_stations_closest_df.shape, (1, 6))

    def test_la_get_barometric_heights(self):
        bar_heights = self.new_la.get_barometric_heights()
        self.assertEqual(bar_heights.shape, (2, 1))
        self.assertAlmostEqual(bar_heights.iloc[0, 0], -23.279, 3)

    def test_la_validate_all(self):
        self.new_la.validate_all()
        self.assertEqual(len(self.new_la.valid_gps_data), 2)

    def test_la_compare_with_real_location(self):
        self.new_la.validate_all()
        self.new_la.compare_with_real_location()
        self.assertEqual(len(self.new_la.valid_gps_data), 2)
        self.assertEqual(self.new_la.all_stations_mean_df.shape, (2, 5))
        self.assertEqual(self.new_la.all_stations_std_df.shape, (2, 5))
        self.assertEqual(self.new_la.all_stations_closest_df.shape, (2, 6))
        self.assertEqual(self.new_la.all_stations_closest_df.iloc[0, 5], 0.0)
        self.assertEqual(self.new_la.all_stations_closest_df.iloc[1, 3], 11.9)
        self.assertEqual(self.new_la.all_stations_closest_df.iloc[0, 0], 5.0)

    def test_la_get_all_dataframes(self):
        self.new_la.analyze_data()
        result_df = self.new_la.get_all_dataframes()
        self.assertEqual(result_df.shape, (2, 18))

    def test_la_get_stats_dataframes(self):
        result_df = self.new_la.get_stats_dataframes()
        self.assertEqual(result_df.shape, (2, 12))

    def test_la_print_to_csv(self):
        self.new_la.analyze_data()
        current_csv_path = os.path.join(LA_TEST_DATA_DIR, "all.csv")
        self.new_la.print_to_csv(current_csv_path)
        test_contents = pd.read_csv(os.path.join(LA_TEST_DATA_DIR, "master.csv"))
        contents = pd.read_csv(current_csv_path)
        for idx in contents.index:
            for clm in contents.columns:
                self.assertAlmostEqual(contents.at[idx, clm], test_contents.at[idx, clm], 4)
        os.remove(current_csv_path)
        current_csv_path = os.path.join(LA_TEST_DATA_DIR, "android.csv")
        self.new_la.print_to_csv(current_csv_path, "Android")
        test_contents = pd.read_csv(os.path.join(LA_TEST_DATA_DIR, "master_android.csv"))
        contents = pd.read_csv(current_csv_path)
        for idx in contents.index:
            for clm in contents.columns:
                self.assertAlmostEqual(contents.at[idx, clm], test_contents.at[idx, clm], 4)
        os.remove(current_csv_path)
        current_csv_path = os.path.join(LA_TEST_DATA_DIR, "ios.csv")
        self.new_la.print_to_csv(current_csv_path, "iOS")
        test_contents = pd.read_csv(os.path.join(LA_TEST_DATA_DIR, "master_ios.csv"))
        contents = pd.read_csv(current_csv_path)
        for idx in contents.index:
            for clm in contents.columns:
                self.assertAlmostEqual(contents.at[idx, clm], test_contents.at[idx, clm], 4)
        os.remove(current_csv_path)


class LocationAnalyzerTests(LoadRedvoxTestFiles):
    def setUp(self) -> None:
        super().setUp()
        self.valid_gps_point = pd.Series({"latitude": SURVEY_LAT + .001, "longitude": SURVEY_LON + .01,
                                          "altitude": SURVEY_ALT + 20.})
        self.dist_gps_point = pd.Series({"latitude": SURVEY_LAT + .01, "longitude": SURVEY_LON + .01,
                                         "altitude": SURVEY_ALT + 100.})
        self.new_la = la.LocationAnalyzer(self.wrapped_packets)
        self.test_w_p = self.redvox_packets["testios1:2"]
        self.gps_data = la.load_position_data(self.test_w_p)
        self.survey = SURVEY
        self.bar_mean = la.AVG_SEA_LEVEL_PRESSURE_KPA
        self.inclusion_ranges = (la.DEFAULT_INCLUSION_HORIZONTAL_M, la.DEFAULT_INCLUSION_VERTICAL_M,
                                 la.DEFAULT_INCLUSION_VERTICAL_BAR_M)

    def test_get_all_ios_station(self):
        ios_df = la.get_all_ios_station(self.new_la.get_stats_dataframes())
        self.assertEqual(ios_df.shape, (1, 12))
        self.assertIn("iOS", ios_df["os"].to_numpy())
        self.assertNotIn("Android", ios_df["os"].to_numpy())

    def test_get_all_android_station(self):
        android_df = la.get_all_android_station(self.new_la.get_stats_dataframes())
        self.assertEqual(android_df.shape, (1, 12))
        self.assertIn("Android", android_df["os"].to_numpy())
        self.assertNotIn("iOS", android_df["os"].to_numpy())

    def test_load_position_data(self):
        self.assertEqual(self.gps_data.get_size(), (3, 3))
        self.assertEqual(self.gps_data.os_type, "iOS")
        self.assertEqual(self.gps_data.id, "testios1")

    def test_compute_barometric_height(self):
        bar_height = la.compute_barometric_height(SURVEY_BAR)
        self.assertAlmostEqual(bar_height, -23.694, 3)
        bar_height = la.compute_barometric_height(SURVEY_BAR, SEA_PRESSURE)
        self.assertAlmostEqual(bar_height, 25.697, 3)

    def test_compute_barometric_height_array(self):
        bar_data = np.array([SURVEY_BAR, SURVEY_BAR + .01, SURVEY_BAR - .01])
        bar_height = la.compute_barometric_height_array(bar_data)
        self.assertAlmostEqual(bar_height[0], -23.694, 3)
        self.assertEqual(len(bar_height), 3)
        bar_height = la.compute_barometric_height_array(bar_data, SEA_PRESSURE)
        self.assertAlmostEqual(bar_height[0], 25.697, 3)
        self.assertEqual(len(bar_height), 3)

    def test_get_component_dist_to_point(self):
        h_dist, v_dist, bar_dist = la.get_component_dist_to_point(SURVEY, self.dist_gps_point, self.bar_mean)
        self.assertAlmostEqual(h_dist, 1526.099, 3)
        self.assertAlmostEqual(v_dist, 100.000, 3)
        self.assertAlmostEqual(bar_dist, 11.900, 3)

    def test_get_gps_dist_to_location(self):
        dist = la.get_gps_dist_to_location(SURVEY, self.gps_data)
        self.assertEqual(len(dist), 3)
        self.assertAlmostEqual(np.mean(dist), 15.262, 3)
        dist = la.get_gps_dist_to_location(SURVEY, self.gps_data, self.bar_mean)
        self.assertEqual(len(dist), 3)
        self.assertAlmostEqual(np.mean(dist), 91.544, 3)

    def test_valid_blacklist(self):
        is_safe = la.validate_blacklist(self.valid_gps_point, self.survey, self.bar_mean, self.inclusion_ranges)
        self.assertTrue(is_safe)

    def test_validate_near_point(self):
        is_close = la.validate_near_point(self.valid_gps_point, self.survey, self.bar_mean, self.inclusion_ranges)
        self.assertFalse(is_close)

    def test_point_on_line_side(self):
        point1 = {"lat": 0, "lon": 0, "alt": 0}
        point2 = {"lat": 10, "lon": 10, "alt": 0}
        point_test1 = {"lat": 1.0, "lon": 10, "alt": 0}
        point_test2 = {"lat": 5, "lon": 5, "alt": 0}
        point_test3 = {"lat": 15, "lon": 2, "alt": 0}
        result = la.point_on_line_side((point1, point2), point_test1)
        self.assertLess(result, 0)     # right of line
        result = la.point_on_line_side((point1, point2), point_test2)
        self.assertEqual(result, 0)    # on the line
        result = la.point_on_line_side((point1, point2), point_test3)
        self.assertGreater(result, 0)  # left of line

    def test_validate_point_in_polygon(self):
        point1 = {"lat": 0, "lon": 0, "alt": 0}
        point2 = {"lat": 0, "lon": 10, "alt": 0}
        point3 = {"lat": 10, "lon": 10, "alt": 0}
        point4 = {"lat": 10, "lon": 0, "alt": 0}
        point_test1 = {"lat": 1.0, "lon": 10, "alt": 0}
        point_test2 = {"lat": 5, "lon": 5, "alt": 0}
        point_test3 = {"lat": 15, "lon": 2, "alt": 0}
        polygon = [point1, point2, point3, point4, point1]
        result = la.validate_point_in_polygon(point_test1, polygon)
        self.assertTrue(result)
        result = la.validate_point_in_polygon(point_test2, polygon)
        self.assertTrue(result)
        result = la.validate_point_in_polygon(point_test3, polygon)
        self.assertFalse(result)

    def test_validate(self):
        valid_data = la.validate(self.gps_data, self.inclusion_ranges, validation_points=BLACKLIST)
        self.assertEqual(valid_data.get_size(), (3, 3))

    def test_compute_solution_all(self):
        result = la.compute_distance_all(self.survey, self.new_la.all_gps_data)
        self.assertEqual(result.shape, (2, 18))
        self.assertEqual(result.iloc[0, 7], 0.0)
        self.assertEqual(result.iloc[1, 7], 0.0)
        self.assertEqual(result.iloc[0, 9], 19.72843)
        self.assertEqual(result.iloc[1, 9], 19.72843)

    def test_compute_closeness(self):
        result = la.compute_distance(self.survey, self.gps_data)
        self.assertIn("testios1", result.keys())
        self.assertEqual(len(result["testios1"]), 18)
        self.assertEqual(result["testios1"][7], 0.0)
        self.assertAlmostEqual(result["testios1"][17], 0.004, 3)

    def test_load_kml(self):
        data = la.load_kml(os.path.join(LA_TEST_DATA_DIR, "master.kml"))
        self.assertIn("testandroid1", data.keys())
        self.assertIn("testios1", data.keys())
        self.assertEqual(len(data["testandroid1"]), 3)

    def test_write_kml(self):
        new_la = la.LocationAnalyzer(self.wrapped_packets)
        data_dict = new_la.get_stats_dataframes().T.to_dict()
        current_kml_path = os.path.join(LA_TEST_DATA_DIR, "all.kml")
        la.write_kml(current_kml_path, data_dict)
        kml_test_data = la.load_kml(os.path.join(LA_TEST_DATA_DIR, "master.kml"))
        data = la.load_kml(current_kml_path)
        self.assertEqual(data, kml_test_data)
        os.remove(current_kml_path)
