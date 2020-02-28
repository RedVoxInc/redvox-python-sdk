"""
This module contains custom error definitions used within this SDK.
"""


class RedVoxError(Exception):
    def __init__(self, message: str):
        super().__init__(f"RedVoxError: {message}")
