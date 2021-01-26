"""
Top level common members and functions.
"""

import enum


class ApiVersion(enum.Enum):
    """
    API versions supported by this SDK
    """

    API900: int = 900
    API1000: int = 1_000
