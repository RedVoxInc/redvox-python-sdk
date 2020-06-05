"""
This module provides methods and classes for requesting bulk RedVox data.
"""

import logging
from typing import List

import redvox.cloud.api as cloud_api
import redvox.cloud.client as cloud_client
import redvox.cloud.data_api as data_api
import redvox.cloud.data_io as data_io

# pylint: disable=C0103
log = logging.getLogger(__name__)


def make_data_req(out_dir: str,
                  protocol: str,
                  host: str,
                  port: int,
                  email: str,
                  password: str,
                  req_start_s: int,
                  req_end_s: int,
                  redvox_ids: List[str],
                  retries: int,
                  secret_token: str) -> bool:
    """
    Makes a data request to the RedVox data_server.
    :param out_dir: The output directory to store downloaded files.
    :param protocol: One of either https or http.
    :param host: The host of the data server.
    :param port: The port of the data server.
    :param email: The email address of the redvox.io user.
    :param password: The password of the redvox.io user.
    :param req_start_s: The request start time as seconds since the epoch.
    :param req_end_s: The request end time as seconds since the epoch.
    :param redvox_ids: A list of RedVox ids.
    :param retries: The number of retries to perform on failed downloads.
    :param secret_token: A shared secret token required for accessing the data service.
    :return: True if this succeeds, False otherwise.
    """
    api_conf: cloud_api.ApiConfig = cloud_api.ApiConfig(protocol,
                                                        host,
                                                        port)
    client: cloud_client.CloudClient = cloud_client.CloudClient(email,
                                                                password,
                                                                api_conf=api_conf,
                                                                secret_token=secret_token)
    data_resp: data_api.DataRangeResp = client.request_data_range(req_start_s, req_end_s, redvox_ids)
    client.close()

    if len(data_resp.signed_urls) == 0:
        log.error("No signed urls returned")
        return False

    data_io.download_files_parallel(data_resp.signed_urls, out_dir, retries)

    return True
