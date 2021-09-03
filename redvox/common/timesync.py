"""
Modules for extracting time synchronization statistics for API 900 and 1000 data.
Currently uses API M packets due to versatility of the packet.
Also includes functions for correcting time arrays.
ALL timestamps in microseconds unless otherwise stated
"""

from functools import reduce
from typing import List, Optional, Union

# noinspection Mypy
import numpy as np

import redvox.api900.lib.api900_pb2 as api900_pb2
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.api900.lib.api900_pb2 import RedvoxPacket
from redvox.common.offset_model import OffsetModel
import redvox.api900.reader_utils as util_900
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api900.wrapped_redvox_packet import WrappedRedvoxPacket
from redvox.common.errors import RedVoxExceptions
from redvox.common import (
    stats_helper as sh,
    tri_message_stats as tms,
    date_time_utils as dt,
)


class TimeSyncData:
    """
    Stores latencies, offsets, and other timesync related information about a single station
    ALL timestamps in microseconds unless otherwise stated
    properties:
        station_id: str, id of station, default empty string
        station_start_timestamp: float, timestamp of when the station was started, default np.nan
        sample_rate_hz: float, sample rate of audio sensor in Hz, default np.nan
        packet_start_timestamp: float, timestamp of when data started recording, default np.nan
        packet_end_timestamp: float, timestamp of when data stopped recording, default np.nan
        packet_duration: float, length of packet in microseconds, default 0.0
        server_acquisition_timestamp: float, timestamp of when packet arrived at server, default np.nan
        time_sync_exchanges_df: dataframe, timestamps that form the time synch exchanges, default empty dataframe
        latencies: np.ndarray, calculated latencies of the exchanges, default empty np.ndarray
        best_latency_index: int, index in latencies array that contains the best latency, default np.nan
        best_latency: float, best latency of the data, default np.nan
        mean_latency: float, mean latency, default np.nan
        latency_std: float, standard deviation of latencies, default np.nan
        offsets: np.ndarray, calculated offsets of the exchanges, default np.ndarray
        best_offset: float, best offset of the data, default np.nan
        mean_offset: float, mean offset, default np.nan
        offset_std: float, standard deviation of offsets, default np.nan
        best_tri_msg_index: int, index of the best tri-message (same as best_latency_index), default np.nan
        best_msg_timestamp_index: int = np.nan, 1 or 3, indicates which tri-message latency array has the best latency
        acquire_travel_time: float, calculated time it took packet to reach server, default np.nan
    """

    def __init__(
            self,
            station_id: str = "",
            sample_rate_hz: float = np.nan,
            num_audio_samples: int = np.nan,
            station_start_timestamp: float = np.nan,
            server_acquisition_timestamp: float = np.nan,
            packet_start_timestamp: float = np.nan,
            packet_end_timestamp: float = np.nan,
            time_sync_exchanges_list: Optional[List[float]] = None,
            best_latency: float = np.nan,
            best_offset: float = 0.0,
    ):
        """
        Initialize properties
        :param station_id: id of station, default empty string
        :param sample_rate_hz: sample rate in hz of the station's audio channel, default np.nan
        :param num_audio_samples: number of audio samples in the data, default np.nan
        :param station_start_timestamp: timestamp of when the station started recording, default np.nan
        :param server_acquisition_timestamp: timestamp of when the data was received at the acquisition server,
                                                default np.nan
        :param packet_start_timestamp: timestamp of the start of the data packet, default np.nan
        :param packet_end_timestamp: timestamp of the end of the data packet, default np.nan
        :param time_sync_exchanges_list: the timesync exchanges of the packet as a flat list, default None
        :param best_latency: the best latency of the packet, default np.nan
        :param best_offset: the best offset of the packet, default 0.0
        """
        self.station_id = station_id
        self.sample_rate_hz = sample_rate_hz
        self.num_audio_samples = num_audio_samples
        self.station_start_timestamp = station_start_timestamp
        self.server_acquisition_timestamp = server_acquisition_timestamp
        self.packet_start_timestamp = packet_start_timestamp
        self.packet_end_timestamp = packet_end_timestamp
        if time_sync_exchanges_list is None:
            time_sync_exchanges_list = []
        else:
            time_sync_exchanges_list = [
                time_sync_exchanges_list[i: i + 6]
                for i in range(0, len(time_sync_exchanges_list), 6)
            ]
        self.time_sync_exchanges_list = np.transpose(time_sync_exchanges_list)
        self.best_latency = best_latency
        self.best_offset = best_offset

        self._compute_tri_message_stats()
        # set the packet duration
        self.packet_duration = self.packet_end_timestamp - self.packet_start_timestamp
        # calculate travel time between corrected end of packet timestamp and server timestamp
        self.acquire_travel_time = self.server_acquisition_timestamp - (
                self.packet_end_timestamp + self.best_offset
        )

    def _compute_tri_message_stats(self):
        """
        Compute the tri-message stats from the data
        """
        if self.num_tri_messages() > 0:
            # compute tri message data from time sync exchanges
            tse = tms.TriMessageStats(
                self.station_id,
                np.array(self.time_sync_exchanges_list[0]),
                np.array(self.time_sync_exchanges_list[1]),
                np.array(self.time_sync_exchanges_list[2]),
                np.array(self.time_sync_exchanges_list[3]),
                np.array(self.time_sync_exchanges_list[4]),
                np.array(self.time_sync_exchanges_list[5]),
            )
            # Compute the statistics for latency and offset
            self.mean_latency = np.mean([*tse.latency1, *tse.latency3])
            self.latency_std = np.std([*tse.latency1, *tse.latency3])
            self.mean_offset = np.mean([*tse.offset1, *tse.offset3])
            self.offset_std = np.std([*tse.offset1, *tse.offset3])
            self.latencies = np.array((tse.latency1, tse.latency3))
            self.offsets = np.array((tse.offset1, tse.offset3))
            self.best_latency_index = tse.best_latency_index
            self.best_tri_msg_index = tse.best_latency_index
            self.best_msg_timestamp_index = tse.best_latency_array_index
            # if best_latency is np.nan, set to best computed latency
            if np.isnan(self.best_latency):
                self.best_latency = tse.best_latency
                self.best_offset = tse.best_offset
            # if best_offset is still default value, use the best computed offset
            elif self.best_offset == 0:
                self.best_offset = tse.best_offset
        else:
            # If here, there are no exchanges to read.  write default or empty values to the correct properties
            self.latencies = np.array(([], []))
            self.offsets = np.array(([], []))
            self.best_tri_msg_index = np.nan
            self.best_latency_index = np.nan
            self.best_latency = np.nan
            self.mean_latency = np.nan
            self.latency_std = np.nan
            self.best_offset = 0
            self.mean_offset = 0
            self.offset_std = 0
            self.best_msg_timestamp_index = np.nan

    def num_tri_messages(self) -> int:
        """
        return the number of tri-message exchanges

        :return: number of tri-message exchanges
        """
        return np.size(self.time_sync_exchanges_list, 0)

    def update_timestamps(self, om: Optional[OffsetModel]):
        """
        update timestamps by adding microseconds based on the OffsetModel.
        if model not supplied, uses the best offset.
        uses negative values to go backwards in time

        :param om: OffsetModel to calculate offsets, default None
        """
        if not om:
            delta = self.best_offset
            self.station_start_timestamp += delta
            self.packet_start_timestamp += delta
            self.packet_end_timestamp += delta
        else:
            self.station_start_timestamp = om.update_time(self.station_start_timestamp)
            self.packet_start_timestamp = om.update_time(self.packet_start_timestamp)
            self.packet_end_timestamp = om.update_time(self.packet_end_timestamp)

    def get_best_latency_timestamp(self) -> float:
        """
        :return: timestamp of best latency, or start of the packet if no best latency.
        """
        if self.best_msg_timestamp_index == 1:
            return self.time_sync_exchanges_list[3][self.best_latency_index]
        elif self.best_msg_timestamp_index == 3:
            return self.time_sync_exchanges_list[5][self.best_latency_index]
        else:
            return self.packet_start_timestamp


def time_sync_data_from_raw_packet(packet: Union[RedvoxPacketM, RedvoxPacket]) -> TimeSyncData:
    """
    :param packet: data packet to get time sync data from
    :return: TimeSyncData object from data packet
    """
    tsd: TimeSyncData
    if isinstance(packet, RedvoxPacketM):
        exchanges: List[float] = reduce(lambda acc, ex: acc + [ex.a1, ex.a2, ex.a3, ex.b1, ex.b2, ex.b3],
                                        packet.timing_information.synch_exchanges,
                                        [])
        tsd = TimeSyncData(
            packet.station_information.id,
            packet.sensors.audio.sample_rate,
            len(packet.sensors.audio.samples.values),
            packet.timing_information.app_start_mach_timestamp,
            packet.timing_information.server_acquisition_arrival_timestamp,
            packet.timing_information.packet_start_mach_timestamp,
            packet.timing_information.packet_end_mach_timestamp,
            exchanges,
            packet.timing_information.best_latency,
            packet.timing_information.best_offset
        )
    else:
        mtz: float = np.nan
        best_latency: float = np.nan
        best_offset: float = np.nan

        for i, v in enumerate(packet.metadata):
            plus_1: int = i + 1
            try:
                if v == "machTimeZero" and plus_1 < len(packet.metadata):
                    mtz = float(packet.metadata[plus_1])
                if v == "bestLatency" and plus_1 < len(packet.metadata):
                    best_latency = float(packet.metadata[plus_1])
                if v == "bestOffset" and plus_1 < len(packet.metadata):
                    best_offset = float(packet.metadata[plus_1])
            except (KeyError, ValueError):
                continue

        # Get synch exchanges
        exchanges: Optional[np.ndarray] = None
        ch: api900_pb2.UnevenlySampledChannel
        for ch in packet.unevenly_sampled_channels:
            if api900_pb2.TIME_SYNCHRONIZATION in ch.channel_types:
                exchanges = util_900.extract_payload(ch)

        tsd = TimeSyncData(
            packet.redvox_id,
            packet.evenly_sampled_channels[0].sample_rate_hz,
            util_900.payload_len(packet.evenly_sampled_channels[0]),
            mtz,
            packet.evenly_sampled_channels[0].first_sample_timestamp_epoch_microseconds_utc,
            packet.server_timestamp_epoch_microseconds_utc,
            packet.app_file_start_timestamp_machine,
            list(exchanges),
            best_latency,
            best_offset,
        )

    return tsd


class TimeSyncAnalysis:
    """
    Used for multiple TimeSyncData objects from a station
    properties:
        station_id: string, the station_id of the station being analyzed, default empty string
        best_latency_index: int, the index of the TimeSyncData object with the best latency, default np.nan
        latency_stats: StatsContainer, the statistics of the latencies
        offset_stats: StatsContainer, the statistics of the offsets
        offset_model: optional OffsetModel, used to calculate offset at a given point in time
        sample_rate_hz: float, the audio sample rate in hz of the station, default np.nan
        timesync_data: list of TimeSyncData, the TimeSyncData to analyze, default empty list
        station_start_timestamp: float, the timestamp of when the station became active, default np.nan
    """

    def __init__(
            self,
            station_id: str = "",
            audio_sample_rate_hz: float = np.nan,
            station_start_timestamp: float = np.nan,
            time_sync_data: Optional[List[TimeSyncData]] = None,
    ):
        """
        Initialize the object

        :param station_id: id of the station to analyze, default empty string
        :param audio_sample_rate_hz: audio sample rate in hz of the station, default np.nan
        :param station_start_timestamp: timestamp of when station started recording, default np.nan
        :param time_sync_data: the TimeSyncData objects created from the packets of the station, default None
        """
        self.station_id: str = station_id
        self.sample_rate_hz: float = audio_sample_rate_hz
        self.station_start_timestamp: float = station_start_timestamp
        self.best_latency_index: int = np.nan
        self.latency_stats = sh.StatsContainer("latency")
        self.offset_stats = sh.StatsContainer("offset")
        self.errors = RedVoxExceptions("TimeSyncAnalysis")
        if time_sync_data:
            self.timesync_data: List[TimeSyncData] = time_sync_data
            self.evaluate_and_validate_data()
        else:
            self.timesync_data = []
            self.offset_model = OffsetModel.empty_model()

    def evaluate_and_validate_data(self):
        """
        check the data for errors and update the analysis statistics
        """
        self.evaluate_latencies()
        self.validate_start_timestamp()
        self.validate_sample_rate()
        self._calc_timesync_stats()
        self.offset_model = self.get_offset_model()

    def get_offset_model(self) -> OffsetModel:
        """
        :return: an OffsetModel based on the information in the timesync analysis
        """
        return OffsetModel(self.get_latencies(), self.get_offsets(),
                           np.array([td.get_best_latency_timestamp() for td in self.timesync_data]),
                           self.timesync_data[0].packet_start_timestamp,
                           self.timesync_data[-1].packet_end_timestamp)

    def _calc_timesync_stats(self):
        """
        calculates the mean and std deviation for latencies and offsets
        """
        if len(self.timesync_data) < 1:
            self.errors.append(
                "Nothing to calculate stats; length of timesync data is less than 1"
            )
        else:
            for index in range(len(self.timesync_data)):
                # add the stats of the latency
                self.latency_stats.add(
                    self.timesync_data[index].mean_latency,
                    self.timesync_data[index].latency_std,
                    self.timesync_data[index].num_tri_messages() * 2,
                    )
                # add the stats of the offset
                self.offset_stats.add(
                    self.timesync_data[index].mean_offset,
                    self.timesync_data[index].offset_std,
                    self.timesync_data[index].num_tri_messages() * 2,
                    )
            self.latency_stats.best_value = self.get_best_latency()
            self.offset_stats.best_value = self.get_best_offset()

    def from_packets(self, packets: List[Union[WrappedRedvoxPacketM, WrappedRedvoxPacket]]) -> 'TimeSyncAnalysis':
        """
        converts packets into TimeSyncData objects, then performs analysis

        :param packets: list of WrappedRedvoxPacketM to convert
        :return: modified version of self
        """
        self.timesync_data = [TimeSyncData(self.station_id,
                                           self.sample_rate_hz,
                                           packet.get_sensors().get_audio().get_num_samples(),
                                           self.station_start_timestamp,
                                           packet.get_timing_information().get_server_acquisition_arrival_timestamp(),
                                           packet.get_timing_information().get_packet_start_mach_timestamp(),
                                           packet.get_timing_information().get_packet_end_mach_timestamp(),
                                           packet.get_timing_information().get_synch_exchange_array(),
                                           packet.get_timing_information().get_best_latency(),
                                           packet.get_timing_information().get_best_offset(),
                                           )
                              if isinstance(packet, WrappedRedvoxPacketM) else
                              TimeSyncData(self.station_id,
                                           self.sample_rate_hz,
                                           packet.microphone_sensor().payload_values().size,
                                           self.station_start_timestamp,
                                           packet.server_timestamp_epoch_microseconds_utc(),
                                           packet.start_timestamp_us_utc(),
                                           packet.end_timestamp_us_utc(),
                                           list(packet.time_synchronization_sensor().payload_values()),
                                           packet.best_latency(),
                                           packet.best_offset(),
                                           )
                              for packet in packets]
        if len(self.timesync_data) > 0:
            self.evaluate_and_validate_data()
        return self

    def from_raw_packets(self, packets: List[Union[RedvoxPacketM, RedvoxPacket]]) -> 'TimeSyncAnalysis':
        """
        converts packets into TimeSyncData objects, then performs analysis

        :param packets: list of WrappedRedvoxPacketM to convert
        :return: modified version of self
        """
        timesync_data: List[TimeSyncData] = []

        packet: Union[RedvoxPacketM, RedvoxPacket]
        for packet in packets:
            tsd: TimeSyncData
            if isinstance(packet, RedvoxPacketM):
                exchanges: List[float] = reduce(lambda acc, ex: acc + [ex.a1, ex.a2, ex.a3, ex.b1, ex.b2, ex.b3],
                                                packet.timing_information.synch_exchanges,
                                                [])
                tsd = TimeSyncData(
                    packet.station_information.id,
                    packet.sensors.audio.sample_rate,
                    len(packet.sensors.audio.samples.values),
                    packet.timing_information.app_start_mach_timestamp,
                    packet.timing_information.server_acquisition_arrival_timestamp,
                    packet.timing_information.packet_start_mach_timestamp,
                    packet.timing_information.packet_end_mach_timestamp,
                    exchanges,
                    packet.timing_information.best_latency,
                    packet.timing_information.best_offset
                )
            else:
                mtz: float = np.nan
                best_latency: float = np.nan
                best_offset: float = np.nan

                for i, v in enumerate(packet.metadata):
                    plus_1: int = i + 1
                    try:
                        if v == "machTimeZero" and plus_1 < len(packet.metadata):
                            mtz = float(packet.metadata[plus_1])
                        if v == "bestLatency" and plus_1 < len(packet.metadata):
                            best_latency = float(packet.metadata[plus_1])
                        if v == "bestOffset" and plus_1 < len(packet.metadata):
                            best_offset = float(packet.metadata[plus_1])
                    except (KeyError, ValueError):
                        continue

                # Get synch exchanges
                exchanges: Optional[np.ndarray] = None
                ch: api900_pb2.UnevenlySampledChannel
                for ch in packet.unevenly_sampled_channels:
                    if api900_pb2.TIME_SYNCHRONIZATION in ch.channel_types:
                        exchanges = util_900.extract_payload(ch)

                tsd = TimeSyncData(
                    packet.redvox_id,
                    packet.evenly_sampled_channels[0].sample_rate_hz,
                    util_900.payload_len(packet.evenly_sampled_channels[0]),
                    mtz,
                    packet.evenly_sampled_channels[0].first_sample_timestamp_epoch_microseconds_utc,
                    packet.server_timestamp_epoch_microseconds_utc,
                    packet.app_file_start_timestamp_machine,
                    list(exchanges),
                    best_latency,
                    best_offset,
                )

            timesync_data.append(tsd)

        self.timesync_data = timesync_data

        if len(self.timesync_data) > 0:
            self.evaluate_and_validate_data()

        return self

    def add_timesync_data(self, timesync_data: TimeSyncData):
        """
        adds a TimeSyncData object to the analysis

        :param timesync_data: TimeSyncData to add
        """
        self.timesync_data.append(timesync_data)
        self.evaluate_and_validate_data()

    def get_num_packets(self) -> int:
        """
        :return: number of packets analyzed
        """
        return len(self.timesync_data)

    def get_best_latency(self) -> float:
        """
        :return: the best latency
        """
        if np.isnan(self.best_latency_index):
            return np.nan
        return self.timesync_data[self.best_latency_index].best_latency

    def get_latencies(self) -> np.array:
        """
        :return: np.array containing all the latencies
        """
        return np.array([ts_data.best_latency for ts_data in self.timesync_data])

    def get_mean_latency(self) -> float:
        """
        :return: the mean of the latencies, or np.nan if it doesn't exist
        """
        return self.latency_stats.mean_of_means()

    def get_latency_stdev(self) -> float:
        """
        :return: the standard deviation of the latencies, or np.nan if it doesn't exist
        """
        return self.latency_stats.total_std_dev()

    def get_best_offset(self) -> float:
        """
        :return: offset associated with the best latency
        """
        if np.isnan(self.best_latency_index):
            return np.nan
        return self.timesync_data[self.best_latency_index].best_offset

    def get_offsets(self) -> np.array:
        """
        :return: np.array containing all the offsets
        """
        return np.array([ts_data.best_offset for ts_data in self.timesync_data])

    def get_mean_offset(self) -> float:
        """
        :return: the mean of the offsets, or np.nan if it doesn't exist
        """
        return self.offset_stats.mean_of_means()

    def get_offset_stdev(self) -> float:
        """
        :return: the standard deviation of the offsets, or np.nan if it doesn't exist
        """
        return self.offset_stats.total_std_dev()

    def get_best_packet_latency_index(self) -> int:
        """
        :return: the best latency's index in the packet with the best latency
        """
        if np.isnan(self.best_latency_index):
            return np.nan
        return self.timesync_data[self.best_latency_index].best_latency_index

    def get_best_start_time(self) -> float:
        """
        :return: start timestamp associated with the best latency
        """
        if np.isnan(self.best_latency_index):
            return np.nan
        return self.timesync_data[self.best_latency_index].packet_start_timestamp

    def get_start_times(self) -> np.array:
        """
        :return: list of the start timestamps of each packet
        """
        start_times = []
        for ts_data in self.timesync_data:
            start_times.append(ts_data.packet_start_timestamp)
        return np.array(start_times)

    def get_bad_packets(self) -> List[int]:
        """
        :return: list of all packets that contains invalid data
        """
        bad_packets = []
        for idx in range(
                self.get_num_packets()
        ):  # mark bad indices (they have a 0 or less value)
            if self.get_latencies()[idx] <= 0 or np.isnan(self.get_latencies()[idx]):
                bad_packets.append(idx)
        return bad_packets

    def evaluate_latencies(self):
        """
        finds the best latency
        outputs warnings if a change in timestamps is detected
        """
        if self.get_num_packets() < 1:
            self.errors.append(
                "Latencies cannot be evaluated; length of timesync data is less than 1"
            )
        else:
            self.best_latency_index = 0
            # assume the first element has the best timesync values for now, then compare with the others
            for index in range(1, self.get_num_packets()):
                best_latency = self.get_best_latency()
                # find the best latency; in this case, the minimum
                # if new value exists and if the current best does not or new value is better than current best, update
                if (not np.isnan(self.timesync_data[index].best_latency) and (np.isnan(best_latency))
                        or self.timesync_data[index].best_latency < best_latency):
                    self.best_latency_index = index

    def validate_start_timestamp(self, debug: bool = False) -> bool:
        """
        confirms if station_start_timestamp differs in any of the timesync_data
        outputs warnings if a change in timestamps is detected

        :param debug: if True, output warning message, default False
        :return: True if no change
        """
        for index in range(self.get_num_packets()):
            # compare station start timestamps; notify when they are different
            if (
                    self.timesync_data[index].station_start_timestamp
                    != self.station_start_timestamp
            ):
                self.errors.append(
                    f"Change in station start timestamp detected; "
                    f"expected: {self.station_start_timestamp}, read: "
                    f"{self.timesync_data[index].station_start_timestamp}"
                )
                if debug:
                    self.errors.print()
                return False
        # if here, all the sample timestamps are the same
        return True

    def validate_sample_rate(self, debug: bool = False) -> bool:
        """
        confirms if sample rate is the same across all timesync_data
        outputs warning if a change in sample rate is detected

        :param debug: if True, output warning message, default False
        :return: True if no change
        """
        for index in range(self.get_num_packets()):
            # compare station start timestamps; notify when they are different
            if (
                    np.isnan(self.timesync_data[index].sample_rate_hz)
                    or self.timesync_data[index].sample_rate_hz != self.sample_rate_hz
            ):
                self.errors.append(
                    f"Change in station sample rate detected; "
                    f"expected: {self.sample_rate_hz}, read: {self.timesync_data[index].sample_rate_hz}"
                )
                if debug:
                    self.errors.print()
                return False
        # if here, all the sample rates are the same
        return True

    def validate_time_gaps(self, gap_duration_s: float, debug: bool = False) -> bool:
        """
        confirms there are no data gaps between packets
        outputs warning if a gap is detected

        :param gap_duration_s: length of time in seconds to be detected as a gap
        :param debug: if True, output warning message, default False
        :return: True if no gap
        """
        if self.get_num_packets() < 2:
            self.errors.append("Less than 2 timesync data objects to evaluate gaps with")
            if debug:
                self.errors.print()
        else:
            for index in range(1, self.get_num_packets()):
                # compare last packet's end timestamp with current start timestamp
                if (
                        dt.microseconds_to_seconds(
                            self.timesync_data[index].packet_start_timestamp
                            - self.timesync_data[index - 1].packet_end_timestamp
                        )
                        > gap_duration_s
                ):
                    self.errors.append(f"Gap detected at packet number: {index}")
                    if debug:
                        self.errors.print()
                    return False
        # if here, no gaps
        return True

    def update_timestamps(self, use_model: bool = True):
        """
        update timestamps by adding microseconds based on the OffsetModel.

        :param use_model: if True, use the model, otherwise use best offset
        """
        if use_model and self.offset_model:
            self.station_start_timestamp += self.offset_model.get_offset_at_new_time(self.station_start_timestamp)
            for tsd in self.timesync_data:
                tsd.update_timestamps(self.offset_model)
        else:
            self.station_start_timestamp += self.get_best_offset()
            for tsd in self.timesync_data:
                tsd.update_timestamps()


def validate_sensors(tsa_data: TimeSyncAnalysis) -> bool:
    """
    Examine all sample rates and mach time zeros to ensure that sensor settings do not change

    :param tsa_data: the TimeSyncAnalysis data to validate
    :return: True if sensor settings do not change
    """
    # check that we have packets to read
    if tsa_data.get_num_packets() < 1:
        print("ERROR: no data to validate.")
        return False
    elif tsa_data.get_num_packets() > 1:
        # if we have more than one packet, we need to validate the data
        return tsa_data.validate_sample_rate() and tsa_data.validate_start_timestamp()
    # we get here if all packets have the same sample rate and mach time zero
    return True


def update_evenly_sampled_time_array(
        ts_analysis: TimeSyncAnalysis,
        num_samples: float = None,
        time_start_array_s: np.array = None,
) -> np.ndarray:
    """
    Correct evenly sampled times using updated time_start_array values as the focal point.
    Expects tsd to have the same number of packets as elements in time_start_array.
    Expects there are no gaps in the data or changes in station sample rate or start time.
    Throws an exception if the number of packets in tsa does not match the length of time_start_array

    :param ts_analysis: TimeSyncAnalysis object that contains the information needed to update the time array
    :param num_samples: number of samples in one file; optional, uses number based on sample rate if not given
    :param time_start_array_s: the array of timestamps to correct in seconds; optional, uses the start times in the
                             TimeSyncAnalysis object if not given
    :return: Revised time array in epoch seconds
    """
    if not validate_sensors(ts_analysis):
        raise AttributeError(
            "ERROR: Change in Station Start Time or Sample Rate detected!"
        )
    if time_start_array_s is None:
        # replace the time_start_array with values from tsd; convert tsd times to seconds
        time_start_array_s = np.array([])
        for tsd in ts_analysis.timesync_data:
            time_start_array_s = np.append(
                time_start_array_s,
                tsd.packet_start_timestamp / dt.MICROSECONDS_IN_SECOND,
                )
    num_files = len(ts_analysis.timesync_data)
    # the TimeSyncData must have the same number of packets as the number of elements in time_start_array
    if num_files != len(time_start_array_s):
        # alert the user, then quit
        raise Exception(
            "ERROR: Attempted to update a time array that doesn't contain "
            "the same number of elements as the TimeSyncAnalysis!"
        )

    # use the number of audio samples in the first data packet
    if num_samples is None:
        num_samples = ts_analysis.timesync_data[0].num_audio_samples
    t_dt = 1.0 / ts_analysis.sample_rate_hz

    # Use TimeSyncData object to find best start index.
    # Samples before will be the number of decoders before a0 times the number of samples in a file.
    # Samples after will be the number of decoders after a0 times the number of samples in a file minus 1;
    # the minus one represents the best a0.
    decoder_idx = ts_analysis.best_latency_index
    samples_before = int(decoder_idx * num_samples)
    samples_after = round((num_files - decoder_idx) * num_samples) - 1
    best_start_sec = time_start_array_s[decoder_idx]

    # build the time arrays separately in epoch seconds, then join into one
    # add 1 to include the actual a0 sample, then add 1 again to skip the a0 sample; this avoids repetition
    timesec_before = np.vectorize(lambda t: best_start_sec - t * t_dt)(
        list(range(int(samples_before + 1)))
    )
    timesec_before = timesec_before[
                     ::-1
                     ]  # reverse 'before' times so they increase from earliest start time
    timesec_after = np.vectorize(lambda t: best_start_sec + t * t_dt)(
        list(range(1, int(samples_after + 1)))
    )
    timesec_rev = np.concatenate([timesec_before, timesec_after])

    return update_time_array_from_analysis(ts_analysis, timesec_rev)


def update_time_array(ts_data: TimeSyncData, time_array_s: np.array) -> np.ndarray:
    """
    Correct timestamps in time_array using information from TimeSyncData

    :param ts_data: TimeSyncData object that contains the information needed to update the time array
    :param time_array_s: the list of timestamps to correct in seconds
    :return: Revised time array in epoch seconds
    """
    return time_array_s + (ts_data.best_offset / dt.MICROSECONDS_IN_SECOND)


def update_time_array_from_analysis(
        ts_analysis: TimeSyncAnalysis, time_array_s: np.array
) -> np.ndarray:
    """
    Correct timestamps in time_array using information from TimeSyncAnalysis

    :param ts_analysis: TimeSyncAnalysis object that contains the information needed to update the time array
    :param time_array_s: the list of timestamps to correct in seconds
    :return: Revised time array in epoch seconds
    """
    return time_array_s + (ts_analysis.get_best_offset() / dt.MICROSECONDS_IN_SECOND)
