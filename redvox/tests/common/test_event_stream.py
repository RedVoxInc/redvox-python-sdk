import unittest

import redvox.tests as tests
import redvox.common.event_stream as es


class EventTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.TEST_DATA_DIR
        cls.event = es.Event(0, "testevent")
        cls.real = es.Event(0, "testreal")

    def test_get_values(self):
        self.assertEqual(self.event.get_string_values(), {})
        self.assertEqual(self.event.get_numeric_values(), {})
        self.assertEqual(self.event.get_boolean_values(), {})
        self.assertEqual(self.event.get_byte_values(), {})

    def test_get_columns(self):
        self.assertEqual(len(self.event.get_string_column("fail")), 0)

    def test_get_classification(self):
        self.assertEqual(len(self.event.get_classification(0)), 0)

    def test_get_string_item(self):
        self.assertEqual(self.event.get_string_item("fail"), None)

    def test_get_numeric_item(self):
        self.assertEqual(self.event.get_numeric_item("fail"), None)

    def test_get_boolean_item(self):
        self.assertEqual(self.event.get_boolean_item("fail"), None)

    def test_get_byte_item(self):
        self.assertEqual(self.event.get_byte_item("fail"), None)

    def test_get_timestamps(self):
        self.assertEqual(self.event.get_timestamp(), 0)
        self.assertEqual(self.event.get_uncorrected_timestamp(), 0)


class EventStreamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.TEST_DATA_DIR
        cls.eventstream = es.EventStream("testevent")

    def test_get_event(self):
        self.assertEqual(self.eventstream.get_event(), None)
        self.assertEqual(self.eventstream.get_event(0), None)
        self.assertEqual(self.eventstream.get_event(-1), None)
