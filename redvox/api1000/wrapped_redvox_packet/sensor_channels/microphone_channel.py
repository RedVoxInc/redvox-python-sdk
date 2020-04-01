import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2
import redvox.api1000.common as common


class MicrophoneChannel(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.MicrophoneChannel):
        super().__init__(proto)
        self._samples: common.Samples = common.Samples(self._proto.samples, self._proto.sample_statistics)

    @staticmethod
    def new() -> 'MicrophoneChannel':
        mic_pb: redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.MicrophoneChannel \
            = redvox_api_1000_pb2.RedvoxPacket1000.SensorChannels.MicrophoneChannel()
        return MicrophoneChannel(mic_pb)

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'MicrophoneChannel':
        common.check_type(sensor_description, [str])
        self._proto.sensor_description = sensor_description
        return self

    def get_first_sample_ts_us(self) -> float:
        return self._proto.first_sample_ts_us

    def set_first_sample_ts_us(self, first_sample_ts_us: float) -> 'MicrophoneChannel':
        common.check_type(first_sample_ts_us, [float, int])
        self._proto.first_sample_ts_us = first_sample_ts_us
        return self

    def get_sample_rate_hz(self) -> float:
        return self._proto.sample_rate_hz

    def set_sample_rate_hz(self, sample_rate_hz: float) -> 'MicrophoneChannel':
        common.check_type(sample_rate_hz, [int, float])
        self._proto.sample_rate_hz = sample_rate_hz
        return self

    def get_samples(self) -> common.Samples:
        return self._samples

