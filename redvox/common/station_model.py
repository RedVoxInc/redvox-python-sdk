from typing import List

import numpy as np

import redvox
from redvox.common.session_model import SessionModel


class StationModel:
    """
    Model for a station.  Does not include data.

    Properties:
        id: string, the id of the station.  Users can change this

        uuid: string, the uuid of the station.  This is set by the app when it is installed on a device

        audio_sample_rate_hz: int, the audio sample rate in hz of the station

        sessions: List of SessionModel: the sessions used to create the StationModel

        app: string, name of the app

        app_version: string, version of the app

        api: float, the api version of the data

        sub_api: float, the sub api of the data

        make: string, make of the station

        model: string, model of the station

        num_sessions: int, number of sessions in the model

        sdk_version: string, version of SDK used to create the model
    """
    def __init__(self,
                 station_id: str = "",
                 uuid: str = "",
                 app: str = "Redvox",
                 api: float = np.nan,
                 sub_api: float = np.nan,
                 make: str = "",
                 model: str = "",
                 app_version: str = ""
                 ):
        self.id: str = station_id
        self.uuid: str = uuid
        self.app: str = app
        self.api: float = api
        self.sub_api: float = sub_api
        self.make: str = make
        self.model: str = model
        self.app_version: str = app_version
        self.num_sessions: int = 0
        self.sdk_version: str = redvox.version()

    def add_session(self, session: SessionModel):
        """
        Add a new session to the StationModel.  id and uuid must match; no change if no match

        :param session: Session to add
        """
        if self.id == session.id() and self.uuid == session.uuid():
            self.num_sessions += 1

    @staticmethod
    def create_from_session(session: SessionModel) -> "StationModel":
        """
        Create StationModel from a single session

        :param session: SessionModel to create StationModel from
        :return: StationModel
        """
        try:
            result = StationModel(session.id(), session.uuid(), session.app, session.api, session.sub_api,
                                  session.make, session.model, session.app_version
                                  )
        except Exception as e:
            raise e
        return result

    @staticmethod
    def create_from_sessions(sessions: List[SessionModel]) -> "StationModel":
        """
        create StationModel from a list of sessions.  Uses the first SessionModel as the base for the StationModel,
        and will ignore any SessionModel that does not align with the first SessionModel

        :param sessions: sessions to create StationModel from
        :return: StationModel
        """
        p1 = sessions.pop(0)
        model = StationModel.create_from_session(p1)
        for p in sessions:
            model.add_session(p)
        sessions.insert(0, p1)
        return model

