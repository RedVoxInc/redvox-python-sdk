from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass

import numpy as np

import redvox
from redvox.common.errors import RedVoxExceptions
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc
from redvox.common.offset_model import OffsetModel, simple_offset_weighted_linear_regression
import redvox.api1000.proto.redvox_api_m_pb2 as api_m
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider


GPS_TRAVEL_MICROS = 60000  # Assumed GPS latency in microseconds

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


class StationModel:
    """
    Station Model designed to summarize the entirety of a station's operational period
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

        first_location: Tuple[float, float, float], Latitude, longitude, and altitude of first location.  Default None

        first_location_source: str, Name of source of first location values.  Default ""

        last_location: Tuple[float, float, float], Latitude, longitude, and altitude of last location.  Default None

        last_location_source: str, Name of source of last location values.  Default ""

        has_moved: bool, If True, location changed during station operation.  Default False

        location_stats: LocationStats, Container for number of times a location source has appeared, the mean of
        the data points, and the std deviation of the data points.  Default empty

        first_latency_timestamp: float, Timestamp of first latency.  Default np.nan

        first_latency: float, First latency of the model.  Default np.nan

        first_offset: float, First offset of the model.  Default np.nan

        last_latency_timestamp: float, Timestamp of last latency.  Default np.nan

        last_latency: float, Last latency of the model.  Default np.nan

        last_offset: float, Last offset of the model.  Default np.nan
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
                 first_location: Optional[Tuple[float, float, float]] = None,
                 first_location_source: str = "",
                 last_location: Optional[Tuple[float, float, float]] = None,
                 last_location_source: str = "",
                 location_stats: Optional[LocationStats] = None,
                 first_latency_timestamp: float = np.nan,
                 first_latency: float = np.nan,
                 first_offset: float = np.nan,
                 last_latency_timestamp: float = np.nan,
                 last_latency: float = np.nan,
                 last_offset: float = np.nan
                 ):
        """
        Initialize a Station Model.  Does not include sensor statistics.  Use function create_from_packet() if you
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
        :param first_location: Optional latitude, longitude and altitude of the first location, default None
        :param first_location_source: source of the first location data, default ""
        :param last_location: Optional latitude, longitude and altitude of the last location, default None
        :param last_location_source: source of the last location data, default ""
        :param location_stats: Optional LocationStats (source names and the count, mean and std deviation of
                                each type of location), default None
        :param first_latency_timestamp: timestamp of the first latency value, default np.nan
        :param first_latency: first latency of the model, default np.nan
        :param first_offset: first offset of the model, default np.nan
        :param last_latency_timestamp: timestamp of the last latency value, default np.nan
        :param last_latency: last latency of the model, default np.nan
        :param last_offset: last offset of the model, default np.nan
        """
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
        self.first_location: Optional[Tuple[float, float, float]] = first_location
        self.first_location_source: str = first_location_source
        self.last_location: Optional[Tuple[float, float, float]] = last_location
        self.last_location_source: str = last_location_source
        self.has_moved: bool = first_location != last_location
        self.location_stats: LocationStats = LocationStats() if location_stats is None else location_stats
        self.first_latency_timestamp: float = first_latency_timestamp
        self.first_latency: float = first_latency
        self.first_offset: float = first_offset
        self.last_latency_timestamp: float = last_latency_timestamp
        self.last_latency: float = last_latency
        self.last_offset: float = last_offset
        self._gps_offsets: list[float] = []
        self._gps_timestamps: list[float] = []
        self._errors: RedVoxExceptions = RedVoxExceptions("StationModel")
        self._sdk_version: str = redvox.version()
        self._sensors: Dict[str, float] = {}
        self._offset_model: OffsetModel = OffsetModel.empty_model()

    def __repr__(self):
        return f"id: {self._id}, " \
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
               f"first_location: {self.first_location}, " \
               f"first_location_source: {self.first_location_source}, " \
               f"last_location: {self.last_location}, " \
               f"last_location_source: {self.last_location_source}, " \
               f"location_stats: {self.location_stats}, " \
               f"has_moved: {self.has_moved}, " \
               f"first_latency_timestamp: {self.first_latency_timestamp}, " \
               f"first_latency: {self.first_latency}, " \
               f"first_offset: {self.first_offset}, " \
               f"last_latency_timestamp: {self.last_latency_timestamp}, " \
               f"last_latency: {self.last_latency}, " \
               f"last_offset: {self.last_offset}, " \
               f"sdk_version: {self._sdk_version}, " \
               f"sensors: {self._sensors}"

    def __str__(self):
        start_date = np.nan if np.isnan(self._start_date) \
            else datetime_from_epoch_microseconds_utc(self._start_date).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        first_timestamp = np.nan if np.isnan(self.first_data_timestamp) \
            else datetime_from_epoch_microseconds_utc(self.first_data_timestamp).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        last_timestamp = np.nan if np.isnan(self.last_data_timestamp) \
            else datetime_from_epoch_microseconds_utc(self.last_data_timestamp).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return f"id: {self._id}, " \
               f"uuid: {self._uuid}, " \
               f"start_date: {start_date}, " \
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
               f"first lat, lon, alt (m): {self.first_location_source}; {self.first_location}, " \
               f"last lat, lon, alt (m): {self.last_location_source}; {self.last_location}, " \
               f"location_stats: {self.location_stats}, " \
               f"has_moved: {self.has_moved}, " \
               f"first_latency_timestamp: {self.first_latency_timestamp}, " \
               f"first_latency: {self.first_latency}, " \
               f"first_offset: {self.first_offset}, " \
               f"last_latency_timestamp: {self.last_latency_timestamp}, " \
               f"last_latency: {self.last_latency}, " \
               f"last_offset: {self.last_offset}, " \
               f"audio_sample_rate_hz: {self.audio_sample_rate_nominal_hz()}, " \
               f"sdk_version: {self._sdk_version}, " \
               f"sensors and sample rate (hz): {self._sensors}"

    def id(self) -> str:
        """
        :return: the id of the StationModel
        """
        return self._id

    def uuid(self) -> str:
        """
        :return: the uuid of the StationModel
        """
        return self._uuid

    def start_date(self) -> float:
        """
        :return: the start_date of the StationModel
        """
        return self._start_date

    def print_errors(self):
        """
        Prints all errors in the StationModel to screen
        """
        self._errors.print()

    def audio_sample_rate_nominal_hz(self) -> float:
        """
        :return: the nominal audio sample rate in hz
        """
        return self._sensors["audio"] if "audio" in self._sensors.keys() else np.nan

    # @staticmethod
    # def _update_std_dev(num_old_samples: int, old_mean: float, old_std: float,
    #                     num_new_samples: int, new_mean: float, new_std: float) -> float:
    #     """
    #     converts old std dev to new std dev
    #
    #     :param num_old_samples: number of old samples
    #     :param old_mean: old mean
    #     :param old_std: old std dev
    #     :param num_new_samples: number of new samples
    #     :param new_mean: new mean
    #     :param new_std: new std dev
    #     :return: new std dev
    #     """
    #     if num_old_samples + num_new_samples == 1:
    #         return 0.
    #     return (((num_old_samples - 1) * old_std * old_std) + ((num_new_samples - 1) * new_std * new_std)
    #             + ((num_old_samples * num_new_samples / (num_old_samples + num_new_samples))
    #                * (old_mean * old_mean + new_mean * new_mean - (2 * new_mean * old_mean)))) / \
    #            (num_old_samples + num_new_samples - 1)

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
                if num_locs > 0:
                    has_lats = packet.sensors.location.HasField("latitude_samples")
                    has_lons = packet.sensors.location.HasField("longitude_samples")
                    has_alts = packet.sensors.location.HasField("altitude_samples")
                    gps_offsets = np.array(packet.sensors.location.timestamps_gps.timestamps) \
                        - np.array(packet.sensors.location.timestamps.timestamps) + GPS_TRAVEL_MICROS
                    if len(gps_offsets) > 0:
                        self._gps_offsets.extend(gps_offsets)
                        self._gps_timestamps.extend(packet.sensors.location.timestamps_gps.timestamps)
                    if self.first_location is None \
                            or self.first_data_timestamp > packet.sensors.location.timestamps.timestamps[0]:
                        self.first_location = (packet.sensors.location.latitude_samples.values[0]
                                               if has_lats else np.nan,
                                               packet.sensors.location.longitude_samples.values[0]
                                               if has_lons else np.nan,
                                               packet.sensors.location.altitude_samples.values[0]
                                               if has_alts else np.nan)
                    if self.last_location is None \
                            or self.last_data_timestamp < packet.sensors.location.timestamps.timestamps[-1]:
                        self.last_location = (packet.sensors.location.latitude_samples.values[-1]
                                              if has_lats else np.nan,
                                              packet.sensors.location.longitude_samples.values[-1]
                                              if has_lons else np.nan,
                                              packet.sensors.location.altitude_samples.values[-1]
                                              if has_alts else np.nan)
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
                        self.first_location_source = "UNKNOWN"
                        self.last_location_source = "UNKNOWN"
                    else:
                        self.first_location_source = \
                            COLUMN_TO_ENUM_FN["location_provider"](packet.sensors.location.location_providers[0])
                        self.last_location_source = \
                            COLUMN_TO_ENUM_FN["location_provider"](packet.sensors.location.location_providers[-1])
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
                if not self.has_moved:
                    self.has_moved = self.first_location != self.last_location
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

    def get_data_from_packet(self, packet: api_m.RedvoxPacketM) -> "StationModel":
        """
        loads data from a packet into the model.  stops reading data if there is an error

        :param packet: API M packet to add
        :return: the updated StationModel
        """
        if self.num_packets < 1:
            return self.create_from_packet(packet)
        if packet.station_information.id == self._id:
            if packet.station_information.uuid == self._uuid:
                if packet.timing_information.app_start_mach_timestamp == self._start_date:
                    packet_start = packet.timing_information.packet_start_mach_timestamp
                    packet_end = packet.timing_information.packet_end_mach_timestamp
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
                            self.last_latency_timestamp = packet_start
                            self.last_latency = packet.timing_information.best_latency
                            self.last_offset = packet.timing_information.best_offset
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
        set the sensor information of a StationModel from a single packet
        CAUTION: Overwrites any existing data

        :param packet: API M packet of data to read
        """
        sensors = get_all_sensors_in_packet(packet)
        sensors.append("health")
        for s in sensors:
            self._sensors[s] = self._get_sensor_data_from_packet(s, packet)

    @staticmethod
    def create_from_packet(packet: api_m.RedvoxPacketM) -> "StationModel":
        """
        create a StationModel from a single packet

        :param packet: API M packet of data to read
        :return: StationModel using the data from the packet
        """
        first_location = None
        first_loc_provider = ""
        last_location = None
        last_loc_provider = ""
        num_locs = int(packet.sensors.location.timestamps.timestamp_statistics.count)
        if _has_sensor(packet, _LOCATION_FIELD_NAME) and num_locs > 0:
            has_lats = packet.sensors.location.HasField("latitude_samples")
            has_lons = packet.sensors.location.HasField("longitude_samples")
            has_alts = packet.sensors.location.HasField("altitude_samples")
            if len(packet.sensors.location.location_providers) < 1:
                first_loc_provider = "UNKNOWN"
                last_loc_provider = "UNKNOWN"
            else:
                first_loc_provider = \
                    COLUMN_TO_ENUM_FN["location_provider"](packet.sensors.location.location_providers[0])
                last_loc_provider = \
                    COLUMN_TO_ENUM_FN["location_provider"](packet.sensors.location.location_providers[-1])

            first_location = (packet.sensors.location.latitude_samples.values[0] if has_lats else np.nan,
                              packet.sensors.location.longitude_samples.values[0] if has_lons else np.nan,
                              packet.sensors.location.altitude_samples.values[0] if has_alts else np.nan)

            last_location = (packet.sensors.location.latitude_samples.values[-1] if has_lats else np.nan,
                             packet.sensors.location.longitude_samples.values[-1] if has_lons else np.nan,
                             packet.sensors.location.altitude_samples.values[-1] if has_alts else np.nan)

        try:
            result = StationModel(packet.station_information.id, packet.station_information.uuid,
                                  packet.timing_information.app_start_mach_timestamp, packet.api, packet.sub_api,
                                  packet.station_information.make, packet.station_information.model,
                                  packet.station_information.app_version,
                                  len(packet.sensors.audio.samples.values) / packet.sensors.audio.sample_rate,
                                  packet.station_information.description, True,
                                  packet.timing_information.packet_start_mach_timestamp,
                                  packet.timing_information.packet_end_mach_timestamp,
                                  first_location, first_loc_provider, last_location, last_loc_provider, None,
                                  packet.timing_information.packet_start_mach_timestamp,
                                  packet.timing_information.best_latency,
                                  packet.timing_information.best_offset,
                                  packet.timing_information.packet_start_mach_timestamp,
                                  packet.timing_information.best_latency,
                                  packet.timing_information.best_offset,
                                  )
            result.set_sensor_data(packet)
        except Exception as e:
            # result = StationModel(station_description=f"FAILED: {e}")
            raise e
        return result

    def stream_data(self, data_stream: List[api_m.RedvoxPacketM]) -> "StationModel":
        """
        Read data from a stream into the StationModel

        :param data_stream: series of files from a single station to read
        :return: updated model
        """
        for p in data_stream:
            self.get_data_from_packet(p)
        return self

    @staticmethod
    def create_from_stream(data_stream: List[api_m.RedvoxPacketM]) -> "StationModel":
        """
        create a StationModel from a single stream of data

        :param data_stream: series of API M files from a single station to read
        :return: StationModel using the data from the stream
        """
        p1 = data_stream.pop(0)
        model = StationModel.create_from_packet(p1)
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

    def set_offset_model(self, model: OffsetModel):
        """
        set the offset model

        :param model: model to set
        """
        self._offset_model = model

    def get_offset_model(self) -> OffsetModel:
        """
        :return: the offset model of the station model
        """
        return self._offset_model

    def get_gps_offsets(self) -> List[float]:
        """
        :return: all gps offsets of the model
        """
        return self._gps_offsets

    def get_gps_timestamps(self) -> List[float]:
        """
        :return: all gps timestamps of the model
        """
        return self._gps_timestamps

    def get_mean_gps_offsets(self) -> float:
        """
        Uses only data points that are less than -1000 and greater than 1000 microseconds, due to forced correction
        in gps timestamps causing some values to be "out of sync" with the rest.

        :return: the mean gps offset or np.nan if it doesn't exist
        """
        valid_gps_points = []
        for g in self._gps_offsets:
            if g < -1000 + GPS_TRAVEL_MICROS or g > 1000 + GPS_TRAVEL_MICROS:
                valid_gps_points.append(g)
        if len(valid_gps_points) > 0:
            return np.mean(valid_gps_points)
        return np.nan

    def get_gps_offset_model(self) -> Tuple[float, float]:
        """
        :return: the slope and intercept of the GPS offset model
        """
        if len(self._gps_offsets) == 0:
            return np.nan, np.nan
        return simple_offset_weighted_linear_regression(np.array(self._gps_offsets),
                                                        np.array(self._gps_timestamps) - self.first_data_timestamp)
