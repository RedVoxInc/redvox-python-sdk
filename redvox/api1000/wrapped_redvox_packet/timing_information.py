from typing import List

import redvox.api1000.wrapped_redvox_packet.common as common
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class SynchExchange(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.TimingInformation.SynchExchange):
        super().__init__(proto)

    @staticmethod
    def new() -> 'SynchExchange':
        return SynchExchange(redvox_api_1000_pb2.RedvoxPacket1000.TimingInformation.SynchExchange())

    def get_unit(self) -> common.Unit:
        return common.Unit.from_proto(self._proto.unit)

    def set_unit(self, unit: common.Unit) -> 'SynchExchange':
        common.check_type(unit, [common.Unit])
        self._proto.unit = unit.into_proto()
        return self

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

    def get_unit(self) -> common.Unit:
        return common.Unit.from_proto(self._proto.unit)

    def set_unit(self, unit: common.Unit) -> 'TimingInformation':
        common.check_type(unit, [common.Unit])
        self._proto.unit = unit.into_proto()
        return self

    def get_packet_start_os_timestamp(self) -> float:
        return self._proto.packet_start_os_timestamp

    def set_packet_start_os_timestamp(self, packet_start_os_timestamp) -> 'TimingInformation':
        common.check_type(packet_start_os_timestamp, [int, float])
        self._proto.packet_start_os_timestamp = packet_start_os_timestamp
        return self

    def get_packet_start_mach_timestamp(self) -> float:
        return self._proto.packet_start_mach_timestamp

    def set_packet_start_mach_timestamp(self, packet_start_mach_timestamp: float) -> 'TimingInformation':
        common.check_type(packet_start_mach_timestamp, [int, float])
        self._proto.packet_start_mach_timestamp = packet_start_mach_timestamp
        return self

    def get_packet_end_os_timestamp(self) -> float:
        return self._proto.packet_end_os_timestamp

    def set_packet_end_os_timestamp(self, packet_end_os_timestamp: float) -> 'TimingInformation':
        common.check_type(packet_end_os_timestamp, [int, float])
        self._proto.packet_end_os_timestamp = packet_end_os_timestamp
        return self

    def get_packet_end_mach_timestamp(self) -> float:
        return self._proto.packet_end_mach_timestamp

    def set_packet_end_mach_timestamp(self, packet_end_mach_timestamp: float) -> 'TimingInformation':
        common.check_type(packet_end_mach_timestamp, [int, float])
        self._proto.packet_end_mach_timestamp = packet_end_mach_timestamp
        return self

    def get_server_acquisition_arrival_timestamp(self) -> float:
        return self._proto.server_acquisition_arrival_timestamp

    def set_server_acquisition_arrival_timestamp(self, server_acquisition_arrival_timestamp: float) -> 'TimingInformation':
        common.check_type(server_acquisition_arrival_timestamp, [int, float])
        self._proto.server_acquisition_arrival_timestamp = server_acquisition_arrival_timestamp
        return self

    def get_app_start_mach_timestamp(self) -> float:
        return self._proto.app_start_mach_timestamp

    def set_app_start_mach_timestamp(self, app_start_mach_timestamp: float) -> 'TimingInformation':
        common.check_type(app_start_mach_timestamp, [int, float])
        self._proto.app_start_mach_timestamp = app_start_mach_timestamp
        return self

    def get_synch_exchanges(self) -> List[SynchExchange]:
        pass

    def set_synch_exchanges(self, synch_exchanges: List[SynchExchange]) -> 'TimingInformation':
        pass

    def get_best_latency(self) -> float:
        return self._proto.best_latency

    def set_best_latency(self, best_latency: float) -> 'TimingInformation':
        common.check_type(best_latency, [int, float])
        self._proto.best_latency= best_latency
        return self

    def get_best_offset(self) -> float:
        return self._proto.best_offset

    def set_best_offset(self, best_offset: float) -> 'TimingInformation':
        common.check_type(best_offset, [int, float])
        self._proto.best_offset = best_offset
        return self
