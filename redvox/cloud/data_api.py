"""
This module contains API definitions and functions for working with raw RedVox data packets.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from dataclasses_json import dataclass_json
import requests

from redvox.cloud.api import ApiConfig, post_req
import redvox.cloud.data_io as data_io
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
        return data_io.download_file(self.signed_url, requests.Session(), out_dir, retries)


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

    def download_fs(self, out_dir: str, retries: int = 3) -> None:
        """
        Download the referenced packets to the provided output directory.
        :param out_dir: Output directory to store the downloaded files.
        :param retries: Number of times to retry downloading the file on failure.
        """
        data_io.download_files_parallel(self.signed_urls, out_dir, retries)


def request_report_data(api_config: ApiConfig,
                        report_data_req: ReportDataReq,
                        session: Optional[requests.Session] = None,
                        timeout: Optional[float] = None) -> Optional[ReportDataResp]:
    """
    Makes an API call to generate a signed URL of a RedVox report.
    :param api_config: An API config.
    :param report_data_req: The request.
    :param session: An (optional) session for re-using an HTTP client.
    :return: The response.
    """
    # noinspection Mypy
    handle_resp: Callable[[requests.Response], ReportDataResp] = lambda resp: ReportDataResp.from_dict(resp.json())
    return post_req(api_config,
                    RoutesV1.DATA_REPORT_REQ,
                    report_data_req,
                    handle_resp,
                    session,
                    timeout)


def request_range_data(api_config: ApiConfig,
                       data_range_req: DataRangeReq,
                       session: Optional[requests.Session] = None,
                       timeout: Optional[float] = None) -> DataRangeResp:
    """
    Requests signed URLs for a range of RedVox packets.
    :param api_config: An API config.
    :param data_range_req: The request.
    :param session: An (optional) session for re-using an HTTP client.
    :return: A DataRangeResp.
    """
    # noinspection Mypy
    handle_resp: Callable[[requests.Response], DataRangeResp] = lambda resp: DataRangeResp.from_dict(resp.json())
    res: Optional[DataRangeResp] = post_req(api_config,
                                            RoutesV1.DATA_RANGE_REQ,
                                            data_range_req,
                                            handle_resp,
                                            session,
                                            timeout)

    return res if res else DataRangeResp([])
