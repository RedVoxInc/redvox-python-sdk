import unittest
import redvox.api1000.wrapped_redvox_packet.user_information as user


class TestUserInfo(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_user_info: user.UserInformation = user.UserInformation.new()
        self.non_empty_user_info: user.UserInformation = user.UserInformation.new()
        self.non_empty_user_info.set_firebase_token("fakeFirebaseToken")

    # def test_validate_user(self):
    #     error_list = user.validate_user_information(self.non_empty_user_info)
    #     self.assertEqual(error_list, [])
    #     error_list = user.validate_user_information(self.empty_user_info)
    #     self.assertNotEqual(error_list, [])
