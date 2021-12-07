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
    * [Accessors](#station-accessors)
    * [Setters](#station-setters)
    * [Save and Load](#station-save-and-load)
  * [Using Station](#using-station)
  * [Station Metadata](#station-metadata)
  * [Station Packet Metadata](#station-packet-metadata)
  * [Timesync and Offset Model](#timesync-and-offset-model)
- [Sensor Data](#sensor-data)
  * [Sensor Data Creation](#sensor-data-creation)
  * [Sensor Data Properties](#sensor-data-properties)
  * [Sensor Data Protected Properties](#sensor-data-protected-properties)
  * [Sensor Data Accessor Functions](#sensor-data-accessor-functions)
  * [Sensor Data Functions](#sensor-data-functions)
  * [Sensor Data Access](#sensor-data-access)
    + [A note on enumerated types](#a-note-on-enumerated-types)
  * [Sensor Subclasses](#sensor-subclasses)
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

All properties of Stations are protected.  You will need to use specific functions to access the properties.
The default value of each property is given.

1. `_id`: string; id of the station, default None
2. `_uuid`: string; uuid of the station, default None
3. `_start_date`: float; microseconds since epoch UTC when the station started recording, default np.nan
4. `_data`: dictionary of sensor type and sensor data associated with the station, default empty dictionary
5. `_metadata`: StationMetadata that didn't go into the sensor data, default empty StationMetadata object
6. `_packet_metadata`: list of StationPacketMetadata that changes from packet to packet, default empty list
7. `_first_data_timestamp`: float; microseconds since epoch UTC of the first data point, default np.nan
8. `_last_data_timestamp`: float; microseconds since epoch UTC of the last data point, default np.nan
9. `_audio_sample_rate_nominal_hz`: float of nominal sample rate of audio component in hz, default np.nan
10. `_is_audio_scrambled`: boolean; True if audio data is scrambled, default False
11. `_is_timestamps_updated`: boolean; True if timestamps have been altered from original data values, default False
12. `_timesync_data`: TimeSync object; contains information about the station's timing values.  Refer to 
    the [Timesync Documentation](#timesync-and-offset-model) for more information
13. `_use_model_correction`: boolean; if True, time correction is done using OffsetModel functions, otherwise
    correction is done by adding the best offset from the OffsetModel (also known as the model's intercept value or
    the best offset from TimeSync).  default True
14.`_correct_timestamps`: boolean; if True, corrects the timestamps of the data.  default False
15.`_gaps`: List of Tuples; pairs of timestamps indicating start and end times of gaps.  Times are not inclusive of 
    the gap. Set by reading the data.  default empty list.
14. `_fs_writer`: FileSystemWriter, stores the information used to save the data to disk.  Defaults to not saving and 
    using the current directory.
15. `_errors`: RedVoxExceptions, class containing a list of all errors encountered when creating the station.  
    This is set by the SDK.  default empty RedVoxExceptions

_[Table of Contents](#table-of-contents)_

### Station Functions

The Station class has two types of functions, Accessors and Setters.

#### Station Accessors

Accessors allow you to read values from the Station.  The Accessor functions are listed below.

1. `id() -> str`: Returns the id of the Station.

2. `uuid() -> str`: Returns the uuid of the Station.

3. `start_date() -> float`: Returns the start_date of the Station.

4. `data() -> List[sd.SensorData]`: Returns the list of SensorData objects in the Station.  See 
   [the section on SensorData](#sensor-data).

5. `get_sensors() -> List[str]`: Returns a list of the sensor names in the Station.

6. `get_station_sensor_types() -> List[sd.SensorType]`: Returns a list of all sensor types in the Station.

7. `gaps() -> List[Tuple[float, float]]`: Returns a list of all gaps in the Station.

8. `metadata() -> st_utils.StationMetadata`: Returns the metadata of the Station

9. `packet_metadata() -> List[st_utils.StationPacketMetadata]`: Returns a list of all packet metadata in the Station.

10. `first_data_timestamp() -> float`: Returns the timestamp of the first audio data point in the Station.

11. `last_data_timestamp() -> float`: Returns the timestamp of the last audio data point in the Station.

12. `use_model_correction() -> bool`: Returns if the Station used its OffsetModel to correct the timestamps.

13. `is_timestamps_updated() -> bool`: Returns if the Station has updated its timestamps from the raw data values.

14. `timesync_data() -> TimeSync`: Returns the TimeSync data of the Station.

15. `has_timesync_data() -> bool`: Returns `True` if the Station has TimeSync data.

16. `audio_sample_rate_nominal_hz() -> float`: Returns the nominal audio sample rate in Hz of the Station.

17. `is_audio_scrambled() -> float`: Returns if the audio data of the Station is scrambled.

18. `check_key() -> bool`: Returns `True` if the Station's key is set, otherwise creates an error and returns `False`.

19. `get_key() -> Optional[st_utils.StationKey]`: Returns the key of the Station if it exists, otherwise returns `None`.

20. `save_dir() -> str`: Returns the name of the directory used to save the Station data.

21. `is_save_to_disk() -> bool`: Returns if the Station data will be saved to disk.

22. `fs_writer() -> FileSystemWriter`: Returns the FileSystemWriter object used by the Station to control saving to disk.

23. `get_mean_packet_duration() -> float`: Returns the mean duration of audio samples in the data packets used to create the Station.

24. `get_mean_packet_audio_samples() -> float`: Returns the mean number of audio samples per data packet used to create the Station.

25. `get_sensor_by_type(sensor_type: sd.SensorType) -> Optional[sd.SensorData]`: Returns the Sensor specified by 
    `sensor_type` or None if the type cannot be found.

26. `errors() -> RedVoxExceptions`: Returns the errors class of the Station.

27. `print_errors()`: Print the errors encountered when creating the Station.

#### Station Setters

Setters allow you to set or change the properties of the Station.  The Setter functions are listed below.

1. `set_save_data(save_on: bool = False)`: Sets the save value of the Station.  If `True`, the data will be saved to disk.

2. `set_id(station_id: str) -> "Station"`: Sets the `_id` of the Station to `station_id` and returns the updated Station.

3. `set_uuid(uuid: str) -> "Station"`: Sets the `_uuid` of the Station to `uuid` and returns the updated Station.

4. `set_start_date(start_timestamp: float) -> "Station"`: Sets the `_start_date` of the Station to `start_timestamp` 
    and returns the updated Station.

5. `set_gaps(gaps: List[Tuple[float, float]])`: Sets the gaps of the Station to `gaps`.

6. `set_metadata(metadata: st_utils.StationMetadata)`: Sets the metadata of the Station to `metadata`

7. `set_packet_metadata(self, packet_metadata: List[st_utils.StationPacketMetadata])`: Sets the packet metadata of the 
    Station to the list of `packet_metadata`.

8. `set_audio_sample_rate_hz(self, sample_rate: float)`: Sets the audio sensor sample rate of the Station to `sample_rate`.

9. `set_audio_scrambled(self, is_scrambled: bool)`: Sets if the audio data of the Station is scrambled.

10. `update_start_and_end_timestamps()`: Sets the `_first_data_timestamp` and `_last_data_timestamp` properties of the 
     Station using the Station's data.

11. `set_timestamps_updated(self, is_updated: bool)`: Sets if the timestamps are updated in the Station.

12. `set_timesync_data(self, timesync: TimeSync)`: Sets the time sync data of the Station to `timesync`.

13. `set_errors(self, errors: RedVoxExceptions)`: Sets the errors of the Station to `errors`.

14. `append_sensor(sensor_data: sd.SensorData)`: Adds the `sensor_data` to the Station or appends the data to an 
     existing SensorData of the same type.

15. `append_station(new_station: "Station")`: Adds the data from the `new_station` to the calling Station, if the keys 
     of both Stations are the same.  If the keys are different or one of the keys is invalid, nothing happens.

#### Station Save and Load

Use these functions to save and load Station data.

1. `save(self, file_name: Optional[str] = None) -> Optional[Path]`

Saves the Station's data to disk if enabled, then returns the path to the saved JSON file.  Does nothing and 
returns `None` if saving is not enabled.

2. `load(in_dir: str = "") -> "Station"`

Uses the first JSON file in the `in_dir` to load the Station's data.  Creates an error if the file cannot be found.

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

dw = DataWindow.load(dw_file_path)

my_station: Station = dw.get_station("id01")[0]

my_id = my_station.id()
first_timestamp = my_station.first_data_timestamp()
last_timestamp = my_station.last_data_timestamp()
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

dw = DataWindow.load(dw_file_path)

my_station: Station = dw.get_station("id01")[0]

my_metadata = my_station.metadata()
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

dw = DataWindow.load(dw_file_path)

my_station: Station = dw.get_station("id01")[0]

for packet in my_station.packet_metadata():
  print(packet.packet_start_mach_timestamp)
  print(packet.packet_end_mach_timestamp)
```

_[Table of Contents](#table-of-contents)_

### Timesync and Offset Model

Station uses a TimeSync object to hold information about the clock synchronization.

The TimeSync class summarizes the timing information of the station.

These are the accessible properties of the class:
1. `arrow_dir`: string; the directory to save the TimeSync data to.  Defaults to "." (current directory)
2. `arrow_file`: string; the name of the JSON file to save the TimeSync data to.  Do not include the extension when setting.
   Defaults to "timesync".
   
These are the functions that retrieve the data:
1. `num_tri_messages(self) -> int`: Returns the number of tri-message sync exchanges in the data.
2. `best_latency() -> float`: Returns the best (lowest) latency of the data.
3. `latencies() -> np.ndarray`: Returns all latencies of the data as two numpy arrays.
4. `mean_latency() -> float`: Returns the mean of the latencies.
5. `latency_std() -> float`: Returns the standard deviation of the latencies.
6. `best_latency_index() -> int`: Returns the position of the best latency in the data.
7. `best_latency_per_exchange() -> np.array`: Returns the lowest latency per data.
8. `best_offset() -> float`: Returns the best offset of the data.
9. `offsets() -> np.ndarray`: Returns all offsets of the data as two numpy arrays.
10. `mean_offset() -> float`: Returns the mean of the offsets.
11. `offset_std() -> float`: Returns the standard deviation of the offsets.
12. `best_offset_per_exchange() -> np.array`: Returns the best latency per exchange.
13. `sync_exchanges() -> np.ndarray`: Returns the timesync exchanges of the station as 6 arrays.  Each array is the 
    same length.  The order of the arrays is a1, a2, a3, b1, b2, b3.
14. `get_exchange_timestamps(index: int) -> np.array`: Returns the timestamps of a specific position in the exchanges.
    The `index` parameter must be a value from 0 to 5.  Any value below 0 and above 5 will be reset to 0.
    Index of 0 refers to all a1 timestamps, index of 1 refers to all a2 timestamps, etc.
15. `data_start_timestamp() -> float`: Returns the first timestamp of the data.
16. `data_end_timestamp() -> float`: Returns the last timestamp of the data.
17. `offset_model() -> OffsetModel`: Returns the OffsetModel used to calculate offset of the station at a given point in time.
    See below for more information about OffsetModel.
18. `to_json_file(file_name: Optional[str] = None) -> Path`: Save the TimeSync object to a json file and the data as a parquet.
    If `file_name` is not specified, uses the TimeSync's `arrow_file` property.  Returns the path to the file if successful.
19. `from_json_file(file_path: str) -> "TimeSync"`: Returns a TimeSync object using the information specified in the 
    JSON file named `file_path`.

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

These are the functions of the OffsetModel:
1. `get_offset_at_time(time: float)`: Returns the offset at the specified `time`
2. `update_time(time: float, use_model_function: bool = True)`: Returns `time` modified by the offset at `time` 
   if `use_model_function` is True, otherwise uses the offset at `start_time`.
3. `update_timestamps(timestamps: np.array, use_model_function: bool = True)`: Returns `timestamps` modified by the offset
   at their respective times if `use_model_function` is True, otherwise uses the offset at `start_time`.

We recommend only reading information from the TimeSync and OffsetModel objects.  
Setting or changing any of the properties may cause unexpected results.

_Example:_
```python
from redvox.common.data_window import DataWindow, DataWindowConfig
from redvox.common.station import Station

conf = DataWindowConfig("input_dir_str")

dw = DataWindow("test_event", config=conf)

my_station: Station = dw.get_station("id01")[0]

my_ts = my_station.timesync_data()
my_om = my_ts.offset_model()
print(my_om.slope)
print(my_om.intercept)
```

_[Table of Contents](#table-of-contents)_

## Sensor Data

SensorData is a format-agnostic representation of the data.  This data can be gathered from or converted to another format as needed.

SensorData represents a single real world recording device like a microphone or accelerometer.

Each SensorData object stores the data as a Pyarrow table, either locally or on disk as a parquet file.

Refer to the [SensorData API documentation](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/sensor_data.html) as needed.

_[Table of Contents](#table-of-contents)_

### Sensor Data Creation

Use one of these functions to create a SensorData object:

1. ```
   __init__(sensor_name: str,
            sensor_data: Optional[pa.Table] = None,
            sensor_type: SensorType = SensorType.UNKNOWN_SENSOR,
            sample_rate_hz: float = np.nan,
            sample_interval_s: float = np.nan,
            sample_interval_std_s: float = np.nan,
            is_sample_rate_fixed: bool = False,
            are_timestamps_altered: bool = False,
            calculate_stats: bool = False,
            use_offset_model_for_correction: bool = False,
            save_data: bool = False,
            arrow_dir: str = ".",
            gaps: Optional[List[Tuple[float, float]]] = None)
   ```
   Initialization function.
   
   _Example:_
   ```python
   import pyarrow as pa
   from redvox.common.sensor_data import SensorData, SensorType
   
   data_table: pa.Table
   audio_type = SensorType.AUDIO
   
   the_sensor = SensorData("my_sensor", data_table, audio_type)
   ```
2. ```
    from_dir(sensor_name: str,
             data_path: str,
             sensor_type: SensorType = SensorType.UNKNOWN_SENSOR,
             sample_rate_hz: float = np.nan,
             sample_interval_s: float = np.nan,
             sample_interval_std_s: float = np.nan,
             is_sample_rate_fixed: bool = False,
             are_timestamps_altered: bool = False,
             calculate_stats: bool = False,
             use_offset_model_for_correction: bool = False,
             save_data: bool = False) -> "SensorDataPa":
   ```
   Return a SensorData object using a directory as the data source.

3. ```
   from_dict(
            sensor_name: str,
            sensor_data: Dict,
            sensor_type: SensorType = SensorType.UNKNOWN_SENSOR,
            sample_rate_hz: float = np.nan,
            sample_interval_s: float = np.nan,
            sample_interval_std_s: float = np.nan,
            is_sample_rate_fixed: bool = False,
            are_timestamps_altered: bool = False,
            calculate_stats: bool = False,
            use_offset_model_for_correction: bool = False,
            save_data: bool = False,
            arrow_dir: str = "") -> "SensorDataPa":
   ```
   Return a SensorData object using a dictionary as the data source.

### Sensor Data Properties

This is the publicly accessible property of the SensorData class: 

1. `name`: string; name of sensor
   
### Sensor Data Protected Properties

These are the protected properties of the SensorData class.  These values are set during initialization of SensorData.
You must use a function to return or update the values.  We do not recommend updating or editing these properties without using their accessor functions.

1. `_type`: SensorType; enumerated type of sensor
2. `_data`: Pyarrow table of the sensor data; always has timestamps as the first column, the other columns are the data fields.
3. `_sample_rate_hz`: float; sample rate in Hz of the sensor, default np.nan, usually 1/sample_interval_s
4. `_sample_interval_s`: float; mean duration in seconds between samples, default np.nan, usually 1/sample_rate
5. `_sample_interval_std_s`: float; standard deviation in seconds between samples, default np.nan
6. `_is_sample_rate_fixed`: boolean; True if sample rate is expected to be constant, default False
7. `_timestamps_altered`: boolean; True if timestamps in the sensor have been altered from their original values, default False
8. `_use_offset_model`: boolean, if True, uses an offset model to correct timestamps, default False
9. `_fs_writer`: FileSystemWriter, stores the information used to save the data to disk.  Defaults to not saving and
   using the current directory.
10. `_gaps`: List of paired tuples; the timestamps of data points on the edge of data gaps.  Any point between the timestamps
    is not valid and exists purely to maintain sample rate.
11. `_errors`: RedVoxExceptions of the sensor data; contains a list of all errors encountered by the sensor.  This is set by the SDK.

_[Table of Contents](#table-of-contents)_

### Sensor Data Accessor Functions

These functions are approved methods of reading values from protected properties of SensorData

1. `type() -> SensorType`: Returns the enumerated type of the sensor
2. `type_as_str() -> str`: Returns the type as a string
3. `file_name() -> str`: Returns the name of the file used to save the data (no extension).
4. `full_file_name(self) -> str`: Returns the full name of the file used to save the data.
5. `base_dir() -> str`: Returns the name of the directory where the data will be saved to.
6. `full_path() -> str`: Returns the full path to the saved file.
7. `fs_writer() -> FileSystemWriter`: Returns the information used to save the data.
8. `pyarrow_table() -> pa.Table`: Returns the data as a Pyarrow table.
9. `data_df() -> pd.DataFrame`: Returns the data as a Pandas dataframe
10. `sample_rate_hz() -> float`: Returns the sample rate of the sensor in Hz.
11. `sample_interval_s() -> float`: Returns the interval between samples in seconds.
12. `sample_interval_std_s() -> float`: Returns the standard deviation of the sample interval in seconds.
13. `is_sample_rate_fixed() -> bool`: Returns if the sample rate of the Sensor is a constant.
14. `is_timestamps_altered() -> bool`: Returns if the timestamps of the Sensor have been updated from their raw values.
15. `used_offset_model() -> bool`: Returns if the offset model was used to correct the timestamps.
16. `is_save_to_disk() -> bool`: Returns if the data will be saved to disk
17. `enable_save_to_disk(new_dir: Optional[str] = None)`: Use this function to enable saving data to disk at the directory given.
    If you call this function without giving a name, it uses the current directory.
18. `gaps() -> List[Tuple]`: Returns the list of gaps.
19. `errors() -> RedVoxExceptions`: Returns the error object.

_[Table of Contents](#table-of-contents)_

### Sensor Data Setter Functions

These functions set the values of SensorData properties:

1. `set_file_name(new_file: Optional[str] = None)`: Set the name of the parquet file that contains the data.
   Do NOT include the extension.  If you call this function without giving a name, it uses the default form.
2. `set_base_dir(new_dir: Optional[str] = None)`: Set the directory containing the parquet file.
   If you call this function without giving a name, it uses the current directory.
3. `set_save_to_disk(save: bool)`: Sets the save to disk flag.  If `True`, saving is enabled.

_[Table of Contents](#table-of-contents)_

### Sensor Data Functions

These functions return specific details from the Sensor's properties:

1. `num_samples()`: Returns the number of data points (rows in the table) in the sensor.
2. `data_timestamps()`: Returns a numpy.array of the timestamps of the data.
3. `first_data_timestamp()`: Returns the first timestamp of the data.
4. `last_data_timestamp()`: Returns the last timestamp of the data.
5. `unaltered_data_timestamps()`: Returns a numpy.array of the raw timestamps as recorded by the sensor.  These values 
   are never updated, adjusted or otherwise changed from what the sensor reported.
6. `samples()`: Returns a numpy.ndarray of all non-timestamp values in the data.**
7. `print_errors()`: Print the errors encountered in the SensorData.

** Reading enumerated types from this function requires additional imports.  Refer to 
[the footnote on enumerated types](#a-note-on-enumerated-types) for more information

#### Sensor Save and Load

Use these functions to save and load Sensor data.

1. `save(self, file_name: Optional[str] = None) -> Optional[Path]`

Saves the Sensor's data to disk if enabled, then returns the path to the saved JSON file.  Does nothing and
returns `None` if saving is not enabled.

2. `load(in_dir: str = "") -> "SensorData"`

Uses the first JSON file in the `in_dir` to load the Sensor's data.  Creates an error if the file cannot be found.


_[Table of Contents](#table-of-contents)_

### Sensor Data Access

The table below shows which columns can be accessed by each sensor

|Sensor name            |Table columns                   |
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

For more details on accessing the values from specific types of sensors, please read [Sensor Subclasses](#sensor-subclasses).

It is intentional that location and best location sensors have the same column names.

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

If Column Name is blank, then all non-timestamp columns in the table have the unit specified.
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

### Sensor Subclasses

The SensorData class works well for generic applications, but not all sensors share the same types of data.  An Audio
Sensor has a microphone channel but no gyroscope channels.  A Gyroscope Sensor has gyroscope_x, y and z channels, but 
no microphone channel.  We have utilized subclasses of SensorData to provide ease of discoverability and access
to Sensor specific channels.

This paradigm has been applied to the Station class.  Notice that station.audio_sensor() returns an AudioSensorData 
object instead of just a SensorData.  The AudioSensorData class has access to all functions and properties of SensorData,
with the addition of functions specifically tuned for Audio data, such as get_microphone().

### Sensor Subclass Functions
Below is the list of functions you can use to access data for each Sensor subclass.
The `get_valid_*()` functions return all the non-nan data points for the specific data type described by the function.

#### Audio Sensor
1. `get_microphone_data() -> np.array`
2. `get_valid_microphone_data() -> np.array`

#### Compressed Audio Sensor
1. `get_compressed_audio_data() -> np.array`
2. `get_valid_compressed_audio_data() -> np.array`
3. `get_audio_codec_data() -> List[str]`

#### Image Sensor
1. `get_image_data() -> np.array`
2. `get_valid_image_data() -> np.array`
3. `get_image_codec_data() -> List[str]`

#### Pressure Sensor
1. `get_pressure_data() -> np.array`
2. `get_valid_pressure_data() -> np.array`

#### Light Sensor
1. `get_light_data() -> np.array`
2. `get_valid_light_data() -> np.array`

#### Proximity Sensor
1. `get_proximity_data() -> np.array`
2. `get_valid_proximity_data() -> np.array`

#### Ambient Temperature Sensor
1. `get_ambient_temperature_data() -> np.array`
2. `get_valid_ambient_temperature_data() -> np.array`

#### Relative Humidity Sensor
1. `get_relative_humidity_data() -> np.array`
2. `get_valid_relative_humidity_data() -> np.array`

#### Accelerometer Sensor
1. `get_accelerometer_x_data() -> np.array`
2. `get_accelerometer_y_data() -> np.array`
3. `get_accelerometer_z_data() -> np.array`
4. `get_valid_accelerometer_x_data() -> np.array`
5. `get_valid_accelerometer_y_data() -> np.array`
6. `get_valid_accelerometer_z_data() -> np.array`

#### Magnetometer Sensor
1. `get_magnetometer_x_data() -> np.array`
2. `get_magnetometer_y_data() -> np.array`
3. `get_magnetometer_z_data() -> np.array`
4. `get_valid_magnetometer_x_data() -> np.array`
5. `get_valid_magnetometer_y_data() -> np.array`
6. `get_valid_magnetometer_z_data() -> np.array`

#### Linear Acceleration Sensor
1. `get_linear_acceleration_x_data() -> np.array`
2. `get_linear_acceleration_y_data() -> np.array`
3. `get_linear_acceleration_z_data() -> np.array`
4. `get_valid_linear_acceleration_x_data() -> np.array`
5. `get_valid_linear_acceleration_y_data() -> np.array`
6. `get_valid_linear_acceleration_z_data() -> np.array`

#### Orientation Sensor
1. `get_orientation_x_data() -> np.array`
2. `get_orientation_y_data() -> np.array`
3. `get_orientation_z_data() -> np.array`
4. `get_valid_orientation_x_data() -> np.array`
5. `get_valid_orientation_y_data() -> np.array`
6. `get_valid_orientation_z_data() -> np.array`

#### Rotation Vector Sensor
1. `get_rotation_vector_x_data() -> np.array`
2. `get_rotation_vector_y_data() -> np.array`
3. `get_rotation_vector_z_data() -> np.array`
4. `get_valid_rotation_vector_x_data() -> np.array`
5. `get_valid_rotation_vector_y_data() -> np.array`
6. `get_valid_rotation_vector_z_data() -> np.array`

#### Gyroscope Sensor
1. `get_gyroscope_x_data() -> np.array`
2. `get_gyroscope_y_data() -> np.array`
3. `get_gyroscope_z_data() -> np.array`
4. `get_valid_gyroscope_x_data() -> np.array`
5. `get_valid_gyroscope_y_data() -> np.array`
6. `get_valid_gyroscope_z_data() -> np.array`

#### Gravity Sensor
1. `get_gravity_x_data() -> np.array`
2. `get_gravity_y_data() -> np.array`
3. `get_gravity_z_data() -> np.array`
4. `get_valid_gravity_x_data() -> np.array`
5. `get_valid_gravity_y_data() -> np.array`
6. `get_valid_gravity_z_data() -> np.array`

#### Location Sensor and Best Location Sensor
1. `get_gps_timestamps_data() -> np.array`
2. `get_valid_gps_timestamps_data() -> np.array`
3. `get_latitude_data() -> np.array`
4. `get_valid_latitude_data() -> np.array`
5. `get_longitude_data() -> np.array`
6. `get_valid_longitude_data() -> np.array`
7. `get_altitude_data() -> np.array`
8. `get_valid_altitude_data() -> np.array`
9. `get_speed_data() -> np.array`
10. `get_valid_speed_data() -> np.array`
11. `get_bearing_data() -> np.array`
12. `get_valid_bearing_data() -> np.array`
13. `get_horizontal_accuracy_data() -> np.array`
14. `get_valid_horizontal_accuracy_data() -> np.array`
15. `get_vertical_accuracy_data() -> np.array`
16. `get_valid_vertical_accuracy_data() -> np.array`
17. `get_speed_accuracy_data() -> np.array`
18. `get_valid_speed_accuracy_data() -> np.array`
19. `get_bearing_accuracy_data() -> np.array`
20. `get_valid_bearing_accuracy_data() -> np.array`
21. `get_location_provider_data() -> np.array`

#### Health Sensor
1. `get_battery_charge_remaining_data() -> np.array`
2. `get_valid_battery_charge_remaining_data() -> np.array`
3. `get_battery_current_strength_data() -> np.array`
4. `get_valid_battery_current_strength_data() -> np.array`
5. `get_internal_temp_c_data() -> np.array`
6. `get_valid_internal_temp_c_data() -> np.array`
7. `get_network_type_data() -> np.array`
8. `get_network_strength_data() -> np.array`
9. `get_valid_network_strength_data() -> np.array`
10. `get_power_state_data() -> np.array`
11. `get_avail_ram_data() -> np.array`
12. `get_valid_avail_ram_data() -> np.array`
13. `get_avail_disk_data() -> np.array`
14. `get_valid_avail_disk_data() -> np.array`
15. `get_cell_service_data() -> np.array`
16. `get_cpu_utilization_data() -> np.array`
17. `get_valid_cpu_utilization_data() -> np.array`
18. `get_wifi_wake_lock_data() -> np.array`
19. `get_screen_state_data() -> np.array`
20. `get_screen_brightness_data() -> np.array`
21. `get_valid_screen_brightness_data() -> np.array`

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
mic_data = station.audio_sensor().get_microphone_data()
timestamps = station.audio_sensor().data_timestamps()

# get accelerometer x channel data, sample rate in hz, and sample interval in seconds
accel_data = station.accelerometer_sensor().get_accelerometer_x_data()
accel_sample_rate = station.accelerometer_sensor().sample_rate_hz()
accel_sample_interval_s = station.accelerometer_sensor().sample_interval_s()
```

_[Table of Contents](#table-of-contents)_
