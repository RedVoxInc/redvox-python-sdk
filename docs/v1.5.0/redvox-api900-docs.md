## Redvox API 900 SDK Documentation

The RedVox SDK is written in Python 3.6+ and provides utility classes, methods, and functions for working with RedVox API 900 data. The API 900 standalone reader provides functionality for easily accessing all packet fields and sensor payloads within individual API 900 packets. The API 900 reader does not perform queries over multiple data sets of aggregation of data.

The Redvox API 900 utilizes Google's protobuf library for serializing and deserializing data between devices. It's possible to interact with API 900 data directly by selecting a pre-compiled language wrapper at https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/generated_code/ and including the wrapper in your software project. These wrappers provide all the functionality required for creating and reading Redvox API 900 files. The low level API 900 data format is described and documented in detail at: https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/doc/api900/api900.md?at=master&fileviewer=file-view-default

### Table of Contents

* [Prerequisites](#markdown-header-prerequisites)
* [Installing from pip](#markdown-header-installing-from-pip)
* [Installing from source](#markdown-header-installing-from-source)
* [Updating the RedVox Python SDK](#markdown-header-updating-the-redvox-python-sdk)
* [Working with the SDK CLI](#markdown-header-working-with-the-sdk-cli)
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
* [Example files](#markdown-header-example-files)
* [Generated API Documentation](#markdown-header-generated-api-documentation)

### Prerequisites

Python 3.6 or greater is required. 

This project depends on `lz4`, `numpy`, and `protobuf` libraries. `coala` is required if you wish to perform linting and/or static analysis. These dependencies will be installed automatically if you install this library from pip (see: [Installing from pip](#markdown-header-installing-from-pip)).


### Installing from pip

Installing the RedVox SDK via pip is the recommended way of obtaining the library. This method also takes care of installing required dependencies.

To install run `pip install redvox`.

### Installing from source

pip is the recommended way of obtaining this library. However, if you are looking for the source distribution, it can be found at https://bitbucket.org/redvoxhi/redvox-api900-python-reader/downloads/

### Updating the RedVox Python SDK

pip is the recommended way of updating this library. To update to the latest version, run `pip install redvox --upgrade --no-cache`.

### Verifying installation

It is possible to verify installation of the library by printing out the version information. There are two top level functions in the `redvox` namespace that do this. `version()` which returns the version number string. An example follows:

```
import redvox

print(redvox.version())
``` 

which, when ran produces the following output:

```
1.5.0
```

### Working with the SDK CLI

The Python SDK provides a small command line interface (CLI) that has the following features:

* Convert .rdvxz files to RedVox API 900 compliant .json files
* Convert RedVox API 900 compliant .json files to .rdvxz files
* Display the contents of .rdvxz files

Once the redvox library has been installed from pip, the CLI can be accessed by running:

`python3 -m redvox.api900.cli [CMD] [FILES]` where [CMD] is one of `to_json`, `to_rdvxz`, or `print` and [FILES] is a list of paths to either *.rdvxz files or *.json files.

##### Example: Converting .rdvxz files to RedVox API 900 .json files

Given the following files in `/docs/v1.5.0/examples/example_data` (or a directory of your choice)

```

```

Let's first convert a single file to .json.

```

```

And now if we look at the directory listing we see the .json file.

```

```

We can convert multiple files at once with:

```

```

and the contents of the directory contains:

```

```

##### Example: Converting RedVox compliant API 900 .json files to .rdvxz files

We can also convert from .json files to .rdvxz files using the `to_rdvxz command`.

Let's start with a directory of .json files.

```

```

We can convert a single file:

```

```

and the contents are now:

```

```

or we can convert all the .json files at once

```

```

which changes the directory contents to:

```

```

##### Example: Displaying the contents of .rdvxz files

It's possible to display the contents of a single or multiple .rdvxz files with the `print` command.

To display the contents of a single file:

```

```

Multiple files can be displayed at once as well with:

```

```

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
| from_json(json: str) | api900_pb2.RedvoxPacket | Accepts a string containing JSON and converts it into an instance of an api900_pb2.RedvoxPacket |
| to_json(redvox_packet: api900_pb2.RedvoxPacket | str | Converts an instance of an api900_pb2.RedvoxPacket into a string containing json |

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
| metadata() | List[str] |
| metadata_as_dict() | Dict[str, str] |
| to_json() | str |

The following methods allow you to set the values of high-level API methods.  Give the method a value that matches the type within the parenthesis and it will change the redvox packet's corresponding data to the value.
| Name |
| -----|
| set_api(int) |
| set_redvox_id(str) |
| set_uuid(str) |
| set_authenticated_email(str) |
| set_authentication_token(str) |
| set_firebase_token(str) |
| set_is_backfilled(bool) |
| set_is_private(bool) |
| set_is_scrambled(bool) |
| set_device_make(str) |
| set_device_model(str) |
| set_device_os(str) |
| set_device_os_version(str) |
| set_app_version(str) |
| set_battery_level_percent(float) |
| set_device_temperature_c(float) |
| set_acquisition_server(str) |
| set_time_synchronization_server(str) |
| set_authentication_server(str) |
| set_app_file_start_timestamp_epoch_microseconds_utc(int) |
| set_app_file_start_timestamp_machine(int) |
| set_server_timestamp_epoch_microseconds_utc(int) |
| set_metadata(List[str]) |

The following methods provide easy access to high-level sensor channel implementations. Each sensor has a method to test for existence, a method for retrieving the sensor, and a method for setting sensor. Please note that `None` can be passed to the set_sensor methods to clear a sensor.

| Name | Return Type |
|------|------|
| has_microphone_channel() | bool |
| microphone_channel() | Optional[MicrophoneSensor] |
| set_microphone_channel(Optional[MicrophoneSensor]) | |
| has_barometer_channel() | bool |
| barometer_channel() | Optional[BarometerSensor] |
| set_barometer_chanel(Optional[BarometerSensor] | |
| has_location_channel() | bool |
| location_channel() | Optional[LocationSensor] |
| set_location_channel(Optional[LocationSensor] | |
| has_time_synchronization_channel() | bool |
| time_synchronization_channel() | Optional[TimeSynchronizationChannel] |
| set_time_synchronization_channel(Optional[TimeSynchronizationChannel] | |
| has_accelerometer_channel() | bool |
| accelerometer_channel() | Optional[AccelerometerSensor] |
| set_accelerometer_channel(Optional[AccelerometerSensor] | |
| has_magnetometer_channel() | bool |
| magnetometer_channel() | Optional[MagnetometerSensor] |
| set_magnetometer_channel(Optional[MagnetometerSensor] | |
| has_gyroscope_channel() | bool |
| gyroscope_channel() | Optional[GyroscopeSensor] |
| set_gyroscope_channel(Optional[GyroscopeSensor] | |
| has_light_channel() | bool |
| light_channel() | Optional[LightSensor] |
| set_light_channel(Optional[LightSensor] | |
| has_infrared_channel() | bool |
| infrared_channel() | Optional[InfraredSensor] |
| set_infrared_channel(Optional[InfraredChannel] | |
| has_image_channel() | bool |
| image_channel() | Optional[ImageChannel] |

It's also possible to convert a WrappedRedvoxPacket into a compressed array of bytes. This can be achieved by calling the compressed_buffer method on a WrappedRedvoxPacket. These compressed buffers can be written to disk as .rdvxz files.

| Name | Type |
| compressed_buffer() | bytes |

##### Example loading RedVox data

Let's look at accessing some of top level fields. 

```python

```

### Working with microphone sensor channels
It's possible to test for the availability of this sensor in a data packet by calling the method `has_microphone_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `microphone_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `MicrophoneSensor` class contains methods for directly accessing the fields and payloads of microphone channels. The following table briefly describes the available methods for microphone sensor channels.

| Name | Type | Description | 
|------|------|-------------|
| sample_rate_hz() | float | Returns the sample rate in Hz of this microphone sensor channel |
| set_sample_rate_hz(float) | | Sets the sample rate in Hz of this microphone sensor channel |
| first_sample_timestamp_epoch_microseconds_utc() | int | The timestamp of the first microphone sample in this packet as the number of microseconds since the epoch UTC |
| set_first_sample_timestamp_epoch_microseconds_utc(int) | | Sets the timestamp of the first microphone sample in this packet as the number of microseconds since the epoch UTC |
| sensor_name() | str | Returns the name of the sensor for this microphone sensor channel |
| set_sensor_name(str) | | Sets the name of the sensor for this microphone sensor channel |
| payload_values() | numpy.ndarray[int] | A numpy array of integers representing the data payload from this packet's microphone channel |
| payload_mean() | float | The mean value of this packet's microphone data payload |
| payload_median() | float | The median value of this packet's microphone data payload |
| payload_std() | float | The standard deviation of this packet's microphone data payload |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| set_metadata(List[str]) | | Sets this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Creating a microphone sensor
This function creates a microphone sensor:

```python

```


##### Example microphone sensor reading

```python

```

### Working with barometer sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_barometer_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `barometer channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `BarometerSensor` class contains methods for directly accessing the fields and payloads of barometer channels. The following table briefly describes the available methods for barometer sensor channels.

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| set_timestamps_microseconds_utc(numpy.ndarray[int]) | | Sets the timestamps |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| set_sensor_name(str) | | Sets the name of the sensor for this sensor channel |
| payload_values() | numpy.ndarray[float] | A numpy array of floats representing the data payload from this packet's barometer channel |
| payload_mean() | float | The mean value of this packet's barometer data payload |
| payload_median() | float | The median value of this packet's barometer data payload |
| payload_std() | float | The standard deviation of this packet's barometer data payload |
| sample_interval_mean() | float | The mean of the sample interval for samples in this packet |
| sample_interval_median() | float | The median of the sample interval for samples in this packet |
| sample_interval_std() | float | The standard deviation of the sample interval for samples in this packet |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| set_metadata(List[str]) | | Sets this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Creating a barometer sensor
This function creates a barometer sensor:

```python

```

##### Example barometer sensor reading

```python

```

### Working with location sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_location_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `location_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `LocationSensor` class contains methods for directly accessing the fields and payloads of location channels. The location channel can return the payload as interleaved values or also return the individual components of the payload. The following table briefly describes the available methods for location sensor channels. 

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| set_timestamps_microseconds_utc(numpy.ndarray[int]) | | Sets the timestamps |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| set_sensor_name(str) | | Sets the name of the sensor for this sensor channel |
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
| set_metadata(List[str]) | | Sets this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Creating a location sensor
These functions create a location sensor:

```python

```

##### Example locations sensor reading

```python

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
| set_metadata(List[str]) | | Sets this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Creating a time synchronization sensor
This function creates a time synchronization sensor:

```python

```

##### Example time synchronization sensor reading

```python

```

### Working with accelerometer sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_accelerometer_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `accelerometer_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `AccelerationSensor` class contains methods for directly accessing the fields and payloads of accelerometer channels. The accelerometer sensor payload can either be accessed as a single interleaved payload which contains all X, Y, and Z components, or each component can be accessed individually. The following table briefly describes the available methods for accelerometer sensor channels. 

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| set_timestamps_microseconds_utc(numpy.ndarray[int]) | | Sets the timestamps |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| set_sensor_name(str) | | Sets the name of the sensor for this sensor channel |
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
| set_metadata(List[str]) | | Sets this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Creating an accelerometer sensor
These functions create an accelerometer sensor:

```python

```


##### Example accelerometer sensor reading

```python

```

### Working with magnetometer sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_magnetometer_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `magenetoner_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `MagnetometerSensor` class contains methods for directly accessing the fields and payloads of magnetometer channels. The magnetometer sensor payload can either be accessed as a single interleaved payload which contains all X, Y, and Z components, or each component can be accessed individually. The following table briefly describes the available methods for magnetometer sensor channels. 

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| set_timestamps_microseconds_utc(numpy.ndarray[int]) | | Sets the timestamps |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| set_sensor_name(str) | | Sets the name of the sensor for this sensor channel |
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
| set_metadata(List[str]) | | Sets this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Creating a magnetometer sensor
These functions create an magnetometer sensor:

```python

```
Give the first function a sensor name (sensor_name), metadata (metadata), the data as an interleaved array (payload), the timestamps in microseconds since epoch utc (timestamps).  The data should look like : [x_0, y_0, z_0, x_1, y_1, z_1, ... , x_n, y_n, z_n] where 0-n is the index of the samples.
Give the second function a sensor name (sensor_name), metadata (metadata), the list of arrays that make up the data (payload), the timestamps in microseconds since epoch utc (timestamps).  There are usually 3 channels in an magnetometer sensor, so you should give this function 3 arrays.  For consistency, put the arrays in order of: x-axis, y-axis, z-axis.

##### Example magnetometer sensor reading

```python

```

### Working with gyroscope sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_gyroscope_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `gyroscope_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `GyroscopeSensor` class contains methods for directly accessing the fields and payloads of gyroscope channels. The gyroscope sensor payload can either be accessed as a single interleaved payload which contains all X, Y, and Z components, or each component can be accessed individually. The following table briefly describes the available methods for gyroscope sensor channels. 

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| set_timestamps_microseconds_utc(numpy.ndarray[int]) | | Sets the timestamps |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| set_sensor_name(str) | | Sets the name of the sensor for this sensor channel |
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
| set_metadata(List[str]) | | Sets this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Creating a gyroscope sensor
These functions create an gyroscope sensor:

```python

```
Give the first function a sensor name (sensor_name), metadata (metadata), the data as an interleaved array (payload), the timestamps in microseconds since epoch utc (timestamps).  The data should look like : [x_0, y_0, z_0, x_1, y_1, z_1, ... , x_n, y_n, z_n] where 0-n is the index of the samples.
Give the second function a sensor name (sensor_name), metadata (metadata), the list of arrays that make up the data (payload), the timestamps in microseconds since epoch utc (timestamps).  There are usually 3 channels in an gyroscope sensor, so you should give this function 3 arrays.  For consistency, put the arrays in order of: x-axis, y-axis, z-axis.

##### Example gyroscope sensor reading

```python

```

### Working with light sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_light_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `light_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `LightSensor` class contains methods for directly accessing the fields and payloads of light channels. The following table briefly describes the available methods for light sensor channels.

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| set_timestamps_microseconds_utc(numpy.ndarray[int]) | | Sets the timestamps |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| set_sensor_name(str) | | Sets the name of the sensor for this sensor channel |
| payload_values() | numpy.ndarray[float] | A numpy array of floats representing the data payload from this packet's light channel |
| payload_mean() | float | The mean value of this packet's light data payload |
| payload_median() | float | The median value of this packet's light data payload |
| payload_std() | float | The standard deviation of this packet's light data payload |
| sample_interval_mean() | float | The mean of the sample interval for samples in this packet |
| sample_interval_median() | float | The median of the sample interval for samples in this packet |
| sample_interval_std() | float | The standard deviation of the sample interval for samples in this packet |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| set_metadata(List[str]) | | Sets this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Creating a light sensor
This function creates a light sensor:

```python

```
Give it a sensor name (sensor_name), metadata (metadata), the data (payload), the timestamps in microseconds since epoch utc (timestamps)

##### Example light sensor reading

```print

```

### Working with infrared sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_infrared_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `infrared_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `InfraredSensor` class contains methods for directly accessing the fields and payloads of infrared channels. The following table briefly describes the available methods for infrared sensor channels.

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| set_timestamps_microseconds_utc(numpy.ndarray[int]) | | Sets the timestamps |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| set_sensor_name(str) | | Sets the name of the sensor for this sensor channel |
| payload_values() | numpy.ndarray[float] | A numpy array of floats representing the data payload from this packet's infrared channel |
| payload_mean() | float | The mean value of this packet's light data payload |
| payload_median() | float | The median value of this packet's light data payload |
| payload_std() | float | The standard deviation of this packet's infrared data payload |
| sample_interval_mean() | float | The mean of the sample interval for samples in this packet |
| sample_interval_median() | float | The median of the sample interval for samples in this packet |
| sample_interval_std() | float | The standard deviation of the sample interval for samples in this packet |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| set_metadata(List[str]) | | Sets this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |

##### Creating an infrared sensor
This function creates an infrared sensor:

```python

```
Give it a sensor name (sensor_name), metadata (metadata), the data (payload), the timestamps in microseconds since epoch utc (timestamps)

##### Example infrared sensor reading

```python

```

### Example files

A set of example files can be found at: https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/

### Generated API documentation

API documentation for this library can be found at: https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/