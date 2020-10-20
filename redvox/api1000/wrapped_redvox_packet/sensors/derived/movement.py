"""
Contains classes and methods for examining movement events.
"""

from collections import defaultdict
from dataclasses import dataclass
import datetime
from enum import Enum
from functools import total_ordering
from typing import Dict, List, Optional, TYPE_CHECKING, Set

import numpy as np

from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc

if TYPE_CHECKING:
    from redvox.api1000.common.mapping import Mapping
    from redvox.api1000.wrapped_redvox_packet.event_streams import Event, EventStream
    from redvox.api1000.wrapped_redvox_packet.sensors.sensors import Sensors
    from redvox.api1000.wrapped_redvox_packet.sensors.xyz import Xyz


class MovementChannel(Enum):
    """
    Enumeration of movement channels.
    """
    GYROSCOPE_X: str = "GYROSCOPE_X"
    GYROSCOPE_Y: str = "GYROSCOPE_Y"
    GYROSCOPE_Z: str = "GYROSCOPE_Z"
    ACCELEROMETER_X: str = "ACCELEROMETER_X"
    ACCELEROMETER_Y: str = "ACCELEROMETER_Y"
    ACCELEROMETER_Z: str = "ACCELEROMETER_Z"


@total_ordering
@dataclass
class MovementEvent:
    """
    Represents the metadata associated with a derived movement event.
    """
    movement_channel: MovementChannel
    movement_start: float
    movement_end: float
    movement_duration: float
    magnitude_min: float
    magnitude_max: float
    magnitude_range: float
    magnitude_mean: float
    magnitude_std_dev: float

    def movement_start_dt(self) -> datetime.datetime:
        """
        :return: The movement start as a datetime.
        """
        return datetime_from_epoch_microseconds_utc(self.movement_start)

    def movement_end_dt(self) -> datetime.datetime:
        """
        :return: The movement end as a datetime.
        """
        return datetime_from_epoch_microseconds_utc(self.movement_end)

    def movement_duration_td(self) -> datetime.timedelta:
        """
        :return: The movement duration as a timedelta.
        """
        return self.movement_end_dt() - self.movement_start_dt()

    def time_diff(self, other: 'MovementEvent') -> datetime.timedelta:
        events: List['MovementEvent'] = sorted([self, other])
        fst: 'MovementEvent' = events[0]
        scd: 'MovementEvent' = events[1]

        return scd.movement_start_dt() - fst.movement_start_dt()

    @staticmethod
    def from_event(event: 'Event') -> 'MovementEvent':
        """
        Converts a generic API M Event into a MovementEvent.
        :param event: The Event to convert.
        :return: A MovementEvent.
        """
        numeric_payload: 'Mapping[float]' = event.get_numeric_payload()
        numeric_payload_dict: Dict[str, float] = numeric_payload.get_metadata()
        return MovementEvent(
            MovementChannel[event.get_description()],
            numeric_payload_dict["movement_start"],
            numeric_payload_dict["movement_end"],
            numeric_payload_dict["movement_duration"],
            numeric_payload_dict["magnitude_min"],
            numeric_payload_dict["magnitude_max"],
            numeric_payload_dict["magnitude_range"],
            numeric_payload_dict["magnitude_mean"],
            numeric_payload_dict["magnitude_std_dev"],
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, MovementEvent) and self.movement_start == other.movement_start

    def __lt__(self, other: 'MovementEvent') -> bool:
        return self.movement_start < other.movement_start


@dataclass
class MovementEventStream:
    """
    Represents a derived movement event stream.
    """
    name: str
    movement_events: List[MovementEvent]

    @staticmethod
    def from_event_stream(event_stream: 'EventStream') -> 'MovementEventStream':
        """
        Converts an API M EventStream into a MovementEventStream.
        :param event_stream: Stream to convert.
        :return: A MovementEventStream.
        """
        movement_events: List[MovementEvent] = list(map(MovementEvent.from_event,
                                                        event_stream.get_events().get_values()))

        movement_events.sort(key=lambda event: event.movement_start_dt())
        return MovementEventStream(event_stream.get_name(), movement_events)

    def events_by_channel(self, movement_channel: MovementChannel) -> List[MovementEvent]:
        return list(filter(lambda event: event.movement_channel == movement_channel, self.movement_events))


@dataclass
class __SensorData:
    timestamps: np.ndarray
    samples: np.ndarray

    def filter_samples(self, start_ts: float, end_ts: float) -> np.ndarray:
        start_idx: Optional[int] = None
        end_idx: Optional[int] = None

        i: int = 0
        for i, ts in enumerate(self.timestamps):
            if ts >= start_ts:
                start_idx = i
                break

        for j in range(i, len(self.timestamps)):
            ts = self.timestamps[j]
            if ts >= end_ts:
                end_idx = j + 1
                break

        return self.samples[start_idx:end_idx]


# noinspection PyTypeChecker
__GYRO_CHANNELS: Set[MovementChannel] = {
    MovementChannel.GYROSCOPE_X,
    MovementChannel.GYROSCOPE_Y,
    MovementChannel.GYROSCOPE_Z,
}

# noinspection PyTypeChecker
__ACCEL_CHANNELS: Set[MovementChannel] = {
    MovementChannel.ACCELEROMETER_X,
    MovementChannel.ACCELEROMETER_Y,
    MovementChannel.ACCELEROMETER_Z,
}

# noinspection PyTypeChecker
__X_CHANNELS: Set[MovementChannel] = {
    MovementChannel.GYROSCOPE_X,
    MovementChannel.ACCELEROMETER_X
}

# noinspection PyTypeChecker
__Y_CHANNELS: Set[MovementChannel] = {
    MovementChannel.GYROSCOPE_Y,
    MovementChannel.ACCELEROMETER_Y
}

# noinspection PyTypeChecker
__Z_CHANNELS: Set[MovementChannel] = {
    MovementChannel.GYROSCOPE_Z,
    MovementChannel.ACCELEROMETER_Z
}


def __samples_for_channel(ch: 'Xyz', channel: MovementChannel) -> np.ndarray:
    if channel in __X_CHANNELS:
        return ch.get_x_samples().get_values()

    if channel in __Y_CHANNELS:
        return ch.get_y_samples().get_values()

    return ch.get_z_samples().get_values()


def __data_for_channel(sensors: Sensors,
                       channel: MovementChannel,
                       start_ts: float,
                       end_ts: float) -> Optional[np.ndarray]:
    sensor: Optional[Xyz] = sensors.get_gyroscope() if channel in __GYRO_CHANNELS else sensors.get_accelerometer()

    if sensor is None:
        return None

    ts: np.ndarray = sensor.get_timestamps().get_timestamps()
    samples: np.ndarray = __samples_for_channel(sensor, channel)
    sensor_data: __SensorData = __SensorData(ts, samples)
    return sensor_data.filter_samples(start_ts, end_ts)


def post_process(movement_event_stream: MovementEventStream,
                 sensors: Sensors,
                 max_merge_gap: datetime.timedelta = datetime.timedelta(seconds=0.5),
                 min_detection: datetime.timedelta = datetime.timedelta(seconds=0.1), ) -> MovementEventStream:
    res: MovementEventStream = MovementEventStream(movement_event_stream.name, [])

    # Group events by channel
    channel_to_events: Dict[MovementChannel, List[MovementEvent]] = defaultdict(list)
    for event in movement_event_stream.movement_events:
        channel_to_events[event.movement_channel].append(event)

    # For each channel, group packets that are "close together"
    for channel, events in channel_to_events.items():
        groups: List[List[MovementEvent]] = []
        group: List[MovementEvent] = [events[0]]

        for i in range(1, len(events)):
            prev: MovementEvent = events[i - 1]
            cur: MovementEvent = events[i]

            if prev.time_diff(cur) < max_merge_gap:
                group.append(cur)
            else:
                groups.append(group)
                group = [cur]

        if len(group) > 0:
            groups.append(group)

        # For each group, compute a new event using the raw data to update statistics
        for group in groups:
            start_ts: float = group[0].movement_start
            end_ts: float = group[-1].movement_end

            data: np.ndarray = __data_for_channel(sensors, channel, start_ts, end_ts)
            data_sq: np.ndarray = data * data
            res.movement_events.append(MovementEvent(
                channel,
                start_ts,
                end_ts,
                end_ts - start_ts,
                data_sq.min(),
                data_sq.max(),
                data_sq.max() - data_sq.min(),
                data_sq.mean(),
                data_sq.std()
            ))

    res.movement_events = list(filter(lambda ev: ev.movement_duration_td() >= min_detection, res.movement_events))
    return res
