"""
Defines generic station objects for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
"""
from typing import List, Dict, Optional

import redvox.common.date_time_utils as dtu
from redvox.common.sensor_data import SensorData, SensorType
from redvox.common.station_utils import StationKey, StationMetadata, DataPacket, StationLocation, \
    station_location_from_data


class Station:
    """
    generic station for api-independent stuff
    Properties:
        station_metadata: StationMetadata
        station_data: dict, all the data associated with this station, default empty dict
        packet_data: list, all DataPacket metadata associated with this station, default empty list
        station_key: Tuple of str, str, float, a unique combination of three values defining the station
    """

    def __init__(self, metadata: StationMetadata, data: Optional[Dict[SensorType, SensorData]] = None,
                 packets: Optional[List[DataPacket]] = None):
        """
        initialize Station
        :param metadata: the station's metadata
        :param data: the station's sensors' data, default None (value is converted to empty dict)
        :param packets: the packets that the data came from, default None (value is converted to empty list)
        """
        self.station_metadata: StationMetadata = metadata
        if data:
            self.station_data: Dict[SensorType, SensorData] = data
        else:
            self.station_data: Dict[SensorType, SensorData] = {}
        # todo add event streams as dict[str, list[event]] i.e movement: [accelerometer, gyroscope, etc]
        if packets:
            self.packet_data: List[DataPacket] = packets
        else:
            self.packet_data: List[DataPacket] = []
        # todo: assert station key is valid
        self.station_key = StationKey(self.station_metadata.station_id, self.station_metadata.station_uuid,
                                      self.station_metadata.timing_data.station_start_timestamp)

    def append_station(self, new_station: 'Station'):
        """
        append a new station to the current station
        :param new_station: Station to append to current station
        """
        if new_station.station_metadata.station_id == self.station_metadata.station_id:
            self.append_station_data(new_station.station_data)
            self.packet_data.extend(new_station.packet_data)
        # todo: regenerate the metadata when adding new station data

    def append_station_data(self, new_station_data: Dict[SensorType, SensorData]):
        """
        append new station data to existing station data
        :param new_station_data: the dictionary of data to add
        """
        for sensor_type, sensor_data in new_station_data.items():
            self.append_sensor(sensor_type, sensor_data)

    def append_sensor(self, sensor_type: SensorType, sensor_data: SensorData):
        """
        append sensor data to an existing sensor_type or add a new sensor to the dictionary
        :param sensor_type: the sensor to append to
        :param sensor_data: the data to append
        """
        if sensor_type in self.station_data.keys():
            self.station_data[sensor_type] = self.station_data[sensor_type].append_data(sensor_data.data_df)
        else:
            self._add_sensor(sensor_type, sensor_data)

    def _delete_sensor(self, sensor_type: SensorType):
        """
        removes a sensor from the data packet if it exists
        :param sensor_type: the sensor to remove
        """
        if sensor_type in self.station_data.keys():
            self.station_data.pop(sensor_type)

    def _add_sensor(self, sensor_type: SensorType, sensor: SensorData):
        """
        adds a sensor to the sensor_data_dict
        :param sensor_type: the type of sensor to add
        :param sensor: the sensor data to add
        """
        if sensor_type in self.station_data.keys():
            raise ValueError(f"Cannot add sensor type ({sensor_type.name}) that already exists in packet!")
        else:
            self.station_data[sensor_type] = sensor

    def has_audio_sensor(self) -> bool:
        """
        check if audio sensor is in sensor_data_dict
        :return: True if audio sensor exists
        """
        return SensorType.AUDIO in self.station_data.keys()

    def has_audio_data(self) -> bool:
        """
        check if the audio sensor has any data
        :return: True if audio sensor has any data
        """
        return self.has_audio_sensor() and self.audio_sensor().num_samples() > 0

    def audio_sensor(self) -> Optional[SensorData]:
        """
        return the audio sensor if it exists
        :return: audio sensor if it exists, None otherwise
        """
        if self.has_audio_sensor():
            return self.station_data[SensorType.AUDIO]
        return None

    def set_audio_sensor(self, audio_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the audio sensor; can remove audio sensor by passing None
        :param audio_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_audio_sensor():
            self._delete_sensor(SensorType.AUDIO)
        if audio_sensor is not None:
            self._add_sensor(SensorType.AUDIO, audio_sensor)
        return self

    def has_location_sensor(self) -> bool:
        """
        check if location sensor is in sensor_data_dict
        :return: True if location sensor exists
        """
        return SensorType.LOCATION in self.station_data.keys()

    def has_location_data(self) -> bool:
        """
        check if the location sensor has any data
        :return: True if location sensor has any data
        """
        return self.has_location_sensor() and self.location_sensor().num_samples() > 0

    def location_sensor(self) -> Optional[SensorData]:
        """
        return the location sensor if it exists
        :return: location sensor if it exists, None otherwise
        """
        if self.has_location_sensor():
            return self.station_data[SensorType.LOCATION]
        return None

    def set_location_sensor(self, loc_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the location sensor; can remove location sensor by passing None
        :param loc_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_location_sensor():
            self._delete_sensor(SensorType.LOCATION)
        if loc_sensor is not None:
            self._add_sensor(SensorType.LOCATION, loc_sensor)
        return self

    def has_accelerometer_sensor(self) -> bool:
        """
        check if accelerometer sensor is in sensor_data_dict
        :return: True if accelerometer sensor exists
        """
        return SensorType.ACCELEROMETER in self.station_data.keys()

    def has_accelerometer_data(self) -> bool:
        """
        check if the accelerometer sensor has any data
        :return: True if accelerometer sensor has any data
        """
        return self.has_accelerometer_sensor() and self.accelerometer_sensor().num_samples() > 0

    def accelerometer_sensor(self) -> Optional[SensorData]:
        """
        return the accelerometer sensor if it exists
        :return: accelerometer sensor if it exists, None otherwise
        """
        if self.has_accelerometer_sensor():
            return self.station_data[SensorType.ACCELEROMETER]
        return None

    def set_accelerometer_sensor(self, acc_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the accelerometer sensor; can remove accelerometer sensor by passing None
        :param acc_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_accelerometer_sensor():
            self._delete_sensor(SensorType.ACCELEROMETER)
        if acc_sensor is not None:
            self._add_sensor(SensorType.ACCELEROMETER, acc_sensor)
        return self

    def has_magnetometer_sensor(self) -> bool:
        """
        check if magnetometer sensor is in sensor_data_dict
        :return: True if magnetometer sensor exists
        """
        return SensorType.MAGNETOMETER in self.station_data.keys()

    def has_magnetometer_data(self) -> bool:
        """
        check if the magnetometer sensor has any data
        :return: True if magnetometer sensor has any data
        """
        return self.has_magnetometer_sensor() and self.magnetometer_sensor().num_samples() > 0

    def magnetometer_sensor(self) -> Optional[SensorData]:
        """
        return the magnetometer sensor if it exists
        :return: magnetometer sensor if it exists, None otherwise
        """
        if self.has_magnetometer_sensor():
            return self.station_data[SensorType.MAGNETOMETER]
        return None

    def set_magnetometer_sensor(self, mag_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the magnetometer sensor; can remove magnetometer sensor by passing None
        :param mag_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_magnetometer_sensor():
            self._delete_sensor(SensorType.MAGNETOMETER)
        if mag_sensor is not None:
            self._add_sensor(SensorType.MAGNETOMETER, mag_sensor)
        return self

    def has_gyroscope_sensor(self) -> bool:
        """
        check if gyroscope sensor is in sensor_data_dict
        :return: True if gyroscope sensor exists
        """
        return SensorType.GYROSCOPE in self.station_data.keys()

    def has_gyroscope_data(self) -> bool:
        """
        check if the gyroscope sensor has any data
        :return: True if gyroscope sensor has any data
        """
        return self.has_gyroscope_sensor() and self.gyroscope_sensor().num_samples() > 0

    def gyroscope_sensor(self) -> Optional[SensorData]:
        """
        return the gyroscope sensor if it exists
        :return: gyroscope sensor if it exists, None otherwise
        """
        if self.has_gyroscope_sensor():
            return self.station_data[SensorType.GYROSCOPE]
        return None

    def set_gyroscope_sensor(self, gyro_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the gyroscope sensor; can remove gyroscope sensor by passing None
        :param gyro_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_gyroscope_sensor():
            self._delete_sensor(SensorType.GYROSCOPE)
        if gyro_sensor is not None:
            self._add_sensor(SensorType.GYROSCOPE, gyro_sensor)
        return self

    def has_barometer_sensor(self) -> bool:
        """
        check if barometer sensor is in sensor_data_dict
        :return: True if barometer sensor exists
        """
        return SensorType.PRESSURE in self.station_data.keys()

    def has_barometer_data(self) -> bool:
        """
        check if the barometer sensor has any data
        :return: True if barometer sensor has any data
        """
        return self.has_barometer_sensor() and self.barometer_sensor().num_samples() > 0

    def barometer_sensor(self) -> Optional[SensorData]:
        """
        return the barometer sensor if it exists
        :return: barometer sensor if it exists, None otherwise
        """
        if self.has_barometer_sensor():
            return self.station_data[SensorType.PRESSURE]
        return None

    def set_barometer_sensor(self, bar_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the barometer sensor; can remove barometer sensor by passing None
        :param bar_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_barometer_sensor():
            self._delete_sensor(SensorType.PRESSURE)
        if bar_sensor is not None:
            self._add_sensor(SensorType.PRESSURE, bar_sensor)
        return self

    def has_light_sensor(self) -> bool:
        """
        check if light sensor is in sensor_data_dict
        :return: True if light sensor exists
        """
        return SensorType.LIGHT in self.station_data.keys()

    def has_light_data(self) -> bool:
        """
        check if the light sensor has any data
        :return: True if light sensor has any data
        """
        return self.has_light_sensor() and self.light_sensor().num_samples() > 0

    def light_sensor(self) -> Optional[SensorData]:
        """
        return the light sensor if it exists
        :return: light sensor if it exists, None otherwise
        """
        if self.has_light_sensor():
            return self.station_data[SensorType.LIGHT]
        return None

    def set_light_sensor(self, light_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the light sensor; can remove light sensor by passing None
        :param light_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_light_sensor():
            self._delete_sensor(SensorType.LIGHT)
        if light_sensor is not None:
            self._add_sensor(SensorType.LIGHT, light_sensor)
        return self

    def has_infrared_sensor(self) -> bool:
        """
        check if infrared sensor is in sensor_data_dict
        :return: True if infrared sensor exists
        """
        return SensorType.INFRARED in self.station_data.keys()

    def has_infrared_data(self) -> bool:
        """
        check if the infrared sensor has any data
        :return: True if infrared sensor has any data
        """
        return self.has_infrared_sensor() and self.infrared_sensor().num_samples() > 0

    def infrared_sensor(self) -> Optional[SensorData]:
        """
        return the infrared sensor if it exists
        :return: infrared sensor if it exists, None otherwise
        """
        if self.has_infrared_sensor():
            return self.station_data[SensorType.INFRARED]
        return None

    def set_infrared_sensor(self, infrd_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the infrared sensor; can remove infrared sensor by passing None
        :param infrd_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_infrared_sensor():
            self._delete_sensor(SensorType.INFRARED)
        if infrd_sensor is not None:
            self._add_sensor(SensorType.INFRARED, infrd_sensor)
        return self

    def has_image_sensor(self) -> bool:
        """
        check if image sensor is in sensor_data_dict
        :return: True if image sensor exists
        """
        return SensorType.IMAGE in self.station_data.keys()

    def has_image_data(self) -> bool:
        """
        check if the image sensor has any data
        :return: True if image sensor has any data
        """
        return self.has_image_sensor() and self.image_sensor().num_samples() > 0

    def image_sensor(self) -> Optional[SensorData]:
        """
        return the image sensor if it exists
        :return: image sensor if it exists, None otherwise
        """
        if self.has_image_sensor():
            return self.station_data[SensorType.IMAGE]
        return None

    def set_image_sensor(self, img_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the image sensor; can remove image sensor by passing None
        :param img_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_image_sensor():
            self._delete_sensor(SensorType.IMAGE)
        if img_sensor is not None:
            self._add_sensor(SensorType.IMAGE, img_sensor)
        return self

    def has_ambient_temperature_sensor(self) -> bool:
        """
        check if ambient temperature sensor is in sensor_data_dict
        :return: True if ambient temperature sensor exists
        """
        return SensorType.TEMPERATURE in self.station_data.keys()

    def has_ambient_temperature_data(self) -> bool:
        """
        check if the ambient temperature sensor has any data
        :return: True if ambient temperature sensor has any data
        """
        return self.has_ambient_temperature_sensor() and self.ambient_temperature_sensor().num_samples() > 0

    def ambient_temperature_sensor(self) -> Optional[SensorData]:
        """
        return the ambient temperature sensor if it exists
        :return: image ambient temperature if it exists, None otherwise
        """
        if self.has_ambient_temperature_sensor():
            return self.station_data[SensorType.TEMPERATURE]
        return None

    def set_ambient_temperature_sensor(self, amtemp_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the ambient temperature sensor; can remove ambient temperature sensor by passing None
        :param amtemp_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_ambient_temperature_sensor():
            self._delete_sensor(SensorType.TEMPERATURE)
        if amtemp_sensor is not None:
            self._add_sensor(SensorType.TEMPERATURE, amtemp_sensor)
        return self

    def has_gravity_sensor(self) -> bool:
        """
        check if gravity sensor is in sensor_data_dict
        :return: True if gravity sensor exists
        """
        return SensorType.GRAVITY in self.station_data.keys()

    def has_gravity_data(self) -> bool:
        """
        check if the gravity sensor has any data
        :return: True if gravity sensor has any data
        """
        return self.has_gravity_sensor() and self.gravity_sensor().num_samples() > 0

    def gravity_sensor(self) -> Optional[SensorData]:
        """
        return the gravity sensor if it exists
        :return: gravity sensor if it exists, None otherwise
        """
        if self.has_gravity_sensor():
            return self.station_data[SensorType.GRAVITY]
        return None

    def set_gravity_sensor(self, grav_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the gravity sensor; can remove gravity sensor by passing None
        :param grav_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_gravity_sensor():
            self._delete_sensor(SensorType.GRAVITY)
        if grav_sensor is not None:
            self._add_sensor(SensorType.GRAVITY, grav_sensor)
        return self

    def has_linear_acceleration_sensor(self) -> bool:
        """
        check if linear acceleration sensor is in sensor_data_dict
        :return: True if linear acceleration sensor exists
        """
        return SensorType.LINEAR_ACCELERATION in self.station_data.keys()

    def has_linear_acceleration_data(self) -> bool:
        """
        check if the linear acceleration sensor has any data
        :return: True if linear acceleration sensor has any data
        """
        return self.has_linear_acceleration_sensor() and self.linear_acceleration_sensor().num_samples() > 0

    def linear_acceleration_sensor(self) -> Optional[SensorData]:
        """
        return the linear acceleration sensor if it exists
        :return: linear acceleration sensor if it exists, None otherwise
        """
        if self.has_linear_acceleration_sensor():
            return self.station_data[SensorType.LINEAR_ACCELERATION]
        return None

    def set_linear_acceleration_sensor(self, linacc_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the linear acceleration sensor; can remove linear acceleration sensor by passing None
        :param linacc_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_linear_acceleration_sensor():
            self._delete_sensor(SensorType.LINEAR_ACCELERATION)
        if linacc_sensor is not None:
            self._add_sensor(SensorType.LINEAR_ACCELERATION, linacc_sensor)
        return self

    def has_orientation_sensor(self) -> bool:
        """
        check if orientation sensor is in sensor_data_dict
        :return: True if orientation sensor exists
        """
        return SensorType.ORIENTATION in self.station_data.keys()

    def has_orientation_data(self) -> bool:
        """
        check if the orientation sensor has any data
        :return: True if orientation sensor has any data
        """
        return self.has_orientation_sensor() and self.orientation_sensor().num_samples() > 0

    def orientation_sensor(self) -> Optional[SensorData]:
        """
        return the orientation sensor if it exists
        :return: orientation sensor if it exists, None otherwise
        """
        if self.has_orientation_sensor():
            return self.station_data[SensorType.ORIENTATION]
        return None

    def set_orientation_sensor(self, orient_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the orientation sensor; can remove orientation sensor by passing None
        :param orient_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_orientation_sensor():
            self._delete_sensor(SensorType.ORIENTATION)
        if orient_sensor is not None:
            self._add_sensor(SensorType.ORIENTATION, orient_sensor)
        return self

    def has_proximity_sensor(self) -> bool:
        """
        check if proximity sensor is in sensor_data_dict
        :return: True if proximity sensor exists
        """
        return SensorType.PROXIMITY in self.station_data.keys()

    def has_proximity_data(self) -> bool:
        """
        check if the proximity sensor has any data
        :return: True if proximity sensor has any data
        """
        return self.has_proximity_sensor() and self.proximity_sensor().num_samples() > 0

    def proximity_sensor(self) -> Optional[SensorData]:
        """
        return the proximity sensor if it exists
        :return: proximity sensor if it exists, None otherwise
        """
        if self.has_proximity_sensor():
            return self.station_data[SensorType.PROXIMITY]
        return None

    def set_proximity_sensor(self, prox_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the proximity sensor; can remove proximity sensor by passing None
        :param prox_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_proximity_sensor():
            self._delete_sensor(SensorType.PROXIMITY)
        if prox_sensor is not None:
            self._add_sensor(SensorType.PROXIMITY, prox_sensor)
        return self

    def has_relative_humidity_sensor(self) -> bool:
        """
        check if relative humidity sensor is in sensor_data_dict
        :return: True if linear relative humidity sensor exists
        """
        return SensorType.RELATIVE_HUMIDITY in self.station_data.keys()

    def has_relative_humidity_data(self) -> bool:
        """
        check if the relative humidity sensor has any data
        :return: True if relative humidity sensor has any data
        """
        return self.has_relative_humidity_sensor() and self.relative_humidity_sensor().num_samples() > 0

    def relative_humidity_sensor(self) -> Optional[SensorData]:
        """
        return the relative humidity sensor if it exists
        :return: relative humidity sensor if it exists, None otherwise
        """
        if self.has_relative_humidity_sensor():
            return self.station_data[SensorType.RELATIVE_HUMIDITY]
        return None

    def set_relative_humidity_sensor(self, relhum_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the relative humidity sensor; can remove relative humidity sensor by passing None
        :param relhum_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_relative_humidity_sensor():
            self._delete_sensor(SensorType.RELATIVE_HUMIDITY)
        if relhum_sensor is not None:
            self._add_sensor(SensorType.RELATIVE_HUMIDITY, relhum_sensor)
        return self

    def has_rotation_vector_sensor(self) -> bool:
        """
        check if rotation vector sensor is in sensor_data_dict
        :return: True if rotation vector sensor exists
        """
        return SensorType.ROTATION_VECTOR in self.station_data.keys()

    def has_rotation_vector_data(self) -> bool:
        """
        check if the rotation vector sensor has any data
        :return: True if rotation vector sensor has any data
        """
        return self.has_rotation_vector_sensor() and self.rotation_vector_sensor().num_samples() > 0

    def rotation_vector_sensor(self) -> Optional[SensorData]:
        """
        return the rotation vector sensor if it exists
        :return: rotation vector sensor if it exists, None otherwise
        """
        if self.has_rotation_vector_sensor():
            return self.station_data[SensorType.ROTATION_VECTOR]
        return None

    def set_rotation_vector_sensor(self, rotvec_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the rotation vector sensor; can remove rotation vector sensor by passing None
        :param rotvec_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_rotation_vector_sensor():
            self._delete_sensor(SensorType.ROTATION_VECTOR)
        if rotvec_sensor is not None:
            self._add_sensor(SensorType.ROTATION_VECTOR, rotvec_sensor)
        return self

    def has_compressed_audio_sensor(self) -> bool:
        """
        check if compressed audio sensor is in sensor_data_dict
        :return: True if compressed audio sensor exists
        """
        return SensorType.COMPRESSED_AUDIO in self.station_data.keys()

    def has_compressed_audio_data(self) -> bool:
        """
        check if the compressed audio sensor has any data
        :return: True if compressed audio sensor has any data
        """
        return self.has_compressed_audio_sensor() and self.compressed_audio_sensor().num_samples() > 0

    def compressed_audio_sensor(self) -> Optional[SensorData]:
        """
        return the compressed audio sensor if it exists
        :return: compressed audio sensor if it exists, None otherwise
        """
        if self.has_compressed_audio_sensor():
            return self.station_data[SensorType.COMPRESSED_AUDIO]
        return None

    def set_compressed_audio_sensor(self, compaudio_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the compressed audio sensor; can remove compressed audio sensor by passing None
        :param compaudio_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_compressed_audio_sensor():
            self._delete_sensor(SensorType.COMPRESSED_AUDIO)
        if compaudio_sensor is not None:
            self._add_sensor(SensorType.COMPRESSED_AUDIO, compaudio_sensor)
        return self

    def has_health_sensor(self) -> bool:
        """
        check if station health is in sensor_data_dict
        :return: True if station health sensor exists
        """
        return SensorType.STATION_HEALTH in self.station_data.keys()

    def has_health_data(self) -> bool:
        """
        check if the station health sensor has any data
        :return: True if station health sensor has any data
        """
        return self.has_health_sensor() and self.health_sensor().num_samples() > 0

    def health_sensor(self) -> Optional[SensorData]:
        """
        return the station health sensor if it exists
        :return: station health sensor if it exists, None otherwise
        """
        if self.has_health_sensor():
            return self.station_data[SensorType.STATION_HEALTH]
        return None

    def set_health_sensor(self, health_sensor: Optional[SensorData]) -> 'Station':
        """
        sets the station health sensor; can remove station health sensor by passing None
        :param health_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_health_sensor():
            self._delete_sensor(SensorType.STATION_HEALTH)
        if health_sensor is not None:
            self._add_sensor(SensorType.STATION_HEALTH, health_sensor)
        return self

    def get_non_audio_sensors(self) -> Dict[SensorType, SensorData]:
        """
        returns all non-audio sensors in the station
        :return: dict of SensorType and SensorData of all non-audio sensors in the station
        """
        return {k: v for (k, v) in self.station_data.items() if SensorType.AUDIO not in k}

    def update_station_locations(self, from_data: bool = False):
        """
        updates the station locations in the metadata
        :param from_data: if True, pulls location data from the location sensor, default False
        """
        if from_data:
            if self.has_location_sensor():
                # noinspection PyTypeChecker
                self.station_metadata.location_data.all_locations = \
                    self.location_sensor().data_df.apply(station_location_from_data, axis=1).values
            else:
                raise ValueError(f"Attempted to update locations of station {self.station_metadata.station_id} "
                                 f"using data, but there is no data!")
        else:
            self.station_metadata.location_data.all_locations = \
                [packet.best_location if packet.best_location else StationLocation() for packet in self.packet_data]

    def update_station_location_metadata(self, start_datetime: float, end_datetime: float):
        """
        update the station's location metadata using the metadata and/or location data of the station
        :param start_datetime: the start timestamp in microseconds since epoch UTC of the window to consider
        :param end_datetime: the end timestamp in microseconds since epoch UTC of the window to consider
        """
        # get locations from packet metadata
        self.update_station_locations()
        self.station_metadata.location_data.update_window_locations(start_datetime, end_datetime)
        # not enough packet metadata locations, get data locations
        if not self.station_metadata.location_data.calc_mean_and_std_from_locations() and self.has_location_data():
            self.update_station_locations(from_data=True)
            self.station_metadata.location_data.update_window_locations(start_datetime, end_datetime)
            self.station_metadata.location_data.calc_mean_and_std_from_locations()

    def packet_gap_detector(self, gap_time_s: float):
        """
        Uses the station's packet and audio data to detect gaps at least gap_time_s seconds long.
        updates the station's packet metadata if there are no gaps
        :param gap_time_s: float, minimum gap time in seconds
        """
        for packet in range(len(self.packet_data) - 1):
            data_start = self.packet_data[packet].data_start_timestamp
            data_num_samples = self.packet_data[packet].num_audio_samples
            next_packet_start_index = \
                self.audio_sensor().data_df.query("timestamps >= @data_start").first_valid_index() + data_num_samples
            data_end = self.audio_sensor().data_timestamps()[next_packet_start_index - 1]
            next_packet_start = self.audio_sensor().data_timestamps()[next_packet_start_index]
            if next_packet_start - data_end < dtu.seconds_to_microseconds(gap_time_s):
                self.packet_data[packet].micros_to_next_packet = \
                    (next_packet_start - data_start) / data_num_samples

    def update_timestamps(self):
        """
        updates the timestamps in all SensorData objects using the station_best_offset of the station_timing
        """
        if self.station_metadata.station_timing_is_corrected:
            print("WARNING: Timestamps already corrected!")
        else:
            if not self.station_metadata.timing_data:
                print("WARNING: Station does not have timing data, assuming existing values are the correct ones!")
            else:
                delta = self.station_metadata.timing_data.station_best_offset
                for sensor in self.station_data.values():
                    sensor.update_data_timestamps(delta)
                for packet in self.packet_data:
                    packet.data_start_timestamp += delta
                    packet.data_end_timestamp += delta
                    if packet.best_location:
                        packet.best_location.update_timestamps(delta)
                self.station_metadata.timing_data.station_first_data_timestamp += delta
                self.station_metadata.location_data.update_timestamps(delta)
            self.station_metadata.station_timing_is_corrected = True

    def revert_timestamps(self):
        """
        reverts the timestamps in all SensorData objects using the station_best_offset of the station_timing
        """
        if self.station_metadata.station_timing_is_corrected:
            if not self.station_metadata.timing_data:
                print("WARNING: Station does not have timing data, assuming existing values are the correct ones!")
            else:
                delta = self.station_metadata.timing_data.station_best_offset
                for sensor in self.station_data.values():
                    sensor.update_data_timestamps(-delta)
                for packet in self.packet_data:
                    packet.data_start_timestamp -= delta
                    packet.data_end_timestamp -= delta
                    if packet.best_location:
                        packet.best_location.update_timestamps(-delta)
                self.station_metadata.timing_data.station_first_data_timestamp -= delta
                self.station_metadata.location_data.update_timestamps(-delta)
                self.station_metadata.station_timing_is_corrected = False
        else:
            print("WARNING: Cannot revert timestamps that are not corrected!")
