from typing import Generic, Callable, List, Dict, TypeVar

from google.protobuf.json_format import MessageToJson, MessageToDict

from redvox.api1000.common.metadata import Metadata
from redvox.api1000.common.lz4 import compress

T = TypeVar('T')
P = TypeVar('P')


class ProtoRepeatedMessage(Generic[P, T]):
    def __init__(self,
                 parent_proto,
                 repeated_field_proto,
                 repeated_field_name: str,
                 from_proto: Callable[[P], T],
                 to_proto: Callable[[T], P]):
        self._parent_proto = parent_proto
        self._repeated_field_proto = repeated_field_proto
        self._repeated_field_name = repeated_field_name
        self._from_proto: Callable[[P], T] = from_proto
        self._to_proto: Callable[[T], P] = to_proto

    def get_count(self) -> int:
        return len(self._repeated_field_proto)

    def get_values(self) -> List[T]:
        return list(map(self._from_proto, self._repeated_field_proto))

    def set_values(self, values: List[T]) -> 'ProtoRepeatedMessage[P, T]':
        return self.clear_values().append_values(values)

    def append_values(self, values: List[T]) -> 'ProtoRepeatedMessage[P, T]':
        self._repeated_field_proto.extend(list(map(self._to_proto, values)))
        return self

    def clear_values(self) -> 'ProtoRepeatedMessage[P, T]':
        self._parent_proto.ClearField(self._repeated_field_name)
        return self


class ProtoBase(Generic[P]):
    def __init__(self,
                 proto: P):
        self._proto: P = proto
        self._metadata: Metadata = Metadata(self._proto.metadata)

    def get_proto(self) -> P:
        return self._proto

    def get_metadata(self) -> Metadata:
        return self._metadata

    def as_json(self) -> str:
        return MessageToJson(self._proto, True)

    def as_dict(self) -> Dict:
        return MessageToDict(self._proto, True)

    def as_bytes(self) -> bytes:
        return self._proto.SerializeToString()

    def as_compressed_bytes(self) -> bytes:
        data: bytes = self.as_bytes()
        return compress(data)

    def __str__(self):
        return self.as_json()


