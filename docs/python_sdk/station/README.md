# <img src="../img/redvox_logo.png" height="25"> **RedVox Python SDK Data Window Manual**

The RedVox Python SDK contains routines for reading, creating, and writing RedVox API 900 and RedVox API 1000 data files. The SDK is open-source.

Station is a Python class designed to store format-agnostic station and sensor data.  Its primary goal is to represent RedVox data, but it is capable of representing a variety of station and sensor configurations.

## Table of Contents

<!-- toc -->

- [Station](#station)
  * [Station Properties](#station-properties)
  * [Station Functions](#station-functions)
  * [Using Station](#using-station)
  * [StationMetadata](#station-metadata)
  * [StationPacketMetadata](#station-packet-metadata)
  * [Timesync](#timesync)
- [Sensor Data](#sensor-data)
  * [Sensor Data Properties](#sensor-data-properties)
  * [Sensor Data Functions](#sensor-data-functions)
  * [Sensor Data DataFrame Access](#sensor-data-dataframe-access)
    + [A note on enumerated types](#a-note-on-enumerated-types)
  * [Using Sensor Data](#using-sensor-data)

<!-- tocstop -->

## Station

Station is a module designed to hold format-agnostic data of various sensors that combine to form a single unit.  The data can be gathered from and turned into various other formats as needed.

Station represents real world combinations of various recording devices such as audio, accelerometer, and pressure sensors.  Stations will not contain more than one of the same type of sensor; this is to allow unambiguous and easy comparison between stations.

Station objects are comprised of a station key, the sensor data, data packet metadata, and other station specific metadata.

Each Station has a unique key.  Keys are comprised of the Station's id, uuid, start timestamp since epoch UTC and the station's metadata.  Stations with the same key can be combined into one Station.

Refer to the [Station API documentation](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/station.html) as needed.

_[Table of Contents](#table-of-contents)_

### Station Properties

These are the properties of the Station class:

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
12. `timesync_analysis`: TimeSyncAnalysis object; contains information about the station's timing values

_[Table of Contents](#table-of-contents)_

### Station Functions

These are the functions of the Station class:
1. `get_mean_packet_duration()`: Returns the mean duration of audio samples in the data packets used to create the Station.
2. `get_mean_packet_audio_samples()`: Returns the mean number of audio samples per data packet used to create the Station.
3. `append_station(new_station)`: Adds the data from the new_station to the calling Station, if the keys of both Stations are the same.  If the keys are different or one of the keys is invalid, nothing happens.
4. `get_key`: Returns the key of Station
5. `check_key`: Returns True if the Station can create a key, False otherwise.  If returning False, prints which value is missing.

For the following 4 functions, replace SENSOR with one of:
audio, compressed_audio, image, location, pressure, barometer, light, infrared, proximity, health, relative_humidity, ambient_temperature, accelerometer, gyroscope, magnetometer, gravity, linear_acceleration, orientation, rotation_vector

6. `has_SENSOR_sensor()`: Returns True if the sensor exists in the station
7. `has_SENSOR_data()`: Returns True if the sensor exists in the station and has data
8. `SENSOR_sensor()`: Returns the SensorData object for the sensor, or `None` if the sensor doesn't exist.
9. `set_SENSOR_sensor(s: Optional[SensorData])`: Returns the updated Station after setting the sensor in the Station or removing it if argument s is `None`.

_[Table of Contents](#table-of-contents)_

### Using Station

Station objects contain metadata for the station and the sensors that recorded the data.

The table below shows the sensor name and the function call required to access the sensor.

|Sensor Name         |Accessor Function               |
|--------------------|--------------------------------|
|audio               |audio_sensor()                  |
|compressed audio    |compressed_audio_sensor()       |
|image               |image_sensor()                  |
|pressure            |pressure_sensor()               |
|light               |light_sensor()                  |
|proximity           |proximity_sensor()              |
|ambient temperature |ambient_temperature_sensor()    |
|relative humidity   |relative_humidity_sensor()      |
|accelerometer       |accelerometer_sensor()          |
|magnetometer        |magnetometer_sensor()           |
|linear acceleration |linear_acceleration_sensor()    |
|orientation         |orientation_sensor()            |
|rotation vector     |rotation_vector_sensor()        |
|gyroscope           |gyroscope_sensor()              |
|gravity             |gravity_sensor()                |
|location            |location_sensor()               |
|station health      |health_sensor()                 |

*** Some stations may use alternate names for their sensors instead of the ones listed above.  
Common replacements are:
* microphone instead of audio
* barometer instead of pressure
* infrared instead of proximity

Refer to the [SensorData](#sensor-data) section on how to access the data.

We recommend only reading information from the Station objects.  
Setting or changing any of the properties in Station may cause unexpected results.

_[Table of Contents](#table-of-contents)_

### Station Metadata

_[Table of Contents](#table-of-contents)_

### Station Packet Metadata

_[Table of Contents](#table-of-contents)_

### Timesync

_[Table of Contents](#table-of-contents)_

## Sensor Data

SensorData is a format-agnostic representation of the data.  This data can be gathered from or converted to another format as needed.

SensorData represents a single real world recording device like a microphone or accelerometer.

Each SensorData object is a Pandas DataFrame with some additional metadata.

Refer to the [SensorData API documentation](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/station_data.html) as needed.

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

_[Table of Contents](#table-of-contents)_

### Sensor Data Functions

These are the functions of the SensorData class:

1. `data_channels()`: Returns a list of the valid channel names (columns of the dataframe)
2. `get_data_channel(channel_name)`: Returns a numpy.array** of the dataframe column with the channel_name, or an error and a list of valid channel names if channel_name does not exist.
3. `num_samples()`: Returns the number of data points (rows in the dataframe) in the sensor
4. `data_timestamps()`: Returns a numpy.array of the timestamps in the dataframe
5. `first_data_timestamp()`: Returns the first timestamp in the dataframe
6. `last_data_timestamp()`: Returns the last timestamp in the dataframe
7. `data_duration_s()`: Returns the duration of the data in seconds
8. `unaltered_data_timestamps()`: Returns a numpy.array of the raw timestamps as recorded by the sensor.  These values are never updated, adjusted or otherwise changed from what the sensor reported.

** Reading enumerated types from this function requires additional imports.  Refer to [the footnote on enumerated types](#a-note-on-enumerated-types) for more information

_[Table of Contents](#table-of-contents)_

### Sensor Data DataFrame Access

The table below shows which columns can be accessed by each sensor

|Sensor name         |Dataframe columns               |
|--------------------|--------------------------------|
|all                 |timestamps, unaltered_timestamps|
|audio               |microphone                      |
|compressed audio    |compressed_audio, audio_codec   |
|image               |image, image_codec              |
|pressure            |pressure                        |
|light               |light                           |
|proximity           |proximity                       |
|ambient temperature |ambient_temp                    |
|relative humidity   |rel_humidity                    |
|accelerometer       |accelerometer_x, accelerometer_y, accelerometer_z|
|magnetometer        |magnetometer_x, magnetometer_y, magnetometer_z|
|linear acceleration |linear_accel_x, linear_accel_y, linear_accel_z|
|orientation         |orientation_x, orientation_y, orientation_z|
|rotation vector     |rotation_vector_x, rotation_vector_y, rotation_vector_z|
|gyroscope           |gyroscope_x, gyroscope_y, gyroscope_z|
|gravity             |gravity_x, gravity_y, gravity_z |
|location            |latitude, longitude, altitude, speed, bearing, horizontal_accuracy, vertical_accuracy, speed_accuracy, bearing_accuracy, location_provider|
|station health      |battery_charge_remaining, battery_current_strength, internal_temp_c, network_type, network_strength, power_state, avail_ram, avail_disk, cell_service|

Please note that entering an invalid channel name for a sensor will raise an error and print the list of allowed names.

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
|location                |latitude, longitude, bearing, bearing accuracy|degrees| 
|                        |altitude, horizontal accuracy, vertical accuracy|meters|
|                        |speed, speed_accuracy   |meters per second|
|                        |location_provider       |enumeration of LocationProvider|
|station health          |battery_charge_remaining|percentage|
|                        |battery_current_strength|microamperes|
|                        |internal_temp_c         |degrees Celsius|
|                        |network_type            |enumeration of NetworkType|
|                        |network_strength        |decibel|
|                        |power_state             |enumeration of PowerState|
|                        |avail_ram, avail_disk   |bytes|
|                        |cell_service            |enumeration of CellServiceState|

If Column Name is blank, then all non-timestamp columns in the dataframe have the unit specified.
Refer to the previous table for specific column names for each sensor.

#### A note on enumerated types
Please note that enumerations require you to import them from the [Redvox SDK](https://pypi.org/project/redvox/#history) before you can properly read their values.

Copy the following lines as needed:
```python
from redvox.api1000.wrapped_redvox_packet.station_information import NetworkType, PowerState, CellServiceState
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
```

_[Table of Contents](#table-of-contents)_

### Using Sensor Data

Assuming you have retrieved a Station object, you may access SensorData using the *_sensor() functions of the Station.

_Examples:_
```python
station.audio_sensor()     # microphone/audio sensor
station.location_sensor()  # location/gps sensor
station.pressure_sensor()  # barometer/pressure sensor
```

Refer to the tables above for specific column names and functions to access the data.

_Examples:_

```python
# get audio data and timestamps:
station.audio_sensor().get_data_channel("microphone")
station.audio_sensor().data_timestamps()

# get accelerometer x channel data, sample rate in hz, and sample interval in seconds
station.accelerometer_sensor().get_data_channel("accelerometer_x")
station.accelerometer_sensor().sample_rate
station.accelerometer_sensor().sample_interval_s
```

_[Table of Contents](#table-of-contents)_

