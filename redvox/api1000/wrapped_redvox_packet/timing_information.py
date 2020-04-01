from typing import List

import redvox.api1000.common as common
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class SynchExchange(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.TimingInformation.SynchExchange):
        super().__init__(proto)

    @staticmethod
    def new() -> 'SynchExchange':
        return SynchExchange(redvox_api_1000_pb2.RedvoxPacket1000.TimingInformation.SynchExchange())

    def get_a1(self) -> float:
        return self._proto.a1

    def set_a1(self, a1: float) -> 'SynchExchange':
        common.check_type(a1, [int, float])
        self._proto.a1 = a1
        return self

    def get_a2(self) -> float:
        return self._proto.a2

    def set_a2(self, a2: float) -> 'SynchExchange':
        common.check_type(a2, [int, float])
        self._proto.a2 = a2
        return self

    def get_a3(self) -> float:
        return self._proto.a3

    def set_a3(self, a3: float) -> 'SynchExchange':
        common.check_type(a3, [int, float])
        self._proto.a3 = a3
        return self

    def get_b1(self) -> float:
        return self._proto.b1

    def set_b1(self, b1: float) -> 'SynchExchange':
        common.check_type(b1, [int, float])
        self._proto.b1 = b1
        return self

    def get_b2(self) -> float:
        return self._proto.b2

    def set_b2(self, b2: float) -> 'SynchExchange':
        common.check_type(b2, [int, float])
        self._proto.b2 = b2
        return self

    def get_b3(self) -> float:
        return self._proto.b3

    def set_b3(self, b3: float) -> 'SynchExchange':
        common.check_type(b3, [int, float])
        self._proto.b3 = b3
        return self


class TimingInformation(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.TimingInformation):
        super().__init__(proto)

    @staticmethod
    def new() -> 'TimingInformation':
        return TimingInformation(redvox_api_1000_pb2.RedvoxPacket1000.TimingInformation())

    def get_packet_start_ts_us_wall(self) -> float:
        return self._proto.packet_start_ts_us_wall

    def set_packet_start_ts_us_wall(self, packet_start_ts_us_wall: float) -> 'TimingInformation':
        common.check_type(packet_start_ts_us_wall, [int, float])
        self._proto.packet_start_ts_us_wall = packet_start_ts_us_wall
        return self

    def get_packet_start_ts_us_mach(self) -> float:
        return self._proto.packet_start_ts_us_mach

    def set_packet_start_ts_us_mach(self, packet_start_ts_us_mach: float) -> 'TimingInformation':
        common.check_type(packet_start_ts_us_mach, [int, float])
        self._proto.packet_start_ts_us_mach = packet_start_ts_us_mach
        return self

    def get_packet_end_ts_us_wall(self) -> float:
        return self._proto.packet_end_ts_us_wall

    def set_packet_end_ts_us_wall(self, packet_end_ts_us_wall: float) -> 'TimingInformation':
        common.check_type(packet_end_ts_us_wall, [int, float])
        self._proto.packet_end_ts_us_wall = packet_end_ts_us_wall
        return self

    def get_packet_end_ts_us_mach(self) -> float:
        return self._proto.packet_end_ts_us_mach

    def set_packet_end_ts_us_mach(self, packet_end_ts_us_mach: float) -> 'TimingInformation':
        common.check_type(packet_end_ts_us_mach, [int, float])
        self._proto.packet_end_ts_us_mach = packet_end_ts_us_mach
        return self

    def get_server_acquisition_arrival_ts_us(self) -> float:
        return self._proto.server_acquisition_arrival_ts_us

    def set_server_acquisition_arrival_ts_us(self, server_acquisition_arrival_ts_us: float) -> 'TimingInformation':
        common.check_type(server_acquisition_arrival_ts_us, [int, float])
        self._proto.server_acquisition_arrival_ts_us = server_acquisition_arrival_ts_us
        return self

    def get_app_start_ts_us_mach(self) -> float:
        return self._proto.app_start_ts_us_mach

    def set_app_start_ts_us_mach(self, app_start_ts_us_mach: float) -> 'TimingInformation':
        common.check_type(app_start_ts_us_mach, [int, float])
        self._proto.app_start_ts_us_mach = app_start_ts_us_mach
        return self

    def get_synch_exchanges(self) -> List[SynchExchange]:
        pass

    def set_synch_exchanges(self, synch_exchanges: List[SynchExchange]) -> 'TimingInformation':
        pass

    def get_best_latency(self) -> float:
        return self._proto.best_latency_us

    def set_best_latency_us(self, best_latency_us: float) -> 'TimingInformation':
        common.check_type(best_latency_us, [int, float])
        self._proto.best_latency_us = best_latency_us
        return self

    def get_best_offset(self) -> float:
        return self._proto.best_offset_us

    def set_best_offset_us(self, best_offset_us: float) -> 'TimingInformation':
        common.check_type(best_offset_us, [int, float])
        self._proto.best_offset_us = best_offset_us
        return self
