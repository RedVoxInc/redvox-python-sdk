import unittest

import redvox.tests as tests
import redvox.common.event_stream as es


class EventStreamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.TEST_DATA_DIR
        cls.eventstream = es.Event(0, "testevent")
        cls.realstream = es.Event(0, "testreal")

    def test_get_values(self):
        self.assertEqual(self.eventstream.get_string_values(), {})
        self.assertEqual(self.eventstream.get_numeric_values(), {})
        self.assertEqual(self.eventstream.get_boolean_values(), {})
        self.assertEqual(self.eventstream.get_byte_values(), {})

    def test_get_columns(self):
        self.assertEqual(len(self.eventstream.get_string_column("fail")), 0)

    def test_get_classification(self):
        self.assertEqual(len(self.eventstream.get_classification(0)), 0)

    def test_get_string_item(self):
        self.assertEqual(self.eventstream.get_string_item("fail"), None)

    def test_get_numeric_item(self):
        self.assertEqual(self.eventstream.get_numeric_item("fail"), None)

    def test_get_boolean_item(self):
        self.assertEqual(self.eventstream.get_boolean_item("fail"), None)

    def test_get_byte_item(self):
        self.assertEqual(self.eventstream.get_byte_item("fail"), None)

    def test_get_timestamps(self):
        self.assertEqual(self.eventstream.get_timestamp(), 0)
        self.assertEqual(self.eventstream.get_uncorrected_timestamp(), 0)
