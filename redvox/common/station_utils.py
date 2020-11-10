"""
Defines generic station metadata for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
"""
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass, field

from redvox.common import tri_message_stats as tms
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider


@dataclass
class StationKey:
    """
    A set of values that uniquely define a station
    Properties:
        id: str, id of the station
        uuid: str, uuid of the station
        start_timestamp_micros: float, starting time of the station in microseconds since epoch UTC
    """
    id: str
    uuid: str
    start_timestamp_micros: float

    def get_key(self) -> Tuple[str, str, float]:
        return self.id, self.uuid, self.start_timestamp_micros


@dataclass
class StationLocation:
    """
    Generic StationLocation class for API-independent analysis
    Properties:
        lat_lon_timestamp: float, timestamp of the latitude and longitude, default np.nan
        altitude_timestamp: float, timestamp of the altitude, default np.nan
        speed_timestamp: float, timestamp of the speed, default np.nan
        bearing_timestamp: float, timestamp of the bearing, default np.nan
        provider: str, method/device name that provided the location, default "None"
        score: float, the value of the location's quality, default np.nan
        latitude: float, the latitude in degrees of the location, default np.nan
        longitude: float, the longitude in degrees of the location, default np.nan
        altitude: float, the altitude in meters of the location, default np.nan
        speed: float, the speed in meters/second of the location, default np.nan
        bearing: float, the bearing in degrees of the location, default np.nan
        horizontal_accuracy: float, the horizontal accuracy in meters of the location, default np.nan
        vertical_accuracy: float, the vertical accuracy in meters of the location, default np.nan
        speed_accuracy: float, the speed accuracy in meters/second of the location, default np.nan
        bearing_accuracy: float, the bearing accuracy in degrees of the location, default np.nan
    """
    lat_lon_timestamp: float = np.nan
    altitude_timestamp: float = np.nan
    speed_timestamp: float = np.nan
    bearing_timestamp: float = np.nan
    provider: str = "None"
    score: float = np.nan
    latitude: float = np.nan
    longitude: float = np.nan
    altitude: float = np.nan
    speed: float = np.nan
    bearing: float = np.nan
    horizontal_accuracy: float = np.nan
    vertical_accuracy: float = np.nan
    speed_accuracy: float = np.nan
    bearing_accuracy: float = np.nan

    def update_timestamps(self, time_delta: float):
        """
        adds the time_delta to the location's timestamps; use negative values to go backwards in time
        :param time_delta: time to add to location's timestamps
        """
        self.lat_lon_timestamp += time_delta
        self.altitude_timestamp += time_delta
        self.speed_timestamp += time_delta
        self.bearing_timestamp += time_delta

    def is_empty(self) -> bool:
        """
        :return: True if there is no lat_lon_timestamp
        """
        return np.isnan(self.lat_lon_timestamp)


def station_location_from_data(data_location: pd.Series) -> StationLocation:
    """
    function to convert a location sensor pandas series to a StationLocation
    :param data_location: a pandas series object to convert
    :return: StationLocation with data from data_location
    """
    return StationLocation(data_location["timestamps"], data_location["timestamps"],
                           data_location["timestamps"], data_location["timestamps"],
                           LocationProvider(data_location["location_provider"]).name,
                           np.nan, data_location["latitude"], data_location["longitude"],
                           data_location["altitude"], data_location["speed"], data_location["bearing"],
                           data_location["horizontal_accuracy"], data_location["vertical_accuracy"],
                           data_location["speed_accuracy"], data_location["bearing_accuracy"])


def _location_sorter(best_location: StationLocation, other_location: StationLocation, new_location: StationLocation,
                     ascending: bool = True) -> Tuple[StationLocation, StationLocation]:
    """
    Sorts up to three locations for quality purposes.
    the ascending parameter is used specifically for timestamps that come before a target time.
    :param best_location: current best location
    :param other_location: current other best location
    :param new_location: new location to compare against
    :param ascending: if True, values are sorted in ascending order, default True
    :return: the new best and other best locations
    """
    if best_location.is_empty():
        new_best_location = new_location
        new_other_location = other_location
    else:
        locs_to_sort = [best_location, other_location, new_location]
        times_to_sort = np.array([x.lat_lon_timestamp for x in locs_to_sort])
        if not ascending:
            times_to_sort *= -1
        sorted_locs = [locs_to_sort[i] for i in np.argsort(times_to_sort)]
        new_best_location = sorted_locs[0]
        new_other_location = sorted_locs[1]
    return new_best_location, new_other_location


@dataclass
class LocationData:
    """
    Location metadata statistics for the station
    Properties:
        best_location: Optional StationLocation object, the best rated location for the station, default None
        all_locations: List of StationLocation objects, all locations for the station including best, default empty list
        mean_latitude: float, the mean latitude in degrees of all locations, default np.nan
        std_latitude: float, the std dev of latitude in degrees of all locations, default 0.0
        mean_longitude: float, the mean longitude in degrees of all locations, default np.nan
        std_longitude: float, the std dev of longitude in degrees of all locations, default 0.0
        mean_altitude: float, the mean altitude in meters of all locations, default np.nan
        std_altitude: float, the std dev of altitude in meters of all locations, default 0.0
        mean_speed: float, the mean speed in meters/second of all locations, default np.nan
        std_speed: float, the std dev of speed in meters/second of all locations, default 0.0
        mean_bearing: float, the mean bearing in degrees of all locations, default np.nan
        std_bearing: float, the std dev of bearing in degrees of all locations, default 0.0
        mean_horizontal_accuracy: float, the mean horizontal accuracy in meters of all locations, default np.nan
        std_horizontal_accuracy: float, the std dev of horizontal accuracy in meters of all locations, default 0.0
        mean_vertical_accuracy: float, the mean vertical accuracy in meters of all locations, default np.nan
        std_vertical_accuracy: float, the std dev of vertical accuracy in meters of all locations, default 0.0
        mean_speed_accuracy: float, the mean speed accuracy in meters/second of all locations, default np.nan
        std_speed_accuracy: float, the std dev of speed accuracy in meters/second of all locations, default 0.0
        mean_bearing_accuracy: float, the mean bearing accuracy in degrees of all locations, default np.nan
        std_bearing_accuracy: float, the std dev of bearing accuracy in degrees of all locations, default 0.0
        mean_provider: str, method/device name that provided the mean location, default "None"
    """
    best_location: Optional[StationLocation] = None
    all_locations: List[StationLocation] = field(default_factory=list)
    mean_latitude: float = np.nan
    std_latitude: float = 0.0
    mean_longitude: float = np.nan
    std_longitude: float = 0.0
    mean_altitude: float = np.nan
    std_altitude: float = 0.0
    mean_speed: float = np.nan
    std_speed: float = 0.0
    mean_bearing: float = np.nan
    std_bearing: float = 0.0
    mean_horizontal_accuracy: float = np.nan
    std_horizontal_accuracy: float = 0.0
    mean_vertical_accuracy: float = np.nan
    std_vertical_accuracy: float = 0.0
    mean_speed_accuracy: float = np.nan
    std_speed_accuracy: float = 0.0
    mean_bearing_accuracy: float = np.nan
    std_bearing_accuracy: float = 0.0
    mean_provider: str = "None"

    def update_timestamps(self, time_delta: float):
        """
        adds the time_delta to all locations' timestamps; use negative values to go backwards in time
        :param time_delta: time to add to all locations' timestamps
        """
        for location in self.all_locations:
            location.lat_lon_timestamp += time_delta
            location.altitude_timestamp += time_delta
            location.speed_timestamp += time_delta
            location.bearing_timestamp += time_delta

    def get_sorted_all_locations(self) -> List[StationLocation]:
        """
        :return: sorted list of self.all_locations by lat_lon_timestamp
        """
        sorted_indices = np.argsort([x.lat_lon_timestamp for x in self.all_locations])
        return [self.all_locations[i] for i in sorted_indices]

    def update_window_locations(self, start_datetime: float, end_datetime: float):
        """
        Updates all_locations to be any location within the window and up to two locations outside the window.
        Locations with timestamp equal to start or end datetimes are considered outside
        :param start_datetime: the start timestamp in microseconds since epoch UTC of the window to consider
        :param end_datetime: the end timestamp in microseconds since epoch UTC of the window to consider
        """
        valid_locations: List[StationLocation] = []
        before_location: StationLocation = StationLocation()
        after_location: StationLocation = StationLocation()
        other_before_location: StationLocation = StationLocation()
        other_after_location: StationLocation = StationLocation()

        for location in self.all_locations:
            if start_datetime < location.lat_lon_timestamp < end_datetime:
                valid_locations.append(location)
            elif start_datetime >= location.lat_lon_timestamp:
                before_location, other_before_location = \
                    _location_sorter(before_location, other_before_location, location, False)
            else:
                after_location, other_after_location = _location_sorter(after_location, other_after_location, location)

        if not before_location.is_empty():
            valid_locations.append(before_location)
        if not after_location.is_empty():
            valid_locations.append(after_location)
        if len(valid_locations) < 2:
            if after_location.is_empty() and not other_before_location.is_empty():
                valid_locations.append(other_before_location)
            elif before_location.is_empty() and not other_after_location.is_empty():
                valid_locations.append(other_after_location)
        self.all_locations = valid_locations

    def calc_mean_and_std_from_locations(self, debug: bool = False) -> bool:
        """
        compute the mean and std dev from the locations in the object
        :param debug: if True, output warnings when they occur, default False
        :return: True if success, False if failed
        """
        if len(self.all_locations) > 0:
            self.mean_latitude = np.mean([x.latitude for x in self.all_locations], axis=0)
            self.std_latitude = np.std([x.latitude for x in self.all_locations], axis=0)
            self.mean_longitude = np.mean([x.longitude for x in self.all_locations], axis=0)
            self.std_longitude = np.std([x.longitude for x in self.all_locations], axis=0)
            self.mean_altitude = np.mean([x.altitude for x in self.all_locations], axis=0)
            self.std_altitude = np.std([x.altitude for x in self.all_locations], axis=0)
            self.mean_speed = np.mean([x.speed for x in self.all_locations], axis=0)
            self.std_speed = np.std([x.speed for x in self.all_locations], axis=0)
            self.mean_bearing = np.mean([x.bearing for x in self.all_locations], axis=0)
            self.std_bearing = np.std([x.bearing for x in self.all_locations], axis=0)
            self.mean_horizontal_accuracy = np.mean([x.horizontal_accuracy for x in self.all_locations], axis=0)
            self.std_horizontal_accuracy = np.std([x.horizontal_accuracy for x in self.all_locations], axis=0)
            self.mean_vertical_accuracy = np.mean([x.vertical_accuracy for x in self.all_locations], axis=0)
            self.std_vertical_accuracy = np.std([x.vertical_accuracy for x in self.all_locations], axis=0)
            self.mean_speed_accuracy = np.mean([x.speed_accuracy for x in self.all_locations], axis=0)
            self.std_speed_accuracy = np.std([x.speed_accuracy for x in self.all_locations], axis=0)
            self.mean_bearing_accuracy = np.mean([x.bearing_accuracy for x in self.all_locations], axis=0)
            self.std_bearing_accuracy = np.std([x.bearing_accuracy for x in self.all_locations], axis=0)
        else:
            if debug:
                print("WARNING: Not enough locations to process mean and std dev on!")
            return False
        return True


class TimeSyncData:
    """
    Generic TimeSync object for packets
    Properties:
        timesync_data: dataframe of the timestamps of the sync exchanges, default empty dataframe
                                Must be a multiple of 6 elements long.
        best_latency: float, best latency of the time sync exchanges, default np.nan
        best_offset: float, best offset of the time sync exchanges, default 0.0
    """
    def __init__(self, timesync_data: np.array = np.array([]),
                 best_latency: float = np.nan, best_offset: float = 0.0):
        """
        initialize the TimeSyncData object
        :param timesync_data: np.array of the timestamps of the sync exchanges, default empty np.array
                                Must be a multiple of 6 elements long.
                                May be 1 dimension, in which case will be converted into a 2-d np.ndarray
        :param best_latency: float, best latency of the time sync exchanges, default np.nan
        :param best_offset: float, best offset of the time sync exchanges, default 0.0
        """
        if len(timesync_data) > 0 and len(timesync_data.shape) != 2:
            timesync_data = np.transpose(tms.transmit_receive_timestamps_microsec(timesync_data))
        elif len(timesync_data) == 0:
            timesync_data = []
        self.timesync_data = pd.DataFrame(timesync_data, columns=["a1", "a2", "a3", "b1", "b2", "b3"])
        self.best_latency = best_latency
        self.best_offset = best_offset

    def num_samples(self) -> int:
        """
        :return: the number of time sync exchanges, which are the rows in the dataframe
        """
        return self.timesync_data.shape[0]


@dataclass
class DataPacket:
    """
    Generic DataPacket class for API-independent analysis
    Properties:
        server_received_timestamp: float, server timestamp of when data was received by the server
        app_start_timestamp: float, machine timestamp of when app started
        data_start_timestamp: float, machine timestamp of the start of the packet's data
        data_end_timestamp: float, machine timestamp of the end of the packet's data, default np.nan
        duration_s: float, duration of data packet in seconds, default 0.0
        num_audio_samples: int, number of audio samples in the data packet, default 0
        timesync: TimeSyncData object, the timesync data associated with the packet, default empty TimeSyncData object
        micros_to_next_packet: float, the length of time in microseconds to reach the next
                                packet's (in the station's data) start time, default np.nan
                                Should be close to 0 or close to self.expected_sample_interval_s
                                (when converted to same units)
        best_location: Optional StationLocation metadata, default None
    """
    server_timestamp: float
    app_start_timestamp: float
    data_start_timestamp: float
    data_end_timestamp: float = np.nan
    duration_s: float = 0.0
    num_audio_samples: int = 0
    timesync: TimeSyncData = TimeSyncData()
    micros_to_next_packet: float = np.nan
    best_location: Optional[StationLocation] = None

    def expected_sample_interval_s(self) -> float:
        """
        the packet's expected sample interval based on its own data
        :return: the packet's expected sample interval in seconds
        """
        return self.duration_s / self.num_audio_samples


@dataclass
class StationTiming:
    """
    Generic StationTiming class for API-independent analysis
    Properties:
        station_start_timestamp: float, timestamp when station started recording
        audio_sample_rate_hz: float, sample rate in hz of audio sensor
        station_first_data_timestamp: float, first timestamp chronologically of the data
        episode_start_timestamp_s: float, timestamp of start of segment of interest in seconds since epoch UTC,
                                    default np.nan
        episode_end_timestamp_s: float, timestamp of end of segment of interest in seconds since epoch UTC,
                                    default np.nan
        station_best_latency: float, best latency of data, default np.nan
        station_best_offset: float, best offset of data, default 0.0
        station_mean_offset: float, mean offset of data, default 0.0
        station_std_offset: float, std dev of offset of data, default 0.0
    """
    station_start_timestamp: float
    audio_sample_rate_hz: float
    station_first_data_timestamp: float
    episode_start_timestamp_s: float = np.nan
    episode_end_timestamp_s: float = np.nan
    station_best_latency: float = np.nan
    station_best_offset: float = 0.0
    station_mean_offset: float = 0.0
    station_std_offset: float = 0.0


@dataclass
class StationMetadata:
    """
    Generic StationMetadata class for API-independent analysis
    Properties:
        station_id: str, id of the station
        station_make: str, maker of the station
        station_model: str, model of the station
        station_timing_is_corrected: bool, if True, the station's timestamps have been altered from their raw values
                                        default False
        station_os: optional str, operating system of the station, default None
        station_os_version: optional str, station OS version, default None
        station_app: optional str, the name of the recording software used by the station, default None
        station_app_version: optional str, the recording software version, default None
        is_mic_scrambled: optional bool, True if mic data is scrambled, default False
        timing_data: optional StationTiming metadata, default None
        station_calib: optional float, station calibration value, default None
        station_network_name: optional str, name/code of network station belongs to, default None
        station_name: optional str, name/code of station, default None
        station_location_name: optional str, name/code of location station is at, default None
        station_channel_name: optional str, name/code of channel station is recording, default None
        station_channel_encoding: optional str, name/code of channel encoding method, default None
        station_uuid: optional str, uuid of the station, default is the same value as station_id
        best_location: optional StationLocation metadata, default empty LocationData
    """
    station_id: str
    station_make: str
    station_model: str
    station_timing_is_corrected: bool = False
    station_os: Optional[str] = None
    station_os_version: Optional[str] = None
    station_app: Optional[str] = None
    station_app_version: Optional[str] = None
    is_mic_scrambled: Optional[bool] = False
    timing_data: Optional[StationTiming] = None
    station_calib: Optional[float] = None
    station_network_name: Optional[str] = None
    station_name: Optional[str] = None
    station_location_name: Optional[str] = None
    station_channel_name: Optional[str] = None
    station_channel_encoding: Optional[str] = None
    station_uuid: Optional[str] = None
    location_data: Optional[LocationData] = None

    def __post_init__(self):
        """
        if the station_uuid is None, set it to be station_id
        if the location data is None, set it to empty LocationData
        """
        if not self.station_uuid:
            self.station_uuid = self.station_id
        if not self.location_data:
            self.location_data = LocationData()
