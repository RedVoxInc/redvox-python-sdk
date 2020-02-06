"""
This module provides custom exception types for API 1000 related errors.
"""


class Api1000Error(Exception):
    def __init__(self, message: str):
        super().__init__(f"Api1000Error: {message}")


class SummaryStatisticsError(Api1000Error):
    def __init__(self, message: str):
        super().__init__(f"SummaryStatisticsError: {message}")


class MicrophoneChannelError(Api1000Error):
    def __init__(self, message: str):
        super().__init__(f"MicrophoneChannelError: {message}")


class SingleChannelError(Api1000Error):
    def __init__(self, message: str):
        super().__init__(f"SingleChannelError: {message}")


class XyzChannelError(Api1000Error):
    def __init__(self, message: str):
        super().__init__(f"XyzChannelError: {message}")


class LocationChannelError(Api1000Error):
    def __init__(self, message: str):
        super().__init__(f"LocationChannelError: {message}")


class Api1000TypeError(Api1000Error):
    def __init__(self, message: str):
        super().__init__(f"Api1000TypeError: {message}")


class WrappedRedvoxPacketApi1000Error(Api1000Error):
    def __init__(self, message: str):
        super().__init__(f"WrappedRedvoxPacketApi1000Error: {message}")
