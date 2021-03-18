import unittest
import numpy as np
import redvox.api1000.wrapped_redvox_packet.wrapped_packet as w_packet
import redvox.api1000.wrapped_redvox_packet.station_information as station
import redvox.api1000.wrapped_redvox_packet.timing_information as timing


class TestWrappedPacket(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_packet_info: w_packet.WrappedRedvoxPacketM = w_packet.WrappedRedvoxPacketM.new()
        self.non_empty_packet_info: w_packet.WrappedRedvoxPacketM = w_packet.WrappedRedvoxPacketM.new()
        self.non_empty_packet_info.set_api(1000)
        self.non_empty_packet_info.get_station_information().set_id("test_station")
        self.non_empty_packet_info.get_station_information().set_uuid("1234567890")
        self.non_empty_packet_info.get_station_information().get_app_settings().get_additional_input_sensors().\
            append_values([station.InputSensor.PRESSURE])
        self.non_empty_packet_info.get_station_information().get_app_settings().set_audio_sampling_rate(
            station.AudioSamplingRate["HZ_80"])
        self.non_empty_packet_info.get_station_information().get_app_settings().set_station_id("test_station")
        self.non_empty_packet_info.get_station_information().get_station_metrics().get_timestamps().set_default_unit()
        self.non_empty_packet_info.get_station_information().get_station_metrics().get_timestamps().set_timestamps(
            np.array([1000, 2000, 3500, 5000]), True)
        sync_exchange: timing.SynchExchange = timing.SynchExchange.new()
        sync_exchange.set_default_unit()
        sync_exchange.set_a1(1000)
        sync_exchange.set_a2(3501)
        sync_exchange.set_a3(3502)
        sync_exchange.set_b1(2500)
        sync_exchange.set_b2(2501)
        sync_exchange.set_b3(5602)
        self.non_empty_packet_info.get_timing_information().get_synch_exchanges().append_values([sync_exchange])
        self.non_empty_packet_info.get_timing_information().set_default_unit()
        self.non_empty_packet_info.get_timing_information().set_app_start_mach_timestamp(1)
        self.non_empty_packet_info.get_timing_information().set_packet_start_os_timestamp(1)
        self.non_empty_packet_info.get_timing_information().set_packet_end_os_timestamp(1)
        self.non_empty_packet_info.get_timing_information().set_packet_start_mach_timestamp(1)
        self.non_empty_packet_info.get_timing_information().set_packet_end_mach_timestamp(1)
        self.non_empty_packet_info.get_station_information().get_service_urls().set_auth_server("https://fake.auth.foo")
        self.non_empty_packet_info.get_station_information().get_service_urls().\
            set_acquisition_server("wss://fake.acquire.foo")
        self.non_empty_packet_info.get_sensors().new_audio()
        self.non_empty_packet_info.get_sensors().get_audio().get_samples().set_values(np.array([1.000, .50, .1025],
                                                                                               dtype=int))
        self.non_empty_packet_info.get_sensors().get_audio().set_sample_rate(80.0)
        self.non_empty_packet_info.get_sensors().get_audio().set_first_sample_timestamp(1)

    def test_validate_packet(self):
        error_list = w_packet.validate_wrapped_packet(self.non_empty_packet_info)
        self.assertEqual(error_list, [])
        error_list = w_packet.validate_wrapped_packet(self.empty_packet_info)
        self.assertNotEqual(error_list, [])
