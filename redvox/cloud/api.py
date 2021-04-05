"""
This module contains methods for interacting with the RedVox cloud based API.
"""
# from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import requests

from redvox.cloud.config import RedVoxConfig
import redvox.cloud.errors as cloud_errors
from redvox.cloud.routes import RoutesV1


def post_req(
    redvox_config: RedVoxConfig,
    route: str,
    req: Any,
    resp_transform: Callable[[requests.Response], Any],
    session: Optional[requests.Session] = None,
    timeout: Optional[float] = 10.0,
) -> Optional[Any]:
    """
    Performs an HTTP POST request.
    :param redvox_config: API endpoint configuration.
    :param route: Route to POST to.
    :param req: Request to send in POST.
    :param resp_transform: Function to transform the response into something we can use.
    :param session: The HTTP session.
    :param timeout: An (optional) timeout.
    :return: The optional response.
    """
    url: str = redvox_config.url(route)
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
    except requests.RequestException as ex:
        raise cloud_errors.ApiConnectionError(
            f"Error making POST request to {url}: with body: {req_dict}: {ex}"
        )


def health_check(
    redvox_config: RedVoxConfig,
    session: Optional[requests.Session] = None,
    timeout: Optional[float] = 10.0,
) -> bool:
    """
    Check that the Cloud API endpoint is up.
    :param redvox_config: The API config.
    :param session: An (optional) session for re-using an HTTP client.
    :param timeout: An optional timeout.
    :return: True if the endpoint is up, False otherwise.
    """
    url: str = redvox_config.url(RoutesV1.HEALTH_CHECK)

    if session:
        resp: requests.Response = session.get(url, timeout=timeout)
    else:
        resp = requests.get(url, timeout=timeout)

    if resp.status_code == 200:
        return True

    return False
