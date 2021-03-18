### RedVox Python SDK

This repository contains code for reading and working with the RedVox API 900 and API 1000 (M) data formats.

* [User Documentation](/docs/python_sdk)
* [API Documentation](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/index.html)

## Changelog

### 3.0.0rc2 (2021-3-18)

* Better process pool management.
* Update numpy deprecated code.

### 3.0.0rc0 (2021-3-17)

* Prep. first release candidate for 3.0 release.

### 3.0.0b8 (2021-3-12)

* Fixed error when creating DataWindows

### 3.0.0b7 (2021-3-12)

* Fixed error when creating DataWindows
* Added unaltered_timestamps to all sensors; these timestamps are unchanged values recorded by the sensor

### 3.0.0b6 (2021-3-11)

* Fixed bug when calculating OffsetModel validity
* Fixed invalid latencies appearing in OffsetModel calculations
* Fixed invalid station ids showing up in DataWindows

### 3.0.0b5 (2021-3-10)

* OffsetModel handles cases where not enough data is present to create a reliable model
* Performance improvements and streamlined processes

### 3.0.0b4 (2021-3-2)

* Performance improvements when creating data window, stations and other classes/data structures
* Fixed incorrect timing adjustment function and object dtypes in dataframe functions

### 3.0.0b3 (2021-3-1)
* Updated timing correction using offset model predictions
* Added timing correction to file searching functionality

### 3.0.0b2 (2021-2-3)

* Updated filter inputs to accept lists
* Fixed bug when pickle-ing station objects

### 3.0.0b1 (2021-2-1)

* Added functionality to automatically correct query times to gather all of user's requested data

### 3.0.0b0 (2021-2-1)

* First beta release of version 3
* Combined API 900 and API 1000 file reading
* Updated file reading interface
* Timing correction
* Cleanup cloud APIs
* Access to new RedVox Cloud APIs (station status, timing stats)
* Persistent RedVox cloud configuration files
* Cleanup cyclic dependency issues
* Fix bugs with nan handling
* Add ability to sort unstructured RedVox files into structured RedVox files


### 3.0.0a23 (2021-1-7)

* Update api900 file reader to truncate file timestamps instead of round
* Update api900 to api1000 conversion to properly convert locations
* Added functions to read api900 and api1000 data from common base directory
* Use api900 to api1000 conversion method to put data from both formats into a DataWindow

### 3.0.0a22 (2021-1-5)

* Update LZ4 compression to be compatible with other LZ4 libraries that work with API M data

### 3.0.0a21 (2020-11)

* Add setters for all sub-messages
* Extend start and end queries for reading data by slight amount
* fixed a bug when creating stations using set locations
* API M protobuf updated
* fixed bug setting compressed audio data

### 3.0.0a20 (2020-11-16)

* Add support for downloading API M data from cloud servers
* Optimize data download using a custom work-stealing process pool
* Standardize CLI

### 3.0.0a19 (2020-11-10)

* Fixed bug with recalculating metadata of stations

### 3.0.0a18 (2020-11-09)

* STATION_HEALTH as sensor type to consolidate battery health, power state, internal temperature, network health, available disk space and RAM, and cell service status into one sensor with the same sample rate and source (station_metrics)
* Time sync data has been added to the station object

### 3.0.0a17 (2020-11-04)

* Image sensors properly load into data windows
* Updated LocationSensors to use best_locations in API M location sensors

### 3.0.0a16 (2020-10-27)

* LocationData added; stores location data of a Station for later use
* DataWindow will compute the most relevant locations into LocationData
* Added sample interval standard deviation to SensorData
* Resolved discrepancies between metadata values and data being read

### 3.0.0a15 (2020-10-20)

* Add ability to post process derived movement events

### 3.0.0a14 (2020-10-06)

* Add ability to query API M metadata from the Cloud HTTP API
* Add methods and classes for working with derived movement results

### 3.0.0a13 (2020-10-01)

* DataWindow will properly bound the data within the start and end times
* DataWindow will fill gaps in data based on the existing data's sample interval
* DataWindow will keep previous locations if none exist between start and end times
* Sensors will properly preserve the mean sample interval as new data is added
* Added function to get time sync exchanges from API M packet

### 3.0.0a12 (2020-09-29)

* Add methods for lazily streaming data from the file system.

### 3.0.0a11 (2020-09-29)

* Add gallery command to CLI for viewing API M image data

### 3.0.0a10 (2020-09-24)

* Data reading functions include location provider value
* Data reading functions include the 2 nearest points if truncation removes all data

### 3.0.0a9 (2020-09-23)

* Data reading functions properly set station's best latency and offset
* Updated DataWindow default values for gap duration to 0.5 seconds and padding to 120 seconds
* Added getters and setters for num samples per window in app settings

### 3.0.0a8 (2020-09-22)

* Improvements to DataWindow, SensorData, and Station classes

### 3.0.0a7 (2020-09-22)

* Added DataWindow class; a station agnostic way of getting exactly the time window of data requested
* Updated SensorData functions to return numpy arrays
* Updated SensorData function names to better match what is being returned
* Added functionality to return user-specified location values from api900 location sensors

### 3.0.0a6 (2020-09-18)

* Improvements to raw_io. Include new summaries in ReadResult.
* Fix bug where querying with just the short ID was not working correctly
* Fix bug ensuring read packets are ordered

### 3.0.0a2 (2020-09-17)

* First alpha release supporting API M

### 2.9.12 (2020-07-17)

* Add support for 16 kHz audio streams

### 2.9.11 (2020-07-07)

* Fix bug where reading data that spanned across several days would leave out data towards end of time window

### 2.9.10 (2020-06-25)

* Authentication responses not return a copy of the claims for convenience

### 2.9.9 (2020-06-25)

* Update dependencies
* Encapsulate HTTP logic for HTTP Cloud Client
* Add tests for Cloud Client
* Add configurable timeout
* Add custom errors and better error handling
* Fix bug where connection would not be closed on authentication error

### 2.9.8 (2020-06-24)

* Large metadata requests are now chunked by the client.
* Change refresh token interval from 1 minute to 10 minutes
* Re-use HTTP client with keep-alive for more efficient HTTP requests
* Add chunked response for timing metadata request

### 2.9.5 (2020-06-23)

* Make Cloud API refresh token interval configurable.
* Allow Cloud API client to be used within "with" blocks for automatic closing of resources

### 2.9.2 (2020-06-11)

* Update dependencies (now dataclasses will only be pulled in on Python 3.6)

### 2.9.1 (2020-06-05)

* Fix bug where timing metadata was not converted into its associated data class.

### 2.9.0 (2020-06-05)

* Add full fledged cloud based API client. This client seamlessly manages authentication tokens behind the scenes.
* Update CLI data request methods to make use of new cloud based client.

### 2.8.7 (2020-06-03)

* Integrate ability to access extracted metadata from RedVox packets utilizing the cloud data API.

### 2.8.6 (2020-05-12)

* Add small HTTP interface to upcoming RedVox cloud API
* Added new sub-command to CLI `data_req_report` which takes a report ID and will download the report data for authenticated users

### 2.8.5 (2020-05-11)

* The auth_token CLI field for the data_req CLI command has been renamed to `secret_auth` to better reflect the fact that it is a shared secrete.  
* CLI for data req now makes the shared secret auth key optional dependent on the settings of the remote server. 

### 2.8.4 (2020-05-07)

* Add `--protocol` option to redvox-cli when making data request. This allows the data client to optionally connect over HTTP (mainly only useful for local testing)

### 2.8.3 (2020-05-06)

* Add `mach_time_zero` to TimeSyncData class
* Add `best_tri_msg_indices` to TimeSyncData class to identify which tri-message exchange indicated the best latency and offset
* Add validation checks to ensure that there is no change in sample rate or `mach_time_zero` in the analyzed packets
* Add check for change in `mach_time_zero` when identifying gaps

### 2.8.2 (2020-04-27)

* Add workaround for accessing `mach_time_zero` in incorrectly constructed Android packets

### 2.8.1 (2020-04-02)

* TriMessageStats will now append empty arrays in a tuple to tri_message_coeffs when the time sync sensor is empty or doesn't exist.
* Functions compute_barometric_height and compute _barometric_height_array take additional optional arguments: surface temperature in K, molar mass of air in kg/mol, acceleration of gravity in m/s2 and the universal gas constant in (kg * m2)/(K * mol * s2)

### 2.8.0 (2020-03-31)

* Added a migration module that allows users to slowly begin migrating API 900 data towards API 1000. A flag can be set either through the API or by setting an environment variable `ENABLE_MIGRATIONS="1"`. When enabled, all getters for numeric types will return floating point values (the only numeric type in API 1000).

### 2.7.9 (2020-03-25)

* Added properties: server_acquisition_times, packet_duration and mach_time_zero to `redvox/api900/timesync/api900_timesync.py` to assist with analyzing time sync data

### 2.7.8 (2020-03-23)

* Added a property: tri_message_coeffs to `redvox/api900/timesync/api900_timesync.py` to allow access to the tri-message coefficients
* Allowed access to the function evaluate_latencies_and_offsets in `redvox/api900/timesync/api900_timesync.py`

### 2.7.7 (2020-03-19)

* Added unit tests for `redvox/common/stats_helper.py`
* The functions mean_of_means, variance_of_means and mean_of_variance in `redvox/common/stats_helper.py` will not fail when sum(counts) is 0.

### 2.7.6 (2020-03-19)

* Added validation function that removes duplicated timestamps to `redvox/api900/timesync/tri_message_stats.py`
* Added get_latency_mean, get_latency_std_dev, get_offset_mean and get_offset_std_dev functions to `redvox/api900/timesync/api900_timesync.py`
* Updated unit tests

### 2.7.5 (2020-03-13)

* Expose new package `redvox/api900/qa`
* Expose new gap detection module `redvox/api900/qa/gap_detection.py`
* Provide a public identify_time_gaps method

### 2.7.1 (2020-03-03)

* Add and define useful constants to `redvox/common/constants.py`
* Add cross-correlation functions to `redvox/common/cross_stats.py`
* Add date time utilities to `redvox/common/date_time_utils.py`
* Add rdvxz file statistics functions to `redvox/common/file_statistics.py`
* Add statistical helper functions to `redvox/common/stats_helper.py`
* Add new time synchronization package at `redvox/api900/timesync`
* Add a location analyzer to `redvox/api900/location_analyzer.py`
* Updated unit tests and documentation
* Updated dependencies to latest versions
* Added additional code QA (pylint, mypy, coverage)

### 2.6.1 (2020-01-28)

* Update bulk data download client to utilize a RedVox provided authentication token

### 2.6.0 (2019-12-11)

* Update the redvox-cli
    * The CLI is now installed when this SDK is installed and available to the user as ```redvox-cli```
    * Added improved logging and error handling
    * Added ability to download bulk RedVox data sets

### 2.5.1 (2019-10-23)

* Add top level setter for mach_time_zero
    * WrappedRedvoxPacket.set_mach_time_zero(self, mach_time_zero: int) -> 'WrappedRedvoxPacket'

### 2.5.0 (2019-10-17)

* Add top level getters and setters for accessing time synchronization metrics stored in RedVox Packet metadata.
    * WrappedRedvoxPacket.best_latency(self) -> typing.Optional[float]
    * WrappedRedvoxPacket.set_best_latency(self, best_latency: float) -> 'WrappedRedvoxPacket'
    * WrappedRedvoxPacket.best_offset(self) -> typing.Optional[float]
    * WrappedRedvoxPacket.set_best_offset(self, best_offset: float) -> 'WrappedRedvoxPacket'
    * WrappedRedvoxPacket.is_synch_corrected(self) -> bool
    * WrappedRedvoxPacket.set_is_synch_corrected(self, is_synch_corrected: bool) -> 'WrappedRedvoxPacket'
* Add shortcut for adding metadata to a RedVox Packet (previously the entire metadata needed to be set at a time)
    * WrappedRedvoxPacket.add_metadata(self, key: str, value: str) -> 'WrappedRedvoxPacket'

### 2.4.0 (2019-10-8)

* Add mach_time_zero accessor to WrappedRedvoxPackets.
    * WrappedRedvoxPacket.mach_time_zero(self) -> typing.Optional[int]

### 2.3.0 (2019-9-25)

* concat._identify_gaps now only checks for dropped data from sensors. It checks for timing continuity by ensuring that the gap between packets is no larger than a configurable amount for a given sample rate.
* concat._identify_sensor_changes was added to identify sensor changes such as change in sample rate, change in sensor name, change in data type, or missing sensor data

### 2.2.1 (2019-5-14)

* Added stat utils tests and updated function
* Edited documentation typos; 2.2.0 documentation still valid for 2.2.1

### 2.2.0 (2019-4-26)

* Add sensor timing correction
* Update documentation
* Fix more cyclic dependency issues

#### 2.1.1 (2019-4-24)

* Start and end timestamps are now optional when reading .rdvxz files from a range. For timestamps that are not supplied, the timestamps are parsed from the data file names to find the earliest and latest timestamp.
* Fixed a bug that created a cyclic dependency between the reader and concat modules. 

### 2.0.0 (2019-4-12)

* Add ability concatenate multiple .rdvxz files together [(docs)](https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.0.0/redvox-api900-docs.md#markdown-header-concatenating-wrappedredvoxpackets)
* Add ability to identify gaps in continuous data when concatenating multiple files
* Read a range of .rdvxz files from a directory with a given time window and optional redvox ids to filter against [(docs)](https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.0.0/redvox-api900-docs.md#markdown-header-loading-redvox-api-900-files-from-a-range)
* Read a range of .rdvxz files from a structured directory with a given time window and optional redvox ids to filter against
* Deprecated several public API methods for setting and accessing sensor fields
* Add objects for summarizing RedVox data ranges [(docs)](https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.0.0/redvox-api900-docs.md#markdown-header-summarizing-wrappedredvoxpackets)
* Add ability to plot summary RedVox data ranges
* Refactor reader.py into several modules
* Update dependency versions

### 1.5.0 (2019-3-20)

* Add setters for all fields
* Add the ability to easily create sensor channels and RedVox packets
* Add CLI that
  * Converts .rdvxz files to .json files
  * Displays the contents of .rdvxz files
* Add ability to compare files and sensor channels
* Update documentation and API documentation
* Add more examples

### 1.4.1 (2019-2-15)

* Update required libraries
* Add ability to get original compressed buffer from WrappedRedvoxPacket
* Add utility functions for LZ4 compression

### v1.4.0 (2018-12-5)

* Added support for serializing to/from JSON
* Fixed bug where has_time_synchronization_channel() would return true even if the payload was empty
