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
* [Full Example](https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.4.1/example.py)
* [Generated API Documentation](https://redvoxhi.bitbucket.io/redvox-sdk/v1.4.1/)

### Prerequisites

Python 3.6 or greater is required. 

This project depends on `lz4`, `numpy`, and `protobuf` libraries. `coala` is required if you wish to perform linting and/or static analysis.


### Installing from pip

Installing the RedVox SDK via pip is the recommended way of obtaining the library. This method also takes care of installing required dependencies.

To install run `pip install redvox`.

### Installing from source

pip is the recommended way of obtaining this library. However, if you are looking for the source distribution, it can be found at https://bitbucket.org/redvoxhi/redvox-api900-python-reader/downloads/

### Verifying installation

It is possible to verify installation of the library by printing out the version information. There are two top level functions in the `redvox` namespace that do this. `version()` which returns the version number string and `print_version()` which prints the version number string. A full example follows:

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

**Example: Converting .rdvxz files to RedVox API 900 .json files**

Given the following files in `/data` (or a directory of your choice)

```
> ls -l /data
total 616
-rwxr-xr-x@ 1 anthony  wheel  25205 Mar 11 14:46 1637660007_1552350841586.rdvxz
-rwxr-xr-x@ 1 anthony  wheel  25133 Mar 11 14:46 1637660007_1552350892787.rdvxz
-rwxr-xr-x@ 1 anthony  wheel  25200 Mar 11 14:46 1637660007_1552350943987.rdvxz
-rwxr-xr-x@ 1 anthony  wheel  25156 Mar 11 14:46 1637660007_1552350995187.rdvxz
-rwxr-xr-x@ 1 anthony  wheel  25147 Mar 11 14:46 1637660007_1552351046386.rdvxz
-rwxr-xr-x@ 1 anthony  wheel  25211 Mar 11 14:46 1637660007_1552351097587.rdvxz
-rwxr-xr-x@ 1 anthony  wheel  25117 Mar 11 14:46 1637660007_1552351148787.rdvxz
-rwxr-xr-x@ 1 anthony  wheel  25264 Mar 11 14:46 1637660007_1552351199987.rdvxz
-rwxr-xr-x@ 1 anthony  wheel  25093 Mar 11 14:46 1637660007_1552351251185.rdvxz
-rwxr-xr-x@ 1 anthony  wheel  25262 Mar 11 14:46 1637660007_1552351302387.rdvxz
-rwxr-xr-x@ 1 anthony  wheel  25240 Mar 11 14:46 1637660007_1552351353587.rdvxz
```

Let's first convert a single file to .json.

```
> python3 -m redvox.api900.cli to_json /data/1637660007_1552350841586.rdvxz
Converting /data/1637660007_1552350841586.rdvxz -> /data/1637660007_1552350841586.json
```

And now if we look at the directory listing we see the .json file.

```
> ls -l /data
total 952
-rw-r--r--  1 anthony  wheel  169519 Mar 11 14:50 1637660007_1552350841586.json
-rwxr-xr-x@ 1 anthony  wheel   25205 Mar 11 14:46 1637660007_1552350841586.rdvxz
-rwxr-xr-x@ 1 anthony  wheel   25133 Mar 11 14:46 1637660007_1552350892787.rdvxz
-rwxr-xr-x@ 1 anthony  wheel   25200 Mar 11 14:46 1637660007_1552350943987.rdvxz
-rwxr-xr-x@ 1 anthony  wheel   25156 Mar 11 14:46 1637660007_1552350995187.rdvxz
-rwxr-xr-x@ 1 anthony  wheel   25147 Mar 11 14:46 1637660007_1552351046386.rdvxz
-rwxr-xr-x@ 1 anthony  wheel   25211 Mar 11 14:46 1637660007_1552351097587.rdvxz
-rwxr-xr-x@ 1 anthony  wheel   25117 Mar 11 14:46 1637660007_1552351148787.rdvxz
-rwxr-xr-x@ 1 anthony  wheel   25264 Mar 11 14:46 1637660007_1552351199987.rdvxz
-rwxr-xr-x@ 1 anthony  wheel   25093 Mar 11 14:46 1637660007_1552351251185.rdvxz
-rwxr-xr-x@ 1 anthony  wheel   25262 Mar 11 14:46 1637660007_1552351302387.rdvxz
-rwxr-xr-x@ 1 anthony  wheel   25240 Mar 11 14:46 1637660007_1552351353587.rdvxz
```

We can convert multiple files at once with:

```
> python3 -m redvox.api900.cli to_json /data/*.rdvxz
Converting /data/1637660007_1552350841586.rdvxz -> /data/1637660007_1552350841586.json
Converting /data/1637660007_1552350892787.rdvxz -> /data/1637660007_1552350892787.json
Converting /data/1637660007_1552350943987.rdvxz -> /data/1637660007_1552350943987.json
Converting /data/1637660007_1552350995187.rdvxz -> /data/1637660007_1552350995187.json
Converting /data/1637660007_1552351046386.rdvxz -> /data/1637660007_1552351046386.json
Converting /data/1637660007_1552351097587.rdvxz -> /data/1637660007_1552351097587.json
Converting /data/1637660007_1552351148787.rdvxz -> /data/1637660007_1552351148787.json
Converting /data/1637660007_1552351199987.rdvxz -> /data/1637660007_1552351199987.json
Converting /data/1637660007_1552351251185.rdvxz -> /data/1637660007_1552351251185.json
Converting /data/1637660007_1552351302387.rdvxz -> /data/1637660007_1552351302387.json
Converting /data/1637660007_1552351353587.rdvxz -> /data/1637660007_1552351353587.json
```

and the contents of the directory contains:

```
> ls -l /data
total 4312
-rw-r--r--  1 anthony  wheel  169519 Mar 11 14:51 1637660007_1552350841586.json
-rwxr-xr-x@ 1 anthony  wheel   25205 Mar 11 14:46 1637660007_1552350841586.rdvxz
-rw-r--r--  1 anthony  wheel  169337 Mar 11 14:51 1637660007_1552350892787.json
-rwxr-xr-x@ 1 anthony  wheel   25133 Mar 11 14:46 1637660007_1552350892787.rdvxz
-rw-r--r--  1 anthony  wheel  169650 Mar 11 14:51 1637660007_1552350943987.json
-rwxr-xr-x@ 1 anthony  wheel   25200 Mar 11 14:46 1637660007_1552350943987.rdvxz
-rw-r--r--  1 anthony  wheel  169327 Mar 11 14:51 1637660007_1552350995187.json
-rwxr-xr-x@ 1 anthony  wheel   25156 Mar 11 14:46 1637660007_1552350995187.rdvxz
-rw-r--r--  1 anthony  wheel  168937 Mar 11 14:51 1637660007_1552351046386.json
-rwxr-xr-x@ 1 anthony  wheel   25147 Mar 11 14:46 1637660007_1552351046386.rdvxz
-rw-r--r--  1 anthony  wheel  169511 Mar 11 14:51 1637660007_1552351097587.json
-rwxr-xr-x@ 1 anthony  wheel   25211 Mar 11 14:46 1637660007_1552351097587.rdvxz
-rw-r--r--  1 anthony  wheel  169474 Mar 11 14:51 1637660007_1552351148787.json
-rwxr-xr-x@ 1 anthony  wheel   25117 Mar 11 14:46 1637660007_1552351148787.rdvxz
-rw-r--r--  1 anthony  wheel  169343 Mar 11 14:51 1637660007_1552351199987.json
-rwxr-xr-x@ 1 anthony  wheel   25264 Mar 11 14:46 1637660007_1552351199987.rdvxz
-rw-r--r--  1 anthony  wheel  169316 Mar 11 14:51 1637660007_1552351251185.json
-rwxr-xr-x@ 1 anthony  wheel   25093 Mar 11 14:46 1637660007_1552351251185.rdvxz
-rw-r--r--  1 anthony  wheel  169456 Mar 11 14:51 1637660007_1552351302387.json
-rwxr-xr-x@ 1 anthony  wheel   25262 Mar 11 14:46 1637660007_1552351302387.rdvxz
-rw-r--r--  1 anthony  wheel  169449 Mar 11 14:51 1637660007_1552351353587.json
-rwxr-xr-x@ 1 anthony  wheel   25240 Mar 11 14:46 1637660007_1552351353587.rdvxz
```

**Example: Converting RedVox compliant API 900 .json files to .rdvxz files**

We can also convert from .json files to .rdvxz files using the `to_rdvxz command`.

Let's start with a directory of .json files.

```
> ls -l /data
total 3696
-rw-r--r--  1 anthony  wheel  169519 Mar 11 14:51 1637660007_1552350841586.json
-rw-r--r--  1 anthony  wheel  169337 Mar 11 14:51 1637660007_1552350892787.json
-rw-r--r--  1 anthony  wheel  169650 Mar 11 14:51 1637660007_1552350943987.json
-rw-r--r--  1 anthony  wheel  169327 Mar 11 14:51 1637660007_1552350995187.json
-rw-r--r--  1 anthony  wheel  168937 Mar 11 14:51 1637660007_1552351046386.json
-rw-r--r--  1 anthony  wheel  169511 Mar 11 14:51 1637660007_1552351097587.json
-rw-r--r--  1 anthony  wheel  169474 Mar 11 14:51 1637660007_1552351148787.json
-rw-r--r--  1 anthony  wheel  169343 Mar 11 14:51 1637660007_1552351199987.json
-rw-r--r--  1 anthony  wheel  169316 Mar 11 14:51 1637660007_1552351251185.json
-rw-r--r--  1 anthony  wheel  169456 Mar 11 14:51 1637660007_1552351302387.json
-rw-r--r--  1 anthony  wheel  169449 Mar 11 14:51 1637660007_1552351353587.json
```

We can convert a single file:

```
> python3 -m redvox.api900.cli to_rdvxz /data/1637660007_1552350841586.json
Converting /data/1637660007_1552350841586.json -> /data/1637660007_1552350841586.rdvxz
```

and the contents are now:

```
> ls -l /data
total 3752
-rw-r--r--  1 anthony  wheel  169519 Mar 11 14:51 1637660007_1552350841586.json
-rw-r--r--  1 anthony  wheel   26963 Mar 11 14:59 1637660007_1552350841586.rdvxz
-rw-r--r--  1 anthony  wheel  169337 Mar 11 14:51 1637660007_1552350892787.json
-rw-r--r--  1 anthony  wheel  169650 Mar 11 14:51 1637660007_1552350943987.json
-rw-r--r--  1 anthony  wheel  169327 Mar 11 14:51 1637660007_1552350995187.json
-rw-r--r--  1 anthony  wheel  168937 Mar 11 14:51 1637660007_1552351046386.json
-rw-r--r--  1 anthony  wheel  169511 Mar 11 14:51 1637660007_1552351097587.json
-rw-r--r--  1 anthony  wheel  169474 Mar 11 14:51 1637660007_1552351148787.json
-rw-r--r--  1 anthony  wheel  169343 Mar 11 14:51 1637660007_1552351199987.json
-rw-r--r--  1 anthony  wheel  169316 Mar 11 14:51 1637660007_1552351251185.json
-rw-r--r--  1 anthony  wheel  169456 Mar 11 14:51 1637660007_1552351302387.json
-rw-r--r--  1 anthony  wheel  169449 Mar 11 14:51 1637660007_1552351353587.json
```

or we can convert all the .json files at once

```
> python3 -m redvox.api900.cli to_rdvxz /data/*.json
Converting /data/1637660007_1552350841586.json -> /data/1637660007_1552350841586.rdvxz
Converting /data/1637660007_1552350892787.json -> /data/1637660007_1552350892787.rdvxz
Converting /data/1637660007_1552350943987.json -> /data/1637660007_1552350943987.rdvxz
Converting /data/1637660007_1552350995187.json -> /data/1637660007_1552350995187.rdvxz
Converting /data/1637660007_1552351046386.json -> /data/1637660007_1552351046386.rdvxz
Converting /data/1637660007_1552351097587.json -> /data/1637660007_1552351097587.rdvxz
Converting /data/1637660007_1552351148787.json -> /data/1637660007_1552351148787.rdvxz
Converting /data/1637660007_1552351199987.json -> /data/1637660007_1552351199987.rdvxz
Converting /data/1637660007_1552351251185.json -> /data/1637660007_1552351251185.rdvxz
Converting /data/1637660007_1552351302387.json -> /data/1637660007_1552351302387.rdvxz
Converting /data/1637660007_1552351353587.json -> /data/1637660007_1552351353587.rdvxz
(redvox-analysis) 
```

which changes the directory contents to:

```
> ls -l /data
total 4312
-rw-r--r--  1 anthony  wheel  169519 Mar 11 14:51 1637660007_1552350841586.json
-rw-r--r--  1 anthony  wheel   26963 Mar 11 15:00 1637660007_1552350841586.rdvxz
-rw-r--r--  1 anthony  wheel  169337 Mar 11 14:51 1637660007_1552350892787.json
-rw-r--r--  1 anthony  wheel   26907 Mar 11 15:00 1637660007_1552350892787.rdvxz
-rw-r--r--  1 anthony  wheel  169650 Mar 11 14:51 1637660007_1552350943987.json
-rw-r--r--  1 anthony  wheel   27091 Mar 11 15:00 1637660007_1552350943987.rdvxz
-rw-r--r--  1 anthony  wheel  169327 Mar 11 14:51 1637660007_1552350995187.json
-rw-r--r--  1 anthony  wheel   27057 Mar 11 15:00 1637660007_1552350995187.rdvxz
-rw-r--r--  1 anthony  wheel  168937 Mar 11 14:51 1637660007_1552351046386.json
-rw-r--r--  1 anthony  wheel   27035 Mar 11 15:00 1637660007_1552351046386.rdvxz
-rw-r--r--  1 anthony  wheel  169511 Mar 11 14:51 1637660007_1552351097587.json
-rw-r--r--  1 anthony  wheel   27119 Mar 11 15:00 1637660007_1552351097587.rdvxz
-rw-r--r--  1 anthony  wheel  169474 Mar 11 14:51 1637660007_1552351148787.json
-rw-r--r--  1 anthony  wheel   26967 Mar 11 15:00 1637660007_1552351148787.rdvxz
-rw-r--r--  1 anthony  wheel  169343 Mar 11 14:51 1637660007_1552351199987.json
-rw-r--r--  1 anthony  wheel   27069 Mar 11 15:00 1637660007_1552351199987.rdvxz
-rw-r--r--  1 anthony  wheel  169316 Mar 11 14:51 1637660007_1552351251185.json
-rw-r--r--  1 anthony  wheel   27022 Mar 11 15:00 1637660007_1552351251185.rdvxz
-rw-r--r--  1 anthony  wheel  169456 Mar 11 14:51 1637660007_1552351302387.json
-rw-r--r--  1 anthony  wheel   27162 Mar 11 15:00 1637660007_1552351302387.rdvxz
-rw-r--r--  1 anthony  wheel  169449 Mar 11 14:51 1637660007_1552351353587.json
-rw-r--r--  1 anthony  wheel   27145 Mar 11 15:00 1637660007_1552351353587.rdvxz
```

**Example: Displaying the contents of .rdvxz files**

It's possible to display the contents of a single or multiple .rdvxz files with the `print` command.

To display the contents of a single file:

```
python3 -m redvox.api900.cli print /data/1637660007_1552351353587.rdvxz

 ------------- Contents of /data/1637660007_1552351353587.rdvxz
api: 900
uuid: "522630568"
redvox_id: "1637660007"
authenticated_email: "redvoxcore@gmail.com"
authentication_token: "redacted-1113962610"
device_make: "Huawei"
device_model: "Nexus 6P"
device_os: "Android"
device_os_version: "8.1.0"
app_version: "2.4.2"
...
```

Multiple files can be displayed at once as well with:

```
python3 -m redvox.api900.cli print /data/*.rdvxz
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

### Writing RedVox API 900 Files
The module now contains a function to write rdvxz files: `write_file`.  It takes a redvox packet and writes its information to a file.  The table below summarizes the function.
| Name | Type | Description |
|------|------|-------------|
| write_file(file: str, redvox_packet: api900_pb2.RedvoxPacket) | No return type: writes a rdvxz file | Writes a redvox file.  Specify the correct file type in the file string. |

Also provided are methods to create a redvox file.  This requires a little knowledge of underlying objects in a sensor.  You may find more information related to these objects in the section "Low Level Access".

Channels can be evenly sampled or unevenly sampled.  Evenly sampled channels have a constant sampling rate, while unevenly sampled channels need a list of timestamps for each sample.  Empty channels can be created and filled with data later.

Sensors contain either a single evenly sampled or unevenly sampled channel.  Each sensor contain has access to the channel's functions through its property named evenly_sampled_channel for unevenly_sampled_channel.  The kind of sampling the sensor does determines which one of the two properties it has.  Sensors are explained starting with the section "Working with microphone sensor channels".  All sensors can be created empty; you can fill in the data later.

Lastly, a redvox packet consists of one or more evenly sampled and/or unevenly sampled sensor channels.  The necessary functions for managing a redvox packet's channels are:
|    Name    | Description |
|------------|-------------|
| add_channel(channel: EvenlySampledChannel or UnevenlySampledChannel) | Adds a channel to the packet |
| edit_channel(channel_type: int, channel: EvenlySampledChannel or UnevenlySampledChannel) | Removes the channel of type channel_type and adds the passed channel to the packet.  Refer to the section "Low Level Access" for more information about channel types |
| delete_channel(channel_type: int) | Removes the channel of type channel_type.  Refer to the section "Low Level Access" for more information about channel types |
| has_channel(channel_type: int) | Checks if the packet has a channel of type channel_type.  Returns True if found, False if not.  Refer to the section "Low Level Access" for more information about channel types |
| get_channel(channel_type: int) | Gets the channel of type channel_type or None if the channel_type is not in the packet.  Refer to the section "Low Level Access" for more information about channel types |

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

```
create_microphone(sensor_name: str, metadata: typing.List[str], payload: numpy.array, rate: float, time: int)
```
Give it a sensor name (sensor_name), metadata (metadata), the data (payload), the sampling rate in Hz (rate), the first timestamp in microseconds since epoch utc (time).

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

    # Changing values
    microphone_sensor_channel.set_sensor_name("Example Microphone")
    microphone_sensor_channel.set_sample_rate_hz(42.0)

    # Setting values
    microphone_sensor_channel.create_microphone("Example Microphone", ["Meta", "data"], [1, 2, 3, 4, 5], 42.0, 0)
    microphone_sensor_channel = MicrophoneSensor().create_microphone("Example Microphone", ["Meta", "data"], [1, 2, 3, 4, 5], 42.0, 0)
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

```
create_barometer(sensor_name: str, metadata: typing.List[str], payload: numpy.array, timestamps: numpy.ndarray)
```
Give it a sensor name (sensor_name), metadata (metadata), the data (payload), the timestamps in microseconds since epoch utc (timestamps)

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

    # Changing values
    barometer_sensor_channel.set_sensor_name("Example Barometer")
    barometer_sensor_channel.timestamps_microseconds_utc([1, 3, 42, 8492, 9001])

    # Setting values
    barometer_sensor_channel.create_barometer("Example Barometer", ["Meta", "data"], [1, 2, 3, 4, 5], [1, 3, 42, 8492, 9001])
    barometer_sensor_channel = BarometerSensor().create_barometer("Example Barometer", ["Meta", "data"], [1, 2, 3, 4, 5], [1, 3, 42, 8492, 9001])
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

```
create_location(sensor_name: str, metadata: typing.List[str], payload: numpy.array, timestamps: numpy.ndarray)
create_location_from_deinterleaved_arrays(sensor_name: str, metadata: typing.List[str], payload: typing.List[numpy.array], timestamps: numpy.ndarray)
```
Give the first function a sensor name (sensor_name), metadata (metadata), the data as an interleaved array (payload), the timestamps in microseconds since epoch utc (timestamps).  The data should look like : [lat0, lon0, alt0, spd0, acc0, lat1, lon1, ... altn, spdn, accn] where 0-n is the index of the samples.
Give the second function a sensor name (sensor_name), metadata (metadata), the list of arrays that make up the data (payload), the timestamps in microseconds since epoch utc (timestamps).  There are usually 5 channels in a location sensor, so you should give this function 5 arrays.  For consistency, put the arrays in order of: latitude, longitude, altitude, speed, accuracy.

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

    # Changing values
    location_channel.set_sensor_name("Example Location")
    location_channel.timestamps_microseconds_utc([1, 3, 42, 8492, 9001])

    # Setting values
    location_channel.create_location("Example Location", ["meta", "data"], [1, 2, 3, 4, 5, 1.1, 2.2, 3.3, 4.4, 5.5, 1.11, 2.22, 3.33, 4.44, 5.55], [1, 10, 100])
    location_channel.create_location_from_deinterleaved_arrays("Example Location", ["meta", "data"], [[1, 1.1, 1.11], [2, 2.2, 2.22], [3, 3.3, 3.33], [4, 4.4, 4.44], [5, 5.5, 5.55]], [1, 10, 100])
    location_channel = LocationSensor().create_location("Example Location", ["meta", "data"], [1, 2, 3, 4, 5, 1.1, 2.2, 3.3, 4.4, 5.5, 1.11, 2.22, 3.33, 4.44, 5.55], [1, 10, 100])
    location_channel = LocationSensor().create_location_from_deinterleaved_arrays("Example Location", ["meta", "data"], [[1, 1.1, 1.11], [2, 2.2, 2.22], [3, 3.3, 3.33], [4, 4.4, 4.44], [5, 5.5, 5.55]], [1, 10, 100])
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

```
create_time(sensor_name: str, metadata: typing.List[str], payload: numpy.array)
```
Give it a sensor name (sensor_name), metadata (metadata), the data (payload).  The timestamps are in the payload for this sensor.

##### Example time synchronization sensor reading

```
redvox_api900_file = reader.wrap(reader.read_file("0000001314_1539627249223.rdvxz"))

if redvox_api900_file.has_time_synchronization_channel():
    time_synchronization_channel = redvox_api900_file.time_synchronization_channel()
    print(time_synchronization_channel.payload_values())
    print(time_synchronization_channel.metadata_as_dict())
    print(time_synchronization_channel.metadata())
    print(time_synchronization_channel.payload_type())

# Setting the channel
time_synchronization_channel.create_time("Example Time Synchronization", ["meta", "data"], [1, 10, 11, 100])
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

```
create_accelerometer(sensor_name: str, metadata: typing.List[str], payload: numpy.array, timestamps: numpy.ndarray)
create_accelerometer_from_deinterleaved_arrays(sensor_name: str, metadata: typing.List[str], payload: typing.List[numpy.array], timestamps: numpy.ndarray)
```
Give the first function a sensor name (sensor_name), metadata (metadata), the data as an interleaved array (payload), the timestamps in microseconds since epoch utc (timestamps).  The data should look like : [x_0, y_0, z_0, x_1, y_1, z_1, ... , x_n, y_n, z_n] where 0-n is the index of the samples.
Give the second function a sensor name (sensor_name), metadata (metadata), the list of arrays that make up the data (payload), the timestamps in microseconds since epoch utc (timestamps).  There are usually 3 channels in an accelerometer sensor, so you should give this function 3 arrays.  For consistency, put the arrays in order of: x-axis, y-axis, z-axis.

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

    # Changing values
    accelerometer_channel.set_sensor_name("Example Accelerometer")
    accelerometer_channel.timestamps_microseconds_utc([1, 3, 42, 8492, 9001])

    # Setting values
    accelerometer_channel.create_accelerometer("Example Accelerometer", ["meta", "data"], [1, 2, 3, 1.1, 2.2, 3.3, 1.11, 2.22, 3.33], [1, 10, 100])
    accelerometer_channel.create_accelerometer_from_deinterleaved_arrays("Example Accelerometer", ["meta", "data"], [[1, 1.1, 1.11], [2, 2.2, 2.22], [3, 3.3, 3.33]], [1, 10, 100])
    accelerometer_channel = AccelerometerSensor().create_accelerometer("Example Accelerometer", ["meta", "data"], [1, 2, 3, 1.1, 2.2, 3.3, 1.11, 2.22, 3.33], [1, 10, 100])
    accelerometer_channel = AccelerometerSensor().create_accelerometer_from_deinterleaved_arrays("Example Accelerometer", ["meta", "data"], [[1, 1.1, 1.11], [2, 2.2, 2.22], [3, 3.3, 3.33]], [1, 10, 100])
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

```
create_magnetometer(sensor_name: str, metadata: typing.List[str], payload: numpy.array, timestamps: numpy.ndarray)
create_magnetometer_from_deinterleaved_arrays(sensor_name: str, metadata: typing.List[str], payload: typing.List[numpy.array], timestamps: numpy.ndarray)
```
Give the first function a sensor name (sensor_name), metadata (metadata), the data as an interleaved array (payload), the timestamps in microseconds since epoch utc (timestamps).  The data should look like : [x_0, y_0, z_0, x_1, y_1, z_1, ... , x_n, y_n, z_n] where 0-n is the index of the samples.
Give the second function a sensor name (sensor_name), metadata (metadata), the list of arrays that make up the data (payload), the timestamps in microseconds since epoch utc (timestamps).  There are usually 3 channels in an magnetometer sensor, so you should give this function 3 arrays.  For consistency, put the arrays in order of: x-axis, y-axis, z-axis.

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

    # Changing values
    magnetometer_channel.set_sensor_name("Example Magnetometer")
    magnetometer_channel.timestamps_microseconds_utc([1, 3, 42, 8492, 9001])

    # Setting values
    magnetometer_channel.create_magnetometer("Example Magnetometer", ["meta", "data"], [1, 2, 3, 1.1, 2.2, 3.3, 1.11, 2.22, 3.33], [1, 10, 100])
    magnetometer_channel.create_magnetometer_from_deinterleaved_arrays("Example Magnetometer", ["meta", "data"], [[1, 1.1, 1.11], [2, 2.2, 2.22], [3, 3.3, 3.33]], [1, 10, 100])
    magnetometer_channel = MagnetometerSensor().create_magnetometer("Example Magnetometer", ["meta", "data"], [1, 2, 3, 1.1, 2.2, 3.3, 1.11, 2.22, 3.33], [1, 10, 100])
    magnetometer_channel = MagnetometerSensor().create_magnetometer_from_deinterleaved_arrays("Example Magnetometer", ["meta", "data"], [[1, 1.1, 1.11], [2, 2.2, 2.22], [3, 3.3, 3.33]], [1, 10, 100])
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

```
create_gyroscope(sensor_name: str, metadata: typing.List[str], payload: numpy.array, timestamps: numpy.ndarray)
create_gyroscope_from_deinterleaved_arrays(sensor_name: str, metadata: typing.List[str], payload: typing.List[numpy.array], timestamps: numpy.ndarray)
```
Give the first function a sensor name (sensor_name), metadata (metadata), the data as an interleaved array (payload), the timestamps in microseconds since epoch utc (timestamps).  The data should look like : [x_0, y_0, z_0, x_1, y_1, z_1, ... , x_n, y_n, z_n] where 0-n is the index of the samples.
Give the second function a sensor name (sensor_name), metadata (metadata), the list of arrays that make up the data (payload), the timestamps in microseconds since epoch utc (timestamps).  There are usually 3 channels in an gyroscope sensor, so you should give this function 3 arrays.  For consistency, put the arrays in order of: x-axis, y-axis, z-axis.

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

    # Changing values
    gyroscope_channel.set_sensor_name("Example Gyroscope")
    gyroscope_channel.timestamps_microseconds_utc([1, 3, 42, 8492, 9001])

    # Setting values
    gyroscope_channel.create_gyroscope("Example Gyroscope", ["meta", "data"], [1, 2, 3, 1.1, 2.2, 3.3, 1.11, 2.22, 3.33], [1, 10, 100])
    gyroscope_channel.create_gyroscope_from_deinterleaved_arrays("Example Gyroscope", ["meta", "data"], [[1, 1.1, 1.11], [2, 2.2, 2.22], [3, 3.3, 3.33]], [1, 10, 100])
    gyroscope_channel = GyroscopeSensor().create_gyroscope("Example Gyroscope", ["meta", "data"], [1, 2, 3, 1.1, 2.2, 3.3, 1.11, 2.22, 3.33], [1, 10, 100])
    gyroscope_channel = GyroscopeSensor().create_gyroscope_from_deinterleaved_arrays("Example Gyroscope", ["meta", "data"], [[1, 1.1, 1.11], [2, 2.2, 2.22], [3, 3.3, 3.33]], [1, 10, 100])

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

```
create_light(sensor_name: str, metadata: typing.List[str], payload: numpy.array, timestamps: numpy.ndarray)
```
Give it a sensor name (sensor_name), metadata (metadata), the data (payload), the timestamps in microseconds since epoch utc (timestamps)

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

    # Changing values
    light_sensor_channel.set_sensor_name("Example Light")
    light_sensor_channel.timestamps_microseconds_utc([1, 3, 42, 8492, 9001])

    # Setting_values
    light_sensor_channel.create_light("Example Light", ["meta", "data"], [1, 2, 3, 4, 5], [1, 10, 100, 1000, 10000])
    light_sensor_channel = LightSensor().create_light("Example Light", ["meta", "data"], [1, 2, 3, 4, 5], [1, 10, 100, 1000, 10000])
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

```
create_infrared(sensor_name: str, metadata: typing.List[str], payload: numpy.array, timestamps: numpy.ndarray)
```
Give it a sensor name (sensor_name), metadata (metadata), the data (payload), the timestamps in microseconds since epoch utc (timestamps)

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

    # Changing values
    infrared_sensor_channel.set_sensor_name("Example Infrared")
    infrared_sensor_channel.timestamps_microseconds_utc([1, 3, 42, 8492, 9001])

    # Setting values
    infrared_sensor_channel.create_infrared("Example Infrared", ["meta", "data"], [1, 2, 3], [1, 10, 100])
    infrared_sensor_channel = InfraredSensor().create_infrared("Example Infrared", ["meta", "data"], [1, 2, 3], [1, 10, 100])
```

### Working with image sensor channels

It's possible to test for the availability of this sensor in a data packet by calling the method `has_image_channel` on an instance of a `WrappedRedvoxPacket`.

The sensor can be accessed from an instance of a `WrappedRedvoxPacket` by calling the method `image_channel`. `None` is returned if the data packet does not have a channel of this sensor type.

The `ImageSensor` class contains methods for directly accessing the fields and payloads of image channels. The following table briefly describes the available methods for infrared sensor channels.

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| set_timestamps_microseconds_utc(numpy.ndarray[int]) | | Sets the timestamps |
| sensor_name() | str | Returns the name of the sensor for this sensor channel |
| set_sensor_name(str) | | Sets the name of the sensor for this sensor channel |
| payload_values() | numpy.ndarray[float] | A numpy array of floats representing the data payload from this packet's image channel |
| sample_interval_mean() | float | The mean of the sample interval for samples in this packet |
| sample_interval_median() | float | The median of the sample interval for samples in this packet |
| sample_interval_std() | float | The standard deviation of the sample interval for samples in this packet |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |
| metadata() | List[str] | Returns this channel's metadata |
| set_metadata(List[str]) | | Sets this channel's metadata |
| payload_type() | str | Return this channel's internal protobuf type as a string |
| num_images() | img | Return the number of images in this channel |
| get_image_offsets() | List[int] | Return a list of byte offsets into this channel's payload where each byte offset represents the starting byte of an image |
| get_image_bytes(idx: int) | numpy.ndarray (uint8) | Returns the bytes associated with the image at this given index (0 indexed) |
| write_image_to_file(idx: int, path: str) | | Writes the image stored at the given index to the given path on disk |
| write_all_images_to_directory(directory: str) | | Writes all available images in this packet to the given directory using a default name for each image |

##### Creating an image sensor
This function creates an image sensor:

```
create_image(sensor_name: str, metadata: typing.List[str], payload: numpy.array, timestamps: numpy.ndarray)
```
Give it a sensor name (sensor_name), metadata (metadata), the data (payload), the timestamps in microseconds since epoch utc (timestamps)

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

    # Changing values
    image_sensor_channel.set_sensor_name("Example Image")
    image_sensor_channel.timestamps_microseconds_utc([1, 3, 42, 8492, 9001])

    # Setting values
    image_sensor_channel.create_image("Example Image", ["images", "0"], [1, 2, 3], [1, 10, 100])
    image_sensor_channel = ImageSensor().create_image("Example Image", ["images", "0"], [1, 2, 3], [1, 10, 100])
```

### Low Level Access
There are many small parts that come together to form a redvox packet.  Many of these are related to the protobuf format.

##### Protobuf
A protobuf is a data container.  A redvox protobuf contains several fields that are replicated in python for easy access.  The python fields are:

| Name | Type | Description |
|------|------|-------------|
| sensor_name | str | The name of the sensor. |
| payload | numpy.ndarray | The payload as a numpy array. The payload type is one of many number types. |
| channel_types | List[api900_pb2.EvenlySampledChannel or api900_pb2.UnevenlySampledChannel] | The types of channels in the payload. |
| value_means | numpy.ndarray | The means of each channel in the payload. |
| value_stds | numpy.ndarray | The standard deviations of each channel in the payload. |
| value_medians | numpy.ndarray | The medians of each channel in the payload. |
| metadata | List[str] | Metadata of payload. |

##### Payloads
A protobuf payload is an array of numbers.  All numbers in the array have the same type, and payloads are stored in protobuf.TYPE.payload where TYPE is one of the following:

| Name | Description |
|------|-------------|
| byte_payload | Bytes |
| uint32_payload | Unsigned integer, 32 bits (0 - 4,294,967,295) |
| uint64_payload | Unsigned integer, 64 bits (0 - 18,446,744,073,709,551,615) |
| int32_payload | Signed integer, 32 bits (-2,147,483,648 - 2,147,483,647) |
| int64_payload | Signed integer, 64 bits (-9,223,372,036,854,775,808 - 9,223,372,036,854,775,807) |
| float32_payload | Signed float, 32 bits (-3.4E+38 to 3.4E+38) |
| float64_payload | Signed float, 64 bits (-1.8E+308 to 1.8E+308 |

Redvox uses int32 for microphone data, int64 for timestamps, and float64 for all other payload data.  Payloads are easy to manipulate when converted into python arrays.  Writing to the protobuf object is not as simple, and requires knowledge of the data type to correctly store them.  We recommend using set_payload() or set_deinterleaved_payload() to store payloads.

##### Channel Types
Channel types are defined in api900.proto and signify where the data is coming from.  The table below lists the supported channel types and their internal integer values:

| Protobuf Name | Integer Value | Description |
|---------------|---------------|-------------|
| MICROPHONE | 0 | Microphone |
| BAROMETER | 1 | Barometer |
| LATITUDE | 2 | Latitude |
| LONGITUDE | 3 | Longitude |
| SPEED | 4 | Speed |
| ALTITUDE | 5 | Altitude
| TIME_SYNCHRONIZATION | 9 | Time Synchronization |
| ACCURACY | 10 | Accuracy |
| ACCELEROMETER_X | 11 | Accelerometer X axis |
| ACCELEROMETER_Y | 12 | Accelerometer Y axis |
| ACCELEROMETER_Z | 13 | Accelerometer Z axis |
| MAGNETOMETER_X | 14 | Magnetometer X axis |
| MAGNETOMETER_Y | 15 | Magnetometer Y axis |
| MAGNETOMETER_Z | 16 | Magnetometer Z axis |
| GYROSCOPE_X | 17 | Gyroscope X axis |
| GYROSCOPE_Y | 18 | Gyroscope Y axis |
| GYROSCOPE_Z | 19 | Gyroscope Z axis |
| OTHER | 20 | Other |
| LIGHT | 21 | Light |
| IMAGE | 22 | Image |
| INFRARED | 23 | Infrared |

When working with channel types, redvox uses the integer value to save space.  A protobuf may contain more than one channel type.  They can be alternately represented by importing the api900_pb2 module from the redvox.api900 library.  Once imported, you can refer to a channel using api900_pb2.CHANNEL_NAME where CHANNEL_NAME is one of the values in all capital letters in the above table.  EX: api900_pb2.MICROPHONE refers to a microphone channel.

##### Interleaving
Payloads may contain more than one channel, and each channel has its own data array, however the actual payload is only one array.  This requires the payload to be interleaved.  For example, a GPS will produce a LATITUDE, LONGITUDE, ALTITUDE, and SPEED values with every update.  For this GPS sensor, the channel_types array would look like [LATITUDE, LONGITUDE, ALTITUDE, SPEED]. The location of the channel type in channel_types determines the offset into the payload and the length of channel_types determines the step size. As such, this hypothetical GPS channel payload is encoded as:
[LAT0, LNG0, ALT0, SPD0, LAT1, LNG1, ALT1, SPD1, ..., LATn, LNGn, ALTn, SPDn] where 0-n is the index of a timestamp.

##### Building a Sensor
A sensor contains one or more channels.  All channels must be either evenly or unevenly sampled; no mixing of the types allowed.  Sensors have access to high level properties of channels, but generally do not have the ability to set or alter those properties.  In order to set or alter the properties of a channel, you must access it directly.  I.E. MicSensor.evenly_sampled_channel.set_payload(...)
To set all the sensor's data at once, you may use its set_channel function, create it using another sensor as an argument or by calling its create_SENSOR statement.  I.E. MicSensor.set_channel(MainMicSensor.evenly_sampled_channel) and MicSensor = MicrophoneSensor(MainMicSensor) both do the same thing: set MicSensor's properties to be a copy of MainMicSensor's.  MicSensor.create_microphone(...) will set MicSensor's properties to the values passed into the function.  new_mic_sensor = MicSensor().create_microphone(...) will also set new_mic_sensor's properties to the values passed into the function.  Refer to the relevant sensor's section for more information about what values to give the function.

##### Functions
These functions allow you to work with the protobuf and its payload.
| Name | Requirements | Description |
|------|--------------|-------------|
| set_payload(channel, step, pl_type) | Interleaved array (channel: numpy.array), the number of arrays interleaved (step: int), the payload type (pl_type: str) | Sets the payload. |
| set_deinterleaved_payload(channels, pl_type) | A list of arrays, all the same size, to interleave (channels: List[numpy.array]), the payload type (pl_type: str) | Sets the payload. |
| set_channel_types(types) | A list of channel types (types: List[Channel Types]) | Sets the channel types. |
| update_stats() | Payload and channel types have been set | Updates the value_means, value_stds and value_medians of the payload. |
| set_sensor_name(name) | Sensor name (name: str) | Sets the name of the sensor. |
| set_metadata(data) | A list of metadata (data: list[str]) | Sets the metadata. |
| set_sample_rate_hz(rate) | A sample rate in Hz (rate: float) | Evenly sampled channels only.  Sets the constant sample rate of an evenly sampled channel. |
| set_first_sample_timestamp_epoch_microseconds_utc(time) | The first timestamp of the data in microseconds since epoch utc (time: int) | Evenly sampled channels only.  Sets the starting timestamp of an evenly sampled channel. |
| set_timestamps_microseconds_utc(timestamps) | A list of timestamps in microseconds since epoch utc (timestamps: numpy.ndarray) | Unevenly sampled channels only.  Sets the list of timestamps of the samples for this channel. |
| set_channel(channel) | Another protobuf channel (channel: varies) | Sets the current channel to be a copy of the argument. Refer to notes below. |
set_channel may be called at different levels; if called from a sensor, it requires the channel of another sensor.  I.E. MicSensor.set_channel(MainMicSensor.evenly_sampled_channel).  If called from a channel, it requires a protobuf channel.  I.E. BarChannel.set_channel(MainBarChannel.protobuf_channel).  Furthermore, evenly sampled channels should only be set to other evenly sampled channels and unevenly sampled channels should only be set to other unevenly sampled channels.
