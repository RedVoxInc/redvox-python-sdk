"""
Prototype class
In Development

Class representing the Station information that can be used to convert Station into another format.
"""

# from typing import List
#
# import numpy as np
#
# import redvox
# from redvox.common.session_model import SessionModel
# from redvox.common.date_time_utils import datetime_from_epoch_microseconds_utc
#
#
# class StationModel:
#     """
#     Model for a station.  Does not include data.
#
#     Properties:
#         id: string, the id of the station.  Users can change this
#
#         uuid: string, the uuid of the station.  This is set by the app when it is installed on a device
#
#         audio_sample_rate_hz: int, the audio sample rate in hz of the station
#
#         sessions: List of SessionModel: the sessions used to create the StationModel
#
#         app: string, name of the app
#
#         app_version: string, version of the app
#
#         api: float, the api version of the data
#
#         sub_api: float, the sub api of the data
#
#         make: string, make of the station
#
#         model: string, model of the station
#
#         num_sessions: int, number of sessions in the model
#
#         sdk_version: string, version of SDK used to create the model
#
#         start_date: float, timestamp of first station data point in microseconds since epoch UTC
#
#         end_date: float, timestamp of last station data point in microseconds since epoch UTC
#
#         changelog: List of str, list of all changes to station during lifetime
#     """
#     def __init__(self,
#                  station_id: str = "",
#                  uuid: str = "",
#                  app_name: str = "Redvox",
#                  api: float = np.nan,
#                  sub_api: float = np.nan,
#                  make: str = "",
#                  model: str = "",
#                  app_version: str = "",
#                  start_date: float = np.nan,
#                  end_date: float = np.nan
#                  ):
#         self.id: str = station_id
#         self.uuid: str = uuid
#         self.app_name: str = app_name
#         self.api: float = api
#         self.sub_api: float = sub_api
#         self.make: str = make
#         self.model: str = model
#         self.app_version: str = app_version
#         self.num_sessions: int = 0
#         self.sdk_version: str = redvox.version()
#         self.start_date: float = start_date
#         self.end_date: float = end_date
#         self.changelog: List[str] = []
#
#     def add_session(self, session: SessionModel):
#         """
#         Add a new session to the StationModel.  id and uuid must match; no change if no match
#
#         :param session: Session to add
#         """
#         if self.id == session.id and self.uuid == session.uuid:
#             self.num_sessions += 1
#             if self.start_date > session.start_date:
#                 self.start_date = session.start_date
#             if self.end_date < session.last_data_timestamp:
#                 self.end_date = session.last_data_timestamp
#             first_timestamp = np.nan if np.isnan(session.first_data_timestamp) \
#                 else datetime_from_epoch_microseconds_utc(
#                 session.first_data_timestamp).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
#             last_timestamp = np.nan if np.isnan(session.last_data_timestamp) \
#                 else datetime_from_epoch_microseconds_utc(
#                 session.last_data_timestamp).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
#             self.changelog.append(f"session from {first_timestamp}: {last_timestamp}")
#
#     @staticmethod
#     def create_from_session(session: SessionModel) -> "StationModel":
#         """
#         Create StationModel from a single session
#
#         :param session: SessionModel to create StationModel from
#         :return: StationModel
#         """
#         try:
#             result = StationModel(session.id, session.uuid, session.app_name, session.api, session.sub_api,
#                                   session.make, session.model, session.app_version, session.start_date,
#                                   session.last_data_timestamp
#                                   )
#         except Exception as e:
#             raise e
#         return result
#
#     @staticmethod
#     def create_from_sessions(sessions: List[SessionModel]) -> "StationModel":
#         """
#         create StationModel from a list of sessions.  Uses the first SessionModel as the base for the StationModel,
#         and will ignore any SessionModel that does not align with the first SessionModel
#
#         :param sessions: sessions to create StationModel from
#         :return: StationModel
#         """
#         p1 = sessions.pop(0)
#         model = StationModel.create_from_session(p1)
#         for p in sessions:
#             model.add_session(p)
#         sessions.insert(0, p1)
#         return model

