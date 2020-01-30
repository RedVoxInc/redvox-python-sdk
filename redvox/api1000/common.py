from typing import Any, Dict, List, Union

import numpy as np

import redvox.api1000.proto.redvox_api_1000_pb2 as redvox_api_1000_pb2

NAN: float = float("NaN")


def none_or_empty(value: Union[List, str, np.ndarray]) -> bool:
    if value is None:
        return True

    return len(value) == 0


def is_protobuf_numerical_type(value: Any) -> bool:
    return isinstance(value, int) or isinstance(value, float)


def is_protobuf_repeated_numerical_type(values: Any) -> bool:
    if values is None:
        return False

    if len(values) == 0:
        return True


def get_metadata(mutable_mapping) -> Dict[str, str]:
    metadata_dict: Dict[str, str] = dict()
    for key in mutable_mapping:
        metadata_dict[key] = mutable_mapping[key]
    return metadata_dict


def set_metadata(mutable_mapping,
                 metadata: Dict[str, str]):
    mutable_mapping.clear()
    for key, value in metadata.items():
        mutable_mapping[key] = value
