import unittest
from typing import Optional

from redvox.cloud.api import ApiConfig
from redvox.cloud.client import CloudClient
import redvox.tests.cloud.cloud_test_utils as test_utils


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client: Optional[CloudClient] = None
        if test_utils.cloud_credentials_provided():
            self.client = test_utils.client_from_credentials()
        else:
            print("Warning: cloud credentials not provided, will skip cloud API tests")
            print("If you want to enable tests, set the appropriate environment variables. Here's a template:")
            print(test_utils.cloud_env_template())

    def tearDown(self) -> None:
        if self.client:
            self.client.close()

    def test_default_api_config(self):
        api_config: ApiConfig = ApiConfig.default()
        self.assertEqual(api_config.protocol, "https")
        self.assertEqual(api_config.host, "redvox.io")
        self.assertEqual(api_config.port, 8080)

    def test_api_config_url(self):
        api_config: ApiConfig = ApiConfig.default()
        self.assertEqual("https://redvox.io:8080/foo", api_config.url("/foo"))

    def test_health_check(self):
        if not self.client:
            return

        self.assertTrue(self.client.health_check())
