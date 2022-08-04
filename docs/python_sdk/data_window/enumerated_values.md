# <img src="../img/redvox_logo.png" height="25"> **RedVox Python SDK DataWindow Enumerated Values Manual**

DataWindow and its underlying structures use enumerated values for several properties and functions.  Enumerated values 
are represented internally as an integer, but can be displayed as a string to be human-readable.

This section describes various enumerations you may encounter and their possible values.

You may find more information about enumerated values in the [API documentation](https://redvoxinc.github.io/redvox-sdk/api_docs/redvox/index.html).

## Table of Contents

<!-- toc -->

- [FileSystemSaveMode](#filesystemsavemode)
- [SensorType](#sensortype)
- [OsType](#ostype)
- [NetworkType](#networktype)
- [PowerState](#powerstate)
- [CellServiceState](#cellservicestate)
- [WifiWakeLock](#wifiwakelock)
- [ScreenState](#screenstate)
- [LocationProvider](#locationprovider)
- [ImageCodec](#imagecodec)
- [AudioCodec](#audiocodec)
- [TimingScoreMethod](#timingscoremethod)
- [ApiVersion](#apiversion)
- [DataPointCreationMode](#datapointcreationmode)
- [DataWindowOutputType](#datawindowoutputtype)

<!-- tocstop -->

## FileSystemSaveMode

This is used to determine which functions are used when saving to disk. It is located in `redvox.common.io`.

These are the values of FileSystemSaveMode:

* `MEM`: save using memory.  Default value.
* `TEMP`: save using temporary directory
* `DISK`: save using path on disk

## SensorType

This is used to denote a Sensor's type.  It is located in `redvox.common.sensor_data.py`

These are the values of SensorType:

* `UNKNOWN_SENSOR`: Used for sensors without a known type.  Default value.
* `ACCELEROMETER`: Used for accelerometer sensor
* `AMBIENT_TEMPERATURE`: Used for ambient temperature sensor
* `AUDIO`: Used for audio/microphone sensor
* `COMPRESSED_AUDIO`: Used for compressed audio sensor
* `GRAVITY`: Used for gravity sensor
* `GYROSCOPE`: Used for gyroscope sensor
* `IMAGE`: Used for camera/image sensor
* `LIGHT`: Used for light/luminosity sensor
* `LINEAR_ACCELERATION`: Used for linear acceleration sensor
* `LOCATION`: Used for location sensor
* `MAGNETOMETER`: Used for magnetometer sensor
* `ORIENTATION`: Used for orientation sensor
* `PRESSURE`: Used for barometer/pressure sensor
* `PROXIMITY`: Used for proximity sensor
* `RELATIVE_HUMIDITY`: Used for relative humidity sensor
* `ROTATION_VECTOR`: Used for rotation vector sensor
* `INFRARED`: Used for proximity/infrared sensor
* `STATION_HEALTH`: Used for station health sensor
* `BEST_LOCATION`: Used for best location sensor

## OsType

This is used by StationMetadata to denote the station's OS.  It is located in 
`redvox.api1000.wrapped_redvox_packet.station_information`.

These are the values of OsType:

* `UNKNOWN_OS`: Unknown OS.  Default value.
* `ANDROID`: Used for Android devices
* `IOS`: Used for iOS devices
* `OSX`: Used for OSX devices
* `LINUX`: Used for Linux devices
* `WINDOWS`: Used for Windows devices

## NetworkType

This is used by Station Health Sensor to denote the type of network the station is using.  It is located in 
`redvox.api1000.wrapped_redvox_packet.station_information`.

These are the values of NetworkType:

* `UNKNOWN_NETWORK`: Unknown network.  Default value.
* `NO_NETWORK`: No network
* `WIFI`: Wifi network
* `CELLULAR`: Cellular network
* `WIRED`: Wired connection

## PowerState

This is used by Station Health Sensor to denote the power charging state of the station.  It is located in
`redvox.api1000.wrapped_redvox_packet.station_information`.

These are the values of PowerState:

* `UNKNOWN_POWER_STATE`: Unknown power state.  Default value.
* `UNPLUGGED`: Power cable unplugged
* `CHARGING`: Station is charging
* `CHARGED`: Station has full charge

## CellServiceState

This is used by Station Health Sensor to denote the status of the cellular service of the station.  It is located in
`redvox.api1000.wrapped_redvox_packet.station_information`.

These are the values of CellServiceState:

* `UNKNOWN`: Unknown cell service state.  Default value.
* `EMERGENCY`: Emergency service
* `NOMINAL`: Cell service is on and working
* `OUT_OF_SERVICE`: Cell service is unreachable
* `POWER_OFF`: Cell service is off

## WifiWakeLock

This is used by Station Health Sensor to denote the status of the station's wifi wake lock state.  It is located in
`redvox.api1000.wrapped_redvox_packet.station_information`.

These are the values of WifiWakeLock:

* `NONE`: No wifi.  Default value.
* `HIGH_PERF`: High performance state
* `LOW_LATENCY`: Low latency state
* `OTHER`: Other state

## ScreenState

This is used by Station Health Sensor to denote the status of the screen status of the station.  It is located in
`redvox.api1000.wrapped_redvox_packet.station_information`.

These are the values of ScreenState:

* `UNKNOWN_SCREEN_STATE`: Unknown screen state.  Default value.
* `ON`: Screen is on
* `OFF`: Screen is off
* `HEADLESS`: Station is running in headless (no screen) mode

## LocationProvider

This is used by Location Sensor to denote the source of the location data.  It is located in 
`redvox.api1000.wrapped_redvox_packet.sensors.location`.

These are the values of LocationProvider:

* `UNKNOWN`: Unknown location provider.  Default value.
* `NONE`: No location provider
* `USER`: User set the location manually
* `GPS`: Location provided by GPS
* `NETWORK`: Location provide by network device

## ImageCodec

This is used by the Image Sensor to denote the codec used to encode the image data.  It is located in
`from redvox.api1000.wrapped_redvox_packet.sensors.image`.

These are the values of ImageCodec:

* `UNKNOWN`: Unknown codec.  Default value.
* `PNG`: PNG codec
* `JPG`: JPG codec
* `BMP`: BMP codec

## AudioCodec

This is used by the Compressed Audio Sensor to denote the codec used to encode the audio data.  It is located in 
`from redvox.api1000.wrapped_redvox_packet.sensors.audio`.

These are the values of AudioCodec:

* `UNKNOWN`: Unknown codec.  Default value.
* `FLAC`: FLAC codec

## TimingScoreMethod

This is used by StationPacketMetadata to denote the method used grade the quality of timing of the data packet. 
It is located in `redvox.api1000.wrapped_redvox_packet.timing_information`.

These are the values of TimingScoreMethod:

* `UNKNOWN`: Unknown method.  Default value.

## ApiVersion

This is used by DataWindowConfig to select which file types to load.  It is located in `redvox.common.versioning`.

These are the values of ApiVersion:

* `API_900`: represents API900 files (.rdvxz extension) 
* `API_1000`: represents API1000 files (.rdvxm extension)
* `UNKNOWN`: represents all other file types.  Default value.

## DataPointCreationMode

This is used to determine how to create new data points when needed.  It is located in `redvox.common.gap_and_pad_utils`.

These are the values of DataPointCreationMode:

* `NAN`: Use np.nan for new points.  Default value.
* `COPY`: Copy the closest real data point
* `INTERPOLATE`: Calculate the interpolation of the new point based on existing points

## DataWindowOutputType

This is used to determine how to save DataWindows to disk, if at all.  It is located in `redvox.common.data_window_io.py`.

These are the values of DataWindowOutputType:

* `NONE`: No saving to disk.  Default value.
* `LZ4`: Save as .lz4
* `PARQUET`: Save as .parquet files
