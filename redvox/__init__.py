"""
Provides library level metadata and constants.
"""

NAME = "redvox"
VERSION = "3.0.0b4"


def version() -> str:
    """Returns the version number of this library."""
    return VERSION


def print_version():
    """Prints the version number of this library"""
    print(version())
