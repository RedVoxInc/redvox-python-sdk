import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from fastkml import kml, styles
from fastkml.geometry import Point
from redvox.api900 import reader
from redvox.common.constants import EPSILON

# LOCATION ANALYSIS
# find the station's best location and possibly compare it against a surveyed point
# The surveyed point can come from Google earth or any other positioning tool.

# VERY IMPORTANT NOTES:
# latitude and longitude measurements are always in degrees (deg)
# altitude and accuracy measurements are always in meters (m)
# barometer measurements are always in kiloPascals (kPa)
# exceptions to this will ALWAYS be noted in comments and variable names

# barometric formula and its constants taken from equations on
#  https://www.math24.net/barometric-formula/
AVG_SEA_LEVEL_PRESSURE_kPa = 101.325
GRAVITY_ACCELERATION_m_PER_s2 = 9.807
MOLAR_MASS_AIR_kg_PER_mol = 0.02896
STANDARD_TEMPERATURE_K = 288.15
UNIVERSAL_GAS_CONSTANT_kg_m2_PER_K_mol_s2 = 8.3143
Mg_DIV_BY_RT = ((MOLAR_MASS_AIR_kg_PER_mol * GRAVITY_ACCELERATION_m_PER_s2) /
                (STANDARD_TEMPERATURE_K * UNIVERSAL_GAS_CONSTANT_kg_m2_PER_K_mol_s2))

# Haversine equation constants from site:
#  https://movable-type.co.uk/scripts/gis-faq-5.1.html
EARTH_RADIUS_M = 6367000.0
DEG_TO_RAD = np.pi / 180.0
RAD_TO_DEG = 180.0 / np.pi

# instruments have only so much accuracy, so if something has a distance less than the following values
#  from a given point, we could feasibly consider it to be close enough to be at the given point.
# horizontal distance in meters for something to be included with a given point
INCLUSION_HORIZONTAL_M = 100.0
# vertical distance in meters for something to be included within a given point
INCLUSION_VERTICAL_M = 50.0
# vertical distance in meters computed via barometer measurements to be included within a given point
INCLUSION_VERTICAL_BAR_M = 10.0

# Survey dictionary minimum keys
# lat: latitude, lon: longitude, alt: altitude, bar: barometer reading
SURVEY_KEYS = ["lat", "lon", "alt", "bar"]
# Optional survey dictionary keys
# sea_bar: pressure reading at sea level
OPTIONAL_SURVEY_KEYS = ["sea_bar"]
# GPS data frame indices
GPS_DATA_INDICES = ["latitude", "longitude", "altitude", "accuracy"]
# closest gps data point to surveyed data frame columns
CLOSEST_TO_SURVEY_COLUMNS = ["closest acc", "closest lat", "closest lon", "closest alt", "closest bar", "distance"]
# mean location data frame columns
MEAN_LOC_COLUMNS = ["mean acc", "mean lat", "mean lon", "mean alt", "mean bar"]
# standard deviation (std) values data frame columns
STD_LOC_COLUMNS = ["std acc", "std lat", "std lon", "std alt", "std bar"]
# station info data frame columns
STATION_INFO_COLUMNS = ["os", "sample rate"]
# master data frame columns
MASTER_COLUMNS = STATION_INFO_COLUMNS + CLOSEST_TO_SURVEY_COLUMNS + MEAN_LOC_COLUMNS + STD_LOC_COLUMNS
# dict of validation methods that can be utilized
VALIDATION_METHODS = {"sol": "close to solution", "mean": "close to mean"}


class DataHolder:
    # a fancy way to hold an array of data.  Also keeps track of the "best value" of the data set.
    def __init__(self, name: str):
        self.id = name
        self._data = []
        self.best_value = None

    def add(self, new_data: float):
        self._data.append(new_data)
        self.replace_zeroes_with_epsilon()

    def set_data(self, new_data: List[float]):
        self._data = new_data
        self.replace_zeroes_with_epsilon()

    def replace_zeroes_with_epsilon(self):
        for index in range(len(self._data)):
            if self._data[index] == 0.0:
                self._data[index] = EPSILON

    def get_mean(self) -> float:
        return np.mean(self._data)

    def get_std(self) -> float:
        return np.std(self._data)

    def get_data(self) -> List[float]:
        return self._data

    def get_len_data(self) -> int:
        return len(self._data)


class GPSDataHolder:
    # holds gps data; latitude, longitude, altitude, and accuracy
    # also holds barometric data
    def __init__(self, name: str, opsys: str, data: Optional[List[List[float]]] = None,
                 mic_samp_rate_hz: float = 80., bar: Optional[DataHolder] = None):
        self.gps_df = pd.DataFrame(data, index=GPS_DATA_INDICES)
        self.barometer = bar
        self.id = name
        self.os_type = opsys
        self.mic_samp_rate_hz = mic_samp_rate_hz
        self.best_data_index = 0

    def clone(self):
        # return a copy of the calling data frame
        new_gps_dh = GPSDataHolder(self.id, self.os_type, None, self.mic_samp_rate_hz, self.barometer)
        new_gps_dh.gps_df = self.gps_df
        new_gps_dh.best_data_index = self.best_data_index
        return new_gps_dh

    def set_data(self, new_data: Optional[List[List[float]]] = None):
        # set gps location data
        self.gps_df = pd.DataFrame(new_data, index=GPS_DATA_INDICES)

    def set_metadata(self, new_id: Optional[str] = None, new_os: Optional[str] = None,
                     new_mic_samp_rate_hz: Optional[float] = None):
        # set id, os and mic sample rate
        if new_id is not None:
            self.id = new_id
        if new_os is not None:
            self.os_type = new_os
        if new_mic_samp_rate_hz is not None:
            self.mic_samp_rate_hz = new_mic_samp_rate_hz

    def get_mean_all(self) -> Dict[str, float]:
        # return the mean of all 5 measurements
        bar_mean = self.barometer.get_mean()
        if bar_mean == 0 or bar_mean is None:
            bar_mean = 0.00000000001
        lat_mean = self.gps_df.loc["latitude"].mean()
        lon_mean = self.gps_df.loc["longitude"].mean()
        alt_mean = self.gps_df.loc["altitude"].mean()
        acc_mean = self.gps_df.loc["accuracy"].mean()

        return {"acc": acc_mean, "lat": lat_mean, "lon": lon_mean, "alt": alt_mean, "bar": bar_mean}

    def get_std_all(self) -> Dict[str, float]:
        # return the standard deviation of all 5 measurements
        bar_std = self.barometer.get_std()
        if bar_std == 0 or bar_std is None:
            bar_std = 0.00000000001
        lat_std = self.gps_df.loc["latitude"].std()
        if np.isnan(lat_std):
            lat_std = 0
        lon_std = self.gps_df.loc["longitude"].std()
        if np.isnan(lon_std):
            lon_std = 0
        alt_std = self.gps_df.loc["altitude"].std()
        if np.isnan(alt_std):
            alt_std = 0
        acc_std = self.gps_df.loc["accuracy"].std()
        if np.isnan(acc_std):
            acc_std = 0

        return {"acc": acc_std, "lat": lat_std, "lon": lon_std, "alt": alt_std, "bar": bar_std}

    def set_barometer(self, bar_data: List[float]):
        # set the barometer dataholder
        self.barometer = DataHolder("barometer")
        self.barometer.set_data(bar_data)
        self.barometer.best_value = np.mean(bar_data)

    def get_size(self):
        # return the length of the gps data and the barometer data
        return self.gps_df.iloc[0].size, self.barometer.get_len_data()


class LocationAnalyzer:
    # stores location information, which can be analyzed later
    # generally finds the means of all measurements, then checks if all points are within limits
    #  then returns the mean location.
    # can be used for multiple devices in different locations if no survey is given to the set.
    # best use for multiple surveyed points is to create 1 analyzer per survey
    # survey must contain the minimum keys listed in SURVEY_KEYS
    #  survey may contain other keys than ones listed in SURVEY_KEYS, with OPTIONAL_SURVEY_KEYS as reserved keys
    def __init__(self, path_to_data: Optional[str] = None, survey: Optional[Dict[str, float]] = None,
                 invalid_points: Optional[List[Dict[str, float]]] = None):
        self.all_devices_closest_df = pd.DataFrame([], columns=CLOSEST_TO_SURVEY_COLUMNS)
        self.all_devices_mean_df = pd.DataFrame([], columns=MEAN_LOC_COLUMNS)
        self.all_devices_std_df = pd.DataFrame([], columns=STD_LOC_COLUMNS)
        self.all_devices_info_df = pd.DataFrame([], columns=STATION_INFO_COLUMNS)
        self.invalid_points = invalid_points
        self.all_gps_data = []
        self.valid_gps_data = []
        self._real_location = survey
        # if given a path to redvox data, load data from there
        if path_to_data is not None:
            self.load_files(path_to_data)

    def set_real_location(self, survey: Dict[str, float] = None):
        # set the real location
        self._real_location = survey

    def get_real_location(self) -> Dict[str, float]:
        # return the real location
        return self._real_location

    def get_all_dataframes(self) -> pd.DataFrame:
        # fuse all dataframes together
        frames = [self.all_devices_info_df, self.all_devices_closest_df,
                  self.all_devices_mean_df, self.all_devices_std_df]
        return pd.concat(frames, axis=1)

    def get_stats_dataframes(self) -> pd.DataFrame:
        # fuse informational and statistic dataframes together
        frames = [self.all_devices_info_df, self.all_devices_mean_df, self.all_devices_std_df]
        return pd.concat(frames, axis=1)

    def load_files(self, path_to_data: str):
        # read data from files in path_to_data
        try:
            packets = reader.read_rdvxz_file_range(path_to_data, concat_continuous_segments=False)
            for redvox_id, w_p in packets.items():
                # get the data values and mean location from packets
                self.get_loc_from_packets(w_p)
        except Exception as err:
            print("Program failed!  {}: {}".format(type(err).__name__, err))

    def analyze_from_files(self, path_to_data: str, survey_dict: Optional[Dict[str, float]] = None,
                           write_output: bool = False):
        # load data from files, analyze it, then if a real location exists,
        #  compare data to real location, then write output
        self.load_files(path_to_data)
        self._real_location = survey_dict
        # analyze data
        self.analyze_data(write_output)

    def analyze_data(self, write_output: bool = False):
        # analyze data, compare to real location if it exists, then write output if desired
        self.validate_all()
        # if there's no real location, make the mean the real location
        if self._real_location is None:
            means = self.all_devices_mean_df
            self._real_location = {"lat": np.mean(means["mean lat"]), "lon": np.mean(means["mean lon"]),
                                   "alt": np.mean(means["mean alt"]), "bar": np.mean(means["mean bar"])}
        self.compare_with_real_location()
        # print results
        if write_output:
            self.print_to_csv("temp.csv")

    def get_loc_from_packets(self, w_p: List[reader.WrappedRedvoxPacket]):
        # given a list of wrapped redvox packets, store the location information and their mean and std
        # extract the information from the packets
        sample_rate = w_p[0].microphone_sensor().sample_rate_hz()
        dev_os_type = w_p[0].device_os()
        idd = w_p[0].redvox_id()
        packet_gps_data = load_position_data(w_p)
        # compute mean location
        mean_loc = packet_gps_data.get_mean_all()
        std_loc = packet_gps_data.get_std_all()
        # store the information
        self.all_gps_data.append(packet_gps_data)
        self.all_devices_info_df.loc[idd] = [dev_os_type, sample_rate]
        self.all_devices_std_df.loc[idd] = [std_loc["acc"], std_loc["lat"], std_loc["lon"],
                                            std_loc["alt"], std_loc["bar"]]
        self.all_devices_mean_df.loc[idd] = [mean_loc["acc"], mean_loc["lat"], mean_loc["lon"],
                                             mean_loc["alt"], mean_loc["bar"]]

    def get_barometric_heights(self, sea_pressure: float = AVG_SEA_LEVEL_PRESSURE_kPa) -> pd.DataFrame:
        # for each device, compute the barometric height using the mean
        bar_heights = {}
        data_dict = self.all_devices_mean_df["mean bar"].T.to_dict()
        for index in data_dict.keys():
            bar_heights[index] = compute_barometric_height(data_dict[index], sea_pressure)
        barometric_heights = pd.DataFrame(bar_heights, index=["bar height"], columns=self.all_devices_mean_df.index)
        return barometric_heights.T

    def validate_all(self, validation_ranges: Tuple[float, float, float] = (INCLUSION_HORIZONTAL_M,
                                                                            INCLUSION_VERTICAL_M,
                                                                            INCLUSION_VERTICAL_BAR_M),):
        # check that all data in the data set are valid.  Remove outliers and strange values
        # validation always assumes nothing is valid when it starts, so empty out the valid_gps_data
        self.valid_gps_data = []
        for device in self.all_gps_data:
            # if self._real_location is not None:
            #     validated_gps = self.validator(device, self._real_location)
            # else:
            #     validated_gps = validate_data(device)
            validated_gps = validate(device, validation_ranges, "blacklist", self.invalid_points)
            if validated_gps.get_size()[0] != 0:
                self.valid_gps_data.append(validated_gps)

    def compare_with_real_location(self):
        # given a real location, find the closest valid data point
        # compute closest point to real location
        result = compute_solution_all(self._real_location, self.valid_gps_data)
        self.all_devices_closest_df = result[CLOSEST_TO_SURVEY_COLUMNS]
        self.all_devices_info_df = result[STATION_INFO_COLUMNS]
        self.all_devices_mean_df = result[MEAN_LOC_COLUMNS]
        self.all_devices_std_df = result[STD_LOC_COLUMNS]

    def print_location_df(self, info_type: Optional[str] = None, os_type: Optional[str] = None):
        # print a dataframe, or all non-solution data frames
        if info_type == "real":
            print_station_df(self.all_devices_closest_df, os_type)
        elif info_type == "info":
            print_station_df(self.all_devices_info_df, os_type)
        elif info_type == "std":
            print_station_df(self.all_devices_std_df, os_type)
        elif info_type == "mean":
            print_station_df(self.all_devices_mean_df, os_type)
        elif info_type == "all":
            print_station_df(self.get_all_dataframes(), os_type)
        else:
            # fuse statistical dataframes together
            print_station_df(self.get_stats_dataframes(), os_type)

    def print_to_csv(self, path: str, os_type: str = None):
        # print dataframes to csv files in path; please supply entire path including file name
        # fuse all dataframes together
        result = self.get_all_dataframes()
        if os_type == "Android":
            get_all_android_station(result).to_csv(path)
        elif os_type == "iOS":
            get_all_ios_station(result).to_csv(path)
        else:
            os_type = "all"
            result.to_csv(path)
        print("Printed {} device data to {}.".format(os_type, path))


def get_all_ios_station(station_df: pd.DataFrame) -> pd.DataFrame:
    # return all iOS stations
    return station_df.loc[station_df["os"] == "iOS"]


def get_all_android_station(station_df: pd.DataFrame) -> pd.DataFrame:
    # return all Android stations
    return station_df.loc[station_df["os"] == "Android"]


def print_station_df(station_df: pd.DataFrame, os_type: Optional[str] = None):
    # Print the data frames, filtering on os type
    if os_type == "Android":
        print(get_all_android_station(station_df))
    elif os_type == "iOS":
        print(get_all_ios_station(station_df))
    else:
        print(station_df)


def load_position_data(w_p: List[reader.WrappedRedvoxPacket]) -> GPSDataHolder:
    # load positional data from wrapped redvox packets
    gps_data = [[], [], [], []]
    packet = None
    packet_name = None
    bar_data = []
    try:
        for packet in w_p:
            packet_name = packet.default_filename()
            if packet.has_barometer_sensor():
                bar_chan = packet.barometer_sensor()  # load barometer data
                bar_data.extend(bar_chan.payload_values())
            else:
                # add defaults
                bar_data.extend([0.0])
                print("WARNING: {} Barometer empty, using default values!".format(packet_name))
            if packet.has_location_sensor():
                # load each channel's data into the container
                loc_chan = packet.location_sensor()
                gps_data[0].extend(loc_chan.payload_values_latitude())
                gps_data[1].extend(loc_chan.payload_values_longitude())
                gps_data[2].extend(loc_chan.payload_values_altitude())
                gps_data[3].extend(loc_chan.payload_values_accuracy())
            else:
                # add defaults
                gps_data[0].extend([0.0])
                gps_data[1].extend([0.0])
                gps_data[2].extend([0.0])
                gps_data[3].extend([0.0])
                print("WARNING: {} Location empty, using default values!".format(packet_name))
    except Exception as eror:
        if packet is not None:
            error_string = "Something went wrong while reading location data from file: {}.  " \
                           "Original message: {}"
            raise Exception(error_string.format(packet_name, eror))
        else:
            raise Exception("No packet found in file.  Original message: {}".format(eror))

    # load data into data holder
    redvox_id = w_p[0].redvox_id()
    gps_dfh = GPSDataHolder(str(redvox_id), w_p[0].device_os(), gps_data,
                            w_p[0].microphone_sensor().sample_rate_hz())
    gps_dfh.set_barometer(bar_data)

    return gps_dfh


def compute_barometric_height(barometric_pressure: float, sea_pressure: float = AVG_SEA_LEVEL_PRESSURE_kPa) -> float:
    # compute height using barometric and sea-level pressure
    # barometric equation from https://www.math24.net/barometric-formula/
    # P(h) = P0 * e**(-Mgh/RT) where:
    # P0 = AVG_SEA_LEVEL_PRESSURE_kPa = 101.325
    # g = GRAVITY_ACCELERATION_m_PER_s2 = 9.807
    # M = MOLAR_MASS_AIR_kg_PER_mol = 0.02896
    # T = STANDARD_TEMPERATURE_K = 288.15
    # R = UNIVERSAL_GAS_CONSTANT_kg_m2_PER_K_mol_s2 = 8.3143
    # therefore h = ln(P0/P(h)) / (Mg/RT)
    # we can't let sea_pressure or barometric_pressure be 0
    # right now the user is responsible for barometric_pressure not being 0
    if sea_pressure == 0.0:
        sea_pressure = EPSILON
    barometric_height = np.log(sea_pressure / barometric_pressure) / Mg_DIV_BY_RT
    return barometric_height


def compute_barometric_height_array(barometric_pressure: np.array, sea_pressure: float = AVG_SEA_LEVEL_PRESSURE_kPa) \
        -> np.array:
    # compute height using barometric and sea-level pressure, where pressure is an array
    # barometric equation from https://www.math24.net/barometric-formula/
    if sea_pressure == 0.0:
        sea_pressure = EPSILON
    barometric_height = np.log(sea_pressure / barometric_pressure) / Mg_DIV_BY_RT
    return barometric_height


def get_component_dist_to_point(point: Dict[str, float], gps_data: pd.Series, bar_mean: float) -> (float, float, float):
    # compute distance from the gps data points to the chosen point
    # return the horizontal, vertical, and barometer components as a tuple
    # horizontal distance
    # use haversine formula
    dlon = gps_data["longitude"] - point["lon"]
    dlat = gps_data["latitude"] - point["lat"]
    haver = np.sin(dlat * DEG_TO_RAD / 2.0) ** 2.0 + (np.cos(point["lat"] * DEG_TO_RAD) *
                                                      np.cos(gps_data["latitude"] * DEG_TO_RAD) *
                                                      np.sin(dlon * DEG_TO_RAD / 2.0) ** 2.0)
    c = 2.0 * np.arcsin(np.min([1.0, np.sqrt(haver)]))
    h_dist = EARTH_RADIUS_M * c
    # vertical distance
    v_dist = np.abs(gps_data["altitude"] - point["alt"])
    # vertical distance using barometer
    v_bar_dist = np.abs(compute_barometric_height(bar_mean) - point["alt"])
    return h_dist, v_dist, v_bar_dist


def get_gps_dist_to_location(loc_df: Dict[str, float], gps_dataholder: GPSDataHolder,
                             bar_alt: Optional[float] = None) -> np.array:
    # compute distance from the gps data points to the location
    # if given a barometer altitude value, use that instead of the gps altitude
    if bar_alt is not None:
        device_alt = bar_alt
    else:
        device_alt = gps_dataholder.gps_df.loc["altitude"].to_numpy()
    # user haversine formula
    dlon = gps_dataholder.gps_df.loc["longitude"].to_numpy() - loc_df["lon"]
    dlat = gps_dataholder.gps_df.loc["latitude"].to_numpy() - loc_df["lat"]
    haver = np.sin(dlat * DEG_TO_RAD / 2.0) ** 2.0 + (np.cos(loc_df["lat"] * DEG_TO_RAD) *
                                                      np.cos(gps_dataholder.gps_df.loc["latitude"].to_numpy()
                                                             * DEG_TO_RAD)
                                                      * np.sin(dlon * DEG_TO_RAD / 2.0) ** 2.0)
    c = 2 * np.arcsin(np.minimum([1.0], np.sqrt(haver)))
    h_dist = EARTH_RADIUS_M * c
    dist_array = (h_dist ** 2 + (loc_df["alt"] - device_alt) ** 2)
    return np.sqrt(dist_array)


def validate_blacklist(gps_data: pd.Series, point: Dict[str, float], bar_mean: float,
                       inclusion_ranges: Tuple[float, float, float] = (INCLUSION_HORIZONTAL_M, INCLUSION_VERTICAL_M,
                                                                       INCLUSION_VERTICAL_BAR_M)) -> bool:
    # return true if point is NOT in blacklist
    # calculate distance from gps data to invalid point
    h_dist, v_dist, v_bar_dist = get_component_dist_to_point(point, gps_data, bar_mean)
    # if outside horizontal and vertical distance, we're far enough away from the invalid point
    return h_dist > inclusion_ranges[0] and (v_dist > inclusion_ranges[1] or v_bar_dist > inclusion_ranges[2])


def validate_near_point(gps_data: pd.Series, point: Dict[str, float], bar_mean: float,
                        inclusion_ranges: Tuple[float, float, float] = (INCLUSION_HORIZONTAL_M, INCLUSION_VERTICAL_M,
                                                                        INCLUSION_VERTICAL_BAR_M)) -> bool:
    # return true if point IS close to point
    # calculate distance from gps data to point
    h_dist, v_dist, v_bar_dist = get_component_dist_to_point(point, gps_data, bar_mean)
    # if within horizontal distance and vertical distance, we're close enough to the point
    return h_dist <= inclusion_ranges[0] and (v_dist <= inclusion_ranges[1] or v_bar_dist <= inclusion_ranges[2])


def validate(data_to_test: GPSDataHolder,
             inclusion_ranges: Tuple[float, float, float] = (INCLUSION_HORIZONTAL_M,
                                                             INCLUSION_VERTICAL_M, INCLUSION_VERTICAL_BAR_M),
             validation_type: str = None, validation_points: List[Dict[str, float]] = None,
             debug: bool = False) -> GPSDataHolder:
    # perform validation.  returns all valid data
    # check if we even have points to compare against
    if len(validation_points) < 1:
        return data_to_test  # no points to check, everything is good
    need_to_test_gps = data_to_test.clone()
    while True:  # keep going until the data doesn't change
        # remove any points in the data that are not close to the points
        validated_gps_data = [[], [], [], []]
        for gps_point in data_to_test.gps_df.columns:
            # extract data to test
            gps_data = data_to_test.gps_df[gps_point]
            point_valid = True  # assume point is valid
            for point in validation_points:
                if validation_type == "solution" or validation_type == "mean":
                    point_valid = validate_near_point(gps_data, point,
                                                      data_to_test.barometer.get_mean(), inclusion_ranges)
                    if not point_valid:  # if point_valid ever becomes false, we can stop processing
                        break
                else:
                    point_valid = validate_blacklist(gps_data, point,
                                                     data_to_test.barometer.get_mean(), inclusion_ranges)
                    if not point_valid:  # if point_valid ever becomes false, we can stop processing
                        break
            if point_valid:  # add only valid points
                validated_gps_data[0].append(gps_data["latitude"])
                validated_gps_data[1].append(gps_data["longitude"])
                validated_gps_data[2].append(gps_data["altitude"])
                validated_gps_data[3].append(gps_data["accuracy"])
        # create the object to return.
        validated_gps = GPSDataHolder(data_to_test.id, data_to_test.os_type, validated_gps_data,
                                      data_to_test.mic_samp_rate_hz, data_to_test.barometer)
        if validated_gps.get_size() == need_to_test_gps.get_size():
            # print message if user allows it
            if debug:
                print("{} data validated".format(validated_gps.id))
            # if data does not change, we are done validating
            return validated_gps
        else:
            # use the new data to update the old data
            need_to_test_gps = validated_gps.clone()


def compute_solution_all(loc_df: Dict[str, float], all_gps_data: List[GPSDataHolder]) -> pd.DataFrame:
    # compare distances from multiple gps points to the location.  return the closest point
    closeness = {}
    for gps_dh in all_gps_data:
        closeness.update(compute_closeness(loc_df, gps_dh))
    return pd.DataFrame(closeness, index=MASTER_COLUMNS).T


def compute_closeness(loc_df: dict, gps_data: GPSDataHolder) -> dict:
    # for a location, compute distance to closest data point
    idd = gps_data.id
    devices_data = {idd: None}
    gps_loc = gps_data.get_mean_all()

    # find closest barometer altitude to location
    # bar_alt_tmp = (((SEA_PRESSURE / np.array(gps_data.barometer.data)) ** 0.190263096) - 1) * (SOL_TEMP / 0.0065)
    if "sea bar" in loc_df.keys() and loc_df["sea_bar"] is not None:
        bar_alt_tmp = compute_barometric_height_array(np.array(gps_data.barometer.get_data()), loc_df["sea_bar"])
    else:
        bar_alt_tmp = compute_barometric_height_array(np.array(gps_data.barometer.get_data()))
    # simplified barometric equation:
    # P(h) = 101.325 * e ** (-0.00012h) -> P(h) / 101.325 = 1 / (e ** 0.00012h)
    # e ** 0.00012h = 101.325 / P(h) -> 0.00012h = ln(101.325) - ln(P))
    # SEA_PRESSURE = 101.325
    # h = ln(SEA_PRESSURE/P(h)) / 0.00012
    min_index = np.argmin(np.abs(bar_alt_tmp - loc_df["alt"]))
    gps_data.barometer.best_value = gps_data.barometer.get_data()[min_index]
    bar_alt = bar_alt_tmp[min_index]
    # for all gps coords, find closest to solution
    dist_array = get_gps_dist_to_location(loc_df, gps_data)
    min_index = np.argmin(dist_array)
    # compute distance using best barometer measurement
    dist_array_bar = get_gps_dist_to_location(loc_df, gps_data, bar_alt)
    min_bar_index = np.argmin(dist_array_bar)
    # compare minimum of pure gps and gps with barometer
    if dist_array_bar[min_bar_index] < dist_array_bar[min_index]:
        min_index = min_bar_index
        dist_array = dist_array_bar

    # finding the std of the distances is basically finding the std of accuracy
    acc_std = np.std(dist_array)
    lat_std = np.std(np.abs(loc_df["lat"] - gps_data.gps_df.loc["latitude"].to_numpy()))
    lon_std = np.std(np.abs(loc_df["lon"] - gps_data.gps_df.loc["longitude"].to_numpy()))
    alt_std = np.std(np.abs(loc_df["alt"] - gps_data.gps_df.loc["altitude"].to_numpy()))
    bar_std = gps_data.barometer.get_std()

    # put data into dictionary to store in data frames later
    devices_data[idd] = [gps_data.os_type, gps_data.mic_samp_rate_hz, gps_data.gps_df.loc["accuracy", min_index],
                         gps_data.gps_df.loc["latitude", min_index], gps_data.gps_df.loc["longitude", min_index],
                         gps_data.gps_df.loc["altitude", min_index], gps_data.barometer.best_value,
                         dist_array[min_index], gps_loc["acc"], gps_loc["lat"], gps_loc["lon"],
                         gps_loc["alt"], gps_loc["bar"], acc_std, lat_std, lon_std, alt_std, bar_std]

    return devices_data


def load_kml(kml_file: str) -> Dict[str, Dict[str, float]]:
    # load locations from a kml file, returning a dictionary of locations
    with open(kml_file, 'r', encoding="utf-8") as my_file:
        kml_doc = my_file.read()
    kml_data = kml.KML()
    kml_data.from_string(bytes(kml_doc, encoding="utf8"))
    locations = list(list(kml_data.features())[0].features())
    set_locations = {}
    for place in locations:
        set_locations[place.name] = {"lon": place.geometry.x, "lat": place.geometry.y, "alt": place.geometry.z}
    return set_locations


def write_kml(kml_file: str, master_dict: Dict[str, Dict[str, float]]):
    # creates a kml file named kml_file using the information in master_dict
    ns = '{http://www.opengis.net/kml/2.2}'
    # declare kml structure and the document
    kmlz = kml.KML(ns=ns)
    doc = kml.Document(ns, '1')
    # declare, then add styles to doc
    doc_style = styles.Style(id='2')
    pnt_style = styles.IconStyle(id='3', color='ff0000ff')
    pnt_style.icon_href = "http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"
    doc_style.append_style(pnt_style)
    doc.append_style(doc_style)
    # id is assigned dynamically as new elements are created
    new_id = 4
    for key in master_dict.keys():
        # how do we know if bar is better than alt?
        # set point description to os and sample rate
        description = "{} {}hz".format(master_dict[key]["os"], str(master_dict[key]["sample rate"]))
        # declare the placemark, then give it some coordinates
        pnt = kml.Placemark(ns, id=str(new_id), name=key, description=description, styleUrl='#2')
        new_id += 1
        pnt.geometry = Point(master_dict[key]["mean lon"], master_dict[key]["mean lat"], master_dict[key]["mean alt"])
        # add placemark to doc
        doc.append(pnt)
    # add the doc to the kml file
    kmlz.append(doc)
    # write the kml file, with nice formatting
    with open(kml_file, 'w', encoding="utf-8") as my_file:
        my_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        my_file.write(kmlz.to_string(prettyprint=True))
