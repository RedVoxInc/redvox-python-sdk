"""
Defines generic station objects for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
Utilizes RedvoxPacketM (API M data packets) as the format of the data due to their versatility
"""
from typing import List, Optional, Tuple, Union
import os
from pathlib import Path

import numpy as np
import pyarrow.dataset as ds
import pyarrow as pa

from redvox.common import station_io as io
from redvox.common.io import FileSystemWriter as Fsw, FileSystemSaveMode, Index, get_json_file, json_file_to_dict
from redvox.common import sensor_data as sd
from redvox.common import station_utils as st_utils
from redvox.common.offset_model import OffsetModel, GPS_LATENCY_MICROS
from redvox.common.timesync import TimeSync
from redvox.common.errors import RedVoxExceptions
import redvox.api1000.proto.redvox_api_m_pb2 as api_m
from redvox.common import packet_to_pyarrow as ptp
from redvox.common import gap_and_pad_utils as gpu
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc, seconds_to_microseconds as s_to_us
from redvox.common.event_stream import EventStreams


STATION_ID_LENGTH: int = 10  # the length of a station ID string


class Station:
    """
    generic station for api-independent stuff; uses API M as the core data object since it's quite versatile

    In order for a list of data to be a station, all the data packets must:
        * Have the same station id
        * Have the same station uuid
        * Have the same start date
        * Have the same audio sample rate
        * Have the same metadata

    Generally speaking, stations can be uniquely identified with a minimum of three values: id, uuid, and start date

    Properties:
        _data: list of sensor data associated with the station, default empty list

        _metadata: StationMetadata consistent across all packets, default empty StationMetadata

        _packet_metadata: list of StationPacketMetadata that changes from packet to packet, default empty list

        _id: str id of the station, default empty string

        _uuid: str uuid of the station, default empty string

        _start_date: float of microseconds since epoch UTC when the station started recording, default np.nan

        _first_data_timestamp: float of microseconds since epoch UTC of the first audio data point, default np.nan

        _last_data_timestamp: float of microseconds since epoch UTC of the last audio data point, default np.nan

        _audio_sample_rate_nominal_hz: float of nominal sample rate of audio component in hz, default np.nan

        _is_audio_scrambled: bool, True if audio data is scrambled, default False

        _is_timestamps_updated: bool, True if timestamps have been altered from original data values, default False

        _timesync_data: TimeSyncArrow object, contains information about the station's time synchronization values

        _correct_timestamps: bool, if True, timestamps are updated as soon as they can be, default False
        Note: If False, Timestamps can still be corrected if the update_timestamps function is invoked.

        _use_model_correction: bool, if True, time correction is done using OffsetModel functions, otherwise
        correction is done by adding the OffsetModel's best offset (intercept value).  default True

        _gaps: List of Tuples of floats indicating start and end times of audio gaps.
        Times are not inclusive of the gap.

        _fs_writer: FileSystemWriter, handles file system i/o parameters

        _errors: RedvoxExceptions, errors encountered by the Station
    """

    def __init__(
        self,
        station_id: str = "",
        uuid: str = "",
        start_timestamp: float = np.nan,
        correct_timestamps: bool = False,
        use_model_correction: bool = True,
        base_dir: str = ".",
        save_data: bool = False,
        use_temp_dir: bool = False,
    ):
        """
        initialize Station

        :param station_id: string id of the station; defined by users of the station, default ""
        :param uuid: string uuid of the station; automatically created by the station, default ""
        :param start_timestamp: timestamp in epoch UTC when station was started, default np.nan
        :param correct_timestamps: if True, correct all timestamps as soon as they can be, default False
        :param use_model_correction: if True, use OffsetModel functions for time correction, add OffsetModel
                                        best offset (intercept value) otherwise.  Default True
        :param base_dir: directory to save parquet files, default "." (current directory)
        :param save_data: if True, save the parquet files to base_dir, otherwise delete them.  default False
        :param use_temp_dir: if True, save the parquet files to a temp dir.  default False
        """
        self._id = station_id
        self._uuid = uuid
        self._start_date = start_timestamp
        self._correct_timestamps = correct_timestamps
        self._use_model_correction = use_model_correction
        self._metadata = st_utils.StationMetadata("None")
        self._packet_metadata: List[st_utils.StationPacketMetadata] = []
        self._errors: RedVoxExceptions = RedVoxExceptions("Station")
        self._first_data_timestamp = np.nan
        self._last_data_timestamp = np.nan
        self._audio_sample_rate_nominal_hz = np.nan
        self._is_audio_scrambled = False
        self._timesync_data = TimeSync()
        self._gps_offset_model = OffsetModel.empty_model()
        self._is_timestamps_updated = False
        if save_data:
            save_mode = FileSystemSaveMode.DISK
        elif use_temp_dir:
            save_mode = FileSystemSaveMode.TEMP
        else:
            save_mode = FileSystemSaveMode.MEM
        self._fs_writer = Fsw("", "", base_dir, save_mode)
        self._event_data = EventStreams()

        self._data: List[sd.SensorData] = []
        self._gaps: List[Tuple[float, float]] = []

    def __repr__(self):
        return (
            f"id: {self._id}, "
            f"uuid: {self._uuid}, "
            f"start_date: {self._start_date}, "
            f"use_model_correction: {self._use_model_correction}, "
            f"is_timestamps_updated: {self._is_timestamps_updated}, "
            f"metadata: {self._metadata.__repr__()}, "
            f"packet_metadata: {[p.__repr__() for p in self._packet_metadata]}, "
            f"audio_sample_rate_hz: {self._audio_sample_rate_nominal_hz}, "
            f"is_audio_scrambled: {self._is_audio_scrambled}, "
            f"timesync: {self._timesync_data.__repr__()}, "
            f"gps_offset_model: {self._gps_offset_model.__repr__()}, "
            f"event_data: {self.event_data().__repr__()}, "
            f"gaps: {[g for g in self._gaps]}"
        )
        # "data": [d.__repr__() for d in self._data],

    def __str__(self):
        start_date = (
            np.nan
            if np.isnan(self._start_date)
            else datetime_from_epoch_microseconds_utc(self._start_date).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        )
        return (
            f"id: {self._id}, "
            f"uuid: {self._uuid}, "
            f"start_date: {start_date}, "
            f"use_model_correction: {self._use_model_correction}, "
            f"is_timestamps_updated: {self._is_timestamps_updated}, "
            f"metadata: {self._metadata.__str__()}, "
            f"audio_sample_rate_hz: {self._audio_sample_rate_nominal_hz}, "
            f"is_audio_scrambled: {self._is_audio_scrambled}, "
            f"timesync: {self._timesync_data.__str__()}, "
            f"gps_offset_model: {self._gps_offset_model.__str__()}, "
            f"event_data: {self.event_data().__str__()}, "
            f"gaps: {[g for g in self._gaps]}"
        )
        # "packet_metadata": [p.__str__() for p in self._packet_metadata],
        # "data": [d.__str__() for d in self._data]

    def as_dict(self) -> dict:
        """
        :return: station as dictionary
        """
        return {
            "id": self._id,
            "uuid": self._uuid,
            "start_date": self._start_date,
            "base_dir": os.path.basename(self.save_dir()),
            "use_model_correction": self._use_model_correction,
            "is_audio_scrambled": self._is_audio_scrambled,
            "is_timestamps_updated": self._is_timestamps_updated,
            "audio_sample_rate_nominal_hz": self._audio_sample_rate_nominal_hz,
            "first_data_timestamp": self._first_data_timestamp,
            "last_data_timestamp": self._last_data_timestamp,
            "metadata": self._metadata.as_dict(),
            "packet_metadata": [p.as_dict() for p in self._packet_metadata],
            "gps_offset_model": self._gps_offset_model.as_dict(),
            "gaps": self._gaps,
            "errors": self._errors.as_dict(),
            "sensors": [s.type().name for s in self._data]
            # "event_data": self._event_data.as_dict()
        }

    def default_station_json_file_name(self) -> str:
        """
        :return: default station json file name (id_startdate), with startdate as integer of microseconds
                    since epoch UTC
        """
        return self._get_id_key()

    def to_json_file(self, file_name: Optional[str] = None) -> Path:
        """
        saves the station as json in station.base_dir, then creates directories and the json for the metadata
        and data in the same base_dir.

        :param file_name: the optional base file name.  Do not include a file extension.
                            If None, a default file name is created using this format:
                            [station_id]_[start_date].json
        :return: path to json file
        """
        return io.to_json_file(self, file_name)

    @staticmethod
    def from_json_file(file_dir: str, file_name: Optional[str] = None) -> "Station":
        """
        convert contents of json file to Station

        :param file_dir: full path to containing directory for the file
        :param file_name: name of file and extension to load data from.  if not given, will use the first .json file
                            in the file_dir
        :return: Station object
        """
        if file_name is None:
            file_name = get_json_file(file_dir)
            if file_name is None:
                result = Station("Empty")
                result.append_error("File to load Sensor from not found.")
                return result
        json_data = json_file_to_dict(os.path.join(file_dir, file_name))
        if "id" in json_data.keys() and "start_date" in json_data.keys():
            result = Station(
                json_data["id"],
                json_data["uuid"],
                json_data["start_date"],
                use_model_correction=json_data["use_model_correction"],
            )
            result._fs_writer.file_name = json_data["base_dir"]
            result._gps_offset_model = (
                OffsetModel.from_dict(json_data["gps_offset_model"])
                if "gps_offset_model" in json_data.keys()
                else OffsetModel.empty_model()
            )
            result.set_save_mode(FileSystemSaveMode.DISK)
            result.set_audio_scrambled(json_data["is_audio_scrambled"])
            result.set_timestamps_updated(json_data["is_timestamps_updated"])
            result.set_audio_sample_rate_hz(json_data["audio_sample_rate_nominal_hz"])
            result.set_metadata(st_utils.StationMetadata.from_dict(json_data["metadata"]))
            result.set_packet_metadata(
                [st_utils.StationPacketMetadata.from_dict(p) for p in json_data["packet_metadata"]]
            )
            result.set_gaps(json_data["gaps"])
            result.set_errors(RedVoxExceptions.from_dict(json_data["errors"]))
            for s in json_data["sensors"]:
                result._data.append(sd.SensorData.from_json_file(os.path.join(file_dir, s)))
            ts_file_name = get_json_file(os.path.join(file_dir, "timesync"))
            result.set_timesync_data(TimeSync.from_json_file(os.path.join(file_dir, "timesync", ts_file_name)))
            ev_file_name = get_json_file(os.path.join(file_dir, "events"))
            result.set_event_data(EventStreams.from_json_file(os.path.join(file_dir, "events"), ev_file_name))
            result.update_first_and_last_data_timestamps()
        else:
            result = Station()
            result.append_error(f"Missing id and start date to identify station in {file_name}")

        return result

    def data(self) -> List[sd.SensorData]:
        """
        :return: the sensors of the station as a list
        """
        return self._data

    def get_sensors(self) -> List[str]:
        """
        :return: the names of sensors of the station as a list
        """
        return [s.name for s in self._data]

    def get_save_dir_sensor(self, sensor: sd.SensorType) -> str:
        """
        :param sensor: the type of sensor to get a save directory for
        :return: the station's save dir with the sensor type name as a subdir
        """
        return os.path.join(self.save_dir(), sensor.name)

    def set_save_mode(self, new_save_mode: FileSystemSaveMode):
        """
        sets the save mode of the Station

        :param new_save_mode: FileSystemSaveMode to change to
        """
        self._fs_writer.set_save_mode(new_save_mode)
        if hasattr(self, "_event_data"):
            self._event_data.set_save_mode(new_save_mode)
        for s in self._data:
            s.set_save_mode(new_save_mode)

    def set_save_data(self, save_on: bool = False):
        """
        set the option to save the station

        :param save_on: if True, saves the station data, default False
        """
        self._fs_writer.save_to_disk = save_on

    def set_save_dir(self, new_dir: str, station_dir_name: Optional[str] = None):
        """
        sets the save directory of a Station.  combines the new_dir and the station_name to form a directory called
        new_dir/station_dir_name/

        Uses the default [station_id]_[station_startdate] if no name is specified

        :param new_dir: new base directory to use
        :param station_dir_name: optional station directory to use
        """
        if station_dir_name is None:
            station_dir_name = self._get_id_key()
        self._fs_writer.file_name = station_dir_name
        if self._fs_writer.is_use_disk():
            self._fs_writer.base_dir = os.path.join(new_dir)
        else:
            self._fs_writer.base_dir = os.path.join(self._fs_writer.get_temp())
        for s in self._data:
            s.move_pyarrow_dir(self.save_dir())
        self._timesync_data.arrow_dir = os.path.join(self.save_dir(), "timesync")
        if hasattr(self, "_event_data"):
            self._event_data.set_save_dir(os.path.join(self.save_dir(), "events"))

    def save_dir(self) -> str:
        """
        :return: directory where files are being written to
        """
        if self._fs_writer.is_use_disk():
            return os.path.join(self._fs_writer.save_dir(), self._fs_writer.file_name)
        elif self._fs_writer.is_use_temp():
            return os.path.join(self._fs_writer.get_temp(), self._get_id_key())
        return "."

    def save(self, file_name: Optional[str] = None) -> Optional[Path]:
        """
        saves the Station to disk.  Does nothing if saving is not enabled.

        :param file_name: the optional base file name.  Do not include a file extension.  Default None.
                            If None, a default file name is created using this format:
                            [station_id]_[start_date].json
        :return: Path to the saved file or None if not saved
        """
        if self.is_save_to_disk():
            self._fs_writer.create_dir()
            return self.to_json_file(file_name)
        return None

    @staticmethod
    def load(in_dir: str = "") -> "Station":
        """
        :param in_dir: structured directory with json metadata file to load
        :return: Station using data from files
        """
        file = get_json_file(in_dir)
        if file is None:
            st = Station("LoadError")
            st.append_error("File to load Station not found.")
            return st
        else:
            return Station.from_json_file(in_dir, file)

    @staticmethod
    def create_from_indexes(
        indexes: List[Index],
        correct_timestamps: bool = False,
        use_model_correction: bool = True,
        base_out_dir: str = ".",
        save_output: bool = False,
        use_temp_dir: bool = False,
    ) -> "Station":
        """
        Use a list of Indexes to create a Station

        :param indexes: List of indexes to use
        :param correct_timestamps: if True, correct timestamps, default False
        :param use_model_correction: if True, correct timestamps using offset model, default True
        :param base_out_dir: directory to save output files to, if saving to disk.  default "." (current directory)
        :param save_output: if True, save output to disk, default False
        :param use_temp_dir: if True, use a temporary directory, default False
        :return: Station using data from the files in the list of indexes.
        """
        station = Station(
            correct_timestamps=correct_timestamps,
            use_model_correction=use_model_correction,
            base_dir=base_out_dir,
            save_data=save_output,
            use_temp_dir=use_temp_dir,
        )
        station.load_from_indexes(indexes)
        return station

    def load_from_indexes(self, indexes: List[Index]):
        """
        fill station using data from a list of Indexes

        :param indexes: List of indexes of the files to read
        """
        self._load_metadata_from_packet(indexes[0].read_first_packet())
        self._timesync_data.arrow_dir = os.path.join(self.save_dir(), "timesync")
        self._timesync_data.arrow_file = f"timesync_{self.start_date_as_str()}"
        all_summaries = ptp.AggregateSummary()
        self._event_data.set_save_dir(os.path.join(self.save_dir(), "events"))
        for idx in indexes:
            pkts = idx.read_contents()
            self._packet_metadata.extend([st_utils.StationPacketMetadata(packet) for packet in pkts])
            self._timesync_data.append_timesync_arrow(TimeSync().from_raw_packets(pkts))
            self._event_data.read_from_packets_list(pkts)
            all_summaries.add_aggregate_summary(
                ptp.stream_to_pyarrow(pkts, self._fs_writer.get_temp() if self.is_save_to_disk() else None)
            )
        all_summaries.merge_all_summaries()
        self._set_pyarrow_sensors(all_summaries)
        if self._correct_timestamps:
            self.update_timestamps()

    @staticmethod
    def create_from_packets(
        packets: List[api_m.RedvoxPacketM],
        correct_timestamps: bool = False,
        use_model_correction: bool = True,
        base_out_dir: str = ".",
        save_output: bool = False,
        use_temp_dir: bool = False,
    ) -> "Station":
        """
        Use a list of Redvox packets to create a Station

        :param packets: API M redvox packets with data to load
        :param correct_timestamps: if True, correct timestamps as soon as possible.  Default False
        :param use_model_correction: if True, use OffsetModel functions for time correction, add OffsetModel
                                        best offset (intercept value) otherwise.  Default True
        :param base_out_dir: directory to save parquet files, default "." (current directory)
        :param save_output: if True, save the parquet files to base_out_dir, otherwise delete them.  default False
        :param use_temp_dir: if True, save the parquet files to a temp dir.  default False
        :return: Station using data from redvox packets.
        """
        station = Station(
            correct_timestamps=correct_timestamps,
            use_model_correction=use_model_correction,
            base_dir=base_out_dir,
            save_data=save_output,
            use_temp_dir=use_temp_dir,
        )
        station.load_data_from_packets(packets)
        return station

    @staticmethod
    def create_from_metadata(
        packet: api_m.RedvoxPacketM,
        use_model_correction: bool = True,
        base_out_dir: str = ".",
        save_output: bool = False,
        use_temp_dir: bool = False,
    ) -> "Station":
        """
        create a station using metadata from a packet.  There will be no sensor or timing data added.

        :param packet: API M redvox packet to load metadata from
        :param use_model_correction: if True, use OffsetModel functions for time correction, add OffsetModel
                                        best offset (intercept value) otherwise.  Default True
        :param base_out_dir: directory to save parquet files, default "." (current directory)
        :param save_output: if True, save the parquet files to base_out_dir, otherwise delete them.  default False
        :param use_temp_dir: if True, save the parquet files to a temp dir.  default False
        :return: Station without any sensor or timing
        """
        station = Station(
            use_model_correction=use_model_correction,
            base_dir=base_out_dir,
            save_data=save_output,
            use_temp_dir=use_temp_dir,
        )
        station._load_metadata_from_packet(packet)
        return station

    def load_data_from_packets(self, packets: List[api_m.RedvoxPacketM]):
        """
        fill station with data from packets

        :param packets: API M redvox packets with data to load
        """
        if packets and st_utils.validate_station_key_list(packets, self._errors):
            # noinspection Mypy
            self._load_metadata_from_packet(packets[0])
            self._packet_metadata = [st_utils.StationPacketMetadata(packet) for packet in packets]
            self._timesync_data = TimeSync().from_raw_packets(packets)
            self._timesync_data.arrow_dir = os.path.join(self.save_dir(), "timesync")
            self._timesync_data.arrow_file = f"timesync_{self.start_date_as_str()}"
            summaries = ptp.stream_to_pyarrow(packets, self._fs_writer.get_temp() if self.is_save_to_disk() else None)
            summaries.merge_all_summaries()
            self._set_pyarrow_sensors(summaries)
            if self._correct_timestamps:
                self.update_timestamps()
            self._event_data.set_save_dir(os.path.join(self.save_dir(), "events"))
            self._event_data.read_from_packets_list(packets)

    def _load_metadata_from_packet(self, packet: api_m.RedvoxPacketM):
        """
        sets metadata that applies to the entire station from a single packet

        :param packet: API-M redvox packet to load metadata from
        """
        self._id = packet.station_information.id.zfill(STATION_ID_LENGTH)
        self._uuid = packet.station_information.uuid
        self._start_date = packet.timing_information.app_start_mach_timestamp
        if self._start_date < 0:
            self._errors.append(
                f"Station {self._id} has station start date before epoch.  Station start date reset to np.nan"
            )
            self._start_date = np.nan
        self._metadata = st_utils.StationMetadata("Redvox", packet)
        if isinstance(packet, api_m.RedvoxPacketM) and packet.sensors.HasField("audio"):
            self._audio_sample_rate_nominal_hz = packet.sensors.audio.sample_rate
            self._is_audio_scrambled = packet.sensors.audio.is_scrambled
        else:
            self._audio_sample_rate_nominal_hz = np.nan
            self._is_audio_scrambled = False

    def _sort_metadata_packets(self):
        """
        orders the metadata packets by their starting timestamps.  Returns nothing, sorts the data in place
        """
        self._packet_metadata.sort(key=lambda t: t.packet_start_mach_timestamp)

    def update_first_and_last_data_timestamps(self):
        """
        uses the audio data to get the first and last timestamp of the station
        """
        self._first_data_timestamp = self.audio_sensor().first_data_timestamp()
        self._last_data_timestamp = self.audio_sensor().last_data_timestamp()

    def set_id(self, station_id: str) -> "Station":
        """
        set the station's id

        :param station_id: id of station
        :return: modified version of self
        """
        self._id = station_id
        return self

    def id(self) -> Optional[str]:
        """
        :return: the station id or None if it doesn't exist
        """
        return self._id

    def set_uuid(self, uuid: str) -> "Station":
        """
        set the station's uuid

        :param uuid: uuid of station
        :return: modified version of self
        """
        self._uuid = uuid
        return self

    def uuid(self) -> Optional[str]:
        """
        :return: the station uuid or None if it doesn't exist
        """
        return self._uuid

    def set_start_date(self, start_timestamp: float) -> "Station":
        """
        set the station's start timestamp in microseconds since epoch utc

        :param start_timestamp: start_timestamp of station
        :return: modified version of self
        """
        self._start_date = start_timestamp
        return self

    def start_date(self) -> float:
        """
        :return: the station start timestamp or np.nan if it doesn't exist
        """
        return self._start_date

    def start_date_as_str(self) -> str:
        """
        :return: station start timestamp as integer string or 0 if it doesn't exist
        """
        return f"{0 if np.isnan(self._start_date) else int(self._start_date)}"

    def check_key(self) -> bool:
        """
        check if the station has enough information to set its key.

        :return: True if key can be set, False if not enough information
        """
        if self._id:
            if self._uuid:
                if np.isnan(self._start_date):
                    self._errors.append("Station start timestamp not defined.")
                return True
            else:
                self._errors.append("Station uuid is not valid.")
        else:
            self._errors.append("Station id is not set.")
        return False

    def get_key(self) -> Optional[st_utils.StationKey]:
        """
        :return: the station's key if id, uuid and start timestamp is set, or None if key cannot be created
        """
        if self.check_key():
            return st_utils.StationKey(self._id, self._uuid, self._start_date)
        return None

    def set_correct_timestamps(self):
        """
        set the correction of timestamps to True.
        """
        self._correct_timestamps = True

    def append_station(self, new_station: "Station"):
        """
        append a new station to the current station; does nothing if keys do not match

        :param new_station: Station to append to current station
        """
        key = self.get_key()
        if key and key.compare_key(new_station.get_key()) and self._metadata.validate_metadata(new_station._metadata):
            self._errors.extend_error(new_station.errors())
            self.append_station_data(new_station._data)
            self._packet_metadata.extend(new_station._packet_metadata)
            self._sort_metadata_packets()
            self._timesync_data.append_timesync_arrow(new_station._timesync_data)
            self._set_gps_offset()
            if not hasattr(self, "_event_data"):
                self._event_data = EventStreams()
            self._event_data.append_streams(new_station.event_data())
            self.update_first_and_last_data_timestamps()

    def append_station_data(self, new_station_data: List[sd.SensorData]):
        """
        append new station data to existing station data

        :param new_station_data: the dictionary of data to add
        """
        for sensor_data in new_station_data:
            self.append_sensor(sensor_data)

    def get_station_sensor_types(self) -> List[sd.SensorType]:
        """
        :return: a list of sensor types in the station
        """
        return [s.type() for s in self._data]

    def get_sensor_by_type(self, sensor_type: sd.SensorType) -> Optional[sd.SensorData]:
        """
        :param sensor_type: type of sensor to get
        :return: the sensor of the type or None if it doesn't exist
        """
        for s in self._data:
            if s.type() == sensor_type:
                return s.class_from_type()
        return None

    def append_sensor(self, sensor_data: sd.SensorData):
        """
        append sensor data to an existing sensor_type or add a new sensor to the dictionary

        :param sensor_data: the data to append
        """
        if sensor_data.type() in self.get_station_sensor_types():
            self.get_sensor_by_type(sensor_data.type()).append_sensor(sensor_data)
        else:
            self._add_sensor(sensor_data.type(), sensor_data)

    def _delete_sensor(self, sensor_type: sd.SensorType):
        """
        removes a sensor from the sensor data dictionary if it exists

        :param sensor_type: the sensor to remove
        """
        if sensor_type in self.get_station_sensor_types():
            self._data.remove(self.get_sensor_by_type(sensor_type))

    def _add_sensor(self, sensor_type: sd.SensorType, sensor: sd.SensorData):
        """
        adds a sensor to the sensor data dictionary

        :param sensor_type: the type of sensor to add
        :param sensor: the sensor data to add
        """
        if sensor_type in self.get_station_sensor_types():
            raise ValueError(f"Cannot add sensor type ({sensor_type.name}) that already exists in packet!")
        else:
            self._data.append(sensor)

    def get_num_packets(self) -> int:
        """
        :return: number of packets used to create station
        """
        return len(self._packet_metadata)

    def get_mean_packet_duration(self) -> float:
        """
        :return: mean duration of packets in microseconds
        """
        return float(
            np.mean([tsd.packet_end_mach_timestamp - tsd.packet_start_mach_timestamp for tsd in self._packet_metadata])
        )

    def get_mean_packet_audio_samples(self) -> float:
        """
        calculate the mean number of audio samples per packet using the
          number of audio sensor's data points and the number of packets

        :return: mean number of audio samples per packet
        """
        # noinspection Mypy
        return self.audio_sensor().num_samples() / self.get_num_packets()

    def has_timesync_data(self) -> bool:
        """
        :return: True if there is timesync data for the station
        """
        return self._timesync_data.num_tri_messages() > 0

    def has_audio_sensor(self) -> bool:
        """
        :return: True if audio sensor exists
        """
        return sd.SensorType.AUDIO in self.get_station_sensor_types()

    def has_audio_data(self) -> bool:
        """
        :return: True if audio sensor exists and has any data
        """
        audio_sensor: Optional[sd.AudioSensor] = self.audio_sensor()
        return audio_sensor is not None and audio_sensor.num_samples() > 0

    def audio_sensor(self) -> Optional[sd.AudioSensor]:
        """
        :return: audio sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.AUDIO)

    def set_audio_sensor(self, audio_sensor: Optional[sd.AudioSensor] = None) -> "Station":
        """
        sets the audio sensor; can remove audio sensor by passing None

        :param audio_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_audio_sensor():
            self._delete_sensor(sd.SensorType.AUDIO)
        if audio_sensor is not None:
            self._add_sensor(sd.SensorType.AUDIO, audio_sensor)
        return self

    def has_location_sensor(self) -> bool:
        """
        :return: True if location sensor exists
        """
        return sd.SensorType.LOCATION in self.get_station_sensor_types()

    def has_location_data(self) -> bool:
        """
        :return: True if location sensor exists and has any data
        """
        location_sensor: Optional[sd.LocationSensor] = self.location_sensor()
        return location_sensor is not None and location_sensor.num_samples() > 0

    def location_sensor(self) -> Optional[sd.LocationSensor]:
        """
        :return: location sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.LOCATION)

    def set_location_sensor(self, loc_sensor: Optional[sd.LocationSensor] = None) -> "Station":
        """
        sets the location sensor; can remove location sensor by passing None

        :param loc_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_location_sensor():
            self._delete_sensor(sd.SensorType.LOCATION)
        if loc_sensor is not None:
            self._add_sensor(sd.SensorType.LOCATION, loc_sensor)
        return self

    def has_best_location_sensor(self) -> bool:
        """
        :return: True if best location sensor exists
        """
        return sd.SensorType.BEST_LOCATION in self.get_station_sensor_types()

    def has_best_location_data(self) -> bool:
        """
        :return: True if best location sensor exists and has any data
        """
        location_sensor: Optional[sd.LocationSensor] = self.best_location_sensor()
        return location_sensor is not None and location_sensor.num_samples() > 0

    def best_location_sensor(self) -> Optional[sd.BestLocationSensor]:
        """
        :return: best location sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.BEST_LOCATION)

    def set_best_location_sensor(self, best_loc_sensor: Optional[sd.BestLocationSensor] = None) -> "Station":
        """
        sets the best location sensor; can remove location sensor by passing None

        :param best_loc_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_best_location_sensor():
            self._delete_sensor(sd.SensorType.BEST_LOCATION)
        if best_loc_sensor is not None:
            self._add_sensor(sd.SensorType.BEST_LOCATION, best_loc_sensor)
        return self

    def has_accelerometer_sensor(self) -> bool:
        """
        :return: True if accelerometer sensor exists
        """
        return sd.SensorType.ACCELEROMETER in self.get_station_sensor_types()

    def has_accelerometer_data(self) -> bool:
        """
        :return: True if accelerometer sensor exists and has any data
        """
        sensor: Optional[sd.AccelerometerSensor] = self.accelerometer_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def accelerometer_sensor(self) -> Optional[sd.AccelerometerSensor]:
        """
        :return: accelerometer sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.ACCELEROMETER)

    def set_accelerometer_sensor(self, acc_sensor: Optional[sd.AccelerometerSensor] = None) -> "Station":
        """
        sets the accelerometer sensor; can remove accelerometer sensor by passing None

        :param acc_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_accelerometer_sensor():
            self._delete_sensor(sd.SensorType.ACCELEROMETER)
        if acc_sensor is not None:
            self._add_sensor(sd.SensorType.ACCELEROMETER, acc_sensor)
        return self

    def has_magnetometer_sensor(self) -> bool:
        """
        :return: True if magnetometer sensor exists
        """
        return sd.SensorType.MAGNETOMETER in self.get_station_sensor_types()

    def has_magnetometer_data(self) -> bool:
        """
        :return: True if magnetometer sensor exists and has any data
        """
        sensor: Optional[sd.MagnetometerSensor] = self.magnetometer_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def magnetometer_sensor(self) -> Optional[sd.MagnetometerSensor]:
        """
        :return: magnetometer sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.MAGNETOMETER)

    def set_magnetometer_sensor(self, mag_sensor: Optional[sd.MagnetometerSensor] = None) -> "Station":
        """
        sets the magnetometer sensor; can remove magnetometer sensor by passing None

        :param mag_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_magnetometer_sensor():
            self._delete_sensor(sd.SensorType.MAGNETOMETER)
        if mag_sensor is not None:
            self._add_sensor(sd.SensorType.MAGNETOMETER, mag_sensor)
        return self

    def has_gyroscope_sensor(self) -> bool:
        """
        :return: True if gyroscope sensor exists
        """
        return sd.SensorType.GYROSCOPE in self.get_station_sensor_types()

    def has_gyroscope_data(self) -> bool:
        """
        :return: True if gyroscope sensor exists and has any data
        """
        sensor: Optional[sd.GyroscopeSensor] = self.gyroscope_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def gyroscope_sensor(self) -> Optional[sd.GyroscopeSensor]:
        """
        :return: gyroscope sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.GYROSCOPE)

    def set_gyroscope_sensor(self, gyro_sensor: Optional[sd.GyroscopeSensor] = None) -> "Station":
        """
        sets the gyroscope sensor; can remove gyroscope sensor by passing None

        :param gyro_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_gyroscope_sensor():
            self._delete_sensor(sd.SensorType.GYROSCOPE)
        if gyro_sensor is not None:
            self._add_sensor(sd.SensorType.GYROSCOPE, gyro_sensor)
        return self

    def has_pressure_sensor(self) -> bool:
        """
        :return: True if pressure sensor exists
        """
        return sd.SensorType.PRESSURE in self.get_station_sensor_types()

    def has_pressure_data(self) -> bool:
        """
        :return: True if pressure sensor exists and has any data
        """
        sensor: Optional[sd.PressureSensor] = self.pressure_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def pressure_sensor(self) -> Optional[sd.PressureSensor]:
        """
        :return: pressure sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.PRESSURE)

    def set_pressure_sensor(self, pressure_sensor: Optional[sd.PressureSensor] = None) -> "Station":
        """
        sets the pressure sensor; can remove pressure sensor by passing None

        :param pressure_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_pressure_sensor():
            self._delete_sensor(sd.SensorType.PRESSURE)
        if pressure_sensor is not None:
            self._add_sensor(sd.SensorType.PRESSURE, pressure_sensor)
        return self

    def has_barometer_sensor(self) -> bool:
        """
        :return: True if barometer (pressure) sensor exists
        """
        return self.has_pressure_sensor()

    def has_barometer_data(self) -> bool:
        """
        :return: True if barometer (pressure) sensor exists and has any data
        """
        return self.has_pressure_data()

    def barometer_sensor(self) -> Optional[sd.PressureSensor]:
        """
        :return: barometer (pressure) sensor if it exists, None otherwise
        """
        return self.pressure_sensor()

    def set_barometer_sensor(self, bar_sensor: Optional[sd.PressureSensor] = None) -> "Station":
        """
        sets the barometer (pressure) sensor; can remove barometer sensor by passing None

        :param bar_sensor: the SensorData to set or None
        :return: the edited station
        """
        return self.set_pressure_sensor(bar_sensor)

    def has_light_sensor(self) -> bool:
        """
        :return: True if light sensor exists
        """
        return sd.SensorType.LIGHT in self.get_station_sensor_types()

    def has_light_data(self) -> bool:
        """
        :return: True if light sensor exists and has any data
        """
        sensor: Optional[sd.LightSensor] = self.light_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def light_sensor(self) -> Optional[sd.LightSensor]:
        """
        :return: light sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.LIGHT)

    def set_light_sensor(self, light_sensor: Optional[sd.LightSensor] = None) -> "Station":
        """
        sets the light sensor; can remove light sensor by passing None

        :param light_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_light_sensor():
            self._delete_sensor(sd.SensorType.LIGHT)
        if light_sensor is not None:
            self._add_sensor(sd.SensorType.LIGHT, light_sensor)
        return self

    def has_infrared_sensor(self) -> bool:
        """
        :return: True if infrared (proximity) sensor exists
        """
        return self.has_proximity_sensor()

    def has_infrared_data(self) -> bool:
        """
        :return: True if infrared (proximity) sensor exists and has any data
        """
        return self.has_proximity_data()

    def infrared_sensor(self) -> Optional[sd.ProximitySensor]:
        """
        :return: infrared (proximity) sensor if it exists, None otherwise
        """
        return self.proximity_sensor()

    def set_infrared_sensor(self, infrd_sensor: Optional[sd.ProximitySensor] = None) -> "Station":
        """
        sets the infrared sensor; can remove infrared sensor by passing None

        :param infrd_sensor: the SensorData to set or None
        :return: the edited Station
        """
        return self.set_proximity_sensor(infrd_sensor)

    def has_proximity_sensor(self) -> bool:
        """
        :return: True if proximity sensor exists
        """
        return sd.SensorType.PROXIMITY in self.get_station_sensor_types()

    def has_proximity_data(self) -> bool:
        """
        :return: True if proximity sensor exists and has any data
        """
        sensor: Optional[sd.ProximitySensor] = self.proximity_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def proximity_sensor(self) -> Optional[sd.ProximitySensor]:
        """
        :return: proximity sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.PROXIMITY)

    def set_proximity_sensor(self, proximity_sensor: Optional[sd.ProximitySensor] = None) -> "Station":
        """
        sets the proximity sensor; can remove proximity sensor by passing None

        :param proximity_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_proximity_sensor():
            self._delete_sensor(sd.SensorType.PROXIMITY)
        if proximity_sensor is not None:
            self._add_sensor(sd.SensorType.PROXIMITY, proximity_sensor)
        return self

    def has_image_sensor(self) -> bool:
        """
        :return: True if image sensor exists
        """
        return sd.SensorType.IMAGE in self.get_station_sensor_types()

    def has_image_data(self) -> bool:
        """
        :return: True if image sensor exists and has any data
        """
        sensor: Optional[sd.ImageSensor] = self.image_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def image_sensor(self) -> Optional[sd.ImageSensor]:
        """
        :return: image sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.IMAGE)

    def set_image_sensor(self, img_sensor: Optional[sd.ImageSensor] = None) -> "Station":
        """
        sets the image sensor; can remove image sensor by passing None

        :param img_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_image_sensor():
            self._delete_sensor(sd.SensorType.IMAGE)
        if img_sensor is not None:
            self._add_sensor(sd.SensorType.IMAGE, img_sensor)
        return self

    def has_ambient_temperature_sensor(self) -> bool:
        """
        :return: True if ambient temperature sensor exists
        """
        return sd.SensorType.AMBIENT_TEMPERATURE in self.get_station_sensor_types()

    def has_ambient_temperature_data(self) -> bool:
        """
        :return: True if ambient temperature sensor exists and has any data
        """
        sensor: Optional[sd.AmbientTemperatureSensor] = self.ambient_temperature_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def ambient_temperature_sensor(self) -> Optional[sd.AmbientTemperatureSensor]:
        """
        :return: ambient temperature sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.AMBIENT_TEMPERATURE)

    def set_ambient_temperature_sensor(
        self, amb_temp_sensor: Optional[sd.AmbientTemperatureSensor] = None
    ) -> "Station":
        """
        sets the ambient temperature sensor; can remove ambient temperature sensor by passing None

        :param amb_temp_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_ambient_temperature_sensor():
            self._delete_sensor(sd.SensorType.AMBIENT_TEMPERATURE)
        if amb_temp_sensor is not None:
            self._add_sensor(sd.SensorType.AMBIENT_TEMPERATURE, amb_temp_sensor)
        return self

    def has_relative_humidity_sensor(self) -> bool:
        """
        :return: True if relative humidity sensor exists
        """
        return sd.SensorType.RELATIVE_HUMIDITY in self.get_station_sensor_types()

    def has_relative_humidity_data(self) -> bool:
        """
        :return: True if relative humidity sensor exists and has any data
        """
        sensor: Optional[sd.RelativeHumiditySensor] = self.relative_humidity_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def relative_humidity_sensor(self) -> Optional[sd.RelativeHumiditySensor]:
        """
        :return: relative humidity sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.RELATIVE_HUMIDITY)

    def set_relative_humidity_sensor(self, rel_hum_sensor: Optional[sd.RelativeHumiditySensor] = None) -> "Station":
        """
        sets the relative humidity sensor; can remove relative humidity sensor by passing None

        :param rel_hum_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_relative_humidity_sensor():
            self._delete_sensor(sd.SensorType.RELATIVE_HUMIDITY)
        if rel_hum_sensor is not None:
            self._add_sensor(sd.SensorType.RELATIVE_HUMIDITY, rel_hum_sensor)
        return self

    def has_gravity_sensor(self) -> bool:
        """
        :return: True if gravity sensor exists
        """
        return sd.SensorType.GRAVITY in self.get_station_sensor_types()

    def has_gravity_data(self) -> bool:
        """
        :return: True if gravity sensor exists and has any data
        """
        sensor: Optional[sd.GravitySensor] = self.gravity_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def gravity_sensor(self) -> Optional[sd.GravitySensor]:
        """
        :return: gravity sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.GRAVITY)

    def set_gravity_sensor(self, grav_sensor: Optional[sd.GravitySensor] = None) -> "Station":
        """
        sets the gravity sensor; can remove gravity sensor by passing None

        :param grav_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_gravity_sensor():
            self._delete_sensor(sd.SensorType.GRAVITY)
        if grav_sensor is not None:
            self._add_sensor(sd.SensorType.GRAVITY, grav_sensor)
        return self

    def has_linear_acceleration_sensor(self) -> bool:
        """
        :return: True if linear acceleration sensor exists
        """
        return sd.SensorType.LINEAR_ACCELERATION in self.get_station_sensor_types()

    def has_linear_acceleration_data(self) -> bool:
        """
        :return: True if linear acceleration sensor exists and has any data
        """
        sensor: Optional[sd.LinearAccelerationSensor] = self.linear_acceleration_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def linear_acceleration_sensor(self) -> Optional[sd.LinearAccelerationSensor]:
        """
        :return: linear acceleration sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.LINEAR_ACCELERATION)

    def set_linear_acceleration_sensor(self, lin_acc_sensor: Optional[sd.LinearAccelerationSensor] = None) -> "Station":
        """
        sets the linear acceleration sensor; can remove linear acceleration sensor by passing None

        :param lin_acc_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_linear_acceleration_sensor():
            self._delete_sensor(sd.SensorType.LINEAR_ACCELERATION)
        if lin_acc_sensor is not None:
            self._add_sensor(sd.SensorType.LINEAR_ACCELERATION, lin_acc_sensor)
        return self

    def has_orientation_sensor(self) -> bool:
        """
        :return: True if orientation sensor exists
        """
        return sd.SensorType.ORIENTATION in self.get_station_sensor_types()

    def has_orientation_data(self) -> bool:
        """
        :return: True if orientation sensor exists and has any data
        """
        sensor: Optional[sd.OrientationSensor] = self.orientation_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def orientation_sensor(self) -> Optional[sd.OrientationSensor]:
        """
        :return: orientation sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.ORIENTATION)

    def set_orientation_sensor(self, orientation_sensor: Optional[sd.OrientationSensor] = None) -> "Station":
        """
        sets the orientation sensor; can remove orientation sensor by passing None

        :param orientation_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_orientation_sensor():
            self._delete_sensor(sd.SensorType.ORIENTATION)
        if orientation_sensor is not None:
            self._add_sensor(sd.SensorType.ORIENTATION, orientation_sensor)
        return self

    def has_rotation_vector_sensor(self) -> bool:
        """
        :return: True if rotation vector sensor exists
        """
        return sd.SensorType.ROTATION_VECTOR in self.get_station_sensor_types()

    def has_rotation_vector_data(self) -> bool:
        """
        :return: True if rotation vector sensor exists and has any data
        """
        sensor: Optional[sd.RotationVectorSensor] = self.rotation_vector_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def rotation_vector_sensor(self) -> Optional[sd.RotationVectorSensor]:
        """
        :return: rotation vector sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.ROTATION_VECTOR)

    def set_rotation_vector_sensor(self, rot_vec_sensor: Optional[sd.RotationVectorSensor] = None) -> "Station":
        """
        sets the rotation vector sensor; can remove rotation vector sensor by passing None

        :param rot_vec_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_rotation_vector_sensor():
            self._delete_sensor(sd.SensorType.ROTATION_VECTOR)
        if rot_vec_sensor is not None:
            self._add_sensor(sd.SensorType.ROTATION_VECTOR, rot_vec_sensor)
        return self

    def has_compressed_audio_sensor(self) -> bool:
        """
        :return: True if compressed audio sensor exists
        """
        return sd.SensorType.COMPRESSED_AUDIO in self.get_station_sensor_types()

    def has_compressed_audio_data(self) -> bool:
        """
        :return: True if compressed audio sensor exists and has any data
        """
        sensor: Optional[sd.CompressedAudioSensor] = self.compressed_audio_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def compressed_audio_sensor(self) -> Optional[sd.CompressedAudioSensor]:
        """
        :return: compressed audio sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.COMPRESSED_AUDIO)

    def set_compressed_audio_sensor(self, comp_audio_sensor: Optional[sd.CompressedAudioSensor] = None) -> "Station":
        """
        sets the compressed audio sensor; can remove compressed audio sensor by passing None

        :param comp_audio_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_compressed_audio_sensor():
            self._delete_sensor(sd.SensorType.COMPRESSED_AUDIO)
        if comp_audio_sensor is not None:
            self._add_sensor(sd.SensorType.COMPRESSED_AUDIO, comp_audio_sensor)
        return self

    def has_health_sensor(self) -> bool:
        """
        :return: True if health sensor (station metrics) exists
        """
        return sd.SensorType.STATION_HEALTH in self.get_station_sensor_types()

    def has_health_data(self) -> bool:
        """
        :return: True if health sensor (station metrics) exists and has data
        """
        sensor: Optional[sd.StationHealthSensor] = self.health_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def health_sensor(self) -> Optional[sd.StationHealthSensor]:
        """
        :return: station health sensor (station metrics) if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.STATION_HEALTH)

    def set_health_sensor(self, health_sensor: Optional[sd.StationHealthSensor] = None) -> "Station":
        """
        sets the health sensor; can remove health sensor by passing None

        :param health_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_health_sensor():
            self._delete_sensor(sd.SensorType.STATION_HEALTH)
        if health_sensor is not None:
            self._add_sensor(sd.SensorType.STATION_HEALTH, health_sensor)
        return self

    def set_gaps(self, gaps: List[Tuple[float, float]]):
        """
        set the audio gaps of the station

        :param gaps: list pairs of timestamps of the data points on the edge of gaps
        """
        self._gaps = gaps

    def gaps(self) -> List[Tuple[float, float]]:
        """
        :return: list pairs of timestamps of the data points on the edge of gaps
        """
        return self._gaps

    def event_data(self) -> EventStreams:
        """
        :return: all EventStreams in the Station
        """
        return self._event_data if hasattr(self, "_event_data") else None

    def set_event_data(self, data: EventStreams):
        """
        set the station's event data

        :param data: EventStreams object to set
        """
        self._event_data = data

    def get_event_data_dir(self) -> str:
        """
        :return: the station's event data directory
        """
        return os.path.join(self.save_dir(), "events")

    def _get_id_key(self) -> str:
        """
        :return: the station's id and start time as a string
        """
        return f"{self._id}_{self.start_date_as_str()}"

    def find_loc_for_stats(self) -> Optional[Union[sd.LocationSensor, sd.BestLocationSensor]]:
        """
        :return: The first one of Location, BestLocation, or None found in the Station
        """
        if self.has_location_data():
            return self.location_sensor()
        elif self.has_best_location_data():
            return self.best_location_sensor()
        return None

    def _fix_sensor_data(self, sensor_type: sd.SensorType, data_table: pa.Table) -> pa.Table:
        """
        fix any problems with the data in data_table due to app/OS version

        :param sensor_type: type of sensor
        :param data_table: the data to edit
        :return: updated table
        """
        # iOS accelerometer recorded values in G's instead of m/s2 before app version 4.1.x
        if (
            sensor_type == sd.SensorType.ACCELEROMETER
            and self.metadata().os == st_utils.OsType["IOS"]
            and (
                self._app_version_major()[0] < 4
                or (self._app_version_major()[0] == 4 and self._app_version_major()[1] == 0)
            )
        ):
            data_table = data_table.set_column(
                2, "accelerometer_x", pa.array(data_table["accelerometer_x"].to_numpy() * -9.8)
            )
            data_table = data_table.set_column(
                3, "accelerometer_y", pa.array(data_table["accelerometer_y"].to_numpy() * -9.8)
            )
            data_table = data_table.set_column(
                4, "accelerometer_z", pa.array(data_table["accelerometer_z"].to_numpy() * -9.8)
            )
        return data_table

    def _set_pyarrow_sensors(self, sensor_summaries: ptp.AggregateSummary):
        """
        create sensors using pyarrow functions to convert summaries to tables and metadata

        :param sensor_summaries: summaries of sensor data that can be used to create sensors
        """
        audio_summary = sensor_summaries.get_audio()
        if audio_summary:
            # fuse audio into a single result
            self._gaps = sensor_summaries.gaps
            self._data.append(
                sd.AudioSensor(
                    audio_summary[0].name,
                    audio_summary[0].data(),
                    audio_summary[0].srate_hz,
                    1 / audio_summary[0].srate_hz,
                    0.0,
                    True,
                    use_offset_model_for_correction=self._use_model_correction,
                    base_dir=self.get_save_dir_sensor(sd.SensorType.AUDIO),
                    save_data=self._fs_writer.is_save_disk(),
                )
            )
            self.update_first_and_last_data_timestamps()
            for snr, sdata in sensor_summaries.get_non_audio().items():
                if self._fs_writer.is_save_disk():
                    data_table = ds.dataset(sdata[0].fdir, format="parquet", exclude_invalid_files=True).to_table()
                else:
                    data_table = sdata[0].data()
                    for i in range(1, len(sdata)):
                        data_table = pa.concat_tables([data_table, sdata[i].data()])
                data_table = self._fix_sensor_data(snr, data_table)
                if np.isnan(sdata[0].srate_hz):
                    timestamps = data_table["timestamps"].to_numpy()
                    interval_micros = float(np.mean(np.diff(timestamps))) if len(timestamps) > 1 else np.nan
                    calculate_stats = True
                    s_rate = np.nan
                    s_intv = np.nan
                    s_intv_std = np.nan
                    fixed_rate = False
                else:
                    interval_micros = s_to_us(sdata[0].smint_s)
                    calculate_stats = False
                    s_rate = sdata[0].srate_hz
                    s_intv = 1 / sdata[0].srate_hz
                    s_intv_std = 0.0
                    fixed_rate = True
                d, g = gpu.fill_gaps(data_table, self._gaps, interval_micros, "copy")
                new_sensor = sd.SensorData(
                    sensor_name=sdata[0].name,
                    sensor_data=d,
                    gaps=g,
                    save_data=self._fs_writer.is_save_disk(),
                    sensor_type=snr,
                    calculate_stats=calculate_stats,
                    sample_rate_hz=s_rate,
                    sample_interval_s=s_intv,
                    sample_interval_std_s=s_intv_std,
                    is_sample_rate_fixed=fixed_rate,
                    use_offset_model_for_correction=self._use_model_correction,
                    base_dir=self.get_save_dir_sensor(sdata[0].stype),
                )
                self._data.append(new_sensor.class_from_type())
            self._set_gps_offset()
        else:
            self._errors.append("Audio Sensor expected, but does not exist.")

    def _set_gps_offset(self):
        """
        uses the Station's location sensor to set the gps offset.
        """
        loc_sensor = self.find_loc_for_stats()
        if loc_sensor:
            gps_timestamps = loc_sensor.get_gps_timestamps_data()
            unique_gps = np.unique(gps_timestamps)
            if len(unique_gps) != len(gps_timestamps):
                keep_gps = []
                for n in unique_gps:
                    for k in range(len(gps_timestamps)):
                        if n == gps_timestamps[k]:
                            keep_gps.append(k)
                            break
                gps_offsets = gps_timestamps[keep_gps] - loc_sensor.data_timestamps()[keep_gps]
            else:
                gps_offsets = gps_timestamps - loc_sensor.data_timestamps()
            gps_offsets += GPS_LATENCY_MICROS
            if all(np.nan_to_num(gps_offsets) == 0.0):
                self._errors.append(f"{self._id} Location data is all invalid, cannot set GPS offset.")
                return
            self._gps_offset_model = OffsetModel(
                np.empty(0), gps_offsets, gps_timestamps, gps_timestamps[0], gps_timestamps[-1]
            )
        else:
            self._errors.append("No location data to set GPS offset.")

    def _app_version_major(self) -> Tuple[int, int]:
        """
        :return: tuple of app version to 2 significant version numbers (i.e: version number x.y.z returns x and y)
        """
        nums = self.metadata().app_version.split(".")
        if self.metadata().os == st_utils.OsType["IOS"]:
            nums[1] = nums[1].split(" ")[0]
        return int(nums[0]), int(nums[1])

    def metadata(self) -> st_utils.StationMetadata:
        """
        :return: station metadata
        """
        return self._metadata

    def set_metadata(self, metadata: st_utils.StationMetadata):
        """
        set the station's metadata

        :param metadata: metadata to set
        """
        self._metadata = metadata

    def packet_metadata(self) -> List[st_utils.StationPacketMetadata]:
        """
        :return: data packet metadata
        """
        return self._packet_metadata

    def set_packet_metadata(self, packet_metadata: List[st_utils.StationPacketMetadata]):
        """
        set the station's packet metadata

        :param packet_metadata: packet metadata to set
        """
        self._packet_metadata = packet_metadata

    def first_data_timestamp(self) -> float:
        """
        :return: first data timestamp of station
        """
        return self._first_data_timestamp

    def last_data_timestamp(self) -> float:
        """
        :return: last data timestamp of station
        """
        return self._last_data_timestamp

    def use_model_correction(self) -> bool:
        """
        :return: if station used an offset model to correct timestamps
        """
        return self._use_model_correction

    def is_timestamps_updated(self) -> bool:
        """
        :return: if station has updated its timestamps
        """
        return self._is_timestamps_updated

    def set_timestamps_updated(self, is_updated: bool):
        """
        set if timestamps in station are already updated

        :param is_updated: is station timestamps updated
        """
        self._is_timestamps_updated = is_updated

    def timesync_data(self) -> TimeSync:
        """
        :return: the timesync data
        """
        return self._timesync_data

    def set_timesync_data(self, timesync: TimeSync):
        """
        set the timesync data for the station

        :param timesync: timesync data
        """
        self._timesync_data = timesync

    def gps_offset_model(self) -> OffsetModel:
        """
        :return: the gps offset model
        """
        if not hasattr(self, "_gps_offset_model"):
            self._set_gps_offset()
        return self._gps_offset_model

    def errors(self) -> RedVoxExceptions:
        """
        :return: errors of the station
        """
        return self._errors

    def set_errors(self, errors: RedVoxExceptions):
        """
        set the errors of the station

        :param errors: errors to set
        """
        self._errors = errors

    def append_error(self, error: str):
        """
        add an error to the station

        :param error: error to add
        """
        self._errors.append(error)

    def print_errors(self):
        """
        prints all errors in Station
        """
        self._errors.print()
        for sen in self._data:
            sen.print_errors()
        if hasattr(self, "_event_data"):
            for ev in self._event_data.streams:
                ev.print_errors()

    def audio_sample_rate_nominal_hz(self) -> float:
        """
        :return: expected audio sample rate of station in hz
        """
        return self._audio_sample_rate_nominal_hz

    def set_audio_sample_rate_hz(self, sample_rate: float):
        """
        set nominal sample rate of audio sensor

        :param sample_rate: rate in hz
        """
        self._audio_sample_rate_nominal_hz = sample_rate

    def is_audio_scrambled(self) -> float:
        """
        :return: if station's audio sensor data is scrambled
        """
        return self._is_audio_scrambled

    def set_audio_scrambled(self, is_scrambled: bool):
        """
        set if the audio is scrambled

        :param is_scrambled: is station audio scrambled
        """
        self._is_audio_scrambled = is_scrambled

    def is_save_to_disk(self) -> bool:
        """
        :return: if station is saving data to disk
        """
        return self._fs_writer.is_save_disk()

    def fs_writer(self) -> Fsw:
        """
        :return: FileSystemWriter for station
        """
        return self._fs_writer

    def set_use_temp_dir(self, use_temp_dir: bool = False):
        """
        :param use_temp_dir: if True, use temp dir to save data.  default False
        """
        self._fs_writer.set_use_temp(use_temp_dir)
        for snr in self._data:
            snr.set_use_temp_dir(use_temp_dir)

    def use_timesync_for_correction(self) -> bool:
        """
        Note: This function means nothing if the station is not set to correct timestamps

        :return: False if timesync has NAN mean latency or best offset is 0. True otherwise
        """
        return (
            False if np.isnan(self._timesync_data.mean_latency()) or self._timesync_data.best_offset() == 0.0 else True
        )

    def update_timestamps(self) -> "Station":
        """
        updates the timestamps in the station using the offset model

        :return: updated Station
        """
        if not self._is_timestamps_updated and self._correct_timestamps:
            offset_model = (
                self._timesync_data.offset_model() if self.use_timesync_for_correction() else self._gps_offset_model
            )
            self._start_date = offset_model.update_time(self._start_date, self._use_model_correction)
            for sensor in self._data:
                sensor.update_data_timestamps(offset_model)
            for packet in self._packet_metadata:
                packet.update_timestamps(offset_model, self._use_model_correction)
            for g in range(len(self._gaps)):
                self._gaps[g] = (offset_model.update_time(self._gaps[g][0]), offset_model.update_time(self._gaps[g][1]))
            if hasattr(self, "_event_data"):
                self._event_data.update_timestamps(offset_model, self.use_model_correction())
            if self._fs_writer.file_name != self._get_id_key():
                if self._fs_writer.is_save_disk():
                    old_name = self.save_dir()
                    self.set_save_dir(self._fs_writer.base_dir)
                    if old_name != "." and os.path.exists(old_name):
                        os.rename(old_name, self.save_dir())
                else:
                    self._fs_writer.file_name = self._get_id_key()
            self.update_first_and_last_data_timestamps()
            self._timesync_data.arrow_file = f"timesync_{self.start_date_as_str()}"
            self._is_timestamps_updated = True
        return self

    def undo_update_timestamps(self) -> "Station":
        """
        undoes non-sensor timestamp updates of the timestamps in the station using the offset model
        sensors already have unaltered timestamps

        :return: updated Station
        """
        if self._is_timestamps_updated:
            offset_model = (
                self._timesync_data.offset_model() if self.use_timesync_for_correction() else self._gps_offset_model
            )
            self._start_date = offset_model.get_original_time(self._start_date, self._use_model_correction)
            for sensor in self._data:
                sensor.set_original_timestamps()
            for packet in self._packet_metadata:
                packet.original_timestamps(offset_model, self._use_model_correction)
            for g in range(len(self._gaps)):
                self._gaps[g] = (
                    offset_model.get_original_time(self._gaps[g][0]),
                    offset_model.get_original_time(self._gaps[g][1]),
                )
            if hasattr(self, "_event_data"):
                self._event_data.original_timestamps(offset_model, self.use_model_correction())
            if self._fs_writer.file_name != self._get_id_key():
                if self._fs_writer.is_save_disk():
                    old_name = self.save_dir()
                    self.set_save_dir(self._fs_writer.base_dir)
                    if old_name != "." and os.path.exists(old_name):
                        os.rename(old_name, self.save_dir())
                else:
                    self._fs_writer.file_name = self._get_id_key()
            self.update_first_and_last_data_timestamps()
            self._timesync_data.arrow_file = f"timesync_{self.start_date_as_str()}"
            self._is_timestamps_updated = False
        return self
