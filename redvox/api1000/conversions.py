# from typing import Dict, Optional
#
# import numpy as np
#
# import redvox.api900.sensors.accelerometer_sensor as api900_accelerometer_sensor
# import redvox.api900.sensors.barometer_sensor as api900_barometer_sensor
# import redvox.api900.sensors.gyroscope_sensor as api900_gyroscope_sensor
# import redvox.api900.sensors.infrared_sensor as api900_infrared_sensor
# import redvox.api900.sensors.light_sensor as api900_light_sensor
# import redvox.api900.sensors.location_sensor as api900_location_sensor
# import redvox.api900.sensors.magnetometer_sensor as api900_magnetometer_sensor
# import redvox.api900.sensors.microphone_sensor as api900_microphone_sensor
# import redvox.api900.sensors.time_synchronization_sensor as api900_time_synchronization_sensor
# import redvox.api900.wrapped_redvox_packet as api900_packet
#
# import redvox.api1000.common as common
# import redvox.api1000.location_channel as api1000_location_channel
# import redvox.api1000.microphone_channel as api1000_microphone_channel
# import redvox.api1000.wrapped_packet as api1000_packet
# import redvox.api1000.single_channel as api1000_single_channel
# import redvox.api1000.xyz_channel as api1000_xyz_channel
#
#
# def convert_device_os(device_os: str) -> api1000_packet.OsType:
#     return api1000_packet.OsType[device_os.upper()]
#
#
# def extract_app_start_ts_uh_mach(metadata_dict: Dict[str, str]) -> float:
#     if "machTimeZero" in metadata_dict:
#         return float(metadata_dict["machTimeZero"])
#
#     return common.NAN
#
#
# def extract_best_latency(metadata_dict: Dict[str, str]) -> float:
#     if "bestLatency" in metadata_dict:
#         return float(metadata_dict["bestLatency"])
#
#     return common.NAN
#
#
# def extract_best_offset(metadata_dict: Dict[str, str]) -> float:
#     if "bestOffset" in metadata_dict:
#         return float(metadata_dict["bestOffset"])
#
#     return common.NAN
#
#
# def extract_synch_params(
#         time_synchronization_sensor_api900: api900_time_synchronization_sensor.TimeSynchronizationSensor) -> np.ndarray:
#     if time_synchronization_sensor_api900 is not None:
#         return time_synchronization_sensor_api900.payload_values()
#
#     return common.EMPTY_ARRAY
#
#
# def compute_mic_duration_us(microphone_sensor_api900: api900_microphone_sensor.MicrophoneSensor) -> float:
#     duration_s: float = float(len(microphone_sensor_api900.payload_values())) / float(
#         microphone_sensor_api900.sample_rate_hz())
#
#     return duration_s * 1_000_000.0
#
# def convert_api900_to_api1000(
#         wrapped_redvox_packet_900: api900_packet.WrappedRedvoxPacket) -> api1000_packet.WrappedRedvoxPacketApi1000:
#     wrapped_redvox_packet_1000: api1000_packet.WrappedRedvoxPacketApi1000 = \
#         api1000_packet.WrappedRedvoxPacketApi1000.new()
#
#     # API
#     wrapped_redvox_packet_1000.set_api(1000)
#
#     # Device information
#     wrapped_redvox_packet_1000.set_auth_email(wrapped_redvox_packet_900.authenticated_email())
#     wrapped_redvox_packet_1000.set_auth_token(wrapped_redvox_packet_900.authentication_token())
#     wrapped_redvox_packet_1000.set_firebase_token(wrapped_redvox_packet_900.firebase_token())
#     wrapped_redvox_packet_1000.set_device_id(wrapped_redvox_packet_900.redvox_id())
#     wrapped_redvox_packet_1000.set_device_uuid(wrapped_redvox_packet_900.uuid())
#     wrapped_redvox_packet_1000.set_device_make(wrapped_redvox_packet_900.device_make())
#     wrapped_redvox_packet_1000.set_device_model(wrapped_redvox_packet_900.device_model())
#     wrapped_redvox_packet_1000.set_device_os(convert_device_os(wrapped_redvox_packet_900.device_os()))
#     wrapped_redvox_packet_1000.set_device_os_version(wrapped_redvox_packet_900.device_os_version())
#     wrapped_redvox_packet_1000.set_device_app_version(wrapped_redvox_packet_900.app_version())
#     wrapped_redvox_packet_1000.set_device_temp_c(wrapped_redvox_packet_900.device_temperature_c())
#     wrapped_redvox_packet_1000.set_device_battery_percent(wrapped_redvox_packet_900.battery_level_percent())
#     wrapped_redvox_packet_1000.set_network_type(api1000_packet.NetworkType.NONE)
#     wrapped_redvox_packet_1000.set_network_strength_db(common.NAN)
#
#     # Packet information
#     wrapped_redvox_packet_1000.set_is_backfilled(wrapped_redvox_packet_900.is_backfilled())
#     wrapped_redvox_packet_1000.set_is_private(wrapped_redvox_packet_900.is_private())
#     wrapped_redvox_packet_1000.set_is_mic_scrambled(wrapped_redvox_packet_900.is_scrambled())
#
#     # Server information
#     wrapped_redvox_packet_1000.set_auth_server_url(wrapped_redvox_packet_900.authentication_server())
#     wrapped_redvox_packet_1000.set_synch_server_url(wrapped_redvox_packet_900.time_synchronization_server())
#     wrapped_redvox_packet_1000.set_acquisition_server_url(wrapped_redvox_packet_900.acquisition_server())
#
#     # Timing
#     wrapped_redvox_packet_1000.set_packet_start_ts_us_wall(
#             float(wrapped_redvox_packet_900.app_file_start_timestamp_epoch_microseconds_utc()))
#     wrapped_redvox_packet_1000.set_packet_start_ts_us_mach(
#             float(wrapped_redvox_packet_900.app_file_start_timestamp_machine()))
#     mic_duration_us: float = compute_mic_duration_us(wrapped_redvox_packet_900.microphone_sensor())
#     wrapped_redvox_packet_1000.set_packet_end_ts_us_wall(wrapped_redvox_packet_1000.get_packet_start_ts_us_wall() + mic_duration_us)
#     wrapped_redvox_packet_1000.set_packet_end_ts_us_mach(wrapped_redvox_packet_1000.get_packet_start_ts_us_mach() + mic_duration_us)
#     wrapped_redvox_packet_1000.set_server_acquisition_arrival_ts_us(
#             wrapped_redvox_packet_900.server_timestamp_epoch_microseconds_utc())
#     wrapped_redvox_packet_1000.set_app_start_ts_us_mach(
#             extract_app_start_ts_uh_mach(wrapped_redvox_packet_900.metadata_as_dict()))
#     wrapped_redvox_packet_1000.set_synch_params(
#             extract_synch_params(wrapped_redvox_packet_900.time_synchronization_sensor()))
#     wrapped_redvox_packet_1000.set_best_latency_us(extract_best_latency(wrapped_redvox_packet_900.metadata_as_dict()))
#     wrapped_redvox_packet_1000.set_best_offset_us(extract_best_offset(wrapped_redvox_packet_900.metadata_as_dict()))
#
#     # Sensors->Channels
#     # Accelerometer
#     accelerometer_sensor_api900: Optional[
#         api900_accelerometer_sensor.AccelerometerSensor] = wrapped_redvox_packet_900.accelerometer_sensor()
#     if accelerometer_sensor_api900 is not None:
#         accelerometer_channel_api1000: api1000_xyz_channel.XyzChannel = api1000_xyz_channel.XyzChannel.new()
#         accelerometer_channel_api1000.set_sensor_description(accelerometer_sensor_api900.sensor_name())
#         accelerometer_channel_api1000.get_sample_ts_us().set_samples(
#                 accelerometer_sensor_api900.timestamps_microseconds_utc(), True)
#         accelerometer_channel_api1000.get_x_samples().set_samples(accelerometer_sensor_api900.payload_values_x(), True)
#         accelerometer_channel_api1000.get_y_samples().set_samples(accelerometer_sensor_api900.payload_values_y(), True)
#         accelerometer_channel_api1000.get_z_samples().set_samples(accelerometer_sensor_api900.payload_values_z(), True)
#         accelerometer_channel_api1000.get_metadata().set_metadata(accelerometer_sensor_api900.metadata_as_dict())
#         wrapped_redvox_packet_1000.set_accelerometer_channel(accelerometer_channel_api1000)
#
#     # Barometer
#     barometer_sensor_api900: Optional[
#         api900_barometer_sensor.BarometerSensor] = wrapped_redvox_packet_900.barometer_sensor()
#     if barometer_sensor_api900 is not None:
#         barometer_channel_api1000: api1000_single_channel.SingleChannel = api1000_single_channel.SingleChannel.new()
#         barometer_channel_api1000.set_sensor_description(barometer_sensor_api900.sensor_name())
#         barometer_channel_api1000.get_sample_ts_us().set_samples(barometer_sensor_api900.timestamps_microseconds_utc(),
#                                                                  True)
#         barometer_channel_api1000.get_samples().set_samples(barometer_sensor_api900.payload_values(), True)
#         barometer_channel_api1000.get_metadata().set_metadata(barometer_sensor_api900.metadata_as_dict())
#         wrapped_redvox_packet_1000.set_barometer_channel(barometer_channel_api1000)
#
#     # Gyroscope
#     gyroscope_sensor_api900: Optional[
#         api900_gyroscope_sensor.GyroscopeSensor] = wrapped_redvox_packet_900.gyroscope_sensor()
#     if gyroscope_sensor_api900 is not None:
#         gyroscope_channel_api1000: api1000_xyz_channel.XyzChannel = api1000_xyz_channel.XyzChannel.new()
#         gyroscope_channel_api1000.set_sensor_description(gyroscope_sensor_api900.sensor_name())
#         gyroscope_channel_api1000.get_sample_ts_us().set_samples(
#                 gyroscope_sensor_api900.timestamps_microseconds_utc(), True)
#         gyroscope_channel_api1000.get_x_samples().set_samples(gyroscope_sensor_api900.payload_values_x(), True)
#         gyroscope_channel_api1000.get_y_samples().set_samples(gyroscope_sensor_api900.payload_values_y(), True)
#         gyroscope_channel_api1000.get_z_samples().set_samples(gyroscope_sensor_api900.payload_values_z(), True)
#         gyroscope_channel_api1000.get_metadata().set_metadata(gyroscope_sensor_api900.metadata_as_dict())
#         wrapped_redvox_packet_1000.set_gyroscope_channel(gyroscope_channel_api1000)
#
#     # Infrared
#     infrared_sensor_api900: Optional[
#         api900_infrared_sensor.InfraredSensor] = wrapped_redvox_packet_900.infrared_sensor()
#     if infrared_sensor_api900 is not None:
#         infrared_channel_api1000: api1000_single_channel.SingleChannel = api1000_single_channel.SingleChannel.new()
#         infrared_channel_api1000.set_sensor_description(infrared_sensor_api900.sensor_name())
#         infrared_channel_api1000.get_sample_ts_us().set_samples(infrared_sensor_api900.timestamps_microseconds_utc(),
#                                                                 True)
#         infrared_channel_api1000.get_samples().set_samples(infrared_sensor_api900.payload_values(), True)
#         infrared_channel_api1000.get_metadata().set_metadata(infrared_sensor_api900.metadata_as_dict())
#         wrapped_redvox_packet_1000.set_infrared_channel(infrared_channel_api1000)
#
#     # Light
#     light_sensor_api900: Optional[api900_light_sensor.LightSensor] = wrapped_redvox_packet_900.light_sensor()
#     if light_sensor_api900 is not None:
#         light_channel_api1000: api1000_single_channel.SingleChannel = api1000_single_channel.SingleChannel.new()
#         light_channel_api1000.set_sensor_description(light_sensor_api900.sensor_name())
#         light_channel_api1000.get_sample_ts_us().set_samples(light_sensor_api900.timestamps_microseconds_utc(), True)
#         light_channel_api1000.get_samples().set_samples(light_sensor_api900.payload_values(), True)
#         light_channel_api1000.get_metadata().set_metadata(light_sensor_api900.metadata_as_dict())
#         wrapped_redvox_packet_1000.set_light_channel(light_channel_api1000)
#
#     # Location
#     location_sensor_api900: Optional[
#         api900_location_sensor.LocationSensor] = wrapped_redvox_packet_900.location_sensor()
#     if location_sensor_api900 is not None:
#         location_channel_api1000: api1000_location_channel.LocationChannel = \
#             api1000_location_channel.LocationChannel.new()
#         location_channel_api1000.set_sensor_description(location_sensor_api900.sensor_name())
#         location_channel_api1000.set_location_permissions_granted(False)
#         location_channel_api1000.set_location_services_enabled(False)
#         location_channel_api1000.set_location_services_requested(False)
#         location_channel_api1000.set_location_provider(api1000_location_channel.LocationProvider["NONE"])
#         location_channel_api1000.get_sample_ts_us().set_samples(location_sensor_api900.timestamps_microseconds_utc(),
#                                                                 True)
#         location_channel_api1000.get_latitude_samples().set_samples(location_sensor_api900.payload_values_latitude(),
#                                                                     True)
#         location_channel_api1000.get_longitude_samples().set_samples(location_sensor_api900.payload_values_longitude(),
#                                                                      True)
#         location_channel_api1000.get_altitude_samples().set_samples(location_sensor_api900.payload_values_altitude(),
#                                                                     True)
#         location_channel_api1000.get_speed_samples().set_samples(location_sensor_api900.payload_values_speed(), True)
#         location_channel_api1000.get_accuracy_samples().set_samples(location_sensor_api900.payload_values_accuracy(),
#                                                                     True)
#         location_channel_api1000.get_metadata().set_metadata(location_sensor_api900.metadata_as_dict())
#         wrapped_redvox_packet_1000.set_location_channel(location_channel_api1000)
#
#     # Magnetometer
#     magnetometer_sensor_api900: Optional[
#         api900_magnetometer_sensor.MagnetometerSensor] = wrapped_redvox_packet_900.magnetometer_sensor()
#     if magnetometer_sensor_api900 is not None:
#         magnetometer_channel_api1000: api1000_xyz_channel.XyzChannel = api1000_xyz_channel.XyzChannel.new()
#         magnetometer_channel_api1000.set_sensor_description(magnetometer_sensor_api900.sensor_name())
#         magnetometer_channel_api1000.get_sample_ts_us().set_samples(
#                 magnetometer_sensor_api900.timestamps_microseconds_utc(), True)
#         magnetometer_channel_api1000.get_x_samples().set_samples(magnetometer_sensor_api900.payload_values_x(), True)
#         magnetometer_channel_api1000.get_y_samples().set_samples(magnetometer_sensor_api900.payload_values_y(), True)
#         magnetometer_channel_api1000.get_z_samples().set_samples(magnetometer_sensor_api900.payload_values_z(), True)
#         magnetometer_channel_api1000.get_metadata().set_metadata(magnetometer_sensor_api900.metadata_as_dict())
#         wrapped_redvox_packet_1000.set_magnetometer_channel(magnetometer_channel_api1000)
#
#     # Microphone
#     microphone_sensor_api900: Optional[
#         api900_microphone_sensor.MicrophoneSensor] = wrapped_redvox_packet_900.microphone_sensor()
#     if microphone_sensor_api900 is not None:
#         microphone_channel_api1000: api1000_microphone_channel.MicrophoneChannel = \
#             api1000_microphone_channel.MicrophoneChannel.new()
#         microphone_channel_api1000.set_sensor_description(microphone_sensor_api900.sensor_name())
#         microphone_channel_api1000.set_first_sample_ts_us(
#                 microphone_sensor_api900.first_sample_timestamp_epoch_microseconds_utc())
#         microphone_channel_api1000.set_sample_rate_hz(microphone_sensor_api900.sample_rate_hz())
#         microphone_channel_api1000.get_samples().set_samples(microphone_sensor_api900.payload_values(), True)
#         microphone_channel_api1000.get_metadata().set_metadata(microphone_sensor_api900.metadata_as_dict())
#         wrapped_redvox_packet_1000.set_microphone_channel(microphone_channel_api1000)
#
#     # Metadata
#     wrapped_redvox_packet_1000.get_metadata().set_metadata(wrapped_redvox_packet_900.metadata_as_dict())
#
#     return wrapped_redvox_packet_1000
