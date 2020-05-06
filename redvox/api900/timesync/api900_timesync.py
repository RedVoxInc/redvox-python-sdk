"""
Modules for extracting time synchronization statistics for API 900 data.
Also includes functions for correcting time arrays.
"""

from typing import List, Optional, Tuple

# noinspection Mypy
import numpy as np

from redvox.api900.reader import WrappedRedvoxPacket
from redvox.api900.reader_utils import empty_array
from redvox.api900.timesync import tri_message_stats
from redvox.common import date_time_utils as dt
from redvox.common import file_statistics as fh
from redvox.common import stats_helper


class TimeSyncData:
    """
    Stores latencies, revised start times, time sync server offsets, and difference in adjusted machine time and
    acquisition server time
    Note that inputs to this must be continuous data; any change in sensor mach_time_zero or sample_rate
    requires a new TimeSyncData object
    ALL times in microseconds
    properties:
        rev_start_times: revised machine start times (per packet)
        server_acquisition_times: time packet arrived at server (per packet)
        latencies: latencies (per packet)
        best_latency: the lowest latency among packets
        best_latency_index: index in latencies array that contains the best latency
        latency_stats: StatsContainer for latencies
        offsets: list of calculated offsets (per packet)
        best_offset: the offset that is paired with the lowest latency
        offset_stats: StatsContainer for offsets
        num_packets: the number of packets being analyzed
        sample_rate_hz: the sample rate in Hz of all packets
        packet_duration: the duration of all packets
        mach_time_zero: the start time of the app in machine time
        num_tri_messages: number of tri-message exchanges (per packet)
        tri_message_coeffs: list of 6-tuples containing the tri-message exchange coefficients (up to 1 tuple per packet)
        best_tri_msg_indices: the index of the best tri-message for each of the tri_message_coeffs tuples
        acquire_travel_time: calculated time it took packet to reach server (up to 1 per packet)
        bad_packets: indices of packets with an undefined or 0 latency
    """

    def __init__(self, wrapped_packets: List[WrappedRedvoxPacket] = None):
        """
        Initialize properties, assume all packets share the same sample rate and are continuous
        :param wrapped_packets: list of data packets
        """
        self.latency_stats: stats_helper.StatsContainer = stats_helper.StatsContainer("latency")
        self.offset_stats: stats_helper.StatsContainer = stats_helper.StatsContainer("offset")
        if wrapped_packets is None or len(wrapped_packets) < 1:
            self.rev_start_times: np.ndarray = np.ndarray((0, 0))
            self.server_acquisition_times: np.ndarray = np.ndarray((0, 0))
            self.latencies: np.ndarray = np.ndarray((0, 0))
            self.best_latency: Optional[float] = None
            self.best_latency_index: Optional[int] = None
            self.offsets: np.ndarray = np.ndarray((0, 0))
            self.best_offset: float = 0.0
            self.num_packets: int = 0
            self.sample_rate_hz: Optional[float] = None
            self.packet_duration: int = 0
            self.mach_time_zero: Optional[float] = None
            self.num_tri_messages: np.ndarray = np.ndarray((0, 0))
            self.tri_message_coeffs: List[Tuple] = []
            self.best_tri_msg_indices: List[int] = []
            self.acquire_travel_time: np.ndarray = np.ndarray((0, 0))
            self.bad_packets: List[int] = []
        else:
            self.get_time_sync_data(wrapped_packets)

    def get_time_sync_data(self, wrapped_packets: List[WrappedRedvoxPacket]):
        """
        Sets the time statistics between machine, time server, and acquisition server for the packets given.
        :param wrapped_packets: wrapped packets with same sample rate
        """
        self.server_acquisition_times = np.zeros(len(wrapped_packets))  # array of server acquisition times
        self.rev_start_times = np.zeros(len(wrapped_packets))   # array of app start times
        self.num_tri_messages = np.zeros(len(wrapped_packets))  # number of tri-message exchanges per packet
        self.latencies = np.zeros(len(wrapped_packets))  # array of minimum latencies
        self.offsets = np.zeros(len(wrapped_packets))  # array of offset applied to machine time to get sync time
        self.num_packets = len(wrapped_packets)  # number of packets in list
        self.tri_message_coeffs = []    # a list of tri-message coefficients
        self.best_tri_msg_indices = []  # a list of the best latency index in each set of tri-message coefficients
        self.bad_packets = []   # list of packets that contain invalid data
        sample_rates = np.zeros(len(wrapped_packets))       # list of sample rates, should all be the same
        mach_time_zeros = np.zeros(len(wrapped_packets))    # list of mach time zeros, should all the be same

        # get the server acquisition time, app start time, and tri message stats
        for i, wrapped_packet in enumerate(wrapped_packets):
            # pass the mach_time_zero and sample_rate into arrays
            sample_rates[i] = wrapped_packet.microphone_sensor().sample_rate_hz()
            mach_time_zeros[i] = wrapped_packet.mach_time_zero()
            self.server_acquisition_times[i] = wrapped_packet.server_timestamp_epoch_microseconds_utc()
            self.rev_start_times[i] = wrapped_packet.app_file_start_timestamp_epoch_microseconds_utc()
            self._compute_tri_message_stats(wrapped_packet, i)

        # check sample rate and mach time zero (if it exists) for changes.  if it changed, sync will not work.
        if not self._validate_sensor_settings(sample_rates, mach_time_zeros):
            raise Exception("ERROR: Sensor settings changed; separate data based on changes and re-analyze")
        self.find_bad_packets()
        self.evaluate_latencies_and_offsets()
        # set the packet duration
        self.packet_duration = dt.seconds_to_microseconds(fh.get_duration_seconds_from_sample_rate(
            int(self.sample_rate_hz)))
        # apply duration to app start to get packet end time, then subtract
        # that from server acquire time to get travel time to acquisition server
        # ASSUMING that acquisition and time-sync server have the same time source
        self.acquire_travel_time = self.server_acquisition_times - (self.rev_start_times + self.packet_duration)

    def evaluate_latencies_and_offsets(self):
        """
        evaluates the goodness of latencies and offsets.
        adjusts rev_start_times if there is a best offset
        """
        # if no decoders synced properly, all latencies are NaNs or all indices are bad
        if np.isnan(self.latencies).all() or len(self.bad_packets) == self.num_packets:
            # make everything empty or None, and best offset is 0 (no change)
            self.latencies = []
            self.offsets = []
            self.best_latency = None
            self.best_latency_index = None
            self.best_offset = 0.0
        else:
            # convert all NaN and negative values from latencies into zero
            self.latencies = np.nan_to_num(self.latencies)
            self.latencies[self.latencies < 0] = 0.0
            # find and set minimum latency based on non-zero latencies
            self.best_latency = np.min(self.get_valid_latencies())
            self.latency_stats.best_value = self.best_latency
            self.best_latency_index = np.where(self.latencies == self.best_latency)[0][0]
            # find all non-NaN, non-zero offsets
            good_offsets = self.get_valid_offsets()

            if good_offsets is not None and len(good_offsets) > 0:
                # there must be some good offsets; convert all NaN offsets to 0
                self.offsets = np.nan_to_num(self.offsets)
                # set best offset based on best latency
                self.best_offset = self.offsets[self.best_latency_index]
                self.offset_stats.best_value = self.best_offset
                # fix all packet start times by adding the packet's offset
                self.rev_start_times += self.best_offset
            else:
                # set offset properties to empty or None
                self.offsets = []

    def _compute_tri_message_stats(self, packet: WrappedRedvoxPacket, index: int):
        """
        helper function to compute tri message stats of the time sync data
        :param packet: a packet to compute tri message stats from
        :param index: the index to add the data to
        """
        # if there is a time sync channel with payload, find the minimum latency and its corresponding offset
        if packet.has_time_synchronization_sensor():
            timesync_channel = packet.time_synchronization_sensor()
            coeffs = timesync_channel.payload_values()
            # set the number of tri-message exchanges in the packet
            self.num_tri_messages[index] = int(len(coeffs) / 6)
            coeffs_tuple: Tuple[
                np.ndarray,
                np.ndarray,
                np.ndarray,
                np.ndarray,
                np.ndarray,
                np.ndarray] = tri_message_stats.transmit_receive_timestamps_microsec(coeffs)
            self.tri_message_coeffs.append(coeffs_tuple)  # save the tri-message exchanges for later
            a1_coeffs: np.ndarray = coeffs_tuple[0]
            a2_coeffs: np.ndarray = coeffs_tuple[1]
            a3_coeffs: np.ndarray = coeffs_tuple[2]
            b1_coeffs: np.ndarray = coeffs_tuple[3]
            b2_coeffs: np.ndarray = coeffs_tuple[4]
            b3_coeffs: np.ndarray = coeffs_tuple[5]
            # get tri message data via TriMessageStats class
            tms = tri_message_stats.TriMessageStats(packet.redvox_id(),
                                                    a1_coeffs,
                                                    a2_coeffs,
                                                    a3_coeffs,
                                                    b1_coeffs,
                                                    b2_coeffs,
                                                    b3_coeffs)
            # check if we actually have exchanges to evaluate
            if self.num_tri_messages[index] > 0:
                # Concatenate d1 and d3 arrays, and o1 and o3 arrays when passing values into stats class
                #  note the last parameter multiplies the number of exchanges by 2, as there are two latencies
                #  and offsets calculated per exchange
                # noinspection PyTypeChecker
                self.latency_stats.add(np.mean([*tms.latency1, *tms.latency3]), np.std([*tms.latency1, *tms.latency3]),
                                       self.num_tri_messages[index] * 2)
                # noinspection PyTypeChecker
                self.offset_stats.add(np.mean([*tms.offset1, *tms.offset3]), np.std([*tms.offset1, *tms.offset3]),
                                      self.num_tri_messages[index] * 2)
                # set the best latency and offset based on the packet's metadata, or tri-message stats if no metadata
                latency: Optional[float] = packet.best_latency()
                # pass the location of the best calculated latency
                self.best_tri_msg_indices.append(tms.best_latency_index)
                if latency is None:
                    # no metadata
                    self.latencies[index] = tms.best_latency
                else:
                    self.latencies[index] = latency
                offset: Optional[float] = packet.best_offset()
                if offset is None:
                    # no metadata
                    self.offsets[index] = tms.best_offset
                else:
                    self.offsets[index] = offset
                # everything has been computed, time to return
                return
        # If here, there are no exchanges to read or there is no sync channel.
        # write default or empty values to the correct properties
        self.latencies[index] = 0.0
        self.offsets[index] = 0.0
        self.tri_message_coeffs.append((empty_array(), empty_array(), empty_array(),
                                        empty_array(), empty_array(), empty_array()))
        # pass the location of the best latency
        self.best_tri_msg_indices.append(-1)
        # noinspection PyTypeChecker
        self.latency_stats.add(0, 0, 0)
        # noinspection PyTypeChecker
        self.offset_stats.add(0, 0, 0)

    def _validate_sensor_settings(self, sample_rates: np.array, mach_time_zeros: np.array) -> bool:
        """
        Examine all sample rates and mach time zeros to ensure that sensor settings do not change
        Sets the sample rate and mach time zero if there is no change
        :param sample_rates: sample rates of all packets from sensor
        :param mach_time_zeros: machine time zero of all packets from sensor
        :return: True if sensor settings do not change
        """
        # set the sample rate and mach time zero
        self.sample_rate_hz = sample_rates[0]
        self.mach_time_zero = mach_time_zeros[0]
        if len(sample_rates) > 1:
            # if there's more than 1 value, we need to compare them
            for i in range(1, len(sample_rates)):
                if self.sample_rate_hz != sample_rates[i]:
                    print("ERROR: sample rate in data packets has changed.")
                    return False
                # process only non-nan mach time zeros
                if not np.isnan(self.mach_time_zero) and self.mach_time_zero != mach_time_zeros[i]:
                    print("ERROR: mach time zero in data packets has changed.")
                    return False
        return True

    def find_bad_packets(self):
        """
        Find bad packets and mark them using the bad_packets property
        Assuming all packets have been processed and all bad packets are marked with a 0 (or are negative)
        """
        for idx in range(len(self.latencies)):  # mark bad indices (they have a 0 or less value)
            if self.latencies[idx] <= 0:
                self.bad_packets.append(idx)

    def get_ratio_bad_packets(self) -> float:
        """
        Return the ratio of packets with bad latency calculations over total packets
        :return: num packets with bad latency calculations / total packets
        """
        if self.num_packets < 1:
            return 0
        return len(self.bad_packets) / float(self.num_packets)

    def get_latency_mean(self) -> Optional[float]:
        """
        return the mean of all latencies, and None if the latencies are invalid.
        :return: the mean of all latencies
        """
        if self.best_latency is None:
            return None
        else:
            return self.latency_stats.mean_of_means()

    def get_latency_std_dev(self) -> Optional[float]:
        """
        return the standard deviation (std_dev) of all latencies, and None if the latencies are invalid.
        :return: the std dev of all latencies
        """
        if self.best_latency is None:
            return None
        else:
            return self.latency_stats.total_std_dev()

    def get_valid_latencies(self, latency_array: np.array = None) -> np.array:
        """
        takes latencies, converts NaNs and negatives to 0, then returns non-zero latencies
        :param latency_array: optional array to clean instead of self.latencies; default None
        :return: non-NaN, non-zero latencies
        """
        if latency_array is None:
            clean_latencies = np.nan_to_num(self.latencies)  # replace NaNs with zeros
        else:
            clean_latencies = np.nan_to_num(latency_array)  # replace NaNs with zeros
        clean_latencies[clean_latencies < 0] = 0  # replace negative latencies with 0
        return clean_latencies[clean_latencies != 0]  # return only non-zero latencies

    def get_offset_mean(self) -> Optional[float]:
        """
        return the mean of all offsets, and 0.0 if the offsets or latencies are invalid.
        :return: the mean of all offsets
        """
        if self.best_latency is None or self.best_offset == 0.0:
            return 0.0
        else:
            return self.offset_stats.mean_of_means()

    def get_offset_std_dev(self) -> Optional[float]:
        """
        return the standard deviation (std_dev) of all offsets, and 0.0 if the offsets or latencies are invalid.
        :return: the std dev of all offsets
        """
        if self.best_latency is None or self.best_offset == 0.0:
            return 0.0
        else:
            return self.offset_stats.total_std_dev()

    def get_valid_offsets(self, offset_array: np.array = None) -> np.array:
        """
        takes valid offsets (based on bad_packets), converts NaNs to 0, then returns non-zero offsets
        :param offset_array: optional array to clean; default None
        :return: non-NaN, non-zero offsets
        """
        if offset_array is None:
            if len(self.bad_packets) > 0:
                valids = []
                for i in range(len(self.offsets)):
                    if i not in self.bad_packets:
                        valids.append(self.offsets[i])
                clean_offsets = np.nan_to_num(valids)  # replace NaNs with zeros
            else:
                clean_offsets = np.nan_to_num(self.offsets)
        else:
            clean_offsets = np.nan_to_num(offset_array)
        return clean_offsets[clean_offsets != 0]  # return only non-zero offsets

    def get_valid_rev_start_times(self) -> np.array:
        """
        return the array of valid (based on bad_packets) revised start times
        :return: array of valid revised start times
        """
        if len(self.bad_packets) > 0:  # return only the start times not associated with a bad packet
            valids = []
            for i in range(len(self.rev_start_times)):
                if i not in self.bad_packets:  # this is a good packet
                    valids.append(self.rev_start_times[i])
            return np.array(valids)
        else:
            return self.rev_start_times

    def get_best_rev_start_time(self) -> int:
        """
        return the revised start time associated with the lowest latency
        :return: revised start time in microseconds associated with the lowest latency
        """
        return self.rev_start_times[self.best_latency_index]


def validate_sensors(wrapped_packets: List[WrappedRedvoxPacket]) -> bool:
    """
    Examine all sample rates and mach time zeros to ensure that sensor settings do not change
    :param wrapped_packets: a list of wrapped redvox packets to read
    :return: True if sensor settings do not change
    """
    # check that we have packets to read
    num_packets = len(wrapped_packets)
    if num_packets < 1:
        print("ERROR: no data to validate.")
        return False
    # if we have more than one packet, we need to validate the data
    elif num_packets > 1:
        sample_rates = np.zeros(num_packets)
        mach_time_zeros = np.zeros(num_packets)
        for j, wrapped_packet in enumerate(wrapped_packets):
            sample_rates[j] = wrapped_packet.microphone_sensor().sample_rate_hz()
            mach_time_zeros[j] = wrapped_packet.mach_time_zero()
        for i in range(1, len(sample_rates)):
            if sample_rates[0] != sample_rates[i]:
                print("ERROR: sample rate in data packets has changed.")
                return False
            # process only non-nan mach time zeros
            if not np.isnan(mach_time_zeros[0]) and mach_time_zeros[0] != mach_time_zeros[i]:
                print("ERROR: mach time zero in data packets has changed.")
                return False
    # we get here if all packets have the same sample rate and mach time zero
    return True


def update_evenly_sampled_time_array(tsd: TimeSyncData, num_samples: float = None,
                                     time_start_array: np.array = None) -> np.ndarray:
    """
    Correct evenly sampled times using updated time_start_array values as the focal point.
    Expects tsd to have the same number of packets as elements in time_start_array
    Inserts data gaps where necessary before building array.
    Throws an exception if the number of packets in tsd does not match the length of time_start_array

    :param tsd: TimeSyncData object that contains the information needed to update the time array
    :param num_samples: number of samples in one file; optional, uses number based on sample rate if not given
    :param time_start_array: the list of timestamps to correct in seconds; optional, uses the start times in the
                             TimeSyncData object if not given
    :return: Revised time array in epoch seconds
    """
    if time_start_array is None:
        # replace the time_start_array with values from tsd; convert tsd times to seconds
        time_start_array = tsd.rev_start_times / dt.MICROSECONDS_IN_SECOND
    num_files = tsd.num_packets
    # the TimeSyncData must have the same number of packets as the number of elements in time_start_array
    if num_files != len(time_start_array):
        # alert the user, then quit
        raise Exception("ERROR: Attempted to update a time array that doesn't contain "
                        "the same number of elements as the TimeSyncData!")

    if num_samples is None:
        num_samples = fh.get_num_points_from_sample_rate(tsd.sample_rate_hz)
    t_dt = 1.0 / tsd.sample_rate_hz

    # Use TimeSyncData object to find best start index.
    # Samples before will be the number of decoders before a0 times the number of samples in a file.
    # Samples after will be the number of decoders after a0 times the number of samples in a file minus 1;
    # the minus one represents the best a0.
    decoder_idx = tsd.best_latency_index
    samples_before = int(decoder_idx * num_samples)
    samples_after = round((num_files - decoder_idx) * num_samples) - 1
    best_start_sec = time_start_array[decoder_idx]

    # build the time arrays separately in epoch seconds, then join into one
    # add 1 to include the actual a0 sample, then add 1 again to skip the a0 sample; this avoids repetition
    timesec_before = np.vectorize(lambda t: best_start_sec - t * t_dt)(list(range(int(samples_before + 1))))
    timesec_before = timesec_before[::-1]  # reverse 'before' times so they increase from earliest start time
    timesec_after = np.vectorize(lambda t: best_start_sec + t * t_dt)(list(range(1, int(samples_after + 1))))
    timesec_rev = np.concatenate([timesec_before, timesec_after])

    return timesec_rev


def update_time_array(tsd: TimeSyncData, time_array: np.array) -> np.ndarray:
    """
    Correct timestamps in time_array using information from TimeSyncData
    :param tsd: TimeSyncData object that contains the information needed to update the time array
    :param time_array: the list of timestamps to correct in seconds
    :return: Revised time array in epoch seconds
    """
    return time_array + (tsd.best_offset / dt.MICROSECONDS_IN_SECOND)


def sync_packet_time_900(wrapped_packets_fs: list, verbose: bool = False):
    """
    Correct the timestamps for api900 data based on minimum latency and best offset of the ensemble.

    :param wrapped_packets_fs: wrapped packets with same sample rate and from same device
    :param verbose: if True, prints statements to assess goodness of time sync
    """

    # assume each packet has a best latency and offset
    latencies = []  # array of minimum latencies
    offsets = []  # array of offset applied to machine time to get sync time

    # latencies and offsets
    for packet in wrapped_packets_fs:
        if packet.has_time_synchronization_sensor():
            # set the best latency and offset based on the packet's metadata
            if packet.best_latency() is not None and packet.best_offset() is not None:
                latencies.append(packet.best_latency())
                offsets.append(packet.best_offset())
            else:
                # metadata not set, use packet contents
                timesync_channel = packet.time_synchronization_sensor()
                coeffs = timesync_channel.payload_values()
                coeffs_tuple: Tuple[
                    np.ndarray,
                    np.ndarray,
                    np.ndarray,
                    np.ndarray,
                    np.ndarray,
                    np.ndarray] = tri_message_stats.transmit_receive_timestamps_microsec(coeffs)
                a1_coeffs: np.ndarray = coeffs_tuple[0]
                a2_coeffs: np.ndarray = coeffs_tuple[1]
                a3_coeffs: np.ndarray = coeffs_tuple[2]
                b1_coeffs: np.ndarray = coeffs_tuple[3]
                b2_coeffs: np.ndarray = coeffs_tuple[4]
                b3_coeffs: np.ndarray = coeffs_tuple[5]
                # get tri message data via TriMessageStats class
                tms = tri_message_stats.TriMessageStats(packet.redvox_id(),
                                                        a1_coeffs,
                                                        a2_coeffs,
                                                        a3_coeffs,
                                                        b1_coeffs,
                                                        b2_coeffs,
                                                        b3_coeffs)
                latencies.append(tms.best_latency)
                offsets.append(tms.best_offset)
        # if there is no time sync channel (usually no communication between device and server), default to 0
        else:
            latencies.append(0)
            offsets.append(0)

    # convert NaN latencies to 0
    latencies = np.nan_to_num(latencies)
    # convert any negative latency to 0.
    latencies[latencies < 0] = 0

    if len(np.nonzero(latencies)[0]) == 0:  # if no decoders synced properly, all latencies are 0
        sync_server = wrapped_packets_fs[0].time_synchronization_server()
        if verbose:
            print('\n{} did not achieve sync with time sync server {}!'.format(
                wrapped_packets_fs[0].redvox_id(), sync_server))
        offset = 0
    else:
        d1_min = np.min(latencies[latencies != 0])
        best_d1_index = np.where(latencies == d1_min)[0][0]
        # correct each packet's timestamps
        offset = int(offsets[best_d1_index])

    for wrapped_packet in wrapped_packets_fs:
        # update the machine file start time and mach time zero
        wrapped_packet.set_app_file_start_timestamp_epoch_microseconds_utc(
            wrapped_packet.app_file_start_timestamp_epoch_microseconds_utc() + offset)
        wrapped_packet.set_app_file_start_timestamp_machine(
            wrapped_packet.app_file_start_timestamp_machine() + offset)
        if wrapped_packet.mach_time_zero() is not None:
            wrapped_packet.set_mach_time_zero(wrapped_packet.mach_time_zero() + offset)
        # update microphone start time
        if wrapped_packet.has_microphone_sensor():
            wrapped_packet.microphone_sensor().set_first_sample_timestamp_epoch_microseconds_utc(
                wrapped_packet.microphone_sensor().first_sample_timestamp_epoch_microseconds_utc() + offset)
        # correct the times in unevenly sampled channels using the packets' best offset
        wrapped_packet.update_uneven_sensor_timestamps(offset)
        wrapped_packet.set_is_synch_corrected(True)
