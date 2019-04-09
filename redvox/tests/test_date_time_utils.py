import unittest

import redvox.api900.date_time_utils as dtutils


class TestDateTimeUtils(unittest.TestCase):
    def test_date_iterator_single(self):
        date_it = dtutils.DateIterator(1554776642, 1554776643)
        self.assertEqual([("2019", "04", "09")],
                         list(date_it))

    def test_date_iterator_two(self):
        date_it = dtutils.DateIterator(1554776642, 1554863042)
        self.assertEqual([("2019", "04", "09"),
                          ("2019", "04", "10")],
                         list(date_it))

    def test_date_iterator_three(self):
        date_it = dtutils.DateIterator(1554776642, 1554949442)
        self.assertEqual([("2019", "04", "09"),
                          ("2019", "04", "10"),
                          ("2019", "04", "11")],
                         list(date_it))

    def test_around_the_corner(self):
        date_it = dtutils.DateIterator(1577759042, 1577845442)
        self.assertEqual([("2019", "12", "31"),
                          ("2020", "01", "01")],
                         list(date_it))

