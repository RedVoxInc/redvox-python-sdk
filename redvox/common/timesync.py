"""
Modules for extracting time synchronization statistics for API 900 and 1000 data.
Currently uses API M packets due to versatility of the packet.
Also includes functions for correcting time arrays.
ALL timestamps in microseconds unless otherwise stated
"""

from functools import reduce
from typing import List, Optional, Union
from pathlib import Path
import os

# noinspection Mypy
import numpy as np
import pyarrow as pa
import pyarrow.dataset as ds

import redvox.common.timesync_io as io
import redvox.api900.lib.api900_pb2 as api900_pb2
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.api900.lib.api900_pb2 import RedvoxPacket
import redvox.api900.reader_utils as util_900
from redvox.common.offset_model import OffsetModel
from redvox.common import (
    tri_message_stats as tms,
)


class TimeSync:
    """
    Stores latencies, offsets, and other timesync related information about a single station
    ALL timestamps in microseconds unless otherwise stated
    Timestamps are never updated from the raw values provided from the data

    Properties:
        _time_sync_exchanges_list: list of lists, timestamps that form the time sync exchanges, default empty list

        _latencies: np.ndarray, calculated latencies of the exchanges.  Must be two equal length arrays,
        default empty np.ndarray

        _best_latency: float, best latency of the data, default np.nan

        _mean_latency: float, mean latency, default np.nan

        _latency_std: float, standard deviation of latencies, default np.nan

        _offsets: np.ndarray, calculated offsets of the exchanges.  Must be two equal length arrays,
        default empty np.ndarray

        _best_offset: float, best offset of the data, default 0.0

        _mean_offset: float, mean offset, default np.nan

        _offset_std: float, standard deviation of offsets, default np.nan

        _data_start: float, start timestamp of the data, default np.nan

        _data_end: float, end timestamp of the data, default np.nan

        _best_latency_index: int, index in latencies/sync exchanges array that contains the best latency,
        default -1

        _best_msg_array_index: int, indicates which latency array has the best latency.
        Must be 1 or 3, other values are invalid.  Default 0

        _offset_model: OffsetModel, used to correct timestamps.

        _arrow_dir: str, directory to save arrow file in, default "." (current dir)

        _arrow_file: str, base name of file to save data as, default "timesync"
    """

    def __init__(
            self,
            time_sync_exchanges_list: Optional[List[float]] = None,
            latencies: Optional[np.ndarray] = None,
            best_latency: float = np.nan,
            mean_latency: float = np.nan,
            latency_std: float = np.nan,
            offsets: Optional[np.ndarray] = None,
            best_offset: float = 0.0,
            mean_offset: float = np.nan,
            offset_std: float = np.nan,
            data_start: float = np.nan,
            data_end: float = np.nan,
            best_latency_index: Optional[int] = None,
            best_array_index: int = 0,
            arrow_dir: str = ".",
            arrow_file_name: str = "timesync"
    ):
        """
        Initialize properties

        :param time_sync_exchanges_list: optional timesync exchanges of the packet as a flat list, default None
        :param latencies: optional arrays of latencies from exchanges; must be two equal length arrays, default None
        :param best_latency: the best latency of set, default np.nan
        :param mean_latency: the mean of all latencies, default np.nan
        :param latency_std: the standard deviation of all latencies, default np.nan
        :param offsets: optional arrays of offsets from exchanges; must be two equal length arrays, default None
        :param best_offset: the best offset of the packet, default 0.0
        :param mean_offset: the mean of all offsets, default np.nan
        :param offset_std: the standard deviation of all offsets, default np.nan
        :param data_start: the start timestamp of the data, default np.nan
        :param data_end: the end timestamp of the data, default np.nan
        :param best_latency_index: optional index of best latency in latencies array, default None
        :param best_array_index: index of best latency array; must be either 1 (first array) or 3 (second array),
                                    any other value is invalid, default 0
        :param arrow_dir: directory to save timesync data in, default "."
        :param arrow_file_name: name of file to save timesync data as.  do not include extensions.  default "timesync"
        """
        self._latencies: np.ndarray = latencies
        self._best_latency: float = best_latency
        self._mean_latency: float = mean_latency
        self._latency_std: float = latency_std
        self._offsets: np.ndarray = offsets
        self._best_offset: float = best_offset
        self._mean_offset: float = mean_offset
        self._offset_std: float = offset_std
        self._best_latency_index: int = best_latency_index
        self._best_msg_array_index: int = best_array_index
        self._data_start: float = data_start
        self._data_end: float = data_end
        self.arrow_dir: str = arrow_dir
        self.arrow_file: str = arrow_file_name

        if time_sync_exchanges_list is None or len(time_sync_exchanges_list) < 1:
            self._time_sync_exchanges_list = [[], [], [], [], [], []]
            self._best_exchange_index_list = []
            self._offset_model: OffsetModel = OffsetModel.empty_model()
        else:
            self._time_sync_exchanges_list = np.transpose([
                time_sync_exchanges_list[i: i + 6]
                for i in range(0, len(time_sync_exchanges_list), 6)
            ])
            self._stats_from_exchanges()

    def __repr__(self):
        return f"best_latency_index: {self._best_latency_index}, " \
               f"best_latency: {self._best_latency}, " \
               f"mean_latency: {self._mean_latency}, " \
               f"latency_std: {self._latency_std}, " \
               f"best_offset: {self._best_offset}, " \
               f"mean_offset: {self._mean_offset}, " \
               f"offset_std: {self._offset_std}"

    def __str__(self):
        return f"best_latency_index: {self._best_latency_index}, " \
               f"best_latency: {self._best_latency}, " \
               f"mean_latency: {self._mean_latency}, " \
               f"latency_std: {self._latency_std}, " \
               f"best_offset: {self._best_offset}, " \
               f"mean_offset: {self._mean_offset}, " \
               f"offset_std: {self._offset_std}"

    def as_dict(self) -> dict:
        """
        :return: TimeSync as a dictionary
        """
        return {
            "best_latency_index": self._best_latency_index,
            "best_msg_array_index": self._best_msg_array_index,
            "best_latency": self._best_latency,
            "mean_latency": self._mean_latency,
            "latency_std": self._latency_std,
            "best_offset": self._best_offset,
            "mean_offset": self._mean_offset,
            "offset_std": self._offset_std,
            "data_start": self._data_start,
            "data_end": self._data_end,
            "arrow_dir": self.arrow_dir,
            "arrow_file_name": self.arrow_file
        }

    def to_json(self):
        """
        :return: TimeSync as json string
        """
        return io.to_json(self)

    def to_json_file(self, file_name: Optional[str] = None) -> Path:
        """
        saves the timesync data as json and data in the same directory.

        :param file_name: the optional base file name.  Do not include a file extension.
                            If None, a default file name is created using this format:
                            timesync.json
        :return: path to json file
        """
        return io.to_json_file(self, file_name)

    @staticmethod
    def from_json_file(file_path: str) -> "TimeSync":
        """
        convert contents of json file to TimeSync data

        :param file_path: full path of file to load data from.
        :return: TimeSyncArrow object
        """
        json_data = io.json_file_to_dict(file_path)
        data = ds.dataset(os.path.join(json_data["arrow_dir"], json_data["arrow_file_name"] + ".parquet"),
                          format="parquet", exclude_invalid_files=True).to_table()
        result = TimeSync(None, np.array((data["latencies1"], data["latencies3"])),
                          json_data["best_latency"], json_data["mean_latency"], json_data["latency_std"],
                          np.array((data["offsets1"], data["offsets3"])),
                          json_data["best_offset"], json_data["mean_offset"], json_data["offset_std"],
                          json_data["data_start"], json_data["data_end"], json_data["best_latency_index"],
                          json_data["best_msg_array_index"], json_data["arrow_dir"], json_data["arrow_file_name"])
        result.set_sync_exchanges([data["a1"].to_numpy(), data["a2"].to_numpy(), data["a3"].to_numpy(),
                                   data["b1"].to_numpy(), data["b2"].to_numpy(), data["b3"].to_numpy()])
        return result

    @staticmethod
    def from_dict(ts_dict: dict, tse_data: List) -> "TimeSync":
        """
        create TimeSync frp, dictionary

        :param ts_dict: dictionary of metadata
        :param tse_data: list of time sync exchanges
        :return: TimeSync object
        """
        return TimeSync(tse_data, ts_dict["best_latency"], ts_dict["best_offset"])

    def data_as_pyarrow(self) -> pa.Table:
        """
        :return: convert timesync exchanges, latencies, and offsets into a pyarrow table
        """
        return pa.Table.from_pydict({
            "a1": self._time_sync_exchanges_list[0],
            "a2": self._time_sync_exchanges_list[1],
            "a3": self._time_sync_exchanges_list[2],
            "b1": self._time_sync_exchanges_list[3],
            "b2": self._time_sync_exchanges_list[4],
            "b3": self._time_sync_exchanges_list[5],
            "latencies1": self._latencies[0],
            "latencies3": self._latencies[1],
            "offsets1": self._offsets[0],
            "offsets3": self._offsets[1]
        })

    def _stats_from_exchanges(self):
        """
        Compute the tri-message stats from the data
        """
        if self.num_tri_messages() < 1:
            self._latencies = np.array(([], []))
            self._offsets = np.array(([], []))
            self._best_latency = np.nan
            self._mean_latency = np.nan
            self._latency_std = np.nan
            self._best_offset = 0
            self._mean_offset = np.nan
            self._offset_std = np.nan
            self._best_latency_index = -1
            self._best_msg_array_index = 0
            self._offset_model = OffsetModel.empty_model()
            self._best_exchange_index_list = []
        elif self._latencies is None:
            # compute tri message data from time sync exchanges
            tse = tms.TriMessageStats(
                "",
                np.array(self._time_sync_exchanges_list[0]),
                np.array(self._time_sync_exchanges_list[1]),
                np.array(self._time_sync_exchanges_list[2]),
                np.array(self._time_sync_exchanges_list[3]),
                np.array(self._time_sync_exchanges_list[4]),
                np.array(self._time_sync_exchanges_list[5]),
            )
            self._latencies = np.array((tse.latency1, tse.latency3))
            if self._offsets is None:
                self._offsets = np.array((tse.offset1, tse.offset3))
            # Compute the statistics for latency and offset
            if np.isnan(self._mean_latency):
                self._mean_latency = np.mean([*self._latencies[0], *self._latencies[1]])
            if np.isnan(self._latency_std):
                self._latency_std = np.std([*self._latencies[0], *self._latencies[1]])
            if np.isnan(self._mean_offset):
                self._mean_offset = np.mean([*self._offsets[0], *self._offsets[1]])
            if np.isnan(self._offset_std):
                self._offset_std = np.std([*self._offsets[0], *self._offsets[1]])
            self._best_exchange_index_list = tse.best_latency_per_exchange_index_array
            self._best_latency_index = tse.best_latency_index
            self._best_msg_array_index = tse.best_latency_array_index
            # if best_latency is np.nan, set to best computed latency
            if np.isnan(self._best_latency):
                self._best_latency = tse.best_latency
                self._best_offset = tse.best_offset
            # if best_offset is still default value, use the best computed offset
            elif self._best_offset == 0:
                self._best_offset = tse.best_offset
            if not np.isnan(self._data_start) and not np.isnan(self._data_end):
                self._offset_model = OffsetModel(self._latencies.flatten(), self._offsets.flatten(),
                                                 self.get_device_exchanges_timestamps(),
                                                 self._data_start, self._data_end)

    def get_exchange_timestamps(self, index: int) -> np.array:
        """
        :param index: index of timestamps to return.  0, 1, 2 are server timestamps.  3, 4, 5 are device
                        any value not from 0 to 5 will be converted to 0
        :return: timestamps from the chosen index.
        """
        if index < 0 or index > 5:
            index = 0
        return self._time_sync_exchanges_list[index]

    def get_device_exchanges_timestamps(self) -> np.array:
        """
        :return: timestamps of sync exchanges initiated by the device
        """
        return np.concatenate((self._time_sync_exchanges_list[3].tolist(), self._time_sync_exchanges_list[5].tolist()))

    def num_tri_messages(self) -> int:
        """
        :return: number of tri-message exchanges
        """
        return np.size(self._time_sync_exchanges_list, 1)

    def get_best_latency_timestamp(self) -> float:
        """
        :return: timestamp of best latency, or np.nan if no best latency.
        """
        if self._best_msg_array_index == 1:
            return self._time_sync_exchanges_list[3][self._best_latency_index]
        elif self._best_msg_array_index == 3:
            return self._time_sync_exchanges_list[5][self._best_latency_index]
        else:
            return np.nan

    def append_timesync_arrow(self, new_data: "TimeSync"):
        """
        adds timesync data from new_data to current

        :param new_data: another TimeSyncArrow object
        """
        self._time_sync_exchanges_list[0] = np.append(self._time_sync_exchanges_list[0],
                                                      new_data._time_sync_exchanges_list[0])
        self._time_sync_exchanges_list[1] = np.append(self._time_sync_exchanges_list[1],
                                                      new_data._time_sync_exchanges_list[1])
        self._time_sync_exchanges_list[2] = np.append(self._time_sync_exchanges_list[2],
                                                      new_data._time_sync_exchanges_list[2])
        self._time_sync_exchanges_list[3] = np.append(self._time_sync_exchanges_list[3],
                                                      new_data._time_sync_exchanges_list[3])
        self._time_sync_exchanges_list[4] = np.append(self._time_sync_exchanges_list[4],
                                                      new_data._time_sync_exchanges_list[4])
        self._time_sync_exchanges_list[5] = np.append(self._time_sync_exchanges_list[5],
                                                      new_data._time_sync_exchanges_list[5])
        if np.isnan(self._data_start):
            self._data_start = new_data._data_start
        elif not np.isnan(new_data._data_start):
            self._data_start = np.min([self._data_start, new_data._data_start])
        if np.isnan(self._data_end):
            self._data_end = new_data._data_end
        elif not np.isnan(new_data._data_end):
            self._data_end = np.max([self._data_end, new_data._data_end])
        if len(self._time_sync_exchanges_list[0]) > 0:
            tse = tms.TriMessageStats(
                "",
                np.array(self._time_sync_exchanges_list[0]),
                np.array(self._time_sync_exchanges_list[1]),
                np.array(self._time_sync_exchanges_list[2]),
                np.array(self._time_sync_exchanges_list[3]),
                np.array(self._time_sync_exchanges_list[4]),
                np.array(self._time_sync_exchanges_list[5]),
            )
            self._latencies = np.array((tse.latency1, tse.latency3))
            self._offsets = np.array((tse.offset1, tse.offset3))
            self._mean_latency = np.mean([*self._latencies[0], *self._latencies[1]])
            self._latency_std = np.std([*self._latencies[0], *self._latencies[1]])
            self._mean_offset = np.mean([*self._offsets[0], *self._offsets[1]])
            self._offset_std = np.std([*self._offsets[0], *self._offsets[1]])
            self._best_latency_index = tse.best_latency_index
            self._best_msg_array_index = tse.best_latency_array_index
            self._best_latency = tse.best_latency
            self._best_offset = tse.best_offset
            self._best_exchange_index_list = tse.best_latency_per_exchange_index_array
            self._offset_model = OffsetModel(self._latencies.flatten(), self._offsets.flatten(),
                                             self.get_device_exchanges_timestamps(),
                                             self._data_start, self._data_end)

    def from_raw_packets(self, packets: List[Union[RedvoxPacketM, RedvoxPacket]]) -> 'TimeSync':
        """
        converts packets into TimeSyncData objects, then performs analysis

        :param packets: list of RedvoxPacketM and RedvoxPacket to convert
        :return: modified version of self
        """
        all_exchanges: List[float] = []
        if isinstance(packets[0], RedvoxPacketM):
            self._data_start = packets[0].timing_information.packet_start_mach_timestamp
        else:
            self._data_start = packets[0].app_file_start_timestamp_machine
        if isinstance(packets[-1], RedvoxPacketM):
            self._data_end = packets[-1].timing_information.packet_end_mach_timestamp
        else:
            self._data_end = packets[-1].app_file_start_timestamp_machine

        packet: Union[RedvoxPacketM, RedvoxPacket]
        for packet in packets:
            if isinstance(packet, RedvoxPacketM):
                all_exchanges.extend(reduce(lambda acc, ex: acc + [ex.a1, ex.a2, ex.a3, ex.b1, ex.b2, ex.b3],
                                            packet.timing_information.synch_exchanges,
                                            []))
            else:
                # Get synch exchanges
                ch: api900_pb2.UnevenlySampledChannel
                for ch in packet.unevenly_sampled_channels:
                    if api900_pb2.TIME_SYNCHRONIZATION in ch.channel_types:
                        all_exchanges.extend(util_900.extract_payload(ch))

        if len(all_exchanges) > 0:
            self._time_sync_exchanges_list = np.transpose([
                all_exchanges[i: i + 6] for i in range(0, len(all_exchanges), 6)
            ])
            tse = tms.TriMessageStats(
                "",
                np.array(self._time_sync_exchanges_list[0]),
                np.array(self._time_sync_exchanges_list[1]),
                np.array(self._time_sync_exchanges_list[2]),
                np.array(self._time_sync_exchanges_list[3]),
                np.array(self._time_sync_exchanges_list[4]),
                np.array(self._time_sync_exchanges_list[5]),
            )
            self._latencies = np.array((tse.latency1, tse.latency3))
            self._offsets = np.array((tse.offset1, tse.offset3))
            # Compute the statistics for latency and offset
            self._mean_latency = np.mean([*self._latencies[0], *self._latencies[1]])
            self._latency_std = np.std([*self._latencies[0], *self._latencies[1]])
            self._mean_offset = np.mean([*self._offsets[0], *self._offsets[1]])
            self._offset_std = np.std([*self._offsets[0], *self._offsets[1]])
            self._best_latency_index = tse.best_latency_index
            self._best_msg_array_index = tse.best_latency_array_index
            self._best_latency = tse.best_latency
            self._best_offset = tse.best_offset
            self._best_exchange_index_list = tse.best_latency_per_exchange_index_array
            self._offset_model = OffsetModel(self._latencies.flatten(), self._offsets.flatten(),
                                             self.get_device_exchanges_timestamps(),
                                             self._data_start, self._data_end)
        else:
            self._latencies = np.array(([], []))
            self._offsets = np.array(([], []))
            self._best_latency = np.nan
            self._mean_latency = np.nan
            self._latency_std = np.nan
            self._best_offset = 0
            self._mean_offset = np.nan
            self._offset_std = np.nan
            self._best_latency_index = -1
            self._best_msg_array_index = 0
            self._best_exchange_index_list = []
            self._offset_model = OffsetModel.empty_model()
        return self

    def sync_exchanges(self) -> np.ndarray:
        """
        :return: time sync exchanges
        """
        return self._time_sync_exchanges_list

    def set_sync_exchanges(self, exchanges: List[np.array]):
        """
        Set the sync exchanges to be the list of exchanges.
        The list of exchanges must have 6 np.arrays, each equal length, and the lists must be in the order of:
        Server1, Server2, Server3, Device1, Device2, Device3

        :param exchanges: 6 lists of equal length of timestamps
        """
        self._time_sync_exchanges_list = exchanges

    def latencies(self) -> np.ndarray:
        """
        :return: latencies as two np.arrays
        """
        return self._latencies

    def best_latency(self) -> float:
        """
        :return: best latency of data
        """
        return self._best_latency

    def mean_latency(self) -> float:
        """
        :return: mean latency of data
        """
        return self._mean_latency

    def latency_std(self) -> float:
        """
        :return: standard deviation of latency
        """
        return self._latency_std

    def best_latency_index(self) -> float:
        """
        :return: index/position of best latency
        """
        return self._best_latency_index

    def best_latency_per_exchange(self) -> np.array:
        """
        :return: the best latency per sync exchange as a numpy array
        """
        return np.array([self._latencies[self._best_exchange_index_list[n]][n] for n in range(self.num_tri_messages())])

    def offsets(self) -> np.ndarray:
        """
        :return: offsets as two np.arrays
        """
        return self._offsets

    def best_offset(self) -> float:
        """
        :return: best offset of data
        """
        return self._best_offset

    def mean_offset(self) -> float:
        """
        :return: mean offset of data
        """
        return self._mean_offset

    def offset_std(self) -> float:
        """
        :return: standard deviation of offset
        """
        return self._offset_std

    def best_offset_per_exchange(self) -> np.array:
        """
        :return: the best offset per sync exchange as a numpy array
        """
        return np.array([self._offsets[self._best_exchange_index_list[n]][n] for n in range(self.num_tri_messages())])

    def offset_model(self) -> OffsetModel:
        """
        :return: OffsetModel of the TimeSync
        """
        return self._offset_model

    def data_start_timestamp(self) -> float:
        """
        :return: timestamp of first data point
        """
        return self._data_start

    def data_end_timestamp(self) -> float:
        """
        :return: timestamp of last data point
        """
        return self._data_end
