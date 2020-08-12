from enum import Enum
import unittest

from google.protobuf.internal.enum_type_wrapper import EnumTypeWrapper

from redvox.api1000.common.decorators import wrap_enum
from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM


class TestDecorators(unittest.TestCase):
    def test_wrap_enum(self):
        @wrap_enum(RedvoxPacketM.StationInformation.OsType)
        class OsType(Enum):
            UNKNOWN_OS: int = 0
            ANDROID: int = 1
            IOS: int = 2
            OSX: int = 3
            LINUX: int = 4
            WINDOWS: int = 5

        os_type = OsType.ANDROID
        self.assertIsNotNone(getattr(os_type, "into_proto", None))
        self.assertIsNotNone(getattr(OsType, "from_proto", None))

        proto_enum: EnumTypeWrapper = os_type.into_proto()
        self.assertEqual(proto_enum, RedvoxPacketM.StationInformation.OsType.ANDROID)
        original_enum: OsType = OsType.from_proto(proto_enum)
        self.assertEqual(original_enum, OsType.ANDROID)
