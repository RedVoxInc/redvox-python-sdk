from unittest import TestCase

from redvox.api1000.common.mapping import Mapping
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM


class TestMapping(TestCase):
    def setUp(self) -> None:
        event_str: RedvoxPacketM.EventStream.Event = RedvoxPacketM.EventStream.Event(string_payload={"foo": "bar"})
        event_numeric: RedvoxPacketM.EventStream.Event = RedvoxPacketM.EventStream.Event(numeric_payload={"foo": 1.0})
        event_boolean: RedvoxPacketM.EventStream.Event = RedvoxPacketM.EventStream.Event(boolean_payload={"foo": True})
        event_byte: RedvoxPacketM.EventStream.Event = RedvoxPacketM.EventStream.Event(
            byte_payload={"foo": "bar".encode("utf-8")})

        self.str_mapping: Mapping[str] = Mapping(event_str.string_payload, str)
        self.numeric_mapping: Mapping[float] = Mapping(event_numeric.numeric_payload, float)
        self.boolean_mapping: Mapping[bool] = Mapping(event_boolean.boolean_payload, bool)
        self.byte_mapping: Mapping[bytes] = Mapping(event_byte.byte_payload, bytes)

        self.empty_str_mapping: Mapping[str] = Mapping(RedvoxPacketM.EventStream.Event().string_payload, str)

    def test_basic(self):
        self.assertEqual(self.str_mapping.get_metadata_count(), 1)
        self.assertEqual(self.numeric_mapping.get_metadata_count(), 1)
        self.assertEqual(self.boolean_mapping.get_metadata_count(), 1)
        self.assertEqual(self.byte_mapping.get_metadata_count(), 1)
        self.assertEqual(self.empty_str_mapping.get_metadata_count(), 0)
