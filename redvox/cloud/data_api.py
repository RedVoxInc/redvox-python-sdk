"""
This module contains API definitions and functions for working with raw RedVox data packets.
"""

from dataclasses import dataclass
from enum import Enum
from multiprocessing.queues import Queue
from typing import Callable, List, Optional, Tuple

from dataclasses_json import dataclass_json
import requests

from redvox.cloud.api import post_req
from redvox.cloud.config import RedVoxConfig
import redvox.cloud.data_io as data_io
import redvox.cloud.data_client as data_client
from redvox.cloud.routes import RoutesV1


@dataclass_json
@dataclass
class ReportDataReq:
    """
    A request for a signed URL to a RedVox report distribution.
    """

    auth_token: str
    report_id: str
    secret_token: Optional[str] = None


@dataclass_json
@dataclass
class ReportDataResp:
    """
    Response for a report signed URL.
    """

    signed_url: str

    def download_buf(self, retries: int = 3) -> Optional[bytes]:
        """
        Downloads the zip compressed report data and returns it as a byte buffer.
        :param retries: Number of times to retry the download of failure.
        :return: Bytes of the compressed report data.
        """
        return data_io.get_file(self.signed_url, retries)

    def download_fs(self, out_dir: str, retries: int = 3) -> Tuple[str, int]:
        """
        Downloads the zip compressed report data to the file system.
        :param out_dir: Output directory to download data to.
        :param retries: Number of times to retry the download on failure.
        :return: A tuple containing the file name and the number of bytes written.
        """
        return data_io.download_file(
            self.signed_url, requests.Session(), out_dir, retries
        )


@dataclass_json
@dataclass
class DataRangeReq:
    """
    Definition of data range request.
    """

    auth_token: str
    start_ts_s: int
    end_ts_s: int
    redvox_ids: List[str]
    secret_token: Optional[str] = None


@dataclass_json
@dataclass
class DataRangeResp:
    """
    Definition of a data range response.
    """

    signed_urls: List[str]

    def download_fs(self, out_dir: str, retries: int = 3, out_queue: Optional[Queue] = None) -> None:
        """
        Download the referenced packets to the provided output directory.
        :param out_dir: Output directory to store the downloaded files.
        :param retries: Number of times to retry downloading the file on failure.
        """
        data_client.download_files(self.signed_urls, out_dir, retries, out_queue=out_queue)

    def append(self, other: "DataRangeResp") -> "DataRangeResp":
        """
        Combines multiple responses.
        :param other: The other response to combine results with.
        :return: A modified instance of self.
        """
        self.signed_urls.extend(other.signed_urls)
        return self


def request_report_data(
    redvox_config: RedVoxConfig,
    report_data_req: ReportDataReq,
    session: Optional[requests.Session] = None,
    timeout: Optional[float] = None,
) -> Optional[ReportDataResp]:
    """
    Makes an API call to generate a signed URL of a RedVox report.
    :param redvox_config: An API config.
    :param report_data_req: The request.
    :param session: An (optional) session for re-using an HTTP client.
    :param timeout: An (optional) timeout.
    :return: The response.
    """
    # noinspection Mypy
    # pylint: disable=E1101
    handle_resp: Callable[
        [requests.Response], ReportDataResp
    ] = lambda resp: ReportDataResp.from_dict(resp.json())
    return post_req(
        redvox_config,
        RoutesV1.DATA_REPORT_REQ,
        report_data_req,
        handle_resp,
        session,
        timeout,
    )


class DataRangeReqType(Enum):
    """
    Type of RedVox data to be requested.
    """

    API_900: str = "API_900"
    API_1000: str = "API_1000"
    API_900_1000: str = "API_900_1000"


def request_range_data(
    redvox_config: RedVoxConfig,
    data_range_req: DataRangeReq,
    session: Optional[requests.Session] = None,
    timeout: Optional[float] = None,
    req_type: DataRangeReqType = DataRangeReqType.API_900,
) -> DataRangeResp:
    """
    Requests signed URLs for a range of RedVox packets.
    :param redvox_config: An API config.
    :param data_range_req: The request.
    :param session: An (optional) session for re-using an HTTP client.
    :param timeout: An (optional) timeout.
    :param req_type: (Optional) defines which type of RedVox data should be requested
    :return: A DataRangeResp.
    """
    # noinspection Mypy
    # pylint: disable=E1101
    handle_resp: Callable[
        [requests.Response], DataRangeResp
    ] = lambda resp: DataRangeResp.from_dict(resp.json())

    # API 900
    if req_type == DataRangeReqType.API_900:
        res: Optional[DataRangeResp] = post_req(
            redvox_config,
            RoutesV1.DATA_RANGE_REQ,
            data_range_req,
            handle_resp,
            session,
            timeout,
        )

        return res if res else DataRangeResp([])
    # API 1000
    elif req_type == DataRangeReqType.API_1000:
        res = post_req(
            redvox_config,
            RoutesV1.DATA_RANGE_REQ_M,
            data_range_req,
            handle_resp,
            session,
            timeout,
        )

        return res if res else DataRangeResp([])
    # API 900 and 1000
    else:
        res_900: Optional[DataRangeResp] = post_req(
            redvox_config,
            RoutesV1.DATA_RANGE_REQ,
            data_range_req,
            handle_resp,
            session,
            timeout,
        )

        res_1000: Optional[DataRangeResp] = post_req(
            redvox_config,
            RoutesV1.DATA_RANGE_REQ_M,
            data_range_req,
            handle_resp,
            session,
            timeout,
        )

        res_900_final: DataRangeResp = DataRangeResp([]) if res_900 is None else res_900
        res_1000_final: DataRangeResp = (
            DataRangeResp([]) if res_1000 is None else res_1000
        )

        return res_900_final.append(res_1000_final)
