"""
This example demonstrates how to read RedVox API 900 files from both disk and memory.

We now accept the original, compressed, binary-encoded .rdvxz files and the larger RedVox API 900 compliant .json files.

When files are read, they return a WrappedRedvoxPacket which provides both high level getters and setters for reading,
modifying, creating, and writing RedVox API 900 files.

Developer documentation: https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.9.2/redvox-api900-docs.md
API documentation: https://redvoxhi.bitbucket.io/redvox-sdk/v2.9.2/api_docs/redvox
"""

# First, we import the RedVox API 900 reader.
from redvox.api900 import reader

# Now, let's load both a .rdvxz file
wrapped_packet = reader.read_rdvxz_file("example_data/example.rdvxz")

# Now that the we have loaded the data into a wrapped_packet, let's look at all of the fields we can access.
# We'll start with top-level metadata.
print("api", wrapped_packet.api())
print("redvox_id", wrapped_packet.redvox_id())
print("uuid", wrapped_packet.uuid())
print("authenticated_email", wrapped_packet.authenticated_email())
print("authentication_token", wrapped_packet.authentication_token())
print("firebase_token", wrapped_packet.firebase_token())
print("is_backfilled", wrapped_packet.is_backfilled())
print("is_private", wrapped_packet.is_private())
print("is_scrambled", wrapped_packet.is_scrambled())
print("device_make", wrapped_packet.device_make())
print("device_model", wrapped_packet.device_model())
print("device_os", wrapped_packet.device_os())
print("device_os_version", wrapped_packet.device_os_version())
print("app_version", wrapped_packet.app_version())
print("battery_level_percent", wrapped_packet.battery_level_percent())
print("device_temperature_c", wrapped_packet.device_temperature_c())
print("acquisition_server", wrapped_packet.acquisition_server())
print("time_synchronization_server", wrapped_packet.time_synchronization_server())
print("authentication_server", wrapped_packet.authentication_server())
print("app_file_start_timestamp_epoch_microseconds_utc", wrapped_packet.app_file_start_timestamp_epoch_microseconds_utc())
print("app_file_start_timestamp_machine", wrapped_packet.app_file_start_timestamp_machine())
print("server_timestamp_epoch_microseconds_utc", wrapped_packet.server_timestamp_epoch_microseconds_utc())
print("metadata", wrapped_packet.metadata())
print("metadata_as_dict", wrapped_packet.metadata_as_dict())

# We can also print out the contents of the entire file
print(wrapped_packet)

# Next, we'll move onto the sensor sensors.
# Each sensor sensor has a "has_sensor" method which tests for the existence of a sensor and a "get_sensor" method
# which either returns the sensor sensor or "None" if the sensor DNE.

# MicrophoneSensor
if wrapped_packet.has_microphone_sensor():
    microphone_sensor = wrapped_packet.microphone_sensor()
    print("sample_rate_hz", microphone_sensor.sample_rate_hz())
    print("sensor_name", microphone_sensor.sensor_name())
    print("first_sample_timestamp_epoch_microseconds_utc", microphone_sensor.first_sample_timestamp_epoch_microseconds_utc())
    print("payload_type", microphone_sensor.payload_type())
    print("payload_values", microphone_sensor.payload_values())
    print("payload_mean", microphone_sensor.payload_mean())
    print("payload_median", microphone_sensor.payload_median())
    print("payload_std", microphone_sensor.payload_std())
    print("metadata", microphone_sensor.metadata())
    print("metadata_as_dict", microphone_sensor.metadata_as_dict())

    # We can also print a description of the sensor itself
    print(microphone_sensor)

# BarometerSensor
if wrapped_packet.has_barometer_sensor():
    barometer_sensor = wrapped_packet.barometer_sensor()
    print("sensor_name", barometer_sensor.sensor_name())
    print("timestamps_microseconds_utc", barometer_sensor.timestamps_microseconds_utc())
    print("payload_type", barometer_sensor.payload_type())
    print("payload_values", barometer_sensor.payload_values())
    print("sample_interval_mean", barometer_sensor.sample_interval_mean())
    print("sample_interval_median", barometer_sensor.sample_interval_median())
    print("sample_interval_std", barometer_sensor.sample_interval_std())
    print("payload_mean", barometer_sensor.payload_mean())
    print("payload_median", barometer_sensor.payload_median())
    print("payload_std", barometer_sensor.payload_std())
    print("metadata", barometer_sensor.metadata())
    print("metadata_as_dict", barometer_sensor.metadata_as_dict())

    # We can also print a description of the sensor itself
    print(barometer_sensor)

# LocationSensor
if wrapped_packet.has_location_sensor():
    location_sensor = wrapped_packet.location_sensor()
    print("sensor_name", location_sensor.sensor_name())
    print("timestamps_microseconds_utc", location_sensor.timestamps_microseconds_utc())
    print("payload_type", location_sensor.payload_type())
    print("payload_values_latitude", location_sensor.payload_values_latitude())
    print("payload_values_longitude", location_sensor.payload_values_longitude())
    print("payload_values_altitude", location_sensor.payload_values_altitude())
    print("payload_values_speed", location_sensor.payload_values_speed())
    print("payload_values_accuracy", location_sensor.payload_values_accuracy())
    print("sample_interval_mean", location_sensor.sample_interval_mean())
    print("sample_interval_median", location_sensor.sample_interval_median())
    print("sample_interval_std", location_sensor.sample_interval_std())
    print("payload_values_latitude_mean", location_sensor.payload_values_latitude_mean())
    print("payload_values_latitude_median", location_sensor.payload_values_latitude_median())
    print("payload_values_latitude_std", location_sensor.payload_values_latitude_std())
    print("payload_values_longitude_mean", location_sensor.payload_values_longitude_mean())
    print("payload_values_longitude_median", location_sensor.payload_values_longitude_median())
    print("payload_values_longitude_std", location_sensor.payload_values_longitude_std())
    print("payload_values_altitude_mean", location_sensor.payload_values_altitude_mean())
    print("payload_values_altitude_median", location_sensor.payload_values_altitude_median())
    print("payload_values_altitude_std", location_sensor.payload_values_altitude_std())
    print("payload_values_speed_mean", location_sensor.payload_values_speed_mean())
    print("payload_values_speed_median", location_sensor.payload_values_speed_median())
    print("payload_values_speed_std", location_sensor.payload_values_speed_std())
    print("payload_values_accuracy_mean", location_sensor.payload_values_accuracy_mean())
    print("payload_values_accuracy_median", location_sensor.payload_values_accuracy_median())
    print("payload_values_accuracy_std", location_sensor.payload_values_accuracy_std())
    print("metadata", location_sensor.metadata())
    print("metadata_as_dict", location_sensor.metadata_as_dict())

    # We can also print a description of the sensor itself
    print(location_sensor)

# TimeSynchronizationSensor
if wrapped_packet.has_time_synchronization_sensor():
    time_synchronization_sensor = wrapped_packet.time_synchronization_sensor()
    print("payload_type", time_synchronization_sensor.payload_type())
    print("payload_values", time_synchronization_sensor.payload_values())
    print("metadata", time_synchronization_sensor.metadata())
    print("metadata_as_dict", time_synchronization_sensor.metadata_as_dict())

    # We can also print a description of the sensor itself
    print(time_synchronization_sensor)

# AccelerometerSensor
if wrapped_packet.has_accelerometer_sensor():
    accelerometer_sensor = wrapped_packet.accelerometer_sensor()
    print("sensor_name", accelerometer_sensor.sensor_name())
    print("timestamps_microseconds_utc", accelerometer_sensor.timestamps_microseconds_utc())
    print("payload_type", accelerometer_sensor.payload_type())
    print("sample_interval_mean", accelerometer_sensor.sample_interval_mean())
    print("sample_interval_median", accelerometer_sensor.sample_interval_median())
    print("sample_interval_std", accelerometer_sensor.sample_interval_std())
    print("payload_values_x", accelerometer_sensor.payload_values_x())
    print("payload_values_y", accelerometer_sensor.payload_values_y())
    print("payload_values_z", accelerometer_sensor.payload_values_z())
    print("payload_values_x_mean", accelerometer_sensor.payload_values_x_mean())
    print("payload_values_x_median", accelerometer_sensor.payload_values_x_median())
    print("payload_values_x_std", accelerometer_sensor.payload_values_x_std())
    print("payload_values_y_mean", accelerometer_sensor.payload_values_y_mean())
    print("payload_values_y_median", accelerometer_sensor.payload_values_y_median())
    print("payload_values_y_std", accelerometer_sensor.payload_values_y_std())
    print("payload_values_z_mean", accelerometer_sensor.payload_values_z_mean())
    print("payload_values_z_median", accelerometer_sensor.payload_values_z_median())
    print("payload_values_z_std", accelerometer_sensor.payload_values_z_std())
    print("metadata", accelerometer_sensor.metadata())
    print("metadata_as_dict", accelerometer_sensor.metadata_as_dict())

    # We can also print a description of the sensor itself
    print(accelerometer_sensor)

# GyroscopeSensor
if wrapped_packet.has_gyroscope_sensor():
    gyroscope_sensor = wrapped_packet.gyroscope_sensor()
    print("sensor_name", gyroscope_sensor.sensor_name())
    print("timestamps_microseconds_utc", gyroscope_sensor.timestamps_microseconds_utc())
    print("payload_type", gyroscope_sensor.payload_type())
    print("sample_interval_mean", gyroscope_sensor.sample_interval_mean())
    print("sample_interval_median", gyroscope_sensor.sample_interval_median())
    print("sample_interval_std", gyroscope_sensor.sample_interval_std())
    print("payload_values_x", gyroscope_sensor.payload_values_x())
    print("payload_values_y", gyroscope_sensor.payload_values_y())
    print("payload_values_z", gyroscope_sensor.payload_values_z())
    print("payload_values_x_mean", gyroscope_sensor.payload_values_x_mean())
    print("payload_values_x_median", gyroscope_sensor.payload_values_x_median())
    print("payload_values_x_std", gyroscope_sensor.payload_values_x_std())
    print("payload_values_y_mean", gyroscope_sensor.payload_values_y_mean())
    print("payload_values_y_median", gyroscope_sensor.payload_values_y_median())
    print("payload_values_y_std", gyroscope_sensor.payload_values_y_std())
    print("payload_values_z_mean", gyroscope_sensor.payload_values_z_mean())
    print("payload_values_z_median", gyroscope_sensor.payload_values_z_median())
    print("payload_values_z_std", gyroscope_sensor.payload_values_z_std())
    print("metadata", gyroscope_sensor.metadata())
    print("metadata_as_dict", gyroscope_sensor.metadata_as_dict())

    # We can also print a description of the sensor itself
    print(gyroscope_sensor)

# MagnetometerSensor
if wrapped_packet.has_magnetometer_sensor():
    magnetometer_sensor = wrapped_packet.magnetometer_sensor()
    print("sensor_name", magnetometer_sensor.sensor_name())
    print("timestamps_microseconds_utc", magnetometer_sensor.timestamps_microseconds_utc())
    print("payload_type", magnetometer_sensor.payload_type())
    print("sample_interval_mean", magnetometer_sensor.sample_interval_mean())
    print("sample_interval_median", magnetometer_sensor.sample_interval_median())
    print("sample_interval_std", magnetometer_sensor.sample_interval_std())
    print("payload_values_x", magnetometer_sensor.payload_values_x())
    print("payload_values_y", magnetometer_sensor.payload_values_y())
    print("payload_values_z", magnetometer_sensor.payload_values_z())
    print("payload_values_x_mean", magnetometer_sensor.payload_values_x_mean())
    print("payload_values_x_median", magnetometer_sensor.payload_values_x_median())
    print("payload_values_x_std", magnetometer_sensor.payload_values_x_std())
    print("payload_values_y_mean", magnetometer_sensor.payload_values_y_mean())
    print("payload_values_y_median", magnetometer_sensor.payload_values_y_median())
    print("payload_values_y_std", magnetometer_sensor.payload_values_y_std())
    print("payload_values_z_mean", magnetometer_sensor.payload_values_z_mean())
    print("payload_values_z_median", magnetometer_sensor.payload_values_z_median())
    print("payload_values_z_std", magnetometer_sensor.payload_values_z_std())
    print("metadata", magnetometer_sensor.metadata())
    print("metadata_as_dict", magnetometer_sensor.metadata_as_dict())

    # We can also print a description of the sensor itself
    print(magnetometer_sensor)

# LightSensor
if wrapped_packet.has_light_sensor():
    light_sensor = wrapped_packet.light_sensor()
    print("sensor_name", light_sensor.sensor_name())
    print("timestamps_microseconds_utc", light_sensor.timestamps_microseconds_utc())
    print("payload_type", light_sensor.payload_type())
    print("payload_values", light_sensor.payload_values())
    print("sample_interval_mean", light_sensor.sample_interval_mean())
    print("sample_interval_median", light_sensor.sample_interval_median())
    print("sample_interval_std", light_sensor.sample_interval_std())
    print("payload_mean", light_sensor.payload_mean())
    print("payload_median", light_sensor.payload_median())
    print("payload_std", light_sensor.payload_std())
    print("metadata", light_sensor.metadata())
    print("metadata_as_dict", light_sensor.metadata_as_dict())

    # We can also print a description of the sensor itself
    print(light_sensor)

# InfraredSensor
if wrapped_packet.has_light_sensor():
    infrared_sensor = wrapped_packet.infrared_sensor()
    print("sensor_name", infrared_sensor.sensor_name())
    print("timestamps_microseconds_utc", infrared_sensor.timestamps_microseconds_utc())
    print("payload_type", infrared_sensor.payload_type())
    print("payload_values", infrared_sensor.payload_values())
    print("sample_interval_mean", infrared_sensor.sample_interval_mean())
    print("sample_interval_median", infrared_sensor.sample_interval_median())
    print("sample_interval_std", infrared_sensor.sample_interval_std())
    print("payload_mean", infrared_sensor.payload_mean())
    print("payload_median", infrared_sensor.payload_median())
    print("payload_std", infrared_sensor.payload_std())
    print("metadata", infrared_sensor.metadata())
    print("metadata_as_dict", infrared_sensor.metadata_as_dict())

    # We can also print a description of the sensor itself
    print(infrared_sensor)

# Cloning a WrappedRedvoxPacket
# It's possible to make a clone of a packet for modification so that the original packet is not modified.
cloned_packet = wrapped_packet.clone()

# Comparing sensor sensors and WrappedRedvoxPackets
# All sensor sensors implement Python's "__eq__" method which allows us to compare sensor sensors by content.
# When comparisons are made, it means that every fields in each sensor matches exactly. Let's look at an example.

# First, let's create a copy of our example packet.
wrapped_packet_2 = wrapped_packet.clone()

# Let's now compare them for equality
print(wrapped_packet == wrapped_packet_2)

# Next, let's modify the second packet and then check for equality
wrapped_packet_2.set_api(901)
print(wrapped_packet == wrapped_packet_2)

# We can also do this for sensor sensors.
print(wrapped_packet.microphone_sensor() == wrapped_packet_2.microphone_sensor())

# And then modify and compare
wrapped_packet_2.microphone_sensor().set_sensor_name("foo")
print(wrapped_packet.microphone_sensor() == wrapped_packet_2.microphone_sensor())

# We can also find the difference between two sensor sensors
print(wrapped_packet.microphone_sensor().diff(wrapped_packet_2.microphone_sensor()))

# Or between two WrappedRedvoxPackets
print(wrapped_packet.diff(wrapped_packet_2))


