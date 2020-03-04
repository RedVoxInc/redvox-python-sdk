"""
This module contains custom error definitions used within this SDK.
"""


class RedVoxError(Exception):
    """
    This class represents generic RedVox SDK errors.
    """
    def __init__(self, message: str):
        super().__init__(f"RedVoxError: {message}")
