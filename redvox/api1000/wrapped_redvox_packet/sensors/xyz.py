import redvox.api1000.common.common as common
import redvox.api1000.common.typing
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2

from typing import List, Optional

import redvox.api1000.common.generic


class Xyz(redvox.api1000.common.generic.ProtoBase[redvox_api_m_pb2.RedvoxPacketM.Sensors.Xyz]):
    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.Xyz):
        super().__init__(proto)
        self._timestamps: common.TimingPayload = common.TimingPayload(proto.timestamps)
        self._x_samples: common.SamplePayload = common.SamplePayload(proto.x_samples)
        self._y_samples: common.SamplePayload = common.SamplePayload(proto.y_samples)
        self._z_samples: common.SamplePayload = common.SamplePayload(proto.z_samples)

    @staticmethod
    def new() -> 'Xyz':
        return Xyz(redvox_api_m_pb2.RedvoxPacketM.Sensors.Xyz())

    def set_unit_xyz(self, unit: common.Unit) -> 'Xyz':
        redvox.api1000.common.typing.check_type(unit, [common.Unit])
        self._x_samples.set_unit(unit)
        self._y_samples.set_unit(unit)
        self._z_samples.set_unit(unit)
        return self

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'Xyz':
        redvox.api1000.common.typing.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_timestamps(self) -> common.TimingPayload:
        return self._timestamps

    def get_x_samples(self) -> common.SamplePayload:
        return self._x_samples

    def get_y_samples(self) -> common.SamplePayload:
        return self._y_samples

    def get_z_samples(self) -> common.SamplePayload:
        return self._z_samples


def validate_xyz(xyz_sensor: Xyz, payload_unit: Optional[common.Unit] = None) -> List[str]:
    errors_list = common.validate_timing_payload(xyz_sensor.get_timestamps())
    errors_list.extend(common.validate_sample_payload(xyz_sensor.get_x_samples(),
                                                      xyz_sensor.get_sensor_description(), payload_unit))
    errors_list.extend(common.validate_sample_payload(xyz_sensor.get_y_samples(),
                                                      xyz_sensor.get_sensor_description(), payload_unit))
    errors_list.extend(common.validate_sample_payload(xyz_sensor.get_z_samples(),
                                                      xyz_sensor.get_sensor_description(), payload_unit))
    return errors_list
