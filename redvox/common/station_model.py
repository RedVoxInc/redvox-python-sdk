"""
Prototype functions for station location and timing summary
Provides an example of how to access the information from a Station object
This module will contain methods to summarize a single Station
"""
from typing import List, Optional
import math

from dataclasses import dataclass
from dataclasses_json import dataclass_json
import numpy as np

from redvox.common.station import Station
from redvox.api1000.wrapped_redvox_packet.sensors.location import LocationProvider


LOCATION_PROVIDER_IDX: int = 10
LATITUDE_IDX: int = 1
LONGITUDE_IDX: int = 2
ALTITUDE_IDX: int = 3


@dataclass_json
@dataclass
class LocationSummary:
    """
    Summary of a Location.  Includes:

    * Location sensor's name
    * Source of data (provider)
    * Number of points
    * The mean and standard deviation of latitude, longitude, and altitude.

    Properties:
        name: str, name of the Location sensor

        provider: str, name of the provider for location data

        latitude_mean: float, mean of the latitude values.  Default 0.0

        latitude_standard_deviation: float, standard deviation of the latitude values.  Default 0.0

        longitude_mean: float, mean of the longitude values.  Default 0.0

        longitude_standard_deviation: float, standard deviation of the longitude values.  Default 0.0

        altitude_mean: float, mean of the altitude values.  Default 0.0

        altitude_standard_deviation: float, standard deviation of the altitude values.  Default 0.0

        num_pts: int, the number of data points in the summary.  Default 0
    """

    name: str
    provider: str
    latitude_mean: float = 0.0
    latitude_standard_deviation: float = 0.0
    longitude_mean: float = 0.0
    longitude_standard_deviation: float = 0.0
    altitude_mean: float = 0.0
    altitude_standard_deviation: float = 0.0
    num_pts: int = 0

    @staticmethod
    def from_station(stn: Station) -> Optional[List["LocationSummary"]]:
        """
        :param stn: Station to get data from
        :return: List of LocationSummary grouped by provider or None
        """
        loc = stn.find_loc_for_stats()
        if loc:
            samples: np.ndarray = loc.samples()

            if loc.num_samples() == 1:
                return [
                    LocationSummary(
                        loc.name,
                        LocationProvider(int(samples[LOCATION_PROVIDER_IDX][0])).name,
                        samples[LATITUDE_IDX][0],
                        0.0,
                        samples[LONGITUDE_IDX][0],
                        0.0,
                        samples[ALTITUDE_IDX][0],
                        0.0,
                        1,
                    )
                ]

            # for each provider, create a new entry in the dictionary or append new data
            loc_prov_to_data: dict = {}
            lat_samples: np.ndarray = samples[LATITUDE_IDX]
            lng_samples: np.ndarray = samples[LONGITUDE_IDX]
            for j in range(min(len(lat_samples), len(lng_samples))):
                if (not math.isnan(lat_samples[j])) and (not math.isnan(lng_samples[j])):
                    prov = LocationProvider(int(samples[LOCATION_PROVIDER_IDX][j])).name
                    data = np.array(
                        [
                            [samples[LATITUDE_IDX][j]],
                            [samples[LONGITUDE_IDX][j]],
                            [samples[ALTITUDE_IDX][j]],
                        ]
                    )
                    loc_prov_to_data[prov] = (
                        data
                        if prov not in loc_prov_to_data.keys()
                        else np.concatenate([loc_prov_to_data[prov], data], 1)
                    )

            loc_sums = []
            for provider, loc_data in loc_prov_to_data.items():
                loc_sums.append(
                    LocationSummary(
                        loc.name,
                        provider,
                        loc_data[0].mean(),
                        loc_data[0].std(),
                        loc_data[1].mean(),
                        loc_data[1].std(),
                        loc_data[2].mean(),
                        loc_data[2].std(),
                        len(loc_data[0]),
                    )
                )
            return loc_sums
        return None
