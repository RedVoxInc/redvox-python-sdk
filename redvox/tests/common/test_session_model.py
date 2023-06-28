import unittest
import tempfile
import os.path

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
        self.assertEqual(model.cloud_session.n_pkts, 3)
        self.assertEqual(model.cloud_session.app_ver, "0.2.0")
        self.assertEqual(model.cloud_session.id, "0000000001")
        self.assertEqual(model.num_sensors(), 3)
        self.assertEqual(model.get_sensor_names(), ["audio", "location", "health"])
        self.assertEqual(model.audio_sample_rate_nominal_hz(), 48000)
        self.assertEqual(len(model.dynamic_sessions), 2)
        self.assertEqual(len(model.get_daily_dynamic_sessions()), 1)
        self.assertEqual(len(model.get_hourly_dynamic_sessions()), 1)

    def test_write_station_model(self):
        tmpdir = tempfile.TemporaryDirectory()
        files = ApiReader(self.input_dir, read_filter=self.station_filter).read_files_by_id("0000000001")

        model = sm.SessionModel.create_from_stream(files)
        model.save(out_dir=tmpdir.name)

        loaded = sm.SessionModel.load(os.path.join(tmpdir.name, "0000000001_1597189452943691_model.json"))

        self.assertEqual(loaded.cloud_session.id, model.cloud_session.id)
        self.assertEqual(loaded.cloud_session.n_pkts, model.cloud_session.n_pkts)
        self.assertEqual(loaded.num_sensors(), model.num_sensors())
        self.assertEqual(loaded.get_sensor_names(), model.get_sensor_names())
        self.assertEqual(loaded.audio_sample_rate_nominal_hz(), model.audio_sample_rate_nominal_hz())
        self.assertEqual(len(loaded.get_daily_dynamic_sessions()), len(model.get_daily_dynamic_sessions()))

        tmpdir.cleanup()
