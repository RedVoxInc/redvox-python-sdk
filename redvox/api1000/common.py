from typing import Any, Dict, List, Optional, Union

import numpy as np
from google.protobuf.json_format import MessageToDict, MessageToJson

import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2

NAN: float = float("NaN")


def none_or_empty(value: Union[List, str, np.ndarray]) -> bool:
    if value is None:
        return True

    return len(value) == 0


def is_protobuf_numerical_type(value: Any) -> bool:
    return isinstance(value, int) or isinstance(value, float)


def is_protobuf_repeated_numerical_type(values: Any) -> bool:
    if not isinstance(values, np.ndarray):
        return False

    if len(values) == 0:
        return True

    value = values.flat[0]
    return isinstance(value, np.floating) or isinstance(value, np.integer)


def get_metadata(mutable_mapping) -> Dict[str, str]:
    metadata_dict: Dict[str, str] = dict()
    for key in mutable_mapping:
        metadata_dict[key] = mutable_mapping[key]
    return metadata_dict


def set_metadata(mutable_mapping,
                 metadata: Dict[str, str]) -> Optional[Any]:
    for key, value in metadata.items():
        if not isinstance(key, str):
            return key

        if not isinstance(value, str):
            return value

    mutable_mapping.clear()
    for key, value in metadata.items():
        mutable_mapping[key] = value

    return None


def append_metadata(mutable_mapping, key: str, value: str) -> Optional[Any]:
    if not isinstance(key, str):
        return key

    if not isinstance(value, str):
        return value

    mutable_mapping[key] = value

    return None


def as_json(value):
    return MessageToJson(value, True)


def as_dict(value) -> Dict:
    return MessageToDict(value, True)


def mean_sample_rate_hz_from_sample_ts_us(sample_ts_us: np.ndarray) -> float:
    sample_ts_s: np.ndarray = sample_ts_us / 1_000_000.0
    diffs: np.ndarray = np.diff(sample_ts_s)
    sample_rates_hz: np.ndarray = 1.0 / diffs
    return sample_rates_hz.mean()



if __name__ == "__main__":
    ts = np.array([0.0, 10_000_000.0, 20_000_000.0, 30_000_000.0])
    print(mean_sample_rate_hz_from_sample_ts_us(ts))
