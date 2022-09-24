from typing import List, Dict, Optional, Callable, Tuple

import numpy as np

import redvox
from redvox.common.sensor_reader_utils import get_all_sensors_in_packet
from redvox.common.errors import RedVoxExceptions
import redvox.api1000.proto.redvox_api_m_pb2 as api_m
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc


class StationModel:
    """
    Station Model designed to summarize the entirety of a station's operational period

    Properties:
        location: lat, lon, alt
        _sensors: the name of sensors and their mean sample rate as a dictionary
    """
    def __init__(self,
                 station_id: str = "",
                 uuid: str = "",
                 start_timestamp: float = np.nan,
                 api: float = np.nan,
                 sub_api: float = np.nan,
                 make: str = "",
                 model: str = "",
                 app_version: str = "",
                 packet_duration_s: float = np.nan,
                 station_description: str = "",
                 created_from_packet: bool = False,
                 first_data_timestamp: float = np.nan,
                 last_data_timestamp: float = np.nan,
                 first_location: Optional[Tuple[float, float, float]] = None,
                 last_location: Optional[Tuple[float, float, float]] = None):
        self._id: str = station_id
        self._uuid: str = uuid
        self._start_date: float = start_timestamp
        self.app: str = "Redvox"
        self.api: float = api
        self.sub_api: float = sub_api
        self.make: str = make
        self.model: str = model
        self.app_version: str = app_version
        self.packet_duration_s: float = packet_duration_s
        self.station_description: str = station_description
        self.num_packets: int = 1 if created_from_packet else 0
        self.first_data_timestamp: float = first_data_timestamp
        self.last_data_timestamp: float = last_data_timestamp
        self.first_location: Optional[Tuple[float, float, float]] = first_location
        self.last_location: Optional[Tuple[float, float, float]] = last_location
        self.has_moved: bool = first_location != last_location
        self._errors: RedVoxExceptions = RedVoxExceptions("StationModel")
        self._sdk_version: str = redvox.version()
        self._sensors: Dict[str, float] = {}

    def __repr__(self):
        return f"id: {self._id}, " \
               f"uuid: {self._uuid}, " \
               f"start_date: {self._start_date}, " \
               f"app: {self.app}, " \
               f"api: {self.api}, " \
               f"sub_api: {self.sub_api}, " \
               f"make: {self.make}, " \
               f"model: {self.model}, " \
               f"app_version: {self.app_version}, " \
               f"packet_duration_s: {self.packet_duration_s}, " \
               f"station_description: {self.station_description}, " \
               f"num_packets: {self.num_packets}, " \
               f"first_data_timestamp: {self.first_data_timestamp}, " \
               f"last_data_timestamp: {self.last_data_timestamp}, " \
               f"first_location: {self.first_location}, " \
               f"last_location: {self.last_location}, " \
               f"has_moved: {self.has_moved}, " \
               f"audio_sample_rate_hz: {self.audio_sample_rate_nominal_hz()}, " \
               f"sdk_version: {self._sdk_version}, " \
               f"sensors: {self._sensors}"

    def __str__(self):
        start_date = np.nan if np.isnan(self._start_date) \
            else datetime_from_epoch_microseconds_utc(self._start_date).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        first_timestamp = np.nan if np.isnan(self.first_data_timestamp) \
            else datetime_from_epoch_microseconds_utc(self.first_data_timestamp).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        last_timestamp = np.nan if np.isnan(self.last_data_timestamp) \
            else datetime_from_epoch_microseconds_utc(self.last_data_timestamp).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return f"id: {self._id}, " \
               f"uuid: {self._uuid}, " \
               f"start_date: {start_date}, " \
               f"app: {self.app}, " \
               f"api: {self.api}, " \
               f"sub_api: {self.sub_api}, " \
               f"make: {self.make}, " \
               f"model: {self.model}, " \
               f"app_version: {self.app_version}, " \
               f"packet_duration_s: {self.packet_duration_s}, " \
               f"station_description: {self.station_description}, " \
               f"num_packets: {self.num_packets}, " \
               f"first_data_timestamp: {first_timestamp}, " \
               f"last_data_timestamp: {last_timestamp}, " \
               f"first_location: {self.first_location}, " \
               f"last_location: {self.last_location}, " \
               f"has_moved: {self.has_moved}, " \
               f"audio_sample_rate_hz: {self.audio_sample_rate_nominal_hz()}, " \
               f"sdk_version: {self._sdk_version}, " \
               f"sensors: {self._sensors}"

    def id(self) -> str:
        """
        :return: the id of the StationModel
        """
        return self._id

    def uuid(self) -> str:
        """
        :return: the uuid of the StationModel
        """
        return self._uuid

    def start_date(self) -> float:
        """
        :return: the start_date of the StationModel
        """
        return self._start_date

    def print_errors(self):
        """
        Prints all errors in the StationModel to screen
        """
        self._errors.print()

    def audio_sample_rate_nominal_hz(self) -> float:
        """
        :return: the nominal audio sample rate in hz
        """
        return self._sensors["audio"]

    def get_data_from_packet(self, packet: api_m.RedvoxPacketM) -> "StationModel":
        """
        loads data from a packet into the model.  stops reading data if there is an error

        :param packet: API M packet to add
        :return: the updated StationModel
        """
        if self.num_packets < 1:
            return self.create_from_packet(packet)
        if packet.station_information.id == self._id:
            if packet.station_information.uuid == self._uuid:
                if packet.timing_information.app_start_mach_timestamp == self._start_date:
                    packet_start = packet.timing_information.packet_start_mach_timestamp
                    packet_end = packet.timing_information.packet_end_mach_timestamp
                    sensors = get_all_sensors_in_packet(packet)
                    sensors.append("health")
                    if list(self._sensors.keys()) != sensors:
                        self._errors.append(f"packet sensors {sensors} does not match.")
                    else:
                        self.num_packets += 1
                        if packet_start < self.first_data_timestamp:
                            self.first_data_timestamp = packet_start
                        if packet_end > self.last_data_timestamp:
                            self.last_data_timestamp = packet_end
                        for s in sensors:
                            if s == "accelerometer":
                                v = packet.sensors.accelerometer.timestamps.mean_sample_rate
                            elif s == "ambient_temperature":
                                v = packet.sensors.ambient_temperature.timestamps.mean_sample_rate
                            elif s == "gravity":
                                v = packet.sensors.gravity.timestamps.mean_sample_rate
                            elif s == "gyroscope":
                                v = packet.sensors.gyroscope.timestamps.mean_sample_rate
                            elif s == "light":
                                v = packet.sensors.light.timestamps.mean_sample_rate
                            elif s == "linear_acceleration":
                                v = packet.sensors.linear_acceleration.timestamps.mean_sample_rate
                            elif s == "location":
                                v = packet.sensors.location.timestamps.mean_sample_rate
                                if self.first_location is None or self.first_data_timestamp > packet_start:
                                    self.first_location = (packet.sensors.location.latitude_samples.values[0],
                                                           packet.sensors.location.longitude_samples.values[0],
                                                           packet.sensors.location.altitude_samples.values[0])
                                if self.last_data_timestamp < packet.sensors.location.timestamps.timestamps[-1]:
                                    self.last_location = (packet.sensors.location.latitude_samples.values[-1],
                                                          packet.sensors.location.longitude_samples.values[-1],
                                                          packet.sensors.location.altitude_samples.values[-1])
                                if not self.has_moved:
                                    self.has_moved = self.first_location != self.last_location
                            elif s == "magnetometer":
                                v = packet.sensors.magnetometer.timestamps.mean_sample_rate
                            elif s == "orientation":
                                v = packet.sensors.orientation.timestamps.mean_sample_rate
                            elif s == "pressure":
                                v = packet.sensors.pressure.timestamps.mean_sample_rate
                            elif s == "proximity":
                                v = packet.sensors.proximity.timestamps.mean_sample_rate
                            elif s == "relative_humidity":
                                v = packet.sensors.relative_humidity.timestamps.mean_sample_rate
                            elif s == "rotation_vector":
                                v = packet.sensors.rotation_vector.timestamps.mean_sample_rate
                            else:
                                v = np.nan
                            self._sensors[s] += (v - self._sensors[s]) / self.num_packets
                else:
                    self._errors.append(f"packet start date {packet.timing_information.app_start_mach_timestamp} "
                                        f"does not match.")
            else:
                self._errors.append(f"packet uuid {packet.station_information.uuid} does not match.")
        else:
            self._errors.append(f"packet id {packet.station_information.id} does not match.")
        return self

    def set_sensor_data(self, packet: api_m.RedvoxPacketM):
        """
        set the sensor information of a StationModel from a single packet
        CAUTION: Overwrites any existing data

        :param packet: API M packet of data to read
        """
        sensors = get_all_sensors_in_packet(packet)
        sensors.append("health")
        for s in sensors:
            if s == "health":
                v = packet.station_information.station_metrics.timestamps.mean_sample_rate
            elif s == "accelerometer":
                v = packet.sensors.accelerometer.timestamps.mean_sample_rate
            elif s == "ambient_temperature":
                v = packet.sensors.ambient_temperature.timestamps.mean_sample_rate
            elif s == "audio":
                v = packet.sensors.audio.sample_rate
            elif s == "compressed_audio":
                v = packet.sensors.compressed_audio.sample_rate
            elif s == "gravity":
                v = packet.sensors.gravity.timestamps.mean_sample_rate
            elif s == "gyroscope":
                v = packet.sensors.gyroscope.timestamps.mean_sample_rate
            elif s == "image":
                v = packet.sensors.image.timestamps.mean_sample_rate
            elif s == "light":
                v = packet.sensors.light.timestamps.mean_sample_rate
            elif s == "linear_acceleration":
                v = packet.sensors.linear_acceleration.timestamps.mean_sample_rate
            elif s == "location":
                v = packet.sensors.location.timestamps.mean_sample_rate
                if self.first_location is None \
                        or self.first_data_timestamp > packet.sensors.location.timestamps.timestamps[0]:
                    self.first_location = (packet.sensors.location.latitude_samples.values[0],
                                           packet.sensors.location.longitude_samples.values[0],
                                           packet.sensors.location.altitude_samples.values[0])
                if self.last_location is None \
                        or self.last_data_timestamp < packet.sensors.location.timestamps.timestamps[-1]:
                    self.last_location = (packet.sensors.location.latitude_samples.values[-1],
                                          packet.sensors.location.longitude_samples.values[-1],
                                          packet.sensors.location.altitude_samples.values[-1])
                if not self.has_moved:
                    self.has_moved = self.first_location != self.last_location
            elif s == "magnetometer":
                v = packet.sensors.magnetometer.timestamps.mean_sample_rate
            elif s == "orientation":
                v = packet.sensors.orientation.timestamps.mean_sample_rate
            elif s == "pressure":
                v = packet.sensors.pressure.timestamps.mean_sample_rate
            elif s == "proximity":
                v = packet.sensors.proximity.timestamps.mean_sample_rate
            elif s == "relative_humidity":
                v = packet.sensors.relative_humidity.timestamps.mean_sample_rate
            elif s == "rotation_vector":
                v = packet.sensors.rotation_vector.timestamps.mean_sample_rate
            else:
                v = np.nan
            self._sensors[s] = v

    @staticmethod
    def create_from_packet(packet: api_m.RedvoxPacketM) -> "StationModel":
        """
        create a StationModel from a single packet

        :param packet: API M packet of data to read
        :return: StationModel using the data from the packet
        """
        result = StationModel(packet.station_information.id, packet.station_information.uuid,
                              packet.timing_information.app_start_mach_timestamp, packet.api, packet.sub_api,
                              packet.station_information.make, packet.station_information.model,
                              packet.station_information.app_version,
                              len(packet.sensors.audio.samples.values) / packet.sensors.audio.sample_rate,
                              packet.station_information.description, True,
                              packet.timing_information.packet_start_mach_timestamp,
                              packet.timing_information.packet_end_mach_timestamp,
                              (packet.sensors.location.latitude_samples.values[0],
                               packet.sensors.location.longitude_samples.values[0],
                               packet.sensors.location.altitude_samples.values[0]),
                              (packet.sensors.location.latitude_samples.values[-1],
                               packet.sensors.location.longitude_samples.values[-1],
                               packet.sensors.location.altitude_samples.values[-1])
                              )
        result.set_sensor_data(packet)
        return result

    def stream_data(self, data_stream: List[api_m.RedvoxPacketM]) -> "StationModel":
        """
        Read data from a stream into the StationModel

        :param data_stream: series of files from a single station to read
        :return: updated model
        """
        for p in data_stream:
            self.get_data_from_packet(p)
        return self

    @staticmethod
    def create_from_stream(data_stream: List[api_m.RedvoxPacketM]) -> "StationModel":
        """
        create a StationModel from a single stream of data

        :param data_stream: series of API M files from a single station to read
        :return: StationModel using the data from the stream
        """
        model = StationModel.create_from_packet(data_stream.pop(0))
        for p in data_stream:
            model.get_data_from_packet(p)
        return model

    def num_sensors(self) -> int:
        """
        :return: number of sensors in the Station
        """
        return len(self._sensors.keys())

    def list_of_sensors(self) -> List[str]:
        """
        :return: list of sensor names as strings
        """
        return list(self._sensors.keys())
