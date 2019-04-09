import unittest

import redvox.api900.reader as reader


class TestReader(unittest.TestCase):
    def test_is_int(self):
        self.assertTrue(reader._is_int("1"))
        self.assertTrue(reader._is_int("0"))
        self.assertTrue(reader._is_int("-1"))
        self.assertFalse(reader._is_int("a"))
        self.assertFalse(reader._is_int("foo"))
        self.assertFalse(reader._is_int(""))

    def test_is_valid_redvox_filename(self):
        self.assertTrue(reader._is_valid_redvox_filename("1637681006_1546631601587.rdvxz"))
        self.assertFalse(reader._is_valid_redvox_filename("163768100_1546631601587.rdvxz"))
        self.assertFalse(reader._is_valid_redvox_filename("16376810066_1546631601587.rdvxz"))
        self.assertFalse(reader._is_valid_redvox_filename("1637681006_154663160158.rdvxz"))
        self.assertFalse(reader._is_valid_redvox_filename("1637681006_15466316015877.rdvxz"))
        self.assertFalse(reader._is_valid_redvox_filename("1637681006_1546631601587"))

    def test_is_path_in_set(self):
        self.assertTrue(reader._is_path_in_set("/1637681006_1546631601587.rdvxz",
                                               1546631601 - 1,
                                               1546631601 + 1,
                                               {"1637681006"}))
        self.assertFalse(reader._is_path_in_set("/1637681007_1546631601587.rdvxz",
                                                1546631601 - 1,
                                                1546631601 + 1,
                                                {"1637681006"}))
        self.assertTrue(reader._is_path_in_set("/0000000001_1000000000000.rdvxz",
                                               1000000000 - 1,
                                               1000000000 + 1,
                                               {"0000000001", "0000000002"}))
        self.assertTrue(reader._is_path_in_set("/0000000002_1000000000000.rdvxz",
                                               1000000000 - 1,
                                               1000000000 + 1,
                                               {"0000000001", "0000000002"}))
        self.assertFalse(reader._is_path_in_set("/0000000003_1000000000000.rdvxz",
                                                1000000000 - 1,
                                                1000000000 + 1,
                                                {"0000000001", "0000000002"}))
        self.assertTrue(reader._is_path_in_set("/0000000001_1000000000000.rdvxz",
                                               1000000000,
                                               1000000000 + 1,
                                               {"0000000001", "0000000002"}))
        self.assertTrue(reader._is_path_in_set("/0000000001_1000000000000.rdvxz",
                                               1000000000 - 1,
                                               1000000000,
                                               {"0000000001", "0000000002"}))

        self.assertTrue(reader._is_path_in_set("/0000000001_1000000000000.rdvxz",
                                               1000000000,
                                               1000000000,
                                               {"0000000001", "0000000002"}))

        self.assertFalse(reader._is_path_in_set("/0000000001_1000000000000.rdvxz",
                                                2000000000,
                                                3000000000,
                                                {"0000000001", "0000000002"}))

        self.assertFalse(reader._is_path_in_set("/0000000001_4000000000000.rdvxz",
                                                1000000000,
                                                3000000000,
                                                {"0000000001", "0000000002"}))
