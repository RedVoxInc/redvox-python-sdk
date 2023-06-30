# <img src="../img/redvox_logo.png" height="25"> **RedVox Python SDK SessionModel Manual**

This readme is about the SDK specific SessionModel built from local files.  We recommend that you use the cloud 
to obtain updated Session Model(s).  For more information about cloud session models, refer to the 
[api_docs](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/session_model_api.html).

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
  * [Using SessionModel](#using-sessionmodel)
  * [SessionModel Properties](#sessionmodel-properties)
  * [SessionModel Functions](#sessionmodel-functions)
- [LocalSessionModels](#localsessionmodels)
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
cloud version of Session Model to get more accurate data.  More information about cloud session models is available in
the [api_docs](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/session_model_api.html). 
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
with. 

#### From Directory of Files

If you have a directory of files or are streaming data, use the `LocalSessionModels` class.  You can access the 
sessions from the class at your convenience.
* [Click here for more information about LocalSessionModels](#localsessionmodels).

```python
# If you are streaming data, adapt this code as necessary.

from redvox.common.session_model import LocalSessionModels
import redvox.common.io as io


session_models: LocalSessionModels = LocalSessionModels()

files_path = "/PATH/TO/FILES_DIR/"
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

#### A Note on Directory Structure
Redvox data must be stored in one of two ways:
1. `Unstructured`: All files exist directly in the specified directory.
2. `Structured`: Files are organized by date and time as specified in the
   [API-M repo](https://github.com/RedVoxInc/redvox-api-1000/blob/master/docs/standards/filenames_and_directory_structures.md#standard-directory-structure).

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

If you have a fixed set of files, use one of the [creation methods](#create-sessionmodel) above to read all the files 
at once.

### Using SessionModel

We recommend using the session model available from the cloud, as that provides the most updated models.  Follow the 
instructions (TODO: LINK GOES HERE) to access the cloud's session models.  If you only have access to local RedVox files, the 
SDK's SessionModel is ideal to use.

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

Session is described in the 
[cloud api](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/session_model_api.html#redvox.cloud.session_model_api.Session). 
For your reference, the properties of the `Session` are:

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

Sensor is described in the 
[cloud_api](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/session_model_api.html#redvox.cloud.session_model_api.Sensor).

Timing is described in the 
[cloud_api](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/session_model_api.html#redvox.cloud.session_model_api.Timing).

DynamicSession is described in the 
[cloud_api](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/cloud/session_model_api.html#redvox.cloud.session_model_api.DynamicSession). 
For your reference, the properties of a `DynamicSession` are:

* `n_pkts`: int, number of files used to create the session.
* `location`: Dictionary of string: LocationStat, the location information of the session.
* `battery`: Stats, statistical information about the battery charge remaining of the station.
* `temperature`: Stats, statistical information about the internal temperature in C of the station.
* `session_key`: string, the key to the DynamicSession, formatted as: 
  `SESSION.id:SESSION.uuid:SESSION.start_ts:start_ts:end_ts` where SESSION is a Session described above.
* `start_ts`: int, the start timestamp of the DynamicSession.  Usually the start of the hour or day.
* `end_ts`: int, the end timestamp of the DynamicSession.  Usually the end of the hour or day.
* `dur`: string, describes the duration of the DynamicSession.  One of `"HOUR"` or `"DAY"`
* `sub`: List of string, the keys to the dynamic sessions associated with the DynamicSession.

### SessionModel Functions

These are the functions SessionModel can invoke:

* `as_dict() -> dict`: returns the SessionModel as a dictionary.
* `from_dict(dictionary: dict) -> "SessionModel"`: converts the `dictionary` into a SessionModel and returns it.
* `compress(self, out_dir: str = ".") -> Path`: compresses the SessionModel into a .pkl file and saves it in directory 
  named `out_dir`.  Returns the path to the saved file.
* `save(self, out_type: str = "json", out_dir: str = ".") -> Path`: saves the SessionModel as a JSON or pickle file in
  the directory named `out_dir`.  Accepts only "pkl" and "json" for `out_type`.  Defaults to JSON file output if 
  out_type is not recognized.  Returns the path to the saved file.
* `load(file_path: str) -> "SessionModel"`: converts the JSON or pickle file located in `file_path` and converts it 
  into a SessionModel.  You must includ the full path and file extension.  Will raise an error if the file is not a 
  .json or .pkl file.
* `create_from_packet(packet: api_m.RedvoxPacketM) -> "SessionModel"`: used to create a SessionModel from a single API M
  Redvox packet.  See [Creating SessionModel from a Single Packet](#single-packet).
* `create_from_stream(data_stream: List[api_m.RedvoxPacketM]) -> "SessionModel"`: used to create a SessionModel from a
  list of API M Redvox packets.  Uses the first packet's information to initialize the SessionModel, and will ignore any
  packet that does not match the first packet's unique identifiers.  See
  [Creating SessionModel from Many Packets](#many-packets).
* `add_data_from_packet(self, packet: api_m.RedvoxPacketM)`: adds the data from a single API M Redvox packet to the 
  SessionModel.  Does not do anything if the unique identifiers of the packet do not match the SessionModel's.
* `add_dynamic_hour(self, data: dict, packet_start: float, session_key: str) -> str`: creates a new hour-long 
  DynamicSession if the key does not match an existing DynamicSession, otherwise updates the existing one with new 
  data.  Returns the key to the new/updated DynamicSession.
* `add_dynamic_day(self, packet: api_m.RedvoxPacketM) -> str`: creates a new day-long DynamicSession if the unique 
  identifiers form the packet do not match an existing DynamicSession, otherwise updates the existing one with new data 
  from the packet.  Also updates any related DynamicSessions.  Returns the key to the new/updated DynamicSession.
* `sdk_version(self) -> str`: returns the SDK version used to make the SessionModel.
* `num_sensors(self) -> int`: returns the number of sensors in the SessionModel.
* `get_sensor_names(self) -> List[str]`: returns the names of the sensors in the SessionModel as a list of strings.
* `get_sensor(self, name: str, desc: Optional[str] = None) -> Optional[cloud_sm.Sensor]`: returns the specific Sensor 
  with the given `name` and optionally the given `desc`.  Returns None if the sensor doesn't exist in the SessionModel.
* `audio_sample_rate_nominal_hz(self) -> float`: returns the SessionModel's expected nominal sample rate of the audio 
  sensor as hz.
* `get_daily_dynamic_sessions(self) -> List[cloud_sm.DynamicSession]`: returns a list of DynamicSession with duration 
  of one day.
* `get_hourly_dynamic_sessions(self) -> List[cloud_sm.DynamicSession]`: returns a list of DynamicSession with duration
  of one hour.
* `print_errors(self)`: prints all errors encountered by the SessionModel.

## LocalSessionModels

LocalSessionModels is the container for multiple SessionModel.  It uses a dictionary to allow instant access to a 
specific SessionModel.

The property of LocalSessionModel is:

* `sessions`: Dictionary of string: SessionModel, container for all the SessionModel.  The key is the SessionModel's 
  session_key().

The functions of LocalSessionModel are:

* `add_packet(self, packet: api_m.RedvoxPacketM) -> str`: adds the `packet` to a SessionModel.  Creates a new 
  SessionModel if needed.  Returns the key to the new or updated SessionModel.
* `get_session(self, key: str) -> Optional[SessionModel]`: returns the SessionModel that matches the `key`.  Returns 
  None if the `key` doesn't match.

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

Use the LocalSessionModels class to handle any SessionModel we end up reading data for.
```python
import redvox.common.session_model as sm
import redvox.common.io as io


# Update this to match your environment
files_path = "/PATH/TO/DATA"

models = sm.LocalSessionModels()

# Files are assumed to be stored in a structured format
index = io.index_structured(files_path)
# Use the line below if files are stored in unstructured format
# index = io.index_unstructured(files_path)

# Read the contents of the files, one file at a time
for p in index.read_contents():
  models.add_packet(p)

# display each of the SessionModel from the files
for k, m in models.sessions.items():
  print(m)
```

## Errors and Troubleshooting

Any statistics calculated from SessionModel are subject to errors.  The 
[cloud version](TODO: LINK GOES HERE) 
of SessionModel provides the most up-to-date results.

If you are not seeing any results from creating a SessionModel, check that the target directory contains the correct 
files.

You are more likely to use the LocalSessionModels class to create multiple SessionModel from large sets of data.  The 
other SessionModel [constructor methods](#single-packet) are intended for advanced users who want to investigate 
specific sets of data.  Refer to the [example code](#sessionmodel-example-code) for a quick example on how to use 
LocalSessionModels to get SessionModel.
