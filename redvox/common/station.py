"""
Defines generic station objects for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
Utilizes WrappedRedvoxPacketM (API M data packets) as the format of the data due to their versatility
"""
from typing import List, Dict, Optional

import numpy as np

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
import redvox.common.date_time_utils as dtu
from redvox.common import sensor_data as sd
from redvox.common.station_utils import StationKey, StationMetadata, DataPacket, StationLocation, \
    station_location_from_data


def validate_station_data(data_packets: List[WrappedRedvoxPacketM]) -> bool:
    """
    Check if all packets have the same key values
    :param data_packets: packets to check
    :return: True if all packets have the same key values
    """
    if len(data_packets) == 1:
        return True
    elif len(data_packets) < 1:
        return False
    elif all(lambda: t.get_station_information().get_id() == data_packets[0].get_station_information().get_id()
             and t.get_station_information().get_uuid() == data_packets[0].get_station_information().get_uuid()
             and t.get_timing_information().get_app_start_mach_timestamp() ==
             data_packets[0].get_timing_information().get_app_start_mach_timestamp()
             for t in data_packets):
        return True
    return False


class Station:
    """
    generic station for api-independent stuff; uses API M as the core data object since its quite versatile
    In order for a list of packets to be a station, all of the packets must:
        Have the same station id
        Have the same station uuid
        Have the same start time
    Properties:
        data: List of data packets associated with the station
        id: str id of the station, default None
        uuid: str uuid of the station, default None
        start_timestamp: float of microseconds since epoch UTC when the station started recording, default np.nan
        key: Tuple of str, str, float, a unique combination of three values defining the station, default None
    """

    def __init__(self, data_packets: Optional[List[WrappedRedvoxPacketM]] = None):
        """
        initialize Station
        :param data_packets: optional list of data packets representing the station, default None
        """
        self.data = data_packets.copy()
        if self.data and validate_station_data(self.data):
            self._sort_data_packets()
            self.id = self.data[0].get_station_information().get_id()
            self.uuid = self.data[0].get_station_information().get_uuid()
            self.start_timestamp = self.data[0].get_timing_information().get_app_start_mach_timestamp()
            self.key = StationKey(self.id, self.uuid, self.start_timestamp)
        else:
            if data_packets:
                print("Warning: Data given to create station is not consistent; check station_id, station_uuid "
                      "and app_start_time of the packets.")
                self.data = None
            self.id = None
            self.uuid = None
            self.start_timestamp = np.nan
            self.key = None

    def _sort_data_packets(self):
        """
        orders the data packets by their starting timestamps.  Returns nothing, sorts the data in place
        """
        self.data.sort(key=lambda t: t.get_timing_information().get_packet_start_mach_timestamp())

    def set_id(self, station_id: str) -> 'Station':
        """
        set the station's id
        :param station_id: id of station
        :return: modified version of self
        """
        self.id = station_id
        return self

    def set_uuid(self, uuid: str) -> 'Station':
        """
        set the station's uuid
        :param uuid: uuid of station
        :return: modified version of self
        """
        self.uuid = uuid
        return self

    def set_start_timestamp(self, start_timestamp: float) -> 'Station':
        """
        set the station's start timestamp in microseconds since epoch utc
        :param start_timestamp: start_timestamp of station
        :return: modified version of self
        """
        self.start_timestamp = start_timestamp
        return self

    def set_key(self) -> 'Station':
        """
        set the station's key if enough information is set
        :return: modified version of self
        """
        if self.id and self.uuid and not np.isnan(self.start_timestamp):
            self.key = StationKey(self.id, self.uuid, self.start_timestamp)
        return self

    def append_station(self, new_station: 'Station'):
        """
        append a new station to the current station
        :param new_station: Station to append to current station
        """
        if new_station.key == self.key:
            self.data.extend(new_station.data)
            self._sort_data_packets()
        else:
            print("Warning: Cannot append new station data if station keys do not match.")

    def append_station_data(self, new_data: List[WrappedRedvoxPacketM]):
        """
        append new station data to existing station data
        :param new_data: the list of packets to add
        """
        new_data_key = StationKey(new_data[0].get_station_information().get_id(),
                                  new_data[0].get_station_information().get_uuid(),
                                  new_data[0].get_timing_information().get_packet_start_mach_timestamp())
        if new_data_key == self.key:
            self.data.extend(new_data)
            self._sort_data_packets()
        else:
            print("Warning: Cannot append new data packets if station keys do not match.")

    def has_audio_sensor(self) -> bool:
        """
        check if audio sensor is in any of the packets
        :return: True if audio sensor exists in any of the packets
        """
        return any(lambda: s.get_sensors().has_audio() for s in self.data)

    def audio_sensor(self) -> Optional[sd.SensorData]:
        """
        return the audio sensor if it exists
        :return: audio sensor if it exists, None otherwise
        """
        return sd.load_apim_audio_from_list(self.data)

    def has_location_sensor(self) -> bool:
        """
        check if location sensor is in sensor_data_dict
        :return: True if location sensor exists
        """
        return any(lambda: s.get_sensors().has_location() for s in self.data)

    def location_sensor(self) -> Optional[sd.SensorData]:
        """
        return the location sensor if it exists
        :return: location sensor if it exists, None otherwise
        """
        return sd.load_apim_location_from_list(self.data)

    # def has_accelerometer_sensor(self) -> bool:
    #     """
    #     check if accelerometer sensor is in sensor_data_dict
    #     :return: True if accelerometer sensor exists
    #     """
    #     return SensorType.ACCELEROMETER in self.station_data.keys()
    #
    # def has_accelerometer_data(self) -> bool:
    #     """
    #     check if the accelerometer sensor has any data
    #     :return: True if accelerometer sensor has any data
    #     """
    #     return self.has_accelerometer_sensor() and self.accelerometer_sensor().num_samples() > 0
    #
    # def accelerometer_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the accelerometer sensor if it exists
    #     :return: accelerometer sensor if it exists, None otherwise
    #     """
    #     if self.has_accelerometer_sensor():
    #         return self.station_data[SensorType.ACCELEROMETER]
    #     return None
    #
    # def set_accelerometer_sensor(self, acc_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the accelerometer sensor; can remove accelerometer sensor by passing None
    #     :param acc_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_accelerometer_sensor():
    #         self._delete_sensor(SensorType.ACCELEROMETER)
    #     if acc_sensor is not None:
    #         self._add_sensor(SensorType.ACCELEROMETER, acc_sensor)
    #     return self
    #
    # def has_magnetometer_sensor(self) -> bool:
    #     """
    #     check if magnetometer sensor is in sensor_data_dict
    #     :return: True if magnetometer sensor exists
    #     """
    #     return SensorType.MAGNETOMETER in self.station_data.keys()
    #
    # def has_magnetometer_data(self) -> bool:
    #     """
    #     check if the magnetometer sensor has any data
    #     :return: True if magnetometer sensor has any data
    #     """
    #     return self.has_magnetometer_sensor() and self.magnetometer_sensor().num_samples() > 0
    #
    # def magnetometer_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the magnetometer sensor if it exists
    #     :return: magnetometer sensor if it exists, None otherwise
    #     """
    #     if self.has_magnetometer_sensor():
    #         return self.station_data[SensorType.MAGNETOMETER]
    #     return None
    #
    # def set_magnetometer_sensor(self, mag_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the magnetometer sensor; can remove magnetometer sensor by passing None
    #     :param mag_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_magnetometer_sensor():
    #         self._delete_sensor(SensorType.MAGNETOMETER)
    #     if mag_sensor is not None:
    #         self._add_sensor(SensorType.MAGNETOMETER, mag_sensor)
    #     return self
    #
    # def has_gyroscope_sensor(self) -> bool:
    #     """
    #     check if gyroscope sensor is in sensor_data_dict
    #     :return: True if gyroscope sensor exists
    #     """
    #     return SensorType.GYROSCOPE in self.station_data.keys()
    #
    # def has_gyroscope_data(self) -> bool:
    #     """
    #     check if the gyroscope sensor has any data
    #     :return: True if gyroscope sensor has any data
    #     """
    #     return self.has_gyroscope_sensor() and self.gyroscope_sensor().num_samples() > 0
    #
    # def gyroscope_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the gyroscope sensor if it exists
    #     :return: gyroscope sensor if it exists, None otherwise
    #     """
    #     if self.has_gyroscope_sensor():
    #         return self.station_data[SensorType.GYROSCOPE]
    #     return None
    #
    # def set_gyroscope_sensor(self, gyro_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the gyroscope sensor; can remove gyroscope sensor by passing None
    #     :param gyro_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_gyroscope_sensor():
    #         self._delete_sensor(SensorType.GYROSCOPE)
    #     if gyro_sensor is not None:
    #         self._add_sensor(SensorType.GYROSCOPE, gyro_sensor)
    #     return self
    #
    # def has_barometer_sensor(self) -> bool:
    #     """
    #     check if barometer sensor is in sensor_data_dict
    #     :return: True if barometer sensor exists
    #     """
    #     return SensorType.PRESSURE in self.station_data.keys()
    #
    # def has_barometer_data(self) -> bool:
    #     """
    #     check if the barometer sensor has any data
    #     :return: True if barometer sensor has any data
    #     """
    #     return self.has_barometer_sensor() and self.barometer_sensor().num_samples() > 0
    #
    # def barometer_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the barometer sensor if it exists
    #     :return: barometer sensor if it exists, None otherwise
    #     """
    #     if self.has_barometer_sensor():
    #         return self.station_data[SensorType.PRESSURE]
    #     return None
    #
    # def set_barometer_sensor(self, bar_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the barometer sensor; can remove barometer sensor by passing None
    #     :param bar_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_barometer_sensor():
    #         self._delete_sensor(SensorType.PRESSURE)
    #     if bar_sensor is not None:
    #         self._add_sensor(SensorType.PRESSURE, bar_sensor)
    #     return self
    #
    # def has_light_sensor(self) -> bool:
    #     """
    #     check if light sensor is in sensor_data_dict
    #     :return: True if light sensor exists
    #     """
    #     return SensorType.LIGHT in self.station_data.keys()
    #
    # def has_light_data(self) -> bool:
    #     """
    #     check if the light sensor has any data
    #     :return: True if light sensor has any data
    #     """
    #     return self.has_light_sensor() and self.light_sensor().num_samples() > 0
    #
    # def light_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the light sensor if it exists
    #     :return: light sensor if it exists, None otherwise
    #     """
    #     if self.has_light_sensor():
    #         return self.station_data[SensorType.LIGHT]
    #     return None
    #
    # def set_light_sensor(self, light_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the light sensor; can remove light sensor by passing None
    #     :param light_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_light_sensor():
    #         self._delete_sensor(SensorType.LIGHT)
    #     if light_sensor is not None:
    #         self._add_sensor(SensorType.LIGHT, light_sensor)
    #     return self
    #
    # def has_infrared_sensor(self) -> bool:
    #     """
    #     check if infrared sensor is in sensor_data_dict
    #     :return: True if infrared sensor exists
    #     """
    #     return SensorType.INFRARED in self.station_data.keys()
    #
    # def has_infrared_data(self) -> bool:
    #     """
    #     check if the infrared sensor has any data
    #     :return: True if infrared sensor has any data
    #     """
    #     return self.has_infrared_sensor() and self.infrared_sensor().num_samples() > 0
    #
    # def infrared_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the infrared sensor if it exists
    #     :return: infrared sensor if it exists, None otherwise
    #     """
    #     if self.has_infrared_sensor():
    #         return self.station_data[SensorType.INFRARED]
    #     return None
    #
    # def set_infrared_sensor(self, infrd_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the infrared sensor; can remove infrared sensor by passing None
    #     :param infrd_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_infrared_sensor():
    #         self._delete_sensor(SensorType.INFRARED)
    #     if infrd_sensor is not None:
    #         self._add_sensor(SensorType.INFRARED, infrd_sensor)
    #     return self
    #
    # def has_image_sensor(self) -> bool:
    #     """
    #     check if image sensor is in sensor_data_dict
    #     :return: True if image sensor exists
    #     """
    #     return SensorType.IMAGE in self.station_data.keys()
    #
    # def has_image_data(self) -> bool:
    #     """
    #     check if the image sensor has any data
    #     :return: True if image sensor has any data
    #     """
    #     return self.has_image_sensor() and self.image_sensor().num_samples() > 0
    #
    # def image_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the image sensor if it exists
    #     :return: image sensor if it exists, None otherwise
    #     """
    #     if self.has_image_sensor():
    #         return self.station_data[SensorType.IMAGE]
    #     return None
    #
    # def set_image_sensor(self, img_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the image sensor; can remove image sensor by passing None
    #     :param img_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_image_sensor():
    #         self._delete_sensor(SensorType.IMAGE)
    #     if img_sensor is not None:
    #         self._add_sensor(SensorType.IMAGE, img_sensor)
    #     return self
    #
    # def has_ambient_temperature_sensor(self) -> bool:
    #     """
    #     check if ambient temperature sensor is in sensor_data_dict
    #     :return: True if ambient temperature sensor exists
    #     """
    #     return SensorType.AMBIENT_TEMPERATURE in self.station_data.keys()
    #
    # def has_ambient_temperature_data(self) -> bool:
    #     """
    #     check if the ambient temperature sensor has any data
    #     :return: True if ambient temperature sensor has any data
    #     """
    #     return self.has_ambient_temperature_sensor() and self.ambient_temperature_sensor().num_samples() > 0
    #
    # def ambient_temperature_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the ambient temperature sensor if it exists
    #     :return: image ambient temperature if it exists, None otherwise
    #     """
    #     if self.has_ambient_temperature_sensor():
    #         return self.station_data[SensorType.AMBIENT_TEMPERATURE]
    #     return None
    #
    # def set_ambient_temperature_sensor(self, amtemp_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the ambient temperature sensor; can remove ambient temperature sensor by passing None
    #     :param amtemp_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_ambient_temperature_sensor():
    #         self._delete_sensor(SensorType.AMBIENT_TEMPERATURE)
    #     if amtemp_sensor is not None:
    #         self._add_sensor(SensorType.AMBIENT_TEMPERATURE, amtemp_sensor)
    #     return self
    #
    # def has_gravity_sensor(self) -> bool:
    #     """
    #     check if gravity sensor is in sensor_data_dict
    #     :return: True if gravity sensor exists
    #     """
    #     return SensorType.GRAVITY in self.station_data.keys()
    #
    # def has_gravity_data(self) -> bool:
    #     """
    #     check if the gravity sensor has any data
    #     :return: True if gravity sensor has any data
    #     """
    #     return self.has_gravity_sensor() and self.gravity_sensor().num_samples() > 0
    #
    # def gravity_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the gravity sensor if it exists
    #     :return: gravity sensor if it exists, None otherwise
    #     """
    #     if self.has_gravity_sensor():
    #         return self.station_data[SensorType.GRAVITY]
    #     return None
    #
    # def set_gravity_sensor(self, grav_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the gravity sensor; can remove gravity sensor by passing None
    #     :param grav_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_gravity_sensor():
    #         self._delete_sensor(SensorType.GRAVITY)
    #     if grav_sensor is not None:
    #         self._add_sensor(SensorType.GRAVITY, grav_sensor)
    #     return self
    #
    # def has_linear_acceleration_sensor(self) -> bool:
    #     """
    #     check if linear acceleration sensor is in sensor_data_dict
    #     :return: True if linear acceleration sensor exists
    #     """
    #     return SensorType.LINEAR_ACCELERATION in self.station_data.keys()
    #
    # def has_linear_acceleration_data(self) -> bool:
    #     """
    #     check if the linear acceleration sensor has any data
    #     :return: True if linear acceleration sensor has any data
    #     """
    #     return self.has_linear_acceleration_sensor() and self.linear_acceleration_sensor().num_samples() > 0
    #
    # def linear_acceleration_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the linear acceleration sensor if it exists
    #     :return: linear acceleration sensor if it exists, None otherwise
    #     """
    #     if self.has_linear_acceleration_sensor():
    #         return self.station_data[SensorType.LINEAR_ACCELERATION]
    #     return None
    #
    # def set_linear_acceleration_sensor(self, linacc_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the linear acceleration sensor; can remove linear acceleration sensor by passing None
    #     :param linacc_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_linear_acceleration_sensor():
    #         self._delete_sensor(SensorType.LINEAR_ACCELERATION)
    #     if linacc_sensor is not None:
    #         self._add_sensor(SensorType.LINEAR_ACCELERATION, linacc_sensor)
    #     return self
    #
    # def has_orientation_sensor(self) -> bool:
    #     """
    #     check if orientation sensor is in sensor_data_dict
    #     :return: True if orientation sensor exists
    #     """
    #     return SensorType.ORIENTATION in self.station_data.keys()
    #
    # def has_orientation_data(self) -> bool:
    #     """
    #     check if the orientation sensor has any data
    #     :return: True if orientation sensor has any data
    #     """
    #     return self.has_orientation_sensor() and self.orientation_sensor().num_samples() > 0
    #
    # def orientation_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the orientation sensor if it exists
    #     :return: orientation sensor if it exists, None otherwise
    #     """
    #     if self.has_orientation_sensor():
    #         return self.station_data[SensorType.ORIENTATION]
    #     return None
    #
    # def set_orientation_sensor(self, orient_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the orientation sensor; can remove orientation sensor by passing None
    #     :param orient_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_orientation_sensor():
    #         self._delete_sensor(SensorType.ORIENTATION)
    #     if orient_sensor is not None:
    #         self._add_sensor(SensorType.ORIENTATION, orient_sensor)
    #     return self
    #
    # def has_proximity_sensor(self) -> bool:
    #     """
    #     check if proximity sensor is in sensor_data_dict
    #     :return: True if proximity sensor exists
    #     """
    #     return SensorType.PROXIMITY in self.station_data.keys()
    #
    # def has_proximity_data(self) -> bool:
    #     """
    #     check if the proximity sensor has any data
    #     :return: True if proximity sensor has any data
    #     """
    #     return self.has_proximity_sensor() and self.proximity_sensor().num_samples() > 0
    #
    # def proximity_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the proximity sensor if it exists
    #     :return: proximity sensor if it exists, None otherwise
    #     """
    #     if self.has_proximity_sensor():
    #         return self.station_data[SensorType.PROXIMITY]
    #     return None
    #
    # def set_proximity_sensor(self, prox_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the proximity sensor; can remove proximity sensor by passing None
    #     :param prox_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_proximity_sensor():
    #         self._delete_sensor(SensorType.PROXIMITY)
    #     if prox_sensor is not None:
    #         self._add_sensor(SensorType.PROXIMITY, prox_sensor)
    #     return self
    #
    # def has_relative_humidity_sensor(self) -> bool:
    #     """
    #     check if relative humidity sensor is in sensor_data_dict
    #     :return: True if linear relative humidity sensor exists
    #     """
    #     return SensorType.RELATIVE_HUMIDITY in self.station_data.keys()
    #
    # def has_relative_humidity_data(self) -> bool:
    #     """
    #     check if the relative humidity sensor has any data
    #     :return: True if relative humidity sensor has any data
    #     """
    #     return self.has_relative_humidity_sensor() and self.relative_humidity_sensor().num_samples() > 0
    #
    # def relative_humidity_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the relative humidity sensor if it exists
    #     :return: relative humidity sensor if it exists, None otherwise
    #     """
    #     if self.has_relative_humidity_sensor():
    #         return self.station_data[SensorType.RELATIVE_HUMIDITY]
    #     return None
    #
    # def set_relative_humidity_sensor(self, relhum_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the relative humidity sensor; can remove relative humidity sensor by passing None
    #     :param relhum_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_relative_humidity_sensor():
    #         self._delete_sensor(SensorType.RELATIVE_HUMIDITY)
    #     if relhum_sensor is not None:
    #         self._add_sensor(SensorType.RELATIVE_HUMIDITY, relhum_sensor)
    #     return self
    #
    # def has_rotation_vector_sensor(self) -> bool:
    #     """
    #     check if rotation vector sensor is in sensor_data_dict
    #     :return: True if rotation vector sensor exists
    #     """
    #     return SensorType.ROTATION_VECTOR in self.station_data.keys()
    #
    # def has_rotation_vector_data(self) -> bool:
    #     """
    #     check if the rotation vector sensor has any data
    #     :return: True if rotation vector sensor has any data
    #     """
    #     return self.has_rotation_vector_sensor() and self.rotation_vector_sensor().num_samples() > 0
    #
    # def rotation_vector_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the rotation vector sensor if it exists
    #     :return: rotation vector sensor if it exists, None otherwise
    #     """
    #     if self.has_rotation_vector_sensor():
    #         return self.station_data[SensorType.ROTATION_VECTOR]
    #     return None
    #
    # def set_rotation_vector_sensor(self, rotvec_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the rotation vector sensor; can remove rotation vector sensor by passing None
    #     :param rotvec_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_rotation_vector_sensor():
    #         self._delete_sensor(SensorType.ROTATION_VECTOR)
    #     if rotvec_sensor is not None:
    #         self._add_sensor(SensorType.ROTATION_VECTOR, rotvec_sensor)
    #     return self
    #
    # def has_compressed_audio_sensor(self) -> bool:
    #     """
    #     check if compressed audio sensor is in sensor_data_dict
    #     :return: True if compressed audio sensor exists
    #     """
    #     return SensorType.COMPRESSED_AUDIO in self.station_data.keys()
    #
    # def has_compressed_audio_data(self) -> bool:
    #     """
    #     check if the compressed audio sensor has any data
    #     :return: True if compressed audio sensor has any data
    #     """
    #     return self.has_compressed_audio_sensor() and self.compressed_audio_sensor().num_samples() > 0
    #
    # def compressed_audio_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the compressed audio sensor if it exists
    #     :return: compressed audio sensor if it exists, None otherwise
    #     """
    #     if self.has_compressed_audio_sensor():
    #         return self.station_data[SensorType.COMPRESSED_AUDIO]
    #     return None
    #
    # def set_compressed_audio_sensor(self, compaudio_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the compressed audio sensor; can remove compressed audio sensor by passing None
    #     :param compaudio_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_compressed_audio_sensor():
    #         self._delete_sensor(SensorType.COMPRESSED_AUDIO)
    #     if compaudio_sensor is not None:
    #         self._add_sensor(SensorType.COMPRESSED_AUDIO, compaudio_sensor)
    #     return self
    #
    # def has_health_sensor(self) -> bool:
    #     """
    #     check if station health is in sensor_data_dict
    #     :return: True if station health sensor exists
    #     """
    #     return SensorType.STATION_HEALTH in self.station_data.keys()
    #
    # def has_health_data(self) -> bool:
    #     """
    #     check if the station health sensor has any data
    #     :return: True if station health sensor has any data
    #     """
    #     return self.has_health_sensor() and self.health_sensor().num_samples() > 0
    #
    # def health_sensor(self) -> Optional[SensorData]:
    #     """
    #     return the station health sensor if it exists
    #     :return: station health sensor if it exists, None otherwise
    #     """
    #     if self.has_health_sensor():
    #         return self.station_data[SensorType.STATION_HEALTH]
    #     return None
    #
    # def set_health_sensor(self, health_sensor: Optional[SensorData]) -> 'Station':
    #     """
    #     sets the station health sensor; can remove station health sensor by passing None
    #     :param health_sensor: the SensorData to set or None
    #     :return: the edited DataPacket
    #     """
    #     if self.has_health_sensor():
    #         self._delete_sensor(SensorType.STATION_HEALTH)
    #     if health_sensor is not None:
    #         self._add_sensor(SensorType.STATION_HEALTH, health_sensor)
    #     return self
    #
    # def get_non_audio_sensors(self) -> Dict[SensorType, SensorData]:
    #     """
    #     returns all non-audio sensors in the station
    #     :return: dict of SensorType and SensorData of all non-audio sensors in the station
    #     """
    #     return {k: v for (k, v) in self.station_data.items() if SensorType.AUDIO not in k}
    #
    # def update_station_locations(self, from_data: bool = False):
    #     """
    #     updates the station locations in the metadata
    #     :param from_data: if True, pulls location data from the location sensor, default False
    #     """
    #     if from_data:
    #         if self.has_location_sensor():
    #             # noinspection PyTypeChecker
    #             self.station_metadata.location_data.all_locations = \
    #                 self.location_sensor().data_df.apply(station_location_from_data, axis=1).values
    #         else:
    #             raise ValueError(f"Attempted to update locations of station {self.station_metadata.station_id} "
    #                              f"using data, but there is no data!")
    #     else:
    #         self.station_metadata.location_data.all_locations = \
    #             [packet.best_location if packet.best_location else StationLocation() for packet in self.packet_data]
    #
    # def update_station_location_metadata(self, start_datetime: float, end_datetime: float):
    #     """
    #     update the station's location metadata using the metadata and/or location data of the station
    #     :param start_datetime: the start timestamp in microseconds since epoch UTC of the window to consider
    #     :param end_datetime: the end timestamp in microseconds since epoch UTC of the window to consider
    #     """
    #     # get locations from packet metadata
    #     self.update_station_locations()
    #     self.station_metadata.location_data.update_window_locations(start_datetime, end_datetime)
    #     # not enough packet metadata locations, get data locations
    #     if not self.station_metadata.location_data.calc_mean_and_std_from_locations() and self.has_location_data():
    #         self.update_station_locations(from_data=True)
    #         self.station_metadata.location_data.update_window_locations(start_datetime, end_datetime)
    #         self.station_metadata.location_data.calc_mean_and_std_from_locations()
    #
    # def packet_gap_detector(self, gap_time_s: float):
    #     """
    #     Uses the station's packet and audio data to detect gaps at least gap_time_s seconds long.
    #     updates the station's packet metadata if there are no gaps
    #     :param gap_time_s: float, minimum gap time in seconds
    #     """
    #     for packet in range(len(self.packet_data) - 1):
    #         data_start = self.packet_data[packet].data_start_timestamp
    #         data_num_samples = self.packet_data[packet].num_audio_samples
    #         next_packet_start_index = \
    #             self.audio_sensor().data_df.query("timestamps >= @data_start").first_valid_index() + data_num_samples
    #         data_end = self.audio_sensor().data_timestamps()[next_packet_start_index - 1]
    #         next_packet_start = self.audio_sensor().data_timestamps()[next_packet_start_index]
    #         if next_packet_start - data_end < dtu.seconds_to_microseconds(gap_time_s):
    #             self.packet_data[packet].micros_to_next_packet = \
    #                 (next_packet_start - data_start) / data_num_samples
    #
    # def update_timestamps(self):
    #     """
    #     updates the timestamps in all SensorData objects using the station_best_offset of the station_timing
    #     """
    #     if self.station_metadata.station_timing_is_corrected:
    #         print("WARNING: Timestamps already corrected!")
    #     else:
    #         if not self.station_metadata.timing_data:
    #             print("WARNING: Station does not have timing data, assuming existing values are the correct ones!")
    #         else:
    #             delta = self.station_metadata.timing_data.station_best_offset
    #             for sensor in self.station_data.values():
    #                 sensor.update_data_timestamps(delta)
    #             for packet in self.packet_data:
    #                 packet.data_start_timestamp += delta
    #                 packet.data_end_timestamp += delta
    #                 if packet.best_location:
    #                     packet.best_location.update_timestamps(delta)
    #             self.station_metadata.timing_data.station_first_data_timestamp += delta
    #             self.station_metadata.location_data.update_timestamps(delta)
    #         self.station_metadata.station_timing_is_corrected = True
    #
    # def revert_timestamps(self):
    #     """
    #     reverts the timestamps in all SensorData objects using the station_best_offset of the station_timing
    #     """
    #     if self.station_metadata.station_timing_is_corrected:
    #         if not self.station_metadata.timing_data:
    #             print("WARNING: Station does not have timing data, assuming existing values are the correct ones!")
    #         else:
    #             delta = self.station_metadata.timing_data.station_best_offset
    #             for sensor in self.station_data.values():
    #                 sensor.update_data_timestamps(-delta)
    #             for packet in self.packet_data:
    #                 packet.data_start_timestamp -= delta
    #                 packet.data_end_timestamp -= delta
    #                 if packet.best_location:
    #                     packet.best_location.update_timestamps(-delta)
    #             self.station_metadata.timing_data.station_first_data_timestamp -= delta
    #             self.station_metadata.location_data.update_timestamps(-delta)
    #             self.station_metadata.station_timing_is_corrected = False
    #     else:
    #         print("WARNING: Cannot revert timestamps that are not corrected!")
