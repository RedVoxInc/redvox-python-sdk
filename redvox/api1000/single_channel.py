import redvox.api1000.common as common
import redvox.api1000.errors as errors
import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2


class SingleChannel(common.ProtoBase):
    def __init__(self, proto: redvox_api_1000_pb2.SingleChannel):
        self._proto = proto
        self._samples: common.Samples = common.Samples(self._proto.samples, self._proto.sample_statistics)
        self._sample_ts_us: common.Samples = common.Samples(self._proto.sample_ts_us, self._proto.sample_ts_statistics)
        self._metadata: common.Metadata = common.Metadata(self._proto.metadata)

    @staticmethod
    def new() -> 'SingleChannel':
        return SingleChannel(redvox_api_1000_pb2.SingleChannel())

    def get_proto(self) -> redvox_api_1000_pb2.SingleChannel:
        return self._proto

    def get_sensor_description(self) -> str:
        return self._proto.sensor_description

    def set_sensor_description(self, sensor_description: str) -> 'SingleChannel':
        if not isinstance(sensor_description, str):
            raise errors.SingleChannelError(f"A string is required, but a "
                                            f"{type(sensor_description)}={sensor_description} was provided")

        self._proto.sensor_description = sensor_description
        return self

    def get_samples(self) -> common.Samples:
        return self._samples

    def get_sample_ts_us(self) -> common.Samples:
        return self._sample_ts_us

    def get_metadata(self) -> common.Metadata:
        return self._metadata

