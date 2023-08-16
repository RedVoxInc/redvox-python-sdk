"""
This module describes methods to store session models from different sources.
This information can be utilized by users as they see fit
"""

from typing import List, Optional, Callable

from redvox.common.session_model import SessionModel
from redvox.common.errors import RedVoxExceptions
from redvox.cloud.client import cloud_client
from redvox.cloud.session_model_api import SessionModelsResp, Session, DynamicSession
from redvox.cloud.errors import CloudApiError


class ModelsContainer:
    """
    Helper module for ApiReader that manages the cloud and SDK session models requested by the ApiReader.

    Cloud models take priority over local models.

    Cloud and Local session models do not overlap.

    Properties:
        cloud_models: SessionModelsResp that contains all the cloud models

        local_models: List[redvox.SessionModel] that contains all the locally created models
    """

    def __init__(self, cloud: Optional[SessionModelsResp] = None, local: Optional[List[SessionModel]] = None):
        """
        initialize the container.

        :param cloud: SessionModelsResp containing all cloud session models
        :param local: list of local session models
        """
        self.cloud_models: Optional[SessionModelsResp] = cloud
        self.local_models: Optional[List[SessionModel]] = local
        self._errors: RedVoxExceptions = RedVoxExceptions("ModelsContainer")

    def __repr__(self):
        """
        :return: representation of ModelsContainer
        """
        return (
            f"cloud_models: {self.cloud_models.__repr__()}, "
            f"local_models: {[f.__repr__() for f in self.local_models]}"
        )

    def as_dict(self) -> dict:
        """
        :return: ModelsContainer as a dictionary
        """
        return {
            "cloud_models": self.cloud_models.to_dict() if self.cloud_models else None,
            "local_models": [f.as_dict() for f in self.local_models] if self.local_models else None,
            "errors": self._errors.as_dict(),
        }

    @staticmethod
    def from_dict(in_dict: dict) -> "ModelsContainer":
        """
        :param in_dict: dictionary to convert into a ModelsContainer
        :return: the ModelsContainer described by the dictionary
        """
        result = ModelsContainer(
            SessionModelsResp.from_dict(in_dict["cloud_models"]) if "cloud_models" in in_dict.keys() else None,
            [SessionModel.from_dict(f) for f in in_dict["local_models"]] if "local_models" in in_dict.keys() else None,
        )
        result._errors = in_dict["errors"]
        return result

    @staticmethod
    def _model_operation(model: Session, func: Callable):
        """
        :param model: Session model to operate on
        :param func: function to perform; takes model as a parameter
        :return: output of the function
        """
        return func(model)

    def get_model(self, session_key: str) -> Optional[Session]:
        """
        :param session_key: the key for the session.  format is: "{STATION_ID}:{STATION_UUID}:{STATION_START_DATE}"
            where STATION_START_DATE is the integer start date of the station in microseconds since epoch UTC.
        :return: cloud session model matching the key or None
        """
        if self.cloud_models:
            for n in self.cloud_models.sessions:
                if session_key == n.session_key():
                    return n
        if self.local_models:
            for n in self.local_models:
                if session_key == n.cloud_session.session_key():
                    return n.cloud_session
        return None

    def get_model_by_key(
        self, station_id: str, uuid: Optional[str] = None, start_date: Optional[int] = None
    ) -> Optional[Session]:
        """
        :param station_id: id of the station to get
        :param uuid: uuid of station to get.  if None, gets the first station that matches other parameters.  Default
                None
        :param start_date: start date in epoch microseconds since epoch UTC of station.  if None, gets first station
                that matches other parameters.  Default None
        :return: First session that matches parameters or None
        """
        # if uuid or start date given, check that it matches, if both given, check if both match
        key_check_func = (
            lambda x: (not uuid and not start_date)
            or (uuid and x.uuid == uuid and not start_date)
            or (start_date and x.start_ts == start_date and not uuid)
            or (uuid and x.uuid == uuid and start_date and x.start_ts == start_date)
        )
        if self.cloud_models:
            for n in self.cloud_models.sessions:
                if n.id == station_id:
                    if self._model_operation(n, key_check_func):
                        return n
        if self.local_models:
            for n in self.local_models:
                if n.cloud_session.id == station_id:
                    if self._model_operation(n.cloud_session, key_check_func):
                        return n.cloud_session
        return None

    def get_all_models(self) -> List[Session]:
        """
        :return: all session models in the container
        """
        models = []
        if self.cloud_models:
            for n in self.cloud_models.sessions:
                models.append(n)
        if self.local_models:
            for n in self.local_models:
                models.append(n.cloud_session)
        return models

    def get_dynamic_session(self, key: str) -> Optional[DynamicSession]:
        """
        :param key: key to the dynamic session, formatted as: ID:UUID:SESSION_START_DATE:DYNAMIC_START:DYNAMIC_END
                    where START and END values times as microseconds since epoch UTC.
        :return: DynamicSession matching the key or None
        """
        key_parts = key.split(":")
        dynamic_session: Optional[DynamicSession] = None
        try:
            client: cloud_client.CloudClient
            with cloud_client() as client:
                dynamic_session: DynamicSession = client.request_dynamic_session_model(
                    f"{key_parts[0]}:{key_parts[1]}:{key_parts[2]}", int(key_parts[3]), int(key_parts[4])
                ).dynamic_session
        except CloudApiError:
            pass
        finally:
            if not dynamic_session:
                for n in self.local_models:
                    for d, s in n.dynamic_sessions.items():
                        if d == key:
                            return s
        return dynamic_session

    def set_cloud_session(self, cloud_resp: SessionModelsResp):
        """
        Set the cloud_models to the cloud_resp
        :param cloud_resp: The new SessionModelsResp from a cloud query
        """
        self.cloud_models = cloud_resp

    def add_cloud_session(self, new_session: Session):
        """
        Add a cloud Session to the container.
        :param new_session: session to add
        """
        if self.cloud_models:
            if self.get_model(new_session.session_key()):
                self._errors.append(f"Attempted to add existing key {new_session.session_key()}")
            else:
                self.cloud_models.sessions.append(new_session)
        else:
            self.set_cloud_session(SessionModelsResp(err=None, sessions=[new_session]))

    def search_cloud_session(
        self,
        id_uuids: Optional[List[str]] = None,
        owner: Optional[str] = None,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        include_public: bool = False,
    ):
        """
        Search the cloud for a range of Session models and overwrites existing cloud_models if there are results.
        All defaults are None except for include_public, which is False.
        Raises any exception found.

        :param id_uuids: An optional list of IDs or ID:UUIDs.
        :param owner: An optional owner.
        :param start_ts: An optional start timestamp in microseconds since epoch UTC.
        :param end_ts: An optional end timestamp in microseconds since epoch UTC.
        :param include_public: Additionally include public sessions that may not be the same as the owner.
        """
        try:
            resp: Optional[SessionModelsResp]
            with cloud_client() as client:
                resp = client.request_session_models(id_uuids, owner, start_ts, end_ts, include_public)
                if len(resp.sessions) > 0:
                    self.cloud_models = resp
        except (CloudApiError, Exception):
            raise

    def set_local_session(self, local_sessions: List[SessionModel]):
        """
        Set the local_models to the local_sessions
        :param local_sessions: The list of new local SessionModel created from files
        """
        self.local_models = local_sessions

    def add_local_session(self, new_session: SessionModel):
        """
        Add a local SessionModel to the container.
        :param new_session: session to add
        """
        if self.local_models:
            if self.get_model(new_session.cloud_session.session_key()):
                self._errors.append(f"Attempted to add existing key {new_session.cloud_session.session_key()}")
            else:
                self.local_models.append(new_session)
        else:
            self.local_models = [new_session]

    def errors(self) -> RedVoxExceptions:
        """
        :return: errors from the ModelsContainer
        """
        return self._errors

    def list_keys(self) -> List[str]:
        """
        :return: all top-level session keys of the models
        """
        keys = []
        if self.cloud_models:
            for k in self.cloud_models.sessions:
                keys.append(k.session_key())
        if self.local_models:
            for k in self.local_models:
                keys.append(k.cloud_session.session_key())
        return keys

    def list_ids(self) -> List[str]:
        """
        :return: all station ids in the models
        """
        keys = []
        if self.cloud_models:
            for k in self.cloud_models.sessions:
                if k.id not in keys:
                    keys.append(k.id)
        if self.local_models:
            for k in self.local_models:
                if k.cloud_session.id not in keys:
                    keys.append(k.cloud_session.id)
        return keys