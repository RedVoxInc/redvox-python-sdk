"""
This module contains classes and methods for working with WrappedRedvoxPackets
"""

import json
import os
import typing

import redvox.api900.date_time_utils as date_time_utils
import redvox.api900.exceptions as exceptions
import redvox.api900.lib.api900_pb2 as api900_pb2
import redvox.api900.reader
import redvox.api900.reader_utils as reader_utils
import redvox.api900.sensors.microphone_sensor as microphone_sensor
import redvox.api900.sensors.barometer_sensor as barometer_sensor
import redvox.api900.sensors.time_synchronization_sensor as time_synchronization_sensor
import redvox.api900.sensors.location_sensor as location_sensor
import redvox.api900.sensors.accelerometer_sensor as accelerometer_sensor
import redvox.api900.sensors.gyroscope_sensor as gyroscope_sensor
import redvox.api900.sensors.magnetometer_sensor as magnetometer_sensor
import redvox.api900.sensors.light_sensor as light_sensor
import redvox.api900.sensors.infrared_sensor as infrared_sensor
import redvox.api900.sensors.image_sensor as image_sensor

from redvox.api900.sensors.evenly_sampled_channel import EvenlySampledChannel
from redvox.api900.sensors.unevenly_sampled_channel import UnevenlySampledChannel


class WrappedRedvoxPacketSummary:
    def __init__(self, wrapped_redvox_packet: 'WrappedRedvoxPacket'):
        microphone_channel = wrapped_redvox_packet.microphone_channel()
        self.start_time_us = wrapped_redvox_packet.app_file_start_timestamp_machine()
        self.end_time_us = self.start_time_us + date_time_utils.seconds_to_microseconds(
            len(microphone_channel.payload_values()) / microphone_channel.sample_rate_hz())
        self.duration_us = self.end_time_us - self.start_time_us
        self.mic_sample_rate_hz = microphone_channel.sample_rate_hz()
        self.has_microphone_sensor = wrapped_redvox_packet.has_microphone_channel()
        self.microphone_sensor_len = self._get_num_samples(wrapped_redvox_packet,
                                                           WrappedRedvoxPacket.microphone_channel,
                                                           microphone_sensor.MicrophoneSensor.payload_values)
        self.has_barometer_sensor = wrapped_redvox_packet.has_barometer_channel()
        self.barometer_sensor_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.barometer_channel,
                                                          barometer_sensor.BarometerSensor.payload_values)
        self.has_time_synchronization_sensor = wrapped_redvox_packet.has_time_synchronization_channel()
        self.time_synchronization_len = self._get_num_samples(wrapped_redvox_packet,
                                                              WrappedRedvoxPacket.time_synchronization_channel,
                                                              time_synchronization_sensor.TimeSynchronizationSensor.payload_values)
        self.has_location_sensor = wrapped_redvox_packet.has_location_channel()
        self.location_sensor_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.location_channel,
                                                         location_sensor.LocationSensor.payload_values_latitude)
        self.has_accelerometer_sensor = wrapped_redvox_packet.has_accelerometer_channel()
        self.accelerometer_sensor_len = self._get_num_samples(wrapped_redvox_packet,
                                                              WrappedRedvoxPacket.accelerometer_channel,
                                                              accelerometer_sensor.AccelerometerSensor.payload_values_x)
        self.has_gyroscope_sensor = wrapped_redvox_packet.has_gyroscope_channel()
        self.gyroscope_sensor_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.gyroscope_channel,
                                                          gyroscope_sensor.GyroscopeSensor.payload_values_x)
        self.has_magnetometer_sensor = wrapped_redvox_packet.has_magnetometer_channel()
        self.magnetometer_sensor_len = self._get_num_samples(wrapped_redvox_packet,
                                                             WrappedRedvoxPacket.magnetometer_channel,
                                                             magnetometer_sensor.MagnetometerSensor.payload_values_x)
        self.has_light_sensor = wrapped_redvox_packet.has_light_channel()
        self.light_sensor_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.light_channel,
                                                      light_sensor.LightSensor.payload_values)
        self.has_infrared_sensor = wrapped_redvox_packet.has_infrared_channel()
        self.infrared_sensor_len = self._get_num_samples(wrapped_redvox_packet, WrappedRedvoxPacket.infrared_channel,
                                                         infrared_sensor.InfraredSensor.payload_values)

    def _get_num_samples(self,
                         wrapped_redvox_packet: 'WrappedRedvoxPacket',
                         sensor_fn,
                         payload_fn):
        sensor = sensor_fn(wrapped_redvox_packet)
        if sensor is None:
            return 0
        else:
            return len(payload_fn(sensor))

    def __str__(self) -> str:
        return json.dumps(self.__dict__)


# pylint: disable=R0904
class WrappedRedvoxPacket:
    """
    This class provides convenience methods for accessing API 900 protobuf redvox packets.

    This packet contains a reference to the original packet which should be used to access all "top-level" fields. For
    accessing channels, this class can search for and return our high-level channel wrappers or can extract the payload
    directly.
    """

    def __init__(self, redvox_packet: api900_pb2.RedvoxPacket = None):
        """
        Initializes this wrapped redvox packet.
        :param redvox_packet: A protobuf redvox packet.
        """
        if redvox_packet is None:
            self._redvox_packet = api900_pb2.RedvoxPacket()
            self._evenly_sampled_channels = list()
            self._unevenly_sampled_channels = list()
            self._metadata_list = list()
            self._channel_cache = {}

        else:
            self._redvox_packet: api900_pb2.RedvoxPacket = redvox_packet
            """Protobuf api 900 redvox packet"""

            self._evenly_sampled_channels: typing.List[EvenlySampledChannel] = list(
                map(EvenlySampledChannel, reader_utils.repeated_to_array(redvox_packet.evenly_sampled_channels)))
            """List of evenly sampled channels"""

            self._unevenly_sampled_channels: typing.List[UnevenlySampledChannel] = list(
                map(UnevenlySampledChannel, reader_utils.repeated_to_array(redvox_packet.unevenly_sampled_channels)))
            """List of unevenly sampled channels"""

            self._metadata_list: typing.List[str] = reader_utils.repeated_to_list(redvox_packet.metadata)
            """List of metadata"""

            self._channel_cache: typing.Dict[int, typing.Union[EvenlySampledChannel, UnevenlySampledChannel]] = {}
            """Holds a mapping of channel type to channel for O(1) access."""

            # Initialize channel cache
            for evenly_sampled_channel in self._evenly_sampled_channels:
                for channel_type in evenly_sampled_channel.channel_types:
                    self._channel_cache[channel_type] = evenly_sampled_channel

            for unevenly_sampled_channel in self._unevenly_sampled_channels:
                for channel_type in unevenly_sampled_channel.channel_types:
                    self._channel_cache[channel_type] = unevenly_sampled_channel

    def redvox_packet(self) -> api900_pb2.RedvoxPacket:
        """
        returns the protobuf redvox packet
        :return: protobuf redvox packet
        """
        return self._redvox_packet

    def _evenly_sampled_channels(self) -> typing.List[EvenlySampledChannel]:
        """
        returns the evenly sampled channels as a copied list to avoid built in functions making untracked changes
        :return: list of evenly sampled channels
        """
        return self._evenly_sampled_channels.copy()

    def _unevenly_sampled_channels(self) -> typing.List[UnevenlySampledChannel]:
        """
        returns the unevenly sampled channels as a copied list to avoid built in functions making untracked changes
        :return: list of unevenly sampled channels
        """
        return self._unevenly_sampled_channels.copy()

    def _refresh_channels(self):
        """
        takes the redvox packet and rebuilds the channel cache from it
        """
        self._evenly_sampled_channels = list(map(EvenlySampledChannel,
                                                 reader_utils.repeated_to_array(
                                                     self._redvox_packet.evenly_sampled_channels)))
        self._unevenly_sampled_channels = list(map(UnevenlySampledChannel,
                                                   reader_utils.repeated_to_array(
                                                       self._redvox_packet.unevenly_sampled_channels)))
        self._channel_cache = {}
        for evenly_sampled_channel in self._evenly_sampled_channels:
            for channel_type in evenly_sampled_channel.channel_types:
                self._channel_cache[channel_type] = evenly_sampled_channel
        for unevenly_sampled_channel in self._unevenly_sampled_channels:
            for channel_type in unevenly_sampled_channel.channel_types:
                self._channel_cache[channel_type] = unevenly_sampled_channel

    def _add_channel(self, channel: typing.Union[EvenlySampledChannel, UnevenlySampledChannel]):
        """
        Add a channel
        :param channel: channel to add
        """
        index, sample = self._find_channel(channel.channel_types[0])
        if index is None and sample is None:
            if type(channel) not in [EvenlySampledChannel, UnevenlySampledChannel]:
                raise TypeError("Channel type to add must be even or uneven.")
            else:
                self._add_channel_redvox_packet(channel)
                self._refresh_channels()
        else:
            raise ValueError("Cannot add a channel with a type that already exists in this packet.")

    def _edit_channel(self, channel_type: int, channel: typing.Union[EvenlySampledChannel, UnevenlySampledChannel]):
        """
        removes the channel with the given type and adds the channel supplied
        :param channel_type: type of channel to remove
        :param channel: the channel to add
        """
        index, sampling = self._find_channel(channel_type)
        if index is not None and sampling is not None:
            if type(channel) == EvenlySampledChannel:
                del self._redvox_packet.evenly_sampled_channels[index]
                self._add_channel_redvox_packet(channel)
            elif type(channel) == UnevenlySampledChannel:
                del self._redvox_packet.unevenly_sampled_channels[index]
                self._add_channel_redvox_packet(channel)
            else:
                raise TypeError("Channel type to edit is unknown!")
            self._refresh_channels()
        else:
            raise TypeError("Unknown channel type specified for edit.")

    def _delete_channel(self, channel_type: int):
        """
        deletes the channel type specified
        :param channel_type: a channel to remove
        """
        index, sampling = self._find_channel(channel_type)
        if index is not None and sampling is not None:
            if sampling == EvenlySampledChannel:
                del self._redvox_packet.evenly_sampled_channels[index]
            else:
                del self._redvox_packet.unevenly_sampled_channels[index]
            self._refresh_channels()
        else:
            raise TypeError("Unknown channel type to remove from packet.")

    def _find_channel(self, channel_type: int) -> (int, typing.Union[EvenlySampledChannel, UnevenlySampledChannel]):
        """
        returns the index of the channel and the kind of sampled array its in
        :return: the index in the even or uneven array and the name of the array
        """
        if self._has_channel(channel_type):
            for idx in range(len(self._evenly_sampled_channels)):
                if channel_type in self._evenly_sampled_channels[idx].channel_types:
                    return idx, EvenlySampledChannel
            for idx in range(len(self._unevenly_sampled_channels)):
                if channel_type in self._unevenly_sampled_channels[idx].channel_types:
                    return idx, UnevenlySampledChannel
            else:
                return None, None
        else:
            return None, None

    def _add_channel_redvox_packet(self, channel: typing.Union[EvenlySampledChannel, UnevenlySampledChannel]):
        """
        adds the channel to the redvox_packet
        :param channel: channel to add
        """
        if type(channel) == EvenlySampledChannel:
            newchan = self._redvox_packet.evenly_sampled_channels.add()
            newchan.sample_rate_hz = channel.sample_rate_hz
            newchan.first_sample_timestamp_epoch_microseconds_utc = \
                channel.first_sample_timestamp_epoch_microseconds_utc
        elif type(channel) == UnevenlySampledChannel:
            newchan = self._redvox_packet.unevenly_sampled_channels.add()
            for time in channel.timestamps_microseconds_utc:
                newchan.timestamps_microseconds_utc.append(time)
            newchan.sample_interval_mean = channel.sample_interval_mean
            newchan.sample_interval_std = channel.sample_interval_std
            newchan.sample_interval_median = channel.sample_interval_median
        else:
            raise TypeError("Channel type to add to redvox packet is unknown!")

        pl_type = channel.get_payload_type()
        if pl_type == "byte_payload":
            newchan.byte_payload.payload.extend(channel.payload)
        elif pl_type == "uint32_payload":
            newchan.uint32_payload.payload.extend(channel.payload)
        elif pl_type == "uint64_payload":
            newchan.uint64_payload.payload.extend(channel.payload)
        elif pl_type == "int32_payload":
            newchan.int32_payload.payload.extend(channel.payload)
        elif pl_type == "int64_payload":
            newchan.int64_payload.payload.extend(channel.payload)
        elif pl_type == "float32_payload":
            newchan.float32_payload.payload.extend(channel.payload)
        elif pl_type == "float64_payload":
            newchan.float64_payload.payload.extend(channel.payload)
        elif pl_type is None:
            pass
        else:
            raise TypeError("Unknown payload type in channel to add.")

        for chan_type in channel.channel_types:
            newchan.channel_types.append(chan_type)
        newchan.sensor_name = channel.sensor_name
        for mean in channel.value_means:
            newchan.value_means.append(mean)
        for stds in channel.value_stds:
            newchan.value_stds.append(stds)
        for median in channel.value_medians:
            newchan.value_medians.append(median)
        for meta in channel.metadata:
            newchan.metadata.append(meta)

    def _get_channel_types(self) -> typing.List[typing.List[int]]:
        """
        Returns a list of channel type enumerations. This is a list of lists, and allows us to easily view
        interleaved channels.
        :return: A list of channel type enumerations.
        """
        channel_types = []
        for evenly_sampled_channel in self._evenly_sampled_channels:
            channel_types.append(evenly_sampled_channel.channel_types)

        for unevenly_sampled_channel in self._unevenly_sampled_channels:
            channel_types.append(unevenly_sampled_channel.channel_types)

        return channel_types

    def _get_channel_type_names(self) -> typing.List[typing.List[str]]:
        """
        Returns a list of channel type names. This is a list of lists, and allows us to easily view
        interleaved channels.
        :return: A list of channel type names. This is a list of lists, and allows us to easily view
        interleaved channels.
        """
        names = []
        for channel_types in self._get_channel_types():
            names.append(list(map(reader_utils.channel_type_name_from_enum, channel_types)))
        return names

    def _get_channel(self, channel_type: int) -> typing.Union[EvenlySampledChannel, UnevenlySampledChannel, None]:
        """
        Returns a channel from this packet according to the channel type.
        :param channel_type: The channel type to search for.
        :return: A high level channel wrapper or None.
        """
        if channel_type in self._channel_cache:
            return self._channel_cache[channel_type]

        return None

    def _has_channel(self, channel_type: int) -> bool:
        """
        Returns True if this packet contains a channel with this type otherwise False.
        :param channel_type: Channel type to search for.
        :return: True is this packet contains a channel with this type otherwise False.
        """
        return channel_type in self._channel_cache

    def _has_channels(self, channel_types: typing.List[int]) -> bool:
        """
        Checks that this packet contains all of the provided channels.
        :param channel_types: Channel types that this packet must contain.
        :return: True if this packet contains all provided channel types, False otherwise.
        """
        has_channel_results = map(self._has_channel, channel_types)
        for has_channel_result in has_channel_results:
            if not has_channel_result:
                return False
        return True

    def to_json(self) -> str:
        """
        Converts the protobuf packet stored in this wrapped packet to JSON.
        :return: The JSON representation of the protobuf encoded packet.
        """
        return reader_utils.to_json(self._redvox_packet)

    def compressed_buffer(self) -> bytes:
        """
        Returns the compressed buffer associated with this packet.
        :return: The compressed buffer associated with this packet.
        """
        return reader_utils.lz4_compress(self._redvox_packet.SerializeToString())

    def default_filename(self, extension: str = "rdvxz") -> str:
        """
        Constructs a default filename from the packet's metadata.
        :param extension: An optional extension to use.
        :return: A default filename from the packet's metadata.
        """
        return "%s_%d.%s" % (self.redvox_id(), int(round(self.app_file_start_timestamp_machine() / 1000.0)), extension)

    def write_rdvxz(self, directory: str, filename: typing.Optional[str] = None):
        """
        Writes a compressed .rdvxz file to the specified directory.
        :param directory: The directory to write the file to.
        :param filename: An optional filename (the default filename will be used if one is not provided).
        """
        filename = self.default_filename() if filename is None else filename
        path = os.path.join(directory, filename)
        with open(path, "wb") as rdvxz_out:
            rdvxz_out.write(self.compressed_buffer())

    def write_json(self, directory: str, filename: typing.Optional[str] = None):
        """
        Writes a RedVox compliant .json file to the specified directory.
        :param directory: The directory to write the file to.
        :param filename: An optional filename (the default filename will be used if one is not provided).
        """
        filename = self.default_filename(extension="json") if filename is None else filename
        path = os.path.join(directory, filename)
        with open(path, "w") as json_out:
            json_out.write(self.to_json())

    def clone(self) -> 'WrappedRedvoxPacket':
        """
        Returns a clone of this WrappedRedvoxPacket.
        :return: A clone of this WrappedRedvoxPacket.
        """
        return redvox.api900.reader.read_rdvxz_buffer(self.compressed_buffer())

    # Start of packet level API getters and setters
    def api(self) -> int:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.api

    def set_api(self, version: int) -> 'WrappedRedvoxPacket':
        """
        sets the api version number
        :param version: version number
        """
        self._redvox_packet.api = version
        return self

    def uuid(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.uuid

    def set_uuid(self, uid: str) -> 'WrappedRedvoxPacket':
        """
        sets the uuid
        :param uid: uuid string
        """
        self._redvox_packet.uuid = uid
        return self

    def redvox_id(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.redvox_id

    def set_redvox_id(self, rid: str) -> 'WrappedRedvoxPacket':
        """
        sets the redvox id
        :param rid: redvox id string
        """
        self._redvox_packet.redvox_id = rid
        return self

    def authenticated_email(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.authenticated_email

    def set_authenticated_email(self, email: str) -> 'WrappedRedvoxPacket':
        """
        sets the authenticated email
        :param email: authenticated email string
        """
        self._redvox_packet.authenticated_email = email
        return self

    def authentication_token(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.authentication_token

    def set_authentication_token(self, token: str) -> 'WrappedRedvoxPacket':
        """
        sets the authentication token
        :param token: authentication token string
        """
        self._redvox_packet.authentication_token = token
        return self

    def firebase_token(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.firebase_token

    def set_firebase_token(self, token: str) -> 'WrappedRedvoxPacket':
        """
        sets the firebase token
        :param token: firebase token string
        """
        self._redvox_packet.firebase_token = token
        return self

    def is_backfilled(self) -> bool:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.is_backfilled

    def set_is_backfilled(self, tof: bool) -> 'WrappedRedvoxPacket':
        """
        sets the is_backfilled flag
        :param tof: true or false
        """
        self._redvox_packet.is_backfilled = tof
        return self

    def is_private(self) -> bool:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.is_private

    def set_is_private(self, tof: bool) -> 'WrappedRedvoxPacket':
        """
        sets the is_private flag
        :param tof: true or false
        """
        self._redvox_packet.is_private = tof
        return self

    def is_scrambled(self) -> bool:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.is_scrambled

    def set_is_scrambled(self, tof: bool) -> 'WrappedRedvoxPacket':
        """
        sets the is_scrambled flag
        :param tof: true or false
        """
        self._redvox_packet.is_scrambled = tof
        return self

    def device_make(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.device_make

    def set_device_make(self, make: str) -> 'WrappedRedvoxPacket':
        """
        sets the make of the device
        :param make: make of the device string
        """
        self._redvox_packet.device_make = make
        return self

    def device_model(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.device_model

    def set_device_model(self, model: str) -> 'WrappedRedvoxPacket':
        """
        sets the model of the device
        :param model: model of the device string
        """
        self._redvox_packet.device_model = model
        return self

    def device_os(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.device_os

    def set_device_os(self, device_os: str) -> 'WrappedRedvoxPacket':
        """
        sets the device operating system
        :param device_os: operating system string
        """
        self._redvox_packet.device_os = device_os
        return self

    def device_os_version(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.device_os_version

    def set_device_os_version(self, version: str) -> 'WrappedRedvoxPacket':
        """
        sets the device OS version
        :param version: device OS version string
        """
        self._redvox_packet.device_os_version = version
        return self

    def app_version(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.app_version

    def set_app_version(self, version: str) -> 'WrappedRedvoxPacket':
        """
        sets the app version number
        :param version: app version string
        """
        self._redvox_packet.app_version = version
        return self

    def battery_level_percent(self) -> float:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.battery_level_percent

    def set_battery_level_percent(self, percent: float) -> 'WrappedRedvoxPacket':
        """
        sets the percentage of battery left
        :param percent: percentage of battery left
        """
        self._redvox_packet.battery_level_percent = percent
        return self

    def device_temperature_c(self) -> float:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.device_temperature_c

    def set_device_temperature_c(self, temp: float) -> 'WrappedRedvoxPacket':
        """
        sets the device temperature in degrees Celsius
        :param temp: temperature in degrees Celsius
        """
        self._redvox_packet.device_temperature_c = temp
        return self

    def acquisition_server(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.acquisition_server

    def set_acquisition_server(self, server: str) -> 'WrappedRedvoxPacket':
        """
        sets the acquisition server url
        :param server: url to acquisition server
        """
        self._redvox_packet.acquisition_server = server
        return self

    # pylint: disable=invalid-name
    def time_synchronization_server(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.time_synchronization_server

    def set_time_synchronization_server(self, server: str) -> 'WrappedRedvoxPacket':
        """
        sets the time synchronization server url
        :param server: url to time synchronization server
        """
        self._redvox_packet.time_synchronization_server = server
        return self

    def authentication_server(self) -> str:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.authentication_server

    def set_authentication_server(self, server: str) -> 'WrappedRedvoxPacket':
        """
        sets the authentication server url
        :param server: url to authentication server
        """
        self._redvox_packet.authentication_server = server
        return self

    # pylint: disable=invalid-name
    def app_file_start_timestamp_epoch_microseconds_utc(self) -> int:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.app_file_start_timestamp_epoch_microseconds_utc

    def set_app_file_start_timestamp_epoch_microseconds_utc(self, time: int) -> 'WrappedRedvoxPacket':
        """
        sets the timestamp of packet creation
        :param time: time when packet was created in microseconds since utc epoch
        """
        self._redvox_packet.app_file_start_timestamp_epoch_microseconds_utc = time
        return self

    # pylint: disable=invalid-name
    def app_file_start_timestamp_machine(self) -> int:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.app_file_start_timestamp_machine

    def set_app_file_start_timestamp_machine(self, time: int) -> 'WrappedRedvoxPacket':
        """
        sets the internal machine timestamp of packet creation
        :param time: time when packet was created on local machine
        """
        self._redvox_packet.app_file_start_timestamp_machine = time
        return self

    # pylint: disable=invalid-name
    def server_timestamp_epoch_microseconds_utc(self) -> int:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._redvox_packet.server_timestamp_epoch_microseconds_utc

    def set_server_timestamp_epoch_microseconds_utc(self, time: int) -> 'WrappedRedvoxPacket':
        """
        sets the server timestamp when the packet was received
        :param time: time when packet was received by server
        """
        self._redvox_packet.server_timestamp_epoch_microseconds_utc = time
        return self

    def metadata(self) -> typing.List[str]:
        """
        See https://bitbucket.org/redvoxhi/redvox-data-apis/src/master/src/api900/api900.proto?at=master for a
        description of this field.
        """
        return self._metadata_list

    def set_metadata(self, data: typing.List[str]) -> 'WrappedRedvoxPacket':
        """
        sets the metadata
        :param data: metadata as list of strings
        """
        self._metadata_list = data
        self._redvox_packet.metadata[:] = data
        return self

    def _clear_metadata(self):
        """
        removes all of the packet level metadata from packet
        """
        del self._redvox_packet.metadata[:]
        self._metadata_list.clear()

    def metadata_as_dict(self) -> typing.Dict[str, str]:
        """
        Return this packet's metadata as a key-value Python dictionary.
        :return: This packet's metadata as a key-value Python dictionary.
        """
        return reader_utils.get_metadata_as_dict(self._metadata_list)

    def set_metadata_as_dict(self, metadata_dict: typing.Dict[str, str]) -> 'WrappedRedvoxPacket':
        self.set_metadata(reader_utils.metadata_dict_to_list(metadata_dict))
        return self

    # Sensor channels
    def has_microphone_channel(self) -> bool:
        """
        Returns if this packet has a microphone channel.
        :return: If this packet has a microphone channel.
        """
        return self._has_channel(api900_pb2.MICROPHONE)

    def microphone_channel(self) -> typing.Optional[microphone_sensor.MicrophoneSensor]:
        """
        Returns the high-level microphone channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level microphone channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_microphone_channel():
            return microphone_sensor.MicrophoneSensor(self._get_channel(api900_pb2.MICROPHONE))

        return None

    def set_microphone_channel(self, microphone_sensor: typing.Optional[
        microphone_sensor.MicrophoneSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packets microphone sensor. A channel can be removed by passing in None.
        :param microphone_sensor: An optional instance of a microphone sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_microphone_channel():
            self._delete_channel(api900_pb2.MICROPHONE)

        if microphone_sensor is not None:
            self._add_channel(microphone_sensor._evenly_sampled_channel)

        return self

    def has_barometer_channel(self) -> bool:
        """
        Returns if this packet has a barometer channel.
        :return: If this packet has a barometer channel.
        """
        return self._has_channel(api900_pb2.BAROMETER)

    def barometer_channel(self) -> typing.Optional[barometer_sensor.BarometerSensor]:
        """
        Returns the high-level barometer channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level barometer channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_barometer_channel():
            return barometer_sensor.BarometerSensor(self._get_channel(api900_pb2.BAROMETER))

        return None

    def set_barometer_channel(self, barometer_sensor: typing.Optional[
        barometer_sensor.BarometerSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packets barometer sensor. A channel can be removed by passing in None.
        :param barometer_sensor: An optional instance of a barometer sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_barometer_channel():
            self._delete_channel(api900_pb2.BAROMETER)

        if barometer_sensor is not None:
            self._add_channel(barometer_sensor._unevenly_sampled_channel)

        return self

    def has_location_channel(self) -> bool:
        """
        Returns if this packet has a location channel.
        :return: If this packet has a location channel.
        """
        return (self._has_channels(
            [api900_pb2.LATITUDE, api900_pb2.LONGITUDE, api900_pb2.ALTITUDE, api900_pb2.SPEED,
             api900_pb2.ACCURACY]) or
                self._has_channels([api900_pb2.LATITUDE, api900_pb2.LONGITUDE]))

    def location_channel(self) -> typing.Optional[location_sensor.LocationSensor]:
        """
        Returns the high-level location channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level location channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_location_channel():
            return location_sensor.LocationSensor(self._get_channel(api900_pb2.LATITUDE))

        return None

    def set_location_channel(self,
                             location_sensor: typing.Optional[location_sensor.LocationSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's location sensor. A channel can be removed by passing in None.
        :param location_sensor: An optional instance of a location sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_location_channel():
            self._delete_channel(api900_pb2.LATITUDE)

        if location_sensor is not None:
            self._add_channel(location_sensor._unevenly_sampled_channel)

        return self

    # pylint: disable=invalid-name,C1801
    def has_time_synchronization_channel(self) -> bool:
        """
        Returns if this packet has a time synchronization channel.
        :return: If this packet has a time synchronization channel.
        """
        if self._has_channel(api900_pb2.TIME_SYNCHRONIZATION):
            ch = time_synchronization_sensor.TimeSynchronizationSensor(
                self._get_channel(api900_pb2.TIME_SYNCHRONIZATION))
            return len(ch.payload_values()) > 0

        return False

    def time_synchronization_channel(self) -> typing.Optional[time_synchronization_sensor.TimeSynchronizationSensor]:
        """
        Returns the high-level time synchronization channel API or None if this packet doesn't contain a channel of
        this type.
        :return: the high-level time synchronization channel API or None if this packet doesn't contain a channel of
        this type.
        """
        if self.has_time_synchronization_channel():
            return time_synchronization_sensor.TimeSynchronizationSensor(
                self._get_channel(api900_pb2.TIME_SYNCHRONIZATION))

        return None

    def set_time_synchronization_channel(self, time_synchronization_sensor: typing.Optional[
        time_synchronization_sensor.TimeSynchronizationSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's time sync sensor. A channel can be removed by passing in None.
        :param time_synchronization_sensor: An optional instance of a time sync sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_time_synchronization_channel():
            self._delete_channel(api900_pb2.TIME_SYNCHRONIZATION)

        if time_synchronization_sensor is not None:
            self._add_channel(time_synchronization_sensor._unevenly_sampled_channel)

        return self

    def has_accelerometer_channel(self) -> bool:
        """
        Returns if this packet has an accelerometer channel.
        :return: If this packet has an accelerometer channel.
        """
        return self._has_channels([api900_pb2.ACCELEROMETER_X, api900_pb2.ACCELEROMETER_Y, api900_pb2.ACCELEROMETER_Z])

    def accelerometer_channel(self) -> typing.Optional[accelerometer_sensor.AccelerometerSensor]:
        """
        Returns the high-level accelerometer channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level accelerometer channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_accelerometer_channel():
            return accelerometer_sensor.AccelerometerSensor(self._get_channel(api900_pb2.ACCELEROMETER_X))

        return None

    def set_accelerometer_channel(self,
                                  accelerometer_sensor: typing.Optional[
                                      accelerometer_sensor.AccelerometerSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's accelerometer sensor. A channel can be removed by passing in None.
        :param accelerometer_sensor: An optional instance of a accelerometer sensor.
        """
        if self.has_accelerometer_channel():
            self._delete_channel(api900_pb2.ACCELEROMETER_X)

        if accelerometer_sensor is not None:
            self._add_channel(accelerometer_sensor._unevenly_sampled_channel)

        return self

    def has_magnetometer_channel(self) -> bool:
        """
        Returns if this packet has a magnetometer channel.
        :return: If this packet has a magnetometer channel.
        """
        return self._has_channels([api900_pb2.MAGNETOMETER_X, api900_pb2.MAGNETOMETER_Y, api900_pb2.MAGNETOMETER_Z])

    def magnetometer_channel(self) -> typing.Optional[magnetometer_sensor.MagnetometerSensor]:
        """
        Returns the high-level magnetometer channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level magnetometer channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_magnetometer_channel():
            return magnetometer_sensor.MagnetometerSensor(self._get_channel(api900_pb2.MAGNETOMETER_X))

        return None

    def set_magnetometer_channel(self,
                                 magnetometer_sensor: typing.Optional[
                                     magnetometer_sensor.MagnetometerSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's magnetomer sensor. A channel can be removed by passing in None.
        :param magnetometer_sensor: An optional instance of a magnetometer sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_magnetometer_channel():
            self._delete_channel(api900_pb2.MAGNETOMETER_X)

        if magnetometer_sensor is not None:
            self._add_channel(magnetometer_sensor._unevenly_sampled_channel)

        return self

    def has_gyroscope_channel(self) -> bool:
        """
        Returns if this packet has a gyroscope channel.
        :return: If this packet has a gyroscope channel.
        """
        return self._has_channels([api900_pb2.GYROSCOPE_X, api900_pb2.GYROSCOPE_Y, api900_pb2.GYROSCOPE_Z])

    def gyroscope_channel(self) -> typing.Optional[gyroscope_sensor.GyroscopeSensor]:
        """
        Returns the high-level gyroscope channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level gyroscope channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_gyroscope_channel():
            return gyroscope_sensor.GyroscopeSensor(self._get_channel(api900_pb2.GYROSCOPE_X))

        return None

    def set_gyroscope_channel(self, gyroscope_sensor: typing.Optional[
        gyroscope_sensor.GyroscopeSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's gyroscope sensor. A channel can be removed by passing in None.
        :param gyroscope_sensor: An optional instance of a gyroscope sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_gyroscope_channel():
            self._delete_channel(api900_pb2.GYROSCOPE_X)

        if gyroscope_sensor is not None:
            self._add_channel(gyroscope_sensor._unevenly_sampled_channel)

        return self

    def has_light_channel(self) -> bool:
        """
        Returns if this packet has a light channel.
        :return: If this packet has a light channel.
        """
        return self._has_channel(api900_pb2.LIGHT)

    def light_channel(self) -> typing.Optional[light_sensor.LightSensor]:
        """
        Returns the high-level light channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level light channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_light_channel():
            return light_sensor.LightSensor(self._get_channel(api900_pb2.LIGHT))

        return None

    def set_light_channel(self, light_sensor: typing.Optional[light_sensor.LightSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's light sensor. A channel can be removed by passing in None.
        :param light_sensor: An optional instance of a light sensor.
        :return: This instance of a wrapped redvox packet.
        """
        if self.has_light_channel():
            self._delete_channel(api900_pb2.LIGHT)

        if light_sensor is not None:
            self._add_channel(light_sensor._unevenly_sampled_channel)

        return self

    def has_infrared_channel(self) -> bool:
        """
        Returns if this packet has an infrared channel.
        :return: If this packlet has an infrared channel.
        """
        return self._has_channel(api900_pb2.INFRARED)

    def infrared_channel(self) -> typing.Optional[infrared_sensor.InfraredSensor]:
        """
        Returns the high-level infrared channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level infrared channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_infrared_channel():
            return infrared_sensor.InfraredSensor(self._get_channel(api900_pb2.INFRARED))

        return None

    def set_infrared_channel(self,
                             infrared_sensor: typing.Optional[infrared_sensor.InfraredSensor]) -> 'WrappedRedvoxPacket':
        """
        Sets this packet's infrared sensor. A channel can be removed by passing in None.
        :param infrared_sensor: An optional instance of a infrared sensor.
        """
        if self.has_infrared_channel():
            self._delete_channel(api900_pb2.INFRARED)

        if infrared_sensor is not None:
            self._add_channel(infrared_sensor._unevenly_sampled_channel)

        return self

    def has_image_channel(self) -> bool:
        """
        Returns if this packet has an image channel.
        :return: If this packlet has an image channel.
        """
        return self._has_channel(api900_pb2.IMAGE)

    def image_channel(self) -> typing.Optional[image_sensor.ImageSensor]:
        """
        Returns the high-level image channel API or None if this packet doesn't contain a channel of this type.
        :return: the high-level image channel API or None if this packet doesn't contain a channel of this type.
        """
        if self.has_image_channel():
            return image_sensor.ImageSensor(self._get_channel(api900_pb2.IMAGE))

        return None

    def set_image_channel(self, image_sensor: typing.Optional[image_sensor.ImageSensor]):
        """
        Set's the image channel.
        :param image_sensor: Image sensor.
        """
        if self.has_image_channel():
            self._delete_channel(api900_pb2.IMAGE)

        if image_sensor is not None:
            self._add_channel(image_sensor._unevenly_sampled_channel)

    def __str__(self):
        """
        Returns protobuf's String representation of this packet.
        :return: Protobuf's String representation of this packet.
        """
        return str(self._redvox_packet)

    def __eq__(self, other):
        return isinstance(other, WrappedRedvoxPacket) and len(self.diff(other)) == 0

    def diff(self, other: 'WrappedRedvoxPacket') -> typing.List[str]:
        """
        Finds the differences (if any) between two WrappedRedvoxPackets.
        :param other: The other wrapped redvox packet to compare to.
        :return: A list of differences or an empty list if there are none.
        """
        diffs = map(lambda tuple2: reader_utils.diff(tuple2[0], tuple2[1]), [
            (self.api(), other.api()),
            (self.redvox_id(), other.redvox_id()),
            (self.uuid(), other.uuid()),
            (self.authenticated_email(), other.authenticated_email()),
            (self.authentication_token(), other.authentication_token()),
            (self.firebase_token(), other.firebase_token()),
            (self.is_backfilled(), other.is_backfilled()),
            (self.is_private(), other.is_private()),
            (self.is_scrambled(), other.is_scrambled()),
            (self.device_make(), other.device_make()),
            (self.device_model(), other.device_model()),
            (self.device_os(), other.device_os()),
            (self.device_os_version(), other.device_os_version()),
            (self.app_version(), other.app_version()),
            (self.battery_level_percent(), other.battery_level_percent()),
            (self.device_temperature_c(), other.device_temperature_c()),
            (self.acquisition_server(), other.acquisition_server()),
            (self.time_synchronization_server(), other.time_synchronization_server()),
            (self.authentication_server(), other.authentication_server()),
            (self.app_file_start_timestamp_epoch_microseconds_utc(),
             other.app_file_start_timestamp_epoch_microseconds_utc()),
            (self.app_file_start_timestamp_machine(), other.app_file_start_timestamp_machine()),
            (self.server_timestamp_epoch_microseconds_utc(),
             other.server_timestamp_epoch_microseconds_utc()),
            (self.metadata(), other.metadata()),
            (self.microphone_channel(), other.microphone_channel()),
            (self.barometer_channel(), other.barometer_channel()),
            (self.location_channel(), other.location_channel()),
            (self.time_synchronization_channel(), other.time_synchronization_channel()),
            (self.accelerometer_channel(), other.accelerometer_channel()),
            (self.magnetometer_channel(), other.magnetometer_channel()),
            (self.gyroscope_channel(), other.gyroscope_channel()),
            (self.light_channel(), other.light_channel()),
            (self.infrared_channel(), other.infrared_channel())
        ])
        # Filter only out only the differences
        diffs = filter(lambda tuple2: tuple2[0], diffs)
        # Extract the difference string
        diffs = map(lambda tuple2: tuple2[1], diffs)
        return list(diffs)
