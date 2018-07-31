import unittest

import numpy


class ArraysTestCase(unittest.TestCase):
    def setUp(self):
        self.empty_array = numpy.array([])

    def assertArraysEqual(self, a1: numpy.ndarray, a2: numpy.ndarray):
        self.assertTrue(numpy.array_equal(a1, a2), msg="{} != {}".format(a1, a2))