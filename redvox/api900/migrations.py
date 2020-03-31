"""
This module provides functions and utilities for slowing migrating API 900 towards API 1000.
"""

from typing import List, Union

import numpy as np

# When set, all payload values and timestamps will be returned as floating point values.
GET_NUMERIC_TYPES_AS_FLOATS: bool = False

NumericLike = Union[
    np.ndarray,
    List[int],
    List[float],
    int,
    float
]


def maybe_convert_to_float(data: NumericLike) -> NumericLike:
    if not GET_NUMERIC_TYPES_AS_FLOATS:
        return data

    if isinstance(data, np.ndarray):
        return data.astype(np.float64)

    if isinstance(data, list):
        return list(map(float, data))

    if isinstance(data, int):
        return float(data)

    # We have no idea what it is, so just return we we got.
    return data


