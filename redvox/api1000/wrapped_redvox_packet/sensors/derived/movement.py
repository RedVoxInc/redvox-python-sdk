"""
Contains classes and methods for examining movement events.
"""

from collections import defaultdict
from dataclasses import dataclass
import datetime
from enum import Enum
from functools import total_ordering
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple

import numpy as np

from redvox.common.constants import NAN
from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc

if TYPE_CHECKING:
    from redvox.api1000.common.mapping import Mapping
    from redvox.api1000.wrapped_redvox_packet.event_streams import Event, EventStream
    from redvox.api1000.wrapped_redvox_packet.sensors.sensors import Sensors
    from redvox.api1000.wrapped_redvox_packet.sensors.xyz import Xyz
    from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM


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


# noinspection DuplicatedCode
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

    def time_diff(self, other: "MovementEvent") -> datetime.timedelta:
        """
        Returns the time difference between two events.
        :param other: The other event to compare against.
        :return: The time difference between this and another event.
        """
        events: List["MovementEvent"] = sorted([self, other])
        fst: "MovementEvent" = events[0]
        scd: "MovementEvent" = events[1]

        return scd.movement_start_dt() - fst.movement_start_dt()

    @staticmethod
    def from_event(event: "Event") -> "MovementEvent":
        """
        Converts a generic API M Event into a MovementEvent.
        :param event: The Event to convert.
        :return: A MovementEvent.
        """
        numeric_payload: "Mapping[float]" = event.get_numeric_payload()
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
        return (
            isinstance(other, MovementEvent)
            and self.movement_start == other.movement_start
        )

    def __lt__(self, other: "MovementEvent") -> bool:
        return self.movement_start < other.movement_start


# noinspection DuplicatedCode
@dataclass
class MovementEventStream:
    """
    Represents a derived movement event stream.
    """

    name: str
    movement_events: List[MovementEvent]

    @staticmethod
    def from_event_stream(event_stream: "EventStream") -> "MovementEventStream":
        """
        Converts an API M EventStream into a MovementEventStream.
        :param event_stream: Stream to convert.
        :return: A MovementEventStream.
        """
        movement_events: List[MovementEvent] = list(
            map(MovementEvent.from_event, event_stream.get_events().get_values())
        )

        movement_events.sort(key=lambda event: event.movement_start_dt())
        return MovementEventStream(event_stream.get_name(), movement_events)

    def events_by_channel(
        self, movement_channel: MovementChannel
    ) -> List[MovementEvent]:
        """
        Returns events for a given channel.
        :param movement_channel: Channel to filter events for.
        :return: A list of movement events.
        """
        return list(
            filter(
                lambda event: event.movement_channel == movement_channel,
                self.movement_events,
            )
        )


@dataclass
class _Stats:
    """
    An encapsulation of summary stats used when updating stats for merged Events.
    """

    mag_min: float = NAN
    mag_max: float = NAN
    mag_range: float = NAN
    mag_mean: float = NAN
    mag_std: float = NAN

    @staticmethod
    def from_samples(samples: np.ndarray) -> "_Stats":
        """
        Converts a set of samples into _Stats.
        :param samples: Samples to calculate stats over.
        :return: An instance of _Stats.
        """
        # noinspection PyArgumentList
        mag_min: float = samples.min()
        # noinspection PyArgumentList
        mag_max: float = samples.max()

        return _Stats(
            mag_min, mag_max, mag_max - mag_min, samples.mean(), samples.std()
        )


# noinspection DuplicatedCode
@dataclass
class MovementData:
    """
    Encapsulates movement data from multiple packets from a single station.
    """

    movement_event_stream: MovementEventStream
    accelerometer_timestamps: Optional[np.ndarray]
    accelerometer_x: Optional[np.ndarray]
    accelerometer_y: Optional[np.ndarray]
    accelerometer_z: Optional[np.ndarray]
    gyroscope_timestamps: Optional[np.ndarray]
    gyroscope_x: Optional[np.ndarray]
    gyroscope_y: Optional[np.ndarray]
    gyroscope_z: Optional[np.ndarray]

    @staticmethod
    def from_packets(packets: List["WrappedRedvoxPacketM"]) -> "MovementData":
        """
        Extracts and concatenates movement data.
        :param packets: The packets to extract movement data from.
        :return: An instance of MovementData.
        """
        movement_event_stream: MovementEventStream = MovementEventStream("Movement", [])
        accelerometer_timestamps: np.ndarray = np.array([])
        accelerometer_x: np.ndarray = np.array([])
        accelerometer_y: np.ndarray = np.array([])
        accelerometer_z: np.ndarray = np.array([])
        gyroscope_timestamps: np.ndarray = np.array([])
        gyroscope_x: np.ndarray = np.array([])
        gyroscope_y: np.ndarray = np.array([])
        gyroscope_z: np.ndarray = np.array([])

        for packet in packets:
            if packet.get_event_streams().get_count() == 1:
                event_stream: "EventStream" = packet.get_event_streams().get_values()[0]
                movement_event_stream.movement_events.extend(
                    list(
                        map(
                            MovementEvent.from_event,
                            event_stream.get_events().get_values(),
                        )
                    )
                )

            sensors: "Sensors" = packet.get_sensors()
            accel: Optional["Xyz"] = sensors.get_accelerometer()
            gyro: Optional["Xyz"] = sensors.get_gyroscope()

            if accel is not None:
                accelerometer_timestamps = np.concatenate(
                    (accelerometer_timestamps, accel.get_timestamps().get_timestamps())
                )
                accelerometer_x = np.concatenate(
                    (accelerometer_x, accel.get_x_samples().get_values())
                )
                accelerometer_y = np.concatenate(
                    (accelerometer_y, accel.get_y_samples().get_values())
                )
                accelerometer_z = np.concatenate(
                    (accelerometer_z, accel.get_z_samples().get_values())
                )

            if gyro is not None:
                gyroscope_timestamps = np.concatenate(
                    (gyroscope_timestamps, gyro.get_timestamps().get_timestamps())
                )
                gyroscope_x = np.concatenate(
                    (gyroscope_x, gyro.get_x_samples().get_values())
                )
                gyroscope_y = np.concatenate(
                    (gyroscope_y, gyro.get_y_samples().get_values())
                )
                gyroscope_z = np.concatenate(
                    (gyroscope_z, gyro.get_z_samples().get_values())
                )

        return MovementData(
            movement_event_stream,
            accelerometer_timestamps,
            accelerometer_x,
            accelerometer_y,
            accelerometer_z,
            gyroscope_timestamps,
            gyroscope_x,
            gyroscope_y,
            gyroscope_z,
        )

    def data_for_channel(
        self, channel: MovementChannel
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the timestamps and samples for a given channel.
        :param channel: Channel to return data for.
        :return: A tuple containing the timestamps and samples for the provided channel.
        """
        if channel == MovementChannel.ACCELEROMETER_X:
            return self.accelerometer_timestamps, self.accelerometer_x

        if channel == MovementChannel.ACCELEROMETER_Y:
            return self.accelerometer_timestamps, self.accelerometer_y

        if channel == MovementChannel.ACCELEROMETER_Z:
            return self.accelerometer_timestamps, self.accelerometer_z

        if channel == MovementChannel.GYROSCOPE_X:
            return self.gyroscope_timestamps, self.gyroscope_x

        if channel == MovementChannel.GYROSCOPE_Y:
            return self.gyroscope_timestamps, self.gyroscope_y

        return self.gyroscope_timestamps, self.gyroscope_z

    def __update_stats(
        self, movement_channel: MovementChannel, start_ts: float, end_ts: float
    ) -> _Stats:
        """
        Compute summary statistics for a particular channel within a particular window.
        :param movement_channel: The channel to compute statistics from.
        :param start_ts: The start time as microseconds since the epoch.
        :param end_ts: The end time as microseconds since the epoch.
        :return: An instance of _Stats.
        """
        timestamps: np.ndarray
        samples: np.ndarray
        (timestamps, samples) = self.data_for_channel(movement_channel)
        samples = samples * samples

        start_idx: Optional[int] = None
        end_idx: Optional[int] = None

        # The goal here is to find the first index that matches the start time and the first index that matches the end
        # time in a single O(N) pass. TODO: this could be improved with binary search.
        i: int = 0
        for i, timestamp in enumerate(timestamps):
            if timestamp >= start_ts:
                start_idx = i
                break

        for j in range(i, len(timestamps)):
            timestamp = timestamps[j]
            if timestamp >= end_ts:
                end_idx = j + 1
                break

        if start_idx is None or end_idx is None:
            return _Stats()

        return _Stats.from_samples(samples[start_idx:end_idx])

    def __merge_movement_events(self, max_merge_gap: datetime.timedelta):
        """
        Merges movement events that are "close together".
        :param max_merge_gap: Any consecutive events that are smaller than this timedelta will be merged.
        """
        res: MovementEventStream = MovementEventStream(
            self.movement_event_stream.name, []
        )

        # Group events by channel
        channel_to_events: Dict[MovementChannel, List[MovementEvent]] = defaultdict(
            list
        )
        for event in self.movement_event_stream.movement_events:
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
                stats: _Stats = self.__update_stats(channel, start_ts, end_ts)
                movement_event: MovementEvent = MovementEvent(
                    channel,
                    start_ts,
                    end_ts,
                    end_ts - start_ts,
                    stats.mag_min,
                    stats.mag_max,
                    stats.mag_range,
                    stats.mag_mean,
                    stats.mag_std,
                )
                res.movement_events.append(movement_event)

        # Replace the current MovementEventStream with the updated one
        self.movement_event_stream = res

    def post_process(
        self,
        max_merge_gap: Optional[datetime.timedelta] = None,
        min_detection: Optional[datetime.timedelta] = None,
    ):
        """
        Performs post-processing on the MovementEventStream to optionally merge close together events and filter out
        short-duration events.
        :param max_merge_gap: When provided, any consecutive packets that have gaps less than this value will be merged.
        :param min_detection: When provided, events with a duration less than this value will be filtered out.
        """

        if max_merge_gap is not None:
            self.__merge_movement_events(max_merge_gap)

        if min_detection is not None:
            self.movement_event_stream.movement_events = list(
                filter(
                    lambda event: event.movement_duration_td() >= min_detection,
                    self.movement_event_stream.movement_events,
                )
            )
