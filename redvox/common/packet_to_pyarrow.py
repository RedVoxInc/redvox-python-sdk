from typing import Optional, Dict, Callable, List, Tuple
import os
from pathlib import Path
from itertools import repeat
from glob import glob

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.common import sensor_reader_utils as srupa
from redvox.common import date_time_utils as dtu
from redvox.common import gap_and_pad_utils as gpu
from redvox.common.sensor_data import SensorType
from redvox.common.errors import RedVoxExceptions


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


@dataclass_json
@dataclass
class PyarrowSummary:
    """
    Summary of a sensor using Pyarrow Tables or parquet files to store the data

    Properties:
        name: str, name of sensor

        stype: SensorType, sensor type of summary

        start: float, start timestamp in microseconds since epoch utc of sensor

        srate: float, sample rate in Hz

        fdir: str, directory where parquet files can be found

        scount: int, number of samples to read

        smint: float, mean interval of sample rate in seconds

        sstd: float, std dev of sample rate in seconds

        _data: optional data as a Pyarrow Table
    """
    name: str
    stype: srupa.SensorType
    start: float
    srate_hz: float
    fdir: str
    scount: int
    smint_s: float = np.nan
    sstd_s: float = np.nan
    _data: Optional[pa.Table] = None

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
        :return: full path and file name of where the file should exist
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
        :return: the data as a Pyarrow Table
        """
        if self.check_data():
            return self._data
        if os.path.exists(self.file_name()):
            return pq.read_table(self.file_name())
        return pa.Table.from_pydict({})


@dataclass_json
@dataclass
class AggregateSummary:
    """
    aggregate of summaries

    properties:
        summaries: the summaries of sensors
        gaps: gaps in audio data as a list of tuples of start and end time
    """
    summaries: List[PyarrowSummary] = field(default_factory=lambda: [])
    gaps: List[Tuple[float, float]] = field(default_factory=lambda: [])
    errors: RedVoxExceptions = RedVoxExceptions("AggregateSummary")

    def to_dict(self) -> dict:
        """
        :return: dictionary representation of all summaries
        """
        result = {}
        for ps in self.summaries:
            result[ps.stype.name] = ps.to_dict()
        return result

    @staticmethod
    def from_dict(summary_dict: dict) -> "AggregateSummary":
        """
        :param summary_dict: dictionary to load data from
        :return: AggregateSummary from a dictionary
        """
        result = AggregateSummary()
        for v in summary_dict.values():
            result.summaries.append(PyarrowSummary(v["name"], SensorType[v["stype"]], v["start"], v["srate_hz"],
                                                   v["fdir"], v["scount"], v["smint_s"], v["sstd_s"]))
        return result

    def add_aggregate_summary(self, agg_sum: 'AggregateSummary'):
        """
        adds another aggregate summary to this one

        :param agg_sum: another aggregate summary to add
        """
        self.summaries.extend(agg_sum.summaries)

    def add_summary(self, pya_sum: PyarrowSummary):
        """
        adds a summary to the aggregate

        :param pya_sum: the summary to add
        """
        self.summaries.append(pya_sum)

    def merge_audio_summaries(self):
        """
        combines and replaces all Audio summaries into a single summary; also adds any gaps in the data
        """
        pckt_info = []
        audio_lst = self.get_audio()
        frst_audio = audio_lst[0]
        use_mem = frst_audio.check_data()
        for adl in audio_lst:
            pckt_info.append((int(adl.start), adl.data()))

        audio_data = gpu.fill_audio_gaps2(pckt_info,
                                          dtu.seconds_to_microseconds(1 / frst_audio.srate_hz)
                                          )
        tbl = audio_data.create_timestamps()
        frst_audio = PyarrowSummary(frst_audio.name, frst_audio.stype, frst_audio.start, frst_audio.srate_hz,
                                    frst_audio.fdir, tbl.num_rows, frst_audio.smint_s, frst_audio.sstd_s,
                                    tbl)
        if not use_mem:
            frst_audio.write_data(True)

        self.gaps = audio_data.gaps
        self.summaries = self.get_non_audio_list()
        self.add_summary(frst_audio)

    def merge_non_audio_summaries(self):
        """
        combines and replaces all summaries per type except for audio summaries
        """
        smrs_dict = {}
        for smry in self.summaries:
            if smry.stype != SensorType.AUDIO:
                if smry.stype in smrs_dict.keys():
                    smrs_dict[smry.stype].append(smry)
                else:
                    smrs_dict[smry.stype] = [smry]
        self.summaries = self.get_audio()
        for styp, smrys in smrs_dict.items():
            if len(smrys) > 0:
                combined_mint = np.mean([smrs.smint_s for smrs in smrys])
                combined_std = np.mean([smrs.sstd_s for smrs in smrys])
                first_summary = smrys.pop(0)
                tbl = first_summary.data()
                if not first_summary.check_data():
                    os.makedirs(first_summary.fdir, exist_ok=True)
                for smrs in smrys:
                    tbl = pa.concat_tables([tbl, smrs.data()])
                    if not first_summary.check_data():
                        os.remove(smrs.file_name())
                if first_summary.check_data():
                    first_summary._data = tbl
                else:
                    pq.write_table(tbl, first_summary.file_name())
                # sort data by timestamps
                tbl = pc.take(tbl, pc.sort_indices(tbl, sort_keys=[("timestamps", "ascending")]))
                timestamps = tbl["timestamps"].to_numpy()
                if len(timestamps) > 1:
                    mnint = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
                    stdint = dtu.microseconds_to_seconds(float(np.std(np.diff(timestamps))))
                else:
                    mnint = np.nan
                    stdint = np.nan
                if not combined_mint + combined_std > mnint > combined_mint - combined_std:
                    self.errors.append(f"Mean interval s of combined {styp.name} sensor does not match the "
                                       f"compilation of individual mean interval s per packet.  Will use compilation "
                                       f"of individual values.")
                    mnint = combined_mint
                    stdint = combined_std
                single_smry = PyarrowSummary(first_summary.name, styp, first_summary.start,
                                             1 / mnint, first_summary.fdir, tbl.num_rows, mnint, stdint,
                                             first_summary.data() if first_summary.check_data() else None
                                             )
                self.summaries.append(single_smry)

    def merge_summaries_of_type(self, stype: SensorType):
        """
        combines and replaces multiple summaries of one SensorType into a single one

        *caution: using this on an audio sensor may cause data validation issues*

        :param stype: the type of sensor to combine
        """
        smrs = []
        other_smrs = []
        for smry in self.summaries:
            if smry.stype == stype:
                smrs.append(smry)
            else:
                other_smrs.append(smry)
        first_summary = smrs.pop(0)
        tbl = first_summary.data()
        if not first_summary.check_data():
            os.makedirs(first_summary.fdir, exist_ok=True)
        for smrys in smrs:
            tbl = pa.concat_tables([first_summary.data(), smrys.data()])
            if first_summary.check_data():
                first_summary._data = tbl
            else:
                pq.write_table(tbl, first_summary.file_name())
                os.remove(smrys.file_name())
        mnint = dtu.microseconds_to_seconds(float(np.mean(np.diff(tbl["timestamps"].to_numpy()))))
        stdint = dtu.microseconds_to_seconds(float(np.std(np.diff(tbl["timestamps"].to_numpy()))))
        single_smry = PyarrowSummary(first_summary.name, first_summary.stype, first_summary.start,
                                     1 / mnint, first_summary.fdir, tbl.num_rows, mnint, stdint,
                                     first_summary.data() if first_summary.check_data() else None
                                     )
        self.summaries = other_smrs
        self.summaries.append(single_smry)

    def merge_all_summaries(self):
        """
        merge all PyarrowSummary with the same sensor type into single PyarrowSummary per type
        """
        self.merge_audio_summaries()
        self.merge_non_audio_summaries()

    def get_audio(self) -> List[PyarrowSummary]:
        """
        :return: a list of PyarrowSummary of only Audio data
        """
        return [s for s in self.summaries if s.stype == srupa.SensorType.AUDIO]

    def get_non_audio(self) -> Dict[srupa.SensorType, List[PyarrowSummary]]:
        """
        :return: a dictionary of {non-Audio SensorType: PyarrowSummary}
        """
        result = {}
        for k in self.sensor_types():
            if k != srupa.SensorType.AUDIO:
                result[k] = [s for s in self.summaries if s.stype == k]
        return result

    def get_non_audio_list(self) -> List[PyarrowSummary]:
        """
        :return: a list of all non-Audio PyarrowSummary
        """
        return [s for s in self.summaries if s.stype != srupa.SensorType.AUDIO]

    def get_sensor(self, stype: srupa.SensorType) -> List[PyarrowSummary]:
        """
        :param stype: type of sensor to find
        :return: a list of all PyarrowSummary of the specified type
        """
        return [s for s in self.summaries if s.stype == stype]

    def sensor_types(self) -> List[srupa.SensorType]:
        """
        :return: a list of sensor types in self.summaries
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
            summary.add_summary(t)

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
        additional_inputs = packet.station_information.app_settings.additional_input_sensors
        if RedvoxPacketM.StationInformation.AppSettings.InputSensor.IMAGE_PER_SECOND in additional_inputs:
            sample_rate = 1.
        # elif RedvoxPacketM.StationInformation.AppSettings.InputSensor.IMAGE_PER_PACKET in additional_inputs:
        else:
            sample_rate = 1 / srupa.__packet_duration_s(packet)
        # else:
        #   sample_rate = np.nan
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
                m_intv = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
                intv_std = dtu.microseconds_to_seconds(float(np.std(np.diff(timestamps))))
            else:
                m_intv = srupa.__packet_duration_s(packet)
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
                loc.sensor_description, srupa.SensorType.BEST_LOCATION, np.nan,
                1./packet_len_s, "", 1, packet_len_s, 0.,
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
    rate = packet.station_information.app_settings.metrics_rate
    if rate == RedvoxPacketM.StationInformation.MetricsRate.ONCE_PER_SECOND:
        sample_rate = 1
    elif rate == RedvoxPacketM.StationInformation.MetricsRate.ONCE_PER_PACKET:
        sample_rate = 1 / srupa.__packet_duration_s(packet)
    else:
        sample_rate = np.nan
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
        Callable[[RedvoxPacketM], srupa.Sensor]
    ] = srupa.__SENSOR_TYPE_TO_SENSOR_FN[sensor_type]
    if srupa.__has_sensor(packet, field_name) and sensor_fn is not None:
        sensor = sensor_fn(packet)
        t = sensor.timestamps.timestamps
        if len(t) > 1:
            m_intv = dtu.microseconds_to_seconds(float(np.mean(np.diff(t))))
            intv_std = dtu.microseconds_to_seconds(float(np.std(np.diff(t))))
        else:
            m_intv = srupa.__packet_duration_s(packet)
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
        Callable[[RedvoxPacketM], srupa.Sensor]
    ] = srupa.__SENSOR_TYPE_TO_SENSOR_FN[sensor_type]
    if srupa.__has_sensor(packet, field_name) and sensor_fn is not None:
        sensor = sensor_fn(packet)
        t = sensor.timestamps.timestamps
        if len(t) > 1:
            m_intv = dtu.microseconds_to_seconds(float(np.mean(np.diff(t))))
            intv_std = dtu.microseconds_to_seconds(float(np.std(np.diff(t))))
        else:
            m_intv = srupa.__packet_duration_s(packet)
            intv_std = 0.
        if len(t) > 0:
            # read packet.station_information.app_settings.additional_input_sensors for fast sensors
            # rename if needed
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
