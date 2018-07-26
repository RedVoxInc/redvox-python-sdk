## Redvox API 900 SDK Documentation

The RedVox SDK is written in Python 3.6+ and provides utility classes, methods, and functions for working with RedVox API 900 data. The API 900 standalone reader provides functionality for easily accessing all packet fields and sensor payloads within individual API 900 packets. The API 900 reader does not perform queries over multiple data sets of aggregation of data.

The Redvox API 900 utilizes Google's protobuf library for serializing and deserializing data between devices. It's possible to interact with API 900 data directly by selecting a pre-compiled language wrapper at https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/generated_code/ and including the wrapper in your software project. These wrappers provide all the functionality required for creating and reading Redvox API 900 files. The low level API 900 data format is described and documented in detail at: https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/doc/api900/api900.md?at=master&fileviewer=file-view-default

### Prerequisites

TODO

### Loading RedVox API 900 Files

The module `redvox/api900/reader.py` contains two functions for loading RedVox API 900 data files: `read_buffer` and `read_file`.

`read_buffer` accepts an array of bytes which represent a serialized RedVox data packet and returns a `WrappedRedvoxPacket`. `read_file` accepts the path to a RedVox data packet file stored somewhere on the file system and also returns a `WrappedRedvoxPacket`.

A `WrappedRedvoxPacket` is a Python class that acts as a wrapper around the raw protobuf API and provides convenience methods for accessing fields and sensor channels of the loaded RedVox packet.

The following is a table that summarizes the fields and methods provided by the WrappedRedvoxPacket class.

| Name | Type | Description |
| -----|------|-------------|
| redvox_packet | api900_pb2.RedvoxPacket | The original low-level protobuf packet. |
| evenly_sampled_channels | List[EvenlySampledChannel] | List of mid-level wrapped evenly sampled channels |
| unevenly_sampled_channels | List[UnevenlySampledChannel] | List of mid-level wrapped unevenly sampled channels |
| metadata | List[str] | List of packet level metadata. |
| _channel_cache | Dict[int, Union[UnevenlySampledChannel, EvenlySampledChannel]] | Contains a hashmap mapping from channel type to channel which provides O(1) access to sensor data once the cache is created |
| microphone_channels | List[MicrophoneSensor] | Contains a list of high-level microphone sensor channels contains in this packet |
| barometer_channels | List[BarometerSensor] | Contains a list of high-level barometer sensor channels contains in this packet |
| location_channels | List[LocationSensor] | Contains a list of high-level location sensor channels contains in this packet |
| time_synchronization | List[TimeSynchronizationSensor] | Contains a list of high-level time synchronization sensor channels contains in this packet |
| magnetometer_channels | List[MagnetometerSensor] | Contains a list of high-level magnetometer sensor channels contains in this packet |
| gyroscope_channels | List[GyroscopeSensor] | Contains a list of high-level gyroscope sensor channels contains in this packet |
| light_channels | List[LightSensor] | Contains a list of high-level lightj sensor channels contains in this packet |


Note that for the lists of channels, an empty list indicates that a particular RedVox packet does not contain any data for that channel list.

##### Example loading RedVox data

TODO

### Working with microphone sensor channels

Microphone sensors can be accessed from `WrappedRedvoxPacket` objects by accessing the member `microphone_sensors`. Each microphone sensor on the device will show up in this list. If there is only one microphone, there will only be a single item in the list. If there are no microphone sensors for a packet, then the list will be empty.

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

##### Example microphone sensor reading

TODO

### Working with barometer sensor channels

Barometer sensors can be accessed from `WrappedRedvoxPacket` objects by accessing the member `barometer_sensors`. Each barometer sensor on the device will show up in this list. If there is only one barometer, there will only be a single item in the list. If there are no barometer sensors for a packet, then the list will be empty.

The `BarometerSensor` class contains methods for directly accessing the fields and payloads of barometer channels. The following table briefly describes the available methods for barometer sensor channels.

| Name | Type | Description | 
|------|------|-------------|
| timestamps_microseconds_utc() | numpy.ndarray[int] | A numpy array of timestamps, where each timestamp is associated with a sample from this channel. For example, timestamp[0] is associated with payload[0], timestamp[1] w/ payload[1], etc. |
| sensor_name() | str | Returns the name of the sensor for this microphone sensor channel |
| payload_values() | numpy.ndarray[float] | A numpy array of floats representing the data payload from this packet's barometer channel |
| payload_mean() | float | The mean value of this packet's barometer data payload |
| payload_median() | float | The median value of this packet's barometer data payload |
| payload_std() | float | The standard deviation of this packet's barometer data payload |
| sample_interval_mean() | float | The mean of the sample interval for samples in this packet |
| sample_interval_mean() | float | The median of the sample interval for samples in this packet |
| sample_interval_mean() | float | The standard deviation of the sample interval for samples in this packet |
| metadata_as_dict() | Dict[str, str] | Returns this channel's metadata as a Python dictionary |

##### Example microphone sensor reading

TODO

### API Documentation

Generated API documentation can be found at: TODO