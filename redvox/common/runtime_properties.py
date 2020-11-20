"""
This module contains several runtime properties that can be modified at runtime to chance the behavior of certain
aspects of the SDK.
"""

from datetime import timedelta

from redvox.api1000.common.common import check_type

__QUERY_TIME_START_BUF: timedelta = timedelta(minutes=2.0)
__QUERY_TIME_END_BUF: timedelta = timedelta(minutes=2.0)


def get_query_time_start_buf() -> timedelta:
    return __QUERY_TIME_START_BUF


def get_query_time_end_buf() -> timedelta:
    return __QUERY_TIME_END_BUF


def set_query_time_start_buf(query_time_start_buf: timedelta) -> None:
    check_type(query_time_start_buf, [timedelta])
    __QUERY_TIME_START_BUF = query_time_start_buf
