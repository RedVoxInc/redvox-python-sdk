"""
Defines generic station objects for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
Utilizes WrappedRedvoxPacketM (API M data packets) as the format of the data due to their versatility
"""
from typing import List, Optional, Dict

import numpy as np

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.common import sensor_data as sd
from redvox.common.station_utils import StationKey
from redvox.common.timesync import TimeSyncAnalysis


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
        Have the same audio sample rate
    Properties:
        data: List of data packets associated with the station
        id: str id of the station, default None
        uuid: str uuid of the station, default None
        start_timestamp: float of microseconds since epoch UTC when the station started recording, default np.nan
        key: Tuple of str, str, float, a unique combination of three values defining the station, default None
        audio_sample_rate_hz: float, sample rate of audio component in hz
        timesync_analysis: TimeSyncAnalysis object, contains information about the station's timing values
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
            if self.data[0].get_sensors().has_audio():
                self.audio_sample_rate_hz = self.data[0].get_sensors().get_audio().get_sample_rate()
            else:
                self.audio_sample_rate_hz = np.nan
        else:
            if data_packets:
                print("Warning: Data given to create station is not consistent; check station_id, station_uuid "
                      "and app_start_time of the packets.")
                self.data = None
            self.id = None
            self.uuid = None
            self.start_timestamp = np.nan
            self.key = None
            self.audio_sample_rate_hz = np.nan
        self.timesync_analysis = TimeSyncAnalysis(self.id, self.audio_sample_rate_hz, self.start_timestamp, self.data)

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
        check if location sensor is in any of the packets
        :return: True if location sensor exists
        """
        return any(lambda: s.get_sensors().has_location() for s in self.data)

    def location_sensor(self) -> Optional[sd.SensorData]:
        """
        return the location sensor if it exists
        :return: location sensor if it exists, None otherwise
        """
        return sd.load_apim_location_from_list(self.data)

    def has_accelerometer_sensor(self) -> bool:
        """
        check if accelerometer sensor is in any of the packets
        :return: True if accelerometer sensor exists
        """
        return any(lambda: s.get_sensors().has_accelerometer() for s in self.data)

    def accelerometer_sensor(self) -> Optional[sd.SensorData]:
        """
        return the accelerometer sensor if it exists
        :return: accelerometer sensor if it exists, None otherwise
        """
        return sd.load_apim_accelerometer_from_list(self.data)

    def has_magnetometer_sensor(self) -> bool:
        """
        check if magnetometer sensor is in any of the packets
        :return: True if magnetometer sensor exists
        """
        return any(lambda: s.get_sensors().has_magnetometer() for s in self.data)

    def magnetometer_sensor(self) -> Optional[sd.SensorData]:
        """
        return the magnetometer sensor if it exists
        :return: magnetometer sensor if it exists, None otherwise
        """
        return sd.load_apim_magnetometer_from_list(self.data)

    def has_gyroscope_sensor(self) -> bool:
        """
        check if gyroscope sensor is in any of the packets
        :return: True if gyroscope sensor exists
        """
        return any(lambda: s.get_sensors().has_gyroscope() for s in self.data)

    def gyroscope_sensor(self) -> Optional[sd.SensorData]:
        """
        return the gyroscope sensor if it exists
        :return: gyroscope sensor if it exists, None otherwise
        """
        return sd.load_apim_gyroscope_from_list(self.data)

    def has_barometer_sensor(self) -> bool:
        """
        check if barometer (aka pressure) sensor is in any of the packets
        :return: True if barometer sensor exists
        """
        return any(lambda: s.get_sensors().has_pressure() for s in self.data)

    def barometer_sensor(self) -> Optional[sd.SensorData]:
        """
        return the barometer (aka pressure) sensor if it exists
        :return: barometer sensor if it exists, None otherwise
        """
        return sd.load_apim_pressure_from_list(self.data)

    def has_pressure_sensor(self) -> bool:
        """
        check if pressure (aka barometer) sensor is in any of the packets
        :return: True if pressure sensor exists
        """
        return any(lambda: s.get_sensors().has_pressure() for s in self.data)

    def pressure_sensor(self) -> Optional[sd.SensorData]:
        """
        return the pressure (aka barometer) sensor if it exists
        :return: pressure sensor if it exists, None otherwise
        """
        return sd.load_apim_pressure_from_list(self.data)

    def has_light_sensor(self) -> bool:
        """
        check if light sensor is in any of the packets
        :return: True if light sensor exists
        """
        return any(lambda: s.get_sensors().has_light() for s in self.data)

    def light_sensor(self) -> Optional[sd.SensorData]:
        """
        return the light sensor if it exists
        :return: light sensor if it exists, None otherwise
        """
        return sd.load_apim_light_from_list(self.data)

    def has_infrared_sensor(self) -> bool:
        """
        check if infrared (proximity) sensor is in any of the packets
        :return: True if infrared sensor exists
        """
        return any(lambda: s.get_sensors().has_proximity() for s in self.data)

    def infrared_sensor(self) -> Optional[sd.SensorData]:
        """
        return the infrared (proximity) sensor if it exists
        :return: infrared sensor if it exists, None otherwise
        """
        return sd.load_apim_proximity_from_list(self.data)

    def has_proximity_sensor(self) -> bool:
        """
        check if proximity (infrared) sensor is in any of the packets
        :return: True if proximity sensor exists
        """
        return any(lambda: s.get_sensors().has_proximity() for s in self.data)

    def proximity_sensor(self) -> Optional[sd.SensorData]:
        """
        return the proximity (infrared) sensor if it exists
        :return: proximity sensor if it exists, None otherwise
        """
        return sd.load_apim_proximity_from_list(self.data)

    def has_image_sensor(self) -> bool:
        """
        check if image sensor is in any of the packets
        :return: True if image sensor exists
        """
        return any(lambda: s.get_sensors().has_image() for s in self.data)

    def image_sensor(self) -> Optional[sd.SensorData]:
        """
        return the image sensor if it exists
        :return: image sensor if it exists, None otherwise
        """
        return sd.load_apim_image_from_list(self.data)

    def has_ambient_temperature_sensor(self) -> bool:
        """
        check if ambient temperature sensor is in any of the packets
        :return: True if ambient temperature sensor exists
        """
        return any(lambda: s.get_sensors().has_ambient_temperature() for s in self.data)

    def ambient_temperature_sensor(self) -> Optional[sd.SensorData]:
        """
        return the ambient temperature sensor if it exists
        :return: image ambient temperature if it exists, None otherwise
        """
        return sd.load_apim_ambient_temp_from_list(self.data)

    def has_relative_humidity_sensor(self) -> bool:
        """
        check if relative humidity sensor is in any of the packets
        :return: True if linear relative humidity sensor exists
        """
        return any(lambda: s.get_sensors().has_relative_humidity() for s in self.data)

    def relative_humidity_sensor(self) -> Optional[sd.SensorData]:
        """
        return the relative humidity sensor if it exists
        :return: relative humidity sensor if it exists, None otherwise
        """
        return sd.load_apim_rel_humidity_from_list(self.data)

    def has_gravity_sensor(self) -> bool:
        """
        check if gravity sensor is in any of the packets
        :return: True if gravity sensor exists
        """
        return any(lambda: s.get_sensors().has_gravity() for s in self.data)

    def gravity_sensor(self) -> Optional[sd.SensorData]:
        """
        return the gravity sensor if it exists
        :return: gravity sensor if it exists, None otherwise
        """
        return sd.load_apim_gravity_from_list(self.data)

    def has_linear_acceleration_sensor(self) -> bool:
        """
        check if linear acceleration sensor is in any of the packets
        :return: True if linear acceleration sensor exists
        """
        return any(lambda: s.get_sensors().has_linear_acceleration() for s in self.data)

    def linear_acceleration_sensor(self) -> Optional[sd.SensorData]:
        """
        return the linear acceleration sensor if it exists
        :return: linear acceleration sensor if it exists, None otherwise
        """
        return sd.load_apim_linear_accel_from_list(self.data)

    def has_orientation_sensor(self) -> bool:
        """
        check if orientation sensor is in any of the packets
        :return: True if orientation sensor exists
        """
        return any(lambda: s.get_sensors().has_orientation() for s in self.data)

    def orientation_sensor(self) -> Optional[sd.SensorData]:
        """
        return the orientation sensor if it exists
        :return: orientation sensor if it exists, None otherwise
        """
        return sd.load_apim_orientation_from_list(self.data)

    def has_rotation_vector_sensor(self) -> bool:
        """
        check if rotation vector sensor is in any of the packets
        :return: True if rotation vector sensor exists
        """
        return any(lambda: s.get_sensors().has_rotation_vector() for s in self.data)

    def rotation_vector_sensor(self) -> Optional[sd.SensorData]:
        """
        return the rotation vector sensor if it exists
        :return: rotation vector sensor if it exists, None otherwise
        """
        return sd.load_apim_rotation_vector_from_list(self.data)

    def has_compressed_audio_sensor(self) -> bool:
        """
        check if compressed audio sensor is in any of the packets
        :return: True if compressed audio sensor exists
        """
        return any(lambda: s.get_sensors().has_compressed_audio() for s in self.data)

    def compressed_audio_sensor(self) -> Optional[sd.SensorData]:
        """
        return the compressed audio sensor if it exists
        :return: compressed audio sensor if it exists, None otherwise
        """
        return sd.load_apim_compressed_audio_from_list(self.data)

    def health_sensor(self) -> Optional[sd.SensorData]:
        """
        return the station health sensor if it exists
        :return: station health sensor if it exists, None otherwise
        """
        return sd.load_apim_health_from_list(self.data)

    def get_all_sensors(self) -> Dict[sd.SensorType, sd.SensorData]:
        """
        return all sensors in the station object
        :return: dict of sensor type and sensor data of all sensors in the station
        """
        result: Dict[sd.SensorType, sd.SensorData] = {}
        if self.has_audio_sensor():
            result[sd.SensorType.AUDIO] = self.audio_sensor()
        if self.has_compressed_audio_sensor():
            result[sd.SensorType.COMPRESSED_AUDIO] = self.compressed_audio_sensor()
        if self.has_image_sensor():
            result[sd.SensorType.IMAGE] = self.image_sensor()
        if self.has_location_sensor():
            result[sd.SensorType.LOCATION] = self.location_sensor()
        if self.has_pressure_sensor():
            result[sd.SensorType.PRESSURE] = self.pressure_sensor()
        if self.has_light_sensor():
            result[sd.SensorType.LIGHT] = self.light_sensor()
        if self.has_ambient_temperature_sensor():
            result[sd.SensorType.AMBIENT_TEMPERATURE] = self.ambient_temperature_sensor()
        if self.has_relative_humidity_sensor():
            result[sd.SensorType.RELATIVE_HUMIDITY] = self.relative_humidity_sensor()
        if self.has_proximity_sensor():
            result[sd.SensorType.PROXIMITY] = self.proximity_sensor()
        if self.has_accelerometer_sensor():
            result[sd.SensorType.ACCELEROMETER] = self.accelerometer_sensor()
        if self.has_gyroscope_sensor():
            result[sd.SensorType.GYROSCOPE] = self.gyroscope_sensor()
        if self.has_magnetometer_sensor():
            result[sd.SensorType.MAGNETOMETER] = self.magnetometer_sensor()
        if self.has_gravity_sensor():
            result[sd.SensorType.GRAVITY] = self.gravity_sensor()
        if self.has_linear_acceleration_sensor():
            result[sd.SensorType.LINEAR_ACCELERATION] = self.linear_acceleration_sensor()
        if self.has_orientation_sensor():
            result[sd.SensorType.ORIENTATION] = self.orientation_sensor()
        if self.has_rotation_vector_sensor():
            result[sd.SensorType.ROTATION_VECTOR] = self.rotation_vector_sensor()
        if self.health_sensor().num_samples() > 0:
            result[sd.SensorType.STATION_HEALTH] = self.health_sensor()
        return result
