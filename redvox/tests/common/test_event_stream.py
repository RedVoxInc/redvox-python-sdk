import unittest

import redvox.tests as tests
import redvox.common.event_stream as es


class EventTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.TEST_DATA_DIR
        cls.event = es.Event(0, "testevent")
        cls.real = es.Event(0, "testreal", {es.EventDataTypes.STRING: {"class_0": "myclass"},
                                            es.EventDataTypes.NUMERIC: {"score_0": 55},
                                            es.EventDataTypes.BOOLEAN: {"is_true": False},
                                            es.EventDataTypes.BYTE: {"byte_code": b"1"}})

    def test_get_values(self):
        self.assertEqual(self.event.get_string_values(), {})
        self.assertEqual(self.event.get_numeric_values(), {})
        self.assertEqual(self.event.get_boolean_values(), {})
        self.assertEqual(self.event.get_byte_values(), {})
        self.assertEqual(self.real.get_string_values(), {"class_0": "myclass"})
        self.assertEqual(self.real.get_numeric_values(), {"score_0": 55})

    def test_get_columns(self):
        self.assertEqual(len(self.event.get_string_column("fail")), 0)
        self.assertEqual(len(self.real.get_string_column("class")), 1)

    def test_get_classification(self):
        self.assertEqual(len(self.event.get_classification(0)), 0)
        self.assertEqual(len(self.real.get_classification(0)), 2)

    def test_get_string_item(self):
        self.assertEqual(self.event.get_string_item("fail"), None)
        self.assertEqual(self.real.get_string_item("class_0"), "myclass")

    def test_get_numeric_item(self):
        self.assertEqual(self.event.get_numeric_item("fail"), None)
        self.assertEqual(self.real.get_numeric_item("score_0"), 55)

    def test_get_boolean_item(self):
        self.assertEqual(self.event.get_boolean_item("fail"), None)
        self.assertEqual(self.real.get_boolean_item("is_true"), False)

    def test_get_byte_item(self):
        self.assertEqual(self.event.get_byte_item("fail"), None)
        self.assertEqual(self.real.get_byte_item("byte_code"), b"1")

    def test_get_timestamps(self):
        self.assertEqual(self.event.get_timestamp(), 0)
        self.assertEqual(self.event.get_uncorrected_timestamp(), 0)

    def test_get_item(self):
        self.assertEqual(0, len(self.event.get_item("fail")))
        columns = self.real.get_item("fail")
        self.assertEqual(4, len(columns))
        for c in columns:
            val = self.real.get_item(c)
            self.assertIsNotNone(val)


class EventStreamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.TEST_DATA_DIR
        cls.eventstream = es.EventStream("testevent")

    def test_get_event(self):
        self.assertEqual(self.eventstream.get_event(), None)
        self.assertEqual(self.eventstream.get_event(0), None)
        self.assertEqual(self.eventstream.get_event(-1), None)
