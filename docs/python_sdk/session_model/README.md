# <img src="../img/redvox_logo.png" height="25"> **RedVox Python SDK SessionModel Manual**

SessionModel creates a short summary of a set of data, and provides this information faster than creating a 
[DataWindow](../data_window).  SessionModel can be used to determine the usefulness of a set or subset of data.

## Table of Contents

<!-- toc -->

- [SessionModel](#sessionmodel)
  * [Create SessionModel](#create-sessionmodel)
    + [From Directory of Files](#from-directory-of-files)
    + [Single Packet](#single-packet)
    + [Many Packets](#many-packets)
    + [Existing SessionModel](#existing-sessionmodel)
  * [Update SessionModel](#update-sessionmodel)
  * [Using SessionModel](#using-sessionmodel)
    + [Sealing SessionModel](#sealing-sessionmodel)
  * [SessionModel Parameters](#sessionmodel-parameters)
  * [SessionModel Properties](#sessionmodel-properties)
  * [SessionModel Functions](#sessionmodel-functions)
- [LocationStats](#locationstats)
  * [LocationStat](#locationstat)
- [ApiReaderModel](#apireadermodel)
- [DataWindow](#datawindow)
- [SessionModel Example Code](#sessionmodel-example-code)
- [Errors and Troubleshooting](#errors-and-troubleshooting)

<!-- tocstop -->

## SessionModel

SessionModel is a module designed to read files quickly and summarize the information within each file.  This summary 
can be merged with other summaries within the same session.

A session is defined as the period of a station that runs continuously from the moment the station starts recording to 
the moment the station stops recording.  Depending on the availability of data, SessionModel may not capture the 
actual entirety of the session.

SessionModel presents the data as is, and will never adjust or correct the data.  It is up to the user to use the 
information obtained from SessionModel to arrive at their own conclusions or perform corrections for future data 
queries.

SessionModel is intended to be an open object until the end of the session, with new information constantly being added 
as it becomes available.  If the information flow stops and the session ends, SessionModel can be 
[sealed](#sealing-sessionmodel) to prevent any future changes to the SessionModel.

If you want a quick example to copy and paste into your Python IDE, check [here](#sessionmodel-example-code)

### Create SessionModel

SessionModel is created using one or more packets of data.  There are three identifiers of a SessionModel.  If you 
create a SessionModel with multiple packets, only the packets with identifiers that all match the first packet's will be 
used.  The three identifiers are:
* Station ID
* Station UUID
* Station Start Date

We recommend [creating SessionModel from files](#from-directory-of-files) if you have a fixed set of files to work 
with.  If you are streaming files into a system, refer to the section [Update SessionModel](#update-sessionmodel). 

#### From Directory of Files

If you have a directory of files, use the ApiReaderModel module to create a SessionModel for each session in the data.
```python
from redvox.common.api_reader import ApiReaderModel


# read files to create models
path_to_files = "/PATH/TO/FILES/"
api_rm = ApiReaderModel(path_to_files, structured_dir=True)

# get the first model
first_model = api_rm.session_models[0]

# print all models' information
for s in api_rm.session_models: 
    print(s)
```

Refer to the section [ApiReaderModel](#apireadermodel) for more information on how to use the module.

#### Single Packet

If you only have a single packet to read from, use the function `create_from_packet()`.
```python
from redvox.common.session_model import SessionModel
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM


# This function only works if the packet is in API M format.
# Note that this is a trivial example and you will have to load the packet using your preferred method.
my_packet: RedvoxPacketM = RedvoxPacketM()
s_model = SessionModel.create_from_packet(my_packet)
```

#### Many Packets

If you have several packets to read from, use the function `create_from_stream()`.  Note that all packets must have the
same 3 unique identifiers as the first packet in the stream, otherwise the packet being read will be ignored.

```python
from redvox.common.session_model import SessionModel
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from typing import List


# This function only works if the packets are in API M format.
# Note that this is a trivial example and you will have to load the packets using your preferred method.
my_packets: List[RedvoxPacketM] = [RedvoxPacketM()]
s_model = SessionModel.create_from_stream(my_packets)
```

#### Existing SessionModel

If you already have a `session_model.json` or `session_model.pkl` file to read from, use the function `load()`.

```python
from redvox.common.session_model import SessionModel


# Also works with .pkl files
my_file_path = "/FULL/PATH/TO/SESSION_MODEL.json"
s_model = SessionModel.load(my_file_path)
```

### Update SessionModel

The recommended use of SessionModel is to run a script that will examine files as they become available and pass them
into the correct SessionModel to update it.

```python
# This code only approximates an environment with streaming data.  Adapt this code as necessary.

from redvox.common.session_model import SessionModel
import redvox.common.io as io
from typing import Dict, Tuple


session_models: Dict[Tuple[str, str, float], SessionModel] = {}

files_path = "/PATH/TO/FILE/STREAM/"
# Files are assumed to be stored in a structured format
index = io.index_structured(files_path)
# Use the line below if files are stored in unstructured format
# index = io.index_unstructured(files_path)

# Read the contents of the files, one file at a time
for p in index.read_contents():    
    # Get the unique identifier for a session
    key = (p.station_information.id, p.station_information.uuid, p.timing_information.app_start_mach_timestamp)
    # Create a new session if it doesn't exist or add to an existing one
    if key not in session_models.keys():
        session_models[key] = SessionModel.create_from_packet(p)
    else:
        session_models[key].add_data_from_packet(p)
```

If you have a fixed set of files, use one of the [creation methods](#create-sessionmodel) above to read all the files 
at once.

### Using SessionModel

A SessionModel is intended to remain open and untouched as long as data for the session can be obtained.  You may 
obtain information about the session at any point during this period, but any information obtained this way may become 
obsolete at any moment.

```python
from redvox.common.session_model import SessionModel


# Note that this is a trivial example and you will need to create a SessionModel using one of the methods above
s_model: SessionModel = SessionModel()
# Print all the information
print(s_model)

# Print properties of the model
print(s_model.session_version())
print(s_model.id)
print(s_model.uuid)
print(s_model.start_date)
print(s_model.app_name)
print(s_model.app_version)
print(s_model.api)
print(s_model.sub_api)
print(s_model.make)
print(s_model.model)
print(s_model.station_description)
print(s_model.packet_duration_s)
print(s_model.num_packets)
print(s_model.first_data_timestamp)
print(s_model.last_data_timestamp)
print(s_model.is_sealed)

# Print the nominal audio sample rate in hz
print(s_model.audio_sample_rate_nominal_hz())

# Print information about the sensors in the session
print(s_model.num_sensors())
print(s_model.list_of_sensors())
print(s_model.get_all_sensors())

# Print information about a specific sensor
sensor_name: str = "SENSORNAMEHERE"
print(s_model.get_sensor_data(sensor_name))

# Print the model's duration in microseconds
print(s_model.model_duration())

# Print time synchronization information
print(s_model.num_timesync_points)
print(s_model.first_latency_timestamp())
print(s_model.last_latency_timestamp())
print(s_model.mean_latency)
print(s_model.mean_offset)
print(s_model.offset_model)

# Print GPS time synchronization information
print(s_model.num_gps_points)
print(s_model.gps_offset)

# Print location information
print(s_model.location_stats)
print(s_model.has_moved)
```

You may finalize a SessionModel by sealing it.  Sealing a model prevents any more data from being added and causes all 
statistics about the model to be calculated.

#### Sealing SessionModel

Sealing a SessionModel requires calling the function `seal_model()`.

```python
from redvox.common.session_model import SessionModel


# Note that this is a trivial example and you will need to create a SessionModel using one of the methods above
s_model: SessionModel = SessionModel()
s_model.seal_model()
```

### SessionModel Parameters

This section will cover the parameters required by the base SessionModel module.  This is invoked if you ever have only 
metadata for a session.  It is unlikely you will create a SessionModel without any data.
This section is included for your reference.

* `station_id`: string, id of the station.  Default "" (empty string).
* `uuid`: string, uuid of the station.  Default "" (empty string).
* `start_timestamp`: float, timestamp from epoch UTC when station was started.  Default np.nan.
* `api`: float, api version of data.  Default np.nan.
* `sub_api`: float, sub-api version of data.  Default np.nan.
* `make`: string, make of station.  Default "" (empty string).
* `model`: string, model of station.  Default "" (empty string).
* `station_description`: string, station description.  Default "" (empty string).
* `app_name`: string, name of the app on station.  Default "Redvox".
* `sensors`: Optional dictionary of sensor name and sample rate in hz.  Default None.

### SessionModel Properties

This section details all properties of the SessionModel.

* `id`: string, id of the station.  Default "" (empty string).
* `uuid`: string, uuid of the station.  Default "" (empty string).
* `start_date`: float, timestamp since epoch UTC of when station was started.  Default np.nan.
* `app_name`: string, name of the app the station is running.  Default "Redvox".
* `app_version`: string, version of the app the station is running.  Default "" (empty string).
* `api`: float, version number of the API the station is using.  Default np.nan.
* `sub_api`: float, version number of the sub-API the station in using.  Default np.nan.
* `make`: string, make of the station.  Default "" (empty string).
* `model`: string, model of the station.  Default "" (empty string).
* `station_description`: string, text description of the station.  Default "" (empty string).
* `packet_duration_s`: float, length of station's data packets in seconds.  Default np.nan.
* `num_packets`: int, number of files used to create the model.  Default 0.
* `first_data_timestamp`: float, timestamp of the first data point used to create the model.  Default np.nan.
* `last_data_timestamp`: float, timestamp of the last data point used to create the model.  Default np.nan.
* `has_moved`: bool, if True, location changed during session.  Default False.
* `location_stats`: LocationStats, container for number of times a location source has appeared the mean, and the 
  standard deviation of the data points.  Default empty LocationStats.
* `best_latency`: float, the best latency of the model.  Default np.nan.
* `num_timesync_points`: int, the number of timesync data points.  Default 0.
* `mean_latency`: float, mean latency of the model.  Default np.nan.
* `mean_offset`: float, mean offset of the model.  Default np.nan.
* `num_gps_points`: int, the number of gps data points.  Default 0.
* `gps_offset`: optional tuple of (float, float), the slope and intercept (in that order) of the gps timing 
  calculations.  Default None.
* `is_sealed`: bool, if True, the SessionModel will not accept any more data.  This means the offset model and gps
  offset values are the best they can be, given the available data.  Default False.

These are privatized properties that users cannot edit:

* `_session_version`: string, the version of the SessionModel.
* `_first_timesync_data`: CircularQueue, container for the first 15 points of timesync data; timestamp, latency, offset.  
  Default empty CircularQueue.
* `_last_timesync_data`: CircularQueue, container for the last 15 points of timesync data.  Default empty CircularQueue.
* `_first_gps_data`: CircularQueue, container for the first 15 points of GPS offset data; timestamp and offset.
  Default empty CircularQueue.
* `_last_gps_data`: CircularQueue, container for the last 15 points of GPS offset data.  Default empty CircularQueue.
* `_sensors`: dictionary of str: float, the name of sensors and their mean sample rate as a dictionary.  Default empty.
* `_sdk_version`: string, the version of the SDK used to create the model.
* `_errors`: RedVoxExceptions, contains any errors found when creating the model.

CircularQueue is a structure designed to hold up to a specified amount of values.  If the queue is full, it can either 
deny adding new values or overwrite the oldest value with a new value.

### SessionModel Functions

These are the functions SessionModel can invoke:

* `as_dict() -> dict`: returns the SessionModel as a dictionary.
* `from_json_dict(json_dict: dict) -> "SessionModel"`: converts the `json_dict` into a SessionModel returns it.
* `compress(self, out_dir: str = ".") -> Path`: compresses the SessionModel into a .pkl file and saved in directory 
  named `out_dir`.  Returns the path to the saved file.
* `save(self, out_type: str = "json", out_dir: str = ".") -> Path`: saves the SessionModel as a JSON or pickle file in
  the directory named `out_dir`.  Accepts only "pkl" and "json" for `out_type`.  Defaults to JSON file output if 
  out_type is not recognized.  Returns the path to the saved file.
* `load(file_path: str) -> "SessionModel"`: converts the JSON or pickle file located in `file_path` and converts it 
  into a SessionModel.  Will raise an error if the file is not a .json or .pkl file.
* `print_errors(self)`: prints all errors encountered by the SessionModel.
* `session_version(self) -> str`: returns the session version of the SessionModel.
* `audio_sample_rate_nominal_hz(self) -> float`: returns the SessionModel's expected nominal sample rate of the audio 
  sensor as hz.
* `add_data_from_packet(self, packet: api_m.RedvoxPacketM) -> "SessionModel"`: adds the data from a single API M Redvox 
  packet to the SessionModel.  Does not do anything if the unique identifiers of the packet do not match the 
  SessionModel's.  Returns the updated SessionModel.
* `set_sensor_data(self, packet: api_m.RedvoxPacketM)`: overwrites any existing sensor data with data from the API M 
  Redvox packet.  CAUTION: Any existing sensor data will be unrecoverable.  Use at your own risk.
* `create_from_packet(packet: api_m.RedvoxPacketM) -> "SessionModel"`: used to create a SessionModel from a single API M
  Redvox packet.  See [Creating SessionModel from a Single Packet](#single-packet).
* `add_from_data_stream(self, data_stream: List[api_m.RedvoxPacketM]) -> "SessionModel"`: adds the data from a stream of
  API M Redvox packets.  Ignores any packet that does not match the unique identifier of the SessionModel.  Returns the 
  updated SessionModel.
* `create_from_stream(data_stream: List[api_m.RedvoxPacketM]) -> "SessionModel"`: used to create a SessionModel from a 
  list of API M Redvox packets.  Uses the first packet's information to initialize the SessionModel, and will ignore any
  packet that does not match the first packet's unique identifiers.  See 
  [Creating SessionModel from Many Packets](#many-packets).
* `num_sensors(self) -> int`: returns the number of sensors in the SessionModel.
* `list_of_sensors(self) -> List[str]`: returns the names of the sensors in the SessionModel as a list of strings.
* `get_all_sensors(self) -> Dict`: returns the names of the sensors and their associated data as a dictionary.
* `get_sensor_data(self, sensor: str) -> Optional[float]`: returns the data of a specific `sensor`.  Returns None if the
  sensor doesn't exist in the SessionModel.
* `get_all_sensor_data(self) -> List[float]`: returns all the sensor data as a list.
* `model_duration(self) -> float`: returns the duration of the data used to create the model in microseconds.
* `first_latency_timestamp(self) -> float`: returns the first timesync timestamp associated with the first latency 
  value.  Returns np.nan if the timestamp doesn't exist.
* `last_latency_timestamp(self) -> float`: returns the last timesync timestamp associated with the last latency value. 
  Returns np.nan if the timestamp doesn't exist.
* `get_offset_model(self) -> OffsetModel`: returns the OffsetModel based on the available timesync data.  Updates the 
  `offset_model` property as well.  This model may differ from one created by a DataWindow on the same set of data.
* `get_gps_offset(self) -> Tuple[float, float]`: returns the offset model created by using available gps data.  Updates 
  the `gps_offset` property as well.  This model may differ from one created using all the gps data points.
* `seal_model(self)`: seals the model, preventing any more data from being added to it.  Calculates the offset model and
  gps offset model.  Sets the `_first_timesync_data`, `_last_timesync_data`, `_first_gps_data`, `_last_gps_data`  
  properties to None to conserve space.

## LocationStats

LocationStats is a module that contains a group of LocationStat objects.  These functions allow you to interact with 
the data:

* `get_all_stats(self) -> List[LocationStat]`: return all LocationStat objects as a list.
* `get_sources(self) -> List[str]`: return all LocationStat sources as a list.  Use the results of this for possible 
  inputs for the other functions.
* `get_stats_for_source(self, source: str) -> Optional[LocationStat]`: return the LocationStat with the specified 
  `source` or None if it doesn't exist.
* `has_source(self, source: str) -> bool`: return True if the `source` has a LocationStat.

### LocationStat

LocationStat is a module that stores the statistical summary of data for one source of location data.  It is capable of 
automatically calculating the variance and standard deviation if exactly one of those is given.  If both are given, it 
assumes that the values of both are correct.

You can access the properties of a LocationStat directly:

* `source_name`: string, the name of the source of the location data.  Default "" (empty string).
* `count`: int, the number of data points used to calculate the stats.  Default 0.
* `means`: tuple of (float, float, float), the mean of the latitude, longitude and altitude, in that order.  Default 
  (np.nan, np.nan, np.nan).
* `variance`: optional tuple of (float, float, float), the variance of the latitude, longitude and altitude, in that 
  order.  Default (0, 0, 0).
* `std_dev`: optional tuple of (float, float, float), the standard deviation of the latitude, longitude and altitude, 
  in that order.  Default (0, 0, 0).

## ApiReaderModel

ApiReaderModel is a specialized variant of the ApiReader module.  It is specifically designed to create one SessionModel
for each of the sessions it finds.

* `base_dir`: string, the directory containing the files to read.
* `structured_dir`: bool, if True, `base_dir` follows the Structured format listed below.  If False, data is 
  Unstructured.  Default False.
* `read_filter`: ReadFilter for the data files, if None, gets everything.  You can read more about using 
  [ReadFilter here](https://github.com/RedVoxInc/redvox-python-sdk/blob/master/docs/python_sdk/low_level_api.md#selectively-filtering-data).
  Default None.
* `debug`: boolean, if True, output program warnings/errors during function execution.  Default False.

#### A Note on Directory Structure
Redvox data must be stored in one of two ways:
1. `Unstructured`: All files exist directly in the `base_dir`.
2. `Structured`: Files are organized by date and time as specified in the 
  [API-M repo](https://github.com/RedVoxInc/redvox-api-1000/blob/master/docs/standards/filenames_and_directory_structures.md#standard-directory-structure).

## DataWindow

DataWindow is a module that will compile and update Redvox data.  It is an involved process that will take much longer 
than creating a SessionModel, but will provide a more complete view of the data.  More information can be found at the 
[DataWindow Documentation](../data_window)

## SessionModel Example Code

Ensure you have installed the latest [Redvox SDK](https://pypi.org/project/redvox/) before running this example.

This example assumes you have downloaded a structured set of .rdvxm files.  Several methods are available to get such 
files:
* [Redvox website](https://redvox.io/#/home)
* [CLI Cloud Download](https://github.com/RedVoxInc/redvox-python-sdk/tree/master/docs/python_sdk/cli#cloud-download-command-details)
* [CLI data req](https://github.com/RedVoxInc/redvox-python-sdk/tree/master/docs/python_sdk/cli#data-req-command-details)

We will use the ApiReaderModel module to access our data and automatically create as many SessionModel objects as 
needed.
```python
# Some sessions may not have enough data to create an offset model.  If any of the SessionModel does not
# create a graph, try removing that station from the data or using a different data set.
from redvox.common.api_reader import ApiReaderModel
import redvox.common.date_time_utils as dt
import matplotlib.pyplot as plt
import numpy as np


# Update this to match your environment
files_path = "/PATH/TO/DATA"

reader = ApiReaderModel(files_path, True)
for m in reader.session_models:
  print(m)
  
  # display the offset model as a plot
  mos = m.get_offset_model()
  # evenly spaced x values
  lmts = np.linspace(0, m.last_latency_timestamp() - m.first_latency_timestamp(), m.num_timesync_points)
  plt.plot(lmts / 1e6, (mos.slope * lmts + mos.intercept) / 1e6, label="offsetmodel")
  plt.title(f"{m.id} offset model")
  plt.ylabel("latency in seconds")
  plt.xlabel(f"seconds from {dt.datetime_from_epoch_microseconds_utc(m.first_latency_timestamp())}")
  
  plt.show()
```

## Errors and Troubleshooting

Any statistics calculated from SessionModel are subject to errors.  Use [DataWindow](../data_window) for best accuracy 
of the whole data set.

If you are not seeing any results from creating a SessionModel, check that the target directory contains the correct 
files.

You are more likely to use the ApiReaderModel module to create SessionModel from large sets of data.  The SessionModel 
[constructor methods](#create-sessionmodel) are intended for advanced users who want to investigate specific sets of 
data.  Refer to the [example code](#sessionmodel-example-code) for a quick example on how to use ApiReaderModel to get 
SessionModel.

Unless you are working with a stream of data, any SessionModel you create is the best summary given the existing data.
You may want to [seal](#sealing-sessionmodel) any SessionModel created from a discrete set of files on disk.

Remember that any SessionModel that can be fed more data is considered open, and the summary can change depending on 
the added data.  Evaluate the summary only if the SessionModel is sealed.