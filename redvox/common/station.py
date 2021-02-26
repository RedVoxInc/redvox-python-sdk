"""
Defines generic station objects for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
Utilizes WrappedRedvoxPacketM (API M data packets) as the format of the data due to their versatility
"""
from typing import List, Optional, Dict
from itertools import repeat
from types import FunctionType

import numpy as np

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.common import sensor_data as sd
from redvox.common.station_utils import StationKey, StationMetadata
from redvox.common.timesync import TimeSyncAnalysis
from redvox.common import offset_model as om


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
    elif all(
        lambda: t.get_station_information().get_id()
        == data_packets[0].get_station_information().get_id()
        and t.get_station_information().get_uuid()
        == data_packets[0].get_station_information().get_uuid()
        and t.get_timing_information().get_app_start_mach_timestamp()
        == data_packets[0].get_timing_information().get_app_start_mach_timestamp()
        for t in data_packets
    ):
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
        data: dict of sensor type and sensor data associated with the station, default empty dictionary
        metadata: list of StationMetadata that didn't go into the sensor data, default empty list
        id: str id of the station, default None
        uuid: str uuid of the station, default None
        start_timestamp: float of microseconds since epoch UTC when the station started recording, default np.nan
        key: Tuple of str, str, float, a unique combination of three values defining the station, default None
        first_data_timestamp: float of microseconds since epoch UTC of the first data point, default np.nan
        last_data_timestamp: float of microseconds since epoch UTC of the last data point, default np.nan
        app_name: str of the name of the app used to record the data, default empty string
        audio_sample_rate_hz: float of sample rate of audio component in hz, default np.nan
        is_audio_scrambled: bool, True if audio data is scrambled, default False
        is_timestamps_updated: bool, True if timestamps have been altered from original data values, default False
        timesync_analysis: TimeSyncAnalysis object, contains information about the station's timing values
    """

    def __init__(self, data_packets: Optional[List[WrappedRedvoxPacketM]] = None):
        """
        initialize Station
        :param data_packets: optional list of data packets representing the station, default None
        """
        self.data = {}
        self.metadata = []
        if data_packets and validate_station_data(data_packets):
            self.id = data_packets[0].get_station_information().get_id()
            self.uuid = data_packets[0].get_station_information().get_uuid()
            self.start_timestamp = (
                data_packets[0].get_timing_information().get_app_start_mach_timestamp()
            )
            self._set_all_sensors(data_packets)
            self._get_start_and_end_timestamps()
            if self.has_audio_sensor():
                self.audio_sample_rate_hz = self.audio_sensor().sample_rate
                self.is_audio_scrambled = (
                    data_packets[0].get_sensors().get_audio().get_is_scrambled()
                )
            else:
                self.audio_sample_rate_hz = np.nan
                self.is_audio_scrambled = False
            self.timesync_analysis = \
                TimeSyncAnalysis(self.id, self.audio_sample_rate_hz, self.start_timestamp).from_packets(data_packets)
            if data_packets and validate_station_data(data_packets):
                self.offset_model = om.OffsetModel(self.timesync_analysis.get_latencies(),
                                                   self.timesync_analysis.get_offsets(),
                                                   self.timesync_analysis.get_start_times() +
                                                   0.5*self.get_mean_packet_duration(),
                                                   5, 3, self.first_data_timestamp, self.last_data_timestamp)
        else:
            if data_packets:
                print(
                    "Warning: Data given to create station is not consistent; check station_id, station_uuid "
                    "and app_start_time of the packets."
                )
            self.id = None
            self.uuid = None
            self.start_timestamp = np.nan
            self.first_data_timestamp = np.nan
            self.last_data_timestamp = np.nan
            self.audio_sample_rate_hz = np.nan
            self.is_audio_scrambled = False
            self.timesync_analysis = TimeSyncAnalysis()
        self.is_timestamps_updated = False

    def _sort_metadata_packets(self):
        """
        orders the metadata packets by their starting timestamps.  Returns nothing, sorts the data in place
        """
        self.metadata.sort(
            key=lambda t: t.packet_start_mach_timestamp
        )

    def _get_start_and_end_timestamps(self):
        """
        uses the sorted metadata packets to get the first and last timestamp of the station
        """
        self.first_data_timestamp = self.audio_sensor().first_data_timestamp()
        self.last_data_timestamp = self.audio_sensor().last_data_timestamp()

    def set_id(self, station_id: str) -> "Station":
        """
        set the station's id
        :param station_id: id of station
        :return: modified version of self
        """
        self.id = station_id
        return self

    def get_id(self) -> Optional[str]:
        """
        :return: the station id or None if it doesn't exist
        """
        return self.id

    def set_uuid(self, uuid: str) -> "Station":
        """
        set the station's uuid
        :param uuid: uuid of station
        :return: modified version of self
        """
        self.uuid = uuid
        return self

    def get_uuid(self) -> Optional[str]:
        """
        :return: the station uuid or None if it doesn't exist
        """
        return self.uuid

    def set_start_timestamp(self, start_timestamp: float) -> "Station":
        """
        set the station's start timestamp in microseconds since epoch utc
        :param start_timestamp: start_timestamp of station
        :return: modified version of self
        """
        self.start_timestamp = start_timestamp
        return self

    def get_start_timestamp(self) -> float:
        """
        :return: the station start timestamp or np.nan if it doesn't exist
        """
        return self.start_timestamp

    def check_key(self) -> bool:
        """
        check if the station has enough information to set its key.
        :return: True if key can be set, False if not enough information
        """
        if self.id:
            if self.uuid:
                if not np.isnan(self.start_timestamp):
                    return True
                print("WARNING: Station start timestamp is not valid.")
            else:
                print("WARNING: Station uuid is not valid.")
        else:
            print("WARNING: Station id is not set.")
        return False

    def get_key(self) -> Optional[StationKey]:
        """
        :return: the station's key if id, uuid and start timestamp is set, or None if key cannot be created
        """
        if self.check_key():
            return StationKey(self.id, self.uuid, self.start_timestamp)
        return None

    def append_station(self, new_station: "Station"):
        """
        append a new station to the current station; does nothing if keys do not match
        :param new_station: Station to append to current station
        """
        if self.get_key() is not None and new_station.get_key() == self.get_key():
            self.append_station_data(new_station.data)
            self.metadata.extend(new_station.metadata)
            self._sort_metadata_packets()
            self._get_start_and_end_timestamps()
            new_timesync_analysis = TimeSyncAnalysis(
                self.id, self.audio_sample_rate_hz, self.start_timestamp,
                self.timesync_analysis.timesync_data + new_station.timesync_analysis.timesync_data
            )
            self.timesync_analysis = new_timesync_analysis

    def append_station_data(self, new_station_data: Dict[sd.SensorType, sd.SensorData]):
        """
        append new station data to existing station data
        :param new_station_data: the dictionary of data to add
        """
        for sensor_type, sensor_data in new_station_data.items():
            self.append_sensor(sensor_data)

    def append_sensor(self, sensor_data: sd.SensorData):
        """
        append sensor data to an existing sensor_type or add a new sensor to the dictionary
        :param sensor_data: the data to append
        """
        if sensor_data.type in self.data.keys():
            self.data[sensor_data.type] = self.data[sensor_data.type].append_data(sensor_data.data_df)
        else:
            self._add_sensor(sensor_data.type, sensor_data)

    def _delete_sensor(self, sensor_type: sd.SensorType):
        """
        removes a sensor from the sensor data dictionary if it exists
        :param sensor_type: the sensor to remove
        """
        if sensor_type in self.data.keys():
            self.data.pop(sensor_type)

    def _add_sensor(self, sensor_type: sd.SensorType, sensor: sd.SensorData):
        """
        adds a sensor to the sensor data dictionary
        :param sensor_type: the type of sensor to add
        :param sensor: the sensor data to add
        """
        if sensor_type in self.data.keys():
            raise ValueError(f"Cannot add sensor type ({sensor_type.name}) that already exists in packet!")
        else:
            self.data[sensor_type] = sensor

    def get_mean_packet_duration(self) -> float:
        """
        calculate the mean packet duration using the stations' packets
        :return: mean duration of packets in microseconds
        """
        return np.mean(
            [tsd.packet_duration for tsd in self.timesync_analysis.timesync_data]
        )

    def get_mean_packet_audio_samples(self) -> float:
        """
        calculate the mean number of audio samples per packet using the
          number of audio sensor's data points and the number of packets
        :return: mean number of audio samples per packet
        """
        return self.audio_sensor().num_samples() / len(self.metadata)

    def has_audio_sensor(self) -> bool:
        """
        check if audio sensor is in the station's data
        :return: True if audio sensor exists
        """
        return sd.SensorType.AUDIO in self.data.keys()

    def has_audio_data(self) -> bool:
        """
        check if the audio sensor has any data
        :return: True if audio sensor has any data
        """
        return self.has_audio_sensor() and self.audio_sensor().num_samples() > 0

    def audio_sensor(self) -> Optional[sd.SensorData]:
        """
        return the audio sensor if it exists
        :return: audio sensor if it exists, None otherwise
        """
        if self.has_audio_sensor():
            return self.data[sd.SensorType.AUDIO]
        return None

    def set_audio_sensor(
        self, audio_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the audio sensor; can remove audio sensor by passing None
        :param audio_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_audio_sensor():
            self._delete_sensor(sd.SensorType.AUDIO)
        if audio_sensor is not None:
            self._add_sensor(sd.SensorType.AUDIO, audio_sensor)
        return self

    def has_location_sensor(self) -> bool:
        """
        check if location sensor is in the station's data
        :return: True if location sensor exists
        """
        return sd.SensorType.LOCATION in self.data.keys()

    def has_location_data(self) -> bool:
        """
        check if the location sensor has any data
        :return: True if location sensor has any data
        """
        return self.has_location_sensor() and self.location_sensor().num_samples() > 0

    def location_sensor(self) -> Optional[sd.SensorData]:
        """
        return the location sensor if it exists
        :return: location sensor if it exists, None otherwise
        """
        if self.has_location_sensor():
            return self.data[sd.SensorType.LOCATION]
        return None

    def set_location_sensor(
        self, loc_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the location sensor; can remove location sensor by passing None
        :param loc_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_location_sensor():
            self._delete_sensor(sd.SensorType.LOCATION)
        if loc_sensor is not None:
            self._add_sensor(sd.SensorType.LOCATION, loc_sensor)
        return self

    def has_accelerometer_sensor(self) -> bool:
        """
        check if accelerometer sensor is in the station's data
        :return: True if accelerometer sensor exists
        """
        return sd.SensorType.ACCELEROMETER in self.data.keys()

    def has_accelerometer_data(self) -> bool:
        """
        check if the accelerometer sensor has any data
        :return: True if accelerometer sensor has any data
        """
        return (
            self.has_accelerometer_sensor()
            and self.accelerometer_sensor().num_samples() > 0
        )

    def accelerometer_sensor(self) -> Optional[sd.SensorData]:
        """
        return the accelerometer sensor if it exists
        :return: accelerometer sensor if it exists, None otherwise
        """
        if self.has_accelerometer_sensor():
            return self.data[sd.SensorType.ACCELEROMETER]
        return None

    def set_accelerometer_sensor(
        self, acc_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the accelerometer sensor; can remove accelerometer sensor by passing None
        :param acc_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_accelerometer_sensor():
            self._delete_sensor(sd.SensorType.ACCELEROMETER)
        if acc_sensor is not None:
            self._add_sensor(sd.SensorType.ACCELEROMETER, acc_sensor)
        return self

    def has_magnetometer_sensor(self) -> bool:
        """
        check if magnetometer sensor is in the station's data
        :return: True if magnetometer sensor exists
        """
        return sd.SensorType.MAGNETOMETER in self.data.keys()

    def has_magnetometer_data(self) -> bool:
        """
        check if the magnetometer sensor has any data
        :return: True if magnetometer sensor has any data
        """
        return (
            self.has_magnetometer_sensor()
            and self.magnetometer_sensor().num_samples() > 0
        )

    def magnetometer_sensor(self) -> Optional[sd.SensorData]:
        """
        return the magnetometer sensor if it exists
        :return: magnetometer sensor if it exists, None otherwise
        """
        if self.has_magnetometer_sensor():
            return self.data[sd.SensorType.MAGNETOMETER]
        return None

    def set_magnetometer_sensor(
        self, mag_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the magnetometer sensor; can remove magnetometer sensor by passing None
        :param mag_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_magnetometer_sensor():
            self._delete_sensor(sd.SensorType.MAGNETOMETER)
        if mag_sensor is not None:
            self._add_sensor(sd.SensorType.MAGNETOMETER, mag_sensor)
        return self

    def has_gyroscope_sensor(self) -> bool:
        """
        check if gyroscope sensor is in the station's data
        :return: True if gyroscope sensor exists
        """
        return sd.SensorType.GYROSCOPE in self.data.keys()

    def has_gyroscope_data(self) -> bool:
        """
        check if the gyroscope sensor has any data
        :return: True if gyroscope sensor has any data
        """
        return self.has_gyroscope_sensor() and self.gyroscope_sensor().num_samples() > 0

    def gyroscope_sensor(self) -> Optional[sd.SensorData]:
        """
        return the gyroscope sensor if it exists
        :return: gyroscope sensor if it exists, None otherwise
        """
        if self.has_gyroscope_sensor():
            return self.data[sd.SensorType.GYROSCOPE]
        return None

    def set_gyroscope_sensor(
        self, gyro_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the gyroscope sensor; can remove gyroscope sensor by passing None
        :param gyro_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_gyroscope_sensor():
            self._delete_sensor(sd.SensorType.GYROSCOPE)
        if gyro_sensor is not None:
            self._add_sensor(sd.SensorType.GYROSCOPE, gyro_sensor)
        return self

    def has_pressure_sensor(self) -> bool:
        """
        check if pressure sensor is in the station's data
        :return: True if pressure sensor exists
        """
        return sd.SensorType.PRESSURE in self.data.keys()

    def has_pressure_data(self) -> bool:
        """
        check if the pressure sensor has any data
        :return: True if pressure sensor has any data
        """
        return self.has_pressure_sensor() and self.pressure_sensor().num_samples() > 0

    def pressure_sensor(self) -> Optional[sd.SensorData]:
        """
        return the pressure sensor if it exists
        :return: pressure sensor if it exists, None otherwise
        """
        if self.has_pressure_sensor():
            return self.data[sd.SensorType.PRESSURE]
        return None

    def set_pressure_sensor(
        self, pressure_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the pressure sensor; can remove pressure sensor by passing None
        :param pressure_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_pressure_sensor():
            self._delete_sensor(sd.SensorType.PRESSURE)
        if pressure_sensor is not None:
            self._add_sensor(sd.SensorType.PRESSURE, pressure_sensor)
        return self

    def has_barometer_sensor(self) -> bool:
        """
        check if barometer (aka pressure) sensor is in any of the packets
        :return: True if barometer sensor exists
        """
        return self.has_pressure_sensor()

    def has_barometer_data(self) -> bool:
        """
        check if the barometer (aka pressure)  sensor has any data
        :return: True if barometer sensor has any data
        """
        return self.has_pressure_data()

    def barometer_sensor(self) -> Optional[sd.SensorData]:
        """
        return the barometer (aka pressure) sensor if it exists
        :return: barometer sensor if it exists, None otherwise
        """
        return self.pressure_sensor()

    def set_barometer_sensor(
        self, bar_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the barometer (pressure) sensor; can remove barometer sensor by passing None
        :param bar_sensor: the SensorData to set or None
        :return: the edited station
        """
        return self.set_pressure_sensor(bar_sensor)

    def has_light_sensor(self) -> bool:
        """
        check if light sensor is in the station's data
        :return: True if light sensor exists
        """
        return sd.SensorType.LIGHT in self.data.keys()

    def has_light_data(self) -> bool:
        """
        check if the light sensor has any data
        :return: True if light sensor has any data
        """
        return self.has_light_sensor() and self.light_sensor().num_samples() > 0

    def light_sensor(self) -> Optional[sd.SensorData]:
        """
        return the light sensor if it exists
        :return: light sensor if it exists, None otherwise
        """
        if self.has_light_sensor():
            return self.data[sd.SensorType.LIGHT]
        return None

    def set_light_sensor(
        self, light_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the light sensor; can remove light sensor by passing None
        :param light_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_light_sensor():
            self._delete_sensor(sd.SensorType.LIGHT)
        if light_sensor is not None:
            self._add_sensor(sd.SensorType.LIGHT, light_sensor)
        return self

    def has_infrared_sensor(self) -> bool:
        """
        check if infrared (proximity) sensor is in any of the packets
        :return: True if infrared sensor exists
        """
        return self.has_proximity_sensor()

    def has_infrared_data(self) -> bool:
        """
        check if infrared (proximity) sensor has any data
        :return: True if infrared sensor has any data
        """
        return self.has_proximity_data()

    def infrared_sensor(self) -> Optional[sd.SensorData]:
        """
        return the infrared (proximity) sensor if it exists
        :return: infrared sensor if it exists, None otherwise
        """
        return self.proximity_sensor()

    def set_infrared_sensor(
        self, infrd_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the infrared sensor; can remove infrared sensor by passing None
        :param infrd_sensor: the SensorData to set or None
        :return: the edited Station
        """
        return self.set_proximity_sensor(infrd_sensor)

    def has_proximity_sensor(self) -> bool:
        """
        check if proximity sensor is in the station's data
        :return: True if proximity sensor exists
        """
        return sd.SensorType.PROXIMITY in self.data.keys()

    def has_proximity_data(self) -> bool:
        """
        check if the proximity sensor has any data
        :return: True if proximity sensor has any data
        """
        return self.has_proximity_sensor() and self.proximity_sensor().num_samples() > 0

    def proximity_sensor(self) -> Optional[sd.SensorData]:
        """
        return the proximity sensor if it exists
        :return: proximity sensor if it exists, None otherwise
        """
        if self.has_proximity_sensor():
            return self.data[sd.SensorType.PROXIMITY]
        return None

    def set_proximity_sensor(
        self, proximity_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the proximity sensor; can remove proximity sensor by passing None
        :param proximity_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_proximity_sensor():
            self._delete_sensor(sd.SensorType.PROXIMITY)
        if proximity_sensor is not None:
            self._add_sensor(sd.SensorType.PROXIMITY, proximity_sensor)
        return self

    def has_image_sensor(self) -> bool:
        """
        check if image sensor is in the station's data
        :return: True if image sensor exists
        """
        return sd.SensorType.IMAGE in self.data.keys()

    def has_image_data(self) -> bool:
        """
        check if the image sensor has any data
        :return: True if image sensor has any data
        """
        return self.has_image_sensor() and self.image_sensor().num_samples() > 0

    def image_sensor(self) -> Optional[sd.SensorData]:
        """
        return the image sensor if it exists
        :return: image sensor if it exists, None otherwise
        """
        if self.has_image_sensor():
            return self.data[sd.SensorType.IMAGE]
        return None

    def set_image_sensor(self, img_sensor: Optional[sd.SensorData] = None) -> "Station":
        """
        sets the image sensor; can remove image sensor by passing None
        :param img_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_image_sensor():
            self._delete_sensor(sd.SensorType.IMAGE)
        if img_sensor is not None:
            self._add_sensor(sd.SensorType.IMAGE, img_sensor)
        return self

    def has_ambient_temperature_sensor(self) -> bool:
        """
        check if ambient temperature sensor is in the station's data
        :return: True if ambient temperature sensor exists
        """
        return sd.SensorType.AMBIENT_TEMPERATURE in self.data.keys()

    def has_ambient_temperature_data(self) -> bool:
        """
        check if the ambient temperature sensor has any data
        :return: True if ambient temperature sensor has any data
        """
        return (
            self.has_ambient_temperature_sensor()
            and self.ambient_temperature_sensor().num_samples() > 0
        )

    def ambient_temperature_sensor(self) -> Optional[sd.SensorData]:
        """
        return the ambient temperature sensor if it exists
        :return: ambient temperature sensor if it exists, None otherwise
        """
        if self.has_ambient_temperature_sensor():
            return self.data[sd.SensorType.AMBIENT_TEMPERATURE]
        return None

    def set_ambient_temperature_sensor(
        self, amb_temp_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the ambient temperature sensor; can remove ambient temperature sensor by passing None
        :param amb_temp_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_ambient_temperature_sensor():
            self._delete_sensor(sd.SensorType.AMBIENT_TEMPERATURE)
        if amb_temp_sensor is not None:
            self._add_sensor(sd.SensorType.AMBIENT_TEMPERATURE, amb_temp_sensor)
        return self

    def has_relative_humidity_sensor(self) -> bool:
        """
        check if relative humidity sensor is in the station's data
        :return: True if relative humidity sensor exists
        """
        return sd.SensorType.RELATIVE_HUMIDITY in self.data.keys()

    def has_relative_humidity_data(self) -> bool:
        """
        check if the relative humidity sensor has any data
        :return: True if relative humidity sensor has any data
        """
        return (
            self.has_relative_humidity_sensor()
            and self.relative_humidity_sensor().num_samples() > 0
        )

    def relative_humidity_sensor(self) -> Optional[sd.SensorData]:
        """
        return the relative humidity sensor if it exists
        :return: relative humidity sensor if it exists, None otherwise
        """
        if self.has_relative_humidity_sensor():
            return self.data[sd.SensorType.RELATIVE_HUMIDITY]
        return None

    def set_relative_humidity_sensor(
        self, rel_hum_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the relative humidity sensor; can remove relative humidity sensor by passing None
        :param rel_hum_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_relative_humidity_sensor():
            self._delete_sensor(sd.SensorType.RELATIVE_HUMIDITY)
        if rel_hum_sensor is not None:
            self._add_sensor(sd.SensorType.RELATIVE_HUMIDITY, rel_hum_sensor)
        return self

    def has_gravity_sensor(self) -> bool:
        """
        check if gravity sensor is in the station's data
        :return: True if gravity sensor exists
        """
        return sd.SensorType.GRAVITY in self.data.keys()

    def has_gravity_data(self) -> bool:
        """
        check if the gravity sensor has any data
        :return: True if gravity sensor has any data
        """
        return self.has_gravity_sensor() and self.gravity_sensor().num_samples() > 0

    def gravity_sensor(self) -> Optional[sd.SensorData]:
        """
        return the gravity sensor if it exists
        :return: gravity sensor if it exists, None otherwise
        """
        if self.has_gravity_sensor():
            return self.data[sd.SensorType.GRAVITY]
        return None

    def set_gravity_sensor(
        self, grav_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the gravity sensor; can remove gravity sensor by passing None
        :param grav_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_gravity_sensor():
            self._delete_sensor(sd.SensorType.GRAVITY)
        if grav_sensor is not None:
            self._add_sensor(sd.SensorType.GRAVITY, grav_sensor)
        return self

    def has_linear_acceleration_sensor(self) -> bool:
        """
        check if linear acceleration sensor is in the station's data
        :return: True if linear acceleration sensor exists
        """
        return sd.SensorType.LINEAR_ACCELERATION in self.data.keys()

    def has_linear_acceleration_data(self) -> bool:
        """
        check if the linear acceleration sensor has any data
        :return: True if linear acceleration sensor has any data
        """
        return (
            self.has_linear_acceleration_sensor()
            and self.linear_acceleration_sensor().num_samples() > 0
        )

    def linear_acceleration_sensor(self) -> Optional[sd.SensorData]:
        """
        return the linear acceleration sensor if it exists
        :return: linear acceleration sensor if it exists, None otherwise
        """
        if self.has_linear_acceleration_sensor():
            return self.data[sd.SensorType.LINEAR_ACCELERATION]
        return None

    def set_linear_acceleration_sensor(
        self, lin_acc_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the linear acceleration sensor; can remove linear acceleration sensor by passing None
        :param lin_acc_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_linear_acceleration_sensor():
            self._delete_sensor(sd.SensorType.LINEAR_ACCELERATION)
        if lin_acc_sensor is not None:
            self._add_sensor(sd.SensorType.LINEAR_ACCELERATION, lin_acc_sensor)
        return self

    def has_orientation_sensor(self) -> bool:
        """
        check if orientation sensor is in the station's data
        :return: True if orientation sensor exists
        """
        return sd.SensorType.ORIENTATION in self.data.keys()

    def has_orientation_data(self) -> bool:
        """
        check if the orientation sensor has any data
        :return: True if orientation sensor has any data
        """
        return (
            self.has_orientation_sensor()
            and self.orientation_sensor().num_samples() > 0
        )

    def orientation_sensor(self) -> Optional[sd.SensorData]:
        """
        return the orientation sensor if it exists
        :return: orientation sensor if it exists, None otherwise
        """
        if self.has_orientation_sensor():
            return self.data[sd.SensorType.ORIENTATION]
        return None

    def set_orientation_sensor(
        self, orientation_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the orientation sensor; can remove orientation sensor by passing None
        :param orientation_sensor: the SensorData to set or None
        :return: the edited Station
        """
        if self.has_orientation_sensor():
            self._delete_sensor(sd.SensorType.ORIENTATION)
        if orientation_sensor is not None:
            self._add_sensor(sd.SensorType.ORIENTATION, orientation_sensor)
        return self

    def has_rotation_vector_sensor(self) -> bool:
        """
        check if rotation vector sensor is in the station's data
        :return: True if rotation vector sensor exists
        """
        return sd.SensorType.ROTATION_VECTOR in self.data.keys()

    def has_rotation_vector_data(self) -> bool:
        """
        check if the rotation vector sensor has any data
        :return: True if rotation vector sensor has any data
        """
        return (
            self.has_rotation_vector_sensor()
            and self.rotation_vector_sensor().num_samples() > 0
        )

    def rotation_vector_sensor(self) -> Optional[sd.SensorData]:
        """
        return the rotation vector sensor if it exists
        :return: rotation vector sensor if it exists, None otherwise
        """
        if self.has_rotation_vector_sensor():
            return self.data[sd.SensorType.ROTATION_VECTOR]
        return None

    def set_rotation_vector_sensor(
        self, rot_vec_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the rotation vector sensor; can remove rotation vector sensor by passing None
        :param rot_vec_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_rotation_vector_sensor():
            self._delete_sensor(sd.SensorType.ROTATION_VECTOR)
        if rot_vec_sensor is not None:
            self._add_sensor(sd.SensorType.ROTATION_VECTOR, rot_vec_sensor)
        return self

    def has_compressed_audio_sensor(self) -> bool:
        """
        check if compressed audio sensor is in the station's data
        :return: True if compressed audio sensor exists
        """
        return sd.SensorType.COMPRESSED_AUDIO in self.data.keys()

    def has_compressed_audio_data(self) -> bool:
        """
        check if the compressed audio sensor has any data
        :return: True if compressed audio sensor has any data
        """
        return (
            self.has_compressed_audio_sensor()
            and self.compressed_audio_sensor().num_samples() > 0
        )

    def compressed_audio_sensor(self) -> Optional[sd.SensorData]:
        """
        return the compressed audio sensor if it exists
        :return: compressed audio sensor if it exists, None otherwise
        """
        if self.has_compressed_audio_sensor():
            return self.data[sd.SensorType.COMPRESSED_AUDIO]
        return None

    def set_compressed_audio_sensor(
        self, comp_audio_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the compressed audio sensor; can remove compressed audio sensor by passing None
        :param comp_audio_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_compressed_audio_sensor():
            self._delete_sensor(sd.SensorType.COMPRESSED_AUDIO)
        if comp_audio_sensor is not None:
            self._add_sensor(sd.SensorType.COMPRESSED_AUDIO, comp_audio_sensor)
        return self

    def has_health_sensor(self) -> bool:
        """
        check if health sensor (station metrics) is in any of the packets
        :return: True if health sensor exists
        """
        return sd.SensorType.STATION_HEALTH in self.data.keys()

    def has_health_data(self) -> bool:
        """
        check if health sensor (station metrics) is in any of the packets
        :return: True if health sensor exists
        """
        return self.has_health_sensor() and self.health_sensor().num_samples() > 0

    def health_sensor(self) -> Optional[sd.SensorData]:
        """
        return the station health sensor if it exists
        :return: station health sensor if it exists, None otherwise
        """
        if self.has_health_sensor():
            return self.data[sd.SensorType.STATION_HEALTH]
        return None

    def set_health_sensor(
        self, health_sensor: Optional[sd.SensorData] = None
    ) -> "Station":
        """
        sets the health sensor; can remove health sensor by passing None
        :param health_sensor: the SensorData to set or None
        :return: the edited DataPacket
        """
        if self.has_health_sensor():
            self._delete_sensor(sd.SensorType.STATION_HEALTH)
        if health_sensor is not None:
            self._add_sensor(sd.SensorType.STATION_HEALTH, health_sensor)
        return self

    def _set_all_sensors(self, packets: List[WrappedRedvoxPacketM]):
        """
        set all sensors from the packets, as well as misc. metadata, and put it in the station
        :param packets: the packets to read data from
        """
        self.data = {}
        self.metadata: List[StationMetadata] = [
            StationMetadata(
                packet.get_api(),
                packet.get_sub_api(),
                packet.get_station_information(),
                "Redvox",
                packet.get_timing_information(),
            ) for packet in packets]
        funcs = [sd.load_apim_audio_from_list,
                 sd.load_apim_compressed_audio_from_list,
                 sd.load_apim_image_from_list,
                 sd.load_apim_location_from_list,
                 sd.load_apim_pressure_from_list,
                 sd.load_apim_light_from_list,
                 sd.load_apim_ambient_temp_from_list,
                 sd.load_apim_rel_humidity_from_list,
                 sd.load_apim_proximity_from_list,
                 sd.load_apim_accelerometer_from_list,
                 sd.load_apim_gyroscope_from_list,
                 sd.load_apim_magnetometer_from_list,
                 sd.load_apim_gravity_from_list,
                 sd.load_apim_linear_accel_from_list,
                 sd.load_apim_orientation_from_list,
                 sd.load_apim_rotation_vector_from_list,
                 sd.load_apim_health_from_list,
                 ]
        sensors = map(FunctionType.__call__, funcs, repeat(packets))
        for sensor in sensors:
            if sensor:
                self.append_sensor(sensor)

    def update_timestamps(self):
        """
        updates the timestamps in the station using the offset model
        """
        if self.is_timestamps_updated:
            print("WARNING: Timestamps already corrected!")
        else:
            if not np.isnan(self.offset_model.slope):
                for sensor in self.data.values():
                    sensor.update_data_timestamps(self.offset_model)
                for packet in self.metadata:
                    packet.update_timestamps(self.offset_model)
                self.timesync_analysis.update_timestamps(self.offset_model)
                self.start_timestamp = self.offset_model.update_time(self.start_timestamp)
                self.first_data_timestamp = self.offset_model.update_time(self.first_data_timestamp)
                self.last_data_timestamp = self.offset_model.update_time(self.last_data_timestamp)
                self.is_timestamps_updated = True
