from datetime import datetime, timedelta
import os
import os.path
import tempfile
from typing import Iterator, Tuple
from unittest import TestCase

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM

import redvox.common.io as io
from redvox.common.date_time_utils import (
    datetime_to_epoch_microseconds_utc as dt2us,
    datetime_to_epoch_milliseconds_utc as dt2ms
)
from redvox.api900.wrapped_redvox_packet import WrappedRedvoxPacket

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

        # Create unstructured synthetic API M data

        # Create unstructured synthetic API 900 data

        # Create structured synthetic API M data

        # Create structured synthetic API M data

    def tearDown(self) -> None:
        self.temp_dir.cleanup()


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


class IndexTests(TestCase):
    pass


class ReadFilterTests(TestCase):
    pass
