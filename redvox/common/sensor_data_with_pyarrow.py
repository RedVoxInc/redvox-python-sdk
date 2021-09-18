"""
Defines generic sensor data and data for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
"""
import enum
from typing import List, Union, Dict, Optional, Tuple
import os
import tempfile
from glob import glob
from pathlib import Path
import json

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq

import redvox.common.date_time_utils as dtu
from redvox.common import offset_model as om
from redvox.common.errors import RedVoxExceptions
from redvox.common.gap_and_pad_utils_wpa import calc_evenly_sampled_timestamps
from redvox.api1000.wrapped_redvox_packet.station_information import (
    NetworkType,
    PowerState,
    CellServiceState,
)
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider
from redvox.api1000.wrapped_redvox_packet.sensors.image import ImageCodec
from redvox.api1000.wrapped_redvox_packet.sensors.audio import AudioCodec

# columns that cannot be interpolated
NON_INTERPOLATED_COLUMNS = ["compressed_audio", "image"]
# columns that are not numeric but can be interpolated
NON_NUMERIC_COLUMNS = ["location_provider", "image_codec", "audio_codec",
                       "network_type", "power_state", "cell_service"]


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
    # battery charge and current level, phone internal temperature, network source and strength,
    # available RAM of the system, cell service status, amount of hard disk space left, power charging state
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

        type: SensorType, enumerated type of sensor, default UNKNOWN_SENSOR

        sample_rate_hz: float, sample rate in Hz of the sensor, default np.nan, usually 1/sample_interval_s

        sample_interval_s: float, mean duration in seconds between samples, default np.nan, usually 1/sample_rate

        sample_interval_std_s: float, standard deviation in seconds between samples, default np.nan

        is_sample_rate_fixed: bool, True if sample rate is constant, default False

        timestamps_altered: bool, True if timestamps in the sensor have been altered from their original values
        default False

        use_offset_model: bool, if True, use an offset model to correct timestamps, otherwise use the best known
        offset.  default False

        errors: RedVoxExceptions, class containing a list of all errors encountered by the sensor.

        gaps: List of Tuples of floats, timestamps of data points on the edge of gaps, default empty list

    Protected:
        _arrow_file: string, file name of data file

        _arrow_dir: string, directory where the data is saved to, default "" (current directory)

        _save_data: bool, if True, save data to _arrow_dir, otherwise use a temp dir.  default False
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
            arrow_dir: str = ".",
            gaps: Optional[List[Tuple[float, float]]] = None
    ):
        """
        initialize the sensor data with params

        :param sensor_name: name of the sensor.  REQUIRED
        :param sensor_type: enumerated type of the sensor, default SensorType.UNKNOWN_SENSOR
        :param sensor_data: Optional pyarrow table with the timestamps and sensor data;
                            first column is always the timestamps,
                            the other columns are the data channels in the sensor
                            if not given, will search arrow_dir for data
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
        :param arrow_dir: directory to save pyarrow table, default "." (current dir).  internally uses a temporary
                            dir if not saving data
        :param gaps: Optional list of timestamp pairs of data points on the edge of gaps in the data.  anything between
                        the pairs of points exists to maintain sample rate and are not considered valid points.
                        Default None
        """
        self.errors: RedVoxExceptions = RedVoxExceptions("Sensor")
        self.name: str = sensor_name
        self.type: SensorType = sensor_type
        self.sample_rate_hz: float = sample_rate_hz
        self.sample_interval_s: float = sample_interval_s
        self.sample_interval_std_s: float = sample_interval_std_s
        self.is_sample_rate_fixed: bool = is_sample_rate_fixed
        self.timestamps_altered: bool = are_timestamps_altered
        self.use_offset_model: bool = use_offset_model_for_correction
        self._arrow_file: str = ""
        self._save_data: bool = save_data
        if gaps:
            self.gaps = gaps
        else:
            self.gaps = []
        self._temp_dir = tempfile.TemporaryDirectory()
        self._arrow_dir: str = arrow_dir if self._save_data or arrow_dir else self._temp_dir.name
        self._data: Optional[pa.Table] = None
        if sensor_data:
            if "timestamps" not in sensor_data.schema.names:
                self.errors.append('must have a column titled "timestamps"')
            elif sensor_data['timestamps'].length() > 0:
                self._arrow_file: str = f"{sensor_type.name}_{int(sensor_data['timestamps'][0].as_py())}.parquet"
                if calculate_stats:
                    self.organize_and_update_stats(sensor_data)
                elif sensor_data["timestamps"].length() > 1:
                    self.sort_by_data_timestamps(sensor_data)
                else:
                    self.write_pyarrow_table(sensor_data)

    def __del__(self):
        self._temp_dir.cleanup()

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
        result = SensorDataPa(sensor_name, None,
                              sensor_type, sample_rate_hz, sample_interval_s, sample_interval_std_s,
                              is_sample_rate_fixed, are_timestamps_altered, calculate_stats,
                              use_offset_model_for_correction, save_data, data_path)
        result.set_arrow_file()
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
        return self._save_data

    def set_arrow_file(self, new_file: Optional[str] = None):
        """
        set the pyarrow file name or use the default: {sensor_type.name}_{int(first_timestamp)}.parquet
        :param new_file: optional file name to change to; default None (use default name)
        """
        if new_file:
            self._arrow_file = new_file
        else:
            self._arrow_file = f"{self.type.name}_{int(self.first_data_timestamp())}.parquet"

    def set_arrow_dir(self, new_dir: str):
        """
        set the pyarrow directory
        :param new_dir: the directory to change to
        """
        self._arrow_dir = new_dir

    def pyarrow_ds(self) -> ds.Dataset:
        """
        :return: the dataset stored in self._arrow_dir
        """
        return ds.dataset(self._arrow_dir, format="parquet", exclude_invalid_files=True)

    def pyarrow_table(self) -> pa.Table:
        """
        :return: the table defined by the dataset stored in self._arrow_dir
        """
        if self._data:
            return self._data
        return self.pyarrow_ds().to_table()

    def data_df(self) -> pd.DataFrame:
        """
        :return: the pandas dataframe defined by the dataset stored in self._arrow_dir
        """
        return self.pyarrow_table().to_pandas()

    def write_pyarrow_table(self, table: pa.Table):
        """
        saves the pyarrow table to disk or to memory if self._save_data is False
        if writing to disk, uses a default filename: {sensor_type}_{first_timestamp}.parquet
        if writing to disk, removes the _data from memory.

        :param table: the table to write
        """
        if self._save_data:
            # clear the output dir where the table will be written to
            filelist = glob(os.path.join(self._arrow_dir, "*.parquet"))
            for f in filelist:
                os.remove(f)
            pq.write_table(table, os.path.join(self._arrow_dir, self._arrow_file))
            self._data = None
        else:
            self._data = table

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
        self._arrow_file: str = f"{self.type.name}_{int(data['timestamps'][0].as_py())}.parquet"
        # self.write_pyarrow_table(data)
        self._data = data

    def organize_and_update_stats(self, ptable: pa.Table) -> "SensorDataPa":
        """
        sorts the data by timestamps, then if the sample rate is not fixed, recalculates the sample rate, interval,
            and interval std dev.  If there is only one value, sets the sample rate, interval, and interval std dev
            to np.nan.  Updates the SensorData object with the new values

        :param ptable: pyarrow table to update
        :return: updated version of self
        """
        self.sort_by_data_timestamps(ptable)
        if not self.is_sample_rate_fixed:
            if self.num_samples() > 1:
                timestamp_diffs = np.diff(self.data_timestamps())
                self.sample_interval_s = dtu.microseconds_to_seconds(
                    float(np.mean(timestamp_diffs))
                )
                self.sample_interval_std_s = dtu.microseconds_to_seconds(
                    float(np.std(timestamp_diffs))
                )
                self.sample_rate_hz = (
                    np.nan
                    if self.is_sample_interval_invalid()
                    else 1 / self.sample_interval_s
                )
            else:
                self.sample_interval_s = np.nan
                self.sample_interval_std_s = np.nan
                self.sample_rate_hz = np.nan
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
        if recalculate_stats and not self.is_sample_rate_fixed:
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
        if recalculate_stats and not self.is_sample_rate_fixed:
            self.organize_and_update_stats(_arrow)
        else:
            self.write_pyarrow_table(_arrow)
        return self

    def is_sample_interval_invalid(self) -> bool:
        """
        :return: True if sample interval is np.nan or equal to 0.0
        """
        return np.isnan(self.sample_interval_s) or self.sample_interval_s == 0.0

    def sensor_type_as_str(self) -> str:
        """
        gets the sensor type as a string

        :return: sensor type of the sensor as a string
        """
        return self.type.name

    def data_timestamps(self) -> np.array:
        """
        :return: the timestamps as a numpy array
        """
        return self.pyarrow_table()["timestamps"].to_numpy()

    def unaltered_data_timestamps(self) -> np.array:
        """
        :return: the unaltered timestamps as a numpy array
        """
        return self.pyarrow_table()["unaltered_timestamps"].to_numpy()

    def first_data_timestamp(self) -> float:
        """
        :return: timestamp of the first data point
        """
        return self.data_timestamps()[0]

    def last_data_timestamp(self) -> float:
        """
        :return: timestamp of the last data point
        """
        return self.data_timestamps()[-1]

    def num_samples(self) -> int:
        """
        :return: the number of rows (samples) in the dataframe
        """
        if self._arrow_file:
            return len(self.data_timestamps())
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
            self.errors.append(f"WARNING: {channel_name} does not exist; try one of {_arrow.schema.names}")
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
        return _arrow[channel_name].to_numpy()

    def get_valid_data_channel_values(self, channel_name: str) -> np.array:
        """
        gets all non-nan values from the channel specified

        :param channel_name: the name of the channel to get data for
        :return: non-nan values of the channel as a numpy array
        """
        channel_data = self.get_data_channel(channel_name)
        return channel_data[~np.isnan(channel_data)]

    def update_data_timestamps(self, offset_model: om.OffsetModel, use_model_function: bool = True):
        """
        updates the timestamps of the data points

        :param offset_model: model used to update the timestamps
        :param use_model_function: if True, use the offset model's correction function to correct time,
                                    otherwise use best offset (model's intercept value).  default True
        """
        slope = dtu.seconds_to_microseconds(self.sample_interval_s) * (1 + offset_model.slope) \
            if use_model_function else dtu.seconds_to_microseconds(self.sample_interval_s)
        if self.type == SensorType.AUDIO:
            # use the model to update the first timestamp or add the best offset (model's intercept value)
            timestamps = pa.array(
                calc_evenly_sampled_timestamps(
                    offset_model.update_time(self.first_data_timestamp(), use_model_function),
                    self.num_samples(),
                    slope))
        else:
            timestamps = pa.array(offset_model.update_timestamps(self.data_timestamps(),
                                                                 use_model_function))
        self._data = self.pyarrow_table().set_column(0, "timestamps", timestamps)
        self.set_arrow_file()
        time_diffs = np.floor(np.diff(self.data_timestamps()))
        if len(time_diffs) > 1:
            self.sample_interval_s = dtu.microseconds_to_seconds(slope)
            if self.sample_interval_s > 0:
                self.sample_rate_hz = 1 / self.sample_interval_s
                self.sample_interval_std_s = dtu.microseconds_to_seconds(np.std(time_diffs))
        self.timestamps_altered = True

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

    def get_file_path(self) -> str:
        """
        :return: the supposed file path to the data file
        """
        return os.path.join(self._arrow_dir, self._arrow_file)

    def as_dict(self) -> dict:
        """
        :return: sensor as dict
        """
        return {
            "name": self.name,
            "type": self.type.name,
            "num_samples": self.num_samples(),
            "sample_rate_hz": self.sample_rate_hz,
            "sample_interval_s": self.sample_interval_s,
            "sample_interval_std_s": self.sample_interval_std_s,
            "is_sample_rate_fixed": self.is_sample_rate_fixed,
            "timestamps_altered": self.timestamps_altered,
            "use_offset_model": self.use_offset_model,
            "gaps": self.gaps,
            "parquet_dir": self._arrow_dir,
            "parquet_file": self._arrow_file,
            "errors": self.errors.as_dict()
        }

    def to_json(self) -> str:
        """
        :return: sensor as json string
        """
        return json.dumps(self.as_dict())

    def to_json_file(self, file_name: Optional[str] = None) -> Path:
        """
        saves the sensor as json and data in the same directory.

        :param file_name: the optional base file name.  Do not include a file extension.
                            If None, a default file name is created using this format:
                            [sensor_type]_[first_timestamp].json
        :return: path to json file
        """
        _file_name: str = (
            file_name
            if file_name is not None
            else self._arrow_file.split(".")[0]
        )
        if self._save_data:
            pq.write_table(self._data, os.path.join(self._arrow_dir, self._arrow_file))
        file_path: Path = Path(self._arrow_dir).joinpath(f"{_file_name}.json")
        with open(file_path, "w") as f_p:
            f_p.write(self.to_json())
            return file_path.resolve(False)

    @staticmethod
    def from_json(file_path: str) -> "SensorDataPa":
        """
        convert contents of json file to SensorData
        :param file_path: full path of file to load data from.
        :return: SensorData object
        """
        with open(file_path, "r") as f_p:
            json_data = json.loads(f_p.read())
        if "name" in json_data.keys():
            result = SensorDataPa.from_dir(json_data["name"], json_data["parquet_dir"], SensorType[json_data["type"]],
                                           json_data["sample_rate_hz"], json_data["sample_interval_s"],
                                           json_data["sample_interval_std_s"], json_data["is_sample_rate_fixed"],
                                           json_data["timestamps_altered"], False, json_data["use_offset_model"])
            result.errors = RedVoxExceptions.from_dict(json_data["errors"])
            result.gaps = json_data["gaps"]

        else:
            result = SensorDataPa("Empty")
            result.errors.append("Loading from json file failed; Sensor missing name.")
        return result
