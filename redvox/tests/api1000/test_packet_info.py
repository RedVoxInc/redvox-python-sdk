import unittest
import redvox.api1000.wrapped_redvox_packet.packet_information as packet_info


class TestPacketInfo(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_packet_info: packet_info.PacketInformation = packet_info.PacketInformation.new()
        self.non_empty_packet_info: packet_info.PacketInformation = packet_info.PacketInformation.new()
        self.non_empty_packet_info.set_is_backfilled(False)

    def test_get_is_backfilled(self):
        self.assertEqual(self.non_empty_packet_info.get_is_backfilled(), False)
