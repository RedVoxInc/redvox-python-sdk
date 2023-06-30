# <img src="../img/redvox_logo.png" height="25"> **RedVox Python SDK SessionModel Manual**

This readme is about the SDK specific SessionModel built from local files.  We recommend that you use the cloud 
to obtain updated Session Model(s).  For more information about cloud Session Models, refer to this (LINK GOES HERE).

SessionModel creates a short summary of a set of local files, in a faster time than creating a 
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

The SDK version of SessionModel is provided specifically for use with local Redvox files.  We recommend utilizing the 
cloud version of Session Model to get more accurate data.  More information about cloud Session Models (LINK GOES HERE).
Of note, the SDK version of SessionModel uses the cloud version as its base.  You can read more about the structure of 
SessionModel [here](#sessionmodel-properties)

If you want a quick example to copy and paste into your Python IDE, check [here](#sessionmodel-example-code)

### Create SessionModel

SessionModel is created using one or more packets of data.  There are three identifiers of a SessionModel.  If you 
create a SessionModel with multiple packets, only the packets with identifiers that all match the first packet's will be 
used.  The three identifiers are:
* Station's ID
* Station's UUID
* Station's Start Date

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
# Note that this is a trivial example, and you will have to load the packet using your preferred method.
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
# Note that this is a trivial example, and you will have to load the packets using your preferred method.
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

If you are streaming files into a system, use the `LocalSessionModels` class and pass in the incoming packet.  You can 
access the sessions from the class at your convenience.

```python
# This code only approximates an environment with streaming data.  Adapt this code as necessary.

from redvox.common.session_model import SessionModel, LocalSessionModels
import redvox.common.io as io
from typing import Dict, Tuple


session_models: LocalSessionModels = LocalSessionModels()

files_path = "/PATH/TO/FILE/STREAM/"
# Files are assumed to be stored in a structured format
index = io.index_structured(files_path)
# Use the line below if files are stored in unstructured format
# index = io.index_unstructured(files_path)

# Read the contents of the files, one file at a time
for p in index.read_contents():
    session_models.add_packet(p)

# get all sessions
for s in session_models.sessions:
    print(s)

# get a specific session
print(session_models.get_session("SPECIFIC:STATION:KEY"))
```

If you have a fixed set of files, use one of the [creation methods](#create-sessionmodel) above to read all the files 
at once.

### Using SessionModel

We recommend using the Session Model available from the cloud, as that provides the most updated models.  Follow the 
instructions (LINK GOES HERE) to access the cloud's Session Models.  If you only have access to local RedVox files, the 
SDK's SessionModel will suffice.

Please note that a local SessionModel is limited to the availability of your data, and may not accurately represent the
session over a longer period of time.

```python
from redvox.common.session_model import SessionModel


# Note that this is a trivial example, and you will need to create a SessionModel using one of the methods above
s_model: SessionModel = SessionModel()
# Print all the information
print(s_model)

# Access the information using the cloud_session property.
print(s_model.cloud_session.id)
print(s_model.cloud_session.uuid)
print(s_model.cloud_session.start_ts)
print(s_model.cloud_session.desc)
print(s_model.cloud_session.app)
print(s_model.cloud_session.app_ver)
print(s_model.cloud_session.api)
print(s_model.cloud_session.sub_api)
print(s_model.cloud_session.make)
print(s_model.cloud_session.model)
print(s_model.cloud_session.owner)
print(s_model.cloud_session.private)
print(s_model.cloud_session.n_pkts)
print(s_model.cloud_session.packet_dur)
print(s_model.cloud_session.client)
print(s_model.cloud_session.client_ver)
print(s_model.cloud_session.session_ver)

# Print information about the sensors in the session
print(s_model.cloud_session.num_sensors())
print(s_model.cloud_session.sensors)

# Print a specific sensor named SENSOR_NAME, with optional description of the sensor
print(s_model.get_sensor("SENSOR_NAME", "OPTIONAL_DESC"))

# Print the audio nominal sample rate in hz
print(s_model.audio_sample_rate_nominal_hz())

# Print time synchronization information
print(s_model.cloud_session.timing)

# Print day-long dynamic sessions
print(s for s in s_model.get_daily_dynamic_sessions())

# Print hour-long dynamic sessions
print(s for s in s_model.get_hourly_dynamic_sessions())
```

### SessionModel Properties

This section details all properties of the SessionModel.

* `cloud_session`: Session, the container for session information.  Default None
* `dynamic_sessions`: Dictionary of string: DynamicSession, the container for session information with a defined 
  start and end time.  Default empty dictionary.

These are privatized properties of SessionModel that users cannot edit:

* `_sdk_version`: string, the version of the SDK used to create the model.
* `_errors`: RedVoxExceptions, contains any errors found when creating the model.

Session is described in the cloud_api (LINK GOES HERE).  The properties of the `cloud_session` are:

* `id`: string, id of the station.
* `uuid`: string, uuid of the station.
* `desc`: string, text description of the station.
* `start_ts`: int, timestamp in microseconds since epoch UTC of when station was started.
* `client`: string, the name of the client that created the session.
* `client_version`: string, the version of the client that created the Session.
* `session_version`: string, the version of the Session model.
* `app`: string, name of the app the station is running.
* `api`: int, version number of the API the station is using.
* `sub_api`: int, version number of the sub-API the station in using.
* `make`: string, make of the station.
* `model`: string, model of the station.
* `app_ver`: string, version of the app the station is running.
* `owner`: string, owner of the station.
* `private`: bool, True if the station is private.
* `packet_dur`: float, length of station's data packets in microseconds.
* `sensors`: list of Sensor, the name, description, and sample rate associated with each sensor.
* `n_pkts`: int, number of files used to create the model.
* `timing`: Timing, the timing information for the Session.
* `sub`: List of string, the keys to the dynamic sessions associated with the Session.

Session has one function:

* `session_key() -> str`: Returns the key to the session, formatted as: `id:uuid:start_ts`

Sensor is described in the cloud_api (LINK GOES HERE).  The properties of a `Sensor` are:

* `name`: string, name of the sensor
* `description`: string, description of the sensor.
* `sample_rate_stats`: Stats, statistical information about the sensor's sample rate.

Timing is described in the cloud_api (LINK GOES HERE).  The properties of a `Timing` are:

* `first_data_ts`: float, the first timestamp of the timing data.
* `last_data_ts`: float, the last timestamp of the timing data.
* `n_ex`: int, the number of exchanges in the timing data.
* `mean_lat`: float, the mean latency of the timing data.
* `mean_off`: float, the mean offset of the timing data.
* `fst_lst`: FirstLastBufTimeSync, stores the first and last series of timesync data points.

FirstLastBufTimeSync is des

DynamicSession is described in the cloud_api (LINK GOES HERE).  The properties of a `DynamicSession` are:

* `n_pkts`: int, number of files used to create the session.
* `location`: Dictionary of string: LocationStat, the location information of the session.
* `battery`: Stats, statistical information about the battery charge remaining of the station.
* `temperature`: Stats, statistical information about the internal temperature in C of the station.
* `session_key`: string, the key to the DynamicSession, formatted as: 
  `SESSION.id:SESSION.uuid:SESSION.start_ts:start_ts:end_ts` where session is a Session described above.
* `start_ts`: int, the start timestamp of the DynamicSession.  Usually the start of the hour or day.
* `end_ts`: int, the end timestamp of the DynamicSession.  Usually the end of the hour or day.
* `dur`: string, describes the duration of the DynamicSession.  One of `"HOUR"` or `"DAY"`
* `sub`: List of string, the keys to the dynamic sessions associated with the DynamicSession.



### SessionModel Functions

These are the functions SessionModel can invoke:

* `as_dict() -> dict`: returns the SessionModel as a dictionary.
* `from_json_dict(source: dict) -> "SessionModel"`: converts the `json_dict` into a SessionModel returns it.
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