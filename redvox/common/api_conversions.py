from typing import List

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api1000.wrapped_redvox_packet.station_information import OsType, StationInformation, StationMetrics
from redvox.api1000.wrapped_redvox_packet.timing_information import SynchExchange
from redvox.api1000.wrapped_redvox_packet.sensors.audio import Audio
from redvox.api1000.wrapped_redvox_packet.sensors.sensors import Sensors
import redvox.api1000.wrapped_redvox_packet.common as common_m
import redvox.common.date_time_utils as dt_utls
import redvox.api900.reader as reader_900
import redvox

import numpy as np


def _migrate_synch_exchanges_900_to_1000(synch_exchanges: np.ndarray) -> List[SynchExchange]:
    exchanges: List[SynchExchange] = []

    for i in range(0, len(synch_exchanges), 6):
        exchange: SynchExchange = SynchExchange.new()
        exchange.set_a1(int(synch_exchanges[i]))
        exchange.set_a2(int(synch_exchanges[i + 1]))
        exchange.set_a3(int(synch_exchanges[i + 2]))
        exchange.set_b1(int(synch_exchanges[i + 3]))
        exchange.set_b2(int(synch_exchanges[i + 4]))
        exchange.set_b3(int(synch_exchanges[i + 5]))
        exchanges.append(exchange)

    return exchanges


def _find_mach_time_zero(packet: reader_900.WrappedRedvoxPacket) -> int:
    if "machTimeZero" in packet.metadata_as_dict():
        return int(packet.metadata_as_dict()["machTimeZero"])

    location_sensor = packet.location_sensor()
    if location_sensor is not None:
        if "machTimeZero" in location_sensor.metadata_as_dict():
            return int(location_sensor.metadata_as_dict()["machTimeZero"])

    return -1


def _packet_length_microseconds_900(packet: reader_900.WrappedRedvoxPacket) -> int:
    microphone_sensor = packet.microphone_sensor()

    if microphone_sensor is not None:
        sample_rate_hz: float = microphone_sensor.sample_rate_hz()
        total_samples: int = len(microphone_sensor.payload_values())
        length_seconds: float = float(total_samples) / sample_rate_hz
        return round(dt_utls.seconds_to_microseconds(length_seconds))

    return 0


def _packet_length_microseconds_1000(packet: reader_900.WrappedRedvoxPacket) -> int:
    pass


def _migrate_os_type_900_to_1000(os: str) -> OsType:
    os_lower: str = os.lower()
    if os_lower == "android":
        return OsType.ANDROID

    if os_lower == "ios":
        return OsType.IOS

    return OsType.UNKNOWN_OS


def convert_api_900_to_1000(wrapped_packet_900: reader_900.WrappedRedvoxPacket) -> WrappedRedvoxPacketM:
    wrapped_packet: WrappedRedvoxPacketM = WrappedRedvoxPacketM.new()

    # Top-level metadata
    wrapped_packet.set_api(1000.0)
    wrapped_packet.get_metadata().append_metadata("migrated_from_api_900", f"v{redvox.VERSION}")

    # User information
    wrapped_packet.get_user_information() \
        .set_auth_email(wrapped_packet_900.authenticated_email()) \
        .set_auth_token(wrapped_packet_900.authentication_token()) \
        .set_firebase_token(wrapped_packet_900.firebase_token())

    # Station information
    station_information: StationInformation = wrapped_packet.get_station_information()
    station_information \
        .set_id(wrapped_packet_900.redvox_id()) \
        .set_uuid(wrapped_packet_900.uuid()) \
        .set_make(wrapped_packet_900.device_make()) \
        .set_model(wrapped_packet_900.device_model()) \
        .set_os(_migrate_os_type_900_to_1000(wrapped_packet_900.device_os())) \
        .set_os_version(wrapped_packet_900.device_os_version()) \
        .set_app_version(wrapped_packet_900.app_version())

    # API 900 does not maintain a copy of its settings. So we will not set anything in AppSettings

    # StationMetrics - We know a couple
    station_metrics: StationMetrics = station_information.get_station_metrics()
    station_metrics.get_timestamps().append_timestamp(wrapped_packet_900.app_file_start_timestamp_machine()) \
        .set_unit(common_m.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
    station_metrics.get_temperature().append_value(wrapped_packet_900.device_temperature_c()) \
        .set_unit(common_m.Unit.DEGREES_CELSIUS)
    station_metrics.get_battery().append_value(wrapped_packet_900.battery_level_percent()) \
        .set_unit(common_m.Unit.PERCENTAGE)

    # Packet information
    wrapped_packet.get_packet_information() \
        .set_is_backfilled(wrapped_packet_900.is_backfilled()) \
        .set_is_private(wrapped_packet_900.is_private())

    # Timing information
    mach_time_900: int = wrapped_packet_900.app_file_start_timestamp_machine()
    os_time_900: int = wrapped_packet_900.app_file_start_timestamp_epoch_microseconds_utc()
    len_micros: int = _packet_length_microseconds_900(wrapped_packet_900)
    best_latency = wrapped_packet_900.best_latency()
    best_latency = best_latency if best_latency is not None else 0.0
    best_offset = wrapped_packet_900.best_offset()
    best_offset = best_offset if best_offset is not None else 0.0

    wrapped_packet.get_timing_information() \
        .set_unit(common_m.Unit.MICROSECONDS_SINCE_UNIX_EPOCH) \
        .set_packet_start_mach_timestamp(mach_time_900) \
        .set_packet_start_os_timestamp(os_time_900) \
        .set_packet_end_mach_timestamp(mach_time_900 + len_micros) \
        .set_packet_end_os_timestamp(os_time_900 + len_micros) \
        .set_server_acquisition_arrival_timestamp(wrapped_packet_900.server_timestamp_epoch_microseconds_utc()) \
        .set_app_start_mach_timestamp(_find_mach_time_zero(wrapped_packet_900)) \
        .set_best_latency(best_latency) \
        .set_best_offset(best_offset)

    time_sensor = wrapped_packet_900.time_synchronization_sensor()
    if time_sensor is not None:
        wrapped_packet.get_timing_information().get_synch_exchanges() \
            .append_values(_migrate_synch_exchanges_900_to_1000(time_sensor.payload_values()))

    # Server information
    wrapped_packet.get_server_information() \
        .set_auth_server_url(wrapped_packet_900.authentication_server()) \
        .set_synch_server_url(wrapped_packet_900.time_synchronization_server()) \
        .set_acquisition_server_url(wrapped_packet_900.acquisition_server())

    # Sensors
    sensors: Sensors = wrapped_packet.get_sensors()
    # Microphone / Audio
    mic_sensor = wrapped_packet_900.microphone_sensor()
    if mic_sensor is not None:
        sensors.new_audio() \
            .set_first_sample_timestamp(mic_sensor.first_sample_timestamp_epoch_microseconds_utc()) \
            .set_is_scrambled(wrapped_packet_900.is_scrambled()) \
            .set_sample_rate(mic_sensor.sample_rate_hz()) \
            .set_sensor_description(mic_sensor.sensor_name()) \
            .get_samples().append_values(mic_sensor.payload_values(), update_value_statistics=True)

    # Barometer
    barometer_sensor = wrapped_packet_900.barometer_sensor()
    if barometer_sensor is not None:
        pressure_sensor = sensors.new_pressure()
        pressure_sensor.set_sensor_description(barometer_sensor.sensor_name())
        pressure_sensor.get_timestamps().set_timestamps(barometer_sensor.timestamps_microseconds_utc(), True)
        pressure_sensor.get_samples().set_values(barometer_sensor.payload_values(), True)

    return wrapped_packet


def convert_api_1000_to_900(wrapped_packet_m: WrappedRedvoxPacketM) -> reader_900.WrappedRedvoxPacket:
    wrapped_packet: reader_900.WrappedRedvoxPacket = reader_900.WrappedRedvoxPacket()

    return wrapped_packet


def main():
    packet: reader_900.WrappedRedvoxPacket = reader_900.read_rdvxz_file(
        "/home/opq/Downloads/1637680002_1587497128130.rdvxz")
    packet_m: WrappedRedvoxPacketM = convert_api_900_to_1000(packet)
    print(packet_m)


if __name__ == "__main__":
    main()
