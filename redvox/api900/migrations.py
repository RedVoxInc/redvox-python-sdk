"""
This module provides functions and utilities for slowing migrating API 900 towards API 1000.
"""

from typing import List, Optional, Union
import os

import numpy as np

# When set, all payload values and timestamps will be returned as floating point values.
GET_NUMERIC_TYPES_AS_FLOATS: bool = False


def __get_numeric_types_as_floats() -> bool:
    from_env: str = os.getenv("GET_NUMERIC_TYPES_AS_FLOATS", "")
    return GET_NUMERIC_TYPES_AS_FLOATS or from_env.lower() in ["true", "1"]


NumericLike = Union[
    np.ndarray,
    List[int],
    List[float],
    int,
    float
]


def maybe_get_float(data: NumericLike) -> NumericLike:
    if not __get_numeric_types_as_floats():
        return data

    if isinstance(data, np.ndarray):
        return data.astype(np.float64)

    if isinstance(data, list):
        return list(map(float, data))

    if isinstance(data, int):
        return float(data)

    # We have no idea what it is, so just return we we got.
    return data


def maybe_set_int(data: NumericLike) -> NumericLike:
    if not __get_numeric_types_as_floats():
        return data

    if isinstance(data, np.ndarray):
        return data.astype(np.int64)

    if isinstance(data, list):
        return list(map(int, data))

    if isinstance(data, float):
        return int(data)

    # We have no idea what it is, so just return we we got.
    return data
