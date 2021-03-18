# <img src="../img/redvox_logo.png" height="25"> **RedVox Python SDK Data Window Manual**

The RedVox Python SDK contains routines for reading, creating, and writing RedVox API 900 and RedVox API 1000 data files. The SDK is open-source.

DataWindow is a Python class designed to fetch data from a source.  It provides many filter options to the user, and will always attempt to get as much information as the user requests.
It is capable of reading and exporting to various formats.

## Table of Contents

<!-- toc -->

- [Data Window](#data-window)
  * [Data Window Parameters](#data-window-parameters)
    + [Required Data Window Parameter](#required-data-window-parameter)
    + [Optional Data Window Parameters](#optional-data-window-parameters)
    + [Advanced Optional Data Window Parameters](#advanced-optional-data-window-parameters)
  * [Creating Data Windows](#creating-data-windows)
  * [Using the Data Window Results](#using-the-data-window-results)
  * [Data Window Functions](#data-window-functions)
- [Station](#station)
  * [Station Properties](#station-properties)
  * [Station Functions](#station-functions)
  * [Using Station](#using-station)
- [Sensor Data](#sensor-data)
  * [Sensor Data Properties](#sensor-data-properties)
  * [Sensor Data Functions](#sensor-data-functions)
  * [Sensor Data DataFrame Access](#sensor-data-dataframe-access)
    + [A note on enumerated types](#a-note-on-enumerated-types)
  * [Using Sensor Data](#using-sensor-data)
- [DataWindow Example Code](#datawindow-example-code)

<!-- tocstop -->

## Data Window

DataWindow is a module designed to search for data within a specified start and end time.  It will provide the most complete set of data it can find to the user.

Depending on the request, DataWindow may take some time to complete.  Please have patience when requesting large or lengthy data sets.

DataWindow is accessible through the Redvox SDK. The source for the latest development version of the SDK capable of reading API M data resides in the [api-m branch of the GitHub repository](https://github.com/RedVoxInc/redvox-python-sdk/tree/api-m). Here, you'll also find links to the API documentation and several sets of examples created from Jupyter notebooks.

We recommend installing the SDK through pip. Select the latest version available on [PyPi](https://pypi.org/project/redvox/#history) and follow the "pip install" instructions.

You may find the DataWindow specific API documentation [here](https://redvoxinc.github.io/redvox-sdk/v3.0.0b4/api_docs/redvox/common/data_window.html)

If you want a quick example to copy and paste into your Python IDE, check [here](#4-datawindow-example-code)

_[Table of Contents](#table-of-contents)_

### Data Window Parameters

DataWindow has several parameters that allow you to filter the data being read.  This section will detail the specifics of each parameter.

_[Table of Contents](#table-of-contents)_

#### Required Data Window Parameter
This field is required for DataWindow to run.

_input_dir:_ a string representing the path to the data that will be read into the DataWindow.  Absolute paths are preferred.

_Linux/Mac examples_:
```
input_dir="/absolute/path/to/data_dir"
input_dir="relative/path/to/data_dir"
```

_Windows examples_:
```
input_dir=\absolute\path\to\data_folder"
input_dir="C:\absolute\path\to\data_folder"
input_dir="relative\path\to\data_folder"
```

_[Table of Contents](#table-of-contents)_

#### Optional Data Window Parameters
These fields do not have to be specified when creating a DataWindow.  Default values for each will be given.

Your data must be stored in one of two ways:
1. `Unstructured`: All files exist in the `input_dir`.
2. `Structured`: Files are organized by date and time as specified in the [API-M repo](https://github.com/RedVoxInc/redvox-api-1000/blob/master/docs/standards/filenames_and_directory_structures.md#standard-directory-structure).

_structured_layout:_ a boolean value representing the structure of the input directory.  If `True`, the data is stored in the Structured format.  The default value is `True`.

_start_datetime:_ a datetime object representing the start of the request time for the DataWindow.  All data timestamps*** in the DataWindow will be equal to or greater than this time.  If `None` or not given, uses the earliest timestamp it finds that matches the other filter criteria.  The default value is `None`.

_Examples:_

```
start_datetime=datetime.datetime(2021, 1, 1, 0, 0, 0)
start_datetime=redvox.common.date_time_utils.datetime_from(2021, 1, 1, 0, 0, 0)
```

_end_datetime:_ a datetime object representing the end of the request time for the DataWindow.  All data timestamps*** in the DataWindow will be equal to or less than this time.  If `None` or not given, uses the latest timestamp it finds that matches the other filter criteria.  The default value is `None`.

_Examples:_

```
end_datetime=datetime.datetime(2021, 1, 1, 0, 0, 0)
end_datetime=redvox.common.date_time_utils.datetime_from(2021, 1, 1, 0, 0, 0)
```

*** There may be some location timestamps which are outside the requested range.  This is normal.  They indicate the best position of the station, and the station has not moved since the timestamp of the best location.

_station_ids:_ a list, set, or tuple of station IDs as strings to filter on.  If `None` or not given, will return all IDs that match the other filter criteria.  The default value is `None`.

_Examples:_

```
station_ids=["1234567890", "9876543210", "1122334455"]  # list
station_ids={"1234567890", "9876543210", "1122334455"}  # set
station_ids=("1234567890", "9876543210", "1122334455")  # tuple
```

_apply_correction:_ a boolean value representing the option to automatically adjust the timestamps of retrieved data.  If `True`, each Station in the returned data will apply a correction to all of its timestamps.  The default value is `True`.

_debug:_ a boolean value that controls the output level of DataWindow.  If `True`, DataWindow will output more information when an error occurs.  The default value is `False`.

#### Advanced Optional Data Window Parameters
It is not recommended to change the following parameters from the defaults.

_start_buffer_td:_ a timedelta object representing how much additional time before the start_datetime to add when looking for data.  If `None` or not given, 120 seconds is added.  The default value is `None`.

_Examples:_

```
start_buffer_td=datetime.timedelta(seconds=120)
start_buffer_td=redvox.common.date_time_utils.timedelta(minutes=2)
```

_end_buffer_td:_ a timedelta object representing how much additional time after the end_datetime to add when looking for data.  If `None` or not given, 120 seconds is added.  The default value is `None`.

_Examples:_

```
end_buffer_td=datetime.timedelta(seconds=120)
end_buffer_td=redvox.common.date_time_utils.timedelta(minutes=2)
```

_gap_time_s:_ a float value representing the minimum number of seconds between data timestamps that indicates a gap in the data.  The default is `0.25` seconds.

_Example:_

`gap_time_s=0.25`

_extensions:_ a set of strings representing the file extensions to filter on.  If `None` or not given, will return all files with extensions that match the other filter criteria.  The default value is `None`.

_Example:_

`extensions={".rdvxm", ".rdvxz"}`

_api_versions:_ a set of ApiVersion values representing the file types to filter on.  If `None` or not given, will return all file types that match the other filter criteria.  The default value is `None`.

_Example:_

`api_versions={ApiVersion.API_900, ApiVersion.API_1000}`

_[Table of Contents](#table-of-contents)_

### Creating Data Windows

DataWindows can be created in two ways.  The first is by invoking the initializer function of the class.

```
datawindow = DataWindow(input_dir=input_dir_str),
                        structured_layout=True_or_False,
                        start_datetime=requested_start_datetime,
                        end_datetime=requested_end_datetime,
                        start_buffer_td=start_padding_timedelta,
                        end_buffer_td=end_padding_timedelta,
                        gap_time_s=gap_time_in_seconds,
                        station_ids=list_or_set_of_station_ids,
                        extensions=set_of_extensions,
                        api_versions=set_of_api_versions,
                        apply_correction=True_or_False,
                        debug=True_or_False)
```

You may prefer a simpler version of the code above that uses the defaults for more complex parameters:

```
datawindow = DataWindow(input_dir=input_dir_str),
                        structured_layout=True_or_False,
                        start_datetime=requested_start_datetime,
                        end_datetime=requested_end_datetime,
                        station_ids=list_or_set_of_station_ids,
                        apply_correction=True_or_False)
```

The second is via a config file.

_[Example Config File](data_window.config.toml)_

Once the config file is created, you must create the DataWindow using this function:

`datawindow = DataWindow.from_config_file(path/to/data_window.config.toml)`

The DataWindowConfiguration specific API documentation is available [here](https://redvoxinc.github.io/redvox-sdk/v3.0.0b4/api_docs/redvox/common/data_window_configuration.html)

_[Table of Contents](#table-of-contents)_

### Using the Data Window Results

DataWindow stores all the data gathered in its stations property, which is a dictionary of station IDs to Station data objects.  There are various methods of accessing the Stations:

```
stations_list = datawindow.get_all_stations()  # All stations as a list
station = datawindow.get_station(station_id)   # The station identified by station_id
stations_dict = datawindow.stations            # All id:station entries
station = datawindow.stations[station_id]      # The station identified by station_id
```

We recommend using the get_all_stations() and get_station(station_id) methods to get the Station objects.

Each Station contains SensorData objects, as well as some metadata about the Station.

Refer to the [Station](#2-station) section or the [Station API documentation](https://redvoxinc.github.io/redvox-sdk/v3.0.0b4/api_docs/redvox/common/station.html) for more information about how to use Station objects.

Refer to the [SensorData](#3-sensor-data) section or the [SensorData API documentation](https://redvoxinc.github.io/redvox-sdk/v3.0.0b4/api_docs/redvox/common/station_data.html) for more information about how to use SensorData objects.

Continuing with the example, we will look at the audio sensor of our station in this example:

```
audio_sensor = station.audio_sensor()
print(audio_sensor.sample_rate)             # sample rate in hz
print(audio_sensor.is_sample_rate_fixed)    # is sample rate constant
print(audio_sensor.sample_interval_s)       # sample interval in seconds
print(audio_sensor.sample_interval_std_s)   # sample interval std dev
print(audio_sensor.data_timestamps())       # data timestamps as numpy array
print(audio_sensor.first_data_timestamp())  # first data timestamp
print(audio_sensor.last_data_timestamp())   # last data timestamp
print(audio_sensor.samples())               # the data as an ndarray
print(audio_sensor.num_samples())           # the number of data samples
print(audio_sensor.data_channels())         # the names of the dataframe columns
```

Each line outputs information about the audio sensor.  The data_channels() function tells us the dataframe column names we can use to access the audio sensor's data.

Audio sensors will typically have two data channels, timestamps and microphone.  We can access data channels in the audio sensor using:

`samples = audio_sensor.get_data_channel("microphone")`

Now that we have access to our data, the possibilities are limitless.  Here is a short pyplot example showing the audio data:
```
import matplotlib.pyplot as plt
plt.plot(audio_sensor.data_timestamps() - audio_sensor.first_data_timestamp(), samples)
plt.title(f"{station.id} - audio data")
plt.xlabel(f"microseconds from {requested_start_datetime}")
plt.show()
```

_[Table of Contents](#table-of-contents)_

### Data Window Functions

These functions allow you to access the information in DataWindow.

1. `get_station(station_id: str)`

Returns the Station with ID = station_id, or `None` if the station doesn't exist

_Examples:_
```
station = datawindow.get_station("0000000001")
not_station = datawindow.get_station("not_a_real_station")
assertIsNone(not_station)
```

2. `get_all_stations()`

Returns all Stations as a list.

_Example:_
```
stations = datawindow.get_all_stations()
for station in stations:
    # do stuff
```

3. `get_all_station_ids()`

Returns all station IDs as a list.

_Example:_
```
station_ids = datawindow.get_all_station_ids()
for id in station_ids:
    print(id)
```

Refer to the [DataWindow API documentation](https://redvoxinc.github.io/redvox-sdk/v3.0.0b4/api_docs/redvox/common/data_window.html) as needed.

_[Table of Contents](#table-of-contents)_

## Station

Station is a module designed to hold format-agnostic data of various sensors that combine to form a single unit.  The data can be gathered from and turned into various other formats as needed.

Station represents real world combinations of various recording devices.  Stations may contain several types of devices, such as audio, accelerometer, and pressure sensors.  Stations will not contain more than one of the same type of sensor; this is to allow unambiguous and easy comparison between stations.

Station objects are comprised of a station key, the sensor data, data packet metadata, and other station specific metadata.

Each Station has a unique key.  Keys are comprised of the Station's id, uuid and start timestamp since epoch UTC.  Stations with the same key can be combined into one Station.

Refer to the [Station API documentation](https://redvoxinc.github.io/redvox-sdk/v3.0.0b4/api_docs/redvox/common/station.html) as needed.

_[Table of Contents](#table-of-contents)_

### Station Properties

These are the properties of the Station class:

1. `data`: dictionary of sensor type and sensor data associated with the station, default empty dictionary
2. `metadata`: list of StationMetadata that didn't go into the sensor data, default empty list
3. `id`: string; id of the station, default None
4. `uuid`: string; uuid of the station, default None
5. `start_timestamp`: float; microseconds since epoch UTC when the station started recording, default np.nan
6. `first_data_timestamp`: float; microseconds since epoch UTC of the first data point, default np.nan
7. `station_end_timestamp`: float; microseconds since epoch UTC of the last data point, default np.nan
8. `app_name`: string; the name of the app used to record the data, default empty string
9. `audio_sample_rate_hz`: float; sample rate of audio component in hz, default np.nan
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

Stations may hold data from many sensors attached to the Station.  Access to each of the sensors is quite simple as long as you know the type of sensor you wish to access.

The table below shows the sensor name and the function call required to get to the sensor.

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

Refer to the [SensorData](#3-sensor-data) section on how to access the data.

We recommend only reading information from the Station objects.  
Setting or changing any of the properties in Station may cause unexpected results. 

_[Table of Contents](#table-of-contents)_

## Sensor Data

SensorData is a format-agnostic representation of the data.  This data can be gathered from or converted to another format as needed.

SensorData represents a single real world recording device like a microphone or accelerometer.

Each SensorData object is a Pandas DataFrame with some additional metadata.

Refer to the [SensorData API documentation](https://redvoxinc.github.io/redvox-sdk/v3.0.0b4/api_docs/redvox/common/station_data.html) as needed.

_[Table of Contents](#table-of-contents)_

### Sensor Data Properties

These are the properties of the SensorData class:

1. `name`: string; name of sensor
2. `type`: SensorType; enumerated type of sensor
3. `data_df`: dataframe of the sensor data; always has timestamps as the first column, the other columns are the data fields
4. `sample_rate`: float; sample rate in Hz of the sensor, default np.nan, usually 1/sample_interval_s
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

|Sensor name         |Dataframe columns              |
|--------------------|-------------------------------|
|audio               |microphone                     |
|compressed audio    |compressed_audio, audio_codec  |
|image               |image, image_codec             |
|pressure            |pressure                       |
|light               |light                          |
|proximity           |proximity                      |
|ambient temperature |ambient_temp                   |
|relative humidity   |rel_humidity                   |
|accelerometer       |accelerometer_x, accelerometer_y, accelerometer_z|
|magnetometer        |magnetometer_x, magnetometer_y, magnetometer_z|
|linear acceleration |linear_accel_x, linear_accel_y, linear_accel_z|
|orientation         |orientation_x, orientation_y, orientation_z|
|rotation vector     |rotation_vector_x, rotation_vector_y, rotation_vector_z|
|gyroscope           |gyroscope_x, gyroscope_y, gyroscope_z|
|gravity             |gravity_x, gravity_y, gravity_z|
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
```
from redvox.api1000.wrapped_redvox_packet.station_information import NetworkType, PowerState, CellServiceState
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
```

_[Table of Contents](#table-of-contents)_

### Using Sensor Data

Assuming you have retrieved a Station object, you may access SensorData using the *_sensor() functions of the Station.

_Examples:_
```
station.audio_sensor()     # microphone/audio sensor
station.location_sensor()  # location/gps sensor
station.pressure_sensor()  # barometer/pressure sensor
```

Refer to the tables above for specific column names and functions to access the data.

_Examples:_

```
# get audio data and timestamps:
station.audio_sensor().get_data_channel("microphone")
station.audio_sensor().data_timestamps()

# get accelerometer x channel data, sample rate in hz, and sample interval in seconds
station.accelerometer_sensor().get_data_channel("accelerometer_x")
station.accelerometer_sensor().sample_rate
station.accelerometer_sensor().sample_interval_s
```

_[Table of Contents](#table-of-contents)_

## DataWindow Example Code

Below are a few examples of how to use DataWindow.  Ensure you have installed the latest Redvox SDK.

Update the variables to match your environment before running.

Using the initializer function:
```
import matplotlib.pyplot as plt

from redvox.common.data_window import DataWindow
import redvox.common.date_time_utils as dt


# Variables
input_dir: str = "/path/to/api_dir"
station_ids = ["list", "of", "ids"]
target_station = "id_from_list"
start_timestamp_s: dt.datetime = dt.datetime_from(start_year,
                                                  start_month,
                                                  start_day,
                                                  start_hour,
                                                  start_minute,
                                                  start_second)
end_timestamp_s: dt.datetime = dt.datetime_from(end_year,
                                                end_month,
                                                end_day,
                                                end_hour,
                                                end_minute,
                                                end_second)
apply_correction: bool = True_or_False
structured_layout: bool = True_or_False
# End Variables

datawindow = DataWindow(input_dir=input_dir,
                        structured_layout=structured_layout,
                        start_datetime=start_timestamp_s,
                        end_datetime=end_timestamp_s,
                        station_ids=station_ids,
                        apply_correction=apply_correction)

station = datawindow.get_station(target_station)

print(f"{station.id} Audio Sensor (All timestamps are in microseconds since epoch UTC):\n"
      f"mic sample rate in hz: {station.audio_sensor().sample_rate}\n"
      f"is mic sample rate constant: {station.audio_sensor().is_sample_rate_fixed}\n"
      f"mic sample interval in seconds: {station.audio_sensor().sample_interval_s}\n"
      f"mic sample interval std dev: {station.audio_sensor().sample_interval_std_s}\n"
      f"the data timestamps as a numpy array:\n {station.audio_sensor().data_timestamps()}\n"
      f"the first data timestamp: {station.audio_sensor().first_data_timestamp()}\n"
      f"the last data timestamp:  {station.audio_sensor().last_data_timestamp()}\n"
      f"the data as an ndarray: {station.audio_sensor().samples()}\n"
      f"the number of data samples: {station.audio_sensor().num_samples()}\n"
      f"the names of the dataframe columns: {station.audio_sensor().data_channels()}\n")
      
print("Let's plot the mic data: ")
samples = station.audio_sensor().get_data_channel("microphone")
plt.plot(station.audio_sensor().data_timestamps() -
         station.audio_sensor().first_data_timestamp(),
         samples)
plt.title(f"{station.id}")
plt.xlabel(f"microseconds from {start_timestamp_s}")
plt.show()
```

Using a config file:

_Remember to update your config file to match your environment before running the example_
```
import matplotlib.pyplot as plt

from redvox.common.data_window import DataWindow


# Variables
config_dir: str = "path/to/config.file.toml"
target_station = "id_from_config"
# End Variables

datawindow = DataWindow.from_config_file(config_dir)

station = datawindow.get_station(target_station)

print(f"{station.id} Audio Sensor (All timestamps are in microseconds since epoch UTC):\n"
      f"mic sample rate in hz: {station.audio_sensor().sample_rate}\n"
      f"is mic sample rate constant: {station.audio_sensor().is_sample_rate_fixed}\n"
      f"mic sample interval in seconds: {station.audio_sensor().sample_interval_s}\n"
      f"mic sample interval std dev: {station.audio_sensor().sample_interval_std_s}\n"
      f"the data timestamps as a numpy array:\n {station.audio_sensor().data_timestamps()}\n"
      f"the first data timestamp: {station.audio_sensor().first_data_timestamp()}\n"
      f"the last data timestamp:  {station.audio_sensor().last_data_timestamp()}\n"
      f"the data as an ndarray: {station.audio_sensor().samples()}\n"
      f"the number of data samples: {station.audio_sensor().num_samples()}\n"
      f"the names of the dataframe columns: {station.audio_sensor().data_channels()}\n")
      
print("Let's plot the mic data: ")
samples = station.audio_sensor().get_data_channel("microphone")
plt.plot(station.audio_sensor().data_timestamps() -
         station.audio_sensor().first_data_timestamp(),
         samples)
plt.title(f"{station.id}")
plt.xlabel(f"microseconds from {datawindow.start_datetime}")
plt.show()
```

_[Table of Contents](#table-of-contents)_