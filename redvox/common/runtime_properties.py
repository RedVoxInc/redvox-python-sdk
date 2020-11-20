"""
This module contains several runtime properties that can be modified at runtime to chance the behavior of certain
aspects of the SDK.
"""

from datetime import timedelta

QUERY_TIME_START_BUF: timedelta = timedelta(minutes=2.0)
QUERY_TIME_END_BUF: timedelta = timedelta(minutes=2.0)