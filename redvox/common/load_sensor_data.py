"""
This module loads or reads sensor data from various sources
"""
import os
import glob
import numpy as np
import pandas as pd
from obspy import read
from typing import List, Dict, Optional
from redvox.api1000 import io as apim_io
from redvox.api900 import reader as api900_io
from redvox.common import file_statistics as fs, date_time_utils as dtu, timesync as ts
from redvox.common.sensor_data import SensorType, SensorData, Station, StationTiming, StationMetadata, DataPacket
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
from redvox.api1000.wrapped_redvox_packet.sensors import xyz, single
from redvox.api1000.wrapped_redvox_packet import wrapped_packet as apim_wp
from dataclasses import dataclass


@dataclass
class StationSummary:
    """
    Contains a summary of each stations data read result.
    """
    station_id: str
    station_uuid: str
    os: str
    os_version: str
    app_version: str
    audio_sampling_rate: float
    total_duration: float
    start_dt: dtu.datetime
    end_dt: dtu.datetime

    @staticmethod
    def from_station(station: Station) -> 'StationSummary':
        total_duration: float = station.audio_sensor().data_duration_s()
        start_dt: dtu.datetime = dtu.datetime_from_epoch_microseconds_utc(station.audio_sensor().first_data_timestamp())
        end_dt: dtu.datetime = dtu.datetime_from_epoch_microseconds_utc(station.audio_sensor().last_data_timestamp())

        station_info = station.station_metadata
        audio = station.audio_sensor()
        return StationSummary(
            station_info.station_id,
            station_info.station_uuid,
            station_info.station_os if station_info.station_os is not None else "OS UNKNOWN",
            station_info.station_os_version if station_info.station_os_version is not None else "OS VERSION UNKNOWN",
            station_info.station_app_version if station_info.station_app_version is not None else "APP VERSION UNKNOWN",
            audio.sample_rate if audio is not None else float("NaN"),
            total_duration,
            start_dt,
            end_dt
        )


class ReadResult:
    """
    Stores station information after being read from files
    """
    def __init__(self,
                 station_id_uuid_to_stations: Dict[str, Station]):
        """
        :param station_id_uuid_to_stations: station_id:station_uuid -> station information
        """
        self.station_id_uuid_to_stations: Dict[str, Station] = station_id_uuid_to_stations
        self.__station_id_to_id_uuid: Dict[str, str] = {}
        self.__station_summaries: List[StationSummary] = []

        self.update_metadata()

    def update_metadata(self):
        """
        updates ids:uuids pairs and summary information
        """
        for id_uuid, station in self.station_id_uuid_to_stations.items():
            s: List[str] = id_uuid.split(":")
            self.__station_id_to_id_uuid[s[0]] = s[1]
            self.__station_summaries.append(StationSummary.from_station(station))

    def __get_station_id_by_uuid(self, uuid: str) -> str:
        """
        given a uuid, returns the station_id
        :param uuid: uuid to search for
        :return: the station_id of the uuid, or an empty string if uuid doesn't exist
        """
        for station_id, station_uuid in self.__station_id_to_id_uuid.items():
            if station_uuid == uuid:
                return station_id
        return ""

    def pop_station(self, station_id: str) -> 'ReadResult':
        """
        removes a station from the ReadResult; station_id can be one of id, uuid or id:uuid
        :param station_id: station to remove
        :return: copy of ReadResult without the station_id specified
        """
        if ":" in station_id:
            s: List[str] = station_id.split(":")
            station_id = s[0]
        elif station_id in self.__station_id_to_id_uuid.values():  # check if uuid was given
            station_id = self.__get_station_id_by_uuid(station_id)
        if self.check_for_id(station_id):
            self.station_id_uuid_to_stations.pop(f"{station_id}:{self.__station_id_to_id_uuid[station_id]}")
            self.__station_id_to_id_uuid.pop(station_id)
            summaries = self.__station_summaries.copy()  # put summaries into temp variable
            self.__station_summaries.clear()             # clear summaries and rebuild
            for summary in summaries:
                if summary.station_id != station_id:
                    self.__station_summaries.append(summary)
        else:
            print(f"ReadResult cannot remove station {station_id} because it does not exist")
        return self

    def check_for_id(self, check_id: str) -> bool:
        """
        Look at keys and shortened keys in for the check_id; must be id or uuid combination
        :param check_id: id to look for
        :return: True if check_id is in the ReadResult
        """
        return check_id in self.__station_id_to_id_uuid.keys() or check_id in self.__station_id_to_id_uuid.values()

    def get_station(self, station_id: str) -> Optional[Station]:
        """
        Find the station identified by the station_id given; it can be id or id:uuid
        :param station_id: str id of station; can be id or id:uuid
        :return: the station if it exists, None otherwise
        """
        if ":" in station_id:
            return self.station_id_uuid_to_stations[station_id]
        elif self.check_for_id(station_id):
            return self.station_id_uuid_to_stations[f"{station_id}:{self.__station_id_to_id_uuid[station_id]}"]
        print(f"WARNING: ReadResult attempted to read station id: {station_id}, but could not find id in results")
        return None

    def get_all_stations(self) -> List[Station]:
        """
        Return a list of all stations in the ReadResult
        :return: a list of all stations
        """
        return list(self.station_id_uuid_to_stations.values())

    def get_station_summaries(self) -> List[StationSummary]:
        """
        :return: A list of StationSummaries contained in this ReadResult
        """
        return self.__station_summaries

    def append_station(self, new_station_id: str, new_station: Station):
        """
        adds a station to the ReadResult.  Appends data to existing stations
        :param new_station_id: id of station to add
        :param new_station: Station object to add
        """
        if self.check_for_id(new_station_id):
            self.station_id_uuid_to_stations[new_station_id].append_station_data(new_station.station_data)
        else:
            self.station_id_uuid_to_stations[new_station_id] = new_station
            self.__station_id_to_id_uuid[new_station.station_metadata.station_id] = \
                new_station.station_metadata.station_uuid
            self.__station_summaries.append(StationSummary.from_station(new_station))

    def append(self, new_stations: 'ReadResult'):
        """
        adds stations to the ReadResult
        :param new_stations: stations to add
        """
        for new_station_id, new_station in new_stations.station_id_uuid_to_stations.items():
            self.append_station(new_station_id, new_station)


def calc_evenly_sampled_timestamps(start: float, samples: int, rate_hz: float) -> np.array:
    """
    given a start time, calculates samples amount of evenly spaced timestamps at rate_hz
    :param start: float, start timestamp
    :param samples: int, number of samples
    :param rate_hz: float, sample rate in hz
    :return: np.array with evenly spaced timestamps starting at start
    """
    return np.array(start + dtu.seconds_to_microseconds(np.arange(0, samples) / rate_hz))


def read_api900_non_mic_sensor(sensor: api900_io.RedvoxSensor, column_id: str) -> SensorData:
    """
    read a sensor that does not have mic data from an api900 data packet
    :param sensor: the non-mic api900 sensor to read
    :param column_id: string, used to name the columns
    :return: generic SensorData object
    """
    timestamps = sensor.timestamps_microseconds_utc()
    if len(timestamps) > 1:
        sample_interval = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
    else:
        sample_interval = np.nan
    if type(sensor) in [api900_io.AccelerometerSensor, api900_io.MagnetometerSensor, api900_io.GyroscopeSensor]:
        data_for_df = np.transpose([timestamps,
                                    sensor.payload_values_x(), sensor.payload_values_y(), sensor.payload_values_z()])
        columns = ["timestamps", f"{column_id}_x", f"{column_id}_y", f"{column_id}_z"]
    else:
        data_for_df = np.transpose([timestamps, sensor.payload_values()])
        columns = ["timestamps", column_id]
    return SensorData(sensor.sensor_name(), pd.DataFrame(data_for_df, columns=columns), 1 / sample_interval,
                      sample_interval, False)


def read_api900_wrapped_packet(wrapped_packet: api900_io.WrappedRedvoxPacket) -> Dict[SensorType, SensorData]:
    """
    reads the data from a wrapped api900 redvox packet into a dictionary of generic data
    :param wrapped_packet: a wrapped api900 redvox packet
    :return: a dictionary containing all the sensor data
    """
    data_dict: Dict[SensorType, SensorData] = {}
    # there are 9 api900 sensors
    if wrapped_packet.has_microphone_sensor():
        sample_rate_hz = wrapped_packet.microphone_sensor().sample_rate_hz()
        timestamps = calc_evenly_sampled_timestamps(
            wrapped_packet.microphone_sensor().first_sample_timestamp_epoch_microseconds_utc(),
            fs.get_num_points_from_sample_rate(sample_rate_hz), sample_rate_hz)
        data_for_df = np.transpose([timestamps, wrapped_packet.microphone_sensor().payload_values().astype(float)])
        data_dict[SensorType.AUDIO] = SensorData(wrapped_packet.microphone_sensor().sensor_name(),
                                                 pd.DataFrame(data_for_df, columns=["timestamps", "microphone"]),
                                                 sample_rate_hz, 1 / sample_rate_hz, True)
    if wrapped_packet.has_accelerometer_sensor():
        data_dict[SensorType.ACCELEROMETER] = \
            read_api900_non_mic_sensor(wrapped_packet.accelerometer_sensor(), "accelerometer")
    if wrapped_packet.has_magnetometer_sensor():
        data_dict[SensorType.MAGNETOMETER] = \
            read_api900_non_mic_sensor(wrapped_packet.magnetometer_sensor(), "magnetometer")
    if wrapped_packet.has_gyroscope_sensor():
        data_dict[SensorType.GYROSCOPE] = read_api900_non_mic_sensor(wrapped_packet.gyroscope_sensor(), "gyroscope")
    if wrapped_packet.has_barometer_sensor():
        data_dict[SensorType.PRESSURE] = read_api900_non_mic_sensor(wrapped_packet.barometer_sensor(), "barometer")
    if wrapped_packet.has_light_sensor():
        data_dict[SensorType.LIGHT] = read_api900_non_mic_sensor(wrapped_packet.light_sensor(), "light")
    if wrapped_packet.has_infrared_sensor():
        data_dict[SensorType.INFRARED] = read_api900_non_mic_sensor(wrapped_packet.infrared_sensor(), "infrared")
    if wrapped_packet.has_image_sensor():
        data_dict[SensorType.IMAGE] = read_api900_non_mic_sensor(wrapped_packet.image_sensor(), "image")
    if wrapped_packet.has_location_sensor():
        timestamps = wrapped_packet.location_sensor().timestamps_microseconds_utc()
        if len(timestamps) > 1:
            sample_interval = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
        else:
            sample_interval = np.nan
        if wrapped_packet.location_sensor().check_for_preset_lat_lon():
            lat_lon = wrapped_packet.location_sensor().get_payload_lat_lon()
            data_for_df = np.array([[timestamps[0], lat_lon[0], lat_lon[1], np.nan, np.nan, np.nan,
                                     LocationProvider.USER]])
        else:
            data_for_df = np.transpose([timestamps,
                                        wrapped_packet.location_sensor().payload_values_latitude(),
                                        wrapped_packet.location_sensor().payload_values_longitude(),
                                        wrapped_packet.location_sensor().payload_values_altitude(),
                                        wrapped_packet.location_sensor().payload_values_speed(),
                                        wrapped_packet.location_sensor().payload_values_accuracy(),
                                        np.full(len(timestamps), np.nan)])
        columns = ["timestamps", "latitude", "longitude", "altitude", "speed", "accuracy", "location_provider"]
        data_dict[SensorType.LOCATION] = SensorData(wrapped_packet.location_sensor().sensor_name(),
                                                    pd.DataFrame(data_for_df, columns=columns),
                                                    1 / sample_interval, sample_interval, False)
    return data_dict


def load_station_from_api900(api900_packet: api900_io.WrappedRedvoxPacket,
                             start_timestamp_utc_s: Optional[int] = None,
                             end_timestamp_utc_s: Optional[int] = None) -> Station:
    """
    reads in station data from a single wrapped api900 packet
    :param api900_packet: wrapped api900 packet to read from
    :param start_timestamp_utc_s: The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: The end timestamp as seconds since the epoch UTC.
    :return: a station Object
    """
    # set station metadata and timing
    timing = StationTiming(api900_packet.mach_time_zero(), api900_packet.microphone_sensor().sample_rate_hz(),
                           api900_packet.app_file_start_timestamp_epoch_microseconds_utc(),
                           start_timestamp_utc_s, end_timestamp_utc_s,
                           np.nan if api900_packet.best_latency() is None else api900_packet.best_latency(),
                           0.0 if api900_packet.best_offset() is None else api900_packet.best_offset())
    metadata = StationMetadata(api900_packet.redvox_id(), api900_packet.device_make(),
                               api900_packet.device_model(), False, api900_packet.device_os(),
                               api900_packet.device_os_version(), "Redvox", api900_packet.app_version(),
                               api900_packet.is_scrambled(), timing, station_uuid=api900_packet.uuid())
    data_dict = read_api900_wrapped_packet(api900_packet)
    packet_data = DataPacket(api900_packet.server_timestamp_epoch_microseconds_utc(),
                             api900_packet.app_file_start_timestamp_machine(),
                             len(api900_packet.microphone_sensor().payload_values()),
                             len(api900_packet.microphone_sensor().payload_values()) /
                             api900_packet.microphone_sensor().sample_rate_hz(),
                             float(api900_packet.start_timestamp_us_utc()), api900_packet.end_timestamp_us_utc(),
                             api900_packet.time_synchronization_sensor().payload_values(),
                             np.nan if api900_packet.best_latency() is None else api900_packet.best_latency(),
                             0.0 if api900_packet.best_offset() is None else api900_packet.best_offset())
    packet_list: List[DataPacket] = [packet_data]
    # get the best timing values for the station
    if timing.station_best_latency is None or np.isnan(timing.station_best_latency):
        ts_analysis = ts.TimeSyncData(packet_data, metadata)
        timing.station_best_latency = ts_analysis.best_latency
        timing.station_best_offset = ts_analysis.best_offset
    return Station(metadata, data_dict, packet_list)


def load_station_from_api900_file(directory: str, start_timestamp_utc_s: Optional[int] = None,
                                  end_timestamp_utc_s: Optional[int] = None) -> Station:
    """
    reads in station data from a single api900 file
    :param directory: string of the file to read from
    :param start_timestamp_utc_s: The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: The end timestamp as seconds since the epoch UTC.
    :return: a station Object
    """
    api900_packet = api900_io.read_rdvxz_file(directory)
    return load_station_from_api900(api900_packet, start_timestamp_utc_s, end_timestamp_utc_s)


def load_file_range_from_api900(directory: str,
                                start_timestamp_utc_s: Optional[int] = None,
                                end_timestamp_utc_s: Optional[int] = None,
                                redvox_ids: Optional[List[str]] = None,
                                structured_layout: bool = False,
                                concat_continuous_segments: bool = True) -> ReadResult:
    """
    reads in api900 data from a directory and returns a list of stations
    note that the param descriptions are taken directly from api900.reader.read_rdvxz_file_range
    :param directory: The root directory of the data. If structured_layout is False, then this directory will
                      contain various unorganized .rdvxz files. If structured_layout is True, then this directory
                      must be the root api900 directory of the structured files.
    :param start_timestamp_utc_s: The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: The end timestamp as seconds since the epoch UTC.
    :param redvox_ids: An optional list of redvox_ids to filter against (default=[]).
    :param structured_layout: An optional value to define if this is loading structured data (default=False).
    :param concat_continuous_segments: An optional value to define if this function should concatenate rdvxz files
                                       into multiple continuous rdvxz files separated at gaps.
    :return: a list of Station objects that contain the data
    """
    all_stations: ReadResult = ReadResult({})
    all_data = api900_io.read_rdvxz_file_range(directory, start_timestamp_utc_s, end_timestamp_utc_s, redvox_ids,
                                               structured_layout, concat_continuous_segments)
    for redvox_id, wrapped_packets in all_data.items():
        # set station metadata and timing based on first packet
        timing = StationTiming(wrapped_packets[0].mach_time_zero(),
                               wrapped_packets[0].microphone_sensor().sample_rate_hz(),
                               wrapped_packets[0].app_file_start_timestamp_epoch_microseconds_utc(),
                               start_timestamp_utc_s, end_timestamp_utc_s,
                               np.nan if wrapped_packets[0].best_latency() is None else
                               wrapped_packets[0].best_latency(),
                               0.0 if wrapped_packets[0].best_offset() is None else wrapped_packets[0].best_offset())
        metadata = StationMetadata(wrapped_packets[0].redvox_id(), wrapped_packets[0].device_make(),
                                   wrapped_packets[0].device_model(), False, wrapped_packets[0].device_os(),
                                   wrapped_packets[0].device_os_version(), "Redvox", wrapped_packets[0].app_version(),
                                   wrapped_packets[0].is_scrambled(), timing, station_uuid=wrapped_packets[0].uuid())
        # add data from packets
        new_station = Station(metadata)
        packet_list: List[DataPacket] = []
        for packet in wrapped_packets:
            if packet.has_time_synchronization_sensor():
                time_sync = packet.time_synchronization_sensor().payload_values()
            else:
                time_sync = None
            data_dict = read_api900_wrapped_packet(packet)
            new_station.append_station_data(data_dict)
            packet_data = DataPacket(packet.server_timestamp_epoch_microseconds_utc(),
                                     packet.app_file_start_timestamp_machine(),
                                     data_dict[SensorType.AUDIO].num_samples(),
                                     data_dict[SensorType.AUDIO].data_duration_s(),
                                     float(packet.start_timestamp_us_utc()), packet.end_timestamp_us_utc(),
                                     time_sync, np.nan if packet.best_latency() is None else packet.best_latency(),
                                     0.0 if packet.best_offset() is None else packet.best_offset())
            packet_list.append(packet_data)
        new_station.packet_data = packet_list

        if timing.station_best_latency is None or np.isnan(timing.station_best_latency):
            # get the best timing values for the station
            ts_analysis = ts.TimeSyncAnalysis(new_station)
            new_station.station_metadata.timing_data.station_best_latency = ts_analysis.get_best_latency()
            new_station.station_metadata.timing_data.station_best_offset = ts_analysis.get_best_offset()

        # create the Station data object
        all_stations.append_station(redvox_id, new_station)

    return all_stations


def read_apim_xyz_sensor(sensor: xyz.Xyz, column_id: str) -> SensorData:
    """
    read a sensor that has xyz data channels from an api M data packet
    :param sensor: the xyz api M sensor to read
    :param column_id: string, used to name the columns
    :return: generic SensorData object
    """
    timestamps = sensor.get_timestamps().get_timestamps()
    if len(timestamps) > 1:
        sample_interval = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
    else:
        sample_interval = np.nan
    data_for_df = np.transpose([timestamps,
                                sensor.get_x_samples().get_values(),
                                sensor.get_y_samples().get_values(),
                                sensor.get_z_samples().get_values()])
    columns = ["timestamps", f"{column_id}_x", f"{column_id}_y", f"{column_id}_z"]
    return SensorData(sensor.get_sensor_description(), pd.DataFrame(data_for_df, columns=columns),
                      1 / sample_interval, sample_interval, False)


def read_apim_single_sensor(sensor: single.Single, column_id: str) -> SensorData:
    """
    read a sensor that has a single data channel from an api M data packet
    :param sensor: the single channel api M sensor to read
    :param column_id: string, used to name the columns
    :return: generic SensorData object
    """
    timestamps = sensor.get_timestamps().get_timestamps()
    if len(timestamps) > 1:
        sample_interval = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
    else:
        sample_interval = np.nan
    data_for_df = np.transpose([timestamps, sensor.get_samples().get_values()])
    columns = ["timestamps", column_id]
    return SensorData(sensor.get_sensor_description(), pd.DataFrame(data_for_df, columns=columns),
                      sample_interval, sample_interval, False)


def load_apim_wrapped_packet(wrapped_packet: apim_wp.WrappedRedvoxPacketM) -> Dict[SensorType, SensorData]:
    """
    reads the data from a wrapped api M redvox packet into a dictionary of generic data
    :param wrapped_packet: a wrapped api M redvox packet
    :return: a dictionary containing all the sensor data
    """
    data_dict: Dict[SensorType, SensorData] = {}
    sensors = wrapped_packet.get_sensors()
    # there are 16 api M sensors
    if sensors.has_audio() and sensors.validate_audio():
        sample_rate_hz = sensors.get_audio().get_sample_rate()
        data_for_df = sensors.get_audio().get_samples().get_values()
        timestamps = calc_evenly_sampled_timestamps(sensors.get_audio().get_first_sample_timestamp(),
                                                    len(data_for_df), sample_rate_hz)
        data_dict[SensorType.AUDIO] = SensorData(sensors.get_audio().get_sensor_description(),
                                                 pd.DataFrame(np.transpose([timestamps, data_for_df]),
                                                              columns=["timestamps", "microphone"]),
                                                 sample_rate_hz, 1 / sample_rate_hz, True)
    if sensors.has_compress_audio() and sensors.validate_compressed_audio():
        sample_rate_hz = sensors.get_compressed_audio().get_sample_rate()
        data_for_df = sensors.get_compressed_audio().get_samples().get_values()
        timestamps = calc_evenly_sampled_timestamps(sensors.get_compressed_audio().get_first_sample_timestamp(),
                                                    len(data_for_df), sample_rate_hz)
        data_dict[SensorType.COMPRESSED_AUDIO] = SensorData(sensors.get_compressed_audio().get_sensor_description(),
                                                            pd.DataFrame(np.transpose([timestamps, data_for_df]),
                                                                         columns=["compressed_audio"]),
                                                            sample_rate_hz, 1 / sample_rate_hz, True)
    if sensors.has_accelerometer() and sensors.validate_accelerometer():
        data_dict[SensorType.ACCELEROMETER] = read_apim_xyz_sensor(sensors.get_accelerometer(), "accelerometer")
    if sensors.has_magnetometer() and sensors.validate_magnetometer():
        data_dict[SensorType.MAGNETOMETER] = read_apim_xyz_sensor(sensors.get_magnetometer(), "magnetometer")
    if sensors.has_linear_acceleration() and sensors.validate_accelerometer():
        data_dict[SensorType.LINEAR_ACCELERATION] = read_apim_xyz_sensor(sensors.get_linear_acceleration(),
                                                                         "linear_accel")
    if sensors.has_orientation() and sensors.validate_orientation():
        data_dict[SensorType.ORIENTATION] = read_apim_xyz_sensor(sensors.get_orientation(), "orientation")
    if sensors.has_rotation_vector() and sensors.validate_rotation_vector():
        data_dict[SensorType.ROTATION_VECTOR] = read_apim_xyz_sensor(sensors.get_rotation_vector(), "rotation_vector")
    if sensors.has_gyroscope() and sensors.validate_gyroscope():
        data_dict[SensorType.GYROSCOPE] = read_apim_xyz_sensor(sensors.get_gyroscope(), "gyroscope")
    if sensors.has_gravity() and sensors.validate_gravity():
        data_dict[SensorType.GRAVITY] = read_apim_xyz_sensor(sensors.get_gravity(), "gravity")
    if sensors.has_pressure() and sensors.validate_pressure():
        data_dict[SensorType.PRESSURE] = read_apim_single_sensor(sensors.get_pressure(), "barometer")
    if sensors.has_light() and sensors.validate_light():
        data_dict[SensorType.LIGHT] = read_apim_single_sensor(sensors.get_light(), "light")
    if sensors.has_proximity() and sensors.validate_proximity():
        data_dict[SensorType.PROXIMITY] = read_apim_single_sensor(sensors.get_proximity(), "proximity")
    if sensors.has_ambient_temperature() and sensors.validate_ambient_temperature():
        data_dict[SensorType.TEMPERATURE] = read_apim_single_sensor(sensors.get_ambient_temperature(), "ambient_temp")
    if sensors.has_relative_humidity() and sensors.validate_relative_humidity():
        data_dict[SensorType.RELATIVE_HUMIDITY] = read_apim_single_sensor(sensors.get_relative_humidity(),
                                                                          "rel_humidity")
    if sensors.has_image() and sensors.validate_image():
        timestamps = sensors.get_image().get_timestamps().get_timestamps()
        if len(timestamps) > 1:
            sample_interval = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
        else:
            sample_interval = np.nan
        data_for_df = np.transpose([timestamps, sensors.get_image().get_samples()])
        data_dict[SensorType.IMAGE] = SensorData(sensors.get_image().get_sensor_description(),
                                                 pd.DataFrame(data_for_df, columns=["image"]),
                                                 1 / sample_interval, sample_interval, False)
    if sensors.has_location():
        if sensors.validate_location():
            timestamps = sensors.get_location().get_timestamps().get_timestamps()
            if len(timestamps) > 1:
                sample_interval = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
            else:
                sample_interval = np.nan
            data_for_df = np.transpose([timestamps,
                                        sensors.get_location().get_latitude_samples().get_values(),
                                        sensors.get_location().get_longitude_samples().get_values(),
                                        sensors.get_location().get_altitude_samples().get_values(),
                                        sensors.get_location().get_speed_samples().get_values(),
                                        sensors.get_location().get_bearing_samples().get_values(),
                                        sensors.get_location().get_horizontal_accuracy_samples().get_values(),
                                        sensors.get_location().get_vertical_accuracy_samples().get_values(),
                                        sensors.get_location().get_speed_samples().get_values(),
                                        sensors.get_location().get_bearing_accuracy_samples().get_values(),
                                        sensors.get_location().get_location_providers().get_values()])
        elif sensors.get_location().get_last_best_location():
            timestamps = [sensors.get_location().get_last_best_location().get_latitude_longitude_timestamp().get_mach()]
            sample_interval = np.nan
            data_for_df = np.transpose([[timestamps],
                                        [sensors.get_location().get_last_best_location().get_latitude()],
                                        [sensors.get_location().get_last_best_location().get_longitude()],
                                        [sensors.get_location().get_last_best_location().get_altitude()],
                                        [sensors.get_location().get_last_best_location().get_speed()],
                                        [sensors.get_location().get_last_best_location().get_bearing()],
                                        [sensors.get_location().get_last_best_location().get_horizontal_accuracy()],
                                        [sensors.get_location().get_last_best_location().get_vertical_accuracy()],
                                        [sensors.get_location().get_last_best_location().get_speed_accuracy()],
                                        [sensors.get_location().get_last_best_location().get_bearing_accuracy()],
                                        [sensors.get_location().get_last_best_location().get_location_provider()]])
        else:
            # well, there's no location, so there's nothing left to do but
            return data_dict
        # if here, location was good, add it in
        columns = ["timestamps", "latitude", "longitude", "altitude", "speed", "bearing",
                   "horizontal_accuracy", "vertical_accuracy", "speed_accuracy", "bearing_accuracy",
                   "location_provider"]
        data_dict[SensorType.LOCATION] = SensorData(sensors.get_location().get_sensor_description(),
                                                    pd.DataFrame(data_for_df, columns=columns),
                                                    1 / sample_interval, sample_interval, False)
    return data_dict


def load_station_from_apim(directory: str, start_timestamp_utc_s: Optional[int] = None,
                           end_timestamp_utc_s: Optional[int] = None) -> Station:
    """
    reads in station data from a single api M file
    :param directory: string of the file to read from
    :param start_timestamp_utc_s: The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: The end timestamp as seconds since the epoch UTC.
    :return: a station Object
    """
    read_packet = apim_io.read_rdvxm_file(directory)
    # set station metadata and timing based on first packet
    if read_packet.get_sensors().validate_audio():
        timing = StationTiming(read_packet.get_timing_information().get_app_start_mach_timestamp(),
                               read_packet.get_sensors().get_audio().get_sample_rate(),
                               read_packet.get_sensors().get_audio().get_first_sample_timestamp(),
                               start_timestamp_utc_s, end_timestamp_utc_s,
                               np.nan if read_packet.get_timing_information().get_best_latency() is None else
                               read_packet.get_timing_information().get_best_latency(),
                               0.0 if read_packet.get_timing_information().get_best_offset() is None else
                               read_packet.get_timing_information().get_best_offset())
    else:
        raise ValueError("Station is missing Audio sensor!")
    metadata = StationMetadata(read_packet.get_station_information().get_id(),
                               read_packet.get_station_information().get_make(),
                               read_packet.get_station_information().get_model(), False,
                               read_packet.get_station_information().get_os().name,
                               read_packet.get_station_information().get_os_version(), "Redvox",
                               read_packet.get_station_information().get_app_version(),
                               read_packet.get_station_information().get_app_settings().get_scramble_audio_data(),
                               timing, station_uuid=read_packet.get_station_information().get_uuid())
    # add data from packets
    time_sync_exchanges = read_packet.get_timing_information().get_synch_exchanges().get_values()
    time_sync = []
    for exchange in time_sync_exchanges:
        time_sync.extend([exchange.get_a1(), exchange.get_a2(), exchange.get_a3(),
                          exchange.get_b1(), exchange.get_b2(), exchange.get_b3()])
    data_dict = load_apim_wrapped_packet(read_packet)
    packet_data = DataPacket(read_packet.get_timing_information().get_server_acquisition_arrival_timestamp(),
                             read_packet.get_timing_information().get_app_start_mach_timestamp(),
                             data_dict[SensorType.AUDIO].num_samples(),
                             data_dict[SensorType.AUDIO].data_duration_s(),
                             read_packet.get_timing_information().get_packet_start_mach_timestamp(),
                             read_packet.get_timing_information().get_packet_end_mach_timestamp(),
                             np.array(time_sync),
                             np.nan if read_packet.get_timing_information().get_best_latency() is None else
                             read_packet.get_timing_information().get_best_latency(),
                             0.0 if read_packet.get_timing_information().get_best_offset() is None else
                             read_packet.get_timing_information().get_best_offset())
    packet_list: List[DataPacket] = [packet_data]
    # get the best timing values for the station
    if timing.station_best_latency is None or np.isnan(timing.station_best_latency):
        ts_analysis = ts.TimeSyncData(packet_data, metadata)
        timing.station_best_latency = ts_analysis.best_latency
        timing.station_best_offset = ts_analysis.best_offset
    return Station(metadata, data_dict, packet_list)


def load_from_file_range_api_m(directory: str,
                               start_timestamp_utc_s: Optional[int] = None,
                               end_timestamp_utc_s: Optional[int] = None,
                               redvox_ids: Optional[List[str]] = None,
                               structured_layout: bool = False) -> ReadResult:
    """
    reads in api M data from a directory and returns a list of stations
    :param directory: The root directory of the data. If structured_layout is False, then this directory will
                      contain various unorganized .rdvxm files. If structured_layout is True, then this directory
                      must be the root api1000 directory of the structured files.
    :param start_timestamp_utc_s: The start timestamp in seconds since the epoch UTC.
    :param end_timestamp_utc_s: The end timestamp in seconds since the epoch UTC.
    :param redvox_ids: An optional list of redvox_ids to filter against, default empty list
    :param structured_layout: An optional value to define if this is loading structured data, default False.
    :return: a list of Station objects that contain the data
    """
    all_stations: ReadResult = ReadResult({})
    all_data = apim_io.read_structured(directory, start_timestamp_utc_s, end_timestamp_utc_s, redvox_ids,
                                       structured_layout)
    for read_packets in all_data.all_wrapped_packets:
        # set station metadata and timing based on first packet
        if read_packets.wrapped_packets[0]:
            if read_packets.wrapped_packets[0].get_sensors().get_audio():
                first_pack = read_packets.wrapped_packets[0]
                timing = StationTiming(read_packets.start_mach_timestamp, read_packets.audio_sample_rate,
                                       first_pack.get_sensors().get_audio().get_first_sample_timestamp(),
                                       start_timestamp_utc_s, end_timestamp_utc_s,
                                       np.nan if first_pack.get_timing_information().get_best_latency() is None else
                                       first_pack.get_timing_information().get_best_latency(),
                                       0.0 if first_pack.get_timing_information().get_best_offset() is None else
                                       first_pack.get_timing_information().get_best_offset())
                station_info = first_pack.get_station_information()
                metadata = StationMetadata(read_packets.redvox_id, station_info.get_make(), station_info.get_model(),
                                           False, station_info.get_os().name, station_info.get_os_version(),
                                           "Redvox", station_info.get_app_version(),
                                           station_info.get_app_settings().get_scramble_audio_data(), timing,
                                           station_uuid=read_packets.uuid)
            else:
                raise ValueError("Error reading data window: Packet is missing Audio sensor!")
        else:
            raise ValueError("Error reading data window: First packet of data is missing!")
        new_station = Station(metadata)
        # add data from packets
        packet_list: List[DataPacket] = []
        for packet in read_packets.wrapped_packets:
            time_sync = packet.get_timing_information().get_synch_exchange_array()
            data_dict = load_apim_wrapped_packet(packet)
            new_station.append_station_data(data_dict)
            packet_data = DataPacket(packet.get_timing_information().get_server_acquisition_arrival_timestamp(),
                                     packet.get_timing_information().get_app_start_mach_timestamp(),
                                     data_dict[SensorType.AUDIO].num_samples(),
                                     data_dict[SensorType.AUDIO].data_duration_s(),
                                     packet.get_timing_information().get_packet_start_mach_timestamp(),
                                     packet.get_timing_information().get_packet_end_mach_timestamp(),
                                     np.array(time_sync),
                                     np.nan if packet.get_timing_information().get_best_latency() is None else
                                     packet.get_timing_information().get_best_latency(),
                                     0.0 if packet.get_timing_information().get_best_offset() is None else
                                     packet.get_timing_information().get_best_offset())
            packet_list.append(packet_data)
        new_station.packet_data = packet_list

        if timing.station_best_latency is None or np.isnan(timing.station_best_latency):
            # get the best timing values for the station
            ts_analysis = ts.TimeSyncAnalysis(new_station)
            new_station.station_metadata.timing_data.station_best_latency = ts_analysis.get_best_latency()
            new_station.station_metadata.timing_data.station_best_offset = ts_analysis.get_best_offset()

        # create the Station data object
        all_stations.append_station(f"{read_packets.redvox_id}:{read_packets.uuid}", new_station)
    return all_stations


def load_from_mseed(file_path: str, station_ids: Optional[List[str]] = None) -> ReadResult:
    """
    load station data from a miniseed file
    :param file_path: the location of the miniseed file
    :param station_ids: the station ids to search for, default None; if None, get all stations
    :return: a list of Station objects that contain the data
    """
    stations: ReadResult = ReadResult({})
    strm = read(file_path)
    for data_stream in strm:
        record_info = data_stream.meta
        start_time = int(dtu.seconds_to_microseconds(data_stream.meta["starttime"].timestamp))
        end_time = int(dtu.seconds_to_microseconds(data_stream.meta["endtime"].timestamp))
        station_timing = StationTiming(np.nan, record_info["sampling_rate"], start_time, start_time, end_time)
        station_id = f'{record_info["network"]}{record_info["station"]}_{record_info["location"]}'
        metadata = StationMetadata(station_id, "mb3_make", "mb3_model", False, "mb3_os", "mb3_os_vers",
                                   "mb3_recorder", "mb3_recorder_version", False, station_timing,
                                   record_info["calib"], record_info["network"], record_info["station"],
                                   record_info["location"], record_info["channel"], record_info["mseed"]["encoding"])
        sample_rate_hz = record_info["sampling_rate"]
        timestamps = calc_evenly_sampled_timestamps(start_time, int(record_info["npts"]), sample_rate_hz)
        data_for_df = np.transpose([timestamps, data_stream.data])
        sensor_data = SensorData(record_info["channel"], pd.DataFrame(data_for_df, columns=["timestamps", "BDF"]),
                                 record_info["sampling_rate"], True)
        data_packet = DataPacket(np.nan, start_time, start_time, end_time)
        if station_ids is None or station_id in station_ids:
            stations.append_station(f"{station_id}:{station_id}", Station(metadata, {SensorType.AUDIO: sensor_data},
                                                                          [data_packet]))
    return stations


def read_all_in_dir(directory: str,
                    start_timestamp_utc_s: Optional[int] = None,
                    end_timestamp_utc_s: Optional[int] = None,
                    redvox_ids: Optional[List[str]] = None,
                    structured_layout: bool = False) -> ReadResult:
    """
    load all data files in the directory
    :param directory: location of all the files; if structured_layout is True, the directory contains a root api1000,
                        api900, or mseed directory, if structured_layout is False, the directory contains unsorted files
    :param start_timestamp_utc_s: The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: The end timestamp as seconds since the epoch UTC.
    :param redvox_ids: An optional list of redvox_ids to filter against, default empty list
    :param structured_layout: An optional value to define if this is loading structured data, default False.
    :return: a list of Station objects that contain the data
    """
    # create the object to store the data
    stations: ReadResult = ReadResult({})
    # if structured_layout, there should be a specifically named folder in directory
    if structured_layout:
        if "api900" not in directory:
            api900_dir = os.path.join(directory, "api900")
        else:
            api900_dir = directory
        if "api1000" not in directory:
            apim_dir = os.path.join(directory, "api1000")
        else:
            apim_dir = directory
        if "mseed" not in directory:
            mseed_dir = os.path.join(directory, "mseed")
        else:
            mseed_dir = directory
        # check if none of the paths exists
        if not (os.path.exists(api900_dir) or os.path.exists(apim_dir) or os.path.exists(mseed_dir)):
            # no specially named directory found; raise error
            raise ValueError(f"{directory} does not contain api900, api1000 or mseed directory.")
    else:
        # load files from unstructured layout; everything is sitting in the main directory
        api900_dir = directory
        apim_dir = directory
        mseed_dir = directory

    # get api900 data
    stations.append(load_file_range_from_api900(api900_dir, start_timestamp_utc_s, end_timestamp_utc_s,
                                                redvox_ids, structured_layout, False))
    # get api1000 data
    stations.append(load_from_file_range_api_m(apim_dir, start_timestamp_utc_s, end_timestamp_utc_s,
                                               redvox_ids, structured_layout))
    # get mseed data
    all_paths = glob.glob(os.path.join(mseed_dir, "*.mseed"))
    for path in all_paths:
        stations.append(load_from_mseed(path, redvox_ids))
    return stations
