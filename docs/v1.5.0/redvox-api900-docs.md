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
* [Working with WrappedRedvoxPackets](#markdown-header-working-with-wrappedredvoxpacket-objects)
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
8 [Modifying and creating WrappedRedvoxPacket objects and sensor channels](#markdown-header-modifying-and-creating-wrappedredvoxpacket-objects-and-sensor-channel)
* [Example files](#markdown-header-example-files)
* [Generated API Documentation](#markdown-header-generated-api-documentation)
* [Developer Guidelines](#markdown-header-developer-guidelines)

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

You can convert a single .rdvxz file to json with a command like:

`python3 -m redvox.api900.cli to_json example_data/example.rdvxz`

You can convert multiple .rdvxz files in the same directory to json with a command like:

`python3 -m redvox.api900.cli to_json example_data/*.rdvxz`

##### Example: Converting RedVox compliant API 900 .json files to .rdvxz files

You can convert a single RedVox AIP 900 compliant json file to .rdvxz with a command like:

`python3 -m redvox.api900.cli to_rdvxz example_data/example.json`

You can convert multiple RedVox AIP 900 compliant json files to .rdvxz with a command like:

`python3 -m redvox.api900.cli to_rdvxz example_data/*.json`

##### Example: Displaying the contents of .rdvxz files

You can display the contents of a single .rdvxz file with:

`python3 -m redvox.api900.cli print example_data/example.rdvxz`

You can display the contents of multiple .rdvxz files with:

`python3 -m redvox.api900.cli print example_data/*.rdvxz`

### Loading RedVox API 900 Files

The module `redvox/api900/reader.py` contains several high-level methods for reading RedVox API 900 .rdvxz files and RedVox API 900 compliant .json files. These methods all return an instance of a [WrappedRedvoxPacket](#markdown-header-working-with-wrappedrevoxpacket-ojects).

These methods are `read_rdvxz_file`, `read_rdvxz_buffer`, `read_json_file`, and `read_json_string`.

Descriptions of these methods can be found at: https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/api_docs/redvox/api900/reader.m.html#header-functions

Examples of the usage can be found at: https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_reading.py

### Working with WrappedRedvoxPacket objects

A WrappedRedvoxPacket is a high-level API that is backed by a protobuf buffer. The high-level API provides getters and setters for all fields and sensor channels that the RedVox API 900 provides.

To see a list of all getters and setters that a WrappedRedvoxPacket provides, please see: https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/api_docs/redvox/api900/reader.m.html#redvox.api900.reader.WrappedRedvoxPacket

To check if a sensor channel is in a packet, you can use any of the `has_channel` methods.

When accessing a sensor channel (e.g. microphone_channel()), if the channel does not exist in the packet, the sensor channel getter will return `None`.

Channels can be removed from a packet by passing `None` to a `set_channel` method.

Examples of reading/writing to/from WrappedRedvoxPacket objects can be found at:

* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_reading.py
* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_modifcation.py
* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_creation.py

The contents of WrappedRedvoxPacket objects can be written to .rdvxz or RedVox API 900 compliant .json files. See https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_writing.py for examples.

### Working with microphone sensor channels

MicrophoneSensor channels are an evenly sampled sensor that contain microphone data in a single payload. The payload represents counts from the microphone. Payloads are represented by integers. 

See https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/api_docs/redvox/api900/reader.m.html#redvox.api900.reader.MicrophoneSensor for a list of methods this sensor provides.

See the following for example usage:

* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_creation.py 
* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_reading.py 


### Working with barometer sensor channels

BarometerSensor channels are an unevenly sampled sensor that contain barometer data in a single payload. UnevenlySampled sampled sensors contain a list of timestamps that correspond to each sample.

See https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/api_docs/redvox/api900/reader.m.html#redvox.api900.reader.BarometerSensor for a list of methods this sensor provides.

See the following for example usage:

* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_creation.py 
* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_reading.py

### Working with location sensor channels

LocationSensor channels are an unevenly sampled sensor that contain location data with 5 payloads. UnevenlySampled sampled sensors contain a list of timestamps that correspond to each sample.

The payload types available to the LocationSensor include:

* latitude
* longitude
* altitude
* speed
* accuracy

This sensor also provides mean, median, and std statistics for each payload type.

See https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/api_docs/redvox/api900/reader.m.html#redvox.api900.reader.LocationSensor for a list of methods this sensor provides.

See the following for example usage:

* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_creation.py 
* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_reading.py

### Working with time synchronization sensor channels

TimeSynchronizationSensor channels are an unevenly sampled sensor that contain time synchronization data in a single payload.

This sensor is unique in that is only contains a payload of values and no timestamps or other fields. 

See https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/api_docs/redvox/api900/reader.m.html#redvox.api900.reader.TimeSynchronizationSensor for a list of methods this sensor provides.

See the following for example usage:

* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_creation.py 
* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_reading.py

### Working with accelerometer sensor channels

AccelerometerSensor channels are an unevenly sampled sensor that contain accelerometer data in 3 payloads. UnevenlySampled sampled sensors contain a list of timestamps that correspond to each sample.

The three payloads are:

* x
* y
* z

Further, each payload type has its own set of mean, median, and std statistics.

See https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/api_docs/redvox/api900/reader.m.html#redvox.api900.reader.AccelerometerSensor for a list of methods this sensor provides.

See the following for example usage:

* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_creation.py 
* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_reading.py

### Working with magnetometer sensor channels

MagnetometerSensor channels are an unevenly sampled sensor that contain magnetometer data in 3 payloads. UnevenlySampled sampled sensors contain a list of timestamps that correspond to each sample.

The three payloads are:

* x
* y
* z

Further, each payload type has its own set of mean, median, and std statistics.

See https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/api_docs/redvox/api900/reader.m.html#redvox.api900.reader.MagnetometerSensor for a list of methods this sensor provides.

See the following for example usage:

* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_creation.py 
* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_reading.py

### Working with gyroscope sensor channels

GyrocopeSensor channels are an unevenly sampled sensor that contain gyroscope data in 3 payloads. UnevenlySampled sampled sensors contain a list of timestamps that correspond to each sample.

The three payloads are:

* x
* y
* z

Further, each payload type has its own set of mean, median, and std statistics.

See https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/api_docs/redvox/api900/reader.m.html#redvox.api900.reader.GyroscopeSensor for a list of methods this sensor provides.

See the following for example usage:

* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_creation.py 
* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_reading.py


### Working with light sensor channels

LightSensor channels are an unevenly sampled sensor that contain light data in a single payload. UnevenlySampled sampled sensors contain a list of timestamps that correspond to each sample.

See https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/api_docs/redvox/api900/reader.m.html#redvox.api900.reader.LightSensor for a list of methods this sensor provides.

See the following for example usage:

* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_creation.py 
* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_reading.py

### Working with infrared sensor channels

InfraredSensor channels are an unevenly sampled sensor that contain infrared data in a single payload. UnevenlySampled sampled sensors contain a list of timestamps that correspond to each sample.

See https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/api_docs/redvox/api900/reader.m.html#redvox.api900.reader.InfraredSensor for a list of methods this sensor provides.

See the following for example usage:

* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_creation.py 
* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_reading.py


### Modifying and Creating WrappedRedvoxPacket Objects and Sensor Channels

It's possible to modify WrappedRedvoxPacket objects and sensor channels as well as create new WrappedRedvoxPacket objects and sensor channels. See the following links for examples:

* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_creation.py 
* https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_modifcation.py

### Testing for Equality and Finding Differences

WrappedRedvoxPacket objects can be compared to each other for equality using the `==` operator. The same is true for comparing sensor channels.

It's also possible to find the differences between WrappedRedvoxPacket objects using the `.diff(other_packer)` method. This will then return a list of differences between the two files or an empty list if there are none.

See the end of https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/example_packet_reading.py for examples of this.

### Example files

A set of example files can be found at: https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/examples/

### Generated API documentation

API documentation for this library can be found at: https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/api_docs/redvox

*Note: to see type information for a particular function, click the `SHOW SOURCE` button.*

### Developer Guidelines

If you plan on making changes to the library, please follow these guidelines.

1. Please perform all work in a separate branch.
2. Ensure all unit tests pass before committing. This can be achieved by running `python3 -m unittest discover` in the root of this project.
3. Ensure all linting checks pass before committing. This requires the pip package `coala-bears` and can be performed by running `coala --ci` in the root of this project.
4. Update the version number in redvox/__init__.py. This project uses [Semantic Versioning](https://semver.org/).
5. Do not introduce backwards incompatible changes unless absolutely necessary.
6. Create a new set of documentation in the docs/ directory that matches the new version. 
7. Update the developer documentation, API documentation, and examples with your new changes.
8. Either create a pull request from your branch (if forked) or check with one of us before attempting to merge changes into master.
 