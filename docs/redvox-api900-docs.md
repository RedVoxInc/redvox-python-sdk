### Redvox API 900 SDK Documentation

The RedVox SDK is written in Python 3.6+ and provides utility classes, methods, and functions for working with RedVox API 900 data. The API 900 standalone reader provides functionality for easily accessing all packet fields and sensor payloads within individual API 900 packets. The API 900 reader does not perform queries over multiple data sets of aggregation of data.

The Redvox API 900 utilizes Google's protobuf library for serializing and deserializing data between devices. It's possible to interact with API 900 data directly by selecting a pre-compiled language wrapper at https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/generated_code/ and including the wrapper in your software project. These wrappers provide all the functionality required for creating and reading Redvox API 900 files. The low level API 900 data format is described and documented in detail at: https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/doc/api900/api900.md?at=master&fileviewer=file-view-default

### Prerequisites

TODO

### Loading RedVox API 900 Files

The module `redvox/api900/reader.py` contains two functions for loading RedVox API 900 data files: `read_buffer` and `read_file`.

`read_buffer` accepts an array of bytes which represent a serialized RedVox data packet and returns a `WrappedRedvoxPacket`. `read_file` accepts the path to a RedVox data packet file stored somewhere on the file system and also returns a `WrappedRedvoxPacket`.

A `WrappedRedvoxPacket` is a Python class that acts as a wrapper around the raw protobuf API and provides convenience methods for accessing fields and sensor channels of the loaded RedVox packet.

The following is a table that summarizes the fields and methods provided by the WrappedRedvoxPacket class.

| Name | Field/Method | Type | Description |
| -----|--------------|------|-------------|
| redvox_packet | Field | api900_pb2.RedvoxPacket | The original low-level protobuf packet. |
| evenly_sampled_channels | Field | List[EvenlySampledChannel] | List of mid-level wrapped evenly sampled channels |
| unevenly_sampled_channels | Field | List[UnevenlySampledChannel] | List of mid-level wrapped unevenly sampled channels |
| metadata | Field | List[str] | List of packet level metadata. |
| _channel_cache | Field | Dict[int, Union[UnevenlySampledChannel, EvenlySampledChannel]] | Contains a hashmap mapping from channel type to channel which provides O(1) access to sensor data once the cache is created |
| microphone_channels | Field | List[MicrophoneSensor] | Contains a list of high-level microphone sensor channels contains in this packet |
| barometer_channels | Field | List[BarometerSensor] | Contains a list of high-level barometer sensor channels contains in this packet |
| location_channels | Field | List[LocationSensor] | Contains a list of high-level location sensor channels contains in this packet |
| time_synchronization | Field | List[TimeSynchronizationSensor] | Contains a list of high-level time synchronization sensor channels contains in this packet |
| magnetometer_channels | Field | List[MagnetometerSensor] | Contains a list of high-level magnetometer sensor channels contains in this packet |
| gyroscope_channels | Field | List[GyroscopeSensor] | Contains a list of high-level gyroscope sensor channels contains in this packet |
| light_channels | Field | List[LightSensor] | Contains a list of high-level light sensor channels contains in this packet |


Note that for the lists of channels, an empty list indicates that a particular RedVox packet does not contain any data for that channel list.

### API Documentation

Generated API documentation can be found at: TODO