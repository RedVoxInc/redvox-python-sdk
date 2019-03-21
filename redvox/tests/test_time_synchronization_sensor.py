from redvox.api900 import reader
from redvox.api900.reader import ReaderException
from redvox.tests.utils import *

import unittest

from numpy import array, array_equal

class TestTimeSynchronizationSensor(unittest.TestCase):
    def setUp(self):
        self.example_sensor = reader.read_rdvxz_file(test_data("example.rdvxz")).time_synchronization_channel()
        self.empty_channel = reader.TimeSynchronizationSensor()

    def test_get_payload_values(self):
        pass

    def test_set_payload_values(self):
        pass

    def test_get_metadata(self):
        pass

    def test_set_metadata(self):
        pass

    def test_get_metadata_as_dict(self):
        pass

    def test_set_metadata_as_dcit(self):
        pass

    def test_eq(self):
        pass

    def test_diff(self):
        pass