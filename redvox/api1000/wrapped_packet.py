"""
This module provides a high level API for creating, reading, and editing RedVox compliant API 1000 files.
"""

import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class WrappedRedvoxPacketApi1000:
    def __init__(self, redvox_proto: redvox_api_1000_pb2.RedvoxPacket1000):
        pass

    @staticmethod
    def from_compressed_bytes(data: bytes) -> 'WrappedRedvoxPacketApi1000':
        pass

    @staticmethod
    def from_compressed_path(rdvxz_path: str) -> 'WrappedRedvoxPacketApi1000':
        pass
