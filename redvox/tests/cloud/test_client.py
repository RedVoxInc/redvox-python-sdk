# import unittest
# from typing import Optional, Tuple, List
# import hashlib
# import tempfile
#
# from redvox.cloud.api import ApiConfig
# from redvox.cloud.client import CloudClient, cloud_client, chunk_time_range
# import redvox.cloud.errors as cloud_errors
# import redvox.tests.cloud.cloud_test_utils as test_utils
# import redvox.api900.reader as reader
#
#
# class ClientTests(unittest.TestCase):
#     def setUp(self) -> None:
#         self.client: Optional[CloudClient] = None
#         if test_utils.cloud_credentials_provided():
#             self.client = test_utils.client_from_credentials()
#         else:
#             print(f"Warning: cloud credentials not provided, will skip cloud API tests\n"
#                   f"If you want to enable tests, set the appropriate environment variables. Here's a template:\n"
#                   f"{test_utils.cloud_env_template()}")
#
#     def tearDown(self) -> None:
#         if self.client:
#             self.client.close()
#
#     def test_chunk_time_range_smaller(self):
#         chunks: List[Tuple[int, int]] = chunk_time_range(0, 9, 10)
#         self.assertEqual([(0, 9)], chunks)
#
#     def test_chunk_time_range_equal(self):
#         chunks: List[Tuple[int, int]] = chunk_time_range(0, 10, 10)
#         self.assertEqual([(0, 10)], chunks)
#
#     def test_chunk_time_range_greater(self):
#         chunks: List[Tuple[int, int]] = chunk_time_range(0, 11, 10)
#         self.assertEqual([(0, 10), (10, 11)], chunks)
#
#     def test_client_init_good(self):
#         if self.client:
#             self.assertTrue(self.client.health_check())
#
#     def test_bad_creds_no_secret(self):
#         with self.assertRaises(cloud_errors.AuthenticationError):
#             with cloud_client("foo", "bar"):
#                 pass
#
#     def test_bad_creds(self):
#         with self.assertRaises(cloud_errors.AuthenticationError):
#             with cloud_client("foo", "bar", secret_token="gucci"):
#                 pass
#
#     def test_bad_protocol(self):
#         with self.assertRaises(cloud_errors.AuthenticationError):
#             with cloud_client("foo",
#                               "bar",
#                               secret_token="gucci",
#                               redvox_conf=ApiConfig(
#                                   "http",
#                                   "redvox.io",
#                                   8080
#                               )):
#                 pass
#
#     def test_bad_host(self):
#         with self.assertRaises(cloud_errors.ApiConnectionError) as context:
#             with cloud_client("foo", "bar", secret_token="gucci", redvox_conf=ApiConfig(
#                     "https",
#                     "redsox.io",
#                     8080
#             ),
#                               timeout=2.0):
#                 pass
#
#         self.assertTrue("timed out" in str(context.exception))
#
#     def test_bad_port(self):
#         with self.assertRaises(cloud_errors.ApiConnectionError) as context:
#             with cloud_client("foo", "bar", secret_token="gucci", redvox_conf=ApiConfig(
#                     "https",
#                     "redvox.io",
#                     8081
#             ),
#                               timeout=2.0):
#                 pass
#
#         self.assertTrue("timed out" in str(context.exception))
#
#     def test_bad_refresh(self):
#         with self.assertRaises(cloud_errors.CloudApiError) as context:
#             with cloud_client("foo",
#                               "bar",
#                               secret_token="gucci",
#                               refresh_token_interval=0,
#                               redvox_conf=ApiConfig(
#                                   "https",
#                                   "redvox.io",
#                                   8080,
#
#                               ),
#                               timeout=2.0):
#                 pass
#
#         self.assertTrue("refresh_token_interval must be strictly > 0" in str(context.exception))
#
#     def test_bad_timeout(self):
#         with self.assertRaises(cloud_errors.CloudApiError) as context:
#             with cloud_client("foo",
#                               "bar",
#                               secret_token="gucci",
#                               redvox_conf=ApiConfig(
#                                   "https",
#                                   "redvox.io",
#                                   8080,
#
#                               ),
#                               timeout=0.0):
#                 pass
#         self.assertTrue("timeout must be strictly > 0" in str(context.exception))
#
#     def test_health_check(self):
#         if self.client:
#             self.assertTrue(self.client.health_check())
#
#     def test_authenticate_user(self):
#         if test_utils.cloud_credentials_provided():
#             self.assertIsNotNone(self.client)
#
#     def test_validate_token(self):
#         if self.client:
#             resp = self.client.validate_own_auth_token()
#             self.assertIsNotNone(resp)
#             self.assertEqual(resp.aud, "api")
#             self.assertEqual(resp.iss, "RedVox, Inc.")
#             self.assertEqual(resp.sub, "redvoxcore@gmail.com")
#             self.assertEqual(resp.tier, "ADMIN")
#
#     def test_refresh_token(self):
#         if self.client:
#             resp = self.client.refresh_own_auth_token()
#             self.assertIsNotNone(resp)
#             self.assertTrue("v2.public." in resp.auth_token)
#
#     def test_request_report_data_good(self):
#         if self.client:
#             resp = self.client.request_report_data("9c88102bb3bf47edab895b9f8a708cc1")
#             self.assertIsNotNone(resp)
#             self.assertTrue("https://s3.us-west-2.amazonaws.com/rdvxdata/report_data/9c88102bb3bf47edab895b9f8a708cc1.zip" in resp.signed_url)
#             data_buf: bytes = resp.download_buf()
#             self.assertEqual("9a332a125929fd904c1c173d6d10a7f22918e4de61808df7bc2a3b5d8553234c36b0abb7370bae576459f8da9479cc694fb35888e2bdd2dad25305f7b6bbe8e0",
#                              hashlib.sha512(data_buf).hexdigest())
#
#     def test_request_report_data_no_access(self):
#         if self.client:
#             resp = self.client.request_report_data("5059d9d0e80c41a7a06ca90045014bc1")
#             self.assertIsNone(resp)
#
#     def test_request_report_data_bad_id(self):
#         if self.client:
#             resp = self.client.request_report_data("foo")
#             self.assertIsNone(resp)
#
#     def test_request_data_range_bad_range(self):
#         if self.client:
#             with self.assertRaises(cloud_errors.CloudApiError) as ctx:
#                 self.client.request_data_range(300, 100, ["1637681013"])
#
#             self.assertEqual("start_ts_s must be < end_ts_s", str(ctx.exception))
#
#     def test_request_data_range_bad_station_ids(self):
#         if self.client:
#             with self.assertRaises(cloud_errors.CloudApiError) as ctx:
#                 self.client.request_data_range(100, 300, [])
#
#             self.assertEqual("At least one station_id must be provided", str(ctx.exception))
#
#     def test_request_data_range_incorrect_station_ids(self):
#         if self.client:
#             resp = self.client.request_data_range(1592956800, 1592960400, ["foo"])
#             self.assertIsNotNone(resp)
#             self.assertEqual(len(resp.signed_urls), 0)
#
#     def test_request_data_range_incorrect_range(self):
#         if self.client:
#             resp = self.client.request_data_range(1340496000, 1340499600, ["foo"])
#             self.assertIsNotNone(resp)
#             self.assertEqual(len(resp.signed_urls), 0)
#
#     def test_request_data_range_good(self):
#         if self.client:
#             resp = self.client.request_data_range(1592956800, 1592960400, ["1637681011",
#                                                                            "1637681014"])
#             self.assertIsNotNone(resp)
#             num_resp: int = len(resp.signed_urls)
#             self.assertTrue(num_resp > 0)
#
#             with tempfile.TemporaryDirectory() as temp_dir:
#                 resp.download_fs(temp_dir)
#                 data = reader.read_rdvxz_file_range(temp_dir + "/api900",
#                                                     structured_layout=True,
#                                                     concat_continuous_segments=False)
#
#                 self.assertTrue("1637681014:1807255410" in data)
#                 self.assertTrue("1637681011:868885745" in data)
#                 self.assertEqual(num_resp, len(data["1637681011:868885745"]) + len(data["1637681014:1807255410"]))
#
#     def test_timing_meta_good(self):
#         if self.client:
#             resp = self.client.request_timing_metadata(1592956800,
#                                                        1592960400, ["1637681011",
#                                                                     "1637681014"])
#
#             self.assertIsNotNone(resp)
#             self.assertTrue(len(resp.items) > 0)
#
#     def test_timing_meta_good_chunked(self):
#         if self.client:
#             resp = self.client.request_timing_metadata(1592956800,
#                                                        1593043200, ["1637681011",
#                                                                     "1637681014"],
#                                                        chunk_by_seconds=3600)
#
#             self.assertIsNotNone(resp)
#             self.assertTrue(len(resp.items) > 0)
