"""
Provides library level metadata and constants.
"""

NAME: str = "redvox"
VERSION: str = "3.0.0rc35"


def version() -> str:
    """Returns the version number of this library."""
    return VERSION


def print_version() -> None:
    """Prints the version number of this library"""
    print(version())
