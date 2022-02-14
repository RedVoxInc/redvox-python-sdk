import unittest

import redvox.tests as tests
import redvox.common.event_stream as es


class EventStreamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.TEST_DATA_DIR
        cls.eventstream = es.EventStream("testevent")
        cls.realstream = es.EventStream("testreal")

    def test_schema(self):
        self.assertEqual(self.eventstream.get_schema(), {"string": [], "numeric": [], "boolean": [], "byte": []})
        self.assertEqual(self.eventstream.get_string_schema(), [])
        self.assertEqual(self.eventstream.get_numeric_schema(), [])
        self.assertEqual(self.eventstream.get_boolean_schema(), [])
        self.assertEqual(self.eventstream.get_byte_schema(), [])

    def test_get_values(self):
        self.assertEqual(self.eventstream.get_string_values().to_pydict(), {})
        self.assertEqual(self.eventstream.get_numeric_values().to_pydict(), {})
        self.assertEqual(self.eventstream.get_boolean_values().to_pydict(), {})
        self.assertEqual(self.eventstream.get_byte_values().to_pydict(), {})

    def test_get_columns(self):
        self.assertEqual(len(self.eventstream.get_string_column("fail")), 0)
        self.assertTrue(self.eventstream.errors().get_num_errors() > 0)

    def test_get_timestamps(self):
        self.assertEqual(len(self.eventstream.timestamps()), 0)
        self.assertEqual(len(self.eventstream.unaltered_timestamps()), 0)
