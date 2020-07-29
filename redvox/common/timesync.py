"""
Modules for extracting time synchronization statistics for API 900 data.
Also includes functions for correcting time arrays.
ALL timestamps in microseconds unless otherwise stated
"""

# noinspection Mypy
import numpy as np
import pandas as pd

from typing import List, Optional, Tuple
from redvox.api900.reader_utils import empty_array
from redvox.common import stats_helper as sh, tri_message_stats as tms, date_time_utils as dt, file_statistics as fh
from redvox.common import sensor_data as sd


class TimeSyncData:
    """
    Stores latencies, offsets, and other timesync related information about a single station
    ALL timestamps in microseconds unless otherwise stated
    properties:
        station_id: str, id of station
        sample_rate_hz: float, sample rate of audio sensor in Hz
        mach_time_zero: int, timestamp of when the station was started
        mach_time_zero: int, timestamp of when app was started
        packet_start_time: int, timestamp of when data started recording
        packet_end_time: int, timestamp of when data stopped recording
        server_acquisition_times: int, timestamp of when packet arrived at server
        time_sync_exchanges_df: dataframe, timestamps that form the time synch exchanges
        latencies: np.ndarray, calculated latencies of the exchanges
        best_latency_index: int, index in latencies array that contains the best latency
        best_latency: float, best latency of the data
        mean_latency: float, mean latency
        latency_std: float, standard deviation of latencies
        offsets: np.ndarray, calculated offsets of the exchanges
        best_offset: int, best offset of the data
        mean_offset: float, mean offset
        offset_std: float, standard deviation of offsets
        best_tri_msg_index: int, index of the best tri-message
        acquire_travel_time: int, calculated time it took packet to reach server
    """

    def __init__(self, station: sd.Station = None):
        """
        Initialize properties
        :param station: station data
        """
        self.best_latency: Optional[float] = None
        if station is None:
            self.station_id: Optional[str] = None
            self.sample_rate_hz: Optional[float] = None
            self.station_start_timestamp: Optional[int] = None
            self.server_acquisition_time: Optional[int] = None
            self.packet_start_time: Optional[int] = None
            self.packet_end_time: Optional[int] = None
            self.packet_duration: int = 0
            self.time_sync_exchanges_df = pd.DataFrame([], columns=["a1", "a2", "a3", "b1", "b2", "b3"])
            self.best_tri_msg_index: Optional[int] = None
            self.latencies: np.ndarray = np.ndarray((0, 0))
            self.best_latency_index: Optional[int] = None
            self.mean_latency: Optional[float] = None
            self.latency_std: Optional[float] = None
            self.offsets: np.ndarray = np.ndarray((0, 0))
            self.best_offset: int = 0
            self.mean_offset: Optional[float] = 0.0
            self.offset_std: Optional[float] = 0.0
            self.acquire_travel_time: Optional[int] = None
            # self.num_packets: int = 0
            # self.bad_packets: List[int] = []
        else:
            self.get_time_sync_data(station)

    def get_time_sync_data(self, station: sd.Station):
        """
        extracts the time sync data from the station data object
        :param station: the station to get data from
        """
        self.station_id = station.sensor_metadata.station_id
        self.sample_rate_hz = station.sensor_data_dict[sd.SensorType.AUDIO].sample_rate
        self.station_start_timestamp = station.timing_data.station_start_timestamp
        self.server_acquisition_time = station.timing_data.server_timestamp
        self.packet_start_time = station.timing_data.app_start_timestamp
        self.packet_end_time = station.timing_data.app_end_timestamp
        self.time_sync_exchanges_df = pd.DataFrame(
            tms.transmit_receive_timestamps_microsec(station.timing_data.timesync),
            index=["a1", "a2", "a3", "b1", "b2", "b3"]).T
        # stations may contain the best latency and offset data already
        if station.timing_data.best_latency:
            self.best_latency = station.timing_data.best_latency
        if station.timing_data.best_offset:
            self.best_offset = station.timing_data.best_offset
        self._compute_tri_message_stats()
        # set the packet duration (this should also be equal to self.packet_end_time - self.packet_start_time)
        self.packet_duration = dt.seconds_to_microseconds(
            fh.get_duration_seconds_from_sample_rate(int(self.sample_rate_hz)))
        # calculate travel time between corrected end of packet timestamp and server timestamp
        self.acquire_travel_time = self.server_acquisition_time - (self.packet_end_time + self.best_offset)

    def _compute_tri_message_stats(self):
        """
        Compute the tri-message stats from the data
        """
        if self.num_tri_messages() > 0:
            # compute tri message data from time sync exchanges
            tse = tms.TriMessageStats(self.station_id,
                                      self.time_sync_exchanges_df["a1"], self.time_sync_exchanges_df["a2"],
                                      self.time_sync_exchanges_df["a3"],
                                      self.time_sync_exchanges_df["b1"], self.time_sync_exchanges_df["b2"],
                                      self.time_sync_exchanges_df["b3"])
            # Compute the statistics for latency and offset
            self.mean_latency = np.mean([*tse.latency1, *tse.latency3])
            self.latency_std = np.std([*tse.latency1, *tse.latency3])
            self.mean_offset = np.mean([*tse.offset1, *tse.offset3])
            self.offset_std = np.std([*tse.offset1, *tse.offset3])
            self.latencies = np.array((tse.latency1, tse.latency3))
            self.offsets = np.array((tse.offset1, tse.offset3))
            self.best_latency_index = tse.best_latency_index
            # if best_latency is None, set to best computed latency
            if self.best_latency is None:
                self.best_latency = tse.best_latency
                self.best_offset = tse.best_offset
            # if best_offset is still default value, use the best computed offset
            elif self.best_offset == 0:
                self.best_offset = tse.best_offset
        else:
            # If here, there are no exchanges to read.  writing default or empty values to the correct properties
            self.best_tri_msg_index = None
            self.best_latency_index = None
            self.best_latency = None
            self.mean_latency = None
            self.latency_std = None
            self.best_offset = 0
            self.mean_offset = 0
            self.offset_std = 0

    def num_tri_messages(self) -> int:
        return self.time_sync_exchanges_df.shape[0]


class TimeSyncAnalysis:
    """
    Used for multiple TimeSyncData objects from a station
    properties:
        station_id: the station id that all the timesync data belongs to
        timesync_data: the timesync data of the station
    """
    def __init__(self, station_id: str, timesync_list: Optional[List[TimeSyncData]] = None):
        self.station_id: str = station_id
        self.timesync_data: List[TimeSyncData] = timesync_list
        self.best_latency_index: int = 0
        self.evaluate_latencies()

    def add_timesync_data(self, timesync_data: TimeSyncData):
        self.timesync_data.append(timesync_data)

    def get_best_latency(self):
        return self.timesync_data[self.best_latency_index].best_latency

    def get_best_offset(self):
        return self.timesync_data[self.best_latency_index].best_offset

    def get_best_packet_latency_index(self):
        return self.timesync_data[self.best_latency_index].best_latency_index

    def evaluate_latencies(self):
        if len(self.timesync_data) < 1:
            raise ValueError("Nothing to evaluate; length of timesync data is less than 1")
        # assume the first element has the best timesync values for now, then compare with the others
        for index in range(1, len(self.timesync_data)):
            # find the best latency; in this case, the minimum
            if self.timesync_data[index].best_latency is not None \
                    and self.timesync_data[index].best_latency < self.get_best_latency():
                self.best_latency_index = index

    def evaluate_start_timestamp(self):
        """
        checks if station_start_timestamp differs in any of the timesync_data
        outputs warnings if a change in timestamps is detected
        """
        if len(self.timesync_data) < 1:
            raise ValueError("Nothing to evaluate; length of timesync data is less than 1")
        station_start_ts = self.timesync_data[0].station_start_timestamp
        for index in range(1, len(self.timesync_data)):
            # compare station start timestamps; notify when they are different
            if self.timesync_data[index].station_start_timestamp is not None \
                    and self.timesync_data[index].station_start_timestamp != station_start_ts:
                print(f"Warning!  Change in station start timestamp detected!  "
                      f"Expected: {station_start_ts}, read: {self.timesync_data[index].station_start_timestamp}")

    def evaluate_sample_rate(self):
        """
        checks if sample rate is the same across all timesync_data
        outputs warning if a change in sample rate is detected
        """
        if len(self.timesync_data) < 1:
            raise ValueError("Nothing to evaluate; length of timesync data is less than 1")
        sample_rate = self.timesync_data[0].sample_rate_hz
        for index in range(1, len(self.timesync_data)):
            # compare station start timestamps; notify when they are different
            if self.timesync_data[index].sample_rate_hz is not None \
                    and self.timesync_data[index].sample_rate_hz != sample_rate:
                print(f"Warning!  Change in station sample rate detected!  "
                      f"Expected: {sample_rate}, read: {self.timesync_data[index].sample_rate_hz}")
