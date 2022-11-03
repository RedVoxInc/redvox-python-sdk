from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass

import numpy as np

import redvox
from redvox.common.errors import RedVoxExceptions
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc
from redvox.common.timesync import TimeSync
from redvox.common.offset_model import OffsetModel, simple_offset_weighted_linear_regression
import redvox.api1000.proto.redvox_api_m_pb2 as api_m
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider


SESSION_VERSION = "2022-11-02"  # Version of the SessionModel
GPS_TRAVEL_MICROS = 60000.  # Assumed GPS latency in microseconds
GPS_VALIDITY_BUFFER = 2000.  # microseconds before GPS offset is considered valid
DEGREES_TO_METERS = 0.00001  # About 1 meter in degrees
NUM_BUFFER_POINTS = 15  # number of data points to keep in a buffer
MOVEMENT_METERS = 5.  # number of meters before station is considered moved

COLUMN_TO_ENUM_FN = {"location_provider": lambda l: LocationProvider(l).name}

# These are used for checking if a field is present or not
_ACCELEROMETER_FIELD_NAME: str = "accelerometer"
_AMBIENT_TEMPERATURE_FIELD_NAME: str = "ambient_temperature"
_AUDIO_FIELD_NAME: str = "audio"
_COMPRESSED_AUDIO_FIELD_NAME: str = "compressed_audio"
_GRAVITY_FIELD_NAME: str = "gravity"
_GYROSCOPE_FIELD_NAME: str = "gyroscope"
_IMAGE_FIELD_NAME: str = "image"
_LIGHT_FIELD_NAME: str = "light"
_LINEAR_ACCELERATION_FIELD_NAME: str = "linear_acceleration"
_LOCATION_FIELD_NAME: str = "location"
_MAGNETOMETER_FIELD_NAME: str = "magnetometer"
_ORIENTATION_FIELD_NAME: str = "orientation"
_PRESSURE_FIELD_NAME: str = "pressure"
_PROXIMITY_FIELD_NAME: str = "proximity"
_RELATIVE_HUMIDITY_FIELD_NAME: str = "relative_humidity"
_ROTATION_VECTOR_FIELD_NAME: str = "rotation_vector"
_VELOCITY_FIELD_NAME: str = "velocity"


def _has_sensor(
        data: Union[api_m.RedvoxPacketM, api_m.RedvoxPacketM.Sensors], field_name: str
) -> bool:
    """
    Returns true if the given packet or sensors instance contains the valid sensor.

    :param data: Either a packet or a packet's sensors message.
    :param field_name: The name of the sensor being checked.
    :return: True if the sensor exists, False otherwise.
    """
    if isinstance(data, api_m.RedvoxPacketM):
        # noinspection Mypy,PyTypeChecker
        return data.sensors.HasField(field_name)

    if isinstance(data, api_m.RedvoxPacketM.Sensors):
        # noinspection Mypy,PyTypeChecker
        return data.HasField(field_name)

    return False


def get_all_sensors_in_packet(packet: api_m.RedvoxPacketM) -> List[str]:
    """
    :param packet: packet to check
    :return: list of all sensors in the packet
    """
    result: List[str] = []
    for s in [_ACCELEROMETER_FIELD_NAME, _AMBIENT_TEMPERATURE_FIELD_NAME, _AUDIO_FIELD_NAME,
              _COMPRESSED_AUDIO_FIELD_NAME, _GRAVITY_FIELD_NAME, _GYROSCOPE_FIELD_NAME, _IMAGE_FIELD_NAME,
              _LIGHT_FIELD_NAME, _LINEAR_ACCELERATION_FIELD_NAME, _LOCATION_FIELD_NAME, _MAGNETOMETER_FIELD_NAME,
              _ORIENTATION_FIELD_NAME, _PRESSURE_FIELD_NAME, _PROXIMITY_FIELD_NAME, _RELATIVE_HUMIDITY_FIELD_NAME,
              _ROTATION_VECTOR_FIELD_NAME, _VELOCITY_FIELD_NAME]:
        if _has_sensor(packet, s):
            result.append(s)
    return result


def _dict_str(d: dict) -> str:
    """
    :param d: dict to stringify
    :return: a dictionary as string
    """
    r = ""
    if len(d.keys()) > 0:
        last_key = list(d.keys())[-1]
        for c, v in d.items():
            r += f"{c}: {v}"
            if c != last_key:
                r += ", "
    return r


@dataclass
class LocationStat:
    """
    Stores the stats of a single location source
    Variance and standard deviation tuples are optional arguments and will be set to 0 if none are given.
    If one is given when initialized, but not the other, the proper relational function will be applied to the
    existing value to get the other.
    If both are given, nothing is done to either value; we assume the user has provided the correct values.

    properties:
        source_name: str, name of the source of the location data.  Default empty string

        count: int, number of data points for that source.  Default 0

        means: Tuple of float, the mean of the latitude, longitude, and altitude.  Default tuple of np.nan

        variance: Tuple of float, the variance of the latitude, longitude, and altitude.  Default tuple of 0

        std_dev: Tuple of float, the standard deviations of latitude, longitude, and altitude.  Default tuple of 0.
    """
    source_name: str = ""
    count: int = 0
    means: Tuple[float, float, float] = (np.nan, np.nan, np.nan)
    variance: Optional[Tuple[float, float, float]] = None
    std_dev: Optional[Tuple[float, float, float]] = None

    def __post_init__(self):
        """
        ensures the variance and std_dev values are correctly set
        """
        if self.variance is None and self.std_dev:
            self.variance = (self.std_dev[0] * self.std_dev[0],
                             self.std_dev[1] * self.std_dev[1],
                             self.std_dev[2] * self.std_dev[2])
        elif self.std_dev is None and self.variance:
            self.std_dev = np.sqrt(self.variance)
        elif self.std_dev is None and self.variance is None:
            self.variance = (0., 0., 0.)
            self.std_dev = (0., 0., 0.)

    def __str__(self):
        return f"source_name: {self.source_name}, " \
               f"count: {self.count}, " \
               f"means (lat, lon, alt): {self.means}, " \
               f"std_dev (lat, lon, alt): {self.std_dev}, " \
               f"variance (lat, lon, alt): {self.variance}"


class LocationStats:
    """
    Stores the stats of all locations

    protected:
        _location_stats: all the location stats, default empty list
    """
    def __init__(self, loc_stats: Optional[List[LocationStat]] = None):
        """
        initialize the stats

        :param loc_stats: the list of stats to start with, default None
        """
        self._location_stats: List[LocationStat] = [] if loc_stats is None else loc_stats

    def __repr__(self):
        return f"_location_stats: {[n for n in self._location_stats]}"

    def __str__(self):
        return f"stats: {[n.__str__() for n in self._location_stats]}"

    def add_loc_stat(self, new_loc: LocationStat):
        """
        adds a LocationStat to the stats

        :param new_loc: LocationStat to add
        """
        self._location_stats.append(new_loc)

    def get_all_stats(self) -> List[LocationStat]:
        """
        :return: all location stats
        """
        return self._location_stats.copy()

    def get_sources(self) -> List[str]:
        """
        :return: the sources of all location stats
        """
        return [n.source_name for n in self._location_stats]

    def get_source(self, source: str) -> Optional[LocationStat]:
        """
        :param source: source name to get
        :return: LocationStat of source requested or None if source doesn't exist
        """
        for n in self._location_stats:
            if n.source_name == source:
                return n
        return None

    def has_source(self, source: str) -> bool:
        """
        :param source: the source name to check for
        :return: True if the source name is in the stats, False otherwise
        """
        for n in self._location_stats:
            if n.source_name == source:
                return True
        return False

    def find_loc_by_source(self, source: str) -> Optional[LocationStat]:
        """
        :param source: the source name to get
        :return: the LocationStat with the same source name as the input, or None if the input doesn't exist
        """
        for n in self._location_stats:
            if n.source_name == source:
                return n
        return None

    def add_count_by_source(self, source: str, val_to_add: int) -> Optional[LocationStat]:
        """
        :param source: the source name to update count for
        :param val_to_add: the number of new points to add to the count
        :return: the LocationStat with the same source name as the input, or None if the source doesn't exist
        """
        for n in self._location_stats:
            if n.source_name == source:
                n.count += val_to_add
                return n
        return None

    def add_means_by_source(self, source: str, val_to_add: int,
                            means_to_add: Tuple[float, float, float]) -> Optional[LocationStat]:
        """
        :param source: the source name to update count and means for
        :param val_to_add: the number of new points to add to the count
        :param means_to_add: the means of the location to add
        :return: the updated LocationStat with the same source name as the input, or None if the source doesn't exist
        """
        for n in self._location_stats:
            if n.source_name == source:
                n.count += val_to_add
                n.means = tuple(map(lambda i, j: i + ((j - i) / n.count), n.means, means_to_add))
                return n
        return None

    @staticmethod
    def _update_variances(num_old_samples: int, old_vari: float, old_mean: float,
                          num_new_samples: int, new_vari: float, new_mean: float) -> float:
        """
        adds new variance to old variance to get variance of total set

        :param num_old_samples: number of old samples
        :param old_vari: old variance
        :param num_new_samples: number of new samples
        :param new_vari: new variance
        :return: variance of total set
        """
        if num_old_samples + num_new_samples == 0:
            return 0.
        combined_mean = (num_old_samples * old_mean + num_new_samples * new_mean) / (num_old_samples + num_new_samples)
        return ((num_old_samples * (old_vari + np.power((old_mean - combined_mean), 2))
                 + num_new_samples * (new_vari + np.power((new_mean - combined_mean), 2)))
                / (num_old_samples + num_new_samples))

    def add_variance_by_source(self, source: str, val_to_add: int,
                               means_to_add: Tuple[float, float, float],
                               varis_to_add: Tuple[float, float, float]) -> Optional[LocationStat]:
        """
        :param source: the source name to update count, means, and std dev for
        :param val_to_add: the number of new points to add to the count
        :param means_to_add: the means of the location to add
        :param varis_to_add: the variances of the location to add
        :return: the updated LocationStat with the same source name as the input, or None if the source doesn't exist
        """
        for n in self._location_stats:
            if n.source_name == source:
                n.variance = (self._update_variances(n.count, n.variance[0], n.means[0],
                                                     val_to_add, varis_to_add[0], means_to_add[0]),
                              self._update_variances(n.count, n.variance[1], n.means[1],
                                                     val_to_add, varis_to_add[1], means_to_add[1]),
                              self._update_variances(n.count, n.variance[2], n.means[2],
                                                     val_to_add, varis_to_add[2], means_to_add[2]))
                n.std_dev = np.sqrt(n.variance)
                self.add_means_by_source(source, val_to_add, means_to_add)
                return n
        return None

    def add_std_dev_by_source(self, source: str, val_to_add: int,
                              means_to_add: Tuple[float, float, float],
                              stds_to_add: Tuple[float, float, float]) -> Optional[LocationStat]:
        """
        :param source: the source name to update count, means, and std dev for
        :param val_to_add: the number of new points to add to the count
        :param means_to_add: the means of the location to add
        :param stds_to_add: the std devs of the location to add
        :return: the updated LocationStat with the same source name as the input, or None if the source doesn't exist
        """
        for n in self._location_stats:
            if n.source_name == source:
                n.variance = (self._update_variances(n.count, n.variance[0], n.means[0],
                                                     val_to_add, stds_to_add[0]*stds_to_add[0], means_to_add[0]),
                              self._update_variances(n.count, n.variance[1], n.means[1],
                                                     val_to_add, stds_to_add[1]*stds_to_add[1], means_to_add[1]),
                              self._update_variances(n.count, n.variance[2], n.means[2],
                                                     val_to_add, stds_to_add[2]*stds_to_add[2], means_to_add[2]))
                n.std_dev = np.sqrt(n.variance)
                self.add_means_by_source(source, val_to_add, means_to_add)
                return n
        return None


class CircularQueue:
    def __init__(self, capacity: int, debug: bool = False):
        self.capacity: int = capacity
        self.data: List = [None] * capacity
        self.head: int = 0
        self.tail: int = -1
        self.size: int = 0
        self.debug: bool = debug

    def _update_index(self, index: int):
        return (index + 1) % self.capacity

    def is_full(self) -> bool:
        return self.size == self.capacity

    def is_empty(self) -> bool:
        return self.size == 0

    def add(self, data: any, limit_size: bool = False):
        """
        adds data to the buffer.  Overwrites values unless limit_size is True

        :param data: data to add
        :param limit_size: if True, will not overwrite data if the buffer is full
        """
        if limit_size and self.is_full():
            if self.debug:
                print("Cannot add to full buffer.")
        else:
            self.tail = self._update_index(self.tail)
            self.data[self.tail] = data
            self.size = np.minimum(self.size + 1, self.capacity)

    def remove(self) -> any:
        if self.is_empty():
            if self.debug:
                print("Cannot remove from empty buffer.")
            return None
        result = self.data[self.head]
        self.head = self._update_index(self.head)
        self.size -= 1
        return result

    def peek(self) -> any:
        if self.is_empty():
            if self.debug:
                print("Cannot look at empty buffer.")
            return None
        return self.data[self.head]

    def peek_tail(self) -> any:
        if self.is_empty():
            if self.debug:
                print("Cannot look at empty buffer.")
            return None
        return self.data[self.tail]

    def peek_index(self, index: int) -> any:
        """
        converts index to be within the buffer's capacity

        :param index: index to look at
        :return: element at index
        """
        if self.is_empty():
            if self.debug:
                print("Cannot look at empty buffer.")
            return None
        return self.data[index % self.capacity]

    def look_at_data(self) -> List:
        if self.is_empty():
            if self.debug:
                print("Buffer is empty.")
            return []
        index = self.head
        result = []
        for i in range(self.size):
            result.append(self.data[index])
            index = self._update_index(index)
        return result


class SessionModel:
    """
    SessionModel is designed to summarize an operational period of a station
    Timestamps are in microseconds since epoch UTC
    Latitude and Longitude are in degrees
    Altitude is in meters
    Sample rates are in hz
    Latency and offset are in microseconds
    Packet duration is in seconds

    Protected:
        _id: str, id of the station.  Default ""

        _uuid: str, uuid of the station.  Default ""

        _start_date: float, Timestamp since epoch UTC of when station was started.  Default np.nan

        _sensors: Dict[str, float], The name of sensors and their mean sample rate as a dictionary.

        _errors: RedVoxExceptions, Contains any errors found when creating the model

        _sdk_version: str, the version of the SDK used to create the model

    Properties:
        app: str, Name of the app the station is running.  Default ""

        api: float, Version number of the API the station is using.  Default np.nan

        sub_api: float, Version number of the sub-API the station in using.  Default np.nan

        make: str, Make of the station.  Default ""

        model: str, Model of the station.  Default ""

        app_version: str, Version of the app the station is running.  Default ""

        packet_duration_s: float, Length of station's data packets in seconds.  Default np.nan

        station_description: str, Text description of the station.  Default ""

        num_packets: int, Number of files used to create the model.  Default 0

        first_data_timestamp: float, Timestamp of the first data point.  Default np.nan

        last_data_timestamp: float, Timestamp of the last data point.  Default np.nan

        has_moved: bool, If True, location changed during station operation.  Default False

        location_stats: LocationStats, Container for number of times a location source has appeared, the mean of
        the data points, and the std deviation of the data points.  Default empty

        best_latency: float, the best latency of the model.  Default np.nan

        num_timesync_points: int, the number of timesync data points.  Default 0

        mean_latency: float, mean latency of the model.  Default np.nan

        mean_offset: float, mean offset of the model.  Default np.nan

        first_timesync_data: CircularQueue, container for the first 15 points of timesync data;
        timestamp, latency, offset.  Default empty

        last_timesync_data: CircularQueue, container for the last 15 points of timesync data.  Default empty

        num_gps_points: int, the number of gps data points.  Default 0

        first_gps_data: CircularQueue, container for the first 15 points of GPS offset data; timestamp and offset.
        Default empty

        last_gps_data: CircularQueue, container for the last 15 points of GPS offset data.  Default empty
    """
    def __init__(self,
                 station_id: str = "",
                 uuid: str = "",
                 start_timestamp: float = np.nan,
                 api: float = np.nan,
                 sub_api: float = np.nan,
                 make: str = "",
                 model: str = "",
                 app_version: str = "",
                 packet_duration_s: float = np.nan,
                 station_description: str = "",
                 created_from_packet: bool = False,
                 first_data_timestamp: float = np.nan,
                 last_data_timestamp: float = np.nan,
                 location_stats: Optional[LocationStats] = None,
                 best_latency: float = np.nan,
                 num_timesync_points: int = 0,
                 num_gps_points: int = 0
                 ):
        """
        Initialize a SessionModel.  Does not include sensor statistics.  Use function create_from_packet() if you
        already have a packet to read from to get a complete model from the packet.

        :param station_id: id of the station, default ""
        :param uuid: uuid of the station, default ""
        :param start_timestamp: timestamp from epoch UTC when station was started, default np.nan
        :param api: api version of data, default np.nan
        :param sub_api: sub-api version of data, default np.nan
        :param make: make of station, default ""
        :param model: model of station, default ""
        :param app_version: version of the app on station, default ""
        :param packet_duration_s: duration of data packets in seconds, default np.nan
        :param station_description: station description, default ""
        :param created_from_packet: if True, the rest of the values came from a packet and sets num_packets to 1.
                                    Default False
        :param first_data_timestamp: first timestamp from epoch UTC of the data, default np.nan
        :param last_data_timestamp: last timestamp from epoch UTC of the data, default np.nan
        :param location_stats: Optional LocationStats (source names and the count, mean and std deviation of
                                each type of location), default None
        :param best_latency: best latency of the station model, default np.nan
        :param num_timesync_points: number of timesync data points, default 0
        :param num_gps_points: number of gps data points, default 0
        """
        self._session_version: str = SESSION_VERSION
        self._id: str = station_id
        self._uuid: str = uuid
        self._start_date: float = start_timestamp
        self.app: str = "Redvox"
        self.api: float = api
        self.sub_api: float = sub_api
        self.make: str = make
        self.model: str = model
        self.app_version: str = app_version
        self.packet_duration_s: float = packet_duration_s
        self.station_description: str = station_description
        self.num_packets: int = 1 if created_from_packet else 0
        self.first_data_timestamp: float = first_data_timestamp
        self.last_data_timestamp: float = last_data_timestamp
        self.has_moved: bool = False
        self.location_stats: LocationStats = LocationStats() if location_stats is None else location_stats
        self.best_latency: float = best_latency
        self.num_timesync_points: int = num_timesync_points
        self.mean_latency: float = np.nan
        self.mean_offset: float = np.nan
        self.first_timesync_data: CircularQueue = CircularQueue(NUM_BUFFER_POINTS)
        self.last_timesync_data: CircularQueue = CircularQueue(NUM_BUFFER_POINTS)
        self.num_gps_points: int = num_gps_points
        self.first_gps_data: CircularQueue = CircularQueue(NUM_BUFFER_POINTS)
        self.last_gps_data: CircularQueue = CircularQueue(NUM_BUFFER_POINTS)
        self._errors: RedVoxExceptions = RedVoxExceptions("SessionModel")
        self._sdk_version: str = redvox.version()
        self._sensors: Dict[str, float] = {}

    def __repr__(self):
        return f"session_version: {self._session_version}, " \
               f"id: {self._id}, " \
               f"uuid: {self._uuid}, " \
               f"start_date: {self._start_date}, " \
               f"app: {self.app}, " \
               f"api: {self.api}, " \
               f"sub_api: {self.sub_api}, " \
               f"make: {self.make}, " \
               f"model: {self.model}, " \
               f"app_version: {self.app_version}, " \
               f"packet_duration_s: {self.packet_duration_s}, " \
               f"station_description: {self.station_description}, " \
               f"num_packets: {self.num_packets}, " \
               f"first_data_timestamp: {self.first_data_timestamp}, " \
               f"last_data_timestamp: {self.last_data_timestamp}, " \
               f"location_stats: {self.location_stats}, " \
               f"has_moved: {self.has_moved}, " \
               f"best_latency: {self.best_latency}, " \
               f"mean_latency: {self.mean_latency}, " \
               f"mean_offset: {self.mean_offset}, " \
               f"sdk_version: {self._sdk_version}, " \
               f"sensors: {self._sensors}"

    def __str__(self):
        s_d = np.nan if np.isnan(self._start_date) \
            else datetime_from_epoch_microseconds_utc(self._start_date).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        first_timestamp = np.nan if np.isnan(self.first_data_timestamp) \
            else datetime_from_epoch_microseconds_utc(self.first_data_timestamp).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        last_timestamp = np.nan if np.isnan(self.last_data_timestamp) \
            else datetime_from_epoch_microseconds_utc(self.last_data_timestamp).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return f"session_version: {self._session_version}, " \
               f"id: {self._id}, " \
               f"uuid: {self._uuid}, " \
               f"start_date: {s_d}, " \
               f"app: {self.app}, " \
               f"api: {self.api}, " \
               f"sub_api: {self.sub_api}, " \
               f"make: {self.make}, " \
               f"model: {self.model}, " \
               f"app_version: {self.app_version}, " \
               f"packet_duration_s: {self.packet_duration_s}, " \
               f"station_description: {self.station_description}, " \
               f"num_packets: {self.num_packets}, " \
               f"first_data_timestamp: {first_timestamp}, " \
               f"last_data_timestamp: {last_timestamp}, " \
               f"location_stats: {self.location_stats}, " \
               f"has_moved: {self.has_moved}, " \
               f"best_latency: {self.best_latency}, " \
               f"mean_latency: {self.mean_latency}, " \
               f"mean_offset: {self.mean_offset}, " \
               f"audio_sample_rate_hz: {self.audio_sample_rate_nominal_hz()}, " \
               f"sdk_version: {self._sdk_version}, " \
               f"sensors and sample rate (hz): {self._sensors}"

    def id(self) -> str:
        """
        :return: the id of the SessionModel
        """
        return self._id

    def uuid(self) -> str:
        """
        :return: the uuid of the SessionModel
        """
        return self._uuid

    def start_date(self) -> float:
        """
        :return: the start_date of the SessionModel
        """
        return self._start_date

    def print_errors(self):
        """
        Prints all errors in the SessionModel to screen
        """
        self._errors.print()

    def audio_sample_rate_nominal_hz(self) -> float:
        """
        :return: the nominal audio sample rate in hz
        """
        return self._sensors["audio"] if "audio" in self._sensors.keys() else np.nan

    def _get_sensor_data_from_packet(self, sensor: str, packet: api_m.RedvoxPacketM) -> float:
        """
        :param: sensor: the sensor to get data for
        :param: packet: the packet to get data from
        :return: mean sample rate from packet for a sensor
        """
        if sensor == "health":
            v = packet.station_information.station_metrics.timestamps.mean_sample_rate
        elif _has_sensor(packet, sensor):
            if sensor == _ACCELEROMETER_FIELD_NAME:
                v = packet.sensors.accelerometer.timestamps.mean_sample_rate
            elif sensor == _AMBIENT_TEMPERATURE_FIELD_NAME:
                v = packet.sensors.ambient_temperature.timestamps.mean_sample_rate
            elif sensor == _AUDIO_FIELD_NAME:
                return packet.sensors.audio.sample_rate
            elif sensor == _COMPRESSED_AUDIO_FIELD_NAME:
                return packet.sensors.compressed_audio.sample_rate
            elif sensor == _GRAVITY_FIELD_NAME:
                v = packet.sensors.gravity.timestamps.mean_sample_rate
            elif sensor == _GYROSCOPE_FIELD_NAME:
                v = packet.sensors.gyroscope.timestamps.mean_sample_rate
            elif sensor == _IMAGE_FIELD_NAME:
                v = packet.sensors.image.timestamps.mean_sample_rate
            elif sensor == _LIGHT_FIELD_NAME:
                v = packet.sensors.light.timestamps.mean_sample_rate
            elif sensor == _LINEAR_ACCELERATION_FIELD_NAME:
                v = packet.sensors.linear_acceleration.timestamps.mean_sample_rate
            elif sensor == _LOCATION_FIELD_NAME:
                v = packet.sensors.location.timestamps.mean_sample_rate
                num_locs = int(packet.sensors.location.timestamps.timestamp_statistics.count)
                gps_offsets = []
                gps_timestamps = []
                if num_locs > 0:
                    has_lats = packet.sensors.location.HasField("latitude_samples")
                    has_lons = packet.sensors.location.HasField("longitude_samples")
                    has_alts = packet.sensors.location.HasField("altitude_samples")
                    gps_offsets = list(np.array(packet.sensors.location.timestamps_gps.timestamps)
                                       - np.array(packet.sensors.location.timestamps.timestamps) + GPS_TRAVEL_MICROS)
                    gps_timestamps = packet.sensors.location.timestamps_gps.timestamps
                    if len(packet.sensors.location.location_providers) < 1:
                        mean_loc = (packet.sensors.location.latitude_samples.value_statistics.mean,
                                    packet.sensors.location.longitude_samples.value_statistics.mean,
                                    packet.sensors.location.altitude_samples.value_statistics.mean)
                        std_loc = (packet.sensors.location.latitude_samples.value_statistics.standard_deviation,
                                   packet.sensors.location.longitude_samples.value_statistics.standard_deviation,
                                   packet.sensors.location.altitude_samples.value_statistics.standard_deviation)
                        if self.location_stats.has_source("UNKNOWN"):
                            self.location_stats.add_std_dev_by_source("UNKNOWN", num_locs, mean_loc, std_loc)
                        else:
                            self.location_stats.add_loc_stat(LocationStat("UNKNOWN", num_locs, mean_loc, None, std_loc))
                    else:
                        data_array = {}
                        for n in range(num_locs):
                            lp = COLUMN_TO_ENUM_FN["location_provider"](
                                packet.sensors.location.location_providers[
                                    0 if num_locs != len(packet.sensors.location.location_providers) else n])
                            if lp not in data_array.keys():
                                data_array[lp] = ([packet.sensors.location.latitude_samples.values[n]
                                                   if has_lats else np.nan],
                                                  [packet.sensors.location.longitude_samples.values[n]
                                                   if has_lons else np.nan],
                                                  [packet.sensors.location.altitude_samples.values[n]
                                                   if has_alts else np.nan])
                            else:
                                data_array[lp][0].append(packet.sensors.location.latitude_samples.values[n]
                                                         if has_lats else np.nan)
                                data_array[lp][1].append(packet.sensors.location.longitude_samples.values[n]
                                                         if has_lons else np.nan)
                                data_array[lp][2].append(packet.sensors.location.altitude_samples.values[n]
                                                         if has_alts else np.nan)
                        for k, d in data_array.items():
                            if self.location_stats.has_source(k):
                                self.location_stats.add_variance_by_source(
                                    k, len(d[0]), (np.mean(d[0]), np.mean(d[1]), np.mean(d[2])),
                                    (np.var(d[0]), np.var(d[1]), np.var(d[2]))
                                )
                            else:
                                self.location_stats.add_loc_stat(
                                    LocationStat(k, len(d[0]), (np.mean(d[0]), np.mean(d[1]), np.mean(d[2])),
                                                 (np.var(d[0]), np.var(d[1]), np.var(d[2])))
                                )
                elif packet.sensors.location.last_best_location is not None:
                    gps_offsets = [packet.sensors.location.last_best_location.latitude_longitude_timestamp.gps
                                   - packet.sensors.location.last_best_location.latitude_longitude_timestamp.mach
                                   + GPS_TRAVEL_MICROS]
                    gps_timestamps = [packet.sensors.location.last_best_location.latitude_longitude_timestamp.gps]
                    mean_loc = (packet.sensors.location.last_best_location.latitude,
                                packet.sensors.location.last_best_location.longitude,
                                packet.sensors.location.last_best_location.altitude)
                    only_prov = COLUMN_TO_ENUM_FN["location_provider"](
                        packet.sensors.location.last_best_location.location_provider)
                    std_loc = (0., 0., 0.)
                    if self.location_stats.has_source(only_prov):
                        self.location_stats.add_std_dev_by_source(only_prov, 1, mean_loc, std_loc)
                    else:
                        self.location_stats.add_loc_stat(LocationStat(only_prov, 1, mean_loc, None, std_loc))
                if len(gps_offsets) > 0 and len(gps_timestamps) > 0:
                    valid_data_points = [i for i in range(len(gps_offsets))
                                         if gps_offsets[i] < GPS_TRAVEL_MICROS - GPS_VALIDITY_BUFFER
                                         or gps_offsets[i] > GPS_TRAVEL_MICROS + GPS_VALIDITY_BUFFER]
                    if len(valid_data_points) > 0:
                        valid_data = [(gps_timestamps[i], gps_offsets[i]) for i in valid_data_points]
                        if self.first_gps_data.is_full():
                            for i in valid_data:
                                self.last_gps_data.add(i)
                        else:
                            for i in valid_data:
                                self.first_gps_data.add(i, True)
                    self.num_gps_points += len(valid_data_points)
                if not self.has_moved:
                    for lc in self.location_stats.get_all_stats():
                        if lc.std_dev[0] > MOVEMENT_METERS * DEGREES_TO_METERS \
                                or lc.std_dev[1] > MOVEMENT_METERS * DEGREES_TO_METERS \
                                or lc.std_dev[2] > MOVEMENT_METERS:
                            self.has_moved = True
            elif sensor == _MAGNETOMETER_FIELD_NAME:
                v = packet.sensors.magnetometer.timestamps.mean_sample_rate
            elif sensor == _ORIENTATION_FIELD_NAME:
                v = packet.sensors.orientation.timestamps.mean_sample_rate
            elif sensor == _PRESSURE_FIELD_NAME:
                v = packet.sensors.pressure.timestamps.mean_sample_rate
            elif sensor == _PROXIMITY_FIELD_NAME:
                v = packet.sensors.proximity.timestamps.mean_sample_rate
            elif sensor == _RELATIVE_HUMIDITY_FIELD_NAME:
                v = packet.sensors.relative_humidity.timestamps.mean_sample_rate
            elif sensor == _ROTATION_VECTOR_FIELD_NAME:
                v = packet.sensors.rotation_vector.timestamps.mean_sample_rate
            elif sensor == _VELOCITY_FIELD_NAME:
                v = packet.sensors.velocity.timestamps.mean_sample_rate
            else:
                return np.nan
        else:
            return np.nan
        return v / 1e-6  # convert microseconds to seconds so rate is in hz

    def get_data_from_packet(self, packet: api_m.RedvoxPacketM) -> "SessionModel":
        """
        loads data from a packet into the model.  stops reading data if there is an error

        :param packet: API M packet to add
        :return: the updated SessionModel
        """
        if packet.station_information.id == self._id:
            if packet.station_information.uuid == self._uuid:
                if packet.timing_information.app_start_mach_timestamp == self._start_date:
                    packet_start = packet.timing_information.packet_start_mach_timestamp
                    packet_end = packet.timing_information.packet_end_mach_timestamp
                    secret = TimeSync().from_raw_packets([packet])
                    if np.isnan(packet.timing_information.best_latency):
                        packet_best_latency = secret.best_latency()
                        packet_best_offset = secret.best_offset()
                    else:
                        packet_best_latency = packet.timing_information.best_latency
                        packet_best_offset = secret.best_offset() if np.isnan(packet.timing_information.best_offset) \
                            else packet.timing_information.best_offset
                    if secret.num_tri_messages() > 0:
                        self.num_timesync_points += secret.num_tri_messages()
                        self.mean_latency = \
                            (self.mean_latency * self.num_packets + packet_best_latency) / (self.num_packets + 1)
                        self.mean_offset = \
                            (self.mean_offset * self.num_packets + packet_best_offset) / (self.num_packets + 1)
                        _secret_offsets = secret.offsets().flatten()
                        _secret_timestamps = secret.get_device_exchanges_timestamps()
                        _secret_latencies = secret.latencies().flatten()
                        if self.first_timesync_data.is_full():
                            for i in range(len(_secret_timestamps)):
                                self.last_timesync_data.add((_secret_timestamps[i], _secret_latencies[i],
                                                             _secret_offsets[i]))
                        else:
                            for i in range(len(_secret_timestamps)):
                                self.first_timesync_data.add((_secret_timestamps[i], _secret_latencies[i],
                                                              _secret_offsets[i]), True)
                    sensors = get_all_sensors_in_packet(packet)
                    sensors.append("health")
                    if list(self._sensors.keys()) != sensors:
                        self._errors.append(f"packet sensors {sensors} does not match.")
                    else:
                        self.num_packets += 1
                        if packet_start < self.first_data_timestamp:
                            self.first_data_timestamp = packet_start
                        if packet_end > self.last_data_timestamp:
                            self.last_data_timestamp = packet_end
                        for s in sensors:
                            if s not in ["audio", "compressed_audio", "health", "image"]:
                                self._sensors[s] += \
                                    (self._get_sensor_data_from_packet(s, packet) - self._sensors[s]) / self.num_packets
                else:
                    self._errors.append(f"packet start date {packet.timing_information.app_start_mach_timestamp} "
                                        f"does not match.")
            else:
                self._errors.append(f"packet uuid {packet.station_information.uuid} does not match.")
        else:
            self._errors.append(f"packet id {packet.station_information.id} does not match.")
        return self

    def set_sensor_data(self, packet: api_m.RedvoxPacketM):
        """
        set the sensor information of a SessionModel from a single packet
        CAUTION: Overwrites any existing data

        :param packet: API M packet of data to read
        """
        sensors = get_all_sensors_in_packet(packet)
        sensors.append("health")
        for s in sensors:
            self._sensors[s] = self._get_sensor_data_from_packet(s, packet)

    @staticmethod
    def create_from_packet(packet: api_m.RedvoxPacketM) -> "SessionModel":
        """
        create a SessionModel from a single packet

        :param packet: API M packet of data to read
        :return: SessionModel using the data from the packet
        """
        try:
            result = SessionModel(packet.station_information.id, packet.station_information.uuid,
                                  packet.timing_information.app_start_mach_timestamp, packet.api, packet.sub_api,
                                  packet.station_information.make, packet.station_information.model,
                                  packet.station_information.app_version,
                                  len(packet.sensors.audio.samples.values) / packet.sensors.audio.sample_rate,
                                  packet.station_information.description,
                                  )
            result.get_data_from_packet(packet)
        except Exception as e:
            # result = SessionModel(station_description=f"FAILED: {e}")
            raise e
        return result

    def stream_data(self, data_stream: List[api_m.RedvoxPacketM]) -> "SessionModel":
        """
        Read data from a stream into the SessionModel

        :param data_stream: series of files from a single station to read
        :return: updated model
        """
        for p in data_stream:
            self.get_data_from_packet(p)
        return self

    @staticmethod
    def create_from_stream(data_stream: List[api_m.RedvoxPacketM]) -> "SessionModel":
        """
        create a SessionModel from a single stream of data

        :param data_stream: series of API M files from a single station to read
        :return: SessionModel using the data from the stream
        """
        p1 = data_stream.pop(0)
        model = SessionModel.create_from_packet(p1)
        for p in data_stream:
            model.get_data_from_packet(p)
        data_stream.insert(0, p1)
        return model

    def num_sensors(self) -> int:
        """
        :return: number of sensors in the Station
        """
        return len(self._sensors.keys())

    def list_of_sensors(self) -> List[str]:
        """
        :return: list of sensor names as strings
        """
        return list(self._sensors.keys())

    def get_sensor_data(self, sensor: str) -> Optional[float]:
        """
        Returns the data associated with a sensor or None if the data doesn't exist.
        Currently returns the mean sample rate of the sensor

        :param sensor: sensor to get data for
        :return: sensor data or None
        """
        if sensor in self._sensors.keys():
            return self._sensors[sensor]
        return None

    def model_duration(self) -> float:
        """
        :return: duration of model in microseconds
        """
        return self.last_data_timestamp - self.first_data_timestamp

    def first_latency_timestamp(self) -> float:
        """
        :return: first latency timestamp of the data or np.nan if it doesn't exist
        """
        if self.first_timesync_data.size > 0:
            return self.first_timesync_data.peek()[0]
        return np.nan

    def last_latency_timestamp(self) -> float:
        """
        :return: last latency timestamp of the data or np.nan if it doesn't exist
        """
        if self.last_timesync_data.size > 0:
            return self.last_timesync_data.peek_tail()[0]
        return np.nan

    def get_offset_model(self) -> OffsetModel:
        """
        note: this uses a set of the first and last data points to approximate the timesync offset model over time.
        For an in-depth analysis, use the entire timesync data set.

        :return: estimated timesync offset model using first and last segments of timesync data
        """
        if self.first_timesync_data.size + self.last_timesync_data.size > 0:
            first_data = self.first_timesync_data.look_at_data()
            last_data = self.last_timesync_data.look_at_data()
            timestamps = np.concatenate([np.array([first_data[i][0] for i in range(len(first_data))]),
                                         np.array([last_data[i][0] for i in range(len(last_data))]),
                                         np.array([self.first_data_timestamp + (self.model_duration() / 2)])])
            latencies = np.concatenate([np.array([first_data[i][1] for i in range(len(first_data))]),
                                        np.array([last_data[i][1] for i in range(len(last_data))]),
                                        np.array([self.mean_latency])])
            offsets = np.concatenate([np.array([first_data[i][2] for i in range(len(first_data))]),
                                      np.array([last_data[i][2] for i in range(len(last_data))]),
                                      np.array([self.mean_offset])])
            return OffsetModel(latencies, offsets, timestamps, self.first_latency_timestamp(),
                               self.last_latency_timestamp(), min_samples_per_bin=1)
        return OffsetModel.empty_model()

    def get_gps_offset(self) -> Tuple[float, float]:
        """
        note: this uses a set of the first and last data points to approximate the gps offset model over time.
        For an in-depth analysis, use the entire GPS data set.

        :return: estimated gps offset model slope and intercept
        """
        if self.first_gps_data.size + self.last_gps_data.size > 0:
            first_data = self.first_gps_data.look_at_data()
            last_data = self.last_gps_data.look_at_data()
            timestamps = np.concatenate([np.array([first_data[i][0] for i in range(len(first_data))]),
                                         np.array([last_data[i][0] for i in range(len(last_data))])])
            offsets = np.concatenate([np.array([first_data[i][1] for i in range(len(first_data))]),
                                      np.array([last_data[i][1] for i in range(len(last_data))])])
            return simple_offset_weighted_linear_regression(offsets, timestamps)
        return np.nan, np.nan
