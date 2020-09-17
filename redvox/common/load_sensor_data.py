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
from redvox.common import file_statistics as fs
from redvox.common import date_time_utils as dtu
from redvox.common.sensor_data import SensorType, SensorData, Station, StationTiming, StationMetadata, DataPacket
from redvox.api1000.wrapped_redvox_packet.sensors import xyz, single
from redvox.api900.timesync.api900_timesync import sync_packet_time_900
from redvox.api1000.wrapped_redvox_packet import wrapped_packet as apim_wp


def calc_evenly_sampled_timestamps(start: float, samples: int, rate_hz: float) -> np.array:
    """
    given a start time, calculates samples amount of evenly spaced timestamps at rate_hz
    :param start: float, start timestamp
    :param samples: int, number of samples
    :param rate_hz: float, sample rate in hz
    :return: np.array with evenly spaced timestamps starting at start
    """
    return np.array(start + dtu.seconds_to_microseconds(np.arange(0, samples) / rate_hz))


def read_api900_non_mic_sensor(sensor: api900_io.RedvoxSensor, packet_length_s: float, column_id: str) -> SensorData:
    """
    read a sensor that does not have mic data from an api900 data packet
    :param sensor: the non-mic api900 sensor to read
    :param packet_length_s: float, the length of the data packet in seconds
    :param column_id: string, used to name the columns
    :return: generic SensorData object
    """
    timestamps = sensor.timestamps_microseconds_utc()
    if type(sensor) in [api900_io.AccelerometerSensor, api900_io.MagnetometerSensor, api900_io.GyroscopeSensor]:
        data_for_df = np.transpose([sensor.payload_values_x(), sensor.payload_values_y(), sensor.payload_values_z()])
        columns = [f"{column_id}_x", f"{column_id}_y", f"{column_id}_z"]
    else:
        data_for_df = np.transpose(sensor.payload_values())
        columns = [column_id]
    return SensorData(sensor.sensor_name(), pd.DataFrame(data_for_df, index=timestamps, columns=columns),
                      len(timestamps) / packet_length_s, False)


def read_api900_wrapped_packet(wrapped_packet: api900_io.WrappedRedvoxPacket) -> Dict[SensorType, SensorData]:
    """
    reads the data from a wrapped api900 redvox packet into a dictionary of generic data
    :param wrapped_packet: a wrapped api900 redvox packet
    :return: a dictionary containing all the sensor data
    """
    packet_length_s: float = wrapped_packet.duration_s()
    data_dict: Dict[SensorType, SensorData] = {}
    # there are 9 api900 sensors
    if wrapped_packet.has_microphone_sensor():
        sample_rate_hz = wrapped_packet.microphone_sensor().sample_rate_hz()
        data_for_df = wrapped_packet.microphone_sensor().payload_values().astype(float)
        timestamps = calc_evenly_sampled_timestamps(
            wrapped_packet.microphone_sensor().first_sample_timestamp_epoch_microseconds_utc(),
            fs.get_num_points_from_sample_rate(sample_rate_hz), sample_rate_hz)
        data_dict[SensorType.AUDIO] = SensorData(wrapped_packet.microphone_sensor().sensor_name(),
                                                 pd.DataFrame(data_for_df, index=timestamps, columns=["microphone"]),
                                                 sample_rate_hz, True)
    if wrapped_packet.has_accelerometer_sensor():
        data_dict[SensorType.ACCELEROMETER] = read_api900_non_mic_sensor(wrapped_packet.accelerometer_sensor(),
                                                                         packet_length_s, "accelerometer")
    if wrapped_packet.has_magnetometer_sensor():
        data_dict[SensorType.MAGNETOMETER] = read_api900_non_mic_sensor(wrapped_packet.magnetometer_sensor(),
                                                                        packet_length_s, "magnetometer")
    if wrapped_packet.has_gyroscope_sensor():
        data_dict[SensorType.GYROSCOPE] = read_api900_non_mic_sensor(wrapped_packet.gyroscope_sensor(),
                                                                     packet_length_s, "gyroscope")
    if wrapped_packet.has_barometer_sensor():
        data_dict[SensorType.PRESSURE] = read_api900_non_mic_sensor(wrapped_packet.barometer_sensor(),
                                                                    packet_length_s, "barometer")
    if wrapped_packet.has_light_sensor():
        data_dict[SensorType.LIGHT] = read_api900_non_mic_sensor(wrapped_packet.light_sensor(),
                                                                 packet_length_s, "light")
    if wrapped_packet.has_infrared_sensor():
        data_dict[SensorType.INFRARED] = read_api900_non_mic_sensor(wrapped_packet.infrared_sensor(),
                                                                    packet_length_s, "infrared")
    if wrapped_packet.has_image_sensor():
        data_dict[SensorType.IMAGE] = read_api900_non_mic_sensor(wrapped_packet.image_sensor(),
                                                                 packet_length_s, "image")
    if wrapped_packet.has_location_sensor():
        timestamps = wrapped_packet.location_sensor().timestamps_microseconds_utc()
        data_for_df = np.transpose([wrapped_packet.location_sensor().payload_values_latitude(),
                                    wrapped_packet.location_sensor().payload_values_longitude(),
                                    wrapped_packet.location_sensor().payload_values_altitude(),
                                    wrapped_packet.location_sensor().payload_values_speed(),
                                    wrapped_packet.location_sensor().payload_values_accuracy()])
        columns = ["latitude", "longitude", "altitude", "speed", "accuracy"]
        data_dict[SensorType.LOCATION] = SensorData(wrapped_packet.location_sensor().sensor_name(),
                                                    pd.DataFrame(data_for_df, index=timestamps, columns=columns),
                                                    len(timestamps) / packet_length_s, False)
    return data_dict


def load_station_from_api900(directory: str, start_timestamp_utc_s: Optional[int] = None,
                             end_timestamp_utc_s: Optional[int] = None) -> Station:
    """
    reads in station data from a single api900 file
    :param directory: string of the file to read from
    :param start_timestamp_utc_s: The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: The end timestamp as seconds since the epoch UTC.
    :return: a station Object
    """
    api900_packet = api900_io.read_rdvxz_file(directory)
    # set station metadata and timing based on first packet
    timing = StationTiming(api900_packet.mach_time_zero(), api900_packet.microphone_sensor().sample_rate_hz(),
                           api900_packet.app_file_start_timestamp_epoch_microseconds_utc(),
                           start_timestamp_utc_s, end_timestamp_utc_s,
                           api900_packet.best_latency(), api900_packet.best_offset())
    metadata = StationMetadata(api900_packet.redvox_id(), api900_packet.device_make(), api900_packet.device_model(),
                               api900_packet.device_os(), api900_packet.device_os_version(),
                               "Redvox", api900_packet.app_version(), api900_packet.is_scrambled(), timing)
    data_dict = read_api900_wrapped_packet(api900_packet)
    packet_data = DataPacket(api900_packet.server_timestamp_epoch_microseconds_utc(),
                             api900_packet.app_file_start_timestamp_machine(),
                             api900_packet.start_timestamp_us_utc(), int(api900_packet.end_timestamp_us_utc()),
                             api900_packet.time_synchronization_sensor().payload_values(),
                             api900_packet.best_latency(), api900_packet.best_offset())
    packet_list: List[DataPacket] = [packet_data]
    return Station(metadata, data_dict, packet_list)


def load_file_range_from_api900(directory: str,
                                start_timestamp_utc_s: Optional[int] = None,
                                end_timestamp_utc_s: Optional[int] = None,
                                redvox_ids: Optional[List[str]] = None,
                                structured_layout: bool = False,
                                concat_continuous_segments: bool = True) -> List[Station]:
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
    all_stations: List[Station] = []
    all_data = api900_io.read_rdvxz_file_range(directory, start_timestamp_utc_s, end_timestamp_utc_s, redvox_ids,
                                               structured_layout, concat_continuous_segments)
    for redvox_id, wrapped_packets in all_data.items():
        # set station metadata and timing based on first packet
        timing = StationTiming(wrapped_packets[0].mach_time_zero(),
                               wrapped_packets[0].microphone_sensor().sample_rate_hz(),
                               wrapped_packets[0].app_file_start_timestamp_epoch_microseconds_utc(),
                               start_timestamp_utc_s, end_timestamp_utc_s,
                               wrapped_packets[0].best_latency(), wrapped_packets[0].best_offset())
        metadata = StationMetadata(redvox_id, wrapped_packets[0].device_make(), wrapped_packets[0].device_model(),
                                   wrapped_packets[0].device_os(), wrapped_packets[0].device_os_version(),
                                   "Redvox", wrapped_packets[0].app_version(), wrapped_packets[0].is_scrambled(),
                                   timing)
        # add data from packets
        new_station = Station(metadata)
        packet_list: List[DataPacket] = []
        for packet in wrapped_packets:
            if packet.has_time_synchronization_sensor():
                time_sync = packet.time_synchronization_sensor().payload_values()
            else:
                time_sync = None
            data_dict = read_api900_wrapped_packet(packet)
            for sensor_type, sensor_data in data_dict.items():
                new_station.append_sensor(sensor_type, sensor_data)
            packet_data = DataPacket(packet.server_timestamp_epoch_microseconds_utc(),
                                     packet.app_file_start_timestamp_machine(),
                                     data_dict[SensorType.AUDIO].num_samples(),
                                     data_dict[SensorType.AUDIO].data_duration_s(),
                                     packet.start_timestamp_us_utc(), packet.end_timestamp_us_utc(),
                                     time_sync, packet.best_latency(), packet.best_offset())
            packet_list.append(packet_data)
        new_station.packet_data = packet_list

        # create the Station data object
        all_stations.append(new_station)

    return all_stations


def read_apim_xyz_sensor(sensor: xyz.Xyz, packet_length_s: float, column_id: str) -> SensorData:
    """
    read a sensor that has xyz data channels from an api M data packet
    :param sensor: the xyz api M sensor to read
    :param packet_length_s: float, the length of the data packet in seconds
    :param column_id: string, used to name the columns
    :return: generic SensorData object
    """
    timestamps = sensor.get_timestamps().get_timestamps()
    data_for_df = np.transpose([sensor.get_x_samples().get_values(),
                                sensor.get_y_samples().get_values(),
                                sensor.get_z_samples().get_values()])
    columns = [f"{column_id}_x", f"{column_id}_y", f"{column_id}_z"]
    return SensorData(sensor.get_sensor_description(), pd.DataFrame(data_for_df, index=timestamps, columns=columns),
                      len(timestamps) / packet_length_s, False)


def read_apim_single_sensor(sensor: single.Single, packet_length_s: float, column_id: str) -> SensorData:
    """
    read a sensor that has a single data channel from an api M data packet
    :param sensor: the single channel api M sensor to read
    :param packet_length_s: float, the length of the data packet in seconds
    :param column_id: string, used to name the columns
    :return: generic SensorData object
    """
    timestamps = sensor.get_timestamps().get_timestamps()
    data_for_df = np.transpose([sensor.get_samples().get_values()])
    columns = [column_id]
    return SensorData(sensor.get_sensor_description(), pd.DataFrame(data_for_df, index=timestamps, columns=columns),
                      len(timestamps) / packet_length_s, False)


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
                                                 pd.DataFrame(data_for_df, index=timestamps, columns=["microphone"]),
                                                 sample_rate_hz, True)
        # if audio exists, use it to get the packet duration, otherwise calculate using the packets' timestamps
        packet_length_s: float = sensors.get_audio().get_duration_s()
    else:
        packet_length_s = \
            dtu.microseconds_to_seconds(wrapped_packet.get_timing_information().get_packet_end_mach_timestamp() -
                                        wrapped_packet.get_timing_information().get_packet_start_mach_timestamp())
    if sensors.has_compress_audio() and sensors.validate_compressed_audio():
        sample_rate_hz = sensors.get_compressed_audio().get_sample_rate()
        data_for_df = sensors.get_compressed_audio().get_samples().get_values()
        timestamps = calc_evenly_sampled_timestamps(sensors.get_compressed_audio().get_first_sample_timestamp(),
                                                    len(data_for_df), sample_rate_hz)
        data_dict[SensorType.COMPRESSED_AUDIO] = SensorData(sensors.get_compressed_audio().get_sensor_description(),
                                                            pd.DataFrame(data_for_df, index=timestamps,
                                                                         columns=["compressed_audio"]),
                                                            sample_rate_hz, True)
    if sensors.has_accelerometer() and sensors.validate_accelerometer():
        data_dict[SensorType.ACCELEROMETER] = read_apim_xyz_sensor(sensors.get_accelerometer(),
                                                                   packet_length_s, "accelerometer")
    if sensors.has_magnetometer() and sensors.validate_magnetometer():
        data_dict[SensorType.MAGNETOMETER] = read_apim_xyz_sensor(sensors.get_magnetometer(),
                                                                  packet_length_s, "magnetometer")
    if sensors.has_linear_acceleration() and sensors.validate_accelerometer():
        data_dict[SensorType.LINEAR_ACCELERATION] = read_apim_xyz_sensor(sensors.get_linear_acceleration(),
                                                                         packet_length_s, "linear_accel")
    if sensors.has_orientation() and sensors.validate_orientation():
        data_dict[SensorType.ORIENTATION] = read_apim_xyz_sensor(sensors.get_orientation(),
                                                                 packet_length_s, "orientation")
    if sensors.has_rotation_vector() and sensors.validate_rotation_vector():
        data_dict[SensorType.ROTATION_VECTOR] = read_apim_xyz_sensor(sensors.get_rotation_vector(),
                                                                     packet_length_s, "rotation_vector")
    if sensors.has_gyroscope() and sensors.validate_gyroscope():
        data_dict[SensorType.GYROSCOPE] = read_apim_xyz_sensor(sensors.get_gyroscope(), packet_length_s, "gyroscope")
    if sensors.has_gravity() and sensors.validate_gravity():
        data_dict[SensorType.GRAVITY] = read_apim_xyz_sensor(sensors.get_gravity(), packet_length_s, "gravity")
    if sensors.has_pressure() and sensors.validate_pressure():
        data_dict[SensorType.PRESSURE] = read_apim_single_sensor(sensors.get_pressure(), packet_length_s, "barometer")
    if sensors.has_light() and sensors.validate_light():
        data_dict[SensorType.LIGHT] = read_apim_single_sensor(sensors.get_light(), packet_length_s, "light")
    if sensors.has_proximity() and sensors.validate_proximity():
        data_dict[SensorType.PROXIMITY] = read_apim_single_sensor(sensors.get_proximity(), packet_length_s, "proximity")
    if sensors.has_ambient_temperature() and sensors.validate_ambient_temperature():
        data_dict[SensorType.TEMPERATURE] = read_apim_single_sensor(sensors.get_ambient_temperature(),
                                                                    packet_length_s, "ambient_temp")
    if sensors.has_relative_humidity() and sensors.validate_relative_humidity():
        data_dict[SensorType.RELATIVE_HUMIDITY] = read_apim_single_sensor(sensors.get_relative_humidity(),
                                                                          packet_length_s, "rel_humidity")
    if sensors.has_image() and sensors.validate_image():
        timestamps = sensors.get_image().get_timestamps().get_timestamps()
        data_for_df = sensors.get_image().get_samples()
        data_dict[SensorType.IMAGE] = SensorData(sensors.get_image().get_sensor_description(),
                                                 pd.DataFrame(data_for_df, index=timestamps, columns=["image"]),
                                                 len(timestamps) / packet_length_s, False)
    if sensors.has_location() and sensors.validate_location():
        timestamps = sensors.get_location().get_timestamps().get_timestamps()
        data_for_df = np.transpose([sensors.get_location().get_latitude_samples().get_values(),
                                    sensors.get_location().get_longitude_samples().get_values(),
                                    sensors.get_location().get_altitude_samples().get_values(),
                                    sensors.get_location().get_speed_samples().get_values(),
                                    sensors.get_location().get_bearing_samples().get_values(),
                                    sensors.get_location().get_horizontal_accuracy_samples().get_values(),
                                    sensors.get_location().get_vertical_accuracy_samples().get_values(),
                                    sensors.get_location().get_speed_samples().get_values(),
                                    sensors.get_location().get_bearing_accuracy_samples().get_values()])
        columns = ["latitude", "longitude", "altitude", "speed", "bearing",
                   "horizontal_accuracy", "vertical_accuracy", "speed_accuracy", "bearing_accuracy"]
        data_dict[SensorType.LOCATION] = SensorData(sensors.get_location().get_sensor_description(),
                                                    pd.DataFrame(data_for_df, index=timestamps, columns=columns),
                                                    len(timestamps) / packet_length_s, False)
    elif sensors.has_location() and sensors.get_location().get_last_best_location():
        timestamps = [sensors.get_location().get_last_best_location().get_latitude_longitude_timestamp().get_mach()]
        data_for_df = np.transpose([[sensors.get_location().get_last_best_location().get_latitude()],
                                    [sensors.get_location().get_last_best_location().get_longitude()],
                                    [sensors.get_location().get_last_best_location().get_altitude()],
                                    [sensors.get_location().get_last_best_location().get_speed()],
                                    [sensors.get_location().get_last_best_location().get_bearing()],
                                    [sensors.get_location().get_last_best_location().get_horizontal_accuracy()],
                                    [sensors.get_location().get_last_best_location().get_vertical_accuracy()],
                                    [sensors.get_location().get_last_best_location().get_speed_accuracy()],
                                    [sensors.get_location().get_last_best_location().get_bearing_accuracy()]])
        columns = ["latitude", "longitude", "altitude", "speed", "bearing",
                   "horizontal_accuracy", "vertical_accuracy", "speed_accuracy", "bearing_accuracy"]
        data_dict[SensorType.LOCATION] = SensorData(sensors.get_location().get_sensor_description(),
                                                    pd.DataFrame(data_for_df, index=timestamps, columns=columns),
                                                    len(timestamps) / packet_length_s, False)
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
                               read_packet.get_timing_information().get_best_latency(),
                               read_packet.get_timing_information().get_best_offset())
    else:
        raise ValueError("Station is missing Audio sensor!")
    metadata = StationMetadata(read_packet.get_station_information().get_id(),
                               read_packet.get_station_information().get_make(),
                               read_packet.get_station_information().get_model(),
                               read_packet.get_station_information().get_os().name,
                               read_packet.get_station_information().get_os_version(), "Redvox",
                               read_packet.get_station_information().get_app_version(),
                               read_packet.get_station_information().get_app_settings().get_scramble_audio_data(),
                               timing)
    # add data from packets
    time_sync = np.array(read_packet.get_timing_information().get_synch_exchanges().get_values())
    data_dict = load_apim_wrapped_packet(read_packet)
    packet_data = DataPacket(read_packet.get_timing_information().get_server_acquisition_arrival_timestamp(),
                             read_packet.get_timing_information().get_app_start_mach_timestamp(),
                             data_dict[SensorType.AUDIO].num_samples(),
                             data_dict[SensorType.AUDIO].data_duration_s(),
                             read_packet.get_timing_information().get_packet_start_mach_timestamp(),
                             read_packet.get_timing_information().get_packet_end_mach_timestamp(),
                             time_sync, read_packet.get_timing_information().get_best_latency(),
                             read_packet.get_timing_information().get_best_offset())
    packet_list: List[DataPacket] = [packet_data]
    return Station(metadata, data_dict, packet_list)


def load_from_file_range_api_m(directory: str,
                               start_timestamp_utc_s: Optional[int] = None,
                               end_timestamp_utc_s: Optional[int] = None,
                               redvox_ids: Optional[List[str]] = None,
                               structured_layout: bool = False) -> List[Station]:
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
    all_stations: List[Station] = []
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
                                       first_pack.get_timing_information().get_best_latency(),
                                       first_pack.get_timing_information().get_best_offset())
                station_info = first_pack.get_station_information()
                metadata = StationMetadata(read_packets.redvox_id, station_info.get_make(), station_info.get_model(),
                                           station_info.get_os().name, station_info.get_os_version(), "Redvox",
                                           station_info.get_app_version(),
                                           station_info.get_app_settings().get_scramble_audio_data(), timing)
            else:
                raise ValueError("Packet is missing Audio sensor!")
        else:
            raise ValueError("First Packet is missing!")
        new_station = Station(metadata)
        # add data from packets
        packet_list: List[DataPacket] = []
        for packet in read_packets.wrapped_packets:
            time_sync = np.array(packet.get_timing_information().get_synch_exchanges().get_values())
            data_dict = load_apim_wrapped_packet(packet)
            new_station.append_station_data(data_dict)
            packet_data = DataPacket(packet.get_timing_information().get_server_acquisition_arrival_timestamp(),
                                     packet.get_timing_information().get_app_start_mach_timestamp(),
                                     data_dict[SensorType.AUDIO].num_samples(),
                                     data_dict[SensorType.AUDIO].data_duration_s(),
                                     packet.get_timing_information().get_packet_start_mach_timestamp(),
                                     packet.get_timing_information().get_packet_end_mach_timestamp(),
                                     time_sync, packet.get_timing_information().get_best_latency(),
                                     packet.get_timing_information().get_best_offset())
            packet_list.append(packet_data)
        new_station.packet_data = packet_list

        # create the Station data object
        all_stations.append(new_station)
    return all_stations


def load_from_mseed(file_path: str) -> List[Station]:
    """
    load station data from a miniseed file
    :param file_path: the location of the miniseed file
    :return: a list of Station objects that contain the data
    """
    stations: List[Station] = []
    strm = read(file_path)
    for data_stream in strm:
        record_info = data_stream.meta
        start_time = int(dtu.seconds_to_microseconds(data_stream.meta["starttime"].timestamp))
        end_time = int(dtu.seconds_to_microseconds(data_stream.meta["endtime"].timestamp))
        station_timing = StationTiming(np.nan, record_info["sampling_rate"], start_time, start_time, end_time)
        metadata = StationMetadata(record_info["network"] + record_info["station"] + "_" + record_info["location"],
                                   "mb3_make", "mb3_model", "mb3_os", "mb3_os_vers", "mb3_recorder",
                                   "mb3_recorder_version", False, station_timing, record_info["calib"],
                                   record_info["network"], record_info["station"], record_info["location"],
                                   record_info["channel"], record_info["mseed"]["encoding"])
        sample_rate_hz = record_info["sampling_rate"]
        data_for_df = data_stream.data
        timestamps = calc_evenly_sampled_timestamps(start_time, int(record_info["npts"]), sample_rate_hz)
        sensor_data = SensorData(record_info["channel"], pd.DataFrame(data_for_df, index=timestamps, columns=["BDF"]),
                                 record_info["sampling_rate"], True)
        data_packet = DataPacket(np.nan, start_time, start_time, end_time)
        stations.append(Station(metadata, {SensorType.AUDIO: sensor_data}, [data_packet]))
    return stations


def read_all_in_dir(directory: str,
                    start_timestamp_utc_s: Optional[int] = None,
                    end_timestamp_utc_s: Optional[int] = None,
                    redvox_ids: Optional[List[str]] = None,
                    structured_layout: bool = False,
                    concat_continuous_segments: bool = True) -> List[Station]:
    """
    load all data files in the directory
    :param directory: location of all the files; if structured_layout is True, the directory contains a root api1000,
                        api900, or mseed directory, if structured_layout is False, the directory contains unsorted files
    :param start_timestamp_utc_s: The start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: The end timestamp as seconds since the epoch UTC.
    :param redvox_ids: An optional list of redvox_ids to filter against, default empty list
    :param structured_layout: An optional value to define if this is loading structured data, default False.
    :param concat_continuous_segments: An optional value to define if this function should concatenate rdvxz files
                                       into multiple continuous rdvxz files separated at gaps.  ONLY WORKS FOR API900
    :return: a list of Station objects that contain the data
    """
    # create the object to store the data
    stations: List[Station] = []
    # if structured_layout, there should be a specifically named folder in directory
    if structured_layout:
        api900_dir = os.path.join(directory, "api900")
        if os.path.exists(api900_dir):
            # get api900 data
            stations.extend(load_file_range_from_api900(api900_dir, start_timestamp_utc_s, end_timestamp_utc_s,
                                                        redvox_ids, True, concat_continuous_segments))
        apim_dir = os.path.join(directory, "api1000")
        if os.path.exists(apim_dir):
            # get api1000 data
            stations.extend(load_from_file_range_api_m(apim_dir, start_timestamp_utc_s, end_timestamp_utc_s,
                                                       redvox_ids, True))
        mseed_dir = os.path.join(directory, "mseed")
        if os.path.exists(mseed_dir):
            # get mseed data
            all_paths = glob.glob(os.path.join(mseed_dir, "*.mseed"))
            for path in all_paths:
                mseed_data = load_from_mseed(path)
                for mseed_station in mseed_data:
                    if mseed_station.station_metadata.station_id in redvox_ids:
                        stations.append(mseed_station)
        else:
            # structured layout requires api1000 or api900 directory
            raise ValueError(f"{directory} does not contain api900 or api1000 directory.")
    # load files from unstructured layout
    # get unstructured api 900 data
    stations.extend(load_file_range_from_api900(directory, start_timestamp_utc_s, end_timestamp_utc_s, redvox_ids,
                                                False, concat_continuous_segments))
    # get unstructured api m data
    stations.extend(load_from_file_range_api_m(directory, start_timestamp_utc_s, end_timestamp_utc_s,
                                               redvox_ids, False))
    # get miniseed data
    mseed_paths = glob.glob(os.path.join(directory, "*.mseed"))
    for path in mseed_paths:
        stations.extend(load_from_mseed(path))
    return stations


def read_data_window_api900(directory: str,
                            redvox_ids: Optional[List[str]] = None,
                            start_timestamp_utc_s: Optional[int] = None,
                            end_timestamp_utc_s: Optional[int] = None,
                            start_padding_s: int = 120,
                            end_padding_s: int = 120,
                            gap_time_s: float = 5,
                            apply_correction: bool = False,
                            structured_layout: bool = False) -> Dict[str, Station]:
    """
    read data from a specified window in the directory
    :param directory: the directory containing the files to read
    :param redvox_ids: the specific ids to search for, default None (gets all ids)
    :param start_timestamp_utc_s: start timestamp of window to search for in seconds since epoch utc,
                                    default None (gets all times)
    :param end_timestamp_utc_s: end timestamp of window to search for in seconds since epoch utc,
                                    default None (gets all times)
    :param start_padding_s: amount of seconds to include in search before start_timestamp_utc_s, default 120
    :param end_padding_s: amount of seconds to include in search after end_timestamp_utc_s, default 120
    :param gap_time_s: amount of seconds to consider as a gap, default 5
    :param apply_correction: if True, applies timing correction to the data before returning, default False
    :param structured_layout: if True, the input directory is specially structured for api900 data, default False
    :return: a dictionary of station id and Station information
    """
    data = api900_io.read_rdvxz_file_range(directory, start_timestamp_utc_s - start_padding_s,
                                           end_timestamp_utc_s + end_padding_s, redvox_ids,
                                           structured_layout, False)
    # create the object to store the data
    all_stations: Dict[str, Station] = {}

    # correct data, then convert to SensorData
    for redvox_id, wrapped_packets in data.items():
        # get the id
        short_id = wrapped_packets[0].redvox_id()
        # apply correction if needed
        if apply_correction:
            sync_packet_time_900(wrapped_packets)
        # prepare an empty dict to add data to
        metadata = StationMetadata(short_id, wrapped_packets[0].device_make(), wrapped_packets[0].device_model())
        result_station = Station(metadata)
        for packet in wrapped_packets:
            # read in the packets' data
            for sensor_type, sensor_data in read_api900_wrapped_packet(packet).items():
                if sensor_type in result_station.station_data.keys():
                    if sensor_type == SensorType.AUDIO:
                        # detect gap between last added timestamp and new data start timestamp
                        last_timestamp = result_station.station_data[SensorType.AUDIO].last_data_timestamp()
                        first_timestamp = sensor_data.first_data_timestamp()
                        time_diff: float = first_timestamp - last_timestamp
                        if time_diff > dtu.seconds_to_microseconds(gap_time_s):
                            missing_points = int(dtu.microseconds_to_seconds(time_diff) * sensor_data.sample_rate)
                            gap_times = np.vectorize(
                                lambda t: last_timestamp + dtu.seconds_to_microseconds(t / sensor_data.sample_rate))(
                                list(range(1, missing_points)))
                            empty_points = np.empty(missing_points - 1)
                            empty_points[:] = np.nan
                            empty_df = pd.DataFrame(empty_points, index=gap_times, columns=["microphone"])
                            result_station.station_data[SensorType.AUDIO].data_df = \
                                pd.concat([result_station.station_data[SensorType.AUDIO].data_df, empty_df])
                    result_station.station_data[sensor_type].data_df = \
                        pd.concat([result_station.station_data[sensor_type].data_df, sensor_data.data_df])
                else:
                    result_station.station_data[sensor_type] = sensor_data
        all_stations[short_id] = result_station

    # check if ids in station
    for ids in redvox_ids:
        if ids not in all_stations.keys():
            # error handling
            print(f"WARNING: {ids} doesn't have any data to read")

    # fill in gaps and truncate
    for station_id, station in all_stations.items():
        # prepare a bunch of information to be used later
        # compute the length in seconds of one sample
        one_sample_s = 1 / station.station_data[SensorType.AUDIO].sample_rate
        # get the start and end timestamps + 1 sample to be safe
        start_timestamp = int(dtu.seconds_to_microseconds(start_timestamp_utc_s - one_sample_s))
        end_timestamp = int(dtu.seconds_to_microseconds(end_timestamp_utc_s + one_sample_s))
        # TRUNCATE!  get only the timestamps between the start and end timestamps
        for sensor_types in station.station_data.keys():
            # get the timestamps of the data
            df_timestamps = station.station_data[sensor_types].data_df.index.to_numpy()
            temp = np.where(
                (start_timestamp < df_timestamps) & (df_timestamps < end_timestamp))[0]
            new_df = station.station_data[sensor_types].data_df.iloc[temp]
            station.station_data[sensor_types].data_df = new_df
        if len(station.station_data[SensorType.AUDIO].data_df.values) < 1:
            print(f"WARNING: {station.station_metadata.station_id} audio sensor has been truncated and "
                  f"no valid data remains!")
        else:
            # FRONT/END GAP FILL!  calculate the audio samples missing based on inputs
            new_df = station.station_data[SensorType.AUDIO].data_df
            first_timestamp = station.station_data[SensorType.AUDIO].first_data_timestamp()
            start_diff = first_timestamp - dtu.seconds_to_microseconds(start_timestamp_utc_s)
            if start_diff > 0:
                num_missing_samples = int(dtu.microseconds_to_seconds(start_diff) *
                                          station.station_data[SensorType.AUDIO].sample_rate)
                time_before = np.vectorize(
                    lambda t: first_timestamp - dtu.seconds_to_microseconds(t * one_sample_s))(
                    list(range(1, num_missing_samples)))
                time_before = time_before[::-1]
                data = np.empty(num_missing_samples - 1)
                data[:] = np.nan
                new_df_values = pd.DataFrame(data, index=time_before, columns=["microphone"])
                new_df = new_df_values.append(new_df)
            last_timestamp = station.station_data[SensorType.AUDIO].data_df.index[-1]
            last_diff = dtu.seconds_to_microseconds(end_timestamp_utc_s) - last_timestamp
            if last_diff > 0:
                num_missing_samples = int(dtu.microseconds_to_seconds(last_diff) *
                                          station.station_data[SensorType.AUDIO].sample_rate)
                time_after = np.vectorize(
                    lambda t: last_timestamp + dtu.seconds_to_microseconds(t * one_sample_s))(
                    list(range(1, num_missing_samples)))
                data = np.empty(num_missing_samples - 1)
                data[:] = np.nan
                new_df_values = pd.DataFrame(data, index=time_after, columns=["microphone"])
                new_df = new_df.append(new_df_values)
            # ALL DONE!  set the dataframe to the updated dataframe
            station.station_data[SensorType.AUDIO].data_df = new_df

    return all_stations
