"""
This module loads or reads station data from various sources
"""
import os
import glob
import numpy as np
import pandas as pd

from obspy import read
from typing import List, Dict, Optional
from dataclasses import dataclass

from redvox.api1000 import io as apim_io
from redvox.api900 import reader as api900_io
from redvox.common import file_statistics as fs, date_time_utils as dtu, timesync as ts
from redvox.common.sensor_data import SensorType, SensorData
from redvox.common.station import Station
from redvox.common.station_utils import DataPacket, StationTiming, StationLocation, StationMetadata, LocationData, \
    TimeSyncData
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
from redvox.api1000.wrapped_redvox_packet.station_information import NetworkType
from redvox.api1000.wrapped_redvox_packet.sensors import xyz, single
from redvox.api1000.wrapped_redvox_packet import wrapped_packet as apim_wp


@dataclass
class StationSummary:
    """
    Contains a summary of each stations' data reader results.
    properties:
        station_id: str, station id
        station_uuid: str, station uuid
        os: str, station os
        os_version: str, station os version
        app_version: str, station app version
        audio_sampling_rate_hz: float, sample rate in hz
        total_duration_s: float, duration of data in seconds
        start_dt: dtu.datetime object, start datetime of data read
        end_dt: dtu.datetime object, end datetime of data read
    """
    station_id: str
    station_uuid: str
    os: str
    os_version: str
    app_version: str
    audio_sampling_rate_hz: float
    total_duration_s: float
    start_dt: dtu.datetime
    end_dt: dtu.datetime

    @staticmethod
    def from_station(station: Station) -> 'StationSummary':
        """
        :param station: the station to make a summary for
        :return: the station summary of a single station
        """
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
            audio.sample_rate if audio is not None else np.nan,
            total_duration,
            start_dt,
            end_dt
        )


class ReadResult:
    """
    Stores station information after being read from files
    Properties:
        station_id_uuid_to_stations: dict of string to Station object, where the string is id:uuid format
        __station_id_to_id_uuid: dict of string to string, maps id to uuid
        __station_summaries: dict of string to StationSummary object, maps id to StationSummary
    """
    def __init__(self,
                 station_id_uuid_to_stations: Dict[str, Station]):
        # result_stations: List[Station] = None):
        """
        :param station_id_uuid_to_stations: station_id:station_uuid -> station information
        """
        # station_keys: List[StationKey] = []
        # self.station_keys_to_stations: Dict[StationKey, Station]
        # for station in result_stations:
        #     station_keys.append(station.station_key)
        #     self.station_keys_to_stations[station.station_key] = station
        # todo: add mach time zero as another key
        self.station_id_uuid_to_stations: Dict[str, Station] = station_id_uuid_to_stations
        self.__station_id_to_id_uuid: Dict[str, str] = {}
        self.__station_summaries: Dict[str, StationSummary] = {}

        self._update_metadata()

    # def search_stations(self, id_or_uuid: str, start_time_micros: float = np.inf) -> Station:
    #     """
    #     Searches the stations in the ReadResult for the first one that matches the exact id or uuid given,
    #         with starting time on or before the time given
    #     :param id_or_uuid: str, the id or uuid of the station to search for
    #     :param start_time_micros: float, the start time of the station to search for, default np.inf
    #     :return: Station object that has the id or uuid and was started on or before the time given
    #     """
    #
    # def get_stations_by_id(self, id_or_uuid: str) -> List[Station]:
    #     pass
    #     return False
    #
    # def get_stations_by_start_time(self, start_time_micros: float) -> List[Station]:
    #     pass
    #     return False

    def _update_metadata(self):
        """
        updates ids:uuids pairs and summary information
        """
        for id_uuid, station in self.station_id_uuid_to_stations.items():
            s: List[str] = id_uuid.split(":")
            self.__station_id_to_id_uuid[s[0]] = s[1]
            self.__station_summaries[s[0]] = StationSummary.from_station(station)

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

    def __get_station_id(self, string_id: str) -> str:
        """
        given an id, uuid, or id:uuid, return id
        :param string_id: string, the id to examine
        :return: the station id corresponding to the input or an empty string if it doesn't exist
        """
        if self.check_for_id(string_id):
            if string_id in self.station_id_uuid_to_stations.keys():
                s: List[str] = string_id.split(":")
                return s[0]
            elif string_id in self.__station_id_to_id_uuid.values():
                return self.__get_station_id_by_uuid(string_id)
            elif string_id in self.__station_id_to_id_uuid.keys():
                return string_id
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
        elif station_id in self.__station_id_to_id_uuid.values():
            station_id = self.__get_station_id_by_uuid(station_id)
        if self.check_for_id(station_id):  # the station_id has been converted into id from id:uuid or uuid
            self.station_id_uuid_to_stations.pop(f"{station_id}:{self.__station_id_to_id_uuid[station_id]}")
            self.__station_id_to_id_uuid.pop(station_id)
            self.__station_summaries.pop(station_id)
        else:
            print(f"ReadResult cannot remove station {station_id} because it does not exist")
        return self

    def check_for_id(self, check_id: str) -> bool:
        """
        Look at keys and shortened keys in for the check_id; must be one of id, id:uuid, or uuid
        :param check_id: id to look for
        :return: True if check_id is in the ReadResult
        """
        return check_id in self.__station_id_to_id_uuid.keys() or \
            check_id in self.__station_id_to_id_uuid.values() or check_id in self.station_id_uuid_to_stations.keys()

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
        :return: a list of all stations in the ReadResult
        """
        return list(self.station_id_uuid_to_stations.values())

    def get_all_station_ids(self) -> List[str]:
        """
        :return: a list of all station ids in the ReadResult
        """
        return list(self.__station_id_to_id_uuid.keys())

    def get_station_summary(self, station_id: str) -> Optional[StationSummary]:
        """
        Find the station summary identified by the station_id given; it can be id or id:uuid
        :return: A StationSummary in this ReadResult if it exists, None otherwise
        """
        if ":" in station_id:
            s: List[str] = station_id.split(":")
            return self.__station_summaries[s[0]]
        elif self.check_for_id(station_id):
            return self.__station_summaries[self.__get_station_id(station_id)]
        print(f"WARNING: ReadResult attempted to read station id: {station_id}, but could not find id in results")
        return None

    def get_station_summaries(self) -> List[StationSummary]:
        """
        :return: A list of StationSummaries contained in this ReadResult
        """
        return list(self.__station_summaries.values())

    def append_station(self, new_station_id: str, new_station: Station):
        """
        adds a station to the ReadResult.  Appends data to existing stations
        :param new_station_id: id of station to add
        :param new_station: Station object to add
        """
        if self.check_for_id(new_station_id):
            self.station_id_uuid_to_stations[new_station_id].append_station(new_station)
        else:
            self.station_id_uuid_to_stations[new_station_id] = new_station
            self.__station_id_to_id_uuid[new_station.station_metadata.station_id] = \
                new_station.station_metadata.station_uuid
            self.__station_summaries[new_station.station_metadata.station_id] = \
                (StationSummary.from_station(new_station))

    def append(self, new_stations: 'ReadResult'):
        """
        adds stations from another ReadResult to the calling ReadResult
        :param new_stations: ReadResult object with stations to add
        """
        for new_station_id, new_station in new_stations.station_id_uuid_to_stations.items():
            self.append_station(new_station_id, new_station)


def calc_evenly_sampled_timestamps(start: float, samples: int, rate_hz: float) -> np.array:
    """
    given a start time, calculates samples amount of evenly spaced timestamps at rate_hz
    :param start: float, start timestamp in microseconds
    :param samples: int, number of samples
    :param rate_hz: float, sample rate in hz
    :return: np.array with evenly spaced timestamps starting at start
    """
    return start + dtu.seconds_to_microseconds(np.arange(0, samples) / rate_hz)


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
        sample_interval_std = dtu.microseconds_to_seconds(float(np.std(np.diff(timestamps))))
    else:
        sample_interval = np.nan
        sample_interval_std = np.nan
    if type(sensor) in [api900_io.AccelerometerSensor, api900_io.MagnetometerSensor, api900_io.GyroscopeSensor]:
        data_for_df = np.transpose([timestamps,
                                    sensor.payload_values_x(), sensor.payload_values_y(), sensor.payload_values_z()])
        columns = ["timestamps", f"{column_id}_x", f"{column_id}_y", f"{column_id}_z"]
    else:
        data_for_df = np.transpose([timestamps, sensor.payload_values()])
        columns = ["timestamps", column_id]
    return SensorData(sensor.sensor_name(), pd.DataFrame(data_for_df, columns=columns), 1 / sample_interval,
                      sample_interval, sample_interval_std, False)


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
                                                 sample_rate_hz, 1 / sample_rate_hz, 0.0, True)
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
            sample_interval_std = dtu.microseconds_to_seconds(float(np.std(np.diff(timestamps))))
        else:
            sample_interval = np.nan
            sample_interval_std = np.nan
        if wrapped_packet.location_sensor().check_for_preset_lat_lon():
            lat_lon = wrapped_packet.location_sensor().get_payload_lat_lon()
            data_for_df = np.array([[timestamps[0], lat_lon[0], lat_lon[1], np.nan, np.nan, np.nan, np.nan,
                                     LocationProvider.USER, np.nan, np.nan, np.nan, np.nan]])
        else:
            if wrapped_packet.location_sensor().sensor_name().lower() == "network":
                provider = LocationProvider.NETWORK
            elif wrapped_packet.location_sensor().sensor_name().lower() == "gps":
                provider = LocationProvider.GPS
            else:
                provider = LocationProvider.UNKNOWN
            data_for_df = np.transpose([timestamps,
                                        wrapped_packet.location_sensor().payload_values_latitude(),
                                        wrapped_packet.location_sensor().payload_values_longitude(),
                                        wrapped_packet.location_sensor().payload_values_altitude(),
                                        wrapped_packet.location_sensor().payload_values_speed(),
                                        wrapped_packet.location_sensor().payload_values_accuracy(),
                                        np.full(len(timestamps), provider),
                                        np.full(len(timestamps), np.nan), np.full(len(timestamps), np.nan),
                                        np.full(len(timestamps), np.nan), np.full(len(timestamps), np.nan)])
        columns = ["timestamps", "latitude", "longitude", "altitude", "speed", "horizontal_accuracy",
                   "location_provider", "bearing", "vertical_accuracy", "speed_accuracy", "bearing_accuracy"]
        data_dict[SensorType.LOCATION] = SensorData(wrapped_packet.location_sensor().sensor_name(),
                                                    pd.DataFrame(data_for_df, columns=columns),
                                                    1 / sample_interval, sample_interval, sample_interval_std, False)
    packet_duration_s = wrapped_packet.duration_s()
    if wrapped_packet.has_time_synchronization_sensor():
        network_type = NetworkType.UNKNOWN_NETWORK
    else:
        network_type = NetworkType.NO_NETWORK
    data_dict[SensorType.STATION_HEALTH] = SensorData("station health",
                                                      pd.DataFrame([[wrapped_packet.start_timestamp_us_utc(),
                                                                     wrapped_packet.battery_level_percent(),
                                                                     wrapped_packet.device_temperature_c(),
                                                                     network_type]],
                                                                   columns=["timestamps", "battery_charge_remaining",
                                                                            "internal_temp_c", "network_type"]),
                                                      1/packet_duration_s, packet_duration_s, 0, False)
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
                           api900_packet.microphone_sensor().first_sample_timestamp_epoch_microseconds_utc(),
                           start_timestamp_utc_s, end_timestamp_utc_s,
                           np.nan if api900_packet.best_latency() is None else api900_packet.best_latency(),
                           0.0 if api900_packet.best_offset() is None else api900_packet.best_offset())
    metadata = StationMetadata(api900_packet.redvox_id(), api900_packet.device_make(),
                               api900_packet.device_model(), False, api900_packet.device_os(),
                               api900_packet.device_os_version(), "Redvox", api900_packet.app_version(),
                               api900_packet.is_scrambled(), timing, station_uuid=api900_packet.uuid())
    data_dict = read_api900_wrapped_packet(api900_packet)
    timesync_data = TimeSyncData(api900_packet.time_synchronization_sensor().payload_values(),
                                 np.nan if api900_packet.best_latency() is None else api900_packet.best_latency(),
                                 0.0 if api900_packet.best_offset() is None else api900_packet.best_offset())
    packet_data = DataPacket(api900_packet.server_timestamp_epoch_microseconds_utc(),
                             api900_packet.app_file_start_timestamp_machine(),
                             float(api900_packet.start_timestamp_us_utc()), api900_packet.end_timestamp_us_utc(),
                             len(api900_packet.microphone_sensor().payload_values()) /
                             api900_packet.microphone_sensor().sample_rate_hz(),
                             len(api900_packet.microphone_sensor().payload_values()), timesync_data)
    packet_list: List[DataPacket] = [packet_data]
    # get the best timing values for the station
    if timing.station_best_latency is None or np.isnan(timing.station_best_latency):
        ts_analysis = ts.TimeSyncData(packet_data, metadata)
        metadata.timing_data.station_best_latency = ts_analysis.best_latency
        metadata.timing_data.station_best_offset = ts_analysis.best_offset
        metadata.timing_data.station_mean_offset = ts_analysis.mean_offset
        metadata.timing_data.station_std_offset = ts_analysis.offset_std
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
                               wrapped_packets[0].microphone_sensor().first_sample_timestamp_epoch_microseconds_utc(),
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
                time_sync = np.array([])
            timesync_data = TimeSyncData(time_sync,
                                         np.nan if packet.best_latency() is None else packet.best_latency(),
                                         0.0 if packet.best_offset() is None else packet.best_offset())
            data_dict = read_api900_wrapped_packet(packet)
            new_station.append_station_data(data_dict)
            packet_data = DataPacket(packet.server_timestamp_epoch_microseconds_utc(),
                                     packet.app_file_start_timestamp_machine(),
                                     float(packet.start_timestamp_us_utc()), packet.end_timestamp_us_utc(),
                                     data_dict[SensorType.AUDIO].data_duration_s(),
                                     data_dict[SensorType.AUDIO].num_samples(),
                                     timesync_data)
            packet_list.append(packet_data)
        new_station.packet_data = packet_list

        if timing.station_best_latency is None or np.isnan(timing.station_best_latency):
            # get the best timing values for the station
            ts_analysis = ts.TimeSyncAnalysis(new_station)
            new_station.station_metadata.timing_data.station_best_latency = ts_analysis.get_best_latency()
            new_station.station_metadata.timing_data.station_best_offset = ts_analysis.get_best_offset()
            new_station.station_metadata.timing_data.station_mean_offset = ts_analysis.get_mean_offset()
            new_station.station_metadata.timing_data.station_std_offset = ts_analysis.get_offset_stdev()

        # create the Station data object
        all_stations.append_station(redvox_id, new_station)

    return all_stations


def read_apim_xyz_sensor(sensor: xyz.Xyz, column_id: str) -> SensorData:
    """
    read a sensor that has xyz data channels from an api M data packet
    raises Attribute Error if sensor does not contain xyz channels
    :param sensor: the xyz api M sensor to read
    :param column_id: string, used to name the columns
    :return: generic SensorData representation of the xyz channel sensor
    """
    timestamps = sensor.get_timestamps().get_timestamps()
    if len(timestamps) > 1:
        sample_interval = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
        sample_interval_std = dtu.microseconds_to_seconds(float(np.std(np.diff(timestamps))))
    else:
        sample_interval = np.nan
        sample_interval_std = np.nan
    try:
        data_for_df = np.transpose([timestamps,
                                    sensor.get_x_samples().get_values(),
                                    sensor.get_y_samples().get_values(),
                                    sensor.get_z_samples().get_values()])
        columns = ["timestamps", f"{column_id}_x", f"{column_id}_y", f"{column_id}_z"]
        return SensorData(sensor.get_sensor_description(), pd.DataFrame(data_for_df, columns=columns),
                          1 / sample_interval, sample_interval, sample_interval_std, False)
    except AttributeError:
        raise


def read_apim_single_sensor(sensor: single.Single, column_id: str) -> SensorData:
    """
    read a sensor that has a single data channel from an api M data packet
    raises Attribute Error if sensor does not contain exactly one
    :param sensor: the single channel api M sensor to read
    :param column_id: string, used to name the columns
    :return: generic SensorData representation of the single channel sensor
    """
    timestamps = sensor.get_timestamps().get_timestamps()
    if len(timestamps) > 1:
        sample_interval = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
        sample_interval_std = dtu.microseconds_to_seconds(float(np.std(np.diff(timestamps))))
    else:
        sample_interval = np.nan
        sample_interval_std = np.nan
    try:
        data_for_df = np.transpose([timestamps, sensor.get_samples().get_values()])
        columns = ["timestamps", column_id]
        return SensorData(sensor.get_sensor_description(), pd.DataFrame(data_for_df, columns=columns),
                          1 / sample_interval, sample_interval, sample_interval_std, False)
    except AttributeError:
        raise


def load_apim_wrapped_packet(wrapped_packet: apim_wp.WrappedRedvoxPacketM) -> Dict[SensorType, SensorData]:
    """
    reads the data from a wrapped api M redvox packet into a dictionary of generic data
    :param wrapped_packet: a wrapped api M redvox packet
    :return: a dictionary containing all the sensor data
    """
    data_dict: Dict[SensorType, SensorData] = {}
    sensors = wrapped_packet.get_sensors()
    # there are 17 api M sensors
    if sensors.has_audio() and sensors.validate_audio():
        sample_rate_hz = sensors.get_audio().get_sample_rate()
        data_for_df = sensors.get_audio().get_samples().get_values()
        timestamps = calc_evenly_sampled_timestamps(sensors.get_audio().get_first_sample_timestamp(),
                                                    len(data_for_df), sample_rate_hz)
        data_dict[SensorType.AUDIO] = SensorData(sensors.get_audio().get_sensor_description(),
                                                 pd.DataFrame(np.transpose([timestamps, data_for_df]),
                                                              columns=["timestamps", "microphone"]),
                                                 sample_rate_hz, 1 / sample_rate_hz, 0.0, True)
    if sensors.has_compress_audio() and sensors.validate_compressed_audio():
        sample_rate_hz = sensors.get_compressed_audio().get_sample_rate()
        data_for_df = sensors.get_compressed_audio().get_samples().get_values()
        timestamps = calc_evenly_sampled_timestamps(sensors.get_compressed_audio().get_first_sample_timestamp(),
                                                    len(data_for_df), sample_rate_hz)
        data_dict[SensorType.COMPRESSED_AUDIO] = SensorData(sensors.get_compressed_audio().get_sensor_description(),
                                                            pd.DataFrame(np.transpose([timestamps, data_for_df]),
                                                                         columns=["compressed_audio"]),
                                                            sample_rate_hz, 1 / sample_rate_hz, 0.0, True)
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
            sample_interval_std = dtu.microseconds_to_seconds(float(np.std(np.diff(timestamps))))
        else:
            sample_interval = np.nan
            sample_interval_std = np.nan
        codecs = np.full(len(timestamps), sensors.get_image().get_image_codec().value)
        data_for_df = np.transpose([timestamps, sensors.get_image().get_samples(), codecs])
        data_dict[SensorType.IMAGE] = SensorData(sensors.get_image().get_sensor_description(),
                                                 pd.DataFrame(data_for_df,
                                                              columns=["timestamps", "image", "image_codec"]),
                                                 1 / sample_interval, sample_interval, sample_interval_std, False)
    if sensors.has_location() and sensors.validate_location():
        if sensors.get_location().is_only_best_values():
            sample_interval = np.nan
            sample_interval_std = np.nan
            if sensors.get_location().get_last_best_location():
                best_loc = sensors.get_location().get_last_best_location()
            else:
                best_loc = sensors.get_location().get_overall_best_location()
            data_for_df = [[best_loc.get_latitude_longitude_timestamp().get_mach(),
                            best_loc.get_latitude(),
                            best_loc.get_longitude(),
                            best_loc.get_altitude(),
                            best_loc.get_speed(),
                            best_loc.get_bearing(),
                            best_loc.get_horizontal_accuracy(),
                            best_loc.get_vertical_accuracy(),
                            best_loc.get_speed_accuracy(),
                            best_loc.get_bearing_accuracy(),
                            best_loc.get_location_provider()]]
        else:
            timestamps = sensors.get_location().get_timestamps().get_timestamps()
            if len(timestamps) > 1:
                sample_interval = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
                sample_interval_std = dtu.microseconds_to_seconds(float(np.std(np.diff(timestamps))))
            else:
                sample_interval = np.nan
                sample_interval_std = np.nan
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
        columns = ["timestamps", "latitude", "longitude", "altitude", "speed", "bearing",
                   "horizontal_accuracy", "vertical_accuracy", "speed_accuracy", "bearing_accuracy",
                   "location_provider"]
        data_dict[SensorType.LOCATION] = SensorData(sensors.get_location().get_sensor_description(),
                                                    pd.DataFrame(data_for_df, columns=columns),
                                                    1 / sample_interval, sample_interval,
                                                    sample_interval_std, False)
    station_metrics = wrapped_packet.get_station_information().get_station_metrics()
    timestamps = station_metrics.get_timestamps().get_timestamps()
    if len(timestamps) > 0:
        if len(timestamps) > 1:
            sample_interval = dtu.microseconds_to_seconds(float(np.mean(np.diff(timestamps))))
            sample_interval_std = dtu.microseconds_to_seconds(float(np.std(np.diff(timestamps))))
        else:
            sample_interval = np.nan
            sample_interval_std = np.nan
        data_dict[SensorType.STATION_HEALTH] = \
            SensorData("station health",
                       pd.DataFrame(np.transpose([timestamps,
                                                  station_metrics.get_battery().get_values(),
                                                  station_metrics.get_battery_current().get_values(),
                                                  station_metrics.get_temperature().get_values(),
                                                  station_metrics.get_network_type().get_values(),
                                                  station_metrics.get_network_strength().get_values(),
                                                  station_metrics.get_power_state().get_values(),
                                                  station_metrics.get_available_ram().get_values(),
                                                  station_metrics.get_available_disk().get_values(),
                                                  station_metrics.get_cell_service_state().get_values()
                                                  ]),
                                    columns=["timestamps", "battery_charge_remaining", "battery_current_strength",
                                             "internal_temp_c", "network_type", "network_strength",
                                             "power_state", "avail_ram", "avail_disk", "cell_service"]),
                       1 / sample_interval, sample_interval_std, 0, False)
    return data_dict


def load_station_from_apim_file(directory: str, start_timestamp_utc_s: Optional[int] = None,
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
    if read_packet.get_sensors().validate_location() and \
            read_packet.get_sensors().get_location().get_last_best_location():
        best_location = read_packet.get_sensors().get_location().get_last_best_location()
        location = StationLocation(best_location.get_latitude_longitude_timestamp().get_mach(),
                                   best_location.get_altitude_timestamp().get_mach(),
                                   best_location.get_speed_timestamp().get_mach(),
                                   best_location.get_bearing_timestamp().get_mach(),
                                   best_location.get_location_provider().name, best_location.get_score(),
                                   best_location.get_latitude(), best_location.get_longitude(),
                                   best_location.get_altitude(), best_location.get_speed(), best_location.get_bearing(),
                                   best_location.get_horizontal_accuracy(), best_location.get_vertical_accuracy(),
                                   best_location.get_speed_accuracy(), best_location.get_bearing_accuracy())
    else:
        location = None
    metadata = StationMetadata(read_packet.get_station_information().get_id(),
                               read_packet.get_station_information().get_make(),
                               read_packet.get_station_information().get_model(), False,
                               read_packet.get_station_information().get_os().name,
                               read_packet.get_station_information().get_os_version(), "Redvox",
                               read_packet.get_station_information().get_app_version(),
                               read_packet.get_station_information().get_app_settings().get_scramble_audio_data(),
                               timing, station_uuid=read_packet.get_station_information().get_uuid(),
                               location_data=LocationData(location, [location]))
    # add data from packets
    data_dict = load_apim_wrapped_packet(read_packet)
    timesync_data = TimeSyncData(np.array(read_packet.get_timing_information().get_synch_exchange_array()),
                                 np.nan if read_packet.get_timing_information().get_best_latency() is None else
                                 read_packet.get_timing_information().get_best_latency(),
                                 0.0 if read_packet.get_timing_information().get_best_offset() is None else
                                 read_packet.get_timing_information().get_best_offset())
    packet_data = DataPacket(read_packet.get_timing_information().get_server_acquisition_arrival_timestamp(),
                             read_packet.get_timing_information().get_app_start_mach_timestamp(),
                             read_packet.get_timing_information().get_packet_start_mach_timestamp(),
                             read_packet.get_timing_information().get_packet_end_mach_timestamp(),
                             data_dict[SensorType.AUDIO].data_duration_s(),
                             data_dict[SensorType.AUDIO].num_samples(), timesync_data)
    packet_list: List[DataPacket] = [packet_data]
    # get the best timing values for the station
    if timing.station_best_latency is None or np.isnan(timing.station_best_latency):
        ts_analysis = ts.TimeSyncData(packet_data, metadata)
        metadata.timing_data.station_best_latency = ts_analysis.best_latency
        metadata.timing_data.station_best_offset = ts_analysis.best_offset
        metadata.timing_data.station_mean_offset = ts_analysis.mean_offset
        metadata.timing_data.station_std_offset = ts_analysis.offset_std
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
            data_dict = load_apim_wrapped_packet(packet)
            new_station.append_station_data(data_dict)
            best_latency = packet.get_timing_information().get_best_latency()
            best_offset = packet.get_timing_information().get_best_offset()
            timesync_data = TimeSyncData(np.array(packet.get_timing_information().get_synch_exchange_array()),
                                         np.nan if best_latency is None else best_latency,
                                         0.0 if best_offset is None else best_offset)
            if packet.get_sensors().validate_location() and \
                    packet.get_sensors().get_location().get_last_best_location():
                best_location = packet.get_sensors().get_location().get_last_best_location()
                location = StationLocation(best_location.get_latitude_longitude_timestamp().get_mach(),
                                           best_location.get_altitude_timestamp().get_mach(),
                                           best_location.get_speed_timestamp().get_mach(),
                                           best_location.get_bearing_timestamp().get_mach(),
                                           best_location.get_location_provider().name, best_location.get_score(),
                                           best_location.get_latitude(), best_location.get_longitude(),
                                           best_location.get_altitude(), best_location.get_speed(),
                                           best_location.get_bearing(), best_location.get_horizontal_accuracy(),
                                           best_location.get_vertical_accuracy(), best_location.get_speed_accuracy(),
                                           best_location.get_bearing_accuracy())
            else:
                location = None
            packet_data = DataPacket(packet.get_timing_information().get_server_acquisition_arrival_timestamp(),
                                     packet.get_timing_information().get_app_start_mach_timestamp(),
                                     packet.get_timing_information().get_packet_start_mach_timestamp(),
                                     packet.get_timing_information().get_packet_end_mach_timestamp(),
                                     data_dict[SensorType.AUDIO].data_duration_s(),
                                     data_dict[SensorType.AUDIO].num_samples(),
                                     timesync_data, best_location=location)
            packet_list.append(packet_data)
        new_station.packet_data = packet_list

        if timing.station_best_latency is None or np.isnan(timing.station_best_latency):
            # get the best timing values for the station
            ts_analysis = ts.TimeSyncAnalysis(new_station)
            new_station.station_metadata.timing_data.station_best_latency = ts_analysis.get_best_latency()
            new_station.station_metadata.timing_data.station_best_offset = ts_analysis.get_best_offset()
            new_station.station_metadata.timing_data.station_mean_offset = ts_analysis.get_mean_offset()
            new_station.station_metadata.timing_data.station_std_offset = ts_analysis.get_offset_stdev()

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
                                 record_info["sampling_rate"], 1 / record_info["sampling_rate"], 0.0, True)
        data_packet = DataPacket(np.nan, start_time, start_time, end_time)
        if station_ids is None or len(station_ids) == 0 or station_id in station_ids:
            stations.append_station(f"{station_id}:{station_id}", Station(metadata, {SensorType.AUDIO: sensor_data},
                                                                          [data_packet]))
    return stations


def read_all_in_dir(directory: str,
                    start_timestamp_utc_s: Optional[int] = None,
                    end_timestamp_utc_s: Optional[int] = None,
                    station_ids: Optional[List[str]] = None,
                    structured_layout: bool = False) -> ReadResult:
    """
    load all data files in the directory
    :param directory: string, location of all the files;
                        if structured_layout is True, the directory contains a root api1000, api900, or mseed directory,
                        if structured_layout is False, the directory contains unsorted files
    :param start_timestamp_utc_s: optional int, The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: optional int, The end timestamp as seconds since the epoch UTC.
    :param station_ids: optional list of string station ids to filter against, default empty list
    :param structured_layout: optional bool to define if this is loading structured data, default False.
    :return: a ReadResult object containing the data requested
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
                                                station_ids, structured_layout, False))
    # get api1000 data
    stations.append(load_from_file_range_api_m(apim_dir, start_timestamp_utc_s, end_timestamp_utc_s,
                                               station_ids, structured_layout))
    # get mseed data
    all_paths = glob.glob(os.path.join(mseed_dir, "*.mseed"))
    for path in all_paths:
        stations.append(load_from_mseed(path, station_ids))
    return stations
