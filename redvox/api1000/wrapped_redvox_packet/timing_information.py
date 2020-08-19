import enum
from typing import List, Union

import redvox.api1000.common.typing
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2
import redvox.api1000.common.common as common
import redvox.api1000.common.generic

from redvox.api1000.common.decorators import wrap_enum

_SYNCH_EXCHANGES_FIELD_NAME: str = "synch_exchanges"
SynchExchangeProto = redvox_api_m_pb2.RedvoxPacketM.TimingInformation.SynchExchange


class SynchExchange(
    redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.TimingInformation.SynchExchange]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.TimingInformation.SynchExchange):
        super().__init__(proto)

    @staticmethod
    def new() -> 'SynchExchange':
        exchange = SynchExchange(redvox_api_m_pb2.RedvoxPacketM.TimingInformation.SynchExchange())
        exchange.set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)
        return exchange

    def get_unit(self) -> common.Unit:
        return common.Unit.from_proto(self._proto.unit)

    def set_default_unit(self) -> 'SynchExchange':
        return self.set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)

    def set_unit(self, unit: Union[common.Unit, int]) -> 'SynchExchange':
        redvox.api1000.common.typing.check_type(unit, [common.Unit])
        self._proto.unit = unit.into_proto()
        return self

    def get_a1(self) -> float:
        return self._proto.a1

    def set_a1(self, a1: float) -> 'SynchExchange':
        redvox.api1000.common.typing.check_type(a1, [int, float])
        self._proto.a1 = a1
        return self

    def get_a2(self) -> float:
        return self._proto.a2

    def set_a2(self, a2: float) -> 'SynchExchange':
        redvox.api1000.common.typing.check_type(a2, [int, float])
        self._proto.a2 = a2
        return self

    def get_a3(self) -> float:
        return self._proto.a3

    def set_a3(self, a3: float) -> 'SynchExchange':
        redvox.api1000.common.typing.check_type(a3, [int, float])
        self._proto.a3 = a3
        return self

    def get_b1(self) -> float:
        return self._proto.b1

    def set_b1(self, b1: float) -> 'SynchExchange':
        redvox.api1000.common.typing.check_type(b1, [int, float])
        self._proto.b1 = b1
        return self

    def get_b2(self) -> float:
        return self._proto.b2

    def set_b2(self, b2: float) -> 'SynchExchange':
        redvox.api1000.common.typing.check_type(b2, [int, float])
        self._proto.b2 = b2
        return self

    def get_b3(self) -> float:
        return self._proto.b3

    def set_b3(self, b3: float) -> 'SynchExchange':
        redvox.api1000.common.typing.check_type(b3, [int, float])
        self._proto.b3 = b3
        return self


def validate_synch_exchange(sync: SynchExchange) -> List[str]:
    errors_list = []
    # assume 0 (default) is an invalid value
    if sync.get_a1() == 0:
        errors_list.append("Sync exchange a1 value is 0")
    if sync.get_a2() == 0:
        errors_list.append("Sync exchange a2 value is 0")
    if sync.get_a3() == 0:
        errors_list.append("Sync exchange a3 value is 0")
    if sync.get_a1() >= sync.get_a2():
        errors_list.append("Sync exchange a1 is greater than or equal to a2")
    if sync.get_a2() > sync.get_a3():
        errors_list.append("Sync exchange a2 is greater than a3")
    if sync.get_b1() == 0:
        errors_list.append("Sync exchange b1 value is 0")
    if sync.get_b2() == 0:
        errors_list.append("Sync exchange b2 value is 0")
    if sync.get_b3() == 0:
        errors_list.append("Sync exchange b3 value is 0")
    if sync.get_b1() > sync.get_b2():
        errors_list.append("Sync exchange b1 value is greater than b2")
    if sync.get_b2() >= sync.get_b3():
        errors_list.append("Sync exchange b2 value is greater than or equal to b3")
    if sync.get_unit() != common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH:
        errors_list.append("Sync exchange unit is not microseconds since unix epoch")
    return errors_list


@wrap_enum(redvox_api_m_pb2.RedvoxPacketM.TimingInformation.TimingScoreMethod)
class TimingScoreMethod(enum.Enum):
    UNKNOWN: int = 0


class TimingInformation(
    redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.TimingInformation]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.TimingInformation):
        super().__init__(proto)
        self._synch_exchanges: redvox.api1000.common.generic.ProtoRepeatedMessage[SynchExchangeProto, SynchExchange] = \
            redvox.api1000.common.generic.ProtoRepeatedMessage(
                proto,
                proto.synch_exchanges,
                _SYNCH_EXCHANGES_FIELD_NAME,
                lambda exchange_proto: SynchExchange(exchange_proto),
                lambda exchange: exchange.get_proto()
            )

    @staticmethod
    def new() -> 'TimingInformation':
        return TimingInformation(redvox_api_m_pb2.RedvoxPacketM.TimingInformation())

    def get_unit(self) -> common.Unit:
        return common.Unit.from_proto(self._proto.unit)

    def set_default_unit(self) -> 'TimingInformation':
        return self.set_unit(common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH)

    def set_unit(self, unit: Union[common.Unit, int]) -> 'TimingInformation':
        redvox.api1000.common.typing.check_type(unit, [common.Unit])
        self._proto.unit = unit.into_proto()
        return self

    def get_packet_start_os_timestamp(self) -> float:
        return self._proto.packet_start_os_timestamp

    def set_packet_start_os_timestamp(self, packet_start_os_timestamp) -> 'TimingInformation':
        redvox.api1000.common.typing.check_type(packet_start_os_timestamp, [int, float])
        self._proto.packet_start_os_timestamp = packet_start_os_timestamp
        return self

    def get_packet_start_mach_timestamp(self) -> float:
        return self._proto.packet_start_mach_timestamp

    def set_packet_start_mach_timestamp(self, packet_start_mach_timestamp: float) -> 'TimingInformation':
        redvox.api1000.common.typing.check_type(packet_start_mach_timestamp, [int, float])
        self._proto.packet_start_mach_timestamp = packet_start_mach_timestamp
        return self

    def get_packet_end_os_timestamp(self) -> float:
        return self._proto.packet_end_os_timestamp

    def set_packet_end_os_timestamp(self, packet_end_os_timestamp: float) -> 'TimingInformation':
        redvox.api1000.common.typing.check_type(packet_end_os_timestamp, [int, float])
        self._proto.packet_end_os_timestamp = packet_end_os_timestamp
        return self

    def get_packet_end_mach_timestamp(self) -> float:
        return self._proto.packet_end_mach_timestamp

    def set_packet_end_mach_timestamp(self, packet_end_mach_timestamp: float) -> 'TimingInformation':
        redvox.api1000.common.typing.check_type(packet_end_mach_timestamp, [int, float])
        self._proto.packet_end_mach_timestamp = packet_end_mach_timestamp
        return self

    def get_server_acquisition_arrival_timestamp(self) -> float:
        return self._proto.server_acquisition_arrival_timestamp

    def set_server_acquisition_arrival_timestamp(self,
                                                 server_acquisition_arrival_timestamp: float) -> 'TimingInformation':
        redvox.api1000.common.typing.check_type(server_acquisition_arrival_timestamp, [int, float])
        self._proto.server_acquisition_arrival_timestamp = server_acquisition_arrival_timestamp
        return self

    def get_app_start_mach_timestamp(self) -> float:
        return self._proto.app_start_mach_timestamp

    def set_app_start_mach_timestamp(self, app_start_mach_timestamp: float) -> 'TimingInformation':
        redvox.api1000.common.typing.check_type(app_start_mach_timestamp, [int, float])
        self._proto.app_start_mach_timestamp = app_start_mach_timestamp
        return self

    def get_synch_exchanges(self) -> redvox.api1000.common.generic.ProtoRepeatedMessage:
        return self._synch_exchanges

    def get_best_latency(self) -> float:
        return self._proto.best_latency

    def set_best_latency(self, best_latency: float) -> 'TimingInformation':
        redvox.api1000.common.typing.check_type(best_latency, [int, float])
        self._proto.best_latency = best_latency
        return self

    def get_best_offset(self) -> float:
        return self._proto.best_offset

    def set_best_offset(self, best_offset: float) -> 'TimingInformation':
        redvox.api1000.common.typing.check_type(best_offset, [int, float])
        self._proto.best_offset = best_offset
        return self

    def get_score(self) -> float:
        return self._proto.score

    def set_score(self, score: float) -> 'TimingInformation':
        redvox.api1000.common.typing.check_type(score, [float])
        self._proto.score = score
        return self

    def get_score_method(self) -> TimingScoreMethod:
        return TimingScoreMethod(self._proto.score_method)

    def set_score_method(self, score_method: TimingScoreMethod) -> 'TimingInformation':
        redvox.api1000.common.typing.check_type(score_method, [TimingScoreMethod])
        self._proto.os = redvox_api_m_pb2.RedvoxPacketM.TimingInformation.TimingScoreMethod.Value(score_method.name)
        return self


def validate_timing_information(timing: TimingInformation) -> List[str]:
    errors_list = []
    synch_vals = timing.get_synch_exchanges().get_values()
    # if we have synchronization values, we can validate them
    # otherwise we can just return an empty list since there's no point in validating nothing
    if len(synch_vals) > 0:
        for sync_exch in synch_vals:
            errors_list.extend(validate_synch_exchange(sync_exch))
    if timing.get_unit() != common.Unit.MICROSECONDS_SINCE_UNIX_EPOCH:
        errors_list.append("Timing information unit is not microseconds since unix epoch")
    if timing.get_packet_start_os_timestamp() == 0:
        errors_list.append("Timing information os start timestamp is 0")
    if timing.get_packet_start_mach_timestamp() == 0:
        errors_list.append("Timing information mach start timestamp is 0")
    if timing.get_packet_end_os_timestamp() == 0:
        errors_list.append("Timing information os end timestamp is 0")
    if timing.get_packet_end_mach_timestamp() == 0:
        errors_list.append("Timing information mach end timestamp is 0")
    if timing.get_app_start_mach_timestamp() == 0:
        errors_list.append("Timing information app mach start timestamp is 0")
    if timing.get_packet_start_os_timestamp() > timing.get_packet_end_os_timestamp():
        errors_list.append("Timing information os end timestamp is less than start timestamp")
    if timing.get_packet_start_mach_timestamp() > timing.get_packet_end_mach_timestamp():
        errors_list.append("Timing information mach end timestamp is less than start timestamp")
        # if timing.get_server_acquisition_arrival_timestamp() == 0:
        #     errors_list.append("Timing information server acquisition arrival timestamp is 0")
    return errors_list
