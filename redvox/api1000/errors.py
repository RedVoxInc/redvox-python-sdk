"""
This module provides custom exception types for API 1000 related errors.
"""


class ApiMError(Exception):
    """
    Base API Error class. All other error classes should be subclasses of this one.
    """
    def __init__(self, message: str):
        super().__init__(f"ApiMError: {message}")


class SummaryStatisticsError(ApiMError):
    """
    An error with summary statistics.
    """
    def __init__(self, message: str):
        super().__init__(f"SummaryStatisticsError: {message}")


class AudioChannelError(ApiMError):
    def __init__(self, message: str):
        super().__init__(f"AudioChannelError: {message}")


class SingleChannelError(ApiMError):
    def __init__(self, message: str):
        super().__init__(f"SingleChannelError: {message}")


class XyzChannelError(ApiMError):
    def __init__(self, message: str):
        super().__init__(f"XyzChannelError: {message}")


class LocationChannelError(ApiMError):
    def __init__(self, message: str):
        super().__init__(f"LocationChannelError: {message}")


class ApiMTypeError(ApiMError):
    def __init__(self, message: str):
        super().__init__(f"ApiMTypeError: {message}")


class WrappedRedvoxPacketMError(ApiMError):
    def __init__(self, message: str):
        super().__init__(f"WrappedRedvoxPacketMError: {message}")


class ApiMConcatenationError(ApiMError):
    def __init__(self, message: str):
        super().__init__(f"ApiMConcatenationError: {message}")


class ApiMOtherError(ApiMError):
    def __init__(self, message: str):
        super().__init__(f"ApiMOtherError: {message}")
