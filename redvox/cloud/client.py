import threading
from typing import List, Optional

import redvox.cloud.api as api
import redvox.cloud.auth_api as auth_api
import redvox.cloud.data_api as data_api
import redvox.cloud.metadata_api as metadata_api


class CloudClient:
    def __init__(self,
                 username: str,
                 password: str,
                 api_conf: api.ApiConfig = api.ApiConfig.default(),
                 secret_token: Optional[str] = None):
        self.api_conf: api.ApiConfig = api_conf
        self.secret_token: Optional[str] = secret_token

        auth_resp: auth_api.AuthResp = self.authenticate_user(username, password)

        if auth_resp.status != 200 or auth_resp.auth_token is None or len(auth_resp.auth_token) == 0:
            raise RuntimeError("Cloud API authentication error")

        self.auth_token: str = auth_resp.auth_token

        self.__refresh_timer = threading.Timer(60.0, self.__refresh_token)
        self.__refresh_timer.start()

    def __refresh_token(self):
        try:
            self.auth_token = self.refresh_own_auth_token().auth_token
            self.__refresh_timer = threading.Timer(60.0, self.__refresh_token)
            self.__refresh_timer.start()
        except:
            pass

    def close(self):
        self.__refresh_timer.cancel()

    def health_check(self) -> bool:
        return api.health_check(self.api_conf)

    def authenticate_user(self, username: str, password: str) -> auth_api.AuthResp:
        auth_req: auth_api.AuthReq = auth_api.AuthReq(username, password)
        return auth_api.authenticate_user(self.api_conf, auth_req)

    def validate_auth_token(self, auth_token: str) -> Optional[auth_api.ValidateTokenResp]:
        token_req: auth_api.ValidateTokenReq = auth_api.ValidateTokenReq(auth_token)
        return auth_api.validate_token(self.api_conf, token_req)

    def validate_own_auth_token(self) -> Optional[auth_api.ValidateTokenResp]:
        return self.validate_auth_token(self.auth_token)

    def refresh_auth_token(self, auth_token: str) -> Optional[auth_api.RefreshTokenResp]:
        refresh_token_req: auth_api.RefreshTokenReq = auth_api.RefreshTokenReq(auth_token)
        return auth_api.refresh_token(self.api_conf, refresh_token_req)

    def refresh_own_auth_token(self) -> Optional[auth_api.RefreshTokenResp]:
        return self.refresh_auth_token(self.auth_token)

    def request_metadata(self,
                         start_ts_s: int,
                         end_ts_s: int,
                         station_ids: List[str],
                         metadata_to_include: List[str]) -> Optional[metadata_api.MetadataResp]:
        metadata_req: metadata_api.MetadataReq = metadata_api.MetadataReq(self.auth_token,
                                                                          start_ts_s,
                                                                          end_ts_s,
                                                                          station_ids,
                                                                          metadata_to_include,
                                                                          self.secret_token)
        return metadata_api.request_metadata(self.api_conf, metadata_req)

    def request_timing_metadata(self,
                                start_ts_s: int,
                                end_ts_s: int,
                                station_ids: List[str]) -> metadata_api.TimingMetaResponse:
        timing_req: metadata_api.TimingMetaRequest = metadata_api.TimingMetaRequest(self.auth_token,
                                                                                    start_ts_s,
                                                                                    end_ts_s,
                                                                                    station_ids,
                                                                                    self.secret_token)
        return metadata_api.request_timing_metadata(self.api_conf, timing_req)

    def request_report_data(self, report_id: str) -> Optional[data_api.ReportDataResp]:
        report_data_req: data_api.ReportDataReq = data_api.ReportDataReq(self.auth_token,
                                                                         report_id,
                                                                         self.secret_token)
        return data_api.request_report_data(self.api_conf, report_data_req)

    def request_data_range(self,
                           start_ts_s: int,
                           end_ts_s: int,
                           station_ids: List[str]) -> data_api.DataRangeResp:
        data_range_req: data_api.DataRangeReq = data_api.DataRangeReq(self.auth_token,
                                                                      start_ts_s,
                                                                      end_ts_s,
                                                                      station_ids,
                                                                      self.secret_token)

        return data_api.request_range_data(self.api_conf, data_range_req)

