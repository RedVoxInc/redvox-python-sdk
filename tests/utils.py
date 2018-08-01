import typing
import unittest

import numpy


class ArraysTestCase(unittest.TestCase):
    def setUp(self):
        self.empty_array = numpy.array([])

    def assertArraysEqual(self, a1: numpy.ndarray, a2: numpy.ndarray):
        self.assertTrue(numpy.array_equal(a1, a2), msg="\n{} \n!=\n {}".format(a1, a2))

    def assertSampledArray(self, array: numpy.ndarray, expected_size: int, samples: typing.List, values: typing.List):
        if len(array) != expected_size:
            self.assertEqual(len(array), expected_size)

        sampled_array = array.take(samples)
        self.assertArraysEqual(sampled_array, numpy.array(values))



    @staticmethod
    def as_array(lst: typing.List) -> numpy.ndarray:
        return numpy.array(lst)

