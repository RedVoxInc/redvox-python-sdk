import pickle
import os
from typing import Optional, List, Dict, Tuple, Union, Callable

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.dataset as ds

from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.common import date_time_utils as dtu
from redvox.common import gap_and_pad_utils_wpa as gpu
from redvox.common import io
from redvox.common import api_conversions as ac
from redvox.common import sensor_reader_utils_wpa as srupa
from redvox.common.station_wpa import StationPa
from redvox.common.station_utils import StationMetadata, StationPacketMetadata


# Maps a sensor type to a function that can extract that sensor for a particular packet.
__SENSOR_NAME_TO_SENSOR_FN: Dict[
    str,
    Optional[
        Callable[
            [RedvoxPacketM],
            srupa.Sensor,
        ]
    ],
] = {
    "health": None,
    "accelerometer": lambda packet: packet.sensors.accelerometer,
    "ambient_temperature": lambda packet: packet.sensors.ambient_temperature,
    "audio": lambda packet: packet.sensors.audio,
    "compressed_audio": lambda packet: packet.sensors.compressed_audio,
    "gravity": lambda packet: packet.sensors.gravity,
    "gyroscope": lambda packet: packet.sensors.gyroscope,
    "image": lambda packet: packet.sensors.image,
    "light": lambda packet: packet.sensors.light,
    "linear_acceleration": lambda packet: packet.sensors.linear_acceleration,
    "location": lambda packet: packet.sensors.location,
    "best_location": lambda packet: packet.sensors.location,
    "magnetometer": lambda packet: packet.sensors.magnetometer,
    "orientation": lambda packet: packet.sensors.orientation,
    "pressure": lambda packet: packet.sensors.pressure,
    "proximity": lambda packet: packet.sensors.proximity,
    "relative_humidity": lambda packet: packet.sensors.relative_humidity,
    "rotation_vector": lambda packet: packet.sensors.rotation_vector,
    "infrared": lambda packet: packet.sensors.proximity,
}


packet_schema = pa.schema([("packet_start_mach_timestamp", pa.float64()),
                           ("packet_end_mach_timestamp", pa.float64()),
                           ("packet_start_os_timestamp", pa.float64()),
                           ("packet_end_os_timestamp", pa.float64()),
                           ("timing_info_score", pa.int64())
                           ])

sensor_schema = pa.schema([("description", pa.string()),
                           ("first_timestamp", pa.float64())
                           ])

station_schema = pa.schema([("id", pa.string()), ("uuid", pa.string()),
                            ("start_time", pa.float64()), ("api", pa.float64()),
                            ("sub_api", pa.float64()), ("make", pa.string()),
                            ("model", pa.string()), ("os", pa.int64()), ("os_version", pa.string()),
                            ("app", pa.string()), ("app_version", pa.string()),
                            ("is_private", pa.bool_()), ("packet_duration_s", pa.float64()),
                            ("station_description", pa.string())])


def packet_to_pyarrow(packet: RedvoxPacketM) -> Dict[str, Tuple[Tuple[str, float], pa.Table]]:
    result = {}
    funcs = [
        load_apim_audio,
        load_apim_compressed_audio,
        load_apim_image,
        load_apim_best_location,
        load_apim_location,
        load_apim_pressure,
        load_apim_light,
        load_apim_ambient_temp,
        load_apim_rel_humidity,
        load_apim_proximity,
        load_apim_accelerometer,
        load_apim_gyroscope,
        load_apim_magnetometer,
        load_apim_gravity,
        load_apim_linear_accel,
        load_apim_orientation,
        load_apim_rotation_vector,
        load_apim_health,
    ]
    sensors = map(lambda fn: fn(packet), funcs)
    for data in sensors:
        if data:
            result[data[0]] = ((data[1], packet.timing_information.packet_start_mach_timestamp), data[2])
    return result


def load_apim_audio(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load audio data from a single redvox packet

    :param packet: packet with data to load
    :return: audio sensor data if it exists, None otherwise
    """
    if srupa.__has_sensor(packet, srupa.__AUDIO_FIELD_NAME):
        audio_sensor: RedvoxPacketM.Sensors.Audio = packet.sensors.audio

        timestamps: np.ndarray = gpu.calc_evenly_sampled_timestamps(
            audio_sensor.first_sample_timestamp,
            len(audio_sensor.samples.values),
            dtu.seconds_to_microseconds(1.0 / audio_sensor.sample_rate),
        )
        return ("audio", audio_sensor.sensor_description,
                pa.Table.from_pydict({"timestamps": timestamps,
                                      "microphone": np.array(audio_sensor.samples.values)})
                )
    return None


def load_apim_compressed_audio(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load compressed audio data from a single redvox packet

    :param packet: packet with data to load
    :return: compressed audio sensor data if it exists, None otherwise
    """
    if srupa.__has_sensor(packet, srupa.__COMPRESSED_AUDIO_FIELD_NAME):
        comp_audio: RedvoxPacketM.Sensors.CompressedAudio = (
            packet.sensors.compressed_audio
        )
        return ("compressed_audio", comp_audio.sensor_description,
                pa.Table.from_pydict(
                    dict(zip(["timestamps", "compressed_audio", "audio_codec"],
                             [
                                 comp_audio.first_sample_timestamp,
                                 np.array(list(comp_audio.audio_bytes)),
                                 comp_audio.audio_codec,
                             ]
                             )
                         )
                )
                )
    return None


def load_apim_image(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load image data from a single redvox packet

    :param packet: packet with data to load
    :return: image sensor data if it exists, None otherwise
    """
    if srupa.__has_sensor(packet, srupa.__IMAGE_FIELD_NAME):
        image_sensor: RedvoxPacketM.Sensors.Image = packet.sensors.image
        timestamps = image_sensor.timestamps.timestamps
        codecs = np.full(len(timestamps), image_sensor.image_codec)
        return ("image", image_sensor.sensor_description,
                pa.Table.from_pydict(
                    dict(zip(["timestamps", "image", "image_codec"],
                             [timestamps, image_sensor.samples, codecs]
                             )
                         )
                )
                )
    return None


def load_apim_location(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load location data from a single packet

    :param packet: packet with data to load
    :return: location sensor data if it exists, None otherwise
    """
    if srupa.__has_sensor(packet, srupa.__LOCATION_FIELD_NAME):
        loc: RedvoxPacketM.Sensors.Location = packet.sensors.location
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
            data_for_df = [[], [], [], [], [], [], [], [], [], [], [], [], []]
            for i in range(len(timestamps)):
                data_for_df[0].append(timestamps[i])
                data_for_df[1].append(np.nan if len(gps_timestamps) <= i else gps_timestamps[i])
                data_for_df[2].append(lat_samples[i])
                data_for_df[3].append(lon_samples[i])
                data_for_df[4].append(np.nan if len(alt_samples) <= i else alt_samples[i])
                data_for_df[5].append(np.nan if len(spd_samples) <= i else spd_samples[i])
                data_for_df[6].append(np.nan if len(bear_samples) <= i else bear_samples[i])
                data_for_df[7].append(np.nan if len(hor_acc_samples) <= i else hor_acc_samples[i])
                data_for_df[8].append(np.nan if len(vert_acc_samples) <= i else vert_acc_samples[i])
                data_for_df[9].append(np.nan if len(spd_acc_samples) <= i else spd_acc_samples[i])
                data_for_df[10].append(np.nan if len(bear_acc_samples) <= i else bear_acc_samples[i])
                data_for_df[11].append(np.nan if len(loc_prov_samples) <= i else loc_prov_samples[i])
        else:
            return None
        return ("location", loc.sensor_description,
                pa.Table.from_pydict(dict(zip([
                    "timestamps",
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
                ], data_for_df)))
                )
    return None


def load_apim_best_location(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load best location data from a single redvox packet

    :param packet: packet with data to load
    :return: best location sensor data if it exists, None otherwise
    """
    if srupa.__has_sensor(packet, srupa.__LOCATION_FIELD_NAME):
        loc: RedvoxPacketM.Sensors.Location = packet.sensors.location
        if loc.HasField("last_best_location") or loc.HasField("overall_best_location"):
            best_loc: RedvoxPacketM.Sensors.Location.BestLocation
            if loc.HasField("last_best_location"):
                best_loc = loc.last_best_location
            else:
                best_loc = loc.overall_best_location
            return ("best_location", loc.sensor_description,
                    pa.Table.from_pydict(
                        dict(zip([
                            "timestamps",
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
                        ],
                            [
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
                    )
    return None


def load_apim_health(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load station health data from a single redvox packet

    :param packet: packet with data to load
    :return: station health data if it exists, None otherwise
    """
    metrics: RedvoxPacketM.StationInformation.StationMetrics = (
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
        data_for_df = []
        for i in range(len(timestamps)):
            new_entry = [
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
        return ("health",  "station health",
                pa.Table.from_pydict(dict(zip([
                    "timestamps",
                    "battery_charge_remaining",
                    "battery_current_strength",
                    "internal_temp_c",
                    "network_type",
                    "network_strength",
                    "power_state",
                    "avail_ram",
                    "avail_disk",
                    "cell_service",
                ], data_for_df)))
                )
    return None


def read_apim_single_sensor(
        sensor: RedvoxPacketM.Sensors.Single, column_id: str
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
        return pa.Table.from_pydict({"timestamps": timestamps, column_id: np.array(sensor.samples.values)})
    except AttributeError:
        raise


def load_single(
        packet: RedvoxPacketM,
        sensor_type: str,
) -> Optional[Tuple[str, str, pa.Table]]:
    sensor_fn: Optional[
        Callable[[RedvoxPacketM], srupa.Sensor]
    ] = __SENSOR_NAME_TO_SENSOR_FN[sensor_type]
    if srupa.__has_sensor(packet, sensor_type) and sensor_fn is not None:
        sensor = sensor_fn(packet)
        return sensor_type, sensor.sensor_description, read_apim_single_sensor(sensor, sensor_type)


def load_apim_pressure(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load pressure data from a single redvox packet

    :param packet: packet with data to load
    :return: pressure sensor data if it exists, None otherwise
    """
    return load_single(packet, "pressure")


def load_apim_light(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load light data from a single redvox packet

    :param packet: packet with data to load
    :return: light sensor data if it exists, None otherwise
    """
    return load_single(packet, "light")


def load_apim_proximity(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load proximity data from a single redvox packet

    :param packet: packet with data to load
    :return: proximity sensor data if it exists, None otherwise
    """
    return load_single(packet, "proximity")


def load_apim_ambient_temp(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load ambient temperature data from a single redvox packet

    :param packet: packet with data to load
    :return: ambient temperature sensor data if it exists, None otherwise
    """
    return load_single(
        packet,
        "ambient_temperature",
    )


def load_apim_rel_humidity(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load relative humidity data from a single redvox packet

    :param packet: packet with data to load
    :return: relative humidity sensor data if it exists, None otherwise
    """
    return load_single(
        packet,
        "relative_humidity",
    )


def read_apim_xyz_sensor(
        sensor: RedvoxPacketM.Sensors.Xyz, column_id: str
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
            f"{column_id}_x",
            f"{column_id}_y",
            f"{column_id}_z",
        ]
        return pa.Table.from_pydict(
            dict(zip(columns, [timestamps,
                               np.array(sensor.x_samples.values),
                               np.array(sensor.y_samples.values),
                               np.array(sensor.z_samples.values),]
                     )
                 )
        )
    except AttributeError:
        raise


def load_xyz(
        packet: RedvoxPacketM,
        sensor_type: str,
) -> Optional[Tuple[str, str, pa.Table]]:
    sensor_fn: Optional[
        Callable[[RedvoxPacketM], srupa.Sensor]
    ] = __SENSOR_NAME_TO_SENSOR_FN[sensor_type]
    if srupa.__has_sensor(packet, sensor_type) and sensor_fn is not None:
        sensor = sensor_fn(packet)
        return sensor_type, sensor.sensor_description, read_apim_xyz_sensor(sensor, sensor_type)


def load_apim_accelerometer(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load accelerometer data from a single redvox packet

    :param packet: packet with data to load
    :return: accelerometer sensor data if it exists, None otherwise
    """
    return load_xyz(
        packet,
        "accelerometer",
    )


def load_apim_magnetometer(packet: RedvoxPacketM,) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load magnetometer data from a single redvox packet

    :param packet: packet with data to load
    :return: magnetometer sensor data if it exists, None otherwise
    """
    return load_xyz(
        packet,
        "magnetometer",
    )


def load_apim_gyroscope(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load gyroscope data from a single redvox packet

    :param packet: packet with data to load
    :return: gyroscope sensor data if it exists, None otherwise
    """
    return load_xyz(packet, "gyroscope")


def load_apim_gravity(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load gravity data from a single redvox packet

    :param packet: packet with data to load
    :return: gravity sensor data if it exists, None otherwise
    """
    return load_xyz(packet, "gravity")


def load_apim_orientation(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load orientation data from a single redvox packet

    :param packet: packet with data to load
    :return: orientation sensor data if it exists, None otherwise
    """
    return load_xyz(
        packet,
        "orientation",
    )


def load_apim_linear_accel(packet: RedvoxPacketM) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load linear acceleration data from a single redvox packet

    :param packet: packet with data to load
    :return: linear acceleration sensor data if it exists, None otherwise
    """
    return load_xyz(
        packet,
        "linear_acceleration",
    )


def load_apim_rotation_vector(packet: RedvoxPacketM,) -> Optional[Tuple[str, str, pa.Table]]:
    """
    load rotation vector data from a single redvox packet

    :param packet: packet with data to load
    :return: rotation vector sensor data if it exists, None otherwise
    """
    return load_xyz(
        packet,
        "rotation_vector",
    )


class PacketToPyarrow:
    def __init__(self, base_dir: str):
        self.base_dir: str = base_dir
        self.stations: Dict[str, StationPa] = {}

    def write_sensor_tables(self, id_str: str, packet: RedvoxPacketM):
        out_dir = os.path.join(self.base_dir, id_str)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        for s_name, data in packet_to_pyarrow(packet).items():
            sensor_dir = os.path.join(out_dir, s_name)
            if not os.path.exists(sensor_dir):
                os.makedirs(sensor_dir)
            pq.write_table(data[1],
                           os.path.join(sensor_dir,
                                        f"{int(data[0][1])}.parquet"))

    def add_packet(self, packet: RedvoxPacketM):
        # noinspection Mypy
        pyary_string = \
            packet.station_information.id + packet.station_information.uuid \
            + int(packet.timing_information.app_start_mach_timestamp).__str__()
        if pyary_string not in self.stations.keys():
            # define directory for temporary file storage, default current dir
            # keep the metadata in memory, but write sensors to temporary files
            # have functions use the metadata to identify the files to read
            # column read is easy: pq.read_table('example.parquet', columns=['one', 'three'])
            # write table is easy: pq.write_table(pa_table, dest_file)
            station = StationPa(station_id=packet.station_information.id, uuid=packet.station_information.uuid,
                                start_time=packet.timing_information.app_start_mach_timestamp)
            station.metadata = StationMetadata("Redvox", packet)
            station.packet_metadata = [StationPacketMetadata(packet)]
            self.stations[pyary_string] = station
        else:
            self.stations[pyary_string].packet_metadata.append(StationPacketMetadata(packet))
        self.write_sensor_tables(pyary_string, packet)

    def read_files(self, indexf: io.Index):
        """
        read all files in an index using pyarrow
        :param indexf: the index to read from
        """
        result = []
        # noinspection PyTypeChecker
        for packet_900 in indexf.stream_raw(
                io.ReadFilter.empty().with_api_versions({io.ApiVersion.API_900})
        ):
            # noinspection Mypy
            packet = ac.convert_api_900_to_1000_raw(packet_900)
            result.append(self.add_packet(packet))
        # noinspection PyTypeChecker
        for packet in indexf.stream_raw(
                io.ReadFilter.empty().with_api_versions({io.ApiVersion.API_1000})
        ):
            result.append(self.add_packet(packet))
        return self
