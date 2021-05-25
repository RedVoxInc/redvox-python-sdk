import unittest

import redvox.tests as tests
from redvox.common.io import ReadFilter
from redvox.common.api_reader import ApiReader
from redvox.common import station_utils as su


class StationMetadataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.TEST_DATA_DIR
        cls.station_filter = ReadFilter(station_ids={"0000000001"})

    def test_station_metadata(self):
        files = ApiReader(self.input_dir, read_filter=self.station_filter).read_files_by_id("0000000001")
        metadata = [su.StationMetadata("Redvox", p) for p in files]
        self.assertEqual(len(metadata), 3)
        self.assertEqual(metadata[2].os_version, "Fedora 32")
        self.assertEqual(metadata[1].app_version, "0.2.0")


class StationPacketMetadataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.TEST_DATA_DIR
        cls.station_filter = ReadFilter(station_ids={"0000000001"})

    def test_station_packet_metadata(self):
        files = ApiReader(self.input_dir, read_filter=self.station_filter).read_files_by_id("0000000001")
        metadata = [su.StationPacketMetadata(p) for p in files]
        self.assertEqual(metadata[0].packet_start_mach_timestamp, 1597189452945991.0)


class StationKeyTest(unittest.TestCase):
    def test_init_key(self):
        key = su.StationKey("test_id", "test_uuid", 0.0)
        other_key = su.StationKey("other_id", "other_uuid", 1.0)
        copy_key = su.StationKey("test_id", "test_uuid", 0.0)
        self.assertEqual(key, copy_key)
        self.assertNotEqual(key, other_key)
