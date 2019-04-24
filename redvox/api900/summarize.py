"""
This module contains functions and classes for summarizing ranges of redvox data.
"""

import datetime
import itertools
import typing

import numpy
import matplotlib.pyplot as plt

import redvox.api900.types as types
import redvox.api900.date_time_utils as date_time_utils


def _sensor_name(sensor: typing.Optional[types.RedvoxSensor]) -> str:
    """
    Extracts the sensor name from a redvox sensor.
    :param sensor: Sensor to get sensor name for.
    :return: The sensor name for the given sensor.
    """
    if sensor is None:
        return ""

    if isinstance(sensor, types.time_synchronization_sensor.TimeSynchronizationSensor):
        return "time synch"

    return sensor.sensor_name()


def _sensor_samples(sensor: typing.Optional[types.RedvoxSensor]) -> int:
    """
    Returns the number of samples a sensor contains.
    :param sensor: Sensor to test.
    :return: Number of samples in sensor.
    """
    if sensor is None:
        return 0

    if isinstance(sensor, (types.microphone_sensor.MicrophoneSensor,
                           types.time_synchronization_sensor.TimeSynchronizationSensor)):
        return len(sensor.payload_values())

    return len(sensor.timestamps_microseconds_utc())


# pylint: disable=R0903
class SensorSummary:
    """
    This class provides a summary of a sensor.
    """

    def __init__(self, sensor: typing.Optional[types.RedvoxSensor]):
        self.has_sensor = sensor is not None
        self.sensor_name = _sensor_name(sensor)
        self.num_samples = _sensor_samples(sensor)

    def __str__(self):
        if not self.has_sensor:
            return "None"
        return "{SensorSummary: %s with %d samples} " % (self.sensor_name, self.num_samples)


# pylint: disable=R0902
# pylint: disable=R0903
class WrappedRedvoxPacketSummary:
    """
    This class provides a summary of a WrappedRedvoxPacket.
    """

    def __init__(self, redvox_packet):
        self.redvox_id = redvox_packet.redvox_id()
        self.uuid = redvox_packet.uuid()
        self.redvox_id_uuid: str = "%s:%s" % (self.redvox_id, self.uuid)
        self.start_timestamp_us: int = redvox_packet.start_timestamp_us_utc()
        self.end_timestamp_us: int = redvox_packet.end_timestamp_us_utc()
        self.duration_s: float = redvox_packet.duration_s()
        self.sample_rate_hz = redvox_packet.microphone_sensor().sample_rate_hz()
        self.microphone_sensor_summary: SensorSummary = SensorSummary(redvox_packet.microphone_sensor())
        self.barometer_sensor_summary: SensorSummary = SensorSummary(redvox_packet.barometer_sensor())
        self.location_sensor_summary: SensorSummary = SensorSummary(redvox_packet.location_sensor())
        # pylint: disable=C0103
        self.time_synchronization_sensor_summary: SensorSummary = SensorSummary(
            redvox_packet.time_synchronization_sensor())
        self.accelerometer_sensor_summary: SensorSummary = SensorSummary(redvox_packet.accelerometer_sensor())
        self.magnetometer_sensor_summary: SensorSummary = SensorSummary(redvox_packet.magnetometer_sensor())
        self.gyroscope_sensor_summary: SensorSummary = SensorSummary(redvox_packet.gyroscope_sensor())
        self.light_sensor_summary: SensorSummary = SensorSummary(redvox_packet.light_sensor())
        self.infrared_sensor_summary: SensorSummary = SensorSummary(redvox_packet.infrared_sensor())

    def __str__(self):
        return "{WrappedRedvoxPacketSummary: %s %d-%d [%f sec] %f %s %s %s %s %s %s %s %s %s} " % (
            self.redvox_id_uuid,
            self.start_timestamp_us,
            self.end_timestamp_us,
            self.duration_s,
            self.sample_rate_hz,
            str(self.microphone_sensor_summary),
            str(self.barometer_sensor_summary),
            str(self.location_sensor_summary),
            str(self.time_synchronization_sensor_summary),
            str(self.accelerometer_sensor_summary),
            str(self.magnetometer_sensor_summary),
            str(self.gyroscope_sensor_summary),
            str(self.light_sensor_summary),
            str(self.infrared_sensor_summary)
        )


# Type vars for compose function.
X = typing.TypeVar("X")
Y = typing.TypeVar("Y")
Z = typing.TypeVar("Z")


def _compose(fn1: typing.Callable[[X], Y],
             fn2: typing.Callable[[Y], Z]) -> typing.Callable[[X], Z]:
    """
    Composes two functions together.
    :param fn1: A function from X -> Y
    :param fn2: A function from Y -> Z
    :return: A function from X -> Z
    """
    return lambda value: fn2(fn1(value))


def summarize_data(grouped_redvox_packets: typing.Dict[str, typing.List]) -> typing.Dict[
        str, typing.List[WrappedRedvoxPacketSummary]]:
    """
    Given grouped redvox packets, generate summaries for each device and each packet.
    :param grouped_redvox_packets: Grouped packets to generate summary for.
    :return: A dictionary which maps redvox ids to summaries of redvox packets for that device.
    """
    summarized = {}
    for id_uuid, wrapped_redvox_packets in grouped_redvox_packets.items():
        summarized[id_uuid] = list(map(WrappedRedvoxPacketSummary, wrapped_redvox_packets))
    return summarized


def _subsample(values: typing.Union[numpy.ndarray, typing.List], num_samples: int) -> typing.Union[
        numpy.ndarray, typing.List]:
    """
    Returns evenly sampled values from an array.
    From https://stackoverflow.com/a/50685454 and https://stackoverflow.com/a/9873935
    :param values: Sequence to extract evenly sampled samples from.
    :param num_samples: Number of samples to extract.
    :return: A new, subsampled array.
    """
    indexes = numpy.round(numpy.linspace(0, len(values) - 1, num_samples)).astype(int)
    if isinstance(values, numpy.ndarray):
        return numpy.take(values, indexes)
    elif isinstance(values, typing.List):
        return [values[i] for i in indexes]
    else:
        raise RuntimeError("Non sequence type passed to subsample")


# pylint: disable=R0914
def plot_summarized_data(summarized_data: typing.Dict[str, typing.List[WrappedRedvoxPacketSummary]]):
    """
    Given summarized data, plot the data to display sensor activity for all passed in summarized data.
    :param summarized_data: Data to plot.
    """
    all_summaries = list(itertools.chain(*summarized_data.values()))

    start_timestamp_us = numpy.min(
        list(map(lambda packet_summary: packet_summary.start_timestamp_us, all_summaries)))
    end_timestamp_us = numpy.max(list(map(lambda packet_summary: packet_summary.end_timestamp_us, all_summaries)))
    start_s = int(date_time_utils.microseconds_to_seconds(start_timestamp_us))
    end_s = int(date_time_utils.microseconds_to_seconds(end_timestamp_us))
    timestamps = numpy.arange(start_s, end_s + 1)

    # Setup the plot
    fig, axes = plt.subplots(nrows=1)
    axes.set_xlim([timestamps[0], timestamps[-1]])
    axes.set_ylim([0, len(summarized_data.keys()) + 1])

    # Not for each device, let's plot its ranges
    yticks = []
    ylabels = []
    i = 1
    for redvox_id, summaries in summarized_data.items():
        for summary in summaries:
            summary_start_s = int(date_time_utils.microseconds_to_seconds(summary.start_timestamp_us))
            summary_end_s = int(date_time_utils.microseconds_to_seconds(summary.end_timestamp_us))
            values = numpy.full(len(timestamps), numpy.nan)
            values[timestamps.searchsorted(summary_start_s):timestamps.searchsorted(summary_end_s)] = i
            axes.plot(timestamps, values)

        yticks.append(i)
        ylabels.append(redvox_id.split(":")[0])
        i += 1

    xticks = _subsample(timestamps, 6)
    datetimes = map(datetime.datetime.utcfromtimestamp, xticks)
    datetimes = map(lambda dt: dt.strftime("%d %H:%M"), datetimes)
    axes.set_xticks(xticks)
    axes.set_xticklabels(list(datetimes))
    axes.set_yticks(yticks)
    axes.set_yticklabels(ylabels)

    axes.tick_params(axis='both', which='major', labelsize=8)
    axes.tick_params(axis='both', which='minor', labelsize=7)

    axes.set_title("RedVox Device Summary")
    axes.set_xlabel("Date and Time")
    axes.set_ylabel("Device Activity")

    fig.text(.5, .01, "UTC %s - %s" % (datetime.datetime.utcfromtimestamp(start_s),
                                       datetime.datetime.utcfromtimestamp(end_s)), ha='center')
    plt.show()
