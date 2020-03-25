"""
Modules for extracting time synchronization statistics according to Tri-Message protocol. All functions assume
payload for ONE data packet/decoder ONLY. These modules will be called separately by API800 and API900 loaders, they
are in themselves helper functions. They do not depend on API formats, they take the time sync payloads as parameters
and use Tri-Message protocol to compute latencies, check criteria, and correct the "machine" start time B0 based on the
minimum latencies.
"""

from typing import Dict, List, Optional, Tuple, Union

# noinspection Mypy
import numpy as np


class TriMessageStats:
    """
    Stores statistics about the tri-message exchanges
    ALL timestamps in microseconds
    Properties:
        packet_id: an identifier for the packet that contains the data.  Used for reporting purposes
        latency1: latencies measured by timestamps 1 and 2
        latency3: latencies measured by timestamps 2 and 3
        offset1: offsets measured by timestamps 1 and 2
        offset3: offsets measured by timestamps 2 and 3
        best_latency: minimum latency that meets all criteria
        best_offset: best offset that meets all criteria
        best_latency_array_index: number of latency array with best latency
        best_latency_index: index in latency array of best latency
        num_messages: number of tri-message exchanges
    """

    def __init__(self,
                 packet_id: Union[str, int],
                 a1: np.ndarray,
                 a2: np.ndarray,
                 a3: np.ndarray,
                 b1: np.ndarray,
                 b2: np.ndarray,
                 b3: np.ndarray):
        """
        Calculate latency, offset, and their qualities.
        :param packet_id: an identifier for reporting purposes
        :param a1: array of server timestamp 1
        :param a2: array of server timestamp 2
        :param a3: array of server timestamp 3
        :param b1: array of device timestamp 1
        :param b2: array of device timestamp 2
        :param b3: array of device timestamp 3
        """
        self.packet_id: Union[str, int] = packet_id
        self.num_messages: int = len(a1)
        # compute latencies and offsets
        latencies_tuple: Tuple[np.ndarray, np.ndarray] = latencies(a1, a2, a3, b1, b2, b3)
        self.latency1: np.ndarray = latencies_tuple[0]
        self.latency3: np.ndarray = latencies_tuple[1]
        offsets_tuple: Tuple[np.ndarray, np.ndarray] = offsets(a1, a2, a3, b1, b2, b3)
        self.offset1: np.ndarray = offsets_tuple[0]
        self.offset3: np.ndarray = offsets_tuple[1]

        self.best_latency: Optional[float] = None
        self.best_latency_array_index: Optional[int] = None
        self.best_latency_index: Optional[int] = None
        self.best_offset: Optional[float] = 0.0

        self.find_best_latency()
        self.find_best_offset()

    def find_best_latency(self) -> None:
        """
        Finds the best latency among the latencies
        """
        try:
            # find value and index of minimum latency of nonzero latencies
            d1_min: float = np.min(self.latency1[self.latency1 != 0])
            d3_min: float = np.min(self.latency3[self.latency3 != 0])

            if d3_min > d1_min:
                self.best_latency = d1_min  # server round trip is shorter
                self.best_latency_array_index = 1
                self.best_latency_index = np.where(self.latency1 == d1_min)[0][0]
            else:
                self.best_latency = d3_min
                self.best_latency_array_index = 3
                self.best_latency_index = np.where(self.latency3 == d3_min)[0][0]
        except ValueError:
            # all latencies for one of the arrays is zero; the data is untrustworthy.  set the defaults
            self.best_latency = None
            self.best_latency_array_index = None
            self.best_latency_index = None

    def find_best_offset(self) -> None:
        """
        Finds the best offset among the offsets
        """
        # if no best latency, find it
        if self.best_latency is None:
            self.find_best_latency()
        # best latency = best offset, if best latency is still None, best offset is 0.0
        if self.best_latency_array_index == 1:
            self.best_offset = self.offset1[self.best_latency_index]
        elif self.best_latency_array_index == 3:
            self.best_offset = self.offset3[self.best_latency_index]
        else:
            self.best_offset = 0.0

    def set_latency(self,
                    a1_coeffs: np.ndarray,
                    a2_coeffs: np.ndarray,
                    a3_coeffs: np.ndarray,
                    b1_coeffs: np.ndarray,
                    b2_coeffs: np.ndarray,
                    b3_coeffs: np.ndarray) -> None:
        """
        set the latency and find the best
        :param a1_coeffs: server timestamp 1
        :param a2_coeffs: server timestamp 2
        :param a3_coeffs: server timestamp 3
        :param b1_coeffs: device timestamp 1
        :param b2_coeffs: device timestamp 2
        :param b3_coeffs: device timestamp 3
        """
        # compute latencies
        self.latency1, self.latency3 = latencies(a1_coeffs, a2_coeffs, a3_coeffs, b1_coeffs, b2_coeffs, b3_coeffs)
        self.find_best_latency()

    def set_offset(self,
                   a1_coeffs: np.ndarray,
                   a2_coeffs: np.ndarray,
                   a3_coeffs: np.ndarray,
                   b1_coeffs: np.ndarray,
                   b2_coeffs: np.ndarray,
                   b3_coeffs: np.ndarray) -> None:
        """
        set the offset and find the best
        :param a1_coeffs: server timestamp 1
        :param a2_coeffs: server timestamp 2
        :param a3_coeffs: server timestamp 3
        :param b1_coeffs: device timestamp 1
        :param b2_coeffs: device timestamp 2
        :param b3_coeffs: device timestamp 3
        """
        # latency calculations are required:
        if self.best_latency is None:
            self.set_latency(a1_coeffs, a2_coeffs, a3_coeffs, b1_coeffs, b2_coeffs, b3_coeffs)
        # compute offsets
        self.offset1, self.offset3 = offsets(a1_coeffs, a2_coeffs, a3_coeffs, b1_coeffs, b2_coeffs, b3_coeffs)
        self.find_best_offset()


def latencies(a1_coeffs: np.ndarray,
              a2_coeffs: np.ndarray,
              a3_coeffs: np.ndarray,
              b1_coeffs: np.ndarray,
              b2_coeffs: np.ndarray,
              b3_coeffs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute latencies in microseconds based on message exchange timestamps.

    Parameters
    ----------
    a1_coeffs, ... b3_coeffs: tri-message timestamps as loaded in transmit_receive_timestamps_microsec

    Returns
    -------
    d1_coeffs: array of server round trip latencies in microseconds
    d3_coeffs: array of device round trip latencies in microseconds
    """
    # Compute latencies in microseconds
    d1_coeffs: np.ndarray = 0.5 * ((a2_coeffs - a1_coeffs) - (b2_coeffs - b1_coeffs))
    d3_coeffs: np.ndarray = 0.5 * ((b3_coeffs - b2_coeffs) - (a3_coeffs - a2_coeffs))

    # convert negative latencies to 0.  negative latencies should not exist naturally
    d1_coeffs[d1_coeffs < 0] = 0
    d3_coeffs[d3_coeffs < 0] = 0

    return d1_coeffs, d3_coeffs


def offsets(a1_coeffs: np.ndarray,
            a2_coeffs: np.ndarray,
            a3_coeffs: np.ndarray,
            b1_coeffs: np.ndarray,
            b2_coeffs: np.ndarray,
            b3_coeffs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute offsets in microseconds based on message exchange timestamps.

    Parameters
    ----------
    a1_coeffs, ... b3_coeffs: tri-message timestamps as loaded in transmit_receive_timestamps_microsec

    Returns
    -------
    o1_coeffs: array of server round trip latencies in microseconds
    o3_coeffs: array of device round trip latencies in microseconds
    """
    # assume the generic equation f = a - b + d
    # where d is latency, f is offset, b is machine time and a is time sync server time
    # refer to latency equations above for definitions of d1_coeffs and d3_coeffs
    # with latency d1_coeffs, the equation is f1 = a1_coeffs - b1_coeffs + d1_coeffs
    # with latency d3_coeffs, the equation is f3 = a3_coeffs - b3_coeffs + d3_coeffs
    # In the absence of latency, offset can be calculated this way:
    # o1_coeffs = (a1_coeffs - b1_coeffs + a2_coeffs - b2_coeffs) / 2.
    # o3_coeffs = (a3_coeffs - b3_coeffs + a2_coeffs - b2_coeffs) / 2.
    # get latencies
    latencies_tuple: Tuple[np.ndarray, np.ndarray] = latencies(a1_coeffs,
                                                               a2_coeffs,
                                                               a3_coeffs,
                                                               b1_coeffs,
                                                               b2_coeffs,
                                                               b3_coeffs)
    d1_coeffs: np.ndarray = latencies_tuple[0]
    d3_coeffs: np.ndarray = latencies_tuple[1]
    # use latency to compute offset in microseconds
    o1_coeffs: np.ndarray = a1_coeffs - b1_coeffs + d1_coeffs
    o3_coeffs: np.ndarray = a3_coeffs - b3_coeffs + d3_coeffs

    return o1_coeffs, o3_coeffs


def validate_timestamps(a1_coeffs: np.ndarray, a2_coeffs: np.ndarray, a3_coeffs: np.ndarray,
                        b1_coeffs: np.ndarray, b2_coeffs: np.ndarray, b3_coeffs: np.ndarray) -> \
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    it's possible some of the tri-message values are duplicated; the duplicates and other invalid times
    must be removed.

       Parameters
       -------
       a1_coeffs, a2_coeffs, a3_coeffs, b1_coeffs, b2_coeffs, b3_coeffs: arrays of message exchange timestamps

       Returns
       -------
       a1_coeffs[valid_indices], a2_coeffs[valid_indices], a3_coeffs[valid_indices],
       b1_coeffs[valid_indices], b2_coeffs[valid_indices], b3_coeffs[valid_indices]:
       arrays of valid message exchange timestamps
    """
    num_timestamps = len(a1_coeffs)
    # if length is 1 or less, no need to validate, just return all the values
    if num_timestamps <= 1:
        return a1_coeffs, a2_coeffs, a3_coeffs, b1_coeffs, b2_coeffs, b3_coeffs
    # if here, there's more than 1 exchange to check
    valid_times: List[Dict] = [{}, {}, {}, {}, {}, {}]
    valid_indices = []
    all_timestamps = [a1_coeffs, a2_coeffs, a3_coeffs, b1_coeffs, b2_coeffs, b3_coeffs]
    # for each set of timestamps a1x, a2x, etc. in all exchanges
    for data_index in range(6):
        for time_index in range(num_timestamps):
            # compare the time to existing information
            time = all_timestamps[data_index][time_index]
            if time not in valid_times:
                # it's not in valid times, it's a new time
                valid_times[data_index][time] = time_index
    for index in valid_times[0].values():
        # if it's not in the first one, it's not valid.  if it doesn't show up in all others, it's not valid
        if index in valid_times[1].values() and index in valid_times[2].values() and \
                index in valid_times[3].values() and index in valid_times[4].values() and \
                index in valid_times[5].values():
            valid_indices.append(index)
    return a1_coeffs[valid_indices], a2_coeffs[valid_indices], a3_coeffs[valid_indices], \
        b1_coeffs[valid_indices], b2_coeffs[valid_indices], b3_coeffs[valid_indices]


def transmit_receive_timestamps_microsec(coeffs: np.ndarray) -> Tuple[
        np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
       Recover Tri-Message timestamp coefficients. Uses concept of
       Tri-Message to synchronize a device with a reference server:

           First, server A transmits a message to device B with timestamp a1_coeffs. B receives the message at timestamp
            b1_coeffs. B then transmits a message back to A with timestamp b2_coeffs. A receives this message at
            timestamp a2_coeffs. A transmits a second message to B at timestamp a3_coeffs. B receives the message at
            timestamp b3_coeffs.

       Parameters
       ----------
       coeffs: array of tri-message coefficients (a1_coeffs, a2_coeffs, a3_coeffs, b1_coeffs, b2_coeffs, b3_coeffs)

       Returns
       -------
       a1_coeffs, a2_coeffs, a3_coeffs, b1_coeffs, b2_coeffs, b3_coeffs: arrays of message exchange timestamps
    """

    if len(coeffs) % 6 != 0:
        raise Exception("Tri-Message contains partial exchange, unsafe to use it for computations.")

    # Timing coefficients
    step: int = 6  # each tri-message exchange contains 6 timestamps, 3 from server and 3 from device
    stop: int = int(len(coeffs) / 6) * step

    a1_coeffs: np.ndarray = coeffs[0: stop: step]  # server first transmit timestamps in epoch microseconds
    a2_coeffs: np.ndarray = coeffs[1: stop: step]  # server first receive timestamps in epoch microseconds
    a3_coeffs: np.ndarray = coeffs[2: stop: step]  # server second transmit timestamps in epoch microseconds
    b1_coeffs: np.ndarray = coeffs[3: stop: step]  # device first receive timestamps in mach microseconds
    b2_coeffs: np.ndarray = coeffs[4: stop: step]  # device first transmit timestamps in mach microseconds
    b3_coeffs: np.ndarray = coeffs[5: stop: step]  # device second receive timestamps in mach microseconds

    # make sure each tri-message exchange contains 6 timestamps (done with modulo check above)
    # assert len(a1_coeffs) == len(a2_coeffs) == len(a3_coeffs) == len(b1_coeffs) == len(b2_coeffs) == len(b3_coeffs)

    return a1_coeffs, a2_coeffs, a3_coeffs, b1_coeffs, b2_coeffs, b3_coeffs
