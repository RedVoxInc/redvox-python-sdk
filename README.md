### RedVox Python SDK

This repository contains code for reading and working with the RedVox API 900 data format.

See: https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v2.0.0/redvox-api900-docs.md for SDK documentation.

### Changelog

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