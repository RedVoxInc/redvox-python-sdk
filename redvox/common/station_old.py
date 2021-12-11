"""
Defines generic station objects for API-independent analysis
all timestamps are integers in microseconds unless otherwise stated
Utilizes WrappedRedvoxPacketM (API M data packets) as the format of the data due to their versatility
"""
from typing import List, Optional, Tuple
from itertools import repeat
from types import FunctionType

import numpy as np

from redvox.common import sensor_data_old as sd
from redvox.common import sensor_reader_utils_old as sdru
from redvox.common import station_utils as st_utils
from redvox.common.timesync_old import TimeSyncAnalysis
from redvox.common.errors import RedVoxExceptions
import redvox.api1000.proto.redvox_api_m_pb2 as api_m


class Station:
    """
    generic station for api-independent stuff; uses API M as the core data object since its quite versatile
    In order for a list of packets to be a station, all of the packets must:
        Have the same station id
        Have the same station uuid
        Have the same start time
        Have the same audio sample rate

    Properties:
        data: list sensor data associated with the station, default empty dictionary

        metadata: StationMetadata consistent across all packets, default empty StationMetadata

        packet_metadata: list of StationPacketMetadata that changes from packet to packet, default empty list

        id: str id of the station, default None

        uuid: str uuid of the station, default None

        start_timestamp: float of microseconds since epoch UTC when the station started recording, default np.nan

        first_data_timestamp: float of microseconds since epoch UTC of the first data point, default np.nan

        last_data_timestamp: float of microseconds since epoch UTC of the last data point, default np.nan

        audio_sample_rate_nominal_hz: float of nominal sample rate of audio component in hz, default np.nan

        is_audio_scrambled: bool, True if audio data is scrambled, default False

        is_timestamps_updated: bool, True if timestamps have been altered from original data values, default False

        timesync_analysis: TimeSyncAnalysis object, contains information about the station's timing values

        use_model_correction: bool, if True, time correction is done using OffsetModel functions, otherwise
        correction is done by adding the OffsetModel's best offset (intercept value).  default True

        _gaps: List of Tuples of floats indicating start and end times of gaps.  Times are not inclusive of the gap.
    """

    def __init__(
            self,
            data_packets: Optional[List[api_m.RedvoxPacketM]] = None,
            station_id: str = None,
            uuid: str = None,
            start_time: float = np.nan,
            use_model_correction: bool = True,
    ):
        """
        initialize Station

        :param data_packets: optional list of data packets representing the station, default None
        :param station_id: optional id if no data packets, default None
        :param uuid: optional uuid if no data packets, default None
        :param start_time: optional start time in microseconds since epoch UTC if no data packets, default np.nan
        :param use_model_correction: if True, use OffsetModel functions for time correction, add OffsetModel best offset
                                        (intercept value) otherwise.  Default True
        """
        self.data = []
        self.packet_metadata: List[st_utils.StationPacketMetadata] = []
        self.is_timestamps_updated = False
        self._gaps: List[Tuple[float, float]] = []
        self.errors: RedVoxExceptions = RedVoxExceptions("Station")
        self.use_model_correction = use_model_correction
        if data_packets and st_utils.validate_station_key_list(data_packets, self.errors):
            # noinspection Mypy
            self._load_metadata_from_packet(data_packets[0])
            self.timesync_analysis = TimeSyncAnalysis(
                self.id, self.audio_sample_rate_nominal_hz, self.start_timestamp
            ).from_raw_packets(data_packets)
            if self.timesync_analysis.errors.get_num_errors() > 0:
                self.errors.extend_error(self.timesync_analysis.errors)
            self._set_all_sensors(data_packets)
            self._get_start_and_end_timestamps()
        else:
            self.id = station_id
            self.uuid = uuid
            self.metadata = st_utils.StationMetadata("None")
            self.start_timestamp = start_time
            self.first_data_timestamp = np.nan
            self.last_data_timestamp = np.nan
            self.audio_sample_rate_nominal_hz = np.nan
            self.is_audio_scrambled = False
            self.timesync_analysis = TimeSyncAnalysis()
        # self.errors.print()

    def _load_metadata_from_packet(self, packet: api_m.RedvoxPacketM):
        """
        sets metadata that applies to the entire station from a single packet

        :param packet: API-M redvox packet to load metadata from
        """
        # self.id = packet.station_information.id
        self.id = packet.station_information.id.zfill(10)
        self.uuid = packet.station_information.uuid
        self.start_timestamp = packet.timing_information.app_start_mach_timestamp
        if self.start_timestamp < 0:
            self.errors.append(
                f"Station {self.id} has station start date before epoch.  "
                f"Station start date reset to np.nan"
            )
            self.start_timestamp = np.nan
        self.metadata = st_utils.StationMetadata("Redvox", packet)
        if isinstance(packet, api_m.RedvoxPacketM) and packet.sensors.HasField("audio"):
            self.audio_sample_rate_nominal_hz = packet.sensors.audio.sample_rate
            self.is_audio_scrambled = packet.sensors.audio.is_scrambled
        else:
            self.audio_sample_rate_nominal_hz = np.nan
            self.is_audio_scrambled = False

    def _sort_metadata_packets(self):
        """
        orders the metadata packets by their starting timestamps.  Returns nothing, sorts the data in place
        """
        self.packet_metadata.sort(key=lambda t: t.packet_start_mach_timestamp)

    def _get_start_and_end_timestamps(self):
        """
        uses the sorted metadata packets to get the first and last timestamp of the station
        """
        self.first_data_timestamp = self.audio_sensor().first_data_timestamp()
        self.last_data_timestamp = self.audio_sensor().last_data_timestamp()

    def print_errors(self):
        """
        prints errors to screen
        """
        self.errors.print()

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
                if np.isnan(self.start_timestamp):
                    self.errors.append("Station start timestamp not defined.")
                return True
            else:
                self.errors.append("Station uuid is not valid.")
        else:
            self.errors.append("Station id is not set.")
        return False

    def get_key(self) -> Optional[st_utils.StationKey]:
        """
        :return: the station's key if id, uuid and start timestamp is set, or None if key cannot be created
        """
        if self.check_key():
            return st_utils.StationKey(self.id, self.uuid, self.start_timestamp)
        return None

    def append_station(self, new_station: "Station"):
        """
        append a new station to the current station; does nothing if keys do not match

        :param new_station: Station to append to current station
        """
        if (
                self.get_key() is not None
                and new_station.get_key() == self.get_key()
                and self.metadata.validate_metadata(new_station.metadata)
        ):
            self.append_station_data(new_station.data)
            self.packet_metadata.extend(new_station.packet_metadata)
            self._sort_metadata_packets()
            self._get_start_and_end_timestamps()
            self.timesync_analysis = TimeSyncAnalysis(
                self.id,
                self.audio_sample_rate_nominal_hz,
                self.start_timestamp,
                self.timesync_analysis.timesync_data
                + new_station.timesync_analysis.timesync_data,
                )

    def append_station_data(self, new_station_data: List[sd.SensorData]):
        """
        append new station data to existing station data

        :param new_station_data: the dictionary of data to add
        """
        for sensor_data in new_station_data:
            self.append_sensor(sensor_data)

    def get_station_sensor_types(self) -> List[sd.SensorType]:
        """
        :return: a list of sensor types in the station
        """
        return [s.type for s in self.data]

    def get_sensor_by_type(self, sensor_type: sd.SensorType) -> Optional[sd.SensorData]:
        """
        :param sensor_type: type of sensor to get
        :return: the sensor of the type or None if it doesn't exist
        """
        for s in self.data:
            if s.type == sensor_type:
                return s
        return None

    def append_sensor(self, sensor_data: sd.SensorData):
        """
        append sensor data to an existing sensor_type or add a new sensor to the dictionary

        :param sensor_data: the data to append
        """
        if sensor_data.type in self.get_station_sensor_types():
            self.get_sensor_by_type(sensor_data.type).append_data(sensor_data.data_df)
        else:
            self._add_sensor(sensor_data.type, sensor_data)
        self.errors.extend_error(sensor_data.errors)

    def _delete_sensor(self, sensor_type: sd.SensorType):
        """
        removes a sensor from the sensor data dictionary if it exists

        :param sensor_type: the sensor to remove
        """
        if sensor_type in self.get_station_sensor_types():
            self.data.remove(self.get_sensor_by_type(sensor_type))

    def _add_sensor(self, sensor_type: sd.SensorType, sensor: sd.SensorData):
        """
        adds a sensor to the sensor data dictionary

        :param sensor_type: the type of sensor to add
        :param sensor: the sensor data to add
        """
        if sensor_type in self.get_station_sensor_types():
            raise ValueError(
                f"Cannot add sensor type ({sensor_type.name}) that already exists in packet!"
            )
        else:
            self.data.append(sensor)

    def get_mean_packet_duration(self) -> float:
        """
        :return: mean duration of packets in microseconds
        """
        return float(
            np.mean(
                [tsd.packet_duration for tsd in self.timesync_analysis.timesync_data]
            )
        )

    def get_mean_packet_audio_samples(self) -> float:
        """
        calculate the mean number of audio samples per packet using the
          number of audio sensor's data points and the number of packets

        :return: mean number of audio samples per packet
        """
        # noinspection Mypy
        return self.audio_sensor().num_samples() / len(self.packet_metadata)

    def has_timesync_data(self) -> bool:
        """
        :return: True if there is timesync data for the station
        """
        return len(self.timesync_analysis.timesync_data) > 0

    def has_audio_sensor(self) -> bool:
        """
        :return: True if audio sensor exists
        """
        return sd.SensorType.AUDIO in self.get_station_sensor_types()

    def has_audio_data(self) -> bool:
        """
        :return: True if audio sensor exists and has any data
        """
        audio_sensor: Optional[sd.AudioSensor] = self.audio_sensor()
        return audio_sensor is not None and audio_sensor.num_samples() > 0

    def audio_sensor(self) -> Optional[sd.AudioSensor]:
        """
        :return: audio sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.AUDIO)

    def set_audio_sensor(
            self, audio_sensor: Optional[sd.AudioSensor] = None
    ) -> "Station":
        """
        sets the audio sensor; can remove audio sensor by passing None

        :param audio_sensor: the AudioSensor to set or None
        :return: the edited Station
        """
        if self.has_audio_sensor():
            self._delete_sensor(sd.SensorType.AUDIO)
        if audio_sensor is not None:
            self._add_sensor(sd.SensorType.AUDIO, audio_sensor)
        return self

    def has_location_sensor(self) -> bool:
        """
        :return: True if location sensor exists
        """
        return sd.SensorType.LOCATION in self.get_station_sensor_types()

    def has_location_data(self) -> bool:
        """
        :return: True if location sensor exists and has any data
        """
        location_sensor: Optional[sd.LocationSensor] = self.location_sensor()
        return location_sensor is not None and location_sensor.num_samples() > 0

    def location_sensor(self) -> Optional[sd.LocationSensor]:
        """
        :return: location sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.LOCATION)

    def set_location_sensor(
            self, loc_sensor: Optional[sd.LocationSensor] = None
    ) -> "Station":
        """
        sets the location sensor; can remove location sensor by passing None

        :param loc_sensor: the LocationSensor to set or None
        :return: the edited Station
        """
        if self.has_location_sensor():
            self._delete_sensor(sd.SensorType.LOCATION)
        if loc_sensor is not None:
            self._add_sensor(sd.SensorType.LOCATION, loc_sensor)
        return self

    def has_best_location_sensor(self) -> bool:
        """
        :return: True if best location sensor exists
        """
        return sd.SensorType.BEST_LOCATION in self.get_station_sensor_types()

    def has_best_location_data(self) -> bool:
        """
        :return: True if best location sensor exists and has any data
        """
        location_sensor: Optional[sd.BestLocationSensor] = self.best_location_sensor()
        return location_sensor is not None and location_sensor.num_samples() > 0

    def best_location_sensor(self) -> Optional[sd.BestLocationSensor]:
        """
        :return: best location sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.BEST_LOCATION)

    def set_best_location_sensor(
            self, best_loc_sensor: Optional[sd.BestLocationSensor] = None
    ) -> "Station":
        """
        sets the best location sensor; can remove location sensor by passing None

        :param best_loc_sensor: the BestLocationSensor to set or None
        :return: the edited Station
        """
        if self.has_best_location_sensor():
            self._delete_sensor(sd.SensorType.BEST_LOCATION)
        if best_loc_sensor is not None:
            self._add_sensor(sd.SensorType.BEST_LOCATION, best_loc_sensor)
        return self

    def has_accelerometer_sensor(self) -> bool:
        """
        :return: True if accelerometer sensor exists
        """
        return sd.SensorType.ACCELEROMETER in self.get_station_sensor_types()

    def has_accelerometer_data(self) -> bool:
        """
        :return: True if accelerometer sensor exists and has any data
        """
        sensor: Optional[sd.AccelerometerSensor] = self.accelerometer_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def accelerometer_sensor(self) -> Optional[sd.AccelerometerSensor]:
        """
        :return: accelerometer sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.ACCELEROMETER)

    def set_accelerometer_sensor(
            self, acc_sensor: Optional[sd.AccelerometerSensor] = None
    ) -> "Station":
        """
        sets the accelerometer sensor; can remove accelerometer sensor by passing None

        :param acc_sensor: the AccelerometerSensor to set or None
        :return: the edited Station
        """
        if self.has_accelerometer_sensor():
            self._delete_sensor(sd.SensorType.ACCELEROMETER)
        if acc_sensor is not None:
            self._add_sensor(sd.SensorType.ACCELEROMETER, acc_sensor)
        return self

    def has_magnetometer_sensor(self) -> bool:
        """
        :return: True if magnetometer sensor exists
        """
        return sd.SensorType.MAGNETOMETER in self.get_station_sensor_types()

    def has_magnetometer_data(self) -> bool:
        """
        :return: True if magnetometer sensor exists and has any data
        """
        sensor: Optional[sd.MagnetometerSensor] = self.magnetometer_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def magnetometer_sensor(self) -> Optional[sd.MagnetometerSensor]:
        """
        :return: magnetometer sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.MAGNETOMETER)

    def set_magnetometer_sensor(
            self, mag_sensor: Optional[sd.MagnetometerSensor] = None
    ) -> "Station":
        """
        sets the magnetometer sensor; can remove magnetometer sensor by passing None

        :param mag_sensor: the MagnetometerSensor to set or None
        :return: the edited Station
        """
        if self.has_magnetometer_sensor():
            self._delete_sensor(sd.SensorType.MAGNETOMETER)
        if mag_sensor is not None:
            self._add_sensor(sd.SensorType.MAGNETOMETER, mag_sensor)
        return self

    def has_gyroscope_sensor(self) -> bool:
        """
        :return: True if gyroscope sensor exists
        """
        return sd.SensorType.GYROSCOPE in self.get_station_sensor_types()

    def has_gyroscope_data(self) -> bool:
        """
        :return: True if gyroscope sensor exists and has any data
        """
        sensor: Optional[sd.GyroscopeSensor] = self.gyroscope_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def gyroscope_sensor(self) -> Optional[sd.GyroscopeSensor]:
        """
        :return: gyroscope sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.GYROSCOPE)

    def set_gyroscope_sensor(
            self, gyro_sensor: Optional[sd.GyroscopeSensor] = None
    ) -> "Station":
        """
        sets the gyroscope sensor; can remove gyroscope sensor by passing None

        :param gyro_sensor: the GyroscopeSensor to set or None
        :return: the edited Station
        """
        if self.has_gyroscope_sensor():
            self._delete_sensor(sd.SensorType.GYROSCOPE)
        if gyro_sensor is not None:
            self._add_sensor(sd.SensorType.GYROSCOPE, gyro_sensor)
        return self

    def has_pressure_sensor(self) -> bool:
        """
        :return: True if pressure sensor exists
        """
        return sd.SensorType.PRESSURE in self.get_station_sensor_types()

    def has_pressure_data(self) -> bool:
        """
        :return: True if pressure sensor exists and has any data
        """
        sensor: Optional[sd.PressureSensor] = self.pressure_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def pressure_sensor(self) -> Optional[sd.PressureSensor]:
        """
        :return: pressure sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.PRESSURE)

    def set_pressure_sensor(
            self, pressure_sensor: Optional[sd.PressureSensor] = None
    ) -> "Station":
        """
        sets the pressure sensor; can remove pressure sensor by passing None

        :param pressure_sensor: the PressureSensor to set or None
        :return: the edited Station
        """
        if self.has_pressure_sensor():
            self._delete_sensor(sd.SensorType.PRESSURE)
        if pressure_sensor is not None:
            self._add_sensor(sd.SensorType.PRESSURE, pressure_sensor)
        return self

    def has_barometer_sensor(self) -> bool:
        """
        :return: True if barometer (pressure) sensor exists
        """
        return self.has_pressure_sensor()

    def has_barometer_data(self) -> bool:
        """
        :return: True if barometer (pressure) sensor exists and has any data
        """
        return self.has_pressure_data()

    def barometer_sensor(self) -> Optional[sd.PressureSensor]:
        """
        :return: barometer (pressure) sensor if it exists, None otherwise
        """
        return self.pressure_sensor()

    def set_barometer_sensor(
            self, bar_sensor: Optional[sd.PressureSensor] = None
    ) -> "Station":
        """
        sets the barometer (pressure) sensor; can remove barometer sensor by passing None

        :param bar_sensor: the PressureSensor to set or None
        :return: the edited station
        """
        return self.set_pressure_sensor(bar_sensor)

    def has_light_sensor(self) -> bool:
        """
        :return: True if light sensor exists
        """
        return sd.SensorType.LIGHT in self.get_station_sensor_types()

    def has_light_data(self) -> bool:
        """
        :return: True if light sensor exists and has any data
        """
        sensor: Optional[sd.LightSensor] = self.light_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def light_sensor(self) -> Optional[sd.LightSensor]:
        """
        :return: light sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.LIGHT)

    def set_light_sensor(
            self, light_sensor: Optional[sd.LightSensor] = None
    ) -> "Station":
        """
        sets the light sensor; can remove light sensor by passing None

        :param light_sensor: the LightSensor to set or None
        :return: the edited Station
        """
        if self.has_light_sensor():
            self._delete_sensor(sd.SensorType.LIGHT)
        if light_sensor is not None:
            self._add_sensor(sd.SensorType.LIGHT, light_sensor)
        return self

    def has_infrared_sensor(self) -> bool:
        """
        :return: True if infrared (proximity) sensor exists
        """
        return self.has_proximity_sensor()

    def has_infrared_data(self) -> bool:
        """
        :return: True if infrared (proximity) sensor exists and has any data
        """
        return self.has_proximity_data()

    def infrared_sensor(self) -> Optional[sd.ProximitySensor]:
        """
        :return: infrared (proximity) sensor if it exists, None otherwise
        """
        return self.proximity_sensor()

    def set_infrared_sensor(
            self, infrd_sensor: Optional[sd.ProximitySensor] = None
    ) -> "Station":
        """
        sets the infrared sensor; can remove infrared sensor by passing None

        :param infrd_sensor: the ProximitySensor to set or None
        :return: the edited Station
        """
        return self.set_proximity_sensor(infrd_sensor)

    def has_proximity_sensor(self) -> bool:
        """
        :return: True if proximity sensor exists
        """
        return sd.SensorType.PROXIMITY in self.get_station_sensor_types()

    def has_proximity_data(self) -> bool:
        """
        :return: True if proximity sensor exists and has any data
        """
        sensor: Optional[sd.ProximitySensor] = self.proximity_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def proximity_sensor(self) -> Optional[sd.ProximitySensor]:
        """
        :return: proximity sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.PROXIMITY)

    def set_proximity_sensor(
            self, proximity_sensor: Optional[sd.ProximitySensor] = None
    ) -> "Station":
        """
        sets the proximity sensor; can remove proximity sensor by passing None

        :param proximity_sensor: the ProximitySensor to set or None
        :return: the edited Station
        """
        if self.has_proximity_sensor():
            self._delete_sensor(sd.SensorType.PROXIMITY)
        if proximity_sensor is not None:
            self._add_sensor(sd.SensorType.PROXIMITY, proximity_sensor)
        return self

    def has_image_sensor(self) -> bool:
        """
        :return: True if image sensor exists
        """
        return sd.SensorType.IMAGE in self.get_station_sensor_types()

    def has_image_data(self) -> bool:
        """
        :return: True if image sensor exists and has any data
        """
        sensor: Optional[sd.ImageSensor] = self.image_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def image_sensor(self) -> Optional[sd.ImageSensor]:
        """
        :return: image sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.IMAGE)

    def set_image_sensor(self, img_sensor: Optional[sd.ImageSensor] = None) -> "Station":
        """
        sets the image sensor; can remove image sensor by passing None

        :param img_sensor: the ImageSensor to set or None
        :return: the edited Station
        """
        if self.has_image_sensor():
            self._delete_sensor(sd.SensorType.IMAGE)
        if img_sensor is not None:
            self._add_sensor(sd.SensorType.IMAGE, img_sensor)
        return self

    def has_ambient_temperature_sensor(self) -> bool:
        """
        :return: True if ambient temperature sensor exists
        """
        return sd.SensorType.AMBIENT_TEMPERATURE in self.get_station_sensor_types()

    def has_ambient_temperature_data(self) -> bool:
        """
        :return: True if ambient temperature sensor exists and has any data
        """
        sensor: Optional[sd.AmbientTemperatureSensor] = self.ambient_temperature_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def ambient_temperature_sensor(self) -> Optional[sd.AmbientTemperatureSensor]:
        """
        :return: ambient temperature sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.AMBIENT_TEMPERATURE)

    def set_ambient_temperature_sensor(
            self, amb_temp_sensor: Optional[sd.AmbientTemperatureSensor] = None
    ) -> "Station":
        """
        sets the ambient temperature sensor; can remove ambient temperature sensor by passing None

        :param amb_temp_sensor: the AmbientTemperatureSensor to set or None
        :return: the edited Station
        """
        if self.has_ambient_temperature_sensor():
            self._delete_sensor(sd.SensorType.AMBIENT_TEMPERATURE)
        if amb_temp_sensor is not None:
            self._add_sensor(sd.SensorType.AMBIENT_TEMPERATURE, amb_temp_sensor)
        return self

    def has_relative_humidity_sensor(self) -> bool:
        """
        :return: True if relative humidity sensor exists
        """
        return sd.SensorType.RELATIVE_HUMIDITY in self.get_station_sensor_types()

    def has_relative_humidity_data(self) -> bool:
        """
        :return: True if relative humidity sensor exists and has any data
        """
        sensor: Optional[sd.RelativeHumiditySensor] = self.relative_humidity_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def relative_humidity_sensor(self) -> Optional[sd.RelativeHumiditySensor]:
        """
        :return: relative humidity sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.RELATIVE_HUMIDITY)

    def set_relative_humidity_sensor(
            self, rel_hum_sensor: Optional[sd.RelativeHumiditySensor] = None
    ) -> "Station":
        """
        sets the relative humidity sensor; can remove relative humidity sensor by passing None

        :param rel_hum_sensor: the RelativeHumiditySensor to set or None
        :return: the edited Station
        """
        if self.has_relative_humidity_sensor():
            self._delete_sensor(sd.SensorType.RELATIVE_HUMIDITY)
        if rel_hum_sensor is not None:
            self._add_sensor(sd.SensorType.RELATIVE_HUMIDITY, rel_hum_sensor)
        return self

    def has_gravity_sensor(self) -> bool:
        """
        :return: True if gravity sensor exists
        """
        return sd.SensorType.GRAVITY in self.get_station_sensor_types()

    def has_gravity_data(self) -> bool:
        """
        :return: True if gravity sensor exists and has any data
        """
        sensor: Optional[sd.GravitySensor] = self.gravity_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def gravity_sensor(self) -> Optional[sd.GravitySensor]:
        """
        :return: gravity sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.GRAVITY)

    def set_gravity_sensor(
            self, grav_sensor: Optional[sd.GravitySensor] = None
    ) -> "Station":
        """
        sets the gravity sensor; can remove gravity sensor by passing None

        :param grav_sensor: the GravitySensor to set or None
        :return: the edited Station
        """
        if self.has_gravity_sensor():
            self._delete_sensor(sd.SensorType.GRAVITY)
        if grav_sensor is not None:
            self._add_sensor(sd.SensorType.GRAVITY, grav_sensor)
        return self

    def has_linear_acceleration_sensor(self) -> bool:
        """
        :return: True if linear acceleration sensor exists
        """
        return sd.SensorType.LINEAR_ACCELERATION in self.get_station_sensor_types()

    def has_linear_acceleration_data(self) -> bool:
        """
        :return: True if linear acceleration sensor exists and has any data
        """
        sensor: Optional[sd.LinearAccelerationSensor] = self.linear_acceleration_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def linear_acceleration_sensor(self) -> Optional[sd.LinearAccelerationSensor]:
        """
        :return: linear acceleration sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.LINEAR_ACCELERATION)

    def set_linear_acceleration_sensor(
            self, lin_acc_sensor: Optional[sd.LinearAccelerationSensor] = None
    ) -> "Station":
        """
        sets the linear acceleration sensor; can remove linear acceleration sensor by passing None

        :param lin_acc_sensor: the LinearAccelerationSensor to set or None
        :return: the edited Station
        """
        if self.has_linear_acceleration_sensor():
            self._delete_sensor(sd.SensorType.LINEAR_ACCELERATION)
        if lin_acc_sensor is not None:
            self._add_sensor(sd.SensorType.LINEAR_ACCELERATION, lin_acc_sensor)
        return self

    def has_orientation_sensor(self) -> bool:
        """
        :return: True if orientation sensor exists
        """
        return sd.SensorType.ORIENTATION in self.get_station_sensor_types()

    def has_orientation_data(self) -> bool:
        """
        :return: True if orientation sensor exists and has any data
        """
        sensor: Optional[sd.OrientationSensor] = self.orientation_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def orientation_sensor(self) -> Optional[sd.OrientationSensor]:
        """
        :return: orientation sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.ORIENTATION)

    def set_orientation_sensor(
            self, orientation_sensor: Optional[sd.OrientationSensor] = None
    ) -> "Station":
        """
        sets the orientation sensor; can remove orientation sensor by passing None

        :param orientation_sensor: the OrientationSensor to set or None
        :return: the edited Station
        """
        if self.has_orientation_sensor():
            self._delete_sensor(sd.SensorType.ORIENTATION)
        if orientation_sensor is not None:
            self._add_sensor(sd.SensorType.ORIENTATION, orientation_sensor)
        return self

    def has_rotation_vector_sensor(self) -> bool:
        """
        :return: True if rotation vector sensor exists
        """
        return sd.SensorType.ROTATION_VECTOR in self.get_station_sensor_types()

    def has_rotation_vector_data(self) -> bool:
        """
        :return: True if rotation vector sensor exists and has any data
        """
        sensor: Optional[sd.RotationVectorSensor] = self.rotation_vector_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def rotation_vector_sensor(self) -> Optional[sd.RotationVectorSensor]:
        """
        :return: rotation vector sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.ROTATION_VECTOR)

    def set_rotation_vector_sensor(
            self, rot_vec_sensor: Optional[sd.RotationVectorSensor] = None
    ) -> "Station":
        """
        sets the rotation vector sensor; can remove rotation vector sensor by passing None

        :param rot_vec_sensor: the RotationVectorSensor to set or None
        :return: the edited DataPacket
        """
        if self.has_rotation_vector_sensor():
            self._delete_sensor(sd.SensorType.ROTATION_VECTOR)
        if rot_vec_sensor is not None:
            self._add_sensor(sd.SensorType.ROTATION_VECTOR, rot_vec_sensor)
        return self

    def has_compressed_audio_sensor(self) -> bool:
        """
        :return: True if compressed audio sensor exists
        """
        return sd.SensorType.COMPRESSED_AUDIO in self.get_station_sensor_types()

    def has_compressed_audio_data(self) -> bool:
        """
        :return: True if compressed audio sensor exists and has any data
        """
        sensor: Optional[sd.CompressedAudioSensor] = self.compressed_audio_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def compressed_audio_sensor(self) -> Optional[sd.CompressedAudioSensor]:
        """
        :return: compressed audio sensor if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.COMPRESSED_AUDIO)

    def set_compressed_audio_sensor(
            self, comp_audio_sensor: Optional[sd.CompressedAudioSensor] = None
    ) -> "Station":
        """
        sets the compressed audio sensor; can remove compressed audio sensor by passing None

        :param comp_audio_sensor: the CompressedAudioSensor to set or None
        :return: the edited DataPacket
        """
        if self.has_compressed_audio_sensor():
            self._delete_sensor(sd.SensorType.COMPRESSED_AUDIO)
        if comp_audio_sensor is not None:
            self._add_sensor(sd.SensorType.COMPRESSED_AUDIO, comp_audio_sensor)
        return self

    def has_health_sensor(self) -> bool:
        """
        :return: True if health sensor (station metrics) exists
        """
        return sd.SensorType.STATION_HEALTH in self.get_station_sensor_types()

    def has_health_data(self) -> bool:
        """
        :return: True if health sensor (station metrics) exists and has data
        """
        sensor: Optional[sd.StationHealthSensor] = self.health_sensor()
        return sensor is not None and sensor.num_samples() > 0

    def health_sensor(self) -> Optional[sd.StationHealthSensor]:
        """
        :return: station health sensor (station metrics) if it exists, None otherwise
        """
        return self.get_sensor_by_type(sd.SensorType.STATION_HEALTH)

    def set_health_sensor(
            self, health_sensor: Optional[sd.StationHealthSensor] = None
    ) -> "Station":
        """
        sets the health sensor; can remove health sensor by passing None

        :param health_sensor: the StationHealthSensor to set or None
        :return: the edited DataPacket
        """
        if self.has_health_sensor():
            self._delete_sensor(sd.SensorType.STATION_HEALTH)
        if health_sensor is not None:
            self._add_sensor(sd.SensorType.STATION_HEALTH, health_sensor)
        return self

    def _set_all_sensors(self, packets: List[api_m.RedvoxPacketM]):
        """
        set all sensors from the packets, as well as misc. metadata, and put it in the station

        :param packets: the packets to read data from
        """
        self.packet_metadata = [
            st_utils.StationPacketMetadata(packet) for packet in packets
        ]
        sensor, self._gaps = sdru.load_apim_audio_from_list(packets)
        if sensor:
            self.append_sensor(sensor)
        funcs = [
            sdru.load_apim_compressed_audio_from_list,
            sdru.load_apim_image_from_list,
            sdru.load_apim_best_location_from_list,
            sdru.load_apim_location_from_list,
            sdru.load_apim_pressure_from_list,
            sdru.load_apim_light_from_list,
            sdru.load_apim_ambient_temp_from_list,
            sdru.load_apim_rel_humidity_from_list,
            sdru.load_apim_proximity_from_list,
            sdru.load_apim_accelerometer_from_list,
            sdru.load_apim_gyroscope_from_list,
            sdru.load_apim_magnetometer_from_list,
            sdru.load_apim_gravity_from_list,
            sdru.load_apim_linear_accel_from_list,
            sdru.load_apim_orientation_from_list,
            sdru.load_apim_rotation_vector_from_list,
            sdru.load_apim_health_from_list,
        ]
        sensors = map(FunctionType.__call__, funcs, repeat(packets), repeat(self._gaps))
        for sensor in sensors:
            if sensor:
                self.append_sensor(sensor)

    @staticmethod
    def from_packet(packet: api_m.RedvoxPacketM) -> "Station":
        start_time = packet.timing_information.app_start_mach_timestamp
        return Station(
            station_id=packet.station_information.id,
            uuid=packet.station_information.uuid,
            start_time=np.nan if start_time < 0 else start_time,
        )._load_packet(packet)

    def load_packet(self, packet: api_m.RedvoxPacketM) -> "Station":
        """
        load all data from a packet

        :param packet: packet to load data from
        :return: updated station or a new station if it doesn't exist
        """
        start_time: float = packet.timing_information.app_start_mach_timestamp
        o_s = Station(
            station_id=packet.station_information.id,
            uuid=packet.station_information.uuid,
            start_time=np.nan if start_time < 0 else start_time,
        )
        if self.get_key() == o_s.get_key():
            return self._load_packet(packet)
        return o_s._load_packet(packet)

    def _load_packet(self, packet: api_m.RedvoxPacketM) -> "Station":
        self.packet_metadata.append(st_utils.StationPacketMetadata(packet))
        funcs = [
            sdru.load_apim_audio,
            sdru.load_apim_compressed_audio,
            sdru.load_apim_image,
            sdru.load_apim_best_location,
            sdru.load_apim_location,
            sdru.load_apim_pressure,
            sdru.load_apim_light,
            sdru.load_apim_ambient_temp,
            sdru.load_apim_rel_humidity,
            sdru.load_apim_proximity,
            sdru.load_apim_accelerometer,
            sdru.load_apim_gyroscope,
            sdru.load_apim_magnetometer,
            sdru.load_apim_gravity,
            sdru.load_apim_linear_accel,
            sdru.load_apim_orientation,
            sdru.load_apim_rotation_vector,
            sdru.load_apim_health,
        ]
        sensors = map(lambda fn: fn(packet), funcs)
        for sensor in sensors:
            if sensor:
                self.append_sensor(sensor)
        return self

    def update_timestamps(self) -> "Station":
        """
        updates the timestamps in the station using the offset model
        """
        if self.is_timestamps_updated:
            self.errors.append("Timestamps already corrected!")
        else:
            for sensor in self.data:
                sensor.update_data_timestamps(self.timesync_analysis.offset_model, self.use_model_correction)
            for packet in self.packet_metadata:
                packet.update_timestamps(self.timesync_analysis.offset_model, self.use_model_correction)
            for g in range(len(self._gaps)):
                self._gaps[g] = (self.timesync_analysis.offset_model.update_time(self._gaps[g][0]),
                                 self.timesync_analysis.offset_model.update_time(self._gaps[g][1]))
            self.timesync_analysis.update_timestamps()
            self.start_timestamp = self.timesync_analysis.offset_model.update_time(
                self.start_timestamp, self.use_model_correction
            )
            self.first_data_timestamp = self.timesync_analysis.offset_model.update_time(
                self.first_data_timestamp, self.use_model_correction
            )
            self.last_data_timestamp = self.timesync_analysis.offset_model.update_time(
                self.last_data_timestamp, self.use_model_correction
            )
            self.is_timestamps_updated = True
        return self
