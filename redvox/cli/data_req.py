"""
This module provides methods and classes for requesting bulk RedVox data.
"""

import logging
from typing import List, TYPE_CHECKING

import redvox.cloud.client as cloud_client
import redvox.cloud.data_api as data_api
import redvox.cloud.data_client as data_client

if TYPE_CHECKING:
    from redvox.cloud.data_api import DataRangeReqType
    from redvox.cloud.config import RedVoxConfig

# pylint: disable=C0103
log = logging.getLogger(__name__)


def make_data_req(
    out_dir: str,
    redvox_config: "RedVoxConfig",
    req_start_s: int,
    req_end_s: int,
    redvox_ids: List[str],
    api_type: "DataRangeReqType",
    retries: int,
    timeout: int,
    correct_query_timing: bool,
) -> bool:
    """
    Makes a data request to the RedVox data_server.
    :param out_dir: The output directory to store downloaded files.
    :param redvox_config: An instance of the RedVox cloud configuration.
    :param req_start_s: The request start time as seconds since the epoch.
    :param req_end_s: The request end time as seconds since the epoch.
    :param redvox_ids: A list of RedVox ids.
    :param api_type: The API level to request data for (can be 900, 1000, or both)
    :param retries: The number of retries to perform on failed downloads.
    :return: True if this succeeds, False otherwise.
    """
    client: cloud_client.CloudClient = cloud_client.CloudClient(redvox_config, timeout=timeout)
    data_resp: data_api.DataRangeResp = client.request_data_range(
        req_start_s, req_end_s, redvox_ids, api_type, correct_query_timing=correct_query_timing
    )
    client.close()

    if len(data_resp.signed_urls) == 0:
        log.info("No signed urls returned")
        return False

    data_client.download_files(data_resp.signed_urls, out_dir, retries)

    return True
