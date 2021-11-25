"""
This module loads sensor data from Redvox packets
"""

from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np

# noinspection Mypy
import pandas as pd

import redvox.api1000.proto.redvox_api_m_pb2 as api_m
from redvox.api1000.wrapped_redvox_packet.station_information import (
    NetworkType,
    PowerState,
    CellServiceState,
    WifiWakeLock,
    ScreenState
)
from redvox.common.stats_helper import StatsContainer
from redvox.common import date_time_utils as dtu
from redvox.common import gap_and_pad_utils_old as gpu
from redvox.common.sensor_data_old import SensorType, SensorData, AudioSensor, CompressedAudioSensor,\
    ImageSensor, LocationSensor, BestLocationSensor, StationHealthSensor

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


def __fill_data_array(input_array: List, num_expected_values: int,
                      default_value: Union[float, int] = np.nan) -> np.array:
    """
    creates a new array filled with [default value] to replace missing values from input_array
    or returns the first [num_expected_values] from input_array

    :param input_array: array of values to take from
    :param num_expected_values: number of expected values to take
    :param default_value: value to use if input_array is shorter than expected
    :return: array of num_expected_values in length
    """
    if len(input_array) < 1:
        return np.full(num_expected_values, default_value)
    elif len(input_array) != num_expected_values:
        return [default_value if len(input_array) < i + 1 else input_array[i] for i in range(num_expected_values)]
    return input_array


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


def get_empty_sensor_data(
        name: str, sensor_type: SensorType = SensorType.UNKNOWN_SENSOR
) -> SensorData:
    """
    create a sensor data object with no data

    :param name: name of the sensor
    :param sensor_type: type of the sensor to create, default SensorType.UNKNOWN_SENSOR
    :return: empty sensor
    """
    return SensorData(name, pd.DataFrame([], columns=["timestamps"]), sensor_type)


def get_sensor_description(sensor: Sensor) -> str:
    """
    read the sensor's description from the sensor

    :param sensor: the sensor to read the description from
    :return: the sensor's description
    """
    return sensor.sensor_description


def get_sensor_description_list(
        packets: List[api_m.RedvoxPacketM], sensor_type: SensorType
) -> Optional[str]:
    """
    read the sensor_type sensor's description from a list of packets

    :param packets: the list of packets to read from
    :param sensor_type: the SensorType of the sensor to read the description of
    :return: the sensor_type sensor's description
    """

    field_name: str = __SENSOR_TYPE_TO_FIELD_NAME[sensor_type]
    sensor_fn: Optional[
        Callable[[api_m.RedvoxPacketM], Sensor]
    ] = __SENSOR_TYPE_TO_SENSOR_FN[sensor_type]
    for packet in packets:
        if __has_sensor(packet, field_name) and sensor_fn is not None:
            return sensor_fn(packet).sensor_description

    return None


def get_sample_statistics(data_df: pd.DataFrame) -> Tuple[float, float, float]:
    """
    calculate the sample rate, interval and interval std dev using the timestamps in the dataframe

    :param data_df: the dataframe containing timestamps to calculate statistics from
    :return: a Tuple containing the sample rate, interval and interval std dev
    """
    sample_interval: float
    sample_interval_std: float
    if data_df["timestamps"].size > 1:
        sample_interval = dtu.microseconds_to_seconds(
            float(np.mean(np.diff(data_df["timestamps"])))
        )
        sample_interval_std = dtu.microseconds_to_seconds(
            float(np.std(np.diff(data_df["timestamps"])))
        )
    else:
        sample_interval = np.nan
        sample_interval_std = np.nan
    return 1.0 / sample_interval, sample_interval, sample_interval_std


def read_apim_xyz_sensor(
        sensor: api_m.RedvoxPacketM.Sensors.Xyz, column_id: str
) -> pd.DataFrame:
    """
    read a sensor that has xyz data channels from an api M data packet
    raises Attribute Error if sensor does not contain xyz channels

    :param sensor: the xyz api M sensor to read
    :param column_id: string, used to name the columns
    :return: Dataframe representing the data in the sensor
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
        return pd.DataFrame(
            np.transpose(
                [
                    timestamps,
                    timestamps,
                    np.array(sensor.x_samples.values),
                    np.array(sensor.y_samples.values),
                    np.array(sensor.z_samples.values),
                ]
            ),
            columns=columns,
        )
    except AttributeError:
        raise


def load_apim_xyz_sensor_from_list(
        sensor_type: SensorType,
        data: List[List[float]],
        gaps: List[Tuple[float, float]],
        column_name: str,
        description: str,
        sample_interval_micros: float,
) -> Optional[SensorData]:
    """
    create a three channel sensor of sensor_type with the column name, description, and data given.

    :param sensor_type: the SensorType of sensor to create
    :param data: the list of data to be added; requires timestamps to be the first list
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :param column_name: the name of the columns that contain the data
    :param description: the description of the sensor
    :param sample_interval_micros: known sample interval in microseconds
    :return: SensorData object or None if no data
    """
    if len(data[0]) > 0:
        data_df: pd.DataFrame = pd.DataFrame(
            np.transpose([data[0], data[0], data[1], data[2], data[3]]),
            columns=[
                "timestamps",
                "unaltered_timestamps",
                f"{column_name}_x",
                f"{column_name}_y",
                f"{column_name}_z",
            ],
        )
        return SensorData(
            description,
            gpu.fill_gaps(data_df, gaps, sample_interval_micros, True),
            sensor_type,
            calculate_stats=True,
        )
    return None


def read_apim_single_sensor(
        sensor: api_m.RedvoxPacketM.Sensors.Single, column_id: str
) -> pd.DataFrame:
    """
    read a sensor that has a single data channel from an api M data packet
    raises Attribute Error if sensor does not contain exactly one data channel

    :param sensor: the single channel api M sensor to read
    :param column_id: string, used to name the columns
    :return: Dataframe representing the data in the sensor
    """
    timestamps: np.ndarray = np.array(sensor.timestamps.timestamps)
    try:
        columns: List[str] = ["timestamps", "unaltered_timestamps", column_id]
        return pd.DataFrame(
            np.transpose([timestamps, timestamps, np.array(sensor.samples.values)]),
            columns=columns,
        )
    except AttributeError:
        raise


def load_apim_single_sensor_from_list(
        sensor_type: SensorType,
        timestamps: List[float],
        data: List[float],
        gaps: List[Tuple[float, float]],
        column_name: str,
        description: str,
        sample_interval_micros: float,
) -> Optional[SensorData]:
    """
    Create a single channel sensor of sensor_type with the column name, timestamps, data, and description

    :param sensor_type: the SensorType of sensor to create
    :param timestamps: the timestamps of the data
    :param data: the list of data to be added
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :param column_name: the name of the columns that contain the data
    :param description: the description of the sensor
    :param sample_interval_micros: known sample interval in microseconds
    :return:
    """
    if len(timestamps) > 0:
        data_df: pd.DataFrame = pd.DataFrame(
            np.transpose([timestamps, timestamps, data]),
            columns=["timestamps", "unaltered_timestamps", column_name],
        )
        return SensorData(
            description,
            gpu.fill_gaps(data_df, gaps, sample_interval_micros, True),
            sensor_type,
            calculate_stats=True,
        )
    return None


def load_apim_audio(packet: api_m.RedvoxPacketM) -> Optional[AudioSensor]:
    """
    load audio data from a single redvox packet

    :param packet: packet with data to load
    :return: audio sensor data if it exists, None otherwise
    """
    if __has_sensor(packet, __AUDIO_FIELD_NAME):
        audio_sensor: api_m.RedvoxPacketM.Sensors.Audio = packet.sensors.audio

        timestamps: np.ndarray = gpu.calc_evenly_sampled_timestamps(
            audio_sensor.first_sample_timestamp,
            len(audio_sensor.samples.values),
            dtu.seconds_to_microseconds(1.0 / audio_sensor.sample_rate),
        )

        return AudioSensor(
            audio_sensor.sensor_description,
            pd.DataFrame(
                np.transpose(
                    [timestamps, timestamps, np.array(audio_sensor.samples.values)]
                ),
                columns=gpu.AUDIO_DF_COLUMNS,
            ),
            audio_sensor.sample_rate,
            1.0 / audio_sensor.sample_rate,
            0.0,
            True,
            )

    return None


def load_apim_audio_from_list(
        packets: List[api_m.RedvoxPacketM],
) -> Tuple[Optional[AudioSensor], List[Tuple[float, float]]]:
    """
    load audio data from a list of redvox packets
    NOTE: This only works because audio sensors in the list should all have the same number of data points.

    :param packets: packets with data to load
    :return: audio sensor data if it exists, None otherwise
    """
    if len(packets) > 0:
        if __has_sensor(
                packets[0], __AUDIO_FIELD_NAME
        ):
            sample_rate_hz: float = packets[0].sensors.audio.sample_rate
            packet_info = [
                (
                    p.sensors.audio.first_sample_timestamp,
                    np.array(p.sensors.audio.samples.values),
                )
                for p in packets
            ]
            gp_result = gpu.fill_audio_gaps(
                packet_info, dtu.seconds_to_microseconds(1 / sample_rate_hz)
            )
            sensor_data = AudioSensor(
                get_sensor_description_list(packets, SensorType.AUDIO),
                gp_result.result_df,
                sample_rate_hz,
                1 / sample_rate_hz,
                0.0,
                True,
                )
            if len(gp_result.errors.get()) > 0:
                sensor_data.errors.extend_error(gp_result.errors)

            return (
                sensor_data,
                gp_result.gaps,
            )
    return None, []


def load_apim_compressed_audio(packet: api_m.RedvoxPacketM) -> Optional[CompressedAudioSensor]:
    """
    load compressed audio data from a single redvox packet

    :param packet: packet with data to load
    :return: compressed audio sensor data if it exists, None otherwise
    """
    if __has_sensor(packet, __COMPRESSED_AUDIO_FIELD_NAME):
        comp_audio: api_m.RedvoxPacketM.Sensors.CompressedAudio = (
            packet.sensors.compressed_audio
        )
        sample_rate_hz = comp_audio.sample_rate
        return CompressedAudioSensor(
            comp_audio.sensor_description,
            pd.DataFrame(
                np.transpose(
                    [
                        comp_audio.first_sample_timestamp,
                        comp_audio.first_sample_timestamp,
                        np.array(list(comp_audio.audio_bytes)),
                        comp_audio.audio_codec,
                    ]
                ),
                columns=COMPRESSED_AUDIO_COLUMNS,
            ),
            sample_rate_hz,
            1 / sample_rate_hz,
            0.0,
            True,
            )
    return None


def load_apim_compressed_audio_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[CompressedAudioSensor]:
    """
    load compressed audio data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: compressed audio sensor data if it exists, None otherwise
    """
    data_list = [[], [], []]
    for packet in packets:
        if __has_sensor(packet, __COMPRESSED_AUDIO_FIELD_NAME):
            comp_audio = packet.sensors.compressed_audio
            data_list[0].append(comp_audio.first_sample_timestamp)
            data_list[1].append(comp_audio.audio_bytes)
            data_list[2].append(comp_audio.audio_codec)

    if len(data_list[0]) > 0:
        data_df = gpu.fill_gaps(
            pd.DataFrame(
                np.transpose([data_list[0], data_list[0], data_list[1], data_list[2]]),
                columns=COMPRESSED_AUDIO_COLUMNS,
            ),
            gaps,
            __packet_duration_us(packets[0]),
            True,
        )
        data_df["audio_codec"] = [d for d in data_df["audio_codec"]]
        sample_rate_hz = packets[0].sensors.compressed_audio.sample_rate
        return CompressedAudioSensor(
            get_sensor_description_list(packets, SensorType.COMPRESSED_AUDIO),
            data_df,
            sample_rate_hz,
            1 / sample_rate_hz,
            0.0,
            True,
            )
    return None


def load_apim_image(packet: api_m.RedvoxPacketM) -> Optional[ImageSensor]:
    """
    load image data from a single redvox packet

    :param packet: packet with data to load
    :return: image sensor data if it exists, None otherwise
    """
    if __has_sensor(packet, __IMAGE_FIELD_NAME):
        image_sensor: api_m.RedvoxPacketM.Sensors.Image = packet.sensors.image
        timestamps = image_sensor.timestamps.timestamps
        codecs = np.full(len(timestamps), image_sensor.image_codec)
        data_df = pd.DataFrame(
            np.transpose([timestamps, timestamps, image_sensor.samples, codecs]),
            columns=IMAGE_COLUMNS,
        )
        data_df["image_codec"] = [d for d in data_df["image_codec"]]
        # image is collected 1 per packet or 1 per second
        sample_rate, sample_interval, sample_interval_std = __stats_for_sensor_per_packet_per_second(
            1, __packet_duration_s(packet), timestamps
        )
        return ImageSensor(
            image_sensor.sensor_description,
            data_df,
            sample_rate,
            sample_interval,
            sample_interval_std,
            True,
        )
    return None


def load_apim_image_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[ImageSensor]:
    """
    load image data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: image sensor data if it exists, None otherwise
    """
    data_list: List[List[float]] = [[], [], []]
    for packet in packets:
        if __has_sensor(packet, __IMAGE_FIELD_NAME):
            image_sensor = packet.sensors.image

            data_list[0].extend(image_sensor.timestamps.timestamps)
            data_list[1].extend(image_sensor.samples)
            data_list[2].extend(
                [
                    image_sensor.image_codec
                    for i in range(len(image_sensor.timestamps.timestamps))
                ]
            )
    if len(data_list[0]) > 0:
        # image is collected 1 per packet or 1 per second
        sample_rate, sample_interval, sample_interval_std = __stats_for_sensor_per_packet_per_second(
            len(packets), __packet_duration_s(packets[0]), data_list[0]
        )
        df = pd.DataFrame(
            np.transpose(
                [data_list[0], data_list[0], data_list[1], data_list[2]]
            ),
            columns=IMAGE_COLUMNS,
        )
        df["timestamps"] = df["timestamps"].astype(float)
        df["unaltered_timestamps"] = df["unaltered_timestamps"].astype(float)
        df["image_codec"] = df["image_codec"].astype(float)
        return ImageSensor(
            get_sensor_description_list(packets, SensorType.IMAGE),
            gpu.fill_gaps(
                df,
                gaps,
                dtu.seconds_to_microseconds(sample_interval),
                True,
            ),
            sample_rate,
            sample_interval,
            sample_interval_std,
            True,
        )
    return None


def __is_only_best_values(loc: api_m.RedvoxPacketM.Sensors.Location) -> bool:
    """
    :return: True if the location does not have data in it and has a last_best_location or overall_best_location
    """
    return len(loc.location_providers) < 1 and (
            loc.HasField("last_best_location") or loc.HasField("overall_best_location")
    )


def load_apim_best_location(packet: api_m.RedvoxPacketM) -> Optional[BestLocationSensor]:
    """
    load best location data from a single redvox packet

    :param packet: packet with data to load
    :return: best location sensor data if it exists, None otherwise
    """
    if __has_sensor(packet, __LOCATION_FIELD_NAME):
        loc: api_m.RedvoxPacketM.Sensors.Location = packet.sensors.location
        if loc.HasField("last_best_location") or loc.HasField("overall_best_location"):
            best_loc: api_m.RedvoxPacketM.Sensors.Location.BestLocation
            if loc.HasField("last_best_location"):
                best_loc = loc.last_best_location
            else:
                best_loc = loc.overall_best_location
            data_df = pd.DataFrame([
                [
                    packet.timing_information.packet_start_mach_timestamp,
                    best_loc.latitude_longitude_timestamp.mach,
                    best_loc.latitude_longitude_timestamp.gps,
                    best_loc.latitude,
                    best_loc.longitude,
                    best_loc.altitude,
                    best_loc.speed,
                    best_loc.bearing,
                    best_loc.horizontal_accuracy,
                    best_loc.vertical_accuracy,
                    best_loc.speed_accuracy,
                    best_loc.bearing_accuracy,
                    best_loc.location_provider,
                ]
            ], columns=LOCATION_COLUMNS)
            sample_rate = 1 / __packet_duration_s(packet)
            return BestLocationSensor(
                loc.sensor_description,
                data_df,
                sample_rate,
                1 / sample_rate,
                np.nan,
                False,
            )
    return None


def load_apim_best_location_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[BestLocationSensor]:
    """
    load best location data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: best location sensor data if it exists, None otherwise
    """
    data_list: List[List[float]] = [[], [], [], [], [], [], [], [], [], [], [], [], []]
    loc_stats = StatsContainer("location_sensor")
    for packet in packets:
        if __has_sensor(packet, __LOCATION_FIELD_NAME):
            loc: api_m.RedvoxPacketM.Sensors.Location = packet.sensors.location
            if loc.HasField("last_best_location") or loc.HasField("overall_best_location"):
                best_loc: api_m.RedvoxPacketM.Sensors.Location.BestLocation
                if loc.HasField("last_best_location"):
                    best_loc = loc.last_best_location
                else:
                    best_loc = loc.overall_best_location
                data_list[0].append(packet.timing_information.packet_start_mach_timestamp)
                data_list[1].append(best_loc.latitude_longitude_timestamp.mach)
                data_list[2].append(best_loc.latitude_longitude_timestamp.gps)
                data_list[3].append(best_loc.latitude)
                data_list[4].append(best_loc.longitude)
                data_list[5].append(best_loc.altitude)
                data_list[6].append(best_loc.speed)
                data_list[7].append(best_loc.bearing)
                data_list[8].append(best_loc.horizontal_accuracy)
                data_list[9].append(best_loc.vertical_accuracy)
                data_list[10].append(best_loc.speed_accuracy)
                data_list[11].append(best_loc.bearing_accuracy)
                data_list[12].append(best_loc.location_provider)
                loc_stats.add(__packet_duration_us(packet), 0, 1)
    if len(data_list[0]) > 0:
        return BestLocationSensor(
            get_sensor_description_list(packets, SensorType.BEST_LOCATION),
            gpu.fill_gaps(
                pd.DataFrame(np.transpose(data_list), columns=LOCATION_COLUMNS),
                gaps,
                loc_stats.mean_of_means(),
                True,
            ),
            calculate_stats=True,
        )
    return None


def load_apim_location(packet: api_m.RedvoxPacketM) -> Optional[LocationSensor]:
    """
    load location data from a single packet

    :param packet: packet with data to load
    :return: location sensor data if it exists, None otherwise
    """
    if __has_sensor(packet, __LOCATION_FIELD_NAME):
        loc: api_m.RedvoxPacketM.Sensors.Location = packet.sensors.location
        timestamps = loc.timestamps.timestamps
        if len(timestamps) > 0:
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
            data_for_df = []
            for i in range(len(timestamps)):
                new_entry = [
                    timestamps[i],
                    timestamps[i],
                    np.nan if len(gps_timestamps) <= i else gps_timestamps[i],
                    lat_samples[i],
                    lon_samples[i],
                    np.nan if len(alt_samples) <= i else alt_samples[i],
                    np.nan if len(spd_samples) <= i else spd_samples[i],
                    np.nan if len(bear_samples) <= i else bear_samples[i],
                    np.nan if len(hor_acc_samples) <= i else hor_acc_samples[i],
                    np.nan if len(vert_acc_samples) <= i else vert_acc_samples[i],
                    np.nan if len(spd_acc_samples) <= i else spd_acc_samples[i],
                    np.nan if len(bear_acc_samples) <= i else bear_acc_samples[i],
                    np.nan if len(loc_prov_samples) <= i else loc_prov_samples[i],
                ]
                data_for_df.append(new_entry)
        else:
            return None
        data_df = pd.DataFrame(data_for_df, columns=LOCATION_COLUMNS)
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return LocationSensor(
            loc.sensor_description,
            data_df,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )
    return None


def load_apim_location_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[LocationSensor]:
    """
    load location data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: location sensor data if it exists, None otherwise
    """
    data_list: List[List[float]] = [[], [], [], [], [], [], [], [], [], [], [], []]
    loc_stats = StatsContainer("location_sensor")
    for packet in packets:
        if __has_sensor(packet, __LOCATION_FIELD_NAME):
            loc: api_m.RedvoxPacketM.Sensors.Location = packet.sensors.location

            num_samples = len(loc.timestamps.timestamps)
            if num_samples > 0:
                samples = loc.timestamps.timestamps
                data_list[0].extend(samples)
                if num_samples == 1:
                    loc_stats.add(
                        __packet_duration_us(packet),
                        0,
                        1,
                    )
                else:
                    loc_stats.add(
                        np.mean(np.diff(samples)),
                        np.std(np.diff(samples)),
                        num_samples - 1,
                        )
                for i in range(num_samples):
                    samples = loc.timestamps_gps.timestamps
                    data_list[1].append(np.nan if len(samples) <= i else samples[i])
                    samples = loc.latitude_samples.values
                    data_list[2].append(samples[i])
                    samples = loc.longitude_samples.values
                    data_list[3].append(samples[i])
                    samples = loc.altitude_samples.values
                    data_list[4].append(
                        np.nan if len(samples) < i + 1 else samples[i]
                    )
                    samples = loc.speed_samples.values
                    data_list[5].append(
                        np.nan if len(samples) < i + 1 else samples[i]
                    )
                    samples = loc.bearing_samples.values
                    data_list[6].append(
                        np.nan if len(samples) < i + 1 else samples[i]
                    )
                    samples = loc.horizontal_accuracy_samples.values
                    data_list[7].append(
                        np.nan if len(samples) < i + 1 else samples[i]
                    )
                    samples = loc.vertical_accuracy_samples.values
                    data_list[8].append(
                        np.nan if len(samples) < i + 1 else samples[i]
                    )
                    samples = loc.speed_accuracy_samples.values
                    data_list[9].append(
                        np.nan if len(samples) < i + 1 else samples[i]
                    )
                    samples = loc.bearing_accuracy_samples.values
                    data_list[10].append(
                        np.nan if len(samples) < i + 1 else samples[i]
                    )
                    samples = list(loc.location_providers)
                    data_list[11].append(
                        api_m.RedvoxPacketM.Sensors.Location.LocationProvider.UNKNOWN
                        if len(samples) < i + 1
                        else samples[i]
                    )
    if len(data_list[0]) > 0:
        data_list.insert(1, data_list[0].copy())
        return LocationSensor(
            get_sensor_description_list(packets, SensorType.LOCATION),
            gpu.fill_gaps(
                pd.DataFrame(np.transpose(data_list), columns=LOCATION_COLUMNS),
                gaps,
                loc_stats.mean_of_means(),
                True,
            ),
            calculate_stats=True,
        )
    return None


def load_single(
        packet: api_m.RedvoxPacketM,
        sensor_type: SensorType,
) -> Optional[SensorData]:
    field_name: str = __SENSOR_TYPE_TO_FIELD_NAME[sensor_type]
    sensor_fn: Optional[
        Callable[[api_m.RedvoxPacketM], Sensor]
    ] = __SENSOR_TYPE_TO_SENSOR_FN[sensor_type]
    if __has_sensor(packet, field_name) and sensor_fn is not None:
        sensor = sensor_fn(packet)
        data_df = read_apim_single_sensor(sensor, field_name)
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            sensor.sensor_description,
            data_df,
            sensor_type,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_single_from_list(
        packets: List[api_m.RedvoxPacketM],
        gaps: List[Tuple[float, float]],
        sensor_type: SensorType,
) -> Optional[SensorData]:
    field_name: str = __SENSOR_TYPE_TO_FIELD_NAME[sensor_type]
    data_list: List[float] = []
    timestamps: List[float] = []
    sensor_stats: StatsContainer = StatsContainer(f"{field_name}_sensor")
    sensor_fn: Optional[
        Callable[[api_m.RedvoxPacketM], Sensor]
    ] = __SENSOR_TYPE_TO_SENSOR_FN[sensor_type]
    for packet in packets:
        if __has_sensor(packet, field_name) and sensor_fn is not None:
            sensor: api_m.RedvoxPacketM.Sensors.Single = sensor_fn(packet)
            data_list.extend(sensor.samples.values)
            ts = sensor.timestamps.timestamps
            timestamps.extend(ts)
            if len(sensor.timestamps.timestamps) == 1:
                sensor_stats.add(__packet_duration_us(packet), 0, 1)
            else:
                sensor_stats.add(np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1)
    if len(data_list) > 0:
        return load_apim_single_sensor_from_list(
            sensor_type,
            timestamps,
            data_list,
            gaps,
            field_name,
            get_sensor_description_list(packets, sensor_type),
            sensor_stats.mean_of_means(),
        )
    return None


def load_apim_pressure(packet: api_m.RedvoxPacketM) -> Optional[SensorData]:
    """
    load pressure data from a single redvox packet

    :param packet: packet with data to load
    :return: pressure sensor data if it exists, None otherwise
    """
    return load_single(packet, SensorType.PRESSURE)


def load_apim_pressure_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load pressure data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: pressure sensor data if it exists, None otherwise
    """
    return load_single_from_list(
        packets,
        gaps,
        SensorType.PRESSURE,
    )


def load_apim_light(packet: api_m.RedvoxPacketM) -> Optional[SensorData]:
    """
    load light data from a single redvox packet

    :param packet: packet with data to load
    :return: light sensor data if it exists, None otherwise
    """
    return load_single(packet, SensorType.LIGHT)


def load_apim_light_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load light data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: light sensor data if it exists, None otherwise
    """
    return load_single_from_list(
        packets,
        gaps,
        SensorType.LIGHT,
    )


def load_apim_proximity(packet: api_m.RedvoxPacketM) -> Optional[SensorData]:
    """
    load proximity data from a single redvox packet

    :param packet: packet with data to load
    :return: proximity sensor data if it exists, None otherwise
    """
    return load_single(packet, SensorType.PROXIMITY)


def load_apim_proximity_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load proximity data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: proximity sensor data if it exists, None otherwise
    """
    return load_single_from_list(
        packets,
        gaps,
        SensorType.PROXIMITY,
    )


def load_apim_ambient_temp(
        packet: api_m.RedvoxPacketM,
) -> Optional[SensorData]:
    """
    load ambient temperature data from a single redvox packet

    :param packet: packet with data to load
    :return: ambient temperature sensor data if it exists, None otherwise
    """
    return load_single(
        packet,
        SensorType.AMBIENT_TEMPERATURE,
    )


def load_apim_ambient_temp_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load ambient temperature data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: ambient temperature sensor data if it exists, None otherwise
    """
    return load_single_from_list(
        packets,
        gaps,
        SensorType.AMBIENT_TEMPERATURE,
    )


def load_apim_rel_humidity(
        packet: api_m.RedvoxPacketM,
) -> Optional[SensorData]:
    """
    load relative humidity data from a single redvox packet

    :param packet: packet with data to load
    :return: relative humidity sensor data if it exists, None otherwise
    """
    return load_single(
        packet,
        SensorType.RELATIVE_HUMIDITY,
    )


def load_apim_rel_humidity_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load relative humidity data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: relative humidity sensor data if it exists, None otherwise
    """
    return load_single_from_list(
        packets,
        gaps,
        SensorType.RELATIVE_HUMIDITY,
    )


def load_xyz(
        packet: api_m.RedvoxPacketM,
        sensor_type: SensorType,
):
    field_name: str = __SENSOR_TYPE_TO_FIELD_NAME[sensor_type]
    sensor_fn: Optional[
        Callable[[api_m.RedvoxPacketM], Sensor]
    ] = __SENSOR_TYPE_TO_SENSOR_FN[sensor_type]
    if __has_sensor(packet, field_name) and sensor_fn is not None:
        sensor = sensor_fn(packet)
        data_df = read_apim_xyz_sensor(sensor, field_name)
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            sensor.sensor_description,
            data_df,
            sensor_type,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_xyz_from_list(
        packets: List[api_m.RedvoxPacketM],
        gaps: List[Tuple[float, float]],
        sensor_type: SensorType,
) -> Optional[SensorData]:
    field_name: str = __SENSOR_TYPE_TO_FIELD_NAME[sensor_type]
    data_list: List[List[float]] = [[], [], [], []]
    sensor_stats: StatsContainer = StatsContainer(f"{field_name}_sensor")
    packet: api_m.RedvoxPacketM
    sensor_fn: Optional[
        Callable[[api_m.RedvoxPacketM], Sensor]
    ] = __SENSOR_TYPE_TO_SENSOR_FN[sensor_type]
    for packet in packets:
        if __has_sensor(packet, field_name) and sensor_fn is not None:
            sensor: api_m.RedvoxPacketM.Sensors.Xyz = sensor_fn(packet)

            ts = sensor.timestamps.timestamps
            data_list[0].extend(ts)
            data_list[1].extend(sensor.x_samples.values)
            data_list[2].extend(sensor.y_samples.values)
            data_list[3].extend(sensor.z_samples.values)
            if len(sensor.timestamps.timestamps) == 1:
                sensor_stats.add(__packet_duration_us(packet), 0, 1)
            else:
                sensor_stats.add(np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1)
    if len(data_list[0]) > 0:
        return load_apim_xyz_sensor_from_list(
            sensor_type,
            data_list,
            gaps,
            field_name,
            get_sensor_description_list(packets, sensor_type),
            sensor_stats.mean_of_means(),
        )
    return None


def load_apim_accelerometer(
        packet: api_m.RedvoxPacketM,
) -> Optional[SensorData]:
    """
    load accelerometer data from a single redvox packet

    :param packet: packet with data to load
    :return: accelerometer sensor data if it exists, None otherwise
    """
    return load_xyz(
        packet,
        SensorType.ACCELEROMETER,
    )


def load_apim_accelerometer_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load accelerometer data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: accelerometer sensor data if it exists, None otherwise
    """
    return load_xyz_from_list(
        packets,
        gaps,
        SensorType.ACCELEROMETER,
    )


def load_apim_magnetometer(
        packet: api_m.RedvoxPacketM,
) -> Optional[SensorData]:
    """
    load magnetometer data from a single redvox packet

    :param packet: packet with data to load
    :return: magnetometer sensor data if it exists, None otherwise
    """
    return load_xyz(
        packet,
        SensorType.MAGNETOMETER,
    )


def load_apim_magnetometer_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load magnetometer data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: magnetometer sensor data if it exists, None otherwise
    """
    return load_xyz_from_list(
        packets,
        gaps,
        SensorType.MAGNETOMETER,
    )


def load_apim_gyroscope(packet: api_m.RedvoxPacketM) -> Optional[SensorData]:
    """
    load gyroscope data from a single redvox packet

    :param packet: packet with data to load
    :return: gyroscope sensor data if it exists, None otherwise
    """
    return load_xyz(packet, SensorType.GYROSCOPE)


def load_apim_gyroscope_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load gyroscope data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: gyroscope sensor data if it exists, None otherwise
    """
    return load_xyz_from_list(
        packets,
        gaps,
        SensorType.GYROSCOPE,
    )


def load_apim_gravity(packet: api_m.RedvoxPacketM) -> Optional[SensorData]:
    """
    load gravity data from a single redvox packet

    :param packet: packet with data to load
    :return: gravity sensor data if it exists, None otherwise
    """
    return load_xyz(packet, SensorType.GRAVITY)


def load_apim_gravity_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load gravity data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: gravity sensor data if it exists, None otherwise
    """
    return load_xyz_from_list(
        packets,
        gaps,
        SensorType.GRAVITY,
    )


def load_apim_orientation(packet: api_m.RedvoxPacketM) -> Optional[SensorData]:
    """
    load orientation data from a single redvox packet

    :param packet: packet with data to load
    :return: orientation sensor data if it exists, None otherwise
    """
    return load_xyz(
        packet,
        SensorType.ORIENTATION,
    )


def load_apim_orientation_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load orientation data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: orientation sensor data if it exists, None otherwise
    """
    return load_xyz_from_list(
        packets,
        gaps,
        SensorType.ORIENTATION,
    )


def load_apim_linear_accel(
        packet: api_m.RedvoxPacketM,
) -> Optional[SensorData]:
    """
    load linear acceleration data from a single redvox packet

    :param packet: packet with data to load
    :return: linear acceleration sensor data if it exists, None otherwise
    """
    return load_xyz(
        packet,
        SensorType.LINEAR_ACCELERATION,
    )


def load_apim_linear_accel_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load linear acceleration data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: linear acceleration sensor data if it exists, None otherwise
    """
    return load_xyz_from_list(
        packets,
        gaps,
        SensorType.LINEAR_ACCELERATION,
    )


def load_apim_rotation_vector(
        packet: api_m.RedvoxPacketM,
) -> Optional[SensorData]:
    """
    load rotation vector data from a single redvox packet

    :param packet: packet with data to load
    :return: rotation vector sensor data if it exists, None otherwise
    """
    return load_xyz(
        packet,
        SensorType.ROTATION_VECTOR,
    )


def load_apim_rotation_vector_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load rotation vector data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: rotation vector sensor data if it exists, None otherwise
    """
    return load_xyz_from_list(
        packets,
        gaps,
        SensorType.ROTATION_VECTOR,
    )


def load_apim_health(packet: api_m.RedvoxPacketM) -> Optional[StationHealthSensor]:
    """
    load station health data from a single redvox packet

    :param packet: packet with data to load
    :return: station health data if it exists, None otherwise
    """
    metrics: api_m.RedvoxPacketM.StationInformation.StationMetrics = (
        packet.station_information.station_metrics
    )
    timestamps = metrics.timestamps.timestamps
    if len(timestamps) > 0:
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
        data_for_df = []
        for i in range(len(timestamps)):
            new_entry = [
                timestamps[i],
                timestamps[i],
                np.nan if len(bat_samples) < i + 1 else bat_samples[i],
                np.nan if len(bat_cur_samples) < i + 1 else bat_cur_samples[i],
                np.nan if len(temp_samples) < i + 1 else temp_samples[i],
                np.nan if len(net_samples) < i + 1 else net_samples[i],
                np.nan if len(net_str_samples) < i + 1 else net_str_samples[i],
                np.nan if len(pow_samples) < i + 1 else pow_samples[i],
                np.nan if len(avail_ram_samples) < i + 1 else avail_ram_samples[i],
                np.nan if len(avail_disk_samples) < i + 1 else avail_disk_samples[i],
                np.nan if len(cell_samples) < i + 1 else cell_samples[i],
                np.nan if len(cpu_util_samples) < i + 1 else cpu_util_samples[i],
                np.nan if len(wake_lock_samples) < i + 1 else wake_lock_samples[i],
                np.nan if len(screen_state_samples) < i + 1 else screen_state_samples[i],
                np.nan if len(screen_bright_samples) < i + 1 else screen_bright_samples[i],
            ]
            data_for_df.append(new_entry)
        data_df = pd.DataFrame(
            data_for_df,
            columns=STATION_HEALTH_COLUMNS,
        )
        # health is collected 1 per packet or 1 per second
        sample_rate, sample_interval, sample_interval_std = __stats_for_sensor_per_packet_per_second(
            1, __packet_duration_s(packet), timestamps
        )
        return StationHealthSensor(
            "station health",
            data_df,
            sample_rate,
            sample_interval,
            sample_interval_std,
            True
            )
    return None


def load_apim_health_from_list(
        packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[StationHealthSensor]:
    """
    load station health data from a list of redvox packets

    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: station health sensor data if it exists, None otherwise
    """
    data_list: List[List[float]] = [[], [], [], [], [], [], [], [], [], [], [], [], [], []]
    for packet in packets:
        metrics = packet.station_information.station_metrics
        timestamps = metrics.timestamps.timestamps
        num_samples = len(timestamps)
        if num_samples > 0:
            data_list[0].extend(timestamps)
            samples = metrics.battery.values
            data_list[1].extend(__fill_data_array(samples, num_samples, np.nan))
            samples = metrics.battery_current.values
            data_list[2].extend(__fill_data_array(samples, num_samples, np.nan))
            samples = metrics.temperature.values
            data_list[3].extend(__fill_data_array(samples, num_samples, np.nan))
            samples = metrics.network_type
            data_list[4].extend(__fill_data_array(samples, num_samples, NetworkType["UNKNOWN_NETWORK"].value))
            samples = metrics.network_strength.values
            data_list[5].extend(__fill_data_array(samples, num_samples, np.nan))
            samples = metrics.power_state
            data_list[6].extend(__fill_data_array(samples, num_samples, PowerState["UNKNOWN_POWER_STATE"].value))
            samples = metrics.available_ram.values
            data_list[7].extend(__fill_data_array(samples, num_samples, np.nan))
            samples = metrics.available_disk.values
            data_list[8].extend(__fill_data_array(samples, num_samples, np.nan))
            samples = metrics.cell_service_state
            data_list[9].extend(__fill_data_array(samples, num_samples, CellServiceState["UNKNOWN"].value))
            samples = metrics.cpu_utilization.values
            data_list[10].extend(__fill_data_array(samples, num_samples, np.nan))
            samples = metrics.wifi_wake_lock
            data_list[11].extend(__fill_data_array(samples, num_samples, WifiWakeLock["OTHER"].value))
            samples = metrics.screen_state
            data_list[12].extend(__fill_data_array(samples, num_samples, ScreenState["UNKNOWN_SCREEN_STATE"].value))
            samples = metrics.screen_brightness.values
            data_list[13].extend(__fill_data_array(samples, num_samples, np.nan))
    if len(data_list[0]) > 0:
        data_list.insert(1, data_list[0].copy())
        # health is collected 1 per packet or 1 per second
        sample_rate, sample_interval, sample_interval_std = __stats_for_sensor_per_packet_per_second(
            len(packets), __packet_duration_s(packets[0]), data_list[0]
        )
        df = gpu.fill_gaps(
            pd.DataFrame(
                np.transpose(data_list),
                columns=STATION_HEALTH_COLUMNS,
            ),
            gaps,
            dtu.seconds_to_microseconds(sample_interval),
            True,
        )
        return StationHealthSensor(
            "station health",
            df,
            sample_rate,
            sample_interval,
            sample_interval_std,
            True
        )
    return None
