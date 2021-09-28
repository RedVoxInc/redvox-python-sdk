"""
Modules for extracting time synchronization statistics for API 900 and 1000 data.
Currently uses API M packets due to versatility of the packet.
Also includes functions for correcting time arrays.
ALL timestamps in microseconds unless otherwise stated
"""

from functools import reduce
from typing import List, Optional, Union
import json
from pathlib import Path
import os

# noinspection Mypy
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.dataset as ds

import redvox.api900.lib.api900_pb2 as api900_pb2
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.api900.lib.api900_pb2 import RedvoxPacket
import redvox.api900.reader_utils as util_900
from redvox.common.offset_model import OffsetModel
from redvox.common import (
    tri_message_stats as tms,
)


class TimeSyncArrow:
    """
    Stores latencies, offsets, and other timesync related information about a single station
    ALL timestamps in microseconds unless otherwise stated
    Timestamps are never updated from the raw values provided from the data
    properties:
        time_sync_exchanges_list: list of lists, timestamps that form the time sync exchanges, default empty list

        latencies: np.ndarray, calculated latencies of the exchanges.  Must be two equal length arrays,
        default empty np.ndarray

        best_latency: float, best latency of the data, default np.nan

        mean_latency: float, mean latency, default np.nan

        latency_std: float, standard deviation of latencies, default np.nan

        offsets: np.ndarray, calculated offsets of the exchanges.  Must be two equal length arrays,
        default empty np.ndarray

        best_offset: float, best offset of the data, default 0.0

        mean_offset: float, mean offset, default np.nan

        offset_std: float, standard deviation of offsets, default np.nan

        data_start: float, start timestamp of the data, default np.nan

        data_end: float, end timestamp of the data, default np.nan

        best_exchange_latency_index: int, index in latencies/sync exchanges array that contains the best latency,
        default np.nan

        best_msg_timestamp_index: int, indicates which latency array has the best latency.
        Must be 1 or 3, other values are invalid.  Default 0

        offset_model: OffsetModel, used to correct timestamps.

        arrow_dir: str, directory to save arrow file in, default "." (current dir)

        arrow_file_name: str, base name of file to save data as, default "timesync"
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
        self.latencies: np.ndarray = latencies
        self.best_latency: float = best_latency
        self.mean_latency: float = mean_latency
        self.latency_std: float = latency_std
        self.offsets: np.ndarray = offsets
        self.best_offset: float = best_offset
        self.mean_offset: float = mean_offset
        self.offset_std: float = offset_std
        self.best_latency_index: int = best_latency_index
        self.best_msg_array_index: int = best_array_index
        self.data_start: float = data_start
        self.data_end: float = data_end
        self.arrow_dir: str = arrow_dir
        self.arrow_file_name: str = arrow_file_name

        if time_sync_exchanges_list is None or len(time_sync_exchanges_list) < 1:
            self.time_sync_exchanges_list = [[], [], [], [], [], []]
        else:
            self.time_sync_exchanges_list = np.transpose([
                time_sync_exchanges_list[i: i + 6]
                for i in range(0, len(time_sync_exchanges_list), 6)
            ])
            self._stats_from_exchanges()

    def as_dict(self):
        return {
            "best_latency_index": self.best_latency_index,
            "best_msg_array_index": self.best_msg_array_index,
            "best_latency": self.best_latency,
            "mean_latency": self.mean_latency,
            "latency_std": self.latency_std,
            "best_offset": self.best_offset,
            "mean_offset": self.mean_offset,
            "offset_std": self.offset_std,
            "data_start": self.data_start,
            "data_end": self.data_end,
            "arrow_dir": self.arrow_dir,
            "arrow_file_name": self.arrow_file_name
        }

    def to_json(self):
        return json.dumps(self.as_dict())

    def to_json_file(self, file_name: Optional[str] = None) -> Path:
        """
        saves the timesync data as json and data in the same directory.

        :param file_name: the optional base file name.  Do not include a file extension.
                            If None, a default file name is created using this format:
                            timesync.json
        :return: path to json file
        """
        _file_name: str = (
            file_name
            if file_name is not None
            else self.arrow_file_name
        )
        file_path: Path = Path(self.arrow_dir).joinpath(f"{_file_name}.json")
        pq.write_table(self.data_as_pyarrow(),
                       Path(self.arrow_dir).joinpath(f"{_file_name}.parquet"))
        with open(file_path, "w") as f_p:
            f_p.write(self.to_json())
            return file_path.resolve(False)

    @staticmethod
    def from_json(file_path: str) -> "TimeSyncArrow":
        """
        convert contents of json file to TimeSync data
        :param file_path: full path of file to load data from.
        :return: TimeSyncArrow object
        """
        with open(file_path, "r") as f_p:
            json_data = json.loads(f_p.read())
        data = ds.dataset(os.path.join(json_data["arrow_dir"], json_data["arrow_file_name"] + ".parquet"),
                          format="parquet", exclude_invalid_files=True).to_table()
        result = TimeSyncArrow(None, np.array((data["latencies1"], data["latencies3"])),
                               json_data["best_latency"], json_data["mean_latency"], json_data["latency_std"],
                               np.array((data["offsets1"], data["offsets3"])),
                               json_data["best_offset"], json_data["mean_offset"], json_data["offset_std"],
                               json_data["data_start"], json_data["data_end"], json_data["best_latency_index"],
                               json_data["best_msg_array_index"], json_data["arrow_dir"], json_data["arrow_file_name"])
        result.time_sync_exchanges_list = [data["a1"].to_numpy(), data["a2"].to_numpy(), data["a3"].to_numpy(),
                                           data["b1"].to_numpy(), data["b2"].to_numpy(), data["b3"].to_numpy()]
        return result

    @staticmethod
    def from_dict(ts_dict: dict, tse_data: List) -> "TimeSyncArrow":
        return TimeSyncArrow(tse_data, ts_dict["best_latency"], ts_dict["best_offset"])

    def data_as_pyarrow(self) -> pa.Table:
        return pa.Table.from_pydict({
            "a1": self.time_sync_exchanges_list[0],
            "a2": self.time_sync_exchanges_list[1],
            "a3": self.time_sync_exchanges_list[2],
            "b1": self.time_sync_exchanges_list[3],
            "b2": self.time_sync_exchanges_list[4],
            "b3": self.time_sync_exchanges_list[5],
            "latencies1": self.latencies[0],
            "latencies3": self.latencies[1],
            "offsets1": self.offsets[0],
            "offsets3": self.offsets[1]
        })

    def _stats_from_exchanges(self):
        """
        Compute the tri-message stats from the data
        """
        if self.num_tri_messages() < 1:
            self.latencies = np.array(([], []))
            self.offsets = np.array(([], []))
            self.best_latency = np.nan
            self.mean_latency = np.nan
            self.latency_std = np.nan
            self.best_offset = 0
            self.mean_offset = np.nan
            self.offset_std = np.nan
            self.best_latency_index = -1
            self.best_msg_array_index = 0
            self.offset_model = OffsetModel.empty_model()
        elif self.latencies is None:
            # compute tri message data from time sync exchanges
            tse = tms.TriMessageStats(
                "",
                np.array(self.time_sync_exchanges_list[0]),
                np.array(self.time_sync_exchanges_list[1]),
                np.array(self.time_sync_exchanges_list[2]),
                np.array(self.time_sync_exchanges_list[3]),
                np.array(self.time_sync_exchanges_list[4]),
                np.array(self.time_sync_exchanges_list[5]),
            )
            self.latencies = np.array((tse.latency1, tse.latency3))
            if self.offsets is None:
                self.offsets = np.array((tse.offset1, tse.offset3))
            # Compute the statistics for latency and offset
            if np.isnan(self.mean_latency):
                self.mean_latency = np.mean([*self.latencies[0], *self.latencies[1]])
            if np.isnan(self.latency_std):
                self.latency_std = np.std([*self.latencies[0], *self.latencies[1]])
            if np.isnan(self.mean_offset):
                self.mean_offset = np.mean([*self.offsets[0], *self.offsets[1]])
            if np.isnan(self.offset_std):
                self.offset_std = np.std([*self.offsets[0], *self.offsets[1]])
            self.best_latency_index = tse.best_latency_index
            self.best_msg_array_index = tse.best_latency_array_index
            # if best_latency is np.nan, set to best computed latency
            if np.isnan(self.best_latency):
                self.best_latency = tse.best_latency
                self.best_offset = tse.best_offset
            # if best_offset is still default value, use the best computed offset
            elif self.best_offset == 0:
                self.best_offset = tse.best_offset
            if not np.isnan(self.data_start) and not np.isnan(self.data_end):
                self.offset_model = OffsetModel(self.latencies.flatten(), self.offsets.flatten(),
                                                self.get_device_exchanges_timestamps(),
                                                self.data_start, self.data_end)

    def get_device_exchanges_timestamps(self) -> np.array:
        """
        :return: timestamps of sync exchanges initiated by the device
        """
        # make this return the actual thing?
        return np.concatenate((self.time_sync_exchanges_list[3].tolist(), self.time_sync_exchanges_list[5].tolist()))
        # self.time_sync_exchanges_list[3].tolist().extend(self.time_sync_exchanges_list[5].tolist())

    def num_tri_messages(self) -> int:
        """
        :return: number of tri-message exchanges
        """
        return np.size(self.time_sync_exchanges_list, 1)

    def get_best_latency_timestamp(self) -> float:
        """
        :return: timestamp of best latency, or start of the packet if no best latency.
        """
        if self.best_msg_array_index == 1:
            return self.time_sync_exchanges_list[3][self.best_latency_index]
        elif self.best_msg_array_index == 3:
            return self.time_sync_exchanges_list[5][self.best_latency_index]
        else:
            return np.nan

    def append_timesync_arrow(self, new_data: "TimeSyncArrow"):
        """
        adds timesync data from new_data to current
        :param new_data: another TimeSyncArrow object
        """
        self.time_sync_exchanges_list[0] = np.append(self.time_sync_exchanges_list[0],
                                                     new_data.time_sync_exchanges_list[0])
        self.time_sync_exchanges_list[1] = np.append(self.time_sync_exchanges_list[1],
                                                     new_data.time_sync_exchanges_list[1])
        self.time_sync_exchanges_list[2] = np.append(self.time_sync_exchanges_list[2],
                                                     new_data.time_sync_exchanges_list[2])
        self.time_sync_exchanges_list[3] = np.append(self.time_sync_exchanges_list[3],
                                                     new_data.time_sync_exchanges_list[3])
        self.time_sync_exchanges_list[4] = np.append(self.time_sync_exchanges_list[4],
                                                     new_data.time_sync_exchanges_list[4])
        self.time_sync_exchanges_list[5] = np.append(self.time_sync_exchanges_list[5],
                                                     new_data.time_sync_exchanges_list[5])
        if np.isnan(self.data_start):
            self.data_start = new_data.data_start
        elif not np.isnan(new_data.data_start):
            self.data_start = np.min([self.data_start, new_data.data_start])
        if np.isnan(self.data_end):
            self.data_end = new_data.data_end
        elif not np.isnan(new_data.data_end):
            self.data_end = np.max([self.data_end, new_data.data_end])
        tse = tms.TriMessageStats(
            "",
            np.array(self.time_sync_exchanges_list[0]),
            np.array(self.time_sync_exchanges_list[1]),
            np.array(self.time_sync_exchanges_list[2]),
            np.array(self.time_sync_exchanges_list[3]),
            np.array(self.time_sync_exchanges_list[4]),
            np.array(self.time_sync_exchanges_list[5]),
        )
        self.latencies = np.array((tse.latency1, tse.latency3))
        self.offsets = np.array((tse.offset1, tse.offset3))
        self.mean_latency = np.mean([*self.latencies[0], *self.latencies[1]])
        self.latency_std = np.std([*self.latencies[0], *self.latencies[1]])
        self.mean_offset = np.mean([*self.offsets[0], *self.offsets[1]])
        self.offset_std = np.std([*self.offsets[0], *self.offsets[1]])
        self.best_latency_index = tse.best_latency_index
        self.best_msg_array_index = tse.best_latency_array_index
        self.best_latency = tse.best_latency
        self.best_offset = tse.best_offset
        self.best_offset = tse.best_offset
        self.offset_model = OffsetModel(self.latencies.flatten(), self.offsets.flatten(),
                                        self.get_device_exchanges_timestamps(),
                                        self.data_start, self.data_end)

    def from_raw_packets(self, packets: List[Union[RedvoxPacketM, RedvoxPacket]]) -> 'TimeSyncArrow':
        """
        converts packets into TimeSyncData objects, then performs analysis

        :param packets: list of WrappedRedvoxPacketM to convert
        :return: modified version of self
        """
        all_exchanges: List[float] = []
        if isinstance(packets[0], RedvoxPacketM):
            self.data_start = packets[0].timing_information.packet_start_mach_timestamp
        else:
            self.data_start = packets[0].app_file_start_timestamp_machine
        if isinstance(packets[-1], RedvoxPacketM):
            self.data_end = packets[-1].timing_information.packet_end_mach_timestamp
        else:
            self.data_end = packets[-1].app_file_start_timestamp_machine

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
            self.time_sync_exchanges_list = np.transpose([
                all_exchanges[i: i + 6] for i in range(0, len(all_exchanges), 6)
            ])
            tse = tms.TriMessageStats(
                "",
                np.array(self.time_sync_exchanges_list[0]),
                np.array(self.time_sync_exchanges_list[1]),
                np.array(self.time_sync_exchanges_list[2]),
                np.array(self.time_sync_exchanges_list[3]),
                np.array(self.time_sync_exchanges_list[4]),
                np.array(self.time_sync_exchanges_list[5]),
            )
            self.latencies = np.array((tse.latency1, tse.latency3))
            self.offsets = np.array((tse.offset1, tse.offset3))
            # Compute the statistics for latency and offset
            self.mean_latency = np.mean([*self.latencies[0], *self.latencies[1]])
            self.latency_std = np.std([*self.latencies[0], *self.latencies[1]])
            self.mean_offset = np.mean([*self.offsets[0], *self.offsets[1]])
            self.offset_std = np.std([*self.offsets[0], *self.offsets[1]])
            self.best_latency_index = tse.best_latency_index
            self.best_msg_array_index = tse.best_latency_array_index
            self.best_latency = tse.best_latency
            self.best_offset = tse.best_offset
            self.offset_model = OffsetModel(self.latencies.flatten(), self.offsets.flatten(),
                                            self.get_device_exchanges_timestamps(),
                                            self.data_start, self.data_end)
        else:
            self.latencies = np.array(([], []))
            self.offsets = np.array(([], []))
            self.best_latency = np.nan
            self.mean_latency = np.nan
            self.latency_std = np.nan
            self.best_offset = 0
            self.mean_offset = np.nan
            self.offset_std = np.nan
            self.best_latency_index = -1
            self.best_msg_array_index = 0
            self.offset_model = OffsetModel.empty_model()
        return self
