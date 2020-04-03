"""
finds a station's best location and compare it against a surveyed point if one is provided
station location data can be loaded from rdvxz files or input manually
The surveyed point can come from Google earth or any other positioning tool.

PLEASE NOTE:
latitude and longitude measurements are always in degrees (deg)
altitude and accuracy measurements are always in meters (m)
barometer measurements are always in kiloPascals (kPa)
exceptions to this will ALWAYS be noted in comments and variable names

barometric formula source: https://www.math24.net/barometric-formula/
barometric formula P(h) = P0 * e**(h * (-Mg/RT))
where h is a height in meters, P(h) is pressure in kPa at h and P0 is sea-level pressure in kPa
 Mg/RT is a constant based on assumptions of average earth based values.

Haversine equation constants from site: https://movable-type.co.uk/scripts/gis-faq-5.1.html
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from fastkml import kml, styles
from fastkml.geometry import Point
from redvox.api900 import reader
from redvox.common.constants import EPSILON, DEG_TO_RAD, AVG_SEA_LEVEL_PRESSURE_KPA, EARTH_RADIUS_M, \
    STANDARD_TEMPERATURE_K, MOLAR_MASS_AIR_KG_PER_MOL, GRAVITY_M_PER_S2, UNIVERSAL_GAS_CONSTANT_KG_M2_PER_K_MOL_S2

# instruments have only so much accuracy, so if something has a distance less than the following values
#  from a given point, we could feasibly consider it to be close enough to be at the given point.
# default horizontal distance in meters for something to be included with a given point
DEFAULT_INCLUSION_HORIZONTAL_M = 100.0
# default vertical distance in meters for something to be included within a given point
DEFAULT_INCLUSION_VERTICAL_M = 50.0
# default vertical distance in meters computed via barometer measurements to be included within a given point
DEFAULT_INCLUSION_VERTICAL_BAR_M = 10.0

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
    """
    Stores an array of float data.  The data is privatized for security.
    It also keeps track of the "best value" of the data set.
    Properties:
        id: a string identifier for the data
        _data: private data storage; all values must be floats
        best_value: the value that best represents the data set
    """
    #
    def __init__(self, name: str):
        """
        sets up the DataHolder
        :param name: a string identifier for the data
        """
        self.id = name
        self._data = []
        self.best_value = None

    def add(self, new_data: float):
        """
        adds one element to the data
        :param new_data: float value to add
        """
        self._data.append(new_data)
        self.replace_zeroes_with_epsilon()

    def set_data(self, new_data: List[float]):
        """
        overwrites the stored data with the new_data
        :param new_data: the new list of floats to overwrite the existing data with
        """
        self._data = new_data
        self.replace_zeroes_with_epsilon()

    def replace_zeroes_with_epsilon(self):
        """
        replaces all 0 values in the data with extremely tiny values
        """
        for index in range(len(self._data)):
            if self._data[index] == 0.0:
                self._data[index] = EPSILON

    def get_mean(self) -> float:
        """
        return the mean of the data
        :return: the mean of the data
        """
        return np.mean(self._data)

    def get_std(self) -> float:
        """
        return the standard deviation of the data
        :return: the standard deviation of the data
        """
        return np.std(self._data)

    def get_data(self) -> List[float]:
        """
        return the data
        :return: the data
        """
        return self._data

    def get_len_data(self) -> int:
        """
        return the length of the data array
        :return: the length of the data array
        """
        return len(self._data)


class GPSDataHolder:
    """
    holds gps data (latitude, longitude, altitude, and accuracy) and barometric data
    uses a dataframe to organize the gps data
    Properties:
        gps_df: a dataframe to hold all the gps data
        barometer: a DataHolder for barometer data
        id: string identifier for the data set
        os_type: string identifier for the operating system of the data set
        mic_samp_rate_hz: float sample rate of station microphone in hz
        best_data_index: the index that corresponds to the best representative of the data
    """
    def __init__(self, name: str, opsys: str, data: Optional[List[List[float]]] = None,
                 mic_samp_rate_hz: float = 80., bar: Optional[DataHolder] = None):
        """
        sets up the GPSDataHolder
        :param name: string identifier for the data set
        :param opsys: string identifier for the data set's operating system
        :param data: the data as a list of list of floats, default None
        :param mic_samp_rate_hz: float sample rate of the microphone in hz, default 80 hz
        :param bar: barometer DataHolder, default None
        """
        self.gps_df = pd.DataFrame(data, index=GPS_DATA_INDICES)
        self.barometer = bar
        self.id = name
        self.os_type = opsys
        self.mic_samp_rate_hz = mic_samp_rate_hz
        self.best_data_index = 0

    def clone(self):
        """
        return a copy of the GPSDataHolder
        :return: an exact copy of the GPSDataHolder
        """
        # return a copy of the calling data frame
        new_gps_dh = GPSDataHolder(self.id, self.os_type, None, self.mic_samp_rate_hz, self.barometer)
        new_gps_dh.gps_df = self.gps_df
        new_gps_dh.best_data_index = self.best_data_index
        return new_gps_dh

    def set_data(self, new_data: Optional[List[List[float]]] = None):
        """
        set gps location data.  data is expected to be 4 lists: latitude values, longitude values, altitude values,
          and accuracy values
        :param new_data: list of list of floats that represent the gps data, default None
        """
        self.gps_df = pd.DataFrame(new_data, index=GPS_DATA_INDICES)

    def set_metadata(self, new_id: Optional[str] = None, new_os: Optional[str] = None,
                     new_mic_samp_rate_hz: Optional[float] = None):
        """
        set metadata fields; id, os and mic sample rate
        :param new_id: the new string identifier for the data set, default None
        :param new_os: the new string identifier for the data set's os, default None
        :param new_mic_samp_rate_hz: float of new microphone sample rate in hz, default None
        """
        if new_id is not None:
            self.id = new_id
        if new_os is not None:
            self.os_type = new_os
        if new_mic_samp_rate_hz is not None:
            self.mic_samp_rate_hz = new_mic_samp_rate_hz

    def get_mean_all(self) -> Dict[str, float]:
        """
        return the means of the latitude, longitude, altitude, accuracy, and barometer
        :return: means of all 5 measurements
        """
        bar_mean = self.barometer.get_mean()
        if bar_mean == 0 or bar_mean is None:
            bar_mean = 0.00000000001
        lat_mean = self.gps_df.loc["latitude"].mean()
        lon_mean = self.gps_df.loc["longitude"].mean()
        alt_mean = self.gps_df.loc["altitude"].mean()
        acc_mean = self.gps_df.loc["accuracy"].mean()

        return {"acc": acc_mean, "lat": lat_mean, "lon": lon_mean, "alt": alt_mean, "bar": bar_mean}

    def get_std_all(self) -> Dict[str, float]:
        """
        return the standard deviations of the latitude, longitude, altitude, accuracy, and barometer
        :return: standard deviations of all 5 measurements
        """
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
        """
        sets the barometer DataHolder.  uses the mean of the data as the best value
        :param bar_data: list of floats to set barometer data as
        """
        self.barometer = DataHolder("barometer")
        self.barometer.set_data(bar_data)
        self.barometer.best_value = np.mean(bar_data)

    def get_size(self) -> (int, int):
        """
        return the amount of gps and barometer data points
        :return: the amount of gps and barometer data points
        """
        return self.gps_df.iloc[0].size, self.barometer.get_len_data()


class LocationAnalyzer:
    """
    stores location information, which can be analyzed later
    contains functions to find mean, standard deviation (std) and validation of data
    use one analyzer per real location point.  one analyzer can accommodate multiple stations per survey point
    the real location dictionary must contain the minimum keys listed in SURVEY_KEYS
    the real location dictionary may contain other keys than ones listed in SURVEY_KEYS
    keys in OPTIONAL_SURVEY_KEYS have special meaning and can only be used as this program intends to use them
    uses dataframes with station id as the index
    Properties:
        all_stations_info_df: dataframe with metadata about all stations
        all_stations_mean_df: dataframe with means from all stations
        all_stations_std_df: dataframe with stds from all stations
        all_stations_closest_df: dataframe with the closest point to the real location and its distance to the
                                    real location for all stations
        invalid_points: a list of gps points that are blacklisted
        _real_location: the surveyed point that the station is located at.  privatized for security
        all_gps_data: a list of all GPSDataHolders that form the data set
        valid_gps_data: a list of all GPSDataHolders that pass validation checks
    """
    def __init__(self, wrapped_packets: List[List[reader.WrappedRedvoxPacket]] = None,
                 real_location: Optional[Dict[str, float]] = None,
                 invalid_points: Optional[List[Dict[str, float]]] = None):
        """
        set up the LocationAnalyzer
        :param wrapped_packets: a list of wrapped redvox packet lists to analyze, default None
        :param real_location: dictionary containing the real location of the station, default None
        :param invalid_points: list of gps points that should not be in the data set, default None
        """
        self.all_stations_closest_df = pd.DataFrame([], columns=CLOSEST_TO_SURVEY_COLUMNS)
        self.all_stations_mean_df = pd.DataFrame([], columns=MEAN_LOC_COLUMNS)
        self.all_stations_std_df = pd.DataFrame([], columns=STD_LOC_COLUMNS)
        self.all_stations_info_df = pd.DataFrame([], columns=STATION_INFO_COLUMNS)
        self.invalid_points = invalid_points
        self.all_gps_data = []
        self.valid_gps_data = []
        self._real_location = real_location
        # if given a path to redvox data, load data from there
        if wrapped_packets is not None:
            for wrapped_device_packets in wrapped_packets:
                self.get_loc_from_packets(wrapped_device_packets)

    def set_real_location(self, survey: Dict[str, float] = None):
        """
        set the real location
        :param survey: dictionary containing the station's location, default None
        """
        self._real_location = survey

    def get_real_location(self) -> Dict[str, float]:
        """
        return the station's real location
        :return: the station's real location
        """
        return self._real_location

    def get_all_dataframes(self) -> pd.DataFrame:
        """
        fuse all dataframes together, joined by station id
        :return: all 4 dataframes fused together
        """
        frames = [self.all_stations_info_df, self.all_stations_closest_df,
                  self.all_stations_mean_df, self.all_stations_std_df]
        return pd.concat(frames, axis=1)

    def get_stats_dataframes(self) -> pd.DataFrame:
        """
        fuse informational and statistic dataframes together, joined by station id
        :return: station info, mean and std dataframes fused together
        """
        frames = [self.all_stations_info_df, self.all_stations_mean_df, self.all_stations_std_df]
        return pd.concat(frames, axis=1)

    def get_loc_from_packets(self, w_p: List[reader.WrappedRedvoxPacket]):
        """
        store the location information and their mean and std using a collection of wrapped redvox packets
        assumes a list of redvox packets shares 1 device id
        :param w_p: a list of wrapped redvox packets to read
        """
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
        self.all_stations_info_df.loc[idd] = [dev_os_type, sample_rate]
        self.all_stations_std_df.loc[idd] = [std_loc["acc"], std_loc["lat"], std_loc["lon"],
                                             std_loc["alt"], std_loc["bar"]]
        self.all_stations_mean_df.loc[idd] = [mean_loc["acc"], mean_loc["lat"], mean_loc["lon"],
                                              mean_loc["alt"], mean_loc["bar"]]

    def analyze_data(self, write_output: bool = False):
        """
        analyze data, then if a real location exists, compare data to real location
          output is written if enabled
        :param write_output: boolean to write any debugging output, default False
        """
        self.validate_all()
        # if there's no real location, make the mean the real location
        if self._real_location is None:
            means = self.all_stations_mean_df
            self._real_location = {"lat": np.mean(means["mean lat"]), "lon": np.mean(means["mean lon"]),
                                   "alt": np.mean(means["mean alt"]), "bar": np.mean(means["mean bar"])}
        self.compare_with_real_location()
        # print results
        if write_output:
            self.print_to_csv("temp.csv")

    def get_barometric_heights(self, sea_pressure: float = AVG_SEA_LEVEL_PRESSURE_KPA) -> pd.DataFrame:
        """
        for each station, compute the barometric height using the mean
        :param sea_pressure: the local sea pressure in kPa, default AVG_SEA_LEVEL_PRESSURE_KPA
        :return: a dataframe with the barometric heights in meters and station id as the index
        """
        bar_heights = {}
        data_dict = self.all_stations_mean_df["mean bar"].T.to_dict()
        for index in data_dict.keys():
            bar_heights[index] = compute_barometric_height(data_dict[index], sea_pressure)
        barometric_heights = pd.DataFrame(bar_heights, index=["bar height"], columns=self.all_stations_mean_df.index)
        return barometric_heights.T

    def validate_all(self, validation_ranges: Tuple[float, float, float] = (DEFAULT_INCLUSION_HORIZONTAL_M,
                                                                            DEFAULT_INCLUSION_VERTICAL_M,
                                                                            DEFAULT_INCLUSION_VERTICAL_BAR_M), ):
        """
        check that all data in the data set are valid.  Remove outliers and strange values
        :param validation_ranges: tuple of floats that the data values are compared against for validation
        """
        # validation always assumes nothing is valid when it starts, so empty out the valid_gps_data
        self.valid_gps_data = []
        for station in self.all_gps_data:
            # if self._real_location is not None:
            #     validated_gps = self.validator(station, self._real_location)
            # else:
            #     validated_gps = validate_data(station)
            validated_gps = validate(station, validation_ranges, "blacklist", self.invalid_points)
            if validated_gps.get_size()[0] != 0:
                self.valid_gps_data.append(validated_gps)

    def compare_with_real_location(self):
        """
        find the closest valid data point to the real location.  information is stored in the data frames
        """
        # compute closest point to real location
        result = compute_distance_all(self._real_location, self.valid_gps_data)
        self.all_stations_closest_df = result[CLOSEST_TO_SURVEY_COLUMNS]
        self.all_stations_info_df = result[STATION_INFO_COLUMNS]
        self.all_stations_mean_df = result[MEAN_LOC_COLUMNS]
        self.all_stations_std_df = result[STD_LOC_COLUMNS]

    def print_location_df(self, info_type: Optional[str] = None, os_type: Optional[str] = None):
        """
        print a single dataframe or a group of dataframes
        :param info_type: string denoting the type or group of dataframes to output, default None
        :param os_type: string denoting the os of the stations to output, default None
        """
        if info_type == "real":
            print_station_df(self.all_stations_closest_df, os_type)
        elif info_type == "info":
            print_station_df(self.all_stations_info_df, os_type)
        elif info_type == "std":
            print_station_df(self.all_stations_std_df, os_type)
        elif info_type == "mean":
            print_station_df(self.all_stations_mean_df, os_type)
        elif info_type == "all":
            print_station_df(self.get_all_dataframes(), os_type)
        else:
            # fuse statistical dataframes together
            print_station_df(self.get_stats_dataframes(), os_type)

    def print_to_csv(self, path: str, os_type: Optional[str] = None, debug: Optional[bool] = False):
        """
        print dataframes to csv files in path
        :param path: string containing full path and file name
        :param os_type: string denoting the os of the stations to output, default None
        :param debug: if true, output debug statements, default False
        """
        # fuse all dataframes together
        result = self.get_all_dataframes()
        if os_type == "Android":
            get_all_android_station(result).to_csv(path)
        elif os_type == "iOS":
            get_all_ios_station(result).to_csv(path)
        else:
            os_type = "all"
            result.to_csv(path)
        if debug:
            print("Printed {} station data to {}.".format(os_type, path))


def get_all_ios_station(station_df: pd.DataFrame) -> pd.DataFrame:
    """
    return all iOS stations in the dataframe
    :param station_df: the dataframe to search
    :return: a dataframe with all data related to iOS stations in the dataframe
    """
    return station_df.loc[station_df["os"] == "iOS"]


def get_all_android_station(station_df: pd.DataFrame) -> pd.DataFrame:
    """
    return all android stations in the dataframe
    :param station_df: the dataframe to search
    :return: a dataframe with all data related to android stations in the dataframe
    """
    return station_df.loc[station_df["os"] == "Android"]


def print_station_df(station_df: pd.DataFrame, os_type: Optional[str] = None):
    """
    print a dataframe, filtering on the station's os type
    :param station_df: a dataframe to search
    :param os_type: os type to filter on, default None
    """
    if os_type == "Android":
        print(get_all_android_station(station_df))
    elif os_type == "iOS":
        print(get_all_ios_station(station_df))
    else:
        print(station_df)


def load_position_data(w_p: List[reader.WrappedRedvoxPacket]) -> GPSDataHolder:
    """
    load gps data from a list of wrapped redvox packets
    :param w_p: list of wrapped packets to read
    :return: all gps data from the packets in a GPSDataHolder
    """
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


def compute_barometric_height(barometric_pressure: float, sea_pressure: float = AVG_SEA_LEVEL_PRESSURE_KPA,
                              standard_temp: float = STANDARD_TEMPERATURE_K,
                              molar_air_mass: float = MOLAR_MASS_AIR_KG_PER_MOL,
                              gravity: float = GRAVITY_M_PER_S2,
                              gas_constant: float = UNIVERSAL_GAS_CONSTANT_KG_M2_PER_K_MOL_S2) -> float:
    """
    compute height of a single point using a station's barometric and sea-level pressure
    barometric equation from https://www.math24.net/barometric-formula/
    :param barometric_pressure: pressure at a station in kPa
    :param sea_pressure: pressure at sea level in kPa, default AVG_SEA_LEVEL_PRESSURE_KPA
    :param standard_temp: surface temperature in K, default STANDARD_TEMPERATURE_K
    :param molar_air_mass: molar mass of air in kg/mol, default MOLAR_MASS_AIR_KG_PER_MOL
    :param gravity: the acceleration of gravity in m/s2, default GRAVITY_M_PER_S2
    :param gas_constant: the universal gas constant in (kg * m2)/(K * mol * s2),
                            default UNIVERSAL_GAS_CONSTANT_KG_M2_PER_K_MOL_S2
    :return: height of station in meters
    """
    # formula and derivations:
    # P(h) = P0 * e**(-Mgh/RT) where:
    # P0 = AVG_SEA_LEVEL_PRESSURE_KPA = 101.325
    # g = GRAVITY_M_PER_S2 = 9.807
    # M = MOLAR_MASS_AIR_KG_PER_MOL = 0.02896
    # T = STANDARD_TEMPERATURE_K = 288.15
    # R = UNIVERSAL_GAS_CONSTANT_KG_M2_PER_K_MOL_S2 = 8.3143
    # therefore h = ln(P0/P(h)) / (Mg/RT)
    # due to log function, we can't let sea_pressure or barometric_pressure be 0
    if sea_pressure == 0.0:
        sea_pressure = EPSILON
    if barometric_pressure == 0.0:
        barometric_pressure = EPSILON
    barometric_height = np.log(sea_pressure / barometric_pressure) / (
            (molar_air_mass * gravity) / (standard_temp * gas_constant))
    return barometric_height


def compute_barometric_height_array(barometric_pressure: np.array, sea_pressure: float = AVG_SEA_LEVEL_PRESSURE_KPA,
                                    standard_temp: float = STANDARD_TEMPERATURE_K,
                                    molar_air_mass: float = MOLAR_MASS_AIR_KG_PER_MOL,
                                    gravity: float = GRAVITY_M_PER_S2,
                                    gas_constant: float = UNIVERSAL_GAS_CONSTANT_KG_M2_PER_K_MOL_S2) -> np.array:
    """
    compute height of many points using each station's barometric and sea-level pressure
    :param barometric_pressure: array of pressures at stations in kPa
    :param sea_pressure: pressure at sea level in kPa, default AVG_SEA_LEVEL_PRESSURE_KPA
    :param standard_temp: surface temperature in K, default STANDARD_TEMPERATURE_K
    :param molar_air_mass: molar mass of air in kg/mol, default MOLAR_MASS_AIR_KG_PER_MOL
    :param gravity: the acceleration of gravity in m/s2, default GRAVITY_M_PER_S2
    :param gas_constant: the universal gas constant in (kg * m2)/(K * mol * s2),
                            default UNIVERSAL_GAS_CONSTANT_KG_M2_PER_K_MOL_S2
    :return: the height of each station in meters
    """
    # due to log function, we can't let sea_pressure or barometric_pressure be 0
    if sea_pressure == 0.0:
        sea_pressure = EPSILON
    for index in range(len(barometric_pressure)):
        if barometric_pressure[index] == 0.0:
            barometric_pressure[index] = EPSILON
    barometric_height = np.log(sea_pressure / barometric_pressure) / (
            (molar_air_mass * gravity) / (standard_temp * gas_constant))
    return barometric_height


def get_component_dist_to_point(point: Dict[str, float], gps_data: pd.Series, bar_mean: float) -> \
        (float, float, float):
    """
    compute distance from the gps data point to the chosen point using haversine formula
    :param point: dict with location to compute distance to
    :param gps_data: series with gps data of one point
    :param bar_mean: the mean barometer reading
    :return: the distance in meters of the horizontal and vertical gps components and barometer readings
    """
    # horizontal distance, use haversine formula
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


def get_gps_dist_to_location(point: Dict[str, float], gps_dataholder: GPSDataHolder,
                             bar_alt: Optional[float] = None) -> np.array:
    """
    compute distance from multiple gps points to the chosen point using haversine formula
    :param point: dict with location to compute distance to
    :param gps_dataholder: all the gps data points to compute distance from
    :param bar_alt: height as measured by a barometer, default None
    :return: array of all distances in meters from gps point to chosen point
    """
    # compute distance from the gps data points to the location
    # if given a barometer altitude value, use that instead of the gps altitude
    if bar_alt is not None:
        station_alt = bar_alt
    else:
        station_alt = gps_dataholder.gps_df.loc["altitude"].to_numpy()
    # user haversine formula
    dlon = gps_dataholder.gps_df.loc["longitude"].to_numpy() - point["lon"]
    dlat = gps_dataholder.gps_df.loc["latitude"].to_numpy() - point["lat"]
    haver = np.sin(dlat * DEG_TO_RAD / 2.0) ** 2.0 + (np.cos(point["lat"] * DEG_TO_RAD) *
                                                      np.cos(gps_dataholder.gps_df.loc["latitude"].to_numpy()
                                                             * DEG_TO_RAD)
                                                      * np.sin(dlon * DEG_TO_RAD / 2.0) ** 2.0)
    c = 2 * np.arcsin(np.minimum([1.0], np.sqrt(haver)))
    h_dist = EARTH_RADIUS_M * c
    dist_array = (h_dist ** 2 + (point["alt"] - station_alt) ** 2)
    return np.sqrt(dist_array)


def validate_blacklist(gps_data: pd.Series, point: Dict[str, float], bar_mean: float,
                       inclusion_ranges: Tuple[float, float, float] = (DEFAULT_INCLUSION_HORIZONTAL_M,
                                                                       DEFAULT_INCLUSION_VERTICAL_M,
                                                                       DEFAULT_INCLUSION_VERTICAL_BAR_M)) -> bool:
    """
    return True if the gps point is NOT in the blacklist
    :param gps_data: data to compare
    :param point: the point that is blacklisted
    :param bar_mean: the mean of the barometer measurements
    :param inclusion_ranges: distance from blacklisted point to be considered close enough
    :return: True if point is not in blacklisted point's vicinity
    """
    # calculate distance from gps data to invalid point
    h_dist, v_dist, v_bar_dist = get_component_dist_to_point(point, gps_data, bar_mean)
    # if outside horizontal and vertical distance, we're far enough away from the invalid point
    return h_dist > inclusion_ranges[0] and (v_dist > inclusion_ranges[1] or v_bar_dist > inclusion_ranges[2])


def validate_near_point(gps_data: pd.Series, point: Dict[str, float], bar_mean: float,
                        inclusion_ranges: Tuple[float, float, float] = (DEFAULT_INCLUSION_HORIZONTAL_M,
                                                                        DEFAULT_INCLUSION_VERTICAL_M,
                                                                        DEFAULT_INCLUSION_VERTICAL_BAR_M)) -> bool:
    """
    return True if the gps point IS close to the chosen point
    :param gps_data: data to compare
    :param point: the chosen point to compare against
    :param bar_mean: the mean of the barometer measurements
    :param inclusion_ranges: distance from chosen point to be considered close enough
    :return: True if point is within the chosen point's vicinity
    """
    # calculate distance from gps data to point
    h_dist, v_dist, v_bar_dist = get_component_dist_to_point(point, gps_data, bar_mean)
    # if within horizontal distance and vertical distance, we're close enough to the point
    return h_dist <= inclusion_ranges[0] and (v_dist <= inclusion_ranges[1] or v_bar_dist <= inclusion_ranges[2])


def point_on_line_side(line_points: Tuple[Dict[str, float], Dict[str, float]], point: Dict[str, float]) -> float:
    """
    check which side of a line the point is on
    algorithm from: http://geomalgorithms.com/a03-_inclusion.html
    :param line_points: two coordinates that define a line
    :param point: point to test
    :return: < 0 for right side, == 0 for on line, > 0 for left side
    """
    return ((line_points[1]["lon"] - line_points[0]["lon"]) * (point["lat"] - line_points[0]["lat"]) -
            (point["lon"] - line_points[0]["lon"]) * (line_points[1]["lat"] - line_points[0]["lat"]))


def validate_point_in_polygon(point: Dict[str, float], edges: List[Dict[str, float]]) -> bool:
    """
    Use winding number algorithm to determine if a point is in a polygon (or on the edge)
    if winding number is 0, point is outside polygon
    algorithm from: http://geomalgorithms.com/a03-_inclusion.html
    :param point: coordinates of the point to compare
    :param edges: list of coordinates of the edges of the polygon, with the last edge equal to the first
    :return: True if point is in the polygon
    """
    wn = 0  # winding number
    for index in range(len(edges) - 1):
        if edges[index]["lat"] <= point["lat"]:
            if edges[index + 1]["lat"] > point["lat"]:
                if point_on_line_side((edges[index], edges[index + 1]), point) >= 0:
                    wn += 1
        elif edges[index + 1]["lat"] <= point["lat"]:
            if point_on_line_side((edges[index], edges[index + 1]), point) <= 0:
                wn -= 1
    return wn != 0


def validate(data_to_test: GPSDataHolder,
             inclusion_ranges: Tuple[float, float, float] = (DEFAULT_INCLUSION_HORIZONTAL_M,
                                                             DEFAULT_INCLUSION_VERTICAL_M,
                                                             DEFAULT_INCLUSION_VERTICAL_BAR_M),
             validation_type: str = None, validation_points: List[Dict[str, float]] = None,
             debug: bool = False) -> GPSDataHolder:
    """
    validation master function.  Can perform any kind of validation requested
    :param data_to_test: gps data to validate
    :param inclusion_ranges: ranges to include a data point with a validation point
    :param validation_type: the kind of validation to perform, default None
    :param validation_points: the points to validate against, default None
    :param debug: if True, output debugging information, default False
    :return: all valid gps data
    """
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


def compute_distance_all(point: Dict[str, float], all_gps_data: List[GPSDataHolder]) -> pd.DataFrame:
    """
    compute distance from all gps data points to the chosen point
    :param point: the point to compute distance to
    :param all_gps_data: the gps data points to compute distance from
    :return: dataframe containing all information about the gps points' distance to the chosen point
    """
    # compare distances from multiple gps points to the location.  return the closest point
    closeness = {}
    for gps_dh in all_gps_data:
        closeness.update(compute_distance(point, gps_dh))
    return pd.DataFrame(closeness, index=MASTER_COLUMNS).T


def compute_distance(point: dict, gps_data: GPSDataHolder) -> dict:
    """
    compute the distance from the gps points to the chosen point
    :param point: the chosen point to compute distance to
    :param gps_data: the data points to compute distance from
    :return: dictionary containing all information about the gps points' distance to the chosen point
    """
    # for a location, compute distance to closest data point
    idd = gps_data.id
    stations_data = {idd: None}
    gps_loc = gps_data.get_mean_all()

    # find closest barometer altitude to location
    # bar_alt_tmp = (((SEA_PRESSURE / np.array(gps_data.barometer.data)) ** 0.190263096) - 1) * (SOL_TEMP / 0.0065)
    if "sea bar" in point.keys() and point["sea_bar"] is not None:
        bar_alt_tmp = compute_barometric_height_array(np.array(gps_data.barometer.get_data()), point["sea_bar"])
    else:
        bar_alt_tmp = compute_barometric_height_array(np.array(gps_data.barometer.get_data()))
    # simplified barometric equation:
    # P(h) = 101.325 * e ** (-0.00012h) -> P(h) / 101.325 = 1 / (e ** 0.00012h)
    # e ** 0.00012h = 101.325 / P(h) -> 0.00012h = ln(101.325) - ln(P))
    # SEA_PRESSURE = 101.325
    # h = ln(SEA_PRESSURE/P(h)) / 0.00012
    min_index = np.argmin(np.abs(bar_alt_tmp - point["alt"]))
    gps_data.barometer.best_value = gps_data.barometer.get_data()[min_index]
    bar_alt = bar_alt_tmp[min_index]
    # for all gps coords, find closest to solution
    dist_array = get_gps_dist_to_location(point, gps_data)
    min_index = np.argmin(dist_array)
    # compute distance using best barometer measurement
    dist_array_bar = get_gps_dist_to_location(point, gps_data, bar_alt)
    min_bar_index = np.argmin(dist_array_bar)
    # compare minimum of pure gps and gps with barometer
    if dist_array_bar[min_bar_index] < dist_array_bar[min_index]:
        min_index = min_bar_index
        dist_array = dist_array_bar

    # finding the std of the distances is basically finding the std of accuracy
    acc_std = np.std(dist_array)
    lat_std = np.std(np.abs(point["lat"] - gps_data.gps_df.loc["latitude"].to_numpy()))
    lon_std = np.std(np.abs(point["lon"] - gps_data.gps_df.loc["longitude"].to_numpy()))
    alt_std = np.std(np.abs(point["alt"] - gps_data.gps_df.loc["altitude"].to_numpy()))
    bar_std = gps_data.barometer.get_std()

    # put data into dictionary to store in data frames later
    stations_data[idd] = [gps_data.os_type, gps_data.mic_samp_rate_hz, gps_data.gps_df.loc["accuracy", min_index],
                          gps_data.gps_df.loc["latitude", min_index], gps_data.gps_df.loc["longitude", min_index],
                          gps_data.gps_df.loc["altitude", min_index], gps_data.barometer.best_value,
                          dist_array[min_index], gps_loc["acc"], gps_loc["lat"], gps_loc["lon"],
                          gps_loc["alt"], gps_loc["bar"], acc_std, lat_std, lon_std, alt_std, bar_std]

    return stations_data


def load_kml(kml_file: str) -> Dict[str, Dict[str, float]]:
    """
    load location from a kml file
    :param kml_file: full path of the file to load data from
    :return: dictionary of locations with identifiers
    """
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
    """
    put information from master_dict into a kml file
    :param kml_file: full path of kml file to write data to
    :param master_dict: the dictionary of information to write
    """
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
