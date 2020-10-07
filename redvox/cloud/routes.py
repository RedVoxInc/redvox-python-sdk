"""
This module contains the route definitions for interacting with the RedVox Cloud API.
"""


class RoutesV1:
    """
    Route definitions for version 1 of the RedVox Cloud API.
    """
    HEALTH_CHECK: str = "/"
    AUTH_USER: str = "/api/v1/auth"
    VALIDATE_TOKEN: str = "/api/v1/auth/token"
    REFRESH_TOKEN: str = "/api/v1/auth/refresh"
    METADATA_REQ: str = "/api/v1/metadata"
    METADATA_REQ_M: str = "/api/v1/metadata/m"
    TIMING_METADATA_REQ: str = "/api/v1/metadata/timing"
    DATA_RANGE_REQ: str = "/api/v1/data/range"
    DATA_REPORT_REQ: str = "/api/v1/data/report"
