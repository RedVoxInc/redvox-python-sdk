"""
Defines generic sensor data and data for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
"""
import enum
from typing import List, Union, Dict, Optional, Tuple
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq

import redvox.common.sensor_data_io as io
import redvox.common.date_time_utils as dtu
from redvox.common.io import FileSystemWriter as Fsw
from redvox.common import offset_model as om
from redvox.common.errors import RedVoxExceptions
from redvox.common.gap_and_pad_utils_wpa import calc_evenly_sampled_timestamps
from redvox.api1000.wrapped_redvox_packet.station_information import (
    NetworkType,
    PowerState,
    CellServiceState,
    WifiWakeLock,
    ScreenState,
)
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
from redvox.api1000.wrapped_redvox_packet.sensors.image import ImageCodec
from redvox.api1000.wrapped_redvox_packet.sensors.audio import AudioCodec

# columns that cannot be interpolated
NON_INTERPOLATED_COLUMNS = ["compressed_audio", "image"]
# columns that are not numeric but can be interpolated
NON_NUMERIC_COLUMNS = ["location_provider", "image_codec", "audio_codec", "network_type",
                       "power_state", "cell_service", "wifi_wake_lock", "screen_state"]


class SensorType(enum.Enum):
    """
    Enumeration of possible types of sensors to read data from
    """

    UNKNOWN_SENSOR = 0  # unknown sensor
    ACCELEROMETER = 1  # meters/second^2
    AMBIENT_TEMPERATURE = 2  # degrees Celsius
    AUDIO = 3  # normalized counts
    COMPRESSED_AUDIO = 4  # bytes (codec specific)
    GRAVITY = 5  # meters/second^2
    GYROSCOPE = 6  # radians/second
    IMAGE = 7  # bytes (codec specific)
    LIGHT = 8  # lux
    LINEAR_ACCELERATION = 9  # meters/second^2
    LOCATION = 10  # See standard
    MAGNETOMETER = 11  # microtesla
    ORIENTATION = 12  # radians
    PRESSURE = 13  # kilopascal
    PROXIMITY = 14  # on, off, cm
    RELATIVE_HUMIDITY = 15  # percentage
    ROTATION_VECTOR = 16  # Unitless
    INFRARED = 17  # this is proximity
    STATION_HEALTH = 18
    # Health sensors: battery charge and current level, phone internal temperature, network source and strength,
    # available RAM of the system, cell service status, amount of hard disk space left, power charging state
    # wifi lock state, cpu utilization, screen state, and screen brightness
    BEST_LOCATION = 19  # See standard

    @staticmethod
    def type_from_str(type_str: str) -> "SensorType":
        """
        converts a string to a sensor type

        :param type_str: string to convert
        :return: a sensor type, UNKNOWN_SENSOR is the default for invalid inputs
        """
        if (
                type_str.lower() == "audio"
                or type_str.lower() == "mic"
                or type_str.lower() == "microphone"
        ):
            return SensorType.AUDIO
        elif type_str.lower() == "accelerometer" or type_str.lower() == "accel":
            return SensorType.ACCELEROMETER
        elif type_str.lower() == "ambient_temperature":
            return SensorType.AMBIENT_TEMPERATURE
        elif type_str.lower() == "compressed_audio":
            return SensorType.COMPRESSED_AUDIO
        elif type_str.lower() == "gravity":
            return SensorType.GRAVITY
        elif type_str.lower() == "gyroscope" or type_str.lower() == "gyro":
            return SensorType.GYROSCOPE
        elif type_str.lower() == "image":
            return SensorType.IMAGE
        elif type_str.lower() == "light":
            return SensorType.LIGHT
        elif (
                type_str.lower() == "linear_acceleration"
                or type_str.lower() == "linear_accel"
        ):
            return SensorType.LINEAR_ACCELERATION
        elif type_str.lower() == "location" or type_str.lower() == "loc":
            return SensorType.LOCATION
        elif type_str.lower() == "best_location" or type_str.lower() == "best_loc":
            return SensorType.BEST_LOCATION
        elif type_str.lower() == "magnetometer" or type_str.lower() == "mag":
            return SensorType.MAGNETOMETER
        elif type_str.lower() == "orientation":
            return SensorType.ORIENTATION
        elif (
                type_str.lower() == "pressure"
                or type_str.lower() == "bar"
                or type_str.lower() == "barometer"
        ):
            return SensorType.PRESSURE
        elif type_str.lower() == "proximity" or type_str.lower() == "infrared":
            return SensorType.PROXIMITY
        elif type_str.lower() == "relative_humidity":
            return SensorType.RELATIVE_HUMIDITY
        elif type_str.lower() == "rotation_vector":
            return SensorType.ROTATION_VECTOR
        else:
            return SensorType.UNKNOWN_SENSOR


class SensorDataPa:
    """
    Generic SensorData class for API-independent analysis

    Properties:
        name: string, name of sensor.  REQUIRED

    Protected:
        _type: SensorType, enumerated type of sensor, default UNKNOWN_SENSOR

        _sample_rate_hz: float, sample rate in Hz of the sensor, default np.nan, usually 1/sample_interval_s

        _sample_interval_s: float, mean duration in seconds between samples, default np.nan, usually 1/sample_rate

        _sample_interval_std_s: float, standard deviation in seconds between samples, default np.nan

        _is_sample_rate_fixed: bool, True if sample rate is constant, default False

        _timestamps_altered: bool, True if timestamps in the sensor have been altered from their original values
        default False

        _use_offset_model: bool, if True, use an offset model to correct timestamps, otherwise use the best known
        offset.  default False

        _errors: RedVoxExceptions, class containing a list of all errors encountered by the sensor.

        _gaps: List of Tuples of floats, timestamps of data points on the edge of gaps, default empty list

        _fs_writer: FileSystemWriter, handles file system i/o parameters

        _data: pyarrow Table, used to store the data when it's not written to the disk.  default None
    """

    def __init__(
            self,
            sensor_name: str,
            sensor_data: Optional[pa.Table] = None,
            sensor_type: SensorType = SensorType.UNKNOWN_SENSOR,
            sample_rate_hz: float = np.nan,
            sample_interval_s: float = np.nan,
            sample_interval_std_s: float = np.nan,
            is_sample_rate_fixed: bool = False,
            are_timestamps_altered: bool = False,
            calculate_stats: bool = False,
            use_offset_model_for_correction: bool = False,
            save_data: bool = False,
            base_dir: str = ".",
            gaps: Optional[List[Tuple[float, float]]] = None,
            show_errors: bool = False
    ):
        """
        initialize the sensor data with params

        :param sensor_name: name of the sensor.  REQUIRED
        :param sensor_type: enumerated type of the sensor, default SensorType.UNKNOWN_SENSOR
        :param sensor_data: Optional pyarrow table with the timestamps and sensor data;
                            first column is always the timestamps,
                            the other columns are specific metadata and data channels in the sensor
                            default is None
        :param sample_rate_hz: sample rate in hz of the data
        :param sample_interval_s: sample interval in seconds of the data
        :param sample_interval_std_s: std dev of sample interval in seconds of the data
        :param is_sample_rate_fixed: if True, sample rate is constant for all data, default False
        :param are_timestamps_altered: if True, timestamps in the sensor have been altered from their
                                        original values, default False
        :param calculate_stats: if True, calculate sample_rate, sample_interval_s, and sample_interval_std_s
                                default False
        :param use_offset_model_for_correction: if True, use an offset model to correct timestamps, otherwise
                                                use the best known offset.  default False
        :param save_data: if True, save the data of the sensor to disk, otherwise use a temporary dir.  default False
        :param base_dir: directory to save pyarrow table, default "." (current dir).  internally uses a temporary
                            dir if not saving data
        :param gaps: Optional list of timestamp pairs of data points on the edge of gaps in the data.  anything between
                        the pairs of points exists to maintain sample rate and are not considered valid points.
                        Default None
        :param show_errors: if True, show any errors encountered.  Default False
        """
        self._errors: RedVoxExceptions = RedVoxExceptions("Sensor")
        self.name: str = sensor_name
        self._type: SensorType = sensor_type
        self._sample_rate_hz: float = sample_rate_hz
        self._sample_interval_s: float = sample_interval_s
        self._sample_interval_std_s: float = sample_interval_std_s
        self._is_sample_rate_fixed: bool = is_sample_rate_fixed
        self._timestamps_altered: bool = are_timestamps_altered
        self._use_offset_model: bool = use_offset_model_for_correction
        self._fs_writer = Fsw("", "parquet", base_dir, save_data)
        self._gaps: List[Tuple] = gaps if gaps else []
        self._data: Optional[pa.Table()] = None
        if sensor_data:
            if "timestamps" not in sensor_data.schema.names:
                self._errors.append('must have a column titled "timestamps"')
            elif sensor_data['timestamps'].length() > 0:
                self.set_file_name(f"{sensor_type.name}_{int(sensor_data['timestamps'][0].as_py())}")
                if calculate_stats:
                    self.organize_and_update_stats(sensor_data)
                elif sensor_data["timestamps"].length() > 1:
                    self.sort_by_data_timestamps(sensor_data)
                else:
                    self.write_pyarrow_table(sensor_data)
        else:
            self._errors.append('cannot be empty')
        if show_errors:
            self.print_errors()

    @staticmethod
    def from_dir(
            sensor_name: str,
            data_path: str,
            sensor_type: SensorType = SensorType.UNKNOWN_SENSOR,
            sample_rate_hz: float = np.nan,
            sample_interval_s: float = np.nan,
            sample_interval_std_s: float = np.nan,
            is_sample_rate_fixed: bool = False,
            are_timestamps_altered: bool = False,
            calculate_stats: bool = False,
            use_offset_model_for_correction: bool = False,
            save_data: bool = False) -> "SensorDataPa":
        """
        init but with a path to directory containing parquet file(s) instead of a table of data

        :param sensor_name: name of the sensor
        :param data_path: path to the directory containing the parquet files
        :param sensor_type: enumerated type of the sensor, default SensorType.UNKNOWN_SENSOR
        :param sample_rate_hz: sample rate in hz of the data, default np.nan
        :param sample_interval_s: sample interval in seconds of the data, default np.nan
        :param sample_interval_std_s: std dev of sample interval in seconds of the data, default np.nan
        :param is_sample_rate_fixed: if True, sample rate is constant for all data, default False
        :param are_timestamps_altered: if True, timestamps in the sensor have been altered from their
                                        original values, default False
        :param calculate_stats: if True, calculate sample_rate, sample_interval_s, and sample_interval_std_s
                                default False
        :param use_offset_model_for_correction: if True, use an offset model to correct timestamps, otherwise
                                                use the best known offset.  default False
        :param save_data: if True, save the data of the sensor to disk, otherwise use a temporary dir.  default False
        :return: SensorData object
        """
        result = SensorDataPa(sensor_name,
                              ds.dataset(data_path, format="parquet", exclude_invalid_files=True).to_table(),
                              sensor_type, sample_rate_hz, sample_interval_s, sample_interval_std_s,
                              is_sample_rate_fixed, are_timestamps_altered, calculate_stats,
                              use_offset_model_for_correction, save_data, data_path)
        result.set_file_name()
        return result

    @staticmethod
    def from_dict(
            sensor_name: str,
            sensor_data: Dict,
            sensor_type: SensorType = SensorType.UNKNOWN_SENSOR,
            sample_rate_hz: float = np.nan,
            sample_interval_s: float = np.nan,
            sample_interval_std_s: float = np.nan,
            is_sample_rate_fixed: bool = False,
            are_timestamps_altered: bool = False,
            calculate_stats: bool = False,
            use_offset_model_for_correction: bool = False,
            save_data: bool = False,
            arrow_dir: str = "",
    ) -> "SensorDataPa":
        """
        init but with a dictionary

        :param sensor_name: name of the sensor
        :param sensor_type: enumerated type of the sensor, default SensorType.UNKNOWN_SENSOR
        :param sensor_data: dict with the timestamps and sensor data; first column is always the timestamps,
                            the other columns are the data channels in the sensor
        :param sample_rate_hz: sample rate in hz of the data, default np.nan
        :param sample_interval_s: sample interval in seconds of the data, default np.nan
        :param sample_interval_std_s: std dev of sample interval in seconds of the data, default np.nan
        :param is_sample_rate_fixed: if True, sample rate is constant for all data, default False
        :param are_timestamps_altered: if True, timestamps in the sensor have been altered from their
                                        original values, default False
        :param calculate_stats: if True, calculate sample_rate, sample_interval_s, and sample_interval_std_s
                                default False
        :param use_offset_model_for_correction: if True, use an offset model to correct timestamps, otherwise
                                                use the best known offset.  default False
        :param save_data: if True, save the data of the sensor to disk, otherwise use a temporary dir.  default False
        :param arrow_dir: directory to save pyarrow table, default "" (current dir).  default temporary dir if not
                            saving data
        :return: SensorData object
        """
        return SensorDataPa(sensor_name, pa.Table.from_pydict(sensor_data), sensor_type, sample_rate_hz,
                            sample_interval_s, sample_interval_std_s, is_sample_rate_fixed, are_timestamps_altered,
                            calculate_stats, use_offset_model_for_correction, save_data, arrow_dir)

    def is_save_to_disk(self) -> bool:
        """
        :return: True if sensor will be saved to disk
        """
        return self._fs_writer.save_to_disk

    def set_save_to_disk(self, save: bool):
        """
        :param save: If True, save to disk
        """
        self._fs_writer.save_to_disk = save

    def set_file_name(self, new_file: Optional[str] = None):
        """
        set the pyarrow file name or use the default: {sensor_type}_{int(first_timestamp)}
        Do not give an extension

        :param new_file: optional file name to change to; default None (use default name)
        """
        self._fs_writer.file_name = new_file if new_file else f"{self._type.name}_{int(self.first_data_timestamp())}"

    def set_base_dir(self, new_dir: Optional[str] = None):
        """
        set the pyarrow directory or use the default: "." (current directory)

        :param new_dir: the directory to change to; default None (use current directory)
        """
        self._fs_writer.base_dir = new_dir if new_dir else "."

    def full_file_name(self) -> str:
        """
        :return: full name of parquet file containing the data
        """
        return self._fs_writer.full_name()

    def file_name(self) -> str:
        """
        :return: file name without extension
        """
        return self._fs_writer.file_name

    def base_dir(self) -> str:
        """
        :return: directory containing parquet files for the sensor
        """
        return self._fs_writer.save_dir()

    def full_path(self) -> str:
        """
        :return: the full path to the data file
        """
        return self._fs_writer.full_path()

    def fs_writer(self) -> Fsw:
        """
        :return: FileSystemWriter object
        """
        return self._fs_writer

    def pyarrow_ds(self, base_dir: Optional[str] = None) -> ds.Dataset:
        """
        :param base_dir: optional directory to use when loading the dataset.  if None, use self.base_dir()
        :return: the dataset stored in base_dir
        """
        if base_dir is None:
            base_dir = self.base_dir()
        return ds.dataset(base_dir, format="parquet", exclude_invalid_files=True)

    def pyarrow_table(self) -> pa.Table:
        """
        :return: the table defined by the dataset stored in self
        """
        return self._data if self._data else self.pyarrow_ds().to_table()

    def data_df(self) -> pd.DataFrame:
        """
        :return: the pandas dataframe defined by the dataset stored in self._arrow_dir
        """
        return self.pyarrow_table().to_pandas()

    def write_pyarrow_table(self, table: pa.Table):
        """
        saves the pyarrow table to disk or to memory.
        if writing to disk, uses a default filename: {sensor_type}_{first_timestamp}.parquet
        creates the directory if it doesn't exist and removes any existing parquet files

        :param table: the table to write
        """
        self._data = table
        # self._fs_writer.create_dir()
        # pq.write_table(table, self.full_path())

    def _actual_file_write_table(self):
        self._fs_writer.create_dir()
        pq.write_table(self._data, self.full_path())
        self._data = None

    def errors(self) -> RedVoxExceptions:
        """
        :return: errors of the sensor
        """
        return self._errors

    def gaps(self) -> List[Tuple]:
        """
        :return: start and end timestamps of gaps in data
        """
        return self._gaps

    def type(self) -> SensorType:
        """
        :return: type of sensor
        """
        return self._type

    def type_as_str(self) -> str:
        """
        gets the sensor type as a string

        :return: sensor type of the sensor as a string
        """
        return self._type.name

    def sample_rate_hz(self) -> float:
        """
        :return: sample rate in Hz
        """
        return self._sample_rate_hz

    def sample_interval_s(self) -> float:
        """
        :return: mean sample interval in seconds
        """
        return self._sample_interval_s

    def sample_interval_std_s(self) -> float:
        """
        :return: sample interval standard deviation in seconds
        """
        return self._sample_interval_std_s

    def is_sample_rate_fixed(self) -> bool:
        """
        :return: true if sample rate of sensor is constant
        """
        return self._is_sample_rate_fixed

    def is_timestamps_altered(self) -> bool:
        """
        :return: true if timestamps have been changed from original data values
        """
        return self._timestamps_altered

    def used_offset_model(self) -> bool:
        """
        :return: true if an offset model was used to perform timestamp corrections
        """
        return self._use_offset_model

    def sort_by_data_timestamps(self, ptable: pa.Table, ascending: bool = True):
        """
        sorts the data based on timestamps

        :param ptable: pyarrow table to sort
        :param ascending: if True, timestamps are sorted in ascending order, else sort by descending order
        """
        if ascending:
            order = "ascending"
        else:
            order = "descending"
        data = pc.take(ptable, pc.sort_indices(ptable, sort_keys=[("timestamps", order)]))
        # if not np.isnan(self.first_data_timestamp()) and self.first_data_timestamp() != data['timestamps'][0].as_py():
        #     os.remove(self.full_path())
        # self.set_file_name(f"{self._type.name}_{int(data['timestamps'][0].as_py())}")
        self.write_pyarrow_table(data)

    def organize_and_update_stats(self, ptable: pa.Table) -> "SensorDataPa":
        """
        sorts the data by timestamps, then if the sample rate is not fixed, recalculates the sample rate, interval,
            and interval std dev.  If there is only one value, sets the sample rate, interval, and interval std dev
            to np.nan.  Updates the SensorData object with the new values

        :param ptable: pyarrow table to update
        :return: updated version of self
        """
        self.sort_by_data_timestamps(ptable)
        if not self._is_sample_rate_fixed:
            if self.num_samples() > 1:
                timestamp_diffs = np.diff(self.data_timestamps())
                self._sample_interval_s = dtu.microseconds_to_seconds(
                    float(np.mean(timestamp_diffs))
                )
                self._sample_interval_std_s = dtu.microseconds_to_seconds(
                    float(np.std(timestamp_diffs))
                )
                self._sample_rate_hz = (
                    np.nan
                    if self.is_sample_interval_invalid()
                    else 1 / self._sample_interval_s
                )
            else:
                self._sample_interval_s = np.nan
                self._sample_interval_std_s = np.nan
                self._sample_rate_hz = np.nan
        return self

    def append_sensor(self, new_sensor: "SensorDataPa", recalculate_stats: bool = False) -> "SensorDataPa":
        """
        append the new data to the sensor, update the sensor's stats on demand if it doesn't have a fixed
            sample rate, then return the updated SensorData object

        :param new_sensor: sensor containing data to add to the calling sensor
        :param recalculate_stats: if True and the sensor does not have a fixed sample rate, sort the timestamps,
                                    recalculate the sample rate, interval, and interval std dev, default False
        :return: the updated SensorData object
        """
        _arrow: pa.Table = pa.concat_tables([self.pyarrow_table(), new_sensor.pyarrow_table()])
        if recalculate_stats and not self._is_sample_rate_fixed:
            self.organize_and_update_stats(_arrow)
        else:
            self.write_pyarrow_table(_arrow)
        return self

    def append_data(
            self, new_data: List[np.array], recalculate_stats: bool = False
    ) -> "SensorDataPa":
        """
        append the new data to the dataframe, update the sensor's stats on demand if it doesn't have a fixed
            sample rate, then return the updated SensorData object

        :param new_data: list of arrays containing data to add to the sensor's dataframe
        :param recalculate_stats: if True and the sensor does not have a fixed sample rate, sort the timestamps,
                                    recalculate the sample rate, interval, and interval std dev, default False
        :return: the updated SensorData object
        """
        _arrow = pa.concat_tables([self.pyarrow_table(),
                                   pa.Table.from_arrays(arrays=[pa.array(s) for s in new_data],
                                                        names=self.data_channels())])
        if recalculate_stats and not self._is_sample_rate_fixed:
            self.organize_and_update_stats(_arrow)
        else:
            self.write_pyarrow_table(_arrow)
        return self

    def is_sample_interval_invalid(self) -> bool:
        """
        :return: True if sample interval is np.nan or equal to 0.0
        """
        return np.isnan(self._sample_interval_s) or self._sample_interval_s == 0.0

    def data_timestamps(self) -> np.array:
        """
        :return: the timestamps as a numpy array or [np.nan] if none exist
        """
        if "timestamps" in self.pyarrow_table().schema.names:
            return self.pyarrow_table()["timestamps"].to_numpy()
        else:
            return np.array([np.nan])

    def unaltered_data_timestamps(self) -> np.array:
        """
        :return: the unaltered timestamps as a numpy array
        """
        if "unaltered_timestamps" in self.pyarrow_table().schema.names:
            return self.pyarrow_table()["unaltered_timestamps"].to_numpy()
        else:
            return np.array([np.nan])

    def first_data_timestamp(self) -> float:
        """
        :return: timestamp of the first data point or np.nan if no timestamps
        """
        return self.data_timestamps()[0]

    def last_data_timestamp(self) -> float:
        """
        :return: timestamp of the last data point or np.nan if no timestamps
        """
        return self.data_timestamps()[-1]

    def num_samples(self) -> int:
        """
        :return: the number of rows (samples) in the dataframe
        """
        if self.pyarrow_table():
            return self.pyarrow_table().num_rows
        return 0

    def samples(self) -> np.ndarray:
        """
        gets the non-timestamp samples of dataframe

        :return: the data values of the dataframe as a numpy ndarray
        """
        return self.data_df().iloc[:, 2:].T.to_numpy()

    def data_channels(self) -> List[str]:
        """
        :return: a list of the names of the columns (data channels) of the dataframe
        """
        return self.pyarrow_table().schema.names

    def get_data_channel(self, channel_name: str) -> Union[np.array, List[str]]:
        """
        gets the data channel specified, raises an error and lists valid fields if channel_name is not in the dataframe

        :param channel_name: the name of the channel to get data for
        :return: the data values of the channel as a numpy array or list of strings for enumerated channels
        """
        _arrow = self.pyarrow_table()
        if channel_name not in _arrow.schema.names:
            self._errors.append(f"WARNING: {channel_name} does not exist; try one of {_arrow.schema.names}")
            return []
        if channel_name == "location_provider":
            return [LocationProvider(c).name for c in _arrow[channel_name]]
        elif channel_name == "image_codec":
            return [ImageCodec(c).name for c in _arrow[channel_name]]
        elif channel_name == "audio_codec":
            return [AudioCodec(c).name for c in _arrow[channel_name]]
        elif channel_name == "network_type":
            return [NetworkType(c).name for c in _arrow[channel_name]]
        elif channel_name == "power_state":
            return [PowerState(c).name for c in _arrow[channel_name]]
        elif channel_name == "cell_service":
            return [CellServiceState(c).name for c in _arrow[channel_name]]
        elif channel_name == "wifi_wake_lock":
            return [WifiWakeLock(c).name for c in _arrow[channel_name]]
        elif channel_name == "screen_state":
            return [ScreenState(c).name for c in _arrow[channel_name]]
        return _arrow[channel_name].to_numpy()

    def get_valid_data_channel_values(self, channel_name: str) -> np.array:
        """
        gets all non-nan values from the channel specified

        :param channel_name: the name of the channel to get data for
        :return: non-nan values of the channel as a numpy array
        """
        channel_data = self.get_data_channel(channel_name)
        return channel_data[~np.isnan(channel_data)]

    def print_errors(self):
        """
        print all errors to screen
        """
        self._errors.print()

    def extend_errors(self, errors: RedVoxExceptions):
        """
        add errors to the SensorData's errors

        :param errors: errors to add
        """
        self._errors.extend_error(errors)

    def update_data_timestamps(self, offset_model: om.OffsetModel):
        """
        updates the timestamps of the data points

        :param offset_model: model used to update the timestamps
        """
        slope = dtu.seconds_to_microseconds(self._sample_interval_s) * (1 + offset_model.slope) \
            if self._use_offset_model else dtu.seconds_to_microseconds(self._sample_interval_s)
        if self._type == SensorType.AUDIO:
            # use the model to update the first timestamp or add the best offset (model's intercept value)
            timestamps = pa.array(
                calc_evenly_sampled_timestamps(
                    offset_model.update_time(self.first_data_timestamp(), self._use_offset_model),
                    self.num_samples(),
                    slope))
        else:
            timestamps = pa.array(offset_model.update_timestamps(self.data_timestamps(),
                                                                 self._use_offset_model))
        # old_name = self.full_path()
        self.write_pyarrow_table(self.pyarrow_table().set_column(0, "timestamps", timestamps))
        self.set_file_name()
        # os.rename(old_name, self.full_path())
        time_diffs = np.floor(np.diff(self.data_timestamps()))
        if len(time_diffs) > 1:
            self._sample_interval_s = dtu.microseconds_to_seconds(slope)
            if self._sample_interval_s > 0:
                self._sample_rate_hz = 1 / self._sample_interval_s
                self._sample_interval_std_s = dtu.microseconds_to_seconds(np.std(time_diffs))
        self._timestamps_altered = True

    def interpolate(self, interpolate_timestamp: float, first_point: int, second_point: int = 0,
                    copy: bool = True) -> pa.Table:
        """
        interpolates two points at the intercept value.  the two points must be consecutive in the dataframe.
        data channels that can't be interpolated are set to np.nan.

        :param interpolate_timestamp: timestamp to interpolate other values
        :param first_point: index of first point
        :param second_point: delta to second point, default 0 (same as first point)
        :param copy: if True, copies the values of the first point, default True
        :return: pyarrow Table of interpolated points
        """
        start_point = self.pyarrow_table().slice(first_point, 1).to_pydict()
        if not copy and second_point:
            i_p = {}
            end_point = self.pyarrow_table().slice(first_point + second_point, 1).to_pydict()
            first_closer = \
                np.abs(start_point[0] - interpolate_timestamp) \
                <= np.abs(end_point[0] - interpolate_timestamp)
            for col in self.pyarrow_table().schema.names:
                # process each column independently into new table object
                if col not in NON_INTERPOLATED_COLUMNS + NON_NUMERIC_COLUMNS:
                    numeric_diff = end_point[col] - start_point[col]
                    numeric_diff = \
                        (numeric_diff / numeric_diff["timestamps"]) * \
                        (interpolate_timestamp - start_point[col]) + start_point[col]
                    i_p[col] = numeric_diff
                elif col in NON_NUMERIC_COLUMNS:
                    if first_closer:
                        i_p[col] = start_point[col]
                    else:
                        i_p[col] = end_point[col]
        else:
            i_p = start_point
        i_p["timestamps"] = [interpolate_timestamp]
        return pa.Table.from_pydict(i_p)

    def as_dict(self) -> dict:
        """
        :return: sensor as dict
        """
        return {
            "name": self.name,
            "type": self._type.name,
            "num_samples": self.num_samples(),
            "sample_rate_hz": self._sample_rate_hz,
            "sample_interval_s": self._sample_interval_s,
            "sample_interval_std_s": self._sample_interval_std_s,
            "is_sample_rate_fixed": self._is_sample_rate_fixed,
            "timestamps_altered": self._timestamps_altered,
            "use_offset_model": self._use_offset_model,
            "gaps": self._gaps,
            "fs_writer": self._fs_writer.as_dict(),
            "errors": self._errors.as_dict()
        }

    def to_json(self) -> str:
        """
        :return: sensor as json string
        """
        return io.to_json(self)

    def to_json_file(self, file_name: Optional[str] = None) -> Path:
        """
        saves the sensor as json and data in the same directory.

        :param file_name: the optional base file name.  Do not include a file extension.
                            If None, a default file name is created using this format:
                            [sensor_type]_[first_timestamp].json
        :return: path to json file
        """
        if self._fs_writer.file_extension == "parquet":
            self._actual_file_write_table()
        return io.to_json_file(self, file_name)

    @staticmethod
    def from_json_file(file_path: str) -> "SensorDataPa":
        """
        convert contents of json file to SensorData

        :param file_path: full path of file to load data from.
        :return: SensorData object
        """
        json_data = io.from_json(file_path)
        if "name" in json_data.keys():
            result = SensorDataPa.from_dir(json_data["name"], json_data["fs_writer"]["base_dir"],
                                           SensorType[json_data["type"]],
                                           json_data["sample_rate_hz"], json_data["sample_interval_s"],
                                           json_data["sample_interval_std_s"], json_data["is_sample_rate_fixed"],
                                           json_data["timestamps_altered"], False, json_data["use_offset_model"])
            result._errors = RedVoxExceptions.from_dict(json_data["errors"])
            result._gaps = json_data["gaps"]
        else:
            result = SensorDataPa("Empty")
            result._errors.append("Loading from json file failed; Sensor missing name.")
        return result
