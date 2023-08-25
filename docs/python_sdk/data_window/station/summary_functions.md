# <img src="../../img/redvox_logo.png" height="25"> **RedVox Python SDK Station Summary Manual**

The RedVox Python SDK contains routines for reading, creating, and writing RedVox API 900 and RedVox API 1000 data
files. The SDK is open-source.

Station is a Python class designed to store format-agnostic station and sensor data.  Its primary goal is to represent
RedVox data, but it is capable of representing a variety of station and sensor configurations.

The functions and code described here allow you to view specific details about the Station.

## Table of Contents

<!-- toc -->

- [Station](#station)
    * [Station Location Summary](#station-location-summary)
- [Location and Timing Summary Example](#location-and-timing-summary-example)

<!-- tocstop -->

## Station

Station is a module designed to hold format-agnostic data of various sensors that combine to form a single unit.
The data can be gathered from and turned into various other formats as needed.

Station represents real world combinations of various recording devices such as audio, accelerometer, and pressure sensors.
Stations will not contain more than one of the same type of sensor; this is to allow unambiguous and easy comparison between stations.

Station objects are comprised of a station key, the sensor data, data packet metadata, and other station specific metadata.

Each Station has a unique key.  Keys are comprised of the Station's id, uuid, start timestamp since epoch UTC and the station's metadata.
Stations with the same key can be combined into one Station to simplify results.

Stations will do their best to fill any gaps that can be detected in the data.

Refer to the [Station API documentation](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/common/station.html) or 
the [Station and SensorData Manual](https://github.com/RedVoxInc/redvox-python-sdk/tree/master/docs/python_sdk/data_window/station) as needed.

_[Table of Contents](#table-of-contents)_

### Station Location Summary

Stations contain a lot of data, which can take time to sift through.  This function demonstrates one way to collate the 
contents of one of the sensors.

The Location summary is grouped by the provider of the location data.

```python
from redvox.common.api_reader import ApiReader
from redvox.common.data_window import DataWindow, DataWindowConfig
from redvox.common.station_model import LocationSummary


# Use your own method to load a Station; the following methods are trivial and will not provide useful
# input without modification.
# Load a Station from a DataWindow
d_win_config = DataWindowConfig(input_dir="input_dir", structured_layout=True)
d_win = DataWindow("my_event", config=d_win_config)
my_station = d_win.first_station()

# Create a Station using a directory.
reader = ApiReader(base_dir="input_dir", structured_dir=True)
my_other_station = reader.get_stations()[0]

# Use the LocationSummary class and print the results
summary = LocationSummary.from_station(my_station)

print(summary)
```

_[Table of Contents](#table-of-contents)_

## Location and Timing Summary Example

This example shows how one might get the location and timing summary from a Station.  Note that the timing values can be
extracted directly from the Station.

```python
from redvox.common.station import Station
from redvox.common.station_model import LocationSummary


def example_of_print_loc_and_timing_summary(stn: Station):
    """
    An example function that shows how you can access location, GNSS, and time sync information and prints it
    :param stn: Station to get data from
    """
    print(f"station_id: {stn.id()}")
    loc_summary = LocationSummary.from_station(stn)
    if loc_summary:
        for m in loc_summary:
            print(
                "-----------------------------\n"
                f"location_provider: {m.provider}, num_pts: {m.num_pts}\n"
                f"latitude  mean: {m.latitude_mean}, std_dev: {m.latitude_standard_deviation}\n"
                f"longitude mean: {m.longitude_mean}, std_dev: {m.longitude_standard_deviation}\n"
                f"altitude  mean: {m.altitude_mean}, std_dev: {m.altitude_standard_deviation}"
            )
        print(
            f"-----------------------------\nGNSS timing:\n"
            f"GNSS offset at start: {stn.gps_offset_model().intercept}\n"
            f"slope: {stn.gps_offset_model().slope}\n"
            f"GNSS estimated latency: {stn.gps_offset_model().mean_latency}\n"
            f"num_pts: {len(stn.location_sensor().get_gps_timestamps_data())}"
        )
    else:
        print("location data not found.")
    print(
        f"-----------------------------\ntimesync:\n"
        f"best_offset: {stn.timesync_data().best_offset()}, offset_std: {stn.timesync_data().offset_std()}\n"
        f"best_latency: {stn.timesync_data().best_latency()}, latency_std: {stn.timesync_data().latency_std()}\n"
        f"num_pts: {stn.timesync_data().num_tri_messages()}\n*****************************\n"
    )
```

_[Table of Contents](#table-of-contents)_
