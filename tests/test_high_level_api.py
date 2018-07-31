from redvox.api900 import reader
import tests.mock_packets

import unittest

from redvox.api900.lib import api900_pb2


class TestWrappedRedvoxPacket(unittest.TestCase):
    def setUp(self):
        self.base_packet: api900_pb2.RedvoxPacket = tests.mock_packets.base_packet()
        self.wrapped_base_packet = reader.wrap(self.base_packet)
        self.wrapped_example_packet = reader.wrap(reader.read_file("0000001314_1532656864354.rdvxz"))

    def test_api(self):
        self.assertEqual(self.wrapped_base_packet.api(), 900)
        self.assertEqual(self.wrapped_example_packet.api(), 900)

    def test_redvox_id(self):
        self.assertEqual(self.wrapped_base_packet.redvox_id(), "1")
        self.assertEqual(self.wrapped_example_packet.redvox_id(), "0000001314")

    def test_uuid(self):
        self.assertEqual(self.wrapped_base_packet.uuid(), "2")
        self.assertEqual(self.wrapped_example_packet.uuid(), "317985785")

    def test_authenticated_email(self):
        self.assertEqual(self.wrapped_base_packet.authenticated_email(), "foo@bar.baz")
        self.assertEqual(self.wrapped_example_packet.authenticated_email(), "anthony.christe@gmail.com")

    def test_firebase_token(self):
        self.assertEqual(self.wrapped_base_packet.authentication_token(), "test_authentication_token")
        self.assertEqual(self.wrapped_example_packet.authentication_token(), "redacted-1005665114")



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
