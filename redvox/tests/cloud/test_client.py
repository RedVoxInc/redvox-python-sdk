import unittest
from typing import Optional, Tuple, List

from redvox.cloud.api import ApiConfig
from redvox.cloud.client import CloudClient, cloud_client, chunk_time_range
import redvox.cloud.errors as cloud_errors
import redvox.tests.cloud.cloud_test_utils as test_utils


class ClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client: Optional[CloudClient] = None
        if test_utils.cloud_credentials_provided():
            self.client = test_utils.client_from_credentials()
        else:
            print("Warning: cloud credentials not provided, will skip cloud API tests")
            print("If you want to enable tests, set the appropriate environment variables. Here's a template:")
            print(test_utils.cloud_env_template())

    def test_chunk_time_range_smaller(self):
        chunks: List[Tuple[int, int]] = chunk_time_range(0, 9, 10)
        self.assertEqual([(0, 9)], chunks)

    def test_chunk_time_range_equal(self):
        chunks: List[Tuple[int, int]] = chunk_time_range(0, 10, 10)
        self.assertEqual([(0, 10)], chunks)

    def test_chunk_time_range_greater(self):
        chunks: List[Tuple[int, int]] = chunk_time_range(0, 11, 10)
        self.assertEqual([(0, 10), (10, 11)], chunks)

    def tearDown(self) -> None:
        if self.client:
            self.client.close()

    def test_client_init_good(self):
        if self.client:
            self.assertTrue(self.client.health_check())

    def test_bad_creds_no_secret(self):
        with self.assertRaises(cloud_errors.AuthenticationError):
            with cloud_client("foo", "bar"):
                pass

    def test_bad_creds(self):
        with self.assertRaises(cloud_errors.AuthenticationError):
            with cloud_client("foo", "bar", secret_token="gucci"):
                pass

    def test_bad_protocol(self):
        with self.assertRaises(cloud_errors.AuthenticationError):
            with cloud_client("foo", "bar", secret_token="gucci", api_conf=ApiConfig(
                    "http",
                    "redvox.io",
                    8080
            )):
                pass

    def test_bad_host(self):
        with self.assertRaises(cloud_errors.ApiConnectionError) as context:
            with cloud_client("foo", "bar", secret_token="gucci", api_conf=ApiConfig(
                    "https",
                    "redsox.io",
                    8080
            ),
                              timeout=2.0):
                pass

        self.assertTrue("timed out" in str(context.exception))

    def test_bad_port(self):
        with self.assertRaises(cloud_errors.ApiConnectionError) as context:
            with cloud_client("foo", "bar", secret_token="gucci", api_conf=ApiConfig(
                    "https",
                    "redvox.io",
                    8081
            ),
                              timeout=2.0):
                pass

        self.assertTrue("timed out" in str(context.exception))

    def test_bad_refresh(self):
        with self.assertRaises(cloud_errors.CloudApiError) as context:
            with cloud_client("foo",
                              "bar",
                              secret_token="gucci",
                refresh_token_interval=0,
                              api_conf=ApiConfig(
                    "https",
                    "redvox.io",
                    8080,

            ),
                              timeout=2.0):
                pass

        self.assertTrue("refresh_token_interval must be strictly > 0" in str(context.exception))

    def test_bad_timeout(self):
        with self.assertRaises(cloud_errors.CloudApiError) as context:
            with cloud_client("foo",
                              "bar",
                              secret_token="gucci",
                              api_conf=ApiConfig(
                                  "https",
                                  "redvox.io",
                                  8080,

                              ),
                              timeout=0.0):
                pass
        print(context.exception)
        self.assertTrue("timeout must be strictly > 0" in str(context.exception))

    def test_health_check(self):
        if self.client:
            self.assertTrue(self.client.health_check())
