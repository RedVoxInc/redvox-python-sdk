"""
This module contains methods for interacting with the RedVox cloud based API.
"""
from dataclasses import dataclass
from typing import Dict, Optional

import requests

from redvox.cloud.routes import RoutesV1


@dataclass
class ApiConfig:
    """
    Provides a configuration for the base API URL.
    """
    protocol: str
    host: str
    port: int

    def url(self, end_point: str) -> str:
        """
        Formats the API URL.
        :param end_point: Endpoint to use.
        :return: The formatted API URL.
        """
        return f"{self.protocol}://{self.host}:{self.port}{end_point}"

    @staticmethod
    def default() -> 'ApiConfig':
        return ApiConfig("https", "redvox.io", 8080)


def health_check(api_config: ApiConfig) -> bool:
    url: str = api_config.url(RoutesV1.HEALTH_CHECK)
    # noinspection Mypy
    resp: requests.Response = requests.get(url)
    if resp.status_code == 200:
        return True

    return False


def post_api_call(api_config: ApiConfig, route: str, body: Dict) -> Optional[Dict]:
    url: str = api_config.url(route)
    # noinspection Mypy
    resp: requests.Response = requests.post(url, json=body)
    if resp.status_code == 200:
        # noinspection Mypy
        return resp.json()
    else:
        return None
