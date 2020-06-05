from dataclasses import dataclass
from typing import List, Optional, Tuple

from dataclasses_json import dataclass_json
import requests

from redvox.cloud.api import ApiConfig
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

    def download_buf(self) -> Optional[bytes]:
        return data_io.get_file(self.signed_url, 3)

    def download_fs(self, out_dir: str) -> Tuple[str, int]:
        return data_io.download_file(self.signed_url, requests.Session(), out_dir, 3)


@dataclass_json
@dataclass
class DataRangeReq:
    auth_token: str
    start_ts_s: int
    end_ts_s: int
    redvox_ids: List[str]
    secret_token: Optional[str] = None


@dataclass_json
@dataclass
class DataRangeResp:
    signed_urls: List[str]

    def download_fs(self, out_dir: str):
        data_io.download_files_parallel(self.signed_urls, out_dir, 3)


def request_report_data(api_config: ApiConfig,
                        report_data_req: ReportDataReq) -> Optional[ReportDataResp]:
    """
    Makes an API call to generate a signed URL of a RedVox report.
    :param api_config: An API config.
    :param report_data_req: The request.
    :return: The response.
    """
    url: str = api_config.url(RoutesV1.DATA_REPORT_REQ)
    # noinspection Mypy
    resp: requests.Response = requests.post(url, json=report_data_req.to_dict())
    if resp.status_code == 200:
        # noinspection Mypy
        return ReportDataResp.from_dict(resp.json())
    else:
        return None


def request_range_data(api_config: ApiConfig,
                       data_range_req: DataRangeReq) -> DataRangeResp:
    url: str = api_config.url(RoutesV1.DATA_RANGE_REQ)
    # noinspection Mypy
    resp: requests.Response = requests.post(url, json=data_range_req.to_dict())
    if resp.status_code == 200:
        # noinspection Mypy
        return DataRangeResp.from_dict(resp.json())
    else:
        return DataRangeResp([])
