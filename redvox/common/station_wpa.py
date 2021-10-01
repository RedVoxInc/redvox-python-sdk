"""
Defines generic station objects for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
Utilizes WrappedRedvoxPacketM (API M data packets) as the format of the data due to their versatility
"""
from typing import List, Optional, Tuple
import tempfile
import os
from pathlib import Path
import json
import shutil
from glob import glob

import numpy as np
import pyarrow.parquet as pq
import pyarrow as pa

from redvox.common import sensor_data_with_pyarrow as sd
from redvox.common import station_utils as st_utils
from redvox.common.timesync_wpa import TimeSyncArrow
from redvox.common.errors import RedVoxExceptions
import redvox.api1000.proto.redvox_api_m_pb2 as api_m
from redvox.common import packet_to_pyarrow as ptp
from redvox.common import gap_and_pad_utils_wpa as gpu
from redvox.common.stats_helper import StatsContainer
from redvox.common.date_time_utils import seconds_to_microseconds as s_to_us


class StationPa:
    """
    generic station for api-independent stuff; uses API M as the core data object since its quite versatile
    In order for a list of packets to be a station, all of the packets must:
        Have the same station id
        Have the same station uuid
        Have the same start time
        Have the same audio sample rate
    Properties:
        data: list sensor data associated with the station, default empty dictionary

        metadata: StationMetadata consistent across all packets, default empty StationMetadata

        packet_metadata: list of StationPacketMetadata that changes from packet to packet, default empty list

        _id: str id of the station, default None

        _uuid: str uuid of the station, default None

        _start_date: float of microseconds since epoch UTC when the station started recording, default np.nan

        first_data_timestamp: float of microseconds since epoch UTC of the first data point, default np.nan

        last_data_timestamp: float of microseconds since epoch UTC of the last data point, default np.nan

        audio_sample_rate_nominal_hz: float of nominal sample rate of audio component in hz, default np.nan

        is_audio_scrambled: bool, True if audio data is scrambled, default False

        is_timestamps_updated: bool, True if timestamps have been altered from original data values, default False

        timesync_data: TimeSyncArrow object, contains information about the station's time synchronization values

        _correct_timestamps: bool, if True, timestamps are updated as soon as they can be, default False

        use_model_correction: bool, if True, time correction is done using OffsetModel functions, otherwise
        correction is done by adding the OffsetModel's best offset (intercept value).  default True

        _gaps: List of Tuples of floats indicating start and end times of gaps.  Times are not inclusive of the gap.
    """

    def __init__(
            self,
            station_id: str = "",
            uuid: str = "",
            start_timestamp: float = np.nan,
            correct_timestamps: bool = False,
            use_model_correction: bool = True,
            base_out_dir: str = "",
            save_output: bool = False
    ):
        """
        initialize Station

        :param station_id: string id of the station; defined by users of the station, default ""
        :param uuid: string uuid of the station; automatically created by the station, default ""
        :param start_timestamp: timestamp in epoch UTC when station was started, default np.nan
        :param correct_timestamps: if True, correct all timestamps as soon as they can be, default False
        :param use_model_correction: if True, use OffsetModel functions for time correction, add OffsetModel
                                        best offset (intercept value) otherwise.  Default True
        :param base_out_dir: directory to save parquet files, default "" (current directory)
        :param save_output: if True, save the parquet files to base_out_dir, otherwise delete them.  default False
        """
        # _sensors is type, name, rate
        self._id = station_id
        self._uuid = uuid
        self._start_date = start_timestamp
        self._correct_timestamps = correct_timestamps
        self.use_model_correction = use_model_correction
        self.metadata = st_utils.StationMetadata("None")
        self.packet_metadata: List[st_utils.StationPacketMetadata] = []
        self.errors: RedVoxExceptions = RedVoxExceptions("Station")
        self.first_data_timestamp = np.nan
        self.last_data_timestamp = np.nan
        self.audio_sample_rate_nominal_hz = np.nan
        self.is_audio_scrambled = False
        self.timesync_data = TimeSyncArrow()
        self.is_timestamps_updated = False
        self.save_output: bool = save_output
        if self.save_output or base_out_dir:
            self.base_dir: str = base_out_dir
            self._temp_dir = None
        else:
            self._temp_dir = tempfile.TemporaryDirectory()
            self.base_dir = self._temp_dir.name

        self._data: List[sd.SensorDataPa] = []
        # self._sensors: Dict[sd.SensorType, Tuple[str, float]] = {}
        self._gaps: List[Tuple[float, float]] = []

    def __del__(self):
        if self._temp_dir:
            self._temp_dir.cleanup()

    def data(self) -> List[sd.SensorDataPa]:
        """
        :return: the sensors of the station as a list
        """
        return self._data

    @staticmethod
    def create_from_dir(in_dir: str = "",
                        use_model_correction: bool = True,
                        base_out_dir: str = "",
                        save_output: bool = False) -> "StationPa":
        """
        :param in_dir: structured directory with parquet files to load
        :param use_model_correction: if True, use OffsetModel functions for time correction, add OffsetModel
                                        best offset (intercept value) otherwise.  Default True
        :param base_out_dir: directory to save parquet files, default "" (current directory)
        :param save_output: if True, save the parquet files to base_out_dir, otherwise delete them.  default False
        :return: station using data from parquet files
        """
        raise AttributeError("Not enough data yet to make station.")
        # station = StationPa(use_model_correction=use_model_correction,
        #                     base_out_dir=base_out_dir, save_output=save_output)
        # station.load_data_from_parquet(in_dir)
        # return station

    @staticmethod
    def create_from_packets(packets: List[api_m.RedvoxPacketM],
                            correct_timestamps: bool = False,
                            use_model_correction: bool = True,
                            base_out_dir: str = "",
                            save_output: bool = False) -> "StationPa":
        """
        :param packets: API M redvox packets with data to load
        :param correct_timestamps: if True, correct timestamps as soon as possible.  Default False
        :param use_model_correction: if True, use OffsetModel functions for time correction, add OffsetModel
                                        best offset (intercept value) otherwise.  Default True
        :param base_out_dir: directory to save parquet files, default "" (current directory)
        :param save_output: if True, save the parquet files to base_out_dir, otherwise delete them.  default False
        :return: station using data from redvox packets.
        """
        station = StationPa(correct_timestamps=correct_timestamps, use_model_correction=use_model_correction,
                            base_out_dir=base_out_dir, save_output=save_output)
        station.load_data_from_packets(packets)
        return station

    @staticmethod
    def create_from_metadata(packet: api_m.RedvoxPacketM,
                             use_model_correction: bool = True,
                             base_out_dir: str = "",
                             save_output: bool = False) -> "StationPa":
        """
        create a station using metadata from a packet.  There will be no sensor or timing data added.

        :param packet: API M redvox packet to load metadata from
        :param use_model_correction: if True, use OffsetModel functions for time correction, add OffsetModel
                                        best offset (intercept value) otherwise.  Default True
        :param base_out_dir: directory to save parquet files, default "" (current directory)
        :param save_output: if True, save the parquet files to base_out_dir, otherwise delete them.  default False
        :return: StationPa without any sensor or timing
        """
        station = StationPa(use_model_correction=use_model_correction, base_out_dir=base_out_dir,
                            save_output=save_output)
        station._load_metadata_from_packet(packet)
        return station

    def load_data_from_packets(self, packets: List[api_m.RedvoxPacketM]):
        """
        fill station with data from packets
        :param packets: API M redvox packets with data to load
        """
        if packets and st_utils.validate_station_key_list(packets, self.errors):
            # noinspection Mypy
            self._load_metadata_from_packet(packets[0])
            self.packet_metadata = [
                st_utils.StationPacketMetadata(packet) for packet in packets
            ]
            self.timesync_data = TimeSyncArrow().from_raw_packets(packets)
            if self._correct_timestamps:
                self._start_date = self.timesync_data.offset_model.update_time(
                    self._start_date, self.use_model_correction
                )
            self.base_dir = os.path.join(self.base_dir, self._get_id_key())
            # self._audio_rate = packets[0].sensors.audio.sample_rate
            # self._audio_name = packets[0].sensors.audio.sensor_description
            if self.save_output:
                if os.path.exists(self.base_dir):
                    shutil.rmtree(self.base_dir)
                os.makedirs(self.base_dir, exist_ok=True)
            self.timesync_data.arrow_dir = os.path.join(self.base_dir, "timesync")
            if self._start_date and not np.isnan(self._start_date):
                self.timesync_data.arrow_file_name = f"timesync_{int(self._start_date)}"
            else:
                self.timesync_data.arrow_file_name = f"timesync_0"
            self._set_pyarrow_sensors(ptp.stream_to_pyarrow(packets, self.base_dir if self.save_output else None))

    def _load_metadata_from_packet(self, packet: api_m.RedvoxPacketM):
        """
        sets metadata that applies to the entire station from a single packet

        :param packet: API-M redvox packet to load metadata from
        """
        # self.id = packet.station_information.id
        self._id = packet.station_information.id.zfill(10)
        self._uuid = packet.station_information.uuid
        self._start_date = packet.timing_information.app_start_mach_timestamp
        if self._start_date < 0:
            self.errors.append(
                f"Station {self._id} has station start date before epoch.  "
                f"Station start date reset to np.nan"
            )
            self._start_date = np.nan
        self.metadata = st_utils.StationMetadata("Redvox", packet)
        if isinstance(packet, api_m.RedvoxPacketM) and packet.sensors.HasField("audio"):
            self.audio_sample_rate_nominal_hz = packet.sensors.audio.sample_rate
            self.is_audio_scrambled = packet.sensors.audio.is_scrambled
        else:
            self.audio_sample_rate_nominal_hz = np.nan
            self.is_audio_scrambled = False

    def _sort_metadata_packets(self):
        """
        orders the metadata packets by their starting timestamps.  Returns nothing, sorts the data in place
        """
        self.packet_metadata.sort(key=lambda t: t.packet_start_mach_timestamp)

    def _get_start_and_end_timestamps(self):
        """
        uses the audio data to get the first and last timestamp of the station
        """
        self.first_data_timestamp = self.audio_sensor().first_data_timestamp()
        self.last_data_timestamp = self.audio_sensor().last_data_timestamp()

    def set_id(self, station_id: str) -> "StationPa":
        """
        set the station's id

        :param station_id: id of station
        :return: modified version of self
        """
        self._id = station_id
        return self

    def get_id(self) -> Optional[str]:
        """
        :return: the station id or None if it doesn't exist
        """
        return self._id

    def set_uuid(self, uuid: str) -> "StationPa":
        """
        set the station's uuid

        :param uuid: uuid of station
        :return: modified version of self
        """
        self._uuid = uuid
        return self

    def get_uuid(self) -> Optional[str]:
        """
        :return: the station uuid or None if it doesn't exist
        """
        return self._uuid

    def set_start_date(self, start_timestamp: float) -> "StationPa":
        """
        set the station's start timestamp in microseconds since epoch utc

        :param start_timestamp: start_timestamp of station
        :return: modified version of self
        """
        self._start_date = start_timestamp
        return self

    def get_start_date(self) -> float:
        """
        :return: the station start timestamp or np.nan if it doesn't exist
        """
        return self._start_date

    def check_key(self) -> bool:
        """
        check if the station has enough information to set its key.

        :return: True if key can be set, False if not enough information
        """
        if self._id:
            if self._uuid:
                if np.isnan(self._start_date):
                    self.errors.append("Station start timestamp not defined.")
                return True
            else:
                self.errors.append("Station uuid is not valid.")
        else:
            self.errors.append("Station id is not set.")
        return False

    def get_key(self) -> Optional[st_utils.StationKey]:
        """
        :return: the station's key if id, uuid and start timestamp is set, or None if key cannot be created
        """
        if self.check_key():
            return st_utils.StationKey(self._id, self._uuid, self._start_date)
        return None

    def append_station(self, new_station: "StationPa"):
        """
        append a new station to the current station; does nothing if keys do not match

        :param new_station: Station to append to current station
        """
        if (
                self.get_key() is not None
                and new_station.get_key() == self.get_key()
                and self.metadata.validate_metadata(new_station.metadata)
        ):
            self.append_station_data(new_station._data)
            self.packet_metadata.extend(new_station.packet_metadata)
            self._sort_metadata_packets()
            self._get_start_and_end_timestamps()
            self.timesync_data.append_timesync_arrow(new_station.timesync_data)

    def append_station_data(self, new_station_data: List[sd.SensorDataPa]):
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
        return [s.type for s in self._data]

    def get_sensor_by_type(self, sensor_type: sd.SensorType) -> Optional[sd.SensorDataPa]:
        """
        :param sensor_type: type of sensor to get
        :return: the sensor of the type or None if it doesn't exist
        """
        for s in self._data:
            if s.type == sensor_type:
                return s
        return None

    def append_sensor(self, sensor_data: sd.SensorDataPa):
        """
        append sensor data to an existing sensor_type or add a new sensor to the dictionary

        :param sensor_data: the data to append
        """
        if sensor_data.type in self.get_station_sensor_types():
            self.get_sensor_by_type(sensor_data.type).append_sensor(sensor_data)
        else:
            self._add_sensor(sensor_data.type, sensor_data)
        self.errors.extend_error(sensor_data.errors)

    def _delete_sensor(self, sensor_type: sd.SensorType):
        """
        removes a sensor from the sensor data dictionary if it exists

        :param sensor_type: the sensor to remove
        """
        if sensor_type in self.get_station_sensor_types():
            self._data.remove(self.get_sensor_by_type(sensor_type))

    def _add_sensor(self, sensor_type: sd.SensorType, sensor: sd.SensorDataPa):
        """
        adds a sensor to the sensor data dictionary

        :param sensor_type: the type of sensor to add
        :param sensor: the sensor data to add
        """
        if sensor_type in self.get_station_sensor_types():
            raise ValueError(
                f"Cannot add sensor type ({sensor_type.name}) that already exists in packet!"
            )
        else:
            self._data.append(sensor)

    def get_mean_packet_duration(self) -> float:
        """
        :return: mean duration of packets in microseconds
        """
        return float(
            np.mean(
                [tsd.packet_end_mach_timestamp - tsd.packet_start_mach_timestamp for tsd in self.packet_metadata]
            )
        )

    def get_mean_packet_audio_samples(self) -> float:
        """
        calculate the mean number of audio samples per packet using the
          number of audio sensor's data points and the number of packets

        :return: mean number of audio samples per packet
        """
        # noinspection Mypy
        return self.audio_sensor().num_samples() / len(self.packet_metadata)

    def has_timesync_data(self) -> bool:
        """
        :return: True if there is timesync data for the station
        """
        return self.timesync_data.num_tri_messages() > 0

    def has_audio_sensor(self) -> bool:
        """
        :return: True if audio sensor exists
        """
        return sd.SensorType.AUDIO in self.get_station_sensor_types()

    def has_audio_data(self) -> bool:
        """
        :return: True if audio sensor exists and has any data
        """
        audio_sensor: Optional[sd.SensorDataPa] = self.audio_sensor()
        return audio_sensor is not None and audio_sensor.num_samples() > 0

    def audio_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: audio sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.AUDIO)

    def set_audio_sensor(
            self, audio_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        location_sensor: Optional[sd.SensorDataPa] = self.location_sensor()
        return location_sensor is not None and location_sensor.num_samples() > 0

    def location_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: location sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.LOCATION)

    def set_location_sensor(
            self, loc_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        location_sensor: Optional[sd.SensorDataPa] = self.best_location_sensor()
        return location_sensor is not None and location_sensor.num_samples() > 0

    def best_location_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: best location sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.BEST_LOCATION)

    def set_best_location_sensor(
            self, best_loc_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.accelerometer_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def accelerometer_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: accelerometer sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.ACCELEROMETER)

    def set_accelerometer_sensor(
            self, acc_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.magnetometer_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def magnetometer_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: magnetometer sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.MAGNETOMETER)

    def set_magnetometer_sensor(
            self, mag_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.gyroscope_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def gyroscope_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: gyroscope sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.GYROSCOPE)

    def set_gyroscope_sensor(
            self, gyro_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.pressure_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def pressure_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: pressure sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.PRESSURE)

    def set_pressure_sensor(
            self, pressure_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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

    def barometer_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: barometer (pressure) sensor if it exists, None otherwise
        """
        return self.pressure_sensor()

    def set_barometer_sensor(
            self, bar_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.light_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def light_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: light sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.LIGHT)

    def set_light_sensor(
            self, light_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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

    def infrared_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: infrared (proximity) sensor if it exists, None otherwise
        """
        return self.proximity_sensor()

    def set_infrared_sensor(
            self, infrd_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.proximity_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def proximity_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: proximity sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.PROXIMITY)

    def set_proximity_sensor(
            self, proximity_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.image_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def image_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: image sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.IMAGE)

    def set_image_sensor(self, img_sensor: Optional[sd.SensorDataPa] = None) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.ambient_temperature_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def ambient_temperature_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: ambient temperature sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.AMBIENT_TEMPERATURE)

    def set_ambient_temperature_sensor(
            self, amb_temp_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.relative_humidity_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def relative_humidity_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: relative humidity sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.RELATIVE_HUMIDITY)

    def set_relative_humidity_sensor(
            self, rel_hum_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.gravity_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def gravity_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: gravity sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.GRAVITY)

    def set_gravity_sensor(
            self, grav_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.linear_acceleration_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def linear_acceleration_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: linear acceleration sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.LINEAR_ACCELERATION)

    def set_linear_acceleration_sensor(
            self, lin_acc_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.orientation_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def orientation_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: orientation sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.ORIENTATION)

    def set_orientation_sensor(
            self, orientation_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.rotation_vector_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def rotation_vector_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: rotation vector sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.ROTATION_VECTOR)

    def set_rotation_vector_sensor(
            self, rot_vec_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.compressed_audio_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def compressed_audio_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: compressed audio sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.COMPRESSED_AUDIO)

    def set_compressed_audio_sensor(
            self, comp_audio_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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
        sensor: Optional[sd.SensorDataPa] = self.health_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def health_sensor(self) -> Optional[sd.SensorDataPa]:
        """
        :return: station health sensor (station metrics) if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.STATION_HEALTH)

    def set_health_sensor(
            self, health_sensor: Optional[sd.SensorDataPa] = None
    ) -> "StationPa":
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

    def get_gaps(self) -> List[Tuple[float, float]]:
        """
        get the audio gaps of the stations
        :return: list pairs of timestamps of the data points on the edge of gaps
        """
        return self._gaps

    def _get_id_key(self) -> str:
        """
        :return: the station's id and start time as a string
        """
        if np.isnan(self._start_date):
            return f"{self._id}_0"
        return f"{self._id}_{int(self._start_date)}"

    def _set_pyarrow_sensors(self, sensor_summaries: ptp.AggregateSummary):
        """
        create pyarrow tables that will become sensors (and in audio's case, just make it a sensor)
        :param sensor_summaries: summaries of sensor data that can be used to create sensors
        """
        self._gaps = sensor_summaries.audio_gaps
        self.errors.extend_error(sensor_summaries.errors)
        audo = sensor_summaries.get_audio()[0]
        if audo:
            # avoid converting packets into parquets for now; just load the data into memory and process
            # if self.save_output:
            #     self._data.append(sd.SensorDataPa.from_dir(
            #         sensor_name=audo.name, data_path=audo.fdir, sensor_type=audo.stype,
            #         sample_rate_hz=audo.srate_hz, sample_interval_s=1/audo.srate_hz,
            #         sample_interval_std_s=0., is_sample_rate_fixed=True)
            #     )
            # else:
            #     self._data.append(sd.SensorDataPa(audo.name, audo.data(), audo.stype,
            #                                       audo.srate_hz, 1/audo.srate_hz, 0., True))
            self._data.append(sd.SensorDataPa(audo.name, audo.data(), audo.stype,
                                              audo.srate_hz, 1/audo.srate_hz, 0., True,
                                              arrow_dir=audo.fdir, save_data=self.save_output))
            self._get_start_and_end_timestamps()
            for snr, sdata in sensor_summaries.get_non_audio().items():
                stats = StatsContainer(snr.name)
                # avoid converting packets into parquets for now; just load the data into memory and process
                # if self.save_output:
                #     data_table = ds.dataset(sdata[0].fdir, format="parquet", exclude_invalid_files=True).to_table()
                # else:
                #     data_table = sdata[0].data()
                #     for i in range(1, len(sdata)):
                #         data_table = pa.concat_tables([data_table, sdata[i].data()])
                data_table = sdata[0].data()
                for i in range(1, len(sdata)):
                    data_table = pa.concat_tables([data_table, sdata[i].data()])
                if np.isnan(sdata[0].srate_hz):
                    for sds in sdata:
                        stats.add(sds.smint_s, sds.sstd_s, sds.scount - 1)
                    d, g = gpu.fill_gaps(
                        data_table,
                        sensor_summaries.audio_gaps,
                        s_to_us(stats.mean_of_means()), True)
                    self._data.append(sd.SensorDataPa(
                        sensor_name=sdata[0].name, sensor_data=d, gaps=g, save_data=self.save_output,
                        sensor_type=snr, calculate_stats=True, is_sample_rate_fixed=False, arrow_dir=sdata[0].fdir)
                    )
                else:
                    d, g = gpu.fill_gaps(
                        data_table,
                        sensor_summaries.audio_gaps,
                        s_to_us(sdata[0].smint_s), True)
                    self._data.append(sd.SensorDataPa(
                        sensor_name=sdata[0].name, sensor_data=d, gaps=g, save_data=self.save_output,
                        sensor_type=snr, sample_rate_hz=sdata[0].srate_hz, sample_interval_s=1/sdata[0].srate_hz,
                        sample_interval_std_s=0., is_sample_rate_fixed=True, arrow_dir=sdata[0].fdir)
                    )
        else:
            self.errors.append("Audio Sensor expected, but does not exist.")

    def update_timestamps(self) -> "StationPa":
        """
        updates the timestamps in the station using the offset model
        """
        if self.is_timestamps_updated:
            self.errors.append("Timestamps already corrected!")
        else:
            # if timestamps were not corrected on creation
            if not self._correct_timestamps:
                # self.timesync_data.update_timestamps(self.use_model_correction)
                self._start_date = self.timesync_data.offset_model.update_time(
                    self._start_date, self.use_model_correction
                )
                self.base_dir = os.path.join(self.base_dir, self._get_id_key())
            for sensor in self._data:
                sensor.update_data_timestamps(self.timesync_data.offset_model, self.use_model_correction)
            for packet in self.packet_metadata:
                packet.update_timestamps(self.timesync_data.offset_model, self.use_model_correction)
            for g in range(len(self._gaps)):
                self._gaps[g] = (self.timesync_data.offset_model.update_time(self._gaps[g][0]),
                                 self.timesync_data.offset_model.update_time(self._gaps[g][1]))
            self._get_start_and_end_timestamps()
            self.is_timestamps_updated = True
        return self

    def to_json(self) -> json:
        """
        :return: station as json string
        """
        return json.dumps({
            "id": self._id,
            "uuid": self._uuid,
            "start_date": self._start_date,
            "base_dir": self.base_dir,
            "use_model_correction": self.use_model_correction,
            "is_audio_scrambled": self.is_audio_scrambled,
            "is_timestamps_updated": self.is_timestamps_updated,
            "audio_sample_rate_nominal_hz": self.audio_sample_rate_nominal_hz,
            "first_data_timestamp": self.first_data_timestamp,
            "last_data_timestamp": self.last_data_timestamp,
            "metadata": self.metadata.as_dict(),
            "packet_metadata": [p.__dict__ for p in self.packet_metadata],
            "gaps": self._gaps,
            "errors": self.errors.as_dict(),
            "sensors": [s.type.name for s in self._data]
        })

    def default_station_json_file_name(self) -> str:
        """
        :return: default station json file name (id_startdate), with startdate as integer
        """
        return f"{self._id}_{int(self._start_date)}"

    def to_json_file(self, file_name: Optional[str] = None) -> Path:
        """
        saves the station as json in station.base_dir, then creates directories and the json for the metadata
        and data in the same base_dir.

        :param file_name: the optional base file name.  Do not include a file extension.
                            If None, a default file name is created using this format:
                            [station_id]_[start_date].json
        :return: path to json file
        """
        _file_name: str = (
            file_name
            if file_name is not None
            else self.default_station_json_file_name()
        )

        # write the sensor objects, using the default values
        for datas in self._data:
            datas.to_json_file()

        ts_dir = os.path.join(self.base_dir, "timesync")
        os.makedirs(ts_dir, exist_ok=True)
        self.timesync_data.to_json_file()

        file_path: Path = Path(self.base_dir).joinpath(f"{_file_name}.json")
        with open(file_path, "w") as f_p:
            f_p.write(self.to_json())
            return file_path.resolve(False)

    @staticmethod
    def from_json_file(file_path: str) -> "StationPa":
        """
        convert contents of json file to Station
        :param file_path: full path of file to load data from.
        :return: Station object
        """
        with open(file_path, "r") as f_p:
            json_data = json.loads(f_p.read())
        result = StationPa(json_data["id"], json_data["uuid"], json_data["start_date"],
                           json_data["use_model_correction"])
        result.is_audio_scrambled = json_data["is_audio_scrambled"]
        result.is_timestamps_updated = json_data["is_timestamps_updated"]
        result.audio_sample_rate_nominal_hz = json_data["audio_sample_rate_nominal_hz"]
        result.first_data_timestamp = json_data["first_data_timestamp"]
        result.last_data_timestamp = json_data["last_data_timestamp"]
        result.metadata = st_utils.StationMetadata.from_dict(json_data["metadata"])
        result.packet_metadata = [st_utils.StationPacketMetadata.from_dict(p) for p in json_data["packet_metadata"]]
        result.gaps = json_data["gaps"]
        result.errors = RedVoxExceptions.from_dict(json_data["errors"])

        for s in json_data["sensors"]:
            file = glob(os.path.join(json_data["base_dir"], s, "*.json"))
            for f in file:
                result._data.append(sd.SensorDataPa.from_json(f))

        file = glob(os.path.join(json_data["base_dir"], "timesync", "*.json"))
        for f in file:
            result.timesync_data = TimeSyncArrow.from_json(f)

        return result


class StationPaJson:
    """
    converts a station into JSON and parquet files
        metadata: StationMetadata consistent across all packets, default empty StationMetadata
        uuid: str uuid of the station, default None
        start_timestamp: float of microseconds since epoch UTC when the station started recording, default np.nan
        first_data_timestamp: float of microseconds since epoch UTC of the first data point, default np.nan
        last_data_timestamp: float of microseconds since epoch UTC of the last data point, default np.nan
        audio_sample_rate_nominal_hz: float of nominal sample rate of audio component in hz, default np.nan
        is_audio_scrambled: bool, True if audio data is scrambled, default False
        is_timestamps_updated: bool, True if timestamps have been altered from original data values, default False
        use_model_correction: bool, if True, time correction is done using OffsetModel functions, otherwise
            correction is done by adding the OffsetModel's best offset (intercept value).  default True
    """
    def __init__(self, station: StationPa):
        self.id = station.get_id()
        gaps = {"gap_start": [], "gap_end": []}
        for gp in station.get_gaps():
            gaps["gap_start"].append(gp[0])
            gaps["gap_end"].append(gp[1])
        pq.write_table(pa.Table.from_pydict(gaps), os.path.join(station.base_dir, "gaps.parquet"))
        packet_metadata = {"packet_start_mach_timestamp": [],
                           "packet_end_mach_timestamp": [],
                           "packet_start_os_timestamp": [],
                           "packet_end_os_timestamp": [],
                           "timing_info_score": []}
        self.packet_metadata = []
        for pmd in station.packet_metadata:
            packet_metadata["packet_start_mach_timestamp"].append(pmd.packet_start_mach_timestamp)
            packet_metadata["packet_end_mach_timestamp"].append(pmd.packet_end_mach_timestamp)
            packet_metadata["packet_start_os_timestamp"].append(pmd.packet_start_os_timestamp)
            packet_metadata["packet_end_os_timestamp"].append(pmd.packet_end_os_timestamp)
            packet_metadata["timing_info_score"].append(pmd.timing_info_score)
        self.packet_metadata = station.packet_metadata
        self.timesync = station.timesync_data
        self.base_dir = station.base_dir
