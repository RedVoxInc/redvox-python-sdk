# <img src="../img/redvox_logo.png" height="25"> **RedVox Python SDK Data Window Manual**

The RedVox Python SDK contains routines for reading, creating, and writing RedVox API 900 and RedVox API 1000 data files. The SDK is open-source.

DataWindowFast is a Python class designed to fetch data from a source.  It provides many filter options to the user while focusing on quick returns.
It is capable of reading and exporting to various formats.

If you wish to learn more about the low-level class used to construct DataWindowFast, refer to the [Station Documentation](station)

## Table of Contents

<!-- toc -->

- [Data Window Fast](#data-window-fast)
  * [Data Window Fast Parameters](#data-window-fast-parameters)
    + [Required Data Window Fast Parameter](#required-data-window-fast-parameter)
    + [Strongly Recommended Data Window Fast Parameters](#strongly-recommended-data-window-fast-parameters)
    + [Optional Data Window Fast Parameters](#optional-data-window-fast-parameters)
    + [Advanced Optional Data Window Fast Parameters](#advanced-optional-data-window-fast-parameters)
  * [Creating Data Windows](#creating-data-windows)
  * [Using the Data Window Fast Results](#using-the-data-window-fast-results)
  * [Data Window Fast Functions](#data-window-fast-functions)
- [Data Window Fast Methodology](#data-window-fast-methodology)
  * [Data Window Fast Initialization](#data-window-fast-initialization)
  * [Data Window Fast File Search](#data-window-fast-file-search)
  * [File Indexing and Timestamp Update](#file-indexing-and-timestamp-update)
  * [Data Aggregation](#data-aggregation)
  * [Data Preparation](#data-preparation)
  * [Data Window Fast Complete](#data-window-fast-complete)
- [Low-Level Data Access](#low-level-data-access)
- [DataWindowFast Example Code](#datawindowfast-example-code)

<!-- tocstop -->

## Data Window Fast

DataWindowFast is a module designed to search for data within a specified start and end time.  It will provide as much of data it can find to the user.

Depending on the request, DataWindowFast may take some time to complete.  Please have patience when requesting large or lengthy data sets.

DataWindowFast is accessible through the Redvox SDK. The source for the latest development version of the SDK capable of reading API M data resides in the [api-m branch of the GitHub repository](https://github.com/RedVoxInc/redvox-python-sdk/tree/api-m). Here, you'll also find links to the API documentation and several sets of examples created from Jupyter notebooks.

We recommend installing the SDK through pip. Select the latest version available on [PyPi](https://pypi.org/project/redvox/#history) and follow the "pip install" instructions.

You may find the DataWindowFast specific API documentation [here](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/data_window.html)

If you want a quick example to copy and paste into your Python IDE, check [here](#datawindowfast-example-code)

_[Table of Contents](#table-of-contents)_

### Data Window Fast Parameters

DataWindowFast has several parameters that allow you to filter the data being read.  This section will detail the specifics of each parameter.

_[Table of Contents](#table-of-contents)_

#### Required Data Window Fast Parameter
This field is required for DataWindowFast to run.

_input_dir:_ a string representing the path to the data that will be read into the DataWindowFast.  Absolute paths are preferred.

_Linux/Mac examples_:
```python
input_dir="/absolute/path/to/data_dir"
input_dir="relative/path/to/data_dir"
```

_Windows examples_:
```python
input_dir="\absolute\path\to\data_folder"
input_dir="C:\absolute\path\to\data_folder"
input_dir="relative\path\to\data_folder"
```

#### Strongly Recommended Data Window Fast Parameters

We strongly recommend setting these parameters when creating a Data Window.

If these parameters are not set, your results will not be aligned.

These parameters are not required to run Data Window.  Default values are given.

_start_datetime:_ a datetime object representing the start of the request time for the DataWindowFast. 
All data timestamps*** in the DataWindowFast will be equal to or greater than this time.  If `None` or not given, uses the earliest timestamp it finds that matches the other filter criteria.  The default value is `None`.

_Examples:_

```python
import datetime
import redvox.common.date_time_utils
start_datetime=datetime.datetime(2021, 1, 1, 0, 0, 0)
start_datetime=redvox.common.date_time_utils.datetime_from(2021, 1, 1, 0, 0, 0)
```

_end_datetime:_ a datetime object representing the end of the request time for the DataWindowFast. 
All data timestamps*** in the DataWindowFast will be equal to or less than this time.  If `None` or not given, uses the latest timestamp it finds that matches the other filter criteria.  The default value is `None`.

_Examples:_

```python
import datetime
import redvox.common.date_time_utils
end_datetime=datetime.datetime(2021, 1, 1, 0, 1, 0)
end_datetime=redvox.common.date_time_utils.datetime_from(2021, 1, 1, 0, 1, 0)
```

*** There may be some location timestamps which are outside the requested range.  This is normal.  They indicate the best position of the station, and the station has not moved since the timestamp of the best location.

_[Table of Contents](#table-of-contents)_

#### Optional Data Window Fast Parameters
These parameters do not have to be set when creating a DataWindowFast.  Default values for each will be given.

First, please note that your data must be stored in one of two ways:
1. `Unstructured`: All files exist in the `input_dir`.
2. `Structured`: Files are organized by date and time as specified in the [API-M repo](https://github.com/RedVoxInc/redvox-api-1000/blob/master/docs/standards/filenames_and_directory_structures.md#standard-directory-structure).

_structured_layout:_ a boolean value representing the structure of the input directory.  If `True`, the data is stored in the Structured format.  The default value is `True`.

_station_ids:_ a list, set, or tuple of station IDs as strings to filter on.  If `None` or not given, will return all IDs that match the other filter criteria.  The default value is `None`.

_Examples:_

```python
station_ids=["1234567890", "9876543210", "1122334455"]  # list
station_ids={"1234567890", "9876543210", "1122334455"}  # set
station_ids=("1234567890", "9876543210", "1122334455")  # tuple
```

_apply_correction:_ a boolean value representing the option to automatically adjust the timestamps of retrieved data.  If `True`, each Station in the returned data will apply a correction to all of its timestamps.  The default value is `True`.

_debug:_ a boolean value that controls the output level of DataWindow.  If `True`, DataWindow will output more information when an error occurs.  The default value is `False`.

#### Advanced Optional Data Window Fast Parameters
We do not recommend changing the following parameters from the defaults.
If your results appear to be incorrect or you are seeing errors in the logs, try adjusting these values to get more data.

_start_buffer_td:_ a timedelta object representing how much additional time before the start_datetime to add when looking for data.  If `None` or not given, 120 seconds is added.  The default value is `None`.

_Examples:_

```python
import datetime
import redvox.common.date_time_utils
start_buffer_td=datetime.timedelta(seconds=120)
start_buffer_td=redvox.common.date_time_utils.timedelta(minutes=2)
```

_end_buffer_td:_ a timedelta object representing how much additional time after the end_datetime to add when looking for data.  If `None` or not given, 120 seconds is added.  The default value is `None`.

_Examples:_

```python
import datetime
import redvox.common.date_time_utils
end_buffer_td=datetime.timedelta(seconds=120)
end_buffer_td=redvox.common.date_time_utils.timedelta(minutes=2)
```

_drop_time_s:_ a float value representing the minimum number of seconds between files of data that indicates a gap in the data.  The default is `0.2` seconds.

_Example:_

`drop_time_s=0.2`

_extensions:_ a set of strings representing the file extensions to filter on.  If `None` or not given, will return all files with extensions that match the other filter criteria.  The default value is `None`.

_Example:_

```python
extensions={".rdvxm", ".rdvxz"}
```

_api_versions:_ a set of ApiVersion values representing the file types to filter on.  If `None` or not given, will return all file types that match the other filter criteria.  The default value is `None`.

_Example:_

```python
from redvox.common.io import ApiVersion
api_versions={ApiVersion.API_900, ApiVersion.API_1000}
```

_copy_edge_points:_ enumerated value representing behavior when creating data points on the edge of the data.  If not given, the default is to copy values. 
The default value is `DataPointCreationMode.COPY`.  Possible values for this parameter are: 
```python
from redvox.common.gap_and_pad_utils import DataPointCreationMode
DataPointCreationMode.NAN           # use np.nan (or appropriate defaults) for edge data points
DataPointCreationMode.COPY          # copy the closest point inside the window
DataPointCreationMode.INTERPOLATE   # find the interpolation between the closest inside and outside points at the edge
```


_[Table of Contents](#table-of-contents)_

### Creating Data Windows

DataWindowFast can be created in two ways.  The first is by invoking the initializer function of the class.

```python
from redvox.common.data_window import DataWindowFast
datawindow = DataWindowFast(input_dir=input_dir_str,
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
                            copy_edge_points=edge_point_creation_mode,
                            debug=True_or_False)
```

You may prefer a simpler version of the code above that uses the defaults for more complex parameters:

```python
from redvox.common.data_window import DataWindowFast
datawindow = DataWindowFast(input_dir=input_dir_str,
                            structured_layout=True_or_False,
                            start_datetime=requested_start_datetime,
                            end_datetime=requested_end_datetime,
                            station_ids=list_or_set_of_station_ids,
                            apply_correction=True_or_False)
```

The second is via a config file.

_[Example Config File](data_window.config.toml)_

Once the config file is created, you must create the DataWindowFast using this function:

`datawindow = DataWindowFast.from_config_file(path/to/data_window.config.toml)`

The DataWindowConfiguration specific API documentation is available [here](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/data_window_configuration.html)

_[Table of Contents](#table-of-contents)_

### Using the Data Window Fast Results

DataWindowFast stores all the data gathered in its stations property, which is a list Station data objects.

```python
station_list = datawindow.stations  # All stations as a list
# A list of stations identified by station_id, uuid, and start timestamp
stations = datawindow.get_station(station_id, station_uuid, station_start_timestamp)
```

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
print(audio_sensor.samples())               # the data (no timestamps) as an ndarray
print(audio_sensor.num_samples())           # the number of data samples
print(audio_sensor.data_channels())         # the names of the dataframe columns
```

Each line outputs information about the audio sensor.  The data_channels() function tells us the dataframe column names we can use to access the audio sensor's data.

Audio sensors will typically have three data channels; timestamps, unaltered_timestamps and microphone.  We can access data channels in the audio sensor using:

`samples = audio_sensor.get_data_channel("microphone")`

Now that we have access to our data, the possibilities are limitless.  Here is a short pyplot example showing the audio data:
```python
import matplotlib.pyplot as plt
plt.plot(audio_sensor.data_timestamps() - audio_sensor.first_data_timestamp(), samples)
plt.title(f"{station.id} - audio data")
plt.xlabel(f"microseconds from {requested_start_datetime}")
plt.show()
```

We can even save our DataWindowFast as a file for later.  Saving the DataWindowFast allows it to be loaded quickly, instead of going through the entire creation process.
```python
from redvox.common.io import serialize_data_window_fast, data_window_fast_to_json_file
serialize_data_window_fast(data_window=datawindow,
                           base_dir=output_dir,
                           file_name=serialized_file_name)
data_window_fast_to_json_file(data_window=datawindow,
                              base_dir=output_dir,
                              file_name=json_file_name,
                              compression_format="lz4")
```

_[Table of Contents](#table-of-contents)_

### Data Window Fast Functions

These functions allow you to access the information in DataWindowFast.

1. `get_station(station_id: str, station_uuid: Optional[str] = None, start_timestamp: Optional[float] = None)`

Returns a list of Stations with ID = station_id and if given, UUID = station_uuid and start date = start_timestamp,
or `None` if the station doesn't exist

station_uuid and start_timestamp are optional; the station_id will often be enough to get a result

_Examples:_
```python
station = datawindow.get_station("0000000001")
not_station = datawindow.get_station("not_a_real_station")
assertIsNone(not_station)
```

These functions allow you to save and load DataWindow objects.

1. `serialize(base_dir: str = ".", file_name: Optional[str] = None, compression_factor: int = 4)`

Serializes and compresses the DataWindowFast to a file.  The file will have the format: `base_dir/file_name`.

If no base directory is provided, uses the current directory (".")

If no file name is provided, the default file name is `[start_ts]_[end_ts]_[num_stations].pkl.lz4`

Compression_factor is a value between 1 and 12. Higher values provide better compression, but take longer (default=4).

Returns the path to the written file.

_Example:_
```python
from redvox.common.data_window import DataWindowFast
datawindow: DataWindowFast
datawindow.serialize(output_dir, "dw_serial.pkl.lz4")
```

2. `deserialize(path: str)`

Decompresses and deserializes a DataWindow written to disk.

Returns the DataWindow.

_Example:_
```python
from redvox.common.data_window import DataWindowFast
datawindow: DataWindowFast
datawindow.deserialize(f"{output_dir}/dw_serial.pkl.lz4")
```

3. `to_json_file(base_dir: str = ".", file_name: Optional[str] = None, compression_format: str = "lz4")`

Serializes and compresses the DataWindowFast to a file, then saves metadata about the DataWindowFast to a JSON file.

The compressed DataWindowFast is placed into a subdirectory named "dw" in the base_dir

If no base directory is provided, uses the current directory (".")

If no file name is provided, the default file name is `[start_ts]_[end_ts]_[num_stations]`

_Do not include a file extension with the file name_

Valid values for compression_format: `"lz4", "pkl"`

The metadata saved is:
* Start datetime
* End datetime
* List of Station ids

_Example:_
```python
from redvox.common.data_window import DataWindowFast
datawindow: DataWindowFast
datawindow.to_json_file(output_dir, "dw_serial", "lz4")
```

4. `to_json(self, compressed_file_base_dir: str = ".", compressed_file_name: Optional[str] = None, compression_format: str = "lz4")`

Serializes and compresses the DataWindowFast to a file, then saves metadata about the DataWindowFast to a JSON string.

The compressed DataWindowFast is placed into a subdirectory named "dw" in the base_dir

If no base directory is provided, uses the current directory (".")

If no file name is provided, the default file name is `[start_ts]_[end_ts]_[num_stations]`

_Do not include a file extension with the file name_

Valid values for compression_format: `"lz4", "pkl"`

The metadata saved is:
* Start datetime
* End datetime
* List of Station ids

_Example:_
```python
from redvox.common.data_window import DataWindowFast
datawindow: DataWindowFast
datawindow.to_json(output_dir, "dw_serial", "lz4")
```

5. `from_json_file(base_dir: str, file_name: str, dw_base_dir: Optional[str] = None, start_dt: Optional[dtu.datetime] = None, end_dt: Optional[dtu.datetime] = None, station_ids: Optional[Iterable[str]] = None)`

Reads a JSON file describing a DataWindowFast, then checks the metadata against the user's requirements.

Returns a DataWindowFast if successful and None if not.

In order for the DataWindowFast to be loaded, all of these must be true:
* The start datetime of the DataWindowFast must be at or before the start_dt parameter
* The end datetime of the DataWindowFast must be at or after the end_dt parameter
* The DataWindowFast must contain all the ids specified in the station_ids parameter

If any of the above three parameters are not specified, their respective conditions will be considered True.

_Example:_
```python
from redvox.common.data_window import DataWindowFast
dw = DataWindowFast.from_json(base_dir, file_name)
dw = DataWindowFast.from_json(base_dir, file_name, start_dt=datetime(2020, 1, 1, 0, 0, 0))
dw = DataWindowFast.from_json(base_dir, file_name, end_dt=datetime(2020, 12, 31, 0, 0, 0))
dw = DataWindowFast.from_json(base_dir, file_name, station_ids=["1234567890", "9876543210"])
dw = DataWindowFast.from_json(base_dir, file_name, start_dt=datetime(2020, 1, 1, 0, 0, 0), end_dt=datetime(2020, 12, 31, 0, 0, 0), station_ids=["1234567890", "9876543210"])
```

6. `from_json(json_str: str, dw_base_dir: str, start_dt: Optional[dtu.datetime] = None, end_dt: Optional[dtu.datetime] = None, station_ids: Optional[Iterable[str]] = None)`

Reads a JSON string describing a DataWindowFast, then checks the metadata against the user's requirements.
The compressed DataWindowFast object must be in the dw_base_dir specified.

Returns a DataWindowFast if successful and None if not.

In order for the DataWindowFast to be loaded, all of these must be true:
* The start datetime of the DataWindowFast must be at or before the start_dt parameter
* The end datetime of the DataWindowFast must be at or after the end_dt parameter
* The DataWindowFast must contain all the ids specified in the station_ids parameter

If any of the above three parameters are not specified, their respective conditions will be considered True.

_Example:_
```python
from redvox.common.data_window import DataWindowFast
dw = DataWindowFast.from_json(json_str, base_dir_dw)
dw = DataWindowFast.from_json(json_str, base_dir_dw, start_dt=datetime(2020, 1, 1, 0, 0, 0))
dw = DataWindowFast.from_json(json_str, base_dir_dw, end_dt=datetime(2020, 12, 31, 0, 0, 0))
dw = DataWindowFast.from_json(json_str, base_dir_dw, station_ids=["1234567890", "9876543210"])
dw = DataWindowFast.from_json(json_str, base_dir_dw, start_dt=datetime(2020, 1, 1, 0, 0, 0), end_dt=datetime(2020, 12, 31, 0, 0, 0), station_ids=["1234567890", "9876543210"])
```

Refer to the [DataWindowFast API documentation](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/data_window.html) as needed.

_[Table of Contents](#table-of-contents)_

## Data Window Fast Methodology

Creating a Data Window Fast involves many processes of varying complexity.  This section will break down and explain each step taken in the creation of the Data Window.

_[Table of Contents](#table-of-contents)_

### Data Window Fast Initialization

When creating a Data Window, the parameters of its creation are stored for future reference. 
Each parameter used to create the Data Window is saved to its respective property.  If the parameter is not specified, the default value is saved.

This process always occurs, regardless of the exact method of DataWindowFast creation.

Once the parameters are saved, the Data Window begins aggregating and updating the data requested.

### Data Window Fast File Search

DataWindowFast uses several methods in the Redvox SDK to gather the files needed to complete the request.

If the user specified a structured directory, we are looking for directories specifically named `api900` and/or `api1000` either as part of the input directory or within the input directory.  Next, we read through the sub-directories of the api directory, which are organized by year, month, day and for api1000 data, by hour as well. 

If the user specified an unstructured directory, we are looking at all files within the input directory.

We add the buffer times to the requested start and end times to get our query start and end times, then get any file with a timestamp within our query times.  We index the files for later analysis.

### File Indexing and Timestamp Update

1. Once all files are indexed, if we had a requested start or end time, we gather basic information from each file and use that to update the file timestamps to match our request times.
   * If we don't have a requested start and end time, we go straight to Data Aggregation

2. We use UTC as the time zone for our data request.  Each recording device will have some amount of offset (LINK HERE), which is a difference in the device's time to "true" time.
   * We can account for this offset by utilizing the basic information from each file to create an offset model (LINK HERE).  We _**always**_ ADD our offset values to device time to get "true" time.

3. Once we have the offset model, we can calculate the "true" time for our gathered data.  We simply take our data's timestamps and add the offset from the model to it.

### Data Aggregation

Once the data is retrieved, it must be aggregated and prepared for the user.

1. All data files are completely read into memory.

2. The data files are organized into Station objects.  Files are put into a station if and only if each of these values are equal across each file: station id, station uuid, station start timestamp and station metadata.

3. Station objects attempt to fill any recognizable gaps in their sensors.

* Any errors encountered while creating the Station object will cause the Data Window to stop.  Information about which value(s) that were not consistent will be displayed.

### Data Preparation

The data is now organized by Station.  This process will be performed on all Stations in the Data Window.

1. Update all timestamps in the Station using the offset model.  This is the final timestamp update before the user gets the data.

2. Check for Audio sensor data.  No Audio sensor data means the Station isn't useful to us, and will be discarded before the user sees it.

3. Remove any Audio data points outside the request window.

4. Remove data points from each non-audio sensor that are outside the request window.  There is one caveat to this step:
   * We will create two rows in each sensor's dataframe with timestamps equal to the start and end timestamps of the trimmed audio sensor.
   * The copy_edge_points parameter determines which data values of these fabricated points will contain.

5. Update the Station metadata.

6. Update the Data Window Fast metadata to match the data.

### Data Window Fast Complete

The Data Window has completed all operations and is ready for you to use!

_[Table of Contents](#table-of-contents)_

## Low-Level Data Access

DataWindowFast uses Station objects to hold its processed data.

Refer to [Station Documentation](station) for more information.

_[Table of Contents](#table-of-contents)_

## DataWindow Example Code

Below are a few examples of how to use DataWindowFast.  Ensure you have installed the latest Redvox SDK.

Update the variables to match your environment before running.

Using the initializer function:
```python
import matplotlib.pyplot as plt

from redvox.common.data_window import DataWindowFast
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

datawindow = DataWindowFast(input_dir=input_dir,
                            structured_layout=structured_layout,
                            start_datetime=start_timestamp_s,
                            end_datetime=end_timestamp_s,
                            station_ids=station_ids,
                            apply_correction=apply_correction)

station = datawindow.get_station(target_station)[0]

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
```python
import matplotlib.pyplot as plt

from redvox.common.data_window import DataWindowFast


# Variables
config_dir: str = "path/to/config.file.toml"
target_station = "id_from_config"
# End Variables

datawindow = DataWindowFast.from_config_file(config_dir)

station = datawindow.get_station(target_station)[0]

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
samples = station.audio_sensor().get_data_channel("microphone")
plt.plot(station.audio_sensor().data_timestamps() -
         station.audio_sensor().first_data_timestamp(),
         samples)
plt.title(f"{station.id}")
plt.xlabel(f"microseconds from {datawindow.start_datetime}")
plt.show()
```

_[Table of Contents](#table-of-contents)_
