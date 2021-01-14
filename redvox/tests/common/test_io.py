from datetime import datetime, timedelta
import os
import os.path
import shutil
import tempfile
from typing import Iterator, Optional, Union, List
from unittest import TestCase

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.common.date_time_utils import (
    datetime_from_epoch_milliseconds_utc as ms2dt,
    datetime_from_epoch_microseconds_utc as us2dt,
    datetime_to_epoch_milliseconds_utc as dt2ms,
    datetime_to_epoch_microseconds_utc as dt2us,
    truncate_dt_ymd,
    truncate_dt_ymdh,
)
import redvox.common.io as io


def dt_range(start: datetime,
             end: datetime,
             step: timedelta) -> Iterator[datetime]:
    dt: datetime = start
    while dt <= end:
        yield dt
        dt += step


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


class IoTests(TestCase):
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


# noinspection Mypy
class IndexEntryTests(TestCase):
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

    def test_read_900(self):
        path: str = copy_exact(self.template_900_path, self.unstructured_900_dir, "0000000900_1609459200000.rdvxz")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        packet = entry.read()
        self.assertIsNotNone(packet)
        self.assertEqual(900, packet.api())

    def test_read_1000(self):
        path: str = copy_exact(self.template_1000_path, self.unstructured_900_dir, "0000001000_1609459200000000.rdvxm")
        entry: io.IndexEntry = io.IndexEntry.from_path(path)
        packet = entry.read()
        self.assertIsNotNone(packet)
        self.assertEqual(1000.0, packet.get_api())

    def test_ordering(self) -> None:
        entries: List[io.IndexEntry] = [
            io.IndexEntry.from_path(copy_exact(self.template_1000_path,
                                               self.unstructured_900_dir,
                                               "0000001003_1.rdvxm")),
            io.IndexEntry.from_path(copy_exact(self.template_1000_path,
                                               self.unstructured_900_dir,
                                               "0000001002_0.rdvxm")),
            io.IndexEntry.from_path(copy_exact(self.template_1000_path,
                                               self.unstructured_900_dir,
                                               "0000001001_-1.rdvxm"))
        ]

        entries.sort()
        self.assertEqual("0000001001", entries[0].station_id)
        self.assertEqual("0000001002", entries[1].station_id)
        self.assertEqual("0000001003", entries[2].station_id)


class IndexTests(TestCase):
    pass


class ReadFilterTests(TestCase):
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

