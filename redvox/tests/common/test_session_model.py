import unittest

import redvox.tests as tests
from redvox.common.io import ReadFilter
from redvox.common.api_reader import ApiReader
import redvox.common.session_model as sm


class SessionModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_dir = tests.TEST_DATA_DIR
        cls.station_filter = ReadFilter(station_ids={"0000000001"})

    def test_station_model(self):
        files = ApiReader(self.input_dir, read_filter=self.station_filter).read_files_by_id("0000000001")

        model = sm.SessionModel.create_from_stream(files)
        self.assertEqual(model.num_packets, 3)
        self.assertEqual(model.app_version, "0.2.0")
        self.assertEqual(model.id, "0000000001")

    def test_station_model_too(self):
        files = ApiReader(self.input_dir, read_filter=self.station_filter).read_files_by_id("0000000001")

        model = sm.SessionModel.create_from_stream(files)
        self.assertEqual(model.num_sensors(), 3)
        self.assertEqual(model.list_of_sensors(), ["audio", "location", "health"])
        self.assertEqual(model.audio_sample_rate_nominal_hz(), 48000)
