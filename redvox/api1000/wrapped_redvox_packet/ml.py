"""
This module provides methods and datatypes for the efficient extraction and manipulation of machine learning data stored
 in RedVox packet EventStreams.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List

import numpy as np
from redvox.api1000.common.generic import ProtoRepeatedMessage
from redvox.api1000.wrapped_redvox_packet.event_streams import EventStream, Event
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM

ML_CLASS_PREFIX: str = "class_"
ML_SCORE_PREFIX: str = "score_"
ML_EVENT_STREAM_NAME: str = "inference"
ML_METADATA_MODEL_VERSION_KEY: str = "model_version"
ML_METADATA_INPUT_SAMPLES_PER_HOP_KEY: str = "input_samples_per_hop"
ML_METADATA_INPUT_SAMPLE_RATE_KEY: str = "input_sample_rate"
ML_METADATA_INPUT_SAMPLES_PER_WINDOW_KEY: str = "input_samples_per_window"


@dataclass
class ExtractedMl:
    """
    Contains the extracted ML classes and scores as well as metadata relating to the utilized model.
    """

    metadata: "MlMetadata"
    windows: List["MlWindow"]

    def sort(self, sort_by: "SortBy") -> "ExtractedMl":
        """
        Sorts the labels in ascending or descending order by either score of class name.
        :param sort_by: The sort operation to use.
        :return: An updated instance of ExtractedMl.
        """
        self.windows = list(map(lambda window: window.sort(sort_by), self.windows))
        return self

    def prune_zeros(self) -> "ExtractedMl":
        """
        Removes labels that have a score of 0.
        :return: An updated instance of ExtractedMl.
        """
        self.windows = list(map(lambda window: window.prune_zeros(), self.windows))
        return self

    def prune_lt(self, min_v: float) -> "ExtractedMl":
        """
        Prunes labels with score less than the provided minimum.
        :param min_v: The minimum acceptable label score.
        :return: An updated instance of ExtractedMl.
        """
        self.windows = list(map(lambda window: window.prune_lt(min_v), self.windows))
        return self

    def retain_top(self, n: int) -> "ExtractedMl":
        """
        Sorts labels in descending order by score and only keeps up to the top n labels.
        :param n: The number of labels to keep.
        :return: An updated instance of ExtractedMl.
        """
        self.windows = list(map(lambda window: window.retain_top(n), self.windows))
        return self


@dataclass
class MlMetadata:
    """
    Metadata relating to the utilized ML model.
    """

    model_name: str
    model_version: str
    input_samples_per_hop: int
    input_sample_rate: int
    input_samples_per_window: int


@dataclass
class MlWindow:
    """
    Labels from a single time window.
    """

    timestamp: int
    labels: List["Label"]

    def sort(self, sort_by: "SortBy") -> "MlWindow":
        """
        Sorts the labels in ascending or descending order by either score of class name.
        :param sort_by: The sort operation to use.
        :return: An updated instance of MlWindow.
        """
        if sort_by is SortBy.CLASS_ASC:
            self.labels = sorted(self.labels, key=lambda label: label.class_name)
        elif sort_by is SortBy.CLASS_DESC:
            self.labels = sorted(
                self.labels, key=lambda label: label.class_name, reverse=True
            )
        elif sort_by is SortBy.SCORE_ASC:
            self.labels = sorted(self.labels, key=lambda label: label.score)
        else:
            self.labels = sorted(
                self.labels, key=lambda label: label.score, reverse=True
            )

        return self

    def prune_zeros(self) -> "MlWindow":
        """
        Removes labels that have a score of 0.
        :return: An updated instance of MlWindow.
        """
        self.labels = list(filter(lambda label: label.score > 0, self.labels))
        return self

    def prune_lt(self, min_v: float) -> "MlWindow":
        """
        Prunes labels with score less than the provided minimum.
        :param min_v: The minimum acceptable label score.
        :return: An updated instance of MlWindow.
        """
        self.labels = list(filter(lambda label: label.score >= min_v, self.labels))
        return self

    def retain_top(self, n: int) -> "MlWindow":
        """
        Sorts labels in descending order by score and only keeps up to the top n labels.
        :param n: The number of labels to keep.
        :return: An updated instance of MlWindow.
        """
        sorted_window: MlWindow = self.sort(SortBy.SCORE_DESC)
        sorted_window.labels = sorted_window.labels[:n]
        return sorted_window


@dataclass
class Label:
    """
    A pair containing a class name and a score.
    """

    class_name: str
    score: float


class SortBy(Enum):
    """
    An enumeration that represents the valid label sorting methods.
    """

    SCORE_ASC: int = 1
    SCORE_DESC: int = 2
    CLASS_ASC: int = 3
    CLASS_DESC: int = 4


def extract_ml_metadata(stream: EventStream) -> MlMetadata:
    """
    Extracts ML metadata from an event stream.
    :param stream: The event stream to extract the ML metadata from.
    :return: An instance of MlMetadata.
    """
    meta: Dict[str, str] = stream.get_metadata().get_metadata()
    name: str = stream.get_events().get_values()[0].get_description()
    return MlMetadata(
        name,
        meta[ML_METADATA_MODEL_VERSION_KEY],
        int(meta[ML_METADATA_INPUT_SAMPLES_PER_HOP_KEY]),
        int(meta[ML_METADATA_INPUT_SAMPLE_RATE_KEY]),
        int(meta[ML_METADATA_INPUT_SAMPLES_PER_WINDOW_KEY]),
    )


def find_ml_event_stream(packet: WrappedRedvoxPacketM) -> Optional[EventStream]:
    """
    Attempts to find an event stream with ML data.
    :param packet: The packet to search in.
    :return: An instance of the matching event stream or None.
    """
    streams: ProtoRepeatedMessage = packet.get_event_streams()

    stream: EventStream
    for stream in streams.get_values():
        if stream.get_name() == ML_EVENT_STREAM_NAME:
            return stream

    return None


def label_at(
    str_payload: Dict[str, str], num_payload: Dict[str, float], idx: int
) -> Label:
    """
    Finds the label and score in the event payloads.
    :param str_payload: The event string payload.
    :param num_payload: The event numeric payload.
    :param idx: The index of the class and score.
    :return: An instance of a Label.
    """
    class_key: str = f"{ML_CLASS_PREFIX}{idx}"
    score_key: str = f"{ML_SCORE_PREFIX}{idx}"

    class_name: str = str_payload[class_key]
    score: float = num_payload[score_key]

    return Label(class_name, score)


def extract_ml_windows(stream: EventStream) -> Optional[List[MlWindow]]:
    """
    Extracts ML windows from an event stream.
    :param stream: The stream to extract windows from.
    :return: A list of ML windows.
    """
    if stream.get_name() != ML_EVENT_STREAM_NAME:
        return None

    timestamps: np.ndarray = stream.get_timestamps().get_timestamps()
    windows: List[MlWindow] = []

    events: List[Event] = stream.get_events().get_values()

    idx_window: int
    timestamp: float
    for (idx_window, timestamp) in enumerate(timestamps):
        event: Event = events[idx_window]
        str_payload: Dict[str, str] = event.get_string_payload().get_metadata()
        num_payload: Dict[str, float] = event.get_numeric_payload().get_metadata()

        labels: List[Label] = []
        for i in range(len(str_payload)):
            label: Label = label_at(str_payload, num_payload, i)
            labels.append(label)

        window: MlWindow = MlWindow(int(round(timestamp)), labels)
        windows.append(window)

    return windows


def extract_ml_from_event_stream(stream: EventStream) -> Optional[ExtractedMl]:
    """
    Extract ML parameters from an event stream.
    :param stream: The event stream to extract ML parameters from.
    :return: The extracted ML parameters or None.
    """
    if stream.get_name() != ML_EVENT_STREAM_NAME:
        return None

    metadata: MlMetadata = extract_ml_metadata(stream)
    windows: List[MlWindow] = extract_ml_windows(stream)
    return ExtractedMl(metadata, windows)


def extract_ml_from_packet(packet: WrappedRedvoxPacketM) -> Optional[ExtractedMl]:
    """
    Extract ML parameters from an event stream.
    :param packet: The packet to extract ML parameters from.
    :return: The extracted ML parameters or None.
    """
    stream: Optional[EventStream] = find_ml_event_stream(packet)
    if stream is None:
        return None
    return extract_ml_from_event_stream(stream)


def extract_ml_from_file(file_path: str) -> Optional[ExtractedMl]:
    """
    Extract ML parameters from a file.
    :param file_path: The path of the packet to extract ML parameters from.
    :return: The extracted ML parameters or None.
    """
    packet: WrappedRedvoxPacketM = WrappedRedvoxPacketM.from_compressed_path(file_path)
    return extract_ml_from_packet(packet)
