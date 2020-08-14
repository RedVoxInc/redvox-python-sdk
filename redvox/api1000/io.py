"""
This module contains functions for reading and writing bulk API M data.
"""
import os
import glob
import redvox.api1000.common.lz4
import redvox.api1000.wrapped_redvox_packet.wrapped_packet as api_m_wp
import redvox.common.date_time_utils as date_time_utils
from typing import List, Optional, Set, Tuple


REDVOX_API_M_FILE_EXT = "rdvxm"


# todo: separate ReadWrappedPackets into multiple objects when gap detected
class ReadWrappedPackets:
    """
    A searchable/sortable list of continuous wrapped API M redvox packets
    A set of API M packets are continuous if:
        * their redvox ids are equal
        * their uuids are equal
        * their app start machine timestamps are equal
        * their sample rate is constant
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
            self.sort_packets()

    def sort_packets(self):
        """
        sort packets by packet_start_timestamp
        """
        sorted(self.wrapped_packets, key=lambda p: p.get_timing_information().get_packet_start_mach_timestamp())

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
            self.sort_packets()
            return True
        return False

    def validate_sensors(self, wrapped_packet: api_m_wp.WrappedRedvoxPacketM) -> bool:
        """
        Checks for difference between sensors of the wrapped_packet and the ReadWrappedPacket
        :param wrapped_packet: packet to check for differences
        :return: True if no change in any sensors, False otherwise
        """
        matches = []
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
            matches.append(prev_sensors == next_sensors)
        return all(matches)

    def identify_gaps(self, allowed_timing_error_s: float, debug: bool = False) -> List[int]:
        """
        Identifies discontinuities in sensor data by checking if sensors drop in and out and by comparing timing info.
        :param allowed_timing_error_s: The amount of timing error in seconds.
        :param debug: if True, output information as function is running, default False
        :return: A list of indices into the original list where gaps were found.
        """
        if len(self.wrapped_packets) <= 1:
            return []

        gaps = set()

        for i in range(1, len(self.wrapped_packets)):
            prev_packet = self.wrapped_packets[i - 1]
            next_packet = self.wrapped_packets[i]

            # so sensors should have been checked already

            # Sensor discontinuity
            # prev_sensors = [prev_packet.get_sensors().has_audio(),
            #                 prev_packet.get_sensors().has_pressure(),
            #                 prev_packet.get_sensors().has_accelerometer(),
            #                 prev_packet.get_sensors().has_gyroscope(),
            #                 prev_packet.get_sensors().has_light(),
            #                 prev_packet.get_sensors().has_image(),
            #                 prev_packet.get_sensors().has_location(),
            #                 prev_packet.get_sensors().has_magnetometer(),
            #                 prev_packet.get_sensors().has_ambient_temperature(),
            #                 prev_packet.get_sensors().has_compress_audio(),
            #                 prev_packet.get_sensors().has_gravity(),
            #                 prev_packet.get_sensors().has_linear_acceleration(),
            #                 prev_packet.get_sensors().has_orientation(),
            #                 prev_packet.get_sensors().has_proximity(),
            #                 prev_packet.get_sensors().has_relative_humidity(),
            #                 prev_packet.get_sensors().has_rotation_vector()]
            #
            # next_sensors = [next_packet.get_sensors().has_audio(),
            #                 next_packet.get_sensors().has_pressure(),
            #                 next_packet.get_sensors().has_accelerometer(),
            #                 next_packet.get_sensors().has_gyroscope(),
            #                 next_packet.get_sensors().has_light(),
            #                 next_packet.get_sensors().has_image(),
            #                 next_packet.get_sensors().has_location(),
            #                 next_packet.get_sensors().has_magnetometer(),
            #                 next_packet.get_sensors().has_ambient_temperature(),
            #                 next_packet.get_sensors().has_compress_audio(),
            #                 next_packet.get_sensors().has_gravity(),
            #                 next_packet.get_sensors().has_linear_acceleration(),
            #                 next_packet.get_sensors().has_orientation(),
            #                 next_packet.get_sensors().has_proximity(),
            #                 next_packet.get_sensors().has_relative_humidity(),
            #                 next_packet.get_sensors().has_rotation_vector()]
            #
            # # pylint: disable=C0200
            # for j in range(len(prev_sensors)):
            #     if prev_sensors[j] != next_sensors[j]:
            #         gaps.add(i)

            # so the only check that shouldn't have been made yet is difference in start/end timestamps
            # Time based gaps
            prev_timestamp = prev_packet.get_timing_information().get_packet_end_mach_timestamp()
            next_timestamp = next_packet.get_timing_information().get_packet_start_mach_timestamp()
            if debug:
                print(next_timestamp - prev_timestamp)
            # timestamps of audio data should be close together
            if date_time_utils.microseconds_to_seconds(next_timestamp - prev_timestamp) > allowed_timing_error_s:
                gaps.add(i)
                if debug:
                    print("time gap")

            # so the mach start time should have been checked already

            # app start time should not change
            # prev_app_start_mach = prev_packet.get_timing_information().get_app_start_mach_timestamp()
            # next_app_start_mach = next_packet.get_timing_information().get_app_start_mach_timestamp()
            # if next_app_start_mach != prev_app_start_mach:
            #     gaps.add(i)
            #     if debug:
            #         print("mach time zero gap")

        return sorted(list(gaps))


class ReadResult:
    """
    Results from reading a directory containing API M redvox data
    properties:
        start_timestamp_s: optional float, start timestamp in seconds of the data being read
        end_timestamp_s: optional float, end timestamp in seconds of the data being read
        all_wrapped_packets: list of lists of wrapped API M redvox packets
    """
    def __init__(self, start_time: float = None, end_time: float = None,
                 wrapped_packets: List[ReadWrappedPackets] = None):
        """
        initialize a ReadResult
        :param start_time: start time of the data being read, default None
        :param end_time: end time of the data being read, default None
        :param wrapped_packets: list of lists of wrapped API M packets containing all the data, default None
        """
        self.start_timestamp_s: Optional[float] = start_time
        self.end_timestamp_s: Optional[float] = end_time
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


def _extract_timestamp(path: str) -> int:
    """
    Extracts a timestamp in microseconds from a file path.
    :param path: Path to extract a timestamp from.
    :return: The timestamp in seconds from a path.
    """
    file = path.split(os.path.sep)[-1].split(".")[0]
    return int(file.split("_")[1])


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
                    start_timestamp_utc: int,
                    end_timestamp_utc: int,
                    redvox_ids: Set[str] = None) -> bool:
    """
    Determines whether a given path is in a provided time range and set of redvox_ids.
    :param path: The path to check.
    :param start_timestamp_utc: Start of time range in microseconds since epoch UTC.
    :param end_timestamp_utc: End of time range in microseconds since epoch UTC.
    :param redvox_ids: Optional set of redvox ids.
    :return: True if path is in set false otherwise.
    """
    if redvox_ids is None:
        redvox_ids = set()
    filename = path.split(os.sep)[-1]

    if not _is_valid_redvox_api_m_filename(filename):
        return False

    timestamp = int(filename[11:27])

    if not start_timestamp_utc <= timestamp <= end_timestamp_utc:
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
                          start_timestamp_utc: int,
                          end_timestamp_utc: int,
                          redvox_ids: Set[str] = None) -> List[str]:
    """
    Given a base directory (which should end with api1000), find the paths of all structured API M redvox files.
    :param directory: The base directory path (which should end with api1000)
    :param start_timestamp_utc: Start timestamp as microseconds since the epoch UTC.
    :param end_timestamp_utc: End timestamp as microseconds since the epoch UTC.
    :param redvox_ids: An optional set of redvox_ids to filter against.
    :return: A list of paths in a structured layout of filtered API M redvox files.
    """
    if redvox_ids is None:
        redvox_ids = set()
    paths = []
    for (year, month, day, hour) in date_time_utils.DateIteratorAPIM(start_timestamp_utc, end_timestamp_utc):
        all_paths = glob.glob(os.path.join(directory, year, month, day, hour, f"*.{REDVOX_API_M_FILE_EXT}"))
        valid_paths = list(
            filter(lambda path: _is_path_in_set(path, start_timestamp_utc, end_timestamp_utc, redvox_ids),
                   all_paths))
        paths.extend(valid_paths)
    return paths


def read_structured(directory: str,
                    start_timestamp_utc: Optional[int] = None,
                    end_timestamp_utc: Optional[int] = None,
                    redvox_ids: Optional[List[str]] = None,
                    structured_layout: bool = True) -> ReadResult:
    """
    read API M data from a directory that contains a specific structure (directory/YYYY/MM/DD/HH)
    Timestamps in directory and parameters are in UNIX time UTC
    :param directory: the root directory that contains the data
    :param start_timestamp_utc: starting timestamp to get data from.  if None, get all data, default None
    :param end_timestamp_utc: ending timestamp to get data from.  if None, get all data, default None
    :param redvox_ids: specific redvox ids to get data for.  if None, get all ids, default None
    :param structured_layout: specifies if directory has specific structure, default True
    :return: a ReadResult object that stores the packets with metadata
    """
    # Remove trailing directory separators
    if redvox_ids is None:
        redvox_ids = []
    while directory.endswith("/") or directory.endswith("\\"):
        directory = directory[:-1]

    if start_timestamp_utc is None or end_timestamp_utc is None:
        ids = None if len(redvox_ids) == 0 else redvox_ids
        start_adjusted, end_adjusted = _get_paths_time_range(directory, ids, True)

        if start_timestamp_utc is None:
            start_timestamp_utc = start_adjusted

        if end_timestamp_utc is None:
            end_timestamp_utc = end_adjusted

    if structured_layout:
        paths = _get_structured_paths(directory,
                                      start_timestamp_utc,
                                      end_timestamp_utc,
                                      set(redvox_ids))
    else:
        all_paths = glob.glob(os.path.join(directory, f"*.{REDVOX_API_M_FILE_EXT}"))
        paths = list(
            filter(lambda pth: _is_path_in_set(pth, start_timestamp_utc, end_timestamp_utc, set(redvox_ids)),
                   all_paths))

    read_result = ReadResult(start_timestamp_utc, end_timestamp_utc)

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
