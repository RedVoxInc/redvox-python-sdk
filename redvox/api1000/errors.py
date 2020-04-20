"""
This module provides custom exception types for API 1000 related errors.
"""


class ApiMError(Exception):
    def __init__(self, message: str):
        super().__init__(f"ApiMError: {message}")


class SummaryStatisticsError(ApiMError):
    def __init__(self, message: str):
        super().__init__(f"SummaryStatisticsError: {message}")


class MicrophoneChannelError(ApiMError):
    def __init__(self, message: str):
        super().__init__(f"MicrophoneChannelError: {message}")


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
