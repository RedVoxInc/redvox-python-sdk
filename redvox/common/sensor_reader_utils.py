"""
This module loads sensor data from Redvox packets
"""

from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np
# noinspection Mypy
import pyarrow as pa

import redvox.api1000.proto.redvox_api_m_pb2 as api_m
from redvox.common import date_time_utils as dtu
from redvox.common.sensor_data import SensorData, SensorType


# Dataframe column definitions
COMPRESSED_AUDIO_COLUMNS: List[str] = [
    "timestamps",
    "unaltered_timestamps",
    "compressed_audio",
    "audio_codec",
]

IMAGE_COLUMNS: List[str] = [
    "timestamps",
    "unaltered_timestamps",
    "image",
    "image_codec",
]

LOCATION_COLUMNS: List[str] = [
    "timestamps",
    "unaltered_timestamps",
    "gps_timestamps",
    "latitude",
    "longitude",
    "altitude",
    "speed",
    "bearing",
    "horizontal_accuracy",
    "vertical_accuracy",
    "speed_accuracy",
    "bearing_accuracy",
    "location_provider",
]

STATION_HEALTH_COLUMNS: List[str] = [
    "timestamps",
    "unaltered_timestamps",
    "battery_charge_remaining",
    "battery_current_strength",
    "internal_temp_c",
    "network_type",
    "network_strength",
    "power_state",
    "avail_ram",
    "avail_disk",
    "cell_service",
    "cpu_utilization",
    "wifi_wake_lock",
    "screen_state",
    "screen_brightness",
]

# These are used for checking if a field is present or not
__ACCELEROMETER_FIELD_NAME: str = "accelerometer"
__AMBIENT_TEMPERATURE_FIELD_NAME: str = "ambient_temperature"
__AUDIO_FIELD_NAME: str = "audio"
__COMPRESSED_AUDIO_FIELD_NAME: str = "compressed_audio"
__GRAVITY_FIELD_NAME: str = "gravity"
__GYROSCOPE_FIELD_NAME: str = "gyroscope"
__IMAGE_FIELD_NAME: str = "image"
__LIGHT_FIELD_NAME: str = "light"
__LINEAR_ACCELERATION_FIELD_NAME: str = "linear_acceleration"
__LOCATION_FIELD_NAME: str = "location"
__MAGNETOMETER_FIELD_NAME: str = "magnetometer"
__ORIENTATION_FIELD_NAME: str = "orientation"
__PRESSURE_FIELD_NAME: str = "pressure"
__PROXIMITY_FIELD_NAME: str = "proximity"
__RELATIVE_HUMIDITY_FIELD_NAME: str = "relative_humidity"
__ROTATION_VECTOR: str = "rotation_vector"
__VELOCITY: str = "velocity"

__SENSOR_TYPE_TO_FIELD_NAME: Dict[SensorType, str] = {
    SensorType.UNKNOWN_SENSOR: "unknown",
    SensorType.STATION_HEALTH: "unknown",
    SensorType.ACCELEROMETER: __ACCELEROMETER_FIELD_NAME,
    SensorType.AMBIENT_TEMPERATURE: __AMBIENT_TEMPERATURE_FIELD_NAME,
    SensorType.AUDIO: __AUDIO_FIELD_NAME,
    SensorType.COMPRESSED_AUDIO: __COMPRESSED_AUDIO_FIELD_NAME,
    SensorType.GRAVITY: __GRAVITY_FIELD_NAME,
    SensorType.GYROSCOPE: __GYROSCOPE_FIELD_NAME,
    SensorType.IMAGE: __IMAGE_FIELD_NAME,
    SensorType.LIGHT: __LIGHT_FIELD_NAME,
    SensorType.LINEAR_ACCELERATION: __LINEAR_ACCELERATION_FIELD_NAME,
    SensorType.LOCATION: __LOCATION_FIELD_NAME,
    SensorType.BEST_LOCATION: __LOCATION_FIELD_NAME,
    SensorType.MAGNETOMETER: __MAGNETOMETER_FIELD_NAME,
    SensorType.ORIENTATION: __ORIENTATION_FIELD_NAME,
    SensorType.PRESSURE: __PRESSURE_FIELD_NAME,
    SensorType.PROXIMITY: __PROXIMITY_FIELD_NAME,
    SensorType.RELATIVE_HUMIDITY: __RELATIVE_HUMIDITY_FIELD_NAME,
    SensorType.ROTATION_VECTOR: __ROTATION_VECTOR,
    SensorType.INFRARED: __PROXIMITY_FIELD_NAME,
}

Sensor = Union[
    api_m.RedvoxPacketM.Sensors.Xyz,
    api_m.RedvoxPacketM.Sensors.Single,
    api_m.RedvoxPacketM.Sensors.Audio,
    api_m.RedvoxPacketM.Sensors.Image,
    api_m.RedvoxPacketM.Sensors.Location,
    api_m.RedvoxPacketM.Sensors.CompressedAudio,
]

# Maps a sensor type to a function that can extract that sensor for a particular packet.
__SENSOR_TYPE_TO_SENSOR_FN: Dict[
    SensorType,
    Optional[
        Callable[
            [api_m.RedvoxPacketM],
            Sensor,
        ]
    ],
] = {
    SensorType.UNKNOWN_SENSOR: None,
    SensorType.STATION_HEALTH: None,
    SensorType.ACCELEROMETER: lambda packet: packet.sensors.accelerometer,
    SensorType.AMBIENT_TEMPERATURE: lambda packet: packet.sensors.ambient_temperature,
    SensorType.AUDIO: lambda packet: packet.sensors.audio,
    SensorType.COMPRESSED_AUDIO: lambda packet: packet.sensors.compressed_audio,
    SensorType.GRAVITY: lambda packet: packet.sensors.gravity,
    SensorType.GYROSCOPE: lambda packet: packet.sensors.gyroscope,
    SensorType.IMAGE: lambda packet: packet.sensors.image,
    SensorType.LIGHT: lambda packet: packet.sensors.light,
    SensorType.LINEAR_ACCELERATION: lambda packet: packet.sensors.linear_acceleration,
    SensorType.LOCATION: lambda packet: packet.sensors.location,
    SensorType.BEST_LOCATION: lambda packet: packet.sensors.location,
    SensorType.MAGNETOMETER: lambda packet: packet.sensors.magnetometer,
    SensorType.ORIENTATION: lambda packet: packet.sensors.orientation,
    SensorType.PRESSURE: lambda packet: packet.sensors.pressure,
    SensorType.PROXIMITY: lambda packet: packet.sensors.proximity,
    SensorType.RELATIVE_HUMIDITY: lambda packet: packet.sensors.relative_humidity,
    SensorType.ROTATION_VECTOR: lambda packet: packet.sensors.rotation_vector,
    SensorType.INFRARED: lambda packet: packet.sensors.proximity,
}


def __has_sensor(
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


def __packet_duration_s(packet: api_m.RedvoxPacketM) -> float:
    """
    Returns the packet duration in seconds.

    :param packet: The packet to calculate the duration for.
    :return: The packet duration in seconds.
    """
    return len(packet.sensors.audio.samples.values) / packet.sensors.audio.sample_rate


def __packet_duration_us(packet: api_m.RedvoxPacketM) -> float:
    """
    Returns the packet duration in microseconds.

    :param packet: The packet to calculate the duration for.
    :return: The packet duration in microseconds.
    """
    return __packet_duration_s(packet) * 1_000_000.0


def __stats_for_sensor_per_packet_per_second(num_packets: int,
                                             packet_dur_s: float,
                                             timestamps: np.array) -> Tuple[float, float, float]:
    """
    Sensor being evaluated must either have 1/packet or 1/second sample rate

    :param num_packets: number of packets to calculate stats for
    :param packet_dur_s: duration of packet in seconds
    :param timestamps: timestamps of the samples
    :return: sample rate in hz, sample interval in seconds, and sample interval std deviation
    """
    if len(timestamps) != num_packets:
        sample_rate = 1.0
    else:
        sample_rate = 1 / packet_dur_s
    sample_interval = 1 / sample_rate
    sample_interval_std = (
        dtu.microseconds_to_seconds(float(np.std(np.diff(timestamps))))
        if len(timestamps) > 1
        else np.nan
    )
    return sample_rate, sample_interval, sample_interval_std


def get_empty_sensor(
        name: str, sensor_type: SensorType = SensorType.UNKNOWN_SENSOR
) -> SensorData:
    """
    create a sensor data object with no data

    :param name: name of the sensor
    :param sensor_type: type of the sensor to create, default SensorType.UNKNOWN_SENSOR
    :return: empty sensor
    """
    return SensorData(name, pa.Table.from_pydict({"timestamps": []}), sensor_type)


def get_sensor_description(sensor: Sensor) -> str:
    """
    read the sensor's description from the sensor

    :param sensor: the sensor to read the description from
    :return: the sensor's description
    """
    return sensor.sensor_description


def get_sample_statistics(data_df: pa.Table) -> Tuple[float, float, float]:
    """
    calculate the sample rate, interval and interval std dev using the timestamps in the dataframe

    :param data_df: the dataframe containing timestamps to calculate statistics from
    :return: a Tuple containing the sample rate, interval and interval std dev
    """
    sample_interval: float
    sample_interval_std: float
    timestamps: np.array = data_df["timestamps"].to_numpy()
    if timestamps.size > 1:
        sample_interval = dtu.microseconds_to_seconds(
            float(np.mean(np.diff(timestamps)))
        )
        sample_interval_std = dtu.microseconds_to_seconds(
            float(np.std(np.diff(timestamps)))
        )
    else:
        sample_interval = np.nan
        sample_interval_std = np.nan
    return 1.0 / sample_interval, sample_interval, sample_interval_std


def read_apim_xyz_sensor(
        sensor: api_m.RedvoxPacketM.Sensors.Xyz, column_id: str
) -> pa.Table:
    """
    read a sensor that has xyz data channels from an api M data packet
    raises Attribute Error if sensor does not contain xyz channels

    :param sensor: the xyz api M sensor to read
    :param column_id: string, used to name the columns
    :return: dictionary representing the data in the sensor
    """
    timestamps: np.ndarray = np.array(sensor.timestamps.timestamps)
    try:
        columns: List[str] = [
            "timestamps",
            "unaltered_timestamps",
            f"{column_id}_x",
            f"{column_id}_y",
            f"{column_id}_z",
        ]
        return pa.Table.from_pydict(
            dict(zip(columns, [timestamps,
                               timestamps,
                               np.array(sensor.x_samples.values),
                               np.array(sensor.y_samples.values),
                               np.array(sensor.z_samples.values),
                               ]
                     )
                 )
        )
    except AttributeError:
        raise


def read_apim_single_sensor(
        sensor: api_m.RedvoxPacketM.Sensors.Single, column_id: str
) -> pa.Table:
    """
    read a sensor that has a single data channel from an api M data packet
    raises Attribute Error if sensor does not contain exactly one data channel

    :param sensor: the single channel api M sensor to read
    :param column_id: string, used to name the columns
    :return: pyarrow table representing the data in the sensor
    """
    timestamps: np.ndarray = np.array(sensor.timestamps.timestamps)
    try:
        columns: List[str] = ["timestamps", "unaltered_timestamps", column_id]
        return pa.Table.from_pydict(dict(zip(columns, [timestamps, timestamps, np.array(sensor.samples.values)])))
    except AttributeError:
        raise


def apim_compressed_audio_to_pyarrow(comp_audio: api_m.RedvoxPacketM.Sensors.CompressedAudio) -> pa.Table:
    """
    :param comp_audio: compressed audio sensor to convert to pyarrow table
    :return: pyarrow table representation of compressed audio data
    """
    return pa.Table.from_pydict(
        dict(zip(COMPRESSED_AUDIO_COLUMNS,
                 [
                     comp_audio.first_sample_timestamp,
                     comp_audio.first_sample_timestamp,
                     np.array(list(comp_audio.audio_bytes)),
                     comp_audio.audio_codec,
                 ]
                 )
             )
    )


def apim_image_to_pyarrow(image_sensor: api_m.RedvoxPacketM.Sensors.Image) -> pa.Table:
    """
    :param image_sensor: image sensor to convert to pyarrow table
    :return: pyarrow table representation of image data
    """
    timestamps = image_sensor.timestamps.timestamps
    codecs = np.full(len(timestamps), image_sensor.image_codec)
    return pa.Table.from_pydict(
        dict(zip(IMAGE_COLUMNS,
                 [timestamps, timestamps, image_sensor.samples, codecs]
                 )
             )
    )


def apim_best_location_to_pyarrow(best_loc: api_m.RedvoxPacketM.Sensors.Location.BestLocation,
                                  packet_start_timestamp: float) -> pa.Table:
    """
    :param best_loc: best location to convert to pyarrow table
    :param packet_start_timestamp: timestamp of packet's first sample
    :return: pyarrow table representation of best location data
    """
    return pa.Table.from_pydict(
        dict(zip(LOCATION_COLUMNS,
                 [
                     [packet_start_timestamp],
                     [best_loc.latitude_longitude_timestamp.mach],
                     [best_loc.latitude_longitude_timestamp.gps],
                     [best_loc.latitude],
                     [best_loc.longitude],
                     [best_loc.altitude],
                     [best_loc.speed],
                     [best_loc.bearing],
                     [best_loc.horizontal_accuracy],
                     [best_loc.vertical_accuracy],
                     [best_loc.speed_accuracy],
                     [best_loc.bearing_accuracy],
                     [best_loc.location_provider],
                 ]
                 )
             )
    )


def apim_location_to_pyarrow(loc: api_m.RedvoxPacketM.Sensors.Location) -> pa.Table:
    """
    :param loc: location sensor to convert to pyarrow table
    :return: pyarrow table representation of location data
    """
    timestamps = loc.timestamps.timestamps
    gps_timestamps = loc.timestamps_gps.timestamps
    lat_samples = loc.latitude_samples.values
    lon_samples = loc.longitude_samples.values
    alt_samples = loc.altitude_samples.values
    spd_samples = loc.speed_samples.values
    bear_samples = loc.bearing_samples.values
    hor_acc_samples = loc.horizontal_accuracy_samples.values
    vert_acc_samples = loc.vertical_accuracy_samples.values
    spd_acc_samples = loc.speed_accuracy_samples.values
    bear_acc_samples = loc.bearing_accuracy_samples.values
    loc_prov_samples = loc.location_providers
    data_for_df = [[], [], [], [], [], [], [], [], [], [], [], [], []]
    for i in range(len(timestamps)):
        data_for_df[0].append(timestamps[i])
        data_for_df[1].append(timestamps[i])
        data_for_df[2].append(np.nan if len(gps_timestamps) <= i else gps_timestamps[i])
        data_for_df[3].append(lat_samples[i])
        data_for_df[4].append(lon_samples[i])
        data_for_df[5].append(np.nan if len(alt_samples) <= i else alt_samples[i])
        data_for_df[6].append(np.nan if len(spd_samples) <= i else spd_samples[i])
        data_for_df[7].append(np.nan if len(bear_samples) <= i else bear_samples[i])
        data_for_df[8].append(np.nan if len(hor_acc_samples) <= i else hor_acc_samples[i])
        data_for_df[9].append(np.nan if len(vert_acc_samples) <= i else vert_acc_samples[i])
        data_for_df[10].append(np.nan if len(spd_acc_samples) <= i else spd_acc_samples[i])
        data_for_df[11].append(np.nan if len(bear_acc_samples) <= i else bear_acc_samples[i])
        data_for_df[12].append(api_m.RedvoxPacketM.Sensors.Location.LocationProvider.UNKNOWN
                               if len(loc_prov_samples) <= i else loc_prov_samples[i])
    return pa.Table.from_pydict(dict(zip(LOCATION_COLUMNS, data_for_df)))


def apim_health_to_pyarrow(metrics: api_m.RedvoxPacketM.StationInformation.StationMetrics) -> pa.Table:
    """
    :param metrics: station metrics to convert to pyarrow table
    :return: pyarrow table representation of station metrics data
    """
    timestamps = metrics.timestamps.timestamps
    bat_samples = metrics.battery.values
    bat_cur_samples = metrics.battery_current.values
    temp_samples = metrics.temperature.values
    net_samples = metrics.network_type
    net_str_samples = metrics.network_strength.values
    pow_samples = metrics.power_state
    avail_ram_samples = metrics.available_ram.values
    avail_disk_samples = metrics.available_disk.values
    cell_samples = metrics.cell_service_state
    cpu_util_samples = metrics.cpu_utilization.values
    wake_lock_samples = metrics.wifi_wake_lock
    screen_state_samples = metrics.screen_state
    screen_bright_samples = metrics.screen_brightness.values
    data_for_df = [], [], [], [], [], [], [], [], [], [], [], [], [], [], []
    for i in range(len(timestamps)):
        data_for_df[0].append(timestamps[i])
        data_for_df[1].append(timestamps[i])
        data_for_df[2].append(np.nan if len(bat_samples) < i + 1 else bat_samples[i])
        data_for_df[3].append(np.nan if len(bat_cur_samples) < i + 1 else bat_cur_samples[i])
        data_for_df[4].append(np.nan if len(temp_samples) < i + 1 else temp_samples[i])
        data_for_df[5].append(api_m.RedvoxPacketM.StationInformation.StationMetrics.NetworkType.UNKNOWN_NETWORK
                              if len(net_samples) < i + 1 else net_samples[i])
        data_for_df[6].append(np.nan if len(net_str_samples) < i + 1 else net_str_samples[i])
        data_for_df[7].append(api_m.RedvoxPacketM.StationInformation.StationMetrics.PowerState.UNKNOWN_POWER_STATE
                              if len(pow_samples) < i + 1 else pow_samples[i])
        data_for_df[8].append(np.nan if len(avail_ram_samples) < i + 1 else avail_ram_samples[i])
        data_for_df[9].append(np.nan if len(avail_disk_samples) < i + 1 else avail_disk_samples[i])
        data_for_df[10].append(api_m.RedvoxPacketM.StationInformation.StationMetrics.CellServiceState.UNKNOWN
                               if len(cell_samples) < i + 1 else cell_samples[i])
        data_for_df[11].append(np.nan if len(cpu_util_samples) < i + 1 else cpu_util_samples[i])
        data_for_df[12].append(api_m.RedvoxPacketM.StationInformation.StationMetrics.WifiWakeLock.NONE
                               if len(wake_lock_samples) < i + 1 else wake_lock_samples[i])
        data_for_df[13].append(api_m.RedvoxPacketM.StationInformation.StationMetrics.ScreenState.UNKNOWN_SCREEN_STATE
                               if len(screen_state_samples) < i + 1 else screen_state_samples[i])
        data_for_df[14].append(np.nan if len(screen_bright_samples) < i + 1 else screen_bright_samples[i])
    return pa.Table.from_pydict(dict(zip(STATION_HEALTH_COLUMNS, data_for_df)))
