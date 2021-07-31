from typing import Optional, Dict, Tuple, Callable, List
import os
from itertools import repeat
from glob import glob

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.common import sensor_reader_utils_wpa as srupa
from redvox.common import gap_and_pad_utils_wpa as gpu
from redvox.common import date_time_utils as dtu
from redvox.common.io import IndexEntry


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


class PyarrowSummary:
    def __init__(self, name: str, stype: srupa.SensorType, start: float, srate: float, fdir: str,
                 data: Optional[pa.Table] = None):
        self.name = name
        self.stype = stype
        self.start = start
        self.srate_hz = srate
        self.fdir = fdir
        self._data = data

    def file_name(self) -> str:
        return os.path.join(self.fdir, f"{self.stype.name}_{int(self.start)}.parquet")

    def clean_fdir(self):
        """
        remove all parquets in the self.fdir
        """
        for f in glob(os.path.join(self.fdir, "*.parquet")):
            os.remove(f)

    def write_data(self) -> str:
        """
        write the summary's data to disk, then removes the data from the object
        :return: the path to the file where the data exists or empty string if data wasn't written
        """
        if self.check_data():
            os.makedirs(self.fdir, exist_ok=True)
            pq.write_table(self._data, self.file_name())
            self._data = None
            return self.file_name()
        return ""

    def check_data(self) -> bool:
        """
        :return: True if data is not written to disk yet
        """
        if self._data:
            return True
        return False


class ConversionSummary:
    def __init__(self, pya_sum: Optional[List[PyarrowSummary]] = None):
        self.summaries = pya_sum

    def add_summary(self, pya_sum: PyarrowSummary):
        self.summaries.append(pya_sum)

    def get_audio(self) -> Optional[PyarrowSummary]:
        for s in self.summaries:
            if s.stype == srupa.SensorType.AUDIO:
                return s
        return None

    def get_non_audio(self) -> List[PyarrowSummary]:
        return [s for s in self.summaries if s.stype != srupa.SensorType.AUDIO]

    def sensor_types(self) -> List[srupa.SensorType]:
        """
        :return: list of sensor types in self.summaries
        """
        return [s.type for s in self.summaries]


def stream_to_pyarrow(packets: List[RedvoxPacketM], out_dir: Optional[str] = None) -> ConversionSummary:
    """
    stream the packets to parquet files for later processing.
    :param packets: redvox packets to convert
    :param out_dir: optional directory to write the pyarrow files to
    :return: summary of the sensors, their data and their file locations
    """
    summary = ConversionSummary()
    for k in map(packet_to_pyarrow, packets, repeat(out_dir)):
        for t in k.summaries:
            if t.stype not in summary.sensor_types():
                summary.add_summary(t)

    audio: PyarrowSummary = summary.get_audio()
    audio_files = glob(os.path.join(audio.fdir, "*.parquet"))
    packet_info = []
    for f in audio_files:
        # Attempt to parse file name parts
        split_name = f.split("_")
        ts_str: str = split_name[1].split(".")[0]
        packet_info.append((int(ts_str), pq.read_table(f)))

    gp_result = gpu.fill_audio_gaps(
        packet_info, dtu.seconds_to_microseconds(1 / audio.srate_hz)
    )
    if audio:
        audio_data = PyarrowSummary(audio.name, srupa.SensorType.AUDIO, audio.start, audio.srate_hz, audio.fdir,
                                    gp_result.result)
        audio_data.write_data()
        summary.add_summary(audio_data)

    non_audio = summary.get_non_audio()
    if len(non_audio) > 0:
        for na in non_audio:
            sensor_data = PyarrowSummary(na.name, na.stype, na.start, na.srate_hz, na.fdir)
            summary.add_summary(sensor_data)

    return summary


def packet_to_pyarrow(packet: RedvoxPacketM, out_dir: str) -> ConversionSummary:
    """
    gets non-audio sensor information by writing it folders with the sensor names to the out_dir

    :param packet: packet to extract data from
    :param out_dir: the directory to write the pyarrow files to
    :return: sensor type: sensor name, start_timestamp, sample rate (if fixed, np.nan otherwise)
    """
    result = ConversionSummary()
    packet_start = int(packet.timing_information.packet_start_mach_timestamp)
    funcs = [
        load_apim_audio,
        load_apim_compressed_audio,
        load_apim_image,
        load_apim_health,
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
    ]
    sensors = map(lambda fn: fn(packet), funcs)
    for data in sensors:
        if data:
            sensor_dir = os.path.join(out_dir, data[0].name)
            if not os.path.exists(sensor_dir):
                os.mkdir(sensor_dir)
            r = PyarrowSummary(data[1], data[0], packet_start, data[3], sensor_dir, data[2])
            r.write_data()
            result.add_summary(r)
    return result


def load_apim_audio(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load audio data from a single redvox packet

    :param packet: packet with data to load
    :return: audio sensor type, name,  data and sample rate
    """
    if srupa.__has_sensor(packet, srupa.__AUDIO_FIELD_NAME):
        audio_sensor: RedvoxPacketM.Sensors.Audio = packet.sensors.audio
        return (srupa.SensorType.AUDIO,
                audio_sensor.sensor_description,
                pa.Table.from_pydict({"microphone": np.array(audio_sensor.samples.values)}),
                audio_sensor.sample_rate
                )
    return None


def load_apim_compressed_audio(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load compressed audio data from a single redvox packet

    :param packet: packet with data to load
    :return: compressed audio sensor data if it exists, None otherwise
    """
    if srupa.__has_sensor(packet, srupa.__COMPRESSED_AUDIO_FIELD_NAME):
        comp_audio: RedvoxPacketM.Sensors.CompressedAudio = (
            packet.sensors.compressed_audio
        )
        return (srupa.SensorType.COMPRESSED_AUDIO,
                comp_audio.sensor_description,
                srupa.apim_compressed_audio_to_pyarrow(comp_audio),
                comp_audio.sample_rate
                )
    return None


def load_apim_image(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load image data from a single redvox packet

    :param packet: packet with data to load
    :return: image sensor data if it exists, None otherwise
    """
    if srupa.__has_sensor(packet, srupa.__IMAGE_FIELD_NAME):
        image_sensor: RedvoxPacketM.Sensors.Image = packet.sensors.image
        timestamps = image_sensor.timestamps.timestamps
        if len(timestamps) > 1:
            sample_rate = 1
        else:
            sample_rate = 1 / srupa.__packet_duration_s(packet)
        return (srupa.SensorType.IMAGE, image_sensor.sensor_description,
                srupa.apim_image_to_pyarrow(image_sensor), sample_rate
                )
    return None


def load_apim_location(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load location data from a single packet

    :param packet: packet with data to load
    :return: location sensor data if it exists, None otherwise
    """
    if srupa.__has_sensor(packet, srupa.__LOCATION_FIELD_NAME):
        loc: RedvoxPacketM.Sensors.Location = packet.sensors.location
        timestamps = loc.timestamps.timestamps
        if len(timestamps) > 0:
            return srupa.SensorType.LOCATION, loc.sensor_description, srupa.apim_location_to_pyarrow(loc), np.nan
    return None


def load_apim_best_location(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
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
            return (srupa.SensorType.BEST_LOCATION,
                    loc.sensor_description,
                    srupa.apim_best_location_to_pyarrow(best_loc,
                                                        packet.timing_information.packet_start_mach_timestamp),
                    np.nan
                    )
    return None


def load_apim_health(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load station health data from a single redvox packet

    :param packet: packet with data to load
    :return: station health data if it exists, None otherwise
    """
    metrics: RedvoxPacketM.StationInformation.StationMetrics = (
        packet.station_information.station_metrics
    )
    timestamps = metrics.timestamps.timestamps
    if len(timestamps) > 1:
        sample_rate = 1
    else:
        sample_rate = 1 / srupa.__packet_duration_s(packet)
    if len(timestamps) > 0:
        data_for_df = srupa.apim_health_to_pyarrow(metrics)
        return srupa.SensorType.STATION_HEALTH, "station health", data_for_df, sample_rate
    return None


def load_single(
        packet: RedvoxPacketM,
        sensor_type: srupa.SensorType,
) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    field_name: str = srupa.__SENSOR_TYPE_TO_FIELD_NAME[sensor_type]
    sensor_fn: Optional[
        Callable[[RedvoxPacketM], srupa.Sensor]
    ] = srupa.__SENSOR_TYPE_TO_SENSOR_FN[sensor_type]
    if srupa.__has_sensor(packet, field_name) and sensor_fn is not None:
        sensor = sensor_fn(packet)
        return sensor_type, sensor.sensor_description, srupa.read_apim_single_sensor(sensor, field_name), np.nan


def load_apim_pressure(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load pressure data from a single redvox packet

    :param packet: packet with data to load
    :return: pressure sensor data if it exists, None otherwise
    """
    return load_single(packet, srupa.SensorType.PRESSURE)


def load_apim_light(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load light data from a single redvox packet

    :param packet: packet with data to load
    :return: light sensor data if it exists, None otherwise
    """
    return load_single(packet, srupa.SensorType.LIGHT)


def load_apim_proximity(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load proximity data from a single redvox packet

    :param packet: packet with data to load
    :return: proximity sensor data if it exists, None otherwise
    """
    return load_single(packet, srupa.SensorType.PROXIMITY)


def load_apim_ambient_temp(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load ambient temperature data from a single redvox packet

    :param packet: packet with data to load
    :return: ambient temperature sensor data if it exists, None otherwise
    """
    return load_single(packet, srupa.SensorType.AMBIENT_TEMPERATURE)


def load_apim_rel_humidity(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load relative humidity data from a single redvox packet

    :param packet: packet with data to load
    :return: relative humidity sensor data if it exists, None otherwise
    """
    return load_single(packet, srupa.SensorType.RELATIVE_HUMIDITY)


def load_xyz(
        packet: RedvoxPacketM,
        sensor_type: srupa.SensorType,
) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    field_name: str = srupa.__SENSOR_TYPE_TO_FIELD_NAME[sensor_type]
    sensor_fn: Optional[
        Callable[[RedvoxPacketM], srupa.Sensor]
    ] = srupa.__SENSOR_TYPE_TO_SENSOR_FN[sensor_type]
    if srupa.__has_sensor(packet, field_name) and sensor_fn is not None:
        sensor = sensor_fn(packet)
        return sensor_type, sensor.sensor_description, srupa.read_apim_xyz_sensor(sensor, field_name), np.nan


def load_apim_accelerometer(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load accelerometer data from a single redvox packet

    :param packet: packet with data to load
    :return: accelerometer sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.ACCELEROMETER)


def load_apim_magnetometer(packet: RedvoxPacketM,) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load magnetometer data from a single redvox packet

    :param packet: packet with data to load
    :return: magnetometer sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.MAGNETOMETER)


def load_apim_gyroscope(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load gyroscope data from a single redvox packet

    :param packet: packet with data to load
    :return: gyroscope sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.GYROSCOPE)


def load_apim_gravity(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load gravity data from a single redvox packet

    :param packet: packet with data to load
    :return: gravity sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.GRAVITY)


def load_apim_orientation(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load orientation data from a single redvox packet

    :param packet: packet with data to load
    :return: orientation sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.ORIENTATION)


def load_apim_linear_accel(packet: RedvoxPacketM) -> Optional[Tuple[srupa.SensorType, str, pa.Table]]:
    """
    load linear acceleration data from a single redvox packet

    :param packet: packet with data to load
    :return: linear acceleration sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.LINEAR_ACCELERATION)


def load_apim_rotation_vector(packet: RedvoxPacketM,) -> Optional[Tuple[srupa.SensorType, str, pa.Table, float]]:
    """
    load rotation vector data from a single redvox packet

    :param packet: packet with data to load
    :return: rotation vector sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.ROTATION_VECTOR)
