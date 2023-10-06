"""
This module contains classes and functions that support SessionModel.
"""
from typing import List, Optional, Tuple, Dict, Union, Callable
from bisect import insort

import numpy as np

import redvox.api1000.proto.redvox_api_m_pb2 as api_m
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
from redvox.cloud import session_model_api as sm
from redvox.common.timesync import TimeSync


NUM_BUFFER_POINTS = 3  # number of data points to keep in a buffer
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
    api_m.RedvoxPacketM.StationInformation.StationMetrics,
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
    sensor_fn: Optional[Callable[[api_m.RedvoxPacketM], Sensor]] = __SENSOR_NAME_TO_SENSOR_FN[sensor_name]
    if (sensor_name == _HEALTH_FIELD_NAME or _has_sensor(packet, sensor_name)) and sensor_fn is not None:
        return sensor_fn(packet)


def _get_mean_sample_rate_from_sensor(sensor: Sensor) -> float:
    """
    :param sensor: Sensor to get data from
    :return: mean sample rate of the sensor or np.nan if sample rate doesn't exist
    """
    return sensor.timestamps.mean_sample_rate if int(sensor.timestamps.timestamp_statistics.count) > 1 else np.nan


def _has_sensor(data: Union[api_m.RedvoxPacketM, api_m.RedvoxPacketM.Sensors], field_name: str) -> bool:
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
    for s in [
        _PRESSURE_FIELD_NAME,
        _LOCATION_FIELD_NAME,
        _ACCELEROMETER_FIELD_NAME,
        _AMBIENT_TEMPERATURE_FIELD_NAME,
        _GRAVITY_FIELD_NAME,
        _GYROSCOPE_FIELD_NAME,
        _IMAGE_FIELD_NAME,
        _LIGHT_FIELD_NAME,
        _LINEAR_ACCELERATION_FIELD_NAME,
        _MAGNETOMETER_FIELD_NAME,
        _ORIENTATION_FIELD_NAME,
        _PROXIMITY_FIELD_NAME,
        _RELATIVE_HUMIDITY_FIELD_NAME,
        _ROTATION_VECTOR_FIELD_NAME,
        _VELOCITY_FIELD_NAME,
    ]:
        if _has_sensor(packet, s):
            sensor = _get_sensor_for_data_extraction(s, packet)
            result.append((s, sensor.sensor_description, sensor.timestamps.mean_sample_rate))
    if packet.station_information.HasField("station_metrics"):
        result.insert(
            2,
            (
                _HEALTH_FIELD_NAME,
                "station_metrics",
                packet.station_information.station_metrics.timestamps.mean_sample_rate,
            ),
        )
    return result


def __ordered_insert(buffer: List, value: Tuple):
    """
    inserts the value into the buffer using the timestamp as the key

    :param value: value to add.  Must include a timestamp and the same data type as the other buffer elements
    """
    if len(buffer) < 1:
        buffer.append(value)
    else:
        insort(buffer, value)


def add_to_fst_buffer(buffer: List, buf_max_size: int, timestamp: float, value):
    """
    Add a value into the first buffer.

    * If the buffer is not full, the value is added automatically
    * If the buffer is full, the value is only added if it comes before the last element.
    * Ignores adding any duplicate values

    :param buffer: the buffer to add the value to
    :param buf_max_size: the maximum size of the buffer
    :param timestamp: timestamp in microseconds since epoch UTC to add.
    :param value: value to add.  Must be the same type of data as the other elements in the queue.
    """
    if (len(buffer) < buf_max_size or timestamp < buffer[-1][0]) and timestamp not in [n[0] for n in buffer]:
        __ordered_insert(buffer, (timestamp, value))
        while len(buffer) > buf_max_size:
            buffer.pop()


def add_to_lst_buffer(buffer: List, buf_max_size: int, timestamp: float, value):
    """
    Add a value into the last buffer.

    * If the buffer is not full, the value is added automatically
    * If the buffer is full, the value is only added if it comes after the first element.
    * Ignores adding any duplicate values

    :param buffer: the buffer to add the value to
    :param buf_max_size: the maximum size of the buffer
    :param timestamp: timestamp in microseconds since epoch UTC to add.
    :param value: value to add.  Must be the same type of data as the other elements in the queue.
    """
    if (len(buffer) < buf_max_size or timestamp > buffer[0][0]) and timestamp not in [n[0] for n in buffer]:
        __ordered_insert(buffer, (timestamp, value))
        while len(buffer) > buf_max_size:
            buffer.pop(0)


def get_local_timesync(packet: api_m.RedvoxPacketM) -> Tuple:
    """
    The returning tuple looks like:

    (start_timestamp, end_timestamp, num_exchanges, best_latency, best_offset, list of TimeSyncData)

    num_exchanges, best_latency and best_offset default to 0.  list of TimeSyncData defaults to empty list.

    :param packet: packet to get timesync data from
    :return: Timing object using data from packet
    """
    ts = TimeSync().from_raw_packets([packet])
    if ts.num_tri_messages() > 0:
        _ts_latencies = ts.latencies().flatten()
        _ts_offsets = ts.offsets().flatten()
        _ts_timestamps = ts.get_device_exchanges_timestamps()
        # add data to the buffers
        _ts_data = [
            sm.TimeSyncData(_ts_timestamps[i], _ts_latencies[i], _ts_offsets[i]) for i in range(len(_ts_timestamps))
        ]
        return (
            ts.data_start_timestamp(),
            ts.data_end_timestamp(),
            ts.num_tri_messages(),
            ts.best_latency(),
            ts.best_offset(),
            _ts_data,
        )
    return (
        ts.data_start_timestamp(),
        ts.data_end_timestamp(),
        0.0,
        0.0,
        0.0,
        [],
    )


def add_to_welford(value: float, welford: Optional[sm.WelfordAggregator] = None) -> sm.WelfordAggregator:
    """
    adds the value to the welford, then returns the updated object.

    If welford is None, creates a new WelfordAggregator object and returns it.

    :param value: the value to add
    :param welford: optional WelfordAggregator object to update.  if not given, will make a new one.  Default None
    :return: updated or new WelfordAggregator object
    """
    if welford is None:
        return sm.WelfordAggregator(0.0, value, 1)
    welford.cnt += 1
    delta = value - welford.mean
    welford.mean += delta / float(welford.cnt)
    delta2 = value - welford.mean
    welford.m2 += delta * delta2
    return welford


def add_to_stats(value: float, stats: Optional[sm.Stats] = None) -> sm.Stats:
    """
    adds the value to the stats, then returns the updated object.

    If stats is None, creates a new Stats object and returns it.

    :param value: the value to add
    :param stats: optional Stats object to update.  if not given, will make a new one.  Default None
    :return: updated or new Stats object
    """
    if stats is None:
        return sm.Stats(value, value, add_to_welford(value))
    if value < stats.min:
        stats.min = value
    if value > stats.max:
        stats.max = value
    add_to_welford(value, stats.welford)
    return stats


def get_location_data(packet: api_m.RedvoxPacketM) -> List[Tuple[str, float, float, float, float]]:
    """
    :param packet: packet to get location data from
    :return: List of location data as a tuples from the packet
    """
    locations = []
    loc = packet.sensors.location
    lat = lon = alt = ts = 0.0
    source = "UNKNOWN"
    num_pts = int(loc.timestamps.timestamp_statistics.count)
    # check for actual location values
    if len(loc.location_providers) < 1 and num_pts > 0:
        lat = loc.latitude_samples.value_statistics.mean
        lon = loc.longitude_samples.value_statistics.mean
        alt = loc.altitude_samples.value_statistics.mean
        ts = loc.timestamps.timestamp_statistics.mean
    elif (
        num_pts > 0
        and loc.latitude_samples.value_statistics.count > 0
        and loc.longitude_samples.value_statistics.count > 0
        and loc.altitude_samples.value_statistics.count > 0
        and num_pts == loc.latitude_samples.value_statistics.count
        and num_pts == loc.altitude_samples.value_statistics.count
        and num_pts == loc.longitude_samples.value_statistics.count
    ):
        lats = loc.latitude_samples.values
        lons = loc.longitude_samples.values
        alts = loc.altitude_samples.values
        tstp = loc.timestamps.timestamps
        for i in range(num_pts):
            source = (
                "UNKNOWN"
                if len(loc.location_providers) != num_pts
                else COLUMN_TO_ENUM_FN["location_provider"](loc.location_providers[i])
            )
            locations.append((source, lats[i], lons[i], alts[i], tstp[i]))
        # set a special flag for later, so we don't add an extra location value
        source = None
    elif loc.last_best_location is not None:
        ts = loc.last_best_location.latitude_longitude_timestamp.mach
        source = COLUMN_TO_ENUM_FN["location_provider"](loc.last_best_location.location_provider)
        lat = loc.last_best_location.latitude
        lon = loc.last_best_location.longitude
        alt = loc.last_best_location.altitude
    elif loc.overall_best_location is not None:
        ts = loc.overall_best_location.latitude_longitude_timestamp.mach
        source = COLUMN_TO_ENUM_FN["location_provider"](loc.overall_best_location.location_provider)
        lat = loc.overall_best_location.latitude
        lon = loc.overall_best_location.longitude
        alt = loc.overall_best_location.altitude
    # source is not None if we got only one location through non-usual methods
    if source is not None:
        locations.append((source, lat, lon, alt, ts))
    return locations


def get_dynamic_data(packet: api_m.RedvoxPacketM) -> Dict:
    """
    :param packet: packet to get data from
    :return: Dictionary of all dynamic session data from the packet
    """
    location = get_location_data(packet)
    battery = packet.station_information.station_metrics.battery.value_statistics.mean
    temperature = packet.station_information.station_metrics.temperature.value_statistics.mean
    return {"location": location, "battery": battery, "temperature": temperature}


def add_to_location(
    lat: float, lon: float, alt: float, timestamp: float, loc_stat: Optional[sm.LocationStat] = None
) -> sm.LocationStat:
    """
    update a LocationStat object with the location, or make a new one

    :param lat: latitude in degrees
    :param lon: longitude in degrees
    :param alt: altitude in meters
    :param timestamp: timestamp in microseconds from epoch UTC
    :param loc_stat: optional LocationStat object to update.  if not given, will make a new one.  Default None
    :return: updated or new LocationStat object
    """
    if loc_stat is None:
        fst_lst = sm.FirstLastBufLocation([], NUM_BUFFER_POINTS, [], NUM_BUFFER_POINTS)
        add_to_fst_buffer(fst_lst.fst, fst_lst.fst_max_size, timestamp, sm.Location(lat, lon, alt))
        add_to_lst_buffer(fst_lst.lst, fst_lst.lst_max_size, timestamp, sm.Location(lat, lon, alt))
        return sm.LocationStat(fst_lst, add_to_stats(lat), add_to_stats(lon), add_to_stats(alt))
    add_to_fst_buffer(loc_stat.fst_lst.fst, loc_stat.fst_lst.fst_max_size, timestamp, sm.Location(lat, lon, alt))
    add_to_lst_buffer(loc_stat.fst_lst.lst, loc_stat.fst_lst.lst_max_size, timestamp, sm.Location(lat, lon, alt))
    loc_stat.lat = add_to_stats(lat, loc_stat.lat)
    loc_stat.lng = add_to_stats(lon, loc_stat.lng)
    loc_stat.alt = add_to_stats(alt, loc_stat.alt)
    return loc_stat


def add_location_data(
    data: List[Tuple[str, float, float, float, float]], loc_dict: Optional[Dict[str, sm.LocationStat]] = None
) -> Dict[str, sm.LocationStat]:
    """
    update a dictionary of LocationStat or make a new dictionary

    :param data: the data to add
    :param loc_dict: the location dictionary to update
    :return: the updated or new location dictionary
    """
    if loc_dict is None:
        loc_dict = {}
    for s in data:
        loc_dict[s[0]] = add_to_location(s[1], s[2], s[3], s[4], loc_dict[s[0]] if s[0] in loc_dict.keys() else None)
    return loc_dict
