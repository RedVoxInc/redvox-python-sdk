"""
This module provides a high level API for creating, reading, and editing RedVox compliant API 1000 files.
"""

from datetime import datetime, timedelta
import os.path
from functools import total_ordering
from typing import Optional, List

# noinspection PyPackageRequirements
from google.protobuf import json_format
import lz4.frame

from redvox.api1000.common.common import check_type
import redvox.api1000.common.typing
import redvox.api1000.errors as errors
import redvox.api1000.wrapped_redvox_packet.sensors.sensors as _sensors
import redvox.api1000.wrapped_redvox_packet.station_information as _station_information
import redvox.api1000.wrapped_redvox_packet.timing_information as _timing_information
import redvox.common.date_time_utils as dt_utils

from redvox.api1000.common.generic import ProtoBase, ProtoRepeatedMessage
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.api1000.wrapped_redvox_packet.event_streams import EventStream


@total_ordering
class WrappedRedvoxPacketM(ProtoBase[RedvoxPacketM]):
    """
    Wraps a RedVox API M protobuf buffer.
    """

    def __init__(self, redvox_proto: RedvoxPacketM):
        super().__init__(redvox_proto)

        self._station_information: _station_information.StationInformation = (
            _station_information.StationInformation(redvox_proto.station_information)
        )

        self._timing_information: _timing_information.TimingInformation = (
            _timing_information.TimingInformation(redvox_proto.timing_information)
        )

        self._sensors: _sensors.Sensors = _sensors.Sensors(redvox_proto.sensors)

        self._event_streams: ProtoRepeatedMessage = ProtoRepeatedMessage(
            redvox_proto,
            redvox_proto.event_streams,
            "event_streams",
            EventStream,
            lambda event_stream: event_stream.get_proto(),
        )

    # Implement methods required for total_ordering
    def __eq__(self, other) -> bool:
        """
        Tests if this packet is equal in time to another packet by comparing start mach timestamps.
        :param other: Other packet to compare against
        :return: True if the packets mach timestamps match, False otherwise
        """
        self_ts: float = self.get_timing_information().get_packet_start_mach_timestamp()
        other_ts: float = (
            other.get_timing_information().get_packet_start_mach_timestamp()
        )
        return self_ts == other_ts

    def __lt__(self, other: "WrappedRedvoxPacketM") -> bool:
        """
        Checks if this packet is less than another packet by comparing start mach times.
        :param other: Other packet to compare against.
        :return: True if this packet is less than the other packet
        """
        self_ts: float = self.get_timing_information().get_packet_start_mach_timestamp()
        other_ts: float = (
            other.get_timing_information().get_packet_start_mach_timestamp()
        )
        return self_ts < other_ts

    @staticmethod
    def new() -> "WrappedRedvoxPacketM":
        """
        Returns a new default instance of a WrappedRedvoxPacketApi1000.
        :return: A new default instance of a WrappedRedvoxPacketApi1000.
        """
        return WrappedRedvoxPacketM(RedvoxPacketM())

    @staticmethod
    def from_compressed_bytes(data: bytes) -> "WrappedRedvoxPacketM":
        """
        Deserializes the byte content of an API M encoded .rdvxz file.
        :param data: The compressed bytes to deserialize.
        :return: An instance of a WrappedRedvoxPacketAPi1000.
        """
        redvox.api1000.common.typing.check_type(data, [bytes])
        proto: RedvoxPacketM = RedvoxPacketM()
        proto.ParseFromString(lz4.frame.decompress(data, False))
        return WrappedRedvoxPacketM(proto)

    @staticmethod
    def from_compressed_path(rdvxm_path: str) -> "WrappedRedvoxPacketM":
        """
        Deserialize an API M encoded .rdvxm file from the specified file system path.
        :param rdvxm_path: Path to the API M encoded file.
        :return: An instance of a WrappedRedvoxPacketApiM.
        """
        redvox.api1000.common.typing.check_type(rdvxm_path, [str])

        if not os.path.isfile(rdvxm_path):
            raise errors.WrappedRedvoxPacketMError(
                f"Path to file={rdvxm_path} does not exist."
            )

        with lz4.frame.open(rdvxm_path, "rb") as serialized_in:
            proto: RedvoxPacketM = RedvoxPacketM()
            proto.ParseFromString(serialized_in.read())
            return WrappedRedvoxPacketM(proto)

    @staticmethod
    def from_json(json_str: str) -> "WrappedRedvoxPacketM":
        """
        read json packet representing an API 1000 packet
        :param json_str: contains the json representing the packet
        :return: An instance of a WrappedRedvoxPacketM
        """
        return WrappedRedvoxPacketM(json_format.Parse(json_str, RedvoxPacketM()))

    @staticmethod
    def from_json_path(json_path: str) -> "WrappedRedvoxPacketM":
        """
        read json from a file representing an api 1000 packet
        :param json_path: the path to the file to read
        :return: wrapped redvox packet api 1000
        """
        with open(json_path, "r") as json_in:
            return WrappedRedvoxPacketM.from_json(json_in.read())

    def default_filename(self, extension: Optional[str] = "rdvxm") -> str:
        """
        Returns the default filename for a given packet.
        :param extension: An (optional) file extension to add to the default file name.
        :return: The default filename for this packet.
        """
        # Format to be exactly 10 characters
        station_id: str = f"{self.get_station_information().get_id():0>10}"
        timestamp: int = round(
            self.get_timing_information().get_packet_start_mach_timestamp()
        )
        filename: str = f"{station_id}_{timestamp}"

        if extension is not None:
            filename = f"{filename}.{extension}"

        return filename

    def default_file_dir(self) -> str:
        """
        Computes the default file directory structure for a structured layout for this particular packet.
        :return:  Directory structure for this packet when using structured layout
        """
        timestamp: float = (
            self.get_timing_information().get_packet_start_mach_timestamp()
        )
        date_time: datetime = dt_utils.datetime_from_epoch_microseconds_utc(timestamp)
        year: str = f"{date_time.year:0>4}"
        month: str = f"{date_time.month:0>2}"
        day: str = f"{date_time.day:0>2}"
        hour: str = f"{date_time.hour:0>2}"
        return os.path.join(year, month, day, hour)

    def default_file_path(self) -> str:
        """
        Computes the default directory structure and file name for this packet for structured layouts.
        :return: The default directory structure and file name for this packet for structured layouts.
        """
        return os.path.join(self.default_file_dir(), self.default_filename())

    def write_compressed_to_file(
        self, base_dir: str, filename: Optional[str] = None
    ) -> str:
        """
        Writes this packet to a .rdvxm file.
        :param base_dir: Directory to write .rdvxm to.
        :param filename: The (optional) file name to use. Will use default file name otherwise.
        :return: Path of written file.
        """
        if filename is None:
            filename = self.default_filename("rdvxm")

        if not os.path.isdir(base_dir):
            raise errors.WrappedRedvoxPacketMError(
                f"Base directory={base_dir} does not exist."
            )

        out_path: str = os.path.join(base_dir, filename)
        with open(out_path, "wb") as compressed_out:
            compressed_out.write(self.as_compressed_bytes())

        return out_path

    def write_json_to_file(self, base_dir: str, filename: Optional[str] = None) -> str:
        """
        Writes this packet to a .json file.
        :param base_dir: Directory to write .json to.
        :param filename: The (optional) file name to use. Will use default file name otherwise.
        :return: Path of written file.
        """
        if filename is None:
            filename = self.default_filename("json")

        if not os.path.isdir(base_dir):
            raise errors.WrappedRedvoxPacketMError(
                f"Base directory={base_dir} does not exist."
            )

        out_path: str = os.path.join(base_dir, filename)
        with open(out_path, "w") as json_out:
            json_out.write(self.as_json())

        return out_path

    def validate(self) -> List[str]:
        """
        Validates this packet.
        :return: A list of validation errors.
        """
        return validate_wrapped_packet(self)

    # Top-level packet fields
    def get_api(self) -> float:
        """
        Returns the API version of this packet.
        :return: The API version of this packet.
        """
        return self._proto.api

    def set_api(self, api: float) -> "WrappedRedvoxPacketM":
        """
        Sets the api version of this packet.
        :param api: The API version (should be 1000.0)
        :return: The modified instance of this packet
        """
        redvox.api1000.common.typing.check_type(api, [int, float])
        self._proto.api = api
        return self

    def get_sub_api(self) -> float:
        """
        Returns the sub_api version. This version tracks small changes within API 1000.
        :return: The sub_api version. This version tracks small changes within API 1000.
        """
        return self._proto.sub_api

    def set_sub_api(self, sub_api: float) -> "WrappedRedvoxPacketM":
        """
        Sets the sub_api.
        :param sub_api: sub_api to set.
        :return: A modified instance of self.
        """
        redvox.api1000.common.typing.check_type(sub_api, [int, float])
        self._proto.sub_api = sub_api
        return self

    def get_station_information(self) -> _station_information.StationInformation:
        """
        :return: An instance of StationInformation
        """
        return self._station_information

    def set_station_information(
        self, station_information: _station_information.StationInformation
    ) -> "WrappedRedvoxPacketM":
        """
        Sets the StationInformation.
        :param station_information: StationInformation to set.
        :return: A modified instance of self.
        """
        check_type(station_information, [_station_information.StationInformation])
        self.get_proto().station_information.CopyFrom(station_information.get_proto())
        self._station_information = _station_information.StationInformation(
            self.get_proto().station_information
        )
        return self

    def get_timing_information(self) -> _timing_information.TimingInformation:
        """
        :return: An instance of TimingInformation
        """
        return self._timing_information

    def set_timing_information(
        self, timing_information: _timing_information.TimingInformation
    ) -> "WrappedRedvoxPacketM":
        """
        Sets the timing information.
        :param timing_information: TimingInformation to set.
        :return: A modified instance of self.
        """
        check_type(timing_information, [_timing_information.TimingInformation])
        self.get_proto().timing_information.CopyFrom(timing_information.get_proto())
        self._timing_information = _timing_information.TimingInformation(
            self.get_proto().timing_information
        )
        return self

    def get_sensors(self) -> _sensors.Sensors:
        """
        :return: An instance of Sensors
        """
        return self._sensors

    def set_sensors(self, sensors: _sensors.Sensors) -> "WrappedRedvoxPacketM":
        """
        Sets the sensors.
        :param sensors: Sensors to set.
        :return: A modified instance of self.
        """
        check_type(sensors, [_sensors.Sensors])
        self.get_proto().sensors.CopyFrom(sensors.get_proto())
        self._sensors = _sensors.Sensors(self.get_proto().sensors)
        return self

    def get_event_streams(self) -> ProtoRepeatedMessage:
        """
        :return: A collection of event streams.
        """
        return self._event_streams

    def set_event_streams(
        self, event_streams: ProtoRepeatedMessage
    ) -> "WrappedRedvoxPacketM":
        """
        Set the event streams from the provided ProtoRepeatedMessage.
        :param event_streams: EventStreams embedded in a ProtoRepeatedMessage.
        :return: A modified instance of self.
        """
        check_type(event_streams, [ProtoRepeatedMessage])
        self._event_streams.clear_values()
        self._event_streams.append_values(event_streams.get_values())
        return self

    # todo: add packet_duration calculations that don't rely on sensors existing if possible

    def get_packet_duration(self) -> timedelta:
        """
        :return: Packet duration as a timedelta
        """
        audio = self.get_sensors().get_audio()
        if audio is not None:
            return audio.get_duration()
        else:
            return timedelta(seconds=0)

    def get_packet_duration_s(self) -> float:
        """
        get the packet duration in seconds from the audio data
        :return: packet duration in seconds
        """
        if self.get_sensors().has_audio():
            return self.get_sensors().get_audio().get_duration_s()
        else:
            return 0.0

    def update_timestamps(self, delta_offset: float = None) -> "WrappedRedvoxPacketM":
        """
        update all timestamps in the packet by adding the delta offset
        :param delta_offset: amount of microseconds to add to existing timestamps
        :return: WrappedRedvoxPacketM with updated timestamps
        """
        if delta_offset is None:
            delta_offset = self.get_timing_information().get_best_offset()
        redvox.api1000.common.typing.check_type(delta_offset, [float])
        # create new wrapped packet to hold changed data
        updated = WrappedRedvoxPacketM(self.get_proto())
        if self.get_proto().HasField("timing_information"):
            # update timing information timestamps
            updated.get_timing_information().set_packet_start_mach_timestamp(
                self.get_timing_information().get_packet_start_mach_timestamp()
                + delta_offset
            )
            updated.get_timing_information().set_packet_end_mach_timestamp(
                self.get_timing_information().get_packet_end_mach_timestamp()
                + delta_offset
            )
            updated.get_timing_information().set_packet_start_os_timestamp(
                self.get_timing_information().get_packet_start_os_timestamp()
                + delta_offset
            )
            updated.get_timing_information().set_packet_end_os_timestamp(
                self.get_timing_information().get_packet_end_os_timestamp()
                + delta_offset
            )
            updated.get_timing_information().set_app_start_mach_timestamp(
                self.get_timing_information().get_app_start_mach_timestamp()
                + delta_offset
            )
        if self.get_sensors().get_proto().HasField("audio"):
            # update audio first sample timestamp
            updated.get_sensors().get_audio().set_first_sample_timestamp(
                self.get_sensors().get_audio().get_first_sample_timestamp()
                + delta_offset
            )
        # todo if self.get_sensors().get_proto().HasField("compressed_audio"):
        # update compressed audio first sample timestamp
        # update timestamp payloads
        if (
            self.get_station_information()
            .get_station_metrics()
            .get_proto()
            .HasField("timestamps")
        ):
            updated.get_station_information().get_station_metrics().get_timestamps().set_timestamps(
                self.get_station_information()
                .get_station_metrics()
                .get_timestamps()
                .get_timestamps()
                + delta_offset,
                True,
            )
        if self.get_sensors().get_accelerometer().get_proto().HasField("timestamps"):
            updated.get_sensors().get_accelerometer().get_timestamps().set_timestamps(
                self.get_sensors().get_accelerometer().get_timestamps().get_timestamps()
                + delta_offset,
                True,
            )
        if (
            self.get_sensors()
            .get_ambient_temperature()
            .get_proto()
            .HasField("timestamps")
        ):
            updated.get_sensors().get_ambient_temperature().get_timestamps().set_timestamps(
                self.get_sensors()
                .get_ambient_temperature()
                .get_timestamps()
                .get_timestamps()
                + delta_offset,
                True,
            )
        if self.get_sensors().get_gravity().get_proto().HasField("timestamps"):
            updated.get_sensors().get_gravity().get_timestamps().set_timestamps(
                self.get_sensors().get_gravity().get_timestamps().get_timestamps()
                + delta_offset,
                True,
            )
        if self.get_sensors().get_gyroscope().get_proto().HasField("timestamps"):
            updated.get_sensors().get_gyroscope().get_timestamps().set_timestamps(
                self.get_sensors().get_gyroscope().get_timestamps().get_timestamps()
                + delta_offset,
                True,
            )
        if self.get_sensors().get_image().get_proto().HasField("timestamps"):
            updated.get_sensors().get_image().get_timestamps().set_timestamps(
                self.get_sensors().get_image().get_timestamps().get_timestamps()
                + delta_offset,
                True,
            )
        if self.get_sensors().get_light().get_proto().HasField("timestamps"):
            updated.get_sensors().get_light().get_timestamps().set_timestamps(
                self.get_sensors().get_light().get_timestamps().get_timestamps()
                + delta_offset,
                True,
            )
        if (
            self.get_sensors()
            .get_linear_acceleration()
            .get_proto()
            .HasField("timestamps")
        ):
            updated.get_sensors().get_linear_acceleration().get_timestamps().set_timestamps(
                self.get_sensors()
                .get_linear_acceleration()
                .get_timestamps()
                .get_timestamps()
                + delta_offset,
                True,
            )
        if self.get_sensors().get_location().get_proto().HasField("timestamps"):
            updated.get_sensors().get_location().get_timestamps().set_timestamps(
                self.get_sensors().get_location().get_timestamps().get_timestamps()
                + delta_offset,
                True,
            )
        if self.get_sensors().get_magnetometer().get_proto().HasField("timestamps"):
            updated.get_sensors().get_magnetometer().get_timestamps().set_timestamps(
                self.get_sensors().get_magnetometer().get_timestamps().get_timestamps()
                + delta_offset,
                True,
            )
        if self.get_sensors().get_orientation().get_proto().HasField("timestamps"):
            updated.get_sensors().get_orientation().get_timestamps().set_timestamps(
                self.get_sensors().get_orientation().get_timestamps().get_timestamps()
                + delta_offset,
                True,
            )
        if self.get_sensors().get_pressure().get_proto().HasField("timestamps"):
            updated.get_sensors().get_pressure().get_timestamps().set_timestamps(
                self.get_sensors().get_pressure().get_timestamps().get_timestamps()
                + delta_offset,
                True,
            )
        if self.get_sensors().get_proximity().get_proto().HasField("timestamps"):
            updated.get_sensors().get_proximity().get_timestamps().set_timestamps(
                self.get_sensors().get_proximity().get_timestamps().get_timestamps()
                + delta_offset,
                True,
            )
        if (
            self.get_sensors()
            .get_relative_humidity()
            .get_proto()
            .HasField("timestamps")
        ):
            updated.get_sensors().get_relative_humidity().get_timestamps().set_timestamps(
                self.get_sensors()
                .get_relative_humidity()
                .get_timestamps()
                .get_timestamps()
                + delta_offset,
                True,
            )
        if self.get_sensors().get_rotation_vector().get_proto().HasField("timestamps"):
            updated.get_sensors().get_rotation_vector().get_timestamps().set_timestamps(
                self.get_sensors()
                .get_rotation_vector()
                .get_timestamps()
                .get_timestamps()
                + delta_offset,
                True,
            )
        return updated


def validate_wrapped_packet(wrapped_packet: WrappedRedvoxPacketM) -> List[str]:
    """
    Validates a wrapped packet.
    :param wrapped_packet: Packet to validate.
    :return: A list of validation errors.
    """
    errors_list = _station_information.validate_station_information(
        wrapped_packet.get_station_information()
    )
    errors_list.extend(
        _timing_information.validate_timing_information(
            wrapped_packet.get_timing_information()
        )
    )
    errors_list.extend(_sensors.validate_sensors(wrapped_packet.get_sensors()))
    if wrapped_packet.get_api() != 1000:
        errors_list.append("Wrapped packet api is not 1000")
    return errors_list
