"""
This module contains custom exceptions for API 900.
"""


class ReaderException(Exception):
    """Custom reader exception"""
    pass


class WrappedRedvoxPacketException(ReaderException):
    """Exception for WrappedRedvoxPackets"""
    pass


class ConcatenationException(WrappedRedvoxPacketException):
    """Excpetion for concatenating WrappedRedvoxPackets"""
    pass
