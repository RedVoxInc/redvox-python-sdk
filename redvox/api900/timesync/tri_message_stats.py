"""
Modules for extracting time synchronization statistics according to Tri-Message protocol. All functions assume
payload for ONE data packet/decoder ONLY. These modules will be called separately by API800 and API900 loaders, they
are in themselves helper functions. They do not depend on API formats, they take the time sync payloads as parameters
and use Tri-Message protocol to compute latencies, check criteria, and correct the "machine" start time B0 based on the
minimum latencies.
"""

from typing import Tuple, Union

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
        self.latency1, self.latency3 = latencies(a1, a2, a3, b1, b2, b3)
        self.offset1, self.offset3 = offsets(a1, a2, a3, b1, b2, b3)

        self.best_latency = None
        self.best_latency_array_index = None
        self.best_latency_index = None
        self.best_offset = None

        self.find_best_latency()
        self.find_best_offset()

    def find_best_latency(self):
        """
        Finds the best latency among the latencies
        """
        # initialize
        self.best_latency = None

        # find value and index of minimum latency of nonzero latencies
        d1_min = np.min(self.latency1[self.latency1 != 0])
        d3_min = np.min(self.latency3[self.latency3 != 0])

        if d3_min > d1_min:
            self.best_latency = d1_min  # server round trip is shorter
            self.best_latency_array_index = 1
            self.best_latency_index = np.where(self.latency1 == d1_min)[0][0]
        else:
            self.best_latency = d3_min
            self.best_latency_array_index = 3
            self.best_latency_index = np.where(self.latency3 == d3_min)[0][0]

    def find_best_offset(self):
        """
        Finds the best offset among the offsets
        """

        # if no best latency, find it
        if self.best_latency is None:
            self.find_best_latency()
        # best latency = best offset
        if self.best_latency_array_index == 1:
            self.best_offset = self.offset1[self.best_latency_index]
        elif self.best_latency_array_index == 3:
            self.best_offset = self.offset3[self.best_latency_index]
        else:
            self.best_offset = None

    def set_latency(self,
                    a1: np.ndarray,
                    a2: np.ndarray,
                    a3: np.ndarray,
                    b1: np.ndarray,
                    b2: np.ndarray,
                    b3: np.ndarray):
        """
        set the latency and find the best
        :param a1: server timestamp 1
        :param a2: server timestamp 2
        :param a3: server timestamp 3
        :param b1: device timestamp 1
        :param b2: device timestamp 2
        :param b3: device timestamp 3
        """
        # compute latencies
        self.latency1, self.latency3 = latencies(a1, a2, a3, b1, b2, b3)
        self.find_best_latency()

    def set_offset(self,
                   a1: np.ndarray,
                   a2: np.ndarray,
                   a3: np.ndarray,
                   b1: np.ndarray,
                   b2: np.ndarray,
                   b3: np.ndarray):
        """
        set the offset and find the best
        :param a1: server timestamp 1
        :param a2: server timestamp 2
        :param a3: server timestamp 3
        :param b1: device timestamp 1
        :param b2: device timestamp 2
        :param b3: device timestamp 3
        """
        # latency calculations are required:
        if self.best_latency is None:
            self.set_latency(a1, a2, a3, b1, b2, b3)
        # compute offsets
        self.offset1, self.offset3 = offsets(a1, a2, a3, b1, b2, b3)
        self.find_best_offset()


def latencies(a1: np.ndarray,
              a2: np.ndarray,
              a3: np.ndarray,
              b1: np.ndarray,
              b2: np.ndarray,
              b3: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute latencies in microseconds based on message exchange timestamps.

    Parameters
    ----------
    a1, ... b3: tri-message timestamps as loaded in transmit_receive_timestamps_microsec

    Returns
    -------
    d1: array of server round trip latencies in microseconds
    d3: array of device round trip latencies in microseconds
    """
    # Compute latencies in microseconds
    d1: np.ndarray = 0.5 * ((a2 - a1) - (b2 - b1))
    d3: np.ndarray = 0.5 * ((b3 - b2) - (a3 - a2))

    # convert negative latencies to 0.  negative latencies should not exist naturally
    d1[d1 < 0] = 0
    d3[d3 < 0] = 0

    return d1, d3


def offsets(a1: np.ndarray, a2: np.ndarray, a3: np.ndarray, b1: np.ndarray, b2: np.ndarray, b3: np.ndarray) -> Tuple[
        np.ndarray, np.ndarray]:
    """
    Compute offsets in microseconds based on message exchange timestamps.

    Parameters
    ----------
    a1, ... b3: tri-message timestamps as loaded in transmit_receive_timestamps_microsec

    Returns
    -------
    o1: array of server round trip latencies in microseconds
    o3: array of device round trip latencies in microseconds
    """
    # assume the generic equation f = a - b + d
    # where d is latency, f is offset, b is machine time and a is time sync server time
    # refer to latency equations above for definitions of d1 and d3
    # with latency d1, the equation is f1 = a1 - b1 + d1
    # with latency d3, the equation is f3 = a3 - b3 + d3
    # In the absence of latency, offset can be calculated this way:
    # o1 = (a1 - b1 + a2 - b2) / 2.
    # o3 = (a3 - b3 + a2 - b2) / 2.
    # get latencies
    latencies_tuple: Tuple[np.ndarray, np.ndarray] = latencies(a1, a2, a3, b1, b2, b3)
    d1: np.ndarray = latencies_tuple[0]
    d3: np.ndarray = latencies_tuple[1]
    # use latency to compute offset in microseconds
    o1: np.ndarray = a1 - b1 + d1
    o3: np.ndarray = a3 - b3 + d3

    return o1, o3


def transmit_receive_timestamps_microsec(coeffs: np.ndarray) -> Tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
       Recover Tri-Message timestamp coefficients. Uses concept of
       Tri-Message to synchronize a device with a reference server:

           First, server A transmits a message to device B with timestamp a1. B receives the message at timestamp b1. B
           then transmits a message back to A with timestamp b2. A receives this message at timestamp a2. A transmits a
           second message to B at timestamp a3. B receives the message at timestamp b3.

       Parameters
       ----------
       coeffs: array of tri-message coefficients (a1, a2, a3, b1, b2, b3)

       Returns
       -------
       a1, a2, a3, b1, b2, b3: arrays of message exchange timestamps
    """

    if len(coeffs) % 6 != 0:
        raise Exception("Tri-Message contains partial exchange, unsafe to use it for computations.")

    # Timing coefficients
    step: int = 6  # each tri-message exchange contains 6 timestamps, 3 from server and 3 from device
    stop: int = int(len(coeffs) / 6) * step

    a1: np.ndarray = coeffs[0: stop: step]  # server first transmit timestamps in epoch microseconds
    a2: np.ndarray = coeffs[1: stop: step]  # server first receive timestamps in epoch microseconds
    a3: np.ndarray = coeffs[2: stop: step]  # server second transmit timestamps in epoch microseconds
    b1: np.ndarray = coeffs[3: stop: step]  # device first receive timestamps in mach microseconds
    b2: np.ndarray = coeffs[4: stop: step]  # device first transmit timestamps in mach microseconds
    b3: np.ndarray = coeffs[5: stop: step]  # device second receive timestamps in mach microseconds

    # make sure each tri-message exchange contains 6 timestamps (done with modulo check above)
    # assert len(a1) == len(a2) == len(a3) == len(b1) == len(b2) == len(b3)

    return a1, a2, a3, b1, b2, b3
