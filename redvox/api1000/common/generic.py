"""
This module contains classes and function that make use of generics. As of April 2020, IntelliJ still does not parse
generics correctly and cause errors to appear where there are none. However, generics can still be statically checked by
mypy, and unless we decide to remove generics, we will place them here.
"""

from typing import Generic, Callable, List, Dict, TypeVar

from google.protobuf.json_format import MessageToJson, MessageToDict

from redvox.api1000.common.metadata import Metadata
from redvox.api1000.common.lz4 import compress

# pylint: disable=C0103
T = TypeVar("T")  # Type parameter for transformed wrapper type
# pylint: disable=C0103
P = TypeVar("P")  # Type parameter for protobuf type


class ProtoRepeatedMessage(Generic[P, T]):
    """
    Encapsulates protobuf repeated fields while transforming values between protobuf and wrapper types.
    """

    def __init__(
        self,
        parent_proto,
        repeated_field_proto,
        repeated_field_name: str,
        from_proto: Callable[[P], T],
        to_proto: Callable[[T], P],
    ):
        """
        :param parent_proto: A reference to this message's parent protobuf
        :param repeated_field_proto: A reference to the repeated field protobuf
        :param repeated_field_name: The name of the repeated protobuf field
        :param from_proto: A function that converts a repeated protobuf value into its wrapper equivelent
        :param to_proto: A function that converts a repeated wrapper value into its protobuf equivelent
        """
        self._parent_proto = parent_proto
        self._repeated_field_proto = repeated_field_proto
        self._repeated_field_name = repeated_field_name
        self._from_proto: Callable[[P], T] = from_proto
        self._to_proto: Callable[[T], P] = to_proto

    def get_count(self) -> int:
        """
        Returns the number of items in this repeated collection.
        :return: The number of items in this repeated collection.
        """
        return len(self._repeated_field_proto)

    def get_values(self) -> List[T]:
        """
        Returns a list of wrapped items stored in this collection.
        :return: A list of wrapped items stored in this collection.
        """
        return list(map(self._from_proto, self._repeated_field_proto))

    def set_values(self, values: List[T]) -> "ProtoRepeatedMessage[P, T]":
        """
        Sets the contents of this collection to the passed in values. The wrapped values are automatically converted
        into protobuf messages.
        :param values: The wrapped values to set.
        :return: This instance of ProtoRepeatedMessage.
        """
        return self.clear_values().append_values(values)

    def append_values(self, values: List[T]) -> "ProtoRepeatedMessage[P, T]":
        """
        Appends the given values to the collection, automatically converting them into protobuf messages.
        :param values: The wrapped values to append.
        :return: This instance of ProtoRepeatedMessage.
        """
        self._repeated_field_proto.extend(list(map(self._to_proto, values)))
        return self

    def clear_values(self) -> "ProtoRepeatedMessage[P, T]":
        """
        Clears all values in this collection.
        :return: This instance of ProtoRepeatedMessage.
        """
        # self._parent_proto.ClearField(self._repeated_field_name)
        del self._repeated_field_proto[:]
        return self

    def __str__(self):
        return str(self._repeated_field_proto)

    def __repr__(self):
        return str(self)


class ProtoBase(Generic[P]):
    """
    This class represents common routines between all sub-messages in API M.
    """

    def __init__(self, proto: P):
        self._proto: P = proto
        self._metadata: Metadata = Metadata(self._proto.metadata)

    def get_proto(self) -> P:
        """
        Return the backing protobuf for this class.
        :return: The backing protobuf for this class.
        """
        return self._proto

    def get_metadata(self) -> Metadata:
        """
        Returns the associated Metadata instance.
        :return: The associated Metadata instance.
        """
        return self._metadata

    def as_json(self) -> str:
        """
        Serializes and returns the backing protobuf as JSON.
        :return: The backing protobuf as JSON.
        """
        return MessageToJson(self._proto, True)

    def as_dict(self) -> Dict:
        """
        Serializes and returns the backing protobuf as a Python dictionary.
        :return: The backing protobuf as a Python dictionary.
        """
        return MessageToDict(self._proto, True)

    def as_bytes(self) -> bytes:
        """
        Serializes and returns the backing protobuf as bytes.
        :return: The backing protobuf as bytes.
        """
        return self._proto.SerializeToString()

    def as_compressed_bytes(self) -> bytes:
        """
        Serializes and returns the backing protobuf as compressed bytes.
        :return: The backing protobuf as compressed bytes.
        """
        data: bytes = self.as_bytes()
        return compress(data)

    def __str__(self):
        """
        Return the JSON representation of the backing protobuf,
        :return: The JSON representation of the backing protobuf.
        """
        return self.as_json()
