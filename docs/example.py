from redvox.api900 import reader

# First, let's read and wrap the file in our high-level wrapper
redvox_api900_file = reader.wrap(reader.read_file("0000001314_1532656864354.rdvxz"))

# Now let's access all fields at the top level of the packet
print(redvox_api900_file.api())
print(redvox_api900_file.redvox_id())
print(redvox_api900_file.uuid())
print(redvox_api900_file.authenticated_email())
print(redvox_api900_file.authentication_token())
print(redvox_api900_file.firebase_token())
print(redvox_api900_file.is_backfilled())
print(redvox_api900_file.is_private())
print(redvox_api900_file.is_scrambled())
print(redvox_api900_file.device_make())
print(redvox_api900_file.device_model())
print(redvox_api900_file.device_os())
print(redvox_api900_file.device_os_version())
print(redvox_api900_file.app_version())
print(redvox_api900_file.battery_level_percent())
print(redvox_api900_file.device_temperature_c())
print(redvox_api900_file.acquisition_server())
print(redvox_api900_file.time_synchronization_server())
print(redvox_api900_file.authentication_server())
print(redvox_api900_file.app_file_start_timestamp_epoch_microseconds_utc())
print(redvox_api900_file.app_file_start_timestamp_machine())
print(redvox_api900_file.server_timestamp_epoch_microseconds_utc())

# First we check to make sure the device has a microphone channel
if redvox_api900_file.has_microphone_channel():
    # Most of the time, if a device has a sensor, it only has one of them...
    microphone_sensor_channel = redvox_api900_file.microphone_channels()[0]

    # Access to sensor fields
    print(microphone_sensor_channel.sensor_name())
    print(microphone_sensor_channel.sample_rate_hz())
    print(microphone_sensor_channel.first_sample_timestamp_epoch_microseconds_utc())
    print(microphone_sensor_channel.payload_mean())
    print(microphone_sensor_channel.payload_std())

    # Access to sensor values
    print(microphone_sensor_channel.payload_values())


# The barometer channel
if redvox_api900_file.has_barometer_channel():
    barometer_sensor_channel = redvox_api900_file.barometer_channels()[0]

    # Access to sensor fields
    print(barometer_sensor_channel.sensor_name())
    print(barometer_sensor_channel.sample_interval_mean())
    print(barometer_sensor_channel.sample_interval_median())
    print(barometer_sensor_channel.sample_interval_std())
    print(barometer_sensor_channel.payload_mean())
    print(barometer_sensor_channel.payload_median())
    print(barometer_sensor_channel.payload_std())

    # Access to sensor values
    print(barometer_sensor_channel.payload_values())

# The location channel
if redvox_api900_file.has_location_channel():
    location_channel = redvox_api900_file.location_channels()[0]

    # Access to sensor fields
    print(location_channel.sensor_name())
    print(location_channel.sample_interval_mean())
    print(location_channel.sample_interval_median())
    print(location_channel.sample_interval_std())
    print(location_channel.payload_values_accuracy_mean())
    print(location_channel.payload_values_accuracy_median())
    print(location_channel.payload_values_accuracy_std())
    print(location_channel.metadata_as_dict())

    # The statistics for the location channels must be accessed individually
    print(location_channel.payload_values_latitude_mean())
    print(location_channel.payload_values_latitude_median())
    print(location_channel.payload_values_latitude_std())
    print(location_channel.payload_values_longitude_mean())
    print(location_channel.payload_values_longitude_median())
    print(location_channel.payload_values_longitude_std())
    print(location_channel.payload_values_altitude_mean())
    print(location_channel.payload_values_altitude_median())
    print(location_channel.payload_values_altitude_std())
    print(location_channel.payload_values_speed_mean())
    print(location_channel.payload_values_speed_median())
    print(location_channel.payload_values_speed_std())

    # The payload can either be accessed as an interleaved payload
    print(location_channel.payload_values())

    # Or individual components can be extracted
    print(location_channel.payload_values_latitude())
    print(location_channel.payload_values_longitude())
    print(location_channel.payload_values_altitude())
    print(location_channel.payload_values_speed())
    print(location_channel.payload_values_accuracy())

# Time synchronization channel
if redvox_api900_file.has_time_synchronization_channel():
    time_synchronization_channel = redvox_api900_file.time_synchronization_channels()[0]
    print(time_synchronization_channel.payload_values())

# Accelerometer channel
if redvox_api900_file.has_accelerometer_channel():
    accelerometer_channel = redvox_api900_file.accelerometer_channels()[0]

    # Access to sensor fields
    print(accelerometer_channel.sensor_name())
    print(accelerometer_channel.sample_interval_mean())
    print(accelerometer_channel.sample_interval_median())
    print(accelerometer_channel.sample_interval_std())

    # The statistics can be accessed for each sensor channel individually
    print(accelerometer_channel.payload_values_x_mean())
    print(accelerometer_channel.payload_values_x_median())
    print(accelerometer_channel.payload_values_x_std())
    print(accelerometer_channel.payload_values_y_mean())
    print(accelerometer_channel.payload_values_y_median())
    print(accelerometer_channel.payload_values_y_std())
    print(accelerometer_channel.payload_values_z_mean())
    print(accelerometer_channel.payload_values_z_median())
    print(accelerometer_channel.payload_values_z_std())

    # The payload can be accessed as a single interleaved channel
    print(accelerometer_channel.payload_values())

    # Or individual components
    print(accelerometer_channel.payload_values_x())
    print(accelerometer_channel.payload_values_y())
    print(accelerometer_channel.payload_values_z())

# Magnetometer channel
if redvox_api900_file.has_magnetometer_channel():
    magnetometer_channel = redvox_api900_file.accelerometer_channels()[0]

    # Access to sensor fields
    print(magnetometer_channel.sensor_name())
    print(magnetometer_channel.sample_interval_mean())
    print(magnetometer_channel.sample_interval_median())
    print(magnetometer_channel.sample_interval_std())

    # The statistics can be accessed for each sensor channel individually
    print(magnetometer_channel.payload_values_x_mean())
    print(magnetometer_channel.payload_values_x_median())
    print(magnetometer_channel.payload_values_x_std())
    print(magnetometer_channel.payload_values_y_mean())
    print(magnetometer_channel.payload_values_y_median())
    print(magnetometer_channel.payload_values_y_std())
    print(magnetometer_channel.payload_values_z_mean())
    print(magnetometer_channel.payload_values_z_median())
    print(magnetometer_channel.payload_values_z_std())

    # The payload can be accessed as a single interleaved channel
    print(magnetometer_channel.payload_values())

    # Or individual components
    print(magnetometer_channel.payload_values_x())
    print(magnetometer_channel.payload_values_y())
    print(magnetometer_channel.payload_values_z())

# Gyroscope channel
if redvox_api900_file.has_magnetometer_channel():
    gyroscope_channel = redvox_api900_file.accelerometer_channels()[0]

    # Access to sensor fields
    print(gyroscope_channel.sensor_name())
    print(gyroscope_channel.sample_interval_mean())
    print(gyroscope_channel.sample_interval_median())
    print(gyroscope_channel.sample_interval_std())

    # The statistics can be accessed for each sensor channel individually
    print(gyroscope_channel.payload_values_x_mean())
    print(gyroscope_channel.payload_values_x_median())
    print(gyroscope_channel.payload_values_x_std())
    print(gyroscope_channel.payload_values_y_mean())
    print(gyroscope_channel.payload_values_y_median())
    print(gyroscope_channel.payload_values_y_std())
    print(gyroscope_channel.payload_values_z_mean())
    print(gyroscope_channel.payload_values_z_median())
    print(gyroscope_channel.payload_values_z_std())

    # The payload can be accessed as a single interleaved channel
    print(gyroscope_channel.payload_values())

    # Or individual components
    print(gyroscope_channel.payload_values_x())
    print(gyroscope_channel.payload_values_y())
    print(gyroscope_channel.payload_values_z())

# The light channel
if redvox_api900_file.has_light_channel():
    light_sensor_channel = redvox_api900_file.light_channels()[0]

    # Access to sensor fields
    print(light_sensor_channel.sensor_name())
    print(light_sensor_channel.sample_interval_mean())
    print(light_sensor_channel.sample_interval_median())
    print(light_sensor_channel.sample_interval_std())
    print(light_sensor_channel.payload_mean())
    print(light_sensor_channel.payload_median())
    print(light_sensor_channel.payload_std())

    # Access to sensor values
    print(light_sensor_channel.payload_values())