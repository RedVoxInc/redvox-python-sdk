## Redvox API 900 SDK Documentation

The RedVox SDK is written in Python 3.6+ and provides utility classes, methods, and functions for working with RedVox API 900 data. The API 900 standalone reader provides functionality for easily accessing all packet fields and sensor payloads within individual API 900 packets. The API 900 reader does not perform queries over multiple data sets of aggregation of data.

The Redvox API 900 utilizes Google's protobuf library for serializing and deserializing data between devices. It's possible to interact with API 900 data directly by selecting a pre-compiled language wrapper at https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/generated_code/ and including the wrapper in your software project. These wrappers provide all the functionality required for creating and reading Redvox API 900 files. The low level API 900 data format is described and documented in detail at: https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/doc/api900/api900.md?at=master&fileviewer=file-view-default

### Table of Contents

* [Prerequisites](#markdown-header-prerequisites)
* [Installing from pip](#markdown-header-installing-from-pip)
* [Loading RedVox API 900 files](#markdown-header-loading-redvox-api-900-files)
* [Working with microphone sensor channels](#markdown-header-working-with-microphone-sensor-channels)
* [Working with barometer sensor channels](#markdown-header-working-with-barometer-sensor-channels)
* [Working with location sensor channels](#markdown-header-working-with-location-sensor-channels)
* [working with time synchronization channels](#markdown-header-working-with-time-synchronization-sensor-channels)
* [Working with accelerometer sensor channels](#markdown-header-working-with-accelerometer-sensor-channels)
* [Working with magnetometer sensor channels](#markdown-header-working-with-magenetometer-sensor-channels)
* [Working with gyroscope sensor channels](#markdown-header-working-with-gyroscope-sensor-channels)
* [Working with light sensor channels](#markdown-header-working-with-light-sensor-channels)
* [Working with infrafred sensor channels](#markdown-header-working-with-infrared-sensor-channels)
* [Working with image sensor channels](#markdown-header-working-with-image-sensor-channels)
* [Full Example](https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.3.1/example.py)
* [Generated API Documentation](https://redvoxhi.bitbucket.io/redvox-sdk/v1.3.1/)

### Prerequisites

Python 3.6 or greater is required. 

This project depends on `lz4`, `numpy`, and `protobuf` libraries. `coala` is required if you wish to perform linting and/or static analysis.


### Installing from pip

Installing the RedVox SDK via pip is the recommended way of obtaining the library. This method also takes care of installing required dependencies.

To install run `pip install redvox`.

### Installing from source

pip is the recomended way of obtaining this library. However, if you are looking for the source distribution, it can be found at https://bitbucket.org/redvoxhi/redvox-api900-python-reader/downloads/

### Loading RedVox API 900 Files

The module `redvox/api900/reader.py` contains two functions for loading RedVox API 900 data files: `read_buffer` and `read_file`. The module also contains one function, `wrap`, that wraps the low-level protobuf RedVox packet in our high-level API which allows easy access to packet fields and sensor data.

`read_buffer` accepts an array of bytes which represent a serialized RedVox data packet and returns a low-level protobuf `api900_pb2.RedvoxPacket`. `read_file` accepts the path to a RedVox data packet file stored somewhere on the file system and also returns a low-level protobuf `api900_pb2.RedvoxPacket`.

A `WrappedRedvoxPacket` is a Python class that acts as a wrapper around the raw protobuf API and provides convenience methods for accessing fields and sensor channels of the loaded RedVox packet.

We can call the `wrap` function to wrap a low-level protobuf packet in our high-level API.

The following table summarizes the available top-level function of reader.py.

| Name | Type | Description |
|------|------|-------------|
| read_file(file: str) | api900_pb2.RedvoxPacket | Reads a file and returns a low-level RedVox API 900 protobuf packet |
| read_buffer(buf: bytes) | api900_pb2.RedvoxPacket | Reads from a buffer of bytes and returns a low-level RedVox API 900 packet |
| wrap(redvox_packet: api900_pb2.RedvoxPacket) | WrappedRedvoxPacket | Wraps a low-level RedVox packet in our high-level API |

The following is a table that summarizes the convenience methods provided by the WrappedRedvoxPacket class. For brevity, we only list the new, high-level API methods. If you wish to use or dig into the low-level protobuf API, please see the section titled "Low Level Access".

The following methods retrieve fields which are described in detail at: https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master

| Name | Type |
| -----|------|
| api() | int |
| redvox_id() | str |
| uuid() | str | 
| authenticated_email() | str | 
| authentication_token() | str | 
| firebase_token() | str |
| is_backfilled() | bool | 
| is_private() | bool |
| is_scrambled() | bool |
| device_make() | str |
| device_model() | str |
| device_os() | str |
| device_os_version() | str |
| app_version() | str |
| battery_level_percent() | float |
| device_temperature_c() | float |
| acquisition_server() | str |
| time_synchronization_server() | str |
| authentication_server() | str |
| app_file_start_timestamp_epoch_microseconds_utc() | int |
| app_file_start_timestamp_machine() | int |
| server_timestamp_epoch_microseconds_utc() | int |
| metadata_as_dict() | Dict[str, str] |

The following methods provide easy access to high-level sensor channel implementations. Each sensor has a method to test for existence and a method for retrieving the sensor data itself. Sensor data is returned in a list since its possible to have more than one of the same sensor type on a single device. 

| Name | Type |
|------|------|
| has_microphone_channel() | bool |
| microphone_channel() | Optional[MicrophoneSensor] |
| has_barometer_channel() | bool |
| barometer_channel() | Optional[BarometerSensor] |
| has_location_channel() | bool |
| location_channel() | Optional[LocationSensor] |
| has_time_synchronization_channel() | bool |
| time_synchronization_channel() | Optional[TimeSynchronizationChannel] |
| has_accelerometer_channel() | bool |
| accelerometer_channel() | Optional[AccelerometerSensor] |
| has_magnetometer_channel() | bool |
| magnetometer_channel() | Optional[MagnetometerSensor] |
| has_gyroscope_channel() | bool |
| gyroscope_channel() | Optional[GyroscopeSensor] |
| has_light_channel() | bool |
| light_channel() | Optional[ListSensor] |
| has_infrared_channel() | bool |
| infrared_channel() | Optional[InfraredSensor] |
| has_image_channel() | bool |
| image_channel() | Optional[ImageChannel] |

##### Example loading RedVox data

Let's look at accessing some of top level fields. 

```
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
```


### Working with microphone sensor channels
It's possible to test for the availability of this sensor in a data packet by calling the method `has_microphone_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `microphone_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `MicrophoneSensor` class contains methods for directly accessing the fields and payloads of microphone channels. The following table briefly describes the available methods for microphone sensor channels.

| Name | Type | Description | 
|------|------|-------------|
| sample_rate_hz() | float | Returns the sample rate in Hz of this microphone sensor channel |
| first_sample_timestamp_epoch_microseconds_utc() | int | The timestamp of the first microphone sample in this packet as the number of microseconds since the epoch UTC |
| sensor_name() | str | Returns the name of the sensor for this microphone sensor channel |
| payload_values() | numpy.ndarray[int] | A numpy array of integers representing the data payload from this packet's microphone channel |
| payload_mean() | float | The mean value of this packet's microphone data payload |
| payload_median() | float | The median value of this packet's microphone data payload |
| payload_std() | float | The standard deviation of this packet's microphone data payload |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Example microphone sensor reading

```
redvox_api900_file = reader.wrap(reader.read_file("0000001314_1539627249223.rdvxz"))

# First we check to make sure the device has a microphone channel
if redvox_api900_file.has_microphone_channel():
    # Most of the time, if a device has a sensor, it only has one of them...
    microphone_sensor_channel = redvox_api900_file.microphone_channel()

    # Access to sensor fields
    print(microphone_sensor_channel.sensor_name())
    print(microphone_sensor_channel.sample_rate_hz())
    print(microphone_sensor_channel.first_sample_timestamp_epoch_microseconds_utc())
    print(microphone_sensor_channel.payload_mean())
    print(microphone_sensor_channel.payload_std())
    print(microphone_sensor_channel.payload_median())
    print(microphone_sensor_channel.metadata_as_dict())
    print(microphone_sensor_channel.metadata())
    print(microphone_sensor_channel.payload_type())

    # Access to sensor values
    print(microphone_sensor_channel.payload_values())
```

### Working with barometer sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_barometer_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `barometer channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `BarometerSensor` class contains methods for directly accessing the fields and payloads of barometer channels. The following table briefly describes the available methods for barometer sensor channels.

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| payload_values() | numpy.ndarray[float] | A numpy array of floats representing the data payload from this packet's barometer channel |
| payload_mean() | float | The mean value of this packet's barometer data payload |
| payload_median() | float | The median value of this packet's barometer data payload |
| payload_std() | float | The standard deviation of this packet's barometer data payload |
| sample_interval_mean() | float | The mean of the sample interval for samples in this packet |
| sample_interval_median() | float | The median of the sample interval for samples in this packet |
| sample_interval_std() | float | The standard deviation of the sample interval for samples in this packet |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Example barometer sensor reading

```
redvox_api900_file = reader.wrap(reader.read_file("0000001314_1539627249223.rdvxz"))

if redvox_api900_file.has_barometer_channel():
    barometer_sensor_channel = redvox_api900_file.barometer_channel()

    # Access to sensor fields
    print(barometer_sensor_channel.sensor_name())
    print(barometer_sensor_channel.timestamps_microseconds_utc())
    print(barometer_sensor_channel.sample_interval_mean())
    print(barometer_sensor_channel.sample_interval_median())
    print(barometer_sensor_channel.sample_interval_std())
    print(barometer_sensor_channel.payload_mean())
    print(barometer_sensor_channel.payload_median())
    print(barometer_sensor_channel.payload_std())
    print(barometer_sensor_channel.metadata_as_dict())
    print(barometer_sensor_channel.metadata())
    print(barometer_sensor_channel.payload_type())

    # Access to sensor values
    print(barometer_sensor_channel.payload_values())
```

### Working with location sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_location_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `location_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `LocationSensor` class contains methods for directly accessing the fields and payloads of location channels. The location channel can return the payload as interleaved values or also return the individual components of the payload. The following table briefly describes the available methods for location sensor channels. 

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| payload_values() | numpy.ndarray[float] | A numpy array of interleaved location values [[latitude_0, longitude_0, altitude_0, speed_0, accuracy_0], [latitude_1, longitude_1, altitude_1, speed_1, accuracy_1], ..., [latitude_n, longitude_n, altitude_n, speed_n, accuracy_n]] |
| payload_values_latitude() | numpy.ndarray[float] | A numpy array contains the latitude values for each sample |
| payload_values_longitude() | numpy.ndarray[float] | A numpy array contains the longitude values for each sample |
| payload_values_altitude() | numpy.ndarray[float] | A numpy array contains the altitude values for each sample |
| payload_values_speed() | numpy.ndarray[float] | A numpy array contains the speed values for each sample |
| payload_values_accuracy() | numpy.ndarray[float] | A numpy array contains the accuracy values for each sample |
| payload_values_latitude_mean() | float | Mean value of latitudes from this location channel |
| payload_values_longitude_mean() | float | Mean value of longitudes from this location channel |
| payload_values_altitude_mean() | float | Mean value of altitudes from this location channel |
| payload_values_speed_mean() | float | Mean value of speeds from this location channel |
| payload_values_accuracy_mean() | float | Mean value of accuracies from this location channel |
| payload_values_latitude_median() | float | Median value of latitudes from this location channel |
| payload_values_longitude_median() | float | Median value of longitudes from this location channel |
| payload_values_altitude_median() | float | Median value of altitudes from this location channel |
| payload_values_speed_median() | float | Median value of speeds from this location channel |
| payload_values_accuracy_median() | float | Median value of accuracies from this location channel |
| payload_values_latitude_std() | float | Standard deviation value of latitudes from this location channel |
| payload_values_longitude_std() | float | Standard deviation value of longitudes from this location channel |
| payload_values_altitude_std() | float | Standard deviation value of altitudes from this location channel |
| payload_values_speed_std() | float | Standard deviation value of speeds from this location channel |
| payload_values_accuracy_std() | float | Standard deviation value of accuracies from this location channel |
| sample_interval_mean() | float | The mean of the sample interval for samples in this packet |
| sample_interval_median() | float | The median of the sample interval for samples in this packet |
| sample_interval_std() | float | The standard deviation of the sample interval for samples in this packet |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Example locations sensor reading

```
redvox_api900_file = reader.wrap(reader.read_file("0000001314_1539627249223.rdvxz"))

if redvox_api900_file.has_location_channel():
    location_channel = redvox_api900_file.location_channel()

    # Access to sensor fields
    print(location_channel.sensor_name())
    print(location_channel.timestamps_microseconds_utc())
    print(location_channel.sample_interval_mean())
    print(location_channel.sample_interval_median())
    print(location_channel.sample_interval_std())
    print(location_channel.payload_values_accuracy_mean())
    print(location_channel.payload_values_accuracy_median())
    print(location_channel.payload_values_accuracy_std())

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

    print(location_channel.metadata_as_dict())
    print(location_channel.metadata())
    print(location_channel.payload_type())
```

### Working with time synchronization sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_time_synchronization_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `time_synchronization_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `TimeSynchronizationSensor` class contains methods for directly accessing the fields and payloads of time synchronization channels. The following table briefly describes the available methods for time synchronization sensor channels. 

| Name | Type | Description | 
|------|------|-------------|
| payload_values() | numpy.ndarray[float] | Time synchronization exchange parameters |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |


##### Example time synchronization sensor reading

```
redvox_api900_file = reader.wrap(reader.read_file("0000001314_1539627249223.rdvxz"))

if redvox_api900_file.has_time_synchronization_channel():
    time_synchronization_channel = redvox_api900_file.time_synchronization_channel()
    print(time_synchronization_channel.payload_values())
    print(time_synchronization_channel.metadata_as_dict())
    print(time_synchronization_channel.metadata())
    print(time_synchronization_channel.payload_type())
```

### Working with accelerometer sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_accelerometer_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `accelerometer_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `AccelerationSensor` class contains methods for directly accessing the fields and payloads of accelerometer channels. The accelerometer sensor payload can either be accessed as a single interleaved payload which contains all X, Y, and Z components, or each component can be accessed individually. The following table briefly describes the available methods for accelerometer sensor channels. 

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| payload_values() | numpy.ndarray[float] | A numpy array of floats representing the X, Y, and Z components of this channel [[x_0, y_0, z_0], [x_1, y_1, z_1], ..., [x_n, y_n, z_n]] |
| payload_values_x() | numpy.ndarray[float] | A numpy array of floats representing the X component of this channel. |
| payload_values_y() | numpy.ndarray[float] | A numpy array of floats representing the Y component of this channel. |
| payload_values_z() | numpy.ndarray[float] | A numpy array of floats representing the Z component of this channel. |
| payload_values_x_mean() | float | The mean value of the X component from this packet's channel |
| payload_values_y_mean() | float | The mean value of the Y component from this packet's channel |
| payload_values_z_mean() | float | The mean value of the Z component from this packet's channel |
| payload_values_x_median() | float | The median value of the X component from this packet's channel |
| payload_values_y_median() | float | The median value of the Y component from this packet's channel |
| payload_values_z_median() | float | The median value of the Z component from this packet's channel |
| payload_values_x_std() | float | The standard deviation value of the X component from this packet's channel |
| payload_values_y_std() | float | The standard deviation value of the Y component from this packet's channel |
| payload_values_z_std() | float | The standard deviation value of the Z component from this packet's channel |
| sample_interval_mean() | float | The mean of the sample interval for samples in this packet |
| sample_interval_median() | float | The median of the sample interval for samples in this packet |
| sample_interval_std() | float | The standard deviation of the sample interval for samples in this packet |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |


##### Example accelerometer sensor reading

```
redvox_api900_file = reader.wrap(reader.read_file("0000001314_1539627249223.rdvxz"))

if redvox_api900_file.has_accelerometer_channel():
    accelerometer_channel = redvox_api900_file.accelerometer_channel()

    # Access to sensor fields
    print(accelerometer_channel.sensor_name())
    print(accelerometer_channel.timestamps_microseconds_utc())
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

    print(accelerometer_channel.metadata_as_dict())
    print(accelerometer_channel.metadata())
    print(accelerometer_channel.payload_type())
```

### Working with magnetometer sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_magnetometer_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `magenetoner_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `MagnetometerSensor` class contains methods for directly accessing the fields and payloads of magnetometer channels. The magnetometer sensor payload can either be accessed as a single interleaved payload which contains all X, Y, and Z components, or each component can be accessed individually. The following table briefly describes the available methods for magnetometer sensor channels. 

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| payload_values() | numpy.ndarray[float] | A numpy array of floats representing the X, Y, and Z components of this channel [[x_0, y_0, z_0], [x_1, y_1, z_1], ..., [x_n, y_n, z_n]] |
| payload_values_x() | numpy.ndarray[float] | A numpy array of floats representing the X component of this channel. |
| payload_values_y() | numpy.ndarray[float] | A numpy array of floats representing the Y component of this channel. |
| payload_values_z() | numpy.ndarray[float] | A numpy array of floats representing the Z component of this channel. |
| payload_values_x_mean() | float | The mean value of the X component from this packet's channel |
| payload_values_y_mean() | float | The mean value of the Y component from this packet's channel |
| payload_values_z_mean() | float | The mean value of the Z component from this packet's channel |
| payload_values_x_median() | float | The median value of the X component from this packet's channel |
| payload_values_y_median() | float | The median value of the Y component from this packet's channel |
| payload_values_z_median() | float | The median value of the Z component from this packet's channel |
| payload_values_x_std() | float | The standard deviation value of the X component from this packet's channel |
| payload_values_y_std() | float | The standard deviation value of the Y component from this packet's channel |
| payload_values_z_std() | float | The standard deviation value of the Z component from this packet's channel |
| sample_interval_mean() | float | The mean of the sample interval for samples in this packet |
| sample_interval_median() | float | The median of the sample interval for samples in this packet |
| sample_interval_std() | float | The standard deviation of the sample interval for samples in this packet |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Example magnetometer sensor reading

```
redvox_api900_file = reader.wrap(reader.read_file("0000001314_1539627249223.rdvxz"))

# Magnetometer channel
if redvox_api900_file.has_magnetometer_channel():
    magnetometer_channel = redvox_api900_file.magnetometer_channel()

    # Access to sensor fields
    print(magnetometer_channel.sensor_name())
    print(magnetometer_channel.timestamps_microseconds_utc())
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

    print(magnetometer_channel.metadata_as_dict())
    print(magnetometer_channel.metadata())
    print(magnetometer_channel.payload_type())
```

### Working with gyroscope sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_gyroscope_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `gyroscope_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `GyroscopeSensor` class contains methods for directly accessing the fields and payloads of gyroscope channels. The gyroscope sensor payload can either be accessed as a single interleaved payload which contains all X, Y, and Z components, or each component can be accessed individually. The following table briefly describes the available methods for gyroscope sensor channels. 

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| payload_values() | numpy.ndarray[float] | A numpy array of floats representing the X, Y, and Z components of this channel [[x_0, y_0, z_0], [x_1, y_1, z_1], ..., [x_n, y_n, z_n]] |
| payload_values_x() | numpy.ndarray[float] | A numpy array of floats representing the X component of this channel. |
| payload_values_y() | numpy.ndarray[float] | A numpy array of floats representing the Y component of this channel. |
| payload_values_z() | numpy.ndarray[float] | A numpy array of floats representing the Z component of this channel. |
| payload_values_x_mean() | float | The mean value of the X component from this packet's channel |
| payload_values_y_mean() | float | The mean value of the Y component from this packet's channel |
| payload_values_z_mean() | float | The mean value of the Z component from this packet's channel |
| payload_values_x_median() | float | The median value of the X component from this packet's channel |
| payload_values_y_median() | float | The median value of the Y component from this packet's channel |
| payload_values_z_median() | float | The median value of the Z component from this packet's channel |
| payload_values_x_std() | float | The standard deviation value of the X component from this packet's channel |
| payload_values_y_std() | float | The standard deviation value of the Y component from this packet's channel |
| payload_values_z_std() | float | The standard deviation value of the Z component from this packet's channel |
| sample_interval_mean() | float | The mean of the sample interval for samples in this packet |
| sample_interval_median() | float | The median of the sample interval for samples in this packet |
| sample_interval_std() | float | The standard deviation of the sample interval for samples in this packet |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Example gyroscope sensor reading

```
redvox_api900_file = reader.wrap(reader.read_file("0000001314_1539627249223.rdvxz"))

if redvox_api900_file.has_magnetometer_channel():
    gyroscope_channel = redvox_api900_file.gyroscope_channel()

    # Access to sensor fields
    print(gyroscope_channel.sensor_name())
    print(gyroscope_channel.timestamps_microseconds_utc())
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

    print(gyroscope_channel.metadata_as_dict())
    print(gyroscope_channel.metadata())
    print(gyroscope_channel.payload_type())

```

### Working with light sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_light_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `light_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `LightSensor` class contains methods for directly accessing the fields and payloads of light channels. The following table briefly describes the available methods for light sensor channels.

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| payload_values() | numpy.ndarray[float] | A numpy array of floats representing the data payload from this packet's light channel |
| payload_mean() | float | The mean value of this packet's light data payload |
| payload_median() | float | The median value of this packet's light data payload |
| payload_std() | float | The standard deviation of this packet's light data payload |
| sample_interval_mean() | float | The mean of the sample interval for samples in this packet |
| sample_interval_median() | float | The median of the sample interval for samples in this packet |
| sample_interval_std() | float | The standard deviation of the sample interval for samples in this packet |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Example light sensor reading

```
redvox_api900_file = reader.wrap(reader.read_file("0000001314_1539627249223.rdvxz"))

if redvox_api900_file.has_light_channel():
    light_sensor_channel = redvox_api900_file.light_channel()

    # Access to sensor fields
    print(light_sensor_channel.sensor_name())
    print(light_sensor_channel.timestamps_microseconds_utc())
    print(light_sensor_channel.sample_interval_mean())
    print(light_sensor_channel.sample_interval_median())
    print(light_sensor_channel.sample_interval_std())
    print(light_sensor_channel.payload_mean())
    print(light_sensor_channel.payload_median())
    print(light_sensor_channel.payload_std())

    # Access to sensor values
    print(light_sensor_channel.payload_values())

    print(light_sensor_channel.metadata_as_dict())
    print(light_sensor_channel.metadata())
    print(light_sensor_channel.payload_type())
```


### Working with infrared sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_infrared_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `infrared_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `InfraredSensor` class contains methods for directly accessing the fields and payloads of infrared channels. The following table briefly describes the available methods for infrared sensor channels.

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| payload_values() | numpy.ndarray[float] | A numpy array of floats representing the data payload from this packet's infrared channel |
| payload_mean() | float | The mean value of this packet's light data payload |
| payload_median() | float | The median value of this packet's light data payload |
| payload_std() | float | The standard deviation of this packet's infrared data payload |
| sample_interval_mean() | float | The mean of the sample interval for samples in this packet |
| sample_interval_median() | float | The median of the sample interval for samples in this packet |
| sample_interval_std() | float | The standard deviation of the sample interval for samples in this packet |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Example infrared sensor reading

```
redvox_api900_file = reader.wrap(reader.read_file("0000001314_1539627249223.rdvxz"))

if redvox_api900_file.has_light_channel():
    infrared_sensor_channel = redvox_api900_file.infrared_channel()

    # Access to sensor fields
    print(infrared_sensor_channel.sensor_name())
    print(infrared_sensor_channel.timestamps_microseconds_utc())
    print(infrared_sensor_channel.sample_interval_mean())
    print(infrared_sensor_channel.sample_interval_median())
    print(infrared_sensor_channel.sample_interval_std())
    print(infrared_sensor_channel.payload_mean())
    print(infrared_sensor_channel.payload_median())
    print(infrared_sensor_channel.payload_std())

    # Access to sensor values
    print(infrared_sensor_channel.payload_values())

    print(infrared_sensor_channel.metadata_as_dict())
    print(infrared_sensor_channel.metadata())
    print(infrared_sensor_channel.payload_type())

```

### Working with image sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_image_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `image_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `ImageSensor` class contains methods for directly accessing the fields and payloads of image channels. The following table briefly describes the available methods for infrared sensor channels.

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| payload_values() | numpy.ndarray[float] | A numpy array of floats representing the data payload from this packet's image channel |
| sample_interval_mean() | float | The mean of the sample interval for samples in this packet |
| sample_interval_median() | float | The median of the sample interval for samples in this packet |
| sample_interval_std() | float | The standard deviation of the sample interval for samples in this packet |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |
| num_images() | img | Return the number of images in this channel |
| get_image_offsets() | List[int] | Return a list of byte offsets into this channel's payload where each byte offset represents the starting byte of an image |
| get_image_bytes(idx: int) | numpy.ndarray (uint8) | Returns the bytes associated with the image at this given index (0 indexed) |
| write_image_to_file(idx: int, path: str) | | Writes the image stored at the given index to the given path on disk |
| write_all_images_to_directory(directory: str) | | Writes all available images in this packet to the given directory using a default name for each image |

##### Example image sensor reading

```
redvox_api900_file = reader.wrap(reader.read_file("0000001314_1539627249223.rdvxz"))

if redvox_api900_file.has_image_channel():
image_sensor_channel = redvox_api900_file.image_channel()

    # Access to sensor fields
    print(image_sensor_channel.sensor_name())
    print(image_sensor_channel.timestamps_microseconds_utc())
    print(image_sensor_channel.sample_interval_mean())
    print(image_sensor_channel.sample_interval_median())
    print(image_sensor_channel.sample_interval_std())

    # Raw byte payload of all images
    print(len(image_sensor_channel.payload_values()))

    # Number of images in packet payload
    print(image_sensor_channel.num_images())

    # Byte offsets of each image in payload
    print(image_sensor_channel.get_image_offsets())

    # Loop through and retrieve the bytes for each image
    for i in range(image_sensor_channel.num_images()):
        print(len(image_sensor_channel.get_image_bytes(i)))

    # Write the image files to disk individually and provide a
    # custom filename
    for i in range(image_sensor_channel.num_images()):
        image_sensor_channel.write_image_to_file(i, "{}.jpg".format(i))

    # Write all available images to disk using default filenames
    image_sensor_channel.write_all_images_to_directory(".")

    print(image_sensor_channel.metadata_as_dict())
    print(image_sensor_channel.metadata())
    print(image_sensor_channel.payload_type())
```