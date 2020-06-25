### RedVox Python SDK

This repository contains code for reading and working with the RedVox API 900 data format.

See: https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.9.2/redvox-api900-docs.md for SDK documentation.

![Bitbucket Pipelines branch](https://img.shields.io/bitbucket/pipelines/redvoxhi/redvox-api900-python-reader/master)

## Changelog

### 2.9.6 (2020-06-24)

* Large metadata requests are now chunked by the client.
* Change refresh token interval from 1 minute to 10 minutes

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
