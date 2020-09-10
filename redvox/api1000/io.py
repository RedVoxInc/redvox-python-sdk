"""
This module contains functions for reading and writing bulk API M data.
"""
import os
import glob
import redvox.api1000.common.lz4
import numpy as np
import redvox.api1000.wrapped_redvox_packet.wrapped_packet as api_m_wp
import redvox.common.date_time_utils as date_time_utils
from typing import List, Optional, Set, Tuple, Callable, TypeVar


REDVOX_API_M_FILE_EXT = "rdvxm"


def calc_evenly_sampled_timestamps(start: float, samples: int, rate_hz: float) -> np.array:
    """
    given a start time, calculates samples amount of evenly spaced timestamps at rate_hz
    :param start: float, start timestamp
    :param samples: int, number of samples
    :param rate_hz: float, sample rate in hz
    :return: np.array with evenly spaced timestamps starting at start
    """
    return np.array(start + date_time_utils.seconds_to_microseconds(np.arange(0, samples) / rate_hz))


# todo: stream inputs and read multiple buffers
class ReadWrappedPackets:
    """
    A searchable/sortable list of continuous wrapped API M redvox packets
    A set of API M packets are continuous if:
        * their redvox ids are equal
        * their uuids are equal
        * their app start machine timestamps are equal
        * their sample rate is constant
        * their sensors do not change
        * there is no considerable gap between the end of one packet and the start of the next
    properties:
        wrapped_packets: list of wrapped redvox API M packets
        redvox_id: string, redvox id of all the packets
        uuid: string, uuid of all the packets
        start_mach_timestamp: float, app_start_mach_timestamp of all the packets
        audio_sample_rate: float, sample rate of the audio sensor
    """
    def __init__(self, wrapped_packets: List[api_m_wp.WrappedRedvoxPacketM]):
        """
        initialize ReadWrappedPackets
        :param wrapped_packets: the packets to add; must be continuous
        """
        # set the values used to check continuity
        self.redvox_id: str = wrapped_packets[0].get_station_information().get_id()
        self.uuid: str = wrapped_packets[0].get_station_information().get_uuid()
        self.start_mach_timestamp: float = wrapped_packets[0].get_timing_information().get_app_start_mach_timestamp()
        self.audio_sample_rate: float = wrapped_packets[0].get_sensors().get_audio().get_sample_rate()
        # set the packets
        self.wrapped_packets: List[api_m_wp.WrappedRedvoxPacketM] = wrapped_packets
        if len(wrapped_packets) > 1:
            self.wrapped_packets = self.sort_packets()

    @staticmethod
    def _default_sort_packets(packet: api_m_wp.WrappedRedvoxPacketM):
        return packet.get_timing_information().get_packet_start_mach_timestamp()

    # this is for below to allow custom criteria to sort on
    T = TypeVar("T")

    def sort_packets(self, sort_func: Optional[Callable[[api_m_wp.WrappedRedvoxPacketM], T]] = None,
                     reverse: bool = False) -> List[api_m_wp.WrappedRedvoxPacketM]:
        """
        sort packets by custom user function, or by default, packet_start_timestamp
        :param sort_func: Optional function defining how to sort the packets, default None (uses packet start mach time)
        :param reverse: bool, if True, sort results in reverse, default False
        :return: the sorted list of packets
        """
        if sort_func is None:
            sort_func = self._default_sort_packets
        return sorted(self.wrapped_packets, key=sort_func, reverse=reverse)

    def add_packet(self, wrapped_packet: api_m_wp.WrappedRedvoxPacketM) -> bool:
        """
        Adds the wrapped packet to the list if it is from the same device
        :param wrapped_packet: packet to potentially add to list
        :return: True if successful, False otherwise
        """
        if wrapped_packet.get_station_information().get_id() == self.redvox_id \
                and wrapped_packet.get_station_information().get_uuid() == self.uuid \
                and wrapped_packet.get_timing_information().get_app_start_mach_timestamp() == self.start_mach_timestamp\
                and self.validate_sensors(wrapped_packet):
            self.wrapped_packets.append(wrapped_packet)
            self.wrapped_packets = self.sort_packets()
            return True
        return False

    def validate_sensors(self, wrapped_packet: api_m_wp.WrappedRedvoxPacketM) -> bool:
        """
        Checks for difference between sensors of the wrapped_packet and the ReadWrappedPacket
        :param wrapped_packet: packet to check for differences
        :return: True if no change in any sensors, False otherwise
        """
        # only 1 packet means sensors don't change
        if len(self.wrapped_packets) <= 1:
            return True
        prev_sensors = [wrapped_packet.get_sensors().has_audio(),
                        wrapped_packet.get_sensors().has_pressure(),
                        wrapped_packet.get_sensors().has_accelerometer(),
                        wrapped_packet.get_sensors().has_gyroscope(),
                        wrapped_packet.get_sensors().has_light(),
                        wrapped_packet.get_sensors().has_image(),
                        wrapped_packet.get_sensors().has_location(),
                        wrapped_packet.get_sensors().has_magnetometer(),
                        wrapped_packet.get_sensors().has_ambient_temperature(),
                        wrapped_packet.get_sensors().has_compress_audio(),
                        wrapped_packet.get_sensors().has_gravity(),
                        wrapped_packet.get_sensors().has_linear_acceleration(),
                        wrapped_packet.get_sensors().has_orientation(),
                        wrapped_packet.get_sensors().has_proximity(),
                        wrapped_packet.get_sensors().has_relative_humidity(),
                        wrapped_packet.get_sensors().has_rotation_vector()]
        for packet in self.wrapped_packets:
            next_sensors = [packet.get_sensors().has_audio(),
                            packet.get_sensors().has_pressure(),
                            packet.get_sensors().has_accelerometer(),
                            packet.get_sensors().has_gyroscope(),
                            packet.get_sensors().has_light(),
                            packet.get_sensors().has_image(),
                            packet.get_sensors().has_location(),
                            packet.get_sensors().has_magnetometer(),
                            packet.get_sensors().has_ambient_temperature(),
                            packet.get_sensors().has_compress_audio(),
                            packet.get_sensors().has_gravity(),
                            packet.get_sensors().has_linear_acceleration(),
                            packet.get_sensors().has_orientation(),
                            packet.get_sensors().has_proximity(),
                            packet.get_sensors().has_relative_humidity(),
                            packet.get_sensors().has_rotation_vector()]
            if prev_sensors != next_sensors:
                return False
        # if here, all sensors match
        return True

    def identify_gaps(self, allowed_timing_error_s: float, debug: bool = False) -> List[int]:
        """
        Identifies discontinuities in sensor data by checking if sensors drop in and out and by comparing timing info.
        :param allowed_timing_error_s: float, the amount of timing error in seconds.
        :param debug: bool, if True, output information as function is running, default False
        :return: A list of indices into the original list where gaps were found.
        """
        if len(self.wrapped_packets) <= 1:
            return []

        gaps = set()

        for i in range(1, len(self.wrapped_packets)):
            prev_packet = self.wrapped_packets[i - 1]
            next_packet = self.wrapped_packets[i]

            prev_timestamp = prev_packet.get_timing_information().get_packet_end_mach_timestamp()
            next_timestamp = next_packet.get_timing_information().get_packet_start_mach_timestamp()
            if debug:
                print(next_timestamp - prev_timestamp)
            # timestamps of audio data should be close together
            if date_time_utils.microseconds_to_seconds(next_timestamp - prev_timestamp) > allowed_timing_error_s:
                gaps.add(i)
                if debug:
                    print("time gap")

        return sorted(list(gaps))


class ReadResult:
    """
    Results from reading a directory containing API M redvox data
    properties:
        start_timestamp: optional float, start timestamp in microseconds of the data being read
        end_timestamp: optional float, end timestamp in microseconds of the data being read
        all_wrapped_packets: list of lists of wrapped API M redvox packets
    """
    def __init__(self, start_time: Optional[float] = None, end_time: Optional[float] = None,
                 wrapped_packets: Optional[List[ReadWrappedPackets]] = None):
        """
        initialize a ReadResult
        :param start_time: start time of the data being read, default None
        :param end_time: end time of the data being read, default None
        :param wrapped_packets: list of lists of wrapped API M packets containing all the data, default None
        """
        self.start_timestamp: Optional[float] = start_time
        self.end_timestamp: Optional[float] = end_time
        if wrapped_packets is None:
            self.all_wrapped_packets = []
        else:
            self.all_wrapped_packets = wrapped_packets

    def add_result(self, wrapped_packets: ReadWrappedPackets):
        """
        adds a ReadWrappedPackets object to the ReadResult
        :param wrapped_packets: a ReadWrappedPackets object
        """
        self.all_wrapped_packets.append(wrapped_packets)

    def add_packet(self, wrapped_packet: api_m_wp.WrappedRedvoxPacketM):
        """
        adds a single wrapped API M redvox packet to the ensemble
        :param wrapped_packet: a single wrapped API M redvox packet
        """
        for packets in self.all_wrapped_packets:
            if packets.add_packet(wrapped_packet):
                # packet got added, stop function
                return
        # went through for loop and nothing got added, so we assume it's a new id to add
        self.all_wrapped_packets.append(ReadWrappedPackets([wrapped_packet]))

    def add_list_of_packets(self, wrapped_packets: List[api_m_wp.WrappedRedvoxPacketM]):
        """
        adds a list of WrappedRedvoxPacketM files to the ReadResult
        :param wrapped_packets: the list of wrapped API M redvox packets to add
        """
        for packet in wrapped_packets:
            self.add_packet(packet)
        end_result = self.reorganize_packets()
        self.all_wrapped_packets = end_result.all_wrapped_packets

    def identify_gaps(self, timing_gap_s: float = 5.0) -> 'ReadResult':
        """
        checks all_wrapped_packets for any time gaps and splits them into continuous objects
        returns a copy of the calling object if no gaps detected
        :param timing_gap_s: amount of seconds allowed between packets to be considered a gap
        :return: an updated ReadResult object
        """
        updated_result = ReadResult(self.start_timestamp, self.end_timestamp)
        for packets in self.all_wrapped_packets:
            gaps = packets.identify_gaps(timing_gap_s)
            start = 0
            for index in gaps:
                split_val = ReadWrappedPackets(packets.wrapped_packets[start:index])
                updated_result.all_wrapped_packets.append(split_val)
                start = index
            # do this one last time to get the rest of the data that wasn't split yet
            split_val = ReadWrappedPackets(packets.wrapped_packets[start:])
            updated_result.all_wrapped_packets.append(split_val)
        return updated_result

    def reorganize_packets(self, timing_gap_s: float = 5.0) -> 'ReadResult':
        """
        takes all_wrapped_packets and recreates the ReadResult object
        :param timing_gap_s: amount of seconds allowed between packets to be considered a gap
        :return: an updated ReadResult object
        """
        updated_result = ReadResult(self.start_timestamp, self.end_timestamp)
        for packets in self.all_wrapped_packets:
            for packet in packets.wrapped_packets:
                updated_result.add_packet(packet)
        return updated_result.identify_gaps(timing_gap_s)

    def get_by_id(self, redvox_id: str) -> List[api_m_wp.WrappedRedvoxPacketM]:
        """
        gets all the packets with the id specified
        :param redvox_id: the redvox id to return values for
        :return: list of API M redvox packets with the redvox_id specified
        """
        results: List[api_m_wp.WrappedRedvoxPacketM] = []
        for packets in self.all_wrapped_packets:
            if packets.redvox_id == redvox_id:
                results.extend(packets.wrapped_packets)
        return results


class StreamResult:
    pass


def wrap(redvox_packet: api_m_wp.RedvoxPacketM) -> api_m_wp.WrappedRedvoxPacketM:
    """
    Wraps a protobuf packet in a WrappedRedocPacket.
    :param redvox_packet: Protobuf packet to wrap.
    :return: A WrappedRedvoxPacket.
    """
    return api_m_wp.WrappedRedvoxPacketM(redvox_packet)


def read_buffer(buf: bytes, is_compressed: bool = True) -> api_m_wp.RedvoxPacketM:
    """
    Deserializes a serialized protobuf RedvoxPacket buffer.
    :param buf: Buffer to deserialize.
    :param is_compressed: Whether or not the buffer is compressed or decompressed.
    :return: Deserialized protobuf redvox packet.
    """
    buffer = redvox.api1000.common.lz4.decompress(buf) if is_compressed else buf
    redvox_packet = api_m_wp.RedvoxPacketM()
    redvox_packet.ParseFromString(buffer)
    return redvox_packet


def read_file(file: str, is_compressed: bool = None) -> api_m_wp.RedvoxPacketM:
    """
    Deserializes a serialized protobuf RedvoxPacketM file.
    :param file: File to deserialize.
    :param is_compressed: Whether or not the file is compressed or decompressed.
    :return: Deserialized protobuf API M redvox packet.
    """
    file_ext = file.split(".")[-1]

    if is_compressed is None:
        _is_compressed = True if file_ext == REDVOX_API_M_FILE_EXT else False
    else:
        _is_compressed = is_compressed
    with open(file, "rb") as fin:
        return read_buffer(fin.read(), _is_compressed)


def read_rdvxm_file(path: str) -> api_m_wp.WrappedRedvoxPacketM:
    """
    Reads a .rdvxm file from the specified path and returns a WrappedRedvoxPacketM.
    :param path: The path of the file.
    :return: A WrappedRedvoxPacketM.
    """
    return wrap(read_file(path))


def read_rdvxm_buffer(buf: bytes) -> api_m_wp.WrappedRedvoxPacketM:
    """
    reads a .rdvxm file from the provided buffer and returns a WrappedRedvoxPacketM
    :param buf: buffer of bytes to read
    :return: A WrappedRedvoxPacketM
    """
    return wrap(read_buffer(buf))


def _extract_timestamp(path: str) -> int:
    """
    Extracts a timestamp in microseconds from a file path.
    :param path: Path to extract a timestamp from.
    :return: The timestamp in seconds from a path.
    """
    file = path.split(os.path.sep)[-1].split(".")[0]
    return int(date_time_utils.microseconds_to_seconds(int(file.split("_")[1])))


def _extract_redvox_id(path: str) -> str:
    """
    Extracts a redvox id from a file path.
    :param path: A path to extract the id from.
    :return: The redvox id.
    """
    file = path.split(os.path.sep)[-1]
    return file.split("_")[0]


def _is_int(int_as_str: str) -> bool:
    """
    Returns true if the given string can be parsed as an int.
    :param int_as_str: String to test.
    :return: True if it is an int, False otherwise.
    """
    try:
        int(int_as_str)
        return True
    except ValueError:
        return False


def _is_valid_redvox_api_m_filename(filename: str) -> bool:
    """
    Given a filename, determine if the filename is a valid API M redvox file name.
    :param filename: Filename to test.
    :return: True if it is valid, false otherwise.
    """
    return len(filename) == 33 and _is_int(filename[0:10]) \
        and filename[10:11] == "_" and _is_int(filename[11:27]) \
        and filename[27:len(filename)] == f".{REDVOX_API_M_FILE_EXT}"


def _is_path_in_set(path: str,
                    start_timestamp_utc_s: int,
                    end_timestamp_utc_s: int,
                    redvox_ids: Set[str] = None) -> bool:
    """
    Determines whether a given path is in a provided time range and set of redvox_ids.
    :param path: The path to check.
    :param start_timestamp_utc_s: Start of time range in seconds since epoch UTC.
    :param end_timestamp_utc_s: End of time range in seconds since epoch UTC.
    :param redvox_ids: Optional set of redvox ids.
    :return: True if path is in set false otherwise.
    """
    if redvox_ids is None:
        redvox_ids = set()
    filename = path.split(os.sep)[-1]

    if not _is_valid_redvox_api_m_filename(filename):
        return False

    timestamp = int(date_time_utils.microseconds_to_seconds(float(filename[11:27])))

    if not start_timestamp_utc_s <= timestamp <= end_timestamp_utc_s:
        return False

    if len(redvox_ids) > 0:
        if len(redvox_ids) > 0:
            redvox_id = filename[0:10]
            if redvox_id not in redvox_ids:
                return False

    return True


def _get_time_range_paths(paths: List[str],
                          redvox_ids: Optional[Set[str]]) -> Tuple[int, int]:
    """
    Given a set of paths, get the start and end timestamps.
    :param paths: Paths to get time range from.
    :param redvox_ids: Redvox ids to filter on.
    :return: A tuple containing the start and end timestamps of the data range.
    """
    if redvox_ids is not None:
        paths = list(filter(lambda path: _extract_redvox_id(path) in redvox_ids, paths))

    if len(paths) == 0:
        return -1, -1

    if len(paths) == 1:
        timestamp = _extract_timestamp(paths[0])
        return timestamp, timestamp

    timestamps = sorted(list(map(_extract_timestamp, paths)))
    return timestamps[0], timestamps[-1]


def _get_paths_time_range(directory: str,
                          redvox_ids: Optional[Set[str]],
                          recursive: bool) -> Tuple[int, int]:
    """
    Gets the start and end time range of a given set of API M data.
    :param directory: The base directory of the data.
    :param redvox_ids: Redvox ids to filter on.
    :param recursive: Whether or not to perform a recursive search.
    :return: A tuple containing the start and end timestamps of the given data set.
    """
    if recursive:
        all_paths = glob.glob(os.path.join(directory, "**", f"*.{REDVOX_API_M_FILE_EXT}"),
                              recursive=recursive)
    else:
        all_paths = glob.glob(os.path.join(directory, f"*.{REDVOX_API_M_FILE_EXT}"),
                              recursive=recursive)

    return _get_time_range_paths(all_paths, redvox_ids)


def _get_structured_paths(directory: str,
                          start_timestamp_utc_s: int,
                          end_timestamp_utc_s: int,
                          redvox_ids: Set[str] = None) -> List[str]:
    """
    Given a base directory (which should end with api1000), find the paths of all structured API M redvox files.
    :param directory: The base directory path (which should end with api1000)
    :param start_timestamp_utc_s: Start timestamp as seconds since the epoch UTC.
    :param end_timestamp_utc_s: End timestamp as seconds since the epoch UTC.
    :param redvox_ids: An optional set of redvox_ids to filter against.
    :return: A list of paths in a structured layout of filtered API M redvox files.
    """
    if redvox_ids is None:
        redvox_ids = set()
    paths = []
    for (year, month, day, hour) in date_time_utils.DateIteratorAPIM(start_timestamp_utc_s, end_timestamp_utc_s):
        all_paths = glob.glob(os.path.join(directory, year, month, day, hour, f"*.{REDVOX_API_M_FILE_EXT}"))
        valid_paths = list(
            filter(lambda path: _is_path_in_set(path, start_timestamp_utc_s, end_timestamp_utc_s, redvox_ids),
                   all_paths))
        paths.extend(valid_paths)
    return paths


def read_structured(directory: str,
                    start_timestamp_utc_s: Optional[int] = None,
                    end_timestamp_utc_s: Optional[int] = None,
                    redvox_ids: Optional[List[str]] = None,
                    structured_layout: bool = True) -> ReadResult:
    """
    read API M data from a directory that contains a specific structure (directory/YYYY/MM/DD/HH)
    Timestamps in directory are in microseconds since epoch UTC
    :param directory: the root directory that contains the data
    :param start_timestamp_utc_s: starting timestamp in seconds since epoch UTC.  if None, get all data, default None
    :param end_timestamp_utc_s: ending timestamp in seconds since epoch UTC.  if None, get all data, default None
    :param redvox_ids: specific redvox ids to get data for.  if None, get all ids, default None
    :param structured_layout: specifies if directory has specific structure, default True
    :return: a ReadResult object that stores the packets with metadata
    """
    # Remove trailing directory separators
    if redvox_ids is None:
        redvox_ids = []
    while directory.endswith("/") or directory.endswith("\\"):
        directory = directory[:-1]

    if start_timestamp_utc_s is None or end_timestamp_utc_s is None:
        ids = None if len(redvox_ids) == 0 else redvox_ids
        start_adjusted, end_adjusted = _get_paths_time_range(directory, ids, structured_layout)

        if start_timestamp_utc_s is None:
            start_timestamp_utc_s = start_adjusted

        if end_timestamp_utc_s is None:
            end_timestamp_utc_s = end_adjusted

    if structured_layout:
        paths = _get_structured_paths(directory,
                                      start_timestamp_utc_s,
                                      end_timestamp_utc_s,
                                      set(redvox_ids))
    else:
        all_paths = glob.glob(os.path.join(directory, f"*.{REDVOX_API_M_FILE_EXT}"))
        paths = list(
            filter(lambda pth: _is_path_in_set(pth, start_timestamp_utc_s, end_timestamp_utc_s, set(redvox_ids)),
                   all_paths))

    read_result = ReadResult(start_timestamp_utc_s, end_timestamp_utc_s)

    for path in paths:
        read_result.add_packet(read_rdvxm_file(path))

    return read_result


def read_dir(directory_path: str) -> ReadResult:
    """
    read API M data from a single directory of unsorted API M redvox data
    :param directory_path: the directory path that contains all the data
    :return: the data as a ReadResult
    """
    # Make sure the directory ends with a trailing slash "/"
    if directory_path[-1] != "/":
        directory_path = directory_path + "/"

    read_result = ReadResult()

    file_paths = sorted(glob.glob(directory_path + f"*.{REDVOX_API_M_FILE_EXT}"))

    for path in file_paths:
        read_result.add_packet(read_rdvxm_file(path))

    return read_result


def stream_structured():
    pass


def stream_dir():
    pass


def read_buffers():
    pass
