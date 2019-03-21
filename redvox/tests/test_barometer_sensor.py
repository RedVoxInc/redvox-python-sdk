from redvox.api900 import reader
from redvox.api900.reader import ReaderException
from redvox.tests.utils import *

import unittest

from numpy import array_equal


class TestBarometerSensor(unittest.TestCase):
    def setUp(self):
        self.example_sensor = reader.read_rdvxz_file(test_data("example.rdvxz")).barometer_channel()
        self.empty_sensor = reader.BarometerSensor()
