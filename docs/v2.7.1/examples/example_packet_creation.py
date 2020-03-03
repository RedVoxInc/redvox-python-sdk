"""
This module shows how to create and set fields in WrappedRedvoxPackets.

Developer documentation: https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v.2.7.1/redvox-api900-docs.md
API documentation: https://redvoxhi.bitbucket.io/redvox-sdk/v.2.7.1/api_docs/redvox
"""

# First, let's import the reader.
from redvox.api900 import reader

# Example timestamps and payload for scalar sensors such as microphone, barometer, time_synchronization, light, and
# infrared
example_scalar_timestamps = [0, 5, 11, 15, 22, 27, 31]
example_scalar_payload = [-10, 0, 10, 20, 15, -6, 0]

# Example timestamps and payload for location sensor
example_location_timestamps = [1, 2, 3]
example_latitude_payload = [1, 2, 3]
example_longitude_payload = [4, 5, 6]
example_altitude_payload = [7, 8, 9]
example_speed_payload = [10, 11, 12]
example_accuracy_payload = [13, 14, 15]

# Example timestamps and payload for XYZ sensors such as accelerometer, magnetometer, and gyroscope
example_xyz_timestamps = [1, 2, 3]
example_x_payload = [1, 2, 3]
example_y_payload = [4, 5, 6]
example_z_payload = [7, 8, 9]

# The high level API provides setters and constructors for all metadata and sensor sensor. Below is an example of
# building a packet from scratch
example_packet = reader.WrappedRedvoxPacket()
example_packet.set_api(900)
example_packet.set_redvox_id("0000000001")
example_packet.set_uuid("123456789")
example_packet.set_authenticated_email("foo@bar.baz")
example_packet.set_authentication_token("redacted-000000")
example_packet.set_firebase_token("example_firebase_token")
example_packet.set_is_backfilled(False)
example_packet.set_is_private(True)
example_packet.set_is_scrambled(False)
example_packet.set_device_make("example_make")
example_packet.set_device_model("example_model")
example_packet.set_device_os("Android")
example_packet.set_device_os_version("8.0.0")
example_packet.set_app_version("2.4.2")
example_packet.set_battery_level_percent(77.5)
example_packet.set_device_temperature_c(21.1)
example_packet.set_acquisition_server("wss://redvox.io/acquisition/v900")
example_packet.set_time_synchronization_server("wss://redvox.io/synch/v2")
example_packet.set_authentication_server("https://redvox.io/login/mobile")
example_packet.set_app_file_start_timestamp_epoch_microseconds_utc(1552075743960135)
example_packet.set_app_file_start_timestamp_machine(1552075743960136)
example_packet.set_server_timestamp_epoch_microseconds_utc(1552075743960139)
example_packet.set_metadata_as_dict({"bar": "baz"})

microphone_sensor = reader.MicrophoneSensor()
microphone_sensor.set_sensor_name("example_mic")
microphone_sensor.set_sample_rate_hz(80.0)
microphone_sensor.set_first_sample_timestamp_epoch_microseconds_utc(1552075743960137)
microphone_sensor.set_metadata(["foo", "bar"])
microphone_sensor.set_payload_values(example_scalar_payload)
example_packet.set_microphone_sensor(microphone_sensor)

barometer_sensor = reader.BarometerSensor()
barometer_sensor.set_sensor_name("example_barometer")
barometer_sensor.set_timestamps_microseconds_utc(example_scalar_timestamps)
barometer_sensor.set_payload_values(example_scalar_payload)
example_packet.set_barometer_sensor(barometer_sensor)

location_sensor = reader.LocationSensor()
location_sensor.set_sensor_name("example_gps")
location_sensor.set_timestamps_microseconds_utc(example_location_timestamps)
location_sensor.set_payload_values(example_latitude_payload,
                                   example_longitude_payload,
                                   example_altitude_payload,
                                   example_speed_payload,
                                   example_accuracy_payload)
example_packet.set_location_sensor(location_sensor)

time_synchronization_sensor = reader.TimeSynchronizationSensor()
time_synchronization_sensor.set_payload_values(example_scalar_payload)
example_packet.set_time_synchronization_sensor(time_synchronization_sensor)

accelerometer_sensor = reader.AccelerometerSensor()
accelerometer_sensor.set_sensor_name("example_accelerometer")
accelerometer_sensor.set_timestamps_microseconds_utc(example_xyz_timestamps)
accelerometer_sensor.set_payload_values(example_x_payload,
                                        example_y_payload,
                                        example_z_payload)
example_packet.set_accelerometer_sensor(accelerometer_sensor)

magnetometer_sensor = reader.MagnetometerSensor()
magnetometer_sensor.set_sensor_name("example_magnetometer")
magnetometer_sensor.set_timestamps_microseconds_utc(example_xyz_timestamps)
magnetometer_sensor.set_payload_values(example_x_payload,
                                       example_y_payload,
                                       example_z_payload)
example_packet.set_magnetometer_sensor(magnetometer_sensor)

gyroscope_sensor = reader.GyroscopeSensor()
gyroscope_sensor.set_sensor_name("example_gyroscope")
gyroscope_sensor.set_timestamps_microseconds_utc(example_xyz_timestamps)
gyroscope_sensor.set_payload_values(example_x_payload,
                                    example_y_payload,
                                    example_z_payload)
example_packet.set_gyroscope_sensor(gyroscope_sensor)

light_sensor = reader.LightSensor()
light_sensor.set_sensor_name("example_light")
light_sensor.set_timestamps_microseconds_utc(example_scalar_timestamps)
light_sensor.set_payload_values(example_scalar_payload)
example_packet.set_light_sensor(light_sensor)

infrared_sensor = reader.InfraredSensor()
infrared_sensor.set_sensor_name("example_infrared")
infrared_sensor.set_timestamps_microseconds_utc(example_scalar_timestamps)
infrared_sensor.set_payload_values(example_scalar_payload)
infrared_sensor.set_metadata(["a", "b", "c", "d"])
example_packet.set_infrared_sensor(infrared_sensor)

# The high-level API also implements the builder pattern allowing packets to be modified and created in-place.
example_packet_2 = reader.WrappedRedvoxPacket() \
    .set_api(900) \
    .set_redvox_id("0000000001") \
    .set_uuid("123456789") \
    .set_authenticated_email("foo@bar.baz") \
    .set_authentication_token("redacted-000000") \
    .set_firebase_token("example_firebase_token") \
    .set_is_backfilled(False) \
    .set_is_private(True) \
    .set_is_scrambled(False) \
    .set_device_make("example_make") \
    .set_device_model("example_model") \
    .set_device_os("Android") \
    .set_device_os_version("8.0.0") \
    .set_app_version("2.4.2") \
    .set_battery_level_percent(77.5) \
    .set_device_temperature_c(21.1) \
    .set_acquisition_server("wss://redvox.io/acquisition/v900") \
    .set_time_synchronization_server("wss://redvox.io/synch/v2") \
    .set_authentication_server("https://redvox.io/login/mobile") \
    .set_app_file_start_timestamp_epoch_microseconds_utc(1552075743960135) \
    .set_app_file_start_timestamp_machine(1552075743960136) \
    .set_server_timestamp_epoch_microseconds_utc(1552075743960139) \
    .set_metadata_as_dict({"bar": "baz"}) \
    .set_microphone_sensor(reader.MicrophoneSensor()
                            .set_sensor_name("example_mic")
                            .set_sample_rate_hz(80.0)
                            .set_first_sample_timestamp_epoch_microseconds_utc(1552075743960137)
                            .set_metadata(["foo", "bar"])
                            .set_payload_values(example_scalar_payload)) \
    .set_barometer_sensor(reader.BarometerSensor()
                           .set_sensor_name("example_barometer")
                           .set_timestamps_microseconds_utc(example_scalar_timestamps)
                           .set_payload_values(example_scalar_payload)) \
    .set_location_sensor(reader.LocationSensor()
                          .set_sensor_name("example_gps")
                          .set_timestamps_microseconds_utc(example_location_timestamps)
                          .set_payload_values(example_latitude_payload,
                                              example_longitude_payload,
                                              example_altitude_payload,
                                              example_speed_payload,
                                              example_accuracy_payload)) \
    .set_time_synchronization_sensor(reader.TimeSynchronizationSensor()
                                      .set_payload_values(example_scalar_payload)) \
    .set_accelerometer_sensor(reader.AccelerometerSensor()
                               .set_sensor_name("example_accelerometer")
                               .set_timestamps_microseconds_utc(example_xyz_timestamps)
                               .set_payload_values(example_x_payload,
                                                   example_y_payload,
                                                   example_z_payload)) \
    .set_magnetometer_sensor(reader.MagnetometerSensor().set_sensor_name("example_magnetometer")
                              .set_timestamps_microseconds_utc(example_xyz_timestamps)
                              .set_payload_values(example_x_payload,
                                                  example_y_payload,
                                                  example_z_payload)) \
    .set_gyroscope_sensor(reader.GyroscopeSensor().set_sensor_name("example_gyroscope")
                           .set_timestamps_microseconds_utc(example_xyz_timestamps)
                           .set_payload_values(example_x_payload,
                                               example_y_payload,
                                               example_z_payload)) \
    .set_light_sensor(reader.LightSensor()
                       .set_sensor_name("example_light")
                       .set_timestamps_microseconds_utc(example_scalar_timestamps)
                       .set_payload_values(example_scalar_payload)) \
    .set_infrared_sensor(reader.InfraredSensor()
                          .set_sensor_name("example_infrared")
                          .set_timestamps_microseconds_utc(example_scalar_timestamps)
                          .set_payload_values(example_scalar_payload)
                          .set_metadata(["a", "b", "c", "d"]))

# To ensure that both these methods are equal, we can compare the redvox packets for equality
print(example_packet == example_packet_2)

# Now that we have a packet constructed, let's write it to disk as a compressed .rdvxz file.
example_packet.write_rdvxz(".")
