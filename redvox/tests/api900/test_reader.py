import os
import unittest

import redvox.api900.reader as reader
import redvox.tests as test_utils


class TestReader(unittest.TestCase):
    def setUp(self):
        self.example_packet = reader.read_rdvxz_file(test_utils.test_data("example.rdvxz"))
        self.cloned_packet = self.example_packet.clone()

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
        self.assertTrue(reader._is_path_in_set(f"{os.sep}1637681006_1546631601587.rdvxz",
                                               1546631601 - 1,
                                               1546631601 + 1,
                                               {"1637681006"}))
        self.assertFalse(reader._is_path_in_set(f"{os.sep}1637681007_1546631601587.rdvxz",
                                                1546631601 - 1,
                                                1546631601 + 1,
                                                {"1637681006"}))
        self.assertTrue(reader._is_path_in_set(f"{os.sep}0000000001_1000000000000.rdvxz",
                                               1000000000 - 1,
                                               1000000000 + 1,
                                               {"0000000001", "0000000002"}))
        self.assertTrue(reader._is_path_in_set(f"{os.sep}0000000002_1000000000000.rdvxz",
                                               1000000000 - 1,
                                               1000000000 + 1,
                                               {"0000000001", "0000000002"}))
        self.assertFalse(reader._is_path_in_set(f"{os.sep}0000000003_1000000000000.rdvxz",
                                                1000000000 - 1,
                                                1000000000 + 1,
                                                {"0000000001", "0000000002"}))
        self.assertTrue(reader._is_path_in_set(f"{os.sep}0000000001_1000000000000.rdvxz",
                                               1000000000,
                                               1000000000 + 1,
                                               {"0000000001", "0000000002"}))
        self.assertTrue(reader._is_path_in_set(f"{os.sep}0000000001_1000000000000.rdvxz",
                                               1000000000 - 1,
                                               1000000000,
                                               {"0000000001", "0000000002"}))

        self.assertTrue(reader._is_path_in_set(f"{os.sep}0000000001_1000000000000.rdvxz",
                                               1000000000,
                                               1000000000,
                                               {"0000000001", "0000000002"}))

        self.assertFalse(reader._is_path_in_set(f"{os.sep}0000000001_1000000000000.rdvxz",
                                                2000000000,
                                                3000000000,
                                                {"0000000001", "0000000002"}))

        self.assertFalse(reader._is_path_in_set(f"{os.sep}0000000001_4000000000000.rdvxz",
                                                1000000000,
                                                3000000000,
                                                {"0000000001", "0000000002"}))

    def test_id_uuid(self):
        self.assertEqual("0000000001:123456789", reader._id_uuid(self.example_packet))
        self.cloned_packet.set_redvox_id("foo").set_uuid("bar")
        self.assertEqual("foo:bar", reader._id_uuid(self.cloned_packet))

    def test_group_by(self):
        class Foo:
            def __init__(self, bar: str):
                self.bar = bar

            def baz(self) -> str:
                return self.bar

        f = Foo("fuzz")
        b = Foo("nuz")
        foos = [f, f, b, f, b, b, b, f, f, b, b, b]
        grouped = reader._group_by(Foo.baz, foos)
        self.assertEqual(5, len(grouped["fuzz"]))
        self.assertEqual(7, len(grouped["nuz"]))

        self.cloned_packet.set_redvox_id("foo").set_uuid("bar")
        packets = [self.example_packet, self.example_packet, self.cloned_packet, self.cloned_packet, self.example_packet]
        grouped = reader._group_by(reader._id_uuid, packets)
        self.assertEqual(3, len(grouped["0000000001:123456789"]))
        self.assertEqual(2, len(grouped["foo:bar"]))

