import typing

import redvox.api900.reader as reader
from redvox.api900 import exceptions

import numpy

WrappedRedvoxPackets = typing.List[reader.WrappedRedvoxPacket]


def partial_hash_sensor(sensor: typing.Union[reader.EvenlySampledSensor,
                                             reader.UnevenlySampledSensor,
                                             reader.TimeSynchronizationSensor]) -> int:
    if isinstance(sensor, reader.UnevenlySampledSensor):
        return hash(sensor) if sensor is None else hash((sensor.sensor_name(), sensor.payload_type()))

    if isinstance(sensor, reader.EvenlySampledSensor):
        return hash(sensor) if sensor is None else hash(
            (sensor.sample_rate_hz(), sensor.sensor_name(), sensor.payload_type()))

    if isinstance(sensor, reader.TimeSynchronizationSensor):
        return hash(sensor) if sensor is None else hash("TimeSynchronizationSensor")

    raise exceptions.ConcatenationException("trying to hash non-sensor type=%s" % type(sensor))


def partial_hash_packet(wrapped_redvox_packet: reader.WrappedRedvoxPacket) -> int:
    return hash((wrapped_redvox_packet.redvox_id(),
                 wrapped_redvox_packet.uuid(),
                 partial_hash_sensor(wrapped_redvox_packet.microphone_channel()),
                 partial_hash_sensor(wrapped_redvox_packet.barometer_channel()),
                 partial_hash_sensor(wrapped_redvox_packet.location_channel()),
                 partial_hash_sensor(wrapped_redvox_packet.time_synchronization_channel()),
                 partial_hash_sensor(wrapped_redvox_packet.accelerometer_channel()),
                 partial_hash_sensor(wrapped_redvox_packet.gyroscope_channel()),
                 partial_hash_sensor(wrapped_redvox_packet.magnetometer_channel()),
                 partial_hash_sensor(wrapped_redvox_packet.light_channel()),
                 partial_hash_sensor(wrapped_redvox_packet.infrared_channel())))


def identify_gaps(wrapped_redvox_packets: WrappedRedvoxPackets) -> typing.List[int]:
    if len(wrapped_redvox_packets) <= 1:
        return []

    gaps = []

    # Sensor changes
    truth_hash = partial_hash_packet(wrapped_redvox_packets[0])
    for i in range(1, len(wrapped_redvox_packets)):
        candidate_hash = partial_hash_packet(wrapped_redvox_packets[i])

        if truth_hash != candidate_hash:
            gaps.append(i)
            truth_hash = candidate_hash

    # Time gaps

    return gaps


def concat_wrapped_redvox_packets(wrapped_redvox_packets: WrappedRedvoxPackets) -> WrappedRedvoxPackets:
    # Check packets are from same device
    device_ids = set(map(lambda packet: packet.redvox_id(), wrapped_redvox_packets))
    if len(device_ids) != 1:
        raise exceptions.ConcatenationException("Not all packets from same device %s" % str(device_ids))

    # Check packets are ordered
    machine_times = list(map(lambda packet: packet.app_file_start_timestamp_machine(),
                             wrapped_redvox_packets))

    if not numpy.all(numpy.diff(numpy.array(machine_times)) > 0):
        raise exceptions.ConcatenationException("Packets are not strictly monotonic")

    gaps = identify_gaps(wrapped_redvox_packets)


