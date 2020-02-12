import enum


class ApiVersion(enum.Enum):
    API900: int = 900
    API1000: int = 1_000


def determine_api_version(data: bytes) -> ApiVersion:
    pass
