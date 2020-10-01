import unittest
import redvox.api1000.wrapped_redvox_packet.timing_information as timing


class TestSyncExchange(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_sync_exchange: timing.SynchExchange = timing.SynchExchange.new()
        self.non_empty_sync_exchange: timing.SynchExchange = timing.SynchExchange.new()
        self.non_empty_sync_exchange.set_default_unit()
        self.non_empty_sync_exchange.set_a1(1000)
        self.non_empty_sync_exchange.set_a2(3501)
        self.non_empty_sync_exchange.set_a3(3502)
        self.non_empty_sync_exchange.set_b1(2500)
        self.non_empty_sync_exchange.set_b2(2501)
        self.non_empty_sync_exchange.set_b3(5602)

    def test_validate_sync(self):
        error_list = timing.validate_synch_exchange(self.non_empty_sync_exchange)
        self.assertEqual(error_list, [])
        self.non_empty_sync_exchange.set_a2(500)
        self.non_empty_sync_exchange.set_a3(100)
        self.non_empty_sync_exchange.set_b2(500)
        self.non_empty_sync_exchange.set_b3(100)
        error_list = timing.validate_synch_exchange(self.non_empty_sync_exchange)
        self.assertNotEqual(error_list, [])
        error_list = timing.validate_synch_exchange(self.empty_sync_exchange)
        self.assertNotEqual(error_list, [])


class TestTimingInfo(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_timing_info: timing.TimingInformation = timing.TimingInformation.new()
        self.non_empty_timing_info: timing.TimingInformation = timing.TimingInformation.new()
        self.non_empty_timing_info.set_default_unit()
        self.non_empty_sync_exchange: timing.SynchExchange = timing.SynchExchange.new()
        self.non_empty_sync_exchange.set_default_unit()
        self.non_empty_sync_exchange.set_a1(1000)
        self.non_empty_sync_exchange.set_a2(3501)
        self.non_empty_sync_exchange.set_a3(3502)
        self.non_empty_sync_exchange.set_b1(2500)
        self.non_empty_sync_exchange.set_b2(2501)
        self.non_empty_sync_exchange.set_b3(5602)
        self.non_empty_timing_info.get_synch_exchanges().append_values([self.non_empty_sync_exchange])
        self.non_empty_timing_info.set_default_unit()
        self.non_empty_timing_info.set_app_start_mach_timestamp(1)
        self.non_empty_timing_info.set_packet_start_os_timestamp(1)
        self.non_empty_timing_info.set_packet_end_os_timestamp(1)
        self.non_empty_timing_info.set_packet_start_mach_timestamp(1)
        self.non_empty_timing_info.set_packet_end_mach_timestamp(1)

    def test_validate_timing(self):
        error_list = timing.validate_timing_information(self.non_empty_timing_info)
        self.assertEqual(error_list, [])
        error_list = timing.validate_timing_information(self.empty_timing_info)
        self.assertNotEqual(error_list, [])

    def test_get_synch_exchange_array(self):
        synch_exchange_array = self.non_empty_timing_info.get_synch_exchange_array()
        self.assertEqual(len(synch_exchange_array), 6)
        self.assertEqual(synch_exchange_array[0], 1000)
        self.assertEqual(synch_exchange_array[5], 5602)
