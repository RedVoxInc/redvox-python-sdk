# <img src="../../img/redvox_logo.png" height="25"> **RedVox Python SDK Station and SensorData Manual**

The RedVox Python SDK contains routines for reading, creating, and writing RedVox API 900 and RedVox API 1000 data 
files. The SDK is open-source.

Station is a Python class designed to store format-agnostic station and sensor data.  Its primary goal is to represent 
RedVox data, but it is capable of representing a variety of station and sensor configurations.

## Table of Contents

<!-- toc -->

- [Station](#station)
  * [Station Properties](#station-properties)
  * [Station Functions](#station-functions)
  * [Using Station](#using-station)
  * [Station Metadata](#station-metadata)
  * [Station Packet Metadata](#station-packet-metadata)
  * [Timesync and Offset Model](#timesync-and-offset-model)
- [Sensor Data](#sensor-data)
  * [Sensor Data Properties](#sensor-data-properties)
  * [Sensor Data Functions](#sensor-data-functions)
  * [Sensor Data DataFrame Access](#sensor-data-dataframe-access)
    + [A note on enumerated types](#a-note-on-enumerated-types)
  * [Using Sensor Data](#using-sensor-data)

<!-- tocstop -->

## Station

Station is a module designed to hold format-agnostic data of various sensors that combine to form a single unit. 
The data can be gathered from and turned into various other formats as needed.

Station represents real world combinations of various recording devices such as audio, accelerometer, and pressure sensors. 
Stations will not contain more than one of the same type of sensor; this is to allow unambiguous and easy comparison between stations.

Station objects are comprised of a station key, the sensor data, data packet metadata, and other station specific metadata.

Each Station has a unique key.  Keys are comprised of the Station's id, uuid, start timestamp since epoch UTC and the station's metadata. 
Stations with the same key can be combined into one Station to simplify results.

Stations will do their best to fill any gaps that can be detected in the data.

Refer to the [Station API documentation](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/station.html) as needed.

_[Table of Contents](#table-of-contents)_

### Station Properties

These are the properties of the Station class and their default values:
1. `id`: string; id of the station, default None
2. `uuid`: string; uuid of the station, default None
3. `data`: dictionary of sensor type and sensor data associated with the station, default empty dictionary
4. `metadata`: StationMetadata that didn't go into the sensor data, default empty StationMetadata object
6. `packet_metadata`: list of StationPacketMetadata that changes from packet to packet, default empty list
7. `start_timestamp`: float; microseconds since epoch UTC when the station started recording, default np.nan
7. `first_data_timestamp`: float; microseconds since epoch UTC of the first data point, default np.nan
8. `station_end_timestamp`: float; microseconds since epoch UTC of the last data point, default np.nan
9. `audio_sample_rate_nominal_hz`: float of nominal sample rate of audio component in hz, default np.nan
10. `is_audio_scrambled`: boolean; True if audio data is scrambled, default False
11. `is_timestamps_updated`: boolean; True if timestamps have been altered from original data values, default False
12. `timesync_analysis`: TimeSyncAnalysis object; contains information about the station's timing values.  Refer to 
    the [Timesync Documentation](#timesync-and-offset-model) for more information
13. `use_model_correction`: boolean, if True, time correction is done using OffsetModel functions, otherwise
    correction is done by adding the best offset from the OffsetModel (also known as the model's intercept value or
    the best offset from TimeSyncAnalysis).  default True
14. `errors`: RedVoxExceptions, class containing a list of all errors encountered when creating the station.  This is set by the SDK.

_[Table of Contents](#table-of-contents)_

### Station Functions

These are the functions of the Station class:
1. `get_mean_packet_duration()`: Returns the mean duration of audio samples in the data packets used to create the Station.
2. `get_mean_packet_audio_samples()`: Returns the mean number of audio samples per data packet used to create the Station.
3. `append_station(new_station)`: Adds the data from the new_station to the calling Station, if the keys of both Stations are the same.
   If the keys are different or one of the keys is invalid, nothing happens.
4. `has_timesync_data()`: Returns True if the Station has timesync data 
5. `get_station_sensor_types()`: Returns a list of all sensor types in the Station
6. `print_errors()`: Print the errors encountered when creating the Station

_[Table of Contents](#table-of-contents)_

### Using Station

The table below shows the sensor name and the function calls required to access, set, and check for the sensor.

|Sensor Name         |Accessor Function            |Exists                           |Has Data                       |Setter |
|--------------------|-----------------------------|---------------------------------|-------------------------------|-------|
|audio               |audio_sensor()               |has_audio_sensor()               |has_audio_data()               |set_audio_sensor() |
|compressed audio    |compressed_audio_sensor()    |has_compressed_audio_sensor()    |has_compressed_audio_data()    |set_compressed_audio_sensor() |
|image               |image_sensor()               |has_image_sensor()               |has_image_data()               |set_image_sensor() |
|pressure            |pressure_sensor()            |has_pressure_sensor()            |has_pressure_data()            |set_pressure_sensor() |
|light               |light_sensor()               |has_light_sensor()               |has_light_data()               |set_light_sensor() |
|proximity           |proximity_sensor()           |has_proximity_sensor()           |has_proximity_data()           |set_proximity_sensor() |
|ambient temperature |ambient_temperature_sensor() |has_ambient_temperature_sensor() |has_ambient_temperature_data() |set_ambient_temperature_sensor() |
|relative humidity   |relative_humidity_sensor()   |has_relative_humidity_sensor()   |has_relative_humidity_data()   |set_relative_humidity_sensor() |
|accelerometer       |accelerometer_sensor()       |has_accelerometer_sensor()       |has_accelerometer_data()       |set_accelerometer_sensor() |
|magnetometer        |magnetometer_sensor()        |has_magnetometer_sensor()        |has_magnetometer_data()        |set_magnetometer_sensor() |
|linear acceleration |linear_acceleration_sensor() |has_linear_acceleration_sensor() |has_linear_acceleration_data() |set_linear_acceleration_sensor() |
|orientation         |orientation_sensor()         |has_orientation_sensor()         |has_orientation_data()         |set_orientation_sensor() |
|rotation vector     |rotation_vector_sensor()     |has_rotation_vector_sensor()     |has_rotation_vector_data()     |set_rotation_vector_sensor() |
|gyroscope           |gyroscope_sensor()           |has_gyroscope_sensor()           |has_gyroscope_data()           |set_gyroscope_sensor() |
|gravity             |gravity_sensor()             |has_gravity_sensor()             |has_gravity_data()             |set_gravity_sensor() |
|location            |location_sensor()            |has_location_sensor()            |has_location_data()            |set_location_sensor() |
|best location       |best_location_sensor()       |has_best_location_sensor()       |has_best_location_data()       |set_best_location_sensor() |
|station health      |health_sensor()              |has_health_sensor()              |has_health_data()              |set_health_sensor() |

*** Some stations may use alternate names for their sensors instead of the ones listed above.
The functions do not change if the sensor's name changes (i.e. you still use audio_sensor() to access the microphone sensor and its data)  
Common replacements are:
* microphone instead of audio
* barometer instead of pressure
* infrared instead of proximity

Refer to the [SensorData](#sensor-data) section on how to access the data.

We recommend only reading information from the Station objects.  
Setting or changing any of the properties in Station or the sensors may cause unexpected results.

_Example:_
```python
from redvox.common.data_window import DataWindow
from redvox.common.station import Station

dw = DataWindow(input_dir_str)

my_station: Station = dw.get_station("id01")[0]

my_id = my_station.id
first_timestamp = my_station.first_data_timestamp
last_timestamp = my_station.last_data_timestamp
mean_packet_duration = my_station.get_mean_packet_duration()
if my_station.has_audio_sensor():
    audio_sensor = my_station.audio_sensor()
```

_[Table of Contents](#table-of-contents)_

### Station Metadata

StationMetadata is the properties of a station that do not change while the station is on.  Any change in the metadata 
usually signals a change in the station.

Please note that while the properties id, uuid, start_timestamp, audio_sample_rate_nominal_hz, and is_audio_scrambled 
are technically metadata, they are very important to identifying the station and must be quickly and easily available 
to read.  Therefore, they exist directly within Station.

These are the properties of the StationMetadata class and their default values:
1. `api`: float; api version, default np.nan
2. `sub_api`: float; sub api version, default np.nan
3. `make`: string; station make, default empty string
4. `model`: string; station model, default empty string
5. `os`: OsType enumeration; station OS, default OsType.UNKNOWN_OS
6. `os_version`: string; station OS version, default empty string
7. `app`: string; station app, default empty string
8. `app_version`: string; station app version, default empty string
9. `is_private`: boolean; is station data private, default False
10. `packet_duration_s`: float; duration of the packet in seconds, default np.nan
11. `station_description`: string; description of the station, default empty string
12. `other_metadata`: dictionary of string to string of other metadata from the packet, default empty list

We recommend only reading information from the StationMetadata objects.  
Setting or changing any of the properties in StationMetadata may cause unexpected results.

_Example:_
```python
from redvox.common.data_window import DataWindow
from redvox.common.station import Station

dw = DataWindow(input_dir_str)

my_station: Station = dw.get_station("id01")[0]

my_metadata = my_station.metadata
print(my_metadata.make)
print(my_metadata.model)
print(my_metadata.station_description)
print(my_metadata.packet_duration_s)
```

_[Table of Contents](#table-of-contents)_

### Station Packet Metadata

StationPacketMetadata is the properties of the packets that contain the station's data that change between packets.

These are the properties of the StationPacketMetadata class and their defaults:
1. `packet_start_mach_timestamp`: float; machine timestamp of packet start in microseconds since epoch UTC
2. `packet_end_mach_timestamp`: float; machine timestamp of packet end in microseconds since epoch UTC
3. `packet_start_os_timestamp`: float; os timestamp of packet start in microseconds since epoch UTC
4. `packet_end_os_timestamp`: float; os timestamp of packet end in microseconds since epoch UTC
5. `timing_info_score`: float; quality of timing information
6. `other_metadata`: dictionary of string to string of other metadata from the packet, default empty list

We recommend only reading information from the StationPacketMetadata objects.  
Setting or changing any of the properties in StationPacketMetadata may cause unexpected results.

_Example:_
```python
from redvox.common.data_window import DataWindow
from redvox.common.station import Station

dw = DataWindow(input_dir_str)

my_station: Station = dw.get_station("id01")[0]

for packet in my_station.packet_metadata:
  print(packet.packet_start_mach_timestamp)
  print(packet.packet_end_mach_timestamp)
```

_[Table of Contents](#table-of-contents)_

### Timesync and Offset Model

The timesync_analysis property of Station contains information about the clock synchronization.
The information is stored as a TimeSyncAnalysis object.

The TimeSyncAnalysis class has a few properties and functions that summarize the timing information of the station.

1. get_best_latency(): Returns the best (lowest) latency of the station
2. get_latencies(): Returns a numpy.array of all latencies of the station
3. latency_stats: StatsContainer; the statistics (mean, std deviation and variance) of the latencies
4. get_best_offset(): Returns the best (corresponding to best latency) offset of the station
5. get_offsets(): Returns a numpy.array of all the offsets of the station
6. offset_stats: StatsContainer; the statistics of the offsets
7. sample_rate_hz: float; the audio sample rate in hz of the station, default np.nan
8. timesync_data: list of TimeSyncData; the TimeSyncData being analyzed, default empty list
9. station_start_timestamp: float; the timestamp of when the station became active, default np.nan
10. offset_model: OffsetModel; model used to calculate offset of the station at a given point in time, default empty model
    See below for more information about OffsetModel

OffsetModel is the primary source for information used to correct the Station's timestamps.

The OffsetModel computes the slope, or change in offset, for the duration of the Station's data, as well as the 
best offset value, or intercept, at the first timestamp of the audio data.

These are the properties of the OffsetModel class and their default values:
1. `start_time`: float; start timestamp of model in microseconds since epoch UTC
2. `end_time`: float; end timestamp of model in microseconds since epoch UTC
3. `k_bins`: int; the number of data bins used to create the model, default is 1 if model is empty
4. `n_samples`: int; the number of samples per data bin; default is 3 (minimum to create a balanced line)
5. `slope`: float; the slope of the change in offset
6. `intercept`: float; the offset at start_time
7. `score`: float; R2 value of the model; 1.0 is best, 0.0 is worst
8. `mean_latency`: float; mean latency of the data
9. `std_dev_latency`: float; latency standard deviation

We recommend only reading information from the TimeSyncAnalysis and OffsetModel objects.  
Setting or changing any of the properties may cause unexpected results.

_Example:_
```python
from redvox.common.data_window import DataWindow
from redvox.common.station import Station

dw = DataWindow(input_dir_str)

my_station: Station = dw.get_station("id01")[0]

my_ts = my_station.timesync_analysis
my_om = my_ts.offset_model
print(my_om.slope)
print(my_om.intercept)
```

_[Table of Contents](#table-of-contents)_

## Sensor Data

SensorData is a format-agnostic representation of the data.  This data can be gathered from or converted to another format as needed.

SensorData represents a single real world recording device like a microphone or accelerometer.

Each SensorData object is a Pandas DataFrame with some additional metadata.

Refer to the [SensorData API documentation](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/sensor_data.html) as needed.

_[Table of Contents](#table-of-contents)_

### Sensor Data Properties

These are the properties of the SensorData class:

1. `name`: string; name of sensor
2. `type`: SensorType; enumerated type of sensor
3. `data_df`: dataframe of the sensor data; always has timestamps as the first column, the other columns are the data fields
4. `sample_rate_hz`: float; sample rate in Hz of the sensor, default np.nan, usually 1/sample_interval_s
5. `sample_interval_s`: float; mean duration in seconds between samples, default np.nan, usually 1/sample_rate
6. `sample_interval_std_s`: float; standard deviation in seconds between samples, default np.nan
7. `is_sample_rate_fixed`: boolean; True if sample rate is constant, default False
8. `timestamps_altered`: boolean; True if timestamps in the sensor have been altered from their original values, default False
9. `errors`: RedVoxExceptions, class containing a list of all errors encountered when creating the sensor.  This is set by the SDK.

_[Table of Contents](#table-of-contents)_

### Sensor Data Functions

These are the functions of the SensorData class:

1. `data_channels()`: Returns a list of the valid channel names (columns of the dataframe)
2. `get_data_channel(channel_name)`: Returns a numpy.array or a list of strings of the dataframe column with the
   channel_name, or an error and a list of valid channel names if channel_name does not exist.
3. `num_samples()`: Returns the number of data points (rows in the dataframe) in the sensor
4. `data_timestamps()`: Returns a numpy.array of the timestamps in the dataframe
5. `first_data_timestamp()`: Returns the first timestamp in the dataframe
6. `last_data_timestamp()`: Returns the last timestamp in the dataframe
7. `unaltered_data_timestamps()`: Returns a numpy.array of the raw timestamps as recorded by the sensor.  These values 
   are never updated, adjusted or otherwise changed from what the sensor reported.
8. `samples()`: Returns a numpy.ndarray of all non-timestamp values in the dataframe**
9. `print_errors()`: Print the errors encountered when creating the SensorData

** Reading enumerated types from this function requires additional imports.  Refer to 
[the footnote on enumerated types](#a-note-on-enumerated-types) for more information

_[Table of Contents](#table-of-contents)_

### Sensor Data DataFrame Access

The table below shows which columns can be accessed by each sensor

|Sensor name            |Dataframe columns               |
|-----------------------|--------------------------------|
|all                    |timestamps, unaltered_timestamps|
|audio                  |microphone                      |
|compressed audio       |compressed_audio, audio_codec   |
|image                  |image, image_codec              |
|pressure               |pressure                        |
|light                  |light                           |
|proximity              |proximity                       |
|ambient temperature    |ambient_temp                    |
|relative humidity      |rel_humidity                    |
|accelerometer          |accelerometer_x, accelerometer_y, accelerometer_z|
|magnetometer           |magnetometer_x, magnetometer_y, magnetometer_z|
|linear acceleration    |linear_accel_x, linear_accel_y, linear_accel_z|
|orientation            |orientation_x, orientation_y, orientation_z|
|rotation vector        |rotation_vector_x, rotation_vector_y, rotation_vector_z|
|gyroscope              |gyroscope_x, gyroscope_y, gyroscope_z|
|gravity                |gravity_x, gravity_y, gravity_z |
|location, best location|gps_timestamps, latitude, longitude, altitude, speed, bearing, horizontal_accuracy, vertical_accuracy, speed_accuracy, bearing_accuracy, location_provider|
|station health         |battery_charge_remaining, battery_current_strength, internal_temp_c, network_type, network_strength, power_state, avail_ram, avail_disk, cell_service, cpu_utilization, wifi wake lock, screen state, screen brightness|

It is intentional that location and best location sensors have the same column names
*** Please note that entering an invalid column name for a sensor will raise an error and print the list of allowed names.

The table below lists the sensors and their data's units

|Sensor name             |Column Name             |units of data|
|------------------------|------------------------|-------------|
|all                     |timestamps, unaltered_timestamps|microseconds since epoch UTC|
|accelerometer           |                        |meters/second^2|
|ambient temperature     |                        |degrees Celsius|
|audio                   |                        |normalized counts (normalization constant = 0x7FFFFF)|
|compressed audio        |                        |bytes (codec specific)|
|gravity                 |                        |meters/second^2|
|gyroscope               |                        |radians/second|
|image                   |                        |bytes (codec specific)|
|light                   |                        |lux|
|linear acceleration     |                        |meters/second^2|
|magnetometer            |                        |microtesla|
|orientation             |                        |radians|
|pressure                |                        |kilopascal (this is also known as barometer sensor)|
|proximity               |                        |cm (this is also known as infrared sensor)|
|relative humidity       |                        |percentage|
|rotation vector         |                        |Unitless|
|location, best location |gps_timestamps          |microseconds since epoch UTC|
|                        |latitude, longitude, bearing, bearing accuracy|degrees| 
|                        |altitude, horizontal accuracy, vertical accuracy|meters|
|                        |speed, speed_accuracy   |meters per second|
|                        |location_provider       |enumeration of LocationProvider|
|station health          |battery_charge_remaining, cpu_utilization, screen_brightness|percentage|
|                        |battery_current_strength|microamperes|
|                        |internal_temp_c         |degrees Celsius|
|                        |network_type            |enumeration of NetworkType|
|                        |network_strength        |decibel|
|                        |power_state             |enumeration of PowerState|
|                        |avail_ram, avail_disk   |bytes|
|                        |cell_service            |enumeration of CellServiceState|
|                        |wifi_wake_lock          |enumeration of WifiWakeLock|
|                        |screen_state            |enumeration of ScreenState|

If Column Name is blank, then all non-timestamp columns in the dataframe have the unit specified.
Refer to the previous table for specific column names for each sensor.
It is intentional that location and best location sensors share the same column names.

#### A note on enumerated types
Please note that enumerations require you to import them from the [Redvox SDK](https://pypi.org/project/redvox/#history) before you can properly read their values.

Copy the following lines as needed:
```python
from redvox.api1000.wrapped_redvox_packet.station_information import NetworkType, PowerState, CellServiceState, WifiWakeLock, ScreenState
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
from redvox.api1000.wrapped_redvox_packet.sensors.image import ImageCodec
from redvox.api1000.wrapped_redvox_packet.sensors.audio import AudioCodec
```

_[Table of Contents](#table-of-contents)_

### Using Sensor Data

Assuming you have retrieved a Station object, you may access SensorData using the *_sensor() functions of the Station.

_Examples:_
```python
audio = station.audio_sensor()     # microphone/audio sensor
location = station.location_sensor()  # location/gps sensor
pressure = station.pressure_sensor()  # barometer/pressure sensor
```

Refer to the tables above for specific column names and functions to access the data.

_Examples:_

```python
# get audio data and timestamps:
mic_data = station.audio_sensor().get_data_channel("microphone")
timestamps = station.audio_sensor().data_timestamps()

# get accelerometer x channel data, sample rate in hz, and sample interval in seconds
accel_data = station.accelerometer_sensor().get_data_channel("accelerometer_x")
accel_sample_rate = station.accelerometer_sensor().sample_rate
accel_sample_interval_s = station.accelerometer_sensor().sample_interval_s
```

_[Table of Contents](#table-of-contents)_

