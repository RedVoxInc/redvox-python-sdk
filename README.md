### RedVox Python SDK

This repository contains code for reading and working with the RedVox API 900 data format.

See: https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.7.1/redvox-api900-docs.md for SDK documentation.

### Changelog

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

#### 2.4.0 (2019-10-8)

* Add mach_time_zero accessor to WrappedRedvoxPackets.
    * WrappedRedvoxPacket.mach_time_zero(self) -> typing.Optional[int]

#### 2.3.0 (2019-9-25)

* concat._identify_gaps now only checks for dropped data from sensors. It checks for timing continuity by ensuring that the gap between packets is no larger than a configurable amount for a given sample rate.
* concat._identify_sensor_changes was added to identify sensor changes such as change in sample rate, change in sensor name, change in data type, or missing sensor data

#### 2.2.1 (2019-5-14)

* Added stat utils tests and updated function
* Edited documentation typos; 2.2.0 documentation still valid for 2.2.1

#### 2.2.0 (2019-4-26)

* Add sensor timing correction
* Update documentation
* Fix more cyclic dependency issues

#### 2.1.1 (2019-4-24)

* Start and end timestamps are now optional when reading .rdvxz files from a range. For timestamps that are not supplied, the timestamps are parsed from the data file names to find the earliest and latest timestamp.
* Fixed a bug that created a cyclic dependency between the reader and concat modules. 

#### 2.0.0 (2019-4-12)

* Add ability concatenate multiple .rdvxz files together [(docs)](https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.0.0/redvox-api900-docs.md#markdown-header-concatenating-wrappedredvoxpackets)
* Add ability to identify gaps in continuous data when concatenating multiple files
* Read a range of .rdvxz files from a directory with a given time window and optional redvox ids to filter against [(docs)](https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.0.0/redvox-api900-docs.md#markdown-header-loading-redvox-api-900-files-from-a-range)
* Read a range of .rdvxz files from a structured directory with a given time window and optional redvox ids to filter against
* Deprecated several public API methods for setting and accessing sensor fields
* Add objects for summarizing RedVox data ranges [(docs)](https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.0.0/redvox-api900-docs.md#markdown-header-summarizing-wrappedredvoxpackets)
* Add ability to plot summary RedVox data ranges
* Refactor reader.py into several modules
* Update dependency versions

#### 1.5.0 (2019-3-20)

* Add setters for all fields
* Add the ability to easily create sensor channels and RedVox packets
* Add CLI that
  * Converts .rdvxz files to .json files
  * Displays the contents of .rdvxz files
* Add ability to compare files and sensor channels
* Update documentation and API documentation
* Add more examples

#### 1.4.1 (2019-2-15)

* Update required libraries
* Add ability to get original compressed buffer from WrappedRedvoxPacket
* Add utility functions for LZ4 compression

##### v1.4.0 (2018-12-5)

* Added support for serializing to/from JSON
* Fixed bug where has_time_synchronization_channel() would return true even if the payload was empty
