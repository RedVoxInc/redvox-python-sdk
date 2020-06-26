"""
This module contains methods for interacting with the RedVox cloud based API.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import requests

import redvox.cloud.errors as cloud_errors
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


def post_req(api_config: ApiConfig,
             route: str,
             req: Any,
             resp_transform: Callable[[requests.Response], Any],
             session: Optional[requests.Session] = None,
             timeout: Optional[float] = 10.0) -> Optional[Any]:
    url: str = api_config.url(route)
    # noinspection Mypy
    req_dict: Dict = req.to_dict()

    try:
        if session:
            resp: requests.Response = session.post(url, json=req_dict, timeout=timeout)
        else:
            resp = requests.post(url, json=req_dict, timeout=timeout)
        if resp.status_code == 200:
            # noinspection Mypy
            return resp_transform(resp)
        else:
            return None
    except requests.RequestException as e:
        raise cloud_errors.ApiConnectionError(f"Error making POST request to {url}: with body: {req_dict}: {e}")


def health_check(api_config: ApiConfig,
                 session: Optional[requests.Session] = None,
                 timeout: Optional[float] = 10.0) -> bool:
    """
    Check that the Cloud API endpoint is up.
    :param api_config: The API config.
    :param session: An (optional) session for re-using an HTTP client.
    :return: True if the endpoint is up, False otherwise.
    """
    url: str = api_config.url(RoutesV1.HEALTH_CHECK)

    if session:
        resp: requests.Response = session.get(url, timeout=timeout)
    else:
        resp = requests.get(url, timeout=timeout)

    if resp.status_code == 200:
        return True

    return False
