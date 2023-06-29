import unittest
import contextlib

import redvox.common.session_model_utils as smu
import redvox.tests as tests
from redvox.cloud.session_model_api import WelfordAggregator, Stats
from redvox.common import api_reader
from redvox.common.io import ReadFilter


class SessionModelUtilsGetAllSensorsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with contextlib.redirect_stdout(None):
            result = api_reader.ApiReader(tests.TEST_DATA_DIR, structured_dir=False,
                                          read_filter=ReadFilter(station_ids={"0000000001"}))
            cls.packet = result.read_files_by_id("0000000001")[0]

    def test_get_all_sensors_in_packet(self):
        test = smu.get_all_sensors_in_packet(self.packet)
        self.assertEqual(len(test), 3)
        self.assertTrue("audio" in [t[0] for t in test])


class SessionModelUtilsFirstLastBufferTest(unittest.TestCase):
    def test_add_to_fst_buffer(self):
        test = [(100, .5), (200, .75), (300, "hi")]
        smu.add_to_fst_buffer(test, 3, 50, "first")
        self.assertEqual(len(test), 3)
        self.assertEqual(test[0][0], 50)
        self.assertEqual(test[0][1], "first")

    def test_add_to_fst_buffer_end(self):
        test = [(100, .5), (200, .75), (300, "hi")]
        smu.add_to_fst_buffer(test, 3, 500, "last")
        self.assertEqual(len(test), 3)
        self.assertEqual(test[2][0], 300)
        self.assertEqual(test[2][1], "hi")

    def test_insert_to_fst_buffer(self):
        test = [(100, .5), (200, .75), (400, "hi")]
        smu.add_to_fst_buffer(test, 4, 300, "invader")
        self.assertEqual(len(test), 4)
        self.assertEqual(test[2][0], 300)
        self.assertEqual(test[2][1], "invader")

    def test_add_to_lst_buffer(self):
        test = [(100, .5), (200, .75), (300, "hi")]
        smu.add_to_lst_buffer(test, 3, 500, "last")
        self.assertEqual(len(test), 3)
        self.assertEqual(test[2][0], 500)
        self.assertEqual(test[2][1], "last")

    def test_add_to_lst_buffer_start(self):
        test = [(100, .5), (200, .75), (300, "hi")]
        smu.add_to_lst_buffer(test, 3, 50, "first")
        self.assertEqual(len(test), 3)
        self.assertEqual(test[0][0], 100)
        self.assertEqual(test[0][1], .5)

    def test_insert_to_lst_buffer(self):
        test = [(100, .5), (200, .75), (400, "hi")]
        smu.add_to_lst_buffer(test, 4, 300, "invader")
        self.assertEqual(len(test), 4)
        self.assertEqual(test[2][0], 300)
        self.assertEqual(test[2][1], "invader")


class SessionModelUtilsGetTimeSyncTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with contextlib.redirect_stdout(None):
            result = api_reader.ApiReader(tests.TEST_DATA_DIR, structured_dir=False,
                                          read_filter=ReadFilter(station_ids={"1637680001"}))
            cls.packet = smu.get_local_timesync(result.read_files_by_id("1637680001")[0])

    def test_first_timesync_timestamp(self):
        self.assertEqual(self.packet[0], 1532459197088257.0)

    def test_last_timesync_timestamp(self):
        self.assertEqual(self.packet[1], 1532459248288257.0)

    def test_num_exchanges(self):
        self.assertEqual(self.packet[2], 4)

    def test_mean_latency(self):
        self.assertAlmostEqual(self.packet[3], 69664., 2)

    def test_mean_offset(self):
        self.assertAlmostEqual(self.packet[4], -22906528.0, 2)


class SessionModelUtilsWelfordTest(unittest.TestCase):
    def test_create_welford(self):
        wf = smu.add_to_welford(100.)
        self.assertEqual(wf.mean, 100.)
        self.assertEqual(wf.m2, 0.)
        self.assertEqual(wf.cnt, 1)

    def test_add_to_welford(self):
        wf = WelfordAggregator(0., 100., 1)
        wf = smu.add_to_welford(200., wf)
        wf = smu.add_to_welford(300., wf)
        self.assertEqual(wf.mean, 200.)
        self.assertEqual(wf.cnt, 3)
        self.assertEqual(wf.m2, 20000.)


class SessionModelUtilsStatsTest(unittest.TestCase):
    def test_create_stats(self):
        sts = smu.add_to_stats(100.)
        self.assertEqual(sts.min, 100.)
        self.assertEqual(sts.max, 100.)
        self.assertEqual(sts.welford.mean, 100.)

    def test_add_to_stats(self):
        sts = Stats(100., 100., WelfordAggregator(0., 100., 1))
        sts = smu.add_to_stats(200., sts)
        sts = smu.add_to_stats(300., sts)
        self.assertEqual(sts.min, 100.)
        self.assertEqual(sts.max, 300.)
        self.assertEqual(sts.welford.mean, 200.)
        self.assertEqual(sts.welford.cnt, 3)
        self.assertEqual(sts.welford.m2, 20000.)


class SessionModelUtilsLocationDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with contextlib.redirect_stdout(None):
            result = api_reader.ApiReader(tests.TEST_DATA_DIR, structured_dir=False,
                                          read_filter=ReadFilter(station_ids={"1637680001"}))
            cls.packet = result.read_files_by_id("1637680001")[0]

    def test_get_location_data(self):
        test = smu.get_location_data(self.packet)
        self.assertEqual(len(test), 2)
        self.assertEqual(test[0][0], "NONE")
        self.assertAlmostEqual(test[0][1], 19.73, 2)
        self.assertAlmostEqual(test[0][2], -156.06, 2)
        self.assertAlmostEqual(test[0][3], 23.2, 2)
        self.assertEqual(test[0][4], 1532459211367682.0)

    def test_add_location(self):
        test = smu.get_location_data(self.packet)
        loc_data = smu.add_location_data(test)
        self.assertEqual(len(loc_data.keys()), 1)
        self.assertEqual(list(loc_data.keys()), ["NONE"])
        first_data = loc_data["NONE"]
        self.assertAlmostEqual(first_data.lat.welford.mean, 19.73, 2)
        self.assertAlmostEqual(first_data.lng.welford.mean, -156.06, 2)
        self.assertAlmostEqual(first_data.alt.welford.mean, 23.2, 2)
        self.assertEqual(len(first_data.fst_lst.fst), 2)


class SessionModelUtilsDynamicDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with contextlib.redirect_stdout(None):
            result = api_reader.ApiReader(tests.TEST_DATA_DIR, structured_dir=False,
                                          read_filter=ReadFilter(station_ids={"0000000001"}))
            cls.packet = result.read_files_by_id("0000000001")[0]

    def test_get_dynamic_data(self):
        test = smu.get_dynamic_data(self.packet)
        self.assertEqual(test["battery"], 0.)
        self.assertEqual(test["temperature"], 0.)
        loc = test["location"]
        self.assertEqual(len(loc), 1)
        self.assertEqual(loc[0][0], "USER")
        self.assertAlmostEqual(loc[0][1], 21.31, 2)
        self.assertAlmostEqual(loc[0][2], -157.79, 2)
        self.assertAlmostEqual(loc[0][3], 141.0, 2)
        self.assertEqual(loc[0][4], 1597189452945991.0)
