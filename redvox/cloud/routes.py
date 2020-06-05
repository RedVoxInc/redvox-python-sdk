class RoutesV1:
    HEALTH_CHECK: str = "/"
    AUTH_USER: str = "/api/v1/auth"
    VALIDATE_TOKEN: str = "/api/v1/auth/token"
    REFRESH_TOKEN: str = "/api/v1/auth/refresh"
    METADATA_REQ: str = "/api/v1/metadata"
    TIMING_METADATA_REQ: str = "/api/v1/metadata/timing"
    DATA_RANGE_REQ: str = "/api/v1/data/range"
    DATA_REPORT_REQ: str = "/api/v1/data/report"
