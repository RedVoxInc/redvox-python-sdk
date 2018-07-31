from redvox.api900 import reader
import tests.mock_packets

import unittest

from redvox.api900.lib import api900_pb2


class TestWrappedRedvoxPacket(unittest.TestCase):
    def setUp(self):
        self.base_packet: api900_pb2.RedvoxPacket = tests.mock_packets.base_packet()
        self.wrapped_synthetic_packet = reader.wrap(self.base_packet)
        self.wrapped_example_packet = reader.wrap(reader.read_file("0000001314_1532656864354.rdvxz"))

    def test_api(self):
        self.assertEqual(self.wrapped_synthetic_packet.api(), 900)
        self.assertEqual(self.wrapped_example_packet.api(), 900)

    def test_redvox_id(self):
        self.assertEqual(self.wrapped_synthetic_packet.redvox_id(), "1")
        self.assertEqual(self.wrapped_example_packet.redvox_id(), "0000001314")

    def test_uuid(self):
        self.assertEqual(self.wrapped_synthetic_packet.uuid(), "2")
        self.assertEqual(self.wrapped_example_packet.uuid(), "317985785")

    def test_authenticated_email(self):
        self.assertEqual(self.wrapped_synthetic_packet.authenticated_email(), "foo@bar.baz")
        self.assertEqual(self.wrapped_example_packet.authenticated_email(), "anthony.christe@gmail.com")

    def test_authentication_token(self):
        self.assertEqual(self.wrapped_synthetic_packet.authentication_token(), "test_authentication_token")
        self.assertEqual(self.wrapped_example_packet.authentication_token(), "redacted-1005665114")

    def test_firebase_token(self):
        self.assertEqual(self.wrapped_synthetic_packet.firebase_token(), "test_firebase_token")
        self.assertEqual(self.wrapped_example_packet.firebase_token(), "eCCYsQxSRCE:APA91bG_RPDPvr-ALh8taZp6sBYVM1ehORnXrhG5PTOVR-KuYIf1dygYgaXEWNMKtXtqzQCyP0tkBwNmTjyvCCZSKwy-hVjWm3NKwgE-DtJdvMOMaw5Jb0DS3_NXnVnuVXrzjixMjAnvecFFagXYSBwKv5LUtMWpBw")

    def test_is_backfilled(self):
        self.assertFalse(self.wrapped_synthetic_packet.is_backfilled())
        self.assertTrue(self.wrapped_example_packet.is_backfilled())

    def test_is_private(self):
        self.assertTrue(self.wrapped_synthetic_packet.is_private())
        self.assertFalse(self.wrapped_example_packet.is_private())

    def test_is_scrambled(self):
        self.assertTrue(self.wrapped_synthetic_packet.is_scrambled())
        self.assertFalse(self.wrapped_example_packet.is_scrambled())

    def test_device_make(self):
        self.assertEqual(self.wrapped_synthetic_packet.device_make(), "test device make")
        self.assertEqual(self.wrapped_example_packet.device_make(), "Google")

    def test_device_model(self):
        self.assertEqual(self.wrapped_synthetic_packet.device_model(), "test device model")
        self.assertEqual(self.wrapped_example_packet.device_model(), "Pixel XL")

    def test_device_os(self):
        self.assertEqual(self.wrapped_synthetic_packet.device_os(), "test device os")
        self.assertEqual(self.wrapped_example_packet.device_os(), "Android")

    def test_device_os_version(self):
        self.assertEqual(self.wrapped_synthetic_packet.device_os_version(), "test device os version")
        self.assertEqual(self.wrapped_example_packet.device_os_version(), "8.1.0")

    def test_app_version(self):
        self.assertEqual(self.wrapped_synthetic_packet.app_version(), "test app version")
        self.assertEqual(self.wrapped_example_packet.app_version(), "2.3.4")

    def test_battery_level_percent(self):
        self.assertEqual(self.wrapped_synthetic_packet.battery_level_percent(), 99.0)
        self.assertEqual(self.wrapped_example_packet.battery_level_percent(), 25.0)

    def test_device_temperature_c(self):
        self.assertEqual(self.wrapped_synthetic_packet.device_temperature_c(), 25.0)
        self.assertEqual(self.wrapped_example_packet.device_temperature_c(), 32.0)

    def test_acquisition_server(self):
        self.assertEqual(self.wrapped_synthetic_packet.acquisition_server(), "test acquisition server")
        self.assertEqual(self.wrapped_example_packet.acquisition_server(), "wss://milton.soest.hawaii.edu:8000/acquisition/v900")

    def test_time_synchronization_server(self):
        self.assertEqual(self.wrapped_synthetic_packet.time_synchronization_server(), "test time synchronization server")
        self.assertEqual(self.wrapped_example_packet.time_synchronization_server(), "wss://redvox.io/synch/v2")

    def test_authentication_server(self):
        self.assertEqual(self.wrapped_synthetic_packet.authentication_server(), "test authentication server")
        self.assertEqual(self.wrapped_example_packet.authentication_server(), "https://redvox.io/login/mobile")

    def test_app_file_start_timestamp_epoch_microseconds_utc(self):
        self.assertEqual(self.wrapped_synthetic_packet.app_file_start_timestamp_epoch_microseconds_utc(), 1519166348000000)
        self.assertEqual(self.wrapped_example_packet.app_file_start_timestamp_epoch_microseconds_utc(), 1532656864354000)

    def test_app_file_start_timestamp_machine(self):
        self.assertEqual(self.wrapped_synthetic_packet.app_file_start_timestamp_machine(), 42)
        self.assertEqual(self.wrapped_example_packet.app_file_start_timestamp_machine(), 1532656848035001)

    def test_server_timestamp_epoch_microseconds_utc(self):
        self.assertEqual(self.wrapped_synthetic_packet.server_timestamp_epoch_microseconds_utc(), 1519166348000000 + 10000)
        self.assertEqual(self.wrapped_example_packet.server_timestamp_epoch_microseconds_utc(), 1532656543460000)

    def test_metadata(self):
        self.assertTrue("foo" in self.wrapped_synthetic_packet.metadata_as_dict())
        self.assertEqual(self.wrapped_synthetic_packet.metadata_as_dict()["foo"], "bar")

class TestEvenlySampledSensor(unittest.TestCase):
    pass


class TestUnevenlySampledSensor(unittest.TestCase):
    pass


class TestUnevenlyXyzSampledSensor(unittest.TestCase):
    pass


class TestMicrophoneSensor(unittest.TestCase):
    pass


class TestBarometerSensor(unittest.TestCase):
    pass


class TestLocationSensor(unittest.TestCase):
    pass


class TestTimeSynchronizationSensor(unittest.TestCase):
    pass


class TestAccelerometerSensor(unittest.TestCase):
    pass


class TestMagnetometerSensor(unittest.TestCase):
    pass


class TestGyroscopeSensor(unittest.TestCase):
    pass


class TestLightSensor(unittest.TestCase):
    pass
