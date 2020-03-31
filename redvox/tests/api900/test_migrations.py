from typing import Any, List
import unittest

import redvox.api900.migrations as migrations

import numpy as np


def arrays_equal(array_1: np.ndarray, array_2: np.ndarray) -> bool:
    return np.array_equal(array_1, array_2) and array_1.dtype == array_2.dtype


def scalars_equal(scalar_1: Any, scalar_2: Any) -> bool:
    return scalar_1 == scalar_2 and type(scalar_1) == type(scalar_2)


def lists_equal(list_1: List[Any], list_2: List[Any]) -> bool:
    if len(list_1) != len(list_2):
        return False

    for i in range(len(list_1)):
        v_1 = list_1[i]
        v_2 = list_2[i]

        if not scalars_equal(v_1, v_2):
            return False

    return True


class MigrationsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.list_of_ints = [1, 2, 3]
        self.list_of_floats = [1.0, 2.0, 3.0]
        self.array_of_ints = np.array(self.list_of_ints)
        self.array_of_floats = np.array(self.list_of_floats)
        self.scalar_int = 1
        self.scalar_float = 1.0
        self.scalar_str = "foo"

    # Since migrations are disabled by default, should always get the same value back
    def test_no_migrations(self):
        self.assertEqual(self.list_of_ints,
                         migrations.maybe_convert_to_float(self.list_of_ints))
        self.assertEqual(self.list_of_floats,
                         migrations.maybe_convert_to_float(self.list_of_floats))
        self.assertTrue(np.array_equal(self.array_of_ints,
                                       migrations.maybe_convert_to_float(self.array_of_ints)))
        self.assertTrue(np.array_equal(self.array_of_floats,
                                       migrations.maybe_convert_to_float(self.array_of_floats)))
        self.assertEqual(self.scalar_int,
                         migrations.maybe_convert_to_float(self.scalar_int))
        self.assertEqual(type(self.scalar_int),
                         type(migrations.maybe_convert_to_float(self.scalar_int)))
