"""
This module contains methods and classes for identifying gaps in RedVox data.
"""

from typing import List

# import redvox.api900.concat as concat
# import redvox.api900.reader as reader
import redvox.common.date_time_utils as date_time_utils


class GapResult:
    """
    This class encapsulates the results of performing gap detection.
    """

    def __init__(self,
                 index: int,
                 description: str) -> None:
        """
        Creates a new GapResult.
        :param index: The index of the gap.
        :param description: A description of the gap.
        """
        self.index = index
        self.description = description

    def __str__(self):
        return f"{self.index}:{self.description}"


def _packet_len_s(wrapped_redvox_packet) -> float:
    """
    Returns the length of a packet in seconds.
    :param wrapped_redvox_packet: Packet to find the length of.
    :return: The length of a packet in seconds.
    """
    microphone_sensor = wrapped_redvox_packet.microphone_sensor()
    return len(microphone_sensor.payload_values()) / microphone_sensor.sample_rate_hz()


def identify_time_gaps(wrapped_redvox_packets: List,
                       allowed_timing_error_s: float = 5.0) -> List[GapResult]:
    """
    Identifies time gaps between wrapped packets.
    :param wrapped_redvox_packets: Packets to check for a gaps.
    :param allowed_timing_error_s: The amount of time in seconds that are provided for timing error.
    :return: A list of GapResults.
    """

    gaps: List[GapResult] = []

    if len(wrapped_redvox_packets) <= 1:
        return gaps

    packet_len_s: float = _packet_len_s(wrapped_redvox_packets[0])
    allowed_gap_s: float = packet_len_s + allowed_timing_error_s

    for i in range(1, len(wrapped_redvox_packets)):
        prev_packet = wrapped_redvox_packets[i - 1]
        next_packet = wrapped_redvox_packets[i]

        prev_timestamp = prev_packet.microphone_sensor().first_sample_timestamp_epoch_microseconds_utc()
        next_timestamp = next_packet.microphone_sensor().first_sample_timestamp_epoch_microseconds_utc()
        time_diff_us: int = next_timestamp - prev_timestamp
        time_diff_s: float = date_time_utils.microseconds_to_seconds(time_diff_us)

        if time_diff_s > allowed_gap_s:
            description: str = f"Time gap. Expected packet length s={packet_len_s}. " \
                               f"Allowed timing error s={allowed_timing_error_s}. " \
                               f"Allowed gap s={allowed_gap_s}. " \
                               f"Actual time gap s={time_diff_s}"
            gaps.append(GapResult(i, description))

            packet_len_s = _packet_len_s(wrapped_redvox_packets[i])
            allowed_gap_s = packet_len_s + allowed_timing_error_s

    return gaps
