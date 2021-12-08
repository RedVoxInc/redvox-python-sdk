## Changelog

### 3.1.0 (2021-12-8)

* Official release 3.1.0
* Summary of changes:
  * Pyarrow backend implemented for DataWindow, Station, SensorData and underlying classes
  * Properties of the above classes have been updated into functions for more secure access
* Please note DataWindows created in versions 3.0.x cannot be loaded in 3.1.0
  * Use the latest 3.0.10 to continue to load 3.0.x DataWindows
  * OR recreate the DataWindows using 3.1.0

### 3.1.0rc5 (2021-12-7)

* Requirements for numpy reduced to >=1.19.5
* Added values for DataWindow saving methods in function description

### 3.1.0rc4 (2021-12-7)

* Added missing functions for Station and SensorData property access
* Documentation updated for new functions

### 3.1.0rc3 (2021-12-1)

* Updated more functions used by old data window module

### 3.1.0rc2 (2021-12-1)

* Added missing notes for 3.1.0rc1 release
* Updated functions used by old data window module

### 3.1.0rc1 (2021-12-1)

* Prepare for release

### 3.0.10rc13 (2021-11-30)

* Added functions to TimeSync to display individual values per exchange
* updated installation requirements

### 3.0.10rc12 (2021-11-29)

* Update SensorData, Station, DataWindow and related classes to use Pyarrow implementations
* Shifted previous versions of the above to *_old files while updated classes in testing

### 3.0.10rc11 (2021-11-16)

* Added missing file used to read data windows written to disk

### 3.0.10rc8 (2021-11-16)

* Updated filesystem writing functions
* Added subclasses to SensorData objects (pyarrow and regular versions)

### 3.0.10rc7 (2021-10-19)

* Shifted DataWindowArrow, StationPa and SensorDataPa to use filesystem to store data
* Standardized attribute access for arrow classes

### 3.0.10rc6 (2021-10-5)

* moved code in ApiReader involving DataWindowArrow to new file; api_reader_dw
* added pretty print option for DataWindowArrow
* Fixed bugs when loading DataWindowArrow from a file

### 3.0.10rc5 (2021-9-30)

* fixed error converting units of sample interval and std dev in pyarrow summaries
* renamed DataWindowOrigin to EventOrigin

### 3.0.10rc4 (2021-9-28)

* fixed error when comparing configuration station ids that are shorter than 10 characters 
* fixed incorrect default value for location providers when loading data using pyarrow

### 3.0.10rc3 (2021-9-27)

* Fixed bug when loading timestamps into offset model using datawindow arrow version
* Allowed other iterables when creating DataWindowConfigWpa

### 3.0.10rc2 (2021-9-17)

* Fixed bug when writing sensors to json files
* Added default name

### 3.0.10rc1 (2021-9-13)

* Merged pyarrow loading into existing data window functionality
* If user saves data to disk, parquet files will be created

### 3.0.10 (2021-9-9)

* Fix missing values in Health Sensor fields

### 3.0.9rc1 (2021-9-1)

* Merged latest release
* Fixed bugs when loading data using pyarrow implementation

### 3.0.9 (2021-8-30)

* Fix missing latencies and offsets attribute when data is missing from files.
* Added missing Health fields from Api 1000 data.

### 3.0.8rc1 (2021-8-30)

* Added missing/incorrect values when creating stations using parquet files.
* Updated version number and changelog to represent correct dates and version numbers.
* Pyarrow functionality complete for data window.  Refer to *_wpa files.

### 3.0.8 (2021-8-11)

* Fix inconsistent storing of enum data from station metrics

### 3.0.7rc0 (2021-8-3)

* Testing pyarrow functionality for Sensors and Stations
* Save parquets of data from Redvox files instead of loading everything at once

### 3.0.7 (2021-7-29)

* Update dependencies
* Tweak cloud client for cloud cloud environment.

### 3.0.6 (2021-7-28)

* Add methods for querying status of optional dependencies
* Add ability to construct cloud client from previously held authentication token

### 3.0.5 (2021-7-27)

* Fixed nan'd missing data points for audio sensors with data that doesn't reach edges of data window
* Added option to prevent usage of offset model when calculating time corrections for data windows and stations
* Added number of samples to api conversion function
* Docs updated to include new functionality

### 3.0.4 (2021-6-24)

* IDs shorter than 10 characters are zero-padded to preserve consistency between file names and internal representations
* DataWindow docs updated

### 3.0.3 (2021-6-16)

* Removed NaN padding from edges of audio sensors
* Streamlined gap-filling method
* Low-level API docs and links updated

### 3.0.2 (2021-6-9)

* Update long description content type for better display on PyPI

### 3.0.1 (2021-6-9)

* Update homepage links

### 3.0.0 (2021-6-7)

* Official release 3.0.0

### 3.0.0rc38 (2021-6-1)

* Moved Best Location values into their own sensor
* Fixed missing apply_correction flag check in DataWindowFast
* Updated DataWindow to use DataWindowFast implementation
* Removed DataWindowFast references from SDK

### 3.0.0rc37 (2021-5-25)

* Api900 conversion will report error when api900 file doesn't contain audio data
* LocationSensor will use packet start mach timestamps if derived from a BestLocation instead of using only the BestLocation's timestamps (which may not have been created within the DataWindow specified).
* Utilize api1000 native reading processes over WrappedPacket reading processes

### 3.0.0rc36 (2021-5-19)

* Fixed api900 conversion setting wrong value for mach time zero (api900) to app start time (api1000)
* SensorData Enumerated values return strings instead of numbers or Enum objects
* Updated Data Window to return multiple stations if a single station id changes its start datetime (one new station per change in start datetime)

### 3.0.0rc35 (2021-5-13)

* Added check for time synchronization data in a Station
* converted Station and SensorData to read directly from raw protobuf instead of the wrapped versions

### 3.0.0rc31 (2021-5-7)

* Add native implementation of file stats extraction

### 3.0.0rc30 (2021-5-5)

* Fixed bugs in DataWindowFast
* Added JSON and serialization to DataWindowFast

### 3.0.0rc29 (2021-5-4)

* Provide native backend for indexing
* Renamed DataWindowSimple to DataWindowFast
* DataWindowFast performance improved
* DataWindowFast can create stations with different start times

### 3.0.0rc28 (2021-4-29)

* Raw protobuf conversion from api900 to apiM implemented
* Improved Data Window performance via DataWindowSimple class; use parallelism for best performance
* Raw protobuf reading implemented for station and sensor creation.

### 3.0.0rc27 (2021-4-23)

* fixed bug when creating edge points in data windows

### 3.0.0rc26 (2021-4-23)

* fixed potential infinite loop when creating data windows
* added tools to read raw protobuf instead of wrapped packets
* added simplified data window process with the goal of producing results faster

### 3.0.0rc25 (2021-4-20)

* updated gap filling to work when gaps are not pre-determined
* improved gap filling performance
* removed extra step when creating data windows

### 3.0.0rc24 (2021-4-19)

* Add ability to stream metadata requests by chunk size chunks
* gap filling performed when data is loaded instead of during data window creation
* filled converted api900 location provider arrays to be same length as number of samples
* fixed creation of interpolated points when dataframes do not contain expected types

### 3.0.0rc23 (2021-4-15)

* Fix bug when downloading data and file already exists

### 3.0.0rc22 (2021-4-15)

* Added gps timestamps to location sensors
* DataWindow and Station documentation updated

### 3.0.0rc21 (2021-4-14)

* Fix cloud based query timing correction for non-contiguous data
* Provide more log message in GUI data downloader
* Make GUI data downloader more resistant and responsive to errors
* Fixed image sensor loading

### 3.0.0rc20 (2021-4-13)

* Fixed loading sensors when some packets do not include all sensors from adjacent packets
* Moved Station documentation out of DataWindow documentation.

### 3.0.0rc19 (2021-4-12)

* Add ability to optionally enable or disable SDK parallelism through global settings or environmental variables
* Added how to use JSON writing and reading to DataWindow docs
* Updated Station.audio_sample_rate_hz to Station.audio_sample_rate_nominal_hz
* Added StationMetadata.station_description; the station's text description

### 3.0.0rc18 (2021-4-9)

* Added JSON writing and reading utility to Data Window

### 3.0.0rc17 (2021-4-8)

* Add GUI for downloading RedVox data from the cloud
* Update GUI libraries to PySide6

### 3.0.0rc14 (2021-4-8)

* Fixed creating Location and Health sensors when data is inconsistent
* Updated and added validation for Station metadata objects

### 3.0.0rc13 (2021-4-7)

* Add CLI argument to disable query timing correction on data requests
* Sensor sample rate update function more accurately adjusts to a slope in offset model

### 3.0.0rc11 (2021-4-6)

* Fixed timestamp discrepancies when creating Audio Sensors
* Added optional automatic timing correction to cloud data queries

### 3.0.0rc10 (2021-4-5)

* Implement functionality to provide cloud based timing corrections
* Updated Data Window creation to include edge timestamps on non-audio sensors

### 3.0.0rc9 (2021-4-1)

* Fixed bug when filling gaps in data window
* updated audio sensor creation to account for gaps in packets

### 3.0.0rc8 (2021-4-1)

* Data Window lz4 serialization and deserialization added
* Audio sensor timestamps are recalculated based on updated first timestamp and sample interval

### 3.0.0rc7 (2021-3-25)

* Make GUI features an optional "extra"
* Fix missing toml dependency
* Remove unused dependencies
* Fix windows specific bugs relating to path management and datetime management
* Update CI to test against more OS environments

### 3.0.0rc3 (2021-3-23)

* Fixed process that updates data window timestamps and properties.
* Added score value to offset model

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
