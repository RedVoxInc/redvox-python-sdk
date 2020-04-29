import unittest
import redvox.api1000.wrapped_redvox_packet.server_information as server


class TestServerInfo(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_server_info: server.ServerInformation = server.ServerInformation.new()
        self.non_empty_server_info: server.ServerInformation = server.ServerInformation.new()
        self.non_empty_server_info.set_auth_server_url("https://fake.auth.foo")
        self.non_empty_server_info.set_acquisition_server_url("wss://fake.acquire.foo")

    # def test_validate_server(self):
    #     error_list = server.validate_server_information(self.non_empty_server_info)
    #     self.assertEqual(error_list, [])
    #     error_list = server.validate_server_information(self.empty_server_info)
    #     self.assertNotEqual(error_list, [])
