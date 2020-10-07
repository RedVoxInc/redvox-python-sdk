"""
Contains classes and methods for examining movement events.
"""

from dataclasses import dataclass
import datetime
from enum import Enum
from typing import Dict, List, TYPE_CHECKING

from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc

if TYPE_CHECKING:
    from redvox.api1000.wrapped_redvox_packet.event_streams import Event, EventStream
    from redvox.api1000.common.mapping import Mapping


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
