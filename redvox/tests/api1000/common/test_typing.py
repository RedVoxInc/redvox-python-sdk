from unittest import TestCase
from typing import Any, Dict, List, Set

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM

from redvox.api1000.errors import ApiMError, ApiMTypeError, ApiMOtherError

from redvox.api1000.common.typing import check_type
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM


class TypingTests(TestCase):
    def test_primitives_ok(self):
        good_types: List[Any] = [
            [1, [int]],
            [1.0, [float]],
            [True, [bool]],
            ["foo", [str]],
            [[1], [list]],
            [{1}, [set]],
            [{1: 2}, [dict]],
        ]
        good_type: List[Any]
        for good_type in good_types:
            check_type(*good_type)

    def test_primitive_bad(self):
        bad_types: List[Any] = [
            [1, [float, bool, str, list, set, dict]],
            [1.0, [int, bool, str, list, set, dict]],
            [True, [int, float, str, list, set, dict]],
            ["foo", [int, float, bool, list, set, dict]],
            [[1], [int, float, bool, str, set, dict]],
            [{1}, [int, float, bool, str, list, dict]],
            [{1: 2}, [int, float, bool, str, list, set]]
        ]

        bad_type: List[Any]
        for bad_type in bad_types:
            with self.assertRaises(ApiMTypeError) as ctx:
                check_type(*bad_type)
            self.assertTrue("Expected type(s)" in str(ctx.exception))

    def test_custom_exception(self):
        with self.assertRaises(ApiMOtherError) as ctx:
            check_type(1.0, [int], exception=ApiMOtherError)
        self.assertTrue("Expected type(s)" in str(ctx.exception))
        self.assertTrue("ApiMOtherError" in str(ctx.exception))

    def test_additional_info(self):
        with self.assertRaises(ApiMTypeError) as ctx:
            check_type(1.0, [int], additional_info="foo")
        self.assertTrue("Expected type(s)" in str(ctx.exception))
        self.assertTrue("foo" in str(ctx.exception))

    # def test_sdk_types(self):
    #     packet_proto: RedvoxPacketM = RedvoxPacketM()
    #     packet: WrappedRedvoxPacketM = WrappedRedvoxPacketM(packet_proto)
    #     good_types: List[Any] = [
    #         [packet, WrappedRedvoxPacketM]
    #     ]
    #
    #     good_type: List[Any]
    #     for good_type in good_types:
    #         check_type(*good_type)
