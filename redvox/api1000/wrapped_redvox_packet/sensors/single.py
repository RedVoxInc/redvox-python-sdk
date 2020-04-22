import redvox.api1000.wrapped_redvox_packet.common as common
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2

from typing import List


class Single(common.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.Sensors.Single]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.Single):
        super().__init__(proto)
        self._timestamps: common.TimingPayload = common.TimingPayload(proto.timestamps)
        self._samples: common.SamplePayload = common.SamplePayload(proto.samples)

    @staticmethod
    def new() -> 'Single':
        return Single(redvox_api_m_pb2.RedvoxPacketM.Sensors.Single())

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'Single':
        common.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_timestamps(self) -> common.TimingPayload:
        return self._timestamps

    def get_samples(self) -> common.SamplePayload:
        return self._samples


def validate_single(single_sensor: Single) -> List[str]:
    errors_list = common.validate_timing_payload(single_sensor.get_timestamps())
    errors_list.extend(common.validate_sample_payload(single_sensor.get_samples()))
    return errors_list
