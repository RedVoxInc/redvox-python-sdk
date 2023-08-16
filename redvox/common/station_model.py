"""
Prototype class
In Development

Class representing the Station information that can be used to convert Station into another format.
Temporary home for station location and timing summary
"""
from typing import List, Optional
import math

from dataclasses import dataclass
import numpy as np

from redvox.common.station import Station
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider


LOCATION_PROVIDER_IDX: int = 10
LATITUDE_IDX: int = 1
LONGITUDE_IDX: int = 2
ALTITUDE_IDX: int = 3


@dataclass
class Location:
    latitude: float
    longitude: float
    altitude: float


@dataclass
class LocationSummary:
    name: str
    provider: str
    location: Location
    latitude_standard_deviation: float
    longitude_standard_deviation: float
    altitude_standard_deviation: float
    num_pts: int


def get_location_summary(stn: Station) -> Optional[List[LocationSummary]]:
    """
    :return: List of LocationSummary with mean and std deviation organized by provider or None
    """
    loc = stn.find_loc_for_stats()
    if loc:
        samples: np.ndarray = loc.samples()

        if loc.num_samples() == 1:
            return [
                LocationSummary(
                    loc.name,
                    LocationProvider(int(samples[LOCATION_PROVIDER_IDX][0])).name,
                    Location(
                        samples[LATITUDE_IDX][0],
                        samples[LONGITUDE_IDX][0],
                        samples[ALTITUDE_IDX][0],
                    ),
                    0.0,
                    0.0,
                    0.0,
                    1,
                )
            ]

        # for each provider, create a new entry in the dictionary or append new data
        loc_prov_to_data: dict = {}
        lat_samples: np.ndarray = samples[LATITUDE_IDX]
        lng_samples: np.ndarray = samples[LONGITUDE_IDX]
        min_len: int = min(len(lat_samples), len(lng_samples))
        for j in range(min_len):
            lat: float = lat_samples[j]
            lng: float = lng_samples[j]
            if (not math.isnan(lat)) and (not math.isnan(lng)):
                prov = LocationProvider(int(samples[LOCATION_PROVIDER_IDX][j])).name
                data = np.array(
                    [
                        [samples[LATITUDE_IDX][j]],
                        [samples[LONGITUDE_IDX][j]],
                        [samples[ALTITUDE_IDX][j]],
                    ]
                )
                loc_prov_to_data[prov] = (
                    data if prov not in loc_prov_to_data.keys() else np.concatenate([loc_prov_to_data[prov], data], 1)
                )

        loc_sums = []
        for f, v in loc_prov_to_data.items():
            loc_sums.append(
                LocationSummary(
                    loc.name,
                    f,
                    Location(
                        v[0].mean(),
                        v[1].mean(),
                        v[2].mean(),
                    ),
                    v[0].std(),
                    v[1].std(),
                    v[2].std(),
                    len(v[0]),
                )
            )
        return loc_sums
    return None


def print_loc_and_timing_summary(stn: Station):
    """
    Prints the location, GNSS, and time sync information
    :param stn:
    """
    print(f"station_id: {stn.id()}")
    loc_summary = get_location_summary(stn)
    if loc_summary:
        for m in loc_summary:
            print(
                "-----------------------------\n"
                f"location_provider: {m.provider}, num_pts: {m.num_pts}\n"
                f"latitude  mean: {m.location.latitude}, std_dev: {m.latitude_standard_deviation}\n"
                f"longitude mean: {m.location.longitude}, std_dev: {m.longitude_standard_deviation}\n"
                f"altitude  mean: {m.location.altitude}, std_dev: {m.altitude_standard_deviation}"
            )
        print(
            f"-----------------------------\nGNSS timing:\n"
            f"GNSS offset at start: {stn.gps_offset_model().intercept}, slope: {stn.gps_offset_model().slope}\n"
            f"GNSS estimated latency: {stn.gps_offset_model().mean_latency}, "
            f"num_pts: {len(stn.location_sensor().get_gps_timestamps_data())}"
        )
    else:
        print("location data not found.")
    print(
        f"-----------------------------\ntimesync:\n"
        f"best_offset: {stn.timesync_data().best_offset()}, offset_std: {stn.timesync_data().offset_std()}\n"
        f"best_latency: {stn.timesync_data().best_latency()}, latency_std: {stn.timesync_data().latency_std()}\n"
        f"num_pts: {stn.timesync_data().num_tri_messages()}\n*****************************\n"
    )


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
