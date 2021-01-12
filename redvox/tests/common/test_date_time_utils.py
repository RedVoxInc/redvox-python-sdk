"""
Date time test module
"""

import unittest
from redvox.common import date_time_utils as dt
from datetime import datetime


class TestDateTime(unittest.TestCase):
    """
    Date time test class
    """

    def test_datetime_to_epoch_s(self):
        self.assertEqual(dt.datetime_to_epoch_seconds_utc(datetime(1988, 7, 15)), 584928000)
        self.assertEqual(dt.datetime_to_epoch_seconds_utc(datetime(1988, 7, 15, 12)), 584971200)
        self.assertEqual(dt.datetime_to_epoch_seconds_utc(datetime(1988, 7, 15, 12, 30)), 584973000)
        self.assertEqual(dt.datetime_to_epoch_seconds_utc(datetime(1988, 7, 15, 12, 30, 25)), 584973025)

    def test_datetime_to_epoch_ms(self):
        self.assertEqual(dt.datetime_to_epoch_milliseconds_utc(datetime(1988, 7, 15)), 584928000000)
        self.assertEqual(dt.datetime_to_epoch_milliseconds_utc(datetime(1988, 7, 15, 12)), 584971200000)
        self.assertEqual(dt.datetime_to_epoch_milliseconds_utc(datetime(1988, 7, 15, 12)), 584971200000)
        self.assertEqual(dt.datetime_to_epoch_milliseconds_utc(datetime(1988, 7, 15, 12, 30)), 584973000000)
        self.assertEqual(dt.datetime_to_epoch_milliseconds_utc(datetime(1988, 7, 15, 12, 30, 25)), 584973025000)

    def test_datetime_to_epoch_us(self):
        self.assertEqual(dt.datetime_to_epoch_microseconds_utc(datetime(1988, 7, 15)), 584928000000000)
        self.assertEqual(dt.datetime_to_epoch_microseconds_utc(datetime(1988, 7, 15, 12)), 584971200000000)
        self.assertEqual(dt.datetime_to_epoch_microseconds_utc(datetime(1988, 7, 15, 12)), 584971200000000)
        self.assertEqual(dt.datetime_to_epoch_microseconds_utc(datetime(1988, 7, 15, 12, 30)), 584973000000000)
        self.assertEqual(dt.datetime_to_epoch_microseconds_utc(datetime(1988, 7, 15, 12, 30, 25)), 584973025000000)

    def test_datetime_from_epoch_seconds_utc(self):
        self.assertEqual(dt.datetime_from_epoch_seconds_utc(1472172968), datetime(2016, 8, 26, 0, 56, 8))

    def test_datetime_from_epoch_milliseconds_utc(self):
        self.assertEqual(dt.datetime_from_epoch_milliseconds_utc(1472173092531),
                         datetime(2016, 8, 26, 0, 58, 12, 531000))

    def test_datetime_from_epoch_microseconds_utc(self):
        self.assertEqual(dt.datetime_from_epoch_microseconds_utc(1472173092531000),
                         datetime(2016, 8, 26, 0, 58, 12, 531000))

    def test_microseconds_to_milliseconds(self):
        self.assertEqual(dt.microseconds_to_milliseconds(1000), 1)

    def test_microseconds_to_seconds(self):
        self.assertEqual(dt.microseconds_to_seconds(1000000), 1)

    def test_microseconds_to_minutes(self):
        self.assertEqual(dt.microseconds_to_minutes(60000000), 1)

    def test_microseconds_to_hours(self):
        self.assertEqual(dt.microseconds_to_hours(3600000000), 1)

    def test_microseconds_to_days(self):
        self.assertEqual(dt.microseconds_to_days(86400000000), 1)

    def test_microseconds_to_weeks(self):
        self.assertEqual(dt.microseconds_to_weeks(604800000000), 1)

    def test_milliseconds_to_microseconds(self):
        self.assertEqual(dt.milliseconds_to_microseconds(1), 1000)

    def test_milliseconds_to_seconds(self):
        self.assertEqual(dt.milliseconds_to_seconds(1000), 1)

    def test_milliseconds_to_minutes(self):
        self.assertEqual(dt.milliseconds_to_minutes(60000), 1)

    def test_milliseconds_to_hours(self):
        self.assertEqual(dt.milliseconds_to_hours(3600000), 1)

    def test_milliseconds_to_days(self):
        self.assertEqual(dt.milliseconds_to_days(86400000), 1)

    def test_milliseconds_to_weeks(self):
        self.assertEqual(dt.milliseconds_to_weeks(604800000), 1)

    def test_seconds_to_microseconds(self):
        self.assertEqual(dt.seconds_to_microseconds(1), 1000000)

    def test_seconds_to_milliseconds(self):
        self.assertEqual(dt.seconds_to_milliseconds(1), 1000)

    def test_seconds_to_minutes(self):
        self.assertEqual(dt.seconds_to_minutes(60), 1)

    def test_seconds_to_hours(self):
        self.assertEqual(dt.seconds_to_hours(3600), 1)

    def test_seconds_to_days(self):
        self.assertEqual(dt.seconds_to_days(86400), 1)

    def test_seconds_to_weeks(self):
        self.assertEqual(dt.seconds_to_weeks(604800), 1)

    def test_minutes_to_microseconds(self):
        self.assertEqual(dt.minutes_to_microseconds(1), 60000000)

    def test_minutes_to_milliseconds(self):
        self.assertEqual(dt.minutes_to_milliseconds(1), 60000)

    def test_minutes_to_seconds(self):
        self.assertEqual(dt.minutes_to_seconds(1), 60)

    def test_minutes_to_hours(self):
        self.assertEqual(dt.minutes_to_hours(60), 1)

    def test_minutes_to_days(self):
        self.assertEqual(dt.minutes_to_days(1440), 1)

    def test_minutes_to_weeks(self):
        self.assertEqual(dt.minutes_to_weeks(10080), 1)

    def test_hours_to_microseconds(self):
        self.assertEqual(dt.hours_to_microseconds(1), 3600000000)

    def test_hours_to_milliseconds(self):
        self.assertEqual(dt.hours_to_milliseconds(1), 3600000)

    def test_hours_to_seconds(self):
        self.assertEqual(dt.hours_to_seconds(1), 3600)

    def test_hours_to_minutes(self):
        self.assertEqual(dt.hours_to_minutes(1), 60)

    def test_hours_to_days(self):
        self.assertEqual(dt.hours_to_days(24), 1)

    def test_hours_to_weeks(self):
        self.assertEqual(dt.hours_to_weeks(168), 1)

    def test_weeks_to_microseconds(self):
        self.assertEqual(dt.weeks_to_microseconds(1), 604800000000)

    def test_weeks_to_milliseconds(self):
        self.assertEqual(dt.weeks_to_milliseconds(1), 604800000)

    def test_weeks_to_seconds(self):
        self.assertEqual(dt.weeks_to_seconds(1), 604800)

    def test_weeks_to_minutes(self):
        self.assertEqual(dt.weeks_to_minutes(1), 10080)

    def test_weeks_to_hours(self):
        self.assertEqual(dt.weeks_to_hours(1), 168)

    def test_weeks_to_days(self):
        self.assertEqual(dt.weeks_to_days(1), 7)

    def test_date_iterator_incorrect_order(self):
        date_it = dt.DateIterator(1593820800, 1593734400)
        self.assertEqual(len(list(date_it)), 0)

    def test_date_iterator_single(self):
        date_it = dt.DateIterator(1554776642, 1554776643)
        self.assertEqual([("2019", "04", "09")],
                         list(date_it))

    def test_date_iterator_two(self):
        date_it = dt.DateIterator(1554776642, 1554863042)
        self.assertEqual([("2019", "04", "09"),
                          ("2019", "04", "10")],
                         list(date_it))

    def test_date_iterator_three(self):
        date_it = dt.DateIterator(1554776642, 1554949442)
        self.assertEqual([("2019", "04", "09"),
                          ("2019", "04", "10"),
                          ("2019", "04", "11")],
                         list(date_it))

    def test_around_the_corner(self):
        date_it = dt.DateIterator(1577759042, 1577845442)
        self.assertEqual([("2019", "12", "31"),
                          ("2020", "01", "01")],
                         list(date_it))

        date_it = dt.DateIterator(1593820680, 1593820920)
        self.assertEqual([("2020", "07", "03"),
                          ("2020", "07", "04")],
                         list(date_it))

    def test_trucate_dt_ymd(self):
        _dt = datetime(2020, 1, 2, 3, 4, 5, 6)
        _dt = dt.truncate_dt_ymd(_dt)

        self.assertEqual(2020, _dt.year)
        self.assertEqual(1, _dt.month)
        self.assertEqual(2, _dt.day)
        self.assertEqual(0, _dt.hour)
        self.assertEqual(0, _dt.minute)
        self.assertEqual(0, _dt.second)
        self.assertEqual(0, _dt.microsecond)

    def test_trucate_dt_ymdh(self):
        _dt = datetime(2020, 1, 2, 3, 4, 5, 6)
        _dt = dt.truncate_dt_ymdh(_dt)

        self.assertEqual(2020, _dt.year)
        self.assertEqual(1, _dt.month)
        self.assertEqual(2, _dt.day)
        self.assertEqual(3, _dt.hour)
        self.assertEqual(0, _dt.minute)
        self.assertEqual(0, _dt.second)
        self.assertEqual(0, _dt.microsecond)
