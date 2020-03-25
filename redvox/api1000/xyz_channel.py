import redvox.api1000.common as common
import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class XyzChannel(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.XyzChannel):
        super().__init__(proto)
        self._sample_ts_us: common.Samples = common.Samples(self._proto.sample_ts_us, self._proto.sample_ts_statistics)
        self._x_samples: common.Samples = common.Samples(self._proto.x_samples, self._proto.x_sample_statistics)
        self._y_samples: common.Samples = common.Samples(self._proto.y_samples, self._proto.y_sample_statistics)
        self._z_samples: common.Samples = common.Samples(self._proto.z_samples, self._proto.z_sample_statistics)

    @staticmethod
    def new() -> 'XyzChannel':
        return XyzChannel(redvox_api_1000_pb2.XyzChannel())

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'XyzChannel':
        if not isinstance(sensor_description, str):
            raise errors.XyzChannelError(f"A string is required, but a "
                                         f"{type(sensor_description)}={sensor_description} was provided")

        self._proto.sensor_description = sensor_description
        return self

    def get_sample_ts_us(self) -> common.Samples:
        return self._sample_ts_us

    def get_mean_sample_rate_hz(self) -> float:
        return common.mean_sample_rate_hz_from_sample_ts_us(self.get_sample_ts_us().get_samples())

    def get_x_samples(self) -> common.Samples:
        return self._x_samples

    def get_y_samples(self) -> common.Samples:
        return self._y_samples

    def get_z_samples(self) -> common.Samples:
        return self._z_samples

