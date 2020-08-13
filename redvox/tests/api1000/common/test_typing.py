from unittest import TestCase
from typing import Any, Dict, List, Set

from redvox.api1000.errors import ApiMError

from redvox.api1000.common.typing import check_type


class TypingTests(TestCase):
    def test_primitives_ok(self):
        check_type(1, [int])
        check_type(1.0, [float])
        check_type(True, [bool])
        check_type("foo", [str])
        check_type([1], [list])
        check_type({1}, [set])
        check_type({1: 2}, [dict])

    def test_primitive_bad(self):
        bad_types: List[Any] = [
            [1, [float, bool, str, list, set, dict]],
            [1.0, [int, bool, str, list, set, dict]],
            [True, [int, float, str, list, set, dict]],
            ["foo", [int, float, bool, list, set, dict]],
            [[1], [int, float, bool, str, set, dict]],
            [{1}, [int, float, bool, str, list, dict]],
            [{1: 2}, [int, float, bool, str, list, set]]
        ]

        for bad_type in bad_types:
            with self.assertRaises(ApiMError) as ctx:
                check_type(*bad_type)
