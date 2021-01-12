from datetime import datetime, timedelta
import os
import os.path
import tempfile
from typing import Iterator
from unittest import TestCase

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM

import redvox.common.io as io
from redvox.common.date_time_utils import (
    datetime_to_epoch_microseconds_utc as dt2us,
)
from redvox.api900.wrapped_redvox_packet import WrappedRedvoxPacket


def dt_range(start: datetime,
             end: datetime,
             step: timedelta) -> Iterator[datetime]:
    dt: datetime = start
    while dt <= end:
        yield dt
        dt += step


def generate_synth_900(base_dir: str,
                       start: datetime,
                       end: datetime,
                       packet_duration: timedelta,
                       station_id: str):
    for dt in dt_range(start, end, packet_duration):
        target_dir: str = os.path.join(base_dir,
                                       "api900"
                                       f"{dt.year:04}",
                                       f"{dt.month:02}",
                                       f"{dt.day:02}")
        os.makedirs(target_dir, exist_ok=True)

        packet: WrappedRedvoxPacket = WrappedRedvoxPacket()
        packet.set_redvox_id(station_id)
        packet.set_app_file_start_timestamp_machine(int(dt2us(dt)))
        packet.write_rdvxz(target_dir)


def generate_synth_1000(base_dir: str,
                        start: datetime,
                        end: datetime,
                        packet_duration: timedelta,
                        station_id: str):
    for dt in dt_range(start, end, packet_duration):
        target_dir: str = os.path.join(base_dir,
                                       "api1000",
                                       f"{dt.year:04}",
                                       f"{dt.month:02}",
                                       f"{dt.day:02}",
                                       f"{dt.hour:02}")
        os.makedirs(target_dir, exist_ok=True)

        packet: WrappedRedvoxPacketM = WrappedRedvoxPacketM.new()
        packet.get_station_information().set_id(station_id)
        packet.get_timing_information().set_packet_start_mach_timestamp(dt2us(dt))
        packet.write_compressed_to_file(target_dir)


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


class IndexEntryTests(TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir_path = self.temp_dir.name

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_from_path_900_good(self) -> None:
        generate_synth_900(self.temp_dir_path,
                           datetime(2021, 1, 1),
                           datetime(2021, 1, 1, 1),
                           timedelta(minutes=1),
                           "0000000900")
        idx = io.index_structured(self.temp_dir_path)
        print(idx)
        entry: io.IndexEntry = io.IndexEntry.from_path(os.path.join(
            self.temp_dir_path,
            "api900",
            "2021",
            "01",
            "01",
            "0000000900_1577836800000.rdvxz"
        ))

        print(entry)

    def test_from_path_900_bad(self) -> None:
        pass


class IndexTests(TestCase):
    pass


class ReadFilterTests(TestCase):
    pass
