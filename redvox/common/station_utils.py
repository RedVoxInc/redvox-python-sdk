"""
Defines generic station metadata for API-independent analysis
all timestamps are floats in microseconds unless otherwise stated
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass
class StationKey:
    """
    A set of values that uniquely define a station
    Properties:
        id: str, id of the station
        uuid: str, uuid of the station
        start_timestamp_micros: float, starting time of the station in microseconds since epoch UTC
    """
    id: str
    uuid: str
    start_timestamp_micros: float

    def get_key(self) -> Tuple[str, str, float]:
        return self.id, self.uuid, self.start_timestamp_micros
