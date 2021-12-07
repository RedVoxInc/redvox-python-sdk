# <img src="../img/redvox_logo.png" height="25"> **RedVox Python SDK Data Window Manual**

The RedVox Python SDK contains routines for reading, creating, and writing RedVox API 900 and RedVox API 1000 
data files. The SDK is open-source.

DataWindow is a Python class designed to fetch data from a source.  
It provides many filter options, is capable of reading and exporting to various formats,
and focuses on quickly returning results.

If you wish to learn more about the low-level class used to construct DataWindow, refer to the [Station Documentation](station)

## Table of Contents

<!-- toc -->

- [Data Window](#data-window)
  * [Data Window Parameters](#data-window-parameters)
    + [Strongly Recommended Data Window Parameters](#strongly-recommended-data-window-parameters)
    + [Optional Data Window Parameters](#optional-data-window-parameters)
  * [Event Origin](#event-origin)
  * [Data Window Config](#data-window-config)
    + [Required Config Parameter](#required-config-parameter)
    + [Strongly Config Recommended Parameters](#strongly-recommended-config-parameters)
    + [Optional Config Parameters](#optional-config-parameters)
    + [Advanced Config Optional Parameters](#advanced-optional-config-parameters)
  * [Creating Data Windows](#creating-data-windows)
  * [Using the Data Window Results](#using-the-data-window-results)
  * [Data Window Properties](#data-window-properties)
  * [Data Window Functions](#data-window-functions)
- [Data Window Methodology](#data-window-methodology)
  * [Data Window Initialization](#data-window-initialization)
  * [Data Window File Search](#data-window-file-search)
  * [File Indexing and Timestamp Update](#file-indexing-and-timestamp-update)
  * [Data Aggregation](#data-aggregation)
  * [Data Preparation](#data-preparation)
  * [Data Window Complete](#data-window-complete)
- [Low-Level Data Access](#low-level-data-access)
- [DataWindow Example Code](#datawindow-example-code)
- [Errors and Troubleshooting](#errors-and-troubleshooting)

<!-- tocstop -->

## Data Window

DataWindow is a module designed to search for data within a specified start and end time.  
It will provide the most complete set of data it can find to the user as efficiently as possible.

Depending on the request, DataWindow may take some time to complete.  
Please have patience when requesting large or lengthy data sets.
Data sources without audio channels or data may not load in DataWindow.  For best results, ensure the source of data
contains at least audio data.

DataWindow is accessible through the Redvox SDK. The source for the latest development version of the SDK capable of reading 
API M data resides in the [api-m branch of the GitHub repository](https://github.com/RedVoxInc/redvox-python-sdk/tree/api-m). 
You'll also find links to the API documentation and several sets of examples created from Jupyter notebooks.

We recommend installing the SDK through pip. Select the latest version available on 
[PyPi](https://pypi.org/project/redvox/#history) and follow the "pip install" instructions.

You may find the DataWindow specific API documentation [here](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/data_window.html)

If you want a quick example to copy and paste into your Python IDE, check [here](#datawindow-example-code)

_[Table of Contents](#table-of-contents)_

### Data Window Parameters

The primary way to create a DataWindow is to invoke its constructor. The constructor has several parameters that allow 
you to customize its behavior.  This section will detail the specifics of each parameter.

_[Table of Contents](#table-of-contents)_

#### Strongly Recommended Data Window Parameters
We strongly recommend setting these parameters when creating a DataWindow.

If these parameters are not set, the given default values will be used.

`event_name`: a string that identifies the DataWindow.  We recommend using descriptive names.  Default is `"dw"`.  If there 
is data in the DataWindow and event_name is still `dw`, it will be updated to `dw_[start_date]_[num_stations]`, 
where `[start_date]` is the first timestamp of the data and `[num_stations]` is the number of stations in the DataWindow 

`event_origin`: Optional EventOrigin object that describes the origin point of the event of interest.  Default is `None`.
Using the default will create an empty EventOrigin.  See the section on [EventOrigin](#event-origin) for more details.

`config`: Optional DataWindowConfig object that describes the parameters of the DataWindow.  Default is `None`.  If there is no
DataWindowConfig, no data will be collected.  See the section on [DataWindowConfig](#data-window-config) for more details.

`out_dir`: a string that identifies the directory to save the DataWindow to.  Default `"."`, or current directory.

`out_type`: a string that identifies the method to save the DataWindow.  Default is `"NONE"` (no saving).

#### Optional Data Window Parameters
This parameter does not have to be set when creating a DataWindow.

`debug`: a boolean value that controls the output level of DataWindow.  If `True`, DataWindow will output more information
when an error occurs.  The default value is `False`.

_[Table of Contents](#table-of-contents)_

### Event Origin
This class defines the location of a source of data.

All parameters for this class are optional.

`provider`: a string that identifies the source of the location data (i.e. "GPS" or "NETWORK"), default is "UNKNOWN"

`lat`: a float value of the latitude in degrees, default is np.nan

`lat_std`: a float value of the latitude standard deviation, default is np.nan

`lon`: a float value of the longitude in degrees, default is np.nan

`lon_std`: a float value of the longitude standard deviation, default is np.nan

`alt`: a float value of the altitude in meters, default is np.nan

`alt_std`: a float value of the altitude standard deviation, default is np.nan

`event_radius_m`: a float value of the event's radius in meters, default is 0.0

_[Table of Contents](#table-of-contents)_

### Data Window Config
This class defines the dimensions of a DataWindow

#### Required Config Parameter
This field is required for any non-empty DataWindowConfig.

`input_dir`: a string representing the path to the data that will be read into the DataWindow.  Absolute paths are preferred.

_Linux/Mac examples_:
```python
input_dir="/absolute/path/to/data_dir"
input_dir="relative/path/to/data_dir"
```

_Windows examples_:
```python
# This example assumes your Windows Python environment requires the backslash character to be escaped
input_dir="\\absolute\\path\\to\\data_folder"
input_dir="C:\\absolute\\path\\to\\data_folder"
input_dir="relative\\path\\to\\data_folder"
```

#### Strongly Recommended Config Parameters

If these parameters are not set, your results will not be aligned.

These parameters are not required to run DataWindow.  Default values are given.

`start_datetime`: a datetime object representing the start of the request time in UTC for the DataWindow.  
All data timestamps in the DataWindow will be equal to or greater than this time.  If `None` or not given, uses the 
earliest timestamp it finds that matches the other filter criteria.  The default value is `None`.

_Examples:_

```python
import datetime
import redvox.common.date_time_utils as dt_utils


start_datetime=datetime.datetime(2021, 1, 1, 0, 0, 0)
start_datetime=dt_utils.datetime_from(2021, 1, 1, 0, 0, 0)
# using epoch seconds
start_datetime=dt_utils.datetime_from_epoch_seconds_utc(1609459200)
```

`end_datetime`: a datetime object representing the end of the request time in UTC for the DataWindow.  
All data timestamps in the DataWindow will be less than this time.  If `None` or not given, uses the latest timestamp 
it finds that matches the other filter criteria.  The default value is `None`.

_Examples:_

```python
import datetime
import redvox.common.date_time_utils as dt_utils


end_datetime=datetime.datetime(2021, 1, 1, 0, 1, 0)
end_datetime=dt_utils.datetime_from(2021, 1, 1, 0, 1, 0)
# using epoch seconds
start_datetime=dt_utils.datetime_from_epoch_seconds_utc(1609459260)
```

### A Note on Time:
All timestamps used in DataWindow are in [UTC](https://www.timeanddate.com/time/aboututc.html).

_[Table of Contents](#table-of-contents)_

#### Optional Config Parameters
These parameters do not have to be set when creating a DataWindow.  Default values for each will be given.

First, please note that your data must be stored in one of two ways:
1. `Unstructured`: All files exist directly in the `input_dir`.
2. `Structured`: Files are organized by date and time as specified in the [API-M repo](https://github.com/RedVoxInc/redvox-api-1000/blob/master/docs/standards/filenames_and_directory_structures.md#standard-directory-structure).

<a id="structured-layout"></a>
`structured_layout`: a boolean value representing the structure of the input directory.  If `True`, the data is stored 
in the Structured format.  The default value is `True`.

`station_ids`: a list, set, or tuple of station IDs as strings to filter on.  If `None` or not given, will return all 
IDs that match the other filter criteria.  The default value is `None`.

_Examples:_

```python
station_ids=["1234567890", "9876543210", "1122334455"]  # list
station_ids={"1234567890", "9876543210", "1122334455"}  # set
station_ids=("1234567890", "9876543210", "1122334455")  # tuple
```

`apply_correction`: a boolean value representing the option to automatically adjust the timestamps of retrieved data.
If `True`, each Station in the returned data will apply a correction to all of its timestamps.  The default value is `True`.

#### Advanced Optional Config Parameters
We do not recommend changing the following parameters from the defaults.

`start_buffer_td`: a timedelta object representing how much additional time before the start_datetime to add when looking for data.
Negative values are changed to 0 seconds.  If `None` or not given, 120 seconds is added.  The default value is `None`.

_Examples:_

```python
import datetime
import redvox.common.date_time_utils
start_buffer_td=datetime.timedelta(seconds=120)
start_buffer_td=redvox.common.date_time_utils.timedelta(minutes=2)
```

`end_buffer_td`: a timedelta object representing how much additional time after the end_datetime to add when looking for data.
Negative values are changed to 0 seconds.  If `None` or not given, 120 seconds is added.  The default value is `None`.

_Examples:_

```python
import datetime
import redvox.common.date_time_utils
end_buffer_td=datetime.timedelta(seconds=120)
end_buffer_td=redvox.common.date_time_utils.timedelta(minutes=2)
```

`drop_time_s`: a float value representing the minimum number of seconds between data files that indicates a gap in the data.
Negative values are changed to the default.  The default is `0.2` seconds.

_Example:_

```python
drop_time_s=0.2
```

`extensions`: a set of strings representing the file extensions to filter on.  If `None` or not given, will return all 
files with extensions that match the other filter criteria. The default value is `None`.

_Example:_

```python
extensions={".rdvxm", ".rdvxz"}
```

`api_versions`: a set of ApiVersion values representing the file types to filter on.  If `None` or not given, will return all 
file types that match the other filter criteria.  The default value is `None`.

_Example:_

```python
from redvox.common.io import ApiVersion
api_versions={ApiVersion.API_900, ApiVersion.API_1000}
```

`copy_edge_points`: enumerated value representing behavior when creating data points on the edge of the data. 
If not given, the default is to copy values. The default value is `DataPointCreationMode.COPY`.  
Possible values for this parameter are:
```python
from redvox.common.gap_and_pad_utils import DataPointCreationMode
DataPointCreationMode.NAN           # use np.nan (or appropriate defaults) for edge data points
DataPointCreationMode.COPY          # copy the closest point inside the window
DataPointCreationMode.INTERPOLATE   # find the interpolation between the closest inside and outside points at the edge
```

`use_model_correction`: a boolean value which determines if the offset model's correction functions are used to correct
the timestamps.  If False, uses the best offset for correction.  The default value is `True`

_[Table of Contents](#table-of-contents)_

### Creating Data Windows

DataWindows can be created by invoking the initializer function of the class.
We will also need to set up a few of the parameters to the initializer function.

```python
from redvox.common.data_window import DataWindow, DataWindowConfig, EventOrigin
source = EventOrigin(
    provider="UNKNOWN",
    lat=latitude_in_degrees,
    lat_std=latitude_stdev,
    lon=longitude_in_degrees,
    lon_std=longitude_stdev,
    alt=altitude_in_meters,
    alt_std=altitude_stdev,
    event_radius_m=radius_in_meters
)
config = DataWindowConfig(
    input_dir=input_dir_str,
    structured_layout=True_or_False,
    start_datetime=requested_start_datetime,
    end_datetime=requested_end_datetime,
    start_buffer_td=start_padding_timedelta,
    end_buffer_td=end_padding_timedelta,
    drop_time_s=gap_time_in_seconds,
    station_ids=list_or_set_of_station_ids,
    extensions=set_of_extensions,
    api_versions=set_of_api_versions,
    apply_correction=True_or_False,
    use_model_correction=True_or_False,
    copy_edge_points=edge_point_creation_mode
)
datawindow = DataWindow(
    event_name=my_event_name,
    event_origin=source,
    config=config,
    out_dir=output_dir_str,
    out_type=type_str,
    debug=True_or_False
)
```

You may prefer a simpler version of the code above that uses the defaults for more complex parameters:

```python
# note that the source location will be undefined
from redvox.common.data_window import DataWindow, DataWindowConfig
config = DataWindowConfig(input_dir=input_dir_str,
                          structured_layout=True_or_False,
                          start_datetime=requested_start_datetime,
                          end_datetime=requested_end_datetime,
                          station_ids=list_or_set_of_station_ids,
                          apply_correction=True_or_False)
datawindow = DataWindow(event_name=my_event_name,
                        config=config,
                        out_dir=output_dir_str,
                        out_type=type_str)
```

The second is via a config file.

_[Example Config File](data_window.config.toml)_

Once the config file is created, you must create the DataWindow using this function:

```python
datawindow = DataWindow.from_config_file("path/to/data_window.config.toml")
```

The DataWindowConfiguration specific API documentation is available [here](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/data_window_configuration.html)

_[Table of Contents](#table-of-contents)_

### Using the Data Window Results

DataWindow stores all the data gathered in its `_stations` property, which is a list of Station data objects.  
These are the methods to access the Stations:

```python
station_list = datawindow.stations()  # All stations as a list
first_station = datawindow.first_station()  # The first station in the list
first_with_id = datawindow.first_station(station_id)  # The first station that matches the station_id
# A list of stations identified by station_id, uuid, and start timestamp
stations = datawindow.get_station(station_id, station_uuid, station_start_timestamp)
```

We recommend using the datawindow.stations() to get all the Station objects and datawindow.get_station() to get specific Stations.

Each Station contains data from the sensors, as well as some metadata about the Station.

Refer to the [Station](station) documentation or the [Station API documentation](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/station.html) for more information about how to use Station objects.

Continuing with the example, we will look at the audio sensor of our station in this example:

```python
station = station_list[0]
audio_sensor = station.audio_sensor()
print(audio_sensor.sample_rate_hz)          # sample rate in hz
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

As a reminder, all timestamps are in [UTC](https://www.timeanddate.com/time/aboututc.html).

Each line outputs information about the audio sensor.

Audio sensors will typically have two data channels, timestamps and microphone. 
We can access the microphone data in the audio sensor using:

```python
samples = audio_sensor.get_microphone_data()
```

Now that we have access to our data, the possibilities are limitless.  Here is a short pyplot example showing the audio data:
```python
import matplotlib.pyplot as plt
plt.plot(audio_sensor.data_timestamps() - audio_sensor.first_data_timestamp(), samples)
plt.title(f"{station.id} - audio data")
plt.xlabel(f"microseconds from {requested_start_datetime}")
plt.show()
```

We can even save our DataWindow and load it later. We currently support two formats: a compressed file and parquet.
Both formats produce a JSON file that contains metadata about the DataWindow.  The JSON file is critical when loading 
DataWindow. Please note that loading DataWindows is much faster than going through the entire creation process.

The format is determined by the DataWindow parameter `out_type`, and the save directory is determined by `out_dir`.
```python
# save the DataWindow based on its parameters
path_to_file = datawindow.save()
```

Loading the DataWindow requires the full path to the JSON file created during the saving process.
```python
# load a previously created DataWindow
datawindow = DataWindowArrow.load(path_to_file)
```

_[Table of Contents](#table-of-contents)_

### Data Window Properties
This is the list of all properties you can access from DataWindow. Many of the values are set via the parameters above.  
Some properties do not have the same name as the initialization parameters.  Defaults for values will be given if
applicable.  All timestamps are in UTC.

* `event_name`: string, identifier for the event.  Default "dw".  Note that when creating a DataWindow, any "dw" event 
  names will be updated to `dw_[start_date]_[num_stations]`, where `[start_date]` is the first timestamp of 
  the data and `[num_stations]` is the number of stations in the DataWindow
* `event_origin`: EventOrigin, class containing position data for the event source.  Default empty EventOrigin
* `config`: DataWindowConfig, class containing Data Window configuration parameters.   Default `None`.  If there is no
  DataWindowConfig, no data will be collected.
* `debug`: boolean, if True, outputs additional information during run time.  Default `False`

This is the list of properties that are set by the SDK during creation of the DataWindow:

* `_sdk_version`: string, version of the SDK used to create the DataWindow.  Set by the SDK during run time.
* `_errors`: RedVoxExceptions, stores any errors found during run time.  Set by the SDK during run time.
* `_stations`: List of Stations, stores all Stations found during run time.  Default empty list

This property is set via the initialization parameters and cannot be changed without using specific functions:

* `_fs_writer`: DataWindowFileSystemWriter, uses the event_name, out_type and out_dir parameters to define how and 
  where to save the DataWindow.

### Event Origin Properties
This is a list of all properties you can access from EventOrigin.  These values are set via the initialization parameters.
Defaults for values will be given.

* `provider`: string, source of the location data (i.e. GPS or NETWORK).  Default UNKNOWN
* `latitude`: float, best estimate of latitude in degrees.  Default np.nan
* `latitude_std`: float, standard deviation of best estimate of latitude.  Default np.nan
* `longitude`: float, best estimate of longitude in degrees, default np.nan
* `longitude_std`: float, standard deviation of best estimate of longitude, default np.nan
* `altitude`: float, best estimate of altitude in meters, default np.nan
* `altitude_std`: float, standard deviation of best estimate of altitude, default np.nan
* `event_radius_m`: float, radius of event in meters, default 0.0

### Data Window Config Properties
This is a list of all properties you can access from DataWindowConfig.  These values are set via the parameters above.
Defaults for values will be given if applicable.  All timestamps are in [UTC](https://www.timeanddate.com/time/aboututc.html).

_It is not recommended to set or change the properties of DataWindowConfig after the DataWindow is created._

* `input_directory`: string, directory that contains the files to read data from.  Required parameter.
* `structured_layout`: bool, if True, the input_directory contains specially named and organized directories of data.  Default True
* `station_ids`: optional set of strings, representing the station ids to filter on. If empty or None, get any ids found in the input directory.  Default None
* `extensions`: optional set of strings, representing file extensions to filter on. If None, gets as much data as it can in the input directory.  Default None
* `api_versions`: optional set of ApiVersions, representing api versions to filter on. If None, get as much data as it can in the input directory.  Default None
* `start_datetime`: optional datetime, start datetime of the window. If None, uses the first timestamp of the filtered data.  Default None
* `end_datetime`: optional datetime, non-inclusive end datetime of the window. If None, uses the last timestamp of the filtered data.  Default None
* `start_buffer_td`: timedelta, the amount of time to include before the start_datetime when filtering data. Default 2 minutes
* `end_buffer_td`: timedelta, the amount of time to include after the end_datetime when filtering data. Default 2 minutes
* `drop_time_s`: float, the minimum amount of seconds between data files that would indicate a gap. Default .2 seconds
* `apply_correction`: bool, if True, update the timestamps in the data based on best station offset.  Default True
* `use_model_correction`: bool, if True, use the offset model's correction functions, otherwise use the best offset.  Default True
* `copy_edge_points`: enumeration of DataPointCreationMode, determines how new values are created in the station data.
  Valid values are NAN, COPY, and INTERPOLATE.  Default COPY

_[Table of Contents](#table-of-contents)_

### Data Window Functions

1. `stations() -> List[StationPa]`

Returns a list of all the Stations in the DataWindow.

2. `get_station(station_id: str, station_uuid: Optional[str] = None, start_timestamp: Optional[float] = None) -> Optional[List[Station]]`

Returns a list of Stations with ID == station_id and if given, UUID == station_uuid and start date == start_timestamp,
or `None` if the station doesn't exist.

station_uuid and start_timestamp are optional; the station_id will often be enough to get a result.

_Examples:_
```python
station_list = datawindow.get_station("0000000001")
not_station = datawindow.get_station("not_a_real_station")
assertIsNone(not_station)
```

2. `first_station(station_id: Optional[str] = None) -> Optional[StationPa]`

Returns the first Station with ID == station_id if given or just the first Station in the list of stations.
If a station_id is given and no station matches, returns `None`.

_Examples:_
```python
single_station = datawindow.first_station("0000000001")
not_station = datawindow.first_station("not_a_real_station")
assertIsNone(not_station)
first_station = datawindow.first_station()
```

3. `station_ids() -> List[str]`

Returns a list of all Station ids in the DataWindow.

4. `start_date() -> float`

Returns the earliest data timestamp in the DataWindow or `np.nan` if there are no stations.

5. `end_date() -> float`

Returns the latest data timestamp in the DataWindow or `np.nan` if there are no stations.

6. `sdk_version() -> str`

Returns the SDK version used to create the DataWindow.

7. `save_dir() -> str`

Returns the directory used to save the DataWindow.

8. `fs_writer() -> FileSystemWriter`

Returns the FileSystemWriter object that stores the information about saving to the file system.

9. `set_out_type(new_out_type: str)`

Sets the output type of the DataWindow to the parameter new_out_type.  Accepted values are: "NONE", "PARQUET", "LZ4"

10. `print_errors()`

Prints the errors encountered while creating a DataWindow.

### Data Window Save and Load Functions

These functions allow you to save and load DataWindow objects.

1. `save() -> Path`

Saves the DataWindow to disk (if saving is enabled) and returns the Path to the save directory.
Creates an error if saving is not enabled.

2. `load(file_path: str) -> DataWindow`

Loads a DataWindow using the JSON file specified by the parameter file_path.

Refer to the [DataWindow API documentation](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/data_window.html) as needed.

_[Table of Contents](#table-of-contents)_

## Data Window Methodology

Creating a Data Window involves many processes of varying complexity.  This section will break down and explain each step taken in the creation of the Data Window.

_[Table of Contents](#table-of-contents)_

### Data Window Initialization

When creating a DataWindow, the parameters of its creation are stored for future reference.
Each parameter used to create the DataWindow is saved to its respective property.  If the parameter is not specified, 
the default value is saved.

Once the parameters are saved, the DataWindow begins aggregating and updating the data requested.

### Data Window File Search

DataWindow uses several methods in the Redvox SDK to gather the files needed to complete the request.

If the user specified a structured directory, we look for directories specifically named `api900` and/or `api1000` 
either as part of the input directory or within the input directory.

Next, we read through the sub-directories of the api directory, which are organized by year, month, day and for api1000 
data, by hour as well. 

If the user specified an unstructured directory, we are looking at all files within the input directory.

We add the buffer times to the requested start and end times to get our query start and end times, then get any file 
with a timestamp within our query times.  We index the files for later analysis.

### File Indexing and Timestamp Update
All timestamps are in [UTC](https://www.timeanddate.com/time/aboututc.html).

1. Once all files are indexed, if we had a requested start or end time, we gather basic information from each file and 
   use that to update the file timestamps to match our request times.
   * If we don't have a requested start and end time, we go straight to Data Aggregation

2. Each recording device will have some amount of offset, which is a difference in the device's time to "true" time.
   * We can account for this offset by utilizing the basic information from each file to create an offset model.  
     We _**always**_ ADD our offset values to device time to get "true" time.

3. Once we have the offset model, we can calculate the "true" time for our gathered data.  To do so, we take the data's 
   timestamps and add the offset from the model to it.

4. If we specified a start and/or end time for our request, we must make sure our data's "true" times are able to 
   satisfy the request. We now want two things to be true:
   * The "true" start time of the data is before or equal to our request start time
   * The "true" end time of the data is after our request end time
  
5. If both of the conditions are true, we have all the data we need and can continue to Data Aggregation.
   
6. If at least one of the two conditions is not true, we will update the query by increasing the corresponding side's
   buffer (default 2 minutes) that failed the criteria by 1.5 times the difference in "true" time and request time. 
   This efficiently expands our search criteria to guarantee our next query will get what we need.
   
7. We continue to Data Aggregation after our second query.

### Data Aggregation

Once the data is retrieved, it must be aggregated and prepared for the user.

1. If there is sufficient RAM, all data files are completely read into memory.  If RAM is not enough, the files will
   be written to a directory on the file system.  The directory is specified by the DataWindow parameters if saving is
   enabled, otherwise it is a temporary directory.

2. The data files are organized into Station objects.  Files are put into a station if and only if each of these values 
   are equal across each file: station id, station uuid, station start timestamp and station metadata.
   * Any change in the station's information will create a new Station object to represent that change.

3. Station objects attempt to fill any recognizable gaps in their sensors.

* Any errors encountered while creating the Station object will be recorded and can be displayed to the user.

### Data Preparation

The data is now organized by Station.  This process will be performed on all Stations in the DataWindow.

1. If apply_correction is True, update all timestamps in the Station using the offset model.  This is the final 
   timestamp update before the user gets the data.

2. Remove any Audio data points outside the request window.

3. Create Audio data points with NaN data values and timestamps based on the Audio sample rate such that the entire Audio record fills 
   the request window and there are no points greater than 2 sample intervals apart or data points outside the window.

4. Remove data points from each non-audio sensor that are outside the request window.

5. Create two rows in each sensor's dataframe with timestamps equal to the start and end timestamps of the trimmed audio sensor.
   * The copy_edge_points parameter determines which data values of these fabricated points will contain.
    
6. Update the Station metadata.  This does not include the Station's timesync data.
   * Note that the Timesync data for a Station is unaltered from the data gathered during operation.
   
7. Update the Data Window metadata to match the data.

### Data Window Complete

The Data Window has completed all operations and is ready for you to use!

_[Table of Contents](#table-of-contents)_

## Low-Level Data Access

DataWindow uses Station objects to hold its processed data.

Refer to [Station Documentation](station) for more information.

_[Table of Contents](#table-of-contents)_

## DataWindow Example Code

Below are a few examples of how to use DataWindow.  Ensure you have installed the latest Redvox SDK.

Update the variables to match your environment before running.

Quick Start:
```python
from redvox.common.data_window import DataWindow

input_dir: str = "/path/to/api_dir"
# for Windows, delete the above line and use the line below instead:
# input_dir: str = "C:\\path\\to\\api_dir

if __name__ == "__main__":
    datawindow = DataWindow(input_dir=input_dir)

    station = datawindow.stations[0]
    
    print(f"{station.id} Audio Sensor (All timestamps are in microseconds since epoch UTC):\n"
          f"mic sample rate in hz: {station.audio_sensor().sample_rate_hz}\n"
          f"is mic sample rate constant: {station.audio_sensor().is_sample_rate_fixed}\n"
          f"mic sample interval in seconds: {station.audio_sensor().sample_interval_s}\n"
          f"mic sample interval std dev: {station.audio_sensor().sample_interval_std_s}\n"
          f"the data timestamps as a numpy array:\n {station.audio_sensor().data_timestamps()}\n"
          f"the first data timestamp: {station.audio_sensor().first_data_timestamp()}\n"
          f"the last data timestamp:  {station.audio_sensor().last_data_timestamp()}\n"
          f"the data as an ndarray: {station.audio_sensor().samples()}\n"
          f"the number of data samples: {station.audio_sensor().num_samples()}\n"
          f"the names of the dataframe columns: {station.audio_sensor().data_channels()}\n")
```


Using the initializer function to display a specific station:
```python
import matplotlib.pyplot as plt

from redvox.common.data_window import DataWindowConfig, DataWindow
import redvox.common.date_time_utils as dt


# Variables
input_dir: str = "/path/to/api_dir"
# for Windows, delete the above line and use the line below instead:
# input_dir: str = "C:\\path\\to\\api_dir
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

config = DataWindowConfig(input_dir=input_dir,
                          structured_layout=structured_layout,
                          start_datetime=start_timestamp_s,
                          end_datetime=end_timestamp_s,
                          station_ids=station_ids,
                          apply_correction=apply_correction)

datawindow = DataWindow(config=config)

station = datawindow.first_station(target_station)

print(f"{station.id} Audio Sensor (All timestamps are in microseconds since epoch UTC):\n"
      f"mic sample rate in hz: {station.audio_sensor().sample_rate_hz}\n"
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
samples = station.audio_sensor().get_microphone_data()
plt.plot(station.audio_sensor().data_timestamps() -
         station.audio_sensor().first_data_timestamp(),
         samples)
plt.title(f"{station.id}")
plt.xlabel(f"microseconds from {start_timestamp_s}")
plt.show()
```

Using a config file to do the same as above:

_[Example Config File](data_window.config.toml)_
_Remember to update your config file to match your environment before running the example_
```python
import matplotlib.pyplot as plt

from redvox.common.data_window import DataWindowConfig, DataWindow


# Variables
config_dir: str = "path/to/config.file.toml"
# for Windows, delete the above line and use the line below instead:
# config_dir: str = "C:\\path\\to\\config.file.toml
target_station = "id_from_config"
# End Variables

datawindow = DataWindow.from_config_file(config_dir)

station = datawindow.first_station(target_station)

print(f"{station.id} Audio Sensor (All timestamps are in microseconds since epoch UTC):\n"
      f"mic sample rate in hz: {station.audio_sensor().sample_rate_hz}\n"
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
samples = station.audio_sensor().get_microphone_data()
plt.plot(station.audio_sensor().data_timestamps() -
         station.audio_sensor().first_data_timestamp(),
         samples)
plt.title(f"{station.id}")
plt.xlabel(f"microseconds from {datawindow.start_datetime}")
plt.show()
```

_[Table of Contents](#table-of-contents)_

## Errors and Troubleshooting

Below are troubleshooting tips in the event DataWindow does not run properly

* Check if the redvox SDK is installed.

* If you can't access the DataWindow class, include this line to import DataWindow into your project:
`from redvox.common.data_window import DataWindow`

### If your files aren't loading through DataWindow:

* Enable the debug parameter in DataWindow to display any errors encountered while creating DataWindow.
```python
datawindow = DataWindow(event_name=my_event_name,
                        # ...
                        debug=True)
```

* Check the value of `input_dir` for any errors, and that the files within the directory are in one of two formats 
(structured or unstructured) described in the [Optional Data Window Parameters](#structured-layout) section.
Use the appropriate value for the `structured` parameter of DataWindowConfig.

* When working with structured directories, ensure that all API 1000 (API M) files are in a directory called `api1000` 
and all API 900 files are in a directory called `api900`.  API 1000 files normally end in `.rdvxm` and API 900 files
normally end in `.rdvxz`

* Adjust the start and end datetime values of DataWindow, as described in the 
[Strongly Recommended Data Window Parameters](#strongly-recommended-data-window-parameters) section.
Timestamps are in [UTC](https://www.timeanddate.com/time/aboututc.html).  Use the 
[date time utilities](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/date_time_utils.html) 
provided in `redvox.common.date_time_utils` to convert UTC epoch times into datetimes.

* Check your files for non-typical extensions.  `.rdvxm` and `.rdxvz` are the two expected file extensions.
If you have other file extensions, those files may not work with DataWindow.

_[Table of Contents](#table-of-contents)_
