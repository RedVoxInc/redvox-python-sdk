import os.path
from typing import List, Dict, Optional, Tuple, Union, Callable
from pathlib import Path
from dataclasses_json import dataclass_json
from dataclasses import dataclass, field

import numpy as np

import redvox
import redvox.api1000.proto.redvox_api_m_pb2 as api_m
import redvox.common.session_io as s_io
from redvox.common.timesync import TimeSync
from redvox.common.errors import RedVoxExceptions
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
from redvox.common.session_model_utils import TimeSyncModel, SensorModel


SESSION_VERSION = "2023-06-20"  # Version of the SessionModel
CLIENT_NAME = "redvox-sdk/session_model"  # Name of the client used to create the SessionModel
CLIENT_VERSION = SESSION_VERSION  # Version of the client used to create the SessionModel
GPS_TRAVEL_MICROS = 60000.  # Assumed GPS latency in microseconds
GPS_VALIDITY_BUFFER = 2000.  # microseconds before GPS offset is considered valid
DEGREES_TO_METERS = 0.00001  # About 1 meter in degrees
NUM_BUFFER_POINTS = 3  # number of data points to keep in a buffer
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


def _get_mean_sample_rate_from_sensor(sensor: Sensor) -> float:
    """
    :param sensor: Sensor to get data from
    :return: number of samples and mean sample rate of the sensor; returns np.nan if sample rate doesn't exist
    """
    num_pts = int(sensor.timestamps.timestamp_statistics.count)
    if num_pts > 1:
        return sensor.timestamps.mean_sample_rate
    return np.nan


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


def get_all_sensors_in_packet(packet: api_m.RedvoxPacketM) -> List[Tuple[str, str, float]]:
    """
    :param packet: packet to check
    :return: list of all sensors as tuple of name, description, and mean sample rate in the packet
    """
    result: List[Tuple] = []
    for s in [_AUDIO_FIELD_NAME, _COMPRESSED_AUDIO_FIELD_NAME]:
        if _has_sensor(packet, s):
            sensor = _get_sensor_for_data_extraction(s, packet)
            result.append((s, sensor.sensor_description, sensor.sample_rate))
    for s in [_PRESSURE_FIELD_NAME, _LOCATION_FIELD_NAME,
              _ACCELEROMETER_FIELD_NAME, _AMBIENT_TEMPERATURE_FIELD_NAME, _GRAVITY_FIELD_NAME,
              _GYROSCOPE_FIELD_NAME, _IMAGE_FIELD_NAME, _LIGHT_FIELD_NAME, _LINEAR_ACCELERATION_FIELD_NAME,
              _MAGNETOMETER_FIELD_NAME, _ORIENTATION_FIELD_NAME, _PROXIMITY_FIELD_NAME,
              _RELATIVE_HUMIDITY_FIELD_NAME, _ROTATION_VECTOR_FIELD_NAME, _VELOCITY_FIELD_NAME]:
        if _has_sensor(packet, s):
            sensor = _get_sensor_for_data_extraction(s, packet)
            result.append((s, sensor.sensor_description, sensor.timestamps.mean_sample_rate))
    if packet.station_information.HasField("station_metrics"):
        result.insert(2, (_HEALTH_FIELD_NAME, "station_metrics",
                          packet.station_information.station_metrics.timestamps.mean_sample_rate))
    return result


@dataclass_json
@dataclass
class SessionModel:
    """
    SessionModel is designed to summarize an operational period of a station.  Summaries do not include data from
    sensors, and only if necessary is limited amounts of data stored within the model.

    Timestamps are in microseconds since epoch UTC

    Sample rates are in hz

    Latency and offset are in microseconds

    Packet duration is in microseconds

    Timestamps are NEVER the corrected values; it is up to the user to apply any corrections derived from information
    presented by this class

    Properties:
        id: str, id of the station.  Default ""

        uuid: str, uuid of the station.  Default ""

        start_date: float, Timestamp since epoch UTC of when station was started.  Default np.nan

        station_description: str, Text description of the station.  Default ""

        app_name: str, Name of the app the station is running.  Default "RedVox"

        api: float, Version number of the API the station is using.  Default np.nan

        sub_api: float, Version number of the sub-API the station in using.  Default np.nan

        make: str, Make of the station.  Default ""

        model: str, Model of the station.  Default ""

        app_version: str, Version of the app the station is running.  Default ""

        owner: str, Owner of the device.  Default ""

        is_private: bool, True if the device data is private.  Default False

        packet_duration: float, Length of station's data packets in microseconds.  Default np.nan

        sensors: List[SensorModel], A list of the name, description, and mean sample rate in Hz for each sensor.

        num_packets: int, Number of files used to create the model.  Default 0

        sub: List[], Links to other models with more granular data.

    Protected:
        timesync_model: TimeSyncModel, Stores all timesync information.

        _session_version: str, the version of the SessionModel.

        _client: str, the name of the client that created the SessionModel.

        _client_version: str, the version of the client that created the SessionModel

        _errors: RedVoxExceptions, Contains any errors found when creating the model.

        _sdk_version: str, the version of the SDK used to create the model.
    """
    id: str = ""
    uuid: str = ""
    start_date: float = np.nan
    station_description: str = ""
    app_name: str = "RedVox"
    api: float = np.nan
    sub_api: float = np.nan
    make: str = ""
    model: str = ""
    app_version: str = ""
    owner: str = ""
    is_private: bool = False
    packet_duration: float = np.nan
    sensors: List[SensorModel] = field(default_factory=list)
    num_packets: int = 0
    sub: List[str] = field(default_factory=list)

    # offset_model: Optional[OffsetModel] = None
    # is_sealed: bool = False
    # first_data_timestamp: float = np.nan
    # last_data_timestamp: float = np.nan
    # location_stats: LocationStats = LocationStats()
    # has_moved: bool = False
    # num_gps_points: int = 0
    # self._first_gps_data: CircularQueue = CircularQueue(NUM_BUFFER_POINTS)
    # self._last_gps_data: CircularQueue = CircularQueue(NUM_BUFFER_POINTS)
    # gps_offset: Optional[Tuple[float, float]] = None

    def __post_init__(self):
        self.timesync_model: TimeSyncModel = TimeSyncModel(NUM_BUFFER_POINTS)
        self._session_version: str = SESSION_VERSION
        self._client: str = CLIENT_NAME
        self._client_version: str = CLIENT_VERSION
        self._errors: RedVoxExceptions = RedVoxExceptions("SessionModel")
        self._sdk_version: str = redvox.version()

    def __repr__(self):
        return f"session_version: {self._session_version}, " \
               f"client: {self._client}, " \
               f"client_version: {self._client_version}, " \
               f"sdk_version: {self._sdk_version}, " \
               f"id: {self.id}, " \
               f"uuid: {self.uuid}, " \
               f"start_date: {self.start_date}, " \
               f"station_description: {self.station_description}, " \
               f"app_name: {self.app_name}, " \
               f"app_version: {self.app_version}, " \
               f"api: {self.api}, " \
               f"sub_api: {self.sub_api}, " \
               f"make: {self.make}, " \
               f"model: {self.model}, " \
               f"owner: {self.owner}, " \
               f"is_private: {self.is_private}, " \
               f"num_packets: {self.num_packets}, " \
               f"packet_duration: {self.packet_duration}, " \
               f"sensors: {self.sensors}, " \
               f"timesync: {self.timesync_model}, " \
               f"sub: {self.sub}"

    def __str__(self):
        s_d = np.nan if np.isnan(self.start_date) \
            else datetime_from_epoch_microseconds_utc(self.start_date).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return f"session_version: {self._session_version}, " \
               f"client: {self._client}, " \
               f"client_version: {self._client_version}, " \
               f"sdk_version: {self._sdk_version}, " \
               f"id: {self.id}, " \
               f"uuid: {self.uuid}, " \
               f"start_date: {s_d}, " \
               f"station_description: {self.station_description}, " \
               f"app_name: {self.app_name}, " \
               f"app_version: {self.app_version}, " \
               f"api: {self.api}, " \
               f"sub_api: {self.sub_api}, " \
               f"make: {self.make}, " \
               f"model: {self.model}, " \
               f"owner: {self.owner}, " \
               f"is_private: {self.is_private}, " \
               f"num_packets: {self.num_packets}, " \
               f"packet_duration: {self.packet_duration}, " \
               f"sensors: {self.sensors}, " \
               f"timesync: {self.timesync_model}, " \
               f"sub: {self.sub}"

    # def as_dict(self) -> dict:
    #     """
    #     :return: SessionModel as a dictionary
    #     """
    #     return {
    #         "session_version": self._session_version,
    #         "client": self._client,
    #         "client_version": self._client_version,
    #         "sdk_version": self._sdk_version,
    #         "id": self.id,
    #         "uuid": self.uuid,
    #         "start_date": self.start_date,
    #         "station_description": self.station_description,
    #         "app_name": self.app_name,
    #         "app_version": self.app_version,
    #         "api": self.api,
    #         "sub_api": self.sub_api,
    #         "make": self.make,
    #         "model": self.model,
    #         "owner": self.owner,
    #         "is_private": self.is_private,
    #         "num_packets": self.num_packets,
    #         "packet_duration": self.packet_duration,
    #         "sensors": self.sensors,
    #         "timesync_model": self.timesync_model,
    #         "sub": self.sub,
    #         "errors": self._errors.as_dict()
    #     }

    def default_json_file_name(self) -> str:
        """
        :return: Default filename as [id]_[start_date], with start_date as integer of microseconds
                    since epoch UTC.  File extension NOT included.
        """
        return f"{self.id}_{0 if np.isnan(self.start_date) else int(self.start_date)}"

    # @staticmethod
    # def from_json_dict(json_dict: dict) -> "SessionModel":
    #     """
    #     Reads a JSON dictionary and recreates the SessionModel.
    #     If dictionary is improperly formatted, raises a ValueError.
    #
    #     :param json_dict: the dictionary to read
    #     :return: SessionModel defined by the JSON
    #     """
    #     result = SessionModel(json_dict["id"], json_dict["uuid"], json_dict["start_date"],
    #                           json_dict["api"], json_dict["sub_api"], json_dict["make"], json_dict["model"],
    #                           json_dict["station_description"], json_dict["app_name"])
    #
    #     result._session_version = json_dict["session_version"]
    #     result.app_version = json_dict["app_version"]
    #     result.packet_duration_s = json_dict["packet_duration_s"]
    #     result.num_packets = json_dict["num_packets"]
    #     result.first_data_timestamp = json_dict["first_data_timestamp"]
    #     result.last_data_timestamp = json_dict["last_data_timestamp"]
    #     result.location_stats = LocationStats.from_dict(json_dict["location_stats"])
    #     result.has_moved = json_dict["has_moved"]
    #     result.num_timesync_points = json_dict["num_timesync_points"]
    #     result.mean_latency = json_dict["mean_latency"]
    #     result.mean_offset = json_dict["mean_offset"]
    #     result.num_gps_points = json_dict["num_gps_points"]
    #     result._errors = RedVoxExceptions.from_dict(json_dict["errors"])
    #     result._sdk_version = json_dict["sdk_version"]
    #     result._sensors = json_dict["sensors"]
    #     result.is_sealed = json_dict["is_sealed"]
    #     if result.is_sealed:
    #         result._first_timesync_data = json_dict["first_timesync_data"]
    #         result._last_timesync_data = json_dict["last_timesync_data"]
    #         result._first_gps_data = json_dict["first_gps_data"]
    #         result._last_gps_data = json_dict["last_gps_data"]
    #     # else:
    #     #     result._first_timesync_data = CircularQueue.from_dict(json_dict["first_timesync_data"])
    #     #     result._last_timesync_data = CircularQueue.from_dict(json_dict["last_timesync_data"])
    #     #     result._first_gps_data = CircularQueue.from_dict(json_dict["first_gps_data"])
    #     #     result._last_gps_data = CircularQueue.from_dict(json_dict["last_gps_data"])
    #     if "offset_model" in json_dict.keys():
    #         result.offset_model = OffsetModel.from_dict(json_dict["offset_model"])
    #     if "gps_offset" in json_dict.keys():
    #         result.gps_offset = json_dict["gps_offset"]
    #
    #     return result

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
            with open(file_path, "r") as f_p:
                return SessionModel.from_json(f_p)
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

    def client(self) -> str:
        """
        :return: SessionModel client name
        """
        return self._client

    def client_version(self) -> str:
        """
        :return: SessionModel client version
        """
        return self._client_version

    def audio_sample_rate_nominal_hz(self) -> float:
        """
        :return: the nominal audio sample rate in hz
        """
        for s in self.sensors:
            if s.name == "audio":
                return s.sample_rate_stats.welford.mean
        return np.nan

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
                mean_sr = _get_mean_sample_rate_from_sensor(snsr)
            else:
                self._errors.append(f"Invalid sensor f{sensor} requested; unable to find it in the packet.")
                return np.nan
        # if sensor == _LOCATION_FIELD_NAME:
        #     # get all the location data
        #     gps_offsets = []
        #     gps_timestamps = []
        #     # check if there is data to read
        #     if num_pts > 0:
        #         has_lats = packet.sensors.location.HasField("latitude_samples")
        #         has_lons = packet.sensors.location.HasField("longitude_samples")
        #         has_alts = packet.sensors.location.HasField("altitude_samples")
        #         gps_offsets = list(np.array(packet.sensors.location.timestamps_gps.timestamps)
        #                            - np.array(packet.sensors.location.timestamps.timestamps) + GPS_TRAVEL_MICROS)
        #         gps_timestamps = packet.sensors.location.timestamps_gps.timestamps
        #         # make sure we have provider data; no providers means using default UNKNOWN provider
        #         if len(packet.sensors.location.location_providers) < 1:
        #             mean_loc = (packet.sensors.location.latitude_samples.value_statistics.mean,
        #                         packet.sensors.location.longitude_samples.value_statistics.mean,
        #                         packet.sensors.location.altitude_samples.value_statistics.mean)
        #             std_loc = (packet.sensors.location.latitude_samples.value_statistics.standard_deviation,
        #                        packet.sensors.location.longitude_samples.value_statistics.standard_deviation,
        #                        packet.sensors.location.altitude_samples.value_statistics.standard_deviation)
        #             self.location_stats.add_std_dev_by_source("UNKNOWN", num_pts, mean_loc, std_loc)
        #         else:
        #             # load the data into the stats objects
        #             data_array = {}
        #             for n in range(num_pts):
        #                 lp = COLUMN_TO_ENUM_FN["location_provider"](
        #                     packet.sensors.location.location_providers[
        #                         0 if num_pts != len(packet.sensors.location.location_providers) else n])
        #                 if lp not in data_array.keys():
        #                     data_array[lp] = ([packet.sensors.location.latitude_samples.values[n]
        #                                        if has_lats else np.nan],
        #                                       [packet.sensors.location.longitude_samples.values[n]
        #                                        if has_lons else np.nan],
        #                                       [packet.sensors.location.altitude_samples.values[n]
        #                                        if has_alts else np.nan])
        #                 else:
        #                     data_array[lp][0].append(packet.sensors.location.latitude_samples.values[n]
        #                                              if has_lats else np.nan)
        #                     data_array[lp][1].append(packet.sensors.location.longitude_samples.values[n]
        #                                              if has_lons else np.nan)
        #                     data_array[lp][2].append(packet.sensors.location.altitude_samples.values[n]
        #                                              if has_alts else np.nan)
        #             for k, d in data_array.items():
        #                 _ = self.location_stats.add_variance_by_source(
        #                     k, len(d[0]), (float(np.mean(d[0])), float(np.mean(d[1])), float(np.mean(d[2]))),
        #                     (float(np.var(d[0])), float(np.var(d[1])), float(np.var(d[2])))
        #                 )
        #     # use the last best location to populate the location data
        #     elif packet.sensors.location.last_best_location is not None:
        #         gps_offsets = [packet.sensors.location.last_best_location.latitude_longitude_timestamp.gps
        #                        - packet.sensors.location.last_best_location.latitude_longitude_timestamp.mach
        #                        + GPS_TRAVEL_MICROS]
        #         gps_timestamps = [packet.sensors.location.last_best_location.latitude_longitude_timestamp.gps]
        #         mean_loc = (packet.sensors.location.last_best_location.latitude,
        #                     packet.sensors.location.last_best_location.longitude,
        #                     packet.sensors.location.last_best_location.altitude)
        #         only_prov = COLUMN_TO_ENUM_FN["location_provider"](
        #             packet.sensors.location.last_best_location.location_provider)
        #         std_loc = (0., 0., 0.)
        #         num_pts = 1
        #         self.location_stats.add_std_dev_by_source(only_prov, num_pts, mean_loc, std_loc)
        #     # add gps points if they exist
        #     if len(gps_offsets) > 0 and len(gps_timestamps) > 0:
        #         valid_data_points = [i for i in range(len(gps_offsets))
        #                              if gps_offsets[i] < GPS_TRAVEL_MICROS - GPS_VALIDITY_BUFFER
        #                              or gps_offsets[i] > GPS_TRAVEL_MICROS + GPS_VALIDITY_BUFFER]
        #         if len(valid_data_points) > 0:
        #             valid_data = [(gps_timestamps[i], gps_offsets[i]) for i in valid_data_points]
        #             if self._first_gps_data.is_full():
        #                 for i in valid_data:
        #                     self._last_gps_data.add(i)
        #             else:
        #                 for i in valid_data:
        #                     self._first_gps_data.add(i, True)
        #         self.num_gps_points += len(valid_data_points)
        #     # check for movement; currently just a large enough std_dev
        #     if not self.has_moved:
        #         for lc in self.location_stats.get_all_stats():
        #             if lc.std_dev[0] > MOVEMENT_METERS * DEGREES_TO_METERS \
        #                     or lc.std_dev[1] > MOVEMENT_METERS * DEGREES_TO_METERS \
        #                     or lc.std_dev[2] > MOVEMENT_METERS:
        #                 self.has_moved = True
        # if num_pts > 0 and np.isnan(mean_sr):
        #     mean_sr = (packet.timing_information.packet_end_mach_timestamp
        #                - packet.timing_information.packet_start_mach_timestamp) / num_pts
        return mean_sr

    def _get_timesync_from_packet(self, packet: api_m.RedvoxPacketM):
        """
        updates the timesync_model using data from the packet

        :param packet: packet to get data from
        """
        self.timesync_model.update_model(TimeSync().from_raw_packets([packet]))

    def add_data_from_packet(self, packet: api_m.RedvoxPacketM) -> "SessionModel":
        """
        adds data from a packet into the model.  Requires the model sensors to have been initialized.

        Stops reading data if there is an error.

        :param packet: API M packet to add
        :return: the updated SessionModel
        """
        # check three main values of the station key
        if packet.station_information.id == self.id:
            if packet.station_information.uuid == self.uuid:
                if packet.timing_information.app_start_mach_timestamp == self.start_date:
                    sensors = get_all_sensors_in_packet(packet)
                    # check that we match all sensors
                    if self.get_sensor_keys() != [(s[0], s[1]) for s in sensors]:
                        self._errors.append(f"packet sensors {sensors} does not match.")
                    else:
                        self._get_timesync_from_packet(packet)
                        self.num_packets += 1
                        for s in sensors:
                            self.sensors[0].update(s[2])
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
        self.sensors = []
        for s in sensors:
            self.sensors.append(SensorModel(s[0], s[1], s[2]))

    @staticmethod
    def create_from_packet(packet: api_m.RedvoxPacketM) -> "SessionModel":
        """
        create a SessionModel from a single packet

        :param packet: API M packet of data to read
        :return: SessionModel using the data from the packet
        """
        try:
            duration = packet.timing_information.packet_end_mach_timestamp\
                       - packet.timing_information.packet_start_mach_timestamp
            result = SessionModel(id=packet.station_information.id, uuid=packet.station_information.uuid,
                                  start_date=packet.timing_information.app_start_mach_timestamp,
                                  station_description=packet.station_information.description,
                                  api=packet.api, sub_api=packet.sub_api, make=packet.station_information.make,
                                  model=packet.station_information.model, owner=packet.station_information.auth_id,
                                  app_version=packet.station_information.app_version,
                                  is_private=packet.station_information.is_private,
                                  packet_duration=duration, num_packets=1
                                  )
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
        return len(self.sensors)

    def get_sensor_names(self) -> List[str]:
        """
        :return: list of sensor names
        """
        return [s.name for s in self.sensors]

    def get_sensor_keys(self) -> List[Tuple[str, str]]:
        """
        :return: list of tuple of sensor names and sensor descriptions
        """
        return [(s.name, s.description) for s in self.sensors]

    def get_all_sensors(self) -> List:
        """
        :return: list of sensor names, descriptions and mean sample rate
        """
        return self.sensors

    def get_sensor_data(self, sensor_name: str, sensor_description: Optional[str] = None) -> Optional[float]:
        """
        Returns the data associated with a sensor or None if the data doesn't exist.

        Requires at least a sensor name to search for.  If sensor description is not given, the first matching
        sensor name will be returned.

        Currently returns the mean sample rate of the sensor

        :param sensor_name: sensor name to get data for
        :param sensor_description: sensor description to get data for.  Default None
        :return: sensor data or None
        """
        if sensor_description is not None:
            for s in self.sensors:
                if s.name == sensor_name and s.description == sensor_description:
                    return s.finalized()[0]
        else:
            for s in self.sensors:
                if s.name == sensor_name:
                    return s.finalized()[0]
        return None

    def get_all_sensor_data(self) -> List[float]:
        """
        :return: list of sensor mean sample rates
        """
        return [s.finalized()[0] for s in self.sensors]

    def model_duration(self) -> float:
        """
        :return: duration of data used to create model in microseconds
        """
        return self.timesync_model.last_timesync_timestamp - self.timesync_model.first_timesync_timestamp

    # def first_latency_timestamp(self) -> float:
    #     """
    #     :return: first latency timestamp of the data or np.nan if it doesn't exist
    #     """
    #     if self._first_timesync_data.size > 0:
    #         return self._first_timesync_data.peek()[0]
    #     return np.nan
    #
    # def last_latency_timestamp(self) -> float:
    #     """
    #     :return: last latency timestamp of the data or np.nan if it doesn't exist
    #     """
    #     if self._last_timesync_data.size > 0:
    #         return self._last_timesync_data.peek_tail()[0]
    #     elif self._first_timesync_data.size > 0:
    #         return self._first_timesync_data.peek_tail()[0]
    #     return np.nan
    #
    # def get_offset_model(self) -> OffsetModel:
    #     """
    #     update the session's offset model using partial timesync data.  If data exists, it will update the model.
    #     Returns a model if it was updated or previously existed.
    #     If data doesn't exist, and there is no existing model, an empty model will be returned.
    #
    #     note: this uses a set of the first and last data points to approximate the timesync offset model over time.
    #     For an in-depth analysis, use the entire timesync data set.
    #
    #     :return: estimated timesync offset model using first and last segments of timesync data
    #     """
    #     has_data = self._first_timesync_data.size + self._last_timesync_data.size > 0
    #     if has_data:
    #         first_data = self._first_timesync_data.look_at_data()
    #         last_data = self._last_timesync_data.look_at_data()
    #         timestamps = np.concatenate([np.array([first_data[i][0] for i in range(len(first_data))]),
    #                                      np.array([last_data[i][0] for i in range(len(last_data))]),
    #                                      np.array([self.first_data_timestamp + (self.model_duration() / 2)])])
    #         latencies = np.concatenate([np.array([first_data[i][1] for i in range(len(first_data))]),
    #                                     np.array([last_data[i][1] for i in range(len(last_data))]),
    #                                     np.array([self.mean_latency])])
    #         offsets = np.concatenate([np.array([first_data[i][2] for i in range(len(first_data))]),
    #                                   np.array([last_data[i][2] for i in range(len(last_data))]),
    #                                   np.array([self.mean_offset])])
    #         self.offset_model = OffsetModel(latencies, offsets, timestamps, self.first_latency_timestamp(),
    #                                         self.last_latency_timestamp(), min_samples_per_bin=1)
    #     if self.offset_model is None:
    #         return OffsetModel.empty_model()
    #     return self.offset_model
    #
    # def get_gps_offset(self) -> Tuple[float, float]:
    #     """
    #     update the session's gps offset model using partial gps data.  If data exists, it will update the model.
    #     Returns a model if it was updated or previously existed.
    #     If data doesn't exist, and there is no existing model, a model with nans will be returned.
    #
    #     note: this uses a set of the first and last data points to approximate the gps offset model over time.
    #     For an in-depth analysis, use the entire GPS data set.
    #
    #     :return: estimated gps offset model slope and intercept using first and last segments of gps data
    #     """
    #     has_data = self._first_gps_data.size + self._last_gps_data.size > 0
    #     if has_data:
    #         first_data = self._first_gps_data.look_at_data()
    #         last_data = self._last_gps_data.look_at_data()
    #         timestamps = np.concatenate([np.array([first_data[i][0] for i in range(len(first_data))]),
    #                                      np.array([last_data[i][0] for i in range(len(last_data))])])
    #         offsets = np.concatenate([np.array([first_data[i][1] for i in range(len(first_data))]),
    #                                   np.array([last_data[i][1] for i in range(len(last_data))])])
    #         self.gps_offset = simple_offset_weighted_linear_regression(offsets, timestamps)
    #     if self.gps_offset is None:
    #         return np.nan, np.nan
    #     return self.gps_offset
    #
    # def seal_model(self):
    #     """
    #     Calculates the offset model and gps offsets, then closes the model.
    #
    #     WARNING: Invoking this function will prevent you from adding any more data to the model.
    #
    #     WARNING: Invoking this function will convert the following properties to None:
    #                 * _first_timesync_data
    #                 * _last_timesync_data
    #                 * _first_gps_data
    #                 * _last_gps_data
    #     """
    #     self.is_sealed = True
    #     _ = self.get_offset_model()
    #     _ = self.get_gps_offset()
    #     self._first_timesync_data = None
    #     self._last_timesync_data = None
    #     self._first_gps_data = None
    #     self._last_gps_data = None
