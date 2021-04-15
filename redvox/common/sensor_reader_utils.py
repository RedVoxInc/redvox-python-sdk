"""
This module loads sensor data from Redvox packets
"""

from typing import List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from redvox.common import date_time_utils as dtu
from redvox.common import gap_and_pad_utils as gpu
from redvox.common.sensor_data import SensorType, SensorData
from redvox.api1000.wrapped_redvox_packet.sensors import xyz, single, audio, image, location
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM


# Dataframe column definitions
COMPRESSED_AUDIO_COLUMNS = ["timestamps", "unaltered_timestamps", "compressed_audio", "audio_codec"]
IMAGE_COLUMNS = ["timestamps", "unaltered_timestamps", "image", "image_codec"]
LOCATION_COLUMNS = ["timestamps", "unaltered_timestamps", "gps_timestamps", "latitude", "longitude",
                    "altitude", "speed", "bearing", "horizontal_accuracy", "vertical_accuracy",
                    "speed_accuracy", "bearing_accuracy", "location_provider"]


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


def get_sensor_description(sensor: Union[xyz.Xyz, single.Single, audio.Audio, image.Image, location.Location]) -> str:
    """
    read the sensor's description from the sensor
    :param sensor: the sensor to read the description from
    :return: the sensor's description
    """
    return sensor.get_sensor_description()


def get_sensor_description_list(wrapped_packets: List[WrappedRedvoxPacketM], sensor_type: SensorType) -> str:
    """
    read the sensor_type sensor's description from a list of packets
    :param wrapped_packets: the list of packets to read from
    :param sensor_type: the SensorType of the sensor to read the description of
    :return: the sensor_type sensor's description
    """
    for packet in wrapped_packets:
        if sensor_type == SensorType.AUDIO and packet.get_sensors().has_audio():
            return get_sensor_description(packet.get_sensors().get_audio())
        if sensor_type == SensorType.IMAGE and packet.get_sensors().has_image():
            return get_sensor_description(packet.get_sensors().get_image())
        if sensor_type == SensorType.LOCATION and packet.get_sensors().has_location():
            return get_sensor_description(packet.get_sensors().get_location())
        if sensor_type == SensorType.PRESSURE and packet.get_sensors().has_pressure():
            return get_sensor_description(packet.get_sensors().get_pressure())
        if sensor_type == SensorType.ACCELEROMETER and packet.get_sensors().has_accelerometer():
            return get_sensor_description(packet.get_sensors().get_accelerometer())
        if sensor_type == SensorType.AMBIENT_TEMPERATURE and packet.get_sensors().has_ambient_temperature():
            return get_sensor_description(packet.get_sensors().get_ambient_temperature())
        if sensor_type == SensorType.COMPRESSED_AUDIO and packet.get_sensors().has_compressed_audio():
            return get_sensor_description(packet.get_sensors().get_compressed_audio())
        if sensor_type == SensorType.GRAVITY and packet.get_sensors().has_gravity():
            return get_sensor_description(packet.get_sensors().get_gravity())
        if sensor_type == SensorType.GYROSCOPE and packet.get_sensors().has_gyroscope():
            return get_sensor_description(packet.get_sensors().get_gyroscope())
        if sensor_type == SensorType.LIGHT and packet.get_sensors().has_light():
            return get_sensor_description(packet.get_sensors().get_light())
        if sensor_type == SensorType.LINEAR_ACCELERATION and packet.get_sensors().has_linear_acceleration():
            return get_sensor_description(packet.get_sensors().get_linear_acceleration())
        if sensor_type == SensorType.MAGNETOMETER and packet.get_sensors().has_magnetometer():
            return get_sensor_description(packet.get_sensors().get_magnetometer())
        if sensor_type == SensorType.ORIENTATION and packet.get_sensors().has_orientation():
            return get_sensor_description(packet.get_sensors().get_orientation())
        if sensor_type == SensorType.PROXIMITY and packet.get_sensors().has_proximity():
            return get_sensor_description(packet.get_sensors().get_proximity())
        if sensor_type == SensorType.RELATIVE_HUMIDITY and packet.get_sensors().has_relative_humidity():
            return get_sensor_description(packet.get_sensors().get_relative_humidity())
        if sensor_type == SensorType.ROTATION_VECTOR and packet.get_sensors().has_rotation_vector():
            return get_sensor_description(packet.get_sensors().get_rotation_vector())


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


def read_apim_xyz_sensor(sensor: xyz.Xyz, column_id: str) -> pd.DataFrame:
    """
    read a sensor that has xyz data channels from an api M data packet
    raises Attribute Error if sensor does not contain xyz channels
    :param sensor: the xyz api M sensor to read
    :param column_id: string, used to name the columns
    :return: Dataframe representing the data in the sensor
    """
    timestamps = sensor.get_timestamps().get_timestamps()
    try:
        columns = ["timestamps", "unaltered_timestamps", f"{column_id}_x", f"{column_id}_y", f"{column_id}_z"]
        return pd.DataFrame(
            np.transpose(
                [
                    timestamps,
                    timestamps,
                    sensor.get_x_samples().get_values(),
                    sensor.get_y_samples().get_values(),
                    sensor.get_z_samples().get_values(),
                ]
            ),
            columns=columns,
        )
    except AttributeError:
        raise


def load_apim_xyz_sensor(sensor_type: SensorType, data: List[List[float]], column_name: str,
                         description: str) -> Optional[SensorData]:
    """
    create a three channel sensor of sensor_type with the column name, description, and data given.
    :param sensor_type: the SensorType of sensor to create
    :param data: the list of data to be added; requires timestamps to be the first list
    :param column_name: the name of the columns that contain the data
    :param description: the description of the sensor
    :return: SensorData object or None if no data
    """
    if len(data[0]) > 0:
        return SensorData(
            description,
            pd.DataFrame(np.transpose([data[0], data[0], data[1], data[2], data[3]]),
                         columns=["timestamps", "unaltered_timestamps",
                                  f"{column_name}_x", f"{column_name}_y", f"{column_name}_z"]),
            sensor_type,
            calculate_stats=True
        )
    return None


def read_apim_single_sensor(sensor: single.Single, column_id: str) -> pd.DataFrame:
    """
    read a sensor that has a single data channel from an api M data packet
    raises Attribute Error if sensor does not contain exactly one data channel
    :param sensor: the single channel api M sensor to read
    :param column_id: string, used to name the columns
    :return: Dataframe representing the data in the sensor
    """
    timestamps = sensor.get_timestamps().get_timestamps()
    try:
        columns = ["timestamps", "unaltered_timestamps", column_id]
        return pd.DataFrame(
            np.transpose([timestamps, timestamps, sensor.get_samples().get_values()]),
            columns=columns,
        )
    except AttributeError:
        raise


def load_apim_single_sensor(sensor_type: SensorType, timestamps: List[float], data: List[float],
                            column_name: str, description: str) -> Optional[SensorData]:
    """
    Create a single channel sensor of sensor_type with the column name, timestamps, data, and description
    :param sensor_type: the SensorType of sensor to create
    :param timestamps: the timestamps of the data
    :param data: the list of data to be added
    :param column_name: the name of the columns that contain the data
    :param description: the description of the sensor
    :return:
    """
    if len(timestamps) > 0:
        return SensorData(
            description,
            pd.DataFrame(np.transpose([timestamps, timestamps, data]),
                         columns=["timestamps", "unaltered_timestamps", column_name]),
            sensor_type,
            calculate_stats=True
        )
    return None


def load_apim_audio(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load audio data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: audio sensor data if it exists, None otherwise
    """
    audio_sensor = wrapped_packet.get_sensors().get_audio()
    if audio_sensor and wrapped_packet.get_sensors().validate_audio():
        sample_rate_hz = audio_sensor.get_sample_rate()
        data_for_df = audio_sensor.get_samples().get_values()
        timestamps = gpu.calc_evenly_sampled_timestamps(
            audio_sensor.get_first_sample_timestamp(), audio_sensor.get_num_samples(),
            dtu.seconds_to_microseconds(1/sample_rate_hz)
        )
        return SensorData(
            get_sensor_description(audio_sensor),
            pd.DataFrame(np.transpose([timestamps, timestamps, data_for_df]), columns=gpu.AUDIO_DF_COLUMNS),
            SensorType.AUDIO,
            sample_rate_hz,
            1 / sample_rate_hz,
            0.0,
            True,
            )
    return None


def load_apim_audio_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load audio data from a list of wrapped packets
    NOTE: This only works because audio sensors in the list should all have the same number of data points.
    :param wrapped_packets: packets with data to load
    :return: audio sensor data if it exists, None otherwise
    """
    if len(wrapped_packets) > 0:
        if wrapped_packets[0].get_sensors().get_audio() and wrapped_packets[0].get_sensors().validate_audio():
            try:
                sample_rate_hz = wrapped_packets[0].get_sensors().get_audio().get_sample_rate()
                packet_info = [(p.get_sensors().get_audio().get_first_sample_timestamp(),
                                p.get_sensors().get_audio().get_samples().get_values(),
                                p.get_sensors().get_audio().get_num_samples())
                               for p in wrapped_packets]
                df = gpu.fill_audio_gaps(packet_info, dtu.seconds_to_microseconds(1/sample_rate_hz))

                return SensorData(
                    get_sensor_description_list(wrapped_packets, SensorType.AUDIO),
                    df,
                    SensorType.AUDIO,
                    sample_rate_hz,
                    1 / sample_rate_hz,
                    0.0,
                    True,
                    )
            except ValueError as error:
                print("Error occurred while loading audio data for station "
                      f"{wrapped_packets[0].get_station_information().get_id()}.\n"
                      f"Original error message: {error}")
    return None


def load_apim_compressed_audio(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load compressed audio data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: compressed audio sensor data if it exists, None otherwise
    """
    comp_audio = wrapped_packet.get_sensors().get_compressed_audio()
    if comp_audio and wrapped_packet.get_sensors().validate_compressed_audio():
        sample_rate_hz = comp_audio.get_sample_rate()
        return SensorData(
            get_sensor_description(comp_audio),
            pd.DataFrame(
                np.transpose(
                    [
                        comp_audio.get_first_sample_timestamp(),
                        comp_audio.get_first_sample_timestamp(),
                        comp_audio.get_audio_bytes(),
                        comp_audio.get_audio_codec(),
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


def load_apim_compressed_audio_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load compressed audio data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: compressed audio sensor data if it exists, None otherwise
    """
    data_df = [[], [], []]
    for packet in wrapped_packets:
        comp_audio = packet.get_sensors().get_compressed_audio()
        if comp_audio and packet.get_sensors().validate_compressed_audio():
            data_df[0].append(comp_audio.get_first_sample_timestamp())
            data_df[1].append(comp_audio.get_audio_bytes())
            data_df[2].append(comp_audio.get_audio_codec())
    if len(data_df[0]) > 0:
        sample_rate_hz = wrapped_packets[0].get_sensors().get_compressed_audio().get_sample_rate()
        return SensorData(
            get_sensor_description_list(wrapped_packets, SensorType.COMPRESSED_AUDIO),
            pd.DataFrame([data_df[0], data_df[0], data_df[1], data_df[2]],
                         index=COMPRESSED_AUDIO_COLUMNS,
                         ).T,
            SensorType.COMPRESSED_AUDIO,
            sample_rate_hz,
            1 / sample_rate_hz,
            0.0,
            True,
            )
    return None


def load_apim_image(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load image data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: image sensor data if it exists, None otherwise
    """
    image_sensor = wrapped_packet.get_sensors().get_image()
    if image_sensor and wrapped_packet.get_sensors().validate_image():
        timestamps = image_sensor .get_timestamps().get_timestamps()
        codecs = np.full(len(timestamps), image_sensor .get_image_codec().value)
        data_df = pd.DataFrame(
            np.transpose([timestamps, timestamps, image_sensor .get_samples(), codecs]),
            columns=IMAGE_COLUMNS,
        )
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(image_sensor),
            data_df,
            SensorType.IMAGE,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )
    return None


def load_apim_image_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load image data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: image sensor data if it exists, None otherwise
    """
    data_list = [[], [], []]
    for packet in wrapped_packets:
        image_sensor = packet.get_sensors().get_image()
        if image_sensor and packet.get_sensors().validate_image():
            data_list[0].extend(image_sensor.get_timestamps().get_timestamps())
            data_list[1].extend(image_sensor.get_samples())
            data_list[2].extend(np.full(len(image_sensor.get_samples()), image_sensor.get_image_codec().value))
    if len(data_list[0]) > 0:
        data_df = pd.DataFrame([data_list[0], data_list[0], data_list[1], data_list[2]], index=IMAGE_COLUMNS).T
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description_list(wrapped_packets, SensorType.IMAGE),
            data_df,
            SensorType.IMAGE,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )
    return None


def load_apim_location(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load location data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: location sensor data if it exists, None otherwise
    """
    loc = wrapped_packet.get_sensors().get_location()
    if loc and wrapped_packet.get_sensors().validate_location():
        if loc.is_only_best_values():
            if loc.get_last_best_location():
                best_loc = loc.get_last_best_location()
            else:
                best_loc = loc.get_overall_best_location()
            data_for_df = [
                [
                    best_loc.get_latitude_longitude_timestamp().get_mach(),
                    best_loc.get_latitude_longitude_timestamp().get_mach(),
                    best_loc.get_latitude_longitude_timestamp().get_gps(),
                    best_loc.get_latitude(),
                    best_loc.get_longitude(),
                    best_loc.get_altitude(),
                    best_loc.get_speed(),
                    best_loc.get_bearing(),
                    best_loc.get_horizontal_accuracy(),
                    best_loc.get_vertical_accuracy(),
                    best_loc.get_speed_accuracy(),
                    best_loc.get_bearing_accuracy(),
                    best_loc.get_location_provider(),
                ]
            ]
        else:
            timestamps = loc.get_timestamps().get_timestamps()
            if len(timestamps) > 0:
                gps_timestamps = loc.get_timestamps_gps().get_timestamps()
                lat_samples = loc.get_latitude_samples().get_values()
                lon_samples = loc.get_longitude_samples().get_values()
                alt_samples = loc.get_altitude_samples().get_values()
                spd_samples = loc.get_speed_samples().get_values()
                bear_samples = loc.get_bearing_samples().get_values()
                hor_acc_samples = loc.get_horizontal_accuracy_samples().get_values()
                vert_acc_samples = loc.get_vertical_accuracy_samples().get_values()
                spd_acc_samples = loc.get_speed_accuracy_samples().get_values()
                bear_acc_samples = loc.get_bearing_accuracy_samples().get_values()
                loc_prov_samples = loc.get_location_providers().get_values()
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
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(loc),
            data_df,
            SensorType.LOCATION,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )
    return None


def load_apim_location_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load location data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: location sensor data if it exists, None otherwise
    """
    data_for_df = [[], [], [], [], [], [], [], [], [], [], [], []]
    for packet in wrapped_packets:
        loc = packet.get_sensors().get_location()
        if loc and packet.get_sensors().validate_location():
            if loc.is_only_best_values():
                if loc.get_last_best_location():
                    best_loc = loc.get_last_best_location()
                else:
                    best_loc = loc.get_overall_best_location()
                data_for_df[0].append(best_loc.get_latitude_longitude_timestamp().get_mach())
                data_for_df[1].append(best_loc.get_latitude_longitude_timestamp().get_gps())
                data_for_df[2].append(best_loc.get_latitude())
                data_for_df[3].append(best_loc.get_longitude())
                data_for_df[4].append(best_loc.get_altitude())
                data_for_df[5].append(best_loc.get_speed())
                data_for_df[6].append(best_loc.get_bearing())
                data_for_df[7].append(best_loc.get_horizontal_accuracy())
                data_for_df[8].append(best_loc.get_vertical_accuracy())
                data_for_df[9].append(best_loc.get_speed_accuracy())
                data_for_df[10].append(best_loc.get_bearing_accuracy())
                data_for_df[11].append(best_loc.get_location_provider())
            else:
                timestamps = loc.get_timestamps().get_timestamps()
                num_samples = len(timestamps)
                if num_samples > 0:
                    gps_timestamps = loc.get_timestamps_gps().get_timestamps()
                    lat_samples = loc.get_latitude_samples().get_values()
                    lon_samples = loc.get_longitude_samples().get_values()
                    alt_samples = loc.get_altitude_samples().get_values()
                    spd_samples = loc.get_speed_samples().get_values()
                    bear_samples = loc.get_bearing_samples().get_values()
                    hor_acc_samples = loc.get_horizontal_accuracy_samples().get_values()
                    vert_acc_samples = loc.get_vertical_accuracy_samples().get_values()
                    spd_acc_samples = loc.get_speed_accuracy_samples().get_values()
                    bear_acc_samples = loc.get_bearing_accuracy_samples().get_values()
                    loc_prov_samples = loc.get_location_providers().get_values()
                    for i in range(num_samples):
                        data_for_df[0].append(timestamps[i])
                        data_for_df[1].append(np.nan if len(gps_timestamps) <= i else gps_timestamps[i])
                        data_for_df[2].append(lat_samples[i])
                        data_for_df[3].append(lon_samples[i])
                        data_for_df[4].append(np.nan if len(alt_samples) < i + 1 else alt_samples[i])
                        data_for_df[5].append(np.nan if len(spd_samples) < i + 1 else spd_samples[i])
                        data_for_df[6].append(np.nan if len(bear_samples) < i + 1 else bear_samples[i])
                        data_for_df[7].append(np.nan if len(hor_acc_samples) < i + 1 else hor_acc_samples[i])
                        data_for_df[8].append(np.nan if len(vert_acc_samples) < i + 1 else vert_acc_samples[i])
                        data_for_df[9].append(np.nan if len(spd_acc_samples) < i + 1 else spd_acc_samples[i])
                        data_for_df[10].append(np.nan if len(bear_acc_samples) < i + 1 else bear_acc_samples[i])
                        data_for_df[11].append(np.nan if len(loc_prov_samples) < i + 1 else loc_prov_samples[i])
    if len(data_for_df[0]) > 0:
        data_for_df.insert(1, data_for_df[0].copy())
        return SensorData(
            get_sensor_description_list(wrapped_packets, SensorType.LOCATION),
            pd.DataFrame(np.transpose(data_for_df), columns=LOCATION_COLUMNS),
            SensorType.LOCATION,
            calculate_stats=True
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
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(pressure),
            data_df,
            SensorType.PRESSURE,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_pressure_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load pressure data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: pressure sensor data if it exists, None otherwise
    """
    data_df = []
    timestamps = []
    for packet in wrapped_packets:
        pressure = packet.get_sensors().get_pressure()
        if pressure and packet.get_sensors().validate_pressure():
            data_df.extend(pressure.get_samples().get_values())
            timestamps.extend(pressure.get_timestamps().get_timestamps())
    if len(data_df) > 0:
        return load_apim_single_sensor(SensorType.PRESSURE, timestamps, data_df, "pressure",
                                       get_sensor_description_list(wrapped_packets, SensorType.PRESSURE))
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
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(light),
            data_df,
            SensorType.LIGHT,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_light_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load light data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: light sensor data if it exists, None otherwise
    """
    data_df = []
    timestamps = []
    for packet in wrapped_packets:
        light = packet.get_sensors().get_light()
        if light and packet.get_sensors().validate_light():
            data_df.extend(light.get_samples().get_values())
            timestamps.extend(light.get_timestamps().get_timestamps())
    if len(data_df) > 0:
        return load_apim_single_sensor(SensorType.LIGHT, timestamps, data_df, "light",
                                       get_sensor_description_list(wrapped_packets, SensorType.LIGHT))
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
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(proximity),
            data_df,
            SensorType.PROXIMITY,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_proximity_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load proximity data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: proximity sensor data if it exists, None otherwise
    """
    data_df = []
    timestamps = []
    for packet in wrapped_packets:
        proximity = packet.get_sensors().get_proximity()
        if proximity and packet.get_sensors().validate_proximity():
            data_df.extend(proximity.get_samples().get_values())
            timestamps.extend(proximity.get_timestamps().get_timestamps())
    if len(data_df) > 0:
        return load_apim_single_sensor(SensorType.PROXIMITY, timestamps, data_df, "proximity",
                                       get_sensor_description_list(wrapped_packets, SensorType.PROXIMITY))
    return None


def load_apim_ambient_temp(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load ambient temperature data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: ambient temperature sensor data if it exists, None otherwise
    """
    ambient_temp = wrapped_packet.get_sensors().get_ambient_temperature()
    if ambient_temp and wrapped_packet.get_sensors().validate_ambient_temperature():
        data_df = read_apim_single_sensor(ambient_temp, "ambient_temp")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(ambient_temp),
            data_df,
            SensorType.AMBIENT_TEMPERATURE,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_ambient_temp_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load ambient temperature data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: ambient temperature sensor data if it exists, None otherwise
    """
    data_df = []
    timestamps = []
    for packet in wrapped_packets:
        amb_temp = packet.get_sensors().get_ambient_temperature()
        if amb_temp and packet.get_sensors().validate_ambient_temperature():
            data_df.extend(amb_temp.get_samples().get_values())
            timestamps.extend(amb_temp.get_timestamps().get_timestamps())
    if len(data_df) > 0:
        return load_apim_single_sensor(SensorType.AMBIENT_TEMPERATURE, timestamps, data_df, "ambient_temp",
                                       get_sensor_description_list(wrapped_packets, SensorType.AMBIENT_TEMPERATURE))
    return None


def load_apim_rel_humidity(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load relative humidity data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: relative humidity sensor data if it exists, None otherwise
    """
    rel_humidity = wrapped_packet.get_sensors().get_relative_humidity()
    if rel_humidity and wrapped_packet.get_sensors().validate_relative_humidity():
        data_df = read_apim_single_sensor(rel_humidity, "rel_humidity")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(rel_humidity),
            data_df,
            SensorType.RELATIVE_HUMIDITY,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_rel_humidity_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load relative humidity data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: relative humidity sensor data if it exists, None otherwise
    """
    data_df = []
    timestamps = []
    for packet in wrapped_packets:
        rel_hum = packet.get_sensors().get_relative_humidity()
        if rel_hum and packet.get_sensors().validate_relative_humidity():
            data_df.extend(rel_hum.get_samples().get_values())
            timestamps.extend(rel_hum.get_timestamps().get_timestamps())
    if len(data_df) > 0:
        return load_apim_single_sensor(SensorType.RELATIVE_HUMIDITY, timestamps, data_df, "rel_humidity",
                                       get_sensor_description_list(wrapped_packets, SensorType.RELATIVE_HUMIDITY))
    return None


def load_apim_accelerometer(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load accelerometer data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: accelerometer sensor data if it exists, None otherwise
    """
    accel = wrapped_packet.get_sensors().get_accelerometer()
    if accel and wrapped_packet.get_sensors().validate_accelerometer():
        data_df = read_apim_xyz_sensor(accel, "accelerometer")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(accel),
            data_df,
            SensorType.ACCELEROMETER,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_accelerometer_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load accelerometer data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: accelerometer sensor data if it exists, None otherwise
    """
    data_df = [[], [], [], []]
    for packet in wrapped_packets:
        accel = packet.get_sensors().get_accelerometer()
        if accel and packet.get_sensors().validate_accelerometer():
            data_df[0].extend(accel.get_timestamps().get_timestamps())
            data_df[1].extend(accel.get_x_samples().get_values())
            data_df[2].extend(accel.get_y_samples().get_values())
            data_df[3].extend(accel.get_z_samples().get_values())
    if len(data_df[0]) > 0:
        return load_apim_xyz_sensor(SensorType.ACCELEROMETER, data_df, "accelerometer",
                                    get_sensor_description_list(wrapped_packets, SensorType.ACCELEROMETER))
    return None


def load_apim_magnetometer(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load magnetometer data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: magnetometer sensor data if it exists, None otherwise
    """
    mag = wrapped_packet.get_sensors().get_magnetometer()
    if mag and wrapped_packet.get_sensors().validate_magnetometer():
        data_df = read_apim_xyz_sensor(mag, "magnetometer")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(mag),
            data_df,
            SensorType.MAGNETOMETER,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_magnetometer_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load magnetometer data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: magnetometer sensor data if it exists, None otherwise
    """
    data_df = [[], [], [], []]
    for packet in wrapped_packets:
        mag = packet.get_sensors().get_magnetometer()
        if mag and packet.get_sensors().validate_magnetometer():
            data_df[0].extend(mag.get_timestamps().get_timestamps())
            data_df[1].extend(mag.get_x_samples().get_values())
            data_df[2].extend(mag.get_y_samples().get_values())
            data_df[3].extend(mag.get_z_samples().get_values())
    if len(data_df[0]) > 0:
        return load_apim_xyz_sensor(SensorType.MAGNETOMETER, data_df, "magnetometer",
                                    get_sensor_description_list(wrapped_packets, SensorType.MAGNETOMETER))
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
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(gyro),
            data_df,
            SensorType.GYROSCOPE,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_gyroscope_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load gyroscope data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: gyroscope sensor data if it exists, None otherwise
    """
    data_df = [[], [], [], []]
    for packet in wrapped_packets:
        gyro = packet.get_sensors().get_gyroscope()
        if gyro and packet.get_sensors().validate_gyroscope():
            data_df[0].extend(gyro.get_timestamps().get_timestamps())
            data_df[1].extend(gyro.get_x_samples().get_values())
            data_df[2].extend(gyro.get_y_samples().get_values())
            data_df[3].extend(gyro.get_z_samples().get_values())
    if len(data_df[0]) > 0:
        return load_apim_xyz_sensor(SensorType.GYROSCOPE, data_df, "gyroscope",
                                    get_sensor_description_list(wrapped_packets, SensorType.GYROSCOPE))
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
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(gravity),
            data_df,
            SensorType.GRAVITY,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_gravity_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load gravity data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: gravity sensor data if it exists, None otherwise
    """
    data_df = [[], [], [], []]
    for packet in wrapped_packets:
        gravity = packet.get_sensors().get_gravity()
        if gravity and packet.get_sensors().validate_gravity():
            data_df[0].extend(gravity.get_timestamps().get_timestamps())
            data_df[1].extend(gravity.get_x_samples().get_values())
            data_df[2].extend(gravity.get_y_samples().get_values())
            data_df[3].extend(gravity.get_z_samples().get_values())
    if len(data_df[0]) > 0:
        return load_apim_xyz_sensor(SensorType.GRAVITY, data_df, "gravity",
                                    get_sensor_description_list(wrapped_packets, SensorType.GRAVITY))
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
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(orientation),
            data_df,
            SensorType.ORIENTATION,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_orientation_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load orientation data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: orientation sensor data if it exists, None otherwise
    """
    data_df = [[], [], [], []]
    for packet in wrapped_packets:
        orient = packet.get_sensors().get_orientation()
        if orient and packet.get_sensors().validate_orientation():
            data_df[0].extend(orient.get_timestamps().get_timestamps())
            data_df[1].extend(orient.get_x_samples().get_values())
            data_df[2].extend(orient.get_y_samples().get_values())
            data_df[3].extend(orient.get_z_samples().get_values())
    if len(data_df[0]) > 0:
        return load_apim_xyz_sensor(SensorType.ORIENTATION, data_df, "orientation",
                                    get_sensor_description_list(wrapped_packets, SensorType.ORIENTATION))
    return None


def load_apim_linear_accel(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load linear acceleration data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: linear acceleration sensor data if it exists, None otherwise
    """
    linear_accel = wrapped_packet.get_sensors().get_linear_acceleration()
    if linear_accel and wrapped_packet.get_sensors().validate_linear_acceleration():
        data_df = read_apim_xyz_sensor(linear_accel, "linear_accel")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(linear_accel),
            data_df,
            SensorType.LINEAR_ACCELERATION,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_linear_accel_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load linear acceleration data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: linear acceleration sensor data if it exists, None otherwise
    """
    data_df = [[], [], [], []]
    for packet in wrapped_packets:
        lin_acc = packet.get_sensors().get_linear_acceleration()
        if lin_acc and packet.get_sensors().validate_linear_acceleration():
            data_df[0].extend(lin_acc.get_timestamps().get_timestamps())
            data_df[1].extend(lin_acc.get_x_samples().get_values())
            data_df[2].extend(lin_acc.get_y_samples().get_values())
            data_df[3].extend(lin_acc.get_z_samples().get_values())
    if len(data_df[0]) > 0:
        return load_apim_xyz_sensor(SensorType.LINEAR_ACCELERATION, data_df, "linear_accel",
                                    get_sensor_description_list(wrapped_packets, SensorType.LINEAR_ACCELERATION))
    return None


def load_apim_rotation_vector(wrapped_packet: WrappedRedvoxPacketM) -> Optional[SensorData]:
    """
    load rotation vector data from a single wrapped packet
    :param wrapped_packet: packet with data to load
    :return: rotation vector sensor data if it exists, None otherwise
    """
    rotation = wrapped_packet.get_sensors().get_rotation_vector()
    if rotation and wrapped_packet.get_sensors().validate_rotation_vector():
        data_df = read_apim_xyz_sensor(rotation, "rotation_vector")
        sample_rate, sample_interval, sample_interval_std = get_sample_statistics(data_df)
        return SensorData(
            get_sensor_description(rotation),
            data_df,
            SensorType.ROTATION_VECTOR,
            sample_rate,
            sample_interval,
            sample_interval_std,
            False,
        )


def load_apim_rotation_vector_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load rotation vector data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: rotation vector sensor data if it exists, None otherwise
    """
    data_df = [[], [], [], []]
    for packet in wrapped_packets:
        rot_vec = packet.get_sensors().get_rotation_vector()
        if rot_vec and packet.get_sensors().validate_rotation_vector():
            data_df[0].extend(rot_vec.get_timestamps().get_timestamps())
            data_df[1].extend(rot_vec.get_x_samples().get_values())
            data_df[2].extend(rot_vec.get_y_samples().get_values())
            data_df[3].extend(rot_vec.get_z_samples().get_values())
    if len(data_df[0]) > 0:
        return load_apim_xyz_sensor(SensorType.ROTATION_VECTOR, data_df, "rotation_vector",
                                    get_sensor_description_list(wrapped_packets, SensorType.ROTATION_VECTOR))
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
        sample_rate = len(data_for_df) / wrapped_packet.get_packet_duration().total_seconds()
        return SensorData(
            "station health",
            data_df,
            SensorType.STATION_HEALTH,
            sample_rate,
            1 / sample_rate,
            np.nan if len(data_for_df) <= 1
            else dtu.microseconds_to_seconds(float(np.std(np.diff(data_df["timestamps"])))),
            False,
            )
    return None


def load_apim_health_from_list(wrapped_packets: List[WrappedRedvoxPacketM]) -> Optional[SensorData]:
    """
    load station health data from a list of wrapped packets
    :param wrapped_packets: packets with data to load
    :return: station health sensor data if it exists, None otherwise
    """
    data_for_df = [[], [], [], [], [], [], [], [], [], []]
    for packet in wrapped_packets:
        metrics = packet.get_station_information().get_station_metrics()
        timestamps = metrics.get_timestamps().get_timestamps()
        num_samples = len(timestamps)
        if num_samples > 0:
            data_for_df[0].extend(timestamps)
            bat_samples = metrics.get_battery().get_values()
            if len(bat_samples) != num_samples:
                bat_samples = np.full(num_samples, np.nan)
            data_for_df[1].extend(bat_samples)
            bat_cur_samples = metrics.get_battery_current().get_values()
            if len(bat_cur_samples) != num_samples:
                bat_cur_samples = np.full(num_samples, np.nan)
            data_for_df[2].extend(bat_cur_samples)
            temp_samples = metrics.get_temperature().get_values()
            if len(temp_samples) != num_samples:
                temp_samples = np.full(num_samples, np.nan)
            data_for_df[3].extend(temp_samples)
            net_samples = metrics.get_network_type().get_values()
            if len(net_samples) != num_samples:
                net_samples = np.full(num_samples, np.nan)
            data_for_df[4].extend(net_samples)
            net_str_samples = metrics.get_network_strength().get_values()
            if len(net_str_samples) != num_samples:
                net_str_samples = np.full(num_samples, np.nan)
            data_for_df[5].extend(net_str_samples)
            pow_samples = metrics.get_power_state().get_values()
            if len(pow_samples) != num_samples:
                pow_samples = np.full(num_samples, np.nan)
            data_for_df[6].extend(pow_samples)
            avail_ram_samples = metrics.get_available_ram().get_values()
            if len(avail_ram_samples) != num_samples:
                avail_ram_samples = np.full(num_samples, np.nan)
            data_for_df[7].extend(avail_ram_samples)
            avail_disk_samples = metrics.get_available_disk().get_values()
            if len(avail_disk_samples) != num_samples:
                avail_disk_samples = np.full(num_samples, np.nan)
            data_for_df[8].extend(avail_disk_samples)
            cell_samples = metrics.get_cell_service_state().get_values()
            if len(cell_samples) != num_samples:
                cell_samples = np.full(num_samples, np.nan)
            data_for_df[9].extend(cell_samples)
    if len(data_for_df[0]) > 0:
        data_for_df.insert(1, data_for_df[0].copy())
        return SensorData(
            "station health",
            pd.DataFrame(
                np.transpose(data_for_df),
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
            SensorType.STATION_HEALTH,
            calculate_stats=True
        )
    return None
