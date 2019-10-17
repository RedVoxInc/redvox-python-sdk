"""
This module contains custom exceptions for API 900.
"""


class ReaderException(Exception):
    """Custom reader exception"""


class WrappedRedvoxPacketException(ReaderException):
    """Exception for WrappedRedvoxPackets"""


class ConcatenationException(WrappedRedvoxPacketException):
    """Exception for concatenating WrappedRedvoxPackets"""
