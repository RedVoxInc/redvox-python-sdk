"""
This module provides functionality for working with single channel API M sensors.
"""
from typing import List, Optional

import redvox.api1000.common.common as common
import redvox.api1000.common.generic
import redvox.api1000.common.typing
import redvox.api1000.proto.redvox_api_m_pb2 as redvox_api_m_pb2


class Single(
    redvox.api1000.common.generic.ProtoBase[
        redvox_api_m_pb2.RedvoxPacketM.Sensors.Single
    ]
):
    """
    This class encapsulates single channel sensors data and metadata
    """

    def __init__(self, proto: redvox_api_m_pb2.RedvoxPacketM.Sensors.Single):
        super().__init__(proto)
        self._timestamps: common.TimingPayload = common.TimingPayload(proto.timestamps)
        self._samples: common.SamplePayload = common.SamplePayload(proto.samples)

    @staticmethod
    def new() -> "Single":
        """
        :return: A new, empty Single sensor instance
        """
        return Single(redvox_api_m_pb2.RedvoxPacketM.Sensors.Single())

    def get_sensor_description(self) -> str:
        """
        :return: The sensor description
        """
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> "Single":
        """
        Sets the sensor description.
        :param sensor_description: Description to set.
        :return: A modified instance of self
        """
        redvox.api1000.common.typing.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_timestamps(self) -> common.TimingPayload:
        """
        :return: The TimingPayload which contains timestamps associated with each sample
        """
        return self._timestamps

    def set_timestamps(self, timestamps: common.TimingPayload) -> "Single":
        """
        Sets the timestamps associated with the sensor payload.
        :param timestamps: Timestamps to set.
        :return: A modified instance of self.
        """
        common.check_type(timestamps, [common.TimingPayload])
        self.get_proto().timestamps.CopyFrom(timestamps.get_proto())
        self._timestamps = common.TimingPayload(self.get_proto().timestamps)
        return self

    def get_samples(self) -> common.SamplePayload:
        """
        :return: The sample payload
        """
        return self._samples

    def set_samples(self, samples: common.SamplePayload) -> "Single":
        """
        Sets the samples for this sensor.
        :param samples: Samples to set.
        :return: A modified instance of self.
        """
        common.check_type(samples, [common.SamplePayload])
        # noinspection Mypy
        self.get_proto().samples.CopyFrom(samples.get_proto())
        self._samples = common.SamplePayload(self.get_proto().samples)
        return self


def validate_single(
    single_sensor: Single, payload_unit: Optional[common.Unit] = None
) -> List[str]:
    """
    Validates the single channel sensor.
    :param single_sensor: Sensor to validate.
    :param payload_unit: Expected unit
    :return: A list of validated errors
    """
    errors_list = common.validate_timing_payload(single_sensor.get_timestamps())
    errors_list.extend(
        common.validate_sample_payload(
            single_sensor.get_samples(),
            single_sensor.get_sensor_description(),
            payload_unit,
        )
    )
    return errors_list
