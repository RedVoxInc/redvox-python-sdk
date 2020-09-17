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
    """
    An audio channel error.
    """
    def __init__(self, message: str):
        super().__init__(f"AudioChannelError: {message}")


class SingleChannelError(ApiMError):
    """
    A single channel error.
    """
    def __init__(self, message: str):
        super().__init__(f"SingleChannelError: {message}")


class XyzChannelError(ApiMError):
    """
    An xyz channel error.
    """
    def __init__(self, message: str):
        super().__init__(f"XyzChannelError: {message}")


class LocationChannelError(ApiMError):
    """
    A location channel error
    """
    def __init__(self, message: str):
        super().__init__(f"LocationChannelError: {message}")


class ApiMTypeError(ApiMError):
    """
    A type error.
    """
    def __init__(self, message: str):
        super().__init__(f"ApiMTypeError: {message}")


class WrappedRedvoxPacketMError(ApiMError):
    """
    A wrapped packet error.
    """
    def __init__(self, message: str):
        super().__init__(f"WrappedRedvoxPacketMError: {message}")


class ApiMConcatenationError(ApiMError):
    """
    A concatenation error.
    """
    def __init__(self, message: str):
        super().__init__(f"ApiMConcatenationError: {message}")


class ApiMImageChannelError(ApiMError):
    def __init__(self, message: str):
        super().__init__(f"ApiMImageChannelError: {message}")


class ApiMOtherError(ApiMError):
    """
    A generic error.
    """
    def __init__(self, message: str):
        super().__init__(f"ApiMOtherError: {message}")
