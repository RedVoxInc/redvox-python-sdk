"""
This module provides a high level API for creating, reading, and editing RedVox compliant API 1000 files.
"""

from typing import Dict, List
import statistics

import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2

class SummaryStatistics:
    def __init__(self, summary_statistics_proto: redvox_api_1000_pb2.SummaryStatistics):
        self.proto: redvox_api_1000_pb2.SummaryStatistics = summary_statistics_proto

    @staticmethod
    def new() -> 'SummaryStatistics':
        proto: redvox_api_1000_pb2.SummaryStatistics = redvox_api_1000_pb2.SummaryStatistics()
        return SummaryStatistics(proto)

    def update_from_values(self, values: List[float]):
        self.proto.count = len(values)
        self.proto.mean = statistics.mean(values)
        self.proto.median = statistics.median(values)
        self.proto.mode = statistics.mode(values)
        self.proto.variance = statistics.variance(values)
        self.proto.min = min(values)
        self.proto.max = max(values)
        self.proto.range = self.proto.max - self.proto.min

    def __str__(self) -> str:
        return str(self.proto)


class MicrophoneChannel:
    pass

class WrappedRedvoxPacketApi1000:
    def __init__(self, redvox_proto: redvox_api_1000_pb2.RedvoxPacket1000):
        pass

    @staticmethod
    def from_compressed_bytes(data: bytes) -> 'WrappedRedvoxPacketApi1000':
        pass

    @staticmethod
    def from_compressed_path(rdvxz_path: str) -> 'WrappedRedvoxPacketApi1000':
        pass
