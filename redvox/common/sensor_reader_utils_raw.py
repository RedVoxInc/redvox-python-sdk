"""
This module loads sensor data from Redvox packets
"""

from typing import List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from redvox.common.stats_helper import StatsContainer
from redvox.common import date_time_utils as dtu
from redvox.common import gap_and_pad_utils as gpu
from redvox.common.sensor_data import SensorType, SensorData
from redvox.api1000.wrapped_redvox_packet.sensors import (
    xyz,
    single,
    audio,
    image,
    location,
)
from redvox.api1000.wrapped_redvox_packet.station_information import (
    NetworkType,
    CellServiceState,
    PowerState,
)
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM

import redvox.api1000.proto.redvox_api_m_pb2 as api_m

# Dataframe column definitions
COMPRESSED_AUDIO_COLUMNS = [
    "timestamps",
    "unaltered_timestamps",
    "compressed_audio",
    "audio_codec",
]
IMAGE_COLUMNS = ["timestamps", "unaltered_timestamps", "image", "image_codec"]
LOCATION_COLUMNS = [
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


def __has_sensor(
    data: Union[api_m.RedvoxPacketM, api_m.RedvoxPacketM.Sensors], field_name: str
) -> bool:
    if isinstance(data, api_m.RedvoxPacketM):
        return data.sensors.HasField(field_name)

    if isinstance(data, api_m.RedvoxPacketM.Sensors):
        return data.HasField(field_name)

    return False


def __packet_duration_s(packet: api_m.RedvoxPacketM) -> float:
    return len(packet.sensors.audio.samples.values) / packet.sensors.audio.sample_rate


def __packet_duration_us(packet: api_m.RedvoxPacketM) -> float:
    return __packet_duration_s(packet) * 1_000_000.0


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


def get_sensor_description(
    sensor: Union[
        api_m.RedvoxPacketM.Sensors.Xyz,
        api_m.RedvoxPacketM.Sensors.Single,
        api_m.RedvoxPacketM.Sensors.Audio,
        api_m.RedvoxPacketM.Sensors.Image,
        api_m.RedvoxPacketM.Sensors.Location,
    ]
) -> str:
    """
    read the sensor's description from the sensor
    :param sensor: the sensor to read the description from
    :return: the sensor's description
    """
    return sensor.sensor_description


def get_sensor_description_list(
    packets: List[api_m.RedvoxPacketM], sensor_type: SensorType
) -> str:
    """
    read the sensor_type sensor's description from a list of packets
    :param packets: the list of packets to read from
    :param sensor_type: the SensorType of the sensor to read the description of
    :return: the sensor_type sensor's description
    """

    for packet in packets:
        if sensor_type == SensorType.AUDIO and __has_sensor(packet, __AUDIO_FIELD_NAME):
            return packet.sensors.audio.sensor_description
        if sensor_type == SensorType.IMAGE and __has_sensor(packet, __IMAGE_FIELD_NAME):
            return packet.sensors.image.sensor_description
        if sensor_type == SensorType.LOCATION and __has_sensor(
            packet, __LOCATION_FIELD_NAME
        ):
            return packet.sensors.location.sensor_description
        if sensor_type == SensorType.PRESSURE and __has_sensor(
            packet, __PRESSURE_FIELD_NAME
        ):
            return packet.sensors.pressure.sensor_description
        if sensor_type == SensorType.ACCELEROMETER and __has_sensor(
            packet, __ACCELEROMETER_FIELD_NAME
        ):
            return packet.sensors.accelerometer.sensor_description
        if sensor_type == SensorType.AMBIENT_TEMPERATURE and __has_sensor(
            packet, __AMBIENT_TEMPERATURE_FIELD_NAME
        ):
            return packet.sensors.ambient_temperature.sensor_description
        if sensor_type == SensorType.COMPRESSED_AUDIO and __has_sensor(
            packet, __COMPRESSED_AUDIO_FIELD_NAME
        ):
            return packet.sensors.compressed_audio.sensor_description
        if sensor_type == SensorType.GRAVITY and __has_sensor(
            packet, __GRAVITY_FIELD_NAME
        ):
            return packet.sensors.gravity.sensor_description
        if sensor_type == SensorType.GYROSCOPE and __has_sensor(
            packet, __GYROSCOPE_FIELD_NAME
        ):
            return packet.sensors.gyroscope.sensor_description
        if sensor_type == SensorType.LIGHT and __has_sensor(packet, __LIGHT_FIELD_NAME):
            return packet.sensors.light.sensor_description
        if sensor_type == SensorType.LINEAR_ACCELERATION and __has_sensor(
            packet, __LINEAR_ACCELERATION_FIELD_NAME
        ):
            return packet.sensors.linear_acceleration.sensor_description
        if sensor_type == SensorType.MAGNETOMETER and __has_sensor(
            packet, __MAGNETOMETER_FIELD_NAME
        ):
            return packet.sensors.magnetometer.sensor_description
        if sensor_type == SensorType.ORIENTATION and __has_sensor(
            packet, __ORIENTATION_FIELD_NAME
        ):
            return packet.sensors.orientation.sensor_description
        if sensor_type == SensorType.PROXIMITY and __has_sensor(
            packet, __PROXIMITY_FIELD_NAME
        ):
            return packet.sensors.proximity.sensor_description
        if sensor_type == SensorType.RELATIVE_HUMIDITY and __has_sensor(
            packet, __RELATIVE_HUMIDITY_FIELD_NAME
        ):
            return packet.sensors.relative_humidity.sensor_description
        if sensor_type == SensorType.ROTATION_VECTOR and __has_sensor(
            packet, __ROTATION_VECTOR
        ):
            return packet.sensors.rotation_vector.sensor_description


def get_sample_statistics(data_df: pd.DataFrame) -> Tuple[float, float, float]:
    """
    calculate the sample rate, interval and interval std dev using the timestamps in the dataframe
    :param data_df: the dataframe containing timestamps to calculate statistics from
    :return: a Tuple containing the sample rate, interval and interval std dev
    """
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
    return 1 / sample_interval, sample_interval, sample_interval_std


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
        columns = [
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


def load_apim_xyz_sensor(
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
        data_df = pd.DataFrame(
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
            gpu.fill_gaps(data_df, gaps, sample_interval_micros),
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
        columns = ["timestamps", "unaltered_timestamps", column_id]
        return pd.DataFrame(
            np.transpose([timestamps, timestamps, np.array(sensor.samples.values)]),
            columns=columns,
        )
    except AttributeError:
        raise


def load_apim_single_sensor(
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
        data_df = pd.DataFrame(
            np.transpose([timestamps, timestamps, data]),
            columns=["timestamps", "unaltered_timestamps", column_name],
        )
        return SensorData(
            description,
            gpu.fill_gaps(data_df, gaps, sample_interval_micros),
            sensor_type,
            calculate_stats=True,
        )
    return None


def load_apim_audio(packet: api_m.RedvoxPacketM) -> Optional[SensorData]:
    """
    load audio data from a single wrapped packet
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

        return SensorData(
            audio_sensor.sensor_description,
            pd.DataFrame(
                np.transpose(
                    [timestamps, timestamps, np.array(audio_sensor.samples.values)]
                ),
                columns=gpu.AUDIO_DF_COLUMNS,
            ),
            SensorType.AUDIO,
            audio_sensor.sample_rate,
            1.0 / audio_sensor.sample_rate,
            0.0,
            True,
        )

    return None


def load_apim_audio_from_list(
    packets: List[api_m.RedvoxPacketM],
) -> (Optional[SensorData], List[Tuple[float, float]]):
    """
    load audio data from a list of wrapped packets
    NOTE: This only works because audio sensors in the list should all have the same number of data points.
    :param packets: packets with data to load
    :return: audio sensor data if it exists, None otherwise
    """
    if len(packets) > 0:
        if __has_sensor(
            packets[0], __AUDIO_FIELD_NAME
        ):  # and packets[0].get_sensors().validate_audio():
            try:
                sample_rate_hz = packets[0].sensors.audio.sample_rate
                packet_info = [
                    (
                        p.sensors.audio.first_sample_timestamp,
                        np.array(p.sensors.audio.samples.values),
                        len(p.sensors.audio.samples.values),
                    )
                    for p in packets
                ]
                df, gaps = gpu.fill_audio_gaps(
                    packet_info, dtu.seconds_to_microseconds(1 / sample_rate_hz)
                )

                return (
                    SensorData(
                        get_sensor_description_list(packets, SensorType.AUDIO),
                        df,
                        SensorType.AUDIO,
                        sample_rate_hz,
                        1 / sample_rate_hz,
                        0.0,
                        True,
                    ),
                    gaps,
                )
            except ValueError as error:
                print(
                    "Error occurred while loading audio data for station "
                    f"{packets[0].get_station_information().get_id()}.\n"
                    f"Original error message: {error}"
                )
    return None, []


def load_apim_compressed_audio(packet: api_m.RedvoxPacketM) -> Optional[SensorData]:
    """
    load compressed audio data from a single wrapped packet
    :param packet: packet with data to load
    :return: compressed audio sensor data if it exists, None otherwise
    """
    if __has_sensor(packet, __COMPRESSED_AUDIO_FIELD_NAME):
        comp_audio: api_m.RedvoxPacketM.Sensors.CompressedAudio = (
            packet.sensors.compressed_audio
        )
        sample_rate_hz = comp_audio.sample_rate
        return SensorData(
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
            SensorType.COMPRESSED_AUDIO,
            sample_rate_hz,
            1 / sample_rate_hz,
            0.0,
            True,
        )
    return None


def load_apim_compressed_audio_from_list(
    packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load compressed audio data from a list of wrapped packets
    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: compressed audio sensor data if it exists, None otherwise
    """
    data_list = [[], [], []]
    for packet in packets:
        if __has_sensor(packet, __COMPRESSED_AUDIO_FIELD_NAME):
            comp_audio = packet.sensors.compressed_audio
            data_list[0].append(comp_audio.first_sample_timestamp)
            data_list[1].append(np.array(list(comp_audio.audio_bytes)))
            data_list[2].append(comp_audio.audio_codec)

    if len(data_list[0]) > 0:
        data_df = gpu.fill_gaps(
            pd.DataFrame(
                np.transpose([data_list[0], data_list[0], data_list[1], data_list[2]]),
                columns=COMPRESSED_AUDIO_COLUMNS,
            ),
            gaps,
            __packet_duration_us(packets[0]),
        )
        data_df["audio_codec"] = [d for d in data_df["audio_codec"]]
        sample_rate_hz = packets[0].sensors.compressed_audio.sample_rate
        return SensorData(
            get_sensor_description_list(packets, SensorType.COMPRESSED_AUDIO),
            data_df,
            SensorType.COMPRESSED_AUDIO,
            sample_rate_hz,
            1 / sample_rate_hz,
            0.0,
            True,
        )
    return None


def load_apim_image(packet: api_m.RedvoxPacketM) -> Optional[SensorData]:
    """
    load image data from a single wrapped packet
    :param packet: packet with data to load
    :return: image sensor data if it exists, None otherwise
    """
    if __has_sensor(packet, __IMAGE_FIELD_NAME):
        image_sensor: api_m.RedvoxPacketM.Sensors.Image = packet.sensors.image
        timestamps: np.ndarray = np.array(image_sensor.timestamps.timestamps)
        codecs = np.full(len(timestamps), image_sensor.image_codec)
        data_df = pd.DataFrame(
            np.transpose([timestamps, timestamps, image_sensor.samples, codecs]),
            columns=IMAGE_COLUMNS,
        )
        data_df["image_codec"] = [d for d in data_df["image_codec"]]
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            image_sensor.sensor_description,
            data_df,
            SensorType.IMAGE,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )
    return None


def load_apim_image_from_list(
    packets: List[api_m.RedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load image data from a list of wrapped packets
    :param packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: image sensor data if it exists, None otherwise
    """
    data_list = [[], [], []]
    for packet in packets:
        if __has_sensor(packet, __IMAGE_FIELD_NAME):
            image_sensor = packet.sensors.image

            data_list[0].extend(np.array(image_sensor.timestamps.timestamps))
            data_list[1].extend(image_sensor.samples)
            data_list[2].extend(
                [
                    image_sensor.image_codec
                    for i in range(len(image_sensor.timestamps.timestamps))
                ]
            )
    if len(data_list[0]) > 0:
        # image is collected 1 per packet or 1 per second
        if len(data_list[0]) > len(packets):
            sample_rate = 1.0
        else:
            sample_rate = 1 / __packet_duration_s(packets[0])
        sample_interval = 1 / sample_rate
        sample_interval_std = (
            dtu.microseconds_to_seconds(float(np.std(np.diff(data_list[0]))))
            if len(data_list[0]) > 1
            else np.nan
        )
        return SensorData(
            get_sensor_description_list(packets, SensorType.IMAGE),
            gpu.fill_gaps(
                pd.DataFrame(
                    np.transpose(
                        [data_list[0], data_list[0], data_list[1], data_list[2]]
                    ),
                    columns=IMAGE_COLUMNS,
                ),
                gaps,
                dtu.seconds_to_microseconds(sample_interval),
            ),
            SensorType.IMAGE,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )
    return None


def __is_only_best_values(loc: api_m.RedvoxPacketM.Sensors.Location) -> bool:
    """
    :return: True if the location does not have data in it and has a last_best_location or overall_best_location
    """
    return len(loc.location_providers) < 1 and (
        loc.HasField("last_best_location") or loc.HasField("overall_best_location")
    )


def load_apim_location(packet: api_m.RedvoxPacketM) -> Optional[SensorData]:
    """
    load location data from a single wrapped packet
    :param packet: packet with data to load
    :return: location sensor data if it exists, None otherwise
    """
    if __has_sensor(packet, __LOCATION_FIELD_NAME):
        loc: api_m.RedvoxPacketM.Sensors.Location = packet.get_sensors().get_location()

        if __is_only_best_values(loc):
            best_loc: api_m.RedvoxPacketM.Sensors.Location.BestLocation
            if loc.HasField("last_best_location"):
                best_loc = loc.last_best_location
            else:
                best_loc = loc.overall_best_location
            data_for_df = [
                [
                    best_loc.latitude_longitude_timestamp.mach,
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
            ]
        else:
            timestamps: np.ndarray = np.array(loc.timestamps.timestamps)
            if len(timestamps) > 0:
                gps_timestamps = np.array(loc.timestamps_gps.timestamps)
                lat_samples = np.array(loc.latitude_samples.values)
                lon_samples = np.array(loc.longitude_samples.values)
                alt_samples = np.array(loc.altitude_samples.values)
                spd_samples = np.array(loc.speed_samples.values)
                bear_samples = np.array(loc.bearing_samples.values)
                hor_acc_samples = np.array(loc.horizontal_accuracy_samples.values)
                vert_acc_samples = np.array(loc.vertical_accuracy_samples.values)
                spd_acc_samples = np.array(loc.speed_accuracy_samples.values)
                bear_acc_samples = np.array(loc.bearing_accuracy_samples.values)
                loc_prov_samples = np.array(loc.location_providers)
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
        return SensorData(
            loc.sensor_description,
            data_df,
            SensorType.LOCATION,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )
    return None


def load_apim_location_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load location data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: location sensor data if it exists, None otherwise
    """
    data_list = [[], [], [], [], [], [], [], [], [], [], [], []]
    loc_stats = StatsContainer("location_sensor")
    for packet in wrapped_packets:
        loc = packet.get_sensors().get_location()
        if loc and packet.get_sensors().validate_location():
            if loc.is_only_best_values():
                if loc.get_last_best_location():
                    best_loc = loc.get_last_best_location()
                else:
                    best_loc = loc.get_overall_best_location()
                data_list[0].append(
                    best_loc.get_latitude_longitude_timestamp().get_mach()
                )
                data_list[1].append(
                    best_loc.get_latitude_longitude_timestamp().get_gps()
                )
                data_list[2].append(best_loc.get_latitude())
                data_list[3].append(best_loc.get_longitude())
                data_list[4].append(best_loc.get_altitude())
                data_list[5].append(best_loc.get_speed())
                data_list[6].append(best_loc.get_bearing())
                data_list[7].append(best_loc.get_horizontal_accuracy())
                data_list[8].append(best_loc.get_vertical_accuracy())
                data_list[9].append(best_loc.get_speed_accuracy())
                data_list[10].append(best_loc.get_bearing_accuracy())
                data_list[11].append(best_loc.get_location_provider())
                loc_stats.add(
                    dtu.seconds_to_microseconds(packet.get_packet_duration_s()), 0, 1
                )
            else:
                num_samples = loc.get_timestamps().get_timestamps_count()
                if num_samples > 0:
                    samples = loc.get_timestamps().get_timestamps()
                    data_list[0].extend(samples)
                    if num_samples == 1:
                        loc_stats.add(
                            dtu.seconds_to_microseconds(packet.get_packet_duration_s()),
                            0,
                            1,
                        )
                    else:
                        loc_stats.add(
                            np.mean(np.diff(samples)),
                            np.std(np.diff(samples)),
                            num_samples - 1,
                        )
                    # data_list[4].extend([np.nan if len(samples) < i + 1
                    #                      else samples[i] for i in range(num_samples)])
                    for i in range(num_samples):
                        samples = loc.get_timestamps_gps().get_timestamps()
                        data_list[1].append(np.nan if len(samples) <= i else samples[i])
                        samples = loc.get_latitude_samples().get_values()
                        data_list[2].append(samples[i])
                        samples = loc.get_longitude_samples().get_values()
                        data_list[3].append(samples[i])
                        samples = loc.get_altitude_samples().get_values()
                        data_list[4].append(
                            np.nan if len(samples) < i + 1 else samples[i]
                        )
                        samples = loc.get_speed_samples().get_values()
                        data_list[5].append(
                            np.nan if len(samples) < i + 1 else samples[i]
                        )
                        samples = loc.get_bearing_samples().get_values()
                        data_list[6].append(
                            np.nan if len(samples) < i + 1 else samples[i]
                        )
                        samples = loc.get_horizontal_accuracy_samples().get_values()
                        data_list[7].append(
                            np.nan if len(samples) < i + 1 else samples[i]
                        )
                        samples = loc.get_vertical_accuracy_samples().get_values()
                        data_list[8].append(
                            np.nan if len(samples) < i + 1 else samples[i]
                        )
                        samples = loc.get_speed_accuracy_samples().get_values()
                        data_list[9].append(
                            np.nan if len(samples) < i + 1 else samples[i]
                        )
                        samples = loc.get_bearing_accuracy_samples().get_values()
                        data_list[10].append(
                            np.nan if len(samples) < i + 1 else samples[i]
                        )
                        samples = loc.get_location_providers().get_values()
                        data_list[11].append(
                            location.LocationProvider["UNKNOWN"]
                            if len(samples) < i + 1
                            else samples[i]
                        )
    if len(data_list[0]) > 0:
        data_list.insert(1, data_list[0].copy())
        return SensorData(
            get_sensor_description_list(wrapped_packets, SensorType.LOCATION),
            gpu.fill_gaps(
                pd.DataFrame(np.transpose(data_list), columns=LOCATION_COLUMNS),
                gaps,
                loc_stats.mean_of_means(),
            ),
            SensorType.LOCATION,
            calculate_stats=True,
        )
    return None


def load_apim_pressure(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load pressure data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: pressure sensor data if it exists, None otherwise
    """
    pressure = wrapped_packet.get_sensors().get_pressure()
    if pressure and wrapped_packet.get_sensors().validate_pressure():
        data_df = read_apim_single_sensor(pressure, "pressure")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            get_sensor_description(pressure),
            data_df,
            SensorType.PRESSURE,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_pressure_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load pressure data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: pressure sensor data if it exists, None otherwise
    """
    data_list = []
    timestamps = []
    pressure_stats = StatsContainer("pressure_sensor")
    for packet in wrapped_packets:
        pressure = packet.get_sensors().get_pressure()
        if pressure and packet.get_sensors().validate_pressure():
            data_list.extend(pressure.get_samples().get_values())
            ts = pressure.get_timestamps().get_timestamps()
            timestamps.extend(ts)
            if pressure.get_timestamps().get_timestamps_count() == 1:
                pressure_stats.add(
                    dtu.seconds_to_microseconds(packet.get_packet_duration_s()), 0, 1
                )
            else:
                pressure_stats.add(
                    np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1
                )
    if len(data_list) > 0:
        return load_apim_single_sensor(
            SensorType.PRESSURE,
            timestamps,
            data_list,
            gaps,
            "pressure",
            get_sensor_description_list(wrapped_packets, SensorType.PRESSURE),
            pressure_stats.mean_of_means(),
        )
    return None


def load_apim_light(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load light data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: light sensor data if it exists, None otherwise
    """
    light = wrapped_packet.get_sensors().get_light()
    if light and wrapped_packet.get_sensors().validate_light():
        data_df = read_apim_single_sensor(light, "light")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            get_sensor_description(light),
            data_df,
            SensorType.LIGHT,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_light_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load light data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: light sensor data if it exists, None otherwise
    """
    data_list = []
    timestamps = []
    light_stats = StatsContainer("light_sensor")
    for packet in wrapped_packets:
        light = packet.get_sensors().get_light()
        if light and packet.get_sensors().validate_light():
            data_list.extend(light.get_samples().get_values())
            ts = light.get_timestamps().get_timestamps()
            timestamps.extend(ts)
            if light.get_timestamps().get_timestamps_count() == 1:
                light_stats.add(
                    dtu.seconds_to_microseconds(packet.get_packet_duration_s()), 0, 1
                )
            else:
                light_stats.add(np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1)
    if len(data_list) > 0:
        return load_apim_single_sensor(
            SensorType.LIGHT,
            timestamps,
            data_list,
            gaps,
            "light",
            get_sensor_description_list(wrapped_packets, SensorType.LIGHT),
            light_stats.mean_of_means(),
        )
    return None


def load_apim_proximity(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load proximity data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: proximity sensor data if it exists, None otherwise
    """
    proximity = wrapped_packet.get_sensors().get_proximity()
    if proximity and wrapped_packet.get_sensors().validate_proximity():
        data_df = read_apim_single_sensor(proximity, "proximity")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            get_sensor_description(proximity),
            data_df,
            SensorType.PROXIMITY,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_proximity_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load proximity data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: proximity sensor data if it exists, None otherwise
    """
    data_list = []
    timestamps = []
    proximity_stats = StatsContainer("proximity_sensor")
    for packet in wrapped_packets:
        proximity = packet.get_sensors().get_proximity()
        if proximity and packet.get_sensors().validate_proximity():
            data_list.extend(proximity.get_samples().get_values())
            ts = proximity.get_timestamps().get_timestamps()
            timestamps.extend(ts)
            if proximity.get_timestamps().get_timestamps_count() == 1:
                proximity_stats.add(
                    dtu.seconds_to_microseconds(packet.get_packet_duration_s()), 0, 1
                )
            else:
                proximity_stats.add(
                    np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1
                )
    if len(data_list) > 0:
        return load_apim_single_sensor(
            SensorType.PROXIMITY,
            timestamps,
            data_list,
            gaps,
            "proximity",
            get_sensor_description_list(wrapped_packets, SensorType.PROXIMITY),
            proximity_stats.mean_of_means(),
        )
    return None


def load_apim_ambient_temp(
    wrapped_packet: WrappedRedvoxPacketM,
) -> Optional[SensorData]:
    """
    load ambient temperature data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: ambient temperature sensor data if it exists, None otherwise
    """
    ambient_temp = wrapped_packet.get_sensors().get_ambient_temperature()
    if ambient_temp and wrapped_packet.get_sensors().validate_ambient_temperature():
        data_df = read_apim_single_sensor(ambient_temp, "ambient_temp")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            get_sensor_description(ambient_temp),
            data_df,
            SensorType.AMBIENT_TEMPERATURE,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_ambient_temp_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load ambient temperature data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: ambient temperature sensor data if it exists, None otherwise
    """
    data_list = []
    timestamps = []
    amb_temp_stats = StatsContainer("amb_temp_sensor")
    for packet in wrapped_packets:
        amb_temp = packet.get_sensors().get_ambient_temperature()
        if amb_temp and packet.get_sensors().validate_ambient_temperature():
            data_list.extend(amb_temp.get_samples().get_values())
            ts = amb_temp.get_timestamps().get_timestamps()
            timestamps.extend(ts)
            if amb_temp.get_timestamps().get_timestamps_count() == 1:
                amb_temp_stats.add(
                    dtu.seconds_to_microseconds(packet.get_packet_duration_s()), 0, 1
                )
            else:
                amb_temp_stats.add(
                    np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1
                )
    if len(data_list) > 0:
        return load_apim_single_sensor(
            SensorType.AMBIENT_TEMPERATURE,
            timestamps,
            data_list,
            gaps,
            "ambient_temp",
            get_sensor_description_list(
                wrapped_packets, SensorType.AMBIENT_TEMPERATURE
            ),
            amb_temp_stats.mean_of_means(),
        )
    return None


def load_apim_rel_humidity(
    wrapped_packet: WrappedRedvoxPacketM,
) -> Optional[SensorData]:
    """
    load relative humidity data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: relative humidity sensor data if it exists, None otherwise
    """
    rel_humidity = wrapped_packet.get_sensors().get_relative_humidity()
    if rel_humidity and wrapped_packet.get_sensors().validate_relative_humidity():
        data_df = read_apim_single_sensor(rel_humidity, "rel_humidity")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            get_sensor_description(rel_humidity),
            data_df,
            SensorType.RELATIVE_HUMIDITY,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_rel_humidity_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load relative humidity data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: relative humidity sensor data if it exists, None otherwise
    """
    data_list = []
    timestamps = []
    rel_hum_stats = StatsContainer("rel_hum_sensor")
    for packet in wrapped_packets:
        rel_hum = packet.get_sensors().get_relative_humidity()
        if rel_hum and packet.get_sensors().validate_relative_humidity():
            data_list.extend(rel_hum.get_samples().get_values())
            ts = rel_hum.get_timestamps().get_timestamps()
            timestamps.extend(ts)
            if rel_hum.get_timestamps().get_timestamps_count() == 1:
                rel_hum_stats.add(
                    dtu.seconds_to_microseconds(packet.get_packet_duration_s()), 0, 1
                )
            else:
                rel_hum_stats.add(
                    np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1
                )
    if len(data_list) > 0:
        return load_apim_single_sensor(
            SensorType.RELATIVE_HUMIDITY,
            timestamps,
            data_list,
            gaps,
            "rel_humidity",
            get_sensor_description_list(wrapped_packets, SensorType.RELATIVE_HUMIDITY),
            rel_hum_stats.mean_of_means(),
        )
    return None


def load_apim_accelerometer(
    wrapped_packet: WrappedRedvoxPacketM,
) -> Optional[SensorData]:
    """
    load accelerometer data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: accelerometer sensor data if it exists, None otherwise
    """
    accel = wrapped_packet.get_sensors().get_accelerometer()
    if accel and wrapped_packet.get_sensors().validate_accelerometer():
        data_df = read_apim_xyz_sensor(accel, "accelerometer")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            get_sensor_description(accel),
            data_df,
            SensorType.ACCELEROMETER,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_accelerometer_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load accelerometer data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: accelerometer sensor data if it exists, None otherwise
    """
    data_list = [[], [], [], []]
    accel_stats = StatsContainer("accel_sensor")
    for packet in wrapped_packets:
        accel = packet.get_sensors().get_accelerometer()
        if accel and packet.get_sensors().validate_accelerometer():
            ts = accel.get_timestamps().get_timestamps()
            data_list[0].extend(ts)
            data_list[1].extend(accel.get_x_samples().get_values())
            data_list[2].extend(accel.get_y_samples().get_values())
            data_list[3].extend(accel.get_z_samples().get_values())
            if accel.get_timestamps().get_timestamps_count() == 1:
                accel_stats.add(
                    dtu.seconds_to_microseconds(packet.get_packet_duration_s()), 0, 1
                )
            else:
                accel_stats.add(np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1)
    if len(data_list[0]) > 0:
        return load_apim_xyz_sensor(
            SensorType.ACCELEROMETER,
            data_list,
            gaps,
            "accelerometer",
            get_sensor_description_list(wrapped_packets, SensorType.ACCELEROMETER),
            accel_stats.mean_of_means(),
        )
    return None


def load_apim_magnetometer(
    wrapped_packet: WrappedRedvoxPacketM,
) -> Optional[SensorData]:
    """
    load magnetometer data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: magnetometer sensor data if it exists, None otherwise
    """
    mag = wrapped_packet.get_sensors().get_magnetometer()
    if mag and wrapped_packet.get_sensors().validate_magnetometer():
        data_df = read_apim_xyz_sensor(mag, "magnetometer")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            get_sensor_description(mag),
            data_df,
            SensorType.MAGNETOMETER,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_magnetometer_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load magnetometer data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: magnetometer sensor data if it exists, None otherwise
    """
    data_list = [[], [], [], []]
    mag_stats = StatsContainer("mag_sensor")
    for packet in wrapped_packets:
        mag = packet.get_sensors().get_magnetometer()
        if mag and packet.get_sensors().validate_magnetometer():
            ts = mag.get_timestamps().get_timestamps()
            data_list[0].extend(ts)
            data_list[1].extend(mag.get_x_samples().get_values())
            data_list[2].extend(mag.get_y_samples().get_values())
            data_list[3].extend(mag.get_z_samples().get_values())
            if mag.get_timestamps().get_timestamps_count() == 1:
                mag_stats.add(
                    dtu.seconds_to_microseconds(packet.get_packet_duration_s()), 0, 1
                )
            else:
                mag_stats.add(np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1)
    if len(data_list[0]) > 0:
        return load_apim_xyz_sensor(
            SensorType.MAGNETOMETER,
            data_list,
            gaps,
            "magnetometer",
            get_sensor_description_list(wrapped_packets, SensorType.MAGNETOMETER),
            mag_stats.mean_of_means(),
        )
    return None


def load_apim_gyroscope(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load gyroscope data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: gyroscope sensor data if it exists, None otherwise
    """
    gyro = wrapped_packet.get_sensors().get_gyroscope()
    if gyro and wrapped_packet.get_sensors().validate_gyroscope():
        data_df = read_apim_xyz_sensor(gyro, "gyroscope")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            get_sensor_description(gyro),
            data_df,
            SensorType.GYROSCOPE,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_gyroscope_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load gyroscope data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: gyroscope sensor data if it exists, None otherwise
    """
    data_list = [[], [], [], []]
    gyro_stats = StatsContainer("gyro_sensor")
    for packet in wrapped_packets:
        gyro = packet.get_sensors().get_gyroscope()
        if gyro and packet.get_sensors().validate_gyroscope():
            ts = gyro.get_timestamps().get_timestamps()
            data_list[0].extend(ts)
            data_list[1].extend(gyro.get_x_samples().get_values())
            data_list[2].extend(gyro.get_y_samples().get_values())
            data_list[3].extend(gyro.get_z_samples().get_values())
            if gyro.get_timestamps().get_timestamps_count() == 1:
                gyro_stats.add(
                    dtu.seconds_to_microseconds(packet.get_packet_duration_s()), 0, 1
                )
            else:
                gyro_stats.add(np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1)
    if len(data_list[0]) > 0:
        return load_apim_xyz_sensor(
            SensorType.GYROSCOPE,
            data_list,
            gaps,
            "gyroscope",
            get_sensor_description_list(wrapped_packets, SensorType.GYROSCOPE),
            gyro_stats.mean_of_means(),
        )
    return None


def load_apim_gravity(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load gravity data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: gravity sensor data if it exists, None otherwise
    """
    gravity = wrapped_packet.get_sensors().get_gravity()
    if gravity and wrapped_packet.get_sensors().validate_gravity():
        data_df = read_apim_xyz_sensor(gravity, "gravity")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            get_sensor_description(gravity),
            data_df,
            SensorType.GRAVITY,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_gravity_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load gravity data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: gravity sensor data if it exists, None otherwise
    """
    data_list = [[], [], [], []]
    gravity_stats = StatsContainer("gravity_sensor")
    for packet in wrapped_packets:
        gravity = packet.get_sensors().get_gravity()
        if gravity and packet.get_sensors().validate_gravity():
            ts = gravity.get_timestamps().get_timestamps()
            data_list[0].extend(ts)
            data_list[1].extend(gravity.get_x_samples().get_values())
            data_list[2].extend(gravity.get_y_samples().get_values())
            data_list[3].extend(gravity.get_z_samples().get_values())
            if gravity.get_timestamps().get_timestamps_count() == 1:
                gravity_stats.add(
                    dtu.seconds_to_microseconds(packet.get_packet_duration_s()), 0, 1
                )
            else:
                gravity_stats.add(
                    np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1
                )
    if len(data_list[0]) > 0:
        return load_apim_xyz_sensor(
            SensorType.GRAVITY,
            data_list,
            gaps,
            "gravity",
            get_sensor_description_list(wrapped_packets, SensorType.GRAVITY),
            gravity_stats.mean_of_means(),
        )
    return None


def load_apim_orientation(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load orientation data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: orientation sensor data if it exists, None otherwise
    """
    orientation = wrapped_packet.get_sensors().get_orientation()
    if orientation and wrapped_packet.get_sensors().validate_orientation():
        data_df = read_apim_xyz_sensor(orientation, "orientation")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            get_sensor_description(orientation),
            data_df,
            SensorType.ORIENTATION,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_orientation_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load orientation data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: orientation sensor data if it exists, None otherwise
    """
    data_list = [[], [], [], []]
    orient_stats = StatsContainer("orient_sensor")
    for packet in wrapped_packets:
        orient = packet.get_sensors().get_orientation()
        if orient and packet.get_sensors().validate_orientation():
            ts = orient.get_timestamps().get_timestamps()
            data_list[0].extend(ts)
            data_list[1].extend(orient.get_x_samples().get_values())
            data_list[2].extend(orient.get_y_samples().get_values())
            data_list[3].extend(orient.get_z_samples().get_values())
            if orient.get_timestamps().get_timestamps_count() == 1:
                orient_stats.add(
                    dtu.seconds_to_microseconds(packet.get_packet_duration_s()), 0, 1
                )
            else:
                orient_stats.add(np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1)
    if len(data_list[0]) > 0:
        return load_apim_xyz_sensor(
            SensorType.ORIENTATION,
            data_list,
            gaps,
            "orientation",
            get_sensor_description_list(wrapped_packets, SensorType.ORIENTATION),
            orient_stats.mean_of_means(),
        )
    return None


def load_apim_linear_accel(
    wrapped_packet: WrappedRedvoxPacketM,
) -> Optional[SensorData]:
    """
    load linear acceleration data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: linear acceleration sensor data if it exists, None otherwise
    """
    linear_accel = wrapped_packet.get_sensors().get_linear_acceleration()
    if linear_accel and wrapped_packet.get_sensors().validate_linear_acceleration():
        data_df = read_apim_xyz_sensor(linear_accel, "linear_accel")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            get_sensor_description(linear_accel),
            data_df,
            SensorType.LINEAR_ACCELERATION,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_linear_accel_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load linear acceleration data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: linear acceleration sensor data if it exists, None otherwise
    """
    data_list = [[], [], [], []]
    lin_acc_stats = StatsContainer("lin_acc_sensor")
    for packet in wrapped_packets:
        lin_acc = packet.get_sensors().get_linear_acceleration()
        if lin_acc and packet.get_sensors().validate_linear_acceleration():
            ts = lin_acc.get_timestamps().get_timestamps()
            data_list[0].extend(ts)
            data_list[1].extend(lin_acc.get_x_samples().get_values())
            data_list[2].extend(lin_acc.get_y_samples().get_values())
            data_list[3].extend(lin_acc.get_z_samples().get_values())
            if lin_acc.get_timestamps().get_timestamps_count() == 1:
                lin_acc_stats.add(
                    dtu.seconds_to_microseconds(packet.get_packet_duration_s()), 0, 1
                )
            else:
                lin_acc_stats.add(
                    np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1
                )
    if len(data_list[0]) > 0:
        return load_apim_xyz_sensor(
            SensorType.LINEAR_ACCELERATION,
            data_list,
            gaps,
            "linear_accel",
            get_sensor_description_list(
                wrapped_packets, SensorType.LINEAR_ACCELERATION
            ),
            lin_acc_stats.mean_of_means(),
        )
    return None


def load_apim_rotation_vector(
    wrapped_packet: WrappedRedvoxPacketM,
) -> Optional[SensorData]:
    """
    load rotation vector data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: rotation vector sensor data if it exists, None otherwise
    """
    rotation = wrapped_packet.get_sensors().get_rotation_vector()
    if rotation and wrapped_packet.get_sensors().validate_rotation_vector():
        data_df = read_apim_xyz_sensor(rotation, "rotation_vector")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(
            data_df
        )
        return SensorData(
            get_sensor_description(rotation),
            data_df,
            SensorType.ROTATION_VECTOR,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_rotation_vector_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load rotation vector data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: rotation vector sensor data if it exists, None otherwise
    """
    data_list = [[], [], [], []]
    rot_vec_stats = StatsContainer("rot_vec_sensor")
    for packet in wrapped_packets:
        rot_vec = packet.get_sensors().get_rotation_vector()
        if rot_vec and packet.get_sensors().validate_rotation_vector():
            ts = rot_vec.get_timestamps().get_timestamps()
            data_list[0].extend(ts)
            data_list[1].extend(rot_vec.get_x_samples().get_values())
            data_list[2].extend(rot_vec.get_y_samples().get_values())
            data_list[3].extend(rot_vec.get_z_samples().get_values())
            if rot_vec.get_timestamps().get_timestamps_count() == 1:
                rot_vec_stats.add(
                    dtu.seconds_to_microseconds(packet.get_packet_duration_s()), 0, 1
                )
            else:
                rot_vec_stats.add(
                    np.mean(np.diff(ts)), np.std(np.diff(ts)), len(ts) - 1
                )
    if len(data_list[0]) > 0:
        return load_apim_xyz_sensor(
            SensorType.ROTATION_VECTOR,
            data_list,
            gaps,
            "rotation_vector",
            get_sensor_description_list(wrapped_packets, SensorType.ROTATION_VECTOR),
            rot_vec_stats.mean_of_means(),
        )
    return None


def load_apim_health(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load station health data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: station health data if it exists, None otherwise
    """
    metrics = wrapped_packet.get_station_information().get_station_metrics()
    timestamps = metrics.get_timestamps().get_timestamps()
    if len(timestamps) > 0:
        bat_samples = metrics.get_battery().get_values()
        bat_cur_samples = metrics.get_battery_current().get_values()
        temp_samples = metrics.get_temperature().get_values()
        net_samples = metrics.get_network_type().get_values()
        net_str_samples = metrics.get_network_strength().get_values()
        pow_samples = metrics.get_power_state().get_values()
        avail_ram_samples = metrics.get_available_ram().get_values()
        avail_disk_samples = metrics.get_available_disk().get_values()
        cell_samples = metrics.get_cell_service_state().get_values()
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
            ]
            data_for_df.append(new_entry)
        data_df = pd.DataFrame(
            data_for_df,
            columns=[
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
            ],
        )
        if len(timestamps) > 1:
            sample_rate = 1
            sample_interval_std = dtu.microseconds_to_seconds(
                float(np.std(np.diff(data_df["timestamps"])))
            )
        else:
            sample_rate = 1 / wrapped_packet.get_packet_duration_s()
            sample_interval_std = np.nan
        return SensorData(
            "station health",
            data_df,
            SensorType.STATION_HEALTH,
            sample_rate,
            1 / sample_rate,
            sample_interval_std,
        )
    return None


def load_apim_health_from_list(
    wrapped_packets: List[WrappedRedvoxPacketM], gaps: List[Tuple[float, float]]
) -> Optional[SensorData]:
    """
    load station health data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :param gaps: the list of non-inclusive start and end times of the gaps in the packets
    :return: station health sensor data if it exists, None otherwise
    """
    data_list: List = [[], [], [], [], [], [], [], [], [], []]
    for packet in wrapped_packets:
        metrics = packet.get_station_information().get_station_metrics()
        timestamps = metrics.get_timestamps().get_timestamps()
        num_samples = len(timestamps)
        if num_samples > 0:
            data_list[0].extend(timestamps)
            samples = metrics.get_battery().get_values()
            if len(samples) != num_samples:
                samples = np.full(num_samples, np.nan)
            data_list[1].extend(samples)
            samples = metrics.get_battery_current().get_values()
            if len(samples) != num_samples:
                samples = np.full(num_samples, np.nan)
            data_list[2].extend(samples)
            samples = metrics.get_temperature().get_values()
            if len(samples) != num_samples:
                samples = np.full(num_samples, np.nan)
            data_list[3].extend(samples)
            samples = metrics.get_network_type().get_values()
            data_list[4].extend(
                [
                    NetworkType["UNKNOWN_NETWORK"]
                    if len(samples) < i + 1
                    else samples[i]
                    for i in range(num_samples)
                ]
            )
            samples = metrics.get_network_strength().get_values()
            if len(samples) != num_samples:
                samples = np.full(num_samples, np.nan)
            data_list[5].extend(samples)
            samples = metrics.get_power_state().get_values()
            data_list[6].extend(
                [
                    PowerState["UNKNOWN_POWER_STATE"]
                    if len(samples) < i + 1
                    else samples[i]
                    for i in range(num_samples)
                ]
            )
            samples = metrics.get_available_ram().get_values()
            if len(samples) != num_samples:
                samples = np.full(num_samples, np.nan)
            data_list[7].extend(samples)
            samples = metrics.get_available_disk().get_values()
            data_list[8].extend(
                samples if len(samples) == num_samples else np.full(num_samples, np.nan)
            )
            samples = metrics.get_cell_service_state().get_values()
            data_list[9].extend(
                [
                    CellServiceState["UNKNOWN"] if len(samples) < i + 1 else samples[i]
                    for i in range(num_samples)
                ]
            )
    if len(data_list[0]) > 0:
        data_list.insert(1, data_list[0].copy())
        # health is collected 1 per packet or 1 per second
        if len(data_list[0]) > len(wrapped_packets):
            sample_rate = 1.0
        else:
            sample_rate = 1 / wrapped_packets[0].get_packet_duration_s()
        sample_interval = 1 / sample_rate
        sample_interval_std = (
            dtu.microseconds_to_seconds(float(np.std(np.diff(data_list[0]))))
            if len(data_list[0]) > 1
            else np.nan
        )
        df = gpu.fill_gaps(
            pd.DataFrame(
                np.transpose(data_list),
                columns=[
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
                ],
            ),
            gaps,
            dtu.seconds_to_microseconds(sample_interval),
        )
        return SensorData(
            "station health",
            df,
            SensorType.STATION_HEALTH,
            sample_rate,
            sample_interval,
            sample_interval_std,
        )
    return None
