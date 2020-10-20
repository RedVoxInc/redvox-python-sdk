import unittest

from redvox.common.station_utils import StationLocation, LocationData


class LocationDataTest(unittest.TestCase):
    def setUp(self):
        self.first_loc = StationLocation(lat_lon_timestamp=1000)
        self.second_loc = StationLocation(lat_lon_timestamp=500)
        self.third_loc = StationLocation(lat_lon_timestamp=2000)
        self.fourth_loc = StationLocation(lat_lon_timestamp=5000)
        self.fifth_loc = StationLocation(lat_lon_timestamp=5500)
        self.sixth_loc = StationLocation(lat_lon_timestamp=7500)
        self.seventh_loc = StationLocation(lat_lon_timestamp=100000)
        self.last_loc = StationLocation(lat_lon_timestamp=9000)
        self.window_start = 1500
        self.window_end = 7500

    def test_normal_use(self):
        loc_data = LocationData(all_locations=[self.first_loc, self.second_loc, self.third_loc, self.fourth_loc,
                                               self.fifth_loc, self.sixth_loc, self.seventh_loc, self.last_loc])
        loc_data.update_window_locations(self.window_start, self.window_end)
        self.assertEqual(len(loc_data.all_locations), 5)
        self.assertEqual(loc_data.all_locations[0].lat_lon_timestamp, 2000)

    def test_outside_before_after(self):
        loc_data = LocationData(all_locations=[self.first_loc, self.seventh_loc, self.second_loc, self.last_loc])
        loc_data.update_window_locations(self.window_start, self.window_end)
        self.assertEqual(len(loc_data.all_locations), 2)
        self.assertEqual(loc_data.all_locations[1].lat_lon_timestamp, 9000)

    def test_only_before(self):
        loc_data = LocationData(all_locations=[self.first_loc, self.first_loc, self.second_loc])
        loc_data.update_window_locations(self.window_start, self.window_end)
        self.assertEqual(len(loc_data.all_locations), 2)
        self.assertEqual(loc_data.all_locations[0].lat_lon_timestamp, 1000)

    def test_only_one(self):
        loc_data = LocationData(all_locations=[self.fourth_loc])
        loc_data.update_window_locations(self.window_start, self.window_end)
        self.assertEqual(len(loc_data.all_locations), 1)
        self.assertEqual(loc_data.all_locations[0].lat_lon_timestamp, 5000)

    def test_add_too_many_early(self):
        loc_data = LocationData(all_locations=[self.fourth_loc, self.first_loc, self.second_loc])
        loc_data.update_window_locations(self.window_start, self.window_end)
        self.assertEqual(len(loc_data.all_locations), 2)
        self.assertEqual(loc_data.all_locations[0].lat_lon_timestamp, 5000)

    def test_add_empty_to_valid(self):
        loc_data = LocationData(all_locations=[self.fourth_loc, StationLocation()])
        loc_data.update_window_locations(self.window_start, self.window_end)
        self.assertEqual(len(loc_data.all_locations), 1)
        self.assertEqual(loc_data.all_locations[0].lat_lon_timestamp, 5000)
