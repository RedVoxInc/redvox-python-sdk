import tempfile
from typing import Optional, Dict, Callable, List
import os
from pathlib import Path
from itertools import repeat
from glob import glob

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.common import sensor_reader_utils as srupa
from redvox.common import gap_and_pad_utils as gpu
from redvox.common import date_time_utils as dtu
from redvox.common.errors import RedVoxExceptions
from redvox.common.stats_helper import StatsContainer


# Maps a sensor type to a function that can extract that sensor for a particular packet.
__SENSOR_NAME_TO_SENSOR_FN: Dict[
    str,
    Optional[
        Callable[
            [RedvoxPacketM],
            srupa.SensorData,
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
                 scount: int, smint: float = np.nan, sstd: float = np.nan, data: Optional[pa.Table] = None):
        """
        initialize a summary of a sensor

        :param name: name of sensor
        :param stype: sensor type of summary
        :param start: start timestamp in microseconds since epoch utc of sensor
        :param srate: sample rate in Hz
        :param fdir: directory where files can be found
        :param scount: number of samples to read
        :param smint: mean interval of sample rate in seconds
        :param sstd: std dev of sample rate in seconds
        :param data: optional data as a pyarrow table
        """
        self.name = name
        self.stype = stype
        self.start = start
        self.srate_hz = srate
        self.fdir = fdir
        self.smint_s = smint
        self.sstd_s = sstd
        self.scount = scount
        self._data = data

    def to_dict(self) -> dict:
        """
        :return: dictionary representation of the data
        """
        return {
            "name": self.name,
            "stype": self.stype.name,
            "start": self.start,
            "srate_hz": self.srate_hz,
            "fdir": self.fdir,
            "smint_s": self.smint_s,
            "sstd_s": self.sstd_s,
            "scount": self.scount
        }

    def file_name(self) -> str:
        """
        :return: full file name of where the file should exist
        """
        return os.path.join(self.fdir, f"{self.stype.name}_{int(self.start)}.parquet")

    def fdir_stem(self) -> str:
        """
        :return: the name of the parent directory of the file
        """
        return Path(self.fdir).stem

    def clean_fdir(self):
        """
        remove all parquets in the self.fdir
        """
        for f in glob(os.path.join(self.fdir, "*.parquet")):
            os.remove(f)

    def write_data(self, clean_dir: bool = False) -> str:
        """
        write the data being summarized to disk, then remove the data from the object

        :param clean_dir: if True, remove any files in the dir before writing the data, default False
        :return: the path to the file where the data exists or empty string if data wasn't written
        """
        if self.check_data():
            os.makedirs(self.fdir, exist_ok=True)
            if clean_dir:
                self.clean_fdir()
            pq.write_table(self._data, self.file_name())
            self._data = None
            return self.file_name()
        return ""

    def check_data(self) -> bool:
        """
        :return: True if data exists as a property (also means not written to disk)
        """
        return True if self._data else False

    def data(self) -> Optional[pa.Table]:
        """
        :return: the data as pyarrow table or None if it doesn't exist
        """
        if self.check_data():
            return self._data
        if os.path.exists(self.file_name()):
            return pq.read_table(self.file_name())
        return pa.Table()


class AggregateSummary:
    """
    aggregate of summaries
    """
    def __init__(self, pya_sum: Optional[List[PyarrowSummary]] = None):
        if not pya_sum:
            pya_sum = []
        self.summaries = pya_sum

    def to_dict(self) -> dict:
        """
        :return: dictionary representation of all summaries
        """
        result = {}
        for ps in self.summaries:
            result[ps.stype.name] = ps.to_dict()
        return result

    def add_aggregate_summary(self, agg_sum: 'AggregateSummary', merge: bool = True):
        """
        adds another aggregate summary to this one

        :param agg_sum: another aggregate summary to add
        :param merge: if True, combine the summaries with the same type
        """
        if merge:
            for agg in agg_sum.summaries:
                self.add_summary(agg)
        else:
            self.summaries.extend(agg_sum.summaries)

    def add_summary(self, pya_sum: PyarrowSummary, merge: bool = True):
        """
        adds a summary to the aggregate

        :param pya_sum: the summary to add
        :param merge: if True, combine the summary with the same type
        """
        if merge:
            summaries = self.get_sensor(pya_sum.stype)
            if len(summaries) > 0:
                first_summary = summaries[0]
                stats = StatsContainer("temp")
                first_summary.srate_hz = (first_summary.scount + pya_sum.scount) / \
                                         ((first_summary.scount / first_summary.srate_hz) +
                                          (pya_sum.scount / pya_sum.srate_hz))
                stats.add(first_summary.smint_s, first_summary.sstd_s, first_summary.scount)
                stats.add(pya_sum.smint_s, pya_sum.sstd_s, pya_sum.scount)
                tbl = pa.concat_tables([first_summary.data(), pya_sum.data()])
                if first_summary.check_data():
                    first_summary._data = tbl
                else:
                    os.makedirs(first_summary.fdir, exist_ok=True)
                    pq.write_table(tbl, first_summary.file_name())
                    os.remove(pya_sum.file_name())
                first_summary.srate_hz = 1 / stats.mean_of_means()
                first_summary.scount = int(np.sum(np.nan_to_num(stats.count_array)))
                first_summary.smint_s = stats.mean_of_means()
                first_summary.sstd_s = stats.total_std_dev()
                return
        self.summaries.append(pya_sum)

    def get_audio(self) -> List[PyarrowSummary]:
        return [s for s in self.summaries if s.stype == srupa.SensorType.AUDIO]

    def get_non_audio(self) -> Dict[srupa.SensorType, List[PyarrowSummary]]:
        result = {}
        for k in self.sensor_types():
            if k != srupa.SensorType.AUDIO:
                result[k] = [s for s in self.summaries if s.stype == k]
        return result

    def get_non_audio_list(self) -> List[PyarrowSummary]:
        return [s for s in self.summaries if s.stype != srupa.SensorType.AUDIO]

    def get_sensor(self, stype: srupa.SensorType) -> List[PyarrowSummary]:
        return [s for s in self.summaries if s.stype == stype]

    def sensor_types(self) -> List[srupa.SensorType]:
        """
        :return: list of sensor types in self.summaries
        """
        result = []
        for s in self.summaries:
            if s.stype not in result:
                result.append(s.stype)
        return result


def stream_to_pyarrow(packets: List[RedvoxPacketM], out_dir: Optional[str] = None) -> AggregateSummary:
    """
    stream the packets to parquet files for later processing.

    :param packets: redvox packets to convert
    :param out_dir: optional directory to write the pyarrow files to; if None, don't write files.  default None
    :return: summary of the sensors, their data and their file locations if possible
    """
    summary = AggregateSummary()
    for k in map(packet_to_pyarrow, packets, repeat(out_dir)):
        for t in k.summaries:
            summary.add_summary(t, False)

    return summary


def packet_to_pyarrow(packet: RedvoxPacketM, out_dir: Optional[str] = None) -> AggregateSummary:
    """
    gets non-audio sensor information by writing it into folders with the sensor names to the out_dir

    :param packet: packet to extract data from
    :param out_dir: optional directory to write the pyarrow files to; if None, don't write files.  default None
    :return: sensor type: sensor name, start_timestamp, sample rate (if fixed, np.nan otherwise)
    """
    result = AggregateSummary()
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
            data.start = packet_start
            if out_dir:
                data.fdir = os.path.join(out_dir, f"{data.stype.name}_SUMMARY")
                data.write_data()
            result.add_summary(data)
    return result


def load_apim_audio(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load audio data from a single redvox packet

    :param packet: packet with data to load
    :return: audio sensor type, name,  data and sample rate
    """
    if srupa.__has_sensor(packet, srupa.__AUDIO_FIELD_NAME):
        audio_sensor: RedvoxPacketM.Sensors.Audio = packet.sensors.audio
        return PyarrowSummary(
            audio_sensor.sensor_description, srupa.SensorType.AUDIO, np.nan, audio_sensor.sample_rate, "",
            int(audio_sensor.samples.value_statistics.count), 1./audio_sensor.sample_rate, 0.,
            pa.Table.from_pydict({"microphone": np.array(audio_sensor.samples.values)})
        )
    return None


def load_apim_compressed_audio(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load compressed audio data from a single redvox packet

    :param packet: packet with data to load
    :return: compressed audio sensor data if it exists, None otherwise
    """
    if srupa.__has_sensor(packet, srupa.__COMPRESSED_AUDIO_FIELD_NAME):
        comp_audio: RedvoxPacketM.Sensors.CompressedAudio = (
            packet.sensors.compressed_audio
        )
        return PyarrowSummary(
            comp_audio.sensor_description, srupa.SensorType.COMPRESSED_AUDIO, np.nan,
            comp_audio.sample_rate, "", np.nan, 1./comp_audio.sample_rate, 0.,
            srupa.apim_compressed_audio_to_pyarrow(comp_audio)
        )
    return None


def load_apim_image(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load image data from a single redvox packet

    :param packet: packet with data to load
    :return: image sensor data if it exists, None otherwise
    """
    if srupa.__has_sensor(packet, srupa.__IMAGE_FIELD_NAME):
        image_sensor: RedvoxPacketM.Sensors.Image = packet.sensors.image
        timestamps = image_sensor.timestamps.timestamps
        if len(timestamps) > 1:
            sample_rate = 1.
        else:
            sample_rate = 1 / srupa.__packet_duration_s(packet)
        return PyarrowSummary(
            image_sensor.sensor_description, srupa.SensorType.IMAGE, np.nan, sample_rate, "",
            len(timestamps), 1./sample_rate, 0., srupa.apim_image_to_pyarrow(image_sensor)
        )
    return None


def load_apim_location(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load location data from a single packet

    :param packet: packet with data to load
    :return: location sensor data if it exists, None otherwise
    """
    if srupa.__has_sensor(packet, srupa.__LOCATION_FIELD_NAME):
        loc: RedvoxPacketM.Sensors.Location = packet.sensors.location
        timestamps = loc.timestamps.timestamps
        if len(timestamps) > 0:
            if len(timestamps) > 1:
                m_intv = np.mean(np.diff(timestamps))
                intv_std = np.std(np.diff(timestamps))
            else:
                m_intv = srupa.__packet_duration_us(packet)
                intv_std = 0.
            return PyarrowSummary(
                loc.sensor_description, srupa.SensorType.LOCATION, np.nan, np.nan, "",
                len(timestamps), m_intv, intv_std, srupa.apim_location_to_pyarrow(loc)
            )
    return None


def load_apim_best_location(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
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
            packet_len_s = srupa.__packet_duration_s(packet)
            return PyarrowSummary(
                loc.sensor_description, srupa.SensorType.BEST_LOCATION, np.nan, 1./packet_len_s, "",
                1, dtu.seconds_to_microseconds(packet_len_s), 0.,
                srupa.apim_best_location_to_pyarrow(best_loc,
                                                    packet.timing_information.packet_start_mach_timestamp),
            )
    return None


def load_apim_health(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
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
        return PyarrowSummary(
            "station health", srupa.SensorType.STATION_HEALTH, np.nan, sample_rate, "",
            len(timestamps), 1./sample_rate, 0., srupa.apim_health_to_pyarrow(metrics)
        )
    return None


def load_single(
        packet: RedvoxPacketM,
        sensor_type: srupa.SensorType,
) -> Optional[PyarrowSummary]:
    field_name: str = srupa.__SENSOR_TYPE_TO_FIELD_NAME[sensor_type]
    sensor_fn: Optional[
        Callable[[RedvoxPacketM], srupa.SensorData]
    ] = srupa.__SENSOR_TYPE_TO_SENSOR_FN[sensor_type]
    if srupa.__has_sensor(packet, field_name) and sensor_fn is not None:
        sensor = sensor_fn(packet)
        t = sensor.timestamps.timestamps
        if len(t) > 1:
            m_intv = np.mean(np.diff(t))
            intv_std = np.std(np.diff(t))
        else:
            m_intv = srupa.__packet_duration_us(packet)
            intv_std = 0.
        if len(t) > 0:
            return PyarrowSummary(
                sensor.sensor_description, sensor_type, np.nan, np.nan, "",
                len(t), m_intv, intv_std, srupa.read_apim_single_sensor(sensor, field_name)
            )
    return None


def load_apim_pressure(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load pressure data from a single redvox packet

    :param packet: packet with data to load
    :return: pressure sensor data if it exists, None otherwise
    """
    return load_single(packet, srupa.SensorType.PRESSURE)


def load_apim_light(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load light data from a single redvox packet

    :param packet: packet with data to load
    :return: light sensor data if it exists, None otherwise
    """
    return load_single(packet, srupa.SensorType.LIGHT)


def load_apim_proximity(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load proximity data from a single redvox packet

    :param packet: packet with data to load
    :return: proximity sensor data if it exists, None otherwise
    """
    return load_single(packet, srupa.SensorType.PROXIMITY)


def load_apim_ambient_temp(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load ambient temperature data from a single redvox packet

    :param packet: packet with data to load
    :return: ambient temperature sensor data if it exists, None otherwise
    """
    return load_single(packet, srupa.SensorType.AMBIENT_TEMPERATURE)


def load_apim_rel_humidity(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load relative humidity data from a single redvox packet

    :param packet: packet with data to load
    :return: relative humidity sensor data if it exists, None otherwise
    """
    return load_single(packet, srupa.SensorType.RELATIVE_HUMIDITY)


def load_xyz(
        packet: RedvoxPacketM,
        sensor_type: srupa.SensorType,
) -> Optional[PyarrowSummary]:
    field_name: str = srupa.__SENSOR_TYPE_TO_FIELD_NAME[sensor_type]
    sensor_fn: Optional[
        Callable[[RedvoxPacketM], srupa.SensorData]
    ] = srupa.__SENSOR_TYPE_TO_SENSOR_FN[sensor_type]
    if srupa.__has_sensor(packet, field_name) and sensor_fn is not None:
        sensor = sensor_fn(packet)
        t = sensor.timestamps.timestamps
        if len(t) > 1:
            m_intv = np.mean(np.diff(t))
            intv_std = np.std(np.diff(t))
        else:
            m_intv = srupa.__packet_duration_us(packet)
            intv_std = 0.
        if len(t) > 0:
            return PyarrowSummary(
                sensor.sensor_description, sensor_type, np.nan, np.nan, "",
                len(t), m_intv, intv_std, srupa.read_apim_xyz_sensor(sensor, field_name)
            )
    return None


def load_apim_accelerometer(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load accelerometer data from a single redvox packet

    :param packet: packet with data to load
    :return: accelerometer sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.ACCELEROMETER)


def load_apim_magnetometer(packet: RedvoxPacketM,) -> Optional[PyarrowSummary]:
    """
    load magnetometer data from a single redvox packet

    :param packet: packet with data to load
    :return: magnetometer sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.MAGNETOMETER)


def load_apim_gyroscope(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load gyroscope data from a single redvox packet

    :param packet: packet with data to load
    :return: gyroscope sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.GYROSCOPE)


def load_apim_gravity(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load gravity data from a single redvox packet

    :param packet: packet with data to load
    :return: gravity sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.GRAVITY)


def load_apim_orientation(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load orientation data from a single redvox packet

    :param packet: packet with data to load
    :return: orientation sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.ORIENTATION)


def load_apim_linear_accel(packet: RedvoxPacketM) -> Optional[PyarrowSummary]:
    """
    load linear acceleration data from a single redvox packet

    :param packet: packet with data to load
    :return: linear acceleration sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.LINEAR_ACCELERATION)


def load_apim_rotation_vector(packet: RedvoxPacketM,) -> Optional[PyarrowSummary]:
    """
    load rotation vector data from a single redvox packet

    :param packet: packet with data to load
    :return: rotation vector sensor data if it exists, None otherwise
    """
    return load_xyz(packet, srupa.SensorType.ROTATION_VECTOR)
