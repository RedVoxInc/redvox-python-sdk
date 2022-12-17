import os.path
from typing import List, Dict, Optional, Tuple, Union, Callable
from pathlib import Path

import numpy as np

import redvox
import redvox.api1000.proto.redvox_api_m_pb2 as api_m
import redvox.common.session_io as s_io
from redvox.common.timesync import TimeSync
from redvox.common.errors import RedVoxExceptions
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
from redvox.common.session_model_utils import LocationStats, CircularQueue
from redvox.common.offset_model import OffsetModel, simple_offset_weighted_linear_regression


SESSION_VERSION = "2022-12-13"  # Version of the SessionModel
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
_HEALTH_FIELD_NAME: str = "health"


Sensor = Union[
    api_m.RedvoxPacketM.Sensors.Xyz,
    api_m.RedvoxPacketM.Sensors.Single,
    api_m.RedvoxPacketM.Sensors.Audio,
    api_m.RedvoxPacketM.Sensors.Image,
    api_m.RedvoxPacketM.Sensors.Location,
    api_m.RedvoxPacketM.Sensors.CompressedAudio,
    api_m.RedvoxPacketM.StationInformation.StationMetrics
]

__SENSOR_NAME_TO_SENSOR_FN: Dict[
    str,
    Optional[
        Callable[
            [api_m.RedvoxPacketM],
            Union[Sensor],
        ]
    ],
] = {
    "unknown": None,
    _HEALTH_FIELD_NAME: lambda packet: packet.station_information.station_metrics,
    _ACCELEROMETER_FIELD_NAME: lambda packet: packet.sensors.accelerometer,
    _AMBIENT_TEMPERATURE_FIELD_NAME: lambda packet: packet.sensors.ambient_temperature,
    _AUDIO_FIELD_NAME: lambda packet: packet.sensors.audio,
    _COMPRESSED_AUDIO_FIELD_NAME: lambda packet: packet.sensors.compressed_audio,
    _GRAVITY_FIELD_NAME: lambda packet: packet.sensors.gravity,
    _GYROSCOPE_FIELD_NAME: lambda packet: packet.sensors.gyroscope,
    _IMAGE_FIELD_NAME: lambda packet: packet.sensors.image,
    _LIGHT_FIELD_NAME: lambda packet: packet.sensors.light,
    _LINEAR_ACCELERATION_FIELD_NAME: lambda packet: packet.sensors.linear_acceleration,
    _LOCATION_FIELD_NAME: lambda packet: packet.sensors.location,
    _MAGNETOMETER_FIELD_NAME: lambda packet: packet.sensors.magnetometer,
    _ORIENTATION_FIELD_NAME: lambda packet: packet.sensors.orientation,
    _PRESSURE_FIELD_NAME: lambda packet: packet.sensors.pressure,
    _PROXIMITY_FIELD_NAME: lambda packet: packet.sensors.proximity,
    _RELATIVE_HUMIDITY_FIELD_NAME: lambda packet: packet.sensors.relative_humidity,
    _ROTATION_VECTOR_FIELD_NAME: lambda packet: packet.sensors.rotation_vector,
    _VELOCITY_FIELD_NAME: lambda packet: packet.sensors.velocity,
}


def _get_sensor_for_data_extraction(sensor_name: str, packet: api_m.RedvoxPacketM) -> Optional[Sensor]:
    """
    :param sensor_name: name of sensor to return
    :param packet: the data packet to get the sensor from
    :return: Sensor that matches the sensor_name or None if that Sensor doesn't exist
    """
    sensor_fn: Optional[
        Callable[[api_m.RedvoxPacketM], Sensor]
    ] = __SENSOR_NAME_TO_SENSOR_FN[sensor_name]
    if (sensor_name == _HEALTH_FIELD_NAME or _has_sensor(packet, sensor_name)) and sensor_fn is not None:
        return sensor_fn(packet)


def _get_mean_sample_rate_from_sensor(sensor: Sensor) -> Tuple[int, float]:
    """
    :param sensor: Sensor to get data from
    :return: number of samples and mean sample rate of the sensor; returns np.nan if sample rate doesn't exist
    """
    num_pts = int(sensor.timestamps.timestamp_statistics.count)
    if num_pts > 1:
        return num_pts, float(np.mean(np.diff(sensor.timestamps.timestamps)))
    return num_pts, np.nan


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
    for s in [_AUDIO_FIELD_NAME, _PRESSURE_FIELD_NAME, _LOCATION_FIELD_NAME, _ACCELEROMETER_FIELD_NAME,
              _AMBIENT_TEMPERATURE_FIELD_NAME, _COMPRESSED_AUDIO_FIELD_NAME, _GRAVITY_FIELD_NAME,
              _GYROSCOPE_FIELD_NAME, _IMAGE_FIELD_NAME, _LIGHT_FIELD_NAME, _LINEAR_ACCELERATION_FIELD_NAME,
              _MAGNETOMETER_FIELD_NAME, _ORIENTATION_FIELD_NAME, _PROXIMITY_FIELD_NAME,
              _RELATIVE_HUMIDITY_FIELD_NAME, _ROTATION_VECTOR_FIELD_NAME, _VELOCITY_FIELD_NAME]:
        if _has_sensor(packet, s):
            result.append(s)
    return result


class SessionModel:
    """
    SessionModel is designed to summarize an operational period of a station.  SessionModel can be sealed, which means
    no more data will be received for the model, and the properties of the SessionModel are valid and the best
    available.  WARNING: Only seal a SessionModel when you are certain the session being modeled is finished.

    Timestamps are in microseconds since epoch UTC

    Latitude and Longitude are in degrees

    Altitude is in meters

    Sample rates are in hz

    Latency and offset are in microseconds

    Packet duration is in seconds

    Timestamps are NEVER the corrected values; it is up to the user to apply any corrections derived from information
    presented by this class

    Protected:
        _session_version: str, the version of the SessionModel.

        _sensors: Dict[str, float], The name of sensors and their mean sample rate as a dictionary.

        _errors: RedVoxExceptions, Contains any errors found when creating the model.

        _sdk_version: str, the version of the SDK used to create the model.

    Properties:
        id: str, id of the station.  Default ""

        uuid: str, uuid of the station.  Default ""

        start_date: float, Timestamp since epoch UTC of when station was started.  Default np.nan

        app_name: str, Name of the app the station is running.  Default "Redvox"

        app_version: str, Version of the app the station is running.  Default ""

        api: float, Version number of the API the station is using.  Default np.nan

        sub_api: float, Version number of the sub-API the station in using.  Default np.nan

        make: str, Make of the station.  Default ""

        model: str, Model of the station.  Default ""

        station_description: str, Text description of the station.  Default ""

        packet_duration_s: float, Length of station's data packets in seconds.  Default np.nan

        num_packets: int, Number of files used to create the model.  Default 0

        first_data_timestamp: float, Timestamp of the first data point used to create the model.  Default np.nan

        last_data_timestamp: float, Timestamp of the last data point used to create the model.  Default np.nan

        has_moved: bool, If True, location changed during session.  Default False

        location_stats: LocationStats, Container for number of times a location source has appeared, the mean of
        the data points, and the std deviation of the data points.  Default empty

        best_latency: float, the best latency of the model.  Default np.nan

        num_timesync_points: int, the number of timesync data points.  Default 0

        mean_latency: float, mean latency of the model.  Default np.nan

        mean_offset: float, mean offset of the model.  Default np.nan

        _first_timesync_data: CircularQueue, container for the first 15 points of timesync data;
        timestamp, latency, offset.  Default empty

        _last_timesync_data: CircularQueue, container for the last 15 points of timesync data.  Default empty

        num_gps_points: int, the number of gps data points.  Default 0

        gps_offset: optional tuple of float, the slope and intercept (in that order) of the gps timing calculations.
        Default None

        _first_gps_data: CircularQueue, container for the first 15 points of GPS offset data; timestamp and offset.
        Default empty

        _last_gps_data: CircularQueue, container for the last 15 points of GPS offset data.  Default empty

        is_sealed: bool, if True, the SessionModel will not accept any more data.  This means the offset model and gps
        offset values are the best they can be, given the available data.  Default False
    """
    def __init__(self,
                 station_id: str = "",
                 uuid: str = "",
                 start_timestamp: float = np.nan,
                 api: float = np.nan,
                 sub_api: float = np.nan,
                 make: str = "",
                 model: str = "",
                 station_description: str = "",
                 app_name: str = "Redvox",
                 sensors: Optional[Dict] = None
                 ):
        """
        Initialize a SessionModel with non-sensor related metadata.  This function uses only the most basic information
        to create the SessionModel; use these other functions if you already have some form of data to read:

        Use function create_from_packet() instead of this if you already have a packet to read from.

        Use function create_from_stream() instead of this if you already have several packets to read from.

        Use function load() instead of this if you already have a session_model.json to read from.

        Lastly, if you create a SessionModel using init, you can only add to the model by using the function
        add_data_from_packet() if you have a single packet or add_data_from_stream() if you have a stream of packets.

        :param station_id: id of the station, default ""
        :param uuid: uuid of the station, default ""
        :param start_timestamp: timestamp from epoch UTC when station was started, default np.nan
        :param api: api version of data, default np.nan
        :param sub_api: sub-api version of data, default np.nan
        :param make: make of station, default ""
        :param model: model of station, default ""
        :param station_description: station description, default ""
        :param app_name: name of the app on station, default "Redvox"
        :param sensors: Optional dictionary of sensor name and sample rate in hz, default None
        """
        self._session_version: str = SESSION_VERSION
        self.id: str = station_id
        self.uuid: str = uuid
        self.start_date: float = start_timestamp
        self.app_name: str = app_name
        self.app_version: str = ""
        self.api: float = api
        self.sub_api: float = sub_api
        self.make: str = make
        self.model: str = model
        self.station_description: str = station_description
        self.packet_duration_s: float = np.nan
        self.num_packets: int = 0
        self.first_data_timestamp: float = np.nan
        self.last_data_timestamp: float = np.nan
        self.location_stats: LocationStats = LocationStats()
        self.has_moved: bool = False
        self.num_timesync_points: int = 0
        self.mean_latency: float = 0.
        self.mean_offset: float = 0.
        self._first_timesync_data: CircularQueue = CircularQueue(NUM_BUFFER_POINTS)
        self._last_timesync_data: CircularQueue = CircularQueue(NUM_BUFFER_POINTS)
        self.offset_model: Optional[OffsetModel] = None
        self.num_gps_points: int = 0
        self._first_gps_data: CircularQueue = CircularQueue(NUM_BUFFER_POINTS)
        self._last_gps_data: CircularQueue = CircularQueue(NUM_BUFFER_POINTS)
        self.gps_offset: Optional[Tuple[float, float]] = None
        self._errors: RedVoxExceptions = RedVoxExceptions("SessionModel")
        self._sdk_version: str = redvox.version()
        self._sensors: Dict[str, float] = sensors if sensors is not None else {}
        self.is_sealed: bool = False

    def __repr__(self):
        if self.is_sealed:
            if self.offset_model is None:
                _ = self.get_offset_model()
            if self.gps_offset is None:
                _ = self.get_gps_offset()
            ts_section = f"offset_model: {self.offset_model}, "
            gps_section = f"gps_offset: {self.gps_offset}, "
        else:
            ts_section = f"first_timesync_data: {self._first_timesync_data}, " \
                         f"last_timesync_data: {self._last_timesync_data}, "
            gps_section = f"first_gps_data: {self._first_gps_data}, " \
                          f"last_gps_data: {self._last_gps_data}, "
        return f"session_version: {self._session_version}, " \
               f"id: {self.id}, " \
               f"uuid: {self.uuid}, " \
               f"start_date: {self.start_date}, " \
               f"app: {self.app_name}, " \
               f"app_version: {self.app_version}, " \
               f"api: {self.api}, " \
               f"sub_api: {self.sub_api}, " \
               f"make: {self.make}, " \
               f"model: {self.model}, " \
               f"packet_duration_s: {self.packet_duration_s}, " \
               f"station_description: {self.station_description}, " \
               f"num_packets: {self.num_packets}, " \
               f"first_data_timestamp: {self.first_data_timestamp}, " \
               f"last_data_timestamp: {self.last_data_timestamp}, " \
               f"num_timesync_points: {self.num_timesync_points}, " \
               f"mean_latency: {self.mean_latency}, " \
               f"mean_offset: {self.mean_offset}, " \
               f"{ts_section}" \
               f"location_stats: {self.location_stats.__repr__()}, " \
               f"has_moved: {self.has_moved}, " \
               f"num_gps_points: {self.num_gps_points}, " \
               f"{gps_section}" \
               f"sdk_version: {self._sdk_version}, " \
               f"sensors: {self._sensors}, " \
               f"is_sealed: {self.is_sealed}"

    def __str__(self):
        s_d = np.nan if np.isnan(self.start_date) \
            else datetime_from_epoch_microseconds_utc(self.start_date).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        first_timestamp = np.nan if np.isnan(self.first_data_timestamp) \
            else datetime_from_epoch_microseconds_utc(self.first_data_timestamp).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        last_timestamp = np.nan if np.isnan(self.last_data_timestamp) \
            else datetime_from_epoch_microseconds_utc(self.last_data_timestamp).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        if self.offset_model is None:
            _ = self.get_offset_model()
        if self.gps_offset is None:
            _ = self.get_gps_offset()
        return f"session_version: {self._session_version}, " \
               f"id: {self.id}, " \
               f"uuid: {self.uuid}, " \
               f"start_date: {s_d}, " \
               f"app: {self.app_name}, " \
               f"app_version: {self.app_version}, " \
               f"api: {self.api}, " \
               f"sub_api: {self.sub_api}, " \
               f"make: {self.make}, " \
               f"model: {self.model}, " \
               f"packet_duration_s: {self.packet_duration_s}, " \
               f"station_description: {self.station_description}, " \
               f"num_packets: {self.num_packets}, " \
               f"first_data_timestamp: {first_timestamp}, " \
               f"last_data_timestamp: {last_timestamp}, " \
               f"offset_model: {self.offset_model}, " \
               f"location_stats: {self.location_stats.__str__()}, " \
               f"has_moved: {self.has_moved}, " \
               f"num_gps_points: {self.num_gps_points}, " \
               f"gps_offset: {self.gps_offset}, " \
               f"audio_sample_rate_hz: {self.audio_sample_rate_nominal_hz()}, " \
               f"sdk_version: {self._sdk_version}, " \
               f"sensors and sample rate (hz): {self._sensors}, " \
               f"is_sealed: {self.is_sealed}"

    def as_dict(self) -> dict:
        """
        :return: SessionModel as a dictionary
        """
        result = {
            "session_version": self._session_version,
            "id": self.id,
            "uuid": self.uuid,
            "start_date": self.start_date,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "api": self.api,
            "sub_api": self.sub_api,
            "make": self.make,
            "model": self.model,
            "station_description": self.station_description,
            "packet_duration_s": self.packet_duration_s,
            "num_packets": self.num_packets,
            "first_data_timestamp": self.first_data_timestamp,
            "last_data_timestamp": self.last_data_timestamp,
            "location_stats": self.location_stats.as_dict(),
            "has_moved": self.has_moved,
            "num_timesync_points": self.num_timesync_points,
            "mean_latency": self.mean_latency,
            "mean_offset": self.mean_offset,
            "num_gps_points": self.num_gps_points,
            "errors": self._errors.as_dict(),
            "sdk_version": self._sdk_version,
            "sensors": self._sensors,
            "is_sealed": self.is_sealed
        }
        if self.is_sealed:
            result["gps_offset"] = self.gps_offset
            result["offset_model"] = self.offset_model.as_dict()
            result["first_timesync_data"] = self._first_timesync_data
            result["last_timesync_data"] = self._last_timesync_data
            result["first_gps_data"] = self._first_gps_data
            result["last_gps_data"] = self._last_gps_data
        else:
            result["first_timesync_data"] = self._first_timesync_data.as_dict()
            result["last_timesync_data"] = self._last_timesync_data.as_dict()
            result["first_gps_data"] = self._first_gps_data.as_dict()
            result["last_gps_data"] = self._last_gps_data.as_dict()
        return result

    def default_json_file_name(self) -> str:
        """
        :return: Default filename as [id]_[startdate], with startdate as integer of microseconds
                    since epoch UTC.  File extension NOT included.
        """
        return f"{self.id}_{0 if np.isnan(self.start_date) else int(self.start_date)}"

    @staticmethod
    def from_json_dict(json_dict: dict) -> "SessionModel":
        """
        Reads a JSON dictionary and recreates the SessionModel.
        If dictionary is improperly formatted, raises a ValueError.

        :param json_dict: the dictionary to read
        :return: SessionModel defined by the JSON
        """
        result = SessionModel(json_dict["id"], json_dict["uuid"], json_dict["start_date"],
                              json_dict["api"], json_dict["sub_api"], json_dict["make"], json_dict["model"],
                              json_dict["station_description"], json_dict["app_name"])

        result._session_version = json_dict["session_version"]
        result.app_version = json_dict["app_version"]
        result.packet_duration_s = json_dict["packet_duration_s"]
        result.num_packets = json_dict["num_packets"]
        result.first_data_timestamp = json_dict["first_data_timestamp"]
        result.last_data_timestamp = json_dict["last_data_timestamp"]
        result.location_stats = LocationStats.from_dict(json_dict["location_stats"])
        result.has_moved = json_dict["has_moved"]
        result.num_timesync_points = json_dict["num_timesync_points"]
        result.mean_latency = json_dict["mean_latency"]
        result.mean_offset = json_dict["mean_offset"]
        result.num_gps_points = json_dict["num_gps_points"]
        result._errors = RedVoxExceptions.from_dict(json_dict["errors"])
        result._sdk_version = json_dict["sdk_version"]
        result._sensors = json_dict["sensors"]
        result.is_sealed = json_dict["is_sealed"]
        if result.is_sealed:
            result._first_timesync_data = json_dict["first_timesync_data"]
            result._last_timesync_data = json_dict["last_timesync_data"]
            result._first_gps_data = json_dict["first_gps_data"]
            result._last_gps_data = json_dict["last_gps_data"]
        else:
            result._first_timesync_data = CircularQueue.from_dict(json_dict["first_timesync_data"])
            result._last_timesync_data = CircularQueue.from_dict(json_dict["last_timesync_data"])
            result._first_gps_data = CircularQueue.from_dict(json_dict["first_gps_data"])
            result._last_gps_data = CircularQueue.from_dict(json_dict["last_gps_data"])
        if "offset_model" in json_dict.keys():
            result.offset_model = OffsetModel.from_dict(json_dict["offset_model"])
        if "gps_offset" in json_dict.keys():
            result.gps_offset = json_dict["gps_offset"]

        return result

    def compress(self, out_dir: str = ".") -> Path:
        """
        Compresses this SessionModel to a file at out_dir.
        Uses the id and start_date to name the file.

        :param out_dir: Directory to save file to.  Default "." (current directory)
        :return: The path to the written file.
        """
        return s_io.compress_session_model(self, out_dir)

    def save(self, out_type: str = "json", out_dir: str = ".") -> Path:
        """
        Save the SessionModel to disk.  Options for out_type are "json" for JSON file and "pkl" for .pkl file.
        Defaults to "json".  File will be named after id and start_date of the SessionModel

        :param out_type: "json" for JSON file and "pkl" for .pkl file
        :param out_dir: Directory to save file to.  Default "." (current directory)
        :return: path to saved file
        """
        if out_type == "pkl":
            return self.compress(out_dir)
        return s_io.session_model_to_json_file(self, out_dir)

    @staticmethod
    def load(file_path: str) -> "SessionModel":
        """
        Load the SessionModel from a JSON or .pkl file.

        :param file_path: full name and path to the SessionModel file
        :return: SessionModel from file
        """
        ext = os.path.splitext(file_path)[1]
        if ext == ".json":
            return SessionModel.from_json_dict(s_io.session_model_dict_from_json_file(file_path))
        elif ext == ".pkl":
            return s_io.decompress_session_model(file_path)
        else:
            raise ValueError(f"{file_path} has unknown file extension; this function only accepts json and pkl files.")

    def print_errors(self):
        """
        Prints all errors in the SessionModel to screen
        """
        self._errors.print()

    def session_version(self) -> str:
        """
        :return: SessionModel version
        """
        return self._session_version

    def audio_sample_rate_nominal_hz(self) -> float:
        """
        :return: the nominal audio sample rate in hz
        """
        return self._sensors["audio"] if "audio" in self._sensors.keys() else np.nan

    def _get_sensor_data_from_packet(self, sensor: str, packet: api_m.RedvoxPacketM) -> float:
        """
        note: sets the sample rate to np.nan if no data is found

        :param: sensor: the sensor to get data for
        :param: packet: the packet to get data from
        :return: mean sample rate from packet for a sensor
        """
        if sensor == _AUDIO_FIELD_NAME:
            return packet.sensors.audio.sample_rate
        elif sensor == _COMPRESSED_AUDIO_FIELD_NAME:
            return packet.sensors.compressed_audio.sample_rate
        else:
            snsr = _get_sensor_for_data_extraction(sensor, packet)
            if snsr is not None:
                num_pts, mean_sr = _get_mean_sample_rate_from_sensor(snsr)
            else:
                return np.nan
        if sensor == _LOCATION_FIELD_NAME:
            # get all the location data
            gps_offsets = []
            gps_timestamps = []
            # check if there is data to read
            if num_pts > 0:
                has_lats = packet.sensors.location.HasField("latitude_samples")
                has_lons = packet.sensors.location.HasField("longitude_samples")
                has_alts = packet.sensors.location.HasField("altitude_samples")
                gps_offsets = list(np.array(packet.sensors.location.timestamps_gps.timestamps)
                                   - np.array(packet.sensors.location.timestamps.timestamps) + GPS_TRAVEL_MICROS)
                gps_timestamps = packet.sensors.location.timestamps_gps.timestamps
                # make sure we have provider data; no providers means using default UNKNOWN provider
                if len(packet.sensors.location.location_providers) < 1:
                    mean_loc = (packet.sensors.location.latitude_samples.value_statistics.mean,
                                packet.sensors.location.longitude_samples.value_statistics.mean,
                                packet.sensors.location.altitude_samples.value_statistics.mean)
                    std_loc = (packet.sensors.location.latitude_samples.value_statistics.standard_deviation,
                               packet.sensors.location.longitude_samples.value_statistics.standard_deviation,
                               packet.sensors.location.altitude_samples.value_statistics.standard_deviation)
                    self.location_stats.add_std_dev_by_source("UNKNOWN", num_pts, mean_loc, std_loc)
                else:
                    # load the data into the stats objects
                    data_array = {}
                    for n in range(num_pts):
                        lp = COLUMN_TO_ENUM_FN["location_provider"](
                            packet.sensors.location.location_providers[
                                0 if num_pts != len(packet.sensors.location.location_providers) else n])
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
                        _ = self.location_stats.add_variance_by_source(
                            k, len(d[0]), (float(np.mean(d[0])), float(np.mean(d[1])), float(np.mean(d[2]))),
                            (float(np.var(d[0])), float(np.var(d[1])), float(np.var(d[2])))
                        )
            # use the last best location to populate the location data
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
                num_pts = 1
                self.location_stats.add_std_dev_by_source(only_prov, num_pts, mean_loc, std_loc)
            # add gps points if they exist
            if len(gps_offsets) > 0 and len(gps_timestamps) > 0:
                valid_data_points = [i for i in range(len(gps_offsets))
                                     if gps_offsets[i] < GPS_TRAVEL_MICROS - GPS_VALIDITY_BUFFER
                                     or gps_offsets[i] > GPS_TRAVEL_MICROS + GPS_VALIDITY_BUFFER]
                if len(valid_data_points) > 0:
                    valid_data = [(gps_timestamps[i], gps_offsets[i]) for i in valid_data_points]
                    if self._first_gps_data.is_full():
                        for i in valid_data:
                            self._last_gps_data.add(i)
                    else:
                        for i in valid_data:
                            self._first_gps_data.add(i, True)
                self.num_gps_points += len(valid_data_points)
            # check for movement; currently just a large enough std_dev
            if not self.has_moved:
                for lc in self.location_stats.get_all_stats():
                    if lc.std_dev[0] > MOVEMENT_METERS * DEGREES_TO_METERS \
                            or lc.std_dev[1] > MOVEMENT_METERS * DEGREES_TO_METERS \
                            or lc.std_dev[2] > MOVEMENT_METERS:
                        self.has_moved = True
        if num_pts > 0 and np.isnan(mean_sr):
            mean_sr = (packet.timing_information.packet_end_mach_timestamp
                       - packet.timing_information.packet_start_mach_timestamp) / num_pts
        return 1e6 / mean_sr

    def _get_timesync_from_packet(self, packet: api_m.RedvoxPacketM):
        """
        :param packet: packet to get data from
        """
        ts = TimeSync().from_raw_packets([packet])
        if np.isnan(packet.timing_information.best_latency):
            packet_best_latency = ts.best_latency()
            packet_best_offset = ts.best_offset()
        else:
            packet_best_latency = packet.timing_information.best_latency
            packet_best_offset = ts.best_offset() if np.isnan(packet.timing_information.best_offset) \
                else packet.timing_information.best_offset
        if ts.num_tri_messages() > 0:
            self.num_timesync_points += ts.num_tri_messages()
            self.mean_latency = \
                (self.mean_latency * self.num_packets + packet_best_latency) / (self.num_packets + 1)
            self.mean_offset = \
                (self.mean_offset * self.num_packets + packet_best_offset) / (self.num_packets + 1)
            _ts_offsets = ts.offsets().flatten()
            _ts_timestamps = ts.get_device_exchanges_timestamps()
            _ts_latencies = ts.latencies().flatten()
            if self._first_timesync_data.is_full():
                for i in range(len(_ts_timestamps)):
                    self._last_timesync_data.add((_ts_timestamps[i], _ts_latencies[i], _ts_offsets[i]))
            else:
                for i in range(len(_ts_timestamps)):
                    self._first_timesync_data.add((_ts_timestamps[i], _ts_latencies[i], _ts_offsets[i]), True)

    def add_data_from_packet(self, packet: api_m.RedvoxPacketM) -> "SessionModel":
        """
        adds data from a packet into the model.  Requires the model sensors to have been initialized.

        Stops reading data if there is an error.  If SessionModel is sealed, this function does nothing.

        :param packet: API M packet to add
        :return: the updated SessionModel
        """
        if not self.is_sealed:
            if packet.station_information.id == self.id:
                if packet.station_information.uuid == self.uuid:
                    if packet.timing_information.app_start_mach_timestamp == self.start_date:
                        self._get_timesync_from_packet(packet)
                        sensors = get_all_sensors_in_packet(packet)
                        sensors.insert(2, "health")
                        if list(self._sensors.keys()) != sensors:
                            self._errors.append(f"packet sensors {sensors} does not match.")
                        else:
                            packet_start = packet.timing_information.packet_start_mach_timestamp
                            packet_end = packet.timing_information.packet_end_mach_timestamp
                            self.num_packets += 1
                            if packet_start < self.first_data_timestamp or np.isnan(self.first_data_timestamp):
                                self.first_data_timestamp = packet_start
                            if packet_end > self.last_data_timestamp or np.isnan(self.last_data_timestamp):
                                self.last_data_timestamp = packet_end
                            for s in sensors:
                                if s not in ["audio", "compressed_audio", "health", "image"]:
                                    self._sensors[s] += (self._get_sensor_data_from_packet(s, packet)
                                                         - self._sensors[s]) / self.num_packets
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
        sensors.insert(2, "health")
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
                                  packet.station_information.description,
                                  )
            result.app_version = packet.station_information.app_version
            result.num_packets = 1
            result.first_data_timestamp = packet.timing_information.packet_start_mach_timestamp
            result.last_data_timestamp = packet.timing_information.packet_end_mach_timestamp
            result.packet_duration_s = (packet.timing_information.packet_end_mach_timestamp -
                                        packet.timing_information.packet_start_mach_timestamp) / 1e6
            result._get_timesync_from_packet(packet)
            result.set_sensor_data(packet)
        except Exception as e:
            # result = SessionModel(station_description=f"FAILED: {e}")
            raise e
        return result

    def add_from_data_stream(self, data_stream: List[api_m.RedvoxPacketM]) -> "SessionModel":
        """
        Add data from a stream of packets into the SessionModel

        :param data_stream: list of packets from a single station to read
        :return: updated SessionModel
        """
        for p in data_stream:
            self.add_data_from_packet(p)
        return self

    @staticmethod
    def create_from_stream(data_stream: List[api_m.RedvoxPacketM]) -> "SessionModel":
        """
        create a SessionModel from a stream of data packets

        :param data_stream: series of API M packets from a single station to read
        :return: SessionModel using the data from the stream
        """
        # print(f"Processing {len(data_stream)} files...")
        p1 = data_stream.pop(0)
        model = SessionModel.create_from_packet(p1)
        for p in data_stream:
            model.add_data_from_packet(p)
        data_stream.insert(0, p1)
        # print(f"Completed SessionModel of {model.id}...")
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

    def get_all_sensors(self) -> Dict:
        """
        :return: list of sensor names and mean sample rate
        """
        return self._sensors

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

    def get_all_sensor_data(self) -> List[float]:
        """
        :return: list of sensor mean sample rates
        """
        return list(self._sensors.values())

    def model_duration(self) -> float:
        """
        :return: duration of data used to create model in microseconds
        """
        return self.last_data_timestamp - self.first_data_timestamp

    def first_latency_timestamp(self) -> float:
        """
        :return: first latency timestamp of the data or np.nan if it doesn't exist
        """
        if self._first_timesync_data.size > 0:
            return self._first_timesync_data.peek()[0]
        return np.nan

    def last_latency_timestamp(self) -> float:
        """
        :return: last latency timestamp of the data or np.nan if it doesn't exist
        """
        if self._last_timesync_data.size > 0:
            return self._last_timesync_data.peek_tail()[0]
        elif self._first_timesync_data.size > 0:
            return self._first_timesync_data.peek_tail()[0]
        return np.nan

    def get_offset_model(self) -> OffsetModel:
        """
        update the session's offset model using partial timesync data.  If data exists, it will update the model.
        Returns a model if it was updated or previously existed.
        If data doesn't exist, and there is no existing model, an empty model will be returned.

        note: this uses a set of the first and last data points to approximate the timesync offset model over time.
        For an in-depth analysis, use the entire timesync data set.

        :return: estimated timesync offset model using first and last segments of timesync data
        """
        has_data = self._first_timesync_data.size + self._last_timesync_data.size > 0
        if has_data:
            first_data = self._first_timesync_data.look_at_data()
            last_data = self._last_timesync_data.look_at_data()
            timestamps = np.concatenate([np.array([first_data[i][0] for i in range(len(first_data))]),
                                         np.array([last_data[i][0] for i in range(len(last_data))]),
                                         np.array([self.first_data_timestamp + (self.model_duration() / 2)])])
            latencies = np.concatenate([np.array([first_data[i][1] for i in range(len(first_data))]),
                                        np.array([last_data[i][1] for i in range(len(last_data))]),
                                        np.array([self.mean_latency])])
            offsets = np.concatenate([np.array([first_data[i][2] for i in range(len(first_data))]),
                                      np.array([last_data[i][2] for i in range(len(last_data))]),
                                      np.array([self.mean_offset])])
            self.offset_model = OffsetModel(latencies, offsets, timestamps, self.first_latency_timestamp(),
                                            self.last_latency_timestamp(), min_samples_per_bin=1)
        if self.offset_model is None:
            return OffsetModel.empty_model()
        return self.offset_model

    def get_gps_offset(self) -> Tuple[float, float]:
        """
        update the session's gps offset model using partial gps data.  If data exists, it will update the model.
        Returns a model if it was updated or previously existed.
        If data doesn't exist, and there is no existing model, a model with nans will be returned.

        note: this uses a set of the first and last data points to approximate the gps offset model over time.
        For an in-depth analysis, use the entire GPS data set.

        :return: estimated gps offset model slope and intercept using first and last segments of gps data
        """
        has_data = self._first_gps_data.size + self._last_gps_data.size > 0
        if has_data:
            first_data = self._first_gps_data.look_at_data()
            last_data = self._last_gps_data.look_at_data()
            timestamps = np.concatenate([np.array([first_data[i][0] for i in range(len(first_data))]),
                                         np.array([last_data[i][0] for i in range(len(last_data))])])
            offsets = np.concatenate([np.array([first_data[i][1] for i in range(len(first_data))]),
                                      np.array([last_data[i][1] for i in range(len(last_data))])])
            self.gps_offset = simple_offset_weighted_linear_regression(offsets, timestamps)
        if self.gps_offset is None:
            return np.nan, np.nan
        return self.gps_offset

    def seal_model(self):
        """
        Calculates the offset model and gps offsets, then closes the model.

        WARNING: Invoking this function will prevent you from adding any more data to the model.

        WARNING: Invoking this function will convert the following properties to None:
                    * _first_timesync_data
                    * _last_timesync_data
                    * _first_gps_data
                    * _last_gps_data
        """
        self.is_sealed = True
        _ = self.get_offset_model()
        _ = self.get_gps_offset()
        self._first_timesync_data = None
        self._last_timesync_data = None
        self._first_gps_data = None
        self._last_gps_data = None
