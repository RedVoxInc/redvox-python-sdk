from datetime import datetime, timedelta
import os
import os.path
import shutil
import tempfile
from typing import Optional, Union
from unittest import TestCase

from redvox.api1000.proto.redvox_api_m_pb2 import RedvoxPacketM
from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.api900.lib.api900_pb2 import RedvoxPacket
from redvox.common.date_time_utils import (
    datetime_from_epoch_milliseconds_utc as ms2dt,
    datetime_from_epoch_microseconds_utc as us2dt,
    datetime_to_epoch_milliseconds_utc as dt2ms,
    datetime_to_epoch_microseconds_utc as dt2us,
    truncate_dt_ymd,
    truncate_dt_ymdh,
)
import redvox.common.io as io


def write_min_api_1000(base_dir: str, file_name: Optional[str] = None) -> str:
    packet: WrappedRedvoxPacketM = WrappedRedvoxPacketM.new()
    packet.set_api(1000.0)
    return packet.write_compressed_to_file(base_dir, file_name)


def write_min_api_900(base_dir: str, file_name: Optional[str] = None) -> str:
    from redvox.api900.wrapped_redvox_packet import WrappedRedvoxPacket
    packet: WrappedRedvoxPacket = WrappedRedvoxPacket()
    packet.set_api(900)
    packet.write_rdvxz(base_dir, file_name)
    return os.path.join(base_dir, packet.default_filename() if file_name is None else file_name)


def copy_api_900(template_path: str,
                 base_dir: str,
                 structured: bool,
                 station_id: str,
                 ts_dt: Union[int, datetime],
                 ext: str = ".rdvxz") -> str:
    ts_ms: int = ts_dt if isinstance(ts_dt, int) else int(dt2ms(ts_dt))

    target_dir: str
    if structured:
        dt: datetime = ms2dt(ts_ms)
        target_dir = os.path.join(base_dir,
                                  "api900",
                                  f"{dt.year:04}",
                                  f"{dt.month:02}",
                                  f"{dt.day:02}")
    else:
        target_dir = base_dir

    os.makedirs(target_dir, exist_ok=True)

    file_name: str = f"{station_id}_{ts_ms}{ext}"
    file_path: str = os.path.join(target_dir, file_name)
    shutil.copy2(template_path, file_path)

    return file_path


def copy_api_1000(template_path: str,
                  base_dir: str,
                  structured: bool,
                  station_id: str,
                  ts_dt: Union[int, datetime],
                  ext: str = ".rdvxm") -> str:
    ts_us: int = ts_dt if isinstance(ts_dt, int) else int(dt2us(ts_dt))

    target_dir: str
    if structured:
        dt: datetime = us2dt(ts_us)
        target_dir = os.path.join(base_dir,
                                  "api1000",
                                  f"{dt.year:04}",
                                  f"{dt.month:02}",
                                  f"{dt.day:02}",
                                  f"{dt.hour:02}")
    else:
        target_dir = base_dir

    os.makedirs(target_dir, exist_ok=True)

    file_name: str = f"{station_id}_{ts_us}{ext}"
    file_path: str = os.path.join(target_dir, file_name)
    shutil.copy2(template_path, file_path)

    return file_path


def copy_exact(template_path: str,
               base_dir: str,
               name: str) -> str:
    os.makedirs(base_dir, exist_ok=True)
    file_path: str = os.path.join(base_dir, name)
    shutil.copy2(template_path, file_path)
    return file_path


# noinspection DuplicatedCode,Mypy
class IoTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.temp_dir_path = cls.temp_dir.name

        cls.template_dir: str = os.path.join(cls.temp_dir_path, "templates")
        os.makedirs(cls.template_dir, exist_ok=True)

        cls.unstructured_900_dir: str = os.path.join(cls.temp_dir_path, "unstructured_900")
        os.makedirs(cls.unstructured_900_dir, exist_ok=True)

        cls.unstructured_1000_dir: str = os.path.join(cls.temp_dir_path, "unstructured_1000")
        os.makedirs(cls.unstructured_1000_dir, exist_ok=True)

        cls.unstructured_900_1000_dir: str = os.path.join(cls.temp_dir_path, "unstructured_900_1000")
        os.makedirs(cls.unstructured_900_1000_dir, exist_ok=True)

        cls.template_900_path = os.path.join(cls.template_dir, "template_900.rdvxz")
        cls.template_1000_path = os.path.join(cls.template_dir, "template_1000.rdvxm")

        write_min_api_900(cls.template_dir, "template_900.rdvxz")
        write_min_api_1000(cls.template_dir, "template_1000.rdvxm")

    # noinspection PyUnresolvedReferences
    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()


class IoTests(IoTestCase):
    def test_is_int_good(self):
        self.assertEqual(0, io._is_int("0"))
        self.assertEqual(1, io._is_int("01"))
        self.assertEqual(1, io._is_int("00001"))
        self.assertEqual(10, io._is_int("000010"))
        self.assertEqual(-10, io._is_int("-000010"))

    def test_is_int_bad(self):
        self.assertIsNone(io._is_int(""))
        self.assertIsNone(io._is_int("000a"))
        self.assertIsNone(io._is_int("foo"))
        self.assertIsNone(io._is_int("1.325"))

    def test_not_none(self):
        self.assertTrue(io._not_none(""))
        self.assertFalse(io._not_none(None))

    def test_list_subdirs_no_valid(self):
        self.assertEqual([], list(io._list_subdirs(self.template_dir, set())))

    def test_list_subdirs_all_valid(self):
        lvl1 = os.path.join(self.temp_dir_path, "foo")
        os.makedirs(lvl1, exist_ok=True)
        os.makedirs(os.path.join(lvl1, "bar"))
        os.makedirs(os.path.join(lvl1, "baz"))

        self.assertEqual({"bar", "baz"}, set(io._list_subdirs(lvl1, {"bar", "baz"})))

    def test_list_subdirs_some_valid(self):
        lvl1 = os.path.join(self.temp_dir_path, "foo")
        os.makedirs(lvl1, exist_ok=True)
        os.makedirs(os.path.join(lvl1, "bar"), exist_ok=True)
        os.makedirs(os.path.join(lvl1, "baz"), exist_ok=True)

        self.assertEqual(["baz"], list(io._list_subdirs(lvl1, {"baz"})))

    def test_index_unstructured_all(self):
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "900_1546300800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "900_1577836800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "900_1609459200000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "901_1546300800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "901_1577836800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "901_1609459200000.rdvxz")

        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1000_1546300800000000.rdvxm")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1000_1577836800000000.rdvxm")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1000_1609459200000000.foo")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1001_1546300800000000.foo")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1001_1577836800000000")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1001_1609459200000000")

        index = io.index_unstructured(self.unstructured_900_1000_dir, io.ReadFilter.empty())
        self.assertEqual(12, len(index.entries))

    def test_index_unstructured_by_api(self):
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "900_1546300800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "900_1577836800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "900_1609459200000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "901_1546300800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "901_1577836800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "901_1609459200000.rdvxz")

        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1000_1546300800000000.rdvxm")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1000_1577836800000000.rdvxm")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1000_1609459200000000.foo")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1001_1546300800000000.foo")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1001_1577836800000000")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1001_1609459200000000")

        index_900 = io.index_unstructured(self.unstructured_900_1000_dir,
                                          io.ReadFilter.empty().with_api_versions({io.ApiVersion.API_900}))
        self.assertEqual(6, len(index_900.entries))

        index_1000 = io.index_unstructured(self.unstructured_900_1000_dir,
                                           io.ReadFilter.empty().with_api_versions({io.ApiVersion.API_1000}))
        self.assertEqual(6, len(index_1000.entries))

    def test_index_unstructured_by_ext(self):
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "900_1546300800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "900_1577836800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "900_1609459200000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "901_1546300800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "901_1577836800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "901_1609459200000.rdvxz")

        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1000_1546300800000000.rdvxm")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1000_1577836800000000.rdvxm")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1000_1609459200000000.foo")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1001_1546300800000000.foo")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1001_1577836800000000")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1001_1609459200000000")

        index = io.index_unstructured(self.unstructured_900_1000_dir,
                                      io.ReadFilter.empty().with_extensions({".rdvxz"}))
        self.assertEqual(6, len(index.entries))
        index = io.index_unstructured(self.unstructured_900_1000_dir,
                                      io.ReadFilter.empty().with_extensions({".rdvxm", ".foo"}))
        self.assertEqual(4, len(index.entries))
        index = io.index_unstructured(self.unstructured_900_1000_dir,
                                      io.ReadFilter.empty().with_extensions({""}))
        self.assertEqual(2, len(index.entries))

    def test_index_unstructured_by_date(self):
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "900_1546300800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "900_1577836800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "900_1609459200000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "901_1546300800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "901_1577836800000.rdvxz")
        copy_exact(self.template_900_path, self.unstructured_900_1000_dir, "901_1609459200000.rdvxz")

        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1000_1546300800000000.rdvxm")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1000_1577836800000000.rdvxm")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1000_1609459200000000.foo")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1001_1546300800000000.foo")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1001_1577836800000000")
        copy_exact(self.template_1000_path, self.unstructured_900_1000_dir, "1001_1609459200000000")

        index = io.index_unstructured(self.unstructured_900_1000_dir,
                                      io.ReadFilter.empty().with_start_ts(1577836800000000))
        self.assertEqual(8, len(index.entries))
        index = io.index_unstructured(self.unstructured_900_1000_dir,
                                      io.ReadFilter.empty().with_start_ts(1577836800000000).with_end_ts(1577836800000000))
        self.assertEqual(4, len(index.entries))
        index = io.index_unstructured(self.unstructured_900_1000_dir,
                                      io.ReadFilter.empty().with_end_ts(1577836800000000))
        self.assertEqual(8, len(index.entries))


class IndexEntryTests(IoTestCase):
    def test_from_path_900_good(self) -> None:
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "0000000900_1609459200000.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNotNone(entry)
        self.assertEqual("0000000900", entry.station_id)
        self.assertEqual(io.ApiVersion.API_900, entry.api_version)
        self.assertEqual(datetime(2021, 1, 1), entry.date_time)
        self.assertEqual(".rdvxz", entry.extension)

    def test_from_path_900_good_short_station_id(self) -> None:
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "9_1609459200000.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertEqual(io.ApiVersion.API_900, entry.api_version)
        self.assertEqual("9", entry.station_id)

    def test_from_path_900_good_long_station_id(self) -> None:
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir,
                               "00000009000000000900_1609459200000.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertEqual(io.ApiVersion.API_900, entry.api_version)
        self.assertEqual("00000009000000000900", entry.station_id)

    def test_from_path_900_no_station_id(self) -> None:
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "_1609459200000.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNone(entry)

    def test_from_path_900_bad_station_id(self) -> None:
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "foo_1609459200000.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNone(entry)

    def test_from_path_900_unix_epoch(self) -> None:
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "00000009000000000900_0.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertEqual(io.ApiVersion.API_900, entry.api_version)
        self.assertEqual(datetime(1970, 1, 1), entry.date_time)

    def test_from_path_900_neg_epoch(self) -> None:
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir,
                               "00000009000000000900_-31536000000.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertEqual(io.ApiVersion.API_900, entry.api_version)
        self.assertEqual(datetime(1969, 1, 1), entry.date_time)

    def test_from_path_900_no_epoch(self) -> None:
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "00000009000000000900_.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNone(entry)

    def test_from_path_900_bad_epoch(self) -> None:
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "00000009000000000900_foo.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNone(entry)

    def test_from_path_900_different_ext(self) -> None:
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "0_0.foo")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertEqual(io.ApiVersion.API_900, entry.api_version)
        self.assertEqual(".foo", entry.extension)

    def test_from_path_900_no_ext(self) -> None:
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "0_0")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertEqual(io.ApiVersion.API_900, entry.api_version)
        self.assertEqual("", entry.extension)

    def test_from_path_900_no_split(self) -> None:
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "00.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNone(entry)

    def test_from_path_900_multi_split(self) -> None:
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "0_0_0.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNone(entry)

    def test_from_path_1000_good(self) -> None:
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir,
                               "00000001000_1609459200000000.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNotNone(entry)
        self.assertEqual("00000001000", entry.station_id)
        self.assertEqual(io.ApiVersion.API_1000, entry.api_version)
        self.assertEqual(datetime(2021, 1, 1), entry.date_time)
        self.assertEqual(".rdvxz", entry.extension)

    def test_from_path_1000_good_short_station_id(self) -> None:
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir, "9_1609459200000000.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertEqual(io.ApiVersion.API_1000, entry.api_version)
        self.assertEqual("9", entry.station_id)

    def test_from_path_1000_good_long_station_id(self) -> None:
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir,
                               "0000000100000000001000_1609459200000000.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertEqual(io.ApiVersion.API_1000, entry.api_version)
        self.assertEqual("0000000100000000001000", entry.station_id)

    def test_from_path_1000_no_station_id(self) -> None:
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir, "_1609459200000000.rdvxm")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNone(entry)

    def test_from_path_1000_bad_station_id(self) -> None:
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir, "foo_1609459200000000.rdvxm")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNone(entry)

    def test_from_path_1000_unix_epoch(self) -> None:
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir, "0000000100000000001000_0.rdvxm")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertEqual(io.ApiVersion.API_1000, entry.api_version)
        self.assertEqual(datetime(1970, 1, 1), entry.date_time)

    def test_from_path_1000_neg_epoch(self) -> None:
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir,
                               "0000000100000000001000_-31536000000000.rdvxm")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertEqual(io.ApiVersion.API_1000, entry.api_version)
        self.assertEqual(datetime(1969, 1, 1), entry.date_time)

    def test_from_path_1000_no_epoch(self) -> None:
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir, "0000000100000000001000_.rdvxm")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNone(entry)

    def test_from_path_1000_bad_epoch(self) -> None:
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir, "0000000100000000001000_foo.rdvxm")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNone(entry)

    def test_from_path_1000_different_ext(self) -> None:
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir, "0_0.foo")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertEqual(io.ApiVersion.API_1000, entry.api_version)
        self.assertEqual(".foo", entry.extension)

    def test_from_path_1000_no_ext(self) -> None:
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir, "0_0")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertEqual(io.ApiVersion.API_1000, entry.api_version)
        self.assertEqual("", entry.extension)

    def test_from_path_1000_no_split(self) -> None:
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir, "00.rdvxm")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNone(entry)

    def test_from_path_1000_multi_split(self) -> None:
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir, "0_0_0.rdvxm")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        self.assertIsNone(entry)

    def test_from_path_dne(self):
        entry: io.IndexEntry = io.IndexEntry.from_path("/foo/0_0.rdvxm")
        self.assertIsNone(entry)

    def test_read_900(self):
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "0000000900_1609459200000.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        packet = entry.read()
        self.assertIsNotNone(packet)
        self.assertEqual(900, packet.api())

    def test_read_raw_900(self):
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "0000000900_1609459200000.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        packet = entry.read_raw()
        self.assertIsNotNone(packet)
        self.assertEqual(900, packet.api)

    def test_read_1000(self):
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir, "0000001000_1609459200000000.rdvxm")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        packet = entry.read()
        self.assertIsNotNone(packet)
        self.assertEqual(1000.0, packet.get_api())

    def test_read_raw_1000(self):
        path: str = copy_exact(self.template_1000_path, self.unstructured_1000_dir, "0000001000_1609459200000000.rdvxm")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        packet = entry.read_raw()
        self.assertIsNotNone(packet)
        self.assertEqual(1000.0, packet.api)


class IndexTests(IoTestCase):
    def test_empty_index(self):
        index: io.Index = io.Index()
        self.assertEqual(0, len(index.entries))
        self.assertEqual(0, len(index.entries))
        summary: io.IndexSummary = index.summarize()
        self.assertEqual(0, len(summary.station_summaries))

        total_streamed: int = 0
        for _ in index.stream():
            total_streamed += 1
        self.assertEqual(0, total_streamed)
        self.assertEqual(0, len(index.read()))

    def test_sort(self):
        entries = [
            io.IndexEntry.from_path(copy_exact(self.template_900_path, self.unstructured_900_dir, "901_1.rdvxz")),
            io.IndexEntry.from_path(copy_exact(self.template_900_path, self.unstructured_900_dir, "901_0.rdvxz")),
            io.IndexEntry.from_path(copy_exact(self.template_900_path, self.unstructured_900_dir, "901_-1")),
            io.IndexEntry.from_path(copy_exact(self.template_900_path, self.unstructured_900_dir, "900_1.rdvxz")),
            io.IndexEntry.from_path(copy_exact(self.template_900_path, self.unstructured_900_dir, "900_0.rdvxz")),
            io.IndexEntry.from_path(copy_exact(self.template_900_path, self.unstructured_900_dir, "900_-1")),

            io.IndexEntry.from_path(copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1001_1.rdvxm")),
            io.IndexEntry.from_path(copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1001_0.rdvxm")),
            io.IndexEntry.from_path(copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1001_-1")),
            io.IndexEntry.from_path(copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1000_1.rdvxm")),
            io.IndexEntry.from_path(copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1000_0.rdvxm")),
            io.IndexEntry.from_path(copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1000_-1")),
        ]

        index = io.Index(entries)
        index.sort()
        self.assertEqual([
            entries[11],
            entries[10],
            entries[9],
            entries[8],
            entries[7],
            entries[6],
            entries[5],
            entries[4],
            entries[3],
            entries[2],
            entries[1],
            entries[0],
        ], index.entries)

    def test_append(self):
        index = io.Index()
        self.assertEqual(0, len(index.entries))
        index.append(iter([]))
        self.assertEqual(0, len(index.entries))
        index.append(iter([
            io.IndexEntry.from_path("0_0", False)
        ]))
        self.assertEqual(1, len(index.entries))
        index.append(iter([
            io.IndexEntry.from_path("0_0", False),
            io.IndexEntry.from_path("0_1", False),
        ]))
        self.assertEqual(3, len(index.entries))

    def test_stream_all(self):
        from redvox.api900.wrapped_redvox_packet import WrappedRedvoxPacket

        index: io.Index = io.Index([
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "900_1609459200000.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "900_1609459200001.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "901_1609459200000.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "901_1609459200001.rdvxz")),

            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1000_1609459200000000.rdvxm")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1000_1609459200001000.foo")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1001_1609459200000000.rdvxm")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1001_1609459200001000.foo")),
        ])

        i: int = 0
        for packet in index.stream(io.ReadFilter.empty()):
            self.assertTrue(isinstance(packet, WrappedRedvoxPacketM) or isinstance(packet, WrappedRedvoxPacket))
            i += 1

        self.assertEqual(8, len(index.entries))

    def test_stream_raw_all(self):
        index: io.Index = io.Index([
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "900_1609459200000.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "900_1609459200001.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "901_1609459200000.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "901_1609459200001.rdvxz")),

            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1000_1609459200000000.rdvxm")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1000_1609459200001000.foo")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1001_1609459200000000.rdvxm")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1001_1609459200001000.foo")),
        ])

        i: int = 0
        for packet in index.stream_raw(io.ReadFilter.empty()):
            self.assertTrue(isinstance(packet, RedvoxPacketM) or isinstance(packet, RedvoxPacket))
            i += 1

        self.assertEqual(8, len(index.entries))

    def test_read_all_raw(self):
        from redvox.api900.wrapped_redvox_packet import WrappedRedvoxPacket

        index: io.Index = io.Index([
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "900_1609459200000.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "900_1609459200001.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "901_1609459200000.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "901_1609459200001.rdvxz")),

            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1000_1609459200000000.rdvxm")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1000_1609459200001000.foo")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1001_1609459200000000.rdvxm")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1001_1609459200001000.foo")),
        ])

        i: int = 0
        for packet in index.read(io.ReadFilter.empty()):
            self.assertTrue(isinstance(packet, WrappedRedvoxPacketM) or isinstance(packet, WrappedRedvoxPacket))
            i += 1

        self.assertEqual(8, len(index.entries))

    def test_read_raw_all(self):
        index: io.Index = io.Index([
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "900_1609459200000.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "900_1609459200001.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "901_1609459200000.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "901_1609459200001.rdvxz")),

            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1000_1609459200000000.rdvxm")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1000_1609459200001000.foo")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1001_1609459200000000.rdvxm")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1001_1609459200001000.foo")),
        ])

        i: int = 0
        for packet in index.read_raw(io.ReadFilter.empty()):
            self.assertTrue(isinstance(packet, RedvoxPacketM) or isinstance(packet, RedvoxPacket))
            i += 1

        self.assertEqual(8, len(index.entries))

    def test_read_filtered(self):
        index: io.Index = io.Index([
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "900_1609459200000.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "900_1609459201000.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "901_1609459200000.rdvxz")),
            io.IndexEntry.from_path(
                copy_exact(self.template_900_path, self.unstructured_900_dir, "901_1609459201000.rdvxz")),

            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1000_1609459200000000.rdvxm")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1000_1609459201000000.foo")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1001_1609459200000000.rdvxm")),
            io.IndexEntry.from_path(
                copy_exact(self.template_1000_path, self.unstructured_1000_dir, "1001_1609459201000000.foo")),
        ])

        self.assertEqual(4, len(index.read(io.ReadFilter.empty().with_api_versions({io.ApiVersion.API_900}))))
        self.assertEqual(4, len(index.read(io.ReadFilter.empty().with_api_versions({io.ApiVersion.API_1000}))))
        self.assertEqual(2, len(index.read(io.ReadFilter.empty().with_station_ids({"901"}))))
        self.assertEqual(6, len(index.read(io.ReadFilter.empty().with_extensions({".foo", ".rdvxz"}))))
        self.assertEqual(4, len(index.read(io.ReadFilter.empty().with_start_dt(datetime(2021, 1, 1, 0, 0, 1)))))
        self.assertEqual(4, len(index.read(io.ReadFilter.empty().with_end_dt(datetime(2021, 1, 1, 0, 0, 0)))))


# noinspection PyTypeChecker,DuplicatedCode,Mypy
class ReadFilterTests(IoTestCase):
    def test_default(self) -> None:
        read_filter = io.ReadFilter()
        self.assertEqual(None, read_filter.start_dt)
        self.assertEqual(timedelta(minutes=2), read_filter.start_dt_buf)
        self.assertEqual(None, read_filter.end_dt)
        self.assertEqual(timedelta(minutes=2), read_filter.end_dt_buf)
        self.assertEqual(None, read_filter.station_ids)
        self.assertEqual({io.ApiVersion.API_900, io.ApiVersion.API_1000}, read_filter.api_versions)
        self.assertEqual({".rdvxm", ".rdvxz"}, read_filter.extensions)

    def test_with_start_ts(self):
        read_filter = io.ReadFilter().with_start_ts(1609459200000000)
        self.assertEqual(datetime(2021, 1, 1), read_filter.start_dt)

    def test_with_end_ts(self):
        read_filter = io.ReadFilter().with_start_ts(1609545600000000)
        self.assertEqual(datetime(2021, 1, 2), read_filter.start_dt)

    def test_apply_dt_in_range(self):
        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 2)
        target = datetime(2021, 1, 1, 12)
        read_filter = io.ReadFilter().with_start_dt(start).with_end_dt(end)
        self.assertTrue(read_filter.apply_dt(target))

    def test_apply_dt_in_buf_start(self):
        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 2)
        target = datetime(2020, 12, 31, 23, 59)
        read_filter = io.ReadFilter().with_start_dt(start).with_end_dt(end)
        self.assertTrue(read_filter.apply_dt(target))

    def test_apply_dt_in_buf_end(self):
        start = datetime(2021, 1, 1)
        end = datetime(2021, 1, 2)
        target = datetime(2021, 1, 2, 0, 1)
        read_filter = io.ReadFilter().with_start_dt(start).with_end_dt(end)
        self.assertTrue(read_filter.apply_dt(target))

    def test_apply_dt_eq_start(self):
        start = datetime(2021, 1, 1)
        buf = timedelta(seconds=0)
        target = datetime(2021, 1, 1)
        read_filter = io.ReadFilter().with_start_dt(start).with_start_dt_buf(buf)
        self.assertTrue(read_filter.apply_dt(target))

    def test_apply_dt_eq_end(self):
        end = datetime(2021, 1, 1)
        buf = timedelta(seconds=0)
        target = datetime(2021, 1, 1)
        read_filter = io.ReadFilter().with_end_dt(end).with_end_dt_buf(buf)
        self.assertTrue(read_filter.apply_dt(target))

    def test_apply_dt_before_start(self):
        start = datetime(2021, 1, 2)
        buf = timedelta(seconds=0)
        target = datetime(2021, 1, 1, 23, 59)
        read_filter = io.ReadFilter().with_start_dt(start).with_start_dt_buf(buf)
        self.assertFalse(read_filter.apply_dt(target))

    def test_apply_dt_after_end(self):
        end = datetime(2021, 1, 2)
        buf = timedelta(seconds=0)
        target = datetime(2021, 1, 2, 0, 1)
        read_filter = io.ReadFilter().with_end_dt(end).with_end_dt_buf(buf)
        self.assertFalse(read_filter.apply_dt(target))

    def test_apply_dt_with_fn_start(self):
        start = datetime(2021, 1, 1, 23, 59)
        buf = timedelta(seconds=0)
        read_filter = io.ReadFilter().with_start_dt(start).with_start_dt_buf(buf)

        self.assertFalse(read_filter.apply_dt(datetime(2021, 1, 1)))
        self.assertTrue(read_filter.apply_dt(datetime(2021, 1, 1), truncate_dt_ymd))

        self.assertFalse(read_filter.apply_dt(datetime(2021, 1, 1, 23)))
        self.assertTrue(read_filter.apply_dt(datetime(2021, 1, 1, 23), truncate_dt_ymdh))

    def test_apply_all_station_ids(self):
        read_filter = io.ReadFilter().with_extensions(None).with_api_versions(None)
        entries = [
            io.IndexEntry.from_path("1_0", strict=False),
            io.IndexEntry.from_path("2_0", strict=False),
            io.IndexEntry.from_path("3_0", strict=False)
        ]
        self.assertEqual(["1", "2", "3"], list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_apply_no_station_ids(self):
        read_filter = io.ReadFilter().with_station_ids({"4"}).with_extensions(None).with_api_versions(None)
        entries = [
            io.IndexEntry.from_path("1_0", strict=False),
            io.IndexEntry.from_path("2_0", strict=False),
            io.IndexEntry.from_path("3_0", strict=False)
        ]
        self.assertEqual([], list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_apply_one_station_ids(self):
        read_filter = io.ReadFilter().with_station_ids({"2"}).with_extensions(None).with_api_versions(None)
        entries = [
            io.IndexEntry.from_path("1_0", strict=False),
            io.IndexEntry.from_path("2_0", strict=False),
            io.IndexEntry.from_path("3_0", strict=False)
        ]
        self.assertEqual(["2"], list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_apply_some_station_ids(self):
        read_filter = io.ReadFilter().with_station_ids({"2", "3", "4"}).with_extensions(None).with_api_versions(None)
        entries = [
            io.IndexEntry.from_path("1_0", strict=False),
            io.IndexEntry.from_path("2_0", strict=False),
            io.IndexEntry.from_path("3_0", strict=False)
        ]
        self.assertEqual(["2", "3"], list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_apply_select_all_station_ids(self):
        read_filter = io.ReadFilter().with_station_ids({"1", "2", "3"}).with_extensions(None).with_api_versions(None)
        entries = [
            io.IndexEntry.from_path("1_0", strict=False),
            io.IndexEntry.from_path("2_0", strict=False),
            io.IndexEntry.from_path("3_0", strict=False)
        ]
        self.assertEqual(["1", "2", "3"], list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_extensions_default(self):
        read_filter = io.ReadFilter().with_api_versions(None)
        entries = [
            io.IndexEntry.from_path("1_0.rdvxm", strict=False),
            io.IndexEntry.from_path("2_0.rdvxz", strict=False),
            io.IndexEntry.from_path("3_0.foo", strict=False),
            io.IndexEntry.from_path("4_0.", strict=False),
            io.IndexEntry.from_path("5_0", strict=False),
        ]
        self.assertEqual(["1", "2"], list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_extensions_all(self):
        read_filter = io.ReadFilter().with_api_versions(None).with_extensions(None)
        entries = [
            io.IndexEntry.from_path("1_0.rdvxm", strict=False),
            io.IndexEntry.from_path("2_0.rdvxz", strict=False),
            io.IndexEntry.from_path("3_0.foo", strict=False),
            io.IndexEntry.from_path("4_0.", strict=False),
            io.IndexEntry.from_path("5_0", strict=False),
        ]
        self.assertEqual(["1", "2", "3", "4", "5"],
                         list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_extensions_none(self):
        read_filter = io.ReadFilter().with_api_versions(None).with_extensions(set())
        entries = [
            io.IndexEntry.from_path("1_0.rdvxm", strict=False),
            io.IndexEntry.from_path("2_0.rdvxz", strict=False),
            io.IndexEntry.from_path("3_0.foo", strict=False),
            io.IndexEntry.from_path("4_0.", strict=False),
            io.IndexEntry.from_path("5_0", strict=False),
        ]
        self.assertEqual([], list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_extensions_none_2(self):
        read_filter = io.ReadFilter().with_api_versions(None).with_extensions({".bar"})
        entries = [
            io.IndexEntry.from_path("1_0.rdvxm", strict=False),
            io.IndexEntry.from_path("2_0.rdvxz", strict=False),
            io.IndexEntry.from_path("3_0.foo", strict=False),
            io.IndexEntry.from_path("4_0.", strict=False),
            io.IndexEntry.from_path("5_0", strict=False),
        ]
        self.assertEqual([], list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_extensions_one(self):
        read_filter = io.ReadFilter().with_api_versions(None).with_extensions({".foo"})
        entries = [
            io.IndexEntry.from_path("1_0.rdvxm", strict=False),
            io.IndexEntry.from_path("2_0.rdvxz", strict=False),
            io.IndexEntry.from_path("3_0.foo", strict=False),
            io.IndexEntry.from_path("4_0.", strict=False),
            io.IndexEntry.from_path("5_0", strict=False),
        ]
        self.assertEqual(["3"], list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_extensions_some(self):
        read_filter = io.ReadFilter().with_api_versions(None).with_extensions({".foo", ".bar", ".rdvxm"})
        entries = [
            io.IndexEntry.from_path("1_0.rdvxm", strict=False),
            io.IndexEntry.from_path("2_0.rdvxz", strict=False),
            io.IndexEntry.from_path("3_0.foo", strict=False),
            io.IndexEntry.from_path("4_0.", strict=False),
            io.IndexEntry.from_path("5_0", strict=False),
        ]
        self.assertEqual(["1", "3"], list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_extensions_select_all(self):
        read_filter = io.ReadFilter().with_api_versions(None).with_extensions({".rdvxm", ".rdvxz", ".foo", "", "."})
        entries = [
            io.IndexEntry.from_path("1_0.rdvxm", strict=False),
            io.IndexEntry.from_path("2_0.rdvxz", strict=False),
            io.IndexEntry.from_path("3_0.foo", strict=False),
            io.IndexEntry.from_path("4_0.", strict=False),
            io.IndexEntry.from_path("5_0", strict=False),
        ]
        self.assertEqual(["1", "2", "3", "4", "5"],
                         list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_api_version_all(self):
        read_filter = io.ReadFilter() \
            .with_extensions(None) \
            .with_api_versions(None)
        api_900_path = copy_exact(self.template_900_path,
                                  self.unstructured_900_dir,
                                  "900_0.rdvxz")
        api_1000_path = copy_exact(self.template_1000_path,
                                   self.unstructured_1000_dir,
                                   "1000_0.rdvxz")
        entries = [
            io.IndexEntry.from_path(api_900_path),
            io.IndexEntry.from_path(api_1000_path),
            io.IndexEntry.from_path("0_0", strict=False)
        ]
        self.assertEqual(["900", "1000", "0"],
                         list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_api_version_unknown(self):
        read_filter = io.ReadFilter() \
            .with_extensions(None) \
            .with_api_versions({io.ApiVersion.UNKNOWN})
        api_900_path = copy_exact(self.template_900_path,
                                  self.unstructured_900_dir,
                                  "900_0.rdvxz")
        api_1000_path = copy_exact(self.template_1000_path,
                                   self.unstructured_1000_dir,
                                   "1000_0.rdvxz")
        entries = [
            io.IndexEntry.from_path(api_900_path),
            io.IndexEntry.from_path(api_1000_path),
            io.IndexEntry.from_path("0_0", strict=False)
        ]
        self.assertEqual(["0"],
                         list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_api_version_900(self):
        read_filter = io.ReadFilter() \
            .with_extensions(None) \
            .with_api_versions({io.ApiVersion.API_900})
        api_900_path = copy_exact(self.template_900_path,
                                  self.unstructured_900_dir,
                                  "900_0.rdvxz")
        api_1000_path = copy_exact(self.template_1000_path,
                                   self.unstructured_1000_dir,
                                   "1000_0.rdvxz")
        entries = [
            io.IndexEntry.from_path(api_900_path),
            io.IndexEntry.from_path(api_1000_path),
            io.IndexEntry.from_path("0_0", strict=False)
        ]
        self.assertEqual(["900"],
                         list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_api_version_1000(self):
        read_filter = io.ReadFilter() \
            .with_extensions(None) \
            .with_api_versions({io.ApiVersion.API_1000})
        api_900_path = copy_exact(self.template_900_path,
                                  self.unstructured_900_dir,
                                  "900_0.rdvxz")
        api_1000_path = copy_exact(self.template_1000_path,
                                   self.unstructured_1000_dir,
                                   "1000_0.rdvxz")
        entries = [
            io.IndexEntry.from_path(api_900_path),
            io.IndexEntry.from_path(api_1000_path),
            io.IndexEntry.from_path("0_0", strict=False)
        ]
        self.assertEqual(["1000"],
                         list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))

    def test_api_version_multi(self):
        read_filter = io.ReadFilter() \
            .with_extensions(None) \
            .with_api_versions(
            {
                io.ApiVersion.API_900,
                io.ApiVersion.API_1000,
                io.ApiVersion.UNKNOWN
            }
        )

        api_900_path = copy_exact(self.template_900_path,
                                  self.unstructured_900_dir,
                                  "900_0.rdvxz")
        api_1000_path = copy_exact(self.template_1000_path,
                                   self.unstructured_1000_dir,
                                   "1000_0.rdvxz")
        entries = [
            io.IndexEntry.from_path(api_900_path),
            io.IndexEntry.from_path(api_1000_path),
            io.IndexEntry.from_path("0_0", strict=False)
        ]
        self.assertEqual(["900", "1000", "0"],
                         list(map(lambda entry: entry.station_id, filter(read_filter.apply, entries))))


class IndexSummaryTests(IoTestCase):
    def test_empty(self):
        summary = io.IndexSummary.from_index(io.Index())
        self.assertEqual(0, summary.total_packets())
        self.assertEqual(0, len(summary.station_ids()))

    def test_mixed(self):
        index = io.Index([
            io.IndexEntry.from_path(copy_exact(self.template_900_path, self.unstructured_900_dir, "1_0.rdvxz")),
            io.IndexEntry.from_path(copy_exact(self.template_900_path, self.unstructured_900_dir, "2_0.rdvxz")),
            io.IndexEntry.from_path(copy_exact(self.template_1000_path, self.unstructured_1000_dir, "3_0.rdvxm")),
            io.IndexEntry.from_path(copy_exact(self.template_1000_path, self.unstructured_1000_dir, "4_0.rdvxm")),
        ])
        summary = index.summarize()
        self.assertEqual(4, summary.total_packets())
        self.assertEqual(2, summary.total_packets(io.ApiVersion.API_900))
        self.assertEqual(2, summary.total_packets(io.ApiVersion.API_1000))

        self.assertEqual({"1", "2", "3", "4"}, set(summary.station_ids()))
        self.assertEqual({"1", "2"}, set(summary.station_ids(io.ApiVersion.API_900)))
        self.assertEqual({"3", "4"}, set(summary.station_ids(io.ApiVersion.API_1000)))


class IndexStationSummaryTests(IoTestCase):
    def test_from_entry_update_900(self):
        summary_900 = io.IndexStationSummary.from_entry(
            io.IndexEntry.from_path(copy_exact(self.template_900_path, self.unstructured_900_dir, "0_0.rdvxz"))
        )

        self.assertEqual(1, summary_900.total_packets)
        self.assertEqual("0", summary_900.station_id)
        self.assertEqual(io.ApiVersion.API_900, summary_900.api_version)
        self.assertEqual(datetime(1970, 1, 1), summary_900.first_packet)
        self.assertEqual(datetime(1970, 1, 1), summary_900.last_packet)

        summary_900.update(
            io.IndexEntry.from_path(copy_exact(self.template_900_path, self.unstructured_900_dir, "0_1000.rdvxz"))
        )
        self.assertEqual(2, summary_900.total_packets)
        self.assertEqual(datetime(1970, 1, 1), summary_900.first_packet)
        self.assertEqual(datetime(1970, 1, 1, 0, 0, 1), summary_900.last_packet)

        summary_900.update(
            io.IndexEntry.from_path(copy_exact(self.template_900_path, self.unstructured_900_dir, "0_-1000.rdvxz"))
        )
        self.assertEqual(3, summary_900.total_packets)
        self.assertEqual(datetime(1969, 12, 31, 23, 59, 59), summary_900.first_packet)
        self.assertEqual(datetime(1970, 1, 1, 0, 0, 1), summary_900.last_packet)

    def test_from_entry_update_1000(self):
        summary_1000 = io.IndexStationSummary.from_entry(
            io.IndexEntry.from_path(copy_exact(self.template_1000_path, self.unstructured_1000_dir, "0_0.rdvxm"))
        )

        self.assertEqual(1, summary_1000.total_packets)
        self.assertEqual("0", summary_1000.station_id)
        self.assertEqual(io.ApiVersion.API_1000, summary_1000.api_version)
        self.assertEqual(datetime(1970, 1, 1), summary_1000.first_packet)
        self.assertEqual(datetime(1970, 1, 1), summary_1000.last_packet)

        summary_1000.update(
            io.IndexEntry.from_path(copy_exact(self.template_1000_path, self.unstructured_1000_dir, "0_1000000.rdvxm"))
        )
        self.assertEqual(2, summary_1000.total_packets)
        self.assertEqual(datetime(1970, 1, 1), summary_1000.first_packet)
        self.assertEqual(datetime(1970, 1, 1, 0, 0, 1), summary_1000.last_packet)

        summary_1000.update(
            io.IndexEntry.from_path(copy_exact(self.template_1000_path, self.unstructured_1000_dir, "0_-1000000.rdvxm"))
        )
        self.assertEqual(3, summary_1000.total_packets)
        self.assertEqual(datetime(1969, 12, 31, 23, 59, 59), summary_1000.first_packet)
        self.assertEqual(datetime(1970, 1, 1, 0, 0, 1), summary_1000.last_packet)


class FileSystemWriterTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        temp_dir_path = self.temp_dir.name
        self.mem_fsw = io.FileSystemWriter("mem", "test", temp_dir_path, io.FileSystemSaveMode.MEM)
        self.temp_fsw = io.FileSystemWriter("temp", "test", temp_dir_path, io.FileSystemSaveMode.TEMP)
        self.disk_fsw = io.FileSystemWriter("disk", "test", temp_dir_path, io.FileSystemSaveMode.DISK)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_save_mode(self):
        self.assertEqual(self.mem_fsw.save_mode(), io.FileSystemSaveMode.MEM.name)
        self.assertEqual(self.temp_fsw.save_mode(), io.FileSystemSaveMode.TEMP.name)
        self.assertEqual(self.disk_fsw.save_mode(), io.FileSystemSaveMode.DISK.name)

    def test_check_is_mem(self):
        self.assertTrue(self.mem_fsw.is_use_mem())
        self.assertFalse(self.temp_fsw.is_use_mem())
        self.assertFalse(self.disk_fsw.is_use_mem())

    def test_check_is_temp(self):
        self.assertTrue(self.temp_fsw.is_use_temp())
        self.assertFalse(self.mem_fsw.is_use_temp())
        self.assertFalse(self.disk_fsw.is_use_temp())

    def test_check_is_disk(self):
        self.assertTrue(self.disk_fsw.is_use_disk())
        self.assertFalse(self.temp_fsw.is_use_disk())
        self.assertFalse(self.mem_fsw.is_use_disk())

    def test_save_dir(self):
        self.assertEqual("", self.mem_fsw.save_dir())

    def test_full_name(self):
        self.assertEqual("mem.test", self.mem_fsw.full_name())
        self.assertEqual("temp.test", self.temp_fsw.full_name())
        self.assertEqual("disk.test", self.disk_fsw.full_name())
