"""
This module contains utilies for working with dates and times.
"""

MICROSECONDS_PER_SECOND = 1_000_000.0


def microseconds_to_seconds(microseconds: float) -> float:
    """
    Converts microseconds to seconds.
    :param microseconds: The microseconds to convert to seconds.
    :return: Seconds from microseconds.
    """
    return microseconds / MICROSECONDS_PER_SECOND
