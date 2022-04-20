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
    STATION_STATUS_TIMELINE: str = "/api/v1/metadata/timeline"
    DATA_RANGE_REQ: str = "/api/v1/data/range"
    DATA_RANGE_REQ_M: str = "/api/v1/data/range/m"
    DATA_REPORT_REQ: str = "/api/v1/data/report"
    STATION_STATS: str = "/api/v1/metadata/stats"


class RoutesV2:
    """
    Route definitions for version 2 of the RedVox Cloud API.
    """
    GEO_METADATA_REQ: str = "/api/v2/metadata/geo"
