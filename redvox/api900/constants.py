"""
This modules contains constants used throughout the SDK.
"""

import enum


class PayloadType(enum.Enum):
    """
    This class provides type safe constants for API 900 payload types.
    """
    BYTE_PAYLOAD: str = "byte_payload"
    UINT32_PAYLOAD: str = "uint32_payload"
    UINT64_PAYLOAD: str = "uint64_payload"
    INT32_PAYLOAD: str = "int32_payload"
    INT64_PAYLOAD: str = "int64_payload"
    FLOAT32_PAYLOAD: str = "float32_payload"
    FLOAT64_PAYLOAD: str = "float64_payload"
