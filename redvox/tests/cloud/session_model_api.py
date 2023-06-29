import unittest

from redvox.api1000.wrapped_redvox_packet.wrapped_packet import WrappedRedvoxPacketM
from redvox.cloud.session_model_api import session_key_from_packet
from redvox.common.errors import RedVoxError


class TestSessionKeyExtraction(unittest.TestCase):
    def test_session_key_from_packet(self):
        pkt: WrappedRedvoxPacketM = WrappedRedvoxPacketM.new()
        pkt.get_station_information().set_id("1234567890")
        pkt.get_station_information().set_uuid("9876543210")
        pkt.get_timing_information().set_app_start_mach_timestamp(123456789.0)

        session_key: str = session_key_from_packet(pkt)
        self.assertEqual(session_key, "1234567890:9876543210:123456789")

    def test_session_key_from_packet_no_station_info(self):
        pkt: WrappedRedvoxPacketM = WrappedRedvoxPacketM.new()
        pkt.get_timing_information().set_app_start_mach_timestamp(123456789.0)
        with self.assertRaises(RedVoxError) as err:
            session_key_from_packet(pkt)
            self.assertTrue("Missing required station info" in err.exception)

    def test_session_key_from_packet_no_timing_info(self):
        pkt: WrappedRedvoxPacketM = WrappedRedvoxPacketM.new()
        pkt.get_station_information().set_id("1234567890")
        pkt.get_station_information().set_uuid("9876543210")
        with self.assertRaises(RedVoxError) as err:
            session_key_from_packet(pkt)
            self.assertTrue("Missing required timing info" in err.exception)
