"""
This module contains constants and helper functions for converting between different time bases. All time based
functions take inputs and output in UTC.
"""

from datetime import datetime, tzinfo, timedelta
from typing import List, Tuple

# noinspection Mypy
import numpy as np

# Microsecond constants
MICROSECONDS_IN_MILLISECOND: float = 1000.0
MICROSECONDS_IN_SECOND: float = 1000000.0
MICROSECONDS_IN_MINUTE: float = 60000000.0
MICROSECONDS_IN_HOUR: float = 3600000000.0
MICROSECONDS_IN_DAY: float = 86400000000.0
MICROSECONDS_IN_WEEK: float = 604800000000.0

# Millisecond constants
MILLISECONDS_IN_SECOND: float = 1000.0
MILLISECONDS_IN_MINUTE: float = 60000.0
MILLISECONDS_IN_HOUR: float = 3600000.0
MILLISECONDS_IN_DAY: float = 86400000.0
MILLISECONDS_IN_WEEK: float = 604800000.0

# Second constants
SECONDS_IN_MINUTE: float = 60.0
SECONDS_IN_HOUR: float = 3600.0
SECONDS_IN_DAY: float = 86400.0
SECONDS_IN_WEEK: float = 604800.0

# Minute constants
MINUTES_IN_HOUR: float = 60.0
MINUTES_IN_DAY: float = 1440.0
MINUTES_IN_WEEK: float = 10080.0

# Hour constants
HOURS_IN_DAY: float = 24.0
HOURS_IN_WEEK: float = 168.0

# Day constants
DAYS_IN_WEEK: float = 7.0

# A datetime object representing the epoch.
EPOCH: datetime = datetime.utcfromtimestamp(0)


class UTC(tzinfo):
    """
    This class represents UTC time.
    """

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)


# An instance of the above class that can be used anywhere the class is needed
UTC_INSTANCE = UTC()


# Microsecond conversions
def microseconds_to_milliseconds(microseconds: float) -> float:
    """
    Converts microseconds to milliseconds.
    :param microseconds: Number of microseconds.
    :return: Number of milliseconds.
    """
    return microseconds / MICROSECONDS_IN_MILLISECOND


def microseconds_to_seconds(microseconds: float) -> float:
    """
    Converts microseconds to seconds.
    :param microseconds: Number of microseconds.
    :return: Number of seconds.
    """
    return microseconds / MICROSECONDS_IN_SECOND


def microseconds_to_minutes(microseconds: float) -> float:
    """
    Converts microseconds to minutes.
    :param microseconds: Number of microseconds.
    :return: Number of minutes.
    """
    return microseconds / MICROSECONDS_IN_MINUTE


def microseconds_to_hours(microseconds: float) -> float:
    """
    Converts microseconds to hours.
    :param microseconds: Number of microseconds.
    :return: Number of hours.
    """
    return microseconds / MICROSECONDS_IN_HOUR


def microseconds_to_days(microseconds: float) -> float:
    """
    Converts microseconds to days.
    :param microseconds: Number of microseconds.
    :return: Number of days.
    """
    return microseconds / MICROSECONDS_IN_DAY


def microseconds_to_weeks(microseconds: float) -> float:
    """
    Converts microseconds to weeks.
    :param microseconds: Number of microseconds.
    :return: Number of weeks.
    """
    return microseconds / MICROSECONDS_IN_WEEK


# Millisecond conversions
def milliseconds_to_microseconds(milliseconds: float) -> float:
    """
    Converts milliseconds to microseconds.
    :param milliseconds: Number of milliseconds.
    :return: Number of microseconds.
    """
    return milliseconds * MICROSECONDS_IN_MILLISECOND


def milliseconds_to_seconds(milliseconds: float) -> float:
    """
    Converts milliseconds to seconds.
    :param milliseconds: Number of milliseconds.
    :return: Number of seconds.
    """
    return milliseconds / MILLISECONDS_IN_SECOND


def milliseconds_to_minutes(milliseconds: float) -> float:
    """
    Converts milliseconds to minutes.
    :param milliseconds: Number of milliseconds.
    :return: Number of minutes.
    """
    return milliseconds / MILLISECONDS_IN_MINUTE


def milliseconds_to_hours(milliseconds: float) -> float:
    """
    Converts milliseconds to hours.
    :param milliseconds: Number of milliseconds.
    :return: Number of hours.
    """
    return milliseconds / MILLISECONDS_IN_HOUR


def milliseconds_to_days(milliseconds: float) -> float:
    """
    Converts milliseconds to days.
    :param milliseconds: Number of milliseconds.
    :return: Number of days.
    """
    return milliseconds / MILLISECONDS_IN_DAY


def milliseconds_to_weeks(milliseconds: float) -> float:
    """
    Converts milliseconds to weeks.
    :param milliseconds: Number of milliseconds.
    :return: Number of weeks.
    """
    return milliseconds / MILLISECONDS_IN_WEEK


# Second conversions
def seconds_to_microseconds(seconds: float) -> float:
    """
    Converts seconds to microseconds.
    :param seconds: Number of seconds.
    :return: Number of microseconds.
    """
    return seconds * MICROSECONDS_IN_SECOND


def seconds_to_milliseconds(seconds: float) -> float:
    """
    Converts seconds to milliseconds.
    :param seconds: Number of seconds.
    :return: Number of milliseconds.
    """
    return seconds * MILLISECONDS_IN_SECOND


def seconds_to_minutes(seconds: float) -> float:
    """
    Converts seconds to minutes.
    :param seconds: Number of seconds.
    :return: Number of minutes.
    """
    return seconds / SECONDS_IN_MINUTE


def seconds_to_hours(seconds: float) -> float:
    """
    Converts seconds to hours.
    :param seconds: Number of seconds.
    :return: Number of hours.
    """
    return seconds / SECONDS_IN_HOUR


def seconds_to_days(seconds: float) -> float:
    """
    Converts seconds to days.
    :param seconds: Number of seconds.
    :return: Number of days.
    """
    return seconds / SECONDS_IN_DAY


def seconds_to_weeks(seconds: float) -> float:
    """
    Converts seconds to weeks.
    :param seconds: Number of seconds.
    :return: Number of weeks.
    """
    return seconds / SECONDS_IN_WEEK


# Minute conversions
def minutes_to_microseconds(minutes: float) -> float:
    """
    Converts minutes to microseconds.
    :param minutes: Number of minutes.
    :return: Number of microseconds.
    """
    return minutes * MICROSECONDS_IN_MINUTE


def minutes_to_milliseconds(minutes: float) -> float:
    """
    Converts minutes to milliseconds.
    :param minutes: Number of minutes.
    :return: Number of milliseconds.
    """
    return minutes * MILLISECONDS_IN_MINUTE


def minutes_to_seconds(minutes: float) -> float:
    """
    Converts minutes to seconds.
    :param minutes: Number of minutes.
    :return: Number of seconds.
    """
    return minutes * SECONDS_IN_MINUTE


def minutes_to_hours(minutes: float) -> float:
    """
    Converts minutes to hours.
    :param minutes: Number of minutes.
    :return: Number of hours.
    """
    return minutes / MINUTES_IN_HOUR


def minutes_to_days(minutes: float) -> float:
    """
    Converts minutes to days.
    :param minutes: Number of minutes.
    :return: Number of days.
    """
    return minutes / MINUTES_IN_DAY


def minutes_to_weeks(minutes: float) -> float:
    """
    Converts minutes to weeks.
    :param minutes: Number of minutes.
    :return: Number of weeks.
    """
    return minutes / MINUTES_IN_WEEK


# Hour conversions
def hours_to_microseconds(hours: float) -> float:
    """
    Converts hours to microseconds.
    :param hours: Number of hours.
    :return: Number of microseconds.
    """
    return hours * MICROSECONDS_IN_HOUR


def hours_to_milliseconds(hours: float) -> float:
    """
    Converts hours to milliseconds.
    :param hours: Number of hours.
    :return: Number of milliseconds.
    """
    return hours * MILLISECONDS_IN_HOUR


def hours_to_seconds(hours: float) -> float:
    """
    Converts hours to seconds.
    :param hours: Number of hours.
    :return: Number of seconds.
    """
    return hours * SECONDS_IN_HOUR


def hours_to_minutes(hours: float) -> float:
    """
    Converts hours to minutes.
    :param hours: Number of hours.
    :return: Number of minutes.
    """
    return hours * MINUTES_IN_HOUR


def hours_to_days(hours: float) -> float:
    """
    Converts hours to days.
    :param hours: Number of hours.
    :return: Number of days.
    """
    return hours / HOURS_IN_DAY


def hours_to_weeks(hours: float) -> float:
    """
    Converts hours to weeks.
    :param hours: Number of hours.
    :return: Number of weeks.
    """
    return hours / HOURS_IN_WEEK


# Week conversions
def weeks_to_microseconds(weeks: float) -> float:
    """
    Converts weeks to microseconds.
    :param weeks: Number of weeks.
    :return: Number of microseconds.
    """
    return weeks * MICROSECONDS_IN_WEEK


def weeks_to_milliseconds(weeks: float) -> float:
    """
    Converts weeks to milliseconds.
    :param weeks: Number of weeks.
    :return: Number of milliseconds.
    """
    return weeks * MILLISECONDS_IN_WEEK


def weeks_to_seconds(weeks: float) -> float:
    """
    Converts weeks to seconds.
    :param weeks: Number of weeks.
    :return: Number of seconds.
    """
    return weeks * SECONDS_IN_WEEK


def weeks_to_minutes(weeks: float) -> float:
    """
    Converts weeks to minutes.
    :param weeks: Number of weeks.
    :return: Number of minutes.
    """
    return weeks * MINUTES_IN_WEEK


def weeks_to_hours(weeks: float) -> float:
    """
    Converts weeks to hours.
    :param weeks: Number of weeks.
    :return: Number of hours.
    """
    return weeks * HOURS_IN_WEEK


def weeks_to_days(weeks: float) -> float:
    """
    Converts weeks to days.
    :param weeks: Number of weeks.
    :return: Number of days.
    """
    return weeks * DAYS_IN_WEEK


def datetime_from(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    """
    Returns a datetime object in UTC based off the given parameters.
    :param year: The year.
    :param month: The month.
    :param day: The day.
    :param hour: The hour (optional, default=0).
    :param minute: The minute (optional, default=0).
    :param second: The second (optional, default=0).
    :return: An instance of a datetime.
    """
    return datetime(year, month, day, hour, minute, second)


def datetime_to_epoch_seconds_utc(date_time: datetime) -> float:
    """
    Given a datetime, return the number of seconds since the epoch UTC.
    :param date_time: An instance of a datetime.
    :return: A UTC second timestamp.
    """
    return (date_time - EPOCH).total_seconds()


def datetime_to_epoch_milliseconds_utc(date_time: datetime) -> float:
    """
    Given a datetime, return the number of milliseconds since the epoch UTC.
    :param date_time: An instance of a datetime.
    :return: A UTC millisecond timestamp.
    """
    epoch_seconds: float = datetime_to_epoch_seconds_utc(date_time)
    return seconds_to_milliseconds(epoch_seconds)


def datetime_to_epoch_microseconds_utc(date_time: datetime) -> float:
    """
    Given a datetime, return the number of microseconds since the epoch UTC.
    :param date_time: The datetime object to convert.
    :return: A UTC microsecond timestamp.
    """
    epoch_seconds: float = datetime_to_epoch_seconds_utc(date_time)
    return seconds_to_microseconds(epoch_seconds)


def datetime_from_epoch_seconds_utc(epoch_seconds_utc: float) -> datetime:
    """
    Given number of seconds since the epoch UTC, return a Python datetime object.
    :param epoch_seconds_utc: A UTC second timestamp.
    :return: A datetime object.
    """
    return datetime.utcfromtimestamp(epoch_seconds_utc)


def datetime_from_epoch_milliseconds_utc(epoch_milliseconds_utc: float) -> datetime:
    """
    Given number of milliseconds since the epoch UTC, return a Python datetime object.
    :param epoch_milliseconds_utc: UTC millisecond timestamp.
    :return: Datetime object.
    """
    seconds: float = milliseconds_to_seconds(epoch_milliseconds_utc)
    return datetime.utcfromtimestamp(seconds)


def datetime_from_epoch_microseconds_utc(epoch_microseconds_utc: float) -> datetime:
    """
    Given number of microseconds since the epoch UTC, return a Python datetime object.
    :param epoch_microseconds_utc: UTC microsecond timestamp.
    :return: A datetime object.
    """
    seconds: float = microseconds_to_seconds(epoch_microseconds_utc)
    return datetime.utcfromtimestamp(seconds)


def datetimes_from_epoch_seconds_utc(epochs_seconds_utc: List[int]) -> List[datetime]:
    """
    Concerts a list of timestamps as seconds since the epoch UTC to a list of datetime objects.
    :param epochs_seconds_utc: List of timestamps to convert.
    :return: A list of datetimes.
    """
    return list(map(datetime_from_epoch_seconds_utc, epochs_seconds_utc))


def generate_timestamps_s_utc(start_timestamp_s_utc: float, sample_rate_hz: float, num_samples: int) -> np.ndarray:
    """
    Given a starting timestamp, a sample rate, and a number of samples, compute timestamps for all samples.
    :param start_timestamp_s_utc: The start timestamp.
    :param sample_rate_hz: The sample rate.
    :param num_samples: The number of samples.
    :return: Timestamps for each sample.
    """
    sample_interval_s: float = 1.0 / sample_rate_hz
    return (np.arange(num_samples) * sample_interval_s) + start_timestamp_s_utc


def now() -> datetime:
    """
    Returns the current datetime in UTC.
    :return: The current datetime in UTC.
    """
    return datetime.utcnow()


class DateIterator:
    """
    This class provides an iterator over dates. That is, it takes a start date and an end date and returns a tuple
    of year, month, day for each date between the start and end.
    """

    def __init__(self,
                 start_timestamp_utc_s: int,
                 end_timestamp_utc_s: int):

        start_dt_full: datetime = datetime.utcfromtimestamp(start_timestamp_utc_s)
        end_dt_full: datetime = datetime.utcfromtimestamp(end_timestamp_utc_s)

        self.start_dt: datetime = datetime_from(start_dt_full.year, start_dt_full.month, start_dt_full.day)
        self.end_dt: datetime = datetime_from(end_dt_full.year, end_dt_full.month, end_dt_full.day)

        self._one_day: timedelta = timedelta(days=1)

    def __iter__(self) -> 'DateIterator':
        return self

    def __next__(self) -> Tuple[str, str, str]:
        """
        Returns the next date in the iterator.
        :return: The next date in the iterator.
        """
        if self.start_dt > self.end_dt:
            raise StopIteration()

        year = str(self.start_dt.year)
        month = f"{self.start_dt.month:02}"
        day = f"{self.start_dt.day:02}"

        self.start_dt += self._one_day

        return year, month, day


class DateIteratorAPIM:
    """
    This class provides an iterator over dates. That is, it takes a start date and an end date and returns a tuple
    of year, month, day and hour for each date between the start and end.
    """

    def __init__(self,
                 start_timestamp_utc_s: int,
                 end_timestamp_utc_s: int):

        start_dt_full: datetime = datetime.utcfromtimestamp(start_timestamp_utc_s)
        end_dt_full: datetime = datetime.utcfromtimestamp(end_timestamp_utc_s)

        self.start_dt: datetime = datetime_from(start_dt_full.year, start_dt_full.month, start_dt_full.day,
                                                start_dt_full.hour)
        self.end_dt: datetime = datetime_from(end_dt_full.year, end_dt_full.month, end_dt_full.day, end_dt_full.hour)

        self._one_day: timedelta = timedelta(days=1)
        self._one_hour: timedelta = timedelta(hours=1)

    def __iter__(self) -> 'DateIteratorAPIM':
        return self

    def __next__(self) -> Tuple[str, str, str, str]:
        """
        Returns the next date in the iterator.
        :return: The next date in the iterator.
        """
        if self.start_dt > self.end_dt:
            raise StopIteration()

        year = str(self.start_dt.year)
        month = f"{self.start_dt.month:02}"
        day = f"{self.start_dt.day:02}"
        hour = f"{self.start_dt.hour:02}"

        self.start_dt += self._one_hour

        return year, month, day, hour
